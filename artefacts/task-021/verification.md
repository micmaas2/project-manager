# Verification — task-021: health-api base image bullseye → bookworm (BL-014)

**Date**: 2026-04-14
**Builder**: Sonnet [Builder]

---

## Acceptance Criteria Verification

### AC1: Dockerfile updated to bookworm base image

```
FROM python:3.11-slim-bookworm AS base
```

**Result**: PASS — Confirmed via `grep 'FROM' /opt/mas/docker/mas/Dockerfile`

Note: Untagged `python:3.11-slim` was actually resolving to Debian 13 (trixie/unstable) on
Pi4 ARM. There is no separate "health-api" service — this refers to the `mas-backend` service
which exposes the `/health` endpoint. Pinned to `python:3.11-slim-bookworm` (Debian 12 LTS)
for reproducible, stable production builds.

---

### AC2: Image builds successfully on Pi4 ARM

```
docker build -f /opt/mas/docker/mas/Dockerfile -t mas-mas-backend /opt/mas
```

**Result**: PASS — Build completed with exit code 0. One cosmetic warning (AS casing) fixed inline.

---

### AC3: health-api container starts and /health returns 200

```bash
sudo docker exec mas-backend curl -sf http://127.0.0.1:8000/health
```

**Output**: `{"status":"healthy"}`

**Result**: PASS

OS in running container:
```
PRETTY_NAME="Debian GNU/Linux 12 (bookworm)"
```

---

### AC4: No regressions in other pi-homelab services

```
docker ps (all mas-* services):
  mas-backend   Up (health: starting → healthy)
  mas-telegram  Up
  mas-frontend  Up (healthy)
  mas-postgres  Up (healthy)
```

**Result**: PASS — All services started. Calendar sync shows a pre-existing OAuth token
error (`invalid_grant`) that predates this change and is unrelated to the base image.

---

## Commit

```
[FIX] Pin base image to python:3.11-slim-bookworm (BL-014)
  bb94d27 on feature/task-021-bookworm-base in /opt/mas
```

## VERDICT: PASS
