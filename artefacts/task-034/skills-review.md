# task-034 — Skills Review: Claude Code Optimization Repository

**Repo**: https://github.com/affaan-m/everything-claude-code  
**Reviewed**: 2026-04-16  
**Reviewer**: Builder (Sonnet)

---

## 1. Repo Inventory Summary

| Component | Count | Description |
|---|---|---|
| Agents | 48 | Specialized subagents (language reviewers, build resolvers, orchestrators) |
| Skills | 183+ | Workflow definitions by domain and stack |
| Commands | 79 | Slash-command shims (migrating to skills-first) |
| Rules | ~10 dirs | Always-follow guidelines by language |
| Hooks | 1 config | `hooks.json` with 5 event types |

**Key agent categories**:
- Language-specific reviewers: go, python, typescript, java, kotlin, rust, cpp, csharp, flutter, dart
- Build resolvers: go, java, kotlin, rust, cpp, dart, pytorch
- Orchestrators: planner, chief-of-staff, loop-operator, harness-optimizer
- Quality/security: code-reviewer, security-reviewer, silent-failure-hunter, refactor-cleaner
- Specialized: a11y-architect, seo-specialist, performance-optimizer, tdd-guide

**Key skill categories**:
- Learning: continuous-learning-v2, agent-eval, agent-introspection-debugging
- Token/cost: context-budget, cost-aware-llm-pipeline, ecc-tools-cost-audit
- Autonomy: autonomous-loops, autonomous-agent-harness, continuous-agent-loop
- Stack-specific: django, golang, docker, git-workflow, github-ops

---

## 2. Applicable Patterns — Ranked by Impact

### Pattern 1: Continuous Learning v2 — Instinct Model with Confidence Scoring
**Fit**: Direct upgrade to our SelfImprover + lessons.md system  
**What it does**: Transforms session observations into "instincts" — atomic learned behaviors with:
- Confidence score (0.3–0.9)
- Domain tag (code-style, testing, git, workflow)
- Trigger + action pair
- Project-scoped vs global scope (prevents cross-project contamination)
- Auto-promotion criteria: appears in 2+ projects with avg confidence ≥0.8

**vs. our current system**: Our `lessons.md` is an append-only table with no confidence, no scope, no promotion criteria. Lessons accumulate without pruning. The instinct model adds structure that enables automated curation.

**Applicable elements**:
- Confidence scoring on SelfImprover proposals
- Project-scoped lessons (separate `lessons-project_manager.md`, `lessons-pensieve.md`)
- Promotion criteria for elevating project lessons to CLAUDE.md
- `/instinct-status` equivalent: a command to show high-confidence lessons only

**Proposed BL item**: BL-085 — Upgrade SelfImprover to instinct model: add confidence field + project scope to lessons.md entries; add promotion criteria to CLAUDE.md

---

### Pattern 2: Context Budget — MCP Server Token Accounting
**Fit**: Directly extends our task-035 token reduction work  
**What it does**: Systematic 4-phase audit:
1. Inventory all components (agents, skills, rules, MCP servers, CLAUDE.md) with token estimates
2. Classify: always/sometimes/rarely needed
3. Detect: bloated descriptions (>30 words in frontmatter), redundant components, heavy agents (>200 lines)
4. Report: prioritized optimization roadmap with savings estimate

**Key insight not in our rewrite-plan.md**: "MCP servers are the largest lever — each tool schema costs ~500 tokens; a 30-tool server costs more than all your skills combined." Our task-026/task-035 analysis focused on CLAUDE.md sections and agent YAMLs but did not audit MCP server overhead.

**Second insight**: Agent frontmatter description >30 words loads into every Task tool invocation. Our current agents should be checked against this threshold.

**Proposed BL item**: BL-086 — Context budget audit pass: measure MCP server tool schema overhead + agent frontmatter word counts; add findings to task-035 rewrite scope if significant

---

### Pattern 3: Agent Eval Harness — Benchmarking Pipeline Stage Quality
**Fit**: Enables data-driven validation of our pipeline stages  
**What it does**:
- Evaluates agent output quality across: pass rate, cost, execution time, consistency
- Uses `git worktree isolation` (no Docker) for reproducible runs
- Tasks defined in YAML with pinned commits
- Judges: deterministic (pytest, grep patterns) + optional LLM-as-judge

