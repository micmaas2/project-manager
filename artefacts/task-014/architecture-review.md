# Architecture Review — 2026-04-11

## Executive Summary

- **mas-frontend container has been unhealthy for 4+ months** (82,589+ consecutive health check failures) due to a confirmed root cause: BusyBox `wget` resolves `localhost` to `[::1]` (IPv6), but nginx only listens on `0.0.0.0:80` (IPv4). The fix is a one-line healthcheck change (`127.0.0.1` instead of `localhost`). The container serves traffic successfully — the broken healthcheck suppresses real health signal.
- **Pi4 is a single point of failure for both pensieve and mas_agent**: n8n (Telegram/Gmail capture), obsidian vault sync, and all mas_agent containers run exclusively on Pi4. No failover, no redundancy, no off-Pi alerting if the device goes offline.
- **GitHub PAT stored as a flat file (`/opt/n8n/github-pat`, perms 600)** — not in a vault. Correctly referenced via n8n credential store (AES-encrypted at rest), but the source file on disk is accessible to any user with Pi4 shell access. No PAT rotation schedule documented.
- **Telegram and Gmail pensieve workflows share ~4 deeply duplicated Code nodes** (`Claude API`, `Parse Claude Response`, `Build Markdown Note`, `Write Note to Vault`) with diverging logic — changes must be applied twice manually, creating a permanent maintenance drag and regression risk.
- **No token budget hard-cap anywhere**: project_manager defines a 500k token cap in CLAUDE.md but has no runtime enforcement; mas_agent has budget config fields but `check_budget()` is report-only (no blocking). Both systems can silently overspend.

---

## System 1: project_manager (MAS/Claude Code)

### Current State

project_manager is a YAML-driven multi-agent orchestration system running locally via Claude Code. It manages task queues (`tasks/queue.json`), coordinates a six-agent pipeline (Manager → Architect/Security → Builder → Reviewer + code-quality-reviewer → Tester → DocUpdater + docs-readme-writer → SelfImprover), and governs a multi-project workspace across seven repos. It operates as a human-in-the-loop system — a PM session is always user-initiated and user-terminated; no autonomous background execution exists.

### Assessment

| Dimension | Finding | Severity |
|---|---|---|
| Operational complexity | Seven distinct agent YAMLs, two hook scripts, and twelve skills must be kept in sync. The M-1 pattern (mirrored rules between CLAUDE.md and agent YAMLs) is manual and error-prone. Session start requires a seven-step manual checklist. No automated verification that hooks are symlinked correctly. | Med |
| Cost | Opus 4.6 is used only for PM, Architect, and Security agents (correctly scoped). Sonnet 4.6 handles execution. Haiku 4.5 handles docs. Token estimates are tracked in `logs/token_log.jsonl` but the 500k cap is advisory only — no runtime guard stops a runaway agent. | Med |
| Security | pre-commit hook correctly blocks main/develop commits and detects sensitive file patterns. commit-msg enforces `[AREA]` format. However: (1) `require_human_approval: false` on ProjectManager despite it having Write/Edit tools — it can modify production files unattended; (2) no RBAC for agent spawning; (3) policy is declarative only (YAML fields) with no runtime enforcement layer. | Med |
| Availability | System is session-scoped (human-initiated). `resume_from` in queue.json supports rate-limit recovery. No persistent daemon, no watchdog, no alerting. If the host reboots mid-session, the paused task is recoverable but requires manual restart. | Low |

### Improvement Proposals

