# Changelog

All notable changes to this project will be documented here.
Follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) conventions.
Format within each version: `Added`, `Changed`, `Fixed`, `Removed`.

---

## [task-047] — 2026-04-28
### Added
- `hooks/security_reminder_hook.py`: PreToolUse hook blocking dangerous code patterns at edit time. Patterns guarded: eval, dynamic code execution, unsafe DOM operations, and dangerous serialization libraries. Patched: false-positive check removed; state files restricted to mode `0o600`.
- `artefacts/task-047/extension-guide.md`: Guide for extending the hook with additional security patterns.

### Changed
- `.claude/settings.json`: Registered `security_reminder_hook.py` as a PreToolUse hook to enforce pattern blocking on every Edit operation.

---

## [task-044] — 2026-04-21
### Changed
- `mas/src/config.py`: Upgraded `LLM_PRIMARY_MODEL` default from `claude-3-5-sonnet-20240620` to `claude-sonnet-4-6` (Pydantic settings).
- `mas/.env.example`, `mas/.env.production.example`: Updated model string to `claude-sonnet-4-6` in example env files.
- `mas/src/cost_tracker.py`: Added pricing entries for `claude-sonnet-4-6` and `claude-haiku-4-5` (EUR per 1M tokens) to keep cost accounting current with deployed models.
- Commits `fedcac5` + `c4cf82f` on branch `feature/task-021-bookworm-base` in `/opt/mas/`; Tester PASS (129/148, 0% regression).

---

## [task-043] — 2026-04-19
### Added
- `artefacts/task-043/research_report.md`: Two-round research across marketplace and built-in Claude Code skills (16+ skills evaluated). Top 3 candidates identified for cross-project adoption: `security-guidance` hook (BL-101), `claude-automation-recommender` (BL-102), and `skill-creator` evals for pm-* skills (BL-103).
- `tasks/backlog.md`: BL-101 (security-guidance hook adoption), BL-102 (claude-automation-recommender cross-project rollout), BL-103 (skill-creator evals for pm-* skills).

---

## [task-042] — 2026-04-19
### Changed
- `.claude/agents/tester.yaml`: Downgraded model from `claude-sonnet-4-6` to `claude-haiku-4-5-20251001`; Label line updated to `[Haiku]`. Tester (BugHunter) no longer requires Sonnet-level reasoning — structured test execution fits Haiku's capability profile.
- `CLAUDE.md`: Model Policy table updated — Tester row now shows Haiku; Sonnet bullet "testing" removed; Haiku bullet expanded to include "Tester (BugHunter)"; Label bullet updated to reflect change. Complexity thresholds and prompt caching eligibility notes added from task-039 design doc.
- All 6 `.claude/agents/*.yaml` files: Explicit version pin strategy locked — each YAML pins a full versioned model string (e.g. `claude-haiku-4-5-20251001`) rather than a generic alias. M-1 mirror verified: all 6 YAML model fields match CLAUDE.md policy table.

### Added
- `artefacts/task-042/decision.md`: Documents the explicit version pin strategy rationale, model assignments per agent, and M-1 mirror verification results.

---

## [task-041] — 2026-04-19
### Changed
- `.claude/commands/pm-run.md`: Added explicit plan-mode opt-out directive at line 3 — "do not enter plan mode. This skill executes a task that is already planned and queued. Proceed directly to the Steps below without calling EnterPlanMode." Prevents ambiguous plan-mode activation caused by the general CLAUDE.md "plan first" mandate conflicting with /pm-run's execution-only intent.

### Added
- `artefacts/task-041/analysis.md`: Evaluation of /pm-run plan-mode gate options. Documents root cause (no explicit gate existed; CLAUDE.md mandate caused false positive triggers), evaluates Option A (post-activation recovery) vs Option B (explicit opt-out preamble), and recommends Option B as the preventative solution.

---

## [task-040] — 2026-04-19
### Added
- `artefacts/task-040/audit_report.md`: Full agent model usage audit across all 6 `.claude/agents/*.yaml` files and 4 built-in subagents. Key findings: (1) Tester→Haiku downgrade recommended ($0.0066/run savings, 73% Tester-stage cost reduction); (2) Reviewer and ProjectManager downgrades NOT recommended (reasoning complexity requirements documented); (3) Haiku version string inconsistency flagged — YAML pins `claude-haiku-4-5-20251001` while CLAUDE.md uses generic alias (housekeeping item). PM stage accounts for 89.3% of pipeline cost; primary lever is PM prompt efficiency, not model swaps.

