# task-034 — Improvement Proposals

## Proposal 1

**Target file**: `tasks/lessons.md` + `.claude/agents/self-improver.yaml`  
**Change**: Add a second research pass to every BL-084-style "explore repo" task. The initial pass from `skills-review.md` identified 7 patterns (BL-085–091); a second deeper pass found 4 more (BL-092–095). Research tasks with large source material should have an explicit "second pass" step to catch items missed in the first scan.  
**Rationale**: The first pass focused on agents and top-level skills. The second pass explored specific SKILL.md files (cost-aware-llm-pipeline, codebase-onboarding, agent-introspection-debugging) that weren't reached in the initial round.  
**Status**: REQUIRES_HUMAN_APPROVAL

---

## Proposal 2

**Target file**: `.claude/commands/pm-run.md`  
**Change**: Add a note in the pipeline execution step: "For research/analysis tasks, require a minimum of 2 exploration rounds before producing the final BL item list. Second round must cover at least 3 skills/files not explored in the first round."  
**Rationale**: BL-092–095 were only found by explicitly going back for a second look. Without this rule, first-pass proposals feel complete but may miss 30–40% of applicable patterns.  
**Status**: REQUIRES_HUMAN_APPROVAL

---

## Proposal 3

**Target file**: `CLAUDE.md` — Architecture/research task Definition of Done  
**Change**: Extend the existing "Architecture/research task Definition of Done" rule to add: "For tasks reviewing an external repo/course: minimum 2 research rounds; second round must fetch SKILL.md / agent source files, not just directory listings."  
**Rationale**: Directory listings (tree view) give names but not content. The missed patterns (BL-092–095) were in SKILL.md files that required a second `WebFetch` call to raw content URLs.  
**Status**: APPROVED
