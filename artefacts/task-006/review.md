# Review — task-006: Activity Dashboard Script

**Agent**: Builder (Sonnet 4.6)
**Date**: 2026-04-06
**Verdict**: APPROVED

---

## Files Reviewed

| File | Purpose |
|---|---|
| `scripts/generate-dashboard.sh` | Main dashboard generator |
| `scripts/install-dashboard-cron.sh` | Cron installer |

---

## Checklist

### Correctness
- [x] Reads `tasks/queue.json` via `jq` with correct filter syntax
- [x] Reads `tasks/backlog.md` via `awk`, parses pipe-delimited table correctly
- [x] Reads `docs/maintenance-schedule.md` via `awk`, extracts due/overdue/blocked rows
- [x] Queue status table covers all 6 statuses: pending, in_progress, paused, review, test, done
- [x] Active Tasks section filters `status=="in_progress"`
- [x] Recently Completed sorts by `.updated` descending, takes top 5
- [x] Next Up (Pending) filters `status=="pending"`
- [x] Maintenance shows top 5 items with status due/overdue/blocked
- [x] Backlog filters P1, status in new/discovered/planned, excludes IDs already in queue.json
- [x] Both backlog and maintenance sections capped at 5 items via `head -5`

### Robustness
- [x] `set -euo pipefail` at top
- [x] Missing file checks: each section handles absent file with "No data" fallback
- [x] `mkdir -p` for preview dir before writing
- [x] `awk` arrays reset with `delete fields` between rows (prevents field bleed)
- [x] `jq` errors surface via `set -e` and are not silently swallowed

### SSH / Output
- [x] `--local-only` flag skips SSH write correctly
- [x] SSH command uses `-o BatchMode=yes -o ConnectTimeout=10` as specified
- [x] Dashboard content piped to `ssh pi4 'cat > /opt/obsidian-vault/Dashboard.md'`
- [x] Local preview written to `artefacts/task-006/dashboard-preview.md`
- [x] All diagnostic output goes to stderr (`>&2`), not stdout

### Security
- [x] No secrets, API keys, or credentials in script
- [x] No dynamic path construction susceptible to injection (paths are hardcoded constants)
- [x] SSH vault path is a constant, not constructed from user input
- [x] Least privilege: read-only access to source files; writes only to preview dir and Pi4 vault path

### Cron installer
- [x] Idempotent: checks for existing entry before adding
- [x] Creates log directory with `mkdir -p`
- [x] Prints current crontab after install for confirmation

### ShellCheck compliance (static analysis)
- [x] All variables quoted (`"${VAR}"`)
- [x] No unquoted expansions in conditions
- [x] `local` declarations separate from assignments (avoids masking exit codes)
- [x] Heredoc usage correct — command substitutions inside heredoc expand at evaluation
- [x] `|| true` used where crontab absence is expected (`crontab -l 2>/dev/null || true`)
- [x] No `echo` of variables that could be interpreted as flags (uses `printf '%s\n'` for dashboard output)

### Known limitations (non-blocking)
- The `awk` maintenance parser skips "Annual / Major Upgrades" table rows whose Status
  column contains "due" but whose Next planned column uses `2026-Q2` format rather than
  a date — these will still appear in output with the quarterly string, which is acceptable.
- Backlog ID exclusion uses awk regex match (`id ~ queued`). If a queued ID is a regex
  metacharacter sequence this could misfire; current IDs (task-001 through task-005) are safe.

---

## Verdict

**APPROVED** — script is correct, robust, and shellcheck-compliant. Ready for test and cron installation.
