# Build Notes — task-023

## Summary
Updated the pm-propose scan logic to use a line-anchored ERE grep pattern that matches only
the `**Status**:` field line in improvement_proposals.md files — preventing false positives
from body text or Tester assertion files.

## Files Changed

### `.claude/commands/pm-propose.md` (Step 1)
- Replaced: `find artefacts -name "improvement_proposals.md"` followed by per-file read
- With: pre-filter `find artefacts -name "improvement_proposals.md" | xargs grep -lE "^\*\*Status\*\*: REQUIRES_HUMAN_APPROVAL"`
- Effect: skip files where all proposals are resolved (no REQUIRES_HUMAN_APPROVAL Status lines)

### `CLAUDE.md` (section 6b)
- Replaced old pattern: `grep -l "REQUIRES_HUMAN_APPROVAL"` (too broad)
- Replaced false-positive warning (now unnecessary — anchor prevents body-text matches)
- With: `grep -lE "^\*\*Status\*\*: REQUIRES_HUMAN_APPROVAL"` + explanation of `^` anchor

## Files NOT Changed
- `.claude/agents/self-improver.yaml` — already writes `**Status**: REQUIRES_HUMAN_APPROVAL` correctly

## Cross-file Consistency
All three files agree on the status value format: `**Status**: REQUIRES_HUMAN_APPROVAL`

## Grep Pattern Choice
`grep -lE "^\*\*Status\*\*: REQUIRES_HUMAN_APPROVAL"`:
- `-l`: list files only (don't print matching lines)
- `-E`: extended regex
- `^`: anchored to start of line — prevents body-text and test-assertion false positives
- `\*\*Status\*\*`: matches literal `**Status**` (asterisks escaped in ERE)

## [Sonnet]
