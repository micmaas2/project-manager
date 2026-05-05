# Improvement Proposals — task-059 batch (EPIC-009)

**Agent**: SelfImprover [Haiku]
**Date**: 2026-05-05
**Source tasks**: task-059 (BL-122), task-060 (BL-124), task-061 (BL-126), task-062 (BL-127), task-063 (BL-128), task-064 (BL-129)

---

## Proposal 1

**Target file**: `CLAUDE.md` — "Cross-file rule mirroring (M-1 pattern)" bullet

**Change**: Add one sentence after the existing M-1 rule to explicitly require that implementing tasks enumerate ALL target files:

Current text ends with:
> Also verify that the `Label all outputs:` directive in each agent YAML matches the tiers listed in the CLAUDE.md Label bullet (Model Policy section) — this is a second M-1 mirror that model-pin checks do not cover.

Append (new sentence):
> **M-1 task scope rule**: every task that fixes or adds a mirrored rule must list ALL N target files in its acceptance criteria and verify all N copies in a single commit — a task that updates N-1 of N copies is incomplete and will be returned by Reviewer.

**Rationale**: task-060 fixed builder.yaml but missed reviewer.yaml; Reviewer Finding 1 (confidence 95) caught it. The existing M-1 rule explains the pattern but says nothing about task scoping. The gap is the absence of an explicit "all copies or none" commit contract. Adding this sentence closes the loophole without growing the rule into a new section.

**Status**: APPROVED

---

## Proposal 2

**Target file**: `CLAUDE.md` — "M-1 copy-paste rule" bullet

**Change**: Extend the existing copy-paste rule to call out skill checklist items specifically:

Current text:
> **M-1 copy-paste rule**: when mirroring a definition across CLAUDE.md and agent YAMLs, copy-paste verbatim — never paraphrase. Unicode vs ASCII symbol variants (`≥` vs `>=`) and synonym substitutions ("issue" vs "defect") both silently break the M-1 verbatim-match contract.

Append one sentence:
> This applies equally to skill checklist items (`.claude/commands/*.md`) that reproduce CLAUDE.md rules — open the exact source line and copy-paste; do not rephrase from memory.

**Rationale**: task-063's pm-start.md failure was a paraphrase of a CLAUDE.md recovery rule, not a YAML-to-CLAUDE.md mirror. The existing copy-paste rule targets "agent YAMLs" explicitly but does not mention skill markdown files. The Reviewer correctly applied the M-1 contract; adding skill files to the rule's stated scope prevents future ambiguity about whether skill markdown files are in scope.

**Status**: APPROVED
