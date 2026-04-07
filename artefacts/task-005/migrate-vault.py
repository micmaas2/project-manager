#!/usr/bin/env python3
"""migrate-vault.py - Retroactive Obsidian vault quality improvement.

Migrates old-format notes (# heading + **Bold:** fields + #hashtag tags) to
YAML frontmatter format, normalises tags, and re-enriches non-LinkedIn URL
captures via the Claude API.

Usage:
    python3 migrate-vault.py --vault /opt/obsidian-vault [--dry-run]

Environment:
    ANTHROPIC_API_KEY - required for URL re-enrichment (link notes only)
"""

import argparse
import json
import os
import re
import sys
from typing import Optional

_PRIVATE_IP_RE = re.compile(
    r"^https?://(localhost|127\.|10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)"
)
_URL_RE = re.compile(r"https?://\S+")
_ACTION_TAGS = frozenset(
    {"buy", "follow-up", "implement", "read-deeper", "share", "review", "needs-review"}
)


def is_old_format(content: str) -> bool:
    """Return True if the note uses the old # heading + **Bold:** field format.

    Requires both: a leading # heading (not YAML frontmatter) AND at least one
    **Key:** value line — so plain Markdown files (e.g. Dashboard.md) are not matched.
    """
    if content.lstrip().startswith("---"):
        return False
    has_heading = any(line.startswith("# ") for line in content.splitlines())
    has_bold_field = bool(_BOLD_RE.search(content))
    return has_heading and has_bold_field


_BOLD_RE = re.compile(r"^\*\*(\w+):\*\*\s*(.+)$", re.MULTILINE)


def _extract_section(lines: list, header: str, stop_on: tuple = ()) -> str:
    """Extract text content of a Markdown section, stopping at stop_on headers or '---'."""
    collected = []
    active = False
    for line in lines:
        stripped = line.strip()
        if stripped == header:
            active = True
            continue
        if active:
            if stripped == "---" or stripped in stop_on:
                break
            collected.append(line)
    return "\n".join(collected).strip()


def _apply_bold_field(key: str, val: str, fields: dict) -> None:
    """Write a single parsed **Key:** value into fields dict."""
    if key == "date":
        fields["date"] = val
    elif key == "category":
        fields["category"] = val
    elif key == "source":
        fields["source"] = val
    elif key == "channel":
        fields["channel"] = val
    elif key == "tags":
        fields["tags"] = [normalize_tag(t) for t in val.split() if t.startswith("#")]


def parse_old_format(content: str) -> dict:
    """Parse an old-format note into a fields dict."""
    fields: dict = {
        "title": "",
        "date": "",
        "category": "Inbox",
        "source": "thought",
        "channel": "telegram",
        "tags": [],
        "summary": "",
        "raw_capture": "",
    }

    lines = content.splitlines()

    for line in lines:
        if line.startswith("# "):
            fields["title"] = line[2:].strip()
            break

    for line in lines:
        match = _BOLD_RE.match(line.strip())
        if match:
            _apply_bold_field(match.group(1).lower(), match.group(2).strip(), fields)

    fields["summary"] = _extract_section(
        lines, "## Summary", stop_on=("## Raw capture",)
    )
    fields["raw_capture"] = _extract_section(lines, "## Raw capture")

    return fields


def normalize_tag(tag: str) -> str:
    """Normalise a tag to hyphenated lowercase. Strips leading #."""
    tag = tag.lstrip("#")
    # Split camelCase: insert hyphen between lower→upper transitions
    tag = re.sub(r"([a-z])([A-Z])", r"\1-\2", tag)
    return tag.lower()


def derive_topic(tags: list) -> str:
    """Pick first non-action tag as topic slug. Falls back to 'inbox'."""
    for tag in tags:
        if tag not in _ACTION_TAGS:
            # Remove hyphens to produce a single-word slug
            return tag.replace("-", "")
    return "inbox"


def is_linkedin_url(url: str) -> bool:
    """Return True if the URL is from linkedin.com."""
    return "linkedin.com" in url


def extract_url(raw_capture: str) -> Optional[str]:
    """Extract the first HTTP URL from raw_capture. Returns None if not found."""
    match = _URL_RE.search(raw_capture)
    return match.group(0) if match else None


def fetch_page_content(url: str) -> Optional[str]:
    """Fetch URL and return extracted plain text (up to 3000 chars).

    Returns None on any error, including private-IP addresses.
    """
    if _PRIVATE_IP_RE.match(url):
        return None
    try:
        import requests  # pylint: disable=import-outside-toplevel
        from bs4 import BeautifulSoup  # pylint: disable=import-outside-toplevel

        resp = requests.get(url, timeout=10, allow_redirects=True)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return text[:3000]
    except Exception:  # pylint: disable=broad-except
        return None


