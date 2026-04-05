# Project Registry

Single index of all projects managed by ProjectManager.
PM updates this when projects are added, plans change, or onboarding scans complete.

Last updated: 2026-04-05 (PI Planning onboarding scan complete)

---

## Projects

| Short name | Path | GitHub Remote | CLAUDE.md | Onboarding | Status |
|---|---|---|---|---|---|
| project_manager | `/opt/claude/project_manager` | `git@github.com:micmaas2/project-manager.git` | `/opt/claude/project_manager/CLAUDE.md` | done | active |
| ccas | `/opt/claude/CCAS` | (no remote, sub-repos have remotes) | `/opt/claude/CCAS/CLAUDE.md` | done | active |
| pi-homelab | `/opt/claude/pi-homelab` | `git@github.com:micmaas2/pi-homelab.git` | `/opt/claude/pi-homelab/CLAUDE.md` | done | active |
| pensieve | `/opt/claude/pensieve` | `git@github.com:micmaas2/pensieve.git` | `/opt/claude/pensieve/CLAUDE.md` | done | active |
| genealogie | `/opt/claude/genealogie` | `git@github.com:micmaas2/genealogie.git` | `/opt/claude/genealogie/CLAUDE.md` | done | active |
| performance_HPT | `/opt/claude/performance_HPT` | `git@github.com:micmaas2/performance-twin.git` | `/opt/claude/performance_HPT/CLAUDE.md` | done | active |
| project1 | `/opt/claude/project1` | (no remote) | `/opt/claude/project1/CLAUDE.md` | done | sandbox |

**Onboarding values**: `pending` (not yet scanned) | `in_progress` (scan running) | `done` (registered in backlog)

---

## Active Plan Files

Plan files live at `/root/.claude/plans/`. PM registers plans here when created and archives them on completion.

| Plan file | Project | Purpose | Status |
|---|---|---|---|
| `glimmering-tinkering-nest.md` | project_manager | PM architecture + MVP1 first task | active |
| `luminous-shimmying-island.md` | project_manager | Multi-agent automation system (MAS) design | active |
| `imperative-wobbling-newell.md` | performance_HPT | HPT Dashboard Fase 1 — live deployment on Pi | active |
| `modular-juggling-peach.md` | genealogie | Genealogy MAS — sortable dashboard & suggestions | active |
| `purrfect-dazzling-prism.md` | performance_HPT | Personal Human Performance Digital Twin design | active |
| `sequential-tumbling-river.md` | pi-homelab | pi-homelab repo consolidation + Pi 4/5 security hardening | active |
| `warm-gathering-scroll.md` | ccas | HANA OS user creation — new Ansible role | active |
| `gentle-crunching-naur.md` | ccas | SAP Start/Stop — instance-level ordering + safety checks | active |
| `curious-jingling-thunder.md` | pi-homelab | HA presence detection fix (Femke + Lucas) | active |
| `eventual-enchanting-hare.md` | pensieve | Token optimisation — switch Claude Sonnet → Haiku | active |
| `nifty-bouncing-sketch.md` | project1 | SAP Security Risk Profile — new section 4A | active |
| `hashed-foraging-frost.md` | project_manager | CLAUDE.md intro update (project_manager is the project) | active |
| `sleepy-wiggling-deer.md` | project1 | Azure Subscription → draw.io diagram generator | active |

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
- CLAUDE.md: `/opt/claude/CCAS/CLAUDE.md` — comprehensive root context for 6 sub-repos
- Sub-repos: `ccas-main`, `ccas-inventory`, `ccas-jenkins`, `ccas-core-infrastructure`, `ccas-sap-applications`, `ccas-platform`
- Current branch: `develop` (ccas-main), remote feature branch `feature/enhance-jenkinsfile-s4hana` open
- Overall completion: ~86–87% (as of 2026-01-25 status doc); ~600h remaining on Unified Plan
- Active plans: `warm-gathering-scroll.md` (HANA OS users), `gentle-crunching-naur.md` (SAP Start/Stop), Unified Plan in `ccas-main/.claude/plans/`
- Status tracker: `ccas-main/.claude/status/CURRENT-STATUS.md` (authoritative)
- Key remaining work: Quick Win #3 Infrastructure Validation Enhancements, Quick Win #4 Documentation; BW/4HANA inventory parametrization (~10% left); ongoing pipeline + playbook expansion

