# Improvement Proposals — task-056

## Proposal 1
**Target file**: CLAUDE.md
**Change**: Add to "Shell script pre-submission check" section (under the exec()-based validator patterns):

```
- If a validator uses exec() to run repo code: catch `SystemExit` explicitly before `except Exception` — `SystemExit` inherits from `BaseException` and bypasses `except Exception`, causing silent false-pass when tested code calls sys.exit() at module level.
```

**Rationale**: CQR found this as a Major issue in task-056. The fix is non-obvious because `SystemExit` is not a subclass of `Exception` — it is a subclass of `BaseException`. An `except Exception` block that appears to "catch everything" silently lets `SystemExit` propagate uncaught (or, in an `exec()` context, propagates up to the hook wrapper and exits the hook with the module's exit code). This produces a false-pass when the tested module calls `sys.exit(0)`. Adding it to CLAUDE.md prevents the same gap in all future `exec()`-based validators.

**Status**: APPROVED
