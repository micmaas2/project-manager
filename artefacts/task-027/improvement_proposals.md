# Improvement Proposals — task-027
**Task**: pm-healthcheck.sh: hooks, schema, YAML, logs check (BL-051)
**Agent**: SelfImprover [Haiku]
**Date**: 2026-04-14

---

## Proposal 1

**Target file**: `CLAUDE.md` — § n8n Workflow Deployment (Pi4) or new § Python Testing Patterns
**Change**: Add a gotcha note for root-bypasses-DAC in unit tests:

> **Testing unwritable paths as root**: `chmod 0o444` does not prevent root from writing. To simulate an unwritable directory in tests, replace it with a regular file (so `touch <dir>/<file>` fails with "Not a directory") or use a mount namespace. Document this at the top of test files that use this pattern.

**Rationale**: Task-027 hit this during test_unwritable_logs. Future test authors will hit it again unless the pattern is documented.
**Status**: REQUIRES_HUMAN_APPROVAL

---

## Proposal 2

**Target file**: `tasks/backlog.md`
**Change**: Add a new BL item for integrating pm-healthcheck.sh into /pm-start:

```
| BL-NEW | EPIC-003 | project_manager: Integrate pm-healthcheck.sh into /pm-start (BL-051 follow-up) | project_manager | P3 | new | 2026-04-14 |
```

**Rationale**: The MVP template explicitly notes "integration into pm-start skill" as out of scope for task-027. This is the natural follow-up to make the healthcheck automatic.
**Status**: REQUIRES_HUMAN_APPROVAL
