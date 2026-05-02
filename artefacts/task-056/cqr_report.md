# CQR Report: task-056 — genealogie SQLite schema validator hook

**Reviewer**: code-quality-reviewer [Sonnet]
**Date**: 2026-05-02
**Files reviewed**:
- `/opt/claude/genealogie/hooks/pre-commit` (lines 37–69, db.py block)
- `/opt/claude/genealogie/hooks/validate_db.py`

---

## Overall Verdict

**APPROVED — no Builder loop required.**

The implementation is sound. All CLAUDE.md shell hook rules are correctly followed. The `exec()` approach is justified and well-contained. One latent correctness risk is worth fixing (F-1); one issue in the existing Reviewer fix suggestion should be noted (F-2); the dead `@classmethod __call__` (already flagged as Reviewer F-2, confidence 90) is confirmed here as a cleanup item only.

---

## Findings

### F-1 — SystemExit from exec'd code bypasses the `except Exception` handler (Major)

**Location**: `validate_db.py`, lines 146–150

**Issue**: `SystemExit` inherits from `BaseException`, not `Exception`. If the module-level code of a staged `db.py` (or any module it imports at exec time) calls `sys.exit()`, the `SystemExit` propagates past the `except Exception as exc` clause and exits `validate_db.py` with that exit code.

Verified by test:
```
$ python3 -c "
try:
    exec('import sys; sys.exit(42)')
except Exception as e:
    print('caught:', e)    # never reached
except SystemExit as e:
    print('SystemExit:', e.code)   # prints 42
"
SystemExit: 42
```

The critical case: if exec'd code calls `sys.exit(0)`, `validate_db.py` exits 0 — the hook passes silently even though `init_db()` was never called. The `finally` block does run (sys.modules is restored), but the caller sees exit 0.

**Current db.py does not call `sys.exit()` at module level**, so this is a latent risk rather than an active defect. The risk surface is real: a future `db.py` that adds a module-level guard (`if __name__ != "db": sys.exit(1)`) would silently pass the hook.

**Fix**: catch `BaseException` (or a `SystemExit` specifically) and re-raise or convert to a controlled failure:

```python
try:
    exec(compile(src, staged_path, "exec"), mod_globals)  # noqa: S102
except SystemExit as exc:
    # Module-level sys.exit() in exec'd code — treat as exec failure unless exit code is 0
    if exc.code != 0:
        print(f"db.py: import/exec error: sys.exit({exc.code}) called at module level", file=sys.stderr)
        sys.exit(1)
    # exit(0) at module level is unusual but not an error; log and continue
    print("db.py: warning: module-level sys.exit(0) in exec'd code — init_db() skipped")
    sys.exit(0)
except Exception as exc:
    print(f"db.py: import/exec error: {exc}", file=sys.stderr)
    sys.exit(1)
```

Alternatively, wrap the entire exec block in `except BaseException`.

---

### F-2 — Reviewer F-1 fix suggestion has a scoping issue for multiple staged db.py files (Minor)

**Location**: `review.md` F-1 fix / `pre-commit` lines 58–66

**Issue**: The Reviewer's suggested fix for temp file cleanup places `trap 'rm -f "$tmp"' EXIT` inside the loop:

```bash
for db_file in $STAGED_DB; do
    tmp=$(mktemp /tmp/db_staged_XXXXXX.py)
    trap 'rm -f "$tmp"' EXIT   # $tmp is evaluated lazily at trap fire time
    ...
done
```

Bash traps evaluate variables at fire time, not at registration time. If two `db.py` files are staged (which `git diff --cached --name-only` can return if the tree has multiple `db.py` paths), the trap is registered twice and `$tmp` holds the value from the *last* iteration when the trap fires. The first iteration's temp file leaks if `git show` fails on that iteration and the shell exits via `set -e`.

In practice, the grep pattern `(^|/)db\.py$` matching multiple paths is an edge case for this codebase, and the risk is a minor `/tmp/` file leak. But the correct fix uses `trap` outside the loop with a list, or inline cleanup:

```bash
# Option A: trap outside loop (simplest, handles all iterations)
tmp=""
trap 'rm -f "$tmp"' EXIT
for db_file in $STAGED_DB; do
    tmp=$(mktemp /tmp/db_staged_XXXXXX.py)
    git show ":$db_file" > "$tmp"
    python3 "$VALIDATOR" "$tmp" || exit 1
    rm -f "$tmp"; tmp=""
done
```