def reenrich_via_claude(raw_capture: str, page_text: str, client) -> Optional[dict]:
    """Call Claude API to produce enriched metadata.

    Returns a dict with title/summary/key_points/analysis/tags/topic, or None on failure.
    """
    prompt_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "..",
        "pensieve",
        "prompts",
        "claude-processor.txt",
    )
    try:
        with open(prompt_path, encoding="utf-8") as fh:
            prompt_template = fh.read()
    except OSError:
        prompt_template = (
            "Process the following raw capture and return ONLY valid JSON.\n"
            "Input: {raw_message}\nSource channel: {source_type_hint}\n"
            'Return: {"title":"","summary":"","key_points":[],"analysis":"",'
            '"tags":[],"topic":"","category":"","source_type":""}'
        )

    augmented_raw = raw_capture
    if page_text:
        augmented_raw += f"\n\n[Page content]:\n{page_text}"

    prompt = prompt_template.replace("{raw_message}", augmented_raw).replace(
        "{source_type_hint}", "telegram"
    )

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        response_text = message.content[0].text.strip()
        # Strip markdown code fences if present
        if response_text.startswith("```"):
            response_text = re.sub(r"^```[a-z]*\n?", "", response_text)
            response_text = re.sub(r"\n?```$", "", response_text)
        return json.loads(response_text)
    except Exception:  # pylint: disable=broad-except
        return None


def build_new_format(fields: dict) -> str:
    """Render new-format note content from a fields dict."""
    tags_str = ", ".join(fields["tags"])
    topic = fields.get("topic") or derive_topic(fields["tags"])

    lines = [
        "---",
        f'title: "{fields["title"]}"',
        f'date: {fields["date"]}',
        f'category: {fields["category"]}',
        f"topic: {topic}",
        f'source: {fields["source"]}',
        f'channel: {fields["channel"]}',
        f"tags: [{tags_str}]",
        "---",
        "",
        "## Summary",
        "",
        fields["summary"],
    ]

    key_points = fields.get("key_points", [])
    if key_points:
        lines += ["", "## Key Points", ""]
        for point in key_points:
            lines.append(f"- {point}")

    analysis = fields.get("analysis", "")
    if analysis:
        lines += ["", "## Analysis", "", analysis]

    lines += ["", "---", "", "## Raw capture", "", fields["raw_capture"], ""]

    return "\n".join(lines)


def migrate_note(filepath: str, dry_run: bool, client) -> bool:
    """Detect, migrate and (optionally) write back a single note.

    Returns True if the note was changed (or would be in dry-run mode).
    """
    with open(filepath, encoding="utf-8") as fh:
        content = fh.read()

    if not is_old_format(content):
        print(f"  skip   {filepath}")
        return False

    fields = parse_old_format(content)
    fields["topic"] = derive_topic(fields["tags"])

    if fields["source"] == "link":
        url = extract_url(fields["raw_capture"])
        if url and not is_linkedin_url(url):
            page_text = fetch_page_content(url)
            if page_text and client:
                enriched = reenrich_via_claude(fields["raw_capture"], page_text, client)
                if enriched:
                    fields["title"] = enriched.get("title", fields["title"])
                    fields["summary"] = enriched.get("summary", fields["summary"])
                    fields["key_points"] = enriched.get("key_points", [])
                    fields["analysis"] = enriched.get("analysis", "")
                    raw_tags = [normalize_tag(t) for t in enriched.get("tags", [])]
                    fields["tags"] = raw_tags
                    fields["topic"] = enriched.get("topic") or derive_topic(raw_tags)
                    print(f"  enrich {filepath}")
                else:
                    _add_needs_review(fields)
                    print(f"  needs-review (enrich failed)  {filepath}")
            else:
                _add_needs_review(fields)
                reason = "fetch failed" if url else "no url"
                print(f"  needs-review ({reason})  {filepath}")
        else:
            _add_needs_review(fields)
            reason = "linkedin" if (url and is_linkedin_url(url)) else "no url"
            print(f"  needs-review ({reason})  {filepath}")
    else:
        print(f"  migrate {filepath}")

    new_content = build_new_format(fields)

    if dry_run:
        print(f"  [dry-run] would write {len(new_content)} bytes → {filepath}")
    else:
        with open(filepath, "w", encoding="utf-8") as fh:
            fh.write(new_content)

    return True


def _add_needs_review(fields: dict) -> None:
    """Add needs-review tag if not already present."""
    if "needs-review" not in fields["tags"]:
        fields["tags"].append("needs-review")


