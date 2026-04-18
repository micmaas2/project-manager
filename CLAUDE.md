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

**Releasing to main**: `git push origin develop:main` — pre-commit hook blocks direct commits on main/develop, so local merge always fails. Use refspec push only.
If main has GitHub API commits that develop lacks (diverged), use `--force-with-lease` after syncing via a feature branch: `git checkout -b feature/sync && git checkout origin/main -- <file> && git commit ... && merge into develop`, then `git push origin develop:main --force-with-lease`.

**Merging feature branches with conflicts into develop**: conflict-free `git merge --no-ff -m "..."` on develop works. When a merge has conflicts, `git commit` after resolution is blocked — abort on develop, resolve on a `feature/sync-X` branch, then `git push origin feature/sync-X:develop` and pull. Avoid `git stash` when branches have diverged — cascading conflicts.

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

**Reviewer confidence scoring**: each finding in review.md includes `confidence: N (1-100)` — Builder loops only on findings >= 80; findings < 80 are routed to build_notes.md only (no loop required). Definition: confidence = certainty the finding is a real issue (not a false positive). M-1 mirror: this definition must match reviewer.yaml and builder.yaml verbatim.

**Built-in Claude Code agents** (invoke via `Agent` tool with `subagent_type`):
- `code-quality-reviewer` — security + quality review; runs parallel to Reviewer; for any regex using `re.DOTALL`, flag use of `$` as a stop anchor (use `\Z` instead) and require a multi-line fixture in Tester; for any documentation that recommends one format as "preferred" (e.g. fine-grained PAT over classic), verify ALL code snippets use that preferred format first — if both forms are valid, add a comment noting both formats
- `docs-readme-writer` — README/module docs; runs parallel to DocUpdater
- `claude-md-management:revise-claude-md` — apply session learnings to CLAUDE.md (session end); invoke via `Skill` tool, NOT `Agent` tool (`subagent_type` does not work for `claude-md-management:*`)
- `claude-md-management:claude-md-improver` — full CLAUDE.md audit (on demand); invoke via `Skill` tool
- **Explore-type subagents cannot write files**: when DocUpdater/docs-readme-writer are spawned as `subagent_type: Explore`, they return proposed content but cannot apply edits. The parent agent must read the agent's output and apply the file changes directly — do not wait for the Explore agent to write.

**Grep tool vs Bash grep**: use the `Grep` tool (not `grep` via Bash) when the search pattern contains backticks or special shell characters — Bash eval will fail with `unexpected EOF while looking for matching backtick`.

**Shell script pre-submission check** (Builder must verify before handing off to Reviewer):
- `bash -n <script>` must exit 0 — **for shell scripts only**; Python scripts use `python3 -m py_compile <script>` instead (`bash -n` cannot parse Python and will spuriously fail)
- If cron/daemon: log guard, flock, SSH identity, logrotate — all present?
- If outbound git/SSH: auth path exported explicitly?
- Log output sanitized (ANSI + control chars stripped) before writing to file?
- If the script accepts file-path arguments (e.g. `--queue`, `--backlog`, `--config`): add a `_safe_path()` containment guard that resolves the path and asserts `_WORKSPACE_ROOT in path.parents` — exit 1 with a descriptive error if not. Document the workspace root as a module-level constant.

**Prompt writing discipline**: All agent prompts MUST use imperative voice addressed to the agent itself ("You will", "Do not", "Stop if"). Never narrate what other agents do — instead state this agent's responsibility relative to other agents' outputs. Orchestration sequencing (waiting, parallelism) belongs in design docs, not embedded in agent prompts.

**Opus advisor escalation**: For ambiguous arch/security decisions, spawn Opus sub-agent (model: claude-opus-4-6) with single `ADVISOR_CONSULT: <question>` + Context + Options. Note in `build_notes.md` under "Advisor Consults". Triggers: architecture tradeoff with no clear winner; security decision outside established patterns; scope ambiguity. Do NOT use for routine decisions.

