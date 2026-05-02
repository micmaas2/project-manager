# Project Manager — Multi-Agent Automation System

**v0.8.0** — Extended pipeline with built-in Claude Code agents. SelfImprover loop fully operational with enforcement gates.
8 tasks delivered end-to-end. Cross-project management active across 7 sibling projects (MVP3 in progress).

A hierarchical multi-agent system that builds automations and scripts across projects.
One orchestrator (ProjectManager, Opus 4.6) reads a task queue and spawns a six-stage
specialist pipeline (all Sonnet 4.6).

Designed for Claude Pro with built-in rate-limit resume support: if a run is interrupted,
tasks are marked `paused` and resume automatically on the next invocation.

---

## Architecture

```
ProjectManager (Opus 4.6)           — orchestrator: reads queue, validates tasks, spawns agents
  ├── Builder         (Sonnet 4.6)  — generates scripts, playbooks, and automation artefacts
  ├── Reviewer        (Sonnet 4.6)  — checks quality, security, and arch compliance
  ├── code-quality-reviewer (built-in, parallel with Reviewer)
  ├── Tester          (Sonnet 4.6)  — validates artefacts with fixture-based tests, writes test_report.md
  ├── DocUpdater      (Sonnet 4.6)  — updates CLAUDE.md, README, CHANGELOG after each task
  ├── docs-readme-writer (built-in, parallel with DocUpdater)
  ├── SelfImprover    (Sonnet 4.6)  — appends lessons to tasks/lessons.md; writes improvement_proposals.md for human review
  └── revise-claude-md (built-in)   — applies session learnings to CLAUDE.md at session end
```

State is entirely file-based. All agents read and write `tasks/queue.json` and
`artefacts/<task_id>/`. No database, no server.

### Task lifecycle

```
pending → in_progress → review → test → doc-update → self-improve → done
                ↑           |       |
                └───────────┘       │  (CHANGES_REQUESTED loops back to builder)
                        ↑           │
                        └───────────┘  (FAIL loops back to builder)

Any step → paused  (on rate limit; resumes at resume_from step)
```

### Pipeline guards

- **Preflight**: ProjectManager checks prerequisites (e.g., `jq` available) before spawning Builder.
  Tasks with unmet prerequisites are blocked with an error in `audit.jsonl`.
- **Self-improvement loop**: SelfImprover runs after every pipeline PASS. It appends to
  `tasks/lessons.md` and writes `improvement_proposals.md`. Proposals require human approval
  before being applied — the PM presents them at end-of-session (step 6b). Current lessons count: 8
  (see `tasks/lessons.md`).
- **Artefact path audit**: ProjectManager runs `ls artefacts/` before assigning any new task ID
  to avoid directory conflicts with informally pre-populated paths.
- **MVP ordering gate**: All stories in lower MVP phases must be `done` before any higher-phase
  task is queued.

---

## Quick Start

### 1. Add a task to the queue

Open `tasks/queue.json` and add an entry to the `tasks` array. Every task **must** include
the full MVP template — the ProjectManager will reject and backlog any task missing required
fields.

```json
{
  "tasks": [
    {
      "id": "task-001",
      "title": "Generate Ansible role for NTP sync",
      "status": "pending",
      "assigned_to": null,
      "target_project": "/opt/claude/CCAS",
      "created": "2026-04-04",
      "resume_from": null,
      "notes": [],
      "mvp": {
        "doel": "Create an Ansible role that configures NTP on all managed hosts using chrony.",
        "niet_in_scope": ["monitoring integration", "Windows hosts"],
        "acceptatiecriteria": [
          "Role applies without errors on Ubuntu 22.04",
          "chrony service is enabled and running after apply",
          "Idempotent: re-run produces no changes"
        ],
        "security_arch_impact": "Low — no secrets; uses OS package manager only",
        "tests_required": "ansible-lint; molecule converge + idempotency test",
        "definition_of_done": "Review APPROVED, test pass rate >= 90%, artefact committed to feature branch",
        "rollback_plan": "Delete role directory; no host state is changed until playbook is run",
        "incident_owner": "Michel Maas",
        "privacy_dpia": "No — no personal data involved",
        "cost_estimate": "< 0.10 EUR (Sonnet 4.6 builder + reviewer run)"
      }
    }
  ]
}
```