| P | Proposal | Effort | Impact | BL ref or NEW |
|---|---|---|---|---|
| P1 | Add runtime token cap enforcement: before spawning each agent, sum `token_estimate` for the task and abort with a structured error if total exceeds 400k (80% of cap). Write a small Python guard callable from manager.yaml. | S | High | NEW: token-cap-enforcer |
| P2 | Set `require_human_approval: true` on ProjectManager (it has Write/Edit tools) and add a confirmation gate before any file write outside `artefacts/`. Currently the agent can silently modify operational files (queue.json, backlog.md) without a human approval step. | S | High | NEW: pm-approval-gate |
| P3 | Automate the M-1 consistency check: add a `make lint-agents` target (or a pre-commit step) that diffs rule counts and text across CLAUDE.md and all `.claude/agents/*.yaml` files. Currently this is a purely manual obligation noted in CLAUDE.md. | M | Med | NEW: m1-lint |
| P4 | Create a `healthcheck.sh` script that verifies: git hooks are symlinked, queue.schema.json validates queue.json, all agent YAMLs parse correctly, and logs are writable. Run at session start (pm-start skill). | S | Med | NEW: pm-healthcheck |
| P5 | Add a token dashboard to `/pm-status`: show cumulative spend per agent per task from `logs/token_log.jsonl`, warn if any task has consumed >80% of its token_estimate. | M | Med | NEW: pm-token-dashboard |

---

## System 2: pensieve (n8n + Pi4 + Obsidian)

### Current State

Pensieve is a personal knowledge capture pipeline. Users submit notes via Telegram (webhook), Gmail (polling label "Pensieve"), or Obsidian Clipper (direct write). The Telegram and Gmail paths call the Claude API (claude-haiku-4-5) to summarize and tag the input, then write a YAML-frontmatter Markdown file to `/opt/obsidian-vault/` on Pi4, which is rclone-mounted to OneDrive and synced to Obsidian. n8n orchestrates all of this as two active workflows running in Docker on Pi4.

### Assessment

| Dimension | Finding | Severity |
|---|---|---|
| Operational complexity | Deployment requires a manual `deploy-workflow.py` run; no CI/CD. There are 4 stale inactive copies of the Telegram workflow in n8n (only 1 active). Gmail capture workflow was built in task-009 but never deployed to n8n — it exists only as a local JSON file. Workflow update requires a three-step sequence (prep → import → restart) documented in CLAUDE.md; no automation. rclone service restart has an undiscoverable dependency on n8n restart. | High |
| Cost | claude-haiku-4-5 at 1,200 max_tokens per call. Cost is proportional to capture volume — low at current usage. No per-workflow cost tracking. No monthly cap configured in n8n. Haiku is the correct model choice for this task. | Low |
| Security | GitHub PAT stored as `/opt/n8n/github-pat` (chmod 600, owner pi) — accessible to all Pi4 shell users. No PAT rotation schedule. n8n credentials are AES-encrypted at rest. Workflow JSONs in the repo use opaque n8n credential IDs (not raw tokens) — no plaintext secrets in git. Telegram webhook is unauthenticated (any HTTP POST to the webhook URL triggers execution) — mitigated by Telegram's own HTTPS-only delivery. | Med |
| Availability | Pi4 is SPOF: n8n, obsidian vault, and rclone mount all live here. No health monitoring of the n8n container. Telegram webhook drops messages silently if n8n is down for >48h (Telegram retry window). Gmail trigger is poll-based — Pi4 outage causes delay, not message loss. No alerting if n8n goes unhealthy. rclone mount failure causes vault writes to silently succeed at OS level but not reach OneDrive (stale FUSE fd). | High |

### Improvement Proposals

