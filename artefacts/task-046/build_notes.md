# task-046: Build Notes — MAS Uptime Monitoring

**Agent**: Builder [Sonnet]
**Date**: 2026-04-27

---

## Discovery findings

### /health endpoint
- `docker exec mas-backend curl -s http://localhost:8000/health` returns `{"status":"healthy"}` (HTTP 200)
- Port 8000 is NOT published to the host — only accessible within Docker networks
- nginx proxy routes `/api/*` to `mas-backend:8000`, but `mas.femic.nl` has NO public DNS record
  - DNS query from Pi4 and from local machine both return NXDOMAIN
  - `mas.femic.nl` resolves only via local router DNS (192.168.1.1), which Uptime-Kuma containers cannot reach
  - Direct IP access via Docker network IP (172.21.0.3) returns HTTP 400 (Host header validation)

### Chosen URL: `http://mas-backend:8000/health`
- Uptime-Kuma connected to `mas_mas-network` Docker network → can reach `mas-backend` by DNS name
- `node -e "require('http').get('http://mas-backend:8000/health', ...)"` returns `200 {"status":"healthy"}`

### Monitoring solution: Uptime-Kuma (self-hosted Docker)
- No external account required
- Reuses existing MAS Telegram bot for alerts
- n8n is available (port 88) but Socket.IO-based Uptime-Kuma gives persistent monitoring with a UI
- `uptime-kuma-api` Python library installed with `--break-system-packages` (Debian 13 PEP 668)

---

## What was automated

| Step | Automated? | Notes |
|------|-----------|-------|
| Deploy Uptime-Kuma container | YES | `docker run` with `--restart=unless-stopped` |
| Connect to mas_mas-network | YES | `docker network connect` |
| Create admin account | YES via script | `KUMA_ADMIN_PASS=<redacted — set via KUMA_ADMIN_PASS env var>` |
| Configure Telegram notification | YES via script | Uses MAS bot token + chat_id |
| Create HTTP monitor | YES via script | `http://mas-backend:8000/health`, 60s interval, 3 retries |
| Verify monitor is UP | YES | `get_monitor_status(1)` returns `MonitorStatus.UP` |

---

## What is left manual

1. **Access Uptime-Kuma UI**: `http://192.168.1.10:3001` — login with `admin` / `<redacted — see KUMA_ADMIN_PASS env var>`
   - The admin password is stored only in the operator's memory; not committed to any file
2. **Test Telegram alert**: manually stop mas-backend and wait ~3 minutes (see deploy-notes.md)
3. **Kuma admin password change**: recommend changing after first login

---

## Decisions

- **Internal URL over external**: `mas.femic.nl` has no public DNS record; monitoring via external URL would be fragile. Internal Docker network is reliable and faster.
- **3 retries × 60s interval = ~3 min to alert**: satisfies the "5 min" SLO with margin.
- **keyword check not used**: the `uptime-kuma-api` v1.2.1 `add_monitor` does not persist the `keyword` field — confirmed via `get_monitors()`. HTTP 200 status code check alone is sufficient (the endpoint returns non-200 on error).
- **uptime-kuma-api installed system-wide**: used `--break-system-packages` on Pi4 (Debian 13). This is a known workaround and acceptable for a Pi4 tools host.

---

## Advisor Consults
None required — decision was straightforward.

---

## Fix Loop (Reviewer + CQR blocking findings)
- F1/F2: Removed hardcoded credential fallbacks; script now fails fast if TELEGRAM_BOT_TOKEN or KUMA_ADMIN_PASS env vars are absent
- F3: Redacted admin password from build_notes.md
- F4: Fixed verify-health.sh default URL to http://mas-backend:8000/health