### 2. Invoke the ProjectManager agent

In Claude Code, open the project_manager directory and run:

```
/agent manager
```

Or from a Claude Code session with this directory as context, say:

> "Run the ProjectManager agent on the task queue."

The ProjectManager will:

**Session start (before any task work):**
- Step 0: Read `tasks/telegram-inbox.md`; promote items to `backlog.md` and clear the inbox
- Step 0b: Read `tasks/lessons.md`; list the 3 most recent rows in the plan preamble as active context

**Per task:**
1. Read `tasks/queue.json` and find the next `pending` or `paused` task
2. Run preflight: validate MVP template fields and check declared prerequisites (e.g., `jq`)
3. Update the task status to `in_progress` and spawn the Builder
4. The Builder writes output to `artefacts/<task_id>/` and hands off to Reviewer
5. The Reviewer writes `review.md` and hands off to Tester (or loops back to Builder)
6. The Tester runs fixture-based tests, writes `test_report.md`, and hands off to DocUpdater (or loops back to Builder)
7. The DocUpdater updates CLAUDE.md, README, and CHANGELOG; writes `doc_update.md`
8. The SelfImprover appends to `tasks/lessons.md` and writes `improvement_proposals.md`; status set to `done`

**Session end:**
- Step 6b: PM reviews all `artefacts/*/improvement_proposals.md` files with `Status: REQUIRES_HUMAN_APPROVAL`. User approves or rejects each proposal before it is applied.

Each step is logged to `logs/audit.jsonl` and `logs/token_log.jsonl`.

### 3. Check results

```
artefacts/<task_id>/                      Primary artefact (script, playbook, config)
artefacts/<task_id>/build_notes.md        Builder assumptions and test instructions
artefacts/<task_id>/review.md             Reviewer decision (APPROVED / CHANGES_REQUESTED)
artefacts/<task_id>/test_report.md        Tester results (PASS / FAIL, pass rate)
artefacts/<task_id>/doc_update.md         DocUpdater change summary
artefacts/<task_id>/improvement_proposals.md   SelfImprover proposals applied next session
artefacts/<task_id>/fixtures/             Controlled test fixtures (e.g., empty/seeded queue)
logs/audit.jsonl              Full audit trail (one JSON object per line)
logs/token_log.jsonl          Token usage per agent per run
```

### 4. Useful one-liners

```bash
# View kanban board (task status at a glance)
cat tasks/kanban.md

# Run the queue status reporter
bash artefacts/task-001/queue-status.sh

# Run the audit log summary
bash artefacts/task-002/audit-summary.sh
```

---

## Scripts

Standalone CLI scripts in `scripts/`:

| Script | Description |
|---|---|
| `scripts/cross-kanban.py` | Unified cross-project kanban view; reads `tasks/queue.json`, groups active tasks by project, outputs one `### project` section per project with `\| Status \| Task ID \| Title \|` table; projects with no active tasks omitted |
| `scripts/pm-priority.py` | Multi-project priority ranking; reads backlog and outputs ranked BL items (BL-004, S-003-1) |
| `scripts/token_cap_enforcer.py` | Preflight cap check: reads `tasks/queue.json`, finds the given task, exits 1 with ALERT if `token_estimate` exceeds 400,000 (80% of 500k project cap), exits 0 otherwise |

```bash
# Generate a unified kanban view grouped by project
python3 scripts/cross-kanban.py

# Override the queue path (e.g., for testing with a fixture)
python3 scripts/cross-kanban.py --queue path/to/queue.json

# Check whether a task's token estimate is within the project cap
python3 scripts/token_cap_enforcer.py --task-id task-016

# Override the queue path (e.g., for testing with a fixture)
python3 scripts/token_cap_enforcer.py --task-id task-016 --queue path/to/queue.json
```

