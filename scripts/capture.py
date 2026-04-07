#!/usr/bin/env python3
"""
capture.py — Submit backlog items or Pensieve notes from a laptop via GitHub API.

No Claude Code, SSH, or VPN required. Requires a GitHub PAT with repo write scope.

Usage:
  # Backlog item (lands in tasks/telegram-inbox.md, picked up by PM at next session)
  GITHUB_TOKEN=ghp_... python3 capture.py backlog "Investigate caching strategy for API"

  # Pensieve note with URL
  GITHUB_TOKEN=ghp_... python3 capture.py pensieve "Great article on RAG" \\
      --url "https://example.com/article" --note "Key point: chunk size matters"

  # Dry run (shows what would be committed, no writes)
  GITHUB_TOKEN=ghp_... python3 capture.py backlog "Test item" --dry-run

Environment variables:
  GITHUB_TOKEN   GitHub PAT with repo write scope (required)
  PM_REPO        Override PM repo (default: micmaas2/project-manager)
  PENSIEVE_REPO  Override Pensieve repo (default: micmaas2/pensieve)
"""

import argparse
import base64
import datetime
import json
import os
import sys
import urllib.error
import urllib.request

GITHUB_API = "https://api.github.com"
DEFAULT_PM_REPO = "micmaas2/project-manager"
DEFAULT_PENSIEVE_REPO = "micmaas2/pensieve"
DEFAULT_BRANCH = "main"


# ---------------------------------------------------------------------------
# GitHub API helpers
# ---------------------------------------------------------------------------

def _request(token: str, method: str, path: str, body: dict | None = None) -> dict:
    url = f"{GITHUB_API}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if body:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        print(f"GitHub API error {exc.code}: {detail}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as exc:
        print(f"Network error: {exc.reason}", file=sys.stderr)
        sys.exit(1)


def _get_file(token: str, repo: str, path: str, branch: str) -> dict:
    return _request(token, "GET", f"/repos/{repo}/contents/{path}?ref={branch}")


def _put_file(
    token: str,
    repo: str,
    path: str,
    message: str,
    content: str,
    sha: str | None,
    branch: str,
) -> dict:
    body: dict = {
        "message": message,
        "content": base64.b64encode(content.encode()).decode(),
        "branch": branch,
    }
    if sha:
        body["sha"] = sha
    return _request(token, "PUT", f"/repos/{repo}/contents/{path}", body)


# ---------------------------------------------------------------------------
# Capture: backlog
# ---------------------------------------------------------------------------

def capture_backlog(
    token: str,
    repo: str,
    title: str,
    branch: str,
    dry_run: bool,
) -> None:
    """Append an item to tasks/telegram-inbox.md via GitHub API commit."""
    file_path = "tasks/telegram-inbox.md"
    today = datetime.date.today().isoformat()
    new_line = f"- {today}: {title}\n"

    file_info = _get_file(token, repo, file_path, branch)
    current = base64.b64decode(file_info["content"]).decode()

    # Ensure single trailing newline before appending
    updated = current.rstrip("\n") + "\n" + new_line

    commit_message = f"[CAPTURE] Backlog item from laptop: {title[:70]}"

    if dry_run:
        print("[dry-run] Would commit to:", file=sys.stderr)
        print(f"  repo:    {repo}", file=sys.stderr)
        print(f"  branch:  {branch}", file=sys.stderr)
        print(f"  file:    {file_path}", file=sys.stderr)
        print(f"  message: {commit_message}", file=sys.stderr)
        print(f"  append:  {new_line.strip()}", file=sys.stderr)
        return

    _put_file(token, repo, file_path, commit_message, updated, file_info["sha"], branch)
    print(f"Backlog item added → {repo}/{file_path} ({branch})")
    print(f"Entry: {new_line.strip()}")


# ---------------------------------------------------------------------------
# Capture: pensieve
# ---------------------------------------------------------------------------

def capture_pensieve(
    token: str,
    repo: str,
    title: str,
    url: str | None,
    note: str | None,
    branch: str,
    dry_run: bool,
) -> None:
    """Create a new Pensieve note via GitHub API commit."""
    today = datetime.date.today().isoformat()
    slug = "".join(c if c.isalnum() or c == "-" else "-" for c in title.lower())[:50].strip("-")
    file_path = f"captures/{today}-{slug}.md"

    lines = [
        "---",
        f'title: "{title}"',
        f"date: {today}",
        "source: laptop-capture",
    ]
    if url:
        lines.append(f'url: "{url}"')
    lines += ["tags: []", "---", ""]
    if note:
        lines.append(note)
        lines.append("")

    content = "\n".join(lines)
    commit_message = f"[CAPTURE] Pensieve note from laptop: {title[:70]}"

    if dry_run:
        print("[dry-run] Would commit to:", file=sys.stderr)
        print(f"  repo:    {repo}", file=sys.stderr)
        print(f"  branch:  {branch}", file=sys.stderr)
        print(f"  file:    {file_path}", file=sys.stderr)
        print(f"  message: {commit_message}", file=sys.stderr)
        print("--- content ---", file=sys.stderr)
        print(content, file=sys.stderr)
        return

    # Check if file already exists (unlikely for new notes, but handle it)
    sha = None
    try:
        file_info = _get_file(token, repo, file_path, branch)
        sha = file_info["sha"]
    except SystemExit:
        pass  # New file — no SHA needed

    _put_file(token, repo, file_path, commit_message, content, sha, branch)
    print(f"Pensieve note created → {repo}/{file_path} ({branch})")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Capture backlog items or Pensieve notes from laptop via GitHub API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "type",
        choices=["backlog", "pensieve"],
        help="Capture type: 'backlog' appends to telegram-inbox.md; 'pensieve' creates a vault note",
    )
    parser.add_argument("title", help="Title or description of the item")
    parser.add_argument("--url", help="Source URL (pensieve only)")
    parser.add_argument("--note", help="Optional body text (pensieve only)")
    parser.add_argument(
        "--pm-repo",
        default=os.environ.get("PM_REPO", DEFAULT_PM_REPO),
        help=f"PM GitHub repo (default: {DEFAULT_PM_REPO})",
    )
    parser.add_argument(
        "--pensieve-repo",
        default=os.environ.get("PENSIEVE_REPO", DEFAULT_PENSIEVE_REPO),
        help=f"Pensieve GitHub repo (default: {DEFAULT_PENSIEVE_REPO})",
    )
    parser.add_argument(
        "--branch",
        default=DEFAULT_BRANCH,
        help=f"Target branch (default: {DEFAULT_BRANCH})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be committed without making any changes",
    )
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        print("Error: GITHUB_TOKEN environment variable is not set.", file=sys.stderr)
        print("Create a PAT at https://github.com/settings/tokens with 'repo' scope.", file=sys.stderr)
        sys.exit(1)

    if args.type == "backlog":
        capture_backlog(
            token=token,
            repo=args.pm_repo,
            title=args.title,
            branch=args.branch,
            dry_run=args.dry_run,
        )
    else:
        capture_pensieve(
            token=token,
            repo=args.pensieve_repo,
            title=args.title,
            url=args.url,
            note=args.note,
            branch=args.branch,
            dry_run=args.dry_run,
        )


if __name__ == "__main__":
    main()
