# Kanban Board

Updated by ProjectManager after every task status change.
Source of truth: `tasks/queue.json`. This board is a human-readable view.

Last updated: 2026-04-07T00:00:00Z

---

## Backlog
_(items in backlog.md not yet in queue)_

- BL-009 CCAS: Quick Win #3 Infrastructure Validation (P2 — next after MVP2 closeout)
- BL-010/011 CCAS: Inventory parametrization + enhance-jenkinsfile-s4hana (P2)
- BL-019/020 performance_HPT: Scaffold repo + HPT Dashboard Phase 1 (P2)
- BL-016 pensieve: Configure Obsidian Clipper (P2 — low automation value, manual)
- BL-012/013 pi-homelab: Security hardening Pi 4 + Pi 5 (P1 — blocked-manual)
- BL-026 pi-homelab: Regular patching (P1 — blocked-ssh, depends on BL-012/013)
- BL-031 PM: git worktrees investigation (P3)
- BL-033 New project: grocery price comparison (P3)
- BL-035 New project: school-ai — AI learning assistant for primary school kids (P2)

---

## Ready
_(in queue.json with status: pending)_

- **task-007** [MVP2] PM: Human-gated improvement proposals to YAML/CLAUDE.md (S-002-4)
- **task-008** [DEMO] PM: Laptop backlog and Pensieve capture mechanism (BL-034)
- **task-009** pensieve: Activate Gmail capture workflow in n8n (BL-015)

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