---

## Rate-Limit Recovery

Claude Pro enforces rate limits. This system handles them without data loss:

**What happens automatically:**
- The active agent writes any partial output to `artefacts/<task_id>/partial/`
- The task status is set to `paused`
- The `resume_from` field is set to the last completed step name
- The agent stops cleanly

**What you do:**
1. Wait for the rate limit window to pass (typically a few minutes to an hour)
2. Re-invoke the ProjectManager: `/agent manager`
3. The ProjectManager reads the `paused` task, reads `resume_from`, and continues from that step

No manual editing of `queue.json` is required. A `paused` task is treated the same as
`pending` — it is picked up on the next run.

---

## Telegram Backlog Intake

Backlog items can be submitted from Telegram without opening a Claude session. Send a message starting with `BACKLOG:` to the Pensieve bot:

```
BACKLOG: Add dark mode to the dashboard
```

The n8n workflow in `pensieve/workflows/telegram-capture.json` handles this path:

```
Telegram "BACKLOG: <title>"
  → n8n strips prefix, fetches tasks/telegram-inbox.md from GitHub
  → appends "- YYYY-MM-DD: <title>" and commits back
  → bot replies "✅ Backlog item queued: <title>" with commit URL
     OR "❌ Kon niet opslaan. Stuur het opnieuw." on failure
```

**At the start of every PM session (step 0, mandatory):** The ProjectManager reads `tasks/telegram-inbox.md`. For each item it:
1. Assigns the next BL ID and adds a row to `tasks/backlog.md`
2. Clears `tasks/telegram-inbox.md` (preserves the header comment)
3. Commits both files together before any other work

This keeps `backlog.md` as the single authoritative list while letting new items arrive asynchronously between sessions.

**Note:** `telegram-inbox.md` is written by n8n via the GitHub Contents API using a PAT with `contents:write` scope on this repo. Direct edits to the file are safe — n8n fetches the current SHA before each write to avoid conflicts.

---

## Queue Schema Reference

`tasks/queue.json` contains a single object with a `tasks` array. Each task object:

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | yes | Unique task identifier (e.g. `task-001`) |
| `title` | string | yes | Short human-readable title |
| `status` | string | yes | One of: `pending`, `in_progress`, `review`, `test`, `done`, `paused` |
| `assigned_to` | string\|null | yes | `"builder"`, `"reviewer"`, `"tester"`, or `null` |
| `target_project` | string | yes | Absolute path to the sibling project this task targets |
| `created` | string | yes | ISO date (`YYYY-MM-DD`) |
| `resume_from` | string\|null | yes | Step name to resume from after a `paused` state |
| `notes` | array | yes | Reviewer/Tester feedback strings appended on loop-back |
| `mvp` | object | yes | Full MVP template (see below) |

**MVP template fields** (all required — ProjectManager rejects tasks missing any):

| Field | Description |
|---|---|
| `doel` | One-sentence goal |
| `niet_in_scope` | Array of explicit exclusions |
| `acceptatiecriteria` | Array of 3–5 measurable acceptance criteria |
| `security_arch_impact` | Security and architecture impact note |
| `tests_required` | Which tests to run (unit / integration / regression) |
| `definition_of_done` | Checklist for task completion |
| `rollback_plan` | Steps to undo this change + owner |
| `incident_owner` | Name / role responsible if something goes wrong |
| `privacy_dpia` | Whether a DPIA is needed and a brief note |
| `cost_estimate` | Estimated token cost in EUR |

---

## Agent Reference

