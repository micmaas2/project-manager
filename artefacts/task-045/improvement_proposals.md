# Improvement Proposals — task-045

## Proposal 1
**Target file**: `CLAUDE.md`
**Change**: Add to MVP template section under `security_arch_impact`:
```
- If the task implements a budget enforcement or rate-limiting gate: add a "comment-at-call-site" checklist item ensuring all guard calls carry explicit notes explaining why the guard must remain at the current scope level (e.g. outside try/except). Maintenance traps where guards are inadvertently moved to a scope they do not protect against are non-obvious failures.
```
**Rationale**: Finding F-1 (confidence 85) in the Reviewer report identified a maintenance trap: if `_check_budget(model)` is later refactored into the `try` block, `BudgetExceededError` would be absorbed by the broad exception handler and enforcement would silently break. This was surfaced via an explicit comment at the call site. Future builders implementing enforcement gates (auth guards, budget checks, timeout guards) benefit from a mandatory checklist item to add explanatory comments protecting against scope-level refactors.
**Status**: APPROVED

## Proposal 2
**Target file**: `CLAUDE.md`
**Change**: Add to the CQR findings discussion (search for "Finding 4: Default budget fallback values are magic numbers"):
```
When config fields have defaults defined (e.g. Field(default=10)), do not use `or` short-circuit fallbacks at runtime — they silently break the zero-as-disable intent. Replace `budget_usd = config.value or 10` with `budget_usd = config.value if config.value is not None else 10`, or remove the fallback entirely if the config default is already correct.
```
**Rationale**: CQR Finding 4 (confidence 68) identified that `or 10` / `or 20` fallbacks fire on both `None` and `0`, silently defeating zero-budget intent (disable enforcement). The issue is subtle — the fallback appears defensive, but it actually breaks a valid disable signal. This pattern recurs in config-heavy tasks; adding it to the CQR findings section gives future Builders a pattern name and clear detection guidance.
**Status**: APPROVED

## Proposal 3
**Target file**: `tasks/lessons.md`
**Change**: Append to the lessons table:
```
| 2026-04-27 | code-quality-reviewer | **Fail-open with explicit logging is the correct safety pattern for budget enforcement — but silent swallowing of zero-budget intent is the inverse risk**: `or 10` fallbacks on `None` and `0` identically. When a user wants to disable enforcement (set budget to 0), the fallback silently re-enables it. Future CQR audits should flag this anti-pattern whenever config defaults and runtime fallbacks co-exist. | All future config-driven enforcement tasks |
```
**Rationale**: This lesson captures a subtle interaction between two good patterns (fail-open design + config defaults) that can combine to break user intent. It belongs in the lessons table as a multi-pattern interaction rule (not in CLAUDE.md, which is policy-scoped).
**Status**: APPROVED
