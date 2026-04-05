# Changelog

All notable changes to this project will be documented here.
Follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) conventions.
Format within each version: `Added`, `Changed`, `Fixed`, `Removed`.

---

## [Unreleased]

### Added
- `artefacts/task-001/queue-status.sh` — bash script that reads `tasks/queue.json`
  and prints a formatted task count summary grouped by all 6 statuses (pending,
  in_progress, paused, review, test, done). Accepts optional queue file path argument.
  Requires `jq`. Passes `bash -n`; 100% test pass rate (5/5 tests).

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
