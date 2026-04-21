# Improvement Proposals — task-038: Add /compact calls at pm-run stage boundaries

## Proposal 1

**Target file**: `.claude/commands/pm-run.md`

**Change**: After each `**→ /compact**` marker, add a one-line re-anchoring instruction:

```
**→ /compact** ← call here, after Builder artefact confirmed, before spawning Reviewer
> After /compact, re-read `tasks/queue.json` to confirm task_id and artefact_path before proceeding.
```

Apply the same pattern after the second /compact marker (Reviewer→Tester boundary).

**Rationale**: After /compact, the agent's working context is reset. The current task_id, artefact_path, and pipeline position are not automatically restored. A brief re-anchor prevents the next stage from starting in an ambiguous state. This was flagged by CQR as a valid UX concern (below threshold for this task's scope) and is now captured as a lesson.

**Status**: APPROVED

---

## Proposal 2

**Target file**: `.claude/commands/pm-run.md`

**Change**: Add a third `/compact` marker at the Tester→DocUpdater boundary (after step 5c closes, before step 5d opens):

```
**→ /compact** ← call here, after Tester report confirmed, before spawning DocUpdater + docs-readme-writer
> After /compact, re-read `tasks/queue.json` to confirm task_id and artefact_path before proceeding.
```

**Rationale**: The Tester stage produces a test report artefact that adds to accumulated context. Clearing context before the documentation stage prevents context-window pressure for longer pipelines. This boundary was identified as valid during review but excluded from task-038 scope (acceptatiecriteria named only 2 boundaries). Scheduling as a follow-up proposal rather than scope-creep into task-038.

**Status**: APPROVED
