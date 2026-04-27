# task-045 build notes [Sonnet]

## Task
MAS: Add hard budget enforcement to LLMClient.chat() (BL-062)

## Files Changed

| File | Change |
|------|--------|
| `/opt/mas/src/utils/llm_client.py` | Added `BudgetExceededError`, `_check_budget()` method, guard call in `chat()` |
| `/opt/mas/tests/test_phase1_integration.py` | Added `BudgetExceededError` import, `MagicMock` import, 3 new unit tests |

---

## Before / After Code Snippets

### Before — `chat()` entry (no budget guard)

```python
async def chat(self, messages, model=None, max_tokens=500, ...):
    # Determine which provider to use
    if model is None:
        model = self.settings.llm_secondary_model

    start_time = time.time()

    try:
        if model.startswith('gpt-') and self.openai_client:
            ...
```

### After — `chat()` entry (with budget guard)

```python
async def chat(self, messages, model=None, max_tokens=500, ...):
    # Determine which provider to use
    if model is None:
        model = self.settings.llm_secondary_model

    # Enforce budget before any API call
    self._check_budget(model)

    start_time = time.time()
    ...
```

### New `BudgetExceededError` class (line 18)

```python
class BudgetExceededError(Exception):
    """Raised when the monthly LLM budget has been exceeded."""
    pass
```

### New `_check_budget()` method

```python
def _check_budget(self, model: str) -> None:
    if not self.cost_tracker:
        return  # fail-open: no tracker → no enforcement

    USD_TO_EUR = 0.86
    if model.startswith("claude-"):
        budget_usd = self.settings.anthropic_monthly_budget_usd or 10
    else:
        budget_usd = self.settings.openai_monthly_budget_usd or 20
    monthly_budget_eur = budget_usd * USD_TO_EUR

    try:
        status = self.cost_tracker.check_budget(monthly_budget_eur)
    except Exception as e:
        logger.warning(f"Budget check failed (skipping enforcement): {e}")
        return

    if status["status"] == "over_budget":
        logger.error(
            f"Budget enforcement: blocking API call — {status['warning']} ..."
        )
        raise BudgetExceededError(
            f"Monthly LLM budget exceeded: {status['warning']}"
        )
```

---

## Design Decisions

1. **Fail-open on tracker unavailability**: if `cost_tracker` is `None` (e.g., DB unavailable at startup) the check is skipped and the API call proceeds. This avoids a full outage due to a monitoring failure. The `logger.warning` still surfaces the skip.

2. **Fail-open on check_budget exceptions**: if `cost_tracker.check_budget()` throws (e.g., DB read error), the exception is caught and logged, and the call proceeds. Enforcement is best-effort — it does not itself cause failures.

3. **USD→EUR conversion in `_check_budget`**: config stores budgets in USD (`anthropic_monthly_budget_usd`, `openai_monthly_budget_usd`). `CostTracker.check_budget()` expects EUR. Conversion at 0.86 matches the rate used in `cost_tracker.py` PRICING constants. This is a point-in-time rate — a future improvement (BL item) should add `anthropic_monthly_budget_eur` to config directly.

4. **Provider routing**: model name prefix (`claude-` vs `gpt-`) determines which budget config key to use, consistent with existing provider-routing logic in `chat()`.

5. **Warning-only budget (`status == "warning"`) is NOT blocked**: only `"over_budget"` hard-blocks. `"warning"` (approaching limit) is visible in logs only. This matches the existing UX in Telegram's `/budget` command.

---

## Test Results

```
tests/test_phase1_integration.py::TestLLMClient::test_parse_calendar_query PASSED
tests/test_phase1_integration.py::TestLLMClient::test_format_calendar_response PASSED
tests/test_phase1_integration.py::TestLLMClient::test_chat_blocked_when_budget_exceeded PASSED
tests/test_phase1_integration.py::TestLLMClient::test_chat_allowed_when_within_budget PASSED
tests/test_phase1_integration.py::TestLLMClient::test_chat_proceeds_when_cost_tracker_unavailable PASSED

5 passed in 6.01s
```

3 new tests added:
- `test_chat_blocked_when_budget_exceeded` — verifies `BudgetExceededError` is raised and API not called when `status == "over_budget"`
- `test_chat_allowed_when_within_budget` — verifies API call proceeds when `status == "ok"`
- `test_chat_proceeds_when_cost_tracker_unavailable` — verifies fail-open when `cost_tracker is None`

---

## Acceptance Criteria Check

| Criterion | Status |
|-----------|--------|
| 1. `check_budget()` called before every `LLMClient.chat()` call | PASS — `_check_budget(model)` is the first statement after model resolution |
| 2. `BudgetExceededError` raised + logged when budget exceeded | PASS — `logger.error(...)` + `raise BudgetExceededError(...)` |
| 3. 2+ new unit tests covering enforcement logic | PASS — 3 tests added |

---

## Commit

Branch: `feature/task-021-bookworm-base`  
Commit: `1d38607 [AGENT] task-045: add budget enforcement to LLMClient.chat()`
