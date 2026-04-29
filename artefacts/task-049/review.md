# Review — task-049

**Reviewer**: Sonnet [Sonnet]  
**Date**: 2026-04-28  
**Task**: Hooks-over-prompts audit — implement top 3 rules as hooks (BL-088)  
**Verdict**: APPROVED

---

## Checklist Results

| Check | Result | Notes |
|-------|--------|-------|
| `python3 -m py_compile hooks/workflow_guard_hook.py` | PASS | exit 0 |
| `python3 -m py_compile hooks/security_reminder_hook.py` | PASS | exit 0 |
| `python3 -m json.tool .claude/settings.json` | PASS | exit 0 |
| Hook 1 registered (Edit\|Write\|MultiEdit → security_reminder_hook) | PASS | Pre-existing matcher, hook added |
| Hook 2 registered (Bash → workflow_guard_hook) | PASS | New matcher entry |
| Hook 3 registered (Edit\|Write\|MultiEdit → workflow_guard_hook) | PASS | Second hook in existing matcher |
| Hooks emit to stderr | PASS | Both scripts use `print(..., file=sys.stderr)` |
| Exit code 2 used for blocking | PASS | Both scripts use `sys.exit(2)` |
| Hook 1 requires BOTH re.DOTALL AND `$` (not either/or) | PASS | `content_check` lambda uses `and`; verified via direct invocation |
| Hook 3 handles atomic updates (status + artefact_path in same change) | PASS | MultiEdit with both fields passes; MultiEdit with only status blocked |
| Hooks do not emit matched text (only static policy messages) | PASS | Reminder strings are static constants; no f-string interpolation |
| No credentials or sensitive values in artefact files | PASS | No live tokens/passwords found |
| CLAUDE.md surrounding context intact | PASS | Lines 255–263 verified; existing content undisturbed |

---

## Findings

### Finding 1 — Hook 1 `content_check` scope is file-level, not call-level

- **Severity**: Minor
- **confidence**: 72 (72)
- **Location**: `hooks/security_reminder_hook.py`, the `re_dotall_dollar_anchor` entry in `REGEX_SECURITY_PATTERNS`
- **Finding**: The `content_check` lambda tests whether `re.compile(...re.DOTALL` appears anywhere in the file content AND whether `$` (not followed by `{`) appears anywhere in the file content — these two patterns are evaluated independently against the full file. A file that contains `re.compile(r"pat", re.DOTALL)` and also contains an unrelated `$` elsewhere (e.g. in a docstring referencing shell syntax, or in a separate non-DOTALL regex) would trigger a false block. Similarly, `re.compile(` and `re.DOTALL` could appear in separate comment blocks and still match.
- **Recommendation**: For a tighter check, scope the `re.DOTALL` search to within the argument span of a single `re.compile()` call and check `$` only within that same span. However, given that `$` in Python source (outside regex literals) is rare, and any `.py` file containing both `re.DOTALL` and `$` is very likely to be the exact scenario the rule targets, the practical false positive rate is low. Acceptable at this confidence level; a follow-up BL item to tighten the scope is recommended if false positives are observed in practice.

**Builder loop required**: No — confidence 72 < 80.

---

### Finding 2 — `"pattern"` field in `re_dotall_dollar_anchor` entry is dead code

- **Severity**: Suggestion
- **confidence**: 90 (90)
- **Location**: `hooks/security_reminder_hook.py:133`
- **Finding**: The `re_dotall_dollar_anchor` entry in `REGEX_SECURITY_PATTERNS` includes a `"pattern"` field (`re.compile(r"re\.compile\s*\(.*?re\.DOTALL", re.DOTALL)`). In `check_patterns()`, the code path for entries with both `path_check` and `content_check` never consults `rp["pattern"]` — it goes directly to the combined `path_check(path) and content_check(content)` branch. The `"pattern"` field is therefore unreachable for this entry and has no effect on detection. While this is not a bug, it may mislead future maintainers into believing the pattern alone guards the check.
- **Recommendation**: Add a comment in the entry noting that `"pattern"` is unused when `content_check` is present and the combined-branch is taken, OR remove the `"pattern"` key from this entry and update `check_patterns()` to not require a `"pattern"` key for combined-check entries. The latter avoids dead code but changes the existing data structure contract.

**Builder loop required**: No — this is a documentation/maintenance suggestion; no functional impact.

---

### Finding 3 — CLAUDE.md does not cross-reference that `re.DOTALL + $` is now hook-enforced

- **Severity**: Suggestion
- **confidence**: 65 (65)
- **Location**: `CLAUDE.md:131` (CQR description) and `CLAUDE.md:255` (PreToolUse hooks paragraph)
- **Finding**: The existing CQR rule at line 131 still reads "for any regex using `re.DOTALL`, flag use of `$` as a stop anchor (use `\Z` instead)". The workflow guard hook paragraph at line 257 mentions only the two rules in `workflow_guard_hook.py`. Neither location cross-references that the `re.DOTALL + $` rule is now also enforced at edit time by `security_reminder_hook.py`. This is a minor documentation gap — a reader of the CQR rule has no indication the rule has a hook-level enforcement layer.
- **Recommendation**: Add a parenthetical to the CQR line: "(also blocked at edit time by security_reminder_hook.py — see PreToolUse hooks paragraph below)". This is a one-line edit and aids discoverability for future maintainers. Confidence is below 80; not a blocking issue.

**Builder loop required**: No — confidence 65 < 80.

---

## Positive Observations

1. **Hook 1 dual-check design is correct**: The combined `path_check + content_check` extension to `check_patterns()` is clean and non-breaking — entries without `content_check` fall through to the existing `elif rp["pattern"].search(content)` branch unchanged.

2. **Hook 2 regex handles flag ordering correctly**: The `git\s+commit\b[^;\n]*--no-verify` pattern catches `--no-verify` both before and after other flags. Test 2d (flag after `-am`) verified PASS in the Tester report and confirmed live during this review.

3. **Hook 3 atomic update requirement is semantically correct**: Blocking a narrow `Edit` that sets only `"status": "done"` without including `"artefact_path"` in `new_string` is the intended behavior — it enforces the CLAUDE.md atomic-update contract. The recommended `python3` atomic update pattern (from CLAUDE.md `queue.json stale-read fix`) naturally includes both fields and passes cleanly.

4. **MultiEdit is fully covered**: Both hooks correctly handle MultiEdit by joining all `new_string` values from the `edits` list. Tested and confirmed.

5. **Hook interference documented and navigated**: The build_notes.md correctly records that the initial Write of the test file was blocked by Hook 1 itself (proving live enforcement), and that CLAUDE.md editing required a split edit per the hook-pattern-interference rule. Both incidents demonstrate the hooks functioning as designed.

6. **No matched text in hook output**: Both `workflow_guard_hook.py` reminders are static string constants with no f-string or `.format()` interpolation of user-supplied content. This is compliant with the principle of never reflecting matched content back to the user.

---

## Verdict: APPROVED

No findings with confidence ≥ 80 require a Builder loop. All 3 hooks are implemented, correctly registered, syntactically valid, and functionally verified by 13/13 integration tests. The two suggestion-level findings (dead `"pattern"` field, CLAUDE.md cross-reference gap) are candidates for a follow-up BL item or SelfImprover proposal rather than a blocking rework.
