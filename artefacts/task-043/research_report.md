# task-043: Claude Code Skills Investigation — Cross-Project Fit

**Date**: 2026-04-19  
**Agent**: Builder [Sonnet]  
**Status**: Complete

---

## Round 1: Skill Inventory

### Sources Surveyed
1. Official plugin marketplace: `/root/.claude/plugins/marketplaces/claude-plugins-official/plugins/`
2. PM project commands: `/opt/claude/project_manager/.claude/commands/`
3. System-reminder skills available in this session

### Round 1 Inventory Table

| Skill / Plugin | Source | Description | Initial Fit Impression |
|---|---|---|---|
| `code-review` | Marketplace | Automated PR review via 4 parallel agents; confidence scoring with 80-threshold filter | HIGH — already mirrors PM's own review pipeline |
| `feature-dev` | Marketplace | 7-phase guided feature development: discovery → exploration → questions → architecture → build → review → summary | HIGH — structured workflow fits all active projects |
| `security-guidance` | Marketplace | PreToolUse hook; warns on file edits matching security patterns (eval, pickle, GitHub Actions injection, innerHTML, etc.) | HIGH — MAS (FastAPI), pensieve (n8n), CCAS (Ansible) all benefit |
| `hookify` | Marketplace | Create custom regex-based hooks from plain English instructions; no-code hook authoring | HIGH — would accelerate PM hook authoring |
| `pr-review-toolkit` | Marketplace | 6 specialized review agents: comment-analyzer, pr-test-analyzer, silent-failure-hunter, type-design-analyzer, code-reviewer, code-simplifier | HIGH — complements existing Reviewer pipeline |
| `claude-code-setup` / `claude-automation-recommender` | Marketplace | Read-only skill; scans codebase and recommends top hooks, skills, MCP servers, subagents, slash commands per category | HIGH — excellent for onboarding each managed project |
| `session-report` | Marketplace | Generates HTML token/cost usage report from `~/.claude/projects` transcripts; analyzes waste, cache hits, top prompts | MEDIUM — useful for PM token governance but niche |
| `skill-creator` | Marketplace | Full skill lifecycle: intent → draft → eval → iterate; includes quantitative benchmarking and description optimizer | HIGH — directly accelerates PM skill library development |
| `mcp-server-dev` | Marketplace | 3-skill bundle: design and build MCP servers (remote HTTP, MCP app with UI widgets, MCPB local bundles) | MEDIUM — relevant for MAS/pensieve API integration work |
| `agent-sdk-dev` | Marketplace | Interactive new-SDK-app scaffolding + best-practice verifier for Python/TypeScript Anthropic SDK apps | MEDIUM — relevant for PM agent code, MAS backend |
| `commit-commands` | Marketplace | `/commit`, `/commit-push-pr`, `/clean_gone` — streamlined git workflows | MEDIUM — useful but PM already has git hooks handling commit format |
| `code-simplifier` | Marketplace | Post-edit code refactoring agent; reduces complexity while preserving functionality | MEDIUM — useful during Builder phase |
| `pyright-lsp` | Marketplace | Python static type-checking language server | LOW for PM (infrastructure-focused); MEDIUM for MAS |
| `typescript-lsp` | Marketplace | TypeScript/JS language server | LOW for PM; MEDIUM for MAS React frontend |
| `frontend-design` | Marketplace | Production-grade UI generation; avoids generic AI aesthetics | LOW for PM; MEDIUM for MAS frontend |
| `mcp-server-dev:build-mcp-server` | Marketplace | Entry point for MCP server design/build workflow | MEDIUM |
| `ralph-loop` | Marketplace | Ralph Wiggum iterative self-referential AI development loops | LOW — experimental/niche |
| `math-olympiad` | Marketplace | Competition math solver with adversarial verification | LOW — not applicable |
| `playground` | Marketplace | Creates interactive HTML playgrounds from scratch | LOW — not applicable |
| `clangd-lsp` / `csharp-lsp` / `gopls-lsp` / etc. | Marketplace | Language servers for C/C++, C#, Go, Java, Kotlin, Lua, PHP, Ruby, Rust, Swift | LOW — none of managed projects use these languages |
| `learning-output-style` / `explanatory-output-style` | Marketplace | Session-start hooks that add explanatory/learning mode | LOW — affects UX style, not functionality |
| `plugin-dev` | Marketplace | Toolkit for building Claude Code plugins | LOW — meta-tooling for marketplace contribution |
| `pm-start`, `pm-run`, `pm-status`, etc. | PM commands | Existing PM orchestration skills | ALREADY IN USE |
| `claude-md-management:revise-claude-md` | Plugin | Session-end CLAUDE.md updater | ALREADY IN USE |
| `init` | System | Initialize new CLAUDE.md for a project | MEDIUM — useful during project onboarding |
| `review` | System | PR review skill | MEDIUM — supplements existing Reviewer agent |
| `security-review` | System | Security review of pending branch changes | HIGH — complements Security agent |
| `claude-api` | System | Claude API/SDK app building and debugging | MEDIUM — relevant for MAS and PM agent code |
| `simplify` | System | Review changed code for reuse, quality, efficiency | MEDIUM — complements Builder pipeline |
| `update-config` | System | Configure Claude Code via settings.json; automates hook/permission management | MEDIUM — ops utility |
| `fewer-permission-prompts` | System | Scans transcripts and adds allowlist to reduce prompts | LOW — QoL improvement |
| `loop` | System | Run a prompt/command on recurring interval | MEDIUM — could automate PM polling tasks |
| `schedule` | System | Create/manage scheduled remote agents on cron | MEDIUM — relevant for PM task automation |

