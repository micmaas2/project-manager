# Project Registry

Single index of all projects managed by ProjectManager.
PM updates this when projects are added, plans change, or onboarding scans complete.

Last updated: 2026-04-05

---

## Projects

| Short name | Path | GitHub Remote | CLAUDE.md | Onboarding | Status |
|---|---|---|---|---|---|
| project_manager | `/opt/claude/project_manager` | `git@github.com:micmaas2/project-manager.git` | `/opt/claude/project_manager/CLAUDE.md` | done | active |
| ccas | `/opt/claude/CCAS` | (no remote) | — | pending | active |
| pi-homelab | `/opt/claude/pi-homelab` | `git@github.com:micmaas2/pi-homelab.git` | — | pending | active |
| pensieve | `/opt/claude/pensieve` | `git@github.com:micmaas2/pensieve.git` | — | pending | active |
| genealogie | `/opt/claude/genealogie` | `git@github.com:micmaas2/genealogie.git` | — | pending | active |
| performance_HPT | `/opt/claude/performance_HPT` | `git@github.com:micmaas2/performance-twin.git` | — | pending | active |
| project1 | `/opt/claude/project1` | (no remote) | — | pending | skeleton |

**Onboarding values**: `pending` (not yet scanned) | `in_progress` (scan running) | `done` (registered in backlog)

---

## Active Plan Files

Plan files live at `/root/.claude/plans/`. PM registers plans here when created and archives them on completion.

| Plan file | Project | Purpose | Status |
|---|---|---|---|
| `glimmering-tinkering-nest.md` | project_manager | PM architecture + MVP1 first task | active |

### Archived Plans

| Plan file | Project | Purpose | Completed |
|---|---|---|---|
| — | — | — | — |

---

## Discovered Artifacts per Project

Populated by PM during onboarding scan. Each project entry lists found requirements, plans, and in-progress work.

### project_manager
- CLAUDE.md: `/opt/claude/project_manager/CLAUDE.md` ✅
- Plan: `glimmering-tinkering-nest.md` (active)
- State: green-field foundation complete, no in-progress branches

### ccas
- Onboarding scan: **pending**

### pi-homelab
- Onboarding scan: **pending**

### pensieve
- Onboarding scan: **pending**

### genealogie
- Onboarding scan: **pending**

### performance_HPT
- Onboarding scan: **pending**

### project1
- Onboarding scan: **pending**

---

## Onboarding Procedure

When adding a project that is already in progress, PM runs this scan **before** scheduling any tasks:

1. Read `<project>/CLAUDE.md` if present
2. Read `<project>/README.md` and any `docs/`, `requirements.md`, `BACKLOG.md`
3. Run `git -C <project> branch -a` and `git log --oneline -20` — note in-progress branches
4. Search `/root/.claude/plans/` for plan files referencing this project
5. Register all findings in the "Discovered Artifacts" section above
6. Create backlog entries in `tasks/backlog.md` for all discovered work
7. Mark onboarding column as `done`
8. Surface findings to user in next planning session for priority confirmation

**Rule**: PM never silently drops or overwrites existing project state.
All discovered work is registered and confirmed with the user before queuing.

---

## How to Add a New Project

1. Add a row to the Projects table (set onboarding = `pending`)
2. PM runs onboarding scan at next session start
3. Discovered artifacts registered here and in `tasks/backlog.md`
4. User confirms priorities in next planning session
