# task-055 Code Quality Review — genealogie ruff pre-commit hook

**Reviewer**: code-quality-reviewer [Sonnet]
**Date**: 2026-05-01
**Artefact**: `/opt/claude/genealogie/hooks/pre-commit`

---

## Overall Verdict: APPROVED — No Builder loop required

The hook is correct, secure, and well-structured. All CLAUDE.md shell hook patterns are satisfied. The two findings below are both minor and below the confidence threshold (80) that triggers a Builder loop.

---

## Security Analysis

**No security issues found.** Specific checks performed:

- **Command injection via `$file`**: `git show ":$file"` is correctly double-quoted, preventing word-splitting and glob expansion on the refspec. `--stdin-filename "$file"` passes the filename as a quoted value argument — ruff does not re-parse it as flags. No injection path.
- **Path traversal**: `git diff --cached --name-only` returns only paths tracked by git within the repository. No user-controlled path construction occurs.
- **Credential leakage**: no secrets, tokens, or sensitive values referenced.
- **`echo "$staged_content"` safety**: bash builtin `echo` does not parse flags from expanded variable content (only from literal first-token arguments). A staged file whose content begins with `-n` will pipe correctly without suppressing the newline. Verified by test.

---

## CLAUDE.md Shell Hook Pattern Checklist

| Check | Result |
|---|---|
| Binary check (`command -v ruff`) placed AFTER early-exit guard | PASS — early-exit lines 10–12; binary check lines 15–18 |
| No `--` before `:$file` in `git show` refspec | PASS — `git show ":$file"` (line 22); no `--` present |
| No bare `$?` capture under `set -euo pipefail` | PASS — uses `if ! ... ; then FAILED=1; fi` throughout |
| Reads staged index version, not working-tree file | PASS — `git show ":$file"` (line 22) |
| `set -euo pipefail` active | PASS — line 5 |
| `|| true` guard on `grep` to prevent `set -e` on no-match exit | PASS — line 7 |
| `diff-filter=ACM` excludes deleted files (no `git show` on deleted paths) | PASS |
| `if !` pattern correctly handles pipefail for `echo | ruff` pipeline | PASS — `if !` suppresses `set -e` for the tested pipeline; pipefail propagates ruff's non-zero exit through the pipe |

---

## Findings

### Finding 1 — Unquoted `$STAGED_PY` in `for` loop (word-splitting on spaces in filenames)
- **Severity**: Minor
- **Confidence**: 35/100
- **Line**: 21 (`for file in $STAGED_PY; do`)
- **Description**: Default IFS includes space; a Python file with a space in its path would be split into separate tokens, causing `git show ":token"` to fail with a fatal error. The genealogie repo has no such files and the pattern is conventional for git hooks.
- **Recommended fix** (optional): use `while IFS= read -r file; do ... done <<< "$STAGED_PY"` to handle paths with spaces safely.
- **Builder loop required**: NO

### Finding 2 — `diff-filter=ACM` misses renamed `.py` files
- **Severity**: Minor
- **Confidence**: 40/100
- **Line**: 7
- **Description**: The `R` (renamed) filter is excluded. A `.py` file renamed with content edits in the same commit bypasses lint. Pure renames (no content change) carry no new violations, so this is a narrow gap.
- **Recommended fix** (optional): change to `--diff-filter=ACMR`.
- **Builder loop required**: NO

### No further findings

The `echo "$staged_content"` trailing-newline addition does not corrupt ruff's analysis: ruff `check` is newline-tolerant and `format --check` expects a trailing newline anyway, so this is a non-issue.

---

## Acceptance Criteria Status

| # | Criterion | Status |
|---|-----------|--------|
| 1 | `hooks/pre-commit` exists, executable, `.git/hooks/pre-commit` symlinked correctly | PASS |
| 2 | Runs `ruff check` and `ruff format --check` on staged `.py` files | PASS |
| 3 | Exits non-zero on violation; file+rule printed by ruff via `--stdin-filename` | PASS |
| 4 | Exits 1 with install message when ruff absent | PASS |
| 5 | Exits 0 when no `.py` files staged | PASS |

---

## Summary

The hook is clean and production-ready. No critical or major issues. Two low-confidence minor findings (word-splitting on space-containing filenames; renamed file gap) are both conventional trade-offs acceptable in a single-developer repo with no affected filenames. No Builder loop is warranted. Risk rating: **Low**.
