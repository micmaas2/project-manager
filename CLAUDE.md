# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

This is the workspace for the multi-agent automation system. Structure: `.claude/agents/` (agent YAMLs), `tasks/` (queue + schema), `hooks/` (git hooks), `artefacts/` (agent outputs), `logs/` (audit + token logs).

---

## Workspace Context

This directory (`project_manager`) is part of the `/opt/claude/` multi-project workspace.
Full project registry: `docs/project-registry.md` (authoritative — update there first).

| Directory | GitHub | Purpose |
|---|---|---|
| `/opt/claude/project_manager` | micmaas2/project-manager | This MAS orchestration system |
| `/opt/claude/CCAS/` | (no remote) | SAP infrastructure automation (Ansible-based) |
| `/opt/claude/pi-homelab/` | micmaas2/pi-homelab | Raspberry Pi / Home Assistant deployment |
| `/opt/claude/pensieve/` | micmaas2/pensieve | TBD |
| `/opt/claude/genealogie/` | micmaas2/genealogie | Genealogy tooling |
| `/opt/claude/performance_HPT/` | micmaas2/performance-twin | Performance / HPT tooling |
| `/opt/claude/project1/` | (no remote) | Generic project skeleton |

**Existing projects may already have plans, requirements, and in-progress work.**
When a project is added or first onboarded, PM runs a discovery scan (see `manager.yaml`) and
registers all existing artifacts in `docs/project-registry.md` before scheduling any tasks.

**No build system, tests, or source code** currently exist in this directory. When code is added, update this file with relevant commands.

---

## Project Goal

Build an incremental hierarchical multi-agent system to generate automations and scripts, accelerate delivery, and replace manual work. Start with MVP1: analyze one workflow and deliver one working automation.

---

## Git Branching Strategy

```
main (production)     ← Stable, tested, approved releases only
  ↑
develop (integration) ← Active development; all features merge here
  ↑
feature/* (work)      ← New features, bug fixes, planned work
```

**Branch naming**: `feature/description`, `bugfix/description`, `phase-X/week-Y-task`

**Workflow**:
1. Create feature branch from `develop`; NEVER commit directly to `develop` or `main`
2. Merge to `develop` when complete and tested
3. `main` updated ONLY after testing in `develop` + user acceptance:
   ```bash
   git checkout main && git merge develop -m "Release: description"
   git tag -a v1.x.x -m "Release version 1.x.x" && git push origin main --tags
   ```

**Git remote**: SSH-based (`git@github.com:micmaas2/project-manager.git`). Run `git remote -v` before adding — it already exists. HTTPS will fail.

**Git hooks** (in `hooks/`, symlinked to `.git/hooks/`):
- `pre-commit` — branch protection (blocks main/develop) + sensitive file detection
- `commit-msg` — enforces `[AREA]` message format; receives commit file as `$1`

NEVER put message-format validation in `pre-commit` — it does not receive `$1` reliably.

**Pre-Commit Hooks**: ALWAYS active — NEVER use `git commit --no-verify`

**Documentation**: Always update `CLAUDE.md`, `README.md`, `CHANGELOG.md` with changes (enforced by hooks).

**Commit format**:
```
[AREA] Brief description

- Detailed change 1
- Detailed change 2
```
Areas: `ROLE`, `DOCS`, `TEST`, `FIX`, `REFACTOR`, `PLAYBOOK`, `JENKINS`, `INVENTORY`, `AGENT`

---

## Model Policy (Token Governance)

- **Sonnet 4.6** — default for execution, building, testing, reviewing (80–90% of work)
- **Opus 4.6** — only for ProjectManager (plan/scope), Architect (design), Security (risk analysis)
- **Pattern**: Opus plans, Sonnet executes
- **Label** all outputs and tool calls with `[Sonnet]` or `[Opus]`
- **Token limits**: max 10,000 tokens per agent run; project cap 500k tokens/run (fail threshold)
- **Artefact stop**: agents stop after delivering a plan, script, test report, or review — continuation requires explicit approval
- **Preflight**: every task requires a token estimate before execution

---

## Agent Roles & Spawn Order

Spawn sequence: Manager → Architect/Security → Builder → Reviewer → Tester

| Agent | Model | Focus | Tools | Stop At |
|-------|-------|-------|-------|---------|
| ProjectManager | Opus | Scope/MVP/coordination | spawn_agent, task_list | Approved MVP plan |
| Architect | Opus | Modular design | diagram, diff | Arch diagram |
| Security | Sonnet | Secrets/auth/validation | checklist | Security OK |
| Builder (ScriptBuilder / TaskAutomator / DeliveryOptimizer) | Sonnet | Code/impl | code_exec, file_edit, bash | Script/patch |
| Reviewer | Sonnet | Quality/arch-compliance | lint, diff | Approved review |
| Tester (BugHunter) | Sonnet | Tests/regression | test_run | 90% pass |

Agent definitions live in `.claude/agents/[name].yaml`. Required fields: `name`, `prompt`, `policy`, `owner`, `incident_owner`.

**Policy schema per agent**:
```yaml
policy:
  allowed_tools: [...]
  max_tokens_per_run: 10000
  require_human_approval: false  # set to TRUE for any agent that has Bash in allowed_tools
  audit_logging: true
  external_calls_allowed: false
owner: "Role Name"
incident_owner: "Role Name"
```

---

## MVP Phases & Scope Discipline

