#!/usr/bin/env python3
"""
pm-priority.py — Multi-project priority ranking for ProjectManager.

Requires Python >= 3.10.

Reads tasks/queue.json and outputs a ranked markdown table sorted by:
  1. Paused tasks first (status: paused)
  2. project_manager tasks before other projects
  3. Priority: P1 > P2 > P3  (looked up from backlog.md via BL-NNN in title)
  4. Oldest created date wins within the same tier

Usage:
    python3 scripts/pm-priority.py [--queue PATH] [--backlog PATH] [--status STATUS[,...]]

Options:
    --queue PATH    Path to queue.json  (default: tasks/queue.json)
    --backlog PATH  Path to backlog.md  (default: tasks/backlog.md)
    --status LIST   Comma-separated statuses to include
                    (default: paused,pending,in_progress,review,test)
                    Known values: paused, pending, in_progress, review, test, done, failed
"""

import argparse
import json
import re
import sys
from pathlib import Path

_PRIORITY_ORDER = {"P1": 0, "P2": 1, "P3": 2}
_DEFAULT_STATUSES = "paused,pending,in_progress,review,test"
_KNOWN_STATUSES = {"paused", "pending", "in_progress", "review", "test", "done", "failed"}
_BL_RE = re.compile(r"\bBL-(\d+)\b")

# Workspace root — paths passed via --queue/--backlog must be inside this directory
_WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


def _safe_path(raw: str, label: str) -> Path:
    """Resolve a user-supplied path and assert it is inside the workspace root."""
    resolved = Path(raw).resolve()
    if _WORKSPACE_ROOT not in (resolved, *resolved.parents):
        print(
            f"ERROR: {label} path is outside the workspace root: {resolved}",
            file=sys.stderr,
        )
        sys.exit(1)
    return resolved


def load_backlog_priorities(backlog_path: Path) -> dict[str, str]:
    """Return a mapping of BL-NNN → priority by parsing backlog.md table rows.

    Columns (1-based after splitting on '|'):
      cols[1] = BL-NNN, cols[5] = Priority (P1/P2/P3)
    Only rows starting with '| BL-' and having a recognised priority are stored.
    """
    priorities: dict[str, str] = {}
    if not backlog_path.exists():
        return priorities
    for line in backlog_path.read_text().splitlines():
        # Table rows look like: | BL-059 | EPIC-003 | ... | pi-homelab | P1 | ...
        if not line.startswith("| BL-"):
            continue
        cols = [c.strip() for c in line.split("|")]
        # cols[0] == '', cols[1] == BL-NNN, cols[5] == Priority
        if len(cols) >= 6:
            bl_id = cols[1].strip()
            priority = cols[5].strip()
            if bl_id and priority in _PRIORITY_ORDER:
                priorities[bl_id] = priority
    return priorities


def extract_bl_id(title: str) -> str | None:
    """Return the first BL-NNN found in a task title, or None."""
    match = _BL_RE.search(title)
    return f"BL-{match.group(1)}" if match else None


def rank_key(task: dict, priorities: dict[str, str]) -> tuple:
    """Return a sort key tuple: (paused_tier, pm_tier, priority_tier, created).

    Ranking order (lower = higher priority):
      1. paused tasks (0) before all others (1)
      2. project_manager (0) before other projects (1)
      3. P1 (0) > P2 (1) > P3 (2) > unknown (9)
      4. Oldest created date (ascending ISO-8601 string)
    """
    status = task.get("status", "")
    project = task.get("project", "")
    title = task.get("title", "")

    bl_id = extract_bl_id(title)
    raw_priority = priorities.get(bl_id, "") if bl_id else ""
    priority_rank = _PRIORITY_ORDER.get(raw_priority, 9)

    is_paused = 0 if status == "paused" else 1
    is_pm = 0 if project == "project_manager" else 1
    created = task.get("created", "9999-99-99")

    return (is_paused, is_pm, priority_rank, created)


def build_table(tasks: list[dict], priorities: dict[str, str]) -> str:
    """Return a markdown table from a ranked task list."""
    header = "| Rank | Task ID | Project | Priority | Status | Title |"
    sep = "|---|---|---|---|---|---|"
    rows = [header, sep]
    for i, task in enumerate(tasks, start=1):
        title = task.get("title", "—").replace("|", "\\|")
        bl_id = extract_bl_id(task.get("title", ""))
        priority = priorities.get(bl_id, "—") if bl_id else "—"
        row = (
            f"| {i} "
            f"| {task.get('id', '—')} "
            f"| {task.get('project', '—')} "
            f"| {priority} "
            f"| {task.get('status', '—')} "
            f"| {title} |"
        )
        rows.append(row)
    return "\n".join(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="PM multi-project priority ranking")
    parser.add_argument("--queue", default="tasks/queue.json")
    parser.add_argument("--backlog", default="tasks/backlog.md")
    parser.add_argument("--status", default=_DEFAULT_STATUSES)
    args = parser.parse_args()

    queue_path = _safe_path(args.queue, "--queue")
    backlog_path = _safe_path(args.backlog, "--backlog")

    if not queue_path.exists():
        print(f"ERROR: queue file not found: {queue_path}", file=sys.stderr)
        sys.exit(1)

    # Validate --status tokens
    include_statuses: set[str] = set()
    for token in args.status.split(","):
        token = token.strip()
        if token not in _KNOWN_STATUSES:
            print(
                f"ERROR: unknown status '{token}'. Known: {', '.join(sorted(_KNOWN_STATUSES))}",
                file=sys.stderr,
            )
            sys.exit(1)
        include_statuses.add(token)

    priorities = load_backlog_priorities(backlog_path)

    with queue_path.open() as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as exc:
            print(f"ERROR: queue.json is not valid JSON: {exc}", file=sys.stderr)
            sys.exit(1)

    tasks = data.get("tasks", [])
    filtered = [t for t in tasks if t.get("status") in include_statuses]
    ranked = sorted(filtered, key=lambda t: rank_key(t, priorities))

    if not ranked:
        print("*(no tasks matching the requested statuses)*")
        return

    print(f"## Priority Ranking — {len(ranked)} task(s)\n")
    print(build_table(ranked, priorities))


if __name__ == "__main__":
    main()
