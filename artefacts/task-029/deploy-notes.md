# Deploy Notes — task-029: Pensieve Capture Sub-workflow

## Files Changed
- `pensieve/workflows/pensieve-capture-sub.json` — NEW sub-workflow
- `pensieve/workflows/telegram-capture.json` — UPDATED (calls sub-workflow)
- `pensieve/workflows/gmail-capture.json` — UPDATED (calls sub-workflow, not yet deployed to n8n)

## Sub-workflow Details
- **Name**: Pensieve — Capture Sub-workflow
- **ID**: `9867c392-2453-450f-9478-12f131d0ff33`
- **Nodes**: Execute Sub-workflow Trigger → Claude API → Parse Claude Response → Build Markdown Note → Write Note to Vault
- **Input interface**: `{ rawText, channel, subject?, from?, messageId? }`
  - `rawText`: text to send to Claude (parent formats this)
  - `channel`: `"telegram"` or `"email"` (controls frontmatter + raw section)
  - `subject`: email subject (email only)
  - `from`: sender address (email only)
  - `messageId`: required for email (validated in Build Note)
- **Credential**: `7AtbJ2N6BEvjqlwQ` (Anthropic API key)

## Deployment Steps Performed
1. `scp pensieve-capture-sub.json pi4:/tmp/` + `docker cp` + `n8n import:workflow` ✅
2. `scp telegram-capture-reply-fix.json pi4:/tmp/` + import ✅
3. `n8n publish:workflow --id=WgIO3y4KvGOxHWu0` + `docker restart n8n` ✅
4. Verified active=True via `n8n export:workflow --id=WgIO3y4KvGOxHWu0`

## Gmail Workflow — Not Yet Deployed
The updated `gmail-capture.json` references the sub-workflow but Gmail capture itself
is not yet deployed to n8n (pending BL-053). Deploy with standard n8n import when ready.

## Rollback
Re-import original Telegram workflow from git tag prior to this commit, then restart n8n.
Original workflow backup: see git history for `pensieve/workflows/telegram-capture.json`.

## Post-deploy Fix: Sub-workflow Activation
**Problem**: After `publish:workflow`, n8n reported "Workflow is not active and cannot be executed"
when Telegram messages triggered the sub-workflow call.

**Cause**: `publish:workflow` sets the published version but leaves `active: false`.
Execute Workflow node requires `active: true` on the sub-workflow.

**Fix**: Activate via REST API:
```bash
N8N_API_KEY=$(cat /opt/n8n/api-key)
curl -X POST http://localhost:88/api/v1/workflows/9867c392-2453-450f-9478-12f131d0ff33/activate \
  -H "X-N8N-API-KEY: $N8N_API_KEY"
```

**Required in deploy checklist**: After importing any sub-workflow, always activate it via the API.
