# Build Notes — task-060 (BL-124)

**Agent**: Builder [Sonnet]
**Date**: 2026-05-05

## Change Applied
`.claude/agents/builder.yaml` Reviewer Confidence Threshold section: added verbatim M-1 definition sentence.

**Added line**: `Definition: confidence = certainty the finding is a real issue (not a false positive).`

## Notes
- Inserted after the `confidence < 80` line, before the "This prevents churn" closing sentence.
- YAML validates cleanly.
