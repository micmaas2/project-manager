# Epics & Stories

Epics define large bodies of work. Stories are the sub-tasks that implement them.
Each story maps to one or more entries in `tasks/queue.json`.

---

## EPIC-001 — Multi-Agent System Foundation

**Goal**: Build and validate the core MAS pipeline end-to-end.
**Project**: project_manager
**Status**: done
**MVP Phase**: MVP1

### Stories

| Story ID | Title | Queue Task | Status |
|---|---|---|---|
| S-001-1 | Agent scaffolding (Manager, Builder, Reviewer, Tester) | — | done |
| S-001-2 | Task queue + schema | — | done |
| S-001-3 | Git hooks (branch protection, commit-msg) | — | done |
| S-001-4 | Tracking infrastructure (backlog, kanban, epics) | — | done |
| S-001-5 | End-to-end pipeline validation (queue status reporter) | task-001 | done |

---

## EPIC-002 — Self-Improvement & Learning Loop

**Goal**: Enable the MAS to learn from every run and improve agent behaviour over time.
**Project**: project_manager
**Status**: done
**MVP Phase**: MVP2

### Stories

| Story ID | Title | Queue Task | Status |
|---|---|---|---|
| S-002-1 | SelfImprover agent (reads logs, writes lessons) | — | done |
| S-002-2 | lessons.md populated after every pipeline run | task-002 | done |
| S-002-3 | PM reads lessons at session start | task-006 | done |
| S-002-4 | Human-gated improvement proposals to YAML/CLAUDE.md | task-007 | done |

---

## EPIC-003 — Multi-Project Coordination

**Goal**: Enable ProjectManager to orchestrate tasks across all /opt/claude/* projects.
**Project**: project_manager
**Status**: done
**MVP Phase**: MVP3

### Stories

| Story ID | Title | Queue Task | Status |
|---|---|---|---|
| S-003-1 | Global priority ranking across projects | task-015 | done |
| S-003-2 | PI/Refinement planning session (user + PM) | task-013 | done |
| S-003-3 | Cross-project kanban view | task-017 | done |
| S-003-4 | Token budget enforcement per project | task-016 | done |

---

## Projects in Scope

| Short name | Path | GitHub | Domain |
|---|---|---|---|
| project_manager | `/opt/claude/project_manager` | micmaas2/project-manager | This MAS system |
| ccas | `/opt/claude/CCAS` | (no remote yet) | SAP infrastructure / Ansible |
| pi-homelab | `/opt/claude/pi-homelab` | micmaas2/pi-homelab | Raspberry Pi / Home Assistant |
| pensieve | `/opt/claude/pensieve` | micmaas2/pensieve | TBD |
| genealogie | `/opt/claude/genealogie` | micmaas2/genealogie | Genealogy tooling |
| performance_HPT | `/opt/claude/performance_HPT` | micmaas2/performance-twin | Performance / HPT |
| project1 | `/opt/claude/project1` | (no remote yet) | Generic skeleton |
