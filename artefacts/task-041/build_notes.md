# task-041 Build Notes

**Agent**: Builder [Sonnet]
**Date**: 2026-04-19

## Token Preflight

Estimated tokens: ~600 (research reads + write two small files + one-line edit). Well under 4,000 limit. Proceeding.

## Files Read

1. `.claude/commands/pm-run.md` — confirmed no plan-mode gate exists; pure execution flow in 5 steps
2. `tasks/lessons.md` — no plan-mode friction entries; no post-incident recovery records for /pm-run specifically
3. `CLAUDE.md` lines 247-250 — two recovery rules: `ExitPlanMode denial` and `ExitPlanMode mid-skill recovery`
4. `tasks/backlog.md` line 138 — BL-097 item text confirmed evaluation scope
5. `.claude/commands/pm-start.md`, `pm-plan.md` — read to understand skill context; neither has plan-mode gates either

## Key Finding

pm-run.md had no plan-mode gate — the BL-097 item asked whether one *should* be added, not whether to remove an existing one. The framing "evaluate whether it adds value or friction" is answered: adding a gate would add friction (second approval for already-approved work). The evidence from CLAUDE.md recovery rules shows the real problem is *spontaneous* plan-mode activation from the general "plan first" mandate — not a deliberate gate.

## Change Applied

Added a one-line execution-mode preamble to `.claude/commands/pm-run.md` immediately after the title:

```
**Execution mode**: do not enter plan mode. This skill executes a task that is already planned and queued. Proceed directly to the Steps below without calling EnterPlanMode.
```

This prevents spontaneous plan-mode activation without adding any user-visible gate. The two CLAUDE.md recovery rules remain valid for other skills (/pm-propose).

## Acceptance Criteria Verification

1. Analysis doc covers: current behaviour (section 1), friction observed (section 2, 4 sources), 2+ alternatives (section 3: Options A, B, C, D) — PASS
2. Clear recommendation: Option B "make explicit opt-out" with rationale — PASS
3. Change recommended and applied to pm-run.md — PASS
