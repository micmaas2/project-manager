# Pensieve — n8n Workflows

n8n workflow JSON files for the Pensieve system. Deployed on Pi4 (192.168.1.10) via the n8n Docker container.

## Workflows

| File | Name | Description | Status |
|------|------|-------------|--------|
| `n8n-healthcheck.json` | n8n Health Check — Idle Workflow Alert | Checks every 15 min if any active n8n workflow is idle >2h during waking hours (07:00–23:00 Amsterdam); sends Telegram alert | Active |

## Deploy Pattern

All workflows follow the same deploy sequence:

1. **Create credential** (if new): `POST /api/v1/credentials` with the appropriate type
2. **Patch workflow JSON**: replace placeholder credential IDs with real ones
3. **Import**: `docker exec n8n n8n import:workflow --input=...`
4. **Activate**: `POST /api/v1/workflows/{id}/activate` (import always deactivates)
5. **Restart**: `docker restart n8n`
6. **Verify**: `GET /api/v1/workflows` — confirm `active: True`

See individual `artefacts/task-XXX/deploy-notes.md` for workflow-specific steps.

## Workflow Details

### `n8n-healthcheck.json`

- **Workflow ID**: `b5717a69-a46c-484e-ac44-aa65e143acfd`
- **Schedule**: every 15 minutes
- **Logic**: queries n8n API for active workflows → checks last execution timestamp → alerts on idle >2h (waking hours only)
- **Telegram credential**: `NB55cLp798oiazqt` (Telegram account)
- **n8n API credential**: `LYT7O6kJGepy6he5` (n8n API Key, httpHeaderAuth)
- **Alert target**: chat_id `7761755508`
- **Deploy notes**: `artefacts/task-030/deploy-notes.md`
- **Tests**: `artefacts/task-030/test_healthcheck_workflow.js` (20/20 passing)