**Cross-file rule mirroring (M-1 pattern)**: Enumerated rules that appear in both CLAUDE.md and agent YAMLs can silently accumulate orphan entries. When editing either file, verify rule counts and text match in both directions. Tester must include a regression guard for any task that modifies mirrored content: (a) rule-count equality check across all copies, (b) absence check for any rule that was removed.

**M-1 copy-paste rule**: when mirroring a definition across CLAUDE.md and agent YAMLs, copy-paste verbatim — never paraphrase. Unicode vs ASCII symbol variants (`≥` vs `>=`) and synonym substitutions ("issue" vs "defect") both silently break the M-1 verbatim-match contract.

**Agent YAML policy schema**: the pre-commit hook enforces that every `.claude/agents/*.yaml` contains all 5 required policy fields (`allowed_tools`, `max_tokens_per_run`, `require_human_approval`, `audit_logging`, `external_calls_allowed`). A commit that adds or modifies an agent YAML without all 5 fields will be rejected.

**PM Skills** (`.claude/commands/`): `/pm-start` `/pm-run` `/pm-status` `/pm-plan` `/pm-propose` `/pm-close` `/pm-lessons` — and `skill-creator` (Marketplace, for new/revised PM skills).

**Plugin marketplace**: official Anthropic plugins at `/root/.claude/plugins/marketplaces/claude-plugins-official/plugins/` — browse with `ls` for available commands, agents, and skills; check `README.md` in each plugin dir.

**Skill authoring rules**: Skills are executable command prompts (`.claude/commands/*.md`).
- Every angle-bracket placeholder must include an explicit resolution instruction naming the source file and lookup pattern — do not assume the reader will infer where data lives.
- Test all placeholders manually before committing: simulate a fresh session with no prior context and verify every `<placeholder>` can be resolved without ambiguity.
- **Security filter ordering: inline, not post-hoc** — inspect for sensitive patterns (password, secret, api_key, etc.) per-item before appending to any buffer; a post-hoc filter is logically bypassed when the buffer already contains sensitive data.

Agent definitions live in `.claude/agents/[name].yaml`. Required fields: `name`, `prompt`, `policy`, `owner`, `incident_owner`.

**Policy schema per agent** (5 required fields): `allowed_tools`, `max_tokens_per_run`, `require_human_approval` (TRUE if Bash/Write/Edit in tools), `audit_logging`, `external_calls_allowed`.

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
  - If the task rotates a credential or secret (PAT, API key, token):
      - Rollback section must include "Estimated time-to-restore: N-M minutes"
      - Estimate covers worst-case manual steps (e.g. generate new token + 2 config updates)
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
- Runbook verification commands that read secret files: always pipe through `head -c N` or `grep -c`; add a warning note discouraging bare `cat` on recorded/shared terminals (shell history risk)

**Observability**:
- Audit trail: who, agent, action, time, artefact
- Token logs: per run and cumulative per task
- Metrics: tokens/run, median latency, success rate, test pass rate
- Alerts: token overspend, policy violations, regressions

**80% cap alert (preflight)**: before starting a task, sum all agent token estimates for that task. If total > 400,000 (80% of 500k cap), halt with: `ALERT: Task <id> estimated tokens (<n>) exceed 80% of project cap. Reduce scope or split task before proceeding.`

**Token rewrite acceptance criteria**: express as savings delta (e.g. "save ≥900 tokens"), not absolute post-rewrite totals. The baseline shifts between plan date and execution date — absolute targets become unachievable when CLAUDE.md grows between task creation and execution.

---

## Workflow Orchestration

