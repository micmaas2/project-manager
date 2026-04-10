# Build Notes — Daily Facts Dedup Fix

**Task**: Fix person-level deduplication in `daily_facts_agent.py`
**Target file on Pi4**: `/opt/mas/src/agents/daily_facts_agent.py`
**Builder**: Sonnet [Builder]
**Date**: 2026-04-10

---

## Root Cause

The agent generated a "Born on This Day" fact each day, but the same person could appear on consecutive days because:

1. The LLM prompt had no awareness of who was featured previously.
2. Person names were never persisted after generation.
3. `_select_best_category` only deduplicates on *category*, not on the person within a category.

---

## Changes Made

### Change 1 — `_build_fact_generation_prompt` signature extended

**Location**: method `_build_fact_generation_prompt`

Added two new optional parameters:
- `excluded_persons: Optional[List[str]] = None` — list of recently featured names
- `strong_exclusion: Optional[str] = None` — single name used in a stronger retry warning

When `excluded_persons` is non-empty, the following block is appended to the prompt:

```
IMPORTANT: Do NOT feature any of these recently featured persons: {names}. Pick a DIFFERENT person born on {month_day}.
```

When `strong_exclusion` is set (retry path), the block is replaced with:

```
YOU MUST NOT feature {name}. This person was already featured recently. Choose a completely different person.
```

`PERSON: [Full name of the person featured]` was also added to the response format block and the example, so the LLM knows to return the featured person's name in a parseable field.

### Change 2 — `_parse_llm_response` extracts PERSON line

**Location**: method `_parse_llm_response`

Added `"person_name": ""` to the initial `fact_data` dict and a new branch:

```python
elif line.startswith("PERSON:"):
    fact_data["person_name"] = line.replace("PERSON:", "").strip()
```

Pattern is identical to the existing FACT/CATEGORY/SOURCE extraction. If the LLM omits the `PERSON:` line, `person_name` remains `""` (no crash, no side effect).

### Change 3 — `_generate_fact_with_llm` wires exclusion and stores person name

**Location**: method `_generate_fact_with_llm`

Three additions:

1. **Before LLM call**: call `_get_recent_person_names(days=7)` and pass the result to `_build_fact_generation_prompt` as `excluded_persons`.

2. **After parse**: if `person_name` is in `excluded_persons` (LLM ignored the instruction), retry once with `strong_exclusion=person_name`. The second response is parsed fresh; the resulting `person_name` is logged.

3. **On DB save**: `generation_params` dict now includes `"person_name"` as the first key:
   ```python
   generation_params={
       "person_name": fact_data.get("person_name", ""),
       "min_words": min_words,
       "max_words": max_words,
       "category": category,
   }
   ```
   This uses the existing JSON column — no schema change required.

### Change 4 — new helper `_get_recent_person_names`

**Location**: new synchronous method on the class

```python
def _get_recent_person_names(self, days: int = 7) -> list:
    with get_db() as db:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        facts = db.query(DailyFact).filter(DailyFact.created_at >= cutoff).all()
        names = []
        for f in facts:
            params = f.generation_params or {}
            name = params.get("person_name", "")
            if name:
                names.append(name)
        return names
```

Reads `generation_params` (existing JSON column). Facts from before this fix have no `person_name` key — `params.get("person_name", "")` returns `""` and the empty string is skipped, so the helper is backward-compatible with existing rows.

---

## Constraints Respected

- No DB migration — `generation_params` JSON column already exists on `DailyFact`.
- `DailyFact` model untouched.
- No other files modified.
- All existing behaviour (category rotation, ratings, length preferences, Telegram formatting) unchanged.

---

## Deployment

Not deployed. The fixed file is at:
`artefacts/task-012/daily_facts_agent_fixed.py`

To deploy, copy to Pi4:
```bash
scp artefacts/task-012/daily_facts_agent_fixed.py pi4:/opt/mas/src/agents/daily_facts_agent.py
```

Then restart the MAS service on Pi4 to pick up the change.

---

## Advisor Consults

None required. All four changes are straightforward and within established patterns.
