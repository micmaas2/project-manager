# Code Quality Review — task-038
**File reviewed**: `.claude/commands/pm-run.md`
**Change scope**: Step 5 expanded into sub-steps 5a–5e with `/compact` calls at two boundaries

---

## CRITICAL Issues (Must Fix)

None.

---

## MAJOR Issues (Should Fix)

### Issue 1: Missing `/compact` before DocUpdater stage (after Tester closes)

**Location**: Between step 5c and step 5d in pm-run.md

**Problem**: A `/compact` boundary is placed after Builder (5a→5b) and after Reviewer resolution (5b→5c), but no `/compact` is placed between Tester and the DocUpdater+docs-readme-writer stage (5c→5d). The Tester stage accumulates test output, fixture output, and regression report content. By the time DocUpdater runs, the context contains Builder artefacts, all Reviewer findings, Builder loop output (if any), and Tester report — this is the highest-context point in the pipeline. If the rationale for compacting at 5a→5b and 5b→5c is to reduce carry-over before each new stage, then the 5c→5d boundary is at minimum as important as those two and arguably more so.

The BL-092 origin ticket (in `artefacts/task-034/skills-review.md`, line 167-168) only proposed boundaries at Builder→Reviewer and Reviewer→Tester. However, the task title ("Add /compact calls at pm-run stage boundaries") is broader, and omitting the Tester→DocUpdater boundary is inconsistent with the stated goal of "clear accumulated context before spawning the next stage."

**Fix**: Add a third `/compact` marker between 5c and 5d:

```
**5c. Tester**
Spawn Tester with task_id. Wait for test_report.md with overall PASS verdict.

**→ /compact** ← call here, after Tester PASS confirmed, before spawning DocUpdater

**5d. DocUpdater + docs-readme-writer** (parallel)
```

---

### Issue 2: No instruction on what to pass forward across a `/compact` boundary

**Location**: Steps 5a and 5b, immediately following each `/compact` marker

**Problem**: `/compact` replaces accumulated context with a summary, but the PM needs to know what minimal state must be re-established after compaction before spawning the next stage. Currently the file says nothing about this. After compacting between 5a and 5b, the PM still needs: the artefact file path(s) from Builder, the task_id, and queue.json status. After compacting between 5b and 5c, it needs: the final review verdict and whether any Builder re-loop occurred. Without explicit re-anchoring instructions, a PM that compacts and then spawns Reviewer may omit critical artefact path context.

**Fix**: Add a one-line re-anchor instruction after each `/compact` marker:

```
**→ /compact** ← call here, after Builder artefact confirmed, before spawning Reviewer
Re-anchor: re-read task_id, artefact_path, and confirm the Builder output file path before proceeding.
```

and:

```
**→ /compact** ← call here, after all Reviewer findings are resolved, before spawning Tester
Re-anchor: re-read task_id, artefact_path, and note whether a Builder re-loop occurred and passed.
```

---

## MINOR Issues (Consider Fixing)

### Issue 3: "Confirm both reviews complete" is ambiguous about the combined-findings step

**Location**: Step 5b, last sentence — "Confirm both reviews complete."

**Problem**: CLAUDE.md states "combine findings before looping Builder" — the combined findings step is a distinct action between the two parallel reviews finishing and any Builder loop decision. The current wording "Confirm both reviews complete" could be read as just a status check rather than an active synthesis step. A PM reading this for the first time may spawn Builder for a loop before merging the two finding sets.

**Fix**: Replace "Confirm both reviews complete." with "Wait for both reviews. Combine findings (confidence ≥80 from either review triggers a Builder loop); route findings <80 to build_notes.md only."

---

### Issue 4: Step 5d file ownership not re-stated (friction for new readers)

**Location**: Step 5d

**Problem**: The file omits the ownership split (DocUpdater → CHANGELOG.md, docs-readme-writer → README.md) that CLAUDE.md mandates under "Doc stage file ownership." The pm-run skill is the execution point where this ownership rule must be enforced. Without it here, a PM executing pm-run has to know to cross-reference CLAUDE.md during execution.

**Fix**: Append to step 5d: "DocUpdater owns CHANGELOG.md; docs-readme-writer owns README.md — assign ownership explicitly to prevent overwrite conflicts."

---

### Issue 5: Step 5e does not mention appending to tasks/lessons.md

**Location**: Step 5e

**Problem**: CLAUDE.md states "SelfImprover runs after every pipeline PASS and appends to `tasks/lessons.md`." Step 5e only says "Wait for improvement_proposals.md." The lessons append is equally required and is the primary observability output of the self-improvement loop.

**Fix**: Extend step 5e to: "Spawn SelfImprover with task_id. Wait for improvement_proposals.md and confirm an entry has been appended to tasks/lessons.md."

---

## Positive Observations

- The parallel stage groupings in 5b and 5d correctly reflect the CLAUDE.md pipeline diagram — "[Reviewer + code-quality-reviewer]" and "[DocUpdater + docs-readme-writer]" are each grouped under a single sub-step, which makes ownership clear and prevents the PM from treating them as sequential.
- The research/analysis task override (minimum 2 rounds, second round coverage rule) is correctly placed at the end of step 5, scoped as an exception clause rather than inline with the main flow.
- The `/compact` boundary labels use consistent formatting ("**→ /compact**") and include explanatory inline comments — clear enough to be action-triggering rather than advisory.
- The "Next step suggestion" block at the end covers all three terminal states (remaining tasks, pending proposals, queue clear) — no missing branch.
- The confidence threshold in step 5b ("≥80") correctly matches the CLAUDE.md definition verbatim, honoring the M-1 copy-paste rule.

---

## Summary

The `/compact` placement at the two implemented boundaries (Builder→Reviewer, Reviewer→Tester) is correct: both are genuine stage closes where accumulated artefact content has been confirmed and the next stage needs a clean slate. The logic is sound.

The main gap is the missing third `/compact` at Tester→DocUpdater (Issue 1), which is the highest-context point in the pipeline and was likely omitted because the originating BL ticket only named two boundaries. Given the stated goal of "clear accumulated context before spawning the next stage," omitting this boundary is inconsistent and should be added.

The secondary concern (Issue 2) is operationally important: compaction without re-anchoring instructions creates a silent failure mode where the PM loses artefact path context across the boundary and spawns the next stage without the necessary pointer.

Issues 3–5 are clarity improvements that reduce the chance of a PM misexecuting the combined-findings step or missing the lessons.md append.

**Overall risk rating: Low** — the changes are correct in intent and placement. The missing third `/compact` is an omission rather than a defect; the re-anchoring gap is a latent failure mode under specific execution paths. Neither is a data-loss or security risk in this context.
