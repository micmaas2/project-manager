# task-048: Automation Recommender — Cross-Project Report

**Date**: 2026-04-28  
**Agent**: Builder [Sonnet]  
**Scope**: 7 managed projects

## Summary Table
| Project | Hooks | MCP | Skills/Subagents | Plugins | Adopt count |
|---------|-------|-----|------------------|---------|-------------|
| project_manager | 2 | 0 | 3 | 0 | 2 |
| CCAS | 2 | 2 | 1 | 0 | 2 |
| pi-homelab | 2 | 2 | 1 | 0 | 2 |
| pensieve | 2 | 2 | 2 | 0 | 2 |
| genealogie | 2 | 1 | 2 | 0 | 2 |
| performance_HPT | 1 | 2 | 2 | 0 | 0 |
| project1 | 0 | 0 | 0 | 0 | 0 |

---

## 1. project_manager

### Codebase Profile
- **Language**: Python (orchestrator + agents)
- **Architecture**: Multi-agent system (Opus 4.6 orchestrator, 6x Sonnet 4.6 specialists)
- **Existing automation**: `.claude/agents/` (6 agents), `.claude/commands/` (7 skills), `hooks/` with security hook, PreToolUse security-guidance (BL-101)
- **State mgmt**: File-based queues (tasks/queue.json, artefacts/)
- **Pipeline**: 7-stage task lifecycle with guards, self-improvement loop, lessons tracking

### Recommendations
| # | Category | Recommendation | Rationale | Decision |
|---|----------|---------------|-----------|----------|
| 1 | Hook | PostToolUse artefact quality checklist | Enforces artefact format (required fields, non-empty mvp_template) before archival; complements PreToolUse security-guidance (BL-101) | **adopt** → BL-104 |
| 2 | Hook | Commit-msg BL-ID correlation validator | Auto-validate that every commit on a feature branch references a BL number; reduces audit gaps | **adopt** → BL-105 |
| 3 | MCP | GitHub MCP for issue/PR automation | Cross-project task intake from GH issues; close completed tasks automatically | defer |
| 4 | Skill | pm-rollback: resume interrupted task from checkpoint | Improves resume logic for paused tasks; currently manual | defer |
| 5 | Skill | Audit query skill: search/filter lessons.md, improvement_proposals.md | Enables meta-analysis of self-improvement trends; low urgency | skip |

---

## 2. CCAS

### Codebase Profile
- **Language**: Ansible + YAML (SAP infrastructure automation)
- **Multi-repo**: 6 sibling repos (ccas-core-infrastructure, ccas-sap-applications, ccas-inventory, ccas-jenkins, ccas-platform, ccas-main)
- **Existing automation**: `.ansible-lint`, `.yamllint`, pre-commit hooks in ccas-main, extensive CLAUDE.md cross-referencing
- **Pipeline**: Jenkins + Ansible orchestration; credential removal completed; inventory parametrization (91% param reduction)
- **State**: File-based inventory, 87% completion status tracked in ccas-main/.claude/status/

### Recommendations
| # | Category | Recommendation | Rationale | Decision |
|---|----------|---------------|-----------|----------|
| 1 | Hook | Ansible playbook syntax + idempotency pre-commit | Enforce `ansible-lint`, validate roles are idempotent; linters exist but not hooked | **adopt** → BL-106 |
| 2 | Hook | Vault credential re-scan — PreToolUse blocking hook | Block Write/Edit at edit time when SAP credential patterns detected; on match: emit file path + line number only — never log matched text; mirrors BL-101 security-guidance pattern | **adopt** → BL-107 |
| 3 | MCP | GitHub MCP for ccas-main repo automation | Sync status docs to GH Issues/Project board; automate P1/P2 milestone tracking | defer |
| 4 | MCP | Ansible MCP (playbook execution + inventory queries) | Direct playbook runs from Claude; cross-repo role testing | defer |
| 5 | Skill | ccas-inventory-sync: read-back parametrization metrics | Query 91% param reduction KPI and report gaps | skip |

---

