# Deploy Notes — task-030: n8n Health Check Workflow

## Prerequisites

- SSH access to `pi4` (192.168.1.10)
- n8n running as Docker container `n8n`
- n8n API key: `/opt/n8n/api-key` on Pi4
- Telegram credential `NB55cLp798oiazqt` ("Telegram account") already in n8n

## Deploy Steps

### Step 1: Create the n8n API Key credential

This workflow calls the n8n internal REST API. The credential `PLACEHOLDER_N8N_API_CRED`
must be replaced with an actual `httpHeaderAuth` credential in n8n.

```bash
API_KEY=$(ssh pi4 "cat /opt/n8n/api-key")
CRED_ID=$(ssh pi4 "curl -s -X POST http://localhost:88/api/v1/credentials \
  -H 'X-N8N-API-KEY: $API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{\"name\": \"n8n API Key\", \"type\": \"httpHeaderAuth\", \"data\": {\"name\": \"X-N8N-API-KEY\", \"value\": \"'$API_KEY'\"}}'" \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
echo "Created credential ID: $CRED_ID"
```

### Step 2: Patch workflow JSON with real credential ID

```bash
API_KEY=$(ssh pi4 "cat /opt/n8n/api-key")
python3 - <<'EOF'
import json, subprocess, sys

# Get credential ID
result = subprocess.run(
    ['ssh', 'pi4', f"""curl -s 'http://localhost:88/api/v1/credentials' -H 'X-N8N-API-KEY: $(cat /opt/n8n/api-key)'"""],
    capture_output=True, text=True
)
# Alternative: get ID from what was created in step 1 above
cred_id = input("Enter credential ID from Step 1: ").strip()

with open('pensieve/workflows/n8n-healthcheck.json') as f:
    wf = json.load(f)

wf_str = json.dumps(wf)
wf_str = wf_str.replace('PLACEHOLDER_N8N_API_CRED', cred_id)
wf_patched = json.loads(wf_str)
wf_patched.pop('tags', None)

with open('/tmp/n8n-healthcheck-deploy.json', 'w') as f:
    json.dump(wf_patched, f, indent=2)

print(f"Patched workflow written to /tmp/n8n-healthcheck-deploy.json")
EOF
```

Or one-liner:
```bash
CRED_ID="<paste from step 1>"
python3 -c "
import json
with open('pensieve/workflows/n8n-healthcheck.json') as f: wf = json.load(f)
wf_str = json.dumps(wf).replace('PLACEHOLDER_N8N_API_CRED', '$CRED_ID')
wf = json.loads(wf_str)
wf.pop('tags', None)
with open('/tmp/n8n-healthcheck-deploy.json', 'w') as f: json.dump(wf, f, indent=2)
print('Done')
"
```

### Step 3: Import + activate workflow

```bash
# Copy to Pi4 and import
scp /tmp/n8n-healthcheck-deploy.json pi4:/tmp/n8n-healthcheck.json
ssh pi4 "docker cp /tmp/n8n-healthcheck.json n8n:/tmp/n8n-healthcheck.json \
  && docker exec n8n n8n import:workflow --input=/tmp/n8n-healthcheck.json"

# Activate via REST API (import deactivates by default)
API_KEY=$(ssh pi4 "cat /opt/n8n/api-key")
ssh pi4 "curl -s -X POST http://localhost:88/api/v1/workflows/b5717a69-a46c-484e-ac44-aa65e143acfd/activate \
  -H 'X-N8N-API-KEY: $API_KEY'"

# Restart n8n to ensure schedule fires
ssh pi4 "docker restart n8n && sleep 5 && docker ps | grep n8n"
```

### Step 4: Verify

```bash
# Check workflow is active
API_KEY=$(ssh pi4 "cat /opt/n8n/api-key")
ssh pi4 "curl -s 'http://localhost:88/api/v1/workflows/b5717a69-a46c-484e-ac44-aa65e143acfd' \
  -H 'X-N8N-API-KEY: $API_KEY'" | python3 -c "import json,sys; w=json.load(sys.stdin); print('active:', w.get('active'))"

# Wait for first scheduled execution (next 15-min mark), then check:
API_KEY=$(ssh pi4 "cat /opt/n8n/api-key")
ssh pi4 "curl -s 'http://localhost:88/api/v1/executions?workflowId=b5717a69-a46c-484e-ac44-aa65e143acfd&limit=1' \
  -H 'X-N8N-API-KEY: $API_KEY'" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('data',[{}])[0].get('status'))"
```

## Known Limitations

- Queries max 100 active workflows (`limit=100`). If the n8n instance ever exceeds 100 active
  workflows, paginate by checking for `nextCursor` in the response.
- Telegram API timeout is handled at the n8n platform level (not configurable per-node in 
  Telegram nodes). The default n8n request timeout applies.

## Rollback

Deactivate or delete the workflow in n8n:
```bash
API_KEY=$(ssh pi4 "cat /opt/n8n/api-key")
ssh pi4 "curl -s -X POST http://localhost:88/api/v1/workflows/b5717a69-a46c-484e-ac44-aa65e143acfd/deactivate \
  -H 'X-N8N-API-KEY: $API_KEY'"
```

## Workflow ID
`b5717a69-a46c-484e-ac44-aa65e143acfd`
