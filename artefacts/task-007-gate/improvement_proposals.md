# Improvement Proposals — task-007-gate

**SelfImprover** [Sonnet] | 2026-04-07

---

## Proposal 1

**Target file**: `CLAUDE.md` — Workflow Orchestration, step 6b (end-of-session proposal review)

**Change**: Add a reminder that SelfImprover must also verify cross-file format consistency when proposals touch both CLAUDE.md and agent YAMLs. Proposed addition at the end of step 6b:

```
Note: when a proposal introduces a format definition (e.g. improvement_proposals.md schema),
verify the format is identical in both CLAUDE.md and the relevant agent YAML before presenting
to the user.
```

**Rationale**: task-007-gate required an explicit cross-file consistency check during review (Reviewer checklist item). This guard currently lives only in Reviewer judgment; making it explicit in step 6b ensures SelfImprover enforces it before proposals reach the user.

**Status**: REJECTED: duplicate of task-006-lessons Proposal 1 (P4) — already applied via PM Planning Session preflight bullet

---

## Proposal 2 — REJECTED: duplicate of task-006 Proposal 1 (P4), which was approved and applied

**Target file**: `CLAUDE.md` — Task Queue & Resume section, "Artefact path assignment" paragraph

**Change**: Elevate the `ls artefacts/` check to a numbered preflight step in the PM planning session description (step in Workflow Orchestration). Currently it is buried in the Task Queue section. Proposed addition:

```
PM Planning preflight: before queuing any new task, run `ls artefacts/` and confirm the
target artefact_path does not already exist. If it does, assign a descriptive suffix.
```

**Rationale**: The artefact-path conflict lesson has now been recorded twice (task-006 and task-007). The fix is documented but placed in a section PMs consult after planning, not during. Surfacing it at the planning step prevents the same collision in future sessions. Recurrence of the same lesson in 2+ runs meets the "significant pattern" threshold.

**Status**: APPROVED