---

## Round 2: Deep-Dive Analysis

### Deep-Dive 1: `security-guidance` (Marketplace Hook Plugin)

**Files read**: `hooks/security_reminder_hook.py`, `hooks/hooks.json`

**How it works**: A `PreToolUse` Python hook that intercepts `Edit`, `Write`, and `MultiEdit` tool calls. It scans the file path and new content against a catalogue of security patterns. On a match, it emits a warning to stderr and **blocks** the tool call (exit code 2). State is session-scoped — each warning shown only once per session.

**Security patterns covered**:
- GitHub Actions workflow injection (`${{ github.event.* }}` in `run:` commands)
- `child_process.exec()` — command injection
- `new Function()` — code injection
- `eval()` — code injection
- `dangerouslySetInnerHTML` — XSS
- `document.write()` — XSS
- `.innerHTML =` — XSS
- `pickle` — arbitrary code execution
- `os.system()` — shell injection

**Per-project fit**:
| Project | Fit | Rationale |
|---|---|---|
| `project_manager` | HIGH | Python agents use Bash/subprocess calls; `os.system` warning directly relevant |
| `pi-homelab` (MAS) | HIGH | FastAPI + React stack; `eval`, `innerHTML`, `dangerouslySetInnerHTML` all patterns in React code; GitHub Actions in n8n workflows |
| `pensieve` | HIGH | n8n workflow JSON uses `eval` in Code nodes; also has GitHub Actions |
| `CCAS` | MEDIUM | Ansible/YAML — patterns less common but Jenkins pipelines use shell script |
| `genealogie` | LOW | Minimal active dev |
| `performance_HPT` | MEDIUM | Python scripts; `os.system` and `pickle` warnings applicable |

**Installation**: Requires adding hook config to project `.claude/settings.json`. Pure Python stdlib — no dependencies.

**Verdict**: HIGH fit for PM, MAS, pensieve. Quick install, zero dependencies, blocks real vulnerabilities at edit time.

---

### Deep-Dive 2: `claude-code-setup` / `claude-automation-recommender` (Marketplace Skill)

**Files read**: Full `SKILL.md`, all reference files (hooks-patterns, subagent-templates, skills-reference, mcp-servers, plugins-reference)

**How it works**: A read-only analysis skill. Phases: (1) scan codebase via `ls`, `cat package.json`, detect framework/language/libs; (2) cross-reference against decision tables for MCP servers, hooks, skills, subagents, plugins; (3) emit ranked report of top 1–2 recommendations per category with specific rationale tied to detected signals.

**What it recommends** (decision tables extracted):
- MCP Servers: context7 (docs lookup), Playwright (frontend testing), GitHub MCP, Supabase, Linear, etc.
- Skills: feature-dev, commit-commands, frontend-design, api-doc, gen-test
- Hooks: auto-format/lint on save, block `.env` edits, type-check on edit
- Subagents: code-reviewer, security-reviewer, api-documenter, test-writer
- Plugins: anthropic-agent-skills, frontend-design, mcp-builder

