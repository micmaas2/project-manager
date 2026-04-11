# Improvement Proposals — task-016

## Proposal 1
**Target file**: CLAUDE.md
**Change**: Under the "Task unit tests" section (Pi4/testing section), add the following note:

> "When writing tests for scripts that use `_safe_path()` workspace-root validation, place fixture files under `artefacts/<task-id>/_fixtures/` — not in `tmp_path` (which resolves to `/tmp`, outside the workspace root and therefore rejected by the path guard)."

**Rationale**: All 9 tests for task-016 initially failed because pytest's `tmp_path` fixture resolves to a path under `/tmp`, which falls outside the workspace root checked by `_safe_path()`. This pattern will recur for any future script that validates paths against a workspace root. Documenting the correct fixture location prevents wasted debug cycles on future tasks.
**Status**: APPROVED
