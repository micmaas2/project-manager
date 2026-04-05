# Improvement Proposals — task-001

## Agent: SelfImprover [Sonnet]
## Date: 2026-04-05
## Source: review.md, test_report.md, build_notes.md, audit.jsonl

---

## Proposals

### 1. Add `prerequisites` field to MVP template

**Pattern observed**: `jq` was not installed at build time. The Builder script
correctly checked for it and failed gracefully, but there was no field in the
MVP template to declare runtime dependencies.

**Proposal**: Add a `prerequisites` field to `queue.schema.json` and
`CLAUDE.md`'s MVP template:
```json
"prerequisites": ["jq >= 1.6", "bash >= 4.0"]
```
This lets the Tester and Builder verify the environment before executing.

---

### 2. Add environment preflight to pipeline

**Pattern observed**: The pipeline had to install `jq` mid-run during the Reviewer
phase. A preflight step before spawning Builder would catch missing dependencies
early, saving pipeline time.

**Proposal**: Add a preflight check step to ProjectManager's pipeline:
```bash
# Preflight: verify required tools
command -v jq >/dev/null || { echo "Install jq first"; exit 1; }
```
Or add a `preflight.sh` script that validates all declared prerequisites.

---

### 3. Test fixture management

**Pattern observed**: The Tester created and deleted temp files inline. For complex
scripts, reusable fixtures in `artefacts/task-XXX/fixtures/` would make tests
reproducible and reviewable.

**Proposal**: Store test fixtures under `artefacts/<task_id>/fixtures/`:
- `fixtures/empty_queue.json`
- `fixtures/seeded_queue.json`
- etc.

These persist after the pipeline completes and can be re-run at any time.
