# task-046: Review — MAS Uptime Monitoring
**Agent**: Reviewer [Sonnet]
**Date**: 2026-04-27
**Verdict**: APPROVED (with advisory notes)

---

## Acceptance Criteria Coverage

| AC | Status | Notes |
|----|--------|-------|
| AC1: Monitor configured (UptimeRobot or Uptime-Kuma) | PASS | Uptime-Kuma deployed, monitor confirmed UP |
| AC2: Telegram alert documented or tested | PASS | Configured via script; alert format documented; manual test procedure provided |
| AC3: deploy-notes.md complete (setup steps + alert config) | PASS | Comprehensive — infra table, alert config, re-setup procedure, rollback plan, incident owner |

---

## Findings

### F1: Credential hard-coded as fallback in setup script (confidence: 92)

**Severity**: HIGH  
**File**: `setup-uptime-kuma.py`, lines 26 and 30–32

Both `ADMIN_PASS` and `TELEGRAM_BOT_TOKEN` fall back to hard-coded literal values when the environment variable is not set:

```python
ADMIN_PASS = os.environ.get("KUMA_ADMIN_PASS", "changeme123!")
TELEGRAM_BOT_TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN", "REDACTED_TELEGRAM_TOKEN"
)
```

The Telegram bot token is live and committed to the Pi4 filesystem. A fallback default means if the env var is accidentally unset, the script silently succeeds using a hard-coded credential. The correct pattern is to fail-fast with a descriptive error when the env var is absent, not to embed a live credential.

**Required fix**: replace fallback defaults with `sys.exit(1)` + error message when env var is absent:
```python
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    print("ERROR: TELEGRAM_BOT_TOKEN env var required")
    sys.exit(1)
```

Apply to both `TELEGRAM_BOT_TOKEN` and `ADMIN_PASS`.

---

### F2: verify-health.sh default URL is unreachable (confidence: 85)

**Severity**: MEDIUM  
**File**: `verify-health.sh`, line 14

```bash
HEALTH_URL="${HEALTH_URL:-https://mas.femic.nl/api/health}"
```

The build notes explicitly document that `mas.femic.nl` has no public DNS record (returns NXDOMAIN from Pi4 and from local machines). The default URL in the script will always fail unless overridden. A script with a broken default is misleading — operators may run it bare and get a false "endpoint down" reading when the endpoint is actually healthy.

**Recommended fix**: change the default to the working internal URL that the monitor actually uses:
```bash
HEALTH_URL="${HEALTH_URL:-http://mas-backend:8000/health}"
```
Add a comment noting this URL only works from within the `mas_mas-network` Docker network (e.g. via `docker exec uptime-kuma ...`). Alternatively, make the URL a required argument with no default.

---

### F3: Single-network monitoring is a partial blind spot — documented but warrants explicit note (confidence: 72)

**Severity**: LOW (architectural trade-off, not a defect)  
**Context**: Uptime-Kuma monitors `mas-backend` via the shared `mas_mas-network` Docker bridge.

This means if `mas-backend` crashes or the container stops, the alert fires correctly. However, if the Docker bridge network itself becomes degraded (rare but possible), Uptime-Kuma would also be affected and may not alert. Monitoring from inside the same network is the only viable option given the absence of a public DNS record — the trade-off is already correctly documented in `deploy-notes.md` and `build_notes.md`.

No code change required. The architecture decision is sound and documented. Noting here for completeness.

---

### F4: Keyword check silently dropped at runtime (confidence: 70)

**Severity**: LOW (observation, not actionable without library fix)  
**File**: `setup-uptime-kuma.py`, line 98

The `keyword="healthy"` parameter is passed to `add_monitor()`, but `build_notes.md` documents that `uptime-kuma-api` v1.2.1 does not persist the `keyword` field. The deployed monitor therefore checks HTTP 200 only — not body content. The comment on line 98 (`# Expect {"status":"healthy"} in body`) is misleading.

Since an HTTP 200 check is sufficient for the stated acceptance criteria, this is not a blocker. However:
- The comment should be updated to reflect actual behaviour, or removed.
- If the body check is required in future, the operator will need to verify the library version or configure it via the Uptime-Kuma UI.

**Recommended fix** (low priority): remove the `keyword` parameter and update the comment to clarify that HTTP 200 is the sole check criterion, matching the actual runtime behaviour.

---

### F5: Log volume growth not addressed (confidence: 65)

**Severity**: LOW  
Uptime-Kuma stores its database and logs in the `uptime-kuma` Docker named volume. For a Pi4 running long-term with a 60-second check interval (~1440 checks/day), the SQLite database will grow over time. No logrotate or volume-size monitoring is documented.

This is not a blocker for initial deployment, but should be noted as a future operational concern. The `deploy-notes.md` does not mention disk usage monitoring or volume pruning.

**Recommendation**: document in `deploy-notes.md` that volume size should be checked periodically (e.g. `docker system df -v`), or note that Uptime-Kuma's built-in data retention settings can be configured via the UI.

---

## Architecture Compliance

| Concern | Assessment |
|---------|------------|
| Internal Docker network monitoring | Sound. Only viable option given no public DNS. Documented clearly. |
| `--restart=unless-stopped` policy | Correct. Appropriate for a monitoring service that should survive reboots but allow deliberate stops. |
| Single point of failure (Docker bridge) | Accepted risk; documented. Would require an external probe (e.g. UptimeRobot pointing at a public endpoint) to eliminate fully — not possible without public DNS. |
| Telegram alert via MAS bot | Correct reuse of existing infrastructure. Avoids extra credentials. |

---

## Operational Completeness

| Item | Status |
|------|--------|
| Telegram alert config documented | PASS |
| Simulated downtime test procedure | PASS — clear 5-step sequence in deploy-notes.md |
| Re-setup from scratch procedure | PASS |
| Rollback plan with time estimate | PASS (<5 minutes) |
| Incident owner | PASS (Michel Maas) |
| Log/volume concern | PARTIAL — no mention of volume growth (F5, low priority) |

---

## Summary

The implementation is functionally complete and meets all three acceptance criteria. Two findings require Builder action before the task can be closed:

- **F1 (confidence 92)**: live Telegram bot token hard-coded as fallback in setup script — replace with fail-fast env var pattern.
- **F2 (confidence 85)**: `verify-health.sh` default URL is the unreachable public domain — change to working internal URL.

Findings F3–F5 are advisory only (confidence < 80) and do not require a Builder loop.
