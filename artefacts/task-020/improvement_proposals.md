# Improvement Proposals — task-020 (BL-065 Daily Facts Birth-Date Fix)

## Proposal 1
**Target file**: `/opt/claude/project_manager/CLAUDE.md` — MVP security checklist (the `If outbound HTTP` / external data block under "MVP template")
**Change**: Add a dedicated bullet to the security checklist:
```
  - If an external API `description` or free-text field is embedded in an LLM prompt or written to a file: strip all ASCII control characters (0x00–0x1F, 0x7F) from every such field before use — not just `\n`. A post-hoc filter applied only at the final write step is insufficient if the value is used in the prompt first.
```
**Rationale**: The existing checklist covered control-char sanitization for YAML/Markdown file writes (added after task-009) but did not explicitly extend the requirement to fields embedded in LLM prompts. The code-quality-reviewer caught an unsanitized `description` field from the Wikipedia API being injected directly into a prompt. Adding this bullet closes the gap for all future tasks that fetch external API data and pass it to an LLM.
**Status**: APPROVED

## Proposal 2
**Target file**: `/opt/mas/src/daily_facts/daily_facts.py` (Pi4 — deployed source)
**Change**: When `_get_born_today_candidates()` returns an empty list (Wikipedia API unreachable, rate-limited, or returns no results), append a short fallback indicator to the Telegram message — e.g. `_(born-today data unavailable — Wikipedia API unreachable)_` — rather than silently falling back to LLM-hallucinated birthdays.
**Rationale**: The current fix is defensive only when candidates are present. If the Wikipedia API is down, the function returns `[]` and the LLM prompt receives no verified names, reverting to the hallucination-prone behaviour that caused BL-065. A visible fallback notice in the Telegram message alerts the operator that the data is unverified, without breaking the daily send. A periodic health-check in n8n could also monitor the Wikipedia endpoint and alert separately, but the in-message indicator is the minimum safe guard.
**Status**: APPROVED