**vs. our current system**: Our Tester and Reviewer agents produce qualitative reviews but no quantitative quality metrics. We cannot currently compare "did the Reviewer catch more issues after we updated reviewer.yaml?" objectively.

**Applicable elements**:
- Eval harness for `reviewer.yaml` quality (task-036 confidence scoring could be validated this way)
- Pass-rate tracking per pipeline stage (does Builder produce reviewable code on first try?)
- Git worktree isolation pattern — more robust than our current single-branch execution

**Proposed BL item**: BL-087 — Lightweight agent eval harness: YAML task definition + worktree isolation + grep-based judge for pipeline stage quality regression testing

---

### Pattern 4: Hooks-Over-Prompts — Enforcing Behavior at the System Level
**Fit**: Systemic improvement to our CLAUDE.md reliability  
**Key insight**: "Language models forget instructions approximately 20% of the time. Automation occurs at the tool level through hooks rather than prompt-based reminders."

The chief-of-staff agent explicitly uses this principle: any behavioral rule that must be followed 100% of the time belongs in a hook, not a CLAUDE.md reminder.

**Applicable elements in our system**:
- "Always write one token_log.jsonl entry per agent invocation" — currently a prompt reminder; should be a PostToolUse hook
- "Never commit directly to develop/main" — already in pre-commit hook ✓ 
- "Always create artefact directory before marking done" — currently prose reminder; could be a Stop hook
- "Run revise-claude-md at session end" — currently relies on pm-close prompt; could be a SessionEnd hook

**vs. current system**: Our hook infrastructure exists (pre-commit, commit-msg) but Stop/PostToolUse hooks are not used for behavioral enforcement.

**Proposed BL item**: BL-088 — Hooks-over-prompts audit: identify top 3 CLAUDE.md behavioral rules that fail ~20% of the time and implement as Stop/PostToolUse hooks in settings.json

---

### Pattern 5: Silent Failure Hunter — Pipeline Script Robustness Audit
**Fit**: Quality check for our growing scripts/ directory  
**What it does**: Audits for:
1. Empty catch blocks / bare `except: pass`
2. Dangerous fallbacks (`.catch(() => [])` patterns)
3. Error propagation loss (generic rethrows, lost stack traces)
4. Missing timeout/error handling on network/file/DB operations
5. Absent rollback mechanisms

**vs. our current system**: Our Builder + Reviewer pipeline catches some of these but the silent-failure-hunter is a dedicated pass specifically for error propagation quality. Our scripts (`pm-priority.py`, `token_cap_enforcer.py`, `cross-kanban.py`, `pm-healthcheck.sh`) have not been audited for silent failures.

**Applicable elements**: Run as a one-off audit agent against `scripts/` after each PM session adds a new script; could be invoked as a pipeline stage between Tester and DocUpdater.

**Proposed BL item**: BL-089 — One-off silent-failure-hunter audit of scripts/: pm-priority.py, token_cap_enforcer.py, cross-kanban.py, token-dashboard.py; create findings report with fixes

---

### Pattern 6: Loop Operator — Checkpoint + Escalation System for pm-run
**Fit**: Enhances our autonomous pm-run execution resilience  
**What it does**: Manages iterative loops with:
- Checkpoints for tracking progress per iteration
- Escalation triggers: no progress across 2 consecutive checkpoints, identical error traces, budget deviation, merge conflicts
- Safety prerequisites: QA enabled, baseline eval established, isolated environment (branch/worktree)
- Scope reduction when problems persist

**vs. our current system**: pm-run is a linear pipeline with no checkpoint tracking and no escalation logic. When the pipeline fails mid-way, there is no automatic scope reduction or escalation — the session just stops.

**Applicable elements**:
- Add checkpoint fields to queue.json tasks (`last_checkpoint`, `checkpoint_count`)
- Define escalation triggers in pm-run.md: same error twice → halt + notify; no artefact after 2 Builder runs → reduce scope
- Require worktree isolation for all pm-run task executions (BL-031 investigates this)

**Proposed BL item**: BL-090 — Add loop-operator checkpoint + escalation logic to pm-run: track checkpoint counts, define 3 escalation triggers, integrate with worktree isolation (BL-031)

