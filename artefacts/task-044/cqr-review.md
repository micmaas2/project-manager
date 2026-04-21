# [Sonnet] Code Quality Review — Task-044: LLM_PRIMARY_MODEL Upgrade

**Reviewer**: code-quality-reviewer (built-in)
**Date**: 2026-04-21
**Scope**: MAS repo on Pi4 (`/opt/mas/`) — config-only model name upgrade from `claude-3-5-sonnet-20240620` to `claude-sonnet-4-6`
**Commit reviewed**: `fedcac5` on `feature/task-021-bookworm-base`

---

## 🔴 Critical Issues (Must Fix)

None.

---

## 🟠 Major Issues (Should Fix)

### M-1: `cost_tracker.py` PRICING table missing `claude-sonnet-4-6` entry
**Location**: `/opt/mas/src/utils/cost_tracker.py` lines 21–35
**Confidence**: 92

The `PRICING` dict does not contain an entry for `claude-sonnet-4-6`. The lookup logic at line 84
iterates over dict keys and checks `key in model_key or model_key.startswith(key)`. With
`model = "claude-sonnet-4-6"`:

- `"claude-3-5-sonnet-20241022" in "claude-sonnet-4-6"` → False
- `"claude-sonnet-4-6".startswith("claude-3-5-sonnet-20241022")` → False
- Same for all other Anthropic entries

The fallback fires (`logger.warning ... using gpt-4o-mini pricing`) and applies GPT-4o-mini
pricing (EUR 0.129/M input, 0.516/M output) instead of the correct Sonnet pricing
(approximately EUR 2.58/M input, 12.90/M output). All cost tracking records from this model
from this point forward will be wrong by roughly 20×. This is a silent data corruption bug
in the cost accounting layer.

**Fix** — add an entry for the new model to the PRICING dict:
```python
# Anthropic (converted to EUR at 1 USD = 0.86 EUR)
# claude-sonnet-4-6 pricing: $3.00/M input, $15.00/M output (verify against Anthropic console)
"claude-sonnet-4-6": {"input": 2.58, "output": 12.90},
```
Confirm the exact USD price against https://www.anthropic.com/pricing before committing — the
values above are an estimate based on Sonnet 3.5 pricing. Update the comment timestamp on line 19
to reflect when the entry was added.

---

## 🟡 Minor Issues (Consider Fixing)

### m-1: SDK version constraint too loose for claude-sonnet-4-6 support
**Location**: `/opt/mas/requirements.txt` — `anthropic>=0.18.0`
**Confidence**: 72

The `anthropic>=0.18.0` lower bound predates `claude-sonnet-4-6` (Anthropic SDK support for the
4.x model series landed in the 0.30+ range). The installed version on Pi4 has not been checked
here. If the running container happens to satisfy a version older than ~0.30, the API call at
`llm_client.py:214` will receive an `invalid_model` error at runtime, not at import time.

**Fix**: tighten to `anthropic>=0.30.0` (or whatever minimum version first documents support for
claude-sonnet-4-6). Alternatively, add a startup assertion in `llm_client.py` that checks the
installed SDK version and logs a warning if it is below the tested floor.

This is minor rather than major because the Pi4's production container is likely already running
a recent SDK version; the risk is a future `pip install` on a clean environment.

### m-2: Archive doc references old model string — minor cosmetic gap
**Location**: `/opt/mas/docs/archive/phases/PHASE1_COMPLETE.md`
**Confidence**: 35

The build notes correctly identify this as intentional historical record. No action required.
Noted here for completeness only; confidence is low that this causes any problem.

### m-3: Cost tracking column name mismatch — pre-existing, not introduced by this task
**Location**: `/opt/mas/src/utils/cost_tracker.py:142`; `/opt/mas/src/data/models.py:178`
**Confidence**: 60

`log_usage` stores the value into a column named `estimated_cost_usd` while the unit is EUR
(the PRICING table comment on line 19 explicitly states EUR). This is a pre-existing naming
inconsistency not introduced by task-044; flagged here because the fallback pricing path
activated by M-1 makes the column semantics even more misleading. Fix in a separate cleanup task.

---

## 🟢 Positive Observations

- **No hardcoded old model string remains in src/ or tests/**: The grep across both directories
  returned zero hits, confirming the change is complete within the searched scope.
- **Syntax check performed by Builder**: `python3 -m py_compile src/config.py` was run and passed —
  correct tool for Python (not `bash -n`).
- **Live `.env.production` already correct**: Verified `LLM_PRIMARY_MODEL=claude-sonnet-4-6` in the
  live production env file; no production incident risk from a stale env value.
- **Model routing is model-string-agnostic**: `llm_client.py:97` routes on `model.startswith('claude-')`
  which matches `claude-sonnet-4-6` correctly — no routing changes needed.
- **Test files contain zero references to the old or new model string**: Tests do not mock or assert
  on the model ID, so no test breakage is expected from this change.
- **Branch strategy correct**: commit on the active feature branch (`feature/task-021-bookworm-base`)
  with merge to main deferred until Tester passes — appropriate gate.

---

## 📋 Summary

This is a low-risk, well-executed config-only change. The three affected files were correctly identified
and updated, the live production env is already correct, and no test files reference the old model ID.

The one substantive issue is M-1: the `cost_tracker.py` PRICING table silently falls back to GPT-4o-mini
pricing for `claude-sonnet-4-6`, producing cost records that are off by roughly 20× for all Anthropic
calls. This should be fixed before merging to main — it is a data quality issue, not a functionality
blocker, but silent incorrect cost accounting is difficult to correct retroactively once records are written.

**Blocking before main merge**: M-1 (add `claude-sonnet-4-6` entry to PRICING dict).
**Non-blocking**: m-1 (SDK version pin), m-3 (pre-existing column name issue).

**Overall risk rating**: Low — no security concerns; no functional regression; one silent data
corruption path in cost tracking that requires a two-line fix.