| Agent | Model | Max tokens/run | Allowed tools | Stops at |
|---|---|---|---|---|
| ProjectManager | Opus 4.6 | 5,000 | Read, Write, Edit, Glob, Agent | Approved MVP plan dispatched |
| Builder | Sonnet 4.6 | 10,000 | Read, Write, Edit, Bash, Glob, Grep | Artefact written to `artefacts/<id>/` |
| Reviewer | Sonnet 4.6 | 10,000 | Read, Write, Glob, Grep | `review.md` written |
| Tester | Sonnet 4.6 | 10,000 | Read, Write, Bash, Glob, Grep | `test_report.md` written |
| DocUpdater | Sonnet 4.6 | 5,000 | Read, Write, Edit, Glob | `doc_update.md` written |
| SelfImprover | Sonnet 4.6 | 5,000 | Read, Write, Edit, Glob | `improvement_proposals.md` written; `lessons.md` appended |

Agent YAML definitions live in `.claude/agents/`. Each definition includes `prompt`,
`policy`, `owner`, and `incident_owner` fields.

**Model labelling:** all Opus outputs are labelled `[Opus]`; all Sonnet outputs are labelled `[Sonnet]`.

---

## Directory Layout

```
.claude/
  agents/                    Agent YAML definitions (manager, builder, reviewer, tester,
                             doc-updater, self-improver)
tasks/
  queue.json                 Task queue — single source of truth for task state
  queue.schema.json          JSON Schema for queue validation
  kanban.md                  Human-readable board view (updated by ProjectManager)
  backlog.md                 Backlogged items not yet queued (with BL IDs)
  telegram-inbox.md          Staging file for BACKLOG: items sent via Telegram (cleared each session)
  epics.md                   Epics and stories
  lessons.md                 Lessons learned — appended by SelfImprover after each PASS
  todo.md                    Session planning notes (not committed to main)
artefacts/
  <task_id>/                 One subdirectory per task
    build_notes.md           Builder assumptions, test instructions, known limits
    review.md                Reviewer decision and findings
    test_report.md           Tester pass/fail report
    doc_update.md            DocUpdater change summary
    improvement_proposals.md SelfImprover proposals (applied at next session start)
    fixtures/                Controlled test inputs (e.g., empty_audit.jsonl, seeded_queue.json)
    partial/                 Partial output saved on rate-limit interruption
logs/
  audit.jsonl                Append-only audit trail (agent, action, task, timestamp)
  token_log.jsonl            Token usage per agent per run
docs/                        Architecture decision records; project-registry.md
  project-registry.md        Authoritative registry of all managed projects and their artefacts
  n8n-deployment.md          n8n Pi4 deployment patterns (Docker, import gotchas, workflow JSON)
  python-testing.md          Python testing patterns (hyphenated filenames, Docker-only packages, root-path quirks)
hooks/                       pre-commit + commit-msg hooks (symlinked to .git/hooks/)
```

---

## Managed Projects

This system is project-agnostic. Tasks specify a `target_project` path. 7 projects currently managed:

| Path | GitHub remote | Status | Notes |
|---|---|---|---|
| `/opt/claude/project_manager/` | micmaas2/project-manager | Active | This system |
| `/opt/claude/CCAS/` | (no remote) | Active | SAP infrastructure automation (Ansible-based) |
| `/opt/claude/pi-homelab/` | micmaas2/pi-homelab | Blocked | Security hardening blocked on manual passwd steps |
| `/opt/claude/pensieve/` | micmaas2/pensieve | Queued | Summarisation, tagging, folder structure improvements backlogged |
| `/opt/claude/genealogie/` | micmaas2/genealogie | Active | Genealogy tooling (GEDCOM-based) |
| `/opt/claude/performance_HPT/` | micmaas2/performance-twin | Active | Performance / HPT tooling |
| `/opt/claude/project1/` | (no remote) | Inactive | Generic project skeleton |

**Notable completed cross-project work:**
- CCAS BL-007/BL-008: `hana_os_users` Ansible role + SAP start/stop ordering implemented
- CCAS task-003: `feature/hana-os-users` merged to develop, stale branch deleted
- task-048 (BL-102): automation-recommender scan across all 7 projects; 10 adopt items registered (BL-104–BL-113) covering hooks, MCP servers, and skills; current highest BL ID: BL-113
- CCAS task-051 (BL-106): ansible-lint pre-commit hook deployed to all 6 CCAS sub-repos via absolute symlink; blocks commits on playbook/role YAML violations

