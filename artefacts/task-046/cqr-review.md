# CQR Review — task-046: MAS Uptime Monitoring (BL-063)

**Reviewer**: code-quality-reviewer [Sonnet]
**Date**: 2026-04-27
**Verdict**: BLOCKING

---

## Overall verdict

BLOCKING — one critical security issue (live credential hardcoded in a committed file) must be
resolved before this task is marked done. All other findings are minor or informational.

---

## Findings

### F1 — CRITICAL: Live Telegram bot token hardcoded as fallback default
**Confidence**: 98
**Location**: `setup-uptime-kuma.py` line 30–31; `/opt/mas/scripts/setup-uptime-kuma.py` (Pi4)
**Status**: BLOCKING

The script uses `os.environ.get("TELEGRAM_BOT_TOKEN", "<live-token>")` with the actual
production bot token as the fallback value. Verified on Pi4: the hardcoded default is a
46-character string matching the Telegram bot token format, and it differs from the value in
`/opt/mas/.env` (meaning the fallback is a separate real token, not a placeholder).

The token appears in plain text in:
- `artefacts/task-046/setup-uptime-kuma.py` (committed to git history)
- `/opt/mas/scripts/setup-uptime-kuma.py` on Pi4 (world-readable: permissions 644, owner root)

Anyone with read access to the repo or Pi4 filesystem (including any process running as a
non-root user) can read the token and send arbitrary Telegram messages as the MAS bot, or
enumerate chats the bot is a member of.

**Fix**:
1. Remove the hardcoded fallback — raise an error if the env var is absent:
   ```python
   TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
   if not TELEGRAM_BOT_TOKEN:
       print("ERROR: TELEGRAM_BOT_TOKEN environment variable is required.")
       sys.exit(1)
   ```
2. Revoke/rotate the exposed token via BotFather (`/revoke` → issue new token → update
   `/opt/mas/.env`). The token that appeared in the artefact file must be treated as
   compromised regardless of whether it was ever used maliciously.
3. Tighten file permissions on the script: `chmod 700 /opt/mas/scripts/setup-uptime-kuma.py`
   (currently 644 — readable by any local user).
4. If the token appears in git history, note that `git log` will expose it. For a private
   Pi4-only repo this is lower risk, but if `project-manager` is ever pushed to a public
   remote the history must be scrubbed (`git filter-repo` or BFG).

---

### F2 — MAJOR: KUMA_ADMIN_PASS fallback is a weak literal password
**Confidence**: 85
**Location**: `setup-uptime-kuma.py` line 26
**Status**: BLOCKING (same class of issue as F1)

```python
ADMIN_PASS = os.environ.get("KUMA_ADMIN_PASS", "changeme123!")
```

`changeme123!` is a well-known placeholder phrase. If the operator runs the script without
setting `KUMA_ADMIN_PASS`, the Uptime-Kuma admin account is created with a guessable password.
Port 3001 is bound to `0.0.0.0` (visible from the LAN), so any device on the home network
can log in to Uptime-Kuma with the default password.

Note: `build_notes.md` line 38 contained `KUMA_ADMIN_PASS='MasAdmin2026!'` in a table cell
(not a secret store). That password should be changed if it was used during actual setup.

**Fix**: Apply the same pattern as F1 — require the env var, do not supply a default:
```python
ADMIN_PASS = os.environ.get("KUMA_ADMIN_PASS")
if not ADMIN_PASS:
    print("ERROR: KUMA_ADMIN_PASS environment variable is required.")
    sys.exit(1)
```

---

### F3 — MAJOR: build_notes.md exposes admin password in plain text
**Confidence**: 90
**Location**: `artefacts/task-046/build_notes.md` line 38
**Status**: BLOCKING (credential exposure in committed artefact)

The table cell `KUMA_ADMIN_PASS='MasAdmin2026!'` is committed to git in the artefact file.
Even if this is a one-off setup password, committing it establishes a pattern of storing
credentials in artefact docs. Uptime-Kuma is accessible from the LAN on port 3001.

**Fix**: Redact the cell to `KUMA_ADMIN_PASS='<set-via-env>'` and document that the password
was set interactively. Rotate the Uptime-Kuma admin password via the UI.