0. **Session start — mandatory checklist (run in order before any task work)**:
   - [ ] **Fetch remote**: Run `git fetch origin` before reading any operational file. n8n commits go directly to `origin/main` via GitHub API — without fetching, inbox items are invisible.
   - [ ] **Telegram inbox**: Run `git show origin/main:tasks/telegram-inbox.md`. Promote each item below the header to `tasks/backlog.md` (next BL ID, EPIC-003, project_manager, P2, new, today), then clear inbox (commit on feature branch → develop → push main). **Dedup**: `grep -i "<keyword>" tasks/backlog.md` before adding. **Routing prefix**: n8n matches exact `BACKLOG: ` (uppercase, colon, space) — `backlog` or `BACKLOG:item` silently dropped.
   - [ ] **Lessons**: Read `tasks/lessons.md`; state the 3 most recent rows before planning. Lessons govern tooling choices and approach — do not repeat captured mistakes.
   - [ ] **Catch-up SelfImprover**: For every `status: done` task in `tasks/queue.json`, verify `artefacts/<artefact_path>/improvement_proposals.md` exists. If absent (directory may not exist either), run SelfImprover for that task — it must create the directory and file from the task definition in queue.json.
   - [ ] **ExitPlanMode denial**: if the user denies ExitPlanMode, use AskUserQuestion to clarify intent before re-attempting — the user may be redirecting to a side task first, not rejecting the plan outright.
   - [ ] **ExitPlanMode mid-skill recovery**: if plan mode activates unexpectedly during a PM skill run (e.g. /pm-propose), write a minimal plan file summarising remaining steps, call ExitPlanMode, then continue the skill after approval.

1. **Plan first (mandatory)**: ALWAYS enter plan mode before any non-trivial task (3+ steps or architectural decisions). Plans are written to `/root/.claude/plans/` (auto-managed by plan mode).
2. **Subagents**: offload research, exploration, and parallel analysis to keep main context clean — one task per subagent; pass only pointers (task_id, file paths), never embed full content.
3. **Token minimization**: agents receive only task_id; they read their own context from files. No large context copied between invocations. Stop after each deliverable.
4. **Verify before done**: never mark complete without proving it works. Ask: "Would a staff engineer approve this?"
   **Artefact minimum for git-only tasks**: even when no code is produced, create `artefacts/<task-id>/verification.md` capturing: commands run (e.g. `git log --oneline`, `ls` of key files), their output, and a PASS/FAIL verdict per acceptance criterion. Tasks with no artefact directory cannot be retrospected by SelfImprover.
   **Architecture/research task Definition of Done**: must include "all `NEW:` proposals in the review document are registered as BL items in `tasks/backlog.md`" — SelfImprover does not do this automatically; it is a required explicit step before marking done. For tasks reviewing an external repo/course: minimum 2 research rounds; second round must fetch SKILL.md / agent source files, not just directory listings.
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
6b. **End-of-session proposal review (human gate)**: At the end of each PM session, read `artefacts/*/improvement_proposals.md` for all tasks completed this session. Present each pending proposal to the user as: target file, proposed change, rationale, APPROVE / REJECT. Apply only approved proposals immediately (edit file, commit). Log rejected proposals with reason in `tasks/lessons.md`. Never apply a proposal without explicit user approval. After all proposals are resolved, invoke `revise-claude-md` via the `Skill` tool (not `Agent`) to bake session learnings into CLAUDE.md and commit the result. **Cross-file consistency check**: when a proposal introduces a format definition (e.g. improvement_proposals.md schema), verify the format is identical in both CLAUDE.md and the relevant agent YAML before presenting to the user. **Proposal response format**: user replies `APPROVE: P1, P3 / REJECT: P2` — apply all approved in one pass, log rejections. **SelfImprover dedup**: when running SelfImprover for multiple tasks in a session, collect all proposals before presenting — remove duplicates and proposals targeting text already present in the target file. **Scanning for pending proposals**: `find artefacts -name "improvement_proposals.md" | xargs grep -lE "^\*\*Status\*\*: REQUIRES_HUMAN_APPROVAL"` — `^` prevents false positives from body text quoting the pattern; do NOT use `grep -rl`. **pm-propose commit discipline**: after applying approved proposals that edit CLAUDE.md, immediately commit on the current feature branch before proceeding — do not leave session-learning edits unstaged across a context boundary.
7. **Autonomous bug fixing**: when given a bug report, fix it — point at logs/errors, then resolve.
8. **Demand elegance (balanced)**: pause and ask "Is there a more elegant way?" before finalising any non-trivial design. Skip for simple fixes — do not over-engineer.
9. **Minimal impact**: touch only what is strictly necessary; avoid side effects on untouched code or config. If you must change something adjacent, flag it explicitly.
10. **Explain with diagrams**: when explaining architecture or non-obvious decisions, prefer ASCII diagrams over prose where they add clarity.