## 3. pi-homelab

### Codebase Profile
- **Platform**: Raspberry Pi (2x) — Home Assistant, Docker stacks (n8n, Nginx Proxy Manager, Ollama, UniFi, MAS)
- **IaC**: Home Assistant YAML configs, docker-compose, shell hardening scripts, restic backups
- **Existing automation**: Docker healthchecks, scp-based config deployment, fail2ban, sysctl hardening
- **State**: Pi 5 (repo) → Pi 4 (production via scp), extensive deployment history in CLAUDE.md

### Recommendations
| # | Category | Recommendation | Rationale | Decision |
|---|----------|---------------|-----------|----------|
| 1 | Hook | Pre-commit: validate HA YAML syntax + Lovelace structure | Catches automation/config breakage before push; prevents failed HA restarts | **adopt** → BL-108 |
| 2 | Hook | Docker Compose schema validation | Ensure stacks stay deployable; catch port/network config errors early | defer |
| 3 | MCP | Docker MCP for container health checks | Poll running stacks (HA, n8n, MAS) from Claude; auto-remediation of crashed services | **adopt** → BL-109 |
| 4 | MCP | Home Assistant MCP | Query entity state, trigger automations, read energy dashboards | defer |
| 5 | Skill | pi-deploy: scp + restart synced services | Encapsulate deployment pattern (sync config → restart service on Pi 4) | defer |

---

## 4. pensieve

### Codebase Profile
- **Purpose**: Personal knowledge capture pipeline (Claude API processor for Telegram/Email/Obsidian)
- **Tech**: n8n workflows (3x JSON), Python deployment scripts, Claude SDK usage
- **Integrations**: Telegram Bot, Gmail, Obsidian Clipper, OneDrive (rclone), Claude API (sonnet-4-6)
- **State**: Live pipeline (2026-03-29), Telegram capture working, Gmail capture + topic routing active
- **Existing automation**: n8n workflows handle routing, YAML injection hardening

### Recommendations
| # | Category | Recommendation | Rationale | Decision |
|---|----------|---------------|-----------|----------|
| 1 | Hook | Pre-commit: validate n8n JSON workflow syntax and schema | Prevent corruption of telegram-capture.json, gmail-capture.json; catches node config errors | **adopt** → BL-110 |
| 2 | MCP | Gmail MCP (native auth pensieve@femic.nl, scope: gmail.readonly) | Eliminate n8n poll latency; direct label reading and message processing; OAuth scope must be `gmail.readonly` (not full access); refresh token must be stored in OS keychain or vault — not plaintext MCP config | **adopt** → BL-111 |
| 3 | MCP | Obsidian MCP | Query vault structure, read/write notes programmatically; complement Clipper | defer |
| 4 | Skill | pensieve-capture: direct Telegram message handler via Claude API | Bypass n8n for simple captures; reduces latency | defer |
| 5 | Skill | vault-audit: scan inbox for duplicates, untagged notes, orphaned links | Periodic hygiene; detect schema drift | defer |

---

## 5. genealogie

### Codebase Profile
- **Type**: Python Flask webapp + Claude MAS (Managed Agent System)
- **Tech**: Python 3 (Flask, python-gedcom, anthropic SDK >= 0.86), SQLite (db.py, models/), Jinja2 templates
- **Architecture**: Genealogy data ingestion → Claude agents → structured output
- **Existing automation**: code-quality-reviewer agent memory, CLAUDE.md project guidance
- **State**: Early stage; no tests yet; has db.py, app.py (Flask), agent orchestration

### Recommendations
| # | Category | Recommendation | Rationale | Decision |
|---|----------|---------------|-----------|----------|
| 1 | Hook | Pre-commit: Python lint (ruff/black) + import validation | Enforce code style; genealogy-mas is Python-first and likely to grow | **adopt** → BL-112 |
| 2 | Hook | SQLite schema validator (check db.py migrations) | Prevent dangling schema changes; genealogy data integrity critical | **adopt** → BL-113 |
| 3 | MCP | GitHub MCP for issue/PR workflow | Genealogy project is early-stage; automate issue→task→PR cycle | defer |
| 4 | Skill | genealogy-export: GEDCOM writing + Claude-augmented lineage formatting | Package output for Ancestry/FamilySearch | defer |
| 5 | Skill | genealogy-verify: cross-reference dates and parent→child relationships | Data quality gate for large imports | defer |

