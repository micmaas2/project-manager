# Build Notes — task-013

**Task**: /pm-plan skill — PI/Refinement planning session workflow (S-003-2)
**Builder**: Sonnet 4.6
**Date**: 2026-04-10

---

## Design Decisions

### Step ordering: fetch → review → intent → template → confirm → commit
Mirroring `/pm-start` ordering: fetch first, then read operational files. State is read once and displayed before any user interaction — this avoids stale reads if the user takes time confirming.

### Placeholder resolution — explicit source mapping
Every angle-bracket placeholder in the skill references a named file and a named column or field. This meets the CLAUDE.md skill authoring rule: "Every angle-bracket placeholder must include an explicit resolution instruction naming the source file and lookup pattern."

Key mappings table in Step 4 maps every MVP template field to a concrete data source or derivation rule.

### Draft-and-confirm loop for MVP templates
Templates are drafted by the skill, then presented to the user for YES/correction cycles before being accepted. This prevents malformed templates entering queue.json and ensures the user retains ownership of scope decisions.

### Token warning at 80% cap
Step 6 warns if cumulative sprint token estimate exceeds 400k (80% of 500k cap), consistent with the preflight threshold used by `/pm-run`.

### artefact_path collision guard
Step 5 explicitly mandates `ls artefacts/` before assigning a path. Implements the same pattern used in CLAUDE.md §Artefact path assignment.

### target_project_path lookup
Step 7 maps the project short name to the Path column in CLAUDE.md's workspace table. This is the authoritative source (not backlog.md or epics.md), consistent with CLAUDE.md §Workspace Context.

### queue.json write strategy
Step 7 mandates a fresh read of queue.json immediately before writing. This avoids the stale-read failure mode documented in CLAUDE.md (§queue.json stale-read fix).

### Commit message format
Follows the `[AREA] Brief description` pattern from CLAUDE.md. Uses `[AGENT]` area (matching the convention used by pm-start and pm-run commits).

---

## Files Produced
- `.claude/commands/pm-plan.md` — the skill file
- `artefacts/task-013/build_notes.md` — this file
- `artefacts/task-013/review.md` — Reviewer output
- `artefacts/task-013/test_report.md` — Tester output
- `artefacts/task-013/improvement_proposals.md` — SelfImprover output
