# Review — task-022: Wire claude-md-improver into /pm-close

**Date**: 2026-04-14
**Reviewer**: Sonnet [Reviewer]

## Implementation Review

### pm-close.md step 3b — counter logic

```
Read docs/session-counter.json (create if absent with {"closes": 0, "last_improver_run": null})
Increment closes by 1. Write back.
Print: Session closes: <closes> / Next run: session <N>
If closes % 5 == 0: invoke claude-md-improver via Skill tool on all managed CLAUDE.md files
Set last_improver_run to today. Commit.
```

**Correctness**: `closes % 5 == 0` correctly triggers on sessions 5, 10, 15... Counter never resets, no drift risk. First trigger is at session 5 (not session 0) because closes is incremented before the modulo check. This is correct — session 0 would trigger on the very first close, which is undesirable.

**Robustness**: "create if absent" clause handles fresh installs and the case where the file was deleted.

**Scope**: Runs claude-md-improver on all 6 managed project CLAUDE.md files in sequence. Guarded with "if file exists" to avoid errors on uncloned projects.

**Commit message format**: `[DOCS] pm-close: session <N>, ran claude-md-improver` matches the established pattern (observed in git log).

### Evidence of working execution

- Session 3: `a947e2c [DOCS] pm-close: session 3`
- Session 4: `5ac5248 [DOCS] pm-close: session 4`
- Session 5: `b98d5a1 [DOCS] pm-close: session 5, ran claude-md-improver`

Counter is incrementing correctly and the improver was triggered at session 5.

## Verdict: APPROVED

No changes required. Implementation is complete, correct, and in production use.
