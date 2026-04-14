# Improvement Proposals — task-026
**Task**: Token reduction analysis: CLAUDE.md + agent YAMLs (BL-049)
**Agent**: SelfImprover [Haiku]
**Date**: 2026-04-14

---

## Proposal 1

**Target file**: `tasks/backlog.md`
**Change**: Add a new backlog item for the actual rewrite execution based on rewrite-plan.md findings.

```
| BL-NEW | EPIC-003 | project_manager: Execute CLAUDE.md + agent YAML token reduction rewrites (from task-026 plan) | project_manager | P2 | new | 2026-04-14 |
```

**Rationale**: task-026 is analysis-only. The rewrite-plan.md identifies ~1,540 tokens of savings across 6 targets with specific per-item strategies. Without a follow-up task, the plan has no execution path.
**Status**: APPROVED

---

## Proposal 2

**Target file**: `CLAUDE.md` — § n8n Workflow Deployment (Pi4)
**Change**: Add a note that Python testing patterns in this section should be relocated to a separate `## Python Testing Patterns` section during the next rewrite pass, to improve navigability.

**Rationale**: Lines 27–42 of the n8n section cover general Python testing gotchas unrelated to n8n. Developers searching for testing patterns look in the wrong section. Structural move has no token cost but improves search surface.
**Status**: APPROVED