**Blocked items requiring manual user steps:**
- pi-homelab Pi 4: run `sudo passwd pi` and remove nopasswd sudoers entry
- pi-homelab Pi 5: `ssh-copy-id` from each laptop, `sudo passwd pi`, remove nopasswd sudoers

---

## Delivered Artefacts

| Task | Artefact | Description |
|---|---|---|
| task-001 | `artefacts/task-001/queue-status.sh` | Prints a colour-coded summary of `tasks/queue.json` by status |
| task-002 | `artefacts/task-002/audit-summary.sh` | Summarises `logs/audit.jsonl` by agent and action; requires `jq` |
| task-003 | — | CCAS: verified `feature/hana-os-users` merged; stale branch deleted |
| task-006 (S-002-3) | CLAUDE.md + `manager.yaml` | PM reads 3 most recent lessons at session start (step 0b) |
| task-007 (S-002-4) | `self-improver.yaml` + CLAUDE.md | Human-gated improvement proposals: PM presents at session end (step 6b); user approves/rejects before application |
| task-011 | `artefacts/task-011/pensieve-sync.sh` | Bash cron script that runs `git pull` on `/opt/obsidian-vault` (Pi4) every 15 minutes to keep the Obsidian vault in sync with `micmaas2/pensieve`. Deploy instructions in `artefacts/task-011/deploy-notes.md`. |
| task-048 | `artefacts/task-048/research_report.md` | Cross-project automation-recommender scan across all 7 managed projects; 10 BL items registered (BL-104–BL-113) covering hooks, MCP servers, and skills recommendations per project. |
| task-051 (BL-106) | `artefacts/task-051/` | CCAS: ansible-lint pre-commit hook (`hooks/pre-commit`) installed as absolute symlink across all 6 CCAS sub-repos; `scripts/install-pre-commit-hooks.sh` updated to use symlinks instead of file copies. |
| task-055 (BL-108) | `artefacts/task-055/` | genealogie: ruff lint + format pre-commit hook (`/opt/claude/genealogie/hooks/pre-commit`); blocks commits on Python lint/format violations; auto-format step included with re-stage instructions. |
| task-056 (BL-109) | `artefacts/task-056/` | genealogie: SQLite schema validator pre-commit hook; `hooks/validate_db.py` runs `py_compile` syntax check + `init_db()` dry-run against `:memory:` SQLite; appended as a validation block in `/opt/claude/genealogie/hooks/pre-commit`. |

All artefacts passed the full 6-agent pipeline (Builder → Reviewer → Tester → DocUpdater → SelfImprover).
Fixture-based testing is in place: each task's `artefacts/<id>/fixtures/` holds controlled inputs
used by the Tester independent of live system state.

---

## Security Hooks

A **PreToolUse** hook intercepts every `Edit`, `Write`, and `MultiEdit` tool call in Claude Code and blocks writes containing known-dangerous patterns before they reach the filesystem.

### Script location

```
hooks/security_reminder_hook.py    Local patched copy (stable — used in settings.json)
```

The hook is registered in `.claude/settings.json`:

```json
"hooks": {
  "PreToolUse": [
    {
      "matcher": "Edit|Write|MultiEdit",
      "hooks": [
        {
          "type": "command",
          "command": "python3 /opt/claude/project_manager/hooks/security_reminder_hook.py"
        }
      ]
    }
  ]
}
```

### Patterns blocked

| Pattern | Risk |
|---|---|
| `eval(` | Arbitrary code execution |
| `os.system` / `from os import system` | Command injection |
| `pickle` | Arbitrary code execution via deserialization |
| `.innerHTML =` / `.innerHTML=` | XSS |
| `dangerouslySetInnerHTML` | XSS (React) |
| `document.write` | XSS |
| `new Function` | Code injection |
| `child_process.exec` | Command injection (Node.js) |
| `.github/workflows/*.yml` path | GitHub Actions command injection |
| `re.compile(…re.DOTALL…$…)` (correlated) | `$` as stop anchor is bypassed by `re.DOTALL`; use `\Z` instead |

