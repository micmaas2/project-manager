# [Haiku] Task-044 Improvement Proposals

**SelfImprover**: SelfImprover agent [Haiku]
**Date**: 2026-04-21
**Task**: MAS: Upgrade LLM_PRIMARY_MODEL → claude-sonnet-4-6 (BL-061)

---

## Proposal 1

**Target file**: `CLAUDE.md` — MVP template section (`## MVP Phases & Scope Discipline`)

**Change**: Add a mandatory checklist item to the Definition of Done block in the MVP template for model-upgrade tasks. Insert the following line into the `Definition of Done` field guidance (after the existing checklist items):

```
- If this task changes or adds an LLM model string: verify the model string appears in
  cost_tracker (or equivalent pricing table); add the pricing entry before closing the task.
```

**Rationale**: task-044 required a second commit solely to add `claude-sonnet-4-6` pricing after CQR caught a ~20× underestimate in cost accounting. The fix was two lines and caught only because CQR ran. Without this checklist item, a future model upgrade task could ship with silent cost corruption. The pattern is predictable and recurring: every model name upgrade creates a pricing-table gap. Making it a DoD item costs nothing and prevents a category of silent data corruption.

**Status**: APPROVED

---

## Proposal 2

**Target file**: `CLAUDE.md` — `## Workflow Orchestration` step 4 (`Verify before done`)

**Change**: Add a sentence to the "Artefact minimum" sub-bullet that covers tasks on external repos (Pi4 MAS, pensieve):

```
For tasks targeting an external repo (Pi4 /opt/mas/, /opt/claude/pensieve/, etc.),
capture a baseline test run as the first artefact step and store it as
`artefacts/<task-id>/baseline_test_run.txt`. The Tester compares against the baseline,
not against 100%, to prove failures predate the task.
```

**Rationale**: task-044 had 14/148 pre-existing test failures (expired OAuth, API mismatches, missing DB tables). The Tester correctly identified them as pre-existing, but required git log analysis to prove it. A stored baseline snapshot makes this comparison immediate and auditable. The pattern will recur on every Pi4 MAS or pensieve task — those repos have long-running technical debt visible in their test suites.

**Status**: APPROVED

---

## Proposal 3

**Target file**: `CLAUDE.md` — `## Agent Roles & Spawn Order` table / pipeline description

**Change**: Add a note to the CQR parallel-review instruction clarifying that CQR must run even on config-only or migration tasks:

```
code-quality-reviewer must run in parallel with Reviewer for ALL task types,
including config-only changes, model upgrades, and documentation migrations.
Silent corruption risks (pricing tables, auth layers, logging paths) are
invisible to scope-limited Reviewer analysis and only surface under CQR
technical impact assessment.
```

**Rationale**: task-044 Reviewer rated the cost_tracker gap at confidence 45 (below the fix threshold) because it appeared to be a pre-existing gap — not a regression. CQR independently applied fallback-logic analysis and rated it confidence 92 (BLOCKING). Without CQR running in parallel, this fix would have been deferred to a future task, allowing ~20× cost underestimates to accumulate silently in the database. The lesson is not that Reviewer failed — it is that CQR provides a categorically different analysis lens (impact analysis vs. scope analysis) that cannot be substituted.

**Status**: APPROVED
