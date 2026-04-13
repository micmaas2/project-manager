# Verification — task-018: Fix mas-frontend Docker healthcheck

**Date**: 2026-04-13
**Agent**: Tester

---

## Commands Run

```bash
# Before fix
docker inspect mas-frontend --format='Health: {{.State.Health.Status}} | FailingStreak: {{.State.Health.FailingStreak}}'
# Output: Health: unhealthy | FailingStreak: 88765

# After rebuild
docker inspect mas-frontend --format='Health: {{.State.Health.Status}} | FailingStreak: {{.State.Health.FailingStreak}} | Started: {{.State.StartedAt}}'
# Output: Health: healthy | FailingStreak: 0 | Started: 2026-04-13T14:32:01.703887326Z

docker ps --filter name=mas-frontend
# NAMES          STATUS
# mas-frontend   Up N min (healthy)
```

## Acceptance Criteria

| Criterion | Result |
|---|---|
| docker-compose.production.yml healthcheck uses 127.0.0.1 | PASS |
| After rebuild: mas-frontend shows (healthy) | PASS |
| FailingStreak resets to 0 | PASS |
| Commit merged to micmaas2/mas_personal_assistant main | PASS (beac1d9) |

## Root Cause

BusyBox `wget` in `nginx:alpine` resolves `localhost` to `[::1]` (IPv6) via `/etc/hosts`. nginx was bound to `0.0.0.0:80` (IPv4 only). The healthcheck connected to `[::1]:80` which was refused — causing 88,765 consecutive failures over 4+ months.

## Fix Applied

- `docker/mas/Dockerfile.frontend` line 38: `localhost` → `127.0.0.1`
- `docker/mas/docker-compose.production.yml` line 68: `localhost` → `127.0.0.1` (frontend)
- `docker/mas/docker-compose.production.yml` line 44: `localhost` → `127.0.0.1` (backend, opportunistic)

## Verdict

**PASS** — mas-frontend container is now healthy. FailingStreak reset from 88,765 to 0.