A match blocks the write (exit code 2) and prints a remediation message to stderr. Each pattern is blocked once per session per file; subsequent occurrences in the same session are allowed through (so legitimate fixes are not blocked). Set `ENABLE_SECURITY_REMINDER=0` to disable the hook for an entire session.

**Patch note**: the local copy removes the broad `exec(` substring from the `child_process_exec` rule (present in the upstream plugin), keeping only the more specific `child_process.exec` and `execSync(` patterns. This prevents false positives on SQL `.execute(` calls and similar names.

### Testing the hook

Simulate a blocked write directly with a JSON payload on stdin:

```bash
HOOK="hooks/security_reminder_hook.py"

# Should BLOCK (exit 2) — os.system pattern
printf '{"session_id":"t1","tool_name":"Write","tool_input":{"file_path":"/tmp/t.py","content":"os.system(\"id\")"}}' \
  | python3 "$HOOK"
echo "Expected exit 2, got: $?"

# Should ALLOW (exit 0) — clean content
printf '{"session_id":"t2","tool_name":"Write","tool_input":{"file_path":"/tmp/t.py","content":"x = 1"}}' \
  | python3 "$HOOK"
echo "Expected exit 0, got: $?"
```

Debug log (written on errors only): `/tmp/security-warnings-log.txt`

### Workflow guard hook

A second PreToolUse hook (`hooks/workflow_guard_hook.py`) enforces two CLAUDE.md must-always-follow rules at edit time:

| Tool | Trigger | Block reason |
|---|---|---|
| `Bash` | command contains `--no-verify` | No legitimate use of hook-bypass in this codebase |
| `Write` on `tasks/queue.json` | `"status": "done"` with empty `"artefact_path"` | Tasks cannot be closed without an artefact path (Write-only; Edit fragments are not checked) |

Both hooks are registered in `.claude/settings.json` under `hooks.PreToolUse`.

### Extending to other projects

See `artefacts/task-047/extension-guide.md` for step-by-step deployment instructions for:
- Other local projects (pensieve, pi-homelab, CCAS, genealogie)
- Remote hosts (MAS on Pi4 at `192.168.1.10`)

The extension guide includes the exact JSON snippet to add to any project's `.claude/settings.json` and a merge-safe Python one-liner for settings files that already have other keys.

---

## Branching and Commit Format

```
main      ← stable releases only (tagged, never committed to directly)
develop   ← integration branch (all features merge here)
feature/* ← all work starts here
```

Never commit directly to `main` or `develop`. The pre-commit hook enforces this.

```
[AREA] Brief description

- Detailed change 1
- Detailed change 2
```

Valid areas: `ROLE`, `DOCS`, `TEST`, `FIX`, `REFACTOR`, `PLAYBOOK`, `JENKINS`, `INVENTORY`, `AGENT`

---

## Contributing — Adding a New Agent

1. Create `.claude/agents/<name>.yaml` with required fields: `name`, `model`, `prompt`, `policy`, `owner`, `incident_owner`
2. Policy must specify `allowed_tools`, `max_tokens_per_run`, `require_human_approval`, `audit_logging`, `external_calls_allowed`
3. The agent must append to `logs/audit.jsonl` and `logs/token_log.jsonl` at each step
4. The agent must handle rate-limit interruption: write partial output, set status `paused`, set `resume_from`
5. Label all outputs `[Opus]` or `[Sonnet]` depending on model
6. Update this README's Agent Reference table
7. Add a CHANGELOG entry under `[Unreleased]`
8. If the agent produces a new artefact type, add it to the Directory Layout and the task lifecycle diagram above

**Pipeline slot guidance:**
- Agents that produce output artefacts go in the Builder/Reviewer/Tester slots
- DocUpdater runs after Tester PASS — do not merge doc-writing into Builder
- SelfImprover always runs last; it writes to `tasks/lessons.md` and `artefacts/<id>/improvement_proposals.md`
