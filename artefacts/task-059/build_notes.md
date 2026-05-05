# Build Notes — task-059 (BL-122)

**Agent**: Builder [Sonnet]
**Date**: 2026-05-05

## Change Applied
`.claude/agents/manager.yaml` line 68: replaced Agent tool invocation with Skill tool instruction.

**Before**: `invoke revise-claude-md (built-in Agent tool, subagent_type=claude-md-management:revise-claude-md)`
**After**: `invoke revise-claude-md via the Skill tool (skill name: revise-claude-md) — do NOT use Agent tool or subagent_type for claude-md-management:* skills`

## Notes
- task-061 (BL-126: add Bash to manager.yaml allowed_tools) batched into this same pipeline run since both touch manager.yaml. See artefacts/task-061/build_notes.md.
- YAML validates cleanly (python3 yaml.safe_load).
