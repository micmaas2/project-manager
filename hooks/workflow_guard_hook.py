#!/usr/bin/env python3
"""
Workflow Guard Hook for Claude Code
Enforces two CLAUDE.md must-always-follow rules:

  Rule 1 (Bash PreToolUse): Block `git commit --no-verify` — absolutely prohibited.
  Rule 2 (Edit/Write PreToolUse): Block setting queue.json task status to "done"
          without a non-empty artefact_path in the same change.

Both rules are better enforced at edit time than at review time because they are
binary, detectable by regex, and have caused repeated incidents.
"""

import json
import re
import sys

# ── Rule 1: git commit --no-verify ──────────────────────────────────────────

NO_VERIFY_RE = re.compile(r"git\s+commit\b[^;\n]*--no-verify")

NO_VERIFY_REMINDER = """⛔ BLOCKED: git commit --no-verify detected.

CLAUDE.md rule: "Pre-Commit Hooks: ALWAYS active — NEVER use git commit --no-verify"

The pre-commit hook enforces branch protection, credential scanning, and agent YAML
policy-schema consistency. Bypassing it defeats these controls.

If a pre-commit hook is failing:
  1. Investigate the root cause (do not bypass).
  2. Fix the underlying issue, re-stage, then commit normally.
  3. If the hook has a bug, fix the hook script in hooks/ and commit that first.

There is no legitimate use of --no-verify in this codebase."""


# ── Rule 2: queue.json status:done without artefact_path ────────────────────

QUEUE_JSON_RE = re.compile(r'"status"\s*:\s*"done"')
ARTEFACT_PATH_RE = re.compile(r'"artefact_path"\s*:\s*"([^"]*)"')

QUEUE_DONE_NO_ARTEFACT_REMINDER = """⛔ BLOCKED: queue.json task marked "status": "done" without a non-empty artefact_path.

CLAUDE.md rule: "a task may not be set to status: done without a non-empty artefact_path.
If no code was produced, set the path and create a verification.md"

Steps to resolve:
  1. Create the artefact directory: mkdir -p artefacts/<task-id>/
  2. Write artefacts/<task-id>/verification.md with commands run, output, and PASS/FAIL per criterion.
  3. Set "artefact_path": "artefacts/<task-id>/" in queue.json before marking done.

SelfImprover cannot retrospect tasks with no artefact directory — traceability requires it."""


def check_bash_command(command: str) -> tuple[str | None, str | None]:
    """Check Bash tool command for prohibited patterns."""
    if NO_VERIFY_RE.search(command):
        return "git_commit_no_verify", NO_VERIFY_REMINDER
    return None, None


def check_queue_json_write(tool_name: str, file_path: str, content: str) -> tuple[str | None, str | None]:
    """Check Write to queue.json for done-without-artefact-path pattern.

    Edit/MultiEdit operate on diff fragments (new_string), not the full document.
    A valid two-step edit — Edit 1: set status=done, Edit 2: set artefact_path — would
    be falsely blocked on Edit 1 because the fragment contains status:done without
    artefact_path. Rule 2 is therefore enforced on Write only (full document available).
    """
    if tool_name in ("Edit", "MultiEdit"):
        return None, None  # Cannot reliably check fragment; only enforce on Write

    # Only check queue.json writes
    if not file_path.endswith("tasks/queue.json") and not file_path.endswith("/queue.json"):
        return None, None

    # If content sets status:done, artefact_path must also be non-empty in the same content
    if QUEUE_JSON_RE.search(content):
        # Check if artefact_path is being set to a non-empty value in the same content block
        paths = ARTEFACT_PATH_RE.findall(content)
        # If any artefact_path match is non-empty (non-empty string), allow it
        if any(p.strip() for p in paths):
            return None, None
        # No non-empty artefact_path found — block
        return "queue_done_no_artefact_path", QUEUE_DONE_NO_ARTEFACT_REMINDER

    return None, None


def extract_content(tool_name: str, tool_input: dict) -> str:
    """Extract the content/command being written or run."""
    if tool_name == "Bash":
        return tool_input.get("command", "")
    if tool_name == "Write":
        return tool_input.get("content", "")
    if tool_name == "Edit":
        return tool_input.get("new_string", "")
    if tool_name == "MultiEdit":
        edits = tool_input.get("edits", [])
        return " ".join(e.get("new_string", "") for e in edits)
    return ""


def main() -> None:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)  # Fail open on parse error

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    content = extract_content(tool_name, tool_input)

    rule_name: str | None = None
    reminder: str | None = None

    if tool_name == "Bash":
        rule_name, reminder = check_bash_command(content)
    elif tool_name in ("Edit", "Write", "MultiEdit"):
        file_path = tool_input.get("file_path", "")
        rule_name, reminder = check_queue_json_write(tool_name, file_path, content)

    if rule_name and reminder:
        print(reminder, file=sys.stderr)
        sys.exit(2)  # Block execution (PreToolUse exit code 2)

    sys.exit(0)


if __name__ == "__main__":
    main()
