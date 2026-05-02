# Test Report — task-056: SQLite Schema Validator Pre-Commit Hook

**Agent**: Tester (BugHunter) [Haiku]
**Date**: 2026-05-02
**Files under test**:
- `/opt/claude/genealogie/hooks/pre-commit` (db.py validation block, lines 37–69)
- `/opt/claude/genealogie/hooks/validate_db.py`

---

## Overall Verdict: PASS

All 4 required test cases and the SystemExit regression test passed with the expected exit codes.

---

## Results Table

| # | Test Case | Expected Exit | Actual Exit | Status |
|---|-----------|:---:|:---:|:---:|
| a | staged db.py with valid schema | 0 | 0 | PASS |
| b | staged db.py with syntax error | 1 | 1 | PASS |
| c | staged db.py with broken SQL in CREATE TABLE | 1 | 1 | PASS |
| d | db.py not staged (only README.md staged) | 0 | 0 | PASS |
| e | SystemExit regression (module-level sys.exit(1)) | 1 | 1 | PASS |

**Total**: 5/5 passed

---

## Captured Output Per Test

### Test (a) — Valid schema → exits 0
```
db.py: syntax OK
db.py: init_db() dry-run OK (:memory:)
Test (a) exit: 0
```

### Test (b) — Syntax error → exits 1
```
db.py: syntax error:   File "/tmp/test_db_syntax.py", line 4
    def init_db(
               ^
SyntaxError: '(' was never closed
Test (b) exit: 1
```

### Test (c) — Broken SQL in CREATE TABLE → exits 1
```
db.py: syntax OK
db.py: init_db() dry-run failed: near "TABL": syntax error
Test (c) exit: 1
```

### Test (d) — db.py not staged → exits 0
```
(no output — hook exits 0 at early-exit guard: no .py files staged)
Test (d) exit: 0
```

### Test (e) — SystemExit regression (CQR F-1 fix) → exits 1
```
db.py: syntax OK
db.py: import/exec error: sys.exit(1) at module level
Test (SystemExit) exit: 1
```

---

## Test Method

Tests (a), (b), (c), (e) call `validate_db.py` directly with temporary files written to `/tmp/`.
The validator reads from disk via `open(staged_path)` — this matches how the hook uses it
(the shell hook pipes `git show ":$db_file"` to a temp file before calling the validator).

Test (d) sets up a minimal git repo in `/tmp/test_no_db/`, symlinks the pre-commit hook,
stages a non-Python file (`README.md`), and runs the hook directly. The hook exits 0
at the early-exit guard (`[ -z "$STAGED_PY" ]`) before reaching the db.py validator.

---

## Notes

- CQR F-1 (SystemExit handling): confirmed working — `sys.exit(1)` at module level is caught
  as `SystemExit`, reported to stderr, and results in exit code 1 (not silent pass).
- The `db.py: syntax OK` line prints before the dry-run error in tests (b) and (c) because
  the syntax check (`py_compile`) passes for test (c) and `print()` in (b) is unreachable
  at compile time — the stderr ordering reflects actual execution flow.
- No ruff dependency issue encountered for test (d) — the hook exits before the ruff check
  because no `.py` files were staged.
