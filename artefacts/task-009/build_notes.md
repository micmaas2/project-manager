# Build Notes — task-009
**Agent**: Builder (Sonnet 4.6) [Sonnet]
**Date**: 2026-04-07

## Summary of changes

Updated `/opt/claude/pensieve/workflows/gmail-capture.json` to align with the current Pensieve note template and fix n8n import issues.

## Changes made

### 1. Added workflow `id` field
- Added UUID `b71e2d83-4776-4d8a-a995-882355294c83`
- Required to avoid `SQLITE_CONSTRAINT` on import (no id = conflict with existing NULL-id row)

### 2. Removed top-level `tags` array
- Removed `["pensieve"]` — tag IDs are DB-internal; importing with them causes `SQLITE_CONSTRAINT`

### 3. Claude API node — system prompt upgraded
- max_tokens: 800 → 1000 (to accommodate larger response)
- Added `topic` field guidance (single lowercase slug for subfolder routing)
- Added `analysis` field guidance (2-3 sentences for articles, 1 sentence for thoughts/tasks)
- Expanded `key_points` from 2-4/15-words to 5-7/25-words (matches Telegram workflow)
- Expanded `tags` from 2-4 to 4-8 (with domain, entity, action tag guidance)
- User message now includes "Source channel: email" hint (per claude-processor.txt format)

### 4. Parse Claude Response node — fully upgraded
- Required fields expanded: added `topic` and `analysis`
- `TOPIC_PATTERN = /^[a-z0-9-]+$/` slug validation (same as Telegram workflow)
- `rawTopic` sanitised before pattern test; falls back to `'general'` on failure
- `analysis` capped at 1000 chars
- `key_points` trimmed to 7 (was 4)
- `tags` trimmed to 8 (was 6)

### 5. Build Markdown Note node — topic subfolder routing
- Path now: `VAULT/Category/Topic/filename.md` (e.g. `Research/Ai/2026-04-07-title.md`)
- `fs.mkdirSync(topicFolder, { recursive: true })` — creates subfolder if absent
- Path traversal check covers both category and topic levels
- `topic` field added to YAML frontmatter
- `## Analysis` section added to note body
- `from` field preserved in frontmatter

## Acceptance criteria pre-check

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Importable without SQLITE_CONSTRAINT | ✓ id added, tags removed |
| 2 | Triggers on Gmail label filter | ✓ unchanged (Label_Pensieve) |
| 3 | Email parsed with summary + tags + topic | ✓ Claude prompt updated |
| 4 | Output matches current template (topic, analysis, frontmatter) | ✓ all fields present |
| 5 | JSON validates via python3 -m json.tool | ✓ exit 0 confirmed |
| Deploy notes | deploy-notes.md present | see separate file |

## Security checks (per MVP template)
- Private IP blocking: N/A (no outbound HTTP from workflow nodes; Claude API call uses n8n credential, not user-controlled URL)
- Path traversal: `filepath.startsWith(VAULT + '/')` guard covers both folder levels
- Topic slug validated against `[a-z0-9-]+` before use in path
- No secrets in workflow JSON — Gmail OAuth and Anthropic API use n8n credential references
