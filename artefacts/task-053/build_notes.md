# task-053 Build Notes — HA YAML Pre-Commit Hook

**Agent**: Builder (Sonnet)
**Date**: 2026-05-01
**Task**: BL-108 / S-007-3 — pi-homelab: HA YAML syntax pre-commit hook

---

## Files Created

| File | Location | Notes |
|------|----------|-------|
| `hooks/pre-commit` | `/opt/claude/pi-homelab/hooks/pre-commit` | Executable shell script (chmod +x) |
| `.git/hooks/pre-commit` | `/opt/claude/pi-homelab/.git/hooks/pre-commit` | Symlink → `../../hooks/pre-commit` |

## Symlink

```
/opt/claude/pi-homelab/.git/hooks/pre-commit -> ../../hooks/pre-commit
```

Verified with `ls -la`:
```
lrwxrwxrwx 1 root root 22 May  1 10:47 .git/hooks/pre-commit -> ../../hooks/pre-commit
```

---

## Pre-Submission Checklist Results

### bash -n syntax check
```
bash -n /opt/claude/pi-homelab/hooks/pre-commit
# Exit code: 0 — PASS
```

### Early-exit before binary check (order verification)
Lines from the script:
- Line 9: `STAGED_YAML=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(yml|yaml)$' || true)`
- Line 12–14: `if [ -z "$STAGED_YAML" ]; then exit 0; fi`  ← early exit FIRST
- Line 17–20: `if ! command -v python3 ...; then ... exit 1; fi`  ← binary check AFTER

**PASS** — early exit is correctly ordered before binary check.

### EXIT_CODE=$? pattern check
```
grep -n 'EXIT_CODE=$?' /opt/claude/pi-homelab/hooks/pre-commit
# No matches — PASS
```
Hook uses `if ! command ...; then` pattern throughout.

### Both .yml AND .yaml extensions covered
```
grep -E '\.(yml|yaml)' /opt/claude/pi-homelab/hooks/pre-commit
# Line 9: grep -E '\.(yml|yaml)$'  — PASS
```
Both extensions are covered in a single `grep -E` pattern per CLAUDE.md requirement.

---

## Functional Tests

### Test 1: Malformed YAML blocks commit
```bash
printf 'key: valid\nbad_indent:\n  - item\n    broken: [unclosed' > test_malformed.yaml
git add test_malformed.yaml
./hooks/pre-commit
# Output:
# YAML syntax error in test_malformed.yaml:
# mapping values are not allowed here
#   in "<unicode string>", line 4, column 11:
#         broken: [unclosed
#               ^
# Exit code: 1 — PASS (blocks commit)
```

### Test 2: No YAML staged — silent exit 0
```bash
# With only non-YAML files staged:
./hooks/pre-commit
# No output
# Exit code: 0 — PASS
```

### Test 3: Valid YAML passes
```bash
# Stage a syntactically correct HA YAML file:
./hooks/pre-commit
# No output
# Exit code: 0 — PASS
```

---

## Design Decisions

- **Early-exit before binary check**: exits 0 silently when no YAML is staged, avoiding a false
  failure in environments where python3 is not installed (and no YAML validation is needed).
- **`|| true` on grep**: prevents `set -euo pipefail` from aborting when no files match
  (grep exits 1 on empty match).
- **`--diff-filter=ACM`**: only validates Added, Copied, Modified files — not Deleted or Renamed
  source, which would trigger file-not-found errors.
- **Existence guard (`[ -f "$file" ]`)**: defensive check in case of complex merges where a
  staged file path no longer exists on disk.
- **Inline Python heredoc style**: the Python snippet is passed as `-c` argument to avoid
  creating temp files; `sys.argv[1]` carries the filename safely without shell expansion risks.

---

## Acceptance Criteria Verification

