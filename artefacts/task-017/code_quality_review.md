# Code Quality Review: cross-kanban.py (task-017)

**Script**: `/opt/claude/project_manager/scripts/cross-kanban.py`  
**Review Date**: 2026-04-13  
**Python Version**: 3.10+ (tested on 3.13)

---

## Security Findings

### 1. Path Traversal Prevention ✓ PASS
**Status**: HIGH confidence pass

The `_safe_path()` function correctly prevents path traversal attacks:
- Uses `Path.resolve()` to normalize and eliminate `..` components
- Validates that the resolved path is either the workspace root itself OR a descendant (via `in resolved.parents` check)
- Returns immediate `sys.exit(1)` with error to stderr on validation failure
- Tested edge cases:
  - `../../../etc/passwd` → Rejected ✓
  - `/opt/claude/tasks/queue.json` (outside root) → Rejected ✓
  - `tasks/queue.json` (inside, relative) → Accepted ✓
  - `/opt/claude/project_manager/tasks/queue.json` (inside, absolute) → Accepted ✓

**No HIGH-risk path traversal vulnerability found.**

### 2. No Outbound HTTP ✓ PASS
**Status**: CONFIRMED

- No `urllib`, `http`, `requests`, or `aiohttp` imports
- No socket operations
- Script only reads local files via `Path.read_text()`
- No external API calls

**Confirmed: Script is offline-only.**

### 3. JSON Decode Error Handling ✓ PASS
**Status**: IMPLEMENTED

Line 87-90: Proper exception handling for both `json.JSONDecodeError` and `UnicodeDecodeError`:
```python
try:
    data = json.loads(queue_path.read_text(encoding="utf-8"))
except (json.JSONDecodeError, UnicodeDecodeError) as exc:
    print(f"ERROR: could not read queue.json: {exc}", file=sys.stderr)
    sys.exit(1)
```

Tested with:
- Malformed JSON: `{invalid json}` → Error message to stderr ✓
- Bad UTF-8 bytes: `b'\x80\x81\x82'` → Error to stderr ✓
- Both return exit code 1 ✓

**No missing error handling.**

### 4. UnicodeDecodeError Handling ✓ PASS
**Status**: IMPLEMENTED

Covered in the same try/except block as JSON errors (line 88). Both exceptions are caught and reported.

**Confirmed: UTF-8 decode errors are handled.**

### 5. re.DOTALL with $ Anchor ✓ PASS
**Status**: NOT APPLICABLE

- No `import re` statement
- No regex usage in the script
- String manipulation uses only `.replace("|", "\\|")` for markdown escaping

**No regex module present — no risk.**

### 6. Shell Injection Risk ✓ PASS
**Status**: SAFE

- No `subprocess` module imported
- No `os.system()` calls
- No shell-like string execution
- Argument parsing via `argparse` (safe)

**Confirmed: No shell injection vectors.**

---

## Quality Findings

### 1. Type Annotations ⚠ MEDIUM - Incomplete

**Status**: Valid but imprecise for Python 3.10+

Line 47 defines `_status_rank()` with return type `tuple` (bare):
```python
def _status_rank(task: dict) -> tuple:
    ...
    return (rank, task.get("created", "9999-99-99"))  # Returns (int, str)
```

**Issue**: In Python 3.10+, PEP 585 allows `tuple[int, str]` for specificity.  
**Current behavior**: The code works fine with bare `tuple`, but loses type checking precision.  
**Recommendation**: Use `tuple[int, str]` for clarity and IDE support.

**All other annotations are correct**:
- `_safe_path(raw: str, label: str) -> Path` ✓
- `_build_project_section(project: str, tasks: list[dict]) -> str` ✓
- `main() -> None` ✓
- `dict[str, list[dict]]` on line 100 ✓

**Severity**: MEDIUM — No functional issue, style/clarity only.

### 2. Error Messages to stderr ✓ PASS

All error messages correctly use `file=sys.stderr`:
- Line 40: `_safe_path()` errors → stderr ✓
- Line 83: Missing file error → stderr ✓
- Line 89: JSON/Unicode decode errors → stderr ✓

