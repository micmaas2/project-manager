"""
token-dashboard.py — Token spend dashboard for /pm-status.

Reads logs/token_log.jsonl and tasks/queue.json, then prints a markdown
table of cumulative token spend per (task_id, agent) with WARN flags on
rows exceeding 80% of the task's token_estimate cap.

Usage:
    python3 scripts/token-dashboard.py [--workspace-root <path>] [--last-n <int>]

Exit codes: always 0 (dashboard — non-fatal).
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Workspace root + path guard
# ---------------------------------------------------------------------------
_WORKSPACE_ROOT = Path(__file__).resolve().parent.parent  # scripts/../


def _safe_path(p: Path) -> Path:
    """Resolve path and assert it stays within _WORKSPACE_ROOT."""
    resolved = p.resolve()
    if _WORKSPACE_ROOT not in resolved.parents and resolved != _WORKSPACE_ROOT:
        print(f"ERROR: Path '{p}' resolves outside workspace root '{_WORKSPACE_ROOT}'", file=sys.stderr)
        sys.exit(1)
    return resolved


# ---------------------------------------------------------------------------
# Argument parsing (stdlib only)
# ---------------------------------------------------------------------------
def _parse_args(argv: list[str]) -> tuple[Path, int | None]:
    """Return (workspace_root, last_n)."""
    global _WORKSPACE_ROOT
    last_n: int | None = None
    i = 1
    while i < len(argv):
        if argv[i] == "--workspace-root" and i + 1 < len(argv):
            _WORKSPACE_ROOT = Path(argv[i + 1]).resolve()
            i += 2
        elif argv[i] == "--last-n" and i + 1 < len(argv):
            try:
                last_n = int(argv[i + 1])
            except ValueError:
                print(f"ERROR: --last-n must be an integer, got '{argv[i+1]}'", file=sys.stderr)
                sys.exit(1)
            i += 2
        else:
            print(f"ERROR: Unknown argument '{argv[i]}'", file=sys.stderr)
            sys.exit(1)
    return _WORKSPACE_ROOT, last_n


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def _load_token_log(log_path: Path, last_n: int | None) -> list[dict]:
    """Read token_log.jsonl; skip missing file or malformed lines."""
    if not log_path.exists():
        return []
    lines: list[str] = log_path.read_text().splitlines()
    if last_n is not None:
        lines = lines[-last_n:]
    entries = []
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            print(f"  [token-dashboard] WARNING: skipping malformed line {i} in token_log.jsonl", file=sys.stderr)
    return entries


def _load_task_caps(queue_path: Path) -> dict[str, int]:
    """Return {task_id: token_estimate} from queue.json."""
    if not queue_path.exists():
        return {}
    try:
        data = json.loads(queue_path.read_text())
        return {t["id"]: t.get("token_estimate", 0) for t in data.get("tasks", [])}
    except (json.JSONDecodeError, KeyError):
        return {}


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------
def _aggregate(entries: list[dict]) -> dict[tuple[str, str], int]:
    """Sum token_estimate grouped by (task_id, agent)."""
    totals: dict[tuple[str, str], int] = defaultdict(int)
    for entry in entries:
        task_id = entry.get("task_id") or ""
        agent = entry.get("agent") or "unknown"
        tokens = entry.get("token_estimate") or 0
        if task_id:
            totals[(task_id, agent)] += tokens
    return dict(totals)


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------
_WARN_THRESHOLD = 0.80
_WARN_MARK = "⚠ WARN"


def _render_table(totals: dict[tuple[str, str], int], caps: dict[str, int]) -> str:
    if not totals:
        return "(no token log entries)\n"

    col_task = max(len("task_id"), max(len(k[0]) for k in totals))
    col_agent = max(len("agent"), max(len(k[1]) for k in totals))

    header = (
        f"| {'task_id':<{col_task}} | {'agent':<{col_agent}} "
        f"| {'tokens_used':>11} | {'token_estimate':>14} | {'%':>6} | flag     |"
    )
    sep = (
        f"|-{'-'*col_task}-|-{'-'*col_agent}"
        f"-|------------:|---------------:|-------:|----------|"
    )

    rows = []
    grand_total = 0
    task_ids_seen: set[str] = set()

    for (task_id, agent) in sorted(totals):
        used = totals[(task_id, agent)]
        cap = caps.get(task_id, 0)
        grand_total += used
        task_ids_seen.add(task_id)

        if cap and cap > 0:
            pct = used / cap * 100
            pct_str = f"{pct:.0f}%"
            flag = _WARN_MARK if pct > _WARN_THRESHOLD * 100 else ""
        else:
            pct_str = "—"
            flag = ""

        rows.append(
            f"| {task_id:<{col_task}} | {agent:<{col_agent}} "
            f"| {used:>11,} | {cap:>14,} | {pct_str:>6} | {flag:<8} |"
        )

    lines = [header, sep] + rows
    lines.append("")
    lines.append(f"Grand total: {grand_total:,} tokens across {len(task_ids_seen)} task(s)")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> None:
    workspace_root, last_n = _parse_args(argv if argv is not None else sys.argv)

    log_path = _safe_path(workspace_root / "logs" / "token_log.jsonl")
    queue_path = _safe_path(workspace_root / "tasks" / "queue.json")

    entries = _load_token_log(log_path, last_n)
    caps = _load_task_caps(queue_path)
    totals = _aggregate(entries)

    print(_render_table(totals, caps), end="")


if __name__ == "__main__":
    main()