| P | Proposal | Effort | Impact | BL ref or NEW |
|---|---|---|---|---|
| P1 | Deploy the gmail-capture.json workflow to n8n (task-009 built it; deploy steps in `artefacts/task-009/deploy-notes.md`). Requires Gmail OAuth credential + Pensieve label re-selection after import. | S | High | BL-015 deploy step (pending) |
| P2 | Refactor shared pipeline stages (`Claude API`, `Parse Claude Response`, `Build Markdown Note`, `Write Note to Vault`) into a single reusable n8n sub-workflow called by both Telegram and Gmail workflows. Eliminates the dual-maintenance burden and divergence risk. | M | High | NEW: pensieve-subworkflow-refactor |
| P3 | Add an n8n health-check Telegram alert: a scheduled workflow that runs every 15 min, pings the n8n API, and sends a Telegram message to the owner if any active workflow has had no execution in >2h during waking hours. | S | High | NEW: pensieve-n8n-healthcheck |
| P4 | Clean up stale workflow copies in n8n: delete 3 inactive "Pensieve — Telegram Capture" duplicates + unnamed "My workflow" entries. Archive to reduce confusion and eliminate false-positive execution history. | S | Low | NEW: n8n-workflow-cleanup |
| P5 | Implement PAT rotation procedure: document a quarterly PAT rotation runbook in `pensieve/docs/pat-rotation.md` and add a calendar reminder. | S | Med | NEW: pat-rotation-runbook |
| P6 | Add `deploy-gmail.sh` wrapper script that runs the three-step deploy sequence for gmail-capture.json non-interactively. Add to the pm-close checklist as a pending deploy guard. | S | Med | NEW: gmail-deploy-automation |

---

## System 3: mas_agent (mas_personal_assistant)

### Current State

mas_personal_assistant is a Docker Compose stack running on Pi4 with four containers: `mas-telegram` (Python polling bot, healthy), `mas-backend` (FastAPI REST API, healthy), `mas-frontend` (nginx React SPA, **unhealthy**), and `mas-postgres` (PostgreSQL 15, healthy). The primary user-facing interface is the Telegram bot, which handles natural language queries and slash commands, routing them through a `Coordinator` to agents including `DailyFactsAgent`, `CalendarAgent`, `PlanningAgent`, and others. The frontend at `mas.femic.nl` provides a web dashboard but receives only automated/crawler traffic.

### Assessment

| Dimension | Finding | Severity |
|---|---|---|
| Operational complexity | Stack deployed 4 months ago via `start.sh`/`stop.sh`/`status.sh`. Updates require SSH → git pull → docker-compose rebuild. `mas-frontend` has been unhealthy for the entire 4-month deployment (82,589 failures). **Root cause confirmed**: BusyBox `wget` resolves `localhost` to `[::1]` (IPv6); nginx only listens on `0.0.0.0:80` (IPv4). The container serves traffic correctly — the healthcheck is wrong. No monitoring alerts on unhealthy containers. | High |
| Cost | Dual LLM clients: OpenAI (gpt-4o-mini secondary) and Anthropic (`claude-3-5-sonnet-20240620` primary — **a 2024 model ID, outdated**). Monthly budgets configured ($20 OpenAI, $10 Anthropic) but `check_budget()` is purely informational — no blocking when budget is exceeded. `daily_facts_agent.py` calls LLM once per day. Total cost likely <$5/month at current usage. | Low |
| Security | (1) **Telegram listener does not validate `chat_id` on inbound messages** — any Telegram user who discovers the bot token can send commands and receive responses. (2) `.env.production` lives at `/opt/mas/.env.production` — never committed to git. (3) JWT secret enforcement implemented (rejects weak defaults at startup). (4) Pre-commit hooks include `detect-secrets`, `bandit`, `mypy`. (5) API has rate limiting and request size limits. The Telegram auth gap is the primary active exposure. | Med |
| Availability | `restart: unless-stopped` on all containers provides auto-restart. 32 daily backups of data + credentials retained 30 days. mas-backend and mas-telegram are healthy. mas-frontend is unhealthy (functionally serving). No off-Pi health monitoring. Pi4 is SPOF. No external uptime monitoring. | Med |

### Improvement Proposals

