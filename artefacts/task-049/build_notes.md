# Build Notes — task-049

**Task**: Hooks-over-prompts audit — implement top 3 rules as hooks (BL-088)  
**Builder**: Sonnet [Sonnet]  
**Date**: 2026-04-28

---

## Architecture Decisions

### Option A vs Option B for hook placement

CLAUDE.md offers two implementation paths:
- **Option A**: Add new rules to `hooks/security_reminder_hook.py`
- **Option B**: New script registered in `.claude/settings.json`

**Decision**: Hybrid approach.
- Hook 1 (re.DOTALL + `$`) was added to `security_reminder_hook.py` — it is a code quality/correctness pattern that fits the existing REGEX_SECURITY_PATTERNS structure. Adding a new pattern entry required minimal change: one dict in the list + a 3-line change to `check_patterns()` to support combined `path_check` + `content_check` in regex patterns.
- Hooks 2 and 3 were implemented in a new `hooks/workflow_guard_hook.py` — they operate on different tools (Bash for Hook 2, queue.json for Hook 3) and are workflow-governance patterns rather than security patterns. Separating them makes the hook file intent clear and avoids bloating the security hook with non-security concerns.

### Why PreToolUse (blocking) for all 3

All three rules are binary: the pattern is either present or absent. There is no "legitimate use" path for any of them:
- Hook 1: `re.DOTALL` + `$` is always a bug. Use `\Z` instead.
- Hook 2: Hook-bypass flag has no legitimate use in this codebase.
- Hook 3: A task marked done without an artefact_path is always an incomplete state.

PostToolUse would warn after the fact; PreToolUse blocks before the bad state is written. All three qualify for blocking.

### Hook 1 pattern design

The `re.DOTALL` + `$` pattern needed both `path_check` (`.py` files only) and `content_check` (both `re.DOTALL` and `$` present together). The existing REGEX_SECURITY_PATTERNS loop only called `rp["pattern"].search(content)` — it had no provision for combined checks. A 3-line extension was added to the loop:

```
# In check_patterns():
if "path_check" in rp and "content_check" in rp:
    if rp["path_check"](normalized_path) and rp["content_check"](content):
        return rp["ruleName"], rp["reminder"]
elif rp["pattern"].search(content):
    return rp["ruleName"], rp["reminder"]
```

The `pattern` field in the new entry serves as a quick-scan guard. The `content_check` lambda does the full combined check.

### Hook 3 design nuance

The queue.json check only fires when BOTH conditions are true:
1. `"status": "done"` appears in the edited content
2. No non-empty `"artefact_path"` value is in the same content block

This means: updating multiple fields in one Edit call (setting status + artefact_path together) is allowed. Updating only status to done without the path is blocked. This matches the intended workflow where the Builder sets both fields atomically.

### Settings.json registration

The workflow_guard_hook is registered twice:
- Under `Edit|Write|MultiEdit` matcher (for Hook 3 — queue.json check)
- Under `Bash` matcher (for Hook 2 — git bypass check)

The security_reminder_hook is already registered under `Edit|Write|MultiEdit`. Both hooks run on every file write; workflow_guard_hook exits early (0) if the file is not queue.json.

---

## Hook Pattern Interference Encountered

When updating CLAUDE.md to reference the new hooks, the initial edit attempt was blocked because the `old_string` included a blocked pattern (from the existing PreToolUse hooks documentation). Per CLAUDE.md "Hook pattern interference" rule, the edit was split to use a narrow `old_string` that avoided the trigger token. Second attempt succeeded.

When writing the test file `/tmp/test_hooks_task049.py`, the initial Write attempt was blocked by Hook 1 itself (the test file contained the `re.DOTALL + $` test payload strings inline). The test file was rewritten using string concatenation to assemble the blocked pattern at runtime, avoiding the hook trigger at write time. This is a concrete demonstration that Hook 1 is working correctly at edit time.

---

## Test Results

All 13 integration tests passed (see test_report.md).

```
Hook 1: re.DOTALL + $ anchor     4/4 PASS
Hook 2: git commit bypass flag   4/4 PASS
Hook 3: queue.json done check    5/5 PASS
Total: 13/13 PASS
```

