# Build Notes — task-014 (Architecture Review)

## Investigation Steps

### Phase 1: project_manager
1. Read `/opt/claude/project_manager/CLAUDE.md` — full workspace context, model policy, agent pipeline, governance rules.
2. Listed `.claude/agents/` — found: builder.yaml, doc-updater.yaml, manager.yaml, reviewer.yaml, self-improver.yaml, tester.yaml.
3. Read `manager.yaml` and `builder.yaml` — confirmed agent policies, model assignments, allowed_tools.
4. Read `hooks/pre-commit` and `hooks/commit-msg` — confirmed branch protection, sensitive-file detection, commit format enforcement.
5. Read `tasks/queue.json` — confirmed schema, observed task-014 is the current task.
6. Read `tasks/backlog.md` — confirmed BL-047 is the source BL item for this task.
7. Read `tasks/lessons.md` and `logs/token_log.jsonl` — confirmed token tracking is estimate-only with no runtime enforcement.

**Key findings**:
- `require_human_approval: false` on ProjectManager despite it having Write/Edit tools.
- 500k token cap in CLAUDE.md is advisory; no runtime enforcement exists.
- M-1 mirroring is manual; no automated consistency check.

### Phase 2: pensieve
1. Read `/opt/claude/pensieve/README.md` — full architecture, stack, known gotchas.
2. Read `workflows/telegram-capture.json` (full) — all nodes, credential references, jsCode blocks.
3. Analyzed `workflows/gmail-capture.json` — node names, credential references.
4. Read `setup/deploy-workflow.py` — confirmed n8n API-based merge/deploy approach.
5. SSH to Pi4: listed active n8n workflows — confirmed 4 stale Telegram Capture copies, gmail-capture.json NOT deployed.
6. SSH to Pi4: exported n8n credentials — confirmed 7 credentials, all AES-encrypted at rest.
7. Checked `/opt/n8n/github-pat` — confirmed flat file, chmod 600, contains real PAT.
8. Verified workflow JSONs in repo use credential ID references only — no plaintext PAT in git.

**Key findings**:
- 4 shared Code nodes between Telegram and Gmail workflows (partially diverged, structurally duplicated).
- Gmail workflow built in task-009 but never deployed to n8n.
- 4 inactive stale workflow copies in n8n.
- GitHub PAT in flat file on Pi4, no rotation schedule.
- n8n credentials AES-encrypted — not a git leak risk.

### Phase 3: mas_agent
1. SSH to Pi4: `docker ps --filter name=mas` — confirmed mas-frontend unhealthy (82,589 failures), others healthy.
2. SSH to Pi4: read `README.md`, `DEPLOYMENT.md` — confirmed architecture, backup strategy.
3. SSH to Pi4: `docker inspect mas-frontend` — confirmed healthcheck: `wget --quiet --tries=1 --spider http://localhost:80`.
4. Ran healthcheck manually in container — confirmed `wget` connects to `[::1]:80` (IPv6) but nginx only listens on `0.0.0.0:80` (IPv4). Root cause: BusyBox wget prefers IPv6 for `localhost`.
5. Confirmed nginx is running and serving traffic (200 responses in access logs).
6. Read `docker/mas/docker-compose.production.yml` — confirmed production stack config and healthchecks.
7. Read `docker-compose.dev.yml` — confirmed dev stack differs (no healthcheck on frontend).
8. Read first 80 lines of `src/agents/daily_facts_agent.py` and first 60 lines of `src/integration/telegram_listener.py`.
9. Read `src/config.py` — confirmed LLM model config (`claude-3-5-sonnet-20240620` — 2024 model ID), budget fields.
10. Grepped `src/utils/cost_tracker.py` and `src/integration/telegram_listener.py` — confirmed `check_budget()` is report-only (no blocking).
11. Grepped `telegram_listener.py` for sender authentication — confirmed NO chat_id validation on inbound messages. Bot responds to any sender.
12. Read `SECURITY_HARDENING_SUMMARY.md` — confirmed JWT enforcement, request size limits, pre-commit hooks (detect-secrets, bandit).
13. Confirmed 32 daily backups in `/opt/mas/backups/`, 30-day retention — working correctly.

**Key findings**:
- mas-frontend healthcheck root cause: IPv6 localhost resolution in BusyBox wget. Fix: use `127.0.0.1`.
- No Telegram sender auth — any user who discovers the bot token can interact with the bot.
- LLM_PRIMARY_MODEL is `claude-3-5-sonnet-20240620` (outdated 2024 ID — should be `claude-sonnet-4-6`).
- Budget config exists but is advisory only (no blocking).
- Security hardening otherwise solid (JWT, rate limiting, detect-secrets).

## Assumptions Made
- The GitHub PAT in `/opt/n8n/github-pat` is the same credential referenced by n8n as "GitHub PAT — project-manager". Not verified by decrypting the n8n credential — assumed from naming and creation date alignment.
- mas_frontend is intentionally not actively used by the owner (only crawler traffic visible in access logs). The dashboard UI is a placeholder for a future phase.

## Known Limitations
- Did not inspect `src/orchestration/coordinator.py` — the full agent routing logic in mas_agent is not reviewed.
- Did not run n8n execution history check — cannot confirm if the Gmail capture workflow was ever manually tested on Pi4.
- Token cost estimates for pensieve (Claude API calls) are not available without n8n execution history.
- Did not audit the full `.env.production` values — only checked structure and confirmed no git commit.

## Verification Steps
- **mas-frontend fix**: `docker exec mas-frontend wget --quiet --tries=1 --spider http://127.0.0.1:80` (should exit 0).
- **Telegram auth gap**: send a Telegram message to the bot from an unauthorized account — should receive a response (confirms the gap exists).
- **Gmail workflow deployment**: check n8n workflow list after deploy — `Pensieve — Gmail Capture` should appear as active.
- **Token cap enforcement**: add a dry-run guard to the proposed Python function and run a task — should print before agent spawn if estimate >400k.