---

## [task-039] — 2026-04-18
### Added
- artefacts/task-039/design-doc.md: cost-aware model routing design — Tester downgrade Sonnet→Haiku, PM prompt caching eligibility, complexity thresholds for future agents
- artefacts/task-039/claude-md-additions.md: proposed CLAUDE.md rule additions pending human review

---

## [task-038] — 2026-04-18
### Changed
- pm-run.md: expanded step 5 into explicit pipeline sub-steps (5a–5e) with /compact markers at Builder→Reviewer and Reviewer→Tester boundaries to reduce context carry-over between stages

---

## [task-035] — 2026-04-17

### Changed
- `CLAUDE.md`: Applied 5 token-reduction rewrites from `artefacts/task-026/rewrite-plan.md` — saved ~930 tokens from CLAUDE.md baseline. Key changes: PM Skills table → 1 line, Opus advisor escalation condensed, policy schema YAML → 1 line, Telegram inbox step shortened, Python testing patterns moved to new `## Python Testing Patterns` section, Pending deployments removed, dashboard-preview note shortened.
- `.claude/agents/manager.yaml`: Multi-Project Priority Order condensed to 1 line; redundant onboarding note removed.
- `.claude/agents/reviewer.yaml`: Opus Advisor Escalation condensed from 9 lines to 2 lines.

### Added
- `CLAUDE.md ## Python Testing Patterns`: New dedicated section consolidating Python testing gotchas previously scattered in n8n section (importlib, sys.modules pre-injection, unwritable paths, fixture files).
- `artefacts/task-035/`: build_notes.md, review.md (APPROVED), test_report.md (21/21 PASS).
- `tasks/backlog.md`: BL-097 (/pm-run plan mode design review), BL-098 (model version pins review).

---

## [task-034] — 2026-04-17

### Added
- `artefacts/task-034/skills-review.md`: Research review of the Claude Code optimization repo (`affaan-m/everything-claude-code`). Repo contains 183+ skills and 48 specialized agents. Identified 11 applicable patterns for this MAS setup across learning, token cost, eval, debugging, and onboarding categories. Registered BL-085 to BL-095 in `tasks/backlog.md`. Notable findings: continuous-learning-v2 instinct model (BL-085), context budget MCP server accounting (BL-086), agent eval harness (BL-087), hooks-over-prompts principle (BL-088), strategic compaction at stage boundaries (BL-092), cost-aware model routing with prompt caching (BL-093), agent introspection debugging protocol (BL-094), structured 4-phase project onboarding (BL-095). Review: APPROVED. Tests: 5/5 PASS.

---

## [task-032] — 2026-04-15

### Added
- `pensieve/docs/pat-rotation.md`: GitHub PAT rotation runbook for n8n on Pi4. Documents affected systems (n8n credential `GitHub PAT — project-manager`, Telegram Capture workflow, `/opt/n8n/github-pat` file), step-by-step rotation procedure with fine-grained PAT guidance, post-rotation verification (UI test, end-to-end Telegram test, file prefix check), quarterly reminder template, rollback path with time-to-restore estimate, and troubleshooting table (BL-057).

---

## [task-031] — 2026-04-15

### Removed
- `n8n (Pi4)`: Deleted 5 stale workflows — 3 duplicate inactive "Pensieve — Telegram Capture" entries (IDs: LXNulqGKD9lVgkCy, E1d8DxnKUHokwMh8, hqMPoEDxmHYxprhd) and 2 unnamed placeholder workflows ("My workflow", "My workflow 2"). Full backup committed before deletion (`artefacts/task-031/wf_backup_before.json`). Active canonical workflow `WgIO3y4KvGOxHWu0` retained and verified operational (execution 309, 2026-04-15T06:37 UTC). n8n now has 5 workflows total, all with clear purpose and ownership. Review: `artefacts/task-031/review.md` APPROVED.

---

## [task-030] — 2026-04-14

