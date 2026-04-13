# Code Quality Review — task-019: Telegram sender chat_id auth guard

**Date**: 2026-04-13
**Agent**: code-quality-reviewer

## Change Summary

Two-hunk diff to `src/integration/telegram_listener.py`:
1. Import `settings` singleton
2. Auth guard at top of `_process_update()` message path

## Findings

### Security

| Area | Severity | Finding |
|---|---|---|
| Log injection via `chat_id` | LOW/NONE | `chat_id` is an `int`; `%s` formatting yields only decimal digits — no injection possible |
| `is not None` guard correctness | OK | Correctly distinguishes `None` (unconfigured) from valid int `0`; short-circuit is correct |
| Type safety of `message["chat"]["id"]` | OK | Telegram API guarantees signed 64-bit int; Python JSON parses as `int` for all chat types |
| Fail-open behavior (None → allow all) | MEDIUM | When `TELEGRAM_CHAT_ID` unset, guard silently disables — a misconfiguration risk |

**Fail-open detail**: When `settings.telegram_chat_id is None`, all senders are accepted without any log signal. A dropped env var (e.g. after Docker Compose change) would silently revert to open mode. The fix is a warning log when unconfigured:
```python
if settings.telegram_chat_id is None:
    logger.warning("TELEGRAM_CHAT_ID not configured — all senders accepted (open mode)")
elif chat_id != settings.telegram_chat_id:
    logger.warning("Unauthorized chat_id %s — dropping", chat_id)
    return
```
**Mitigation in current state**: `TELEGRAM_CHAT_ID` is confirmed set in `.env.production` — active risk is low. Improvement proposal filed.

### Quality

- Guard placement (after chat_id extraction, before username logging) is correct — unauthorized messages don't appear in INFO logs
- `logger.warning` severity is appropriate for dropped unauthorized messages
- No hardcoded values; all via `settings`

## Verdict

**APPROVED with 1 improvement proposal** (fail-open warning log — not blocking for this task).