Success messages go to stdout:
- Line 96: `"No active tasks"` → stdout ✓
- Line 105-107: Kanban output → stdout ✓

**Confirmed: stderr/stdout separation is correct.**

### 3. Docstring Accuracy ✓ PASS

Docstring (lines 2-18) claims script:
- ✓ Reads tasks/queue.json
- ✓ Outputs markdown kanban grouped by project
- ✓ Sorted by status within each project
- ✓ Shows only active tasks: paused, in_progress, review, test, pending
- ✓ Omits projects with no active tasks
- ✓ Prints 'No active tasks' when queue is empty or all done/failed
- ✓ Accepts `--queue PATH` argument with default `tasks/queue.json`

**All docstring claims verified against code.**

### 4. Dead Code or No-op Operations ✓ PASS

All code serves a purpose:
- `_ACTIVE_STATUSES` (line 26): Used on line 93 to filter tasks
- `_STATUS_ORDER` (line 29): Used on line 50 for sorting
- `_WORKSPACE_ROOT` (line 32): Used on line 38 for path validation
- All functions called: `_safe_path` (line 80), `_status_rank` (line 56), `_build_project_section` (line 106)

**No dead code found.**

### 5. Module Constants Naming ✓ PASS

All constants follow Python convention with `_LEADING_UNDERSCORE` for private module-level constants:
- `_ACTIVE_STATUSES` — clear name, descriptive ✓
- `_STATUS_ORDER` — clear name, includes comment ✓
- `_WORKSPACE_ROOT` — clear name, includes comment ✓

**Naming is excellent.**

### 6. Edge Cases ⚠ LOW - Minor edge case exists

The script handles most edge cases well, but one minor case exists:

**Edge case: Task with `project: None`**
```python
task = {"id": "t3", "project": None, "status": "paused"}
project = task.get("project", "unknown")  # Returns None, not "unknown"
```

When a task explicitly has `project: None`, it gets rendered as `### None` in the markdown instead of `### unknown`.

**Fix** (optional): Line 102 should be:
```python
project = task.get("project", "unknown") or "unknown"
```

This would handle both missing and null values consistently.

**Severity**: LOW — Unlikely in practice (queue.json schema likely prevents this), but possible with malformed data.

**Note**: All test cases pass (8/8), indicating tests don't cover this edge case but tests use well-formed data.

---

## Test Coverage

All 8 unit tests pass:
- ✓ test_three_project_sections_present
- ✓ test_done_project_omitted
- ✓ test_tasks_in_correct_project_section
- ✓ test_status_sort_order_within_project
- ✓ test_empty_queue_prints_no_active_tasks
- ✓ test_all_done_queue_prints_no_active_tasks
- ✓ test_header_present
- ✓ test_pipe_chars_escaped_in_title

Tests are comprehensive but don't cover the `project: None` edge case.

---

## Summary

### Security Assessment: APPROVED
✓ No path traversal vulnerabilities  
✓ No HTTP/network access  
✓ Proper error handling for JSON and encoding issues  
✓ No regex risks  
✓ No shell injection risks  

### Quality Assessment: APPROVED with minor notes
✓ Error/stdout separation correct  
✓ Docstring accurate and complete  
✓ No dead code  
✓ Constants well-named  
✓ Edge cases mostly handled  

### Issues Found
1. **MEDIUM**: Type annotation for `_status_rank()` could be more specific (`tuple[int, str]` instead of bare `tuple`)
2. **LOW**: Task with `project: None` renders as `### None` instead of `### unknown` (minor, unlikely in practice)

### Recommendations
1. Update line 47 type annotation: `-> tuple[int, str]` for clarity
2. Optional: Add null-coalescing on line 102 to handle `project: None` consistently
3. Optional: Add test case for task with `project: None`

---

## FINAL VERDICT: **APPROVED**

The script is secure, functional, and production-ready. The identified issues are minor quality improvements, not blockers. All security checks pass. All tests pass.

**Approved for production use.**