### Added
- `pensieve/workflows/n8n-healthcheck.json`: Scheduled n8n workflow for monitoring idle workflows during waking hours (07:00–23:00 Amsterdam). Checks every 15 minutes if any active workflow has been idle >2h; sends Telegram alert to personal chat via main Telegram account. Deployed and active on Pi4 as workflow `b5717a69-a46c-484e-ac44-aa65e143acfd`. Unit tests: 20/20 passing (`artefacts/task-030/test_healthcheck_workflow.js`). Deploy notes: `artefacts/task-030/deploy-notes.md`.

---

## [task-020] — 2026-04-14

### Fixed
- `mas_personal_assistant`: LLM birth-date hallucination in the daily facts feature (BL-065). `DailyFactsAgent` now fetches verified born-today candidates from the Wikipedia REST API before building the LLM prompt. New `_get_born_today_candidates()` method parses all births for the current date, sorts intellectuals/scientists first (ranked by `_INTELLECTUAL_KEYWORDS` frozenset) then oldest-first, and returns the top 12 candidates. ASCII control characters are stripped from `description` and `extract` fields before returning (prompt injection guard). `_build_fact_generation_prompt()` extended with a `candidates` parameter — when candidates are available the prompt lists verified names; falls back to free-form generation if the Wikipedia call returns empty. 11/11 unit tests passing (`artefacts/task-020/test_daily_facts_regression.py`).

---

## [task-019] — 2026-04-13

### Added
- `mas_personal_assistant`: Telegram sender chat_id authentication guard in `telegram_listener.py` (BL-060). Inbound messages from unauthorized senders (chat_id ≠ TELEGRAM_CHAT_ID) are dropped with WARNING log. Fails open when TELEGRAM_CHAT_ID is not configured (backward-compatible). 8/8 unit tests passing. Committed to micmaas2/mas_personal_assistant main (1b3b139).

---

## [Unreleased]

### task-037 — CLAUDE.md size reduction [2026-04-17]
- Reduced CLAUDE.md from 39,310 to 29,830 chars (24% reduction, target was ≤35,000)
- Moved n8n Pi4 deployment patterns to docs/n8n-deployment.md
- Moved Python testing patterns to docs/python-testing.md
- All operational rules preserved; pointer lines added in CLAUDE.md

### Added
- `scripts/cross-kanban.py`: unified cross-project kanban view; reads queue.json, groups active tasks (paused/in_progress/review/test/pending) by project, outputs one `### project` section per project with status|task-id|title table; projects with no active tasks omitted; handles empty queue gracefully (task-017, S-003-3, BL-064, EPIC-003)
- `.claude/commands/pm-status.md` step 3 updated to invoke `python3 scripts/cross-kanban.py` below the kanban
- `scripts/token_cap_enforcer.py`: CLI preflight script; reads `token_estimate` from `tasks/queue.json` for a given `--task-id`; exits 1 with ALERT if estimate exceeds 400,000 (80% of 500k cap), exits 0 with OK otherwise; 9/9 unit tests passing (BL-050, S-003-4)
- `.claude/agents/manager.yaml`: step 5 updated to explicitly invoke `python3 scripts/token_cap_enforcer.py --task-id <task_id>` as part of token cap preflight before task execution
- `scripts/pm-priority.py`: multi-project priority ranking; reads queue.json + backlog.md, outputs ranked markdown table (paused → project_manager → P1>P2>P3 → oldest)
- `/pm-status` (pm-status.md): now invokes pm-priority.py as step 1 for ranked task view

### Fixed
- `tasks/queue.json`: task-015/016/017 titles updated to include BL-NNN references for priority lookup

### Added
- task-013: `/pm-plan` skill — PI/Refinement planning session workflow; guides user through backlog review, epic/story mapping, MVP template drafting, and queue.json commit in one repeatable flow. All placeholders resolved from named sources; feature branch commit includes queue.json + backlog.md + kanban.md + epics.md (BL-003, S-003-2)

### Fixed
- task-012: daily_facts_agent — 7-day person dedup window prevents same person appearing multiple days in a row; PERSON field added to LLM prompt, person_name stored in generation_params, case-normalised comparison, multi-line FACT parsing fixed (BL-039)

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
