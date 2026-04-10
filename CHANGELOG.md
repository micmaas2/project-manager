# Changelog

All notable changes to this project will be documented here.
Follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) conventions.
Format within each version: `Added`, `Changed`, `Fixed`, `Removed`.

---

## [Unreleased]

### Added
- task-011: pensieve-sync.sh cron script for Pi4 — git-pulls micmaas2/pensieve into /opt/obsidian-vault every 15 min; includes flock guard, --ff-only merge, log sanitization, stash-pop conflict detection (BL-036)
- **Built-in agent pipeline integration**: `code-quality-reviewer`, `docs-readme-writer`, and `claude-md-management:revise-claude-md` wired into the standard task pipeline. Review and doc stages now run YAML agents + built-in agents in parallel; `revise-claude-md` runs at session end after proposals are resolved.
- **Session step 0c — SelfImprover catch-up**: PM scans all `done` tasks at session start for missing `improvement_proposals.md`; runs SelfImprover for any that lack it. Prevents silent pipeline gaps from manual or interrupted runs.
- **SelfImprover verification gate**: ProjectManager verifies SelfImprover produced output (proposals or new lessons entry) before setting a task to `done`. Re-runs SelfImprover if neither exists.
- **SelfImprover security rule**: when a security pattern was implemented correctly but not driven by the MVP template, SelfImprover must always raise a template-targeting proposal — not just a lesson.
- **Proposal dedup + response format**: proposal review now documents the expected response format (`APPROVE: P1, P3 / REJECT: P2`) and requires deduplication of cross-task proposals before presenting to user.
- **Artefact path preflight in PM planning**: `ls artefacts/` now called out explicitly in the PM Planning Session step, not just in the queue section.
- **MVP template additions**: `no_external_deps: true/false` field + outbound HTTP security sub-checklist under `Security/arch impact`.
- **BL-036**: Pi4 vault sync — pull pensieve repo into Obsidian vault (cron or webhook).
- **SelfImprover backfill**: ran SelfImprover for tasks 005, 006-lessons, 007-gate, 008; 11 new lessons added, 9 proposals generated and reviewed.
- **EPIC-002 complete (MVP2 — Self-Improvement & Learning Loop)**: all stories done.
- **Session step 0b** (task-006 / S-002-3): ProjectManager reads `tasks/lessons.md` at the start
  of every session and lists the 3 most recent rows in its plan preamble as active context.
  Prevents recurrence of already-documented failure patterns without manual re-reading.
- **Session step 6b — human-gated improvement proposals** (task-007 / S-002-4): SelfImprover
  writes structured `improvement_proposals.md` files (one `## Proposal N` section per proposal,
  with `Target file`, `Change`, `Rationale`, and `Status: REQUIRES_HUMAN_APPROVAL` fields).
  PM presents all pending proposals at end-of-session; user approves or rejects each before
  application. Prevents unreviewed changes to agent YAMLs and CLAUDE.md.
- **Artefact path audit rule**: PM runs `ls artefacts/` before assigning new task IDs to prevent
  directory conflicts with pre-existing paths.
- **MVP ordering gate**: tasks in higher MVP phases may not be queued until all lower-phase
  stories are `done`.
- **Backlog sync rule**: BL entries updated to `done` in the same commit as queue task completion.
- task-008 (BL-034): Laptop backlog / Pensieve capture — queued, pending.
- task-009 (BL-015): Gmail capture workflow in n8n — queued, pending.
- `artefacts/task-002/audit-summary.sh` — bash script that reads `logs/audit.jsonl`
  and prints a formatted summary of agent actions grouped by agent name and action type.
  Accepts optional log file path argument. Requires `jq >= 1.6`. Passes `bash -n`;
  100% test pass rate (5/5 tests). Validates MVP2 preflight + fixtures improvements.
- `artefacts/task-001/queue-status.sh` — bash script that reads `tasks/queue.json`
  and prints a formatted task count summary grouped by all 6 statuses (pending,
  in_progress, paused, review, test, done). Accepts optional queue file path argument.
  Requires `jq`. Passes `bash -n`; 100% test pass rate (5/5 tests).

### Changed
- `.claude/agents/self-improver.yaml`: `improvement_proposals.md` output format now explicitly
  documented in the prompt (section headers, field names, `Status: REQUIRES_HUMAN_APPROVAL`).
  `require_human_approval: true` policy field enforces this at runtime.

## [0.1.0] — 2026-04-04

### Added
- Directory structure: `tasks/`, `artefacts/`, `logs/`, `scripts/`, `docs/`, `hooks/`
- `tasks/queue.json` — file-based task queue with status lifecycle (`pending` → `in_progress` → `review` → `test` → `done`) and `paused` state for rate-limit recovery
- `.claude/agents/manager.yaml` — ProjectManager orchestrator (Opus 4.6): reads queue, validates MVP template, spawns agents, writes audit logs
- `.claude/agents/builder.yaml` — Builder agent (Sonnet 4.6): generates scripts/playbooks, writes to `artefacts/<task_id>/`, hands off to Reviewer
- `.claude/agents/reviewer.yaml` — Reviewer agent (Sonnet 4.6): checks artefacts for correctness, security, and arch compliance, writes `review.md`
- `.claude/agents/tester.yaml` — Tester agent (Sonnet 4.6): validates artefacts, enforces 90% pass threshold, writes `test_report.md`
- `hooks/pre-commit` — pre-commit hook enforcing branch protection (`main`/`develop` direct commits blocked) and documentation update requirements; symlinked to `.git/hooks/pre-commit`
- `CLAUDE.md` — primary project instructions covering agent roles, MVP template schema, governance, token policy, and git workflow
- `README.md` — project overview with Quick Start, queue schema reference, and rate-limit recovery guide
