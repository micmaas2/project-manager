# Test Report — task-015

**Status: PASS**

## Run

```
python3 -m pytest artefacts/task-015/test_pm_priority.py -v
```

## Results

14/14 tests passed. 0 failed. 0 errors.

| Test | Result |
|---|---|
| TestLoadBacklogPriorities::test_missing_file_returns_empty | PASS |
| TestLoadBacklogPriorities::test_parses_known_priorities | PASS |
| TestExtractBlId::test_first_bl_in_multiple | PASS |
| TestExtractBlId::test_no_bl | PASS |
| TestExtractBlId::test_single_bl | PASS |
| TestExtractBlId::test_zero_padded | PASS |
| TestRanking::test_custom_status_filter | PASS |
| TestRanking::test_done_tasks_excluded_by_default | PASS |
| TestRanking::test_oldest_created_wins_within_same_tier | PASS |
| TestRanking::test_output_contains_header | PASS |
| TestRanking::test_paused_first | PASS |
| TestRanking::test_pm_before_other_projects | PASS |
| TestRanking::test_priority_column_shows_value | PASS |
| TestEmptyQueue::test_empty_queue_no_error | PASS |

## Notes

- 3 blocking issues from code-quality-reviewer were fixed before Tester ran:
  1. `json.JSONDecodeError` now caught with descriptive message
  2. `--status` tokens validated against known enum; unknown values exit 1 with error
  3. `--queue` and `--backlog` paths validated against `_WORKSPACE_ROOT` (no path traversal)
- Test fixture files updated to write inside `artefacts/task-015/` (workspace root) so the path-containment guard passes during tests.
- Live smoke-test output:

```
## Priority Ranking — 5 task(s)

| Rank | Task ID | Project | Priority | Status | Title |
|---|---|---|---|---|---|
| 1 | task-015 | project_manager | P2 | in_progress | project_manager: Multi-project priority ranking in PM (BL-004, S-003-1) |
| 2 | task-016 | project_manager | P2 | pending | project_manager: Python token-cap-enforcer script (BL-050, S-003-4) |
| 3 | task-017 | project_manager | P2 | pending | project_manager: Cross-project kanban view script (BL-064, S-003-3) |
| 4 | task-018 | pi-homelab | P1 | pending | mas_agent: Fix mas-frontend Docker healthcheck (BL-059) |
| 5 | task-019 | pi-homelab | P1 | pending | mas_agent: Telegram sender chat_id auth guard (BL-060) |
```