**Per-project fit**:
| Project | Fit | Rationale |
|---|---|---|
| `project_manager` | HIGH | Multi-agent YAML system — would surface Ansible/Python hooks, validate existing setup, identify gaps in hook coverage |
| `pi-homelab` | HIGH | Docker + HA + n8n stack — would recommend Playwright MCP for HA frontend testing, GitHub MCP, Docker MCP |
| `CCAS` | HIGH | 6 Ansible repos — would surface Jenkins pipeline hooks, security-reviewer subagent for Ansible playbooks |
| `pensieve` | HIGH | n8n workflows — would recommend context7 for docs, GitHub MCP |
| `MAS` | HIGH | FastAPI + PostgreSQL + React — would surface Supabase/DB MCP, pyright-lsp, frontend-design |
| `performance_HPT` | MEDIUM | Python-only — would surface pyright-lsp, gen-test skill, testing hooks |
| `genealogie` | MEDIUM | Light activity — one-time setup recommendation still valuable |

**Key value**: Run once per project to get a tailored optimization report. Particularly valuable as new projects onboard.

**Verdict**: HIGH fit across all projects. Directly addresses the "what automations should each project have?" question that currently requires manual analysis.

---

### Deep-Dive 3: `skill-creator` (Marketplace Skill)

**Files read**: Full `SKILL.md`, agents structure, eval scripts

**How it works**: Full skill development lifecycle skill. Steps: (1) capture intent by interviewing user; (2) write SKILL.md draft following 3-level progressive disclosure architecture; (3) create test cases (skip for subjective outputs); (4) run evals in background via `run_eval.py` / `run_loop.py`; (5) display results to user via `generate_review.py` + HTML viewer; (6) rewrite skill based on feedback; (7) iterate; (8) run description optimizer. Includes quantitative benchmarking with variance analysis.

**Architecture guidance it provides**:
- Skill anatomy: `SKILL.md` + optional `scripts/`, `references/`, `assets/`
- Metadata level (~100 words always in context), body (<500 lines ideal), bundled resources (unlimited)
- Invocation control: `disable-model-invocation: true` (user-only), `user-invocable: false` (Claude-only)
- Description writing: "pushy" descriptions to combat Claude's undertriggering tendency

**Per-project fit**:
| Project | Fit | Rationale |
|---|---|---|
| `project_manager` | HIGH | PM already has 7 skills (`pm-start`, `pm-run`, etc.) but they lack formal evals. skill-creator would add quantitative benchmarking to improve triggering accuracy of pm-* skills and help build new skills faster |
| `pi-homelab` | MEDIUM | Could create HA-specific skills (e.g. `/ha-deploy`, `/n8n-import`) but no current skill library to improve |
| `CCAS` | MEDIUM | Could create `/ansible-lint`, `/deploy-playbook` skills — high repetition tasks |
| `pensieve` | LOW-MEDIUM | Early stage project; skill authoring premature |
| `MAS` | MEDIUM | Could formalize `/deploy-mas`, `/run-migrations` as skills |

**Key value for PM**: The existing pm-* skills were authored without formal evals. skill-creator + `run_eval.py` could add regression tests to ensure `/pm-run` triggers correctly and doesn't skip steps. Also directly used when implementing the top-3 recommendations from this report.

**Verdict**: HIGH fit for project_manager specifically (existing skill library to improve), MEDIUM for other projects.

---

### Deep-Dive 4: `pr-review-toolkit` (Marketplace — 6-agent bundle)

**Files read**: Full `README.md`

**How it works**: 6 specialized review subagents invoked by natural language or explicitly:
- `comment-analyzer` — comment accuracy and documentation rot
- `pr-test-analyzer` — test coverage quality (rates gaps 1-10)
- `silent-failure-hunter` — catch blocks, missing error logging, inappropriate fallbacks
- `type-design-analyzer` — type encapsulation, invariant expression (1-10 ratings)
- `code-reviewer` — CLAUDE.md compliance, bugs, quality (0-100 confidence)
- `code-simplifier` — complexity reduction, readability

**Relation to existing PM pipeline**: PM already runs `Reviewer (YAML)` + `code-quality-reviewer (built-in)` in parallel. This toolkit adds 4 new dimensions not currently covered: comment accuracy, test coverage gap rating, silent failure detection, and type design quality.