| # | Criterion | Status |
|---|-----------|--------|
| 1 | hooks/pre-commit exists, is executable, symlink in .git/hooks | PASS |
| 2 | Validates staged .yaml files via python3 yaml.safe_load() | PASS |
| 3 | Exits non-zero + reports file + parse error on syntax failure | PASS |
| 4 | Exits 0 silently when no .yaml files staged | PASS |
| 5 | bash -n exits 0; malformed YAML test confirms blocking | PASS |

---

## Fix Pass — 2026-05-01

**Trigger**: Reviewer + CQR loop required for findings with confidence ≥ 80.

### Changes Applied

#### Fix 1 + Fix 4 (CQR confidence 98): HA custom YAML tags — wildcard multi-constructor + safe_load_all

**Problem**: `yaml.safe_load()` raises `ConstructorError` on Home Assistant custom tags (`!secret`, `!include`, `!include_dir_list`, `!include_dir_merge_named`, `!env_var`, etc.), blocking valid HA YAML commits. Also `yaml.safe_load()` only parses the first document in multi-document YAML files.

**Fix**: Registered a wildcard multi-constructor on `SafeLoader` before loading, and switched to `list(yaml.safe_load_all(...))` to force full parsing of all documents.

```python
def _ignore_unknown_tags(loader, tag_suffix, node):
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    elif isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    return loader.construct_mapping(node)

yaml.add_multi_constructor('', _ignore_unknown_tags, Loader=yaml.SafeLoader)
list(yaml.safe_load_all(sys.stdin.buffer.read().decode('utf-8')))
```

#### Fix 2 (CQR confidence 99/95, Reviewer F2 confidence 90): PyYAML is not stdlib — added explicit check

**Problem**: The comment claimed "no external dependencies required" but PyYAML is a third-party package (`python3-yaml`). No runtime check existed for its presence.

**Fix**: Updated the header comment on line 3. Added a PyYAML availability check after the `python3` binary check (order: collect inputs → early exit → check python3 → check yaml module → loop).

```bash
if ! python3 -c "import yaml" &>/dev/null; then
    echo "ERROR: PyYAML not found — install with: sudo apt install python3-yaml" >&2
    exit 1
fi
```

#### Fix 3 (CQR confidence 95): Validate staged content, not working-tree file

**Problem**: The hook read the working-tree file (`open(sys.argv[1]).read()`), meaning an unstaged modification to the file could cause a false failure or false pass depending on timing.

**Fix**: Replaced `open(sys.argv[1]).read()` with `git show ":$file" | python3 -c "... sys.stdin.buffer.read().decode('utf-8') ..."`. The file is piped from the git index. `sys.argv[1]` still receives the filename for error messages.

Replaced `[ ! -f "$file" ]` working-tree guard with `git ls-files --error-unmatch "$file"` index guard — semantically correct for staged-only validation.

#### Fix 5 (CQR confidence 80): UTF-8 locale-safe decoding

**Problem**: `open(file)` without `encoding='utf-8'` or locale-safe stdin read could silently mis-decode UTF-8 content on non-UTF-8 locales.

**Fix**: Used `sys.stdin.buffer.read().decode('utf-8')` — reads raw bytes from stdin and decodes as UTF-8 unconditionally, regardless of the locale environment.

---

### Post-Fix Pre-Submission Checklist

```
bash -n /opt/claude/pi-homelab/hooks/pre-commit
# Exit code: 0 — PASS
```

| Check | Result |
|-------|--------|
| Early exit before binary check (line 13 < line 17 < line 23) | PASS |
| No `EXIT_CODE=$?` pattern | PASS |
| Both .yml AND .yaml covered (grep -E '\.(yml\|yaml)$') | PASS |
| PyYAML availability check present | PASS |
| Staged content used (git show ":$file") | PASS |
| UTF-8 locale-safe decoding (stdin.buffer.read().decode) | PASS |
| HA custom tags handled (wildcard multi-constructor) | PASS |
| Multi-document YAML handled (safe_load_all) | PASS |
