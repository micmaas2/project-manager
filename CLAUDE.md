# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

This is the workspace for the multi-agent automation system. Structure: `.claude/agents/` (agent YAMLs), `tasks/` (queue + schema), `hooks/` (git hooks), `artefacts/` (agent outputs), `logs/` (audit + token logs).

---

## Workspace Context

This directory (`project_manager`) is part of the `/opt/claude/` multi-project workspace.
Full project registry: `docs/project-registry.md` (authoritative — update there first when adding or onboarding a project during a PM planning session).

| Directory | GitHub | Purpose |
|---|---|---|
| `/opt/claude/project_manager` | micmaas2/project-manager | This MAS orchestration system |
| `/opt/claude/CCAS/` | (no remote) | SAP infrastructure automation (Ansible-based) |
| `/opt/claude/pi-homelab/` | micmaas2/pi-homelab | Raspberry Pi / Home Assistant deployment |
| `/opt/claude/pensieve/` | micmaas2/pensieve | TBD |
| `/opt/claude/genealogie/` | micmaas2/genealogie | Genealogy tooling |
| `/opt/claude/performance_HPT/` | micmaas2/performance-twin | Performance / HPT tooling |
| `/opt/claude/project1/` | (no remote) | Generic project skeleton |
| Pi4: `/opt/mas/` | micmaas2/mas_personal_assistant (private) | Personal assistant — Telegram bot, FastAPI, PostgreSQL, React (mas.femic.nl) |

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

**Releasing to main**: `git push origin develop:main` — the only working release path.
The pre-commit hook blocks ALL commits on `main` and `develop` (including merge commits), so
`git checkout main && git merge develop` always fails locally. Use the refspec push instead.
If main has GitHub API commits that develop lacks (diverged), use `--force-with-lease` after
syncing via a feature branch: `git checkout -b feature/sync && git checkout origin/main -- <file> && git commit ... && merge into develop`, then `git push origin develop:main --force-with-lease`.

**Merging feature branches with conflicts into develop**: conflict-free `git merge --no-ff -m "..."` on develop works (git internal path bypasses the hook). When a merge has conflicts, `git commit` after resolution is blocked. Pattern:
1. `git merge --abort` on develop
2. `git checkout -b feature/sync-X` (from develop)
3. `git merge feature/X` — resolve conflicts here, `git commit` (allowed on feature branch)
4. `git push origin feature/sync-X:develop` — pushes resolved state to remote develop
5. `git checkout develop && git pull origin develop` — sync local
Avoid `git stash && checkout && stash pop` when branches have diverged — it creates cascading conflicts.

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
- **Haiku 4.5** — DocUpdater, SelfImprover, revise-claude-md, and any agent doing templated/structured work with no complex reasoning required
- **Pattern**: Opus plans, Sonnet executes, Haiku documents
- **Default to Haiku** for any agent that does not require reasoning over complex context
- **Label** all outputs and tool calls with `[Sonnet]` or `[Opus]`
- **Token limits**: max 10,000 tokens per agent run; project cap 500k tokens/run (fail threshold)
- **Artefact stop**: agents stop after delivering a plan, script, test report, or review — continuation requires explicit approval
- **Preflight**: every task requires a token estimate before execution

---

## Agent Roles & Spawn Order

Spawn sequence: Manager → Architect/Security → Builder → [Reviewer + code-quality-reviewer] → Tester → [DocUpdater + docs-readme-writer] → SelfImprover

| Agent | Type | Model | Focus | Stop At |
|-------|------|-------|-------|---------|
| ProjectManager | YAML | Opus | Scope/MVP/coordination | Approved MVP plan |
| Architect | YAML | Opus | Modular design | Arch diagram |
| Security | YAML | Sonnet | Secrets/auth/validation | Security OK |
| Builder (ScriptBuilder / TaskAutomator / DeliveryOptimizer) | YAML | Sonnet | Code/impl | Script/patch |
| Reviewer | YAML | Sonnet | Quality/arch-compliance | Approved review |
| code-quality-reviewer | built-in | Sonnet | Security, quality, best-practices | Review report |
| Tester (BugHunter) | YAML | Sonnet | Tests/regression | 90% pass |
| DocUpdater | YAML | Haiku | Docs/changelog | Updated docs |
| docs-readme-writer | built-in | Haiku | README/module docs | Docs written |
| SelfImprover | YAML | Haiku | Lessons/proposals | proposals.md written |
| revise-claude-md | built-in | Haiku | CLAUDE.md session learnings | CLAUDE.md updated |

