# Improvement Proposals — task-037

## Proposal 1
**Target file**: CLAUDE.md

**Change**: Add a new subsection under "Workflow Orchestration" (step 4, after "Verify before done") titled "Content Migration Checklist for Document Extraction" with the following guidance:

```
When moving a section from CLAUDE.md to a linked doc (e.g., extracting n8n patterns to docs/n8n-deployment.md):

1. **Pre-move mapping**: List every sentence in the source section in a checklist
2. **Destination verification**: For each sentence, confirm it appears in the destination doc (check word-for-word or paraphrased if semantically identical)
3. **Source retention decision**: Mark each sentence as either "moved" or "kept in source" — no orphans
4. **Pointer line**: Add a "See `docs/X.md` for: topic1, topic2, ..." line in CLAUDE.md pointing to the extracted content
5. **Final verification**: `wc -c CLAUDE.md` and `grep -c "<critical_phrase>"` for any rules that must remain present

Silent content drops increase code-quality-reviewer rework cycles (confidence 97 finding in task-037) and delay approval.
```

**Rationale**: The task-037 CQR review identified that 5 actionable instructions were removed and not added to the destination doc (Docker error messages, build time note, Pensieve branch instruction). A pre-move checklist makes this visible upfront and prevents rework. This pattern is specific enough to document in CLAUDE.md and will recur whenever a section is refactored into linked docs.

**Status**: APPROVED

---

## Proposal 2
**Target file**: CLAUDE.md (Task Queue & Resume section)

**Change**: Expand the "Artefact path assignment" paragraph to include:

```
When assigning `artefact_path` for a new task, run `ls artefacts/` first to check for path conflicts. 
If the target path already exists (from an informal task or previous sprint), use a descriptive suffix 
(e.g., `task-037-docs-reduction/`) rather than the bare ID. This prevents accidental clobbering of 
prior task outputs and enables retrospective analysis by SelfImprover for both the old and new work.
```

**Rationale**: CLAUDE.md already documents the fix in step 7 of the PM planning session ("always audit `ls artefacts/` before assigning the next task ID"), but the lessons.md entry shows this instruction is not being followed at planning time. Moving the guidance to the queue schema section (step 2 of PM sessions, earlier in the workflow) makes it more discoverable — the PM reads task tracking rules before launching the planning session.

**Status**: APPROVED
