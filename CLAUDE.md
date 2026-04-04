# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

This is a workspace context directory under `/opt/claude/`. It contains no source code of its own — it serves as the working directory for Claude Code sessions.

---

## Workspace Context

This directory (`project_manager`) is part of the `/opt/claude/` multi-project workspace. Sibling projects:

| Directory | Purpose |
|---|---|
| `/opt/claude/CCAS/` | SAP infrastructure automation (Ansible-based, multiple repos) |
| `/opt/claude/pi-homelab/` | Raspberry Pi Home Assistant deployment (Pi 4 & Pi 5) |
| `/opt/claude/project1/` | Generic project skeleton |

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

**Pre-Commit Hooks**: ALWAYS active — NEVER use `git commit --no-verify`

**Documentation**: Always update `CLAUDE.md`, `README.md`, `CHANGELOG.md` with changes (enforced by hooks).

**Commit format**:
```
[AREA] Brief description

- Detailed change 1
- Detailed change 2
```
Areas: `ROLE`, `DOCS`, `TEST`, `FIX`, `REFACTOR`, `PLAYBOOK`, `JENKINS`, `INVENTORY`

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
  require_human_approval: false
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

1. **Plan first**: enter plan mode for any non-trivial task (3+ steps or architectural decisions); write plan to `tasks/todo.md`
2. **Subagents**: offload research, exploration, and parallel analysis to keep main context clean — one task per subagent
3. **Verify before done**: never mark complete without proving it works
4. **Self-improvement**: after any user correction, update `tasks/lessons.md`; review lessons at session start
5. **Autonomous bug fixing**: when given a bug report, fix it — point at logs/errors, then resolve

**Task tracking**:
- Plan → `tasks/todo.md` (checkable items)
- Lessons → `tasks/lessons.md`
- Mark items complete immediately as you go

---

## CI/CD & Release

Pipeline: Preflight → policy checks → unit/integration tests → canary → full rollout

Test types: unit (generated scripts), integration (tool interactions), regression (per agent update), adversarial (prompt injection / hallucination triggers), canary releases for production.

**Release checklist**: policy field present; preflight token estimate done; security checklist green; tests pass; rollback plan defined.
