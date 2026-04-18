# n8n Workflow Deployment (Pi4) — Reference

SSH alias: `pi4` (192.168.1.10). n8n runs as Docker container `n8n`.
GitHub PAT for project-manager API calls: `/opt/n8n/github-pat` on Pi4.

**Pi4 Python packages**: verify before deploying scripts: `ssh pi4 "python3 -c 'import X'"`.
Install missing packages with `pip3 install <pkg> --break-system-packages` (Debian-managed env).
`beautifulsoup4` installs as `beautifulsoup4` but imports as `bs4`.

**Pi4 root-owned git repo** (`/opt/mas`): all git operations require sudo and explicit identity flags — root has no git config on Pi4. Pattern:
```bash
sudo git -C /opt/mas -c user.name='Michel Maas' -c user.email='michel@femic.nl' <cmd>
```
Use `-c` flags rather than permanently configuring root's git config.

**Docker compose `--build` rebuilds depends_on chain**: `docker compose up -d --build <service>` also rebuilds services listed under `depends_on` for that service. On Pi4 ARM, a Python pip install layer can take 5+ minutes — plan for the full dependency chain build time, not just the target service.

**`--no-deps` for targeted rebuilds**: `docker compose up -d --no-deps --build mas-telegram`. Omit `--no-deps` only when dependency layers also changed.

**Pi4 docker-compose env file**: `docker-compose.dev.yml` hardcodes `env_file: .env`. `/opt/mas/.env` does not exist — symlink before any compose command: `sudo ln -sf .env.production .env`. Without this, compose exits with "env file /opt/mas/.env not found".

## Credential-placeholder patching

Required before import if workflow JSON contains `"id": "PLACEHOLDER_*"`:

```bash
# 1. Create credential in n8n
API_KEY=$(ssh pi4 "cat /opt/n8n/api-key")
CRED_ID=$(ssh pi4 "curl -s -X POST http://localhost:88/api/v1/credentials \
  -H 'X-N8N-API-KEY: $API_KEY' -H 'Content-Type: application/json' \
  -d '{\"name\": \"My Cred\", \"type\": \"httpHeaderAuth\", \"data\": {\"name\": \"X-Header\", \"value\": \"<value>\"}}'" \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
# 2. Patch JSON
python3 -c "import json; wf=json.loads(open('workflow.json').read().replace('PLACEHOLDER_CRED', '$CRED_ID')); wf.pop('tags',None); json.dump(wf,open('/tmp/wf.json','w'),indent=2)"
```

## Deploy sequence (all four steps required)

```bash
# 1. Prep: inject workflow id + strip tags + patch credential placeholders
python3 -c "import json; wf=json.load(open('workflow.json')); wf['id']='<UUID>'; wf.pop('tags',None); json.dump(wf,open('/tmp/wf.json','w'))"
# 2. Import (NOTE: import:workflow always DEACTIVATES the workflow)
scp /tmp/wf.json pi4:/tmp/wf.json && ssh pi4 "docker cp /tmp/wf.json n8n:/tmp/wf.json && docker exec n8n n8n import:workflow --input=/tmp/wf.json"
# 3. Activate via REST API (publish:workflow does NOT activate — use REST API)
API_KEY=$(ssh pi4 "cat /opt/n8n/api-key")
ssh pi4 "curl -s -X POST http://localhost:88/api/v1/workflows/<UUID>/activate -H 'X-N8N-API-KEY: $API_KEY'"
# 4. Restart (required for schedule triggers to register)
ssh pi4 "docker restart n8n && sleep 5 && docker ps | grep n8n"
```

## Import gotchas

- Workflow JSON must have `id` (UUID string) — omitting causes `SQLITE_CONSTRAINT` on import
- Strip `tags` array before import — tag IDs are DB-internal and cause `SQLITE_CONSTRAINT`
- `--userId=1` (numeric) fails; use UUID string or omit entirely
- No `sqlite3` in the n8n container; use `docker exec n8n n8n export:workflow --all` to inspect
- Find active workflow ID: export all + filter by `active: true` and most recent `updatedAt`
- **Credential IDs are internal UUIDs** — a placeholder/mismatched ID causes silent auth failure (no credential header sent). After import, verify each node's `id` matches a real credential (`n8n export:credentials --all`); patch with Python before import.
- `export:workflow --id=X --output=file.json` wraps output in a JSON array — use `data[0]` when loading a single exported workflow in Python.

