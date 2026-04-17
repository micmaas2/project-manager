# Improvement Proposals: task-035

**Task**: task-035 — CLAUDE.md + Agent YAML token reduction rewrites
**SelfImprover run**: 2026-04-17

---

## Proposal 1

**Target file**: `tasks/backlog.md`
**Change**: Promote BL-096 (CLAUDE.md size reduction) to P1 in queue — CLAUDE.md is still 9,402 tokens / ~37.6k chars after these rewrites; further reduction needed.
**Rationale**: Even with 930-token savings from this task, CLAUDE.md remains large. BL-096 calls for structural reorganisation (linked docs, archived reference content) which this task did not address.
**Status**: REJECTED: already applied — BL-096 was already P1 in backlog.md at review time

---

## Proposal 2

**Target file**: `CLAUDE.md` — Token count acceptance criteria note
**Change**: Add note to task queue schema or PM Planning Session section: "When creating rewrite plan tasks that target specific token counts, include a note that the baseline may shift between plan date and execution date — acceptance criteria should express savings delta (e.g. 'save ≥900 tokens') rather than absolute post-rewrite totals."
**Rationale**: The task-035 acceptance criterion of `<= 11,510` could not be met because CLAUDE.md grew 1,517 tokens between task-026 (plan) and task-035 (execution). Expressing targets as deltas makes the criteria stable.
**Status**: APPROVED