---

### F4 — MINOR: No connection timeout on UptimeKumaApi
**Confidence**: 70
**Location**: `setup-uptime-kuma.py` line 45
**Status**: Non-blocking

`UptimeKumaApi(KUMA_URL)` uses the library's default Socket.IO timeout. If Uptime-Kuma is
down or slow, the script may hang indefinitely. This is a one-shot setup script so the
practical impact is low, but a timeout parameter (if supported by the library version) would
make it safer to run in automation:
```python
api = UptimeKumaApi(KUMA_URL, timeout=30)
```
Check the `uptime-kuma-api` v1.2.1 docs — if `timeout` is not a constructor arg, wrap the
call in `signal.alarm` or document the hang risk.

---

### F5 — MINOR: Bare `except Exception` swallows unexpected errors at login
**Confidence**: 65
**Location**: `setup-uptime-kuma.py` lines 53–60
**Status**: Non-blocking

The exception handler checks `"need_setup"` / `"setup"` in the error string. Any other
exception (network error, auth failure with a different message, library version change) falls
through to the `else` branch and calls `sys.exit(1)` — which is correct. However, the error
message printed is the raw exception string (`f"ERROR: {e}"`), which may contain internal
state. Not a security risk in this context (script runs locally by root), but note it for
future scripts that log to shared facilities.

---

### F6 — MINOR: Magic numbers for ports not documented as constants
**Confidence**: 55
**Location**: `setup-uptime-kuma.py` lines 24, 36; `verify-health.sh` line 14; `deploy-notes.md`
**Status**: Non-blocking

Port 3001 (Uptime-Kuma) and port 8000 (mas-backend) appear as literals in multiple places.
They are defined inline rather than as named constants. Given that this is a one-off setup
script, this is low impact, but `UPTIME_KUMA_PORT = 3001` and `MAS_BACKEND_PORT = 8000` at
module top would make future port changes a single-line edit.

---

### F7 — INFORMATIONAL: re.DOTALL / $ anchor — not applicable
**Confidence**: N/A

No regular expression usage in either script. This check passes cleanly.

---

### F8 — INFORMATIONAL: No use of eval, os.system, or shell=True
**Confidence**: N/A

Neither script uses `eval`, `os.system`, `subprocess` with `shell=True`, or any other
command-injection-prone pattern. Clean.

---

### F9 — POSITIVE: verify-health.sh is well-structured
**Confidence**: N/A

- `set -euo pipefail` is present.
- `curl` has `--max-time` (10 s) and `--silent`.
- curl exit code is captured via `|| HTTP_CODE="000"` so the script does not abort on
  connection failure — the non-200 branch handles it cleanly.
- Exit codes 0/1 are documented in the header comment.
- URL is overridable via environment variable.
- No shell injection risk (HEALTH_URL is operator-controlled, not user-supplied).

---

### F10 — POSITIVE: Idempotent setup logic
**Confidence**: N/A

The script checks for existing notifications and monitors by name before creating them.
Re-running is safe and will not duplicate resources. Good defensive design for a one-shot
provisioning script.

---

## Summary

| # | Severity | Issue | Confidence | Blocking? |
|---|----------|-------|-----------|-----------|
| F1 | Critical | Live Telegram bot token hardcoded as env default | 98 | YES |
| F2 | Major | Weak literal password as KUMA_ADMIN_PASS default | 85 | YES |
| F3 | Major | Admin password in plain text in build_notes.md artefact | 90 | YES |
| F4 | Minor | No connection timeout on UptimeKumaApi | 70 | No |
| F5 | Minor | Bare except swallows unexpected login errors | 65 | No |
| F6 | Minor | Magic port numbers not extracted to named constants | 55 | No |

**Required actions before DONE**:
1. Remove the hardcoded Telegram bot token fallback; revoke and rotate the exposed token.
2. Remove the hardcoded password fallback from setup-uptime-kuma.py.
3. Redact `MasAdmin2026!` from build_notes.md; rotate the Uptime-Kuma admin password.
4. Tighten script file permissions on Pi4 to 700.

The `verify-health.sh` script is production-ready as-is.
