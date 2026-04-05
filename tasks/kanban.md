# Kanban Board

Updated by ProjectManager after every task status change.
Source of truth: `tasks/queue.json`. This board is a human-readable view.

Last updated: 2026-04-05T11:00:00Z

---

## Backlog
_(items in backlog.md not yet in queue)_

- BL-001 SelfImprover agent
- BL-002 DocUpdater agent
- BL-003 PI/Refinement planning workflow
- BL-004 Multi-project priority ranking
- BL-005 CCAS: first Ansible role
- BL-006 pi-homelab: deployment script

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

- **task-002** Audit log summary script — `artefacts/task-002/audit-summary.sh` [2026-04-05]
- **task-001** Queue status reporter script — `artefacts/task-001/queue-status.sh` [2026-04-05]

---

## Blocked / Paused
_(status: paused — rate-limited or awaiting human input)_

_(empty)_
