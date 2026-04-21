# task-043 Build Notes

**Agent**: Builder [Sonnet]  
**Date**: 2026-04-19  
**Task**: Claude Code skills investigation — cross-project fit

---

## Research Process

### Round 1 Summary

**Sources scanned**:
1. `/root/.claude/plugins/marketplaces/claude-plugins-official/plugins/` — 32 plugin directories
2. `/opt/claude/project_manager/.claude/commands/` — 7 PM skill files
3. System-reminder listing — 19 skills available in session

**Method**: `ls` of marketplace + `head -5 README.md` for each plugin. Produced 34-row inventory table with initial fit impressions.

**Key observation**: Many plugins are language servers (clangd, csharp, gopls, jdtls, kotlin, lua, php, ruby, rust, swift, typescript, pyright) that are LOW fit because no managed project uses those languages as a primary development language.

### Round 2 Deep-Dives

Four skills selected for full file reads:

1. **`security-guidance`** — Read full Python hook script (310 lines) + hooks.json config. Discovered concrete security patterns catalogue and blocking mechanism (exit code 2). Confirmed zero external dependencies.

2. **`claude-code-setup` / `claude-automation-recommender`** — Read full SKILL.md (250+ lines) + all reference files (hooks-patterns.md, subagent-templates.md, skills-reference.md, mcp-servers.md, plugins-reference.md). Discovered detailed decision tables cross-referencing codebase signals to automation recommendations.

3. **`skill-creator`** — Read full SKILL.md (300+ lines). Discovered eval infrastructure (Python scripts: run_eval.py, run_loop.py, generate_review.py, HTML viewer). Key insight: existing pm-* skills have no formal evals — this is a gap skill-creator directly addresses.

4. **`pr-review-toolkit`** — Read full README.md. Discovered 6-agent bundle with 4 new review dimensions not in PM's current pipeline (comment accuracy, test coverage gap rating, silent failure detection, type design). Noted `silent-failure-hunter` is highly relevant to PM's Python agents.

### Project Context Scan

Read CLAUDE.md for CCAS and pi-homelab to understand tech stacks:
- **CCAS**: 6 Ansible repos + Jenkins; ~87% complete architectural plan in progress
- **pi-homelab**: Pi 4 (Docker: HA, n8n, NPM, UniFi, MAS) + Pi 5 (Ollama); Debian 13
- **pensieve**: n8n workflow library + templates
- **MAS**: FastAPI + PostgreSQL + React at mas.femic.nl

---

## BL Items Added

| BL ID | Title | Location in backlog.md |
|---|---|---|
| BL-101 | Install security-guidance PreToolUse hook | Added to tasks/backlog.md |
| BL-102 | Run claude-automation-recommender at project onboarding | Added to tasks/backlog.md |
| BL-103 | Add skill-creator evals to pm-* skill library | Added to tasks/backlog.md |

---

## Acceptance Criteria Verification

1. **Minimum 2 research rounds**: ✅ Round 1 (inventory, 34 skills) + Round 2 (4 deep-dives with full file reads)
2. **≥5 skills evaluated with fit rating**: ✅ 15 skills in evaluation summary table with high/medium/low ratings and rationale
3. **Top 3 candidates with per-project rationale**: ✅ security-guidance, claude-automation-recommender, skill-creator — each with rationale for PM, MAS, pensieve, CCAS, pi-homelab, genealogie, performance_HPT
4. **Each top-3 registered as BL item**: ✅ BL-101, BL-102, BL-103 added to tasks/backlog.md

---

## Notable Findings

- **security-guidance** is the highest-impact immediate win: production-ready, zero dependencies, blocks real vulnerability classes relevant to every active project.
- **claude-automation-recommender** is "free" (no install, read-only) and would give each project a tailored automation roadmap — valuable to run at start of any new project session.
- **skill-creator** reveals a gap: the 7 existing pm-* skills have no formal evals, meaning their triggering reliability has never been measured.
- `pr-review-toolkit`'s `silent-failure-hunter` agent is particularly relevant for PM — Python agents have multiple try/except paths that may swallow errors silently.
- Language server plugins (10+ entries) are low-fit for all managed projects and should not be prioritized.

---

## Fix Loop (post-review)

**Triggered by**: Reviewer F-3 (conf 80), CQR F-2 (conf 85), CQR F-3 (conf 98)

### Fix 1 — BLOCKING: BL-101/102/103 Epic column corrected (CQR F-3, conf 98)

**File**: `tasks/backlog.md`  
**Issue**: BL-101, BL-102, BL-103 rows had `EPIC-003` in the Epic column. New backlog items not yet associated with an epic must use `—`.  
**Fix applied**: Changed column 2 from `EPIC-003` to `—` for all three rows.  
**Rationale**: These items were surfaced by task-043 research, not originally scoped under EPIC-003. Assigning an epic requires deliberate PM decision, not automatic inheritance.

### Fix 2: Top 3 "why over alternatives" sentences added (Reviewer F-3, CQR F-2)

**File**: `artefacts/task-043/research_report.md`  
**Issue**: Top 3 section lacked rationale for why each candidate was chosen over equally-rated alternatives. Reviewer and CQR both flagged this as a gap in decision traceability.  
**Fix applied**: Added one "Why over alternatives" sentence per Top 3 entry:
- `security-guidance` — chosen over `pr-review-toolkit`: blocks vulnerabilities pre-commit vs. post-fact review; the PreToolUse blocking mechanism is unique.
- `claude-automation-recommender` — no direct competitor; zero-install read-only design makes it the safe first step before any other tool install.
- `skill-creator` — chosen over `pr-review-toolkit`: addresses the PM-specific gap of missing formal evals on pm-* skills; `pr-review-toolkit` cannot fill that gap.