**Built-in Claude Code agents** (invoke via `Agent` tool with `subagent_type`):
- `code-quality-reviewer` — security + quality review; runs parallel to Reviewer; for any regex using `re.DOTALL`, flag use of `$` as a stop anchor (use `\Z` instead) and require a multi-line fixture in Tester
- `docs-readme-writer` — README/module docs; runs parallel to DocUpdater
- `claude-md-management:revise-claude-md` — apply session learnings to CLAUDE.md (session end); invoke via `Skill` tool, NOT `Agent` tool (`subagent_type` does not work for `claude-md-management:*`)
- `claude-md-management:claude-md-improver` — full CLAUDE.md audit (on demand); invoke via `Skill` tool
- **Explore-type subagents cannot write files**: when DocUpdater/docs-readme-writer are spawned as `subagent_type: Explore`, they return proposed content but cannot apply edits. The parent agent must read the agent's output and apply the file changes directly — do not wait for the Explore agent to write.

**Shell script pre-submission check** (Builder must verify before handing off to Reviewer):
- `bash -n <script>` must exit 0 — **for shell scripts only**; Python scripts use `python3 -m py_compile <script>` instead (`bash -n` cannot parse Python and will spuriously fail)
- If cron/daemon: log guard, flock, SSH identity, logrotate — all present?
- If outbound git/SSH: auth path exported explicitly?
- Log output sanitized (ANSI + control chars stripped) before writing to file?
- If the script accepts file-path arguments (e.g. `--queue`, `--backlog`, `--config`): add a `_safe_path()` containment guard that resolves the path and asserts `_WORKSPACE_ROOT in path.parents` — exit 1 with a descriptive error if not. Document the workspace root as a module-level constant.

**Prompt writing discipline**: All agent prompts MUST use imperative voice addressed to the agent itself ("You will", "Do not", "Stop if"). Never narrate what other agents do — instead state this agent's responsibility relative to other agents' outputs. Orchestration sequencing (waiting, parallelism) belongs in design docs, not embedded in agent prompts.

**Opus advisor escalation**: When Builder or Reviewer hits an ambiguous architectural or security decision that context alone cannot resolve, spawn a focused Opus sub-agent (model: claude-opus-4-6) with ONE question. Format:
```
ADVISOR_CONSULT: <single specific question>
Context: <2-3 sentences of relevant background>
Options considered: <list>
```
Opus returns a recommendation; Builder/Reviewer continues with it and notes the escalation in `build_notes.md` under "Advisor Consults". Triggers: architecture tradeoff with no clear winner; security decision outside established patterns; scope ambiguity where both interpretations are defensible. Do NOT use for routine decisions.

**Cross-file rule mirroring (M-1 pattern)**: Enumerated rules that appear in both CLAUDE.md and agent YAMLs can silently accumulate orphan entries. When editing either file, verify rule counts and text match in both directions. Tester must include a regression guard for any task that modifies mirrored content: (a) rule-count equality check across all copies, (b) absence check for any rule that was removed.

**Agent YAML policy schema**: the pre-commit hook enforces that every `.claude/agents/*.yaml` contains all 5 required policy fields (`allowed_tools`, `max_tokens_per_run`, `require_human_approval`, `audit_logging`, `external_calls_allowed`). A commit that adds or modifies an agent YAML without all 5 fields will be rejected.

**PM Skills** (invoke as `/pm-start`, `/pm-status`, etc. — files in `.claude/commands/`):

| Skill | File | Purpose |
|-------|------|---------|
| `/pm-start` | `pm-start.md` | Session startup: fetch, inbox, lessons, queue, phase gate, summary |
| `/pm-status` | `pm-status.md` | Queue counts, kanban, phase status, token spend |
| `/pm-plan` | `pm-plan.md` | PI/Refinement planning session: backlog review, MVP templates, queue tasks |
| `/pm-propose` | `pm-propose.md` | End-of-session proposal review: scan, deduplicate, apply, bake |
| `/pm-close` | `pm-close.md` | Sprint close: clean tree → proposals → merge → push → phase gate |
| `/pm-lessons` | `pm-lessons.md` | Print last 10 lessons |
| `/pm-run` | `pm-run.md` | Execute next pending task through full pipeline |
| `skill-creator` | Marketplace | Eval-driven skill authoring; run for new/revised PM skills |