1. **MVP1**: Setup + ScriptBuilder (script generation/test)
2. **MVP2**: Team — Automator + Reviewer
3. **MVP3**: Manager + DeliveryOptimizer
4. **MVP4**: Production (hooks, scheduling, monitoring)

**Human gate**: approve each MVP phase end before proceeding.

**MVP template** (required for every task):
```
Doel: <1 sentence>
Niet in scope: <short list>
Acceptatiecriteria: 1) ... 2) ... 3) ...
SLOs: latency < X ms; tests >= 90%
max_tokens_per_run: 8000
Security/arch impact: <note>
Prerequisites: [tool >= version, ...]
Tests: unit/integration/regression
Rollback plan: <steps + owner>
Privacy DPIA: yes/no + note
Cost estimate: EUR ...
Definition of Done: <checklist>
Incident owner: <Name / Role>
```

ProjectManager enforces all scope. Work outside MVP is rejected or backlogged.

---

## Governance, Security & Observability

**Runtime policy**: all agent actions pass a policy layer checking `allowed_tools`, `max_tokens_per_run`, `external_calls_allowed`, `require_human_approval`. Non-compliant actions are blocked and logged.

**Security principles**:
- Least privilege for tools and API scopes
- Secrets only via central vault; never in prompts or logs
- RBAC for agent spawn and policy changes
- Prompt sanitization; adversarial tests for prompt injection

**Observability**:
- Audit trail: who, agent, action, time, artefact
- Token logs: per run and cumulative per task
- Metrics: tokens/run, median latency, success rate, test pass rate
- Alerts: token overspend, policy violations, regressions

---

## Workflow Orchestration

1. **Plan first (mandatory)**: ALWAYS enter plan mode before any non-trivial task (3+ steps or architectural decisions). Write plan to `tasks/todo.md`.
2. **Subagents**: offload research, exploration, and parallel analysis to keep main context clean — one task per subagent; pass only pointers (task_id, file paths), never embed full content.
3. **Token minimization**: agents receive only task_id; they read their own context from files. No large context copied between invocations. Stop after each deliverable.
4. **Verify before done**: never mark complete without proving it works. Ask: "Would a staff engineer approve this?"
5. **Self-improvement**: SelfImprover runs after every pipeline PASS and appends to `tasks/lessons.md`. After any correction: update CLAUDE.md so the mistake cannot recur; commit to git.
6. **Always-on pipeline**: every task runs Builder → Reviewer (quality + security + scope) → Tester → DocUpdater → SelfImprover. No skipping.
7. **Autonomous bug fixing**: when given a bug report, fix it — point at logs/errors, then resolve.
8. **Demand elegance (balanced)**: pause and ask "Is there a more elegant way?" before finalising any non-trivial design. Skip for simple fixes — do not over-engineer.
9. **Minimal impact**: touch only what is strictly necessary; avoid side effects on untouched code or config. If you must change something adjacent, flag it explicitly.
10. **Explain with diagrams**: when explaining architecture or non-obvious decisions, prefer ASCII diagrams over prose where they add clarity.

**PM Planning Session**: invoke ProjectManager with "planning" intent to review backlog, reprioritize, and onboard new projects. PM presents backlog and asks for user confirmation before queuing tasks.

**Task tracking**:
- Active queue → `tasks/queue.json`
- Backlog + scope-drift → `tasks/backlog.md`
- Kanban view → `tasks/kanban.md`
- Epics & stories → `tasks/epics.md`
- Plan files → `/root/.claude/plans/` (registered in `docs/project-registry.md`)
- Lessons → `tasks/lessons.md`
- Mark items complete immediately as you go

---

## CI/CD & Release

Pipeline: Preflight → policy checks → unit/integration tests → canary → full rollout

Test types: unit (generated scripts), integration (tool interactions), regression (per agent update), adversarial (prompt injection / hallucination triggers), canary releases for production.

**Release checklist**: policy field present; preflight token estimate done; security checklist green; tests pass; rollback plan defined.

---

## Task Queue & Resume

All agent work is tracked in `tasks/queue.json`. Schema:

```json
{
  "tasks": [
    {
      "id": "task_001",
      "title": "...",
      "project": "pensieve|ccas|pi-homelab|other",
      "assigned_to": "builder|reviewer|tester",
      "status": "pending|in_progress|paused|review|test|done|failed",
      "artefact_path": "artefacts/task_001/",
      "created": "ISO8601",
      "updated": "ISO8601",
      "token_estimate": 8000,
      "resume_from": null,
      "notes": "",
      "mvp_template": {
        "doel": "",
        "niet_in_scope": [],
        "acceptatiecriteria": [],
        "security_arch_impact": "",
        "tests": "",
        "definition_of_done": [],
        "rollback_plan": "",
        "incident_owner": ""
      }
    }
  ]
}
```

**Rate limit / resume flow**:
1. Agent hits rate limit → sets `status: "paused"`, `resume_from: "<step_name>"` → stops
2. User waits for rate limit to reset
3. User runs ProjectManager agent again
4. ProjectManager reads queue, finds paused tasks, resumes from `resume_from` step

**Queue validation**: `tasks/queue.schema.json` enforces all field types. Key constraint: `artefact_path` must match `^artefacts/[a-zA-Z0-9_-]+/$` — no path traversal. Validate with any JSON Schema tool before adding tasks manually.

**Logs**:
- `logs/audit.jsonl` — append-only, one JSON object per line: `{timestamp, agent, task_id, action, status}`
- `logs/token_log.jsonl` — per-run token accounting: `{timestamp, agent, task_id, token_estimate}`
