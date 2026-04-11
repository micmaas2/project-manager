#!/usr/bin/env python3
"""
token_cap_enforcer.py — Preflight token cap check for ProjectManager.

Reads a task's token_estimate from tasks/queue.json by task_id and exits
with a structured error if it exceeds 400,000 (80% of the 500k project cap).

Usage:
    python3 scripts/token_cap_enforcer.py --task-id task-016
    python3 scripts/token_cap_enforcer.py --task-id task-016 --queue path/to/queue.json

Exit codes:
    0  — token_estimate is within cap (or task has no estimate)
    1  — token_estimate exceeds 80% cap, or usage/file error
"""

import argparse
import json
import sys
from pathlib import Path

_CAP_THRESHOLD = 400_000  # 80% of 500k project cap

# Workspace root — --queue path must be inside this directory
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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Token cap preflight check — exits 1 if task exceeds 80% of 500k cap."
    )
    parser.add_argument(
        "--task-id",
        required=True,
        help="Task ID to check (e.g. task-016)",
    )
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
        print(f"ERROR: could not parse queue.json: {exc}", file=sys.stderr)
        sys.exit(1)

    tasks = data.get("tasks", [])
    task = next((t for t in tasks if t.get("id") == args.task_id), None)

    if task is None:
        print(f"ERROR: task '{args.task_id}' not found in queue.json", file=sys.stderr)
        sys.exit(1)

    estimate = task.get("token_estimate")

    if estimate is None:
        # No estimate recorded — pass through without blocking
        print(f"OK: {args.task_id} token_estimate=none (no estimate recorded)")
        sys.exit(0)

    if not isinstance(estimate, (int, float)):
        print(
            f"ERROR: token_estimate for '{args.task_id}' is not a number: {estimate!r}",
            file=sys.stderr,
        )
        sys.exit(1)

    if estimate > _CAP_THRESHOLD:
        print(
            f"ALERT: Task {args.task_id} estimated tokens ({int(estimate)}) exceed "
            f"80% of project cap (400k). Reduce scope or split task before proceeding."
        )
        sys.exit(1)

    print(f"OK: {args.task_id} token_estimate={int(estimate)}")
    sys.exit(0)


if __name__ == "__main__":
    main()