---

### Pattern 7: Hook Profiles — Configurable Enforcement Levels
**Fit**: Quality-of-life improvement for different session types  
**What it does**: Three hook profiles controlled by `ECC_HOOK_PROFILE` env var:
- `minimal`: only safety-critical hooks (branch protection, secret detection)
- `standard`: minimal + quality hooks (format, lint)
- `strict`: all hooks including advisory and workflow enforcement

**vs. our current system**: Our hooks are binary (on/off). During exploratory sessions or quick fixes, full strict-mode hooks add friction (e.g., requiring all docs updated even for a one-line config change).

**Proposed BL item**: BL-091 — Hook profiles: add ECC_HOOK_PROFILE-style env var to settings.json; minimal (branch protection only) / standard (current) / strict (+ token log enforcement)

---

### Pattern 8: Strategic Compaction at Pipeline Stage Boundaries
**Fit**: Direct token cost reduction for long pm-run pipeline runs  
**Source**: Repo token optimization section — "Strategic compaction at logical breakpoints, not at 95% context"  
**What it does**: Rather than letting Claude Code auto-compact at 95% context fill, invoke `/compact` explicitly between heavy pipeline stages to reset accumulated context before starting the next stage.

**vs. our current system**: pm-run runs all stages in one continuous context. Context from Builder (reading all task files, writing artefacts) carries into Reviewer and Tester, inflating cost. No explicit compaction points exist.

**Applicable elements**:
- Add `/compact` call in pm-run.md between Builder output and Reviewer start
- Add `/compact` call between Reviewer output and Tester start
- Estimated reduction: 20–40% per-stage token cost on long tasks

**Proposed BL item**: BL-092 — Add strategic /compact calls at pm-run stage boundaries (Builder→Reviewer, Reviewer→Tester) to reduce context carry-over

---

### Pattern 9: Cost-Aware Model Routing with Complexity Thresholds
**Fit**: Programmatic enforcement of our existing model tier policy  
**Source**: `cost-aware-llm-pipeline` skill  
**What it does**:
- Routes to Haiku vs Sonnet based on text length and item count thresholds (e.g., text >= SONNET_THRESHOLD → Sonnet, else Haiku)
- Immutable budget tracking: frozen dataclasses, each `add()` returns a new instance — no silent mutation
- Fail-fast BudgetExceededError before processing starts
- Prompt caching for system prompts >1024 tokens (reduces redundant API cost on repeated invocations)

**vs. our current system**: Our model policy is prose documentation (CLAUDE.md model policy table). Agents can ignore it; nothing enforces Haiku for DocUpdater or prevents Builder from using Opus. No prompt caching is configured.

**Applicable elements**:
- Add prompt caching (`cache_control: ephemeral`) to manager.yaml system prompt (currently >1024 tokens)
- Extend token_cap_enforcer.py to also check assigned_to matches allowed model tier
- Document complexity thresholds: tasks with token_estimate < 3000 → Haiku eligible

**Proposed BL item**: BL-093 — Cost-aware model routing: complexity thresholds (token_estimate → Haiku vs Sonnet) + prompt caching for agent system prompts >1024 tokens

---

### Pattern 10: Agent Introspection Debugging Protocol
**Fit**: Structured response when pipeline stages fail silently  
**Source**: `agent-introspection-debugging` skill  
**What it does**: 4-phase self-debug:
1. **Failure Capture** — record error, last tool calls, context pressure, environment assumptions
2. **Root-Cause Diagnosis** — match against known patterns (loops, context overflow, service unavailability, file state mismatch)
3. **Contained Recovery** — smallest safe action that tests the diagnosis; "stop retries, restate hypothesis"
4. **Introspection Report** — structured: what failed / why / what was tried / evidence of improvement

**Key principle**: "Verify the world state instead of trusting memory" — run one discriminating check before retrying. Prevents token waste from repeating failed actions with minor wording changes.

**vs. our current system**: When a pipeline stage fails, the response is ad-hoc (re-read files, retry). No structured protocol exists in CLAUDE.md or pm-run.md for diagnosing stage failures.

**Proposed BL item**: BL-094 — Add agent introspection debugging protocol to CLAUDE.md: 4-phase structured self-debug for pipeline stage failures

---

