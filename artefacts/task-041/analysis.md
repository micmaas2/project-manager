# task-041: /pm-run Plan-Mode Gate Evaluation

**Agent**: Builder [Sonnet]
**Date**: 2026-04-19
**BL-097**

---

## 1. Current Behaviour

`/pm-run` (`.claude/commands/pm-run.md`) has **no plan-mode gate**. The skill executes immediately:

1. Find next task in queue.json (paused-first, then pending by priority)
2. Present task details
3. Validate MVP template fields
4. Preflight token check
5. Execute pipeline stages (Builder → Reviewer + CQR → Tester → DocUpdater + docs-readme-writer → SelfImprover)
6. Print next-step suggestion

There is no `EnterPlanMode` or `ExitPlanMode` call anywhere in pm-run.md.

**However**, CLAUDE.md contains two recovery rules specifically about plan-mode interactions during PM skill runs:

- `ExitPlanMode denial` (CLAUDE.md section 0 session-start checklist): "if the user denies ExitPlanMode, use AskUserQuestion to clarify intent before re-attempting"
- `ExitPlanMode mid-skill recovery` (same section): "if plan mode activates unexpectedly during a PM skill run (e.g. /pm-propose), write a minimal plan file summarising remaining steps, call ExitPlanMode, then continue the skill after approval."

These rules document reactive handling for situations where Claude's general "plan first" instinct (CLAUDE.md step 1: "ALWAYS enter plan mode before any non-trivial task (3+ steps)") fires mid-skill — interrupting automated pipeline execution.

---

## 2. Friction Observed

**Source 1 — CLAUDE.md recovery rules** (primary evidence)

Two dedicated recovery rules exist in CLAUDE.md for plan-mode interruptions during PM skill runs. Recovery rules in CLAUDE.md always represent a past failure mode that required a documented workaround. The `ExitPlanMode mid-skill recovery` rule names `/pm-propose` as a concrete example — strongly implies plan-mode interruptions have occurred in practice, disrupting skill execution flow.

**Source 2 — Nature of /pm-run**

/pm-run is pure execution: the task is already fully specified (id, mvp_template, acceptance criteria, rollback plan, token estimate — all present in queue.json from the prior /pm-plan session). There is no ambiguity to resolve before execution. The pipeline is deterministic.

Entering plan mode would only add a human-approval gate before a pipeline that is already gated by:
- MVP template validation (step 3)
- Preflight token check (step 4)
- Builder artefact confirmation (step 5a)

**Source 3 — No lessons.md entry for plan-mode friction in /pm-run**

`tasks/lessons.md` has no entry for plan-mode friction specifically from /pm-run. The interruptions captured in CLAUDE.md were discovered conceptually (e.g. from /pm-propose), not from a documented /pm-run post-mortem. The risk is prospective, not post-incident.

**Source 4 — CLAUDE.md "plan first" rule creates ambiguity**

CLAUDE.md step 1 says "ALWAYS enter plan mode before any non-trivial task (3+ steps or architectural decisions)". A PM skill run with 5+ pipeline stages qualifies textually. Without an explicit opt-out in the skill itself, each /pm-run invocation is susceptible to spontaneous plan-mode activation.

---

## 3. Alternative Approaches

### Option A: Keep as-is (no gate, no explicit opt-out)

Leave pm-run.md unchanged. Rely on the two CLAUDE.md recovery rules to handle any spontaneous plan-mode activation.

**Pros**: no change required; recovery rules already documented.
**Cons**: root cause (ambiguity from "plan first" mandate) unresolved. Recovery is reactive — fires after interruption, requiring extra user interaction. The `ExitPlanMode mid-skill recovery` rule adds cognitive load (write a plan file, call ExitPlanMode, re-anchor). Spontaneous plan-mode activations interrupt automated pipelines mid-execution.

---

### Option B: Add an explicit plan-mode opt-out instruction to pm-run.md (RECOMMENDED)

Add a single instruction near the top of pm-run.md: "Do not enter plan mode. This skill is execution-only — the task is already planned and queued. Proceed directly to Step 1."

**Pros**: eliminates the ambiguity that triggers spontaneous plan-mode activation. Zero user-visible change; skill runs exactly as today but with the "plan first" mandate explicitly overridden for this context. No ExitPlanMode call needed — instruction prevents activation rather than recovering from it. Removes the need for both CLAUDE.md recovery rules to fire for /pm-run cases.
**Cons**: none identified. This is a clarifying instruction, not a structural change.

---

### Option C: Add an explicit EnterPlanMode + ExitPlanMode gate

Add `EnterPlanMode` at the start of pm-run.md (present task details as a plan, await approval, then ExitPlanMode before executing).

**Pros**: gives user a visible approval moment before pipeline execution begins.
**Cons**: task is already planned and approved in /pm-plan. A second approval gate creates redundancy and user fatigue. Every /pm-run invocation requires explicit user approval even for trivial P3 tasks. Contradicts the "queued = approved" contract from /pm-plan. ExitPlanMode is another failure point requiring the mid-skill recovery rule.

---

### Option D: Conditional gate based on task complexity

Add plan-mode gate only for tasks above a token threshold or with a `requires_gate` flag.

**Pros**: differentiates trivial vs high-stakes tasks.
**Cons**: adds branching logic to a deterministic skill. The complexity signal is already present in the MVP template — surfaced during /pm-plan. Adds maintenance overhead. Over-engineering for a non-blocking problem.

---

## 4. Recommendation

**Apply Option B: add an explicit plan-mode opt-out preamble to pm-run.md.**

Rationale:
1. /pm-run executes work already planned and approved in /pm-plan. A plan-mode gate is a second approval for already-gated work.
2. The two CLAUDE.md recovery rules are workarounds for the underlying ambiguity. Option B resolves the root cause (prevent activation) rather than the symptom (recover after activation).
3. No structural change to the pipeline; no new user interaction required.
4. The change is one sentence — minimal impact surface.
5. Once pm-run.md carries an explicit "execution-only, no plan mode" directive, the CLAUDE.md recovery rules remain correct and useful for other skills but no longer apply to /pm-run.
