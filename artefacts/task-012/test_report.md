# Test Report — task-012 daily_facts_agent_fixed.py

**Tester**: Tester agent [Sonnet]  
**Date**: 2026-04-10  
**Test file**: `artefacts/task-012/test_daily_facts_fix.py`  
**Run command**: `python3 -m pytest artefacts/task-012/test_daily_facts_fix.py -v`

---

## Per-Test Results

| ID | Test name | Class | Result | Notes |
|----|-----------|-------|--------|-------|
| T-01 | `test_person_name_lowercased_and_stripped` | `TestParseResponseCaseNormalisation` | **PASS** | `_parse_llm_response` + store normalisation correctly produces `"albert einstein"` |
| T-02 | `test_db_uppercase_name_returned_as_lowercase` | `TestGetRecentPersonNamesCaseNormalisation` | **PASS** | `_get_recent_person_names` lowercases `"ALBERT EINSTEIN"` from DB to `"albert einstein"` |
| T-03 | `test_retry_on_duplicate_person` | `TestDedupRetryFires` | **PASS** | LLM called exactly 2 times when returned person is on exclusion list |
| T-04 | `test_returns_empty_list_on_db_error` | `TestGetRecentPersonNamesDbFailure` | **PASS** | Returns `[]` without raising when DB throws on `__enter__` |
| T-05 | `test_multi_line_fact_captured_in_full` | `TestParseMultiLineFactText` | **FAIL** | BUG FOUND — see below |
| T-06 | `test_prompt_contains_utc_date` | `TestUtcDateInPrompt` | **PASS** | Prompt contains today's UTC date in `dd Month` format (computed dynamically) |
| T-07 | `test_retry_prompt_has_strong_warning_and_exclusion_list` | `TestRetryPromptContainsFullExclusionList` | **PASS** | Retry prompt contains `YOU MUST NOT` and `IMPORTANT: Do NOT feature` with full exclusion list |

**Summary: 6 PASS / 1 FAIL**

---

## Bug Report — T-05 FAIL

**Severity**: Medium  
**Location**: `_parse_llm_response` (line 315–320 in `daily_facts_agent_fixed.py`)  
**Description**: Multi-line FACT text is truncated to the first line only.

**Root cause**: The regex uses both `re.DOTALL` and `re.MULTILINE`. In `re.MULTILINE` mode, `$` matches the end of *each line*, not the end of the full string. The pattern `(.*?)(?=...|$)` therefore has its lazy quantifier stopped at the first `$` (end of line 1) before the lookahead for the next field label (`CATEGORY`, `PERSON`, etc.) can fire. Despite `re.DOTALL` allowing `.` to match newlines, the `$` anchor wins first.

**Reproduction**:
```python
import re
text = "FACT: Line one.\nLine two.\nLine three.\nCATEGORY: x\n..."
m = re.search(r'^FACT:\s*(.*?)(?=\n(?:FACT|CATEGORY|PERSON|SOURCE):|$)',
              text, re.DOTALL | re.IGNORECASE | re.MULTILINE)
print(m.group(1))  # => 'Line one.'  (truncated)
```

**Proposed fix**: Remove `re.MULTILINE` and replace `^` with `(?:^|\n)` (or use `\A`), and replace `$` in the trailing lookahead with `\Z`:
```python
m = re.search(
    rf'(?:^|\n){label}:\s*(.*?)(?=\n(?:FACT|CATEGORY|PERSON|SOURCE):|\Z)',
    text,
    re.DOTALL | re.IGNORECASE,
)
```

**Impact**: When LLM returns a FACT spanning multiple lines (which is the normal case for a 50–150 word fact), `fact_text` is silently truncated to just the first line. All downstream processing (word count, storage, Telegram message) receives an incomplete fact.

---

## Overall Verdict

**CONDITIONAL PASS** — 6 of 7 tests pass. The one failure (T-05) exposes a real defect in `_parse_llm_response` that causes silent data loss for multi-line facts. This bug must be fixed before the agent is considered production-ready. All four "Change" fixes (case normalisation, dedup retry, UTC date in prompt, retry exclusion list) are verified correct by T-01, T-02, T-03, T-04, T-06, T-07.

**Action required**: Fix the `_parse_llm_response` regex (see proposed fix above), then re-run tests to confirm 7/7 PASS.

## Re-run after regex fix

Regex fix applied: removed `re.MULTILINE`, replaced `^` with `(?:^|\n)` and `$` with `\Z`.

| ID | Result |
|----|--------|
| T-01 | PASS |
| T-02 | PASS |
| T-03 | PASS |
| T-04 | PASS |
| T-05 | PASS |
| T-06 | PASS |
| T-07 | PASS |

**Overall verdict: PASS — 7/7**
