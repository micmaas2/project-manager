# Task-054 Build Notes
## n8n JSON workflow pre-commit hook — pensieve repo

### What was built
A bash pre-commit hook at `/opt/claude/pensieve/hooks/pre-commit` that:
- Collects staged `.json` files via `git diff --cached --name-only --diff-filter=ACM | grep -E '\.json$'`
- Exits 0 silently if no JSON files are staged (early-exit before binary check — per CLAUDE.md ordering rule)
- Checks that `python3` is available (after early-exit)
- For each staged file: reads from the git index via `git show ":$file"` (not the working tree)
- Validates JSON using `python3 -c "import sys, json; json.load(sys.stdin)"`
- On parse error: prints `ERROR: <file>: <error message>` to stderr, sets FAILED=1
- Exits 1 if any file failed, exits 0 otherwise

Symlink: `/opt/claude/pensieve/.git/hooks/pre-commit` → `../../hooks/pre-commit`

### Design decisions
1. **Staged-index read via `git show ":$file"`**: per CLAUDE.md lesson, reading the working tree causes false pass/fail when disk content differs from staged content. Piping `git show` output to Python stdin ensures we validate exactly what will be committed.
2. **`sys.argv[1]` for filename in error messages**: filename passed as positional argument to the inline Python; the error message uses `sys.argv[1]` rather than capturing from the shell variable, keeping the Python block self-contained.
3. **Early-exit before binary check**: per CLAUDE.md ordering rule — (1) collect inputs, (2) exit 0 if inputs empty, (3) check binary present. This prevents false failures on environments without python3 when there is nothing to validate.
4. **`git ls-files --error-unmatch`**: safety net to confirm file is tracked in the index (not just on disk), matching the pi-homelab reference pattern.
5. **`|| true` on grep**: prevents `set -euo pipefail` from aborting when no JSON files match (grep exits 1 on no match).
6. **stdlib only**: uses only `json` from Python's standard library — no pip dependencies.

### Reference
Pattern follows `/opt/claude/pi-homelab/hooks/pre-commit` (S-007-2) closely, with:
- YAML → JSON (simpler: no multi-document load, no custom tag handling needed)
- PyYAML availability check removed (stdlib `json` always available with python3)

### Verification steps run

#### bash -n syntax check
```
bash -n /opt/claude/pensieve/hooks/pre-commit
# exit 0 — PASS
```

#### Functional tests (all PASS)
| Test | Scenario | Expected | Result |
|------|----------|----------|--------|
| 1 | No JSON files staged | exit 0, no output | PASS |
| 2 | Valid JSON staged (workflows/gmail-capture.json) | exit 0, no output | PASS |
| 3 | Invalid JSON staged (malformed workflows/bad_workflow.json) | exit 1, `ERROR: workflows/bad_workflow.json: Expecting ',' delimiter: line 5 column 3 (char 74)` | PASS |
| 4 | Only non-JSON files staged (README.md) | exit 0, no output | PASS |
| 5 | Symlink resolves and is executable | symlink → `../../hooks/pre-commit`, executable | PASS |

### Acceptance criteria verification
1. ✅ `hooks/pre-commit` exists at `/opt/claude/pensieve/hooks/`, is executable (`chmod +x`), and `.git/hooks/pre-commit` symlinks to `../../hooks/pre-commit`
2. ✅ Hook validates all staged `.json` files using `python3 json.load()` via stdin from `git show ":$file"`
3. ✅ Hook exits 1 and reports `ERROR: <file>: <parse error>` to stderr on JSON syntax failure (Test 3 verified)
4. ✅ Hook exits 0 silently when no `.json` files are staged (Tests 1 and 4 verified)
5. ✅ `bash -n hooks/pre-commit` exits 0

### Files created
- `/opt/claude/pensieve/hooks/pre-commit` (new, executable)
- `/opt/claude/pensieve/.git/hooks/pre-commit` (symlink → `../../hooks/pre-commit`)
- `/opt/claude/project_manager/artefacts/task-054/build_notes.md` (this file)

---

## Builder Loop Fixes

Three review-mandated fixes applied to `/opt/claude/pensieve/hooks/pre-commit`:

### Fix 1 — Remove `2>&1` from `git show` block (confidence 88)
- **Line changed**: 38 (formerly `" "$file" 2>&1; then`)
- **Change**: removed trailing `2>&1` so Python's `print(..., file=sys.stderr)` on error now reaches the terminal instead of being consumed and discarded by the `if !` construct
- **Final form**: `" "$file"; then`

### Fix 2 — Add `--` to `git show` call (confidence 85)
- **Line changed**: 30 (formerly `if ! git show ":$file" | python3 -c "`)
- **Change**: added `--` before the refspec to prevent flag injection if a filename begins with `-`
- **Final form**: `if ! git show -- ":$file" | python3 -c "`
- Note: Fix 1 and Fix 2 were applied to the same block in one edit pass.

### Fix 3 — Remove redundant `2>&1` from `git ls-files` check (confidence 95)
- **Line changed**: 26 (formerly `if ! git ls-files --error-unmatch "$file" &>/dev/null 2>&1; then`)
- **Change**: `&>/dev/null 2>&1` is equivalent to `>/dev/null 2>&1 2>&1`; the second redirect is a no-op. Simplified to `&>/dev/null`
- **Final form**: `if ! git ls-files --error-unmatch "$file" &>/dev/null; then`

### Verification
```
bash -n /opt/claude/pensieve/hooks/pre-commit
# exit code: 0 — PASS
```
