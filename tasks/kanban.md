# Kanban Board

Updated by ProjectManager after every task status change.
Source of truth: `tasks/queue.json`. This board is a human-readable view.

Last updated: 2026-04-14T00:00:00Z

---

## Backlog
_(items in backlog.md not yet in queue)_

- BL-009 CCAS: Quick Win #3 Infrastructure Validation (P2)
- BL-010/011 CCAS: Inventory parametrization + enhance-jenkinsfile-s4hana (P2)
- BL-019/020 performance_HPT: Scaffold repo + HPT Dashboard Phase 1 (P2)
- BL-016 pensieve: Configure Obsidian Clipper (P2 — low automation value, manual)
- BL-012/013 pi-homelab: Security hardening Pi 4 + Pi 5 (P1 — blocked-manual)
- BL-026 pi-homelab: Regular patching (P1 — blocked-ssh, depends on BL-012/013)
- BL-035 school-ai: AI learning assistant new project (P2)
- BL-038 project_manager: Mempalace-style memory investigation (P3)
- BL-031 PM: git worktrees investigation (P3)
- BL-033 New project: grocery price comparison (P3)

---

## Ready
_(in queue.json with status: pending)_

- **task-025** genealogie: Merge develop to main, tag v2.x (BL-018)
- **task-026** Token reduction analysis: CLAUDE.md + agent YAMLs (BL-049)
- **task-027** pm-healthcheck.sh: hooks, schema, YAML, logs check (BL-051)
- **task-028** Token spend dashboard in /pm-status (BL-052)
- **task-029** pensieve: Refactor shared nodes into n8n sub-workflow (BL-054)
- **task-030** pensieve: n8n health-check workflow (BL-055)
- **task-031** pensieve: Clean up stale n8n workflows (BL-056)
- **task-032** pensieve: PAT rotation runbook (BL-057)

---

## In Progress
_(status: in_progress)_

_(empty)_

---

## Review
_(status: review — awaiting Reviewer)_

_(empty)_

---

## Testing
_(status: test — awaiting Tester)_

_(empty)_

---

## Done
_(status: done — pipeline complete, artefact delivered)_

- **task-024** project_manager: Review Anthropic agent skills course (BL-045) [2026-04-14]
- **task-023** project_manager: Mark resolved improvement_proposals.md files as done (BL-046) [2026-04-14]
- **task-022** project_manager: Wire claude-md-improver into /pm-close every 5th session (BL-048) [2026-04-14]
- **task-021** pi-homelab: Migrate health-api base image bullseye → bookworm (BL-014) [2026-04-14]
- **task-020** mas daily facts: birth-date regression fix (BL-065) [2026-04-14]
- **task-019** mas_agent: Telegram sender chat_id auth guard (BL-060) [2026-04-13]
- **task-018** mas_agent: Fix mas-frontend Docker healthcheck (BL-059) [2026-04-13]
- **task-017** project_manager: Cross-project kanban view script (BL-064, S-003-3) [2026-04-13]
- **task-016** project_manager: Python token-cap-enforcer script (BL-050, S-003-4) [2026-04-13]
- **task-015** project_manager: Multi-project priority ranking in PM (BL-004, S-003-1) [2026-04-11]
- **task-014** Architecture review — MAS/Claude Code, pensieve, mas_agent (BL-047) [2026-04-11]
- **task-013** PM: /pm-plan skill — PI/Refinement planning session (BL-003, S-003-2) [2026-04-11]
- **task-012** project_manager: Fix MAS daily facts — birth-date match + 7-day dedup (BL-039) [2026-04-11]
- **task-011** pi-homelab: Pi4 vault sync — pull pensieve into Obsidian vault (BL-036) [2026-04-11]
- **task-009** pensieve: Activate Gmail capture workflow in n8n (BL-015) [2026-04-07]
- **task-008** PM: Laptop backlog/Pensieve capture — `scripts/capture.py` (BL-034) [2026-04-07]
- **task-007** PM: Human-gated improvement proposals (S-002-4) — MVP2 COMPLETE [2026-04-07]
- **task-006** PM: lessons.md read at session start (S-002-3) [2026-04-07]
- **task-005** pensieve: Retroactive vault quality improvement script [2026-04-07]
- **task-004** pensieve: Improved captures — richer summaries, tagging, topic folders [2026-04-05]
- **task-003** CCAS: feature/hana-os-users verified merged + stale branch deleted [2026-04-05]
- **task-002** Audit log summary script — `artefacts/task-002/audit-summary.sh` [2026-04-05]
- **task-001** Queue status reporter script — `artefacts/task-001/queue-status.sh` [2026-04-05]

---

## Blocked / Paused
_(status: paused — rate-limited or awaiting human input)_

- **BL-012** pi-homelab: Pi 4 passwd hardening — waiting for user to run `sudo passwd pi` + remove nopasswd sudoers on Pi 4
- **BL-013** pi-homelab: Pi 5 security prereqs — waiting for user to: (1) `ssh-copy-id pi@<pi5-ip>` from each laptop, (2) `sudo passwd pi`, (3) remove nopasswd sudoers
