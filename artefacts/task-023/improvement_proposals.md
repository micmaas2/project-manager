# Improvement Proposals — task-023

## Proposal 1
**Target file**: `.claude/agents/self-improver.yaml`
**Change**: Add a note in the output section clarifying that the Status field must appear on its own
line (not embedded in body text) for the grep scan to work correctly:
```yaml
  # IMPORTANT: **Status** must be on its own line — the pm-propose scan uses
  # grep -lE "^\*\*Status\*\*:" to match Status lines only, not body text.
```
**Rationale**: Without this note, a future author editing the proposal template might embed
the Status value in a multi-line Change block, silently breaking the scan.
**Status**: REQUIRES_HUMAN_APPROVAL
