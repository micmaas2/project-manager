# Build Notes — task-021: health-api base image → bookworm (BL-014)

**Date**: 2026-04-14
**Builder**: Sonnet [Builder]
**Target**: `/opt/mas/docker/mas/Dockerfile` (Pi4)

---

## Discovery

No separate "health-api" service exists. The BL-014 description `(health-api)` refers to the
`mas-backend` container which serves the `/health` endpoint. The `mas-telegram` container also
uses the same Dockerfile.

The current `FROM python:3.11-slim` tag was resolving to **Debian 13 (trixie)** on Pi4 ARM —
not bullseye as the backlog implied. Trixie is Debian unstable/testing, not suitable for
production. Pinning to `python:3.11-slim-bookworm` (Debian 12 LTS) is correct.

---

## Change

```diff
- FROM python:3.11-slim as base
+ FROM python:3.11-slim-bookworm AS base
```

Also fixed `AS` casing (cosmetic Docker warning).

---

## Result

- Build: exit 0, no errors
- Runtime OS: `Debian GNU/Linux 12 (bookworm)` ✓
- `/health` endpoint: `{"status":"healthy"}` ✓
- All mas-* containers healthy ✓

---

## Advisor Consults

None required.

---

## Code Review Notes (code-quality-reviewer)

**APPROVED** with two advisory items (not blockers):
1. **SHA digest pinning** — for stronger supply-chain security, pin with `@sha256:...`; recommend as a separate backlog item
2. **Multi-stage build** — `gcc`/`g++` build tools remain in the production image; separate build/runtime stages would reduce attack surface; recommend as a separate backlog item
