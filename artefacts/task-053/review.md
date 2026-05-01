# task-053 Review — HA YAML Pre-Commit Hook

**Agent**: Reviewer (Sonnet)
**Date**: 2026-05-01
**Artefact reviewed**: `/opt/claude/pi-homelab/hooks/pre-commit`

---

## Shell Script Checklist (CLAUDE.md)

| Check | Result |
|-------|--------|
| `bash -n` exits 0 | PASS — verified live |
| Early-exit before binary check | PASS — exit 0 on empty staged list (line 12–14) before `command -v python3` (line 17–20) |
| No `EXIT_CODE=$?` under `set -euo pipefail` | PASS — uses `if ! command ...; then` and `if [ "$FAILED" -ne 0 ]` patterns throughout |
| Both `.yml` AND `.yaml` covered | PASS — `grep -E '\.(yml|yaml)$'` on line 9 |
| `|| true` guard on grep | PASS — prevents `set -e` abort when no YAML files staged |
| No user-supplied path construction | PASS — file paths come from `git diff --cached --name-only` (repo-relative, git-controlled) |
| No hardcoded secrets or secret-named env vars | PASS |
| Executable bit set | PASS — `-rwxr-xr-x` confirmed |
| Symlink present | PASS — `.git/hooks/pre-commit -> ../../hooks/pre-commit` confirmed |

---

## Acceptance Criteria

| # | Criterion | Result |
|---|-----------|--------|
| 1 | hooks/pre-commit exists, is executable, symlink in .git/hooks | PASS |
| 2 | Validates staged .yaml files using `python3 yaml.safe_load()` | PASS (with caveat — see Finding 1) |
| 3 | Exits non-zero + reports file + parse error on syntax failure | PASS |
| 4 | Exits 0 silently when no .yaml files staged | PASS |
| 5 | `bash -n` exits 0; malformed YAML test confirms blocking | PASS |

---

## Findings

## Finding 1: `yaml.safe_load()` silently blocks valid multi-document YAML
**Severity**: major
**Confidence**: 85
**Description**: `yaml.safe_load()` raises `yaml.scanner.ScannerError` when the input contains multiple YAML documents separated by `---`. This means a syntactically valid HA configuration file with multiple documents (a legitimate YAML pattern) will cause the hook to exit 1 and block the commit. Test confirmed:

```python
import yaml
yaml.safe_load("key: val\n---\nkey2: val2\n")
# Raises: expected a single document in the stream
```

Home Assistant configuration files sometimes use `---` document separators (e.g. in automation YAML exported from the UI or template files). The correct fix is to use `yaml.safe_load_all()` wrapped in `list()` to consume all documents and catch errors across all of them:

```python
list(yaml.safe_load_all(open(sys.argv[1]).read()))
```

`safe_load_all()` passes valid multi-document YAML and still correctly raises `yaml.YAMLError` on malformed syntax — verified.

**Recommendation**: Replace `yaml.safe_load(...)` with `list(yaml.safe_load_all(...))` in the inline Python snippet. This is a one-character-range change that eliminates the false-positive blocking of valid multi-doc HA YAML.

---

## Finding 2: Comment claims `yaml` is Python stdlib — it is not
**Severity**: minor
**Confidence**: 90
**Description**: Line 3 of the script reads:

```bash
# Uses Python stdlib yaml.safe_load() — no external dependencies required.
```

The `yaml` module is **PyYAML** (`python3-yaml`, PyPI package `pyyaml`), not a Python standard library module. It is a system Debian package (`dpkg -l python3-yaml` confirms `ii python3-yaml 6.0.2-1+b2`). On Raspberry Pi OS it is typically pre-installed as a system package and is reliably available, but it is architecturally incorrect to describe it as "stdlib". Similarly, the MVP template's `security_arch_impact` field states "stdlib yaml only", which is inaccurate.

This is a documentation accuracy issue, not a functional defect. The hook will work correctly on any standard Pi OS installation where `python3-yaml` is present.

**Recommendation**: Update the comment to: `# Uses PyYAML (python3-yaml system package) — pre-installed on Raspberry Pi OS; no pip/npm deps required.` Also correct the MVP template `security_arch_impact` note in queue.json.

---

## Finding 3: Hook validates working-tree file, not staged index content
**Severity**: minor
**Confidence**: 72
**Description**: The hook collects staged file paths via `git diff --cached --name-only` but then opens each file from disk (`open(sys.argv[1]).read()` reads the working-tree path). If a developer stages a file with `git add file.yaml` and then edits the file on disk before committing, the hook validates the on-disk version (possibly different from what will be committed). The commit could succeed for broken staged content that happens to have been fixed on disk, or fail for valid staged content that was subsequently broken on disk.

The correct approach is to read the staged content via `git show :file.yaml` (or `git cat-file blob :file.yaml`) for each file. However, this is a common trade-off in hook design — the simpler disk read avoids subprocess overhead and is correct in the common case where the staged and working-tree versions match.

Confidence is 72 (below the 80 loop threshold) because this is a known intentional simplification in many pre-commit hook implementations, the acceptance criteria do not require staged-content validation, and it is not a security issue in this context.

**Recommendation**: Document the design decision explicitly in a comment near line 26, e.g.: `# Note: reads from working tree, not git index — sufficient for this validation use case.` No code change required.

---

## Finding 4: `--diff-filter=ACM` excludes renamed YAML files
**Severity**: info
**Confidence**: 65
**Description**: The `--diff-filter=ACM` flag covers Added, Copied, and Modified files but excludes Renamed (`R`) files. A file renamed to `.yaml` (e.g. `config.txt` → `config.yaml`) will not be validated by this hook on the rename commit. This is a minor gap — renames to .yaml are uncommon, and the file content validation would fire on the next modification.

**Recommendation**: Consider changing to `--diff-filter=ACMR` to include renamed files. The existing existence guard (`[ -f "$file" ]`) already handles the edge case of renamed-away files safely. No urgency — info only.

---

## Overall verdict

**APPROVED WITH MINOR NOTES**

Builder must loop on findings with confidence >= 80 only.

Finding 1 (confidence 85) requires a fix: replace `yaml.safe_load()` with `list(yaml.safe_load_all(...))` to prevent false-positive blocking of valid multi-document HA YAML files.

Finding 2 (confidence 90) requires a comment correction only: update the "stdlib" comment to accurately describe PyYAML as a system package.

Findings 3 and 4 (confidence 72 and 65) are below the 80 threshold — log to `build_notes.md` only, no Builder loop required.

The hook is structurally sound, passes all CLAUDE.md shell script checklist items, and meets the acceptance criteria. The `safe_load_all` fix is a one-line change with no structural impact.
