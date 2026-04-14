# Anthropic Agent Skills Course Review — task-024

## Source Material

Reviewed the Claude Code official plugin marketplace at:
`/root/.claude/plugins/marketplaces/claude-plugins-official/plugins/`

Plugins examined: `agent-sdk-dev`, `skill-creator`, `session-report`, `hookify`,
`code-review`, `feature-dev`, `claude-md-management`, `plugin-dev`

---

## Summary of Available Plugins / Skill Patterns

| Plugin | Type | Key Capability |
|--------|------|----------------|
| `agent-sdk-dev` | Commands + agents | Scaffold + verify Claude Agent SDK apps (Python/TS) |
| `skill-creator` | Skill | Create, eval-loop, and optimize skill descriptions |
| `session-report` | Skill | HTML token/usage report from session transcripts |
| `hookify` | Commands | Create hooks from conversation patterns or instructions |
| `code-review` | Command | Multi-agent parallel PR review with confidence scoring |
| `feature-dev` | Command | 7-phase structured feature development workflow |
| `claude-md-management` | Skills | `revise-claude-md` + `claude-md-improver` (already used) |

---

## Identified Skills / Patterns — Prioritized by Applicability

### 1. `session-report` — Token Observability Dashboard (P2)

**What it does**: Runs `analyze-sessions.mjs` against `~/.claude/projects` transcripts,
generates a self-contained HTML report with: total tokens, cache hit rate, per-project/skill
breakdown, top expensive prompts, subagent token consumption, anomaly narrative.

**Applicability to MAS**:
- Our current observability is `logs/token_log.jsonl` (manual, text-only).
- `session-report` would give us an interactive HTML view without custom tooling.
- Directly addresses token governance goal: "Alerts: token overspend, policy violations."
- Could be wired into `/pm-status` or `/pm-close` to show a weekly token spend summary.

**Gap from current state**: We don't use this skill at all. Installing it would give
token observability with near-zero implementation effort.

**Proposed BL item**: BL-073 — Install `session-report` skill; wire into `/pm-status`
to print last-7-day token summary at session start. P2.

---

### 2. `skill-creator` — Systematic PM Skill Iteration (P2)

**What it does**: End-to-end skill development lifecycle:
1. Draft SKILL.md from user intent
2. Write eval test cases (evals.json)
3. Spawn with-skill + baseline subagents in parallel
4. Grade with assertions + quantitative benchmark
5. Serve eval viewer HTML for human review
6. Iterate based on feedback
7. Optimize trigger description with `run_loop.py`

**Applicability to MAS**:
- Our PM skills (`pm-run`, `pm-close`, `pm-propose`, etc.) were hand-authored with no evals.
- Several have known quality issues (e.g. pm-propose false-positive scan, fixed in task-023).
- `skill-creator` provides a rigorous loop to catch and fix such issues before they hit production.
- The description-optimization step (trigger accuracy) is valuable for skills like `pm-run`
  and `pm-close` which must fire reliably.

**Gap from current state**: Skills authored without evals; no baseline comparisons; no
trigger optimization. `skill-creator` fills all three gaps with a structured workflow.

**Proposed BL item**: BL-074 — Use `skill-creator` to audit and iterate on the 3 highest-usage
PM skills (`pm-run`, `pm-propose`, `pm-close`); run evals, fix weaknesses, optimize descriptions.
project_manager, P2.

---

### 3. `hookify` — Behavior Guard Automation (P3)

**What it does**: Converts a natural-language description of an unwanted behavior into a
hookify markdown config file (`.claude/hookify.*.md`) with:
- Regex patterns to detect the behavior in tool calls
- A warning message to show when triggered
- Instant effect (no restart required)

