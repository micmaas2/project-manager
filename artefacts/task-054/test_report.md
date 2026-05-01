# Test Report — task-054: Pensieve pre-commit JSON validation hook

**Agent**: Tester (BugHunter) [Haiku]
**Date**: 2026-05-01
**Test run**: Post-fix (bug fix: `--` separator removed from `git show ":$file"`)
**Overall verdict**: PASS

---

## Bug Fix Applied

**What changed**: The `--` separator was removed from `git show ":$file"` (reverted to `git show ":$file"` without `--`).

**Why**: The `--` separator in `git show -- ":$file"` instructed git to treat `:$file` as a working-tree pathspec rather than an index object reference. This caused `git show` to output commit log/diff metadata instead of staged file contents, which then failed `json.load()` for every staged JSON file — a false positive that blocked all commits containing JSON. Without `--`, the `:$file` index-entry syntax is self-disambiguating and git correctly returns the staged file contents.

---

## bash -n Syntax Verification

```
$ bash -n /opt/claude/pensieve/hooks/pre-commit; echo "exit: $?"
exit: 0
```

Result: **PASS** — no shell syntax errors.

---

## Test Environment

Tests run in `/tmp/test-hook-054b` with:
- `git init` fresh repo (no initial commit needed — hook uses index-entry syntax `git show ":$file"` which works on a brand-new repo with no HEAD)
- Files staged with `git add` then validated by invoking hook via `bash /opt/claude/pensieve/hooks/pre-commit`
- git version 2.47.3

---

## Test Cases

### Test (c): no JSON staged → exits 0

**Command**:
```bash
bash /opt/claude/pensieve/hooks/pre-commit; echo "exit_c=$?"
```

**Actual output**:
```
exit_c=0
```

**Expected**: exit 0, no output
**Result**: **PASS**

---

### Test (a): staged valid JSON → exits 0

**Setup**: Valid JSON file `valid.json` containing `{"key":"value"}` staged via `git add`.

**Command**:
```bash
printf '{"key":"value"}\n' > valid.json && git add valid.json
bash /opt/claude/pensieve/hooks/pre-commit; echo "exit_a=$?"
```

**Actual output**:
```
exit_a=0
```

**Expected**: exit 0, no output
**Result**: **PASS**

---

### Test (b): staged malformed JSON → exits 1 with error message

**Setup**: Malformed JSON file `bad.json` containing `not json {{{` staged via `git add`.

**Command**:
```bash
printf 'not json {{{\n' > bad.json && git add bad.json
bash /opt/claude/pensieve/hooks/pre-commit 2>&1; echo "exit_b=$?"
```

**Actual output**:
```
ERROR: bad.json: Expecting value: line 1 column 1 (char 0)
exit_b=1
```

**Expected**: exit 1, error message on stderr including filename and parse error
**Result**: **PASS**

---

## Acceptance Criteria Verification

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Validates staged `.json` files via `python3 json.load()` | PASS |
| 2 | Exits non-zero and reports offending file + parse error on malformed JSON | PASS |
| 3 | Exits 0 silently when no `.json` staged | PASS |
| 4 | Exits 0 silently when valid JSON is staged | PASS |
| 5 | `bash -n hooks/pre-commit` exits 0 | PASS |

---

## Summary

| Test | Expected exit | Actual exit | Expected output | Actual output | Result |
|------|--------------|-------------|-----------------|---------------|--------|
| (c) no JSON staged | 0 | 0 | silent | silent | PASS |
| (a) staged valid JSON | 0 | 0 | silent | silent | PASS |
| (b) staged malformed JSON | 1 | 1 | error on stderr | `ERROR: bad.json: Expecting value: line 1 column 1 (char 0)` | PASS |
| bash -n syntax check | 0 | 0 | — | — | PASS |

**Tests passed**: 4/4
**Tests failed**: 0/4

All acceptance criteria met. Hook is ready for production use.
