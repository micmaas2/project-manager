#!/usr/bin/env python3
"""
cross-kanban.py — Unified cross-project kanban view for ProjectManager.

Reads tasks/queue.json and outputs a markdown kanban grouped by project, then
sorted by status within each project. Only active tasks are shown
(paused, in_progress, review, test, pending). Projects with no active tasks
are omitted. Prints 'No active tasks' when the queue is empty or all tasks
are done/failed.

Requires Python >= 3.10.

Usage:
    python3 scripts/cross-kanban.py [--queue PATH]

Options:
    --queue PATH    Path to queue.json  (default: tasks/queue.json)
"""

import argparse
import json
import sys
from pathlib import Path

# Active statuses included in the kanban view
_ACTIVE_STATUSES = {"paused", "in_progress", "review", "test", "pending"}

# Display order: most urgent / blocked statuses first
_STATUS_ORDER = ["paused", "in_progress", "review", "test", "pending"]

# Workspace root — paths passed via --queue must reside inside here
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


def _status_rank(task: dict) -> tuple:
    """Sort key: status display order, then oldest created date first."""
    status = task.get("status", "")
    rank = _STATUS_ORDER.index(status) if status in _STATUS_ORDER else 99
    return (rank, task.get("created", "9999-99-99"))


def _build_project_section(project: str, tasks: list[dict]) -> str:
    """Return a markdown section for one project's active tasks."""
    sorted_tasks = sorted(tasks, key=_status_rank)
    lines = [
        f"### {project}",
        "",
        "| Status | Task ID | Title |",
        "|---|---|---|",
    ]
    for t in sorted_tasks:
        title = t.get("title", "—").replace("|", "\\|")
        status = t.get("status", "—")
        task_id = t.get("id", "—")
        lines.append(f"| {status} | {task_id} | {title} |")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Cross-project kanban view")
    parser.add_argument(
        "--queue",
        default="tasks/queue.json",
        help="Path to queue.json (default: tasks/queue.json)",
    )
    args = parser.parse_args()

    queue_path = _safe_path(args.queue, "--queue")

    if not queue_path.exists():
        print(f"ERROR: queue file not found: {queue_path}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(queue_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"ERROR: could not read queue.json: {exc}", file=sys.stderr)
        sys.exit(1)

    tasks = data.get("tasks", [])
    active = [t for t in tasks if t.get("status") in _ACTIVE_STATUSES]

    if not active:
        print("No active tasks")
        return

    # Group by project, preserving first-seen order from queue.json
    by_project: dict[str, list[dict]] = {}
    for task in active:
        project = task.get("project") or "unknown"
        by_project.setdefault(project, []).append(task)

    print("## Cross-Project Kanban\n")
    sections = [_build_project_section(p, t) for p, t in by_project.items()]
    print("\n\n".join(sections))


if __name__ == "__main__":
    main()
