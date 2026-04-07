# Improvement Proposals — task-004

**Agent**: SelfImprover (Sonnet 4.6)
**Date**: 2026-04-07
**Task**: task-004 — pensieve: Improved captures — richer summaries, better tagging, topic folders

---

## Proposal 1

**Target file**: `CLAUDE.md` — MVP template section (under `Security/arch impact`)

**Change**:

Add the following bullet to the MVP template's `Security/arch impact` block, after the existing outbound-HTTP checks:

```
  - If any user-controlled value (topic, category, tag, filename) is used in a file path:
      - Validate against an allowlist or strict regex (e.g. `[a-z0-9-]+`) before path construction
      - Assert `finalPath.startsWith(ALLOWED_ROOT)` after construction and before any write
```

**Rationale**: task-004 implemented slug validation and `filepath.startsWith(VAULT + '/')` correctly, but these were added from Builder experience — the MVP template's security section did not require them. Without an explicit mandate, future tasks writing files at dynamic paths may skip the path-traversal guard. Making this a required checklist item in the template ensures it is evaluated during preflight and review on every applicable task.

**Status**: APPROVED

---

## Proposal 2

**Target file**: `CLAUDE.md` — MVP template section (under `Security/arch impact` or as a new `LLM output contracts` note)

**Change**:

Add the following line to the MVP template, under or adjacent to the security block:

```
  - If LLM output is used as a structured field (slug, enum, filename): the prompt character-set
    constraint and the validation regex in code must be identical. Document both in the task artefact.
```

**Rationale**: The Reviewer observed that `claude-processor.txt` said "no hyphens" while `TOPIC_PATTERN = /^[a-z0-9-]+$/` accepted them. This is benign here (code is more permissive), but if the model strictly follows the prompt, valid hyphenated slugs get silently dropped or sanitised — a latent defect. Requiring prompt/validator alignment in the MVP template prevents this class of inconsistency being shipped without a deliberate decision.

**Status**: APPROVED

---

## Proposal 3

**Target file**: `.claude/agents/builder.yaml` (or the relevant n8n / capture builder agent YAML)

**Change**:

Add the following to the builder agent's prompt or checklist section:

```
- When a workflow confirmation message is sent to the user (e.g. Telegram reply), the message
  MUST include the fully-resolved destination path (e.g. Category/Topic/filename.md), not just
  the filename. This allows the user to verify correct folder placement without opening the
  target application.
```

**Rationale**: task-004's Telegram confirmation showed only `title` and `filename`, omitting `Category/Topic`. The Reviewer flagged this as a non-blocking UX gap. Baking this rule into the Builder agent prompt ensures future capture workflows emit traceable confirmations by default, rather than relying on a Reviewer catch.

**Status**: APPROVED
