# task-033 — Improvement Proposals

## Proposal 1

**Target file**: `tasks/lessons.md`
**Change**: Add lesson: "Obsidian vault sync issues (missing files) should be triaged by checking Pi4 vault directly via SSH before assuming n8n failure. If files are on Pi4 but not in app → Obsidian sync issue; fix by deleting + re-adding vault in app."
**Rationale**: This was the root cause of a false n8n debug task. A triage checklist saves time in future.
**Status**: REQUIRES_HUMAN_APPROVAL
