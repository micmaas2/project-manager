# Project Manager — Multi-Agent Automation System

A hierarchical multi-agent system that builds automations and scripts across projects.
One orchestrator (ProjectManager, Opus 4.6) reads a task queue and spawns specialist
Builder, Reviewer, and Tester agents (all Sonnet 4.6).

Designed for Claude Pro with built-in rate-limit resume support: if a run is interrupted,
tasks are marked `paused` and resume automatically on the next invocation.

---

## Architecture

```
ProjectManager (Opus 4.6)       — orchestrator: reads queue, validates tasks, spawns agents
  ├── Builder    (Sonnet 4.6)   — generates scripts, playbooks, and automation artefacts
  ├── Reviewer   (Sonnet 4.6)   — checks quality, security, and arch compliance
  └── Tester     (Sonnet 4.6)   — validates artefacts, writes test_report.md
```

State is entirely file-based. All agents read and write `tasks/queue.json` and
`artefacts/<task_id>/`. No database, no server.

### Task lifecycle

```
pending → in_progress → review → test → done
                ↑           |       |
                └───────────┘       │  (CHANGES_REQUESTED loops back to builder)
                        ↑           │
                        └───────────┘  (FAIL loops back to builder)

Any step → paused  (on rate limit; resumes at resume_from step)
```

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
1. Read `tasks/queue.json` and find the next `pending` or `paused` task
2. Validate the MVP template fields
3. Update the task status to `in_progress` and spawn the Builder
4. The Builder writes output to `artefacts/<task_id>/` and hands off to Reviewer
5. The Reviewer writes `review.md` and hands off to Tester (or loops back to Builder)
6. The Tester writes `test_report.md` and sets status to `done` (or loops back to Builder)

Each step is logged to `logs/audit.jsonl` and `logs/token_log.jsonl`.

### 3. Check results

```
artefacts/<task_id>/          Primary artefact (script, playbook, config)
artefacts/<task_id>/build_notes.md    Builder assumptions and test instructions
artefacts/<task_id>/review.md         Reviewer decision (APPROVED / CHANGES_REQUESTED)
artefacts/<task_id>/test_report.md    Tester results (PASS / FAIL, pass rate)
logs/audit.jsonl              Full audit trail (one JSON object per line)
logs/token_log.jsonl          Token usage per agent per run
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

Agent YAML definitions live in `.claude/agents/`. Each definition includes `prompt`,
`policy`, `owner`, and `incident_owner` fields.

**Model labelling:** all Opus outputs are labelled `[Opus]`; all Sonnet outputs are labelled `[Sonnet]`.

---

## Directory Layout

```
.claude/
  agents/             Agent YAML definitions (manager, builder, reviewer, tester)
tasks/
  queue.json          Task queue — the single source of truth for task state
  todo.md             Session planning notes (not committed to main)
  lessons.md          Lessons learned — updated after any correction
artefacts/
  <task_id>/          One subdirectory per task
    build_notes.md    Builder assumptions, test instructions, known limits
    review.md         Reviewer decision and findings
    test_report.md    Tester pass/fail report
    partial/          Partial output saved on rate-limit interruption
logs/
  audit.jsonl         Append-only audit trail (agent, action, task, timestamp)
  token_log.jsonl     Token usage per agent per run
scripts/              Generated automation scripts (after Tester PASS)
docs/                 Architecture decision records
hooks/                pre-commit hook (symlinked to .git/hooks/pre-commit)
```

---

## Target Projects

This system is project-agnostic. Tasks specify a `target_project` path. Current sibling projects:

| Path | Description |
|---|---|
| `/opt/claude/CCAS/` | SAP infrastructure automation — Ansible-based, multiple repos |
| `/opt/claude/pi-homelab/` | Raspberry Pi Home Assistant deployment (Pi 4 and Pi 5) |
| `/opt/claude/project1/` | Generic project skeleton |

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
