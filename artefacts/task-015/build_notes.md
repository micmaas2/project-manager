# Build Notes — task-015

## Summary
Implemented `scripts/pm-priority.py` — a stdlib-only script that ranks active tasks by:
1. Paused tasks first
2. project_manager tasks before other projects
3. P1 > P2 > P3 (priority looked up from backlog.md via BL-NNN extracted from title)
4. Oldest created date within the same tier

Updated `.claude/commands/pm-status.md` to invoke `pm-priority.py` as step 1.

## Design Decisions

**Priority lookup via backlog.md cross-reference**: queue.json has no `priority` field. The script extracts BL-NNN from the task title via regex and looks it up in backlog.md. This is the only place priority is authoritatively recorded.

**Title fix**: task-015/016/017 titles only contained S-NNN story IDs, not BL-NNN. Updated queue.json titles to include BL-NNN so pm-priority.py can look them up (e.g. `(BL-004, S-003-1)` instead of just `(S-003-1)`).

**No schema change required**: kept the existing queue.json schema — priority lives in backlog.md as the single source of truth.

## Files Changed
- `scripts/pm-priority.py` — new script
- `.claude/commands/pm-status.md` — added step 1 (priority ranking call)
- `tasks/queue.json` — task-015/016/017 titles updated to include BL-NNN, task-015 status → in_progress

## Test Results
14/14 unit tests passing via `python3 -m pytest artefacts/task-015/test_pm_priority.py -v`
