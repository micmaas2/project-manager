# Improvement Proposals — task-031

## Proposal 1

**Target file:** `CLAUDE.md`  
**Change:** Add a note to the "n8n Workflow Deployment" section that `n8n export:workflow --all` only exports **active** (non-archived) workflows. Soft-deleted (archived) workflows are excluded. If true deletion is needed, the REST `DELETE /api/v1/workflows/{id}` endpoint archives them and they disappear from the export — this is expected behaviour, not data loss.  
**Rationale:** The difference between "export shows N workflows" and "n8n has N+K archived workflows" was not documented. Future cleanup tasks should know that a reduced export count after deletion is expected and correct.  
**Status:** APPROVED

---

## Proposal 2

**Target file:** `CLAUDE.md` — `n8n Workflow Deployment` section  
**Change:** Add quick cleanup pattern:
```bash
# List all workflows (active only — archived excluded from export)
ssh pi4 "docker exec n8n n8n export:workflow --all --output=/home/node/wf.json && docker cp n8n:/home/node/wf.json /tmp/wf.json" && python3 -c "import json; [print(w['id'],'|',w['name'],'|',w.get('active')) for w in json.load(open('/tmp/wf.json'))]"

# Delete a workflow (soft-archive via REST)
API_KEY=$(ssh pi4 "cat /opt/n8n/api-key")
ssh pi4 "curl -s -X DELETE 'http://localhost:88/api/v1/workflows/<id>' -H 'X-N8N-API-KEY: $API_KEY'"
```
**Rationale:** The DELETE pattern was pieced together from first principles during task-031. It should be a first-class documented operation alongside the existing "deploy sequence" and "quick health check" patterns.  
**Status:** APPROVED