Note: this is an advisory on the Reviewer's suggested fix, not a defect in the committed code (which currently has no trap). The currently committed code has the minor leak described in Reviewer F-1. Both issues are below the Builder-loop threshold given the low severity.

---

### F-3 — exec() globals lack explicit `__builtins__` restriction (Informational / Not a defect)

**Location**: `validate_db.py`, lines 142–147

When `exec()` is called with a dict that does not contain `__builtins__`, Python automatically injects the full `builtins` module. This means the exec'd code has unrestricted access to `open`, `__import__`, `os`, etc.

**This is not a defect for this use case.** The staged code comes from the repository itself (git index), not from user input. Restricting builtins would break legitimate db.py code that calls `sqlite3.connect()`, `json.dumps()`, etc. The threat model is "does this db.py have a valid schema?" not "is this code untrusted?"

The `# noqa: S102` annotation on line 147 correctly acknowledges the intentional exec usage. No change required.

---

## CLAUDE.md Shell Hook Compliance

All mandatory rules verified independently:

| Rule | Status | Evidence |
|------|--------|----------|
| No `--` before `:$db_file` index refspec | PASS | `git show ":$db_file" > "$tmp"` (line 60) — no `--` |
| Reads staged index, not working-tree | PASS | `git show ":$db_file"` pipes to temp file |
| Binary check after early-exit guard | PASS | `python3` check at line 45, inside `if [ -n "$STAGED_DB" ]` at line 43 |
| No bare `$?` capture under `set -e` | PASS | `if ! python3 ...` pattern used; no bare `$?` anywhere |
| Python scripts use `py_compile`, not `bash -n` | PASS | `py_compile.compile(doraise=True)` in validator; `bash -n` not used |
| Stdlib only — no external deps | PASS | `sys`, `py_compile`, `types`, `sqlite3` only |
| `exec()` annotated `# noqa: S102` | PASS | Line 147 |
| `set -euo pipefail` at top | PASS | Line 5 |

---

## Security Assessment

**No injection or traversal vulnerabilities found.**

- `staged_path` (sys.argv[1]) is constructed by `mktemp` inside the hook script — not derived from user input, git file content, or environment variables. The CLAUDE.md `_safe_path()` containment guard requirement applies to operator-supplied paths (e.g. `--queue`, `--config` flags); it does not apply here.
- All f-string SQL patterns in `db.py` interpolate only column names from hardcoded dict lookups (`_COL_MAP`, `_run_migrations` list). No user-controlled values reach the interpolation. Not a SQL injection surface.
- `sys.modules` restoration in `finally` is correct: `None` values are removed via `pop(name, None)`; existing modules are re-inserted. Cleanup runs even when `sys.exit()` is called inside the `try` block (finally runs before SystemExit propagates).

---

## Positive Observations

- **Correct architecture**: full exec-based dry-run preferred over static SQL extraction — validates the actual Python migration logic, not just SQL strings. Build notes correctly justify this choice.
- **Mock design**: mock modules are minimal but complete for `init_db()` surface. Brittle-by-design failure (AttributeError on unknown config field) is the correct tradeoff — it catches real regressions immediately rather than silently passing.
- **Early-exit ordering**: ruff block exits early if no `.py` files staged; `db.py` block runs only when `db.py` is among the staged files. Since `db.py` is a `.py` file, the early-exit at line 10 fires only when zero Python files are staged — not a false-negative path.
- **grep pattern correctness**: `(^|/)db\.py$` correctly matches `db.py`, `src/db.py`, and `genealogy-mas/db.py` while excluding `mydb.py` and `db.pyx`. Verified.

---

## Summary

The implementation is functionally correct and follows all applicable CLAUDE.md hook patterns. One genuine latent risk exists (F-1: `SystemExit` bypass) — it does not affect current `db.py` but could silently pass a future version that adds a module-level guard. The fix is a two-line `except SystemExit` clause. F-2 is an advisory on the Reviewer's proposed trap fix, not a bug in the committed code. F-3 is informational.

**Overall risk rating: Low.**

**Builder loop**: not required. F-1 is recommended as a cleanup in the current task or a follow-on; it does not block the task closing.