---

## 6. performance_HPT

### Codebase Profile
- **Type**: Workspace context directory (Human Performance Technology / Load-Fatigue-Performance reflection)
- **Status**: Early-stage skeleton (no tasks/ or agents/ yet)
- **Existing automation**: code-quality-reviewer agent memory only
- **Purpose**: Personal digital twin for reflection

### Recommendations
| # | Category | Recommendation | Rationale | Decision |
|---|----------|---------------|-----------|----------|
| 1 | Hook | Pre-commit: YAML schema for performance metrics | Ensure logs/entries stay parseable; consistency across sessions | defer |
| 2 | MCP | Google Sheets MCP (performance tracking dashboards) | Query/write load-fatigue metrics; integrate with Calendar | defer |
| 3 | MCP | Google Calendar MCP (read workload events) | Correlate performance drops with high-meeting days | defer |
| 4 | Skill | hpt-log: structured session logging template | Template-driven entry format; aggregates into weekly summary | defer |
| 5 | Skill | hpt-analysis: trend detection across 8-week rolling window | Auto-flag patterns (e.g., fatigue spikes post-sprint) | skip |

*No adopt items — project is too early-stage; defer until structure is established.*

---

## 7. project1

### Codebase Profile
- **Type**: Generic project skeleton / SAP audit artifact hub
- **Status**: Minimal structure; only sap-audit/ subdirectory with one solution design doc
- **Existing automation**: None (only `.claude/settings.local.json`)
- **Purpose**: Unclear; appears to be template or incubator

### Recommendations
| # | Category | Recommendation | Rationale | Decision |
|---|----------|---------------|-----------|----------|
| 1 | Hook | Pre-commit: README validation (enforce project metadata) | Requires README.md with purpose/status; prevents abandoned repos | skip |
| 2 | MCP | — | No clear project purpose or tech stack yet | skip |
| 3 | Skill | — | Defer until project intent clarified | skip |

*No adopt items — project intent unclear; no automation warranted until scoped.*

---

## Adopt Items — Registered as BL Entries

| BL ID | Project | Category | Recommendation | Rationale |
|-------|---------|----------|---------------|-----------|
| BL-104 | project_manager | Hook | PostToolUse artefact quality checklist | Enforce artefact format before archival; complement BL-101 security hook |
| BL-105 | project_manager | Hook | Commit-msg BL-ID correlation validator | Auto-validate every commit references a BL number; closes audit gaps |
| BL-106 | CCAS | Hook | Ansible playbook syntax + idempotency pre-commit | Linters exist but not hooked; enforce before push |
| BL-107 | CCAS | Hook (PreToolUse) | Vault credential re-scan — blocking at edit time; emit path+line only, never matched text | Prevent SAP credentials from ever entering git history; mirrors BL-101 security-guidance pattern |
| BL-108 | pi-homelab | Hook | HA YAML syntax + Lovelace structure pre-commit | Prevent failed HA restarts from config errors |
| BL-109 | pi-homelab | MCP | Docker MCP for container health checks | Poll running stacks from Claude; enable auto-remediation |
| BL-110 | pensieve | Hook | n8n JSON workflow syntax pre-commit | Prevent corruption of live capture workflows |
| BL-111 | pensieve | MCP | Gmail MCP — scope: gmail.readonly; refresh token via OS keychain/vault, not plaintext config | Eliminate n8n poll latency; enforce least-privilege OAuth scope |
| BL-112 | genealogie | Hook | Python lint (ruff/black) pre-commit | Enforce code style as Python codebase grows |
| BL-113 | genealogie | Hook | SQLite schema validator pre-commit | Protect genealogy data integrity across migrations |
