# Project Dashboard
_Last updated: 2026-05-04 15:15_

## Queue Status

| Status | Count |
|---|---|
| pending | 0 |
| in_progress | 0 |
| paused | 0 |
| review | 0 |
| test | 0 |
| done | 57 |

## Active Tasks

_No tasks currently in progress._

## Recently Completed

- **task-058** project_manager: CLAUDE.md size reduction — migrate verbose sections to linked docs (BL-118) [2026-05-04]
- **task-057** project_manager: PM system audit — CLAUDE.md, agent YAMLs, skills quality review (BL-078) [2026-05-03]
- **task-056** genealogie: SQLite schema validator pre-commit hook (BL-113, S-007-6) [2026-05-02]
- **task-055** genealogie: Python lint (ruff) pre-commit hook (BL-112, S-007-5) [2026-05-02]
- **task-054** pensieve: n8n JSON workflow syntax pre-commit hook (BL-110, S-007-4) [2026-05-01]

## Next Up (Pending)

_No pending tasks._

## Maintenance — Due Soon

- HA automation health check — due 2026-04-12
- Pensieve workflow health — due 2026-04-12
- Pi 4 full patch run — due 2026-04-12
- Pi 4 Docker stack check — due 2026-04-12
- Let's Encrypt cert expiry check — due 2026-04-12

## Top Backlog (P1, not yet queued)

- BL-053: pensieve: Deploy gmail-capture.json workflow to n8n on Pi4 — built in task-009, deploy steps in artefacts/task-009/deploy-notes.md; requires Gmail OAuth credential + Pensieve label re-selection after import (arch-review pensieve-P1) [pensieve]
- BL-122: project_manager: Fix manager.yaml — revise-claude-md invocation uses wrong tool (subagent_type=claude-md-management:revise-claude-md); must use Skill tool per CLAUDE.md (agent tool does not work for claude-md-management:*). NOTE: steps 7b (code-quality-reviewer) and 7d (docs-readme-writer) use subagent_type correctly — do NOT change those. [project_manager]
- BL-123: project_manager: Fix reviewer.yaml — require_human_approval must be true (has Write+Bash in allowed_tools; violates CLAUDE.md policy schema) [project_manager]
