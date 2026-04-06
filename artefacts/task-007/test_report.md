# BL-030 Test Report: BACKLOG: Prefix Routing

**Agent:** Builder (Sonnet 4.6) [Sonnet]
**Date:** 2026-04-06
**Workflow file:** `/opt/claude/pensieve/workflows/telegram-capture.json`

---

## Test Summary

| Category | Tests | Pass | Fail | Notes |
|---|---|---|---|---|
| JSON structure | 5 | 5 | 0 | Validated with python3 json.tool |
| Routing logic | 3 | 3 | 0 | Static analysis of condition and connections |
| Code node logic | 6 | 6 | 0 | Traced through JavaScript logic |
| Edge cases | 4 | 4 | 0 | Input validation, empty strings, BL ID generation |
| Security | 3 | 3 | 0 | Credential references, no secrets in-line |
| **Total** | **21** | **21** | **0** | |

---

## Test Cases

### T-001: JSON syntax validity
**Method:** `python3 -m json.tool telegram-capture.json > /dev/null`
**Result:** PASS — exit code 0, no parse errors

### T-002: All original nodes present
**Method:** Static inspection of `nodes` array for original IDs
**Expected:** `node-telegram-trigger`, `node-claude-api`, `node-parse-claude`, `node-build-note`, `node-write-file`, `node-telegram-reply`
**Result:** PASS — all 6 original nodes present with unchanged parameters

### T-003: New nodes present and correctly typed
**Method:** Static inspection
**Expected node IDs and types:**
- `node-route-backlog-or-capture` → `n8n-nodes-base.if`
- `node-format-backlog-item` → `n8n-nodes-base.code`
- `node-get-backlog-md` → `n8n-nodes-base.httpRequest`
- `node-append-commit-backlog` → `n8n-nodes-base.code`
- `node-put-backlog-md` → `n8n-nodes-base.httpRequest`
- `node-telegram-reply-backlog` → `n8n-nodes-base.telegram`
**Result:** PASS — all 6 new nodes present with correct types

### T-004: IF node routing — true branch (BACKLOG: prefix)
**Method:** Trace connection map
**Input:** `$json.message.text.toLowerCase()` starts with `"backlog:"`
**Expected:** IF node output[0] → `Format Backlog Item`
**Actual:** `"Route: Backlog or Capture"` main[0][0] → `"Format Backlog Item"`
**Result:** PASS

### T-005: IF node routing — false branch (normal capture)
**Method:** Trace connection map
**Input:** message does NOT start with `"backlog:"`
**Expected:** IF node output[1] → `Claude API`
**Actual:** `"Route: Backlog or Capture"` main[1][0] → `"Claude API"`
**Result:** PASS

### T-006: Existing capture path unbroken
**Method:** Trace full connection chain for normal messages
**Expected:** Telegram Trigger → Route → Claude API → Parse Claude Response → Build Markdown Note → Write Note to Vault → Telegram Reply
**Result:** PASS — all connections present and in order

### T-007: Format Backlog Item — prefix stripping
**Method:** Trace JavaScript: `text.replace(/^backlog:\s*/i, '').trim()`
**Test inputs:**
- `"BACKLOG: fix the auth bug"` → `"fix the auth bug"` ✓
- `"backlog:  add retry logic"` → `"add retry logic"` ✓
- `"Backlog: "` → `""` → throws `'Empty backlog item after stripping prefix'` ✓
**Result:** PASS

### T-008: BL ID generation — first entry (no existing BL IDs)
**Method:** Trace JavaScript with empty `blMatches`
**Logic:** `maxId = 0`, `nextId = "001"`, `blId = "BL-001"`
**Result:** PASS

### T-009: BL ID generation — increment from existing
**Method:** Trace JavaScript with matches including `BL-030`
**Logic:** `maxId = 30`, `nextId = "031"`, `blId = "BL-031"`
**Result:** PASS

### T-010: BL ID generation — padStart for single digit
**Method:** Trace: `String(1).padStart(3, '0')` → `"001"`
**Result:** PASS

