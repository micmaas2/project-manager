## Review: task-056 — db.py schema validator hook

**Verdict: APPROVED** (with advisory notes; no findings ≥ 80 require a Builder loop)

Reviewer: [Sonnet]
Date: 2026-05-02

---

## Acceptance Criteria Status

| # | Criterion | Status | Notes |
|---|-----------|--------|-------|
| AC-1 | `hooks/pre-commit` appended; symlink in place | PASS | Block at lines 37–69; `.git/hooks/pre-commit → ../../hooks/pre-commit` symlink confirmed |
| AC-2 | When db.py staged: runs syntax check AND init_db() dry-run; exits non-zero on either failure | PASS | `py_compile.compile(doraise=True)` + `mod_globals["init_db"]()` both present; failures exit 1 |
| AC-3 | When db.py not staged: exits 0 silently | PASS | `STAGED_DB` empty → `if [ -n "$STAGED_DB" ]` block skipped; falls through to `exit 0` |
| AC-4 | Dry-run isolation: DB_PATH patched to `:memory:` | PASS | `config_mod.DB_PATH = ":memory:"` injected into `sys.modules["config"]` before exec |

End-to-end verification: `python3 hooks/validate_db.py genealogy-mas/db.py` outputs `db.py: syntax OK` and `db.py: init_db() dry-run OK (:memory:)` — confirmed working.

---

## Findings

### F-1 — Temp file leak when `git show` fails under `set -euo pipefail`
**Confidence: 72** (below 80 — no Builder loop required; route to build_notes.md)

In the shell block:
```bash
tmp=$(mktemp /tmp/db_staged_XXXXXX.py)
git show ":$db_file" > "$tmp"
if ! python3 "$VALIDATOR" "$tmp"; then
    rm -f "$tmp"
    exit 1
fi
rm -f "$tmp"
```

Under `set -euo pipefail`, if `git show ":$db_file"` fails (e.g. index corruption, git error), the shell exits immediately at that line — `rm -f "$tmp"` is never reached. The temp file remains in `/tmp/` until the next reboot.

This is a low-severity issue: `/tmp/` files do not accumulate across reboots, the temp file contains only staged Python source (no secrets), and the `git show` failure scenario is rare for a well-functioning repo. A `trap 'rm -f "$tmp"' EXIT` added before the mktemp call would fix this cleanly, but the risk is minor enough that it does not block approval.

**Fix if desired:**
```bash
tmp=$(mktemp /tmp/db_staged_XXXXXX.py)
trap 'rm -f "$tmp"' EXIT
git show ":$db_file" > "$tmp"
...
```

---

### F-2 — `@classmethod __call__` on mock enum subclasses is dead code
**Confidence: 90** (≥ 80 — but this is a code quality / clarity finding; no behavioral defect)

The three mock classes (`SuggestionStatus`, `SuggestionType`, `AkteStatus`) each define:
```python
@classmethod
def __call__(cls, value):
    return cls(value)
```

Python's type machinery invokes `type.__call__` (the metaclass) when you write `SuggestionStatus("pending")` — it calls `cls.__new__` and `cls.__init__`, not `cls.__call__` on the class object itself. The `@classmethod __call__` would only be invoked via `SuggestionStatus.__call__("pending")` (explicit method call) or `instance(args)` (calling an instance as a callable), neither of which occurs in db.py.

**Verified:** calling `SuggestionStatus("pending")` dispatches through `_Enum.__init__` and returns a correct `SuggestionStatus` instance with `.value = "pending"`. The mock enum factory works correctly — the classmethod is simply never called.

**Behavioral impact: none.** The mock passes the dry-run correctly. However, the `@classmethod __call__` adds misleading noise and may confuse future maintainers into thinking it is the mechanism making construction work. The noqa annotation `# noqa: N805` (wrong-self-type for classmethods) also appears to be applied to a method that is not actually needed.

**Recommended fix:** remove the three `@classmethod __call__` methods. The subclass constructors work via `_Enum.__init__` inheritance alone.

---

### F-3 — Mock brittleness from hardcoded class names (acceptable tradeoff)
**Confidence: 55** (below 80 — advisory only)

The mock hardcodes all enum values (`PENDING`, `APPROVED`, `REJECTED`, etc.) and all config attributes (`DB_PATH`, `SYNC_VERSION`, `RESEARCH_COOLDOWN_DAYS`) from db.py's current dependencies. If db.py adds a new import from `config` or `models.*`, the validator will fail with an `AttributeError` or `ImportError` — not a syntax error — and the error message will be:

```
db.py: import/exec error: module 'config' has no attribute 'NEW_FIELD'
```

This is an acceptable tradeoff: the validator is a pre-commit hook, not a unit test suite. When the mock needs updating, the failure is immediate, explicit, and easy to diagnose. The alternative (fully dynamic mock using `unittest.mock.MagicMock`) would silently pass even when db.py introduces genuine schema regressions, which is the opposite of the goal.

**Assessment:** current design is correct for this use case. No change required.

---

### F-4 — Shell block ordering: early-exit affects only the ruff stage, not the db.py block
**Confidence: 95** (informational verification — confirms correct design, no defect)

The concern raised in the review prompt: "if STAGED_PY is empty, the hook exits 0 at line 10 — but db.py IS a .py file."

This is correct: if db.py is staged, it matches `grep '\.py$'`, so `STAGED_PY` is non-empty. The early exit at line 10 only fires when no `.py` files are staged at all. If db.py is staged, ruff runs first (correct: catches style issues before the heavier dry-run), then the db.py block runs. The ordering is intentional and correct.

**No action required.**

---

### F-5 — CLAUDE.md compliance: all mandatory shell-script rules verified
**Confidence: 95** (all pass)

| Rule | Status |
|------|--------|
| No `--` before `:$db_file` index refspec | PASS — `git show ":$db_file" > "$tmp"` (no `--`) |
| Reads staged index version (not working-tree file) | PASS — `git show ":$db_file"` used |
| Binary check after early-exit guard | PASS — `python3` check at line 45, after `if [ -n "$STAGED_DB" ]` at line 43 |
| No bare `$?` capture after a command under `set -e` | PASS — `if ! python3 ...` pattern used throughout |
| `python3 -m py_compile` / `py_compile.compile` used (not `bash -n`) | PASS — Python script uses `py_compile.compile(doraise=True)` |
| Stdlib only (no external deps) | PASS — `sys`, `py_compile`, `types`, `sqlite3` only |
| `exec()` use annotated with `# noqa: S102` | PASS — line 147 |

---

## Summary

The implementation is functionally correct and well-structured. The dry-run correctly isolates against `:memory:`, module-level imports are properly mocked, and the hook ordering is sound. The only finding requiring attention is F-2 (dead `@classmethod __call__` — confidence 90), which is a code clarity issue with no behavioral impact. F-1 (temp file leak) is below the 80-threshold and acceptable given the low severity. F-3 (mock brittleness) is an acknowledged tradeoff, not a defect.

**Builder loop**: not required. F-2 may be addressed as a cleanup in the same task if the Builder chooses to, or deferred to a backlog item. All acceptance criteria pass.