**Plugin marketplace**: official Anthropic plugins at `/root/.claude/plugins/marketplaces/claude-plugins-official/plugins/` — browse with `ls` for available commands, agents, and skills; check `README.md` in each plugin dir.

**Skill authoring rules**: Skills are executable command prompts (`.claude/commands/*.md`).
- Every angle-bracket placeholder must include an explicit resolution instruction naming the source file and lookup pattern — do not assume the reader will infer where data lives.
- Test all placeholders manually before committing: simulate a fresh session with no prior context and verify every `<placeholder>` can be resolved without ambiguity.
- **Security filter ordering: inline, not post-hoc** — inspect for sensitive patterns (password, secret, api_key, etc.) per-item before appending to any buffer; a post-hoc filter is logically bypassed when the buffer already contains sensitive data.

Agent definitions live in `.claude/agents/[name].yaml`. Required fields: `name`, `prompt`, `policy`, `owner`, `incident_owner`.

**Policy schema per agent**:
```yaml
policy:
  allowed_tools: [...]
  max_tokens_per_run: 10000
  require_human_approval: false  # set to TRUE for any agent that has Bash, Write, or Edit in allowed_tools
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
  - If outbound HTTP: private IP ranges blocked (localhost, 127.x, 10.x, 192.168.x, 172.16-31.x)?
  - If outbound HTTP: request timeout set?
  - If any user-controlled value (topic, category, tag, filename) is used in a file path:
      - Validate against allowlist or strict regex (e.g. [a-z0-9-]+) before path construction
      - Assert finalPath.startsWith(ALLOWED_ROOT) after construction (use path.resolve to collapse ..)
  - If LLM output is used as a structured field (slug, enum, filename): prompt character-set
    constraint and validation regex in code must be identical — document both in the artefact
  - If any field value from external data (email headers, API responses, user input) is
    interpolated into YAML/JSON/Markdown: escape strings before interpolation (e.g. replace
    " with \" in YAML double-quoted scalars; strip ASCII control chars 0x00-0x1F, not just \n)
  - If any free-text field from an external API (description, extract, title, etc.) is embedded
    in an LLM prompt: strip ASCII control chars 0x00–0x1F (excluding \t and \n) — apply to ALL
    fields passed to the prompt, not only to those written to files
  - If an external ID (e.g. message ID, record ID) is passed to a downstream step: validate
    it is non-null/non-empty at point of use; throw a descriptive error if absent
  - If the script runs under cron or systemd (no interactive terminal):
      - Log writability guard: verify/create log file before first write; exit to stderr if unwritable
      - Concurrency lock: use `flock -n` on a lock file at startup; skip (exit 0) if lock held
      - SSH/auth identity: export `GIT_SSH_COMMAND` or equivalent explicitly — cron env has no agent
      - Log rotation: document logrotate config as a **required** deploy step, not optional
No external deps: true/false  (if true: stdlib/built-ins only; no pip/npm installs)
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

**80% cap alert (preflight)**: before starting a task, sum all agent token estimates for that task. If total > 400,000 (80% of 500k cap), halt with: `ALERT: Task <id> estimated tokens (<n>) exceed 80% of project cap. Reduce scope or split task before proceeding.`

---

## Workflow Orchestration

0. **Session start — mandatory checklist (run in order before any task work)**:
   - [ ] **Fetch remote**: Run `git fetch origin` before reading any operational file. n8n commits go directly to `origin/main` via GitHub API — without fetching, inbox items are invisible.
   - [ ] **Telegram inbox**: Run `git show origin/main:tasks/telegram-inbox.md` to read the live inbox (not the local checkout). If items exist below the header, promote each to `tasks/backlog.md` (next BL ID, EPIC-003, project_manager, P2, new, today), then clear: if local `tasks/telegram-inbox.md` is already the clean header, just `git push origin develop:main --force-with-lease`; otherwise commit the cleared file on a feature branch first, merge to develop, then push.
   - [ ] **Lessons**: Read `tasks/lessons.md`; state the 3 most recent rows before planning. Lessons govern tooling choices and approach — do not repeat captured mistakes.
   - [ ] **Catch-up SelfImprover**: For every `status: done` task in `tasks/queue.json`, verify `artefacts/<artefact_path>/improvement_proposals.md` exists. If absent (directory may not exist either), run SelfImprover for that task — it must create the directory and file from the task definition in queue.json.
   - [ ] **ExitPlanMode denial**: if the user denies ExitPlanMode, use AskUserQuestion to clarify intent before re-attempting — the user may be redirecting to a side task first, not rejecting the plan outright.

1. **Plan first (mandatory)**: ALWAYS enter plan mode before any non-trivial task (3+ steps or architectural decisions). Plans are written to `/root/.claude/plans/` (auto-managed by plan mode).
2. **Subagents**: offload research, exploration, and parallel analysis to keep main context clean — one task per subagent; pass only pointers (task_id, file paths), never embed full content.
3. **Token minimization**: agents receive only task_id; they read their own context from files. No large context copied between invocations. Stop after each deliverable.
4. **Verify before done**: never mark complete without proving it works. Ask: "Would a staff engineer approve this?"
   **Artefact minimum for git-only tasks**: even when no code is produced, create `artefacts/<task-id>/verification.md` capturing: commands run (e.g. `git log --oneline`, `ls` of key files), their output, and a PASS/FAIL verdict per acceptance criterion. Tasks with no artefact directory cannot be retrospected by SelfImprover.
   **Architecture/research task Definition of Done**: must include "all `NEW:` proposals in the review document are registered as BL items in `tasks/backlog.md`" — SelfImprover does not do this automatically; it is a required explicit step before marking done.
5. **Self-improvement**: SelfImprover runs after every pipeline PASS and appends to `tasks/lessons.md`. If a significant pattern is found it also writes `artefacts/<task_id>/improvement_proposals.md` (format below). After any correction: update CLAUDE.md so the mistake cannot recur; commit to git.
6. **Always-on pipeline**: every task runs the full pipeline — no skipping:
   ```
   Builder
     → [Reviewer (YAML agent) + code-quality-reviewer (built-in)] — run IN PARALLEL; combine findings before looping Builder
     → Tester
     → [DocUpdater (YAML agent) + docs-readme-writer (built-in)]  — run IN PARALLEL
     → SelfImprover (YAML agent)
   ```
   Built-in agent roles:
   - `code-quality-reviewer` — security, quality, best-practices check on all new/modified code
   - `docs-readme-writer` — creates/updates README and module docs for code-producing tasks

   **Doc stage file ownership**: when DocUpdater and docs-readme-writer run in parallel, assign ownership explicitly: DocUpdater → `CHANGELOG.md`; docs-readme-writer → `README.md`. This prevents overwrite conflicts when both agents target the same file.
6b. **End-of-session proposal review (human gate)**: At the end of each PM session, read `artefacts/*/improvement_proposals.md` for all tasks completed this session. Present each pending proposal to the user as: target file, proposed change, rationale, APPROVE / REJECT. Apply only approved proposals immediately (edit file, commit). Log rejected proposals with reason in `tasks/lessons.md`. Never apply a proposal without explicit user approval. After all proposals are resolved, invoke `revise-claude-md` via the `Skill` tool (not `Agent`) to bake session learnings into CLAUDE.md and commit the result. **Cross-file consistency check**: when a proposal introduces a format definition (e.g. improvement_proposals.md schema), verify the format is identical in both CLAUDE.md and the relevant agent YAML before presenting to the user. **Proposal response format**: user replies `APPROVE: P1, P3 / REJECT: P2` — apply all approved in one pass, log rejections. **SelfImprover dedup**: when running SelfImprover for multiple tasks in a session, collect all proposals before presenting — remove duplicates and proposals targeting text already present in the target file. **Scanning for pending proposals**: use `find artefacts -name "improvement_proposals.md" | xargs grep -lE "^\*\*Status\*\*: REQUIRES_HUMAN_APPROVAL"` — the `^` anchor matches only lines that start with `**Status**:`, preventing false positives from test files or proposal body text that quote the pattern. Do NOT use `grep -rl` on the whole artefacts dir. **pm-propose commit discipline**: after applying approved proposals that edit CLAUDE.md, immediately commit on the current feature branch before proceeding — do not leave session-learning edits unstaged across a context boundary.
7. **Autonomous bug fixing**: when given a bug report, fix it — point at logs/errors, then resolve.
8. **Demand elegance (balanced)**: pause and ask "Is there a more elegant way?" before finalising any non-trivial design. Skip for simple fixes — do not over-engineer.
9. **Minimal impact**: touch only what is strictly necessary; avoid side effects on untouched code or config. If you must change something adjacent, flag it explicitly.
10. **Explain with diagrams**: when explaining architecture or non-obvious decisions, prefer ASCII diagrams over prose where they add clarity.

**PM Planning Session**: invoke ProjectManager with "planning" intent to review backlog, reprioritize, and onboard new projects. PM presents backlog and asks for user confirmation before queuing tasks. **Preflight**: run `ls artefacts/` before assigning any task ID — use a descriptive suffix (e.g. `task-007-gate/`) if the target path already exists.
**MVP ordering gate**: During PM planning, check epics.md for any stories with status `planned` in lower MVP phases before queuing higher-phase work. All stories in a phase must be `done` before the next phase is prioritized.

**Task tracking**:
- Active queue → `tasks/queue.json`
- Backlog + scope-drift → `tasks/backlog.md`
- Kanban view → `tasks/kanban.md`
- Epics & stories → `tasks/epics.md`
- Plan files → `/root/.claude/plans/` (registered in `docs/project-registry.md`)
- Lessons → `tasks/lessons.md` (append-only table: `| Date | Agent | Lesson | Applied To |`)
- Improvement proposals → `artefacts/<task_id>/improvement_proposals.md` (one `## Proposal N` section per proposal, fields: **Target file**, **Change** (diff or description), **Rationale**, **Status**: `REQUIRES_HUMAN_APPROVAL` → `APPROVED` / `REJECTED: <reason>`)
- **Artefact path required on done**: a task may not be set to `status: done` without a non-empty `artefact_path`. If no code was produced, set the path and create a `verification.md` (see step 4).
- Mark items complete immediately as you go
- When marking a queue task `done`, also update the corresponding BL entries in `tasks/backlog.md` to `done` status in the same commit.

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
      "notes": [],
      "mvp_template": {
        "doel": "",
        "niet_in_scope": [],
        "acceptatiecriteria": [],
        "security_arch_impact": "",
        "tests_required": "",
        "definition_of_done": [],
        "rollback_plan": "",
        "incident_owner": "",
        "privacy_dpia": "",
        "cost_estimate": ""
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

**Artefact path assignment**: Before adding a new task to queue.json, run `ls artefacts/` to check if the target path already exists. If it does, use a descriptive suffix (e.g. `artefacts/task-008-laptop/`) rather than the bare ID.

**`assigned_to` tracks pipeline stage**: update `assigned_to` at every stage transition alongside `status` (`builder` → `reviewer+code-quality-reviewer` → `tester` → `doc-updater+docs-readme-writer` → `self-improver`). For parallel stages set `assigned_to` to both agents: `"reviewer+code-quality-reviewer"` or `"doc-updater+docs-readme-writer"`.

**queue.json stale-read fix**: if the Edit tool fails with "file modified since read", use `python3 -c "import json; q=json.load(open('tasks/queue.json')); ...; json.dump(q,open('tasks/queue.json','w'),indent=2)"` to atomically update it.

**Python datetime**: use `datetime.now(datetime.UTC).isoformat()` not `datetime.utcnow()` — deprecated in Python 3.12+; system runs 3.13.5.

**Logs**:
- `logs/audit.jsonl` — append-only, one JSON object per line: `{timestamp, agent, task_id, action, status}`
- `logs/token_log.jsonl` — per-run token accounting: `{timestamp, agent, task_id, token_estimate}`
  Every sub-agent (Builder, Reviewer, Tester, DocUpdater, SelfImprover) must write one entry per invocation — not just ProjectManager. This enables per-agent token observability and identifies highest-cost pipeline stages.

---

## n8n Workflow Deployment (Pi4)

SSH alias: `pi4` (192.168.1.10). n8n runs as Docker container `n8n`.
GitHub PAT for project-manager API calls: `/opt/n8n/github-pat` on Pi4.

**Vault location**: `/opt/obsidian-vault/` exists on Pi4 only — not on the local host.
Explore agents run locally; always use `ssh pi4 "find /opt/obsidian-vault ..."` for vault state.

**dashboard-preview.md is cron-auto-updated**: `artefacts/task-006/dashboard-preview.md` is regenerated every 15 min by a Pi4 cron job. Expect it as a dirty unstaged file at session start and pm-close — commit it on a quick feature branch before proceeding (timestamp + done count update only).

**Pi4 Python packages**: verify before deploying scripts: `ssh pi4 "python3 -c 'import X'"`.
Install missing packages with `pip3 install <pkg> --break-system-packages` (Debian-managed env).
`beautifulsoup4` installs as `beautifulsoup4` but imports as `bs4`.

**Pi4 root-owned git repo** (`/opt/mas`): all git operations require sudo and explicit identity flags — root has no git config on Pi4. Pattern:
```bash
sudo git -C /opt/mas -c user.name='Michel Maas' -c user.email='michel@femic.nl' <cmd>
```
Use `-c` flags rather than permanently configuring root's git config.

**Docker compose `--build` rebuilds depends_on chain**: `docker compose up -d --build <service>` also rebuilds services listed under `depends_on` for that service. On Pi4 ARM, a Python pip install layer can take 5+ minutes — plan for the full dependency chain build time, not just the target service.

**`--no-deps` for targeted rebuilds**: add `--no-deps` to rebuild only the target service without triggering its `depends_on` chain: `docker compose up -d --no-deps --build mas-telegram`. Omit `--no-deps` only when dependency layers also changed.

**Pi4 docker-compose env file**: `docker-compose.dev.yml` hardcodes `env_file: .env`. `/opt/mas/.env` does not exist — symlink before any compose command: `sudo ln -sf .env.production .env`. Without this, compose exits with "env file /opt/mas/.env not found".

**Hyphenated script filenames**: `migrate-vault.py` cannot be imported directly in Python tests.
Use `importlib.util.spec_from_file_location("name", "path/to/script.py")` instead.

**Testing hyphenated-filename scripts**: Use `importlib.util.spec_from_file_location("module_name", path)` in all test files for scripts with hyphens in their names — this is the only safe import path. See `artefacts/task-005/test_migrate_vault.py` as the canonical example.

**Testing Docker-only packages**: when a Python package (e.g. `src.integration`) exists only inside a Docker image and cannot be imported on the host, use `sys.modules` pre-injection:
1. Copy the source file to `/tmp` on the host (`scp pi4:/opt/mas/src/integration/file.py /tmp/`).
2. Pre-populate `sys.modules` with `MagicMock` entries for all transitive imports before loading the file. Use `type(name, (), {})` (not `MagicMock`) for mixin classes to satisfy Python's MRO.
3. Load via `importlib.util.spec_from_file_location("module.name", "/tmp/file.py")`.
This lets unit tests run locally without a Docker environment. See `artefacts/task-019/test_auth_guard.py` as the canonical example.

**Task unit tests**: test files live in `artefacts/<task-id>/test_*.py`; run with `python3 -m pytest artefacts/<task-id>/test_*.py -v`. Use `importlib.util.spec_from_file_location` + `unittest.mock.patch.object` to test scripts without making them importable packages.

**Testing unwritable paths as root**: `chmod 0o444` does NOT prevent root from writing. To simulate an unwritable directory in tests, replace it with a regular file (so `touch <dir>/<file>` fails with "Not a directory"). Document this pattern at the top of any test file that uses it.

**NOTE — Python testing patterns relocation**: The Python testing gotchas below (importlib, sys.modules, hyphenated filenames, Docker-only packages) are currently in the n8n section for historical reasons. During the next CLAUDE.md rewrite pass (BL-079), relocate them to a dedicated `## Python Testing Patterns` section for discoverability.

**Fixture files for path-guarded scripts**: when writing tests for scripts that use `_safe_path()` workspace-root validation, place fixture files under `artefacts/<task-id>/_fixtures/` — not in `tmp_path` (which resolves to `/tmp`, outside the workspace root and therefore rejected by the path guard).

**GitHub API commits (stdlib)**: read a file with `GET /repos/{repo}/contents/{path}?ref={branch}` → decode `base64.b64decode(resp["content"])`; write with `PUT /repos/{repo}/contents/{path}` + `{"content": base64.b64encode(...).decode(), "sha": <existing_sha_or_omit_for_new>, "branch": ...}`. No `requests` package needed — `urllib.request` suffices.

**Credential-placeholder patching** (required before import if workflow JSON contains `"id": "PLACEHOLDER_*"`):
```bash
# 1. Create credential in n8n (example: httpHeaderAuth for an API key)
API_KEY=$(ssh pi4 "cat /opt/n8n/api-key")
CRED_ID=$(ssh pi4 "curl -s -X POST http://localhost:88/api/v1/credentials \
  -H 'X-N8N-API-KEY: $API_KEY' -H 'Content-Type: application/json' \
  -d '{\"name\": \"My Cred\", \"type\": \"httpHeaderAuth\", \"data\": {\"name\": \"X-Header\", \"value\": \"<value>\"}}'" \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
# 2. Patch JSON
python3 -c "import json; wf=json.loads(open('workflow.json').read().replace('PLACEHOLDER_CRED', '$CRED_ID')); wf.pop('tags',None); json.dump(wf,open('/tmp/wf.json','w'),indent=2)"
```

**Deploy sequence** (all four steps required):
```bash
# 1. Prep: inject workflow id + strip tags + patch credential placeholders (see above)
python3 -c "import json; wf=json.load(open('workflow.json')); wf['id']='<UUID>'; wf.pop('tags',None); json.dump(wf,open('/tmp/wf.json','w'))"
# 2. Import (NOTE: import:workflow always DEACTIVATES the workflow — activation is a separate step)
scp /tmp/wf.json pi4:/tmp/wf.json && ssh pi4 "docker cp /tmp/wf.json n8n:/tmp/wf.json && docker exec n8n n8n import:workflow --input=/tmp/wf.json"
# 3. Activate via REST API (publish:workflow does NOT activate — use REST API)
API_KEY=$(ssh pi4 "cat /opt/n8n/api-key")
ssh pi4 "curl -s -X POST http://localhost:88/api/v1/workflows/<UUID>/activate -H 'X-N8N-API-KEY: $API_KEY'"
# 4. Restart (required for schedule triggers to register)
ssh pi4 "docker restart n8n && sleep 5 && docker ps | grep n8n"
```

**Import gotchas**:
- Workflow JSON must have `id` (UUID string) — omitting causes `SQLITE_CONSTRAINT` on import
- Strip `tags` array before import — tag IDs are DB-internal and cause `SQLITE_CONSTRAINT`
- `--userId=1` (numeric) fails; use UUID string or omit entirely
- No `sqlite3` in the n8n container; use `docker exec n8n n8n export:workflow --all` to inspect
- Find active workflow ID: export all + filter by `active: true` and most recent `updatedAt`
- **Credential IDs in workflow JSON are placeholders** — n8n resolves credentials by internal UUID, not name. A mismatched or placeholder ID (e.g. `anthropic-cred`) causes silent auth failures; the HTTP node sends no credential header. After every import, verify each node's credential `id` matches a real credential (`n8n export:credentials --all`). Patch with Python before import if needed.
- `export:workflow --id=X --output=file.json` wraps output in a JSON array — use `data[0]` when loading a single exported workflow in Python.

**Pending deployments** (not yet imported into n8n on Pi4):
- `pensieve/workflows/gmail-capture.json` — built in task-009; deploy steps in `artefacts/task-009/deploy-notes.md`; requires Gmail OAuth credential + Pensieve label re-selection after import.

**Quick health check** (verify active workflows + credentials):
```bash
ssh pi4 "docker exec n8n n8n export:workflow --all --output=/home/node/wf.json && docker cp n8n:/home/node/wf.json /tmp/wf.json" && python3 -c "import json; [print(w['id'],'|',w['name'],'|',w.get('active')) for w in json.load(open('/tmp/wf.json'))]"
ssh pi4 "docker exec n8n n8n export:credentials --all --output=/home/node/creds.json && docker cp n8n:/home/node/creds.json /tmp/creds.json" && python3 -c "import json; [print(c['id'],'|',c['name'],'|',c['type']) for c in json.load(open('/tmp/creds.json'))]"
```
**Note**: `n8n export:workflow --all` only exports **non-archived** (active or inactive-but-not-deleted) workflows. Workflows deleted via the REST API are soft-archived and excluded from the export — a reduced count after deletion is expected behaviour, not data loss.

**Deleting a workflow** (soft-archive via REST — excluded from future exports):
```bash
# Pre-condition: commit a full export as backup before deleting (git-tracked artefact)
API_KEY=$(ssh pi4 "cat /opt/n8n/api-key")
ssh pi4 "curl -s -X DELETE 'http://localhost:88/api/v1/workflows/<id>' -H 'X-N8N-API-KEY: $API_KEY'"
# Verify: re-export and confirm count = (before − deleted)
```

**Updating workflow JSON programmatically**: when modifying n8n workflow nodes that contain
multi-line `jsCode` or `jsonBody` strings, use Python to load/modify/dump — avoids JSON
double-escaping errors that make the Edit tool unreliable for these files:
```python
import json
with open('workflows/foo.json') as f: wf = json.load(f)
for n in wf['nodes']:
    if n['id'] == 'node-target': n['parameters']['jsCode'] = "new code..."
with open('workflows/foo.json', 'w') as f: json.dump(wf, f, indent=2, ensure_ascii=False)
```

**Testing n8n Code nodes**: extract `jsCode` from the workflow JSON at runtime (no copy-paste
drift), execute in `node:vm` with a mocked context (mock `require('fs')`, `require('path')`,
`$()` helper). See `artefacts/task-009/test_gmail_workflow.js` as the canonical example.
Run with: `/root/.nvm/versions/node/v24.12.0/bin/node artefacts/<task-id>/test_*.js`

**n8n HTTP Request timeout**: always set `"options": {"timeout": 10000}` on HTTP Request nodes calling internal APIs (Pi4 localhost). Default is 300s — a hung n8n API stalls the workflow for 5 min.

**Timezone in n8n Code nodes**: use `Intl.DateTimeFormat('nl-NL', {timeZone: 'Europe/Amsterdam', hour: 'numeric', hour12: false})` to get Amsterdam local hour. Handles DST automatically. Avoid raw UTC offsets.

**Finding Telegram chat_id from n8n execution history**: `GET /api/v1/executions/{id}?includeData=true` → parse JSON for `"chat":{"id":...}` pattern. Useful when no config stores the chat_id and you need the user's personal ID.

**n8n workflow JSON patterns**:
- Use `specifyBody: "json"` + `jsonBody: "={{ $json.obj }}"` when passing an object — `specifyBody: "string"` silently mangles complex payloads (e.g. long base64 bodies)
- Avoid `?.` optional chaining in IF node expressions — use `$json.commit ? 'ok' : ''` instead
- Never interpolate `$json.error` into Telegram `text` fields — GitHub API error strings contain backticks/underscores that trigger Telegram "can't parse entities"
- `continueOnFail: true` at node level handles 404s gracefully (e.g. GET a file that may not exist yet)
- **n8n REST API `limit=N` is a hard cap**: if querying `/api/v1/workflows` or `/api/v1/executions` with `limit=N`, add a comment noting the assumption (e.g. `// assumes ≤100 active workflows`). If the instance may exceed N, check `nextCursor` in the response and loop until null. Document the pagination requirement in `deploy-notes.md`.
- **Code node returning `[]` stops the downstream chain**: no IF/Switch node needed for guard conditions (e.g. night hours, empty results, length mismatch). Return `[]` to halt; return `[{json: {...}}]` to continue.

**main/develop divergence**: n8n commits via GitHub API go directly to `main` (default branch, no hooks).
Operational files written by n8n (e.g. `tasks/telegram-inbox.md`) must exist on `main`, not just `develop`.
When creating such files locally, also push them to `main` via the GitHub API or a fast-track merge.
