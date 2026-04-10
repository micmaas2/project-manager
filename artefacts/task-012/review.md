# Review — Daily Facts Dedup Fix (Final Re-Review)
**Task**: task-012
**Reviewer**: Sonnet [Reviewer]
**Date**: 2026-04-10
**File reviewed**: `artefacts/task-012/daily_facts_agent_fixed.py`
**Supersedes**: prior review of same file

---

## Verdict: APPROVED

All criteria pass. The M-1 fix has been correctly applied.

---

## M-1 Fix Verification

**Location**: `_build_fact_generation_prompt`, lines 260–271

Both blocks are now independent `if` statements using `+=` to append to `exclusion_block`:

```python
exclusion_block = ""
if strong_exclusion:
    exclusion_block += (
        f"\nYOU MUST NOT feature {strong_exclusion}. "
        f"This person was already featured recently. Choose a completely different person.\n"
    )
if excluded_persons:
    names_str = ", ".join(excluded_persons)
    exclusion_block += (
        f"\nIMPORTANT: Do NOT feature any of these recently featured persons: {names_str}. "
        f"Pick a DIFFERENT person born on {month_day}.\n"
    )
```

- Line 261: `if strong_exclusion:` — independent block (not coupled to `excluded_persons`)
- Line 266: `if excluded_persons:` — independent block (not `elif`; always evaluated)
- Both use `+=` on `exclusion_block` — both sections appear in the retry prompt when applicable

The retry prompt now contains the strong per-person warning AND the full 7-day exclusion list when both conditions hold.

---

## Previously Passing Criteria (unchanged)

| # | Criterion | Status |
|---|-----------|--------|
| C-1 | Person name normalised to `.strip().lower()` on store, read, and compare | PASS |
| C-2 | `_get_recent_person_names` has try/except returning `[]` on failure | PASS |
| M-1 | Retry passes full exclusion list AND strong_exclusion (not either/or) | PASS |
| M-2 | FACT parsing uses regex with re.DOTALL (not line-by-line) | PASS |
| M-4 | `datetime.now(timezone.utc)` used in prompt date | PASS |

---

## Non-Blocking Observations (carried forward, no action required)

1. **Retry result not re-checked against exclusion list**: After the single retry, the result is logged but not re-validated. By design (single retry), acceptable.
2. **Partial-name mismatch**: If the LLM returns `"Einstein"` instead of `"Albert Einstein"`, the `.strip().lower()` comparison still misses it. Low risk given prompt examples enforce full names. Known limitation.
3. **Synchronous DB call in async method**: Consistent with `_select_best_category`; no regression.
