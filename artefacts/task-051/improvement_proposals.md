# task-051 — Improvement Proposals

**Agent**: SelfImprover [Haiku]
**Date**: 2026-04-30

---

## Proposal 1

**Target file**: `CLAUDE.md` — Shell script pre-submission check (Builder checklist)

**Change**:

Add a new bullet to the "Shell script pre-submission check" section:

```
- If the script has a guard that requires a tool to be present (binary check) AND an
  early-exit path that bypasses the tool entirely (e.g. empty staged files): order the
  early-exit check BEFORE the binary-presence check. A binary check that fires on a
  no-op path causes false failures on clean environments where the tool is not installed.
  Correct order: (1) collect inputs, (2) exit 0 if inputs empty, (3) check tool present.
```

**Rationale**: task-051 Tester caught a bug where `ansible-lint` binary check ran before the empty-staged-files early exit. On a clean repo with no staged YAML files, the hook exited 1 with an installation error even though no lint was needed. The correct sequence — collect inputs, early-exit on empty, then check binary — was not in the Builder checklist and required a Tester-driven fix loop. Adding this ordering rule prevents the same mistake in any future hook or script that has optional-tool logic.

**Status**: REQUIRES_HUMAN_APPROVAL

---

## Proposal 2

**Target file**: `CLAUDE.md` — Shell script pre-submission check (Builder checklist)

**Change**:

Add a new bullet to the "Shell script pre-submission check" section:

```
- Under `set -euo pipefail`, never use a bare command call followed by `EXIT_CODE=$?`
  to capture failure — `set -e` terminates the script before `$?` is reached. Use the
  `if ! command ...; then` idiom instead: the `if !` construct suppresses `set -e` for
  the tested command and allows the failure branch to execute. This applies to any
  command whose non-zero exit must be handled explicitly (e.g. linters, validators).
```

**Rationale**: task-051 Reviewer F1 (confidence 90) found that `EXIT_CODE=$?` after `ansible-lint` was dead code under `set -e` — the script terminated before the capture could run. The Reviewer correctly recommended `if ! ansible-lint ...; then`. This is a recurring shell scripting trap (the original Builder build also contained this pattern). Adding the rule to the pre-submission checklist ensures Builder self-checks for it before handing off to Reviewer.

**Status**: REQUIRES_HUMAN_APPROVAL

---

## Proposal 3

**Target file**: `CLAUDE.md` — Shell script pre-submission check (Builder checklist)

**Change**:

Add a note to the existing file-extension filter bullet (or add a new bullet):

```
- If the hook/script filters files by extension using grep: include both `.yml` AND
  `.yaml` variants unless one is explicitly excluded by design. Use `grep -E '\.(yml|yaml)$'`
  as the default pattern. Document in a comment if only one extension is intentionally
  targeted (e.g. `# jenkins.yaml excluded: not Ansible`).
```

**Rationale**: task-051 CQR caught the `.yaml` extension omission (Reviewer rated it conf 72 — below the ≥80 fix loop threshold). The Reviewer noted 3 `.yaml` files in CCAS that would be silently skipped. The fix (`grep -E '\.(yml|yaml)'`) was applied in the Builder loop. For any shell hook filtering YAML files, both extensions should be the default unless explicitly excluded. Adding this to the pre-submission checklist prevents a silent lint gap on `.yaml`-named files.

**Status**: REQUIRES_HUMAN_APPROVAL
