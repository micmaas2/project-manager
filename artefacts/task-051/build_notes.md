# task-051 — Build Notes
**Agent**: Builder (Sonnet)
**Date**: 2026-04-30

## What was built

### 1. Hook script: `/opt/claude/CCAS/hooks/pre-commit`
A shared bash pre-commit hook that runs `ansible-lint` on staged `.yml` files across all 6 CCAS sub-repos. Key behaviours:
- Uses `readlink -f "${BASH_SOURCE[0]}"` to follow symlinks and locate the CCAS workspace root (`CCAS_ROOT`), enabling the hook to find `.ansible-lint` regardless of which sub-repo is committing.
- Checks for `ansible-lint` in PATH before anything else; exits 1 with a clear installation message if absent.
- Filters staged files with `git diff --cached --name-only --diff-filter=ACM | grep '\.yml$'`; exits 0 immediately when the list is empty (no lint overhead for non-YAML commits).
- Passes `--config "$CCAS_ROOT/.ansible-lint"` so the shared workspace config applies uniformly.
- Exits with ansible-lint's own exit code (non-zero on violations).

### 2. Symlinks installed
`/opt/claude/CCAS/<subrepo>/.git/hooks/pre-commit → /opt/claude/CCAS/hooks/pre-commit` for all 6 repos:
- ccas-core-infrastructure
- ccas-inventory
- ccas-jenkins
- ccas-main
- ccas-platform
- ccas-sap-applications

### 3. Test script: `artefacts/task-051/test_pre_commit.sh`
Covers 4 scenarios; 2 runnable without ansible-lint (c, d), 2 require it (a, b, documented as SKIP).

## Design decisions

- **Symlink-aware path resolution**: `${BASH_SOURCE[0]}` gives the symlink path (sub-repo `.git/hooks/pre-commit`); `readlink -f` gives the real file path in `CCAS/hooks/`. `dirname` twice yields `CCAS_ROOT` regardless of commit location.
- **Early abort on missing ansible-lint**: avoids confusing "command not found" errors buried in output; the error message explicitly names the fix (`pip install ansible-lint`).
- **`set -euo pipefail`**: strict mode ensures unexpected failures propagate rather than being silently swallowed.
- **`# shellcheck disable=SC2086`**: `$STAGED_FILES` is intentionally unquoted to allow word-splitting into multiple file arguments to ansible-lint. This is safe because the values come from `git diff --name-only` (no spaces in tracked filenames).
- **No pip install performed**: ansible-lint is not installed on this machine and was not installed as part of this task. The hook handles its absence gracefully.

## Files created / modified
| Path | Action |
|------|--------|
| `/opt/claude/CCAS/hooks/pre-commit` | Created (executable) |
| `/opt/claude/CCAS/ccas-*/. git/hooks/pre-commit` | Symlinked (×6) |
| `artefacts/task-051/build_notes.md` | Created |
| `artefacts/task-051/test_results.md` | Created |
| `artefacts/task-051/test_pre_commit.sh` | Created (executable) |

## No credentials committed
No secrets, tokens, or sensitive values appear in any artefact.

---

## Fix loop — 2026-04-30 (Reviewer findings, confidence ≥ 80)

**Fix 1 + Fix 4 (combined): Hook script rewrite**
Applied to `/opt/claude/CCAS/hooks/pre-commit`:
- Replaced string-based `STAGED_FILES` capture (`$()` subshell + `grep`) with `mapfile -t STAGED_FILES < <(...)` — eliminates word-splitting issues with filenames.
- Extended grep pattern from `\.yml$` to `\.(yml|yaml)$` via `grep -E` — `.yaml` extensions were silently skipped before.
- Replaced unquoted `$STAGED_FILES` in the `ansible-lint` call (required `# shellcheck disable=SC2086`) with properly quoted `"${STAGED_FILES[@]}"`.
- Replaced manual `EXIT_CODE` capture + `if [ "$EXIT_CODE" -ne 0 ]` pattern with `if ! ansible-lint ...; then` — the `if !` construct suppresses `set -e` for the tested command, making the failure path safe and idiomatic.
- Removed now-redundant `# shellcheck disable=SC2086` directive.
- Simplified header comment (removed `# Usage` and `# To skip` lines now in install docs).

**Fix 2: Install script — symlinks instead of copies**
Applied to `/opt/claude/CCAS/ccas-main/scripts/install-pre-commit-hooks.sh`:
- Replaced `SOURCE_HOOK="$PROJECT_ROOT/.git/hooks/pre-commit"` lookup with `CANONICAL_HOOK="/opt/claude/CCAS/hooks/pre-commit"` — points directly to the authoritative hook, not a copy inside ccas-main.
- Replaced `cp "$SOURCE_HOOK" "$HOOK_PATH" && chmod +x "$HOOK_PATH"` with `ln -sf "$CANONICAL_HOOK" "$HOOK_PATH"` — symlinks auto-update when the canonical hook changes; no manual re-install needed.
- Removed backup block (`cp "$HOOK_PATH" "$HOOK_PATH.backup.*"`) — symlinks are trivially re-created; backups of copies were misleading (backed up the wrong file, not the canonical source).

**Syntax verification**:
- `bash -n /opt/claude/CCAS/hooks/pre-commit` → exit 0
- `bash -n /opt/claude/CCAS/ccas-main/scripts/install-pre-commit-hooks.sh` → exit 0
