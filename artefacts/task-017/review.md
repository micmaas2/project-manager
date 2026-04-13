# Task-017 Review — Cross-Project Kanban View Script

**Reviewer**: Claude Code (Haiku 4.5)
**Date**: 2026-04-13
**Branch**: feature/task-017-cross-kanban

## Acceptance Criteria Review

✓ **1. Script outputs markdown with one section per project, each containing a kanban table (status | task-id | title)**
  - Script produces `### {project}` headings for each project
  - Each project section contains a markdown table with columns: Status | Task ID | Title
  - All 8 tests pass, including `test_three_project_sections_present`

✓ **2. Projects with no active tasks are omitted from output**
  - Filtering logic correctly implements: `active = [t for t in tasks if t.get("status") in _ACTIVE_STATUSES]`
  - Active statuses limited to: paused, in_progress, review, test, pending
  - Test `test_done_project_omitted` confirms projects with only done/failed tasks are excluded

✓ **3. Output callable from /pm-status (one line added to pm-status.md)**
  - pm-status.md step 3 correctly updated on line 14
  - Command: `python3 scripts/cross-kanban.py` (cwd: project_manager root)
  - Integration point is clean and minimal

✓ **4. Script handles queue.json with 0 tasks gracefully (prints 'No active tasks')**
  - Empty queue outputs: `No active tasks`
  - All-done queue outputs: `No active tasks`
  - Tests `test_empty_queue_prints_no_active_tasks` and `test_all_done_queue_prints_no_active_tasks` both pass

## Review Checklist

✓ **_safe_path() workspace-root guard present**
  - Lines 31-44: `_WORKSPACE_ROOT = Path(__file__).resolve().parent.parent`
  - Guard checks: `if _WORKSPACE_ROOT not in (resolved, *resolved.parents)`
  - Proper sys.exit(1) on violation
  - Validated: workspace guard rejects /tmp paths outside project_manager/

✓ **read_text(encoding="utf-8") + UnicodeDecodeError catch present**
  - Line 87: `json.loads(queue_path.read_text(encoding="utf-8"))`
  - Line 88: `except (json.JSONDecodeError, UnicodeDecodeError) as exc:`
  - Both exception types handled correctly

✓ **Pipe chars in titles escaped**
  - Line 64: `title = t.get("title", "—").replace("|", "\\|")`
  - Test `test_pipe_chars_escaped_in_title` confirms: `r"title with \| pipe"` in output
  - Pipe escaping validated with edge-case testing

✓ **No external dependencies (stdlib only)**
  - Imports: argparse, json, sys, pathlib (all standard library)
  - No third-party dependencies
  - Python >= 3.10 requirement documented in docstring

✓ **Output matches (status | task-id | title) table format required**
  - Table header: `| Status | Task ID | Title |`
  - Separator row: `|---|---|---|`
  - Data rows format: `| {status} | {task_id} | {title} |`
  - Functional test confirms correct output structure

✓ **pm-status.md change is minimal and correct**
  - Single line (14) in step 3 added
  - Content: "Then run `python3 scripts/cross-kanban.py` (cwd: project_manager root) and print its output below the kanban."
  - Change is appropriately integrated into the workflow

✓ **Test suite passes (8/8)**
  - test_three_project_sections_present: PASSED
  - test_done_project_omitted: PASSED
  - test_tasks_in_correct_project_section: PASSED
  - test_status_sort_order_within_project: PASSED
  - test_empty_queue_prints_no_active_tasks: PASSED
  - test_all_done_queue_prints_no_active_tasks: PASSED
  - test_header_present: PASSED
  - test_pipe_chars_escaped_in_title: PASSED

## Summary

All acceptance criteria satisfied. Implementation is robust, security-aware (workspace root guard), handles edge cases (empty queue, unicode, pipe escaping), and passes all tests. The integration with pm-status.md is minimal and correct.

---

# APPROVED

No changes requested. Ready for merge to main.