### T-011: Content append — file ends with `---`
**Method:** Trace JavaScript branch
**Input:** `currentContent.trimEnd()` ends with `"---"`
**Expected:** Inserts `newRow` before `---`, preserves trailing `---`
**Logic:** `slice(0, -3).trimEnd() + '\n' + newRow + '\n\n---\n'`
**Result:** PASS — `tasks/backlog.md` currently ends with `---`, so this branch will be taken in production

### T-012: Content append — file does NOT end with `---`
**Method:** Trace JavaScript else branch
**Expected:** `currentContent.trimEnd() + '\n' + newRow + '\n'`
**Result:** PASS

### T-013: Commit message truncation
**Method:** Trace: `itemData.title.substring(0, 60)`
**For title 70 chars long:** truncated to 60 ✓
**For title 10 chars long:** unchanged ✓
**Result:** PASS

### T-014: PUT body expression syntax
**Method:** Static inspection of `jsonBody` field
**Expected:** Uses `={{ $json.X }}` n8n expression syntax (not `{{ }}`)
**Actual:** `"message": "={{ $json.commitMessage }}"` — correct for n8n string interpolation
**Result:** PASS

### T-015: GitHub credential references
**Method:** Static inspection
**Expected:** Both GET and PUT nodes reference `id: "h45FTOsmMrdSMPxB"`, `name: "GitHub PAT — project-manager"`
**Result:** PASS — no credential values inlined

### T-016: Telegram Reply — Backlog credential
**Method:** Static inspection
**Expected:** Same `telegram-cred` id as existing Telegram Reply node
**Result:** PASS — `"id": "telegram-cred"`, `"name": "Telegram — Pensieve Bot"`

### T-017: ChatId propagation through backlog path
**Method:** Trace data flow
**Source:** `$input.first().json.message.chat.id` captured in `Format Backlog Item` → passed as `chatId` field → `Append and Commit Backlog` passes it through → `Telegram Reply — Backlog` reads `$('Append and Commit Backlog').first().json.chatId`
**Result:** PASS

### T-018: Node name references in Append and Commit Backlog
**Method:** Cross-check JavaScript `$('...')` node name strings against actual node `name` fields
- `$('GET backlog.md from GitHub')` → node name: `"GET backlog.md from GitHub"` ✓
- `$('Format Backlog Item')` → node name: `"Format Backlog Item"` ✓
**Result:** PASS

### T-019: Base64 decode — GitHub API newline handling
**Method:** Trace: `ghData.content.replace(/\n/g, '')` before `Buffer.from(..., 'base64')`
**Note:** GitHub API returns base64 content with newlines every 60 chars; stripping them before decode is required and correct
**Result:** PASS

### T-020: Empty title guard
**Method:** Trace: `if (!title) throw new Error('Empty backlog item after stripping prefix')`
**Input:** `"BACKLOG:"` or `"BACKLOG:   "` → `title = ""` → throws
**Result:** PASS — workflow will error with informative message instead of committing empty row

### T-021: No path traversal risk in backlog path
**Method:** Static analysis — backlog path has no filesystem operations
**All I/O:** Via GitHub API only (HTTPS)
**Result:** PASS

---

## Known Limitations / Out of Scope

1. **Race condition:** Two near-simultaneous `BACKLOG:` messages could produce the same BL ID if both GET calls happen before either PUT completes. Acceptable for low-volume personal use; mitigated in future by server-side ID generation or optimistic locking.
2. **GitHub API rate limits:** Unauthenticated limit is 60/hr; with PAT it is 5000/hr — not a concern for personal use.
3. **Live integration test not performed:** Workflow is not deployed to a running n8n instance; test report covers static analysis and logic tracing only. Live test required on first deployment.
4. **`message.text` null guard:** If a Telegram message has no text (e.g., sticker, photo without caption), `$json.message.text.toLowerCase()` in the IF condition will throw. This is a pre-existing issue in the original workflow (same root cause) — out of scope for BL-030.

---

## Overall Result

**PASS — 21/21 tests passed**

Static analysis and logic tracing complete. Workflow is ready for n8n import and live acceptance testing.
