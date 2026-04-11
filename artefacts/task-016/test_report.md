# Test Report — task-016 token_cap_enforcer.py

**Date**: 2026-04-11  
**Status**: PASS  
**Suite**: artefacts/task-016/test_token_cap_enforcer.py  
**Runner**: python3 -m pytest -v  

## Results

| Test | Result |
|------|--------|
| test_below_threshold_exits_0 | PASS |
| test_above_threshold_exits_1 | PASS |
| test_exactly_at_threshold_exits_0 | PASS |
| test_one_above_threshold_exits_1 | PASS |
| test_no_estimate_exits_0 | PASS |
| test_task_not_found_exits_1 | PASS |
| test_queue_file_missing_exits_1 | PASS |
| test_invalid_json_exits_1 | PASS |
| test_multiple_tasks_correct_one_selected | PASS |

**9 passed, 0 failed** in 0.44s

## Coverage

- Below threshold (5000) → exit 0, OK message ✓
- Above threshold (450000) → exit 1, ALERT message ✓
- Exactly at threshold (400000) → exit 0 (strict `>` boundary) ✓
- One above threshold (400001) → exit 1 ✓
- No token_estimate field → exit 0, none message ✓
- Task ID not in queue → exit 1, stderr error ✓
- Queue file missing → exit 1, stderr error ✓
- Invalid JSON in queue → exit 1, stderr "could not parse" ✓
- Multiple tasks in queue, correct one selected ✓

## Notes

Fixture files are written to `artefacts/task-016/_fixtures/` (inside workspace root)
because `_safe_path()` in the script validates that `--queue` is within the workspace.
Tests using `/tmp` via pytest `tmp_path` would be rejected by this security check.