## Quick health check

```bash
# Prefer piping stdout — n8n export:workflow --output writes inside the container
ssh pi4 "docker exec n8n n8n export:workflow --all 2>/dev/null" > /tmp/wf.json && python3 -c "import json; [print(w['id'],'|',w['name'],'|',w.get('active')) for w in json.load(open('/tmp/wf.json'))]"
ssh pi4 "docker exec n8n n8n export:credentials --all 2>/dev/null" > /tmp/creds.json && python3 -c "import json; [print(c['id'],'|',c['name'],'|',c['type']) for c in json.load(open('/tmp/creds.json'))]"
```

**Note**: `n8n export:workflow --all` only exports **non-archived** workflows. Workflows deleted via the REST API are soft-archived and excluded — a reduced count after deletion is expected behaviour, not data loss.

## Deleting a workflow (soft-archive via REST — excluded from future exports)

```bash
# Pre-condition: commit a full export as backup before deleting (git-tracked artefact)
API_KEY=$(ssh pi4 "cat /opt/n8n/api-key")
ssh pi4 "curl -s -X DELETE 'http://localhost:88/api/v1/workflows/<id>' -H 'X-N8N-API-KEY: $API_KEY'"
# Verify: re-export and confirm count = (before − deleted)
```

## Updating workflow JSON programmatically

When modifying n8n workflow nodes that contain multi-line `jsCode` or `jsonBody` strings, use Python to load/modify/dump — avoids JSON double-escaping errors that make the Edit tool unreliable:

```python
import json
with open('workflows/foo.json') as f: wf = json.load(f)
for n in wf['nodes']:
    if n['id'] == 'node-target': n['parameters']['jsCode'] = "new code..."
with open('workflows/foo.json', 'w') as f: json.dump(wf, f, indent=2, ensure_ascii=False)
```

## Testing n8n Code nodes

Extract `jsCode` from the workflow JSON at runtime (no copy-paste drift), execute in `node:vm` with a mocked context (mock `require('fs')`, `require('path')`, `$()` helper). See `artefacts/task-009/test_gmail_workflow.js` as the canonical example.
Run with: `/root/.nvm/versions/node/v24.12.0/bin/node artefacts/<task-id>/test_*.js`

**Code node module restrictions**: `require('path')` is disallowed in the n8n JS task runner (2.x) — use a manual `normalizePath()` function instead of `path.resolve()`. `require('fs')` is still allowed.

## n8n patterns and gotchas

**HTTP Request timeout**: always set `"options": {"timeout": 10000}` on HTTP Request nodes calling internal APIs (Pi4 localhost). Default is 300s — a hung n8n API stalls the workflow for 5 min.

**Timezone**: use `Intl.DateTimeFormat('nl-NL', {timeZone: 'Europe/Amsterdam', hour: 'numeric', hour12: false})` to get Amsterdam local hour. Handles DST automatically. Avoid raw UTC offsets.

**Finding Telegram chat_id from execution history**: `GET /api/v1/executions/{id}?includeData=true` → parse JSON for `"chat":{"id":...}` pattern.

**Workflow JSON patterns**:
- Use `specifyBody: "json"` + `jsonBody: "={{ $json.obj }}"` when passing an object — `specifyBody: "string"` silently mangles complex payloads
- Avoid `?.` optional chaining in IF node expressions — use `$json.commit ? 'ok' : ''` instead
- Never interpolate `$json.error` into Telegram `text` fields — GitHub API error strings contain backticks/underscores that trigger Telegram "can't parse entities"
- `continueOnFail: true` at node level handles 404s gracefully
- **REST API `limit=N` is a hard cap**: add a comment noting the assumption (e.g. `// assumes ≤100 active workflows`). Check `nextCursor` in the response and loop until null for large instances. Document the pagination requirement in `deploy-notes.md`.
- **Code node returning `[]` stops the downstream chain**: no IF/Switch node needed for guard conditions. Return `[]` to halt; return `[{json: {...}}]` to continue.
- **Workflow self-exclusion: UUID primary, name fallback** — name-only exclusion breaks on rename; UUID is immutable post-deploy. Combine both: `w.id !== '<UUID>' && w.name !== '<Name>'`.
