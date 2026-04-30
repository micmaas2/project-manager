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

## EPIC-004 — System Quality & Optimization

**Goal**: Improve system reliability, reduce token overhead, and integrate best-practice patterns from the Claude Code ecosystem.
**Project**: project_manager
**Status**: done
**MVP Phase**: MVP4

### Stories

| Story ID | Title | Queue Task | Status |
|---|---|---|---|
| S-004-1 | Pensieve pipeline stability debug | task-033 | done |
| S-004-2 | CLAUDE.md + agent YAML token reduction rewrites | task-035 | done |
| S-004-3 | Reviewer confidence scoring | task-036 | done |
| S-004-4 | Claude Code skills & agents integration research | task-034 | done |

---

## EPIC-005 — System Housekeeping & Cost Optimisation

**Goal**: Reduce CLAUDE.md size, lower token/cost overhead, optimise model assignments, and improve system tooling quality.
**Project**: project_manager
**Status**: done
**MVP Phase**: MVP4

### Stories

| Story ID | Title | Queue Task | Status |
|---|---|---|---|
| S-005-1 | CLAUDE.md size reduction — target ≤35k chars | task-037 | done |
| S-005-2 | Add /compact calls at pm-run stage boundaries | task-038 | done |
| S-005-3 | Cost-aware model routing design | task-039 | done |
| S-005-4 | Agent model usage audit — cost reduction | task-040 | done |
| S-005-5 | /pm-run plan-mode gate evaluation | task-041 | done |
| S-005-6 | Model version pins review and update | task-042 | done |
| S-005-7 | Claude Code skills investigation — cross-project fit | task-043 | done |

---

## EPIC-006 — MAS Hardening & project_manager Quick Wins

**Goal**: Harden the MAS personal assistant (model upgrade, budget enforcement, uptime monitoring) and deliver fast-win improvements to the project_manager tooling (security hook, automation scan, hooks-over-prompts).
**Project**: pi-homelab / project_manager
**Status**: done
**MVP Phase**: MVP4

### Stories

| Story ID | Title | Queue Task | Status |
|---|---|---|---|
| S-006-1 | MAS: Upgrade LLM_PRIMARY_MODEL → claude-sonnet-4-6 | task-044 | done |
| S-006-2 | MAS: Add hard budget enforcement to LLMClient.chat() | task-045 | done |
| S-006-3 | MAS: Configure uptime monitoring for /health endpoint | task-046 | done |
| S-006-4 | Install security-guidance PreToolUse hook | task-047 | done |
| S-006-5 | Run claude-automation-recommender across all projects | task-048 | done |
| S-006-6 | Hooks-over-prompts audit — implement top 3 rules as hooks | task-049 | done |
| S-006-7 | SelfImprover: add confidence score + project scope to lessons | task-050 | done |

---

## EPIC-007 — Cross-Project Hardening: Pre-Commit Hooks

**Goal**: Install pre-commit hooks across all managed repos (CCAS, pi-homelab, pensieve, genealogie) to enforce syntax validation, credential blocking, and code style at edit time — preventing broken configs, style drift, and credential leaks from ever entering git history.
**Project**: multi-project (ccas, pi-homelab, pensieve, genealogie)
**Status**: in_progress
**MVP Phase**: MVP4

### Stories

| Story ID | Title | Queue Task | Status |
|---|---|---|---|
| S-007-1 | CCAS: Ansible lint + idempotency pre-commit hook (BL-106) | task-051 | in_progress |
| S-007-2 | CCAS: SAP credential PreToolUse blocking hook (BL-107) | task-052 | in_progress |
| S-007-3 | pi-homelab: HA YAML syntax + Lovelace pre-commit hook (BL-108) | task-053 | in_progress |
| S-007-4 | pensieve: n8n JSON workflow syntax pre-commit hook (BL-110) | task-054 | in_progress |
| S-007-5 | genealogie: Python lint (ruff/black) pre-commit hook (BL-112) | task-055 | in_progress |
| S-007-6 | genealogie: SQLite schema validator pre-commit hook (BL-113) | task-056 | in_progress |

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
