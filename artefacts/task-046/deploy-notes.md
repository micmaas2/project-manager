# task-046: Deploy Notes — MAS Uptime Monitoring

## What was configured

**Monitoring tool**: Uptime-Kuma (self-hosted Docker, `louislam/uptime-kuma:1`)
**Monitor target**: `http://mas-backend:8000/health` (internal Docker network)
**Alert channel**: Telegram (MAS bot → chat_id `7761755508`)
**Check interval**: 60 seconds
**Alert threshold**: 3 failed checks (~3 minutes) → Telegram alert fires

---

## Infrastructure

| Component | Details |
|-----------|---------|
| Container name | `uptime-kuma` |
| Port | `0.0.0.0:3001->3001/tcp` |
| Volume | `uptime-kuma` (Docker named volume, persisted) |
| Restart policy | `unless-stopped` |
| Docker networks | `bridge` (default) + `mas_mas-network` |
| UI URL | http://192.168.1.10:3001 |

### Why internal URL?
`mas.femic.nl` has no public DNS record — it resolves only via the home router's local DNS
(192.168.1.1), which Docker containers cannot reach. Uptime-Kuma is connected to the
`mas_mas-network` bridge network, enabling direct access to `mas-backend` by container name.

---

## Monitor configuration

| Field | Value |
|-------|-------|
| Name | MAS Backend /health |
| Type | HTTP |
| URL | `http://mas-backend:8000/health` |
| Method | GET |
| Expected status | 200 |
| Interval | 60s |
| Max retries | 3 |
| Notification | MAS Telegram Alert (Telegram) |
| Status (as of 2026-04-27) | UP |

---

## Telegram alert configuration

The Telegram notification uses the existing MAS bot:
- **Bot token**: from `/opt/mas/.env` → `TELEGRAM_BOT_TOKEN`
- **Chat ID**: from `/opt/mas/.env` → `TELEGRAM_CHAT_ID` (`7761755508`)
- Alert message format: Uptime-Kuma sends: `[MAS Backend /health] is DOWN — reason`

---

## Simulating downtime to test the alert

```bash
# 1. Stop mas-backend
ssh pi4 "docker stop mas-backend"

# 2. Wait ~3 minutes — Uptime-Kuma will fire a Telegram alert after 3 failed checks

# 3. Verify Telegram received the alert

# 4. Restart mas-backend
ssh pi4 "docker start mas-backend"

# 5. Uptime-Kuma sends a recovery notification when the check passes again
```

---

## Re-running setup from scratch

If Uptime-Kuma data needs to be reset:

```bash
# On Pi4:
sudo docker stop uptime-kuma && sudo docker rm uptime-kuma
sudo docker volume rm uptime-kuma
sudo docker run -d --restart=unless-stopped --name uptime-kuma \
  -p 3001:3001 -v uptime-kuma:/app/data louislam/uptime-kuma:1
sudo docker network connect mas_mas-network uptime-kuma

# Wait ~10 seconds, then run the setup script:
KUMA_ADMIN_PASS='<your-password>' python3 /opt/mas/scripts/setup-uptime-kuma.py
```

The setup script is at `/opt/mas/scripts/setup-uptime-kuma.py` on Pi4.
It creates the admin account, Telegram notification, and HTTP monitor in one pass.
On subsequent runs it detects existing resources and skips creation.

---

## Uptime-Kuma UI access

- URL: http://192.168.1.10:3001
- Username: `admin`
- Password: set during setup (not stored in any file; change via UI if needed)

---

## Verifying endpoint health manually

Use the `verify-health.sh` script (artefact in this directory) OR:

```bash
# From Pi4 (via Docker exec):
docker exec mas-backend curl -s http://localhost:8000/health
# Expected: {"status":"healthy"}

# From Uptime-Kuma container:
docker exec uptime-kuma node -e \
  "require('http').get('http://mas-backend:8000/health', r=>r.pipe(process.stdout))"
# Expected: {"status":"healthy"}
```

---

## Rollback plan

1. Stop and remove Uptime-Kuma: `sudo docker stop uptime-kuma && sudo docker rm uptime-kuma`
2. Optionally remove data volume: `sudo docker volume rm uptime-kuma`
3. No changes were made to mas-backend, the MAS codebase, or nginx config
4. Estimated time-to-remove: <5 minutes

## Incident owner

Michel Maas
