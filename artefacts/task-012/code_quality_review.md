# Code Quality Review — `daily_facts_agent_fixed.py`

Reviewer: code-quality-reviewer (Sonnet 4.6)
Date: 2026-04-10
Scope: dedup bug fix (Changes 1–4 as annotated in source)

---

## Critical Issues (Must Fix)

### C-1 — Case-insensitive comparison missing: dedup is trivially bypassed

**Location**: `_generate_fact_with_llm`, line 173; `_get_recent_person_names`, lines 334–336

**Risk**: The comparison `person_name in excluded_persons` is a case-sensitive Python `in` check on a plain list. The LLM may return `"albert einstein"`, `"Einstein"`, or `"ALBERT EINSTEIN"` while the stored value is `"Albert Einstein"`. All of these will pass the check undetected, making the dedup ineffective.

**Fix**:
```python
# In _get_recent_person_names, normalise on the way out
name = params.get("person_name", "").strip().lower()

# In _generate_fact_with_llm, normalise before comparison
person_name_norm = person_name.strip().lower()
excluded_norm = [n.lower() for n in excluded_persons]
if person_name_norm and excluded_norm and person_name_norm in excluded_norm:
    ...
```

Also normalise before storing to the DB so the data is clean from day one:
```python
"person_name": fact_data.get("person_name", "").strip(),
```

---

### C-2 — No exception handling in `_get_recent_person_names`: DB failure silently disables dedup

**Location**: `_get_recent_person_names`, lines 321–337

**Risk**: If the DB is unavailable, `get_db()` or the query raises an exception. Because there is no try/except, the exception propagates to `_generate_fact_with_llm` (line 154), which is itself called from `_get_daily_fact`. The entire fact-generation pipeline fails instead of degrading gracefully with an empty exclusion list.

**Fix**:
```python
def _get_recent_person_names(self, days: int = 7) -> list:
    try:
        with get_db() as db:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            facts = db.query(DailyFact).filter(DailyFact.created_at >= cutoff).all()
            names = []
            for f in facts:
                params = f.generation_params or {}
                name = params.get("person_name", "").strip()
                if name:
                    names.append(name)
            return names
    except Exception as exc:
        logger.warning(f"_get_recent_person_names failed, skipping exclusion list: {exc}")
        return []
```

---

## Major Issues (Should Fix)

### M-1 — `strong_exclusion` retry only names the single offending person, not the full list

**Location**: `_generate_fact_with_llm`, lines 177–192; `_build_fact_generation_prompt`, lines 258–261

**Risk**: The retry prompt includes `strong_exclusion` *instead of* the full `excluded_persons` list (see `_build_fact_generation_prompt`: when `strong_exclusion` is set, the `elif excluded_persons` branch is skipped). On retry the LLM sees only "do not use X" but has no reminder that the other 6 recently featured persons are also off limits. It can still repeat any of those.

**Fix**: Always include the full exclusion list; add the strong emphasis *in addition*:
```python
if strong_exclusion:
    names_str = ", ".join(excluded_persons) if excluded_persons else strong_exclusion
    exclusion_block = (
        f"\nYOU MUST NOT feature {strong_exclusion} — already featured recently. "
        f"Also avoid these recently featured persons: {names_str}. "
        f"Choose a completely different person.\n"
    )
elif excluded_persons:
    ...
```

---

### M-2 — `_parse_llm_response` only reads the first matching line; multi-line `FACT:` blocks are truncated

**Location**: `_parse_llm_response`, lines 305–306

**Risk**: The parser iterates line by line and overwrites `fact_text` only when it sees `FACT:` at the start of a line. If the LLM wraps the fact across multiple lines (which happens regularly for 100–150 word facts), only the first line is captured. This is a pre-existing bug but the new `PERSON:` field makes the symptom worse: a truncated `fact_text` with a valid `person_name` will be stored and deduped, hiding the truncation.

**Fix**:
```python
# After the loop, handle multi-line FACT block
import re
fact_match = re.search(r'^FACT:\s*(.+?)(?=\nCATEGORY:|\nSOURCE:|\nPERSON:|$)', response, re.DOTALL | re.MULTILINE)
if fact_match:
    fact_data["fact_text"] = fact_match.group(1).strip()
```

---

### M-3 — `_get_recent_person_names` returns names from *all categories*, not just the category being generated

**Location**: `_get_recent_person_names`, lines 329–337; call site, line 154

**Risk**: Both categories (`born_today_quote`, `born_today_discovery`) feature the same person pool (scientists/philosophers born on a given date). The current implementation correctly queries across categories, so this is not an active defect. However, if a third category not related to "born on this day" is ever added to `available_categories`, its person names will pollute the exclusion list for the born-today categories (and vice versa). The query has no category filter and no comment explaining this is intentional.

