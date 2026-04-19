# task-041: Improvement Proposals

**Agent**: SelfImprover [Haiku]
**Date**: 2026-04-19

---

## Proposal 1

**Target file**: `CLAUDE.md`
**Change**: Add a note to the "Plan first (mandatory)" step (step 1) clarifying that execution-only PM skills (pm-run, pm-close) carry explicit plan-mode opt-out directives and are exempt from the general mandate:

```
1. **Plan first (mandatory)**: ALWAYS enter plan mode before any non-trivial task (3+ steps or architectural decisions). **Exception**: PM skills that carry an explicit "Execution mode: do not enter plan mode" preamble are exempt — they execute already-planned and queued work.
```

**Rationale**: The current "ALWAYS enter plan mode" mandate textually covers execution-only skills with 5+ deterministic pipeline stages (e.g. /pm-run). Without a documented exception, the mandate creates ambiguity that causes spontaneous plan-mode activation during automated pipeline runs. The opt-out directive in pm-run.md resolves the activation, but the CLAUDE.md mandate itself should acknowledge the exception pattern so future skill authors know when to include it.
**Status**: REQUIRES_HUMAN_APPROVAL

---

## Proposal 2

**Target file**: `.claude/commands/pm-run.md` (verify opt-out is already applied) + any new execution-only skill files
**Change**: Add to PM skill authoring guidelines in CLAUDE.md (Skill authoring rules section) a rule stating: "Execution-only skills (no scope ambiguity, task already fully specified) must include an explicit plan-mode opt-out preamble: `**Execution mode**: do not enter plan mode. This skill executes already-planned work. Proceed directly to the Steps below without calling EnterPlanMode.`"

**Rationale**: task-041 identified that pm-run.md lacked the opt-out and was susceptible to spontaneous plan-mode interruption. Codifying this as a skill authoring rule ensures future execution-only skills (e.g. pm-close, any future pm-deploy) include the opt-out by default rather than requiring a dedicated evaluation task for each one.
**Status**: REQUIRES_HUMAN_APPROVAL
