# Backlog

Unscheduled items, scope-drift captures, and future ideas. Maintained by ProjectManager.
Items move to `queue.json` when prioritized and assigned an MVP template.

---

## Epics

| Epic ID | Title | Project | Status |
|---|---|---|---|
| EPIC-001 | Multi-Agent System Foundation | project_manager | done |
| EPIC-002 | Self-Improvement & Learning Loop | project_manager | in_progress |
| EPIC-003 | Multi-Project Coordination | project_manager | in_progress |

---

## Backlog Items

| ID | Epic | Title | Project | Priority | Status | Added |
|---|---|---|---|---|---|---|
| BL-003 | EPIC-003 | PI/Refinement planning session workflow | project_manager | P2 | planned | 2026-04-05 |
| BL-004 | EPIC-003 | Multi-project priority ranking in PM | project_manager | P2 | planned | 2026-04-05 |
| BL-007a | EPIC-003 | CCAS: Merge feature/hana-os-users → ccas-jenkins develop | ccas | P1 | done | 2026-04-05 |
| BL-009 | EPIC-003 | CCAS: Quick Win #3 — Infrastructure Validation Enhancements | ccas | P2 | discovered | 2026-04-05 |
| BL-010 | EPIC-003 | CCAS: BW/4HANA inventory parametrization — final ~10% | ccas | P2 | discovered | 2026-04-05 |
| BL-011 | EPIC-003 | CCAS: Resolve open remote branch feature/enhance-jenkinsfile-s4hana | ccas | P2 | discovered | 2026-04-05 |
| BL-012 | EPIC-003 | pi-homelab: Pi 4 passwd hardening + remove nopasswd sudoers | pi-homelab | P1 | blocked-manual | 2026-04-05 |
| BL-013 | EPIC-003 | pi-homelab: Pi 5 manual security prereqs + apply-hardening.sh | pi-homelab | P1 | blocked-manual | 2026-04-05 |
| BL-026 | EPIC-003 | pi-homelab: Regular patching — Pi 4 SSH fix + first patch run | pi-homelab | P1 | blocked-ssh | 2026-04-05 |
| BL-014 | EPIC-003 | pi-homelab: Migrate python:3.11-slim-bullseye → bookworm (health-api) | pi-homelab | P2 | discovered | 2026-04-05 |
| BL-015 | EPIC-003 | pensieve: Activate Gmail capture workflow in n8n | pensieve | P1 | planned | 2026-04-05 |
| BL-016 | EPIC-003 | pensieve: Configure Obsidian Clipper | pensieve | P2 | discovered | 2026-04-05 |
| BL-023 | EPIC-003 | pensieve: Improve article/blog summarisation quality | pensieve | P1 | done | 2026-04-05 |
| BL-024 | EPIC-003 | pensieve: Improved tagging for captured content | pensieve | P1 | done | 2026-04-05 |
| BL-025 | EPIC-003 | pensieve: Store files in topic-based folders for better search | pensieve | P1 | done | 2026-04-05 |
| BL-027 | EPIC-003 | pensieve: Retroactive vault quality improvement — format migration, tag normalization, URL re-enrichment | pensieve | P1 | done | 2026-04-05 |
| BL-017 | EPIC-003 | genealogie: Implement MyHeritageAgent write-back via MyHeritage API | genealogie | P2 | discovered | 2026-04-05 |
| BL-018 | EPIC-003 | genealogie: Merge develop → main and tag v2.x release | genealogie | P3 | discovered | 2026-04-05 |
| BL-019 | EPIC-003 | performance_HPT: Scaffold performance-twin repo + deploy HPT Dashboard | performance_HPT | P2 | discovered | 2026-04-05 |
| BL-020 | EPIC-003 | performance_HPT: HPT Dashboard Fase 1 — move from /opt/claude/future/ into repo (imperative-wobbling-newell.md) | performance_HPT | P2 | discovered | 2026-04-05 |
| BL-028 | EPIC-003 | project_manager: Merge Boris Cherny CLAUDE.md principles + archive original | project_manager | P2 | done | 2026-04-06 |
| BL-029 | EPIC-003 | project_manager: Activity dashboard in Obsidian vault (auto-generated markdown, 15-min cron) | project_manager | P2 | done | 2026-04-06 |
| BL-030 | EPIC-003 | pensieve: Phone backlog submission via Telegram BACKLOG: prefix → GitHub API commit | pensieve | P2 | done | 2026-04-06 |
| BL-031 | EPIC-003 | project_manager: Investigate git worktrees as isolation mechanism for parallel agent runs | project_manager | P3 | new | 2026-04-06 |
| BL-033 | EPIC-003 | New project proposal: grocery price comparison across stores (requirements + plan first) | project_manager | P3 | new | 2026-04-06 |
| BL-034 | EPIC-003 | project_manager: Add backlog and Pensieve capture from laptop (not only Telegram/phone) | project_manager | P2 | planned | 2026-04-06 |
| BL-035 | EPIC-003 | New project proposal: school-ai — AI learning assistant for primary school kids (helps learn, not do work) | school-ai | P2 | new | 2026-04-07 |

---

## Scope-Drift Log

Items automatically added here when an agent produces work outside the MVP spec.

| Date | Task ID | Agent | Drift Description | Disposition |
|---|---|---|---|---|
| — | — | — | — | — |

---

## Archived

Items completed, rejected, or no longer relevant.

| ID | Title | Reason | Date |
|---|---|---|---|
| BL-001 | SelfImprover agent implementation | Delivered as part of task-001/task-002 pipeline (lessons.md + improvement_proposals.md) | 2026-04-05 |
| BL-002 | DocUpdater agent implementation | Delivered as part of task-001/task-002 pipeline (CHANGELOG.md updates) | 2026-04-05 |
| BL-005 | First real task: CCAS Ansible role generation | Superseded by BL-007 (hana_os_users already implemented) | 2026-04-05 |
| BL-006 | First real task: pi-homelab deployment script | Superseded by BL-012/013 (hardening already in repo) | 2026-04-05 |
| BL-007 | CCAS: HANA OS user creation Ansible role | Role, playbook, inventory, and Jenkins pipeline all committed to ccas-core-infrastructure develop. Remaining: BL-007a (merge ccas-jenkins feature branch) | 2026-04-05 |
| BL-008 | CCAS: SAP Start/Stop instance-level ordering | Fully implemented — sap_start.yml, sap_stop.yml (per-instance ordering), hana_stop.yml (safety check), Jenkinsfile v3 (TARGET_HOST). All in ccas-jenkins develop | 2026-04-05 |
| BL-021 | project1: SAP Security Risk Profile section 4A | project1 is sandbox — not a managed project | 2026-04-05 |
| BL-022 | project1: Azure diagram generator | project1 is sandbox — not a managed project | 2026-04-05 |
| BL-032 | test backlog routing via telegram | Test entry — confirmed pipeline working | 2026-04-06 |
