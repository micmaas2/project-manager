# Test Report — task-032: pensieve PAT rotation runbook

**Date**: 2026-04-15
**Tester**: Tester agent (Sonnet)
**File under test**: `/opt/claude/pensieve/docs/pat-rotation.md`

---

## Check Results

### Check 1 — File exists
**Result**: PASS
**Evidence**: `/opt/claude/pensieve/docs/pat-rotation.md` resolved without error; file contains 174 lines.

---

### Check 2 — Contains step-by-step rotation procedure (numbered steps 1–4)
**Result**: PASS
**Evidence**: File contains all four numbered steps under `## Rotation Steps`:
- `### Step 1 — Create new PAT on GitHub` (line 50)
- `### Step 2 — Update the PAT file on Pi4` (line 73)
- `### Step 3 — Update the n8n credential` (line 87)
- `### Step 4 — Revoke the old PAT` (line 100)

Each step contains actionable sub-steps with UI navigation paths and CLI commands.

---

### Check 3 — Contains affected systems list (table or section covering n8n credential + workflow + file)
**Result**: PASS
**Evidence**: `## Affected Systems` section (line 10) contains a three-row table covering:
- n8n credential `GitHub PAT — project-manager` (id: `h45FTOsmMrdSMPxB`) on Pi4
- Workflow: `Pensieve — Telegram Capture` (n8n Docker container on Pi4)
- PAT file at `/opt/n8n/github-pat` on Pi4

All three required systems (n8n credential, workflow, file) are present.

---

### Check 4 — Contains post-rotation verification steps
**Result**: PASS
**Evidence**: `## Post-Rotation Verification` section (line 110) contains three verification sub-steps:
- `4a — Manual test via n8n UI` — execute workflow and check node HTTP status codes
- `4b — End-to-end test via Telegram` — send a message and verify inbox receipt
- `4c — Verify PAT file on Pi4` — confirm file prefix via `head -c 4`

---

### Check 5 — Contains quarterly reminder section
**Result**: PASS
**Evidence**: `## Quarterly Reminder` section (line 138) specifies:
- 90-day rotation schedule
- Google Calendar event title, recurrence, and description text
- Backlog BL item guidance for 2-week advance notice

---

### Check 6 — Secret scan: classic PAT pattern `ghp_[a-zA-Z0-9]{36}`
**Result**: PASS
**Evidence**: `grep -E "ghp_[a-zA-Z0-9]{36}" pat-rotation.md` → exit 1 (no matches).
Note: the file references the prefix `ghp_` as a literal placeholder string `ghp_<YOUR_NEW_TOKEN>` and a 4-char prefix check `'ghp_'` — neither match the 36-character suffix required by the pattern.

---

### Check 7 — Secret scan: fine-grained PAT pattern `github_pat_[a-zA-Z0-9_]{82}`
**Result**: PASS
**Evidence**: `grep -E "github_pat_[a-zA-Z0-9_]{82}" pat-rotation.md` → exit 1 (no matches).

---

### Check 8 — Contains rollback section
**Result**: PASS
**Evidence**: `## Rollback` section (line 152) covers:
- Steps to revoke the new (failed) PAT
- Acknowledgement that old PAT is already revoked (no automatic rollback)
- Recovery path: repeat Steps 1–3 to generate and install a fresh PAT
- Estimated time-to-restore: 5–10 minutes
- Preventive advice: complete Steps 1–3 before executing Step 4

---

## Summary

| # | Check | Result |
|---|---|---|
| 1 | File exists | PASS |
| 2 | Numbered rotation steps 1–4 | PASS |
| 3 | Affected systems table (credential + workflow + file) | PASS |
| 4 | Post-rotation verification steps | PASS |
| 5 | Quarterly reminder section | PASS |
| 6 | No live classic PAT (`ghp_` + 36 chars) | PASS |
| 7 | No live fine-grained PAT (`github_pat_` + 82 chars) | PASS |
| 8 | Rollback section | PASS |

## Overall Verdict: PASS

All 8 checks passed. The runbook is complete, correctly structured, and contains no embedded secrets.
