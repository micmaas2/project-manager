# Test Report — task-013

**Tester**: Sonnet 4.6
**Date**: 2026-04-11
**Artefact**: `.claude/commands/pm-plan.md`
**Method**: Manual dry-run walkthrough simulating a fresh session with no prior context

---

## Test Cases

### T-01 — Step 1: Next task ID computation
**Scenario**: Simulate Step 1 — read queue.json, find highest task ID, compute next.
**Procedure**: Parse all `"id"` fields matching `task-NNN`, extract max integer, add 1.
**Result**: max ID = 13 (`task-013`), next = 14 → `task-014` (zero-padded to 3 digits)
**Verdict**: PASS

---

### T-02 — Step 2: Backlog filtering
**Scenario**: Filter backlog.md to exclude done/blocked/archived items.
**Procedure**: Parse each `| BL-NNN |` row in `tasks/backlog.md`; filter where column 7 (Status) is NOT `done`, `blocked-manual`, `blocked-ssh`, or `archived`.
**Result**: 15 plannable items found; done/blocked items correctly excluded.
**Verdict**: PASS

---

### T-03 — Step 3: ID validation against backlog.md
**Scenario**: User lists `BL-009` (valid) and `BL-999` (invalid).
**Procedure**: Check each ID against column 1 of backlog.md rows.
**Result**: `BL-009` found — proceed. `BL-999` not found — skill would report missing ID and stop.
**Verdict**: PASS

---

### T-04 — Step 4: MVP template field mapping completeness
**Scenario**: Verify all 11 required MVP template fields have an explicit source mapping.
**Required fields** (from CLAUDE.md §MVP template): `doel`, `niet_in_scope`, `acceptatiecriteria`, `security_arch_impact`, `tests_required`, `definition_of_done`, `rollback_plan`, `incident_owner`, `privacy_dpia`, `cost_estimate`, `prerequisites`
**Result**: All 11 fields present in Step 4 mapping table; each has a named source.
**Verdict**: PASS

---

### T-05 — Step 5: Artefact collision check
**Scenario**: Verify `artefacts/task-014/` does not exist before assigning.
**Procedure**: `ls artefacts/` — check for `task-014` prefix.
**Result**: No collision. Skill would assign `artefacts/task-014/` without suffix.
**Verdict**: PASS

---

### T-06 — Step 6: Token cap warning logic
**Scenario**: Total sprint token estimate remains well below 400k cap.
**Procedure**: Sum token_estimate for all pending tasks + hypothetical sprint tasks.
**Result**: Total = 16,000 — no warning triggered. Logic correctly gates at 400,000.
**Verdict**: PASS

---

### T-07 — Step 7: queue.json JSON validity after append
**Scenario**: Simulate appending a new task object and re-parsing the result.
**Procedure**: `json.load` → `append` → `json.dumps` → `json.loads` roundtrip.
**Result**: No parse error; all fields serialise correctly including `null` values.
**Verdict**: PASS

---

### T-08 — Step 8: All 4 files committed on feature branch
**Scenario**: Verify skill commits queue.json, backlog.md, kanban.md, epics.md together.
**Procedure**: Read Step 8 instruction — "Commit all four file changes together (queue.json + backlog.md + kanban.md + epics.md)".
**Result**: Step 8 explicitly names all 4 files after Reviewer fix R-1 was applied.
**Verdict**: PASS

---

### T-09 — Step 7: target_project_path lookup via CLAUDE.md workspace table
**Scenario**: Simulate looking up `ccas` project path.
**Procedure**: Read CLAUDE.md §Workspace Context table; match `CCAS/` row to `/opt/claude/CCAS/`.
**Result**: Path resolved unambiguously from table. All 7 project entries present and distinct.
**Verdict**: PASS

---

### T-10 — Schema-valid queue.json (acceptance criterion)
**Scenario**: Resulting queue.json remains valid against queue.schema.json.
**Procedure**: Verify task object structure matches schema constraints (artefact_path non-empty for pending tasks; required fields present).
**Result**: Test task object in T-07 has non-empty artefact_path and all required fields. Schema constraint satisfied.
**Verdict**: PASS

---

## Summary

| Test | Verdict |
|---|---|
| T-01 Next task ID computation | PASS |
| T-02 Backlog filtering | PASS |
| T-03 ID validation | PASS |
| T-04 MVP field mapping completeness | PASS |
| T-05 Artefact collision check | PASS |
| T-06 Token cap warning logic | PASS |
| T-07 queue.json JSON validity | PASS |
| T-08 Four files committed on branch | PASS |
| T-09 Workspace table lookup | PASS |
| T-10 Schema-valid queue entry | PASS |

**Pass rate: 10/10 (100%)**

## PASS