**Recommendation**: Add a docstring note that cross-category exclusion is intentional for the current category set. If/when a non-person category is added, add a category filter parameter.

---

### M-4 — `_generate_fact_with_llm` opens a second `get_db()` context after the LLM call, but `_get_recent_person_names` already opened a first one

**Location**: Lines 154, 197

**Risk**: Not a correctness bug with a properly pooled DB, but two separate context managers in one code path means two connections are checked out sequentially. If `get_db()` uses a scoped session, the second open may see slightly stale state (e.g. a fact committed by a concurrent request between the two opens). Minimal risk in a single-user bot, worth documenting.

---

## Minor Issues (Consider Fixing)

### m-1 — Retry result is not checked for success before saving to DB

**Location**: Lines 191–193

After the retry, `fact_data` is accepted unconditionally. If the retry LLM call raises an exception or returns an unparseable response, `fact_data["fact_text"]` will be empty and `fact_data.get("fact_text", response)` on line 199 falls back to the raw `retry_response` string — which is the full unparsed LLM output. This is the same fallback as the pre-existing code, but it now triggers silently on retry failure.

Add a guard:
```python
if not fact_data.get("fact_text"):
    logger.warning("Retry response also failed to parse; using raw response as fallback.")
```

---

### m-2 — `_rate_fact` uses `if rating:` which treats `rating=0` as falsy

**Location**: Lines 395, 405

This is a pre-existing issue but worth noting: `rating=0` (invalid per the 1–5 constraint) would not be caught by the `if rating:` guard and would skip the update silently. The validation check on line 385 (`if rating and not (1 <= rating <= 5)`) also skips when `rating=0`, so a zero rating slips through unchecked and un-stored.

Fix: use `if rating is not None:` for the guard checks.

---

### m-3 — `excluded_persons` logged at INFO with full name list — potential PII concern

**Location**: Line 155

```python
logger.info(f"Excluding {len(excluded_persons)} recently featured persons: {excluded_persons}")
```

Person names from historical figures are not PII in this context, but the log line includes the full list on every generation call. If the category scope ever expands to living persons this becomes a data-retention concern. Consider logging only the count at INFO and the full list at DEBUG.

---

### m-4 — `_build_fact_generation_prompt` uses `datetime.now()` without timezone (line 241)

```python
today = datetime.now()
```

All other `datetime.now()` calls in the file use `timezone.utc`. This one does not. On a server in a non-UTC timezone this will yield the wrong `month_day`, causing the "born on this day" prompt to target the wrong calendar date.

Fix:
```python
today = datetime.now(timezone.utc)
```

---

### m-5 — `_format_fact_message` does not escape Telegram MarkdownV2 special characters

**Location**: Lines 603–612

The `fact_text` (LLM-generated Dutch text) is interpolated directly into a string that uses Telegram `*bold*` markers. LLM output routinely contains parentheses, hyphens, and dots — all of which break Telegram's MarkdownV2 parser. This causes silent message-send failures. This is pre-existing but the new Dutch-language facts (which include birth/death year ranges like `(1879-1955)`) make it more likely to trigger.

---

## Positive Observations

- The no-migration approach (storing `person_name` in the existing `generation_params` JSON column) is clean and avoids schema risk for a low-cost fix.
- Exception handling in `_generate_fact_with_llm` and `process` is consistently delegated to `handle_error` — the new code follows the same pattern.
- The single-retry cap is the right call: one retry prevents infinite loops, and the failure mode (storing a repeated person) is benign rather than catastrophic.
- `strong_exclusion` as a separate parameter that changes prompt tone on retry is a good prompt-engineering pattern, even though the implementation has a gap (see M-1).
- `_get_recent_person_names` correctly handles `None` for `generation_params` via `f.generation_params or {}`, which is robust for pre-migration rows.

---

## Summary

The dedup design is sound and the no-migration approach is pragmatic. However, two issues (C-1, C-2) undermine its correctness in production: case-insensitive comparison is missing, meaning the LLM can trivially bypass dedup with minor name casing variation, and a DB error in `_get_recent_person_names` will crash the entire generation pipeline rather than degrading gracefully. These must be fixed before the feature can be relied upon.

The major issues (M-1, M-2) reduce dedup effectiveness further: the retry drops the full exclusion list, and multi-line facts are silently truncated. M-4 (naive UTC usage) will cause wrong-date prompts on non-UTC hosts.

**Overall risk rating: Medium.** No security vulnerabilities or data-loss paths are introduced. The dedup feature is partially effective as written but not reliable. Existing rating/preference/category code is unaffected by these changes — regression risk is low.

**Priority fix order**: C-2 (add try/except to `_get_recent_person_names`) → C-1 (case normalisation) → M-1 (full exclusion list on retry) → m-4 (UTC in `_build_fact_generation_prompt`).
