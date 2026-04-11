# Review — task-015

## Status: APPROVED

All 5 acceptance criteria pass. 3 BLOCKING security issues from code-quality-reviewer were fixed before Tester ran. 14/14 tests pass.

---

## Acceptance Criteria

| AC | Evidence | Pass/Fail |
|---|---|---|
| AC1: pm-priority.py reads queue.json and outputs ranked markdown table (rank, task-id, project, priority, status, title) | `build_table()` constructs exactly those 6 columns. Live run produces correct output against real queue.json. | PASS |
| AC2: Paused tasks always appear first | `rank_key()` sets `is_paused=0` for status=="paused", 1 otherwise — first sort dimension. `test_paused_first` verifies. | PASS |
| AC3: project_manager tasks outrank same-priority tasks from other projects | `is_pm=0` for project=="project_manager" — second sort dimension. `test_pm_before_other_projects` verifies. | PASS |
| AC4: Within same project+priority, oldest created date wins | `created` string (ISO8601) is fourth sort key; lexicographic ordering equals chronological. `test_oldest_created_wins_within_same_tier` verifies. | PASS |
| AC5: /pm-status skill updated to invoke pm-priority.py | pm-status.md step 1 reads "Run `python3 scripts/pm-priority.py`" with fallback if absent. Steps renumbered 1–5. | PASS |

---

## Security Fixes Applied (from code-quality-reviewer)

| Issue | Severity | Fix |
|---|---|---|
| Path traversal on `--queue`/`--backlog` | BLOCKING | `_safe_path()` resolves path and asserts `_WORKSPACE_ROOT` in parents |
| `json.load` uncaught `JSONDecodeError` | BLOCKING | Wrapped in try/except; descriptive error + exit 1 |
| `--status` accepts unknown values silently | BLOCKING | Validated against `_KNOWN_STATUSES` enum; exit 1 on unknown token |

---

## Non-blocking Notes

1. Column index comment fixed: `cols[5] == Priority` (was wrong: `cols[4]`). Code was always correct; comment now matches.
2. `build_table` now escapes `|` in title cells.
3. Python >= 3.10 documented in module docstring.
4. Test fixture files write to `artefacts/task-015/` (inside workspace) to satisfy path-containment guard.

---

## Verdict

APPROVED. Ship as-is.
