# Test Report — task-017: Cross-project kanban view script

**Date**: 2026-04-13
**Agent**: Tester
**Script**: scripts/cross-kanban.py

---

## Test Execution

```
python3 -m pytest artefacts/task-017/test_cross_kanban.py -v
```

### Results

| # | Test | Result |
|---|---|---|
| 1 | test_three_project_sections_present | PASS |
| 2 | test_done_project_omitted | PASS |
| 3 | test_tasks_in_correct_project_section | PASS |
| 4 | test_status_sort_order_within_project | PASS |
| 5 | test_empty_queue_prints_no_active_tasks | PASS |
| 6 | test_all_done_queue_prints_no_active_tasks | PASS |
| 7 | test_header_present | PASS |
| 8 | test_pipe_chars_escaped_in_title | PASS |

**Total**: 8/8 PASS

---

## Acceptance Criteria Verification

| Criterion | Test(s) | Result |
|---|---|---|
| One section per project with status\|task-id\|title table | test_three_project_sections_present, test_tasks_in_correct_project_section | PASS |
| Projects with no active tasks omitted | test_done_project_omitted | PASS |
| Output callable from /pm-status | pm-status.md updated (manual inspection) | PASS |
| 0 tasks → 'No active tasks' | test_empty_queue_prints_no_active_tasks, test_all_done_queue_prints_no_active_tasks | PASS |

---

## Live Run Verification

```
python3 scripts/cross-kanban.py
```

Output:
```
## Cross-Project Kanban

### project_manager

| Status | Task ID | Title |
|---|---|---|
| pending | task-017 | project_manager: Cross-project kanban view script (BL-064, S-003-3) |

### pi-homelab

| Status | Task ID | Title |
|---|---|---|
| pending | task-018 | mas_agent: Fix mas-frontend Docker healthcheck (BL-059) |
| pending | task-019 | mas_agent: Telegram sender chat_id auth guard (BL-060) |
```

---

## Verdict

**PASS** — All 8 unit tests pass, all 4 acceptance criteria satisfied, live run produces correct output.