| P | Proposal | Effort | Impact | BL ref or NEW |
|---|---|---|---|---|
| P1 | Fix mas-frontend healthcheck: change `http://localhost:80` to `http://127.0.0.1:80` in the production docker-compose or Dockerfile. Rebuild container. Resolves 4+ months of false unhealthy state. | S | High | NEW: fix-frontend-healthcheck |
| P2 | Add Telegram sender auth guard in `telegram_listener.py`: at the top of `_process_update()`, compare `message["chat"]["id"]` against `settings.telegram_chat_id` and drop (with a warning log) any update from an unauthorized chat. | S | High | NEW: telegram-sender-authz |
| P3 | Upgrade `LLM_PRIMARY_MODEL` from `claude-3-5-sonnet-20240620` to `claude-sonnet-4-6` to align with project_manager's model policy and access current model capabilities. | S | Med | NEW: mas-model-upgrade |
| P4 | Add hard budget enforcement to `LLMClient.chat()`: call `check_budget()` before each API call; if budget is exceeded, raise a `BudgetExceededError` rather than proceeding. Log the blocked call. | M | Med | NEW: mas-budget-hard-cap |
| P5 | Add external uptime monitoring for mas-telegram and mas-backend: configure UptimeRobot or Uptime-Kuma to ping the `/health` endpoint of mas-backend (already implemented). Alert via Telegram if non-200 for >5 min. | S | Med | NEW: mas-external-monitoring |

---

## Cross-cutting Concerns

- **Pi4 is SPOF for both pensieve and mas_agent**: n8n, obsidian vault, mas containers, and Nginx Proxy Manager all run here. A single hardware failure, power outage, or SD card corruption disables both systems simultaneously. Mitigation options: (a) nightly Pi4 SD card image backup to Pi5 or NAS, (b) n8n cloud fallback, (c) redundant Pi4 for critical services.
- **No cross-system monitoring or alerting**: all three systems run independently with no shared observability plane. There is no Telegram alert if n8n goes down, no notification if mas_agent crashes, and no token overspend alert from project_manager. A single lightweight n8n health-check workflow would cover pensieve and mas_agent simultaneously.
- **No token budget hard cap in any system**: project_manager tracks estimates in `token_log.jsonl` but the 500k cap in CLAUDE.md is advisory. mas_agent has budget fields but `check_budget()` is report-only. A shared pattern (config → pre-call check → blocking error) should be standardized across both.
- **No cross-project coordination**: project_manager manages its own task queue; mas_personal_assistant has its own task model. A backlog item submitted via Telegram BACKLOG: flows through pensieve → project_manager but never reaches mas_agent's task system (and vice versa). There is no shared task or context state between the two systems.
- **Dual LLM vendor dependency (mas_agent)**: mas_agent uses both OpenAI and Anthropic. project_manager and pensieve use Anthropic only. Consolidating mas_agent to Anthropic-only (gpt-4o-mini → haiku-4-5 for secondary tasks) would reduce vendor surface and align with the house model policy.
- **n8n version lag**: n8n is running v2.13.4 with a deprecation warning about `/home/node/.n8n/binaryData` being renamed in v3. No upgrade plan documented.

---

## Recommended Next Actions (top 5 ranked by effort-vs-impact)

| Rank | Action | System | Effort | Why now |
|---|---|---|---|---|
| 1 | Fix mas-frontend healthcheck (`localhost` → `127.0.0.1`) | mas_agent | S | 4+ months of false alarm suppresses real health signal; confirmed 1-line fix |
| 2 | Add Telegram sender auth guard in `telegram_listener.py` | mas_agent | S | Any Telegram user can issue commands; active security gap with a simple fix |
| 3 | Add n8n health-check workflow with Telegram alert | pensieve | S | Pi4 SPOF + no alerting = silent failure; covers pensieve and mas_agent in one workflow |
| 4 | Refactor pensieve shared pipeline into n8n sub-workflow | pensieve | M | 4 duplicated Code nodes; every future AI pipeline change must be applied twice |
| 5 | Add runtime token cap enforcement in project_manager | project_manager | S | Declared 500k policy has no runtime enforcement; runaway agent can silently exceed budget |
