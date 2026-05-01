# Improvement Proposals — task-053

**Agent**: SelfImprover [Haiku]
**Date**: 2026-05-01
**Task**: BL-108 / S-007-3 — pi-homelab: HA YAML pre-commit hook

---

## Proposal 1: HA custom YAML tags — register wildcard multi-constructor in pre-commit hooks for HA/DSL YAML

**Target file**: CLAUDE.md — Shell script pre-submission check section

**Change**:

Add the following bullet under the **Shell script pre-submission check** block (after the `grep -E '\.(yml|yaml)$'` bullet):

```
- If the hook validates YAML files from a project using custom tags (e.g. Home Assistant
  `!secret`, `!include`, `!env_var`): register a wildcard multi-constructor on SafeLoader
  before any load call: `yaml.add_multi_constructor('', _ignore_unknown_tags, Loader=yaml.SafeLoader)`.
  Without this, every valid custom-tag file raises ConstructorError and blocks the commit —
  a blanket false positive. Also use `list(yaml.safe_load_all(...))` instead of `yaml.safe_load(...)`
  to parse multi-document YAML streams without raising on `---` separators.
```

**Rationale**: task-053 CQR and Reviewer both flagged `yaml.safe_load()` as incapable of handling HA custom tags and multi-document files at confidence 98 and 85 respectively. These are HA-specific patterns that any pi-homelab hook maintainer would hit immediately. Adding the pattern to the Builder pre-submission checklist prevents the initial broken version from being shipped and requiring a fix loop.

**Status**: APPROVED

---

## Proposal 2: PyYAML stdlib misconception — mandate explicit package availability check in hooks that import yaml

**Target file**: CLAUDE.md — Shell script pre-submission check section

**Change**:

Add the following bullet under the **Shell script pre-submission check** block (grouped with the binary-check ordering bullet):

```
- If the hook uses `import yaml` (PyYAML / `python3-yaml`): add an explicit availability guard
  after the `python3` binary check — PyYAML is NOT stdlib:
  ```bash
  if ! python3 -c "import yaml" &>/dev/null; then
      echo "ERROR: PyYAML not found — install with: sudo apt install python3-yaml" >&2
      exit 1
  fi
  ```
  Do not document it as "no external dependencies required" in script comments — PyYAML is a
  system/PyPI package. Correct comment: "Uses PyYAML (python3-yaml) — pre-installed on Raspberry Pi OS."
```

**Rationale**: task-053 Reviewer F2 (conf 90) and CQR (conf 99) both caught the stdlib misconception. The package is reliably present on Pi OS but the absence check prevents cryptic `ModuleNotFoundError` on fresh environments. Two independent review agents flagging the same issue at high confidence warrants a checklist rule.

**Status**: APPROVED

---

## Proposal 3: Staged content validation — mandate `git show ":$file"` in pre-commit hooks, not working-tree reads

**Target file**: CLAUDE.md — Shell script pre-submission check section

**Change**:

Add the following bullet under the **Shell script pre-submission check** block:

```
- If the hook validates file content: read the staged index version via `git show ":$file"`
  piped to the validator via stdin — do NOT open the working-tree file directly. Reading from
  disk means on-disk edits after `git add` cause false passes or false failures depending on
  timing. Pass the filename as a separate `sys.argv` argument for error message context only.
  Replace `[ -f "$file" ]` disk-existence guards with `git ls-files --error-unmatch "$file"`
  to check the index.
```

**Rationale**: task-053 CQR Finding 3 (conf 95) identified this as a correctness bug — the hook validated the working-tree file, not what was actually being committed. This is the canonical correct approach for pre-commit hooks and should be a Builder checklist item to prevent the same mistake in future hook tasks.

**Status**: APPROVED
