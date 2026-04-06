# BL-030 Review: BACKLOG: Prefix Routing for Telegram Workflow

**Status: APPROVED**

**Reviewer:** Builder agent (Sonnet 4.6) [Sonnet]
**Date:** 2026-04-06
**Artefact:** `/opt/claude/pensieve/workflows/telegram-capture.json`

---

## Review Checklist

### Architecture / Design
- [x] IF node inserted correctly between Telegram Trigger and Claude API — existing capture path unchanged
- [x] IF node output index 0 (true branch) routes to backlog sub-flow; index 1 (false branch) routes to Claude API — matches n8n IF node output ordering
- [x] Backlog sub-flow is a clean linear chain: Format → GET → Append+Commit → PUT → Reply
- [x] Existing nodes (Claude API, Parse Claude Response, Build Markdown Note, Write Note to Vault, Telegram Reply) are untouched in logic and IDs
- [x] Node positions spread vertically (y=120 for backlog path, y=480 for capture path) to avoid overlap in n8n canvas

### Security
- [x] GitHub PAT credential referenced by id (`h45FTOsmMrdSMPxB`) and name — never inlined in workflow
- [x] No secrets in node parameters or jsCode
- [x] Path traversal not applicable (no filesystem writes in backlog path)
- [x] Input validation: `Format Backlog Item` throws on empty title after prefix strip
- [x] Base64 content round-trip is safe (newline stripping before decode matches GitHub API behavior)

### Code Quality — Format Backlog Item
- [x] Regex `^backlog:\s*` with `i` flag correctly strips prefix case-insensitively
- [x] Returns `title`, `date`, `chatId` — all consumed downstream
- [x] Guard against empty title present

### Code Quality — Append and Commit Backlog
- [x] BL ID scanning uses `matchAll` with capture group — correct regex `/BL-(\d+)/g`
- [x] `padStart(3, '0')` produces BL-001, BL-002 etc.
- [x] Appends before trailing `---` if present, otherwise appends at end — handles both backlog.md formats
- [x] Commit message truncated at 60 chars for title — prevents oversized commit messages
- [x] References upstream nodes by exact name strings matching node `name` fields

### HTTP Request nodes
- [x] GET node: `authentication: "genericCredentialType"`, `genericAuthType: "httpHeaderAuth"` — correct for n8n v4
- [x] PUT node: same auth pattern; `Content-Type: application/json` header present
- [x] PUT body uses `={{ $json.commitMessage }}` / `={{ $json.encoded }}` / `={{ $json.sha }}` — correct n8n expression syntax
- [x] `User-Agent: n8n-pensieve` present on both GitHub calls (required by GitHub API)

### Telegram Reply — Backlog
- [x] `chatId` pulled from `Append and Commit Backlog` node output (has it from Format Backlog Item)
- [x] Message format: Dutch language consistent with existing reply node (`Backlog item toegevoegd`)
- [x] Credentials: same `telegram-cred` as existing Telegram Reply node

### JSON Integrity
- [x] `python3 -m json.tool` validation passed — no syntax errors
- [x] All existing node IDs preserved (`node-telegram-trigger`, `node-claude-api`, etc.)
- [x] New node IDs are unique and descriptive (`node-route-backlog-or-capture`, `node-format-backlog-item`, `node-get-backlog-md`, `node-append-commit-backlog`, `node-put-backlog-md`, `node-telegram-reply-backlog`)
- [x] All connections present and bidirectionally consistent (every node that should receive has a source, every source has a target)

---

## Issues Found

None — no blocking issues.

### Minor Notes (non-blocking)
1. `Format Backlog Item` reads directly from `$input.first().json.message.text` (Telegram Trigger data flows through the IF node unchanged), which is correct n8n behavior for IF node pass-through.
2. The `GET backlog.md from GitHub` node does not need to pass `itemData` — the `Append and Commit Backlog` code node correctly fetches it from the named `Format Backlog Item` node reference. Dual-parent data access pattern is idiomatic n8n.
3. The `NOTES` field in the workflow was extended with GitHub PAT setup instructions (step 5) — appropriate documentation addition.

---

## Verdict

**APPROVED** — Implementation is complete, secure, and architecturally sound. Ready for import into n8n and live testing with a Telegram message prefixed `BACKLOG:`.