### Pattern 11: Structured Codebase Onboarding for New Projects
**Fit**: Replaces our ad-hoc project onboarding process  
**Source**: `codebase-onboarding` skill  
**What it does**: 4-phase structured discovery:
1. **Reconnaissance** — parallel checks: package manifests, framework fingerprinting, entry points, directory structure, CI workflows, test structure
2. **Architecture Mapping** — tech stack, architecture pattern, key directory → purpose mapping, data flow trace
3. **Convention Detection** — naming conventions, error handling patterns, git conventions
4. **Generate Artefacts** — Onboarding Guide + starter CLAUDE.md for the project

**vs. our current system**: CLAUDE.md says "PM runs a discovery scan when a project is added" but provides no structured steps. In practice, onboarding is manual and inconsistent across projects.

**Proposed BL item**: BL-095 — Structured codebase onboarding: 4-phase discovery checklist in pm-plan.md for new projects added to registry

---

**Note on count discrepancy**: The original social media post cited "108 skills + 25 agents." The current repo contains 183+ skills and 48 agents — the repo has grown significantly since the post was written.

---

## 3. Items NOT Applicable (with rationale)

| Pattern | Reason not applicable |
|---|---|
| Language-specific reviewers (go, java, rust, etc.) | Our stack is Python/Shell/JSON — no multi-language codebase |
| Build resolvers (cpp, dart, pytorch, etc.) | No compiled code targets in our stack |
| AgentShield (1,282 tests) | Overkill for our current scale; our security review agent covers our threat model |
| chief-of-staff (email/Slack/LINE) | We use Telegram only; our inbox workflow already handles this |
| GAN evaluator/generator/planner | No ML model training in scope |
| Healthcare/HIPAA compliance skills | Not our domain |
| SEO specialist, brand-voice, investor-outreach | Not applicable |
| Two-tier skill placement (~/.claude/skills/) | Our skill files are few and curated; separation adds complexity without benefit at current scale |

---

## 4. Proposed BL Items

| BL ID | Title | Project | Priority | Rationale |
|---|---|---|---|---|
| BL-085 | SelfImprover: add confidence score + project scope to lessons.md instinct model | project_manager | P2 | Upgrades our unstructured append-only table to a curated, promotable instinct library |
| BL-086 | Context budget audit: MCP server tool schema overhead + agent frontmatter word counts | project_manager | P2 | Extends task-035 scope with dimension not in rewrite-plan.md; MCP may be largest token lever |
| BL-087 | Agent eval harness: YAML tasks + worktree isolation + grep judge for pipeline regression | project_manager | P2 | Enables quantitative pipeline quality tracking; prerequisite for task-036 validation |
| BL-088 | Hooks-over-prompts audit: move top 3 must-always-follow rules to Stop/PostToolUse hooks | project_manager | P2 | Closes ~20% instruction-forget rate for critical behavioral rules |
| BL-089 | Silent-failure-hunter audit of scripts/: one-off pass on all PM helper scripts | project_manager | P3 | Low-risk quality pass; ensures our growing script library has proper error propagation |
| BL-090 | pm-run: loop-operator checkpoint + escalation logic (integrate with BL-031 worktrees) | project_manager | P3 | Improves autonomous run resilience; depends on BL-031 worktree investigation |
| BL-091 | Hook profiles: minimal/standard/strict via env var in settings.json | project_manager | P3 | Quality-of-life; reduces friction in exploratory sessions without dropping safety hooks |
| BL-092 | Strategic /compact at pm-run stage boundaries (Builder→Reviewer, Reviewer→Tester) | project_manager | P2 | 20–40% per-stage token reduction on long pipelines |
| BL-093 | Cost-aware model routing: token_estimate thresholds + prompt caching for system prompts >1024 tokens | project_manager | P2 | Programmatic enforcement of model tier policy; prompt caching reduces repeated-invocation cost |
| BL-094 | Agent introspection debugging protocol in CLAUDE.md: 4-phase structured self-debug | project_manager | P2 | Prevents token waste from ad-hoc retry loops; "verify world state, don't trust memory" |
| BL-095 | Structured 4-phase codebase onboarding in pm-plan.md for new projects added to registry | project_manager | P3 | Replaces ad-hoc onboarding with consistent structured discovery |