**Per-project fit**:
| Project | Fit | Rationale |
|---|---|---|
| `project_manager` | HIGH | `silent-failure-hunter` directly addresses Python agent error handling; `pr-test-analyzer` would catch test gaps in new skills |
| `MAS` | HIGH | FastAPI + React: `type-design-analyzer` for Python Pydantic models and TypeScript types; `silent-failure-hunter` for API error handling; `comment-analyzer` for API docstrings |
| `CCAS` | MEDIUM | Ansible YAML — most agents more relevant to application code |
| `pensieve` | MEDIUM | n8n Python scripts benefit from `silent-failure-hunter` and `pr-test-analyzer` |
| `pi-homelab` | LOW | Config files and Docker compose — code review agents less applicable |

**Verdict**: HIGH fit for PM and MAS. Extends the current review pipeline with 4 new quality dimensions.

---

## Evaluation Summary Table

| Skill | Overall Fit | Best-Fit Projects | Rationale |
|---|---|---|---|
| `security-guidance` (hook) | HIGH | PM, MAS, pensieve | Blocks real vulnerabilities at edit time; patterns match actual tech stacks |
| `claude-code-setup` | HIGH | ALL | Codebase-specific automation recommendations; valuable at project onboarding |
| `skill-creator` | HIGH | project_manager | Adds evals and description optimization to existing pm-* skill library |
| `pr-review-toolkit` | HIGH | PM, MAS | 4 new review dimensions not in current pipeline |
| `code-review` | HIGH | ALL | Mirrors PM's own review logic; useful on all GitHub-tracked projects |
| `feature-dev` | HIGH | MAS, CCAS | 7-phase structured workflow prevents rushing into code on complex features |
| `hookify` | MEDIUM | project_manager | Accelerates hook authoring for PM governance rules |
| `session-report` | MEDIUM | project_manager | Token governance; identifies cost outliers across agents |
| `mcp-server-dev` | MEDIUM | MAS, pensieve | Formalizes API/integration layer development |
| `agent-sdk-dev` | MEDIUM | project_manager, MAS | Scaffolding for new Anthropic SDK integrations |
| `commit-commands` | MEDIUM | ALL | Reduces friction but PM's commit hooks already enforce format |
| `simplify` (built-in) | MEDIUM | ALL | Useful post-Builder refactor pass |
| `security-review` (built-in) | HIGH | ALL | Branch-level security audit; complements Security agent |
| `pyright-lsp` | LOW-MEDIUM | MAS | Only useful if MAS Python dev happens in this environment |
| `frontend-design` | LOW | MAS | MAS has a React frontend but PM sessions rarely touch it |
| Language servers (others) | LOW | None currently | No C#, Go, Java, Rust, etc. projects active |

---

## Top 3 Recommendations

### #1: `security-guidance` — Install as PreToolUse hook

**What it is**: A production-ready Python hook that blocks dangerous code patterns (eval, innerHTML, pickle, os.system, GitHub Actions injection) at edit time.

**Per-project rationale**:
- **project_manager**: PM Python agents write Bash subprocess calls and use file I/O. `os.system` warning prevents shell injection in generated scripts. Aligns with PM's existing security checklist.
- **MAS** (pi4): FastAPI backend + React frontend. `dangerouslySetInnerHTML`, `eval`, `innerHTML` patterns directly relevant. Also covers GitHub Actions workflows if/when added to MAS repo.
- **pensieve**: n8n uses Code nodes with `eval` style JavaScript. GitHub Actions injection pattern applies to any CI added.
- **CCAS**: Jenkins pipelines use shell scripts; `os.system` pattern applicable to Python tooling in ccas-main.
- **pi-homelab**: Lower priority (config-heavy repo), but Docker + bash scripts present.

**Effort to adopt**: Copy `hooks/` dir + register in `.claude/settings.json`. ~30 min per project.

**Why over alternatives**: Chosen over `pr-review-toolkit` (also HIGH for PM) because `security-guidance` acts as a zero-dependency PreToolUse guard that prevents vulnerabilities from entering the codebase at all, rather than catching them in review after the fact — the blocking mechanism adds a control layer that no review-phase tool can replicate.

