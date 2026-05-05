# Kanban Board

Updated by ProjectManager after every task status change.
Source of truth: `tasks/queue.json`. This board is a human-readable view.

Last updated: 2026-04-17T12:06:44Z

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

- **task-033** pensieve: Debug missing Obsidian md files since 2026-04-09 (BL-083)
- **task-034** project_manager: Explore Claude Code optimization repo — 108 skills + 25 agents (BL-084)
- **task-035** project_manager: Execute CLAUDE.md + agent YAML token reduction rewrites (BL-079)
- **task-036** project_manager: Add confidence scoring to Reviewer YAML output (BL-076)
- **task-037** project_manager: CLAUDE.md size reduction — target ≤35k chars (BL-096)
- **task-038** project_manager: Add /compact calls at pm-run stage boundaries (BL-092)
- **task-039** project_manager: Cost-aware model routing design (BL-093)
- **task-040** project_manager: Agent model usage audit — cost reduction (BL-099)
- **task-041** project_manager: /pm-run plan-mode gate evaluation (BL-097)
- **task-042** project_manager: Model version pins review and update (BL-098)
- **task-043** project_manager: Claude Code skills investigation — cross-project fit (BL-100)
- **task-044** pi-homelab: MAS — Upgrade LLM_PRIMARY_MODEL → claude-sonnet-4-6 (BL-061)
- **task-045** pi-homelab: MAS — Add hard budget enforcement to LLMClient.chat() (BL-062)
- **task-046** pi-homelab: MAS — Configure uptime monitoring for /health endpoint (BL-063)
- **task-047** project_manager: Install security-guidance PreToolUse hook (BL-101)
- **task-048** project_manager: Run claude-automation-recommender across all projects (BL-102)
- **task-049** project_manager: Hooks-over-prompts audit — implement top 3 rules as hooks (BL-088)
- **task-050** project_manager: SelfImprover — add confidence score + project scope to lessons (BL-085)
- **task-051** ccas: Ansible lint + idempotency pre-commit hook (BL-106)
- **task-052** ccas: SAP credential PreToolUse blocking hook (BL-107)
- **task-053** pi-homelab: HA YAML syntax pre-commit hook (BL-108)
- **task-054** pensieve: n8n JSON workflow syntax pre-commit hook (BL-110)
- **task-055** genealogie: Python lint (ruff) pre-commit hook (BL-112)
- **task-056** genealogie: SQLite schema validator pre-commit hook (BL-113)
- **task-057** project_manager: PM system audit — CLAUDE.md, agent YAMLs, skills quality review (BL-078)
- **task-058** project_manager: CLAUDE.md size reduction — migrate verbose sections to linked docs (BL-118)
- **task-059** project_manager: Fix manager.yaml — revise-claude-md invocation uses wrong tool (BL-122)
- **task-060** project_manager: Fix builder.yaml — M-1 mirror gap confidence definition (BL-124)
- **task-061** project_manager: Fix manager.yaml — add Bash to allowed_tools (BL-126)
- **task-062** project_manager: Add execution-mode preamble to pm-close.md (BL-127)
- **task-063** project_manager: Fix pm-start.md — 2 missing session checklist items (BL-128)
- **task-064** project_manager: Fix CLAUDE.md — stale EPIC-003 reference in inbox promotion (BL-129)

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
