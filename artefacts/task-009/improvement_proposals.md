# Improvement Proposals — task-009

[Sonnet]
**Agent**: SelfImprover (Sonnet 4.6)
**Date**: 2026-04-07
**Task**: task-009 — Pensieve Gmail Capture Workflow

---

## Proposal 1

**Target file**: `tasks/queue.json` (MVP template `security_arch_impact` field) — enforced via CLAUDE.md MVP template definition and `manager.yaml` prompt

**Change**:
Add a mandatory checklist item to the MVP template `security_arch_impact` block for any task that writes user-controlled or externally-sourced values into structured text formats (YAML, JSON, Markdown frontmatter):

```
- If any field value sourced from external data (email headers, API responses, user input)
  is interpolated into YAML/JSON/Markdown: YAML-escape or JSON-encode strings before
  interpolation (e.g. replace `"` with `\"` in YAML double-quoted scalars; strip or escape
  newlines and control characters).
```

The task-009 Builder correctly implemented YAML escaping for `title` and `from` (Tests 9 and 10 pass), but this was not specified anywhere in the MVP template — it was caught by code-quality-reviewer at HIGH severity and by Reviewer as a non-blocking observation. The fix only existed because Builder applied it from experience, not from a template requirement.

**Rationale**: YAML injection via unescaped email sender display names or subject lines is a realistic attack surface for any note-capture workflow. Requiring explicit YAML-escape guards in the MVP template ensures Builder implements them by default rather than as an afterthought, and means Reviewer can treat their absence as a template non-compliance rather than just an observation.

**Status**: REQUIRES_HUMAN_APPROVAL

---

## Proposal 2

**Target file**: `tasks/queue.json` (MVP template `security_arch_impact` field) — enforced via CLAUDE.md MVP template definition and `manager.yaml` prompt

**Change**:
Add a mandatory checklist item to the MVP template for any task that uses an externally-sourced ID (e.g. `gmailData.id`, API object IDs) as a downstream dependency (e.g. to mark an email read, to reference a record):

```
- If an external ID (e.g. message ID, record ID) is used in a subsequent step:
  validate it is non-null/non-empty before proceeding; throw a descriptive error if absent
  (e.g. "gmailData.id is required to mark email as read").
```

The task-009 Builder implemented a `gmailData.id` null check (Test 11 passes), but the MVP template's security section did not require it. The guard was added from experience, not specification. Without this requirement, a future Builder might omit the null check, causing a silent failure where notes are written but emails are never marked as read.

**Rationale**: External IDs from third-party APIs (Gmail, calendar, CRM) are not guaranteed to be present in every response. A downstream step that silently skips when the ID is missing (or crashes without a user-facing error) creates a hard-to-debug operational failure. The MVP template should mandate null-guards for any cross-step ID dependency.

**Status**: REQUIRES_HUMAN_APPROVAL

---

## Proposal 3

**Target file**: `tasks/queue.json` (MVP template `security_arch_impact` field) — enforced via CLAUDE.md MVP template definition and `manager.yaml` prompt

**Change**:
Add a control-character stripping standard to the MVP template for any task that writes externally-sourced string fields into file content or structured formats:

```
- For any string field sourced from external data that will be written to a file or
  structured format: strip or escape ASCII control characters (chars 0x00–0x1F, 0x7F)
  before use. Newline stripping alone is insufficient — also strip null bytes, carriage
  returns, tabs-in-unexpected-positions, and other control characters that can corrupt
  YAML/Markdown parsing or downstream tooling.
```

The task-009 `from` field had newline stripping (`replace(/\n/g, ' ')`) but no general control-character sanitisation. The Reviewer noted the `"` escaping gap; a broader control-character strip was not mandated anywhere. Email sender display names sourced from untrusted external systems can contain arbitrary control characters.

**Rationale**: Newline-only stripping is a partial defence. A complete sanitisation pass over externally-sourced strings before writing to YAML/Markdown prevents a class of corruption bugs and injection vectors. Mandating this in the MVP template ensures it is implemented at build time rather than discovered during review.

**Status**: REQUIRES_HUMAN_APPROVAL
