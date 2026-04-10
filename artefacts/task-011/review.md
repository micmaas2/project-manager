# Review — task-011: pensieve-sync.sh

Reviewer: Reviewer [Sonnet]  
Pass: 2 (final)  
Date: 2026-04-10  
Status: **APPROVED**

---

## Acceptance Criteria

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Cron runs every 15 min on Pi4; pulls latest pensieve commits into /opt/obsidian-vault | PASS |
| 2 | Script logs success/failure to /var/log/pensieve-sync.log with timestamp | PASS |
| 3 | On pull failure, does NOT overwrite local files; logs error and exits non-zero | PASS |
| 4 | Deploy script and cron entry documented in artefacts/task-011/deploy-notes.md | PASS |

---

## Change Request Resolution (Pass 1 → Pass 2)

### CR-1 — Log file guard [RESOLVED]

**Verified**: Lines 35–41 add an early self-check that (a) creates the log file via `touch` if absent, printing to stderr and exiting 1 on failure, and (b) checks writability and exits to stderr if unwritable. Guard runs before the first `log()` call, so silent cron death is prevented.

### CR-2 — SSH identity in cron environment [RESOLVED]

**Verified**: Line 19 exports `GIT_SSH_COMMAND="ssh -i /root/.ssh/id_rsa -o StrictHostKeyChecking=no"` in the configuration block, making the key path explicit and cron-safe. `deploy-notes.md` lines 16–45 contain a dedicated "Deploy key for cron" section explaining the default path, how to override it, and the `/root/.ssh/config` alternative — both the script and the documentation are consistent.

---

## Code-Quality Finding Resolution (Pass 1 → Pass 2)

### M-1 — git output sanitized before logging [RESOLVED]

**Verified**: `sanitize_line()` (lines 61–68) strips ANSI escape sequences (`ESC [ ... m` and `ESC <char>`) via `sed`, then removes remaining non-printable control characters (0x00–0x08, 0x0B–0x1F, 0x7F) via `tr -d`, preserving TAB (0x09) and LF. Applied at all four git-output capture points (lines 117, 124, 131, 145).

### M-2 — `git diff --check` after error-path stash pop [RESOLVED]

**Verified**: Lines 132–143 — on `git merge --ff-only` failure, if stash pop succeeds, `git diff --check` is run; any conflict markers trigger `log "ERROR"` and `exit 1` before `log_and_exit` is reached. Failure path is clean and non-destructive.

### m-2 — `flock -n` concurrency guard [RESOLVED]

**Verified**: Lines 24–30 — `exec 9>/var/lock/pensieve-sync.lock` + `flock -n 9` placed at script startup, before the log file guard. Concurrent instances exit 0 immediately with a stderr warning (appropriate — skipping is not a failure). Lockfile path (`/var/lock/`) is standard on Debian/Raspberry Pi OS.

### m-3 — logrotate promoted to required step [RESOLVED]

**Verified**: `deploy-notes.md` Step 5 (lines 132–158) opens with: *"Unbounded log growth will fill the filesystem over time. This step is **required**, not optional."* The `copytruncate` rationale is correctly explained for concurrent-write safety.

---

## Full Checklist

| Item | Result |
|------|--------|
| `set -euo pipefail` present | PASS (line 5) |
| Log file guard (create + writability) before first log write | PASS (lines 35–41) |
| `flock -n` concurrency guard at startup | PASS (lines 24–30) |
| SSH identity exported for cron | PASS (line 19) |
| git output sanitized (ANSI + control chars) before logging | PASS (lines 61–68, applied at lines 117/124/131/145) |
| `git diff --check` after error-path stash pop | PASS (lines 135–138) |
| Fetch failure: vault untouched, stash restored, exit 1 | PASS (lines 116–123) |
| Merge failure: vault untouched, stash restored with conflict check, exit 1 | PASS (lines 130–144) |
| Successful path logs commit count and SHA range | PASS (lines 163–168) |
| Cron entry `*/15 * * * *` documented in deploy-notes.md | PASS (Step 4) |
| SSH deploy key guidance in deploy-notes.md | PASS (Prerequisites section) |
| Logrotate marked required in deploy-notes.md | PASS (Step 5) |
| No secrets or hardcoded credentials | PASS |
| No external deps beyond git + bash + coreutils | PASS |

---

## Non-blocking Observations

- **Stash pop without `--index`**: `git stash pop` does not restore the original staged/unstaged split. Acceptable — vault is append-only and the stash scenario is already flagged as WARN-worthy.
- **`/root/.ssh/id_rsa` default path**: the script comments clearly instruct the operator to verify or update this path before deploying. Adequate for a deploy-time decision.
- **Empty GIT log lines**: blank lines from git output appear as `[GIT] ` in the log. Cosmetic; no functional impact.

---

## Summary

All four acceptance criteria pass. All change requests (CR-1, CR-2) and all code-quality findings (M-1, M-2, m-2, m-3) from Pass 1 are verifiably resolved in the updated script and deploy notes. The implementation is correct, defensively written, and safe to deploy.

**Status: APPROVED — ready for Tester.**
