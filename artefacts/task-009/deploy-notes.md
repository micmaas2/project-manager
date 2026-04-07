# Deploy Notes — task-009
**Pensieve Gmail Capture — n8n on Pi4**

## Prerequisites (one-time setup)

1. **Gmail OAuth credential** — in n8n UI: Settings → Credentials → New → Gmail OAuth2
   - Name: `Gmail — michel.maas@gmail.com`
   - Credential id referenced in workflow: `gmail-cred`

2. **Anthropic credential** — already exists from Telegram workflow
   - Name: `Anthropic API Key` (httpHeaderAuth, id: `anthropic-cred`)

3. **Gmail label + filter**
   - In Gmail: create label `Pensieve`
   - Add filter: `to:pensieve@femic.nl` → apply label `Pensieve`
   - Alternatively: manually label emails you want captured

4. **Obsidian vault** — must be mounted at `/opt/obsidian-vault` on Pi4 (already in place)

---

## Deploy sequence

```bash
# Step 1: Prep workflow — inject id, confirm tags are absent
python3 -c "
import json
wf = json.load(open('workflows/gmail-capture.json'))
assert 'id' in wf, 'id missing'
assert 'tags' not in wf, 'tags must not be present'
print('id:', wf['id'])
print('Prep OK')
"

# Step 2: Copy to Pi4 and import
scp workflows/gmail-capture.json pi4:/tmp/gmail-capture.json
ssh pi4 "docker cp /tmp/gmail-capture.json n8n:/tmp/gmail-capture.json && \
         docker exec n8n n8n import:workflow --input=/tmp/gmail-capture.json && \
         docker exec n8n n8n publish:workflow --id=b71e2d83-4776-4d8a-a995-882355294c83"

# Step 3: Restart n8n
ssh pi4 "docker restart n8n && sleep 5 && docker ps | grep n8n"
```

---

## Post-import: re-select Gmail label

After importing, open the **Gmail Trigger** node in the n8n UI and re-select the `Pensieve` label from the dropdown. The placeholder label ID (`Label_Pensieve`) in the workflow JSON will not match your account's internal label ID. This is a one-time manual step.

---

## Dry-run test

Send a test email to `pensieve@femic.nl` (or manually label an existing email `Pensieve`). The workflow polls every minute. Check:
1. n8n execution log for the Gmail Trigger run
2. Vault path: `/opt/obsidian-vault/{Category}/{Topic}/YYYY-MM-DD-*.md` on Pi4
3. YAML frontmatter contains: `topic`, `source`, `channel: email`, `from`

---

## Rollback

Delete the workflow in n8n UI (Workflows → ... → Delete). No vault writes occur until the workflow is active and a labelled email arrives. Re-import the previous version if needed.

---

## Workflow UUID

`b71e2d83-4776-4d8a-a995-882355294c83`