**PM Planning Session**: invoke ProjectManager with "planning" intent to review, reprioritize, and onboard. PM asks for confirmation before queuing. **Preflight**: `ls artefacts/` before assigning IDs — use descriptive suffix if path exists.
**Phase gate announcement rule**: when /pm-start detects a phase gate is reached, the announcement section must end with an explicit yes/no approval question before printing the queue summary — do not leave the user with a statement and no prompt.
**MVP ordering gate**: During PM planning, check epics.md for any stories with status `planned` in lower MVP phases before queuing higher-phase work. All stories in a phase must be `done` before the next phase is prioritized.

**Task tracking**:
- Active queue → `tasks/queue.json`
- Backlog + scope-drift → `tasks/backlog.md`
- Kanban view → `tasks/kanban.md`
- Epics & stories → `tasks/epics.md`
- Plan files → `/root/.claude/plans/` (registered in `docs/project-registry.md`)
- Lessons → `tasks/lessons.md` (append-only table: `| Date | Agent | Lesson | Applied To |`)
- Improvement proposals → `artefacts/<task_id>/improvement_proposals.md` (one `## Proposal N` section per proposal, fields: **Target file**, **Change** (diff or description), **Rationale**, **Status:** `REQUIRES_HUMAN_APPROVAL` → `APPROVED` / `REJECTED: <reason>`)
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

**Logs** (`logs/` is gitignored — never `git add logs/`):
- `logs/audit.jsonl` — append-only, one JSON object per line: `{timestamp, agent, task_id, action, status}`
- `logs/token_log.jsonl` — per-run token accounting: `{timestamp, agent, task_id, token_estimate}`
  Every sub-agent (Builder, Reviewer, Tester, DocUpdater, SelfImprover) must write one entry per invocation — not just ProjectManager. This enables per-agent token observability and identifies highest-cost pipeline stages.

---

## n8n Workflow Deployment (Pi4)

SSH alias: `pi4` (192.168.1.10). n8n runs as Docker container `n8n`.
GitHub PAT: `/opt/n8n/github-pat` on Pi4. See `docs/n8n-deployment.md` for: full deploy sequence, import gotchas, Pi4 Docker patterns, workflow JSON patterns.

**Vault location**: `/opt/obsidian-vault/` exists on Pi4 only — not on the local host.
Explore agents run locally; always use `ssh pi4 "find /opt/obsidian-vault ..."` for vault state.

**Pensieve repo active branch**: always run `git -C /opt/claude/pensieve branch --show-current` before committing to the pensieve repo — it may be on a long-lived feature branch (e.g. `feature/task-029-capture-subworkflow`) rather than `main`. Doc commits intended for `main` must target the correct branch.

**dashboard-preview.md**: cron-updated every 15 min on Pi4 — commit on feature branch before pm-close (timestamp + done count only).

**GitHub API commits (stdlib)**: read: `GET /repos/{repo}/contents/{path}?ref={branch}` → `base64.b64decode(resp["content"])`; write: `PUT /repos/{repo}/contents/{path}` + `{"content": base64.b64encode(...).decode(), "sha": <sha_or_omit>, "branch": ...}`. Use `urllib.request`.

**main/develop divergence**: n8n commits via GitHub API go directly to `main` (default branch, no hooks).
Operational files written by n8n (e.g. `tasks/telegram-inbox.md`) must exist on `main`, not just `develop`.
When creating such files locally, also push them to `main` via the GitHub API or a fast-track merge.

---

## Python Testing Patterns

See `docs/python-testing.md` for: hyphenated filenames, Docker-only packages, unwritable paths as root, path-guarded fixtures, pytest run command.
