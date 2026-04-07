# Review — task-008: Laptop Backlog and Pensieve Capture

**Agent**: Builder (Sonnet 4.6)
**Date**: 2026-04-07
**Verdict**: APPROVED

---

## Files Reviewed

| File | Purpose |
|---|---|
| `scripts/capture.py` | Main capture script (stdlib only, Python 3.10+) |
| `artefacts/task-008/deploy-notes.md` | Setup and usage guide |
| `artefacts/task-008/test_capture.py` | Unit tests (7 cases, no network) |

---

## Checklist

### Correctness
- [x] Backlog: reads current telegram-inbox.md via GitHub API, appends new line, commits
- [x] Pensieve: creates YAML frontmatter note in `captures/YYYY-MM-DD-<slug>.md` in pensieve repo
- [x] `rstrip("\n") + "\n"` pattern ensures exactly one newline before new item (no blank lines between entries)
- [x] Date format: ISO 8601 (`YYYY-MM-DD`) via `datetime.date.today().isoformat()`
- [x] Slug: alphanumeric + hyphens only, max 50 chars, strips leading/trailing hyphens
- [x] `--dry-run` reads file (to show what would append) but skips `_put_file` entirely

### Security
- [x] Token read from `GITHUB_TOKEN` env var — never hardcoded, never printed
- [x] Error messages do not echo the token
- [x] `urllib.request` with 15s timeout — no redirect to private IPs possible via HTTPS API endpoint
- [x] Slug sanitised before use in file path: `c if c.isalnum() or c == "-" else "-"` — no path traversal
- [x] File path is always `captures/YYYY-MM-DD-<slug>.md` (controlled prefix) — no user-controlled path injection

### Robustness
- [x] Missing token → clear error message with PAT creation URL, exits 1
- [x] HTTP errors from GitHub API → status code + body printed, exits 1
- [x] Network errors → URLError message printed, exits 1
- [x] Existing pensieve note (SHA collision) handled — SHA fetched and passed for update
- [x] No external dependencies — stdlib only (`urllib`, `base64`, `json`, `argparse`, `datetime`)

### Scope compliance
- [x] No Claude Code or SSH required — GitHub API only ✓
- [x] Works from any laptop with Python 3.10+ and a GitHub PAT ✓
- [x] deploy-notes.md documents setup, usage, demo script, and known limitations ✓

### Known limitations (documented)
- Pensieve notes land in GitHub repo (`captures/`), not directly in Pi4 Obsidian vault — vault sync requires Pi4-side pull or task-009 webhook
- `--dry-run` still makes one read API call (by design — shows what would be appended)

---

## Verdict

**APPROVED** — correct, secure, zero external deps. Demo-ready.
