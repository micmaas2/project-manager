# Improvement Proposals — task-050

**Agent**: SelfImprover [Haiku]
**Date**: 2026-04-29

---

## Proposal 1

**Target file**: `/opt/claude/project_manager/.claude/agents/self-improver.yaml`

**Change**:
Add the confidence scoring rubric (currently only in build_notes.md) directly into the `Confidence` field definition in the agent YAML prompt, immediately after the `integer 1-100` line:

```yaml
  - `Confidence`: integer 1-100 — how certain is this lesson applicable to future work? (1=speculative, 100=proven pattern)
    Rubric: 90-100 = proven pattern (3+ tasks, same failure mode); 70-89 = high (2+ occurrences or clear root cause); 50-69 = moderate (single occurrence, plausible generalization); 1-49 = speculative (edge case, context-dependent)
```

**Rationale**: The calibration rubric defined in build_notes.md is invisible to self-improver at runtime — the agent only reads its own prompt. Without the rubric, confidence scores will drift and become non-comparable across sessions. CQR (m-1) and Reviewer F3 (conf 48) both identified this gap. Embedding the rubric in the YAML prompt makes scoring consistent and auditable without any external reference.

**Status**: APPROVED

---

## Proposal 2

**Target file**: `/opt/claude/project_manager/tasks/backlog.md`

**Change**:
Register a new backlog item to backfill existing lessons.md rows with `| — | — |` placeholder values for the two new `Confidence` and `Scope` columns, resolving the structural table inconsistency introduced by task-050.

Add entry:
```
- BL-NNN | Backfill lessons.md existing rows with Confidence/Scope placeholder values | EPIC-003 | project_manager | P3 | new | 2026-04-29
```

**Rationale**: Reviewer F1 (conf 72) and CQR m-2 both flagged that 27+ existing rows in lessons.md now have 4 pipe-separated fields while the header specifies 6. This breaks Markdown table rendering and any future tooling that parses lessons.md by column index. The fix is a simple one-pass sed/python backfill — low effort, high traceability value. This is a repeated pattern: schema additions to append-only tables without backfill create silent structural drift. Queueing the backfill as a mandatory follow-up at build time prevents this debt from accumulating.

**Status**: APPROVED