def parse_yaml_frontmatter(content: str) -> Optional[dict]:
    """Extract fields from a YAML-frontmatter note. Returns None if not parseable."""
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    try:
        end = lines.index("---", 1)
    except ValueError:
        return None
    fm_lines = lines[1:end]
    fields: dict = {}
    for line in fm_lines:
        if ": " in line:
            key, _, val = line.partition(": ")
            fields[key.strip()] = val.strip().strip('"')
    # Parse tags list: "tags: [a, b, c]"
    for line in fm_lines:
        if line.startswith("tags:"):
            raw = line[5:].strip().strip("[]")
            fields["tags"] = [t.strip() for t in raw.split(",") if t.strip()]
            break
    # Extract summary and raw_capture from body
    body_lines = lines[end + 1:]
    fields["summary"] = _extract_section(
        body_lines, "## Summary",
        stop_on=("## Key Points", "## Analysis", "## Raw capture")
    )
    fields["key_points_text"] = _extract_section(
        body_lines, "## Key Points", stop_on=("## Analysis", "## Raw capture")
    )
    fields["analysis"] = _extract_section(body_lines, "## Analysis", stop_on=("## Raw capture",))
    fields["raw_capture"] = _extract_section(body_lines, "## Raw capture")
    return fields


def _reenrich_skip_reason(fields: dict) -> Optional[str]:
    """Return a skip reason string if this note should not be re-enriched, else None."""
    if "needs-review" not in fields.get("tags", []):
        return "no needs-review"
    if fields.get("source") != "link":
        return "not a link note"
    url = extract_url(fields.get("raw_capture", ""))
    if not url or is_linkedin_url(url):
        return "linkedin/no-url"
    return None


def reenrich_note(filepath: str, dry_run: bool, client) -> bool:
    """Re-enrich a YAML-frontmatter note that has the needs-review tag.

    Attempts URL fetch + Claude API enrichment. Returns True if changed.
    """
    with open(filepath, encoding="utf-8") as fh:
        content = fh.read()

    fields = parse_yaml_frontmatter(content)
    if not fields:
        return False

    reason = _reenrich_skip_reason(fields)
    if reason:
        print(f"  skip   ({reason}) {filepath}")
        return False

    url = extract_url(fields.get("raw_capture", ""))
    page_text = fetch_page_content(url)
    if not page_text:
        print(f"  skip   (fetch failed) {filepath}")
        return False

    enriched = reenrich_via_claude(fields["raw_capture"], page_text, client)
    if not enriched:
        print(f"  skip   (enrich failed) {filepath}")
        return False

    # Remove needs-review, apply enriched data
    new_tags = [normalize_tag(t) for t in enriched.get("tags", [])]
    new_fields = {
        "title": enriched.get("title", fields.get("title", "")),
        "date": fields.get("date", ""),
        "category": enriched.get("category", fields.get("category", "Inbox")),
        "topic": enriched.get("topic") or derive_topic(new_tags),
        "source": fields.get("source", "link"),
        "channel": fields.get("channel", "telegram"),
        "tags": new_tags,
        "summary": enriched.get("summary", fields.get("summary", "")),
        "key_points": enriched.get("key_points", []),
        "analysis": enriched.get("analysis", ""),
        "raw_capture": fields.get("raw_capture", ""),
    }
    print(f"  enrich {filepath}")
    new_content = build_new_format(new_fields)

    if dry_run:
        print(f"  [dry-run] would write {len(new_content)} bytes → {filepath}")
    else:
        with open(filepath, "w", encoding="utf-8") as fh:
            fh.write(new_content)
    return True


def main() -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="Retroactively migrate Pensieve vault notes to YAML frontmatter."
    )
    parser.add_argument("--vault", required=True, help="Path to Obsidian vault root")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned changes without writing files",
    )
    parser.add_argument(
        "--reenrich-needs-review",
        action="store_true",
        help="Re-enrich already-migrated notes that have the needs-review tag",
    )
    args = parser.parse_args()

    vault_path = os.path.realpath(args.vault)
    if not os.path.isdir(vault_path):
        print(f"ERROR: vault path does not exist: {vault_path}", file=sys.stderr)
        return 1

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    client = None
    if api_key:
        try:
            import anthropic  # pylint: disable=import-outside-toplevel

            client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            print(
                "WARNING: anthropic package not installed; URL re-enrichment disabled.",
                file=sys.stderr,
            )
    else:
        print(
            "WARNING: ANTHROPIC_API_KEY not set; URL re-enrichment disabled.",
            file=sys.stderr,
        )

    changed = 0
    skipped = 0
    action_fn = reenrich_note if args.reenrich_needs_review else migrate_note
    for dirpath, _dirs, filenames in os.walk(vault_path):
        for fname in sorted(filenames):
            if not fname.endswith(".md"):
                continue
            filepath = os.path.join(dirpath, fname)
            # Safety: ensure path stays within vault
            if not os.path.realpath(filepath).startswith(vault_path):
                continue
            if action_fn(filepath, args.dry_run, client):
                changed += 1
            else:
                skipped += 1

    action = "would migrate" if args.dry_run else "migrated"
    print(
        f"\nDone: {action} {changed} note(s); skipped {skipped} already-current note(s)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
