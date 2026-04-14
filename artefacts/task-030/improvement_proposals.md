# Improvement Proposals — task-030

## Proposal 1

**Target file**: `CLAUDE.md` (n8n deployment section)
**Change**: Document the credential-placeholder patching pattern before importing n8n workflow JSON. Add checklist: (1) search for `"id": "PLACEHOLDER_*"` in workflow JSON, (2) create live credentials in n8n first (`POST /api/v1/credentials`), (3) patch JSON with real IDs via Python one-liner before import. Include the canonical one-liner: `python3 -c "import json; wf=json.loads(open('wf.json').read().replace('PLACEHOLDER_CRED', 'REAL_ID')); json.dump(wf, open('/tmp/deploy.json','w'), indent=2)"`
**Rationale**: task-030 required manual credential creation and JSON patching not covered by the existing deploy pattern. This pattern recurs for every n8n workflow calling external APIs.
**Status**: REQUIRES_HUMAN_APPROVAL

---

## Proposal 2

**Target file**: `CLAUDE.md` (n8n workflow task acceptance criteria)
**Change**: Add required acceptance criterion for n8n workflow tasks: "Unit tests extract `jsCode` from workflow JSON at runtime, execute in `node:vm` with mocked `Intl.DateTimeFormat` for timezone testing; ≥90% line coverage of all Code nodes." Point to `artefacts/task-030/test_healthcheck_workflow.js` as the canonical example.
**Rationale**: The node:vm test pattern (extract jsCode → run in mocked context) caught the length-mismatch gap and timezone boundary conditions before deploy. It runs locally without Pi4 and has zero deploy cost. Worth mandating for all n8n Code node tasks.
**Status**: REQUIRES_HUMAN_APPROVAL

---

## Proposal 3

**Target file**: `CLAUDE.md` (n8n deploy notes template)
**Change**: Add mandatory deploy checklist for n8n workflows: (1) `import:workflow` always deactivates — must follow with `POST /api/v1/workflows/{id}/activate`; (2) `docker restart n8n` to register schedule triggers; (3) verify `active: true` in subsequent GET; (4) wait for first scheduled execution before marking PASS.
**Rationale**: task-030 confirmed this sequence is the only reliable activation path. `publish:workflow` does not activate. Recording it as a mandatory checklist prevents future Builders shipping inactive scheduled workflows.
**Status**: REQUIRES_HUMAN_APPROVAL

---

## Proposal 4

**Target file**: `CLAUDE.md` (n8n security checklist in MVP template)
**Change**: Add to the security checklist under "If outbound HTTP": "If querying n8n REST API with `limit=N`, document the hard limit and whether `nextCursor`-based pagination is required. Add a comment in the Code node citing the limit assumption."
**Rationale**: task-030 health-check uses `limit=100` with only a comment. If ever >100 active workflows exist, idle ones beyond the limit are silently missed. Documenting the pagination requirement at spec time prevents silent data loss.
**Status**: REQUIRES_HUMAN_APPROVAL