---

## Files Modified

| File | Change |
|------|--------|
| `hooks/security_reminder_hook.py` | Added `re_dotall_dollar_anchor` to REGEX_SECURITY_PATTERNS; extended `check_patterns()` for combined path+content check |
| `hooks/workflow_guard_hook.py` | New script: Hook 2 (git bypass) + Hook 3 (queue.json done check) |
| `.claude/settings.json` | Registered workflow_guard_hook under Edit/Write/MultiEdit and Bash matchers |
| `CLAUDE.md` | Added Workflow guard hook reference paragraph |

---

## Advisor Consults

None required. All three rules are unambiguous binary patterns with no legitimate-use exceptions.

---

## Fix Loop — CQR Findings Round 1 (2026-04-29)

Five findings (all confidence ≥80) were resolved in a second Builder pass.

### Fix 1 — `re_dotall_dollar_anchor` false-positive (CQR #1, confidence 85)
**Problem**: The original dual-scan design used two independent `re.search` calls — one for `re.compile(...re.DOTALL` anywhere in the file, and one for `$` anywhere in the file. These could match in unrelated locations, producing false positives.

**Fix**: Replaced both `"pattern"` and `"content_check"` lambda with a single correlated regex that requires `$` to appear within the *same* `re.compile(...)` call arguments as `re.DOTALL`. The new regex matches either ordering (`$ ... re.DOTALL` or `re.DOTALL ... $`) within the parentheses of a single `re.compile` call.

**Implementation note**: The edit was performed using narrow `old_string` splits to avoid self-triggering the hook (see "Hook Pattern Interference Encountered" above). A `DOLLAR_ANCHOR` placeholder was used as an intermediate step.

### Fix 2 — Deduplication bypass for blocking rules (CQR #3, confidence 82)
**Problem**: After a blocking rule fired once, the dedup key suppressed all future fires for that file+rule combination in the same session. This allowed a second credential commit (for example) after the first block was acknowledged and the session continued.

**Fix**: Added `BLOCKING_RULE_NAMES = {"telegram_bot_token", "env_get_secret_default", "re_dotall_dollar_anchor"}` constant. In `main()`, blocking rules always fire regardless of `shown_warnings` state. Dedup state is still tracked and saved for advisory (non-blocking) rules only.

### Fix 3 — File path in blocking output (CQR #4, confidence 80)
**Problem**: Blocking messages were printed without file path context, violating the CLAUDE.md security policy "emit path+line only — never matched text."

**Fix**: Added a best-effort line-number scan (iterates `content.split("\n")`, checks each line against the matched rule's compiled pattern). Output is now prefixed `[file_path:line_number]` when a line match is found, or `[file_path]` if not. Matched text is never included.

### Fix 4 — queue.json check restricted to Write only (CQR #3 workflow_guard, confidence 88)
**Problem**: `check_queue_json_write()` operated on `new_string` (a diff fragment for Edit calls), not the full document. A valid two-step edit — Edit 1 sets `status: done`, Edit 2 sets `artefact_path` — would be falsely blocked on Edit 1.

**Fix**: Added an early return for `Edit`/`MultiEdit` tool names in `check_queue_json_write()`. Rule 2 is now enforced on `Write` calls only, where the full document is available. The function signature was updated to accept `tool_name` as first parameter; the call site in `main()` was updated accordingly. A doc comment explains the rationale.

### Fix 5 — Self-triggering warning comment (CQR #11, confidence 88)
**Problem**: The `re_dotall_dollar_anchor` rule's own source contains both a `re.compile` call with `re.DOTALL` and a `$` character, so future edits to that rule would self-trigger the hook.

**Fix**: Added a `# NOTE:` comment block immediately above the rule entry explaining that this rule matches the file's own content and directing future editors to use the split-edit workaround from CLAUDE.md "Hook pattern interference".

### Compile verification
```
python3 -m py_compile hooks/security_reminder_hook.py  → exit 0
python3 -m py_compile hooks/workflow_guard_hook.py     → exit 0
```
