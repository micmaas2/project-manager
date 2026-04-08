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
| DocUpdater | YAML | Sonnet | Docs/changelog | Updated docs |
| docs-readme-writer | built-in | Sonnet | README/module docs | Docs written |
| SelfImprover | YAML | Sonnet | Lessons/proposals | proposals.md written |
| revise-claude-md | built-in | Sonnet | CLAUDE.md session learnings | CLAUDE.md updated |

**Built-in Claude Code agents** (invoke via `Agent` tool with `subagent_type`):
- `code-quality-reviewer` — security + quality review; runs parallel to Reviewer
- `docs-readme-writer` — README/module docs; runs parallel to DocUpdater
- `claude-md-management:revise-claude-md` — apply session learnings to CLAUDE.md (session end)
- `claude-md-management:claude-md-improver` — full CLAUDE.md audit (on demand)

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
  - If an external ID (e.g. message ID, record ID) is passed to a downstream step: validate
    it is non-null/non-empty at point of use; throw a descriptive error if absent
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

---

## Workflow Orchestration

0. **Session start — mandatory checklist (run in order before any task work)**:
   - [ ] **Telegram inbox**: Read `tasks/telegram-inbox.md`. If items exist below the header, promote each to `tasks/backlog.md` (next BL ID, EPIC-003, project_manager, P2, new, today), clear the file to the two-line header, commit on a feature branch.
   - [ ] **Lessons**: Read `tasks/lessons.md`; state the 3 most recent rows before planning. Lessons govern tooling choices and approach — do not repeat captured mistakes.
   - [ ] **Catch-up SelfImprover**: For every `status: done` task in `tasks/queue.json`, verify `artefacts/<artefact_path>/improvement_proposals.md` exists. If absent, run SelfImprover for that task first.

1. **Plan first (mandatory)**: ALWAYS enter plan mode before any non-trivial task (3+ steps or architectural decisions). Plans are written to `/root/.claude/plans/` (auto-managed by plan mode).
2. **Subagents**: offload research, exploration, and parallel analysis to keep main context clean — one task per subagent; pass only pointers (task_id, file paths), never embed full content.
3. **Token minimization**: agents receive only task_id; they read their own context from files. No large context copied between invocations. Stop after each deliverable.
4. **Verify before done**: never mark complete without proving it works. Ask: "Would a staff engineer approve this?"
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
6b. **End-of-session proposal review (human gate)**: At the end of each PM session, read `artefacts/*/improvement_proposals.md` for all tasks completed this session. Present each pending proposal to the user as: target file, proposed change, rationale, APPROVE / REJECT. Apply only approved proposals immediately (edit file, commit). Log rejected proposals with reason in `tasks/lessons.md`. Never apply a proposal without explicit user approval. After all proposals are resolved, invoke the `revise-claude-md` built-in agent to bake session learnings into CLAUDE.md and commit the result. **Cross-file consistency check**: when a proposal introduces a format definition (e.g. improvement_proposals.md schema), verify the format is identical in both CLAUDE.md and the relevant agent YAML before presenting to the user. **Proposal response format**: user replies `APPROVE: P1, P3 / REJECT: P2` — apply all approved in one pass, log rejections. **SelfImprover dedup**: when running SelfImprover for multiple tasks in a session, collect all proposals before presenting — remove duplicates and proposals targeting text already present in the target file.
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

**Logs**:
- `logs/audit.jsonl` — append-only, one JSON object per line: `{timestamp, agent, task_id, action, status}`
- `logs/token_log.jsonl` — per-run token accounting: `{timestamp, agent, task_id, token_estimate}`

---

## n8n Workflow Deployment (Pi4)

SSH alias: `pi4` (192.168.1.10). n8n runs as Docker container `n8n`.
GitHub PAT for project-manager API calls: `/opt/n8n/github-pat` on Pi4.

**Vault location**: `/opt/obsidian-vault/` exists on Pi4 only — not on the local host.
Explore agents run locally; always use `ssh pi4 "find /opt/obsidian-vault ..."` for vault state.

**Pi4 Python packages**: verify before deploying scripts: `ssh pi4 "python3 -c 'import X'"`.
Install missing packages with `pip3 install <pkg> --break-system-packages` (Debian-managed env).
`beautifulsoup4` installs as `beautifulsoup4` but imports as `bs4`.

**Hyphenated script filenames**: `migrate-vault.py` cannot be imported directly in Python tests.
Use `importlib.util.spec_from_file_location("name", "path/to/script.py")` instead.

**Testing hyphenated-filename scripts**: Use `importlib.util.spec_from_file_location("module_name", path)` in all test files for scripts with hyphens in their names — this is the only safe import path. See `artefacts/task-005/test_migrate_vault.py` as the canonical example.

**Task unit tests**: test files live in `artefacts/<task-id>/test_*.py`; run with `python3 -m pytest artefacts/<task-id>/test_*.py -v`. Use `importlib.util.spec_from_file_location` + `unittest.mock.patch.object` to test scripts without making them importable packages.

**GitHub API commits (stdlib)**: read a file with `GET /repos/{repo}/contents/{path}?ref={branch}` → decode `base64.b64decode(resp["content"])`; write with `PUT /repos/{repo}/contents/{path}` + `{"content": base64.b64encode(...).decode(), "sha": <existing_sha_or_omit_for_new>, "branch": ...}`. No `requests` package needed — `urllib.request` suffices.

**Deploy sequence** (all three steps required):
```bash
# 1. Prep: inject workflow id + strip tags
python3 -c "import json; wf=json.load(open('workflow.json')); wf['id']='<UUID>'; wf.pop('tags',None); json.dump(wf,open('/tmp/wf.json','w'))"
# 2. Import + publish
scp /tmp/wf.json pi4:/tmp/wf.json && ssh pi4 "docker cp /tmp/wf.json n8n:/tmp/wf.json && docker exec n8n n8n import:workflow --input=/tmp/wf.json && docker exec n8n n8n publish:workflow --id=<UUID>"
# 3. Restart
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

**n8n workflow JSON patterns**:
- Use `specifyBody: "json"` + `jsonBody: "={{ $json.obj }}"` when passing an object — `specifyBody: "string"` silently mangles complex payloads (e.g. long base64 bodies)
- Avoid `?.` optional chaining in IF node expressions — use `$json.commit ? 'ok' : ''` instead
- Never interpolate `$json.error` into Telegram `text` fields — GitHub API error strings contain backticks/underscores that trigger Telegram "can't parse entities"
- `continueOnFail: true` at node level handles 404s gracefully (e.g. GET a file that may not exist yet)

**main/develop divergence**: n8n commits via GitHub API go directly to `main` (default branch, no hooks).
Operational files written by n8n (e.g. `tasks/telegram-inbox.md`) must exist on `main`, not just `develop`.
When creating such files locally, also push them to `main` via the GitHub API or a fast-track merge.