### pi-homelab
- CLAUDE.md: `/opt/claude/pi-homelab/CLAUDE.md` — rich operational reference (Pi 4 + Pi 5 context)
- Branch: `main` only (single branch); last commit 2026-03-29
- Key files: `AUTOMATIONS.md` (full automation inventory), `docs/ENERGY_DASHBOARD_SETUP.md`, `docs/UNIFI_UPDATE_TRACKING.md`, `plans/` (3 files)
- Active Docker stacks on Pi 4: HA, n8n, NPM, UniFi, MAS
- Active plans: `sequential-tumbling-river.md` (repo consolidation + security hardening), `curious-jingling-thunder.md` (presence detection fix)
- Pending (from CLAUDE.md): Pi 4 passwd hardening; migrate python:3.11-slim-bullseye → bookworm; Pi 5 manual security prereqs + apply-hardening.sh
- Most recently active project (last commit 2026-03-29, n8n fs built-in fix)

### pensieve
- CLAUDE.md: `/opt/claude/pensieve/CLAUDE.md` — knowledge capture pipeline (Telegram/Email/Obsidian → Claude → Obsidian vault)
- Branches: `main` (current), `develop`, `feature/initial-setup` (all on remote)
- Last commit: 2026-03-29 (switch Sonnet → Haiku, max_tokens reduction)
- BACKLOG.md: Gmail capture workflow not yet activated in n8n; Obsidian Clipper not configured
- Active plans: `eventual-enchanting-hare.md` (Haiku token optimisation, possibly already done per commit)
- Workflows: `workflows/gmail-capture.json` ready but not imported; `workflows/telegram-capture.json` active

### genealogie
- CLAUDE.md: `/opt/claude/genealogie/CLAUDE.md` — full implementation context; code in `genealogy-mas/`
- Branches: `develop` (current), `main`; both on remote
- Implementation complete: Flask dashboard, SQLite, GEDCOM, OpenArch, MyHeritage OAuth2, ConflictResolver
- Last commits (10): all FEAT/FIX/DOCS — v2.1.1 most recent; active development visible
- Active plans: `modular-juggling-peach.md` (sortable dashboard/tables — may already be done per commit history)
- Python stack: system Python, no venv; `anthropic httpx python-gedcom flask flask-wtf python-dotenv`
- Status: most feature-complete project of all siblings; currently in maintain/enhance mode

### performance_HPT
- CLAUDE.md: `/opt/claude/performance_HPT/CLAUDE.md` — workspace context, "no source code currently"
- README.md references `performance-twin/` subdirectory — does NOT exist yet (scaffold not created)
- Branches: `develop`, `main`, `feature/fix-initial-scaffold` (on remote); last commit = scaffold fixes
- `tasks/` dir exists: `todo.md` and `lessons.md` (both empty/template only)
- Active plans: `imperative-wobbling-newell.md` (HPT Dashboard Fase 1 — code on Pi in `/opt/claude/future/hpt-dashboard/`, not in this repo); `purrfect-dazzling-prism.md` (Personal Performance Digital Twin design)
- Status: pre-code — plans exist but implementation not yet scaffolded in repo

### project1
- CLAUDE.md: `/opt/claude/project1/CLAUDE.md` — generic skeleton + SAP audit artifact
- Key artifact: `sap-audit/audit-log-analysis.md` — SAP audit log solution design (buy vs build analysis)
- No git repo initialised (branch scan returned exit 128)
- Active plans: `nifty-bouncing-sketch.md` (SAP security risk profile section 4A), `sleepy-wiggling-deer.md` (Azure → draw.io diagram generator)
- Status: document/research repository, no code; referenced artifact is a deliverable document

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
