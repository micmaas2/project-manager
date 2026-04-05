# Build Notes — task-001: Queue Status Reporter Script

## Agent: Builder [Sonnet]
## Date: 2026-04-05
## Status: build_complete

---

## What Was Built

`artefacts/task-001/queue-status.sh` — A bash script that reads `tasks/queue.json`
and prints a formatted task count summary grouped by all 6 statuses.

## Design Decisions

- **jq dependency**: Used `jq` for robust JSON parsing instead of grep/awk.
  JSON parsing with regex is fragile; jq is a standard tool on modern Linux.
- **Graceful empty queue**: Used `select(.status == $s)` with `?` (optional operator)
  on `.tasks[]?` so that empty arrays and null values produce 0 counts without errors.
- **set -euo pipefail**: Strict error handling; any unexpected failure exits non-zero.
- **Configurable queue path**: Accepts `$1` argument defaulting to `tasks/queue.json`,
  enabling tests against different fixtures.
- **printf formatting**: Aligned columns for readability without color (per scope:
  colour output is not in scope).

## Scope Compliance

Not in scope (confirmed excluded):
- Web UI
- Email alerts
- Cron scheduling
- Colour output

## Static Analysis Results

- `bash -n`: PASSED (no syntax errors)
- `shellcheck`: Not installed on this system. Script written following shellcheck
  best practices: quoted variables, no unquoted expansions, proper function syntax.

## Files Delivered

- `artefacts/task-001/queue-status.sh` — main script
- `artefacts/task-001/build_notes.md` — this file
