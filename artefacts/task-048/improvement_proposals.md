# Improvement Proposals: task-048

**Agent**: SelfImprover [Haiku]  
**Date**: 2026-04-28  
**Task**: task-048 — automation-recommender cross-project scan

---

## Proposal 1
**Target file**: `.claude/commands/pm-run.md` (ExitPlanMode mid-skill recovery)  
**Change**: Document the ExitPlanMode mid-skill recovery as a first-class procedural step in pm-run: when plan mode activates unexpectedly, the skill must (1) write a checkpoint plan file with remaining pipeline stages + current task_id + artefact_path, (2) call ExitPlanMode, (3) resume after approval. Add an explicit numbered step to pm-run covering this recovery path so it is not left to improvisation.  
**Rationale**: task-048 required manual ExitPlanMode recovery when plan mode activated at skill start. CLAUDE.md documents the pattern but pm-run has no explicit recovery step — requiring the executor to derive it from general guidance. Making it explicit in the skill reduces friction for future runs.  
**Status**: APPROVED

---

## Proposal 2
**Target file**: `CLAUDE.md` — Doc stage file ownership rule  
**Change**: Add enforcement note to the "Doc stage file ownership" rule: "If docs-readme-writer does not confirm README.md was modified in its output, the parent agent must apply the README update directly before committing." This makes the parent's fallback responsibility explicit rather than relying on agent self-report.  
**Rationale**: task-048 docs-readme-writer committed all other artefacts but skipped README.md; the gap was only caught by checking the commit diff. The CLAUDE.md ownership rule says docs-readme-writer owns README.md but doesn't specify what the parent should do if the agent fails to deliver. An explicit fallback instruction prevents silent omissions.  
**Status**: APPROVED

---

## Proposal 3
**Target file**: `CLAUDE.md` — security BL description standards  
**Change**: Add a rule: "When registering a BL item in category Hook or MCP that involves credential handling or OAuth: the description must include (a) hook type (PreToolUse/PostToolUse), (b) what the hook emits on match (path+line only — never matched text), (c) OAuth scope if applicable. Reviewer must verify these fields before marking the BL item ready."  
**Rationale**: task-048 code-quality-reviewer caught two security description gaps at ≥85 confidence (BL-107 hook type, BL-111 OAuth scope), requiring a Builder loop after Reviewer approval. Encoding the required fields as a standard would shift this check to BL registration time and eliminate the loop.  
**Status**: APPROVED
