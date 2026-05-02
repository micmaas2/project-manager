# task-055 Review — genealogie ruff pre-commit hook

**Reviewer**: Reviewer agent [Sonnet]
**Date**: 2026-05-01
**Artefact**: `/opt/claude/genealogie/hooks/pre-commit`

---

## Verdict: APPROVED

The hook is correct, safe, and satisfies all five acceptance criteria. One low-confidence style finding (word-splitting risk on filenames with spaces) is noted but does not block approval — genealogie has no Python files with spaces in their names, and the pattern is conventional for git hooks.

---

## Findings

### Finding 1 — Unquoted `$STAGED_PY` in `for` loop (word-splitting risk)
- **confidence: 35 (1–100)**
- **Lines**: 21 (`for file in $STAGED_PY; do`)
- **Description**: `$STAGED_PY` holds newline-delimited output from `git diff --name-only`. Iterating over it unquoted with default `IFS` (space+tab+newline) works correctly for filenames without spaces but would split any path containing a space into separate tokens, causing `git show ":token"` to fail.
- **Severity**: Low — genealogie has zero Python files with spaces in names; the conventional `for file in $VAR` idiom is widely used in git hooks and acceptable here.
- **Recommended fix** (optional hardening): replace the `for` loop with a `while read` loop to handle the unlikely space-in-path case:
  ```bash
  while IFS= read -r file; do
      staged_content=$(git show ":$file")
      if ! echo "$staged_content" | ruff check --stdin-filename "$file" -; then
          FAILED=1
      fi
      if ! echo "$staged_content" | ruff format --check --stdin-filename "$file" -; then
          FAILED=1
      fi
  done <<< "$STAGED_PY"
  ```
- **Builder loop required**: NO (confidence < 80)

### Finding 2 — `diff-filter=ACM` excludes renamed `.py` files
- **confidence: 40 (1–100)**
- **Lines**: 7
- **Description**: `--diff-filter=ACM` captures Added, Copied, Modified files. Renamed files (`R` filter) are excluded — a `.py` file renamed in a commit (with or without edits to its content) would not be linted.
- **Severity**: Low — renames without content changes carry no new violations; renames with content changes are a gap but uncommon in typical commit workflows.
- **Recommended fix** (optional): change to `--diff-filter=ACMR` to include renamed files. The staged content of renamed files is still accessible via `git show ":$file"` using the new path.
- **Builder loop required**: NO (confidence < 80)

### No other findings

The following CLAUDE.md checks all pass:

| Check | Result |
|---|---|
| Binary check AFTER early-exit guard | PASS — `command -v ruff` is on line 15; early-exit is lines 10–12 |
| No `--` before `:$file` refspec | PASS — `git show ":$file"` (line 22), no `--` present |
| No bare `$?` capture under `set -e` | PASS — uses `if ! ... ; then FAILED=1; fi` pattern throughout |
| Reads staged index via `git show ":$file"` | PASS — line 22 |
| `set -euo pipefail` in use | PASS — line 5 |
| `bash -n` syntax check | PASS |

---

## Acceptance Criteria Status

| # | Criterion | Status | Notes |
|---|-----------|--------|-------|
| 1 | `hooks/pre-commit` exists at `/opt/claude/genealogie/hooks/`, executable, `.git/hooks/pre-commit` symlinks to it | PASS | `-rwxr-xr-x`; symlink `-> ../../hooks/pre-commit` resolves correctly |
| 2 | Hook runs `ruff check` and `ruff format --check` on staged `.py` files | PASS | Lines 23 and 26; uses `--stdin-filename "$file"` for correct error attribution |
| 3 | Hook exits non-zero if any ruff violation; prints offending file + rule | PASS | ruff natively outputs `filename:line:col: RULEXX description` with `--stdin-filename`; `FAILED` flag propagates to `exit 1` on line 34 |
| 4 | Hook fails with "ruff not installed — run pip install ruff" if absent | PASS | Lines 15–18; `command -v ruff` guard with correct error message |
| 5 | Hook exits 0 when no `.py` files staged | PASS | Lines 10–12; early-exit before binary check |

---

## Summary

The implementation is clean and correct. All five acceptance criteria are satisfied. Both findings are low-confidence (35 and 40) and concern edge cases not present in this repository. No Builder loop is required. The hook is safe to ship as-is.
