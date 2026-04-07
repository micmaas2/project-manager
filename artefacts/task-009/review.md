# Review — task-009: Pensieve Gmail Capture Workflow
**Agent**: Reviewer (Sonnet 4.6) [Sonnet]
**Date**: 2026-04-07
**Artefact**: `/opt/claude/pensieve/workflows/gmail-capture.json`

---

## Verdict: APPROVED

All acceptance criteria pass. No blocking security issues found. Minor observations noted below (non-blocking).

---

## Acceptance Criteria

| # | Criterion | Result | Notes |
|---|-----------|--------|-------|
| 1 | Importable without SQLITE_CONSTRAINT: `id` UUID present, no top-level `tags` | PASS | `id: b71e2d83-4776-4d8a-a995-882355294c83` confirmed; `tags` key absent from top-level keys |
| 2 | Triggers on Gmail label filter (Label_Pensieve, unread) | PASS | `labelIds: ["Label_Pensieve"]`, `readStatus: "unread"` present in Gmail Trigger node |
| 3 | Claude API prompt includes topic, analysis, 5-7 key_points (max 25 words each), 4-8 tags — matches claude-processor.txt | PASS | System prompt specifies: `key_points (array of 5-7 … max 25 words each)`, `tags (array of 4-8 …)`, `analysis (string, 2-3 sentences … single brief sentence)`, `topic (single lowercase slug)` |
| 4 | Parse Claude Response: validates topic (TOPIC_PATTERN `/^[a-z0-9-]+$/`), analysis (string ≤1000 chars), key_points trimmed to 7, tags trimmed to 8 | PASS | `TOPIC_PATTERN = /^[a-z0-9-]+$/`; rawTopic sanitised with `/[^a-z0-9-]/g` before test; `analysis.substring(0, 1000)`; `.slice(0, 7)` for key_points; `.slice(0, 8)` for tags — all confirmed |
| 5 | Build Markdown Note: Category/Topic/filename.md path, `fs.mkdirSync` with `{recursive:true}`, YAML frontmatter includes topic+from+channel:email+analysis section | PASS | Path: `topicFolder = categoryFolder + '/' + topicFolderName`; `fs.mkdirSync(topicFolder, { recursive: true })`; frontmatter includes `topic`, `from`, `channel: email`; `## Analysis` section present in note body |
| 6 | JSON valid (`python3 -m json.tool`) | PASS | Exit 0 confirmed |
| 7 | `deploy-notes.md` present with import steps | PASS | File present at `artefacts/task-009/deploy-notes.md`; includes all 3 deploy steps (prep/assert, scp+import+publish, restart) plus post-import label re-selection and dry-run test instructions |

---

## Security Findings

| # | Check | Result | Notes |
|---|-------|--------|-------|
| S1 | No secrets in workflow JSON | PASS | Gmail uses `gmailOAuth2.id: "gmail-cred"`; Claude API uses `httpHeaderAuth.id: "anthropic-cred"` — both are n8n credential references, no raw keys |
| S2 | Path traversal: `filepath.startsWith(VAULT + '/')` present and covering both levels | PASS | Check runs after `topicFolder` and `filepath` are fully assembled, covering both category and topic subfolder levels |
| S3 | Topic slug sanitised before TOPIC_PATTERN test | PASS | `rawTopic = String(parsed.topic || '').toLowerCase().replace(/[^a-z0-9-]/g, '').substring(0, 30)` — sanitised before `TOPIC_PATTERN.test(rawTopic)` |
| S4 | Prompt/validator alignment: topic format consistent | PASS | Prompt says "single lowercase slug … e.g. ai, sap, homelab" (hyphens implicitly allowed via examples); TOPIC_PATTERN is `/^[a-z0-9-]+$/`; consistent. No conflict between prompt and validator. |

---

## Scope Violations

None.

- **Telegram workflow** (`telegram-capture.json`): not modified by this task — confirmed by file read. (Note: it has a pre-existing `tags` array and no `id` field; this is outside task-009 scope.)
- **Gmail trigger mechanism**: Label_Pensieve + unread filter unchanged.
- **Mark Email as Read node**: present (`node-mark-read`), wired after Write Note to Vault, uses `$('Build Markdown Note').first().json.messageId`.

---

## Minor Observations (non-blocking)

1. **Write Note uses `flag: 'wx'` (exclusive create)**: `fs.writeFileSync(filepath, noteContent, { encoding: 'utf-8', flag: 'wx' })` will throw `EEXIST` if two emails on the same day produce the same title slug. Edge case but possible for bulk-labelled emails. Consider `flag: 'w'` or appending a short unique suffix. Not blocking for MVP.

2. **`from` field not YAML-safe**: The sender address is newline-stripped but not otherwise escaped. If a sender display name contains `"` (e.g. `Jane "Admin" Doe`), it will produce invalid YAML in the frontmatter. Risk is low in practice. Consider `fromSender.replace(/"/g, "'")` as a simple guard.

3. **Telegram workflow has pre-existing import issues**: `tags: ["pensieve"]` is present at the top level and `id` is absent. Importing the Telegram workflow will hit `SQLITE_CONSTRAINT`. Recommend a follow-up task to apply the same id/tags fixes — not in scope here.

4. **`active: false`** in exported JSON: expected — workflow must be manually activated in n8n after import per deploy notes. Correct.

---

## Summary

The Gmail Capture workflow is well-constructed and closely mirrors the Telegram reference implementation. All 7 acceptance criteria pass, all 4 security checks pass, no scope violations. The two minor code observations (exclusive write flag, YAML injection in `from` field) are non-blocking for initial deployment. A follow-up hardening task is recommended before production load. The deploy-notes are complete and actionable.

**Verdict: APPROVED** — proceed to Tester.
