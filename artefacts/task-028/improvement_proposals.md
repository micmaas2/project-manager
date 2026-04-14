# Improvement Proposals — task-028
**Task**: Token spend dashboard in /pm-status (BL-052)
**Agent**: SelfImprover [Haiku]
**Date**: 2026-04-14

---

## Proposal 1

**Target file**: `logs/token_log.jsonl`
**Change**: All future agent runs should write a token log entry per agent invocation (not just at the ProjectManager level). Pattern:
```json
{"timestamp":"ISO8601","agent":"Builder","task_id":"task-028","action":"token_log","token_estimate":8000}
```
**Rationale**: The current log has only 1 entry from `task-001` (ProjectManager-level). The dashboard is most useful when each sub-agent (Builder, Reviewer, Tester, etc.) logs its own token estimate. This would reveal which agent in the pipeline is the biggest consumer.
**Status**: APPROVED

---

No other significant patterns found. This was a straightforward script-writing task with no unusual failure modes.
