# Review: task-045 — MAS: Add hard budget enforcement to LLMClient.chat() [Sonnet]

**Reviewer**: Reviewer agent [Sonnet]  
**Date**: 2026-04-27  
**Commit reviewed**: `1d38607` on branch `feature/task-021-bookworm-base`

---

## Overall Verdict: APPROVED

The implementation is clean, well-scoped, and fits naturally into the existing codebase patterns. All 3 acceptance criteria are met. Two low-confidence observations are noted for awareness but do not require Builder action.

---

## Acceptance Criteria Check

| Criterion | Status | Notes |
|-----------|--------|-------|
| 1. `check_budget()` called before every `LLMClient.chat()` call | PASS | `_check_budget(model)` is the first statement after model resolution, before `start_time = time.time()` |
| 2. `BudgetExceededError` raised + logged when budget exceeded | PASS | `logger.error(...)` + `raise BudgetExceededError(...)` present |
| 3. 2+ new unit tests covering enforcement logic | PASS | 3 new tests added and confirmed passing |

---

## M-1 Mirror Check: Fail-open Behaviour

build_notes.md documents two fail-open paths:
1. `cost_tracker is None` → return immediately (no enforcement)
2. `cost_tracker.check_budget()` raises → catch, log warning, return

Both are implemented verbatim in `_check_budget()`. The behaviour is consistent between the documented design and the code. **M-1 check: PASS.**

---

## Findings

### Finding 1 — `BudgetExceededError` silently absorbed by `chat()` error handler
**Confidence: 85**

`_check_budget()` raises `BudgetExceededError` before the `try` block in `chat()`, so it propagates cleanly to the caller — this is correct. However, if a future refactor moves `_check_budget(model)` to inside the `try` block (e.g. to share the start_time or cost-logging logic), `BudgetExceededError` would be caught by the broad `except Exception as e:` handler at the bottom of `chat()`, swallowed, and returned as the string `"Error: Monthly LLM budget exceeded: ..."`. This would silently break enforcement.

**Recommendation**: Add a comment in `chat()` at the `_check_budget(model)` call line explicitly noting it must remain outside the `try` block:
```python
# NOTE: _check_budget must stay outside the try/except below — BudgetExceededError
# must propagate to callers, not be caught and converted to an error string.
self._check_budget(model)
```
This is a low-cost guard against a non-obvious maintenance trap.

---

### Finding 2 — No test for `check_budget()` exception path (fail-open on DB error)
**Confidence: 55**

build_notes.md documents a second fail-open path: if `cost_tracker.check_budget()` throws (e.g. DB read error), the exception is caught, logged, and the API call proceeds. The three new tests cover: (a) over-budget block, (b) within-budget allow, (c) `cost_tracker is None`. The exception-path scenario has no dedicated test.

This is low-confidence because the missing test is for a secondary defensive path, not the primary enforcement path. The current test coverage is adequate for the acceptance criteria. Flagged as a future hardening opportunity, not a blocker.

---

### Finding 3 — USD_TO_EUR hardcoded rate
**Confidence: 30**

`USD_TO_EUR = 0.86` is a local constant in `_check_budget()`, while `cost_tracker.py`'s `PRICING` dict comment also references `1 USD = 0.86 EUR`. The build_notes.md explicitly acknowledges this as a known trade-off and proposes a future BL item (`anthropic_monthly_budget_eur` config key). No action required — noted for completeness only.

---

## Architecture Compliance

- `BudgetExceededError` follows the existing exception placement pattern: module-level, before the class definition, same file as the raising code. Consistent with how other errors (e.g. `OpenAIError` imports) are organized.
- `_check_budget()` is a private method (underscore prefix) that delegates to `CostTracker.check_budget()` — correct separation of concerns; budget business logic stays in `cost_tracker.py`.
- Provider routing (`claude-` vs `gpt-` prefix) mirrors the identical pattern used in `chat()` itself for model dispatch. Consistent.
- Fail-open on tracker unavailability matches the existing pattern in `__init__`: `cost_tracker` is already initialized inside a `try/except`, so callers already expect it may be `None`.

---

## Code Quality

- Naming: `BudgetExceededError`, `_check_budget`, `budget_usd`, `monthly_budget_eur` — all clear and consistent with surrounding codebase style.
- Error logging: `logger.error(...)` for the hard-block case (correct level for enforcement action); `logger.warning(...)` for the skip-on-exception case (correct — enforcement is best-effort). Log levels are appropriate.
- The `logger.error` in `_check_budget` includes `model`, `current_spend_eur`, and `monthly_budget_eur` — sufficient operational context for incident response.
- `status["status"] == "over_budget"` is a string comparison on a known-schema dict returned by `CostTracker.check_budget()`. This is consistent with how the Telegram `/budget` command uses the same dict.

---

## Summary

The implementation is production-ready for the defined scope. Finding 1 (confidence 85) warrants a Builder fix: a one-line comment to protect against a maintenance regression. Finding 2 (confidence 55) is below the 80-confidence loop threshold — route to build_notes.md only. Finding 3 (confidence 30) is informational.

**Builder loops on**: Finding 1 only (confidence ≥ 80).

---

## Builder Fix Loop Result

**Finding F-1 (confidence 85) — RESOLVED**

Fix: expanded comment at `self._check_budget(model)` call site in `chat()` (lines 130–131) to explicitly state it must remain outside the `try` block. Commit 86e402f on Pi4.

Tests re-run post-fix: 16 passed, 2 pre-existing Google OAuth failures (unrelated to this task — confirmed identical to pre-change baseline).

**Final verdict: APPROVED**
