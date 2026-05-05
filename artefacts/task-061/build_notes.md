# Build Notes — task-061 (BL-126)

**Agent**: Builder [Sonnet]
**Date**: 2026-05-05

## Change Applied
`.claude/agents/manager.yaml` policy.allowed_tools: added `Bash`.

**Before**: allowed_tools: Read, Write, Edit, Glob, Agent
**After**: allowed_tools: Read, Write, Edit, Glob, Agent, Bash

require_human_approval remains true — no additional change needed.

## Notes
- Batched with task-059 (same file). Both changes applied in the same feature branch.
- YAML validates cleanly.
