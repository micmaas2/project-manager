# Kanban Board

Updated by ProjectManager after every task status change.
Source of truth: `tasks/queue.json`. This board is a human-readable view.

Last updated: 2026-04-05T12:00:00Z

---

## Backlog
_(items in backlog.md not yet in queue)_

- BL-007a CCAS: Merge feature/hana-os-users → ccas-jenkins develop → task-003 ✅ queued
- BL-009 CCAS: Quick Win #3 Infrastructure Validation
- BL-012/013 pi-homelab: Security hardening (blocked-manual — user passwd steps needed first)
- BL-015 pensieve: Gmail capture activation
- BL-023/024/025 pensieve: Improved summarisation, tagging, folder structure (new)

---

## Ready
_(in queue.json with status: pending)_

_(empty)_

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

- **task-003** CCAS: feature/hana-os-users verified merged + stale branch deleted [2026-04-05]
- **task-002** Audit log summary script — `artefacts/task-002/audit-summary.sh` [2026-04-05]
- **task-001** Queue status reporter script — `artefacts/task-001/queue-status.sh` [2026-04-05]

---

## Blocked / Paused
_(status: paused — rate-limited or awaiting human input)_

- **BL-012** pi-homelab: Pi 4 passwd hardening — waiting for user to run `sudo passwd pi` + remove nopasswd sudoers on Pi 4
- **BL-013** pi-homelab: Pi 5 security prereqs — waiting for user to: (1) `ssh-copy-id pi@<pi5-ip>` from each laptop, (2) `sudo passwd pi`, (3) remove nopasswd sudoers
