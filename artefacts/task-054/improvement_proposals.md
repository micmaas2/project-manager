# Improvement Proposals — task-054
**Agent**: SelfImprover [Haiku]
**Date**: 2026-05-01
**Task**: pensieve: n8n JSON workflow syntax pre-commit hook (BL-110, S-007-4)

---

## Proposal 1

**Target file**: `tasks/lessons.md`
**Change**: Append lesson documenting that `git show -- ":$file"` is incorrect for index refspec reads — the `--` separator causes git to treat `:$file` as a pathspec rather than an index object reference, breaking staged-content reads.
**Rationale**: CQR recommended `--` (confidence 85) as flag-injection hardening. The recommendation was factually wrong for the `:filename` index refspec syntax, which is self-disambiguating and does not accept `--` in the same way positional file arguments do. The Tester caught this during functional testing — it caused a false positive that blocked all valid JSON commits. This is a new, distinct failure mode not covered by the existing lesson (row 128) which correctly documents `git show ":$file"` as the right pattern. The new lesson should clarify why `--` must NOT be added to this specific syntax.
**Status**: SKIPPED: already present in tasks/lessons.md

---

## Proposal 2

**Target file**: `CLAUDE.md` (shell script pre-submission check section)
**Change**: Add a note to the existing `git show ":$file"` index-read rule (currently in lessons.md row 128) clarifying: "Do NOT add `--` before the `:$file` index refspec — `git show -- ":$file"` treats `:$file` as a working-tree pathspec and returns commit metadata instead of staged file contents, causing false-positive failures on all valid commits."
**Rationale**: The current CLAUDE.md lesson (row 128 in lessons.md, also baked into the shell script checklist) states to use `git show ":$file"` but does not warn against the common `--` hardening attempt. A future Builder or CQR may repeat the same mistake — recommending `--` because it is a widely documented git safety practice for separating flags from filenames. Embedding a brief anti-pattern note directly in the CLAUDE.md checklist prevents this failure class from recurring regardless of whether the Builder reads lessons.md first.
**Status**: APPROVED

---

## Proposal 3

**Target file**: `.claude/agents/code-quality-reviewer` (built-in — cannot edit YAML) → document in `CLAUDE.md` under the `code-quality-reviewer` bullet
**Change**: Add a note under the built-in `code-quality-reviewer` description: "When recommending git hardening patterns (e.g. adding `--` to git commands), verify against git documentation that the syntax is correct for the specific invocation context — index refspecs (`:filename`) and positional file arguments have different disambiguation rules."
**Rationale**: CQR's confidence 85 recommendation was technically incorrect. The `--` separator is valid and important for commands like `git checkout -- <file>` (separating flags from pathspecs), but it changes semantics for `git show` with index-object references. CQR has no special context for git index syntax, and the recommendation was plausible but wrong. A reminder in CLAUDE.md that CQR git-hardening recommendations should be verified against git docs before applying will reduce false positives from this class of error.
**Status**: APPROVED

---

## Proposal 4

**Target file**: `tasks/lessons.md`
**Change**: Append a lesson noting that the Tester correctly served as the last line of defence when a CQR recommendation (above loop threshold, confidence 85) introduced a regression. This validates the pipeline order: Reviewer+CQR findings ≥80 trigger Builder loop → Tester must still verify the fix does not introduce new regressions.
**Rationale**: task-054 demonstrates that even when Builder correctly applies a CQR recommendation (confidence 85, above the loop threshold), the resulting change can be functionally wrong. The Tester's functional test suite caught the regression that static analysis and code review missed. This is a positive confirmation that the full pipeline (Builder → Reviewer+CQR → Tester) is necessary and that Tester must never be skipped even when Reviewer+CQR are clean.
**Status**: SKIPPED: already present in tasks/lessons.md