**BL item**: Register for project_manager first, then expand to MAS and pensieve.

---

### #2: `claude-code-setup` (`claude-automation-recommender`) — Run at project onboarding

**What it is**: Read-only codebase scan that produces a ranked list of hooks, skills, MCP servers, subagents, and plugins tailored to detected tech stack.

**Per-project rationale**:
- **project_manager**: PM has 7 skills and an agent pipeline but has never been scanned for recommended MCP servers or hook gaps. Would surface database/GitHub MCP recommendations and validate hook coverage.
- **CCAS**: 6-repo Ansible workspace with Jenkins. Scan would surface Ansible-lint hooks, security-reviewer subagent for playbooks, GitHub MCP for 6-repo PR workflow.
- **MAS**: FastAPI + PostgreSQL + React. Would surface Playwright MCP (API testing), pyright-lsp, Supabase/DB MCP, and custom `deploy-mas` skill.
- **pi-homelab**: Docker + HA + n8n. Would surface Docker MCP, context7 for HA YAML docs, GitHub MCP.
- **pensieve**: Early-stage n8n workflow repo. First-time scan would establish automation baseline before any significant dev work begins.
- **genealogie** / **performance_HPT**: Low-activity projects still benefit from a one-time scan to identify quick wins.

**Effort to adopt**: Zero install — it is a read-only skill invoked via natural language ("recommend automations for this project"). Run at the start of a session for any project.

**Why over alternatives**: No direct competitor at this category — uniquely positioned as a read-only cross-project onboarding scanner. Its zero-install, non-mutating design means it can be run safely on any project at any time with no side effects, making it the natural first step before installing any hook or skill.

**BL item**: Add as a step to the PM project onboarding procedure in CLAUDE.md.

---

### #3: `skill-creator` — Improve pm-* skill library quality

**What it is**: Full skill development lifecycle tool with automated eval runs, quantitative benchmarking, and description optimization.

**Per-project rationale**:
- **project_manager**: The 7 existing pm-* skills (`pm-start`, `pm-run`, `pm-status`, `pm-plan`, `pm-propose`, `pm-close`, `pm-lessons`) were written without formal evals. skill-creator would: (a) add test case suites for each skill; (b) run `run_eval.py` to measure triggering accuracy; (c) use the description optimizer to ensure skills trigger reliably. Directly reduces the "skill doesn't fire when expected" class of PM failures.
- **CCAS**: High-repetition Ansible tasks (lint, deploy, playbook run) are prime candidates for custom skills. skill-creator provides the scaffolding and eval framework to build and validate them.
- **MAS**: `/deploy-mas`, `/run-migrations`, `/rotate-secrets` are recurring operations that could be formalized as skills. skill-creator provides the workflow to make them robust.
- **All projects**: As each project is onboarded, skill-creator provides the standard process for creating project-specific skills.

**Effort to adopt**: Invoke via system-reminder (`skill-creator` already listed as available). No installation required.

**Why over alternatives**: Chosen over `pr-review-toolkit` (also HIGH for PM) because `skill-creator` addresses a gap unique to PM — the 7 existing pm-* skills have no formal evals. `pr-review-toolkit` improves code review quality but cannot fill the eval-and-description-optimization gap that causes pm-* skills to undertrigger or skip steps. Both are valuable but `skill-creator` solves the higher-priority PM-specific deficiency.

**BL item**: Start with pm-* skill eval coverage; expand to CCAS and MAS custom skills.

---

## Top 3 → BL Items

| BL ID | Title | Project | Description |
|---|---|---|---|
| BL-101 | Install security-guidance PreToolUse hook | project_manager | Install the official security-guidance plugin hook in project_manager (and subsequently MAS, pensieve). Blocks eval/os.system/innerHTML/pickle/GHA-injection patterns at edit time. Effort: ~30 min per project. |
| BL-102 | Run claude-automation-recommender at project onboarding | project_manager | Add claude-code-setup (claude-automation-recommender) scan as a mandatory step in PM project onboarding procedure. Run for each managed project to surface top hooks/MCP/skills/subagent recommendations. |
| BL-103 | Add skill-creator evals to pm-* skill library | project_manager | Use skill-creator to add formal eval test suites and description optimization to all 7 pm-* skills. Reduces triggering failures; establishes eval baseline for future skill authoring. |