**Applicability to MAS**:
- Our current guards are in `pre-commit` (git hooks) and CLAUDE.md rules.
- Some CLAUDE.md rules would be better as real-time hooks (e.g., "never commit to develop
  directly", "never use grep -rl on artefacts dir").
- `hookify` could automate creation of these guards from the existing rules.

**Gap from current state**: Behavior guards exist only as prose rules (CLAUDE.md) or git hooks.
`hookify` fills the in-session behavior guard gap.

**Proposed BL item**: BL-075 — Evaluate `hookify` for key MAS safety rules (e.g. no direct
develop commit, no grep -rl on artefacts); create 2-3 hookify rules as proof-of-concept.
project_manager, P3.

---

### 4. Confidence-Scoring Pattern from `code-review` (P2)

**What it does**: The `code-review` plugin scores each issue 0-100 for confidence, then
filters to only present issues above a threshold (80). This prevents low-signal noise from
reviewers drowning out high-signal findings.

**Applicability to MAS**:
- Our Reviewer YAML currently lists all findings without prioritization.
- Reviewer output sometimes generates noise that requires Builder iteration on minor issues.
- Adding a confidence/severity field to Reviewer output format (HIGH/MEDIUM/LOW + score)
  and having Builder only loop on HIGH findings would reduce unnecessary pipeline iterations.

**Gap from current state**: Reviewer produces flat findings list. No filtering by signal quality.

**Proposed BL item**: BL-076 — Add confidence scoring (1-100) to Reviewer YAML output format;
Builder loops only on score >= 80 findings; LOW findings appended to build_notes.md only.
project_manager, P2.

---

### 5. `agent-sdk-dev` — Claude Agent SDK Scaffolding (P3)

**What it does**: Interactive scaffolding of Claude Agent SDK apps (Python/TypeScript):
- Checks for latest SDK version
- Creates project files, .env.example, .gitignore
- Verifier agents check for correct patterns (streaming, permissions, MCP, subagents, sessions)

**Applicability to MAS**:
- Currently our agents are YAML+prompt definitions run by Claude Code.
- As MAS matures (MVP3/4), some agents may be better implemented as proper SDK apps
  (e.g., a persistent ProjectManager daemon that polls queue.json).
- `/new-sdk-app` + verifier agents would give us a clean starting point when we reach that phase.

**Gap from current state**: No SDK apps in the MAS yet — this is a future-phase capability.

**Proposed BL item**: BL-077 — Research: evaluate whether ProjectManager or Task queue processor
should be rebuilt as a Claude Agent SDK app (Python); prototype with `/new-sdk-app`. P3.

---

## Cross-Cutting Patterns (no separate BL item needed)

**Progressive disclosure in SKILL.md** (`skill-creator` doc):
- Skills use 3-level loading: metadata (~100 words always), SKILL.md body (<500 lines on trigger),
  bundled resources (on demand).
- Our PM skills are inline monoliths in `.claude/commands/*.md`.
- For skills exceeding ~200 lines, moving reference content to `references/` subdirs would reduce
  context load per invocation.
- This is a free refactor — no BL item; apply opportunistically during task-skill edits.

**Skill description "push" principle** (`skill-creator` doc):
- Descriptions should be slightly assertive: "use this skill whenever X" not just "skill for X".
- Audit our existing skill descriptions — some may undertrigger.
- Applied inline when editing skill files; no separate BL item.

---

## Summary: Proposed BL Items

| BL ID | Title | Project | Priority |
|-------|-------|---------|----------|
| BL-073 | Install `session-report`; wire into `/pm-status` for 7-day token summary | project_manager | P2 |
| BL-074 | Use `skill-creator` to audit + iterate on `pm-run`, `pm-propose`, `pm-close` | project_manager | P2 |
| BL-075 | Evaluate `hookify` for MAS safety rules (proof-of-concept 2-3 rules) | project_manager | P3 |
| BL-076 | Add confidence scoring to Reviewer YAML; Builder loops on score >= 80 only | project_manager | P2 |
| BL-077 | Research: PM or task-queue as Claude Agent SDK app (Python) | project_manager | P3 |

## [Sonnet]
