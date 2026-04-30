# Review: task-052 — CCAS SAP Credential PreToolUse Hook

**Reviewer**: Reviewer agent [Sonnet]  
**Date**: 2026-04-30  
**Verdict**: **APPROVED** (with advisory notes for Builder)

---

## Acceptance Criteria Assessment

| # | Criterion | Result |
|---|-----------|--------|
| 1 | `hooks/sap_credential_hook.py` exists at `/opt/claude/CCAS/hooks/` and is executable | PASS (`-rwxr-xr-x`) |
| 2 | `.claude/settings.json` created at `/opt/claude/CCAS/.claude/` with PreToolUse registration for Edit\|Write\|MultiEdit | PASS |
| 3 | Hook detects and blocks: hdbuserstore passwords, RFC dest `passwd=`, BTP `client_secret`, inline SAP passwords | PASS — all 4 rule families implemented and tested |
| 4 | Blocking output emits `file_path:line_number` only — never matched credential value | PASS — verified by output inspection |
| 5 | Blocking rules bypass session dedup (`BLOCKING_RULE_NAMES` constant present, covers all 4 rules) | PASS — dynamic set comprehension over `SAP_CREDENTIAL_PATTERNS` |

---

## Findings

| # | ruleName | Description | Confidence | Severity | Action |
|---|----------|-------------|------------|----------|--------|
| F-01 | `sap_rfc_passwd` | Narrow character class causes false negatives on RFC passwords containing `.`, `/`, `:` in positions 1–3 | 85 | Medium | Builder loop |
| F-02 | `sap_rfc_passwd` | No test case for `passwd=${VAR}` shell-variable exclusion (other 3 rules have `${VAR}` coverage) | 72 | Low | Notes only |
| F-03 | All rules | No test case: MultiEdit with all-clean edits should return exit 0 (only mixed covered) | 65 | Low | Notes only |
| F-04 | N/A | `_WORKSPACE_ROOT` is defined but unused — adds confusion without enforcing path containment | 60 | Low | Notes only |

---

## Finding Detail

### F-01 — `sap_rfc_passwd` narrow character class (confidence: 85) — BUILDER LOOP

**Location**: `sap_credential_hook.py` lines 59–65

The `sap_rfc_passwd` pattern uses a restricted character class:
```
[A-Za-z0-9!@#$%^&*()\-_+=|]{4,}
```

The other three rules all use `\S{4,}` or `\S{8,}` (any non-whitespace), which is consistent and comprehensive. The RFC rule's limited class misses passwords that contain `.` (dot), `/` (slash), `:` (colon), or `;` (semicolon) in the first 1–3 positions. Specifically:

- `passwd=ab/cd99` — `ab` is only 2 chars before `/`, minimum not reached — **not blocked**
- `passwd=abc.def` — `abc` is only 3 chars before `.`, minimum not reached — **not blocked**
- `passwd=abcd.ef` — `abcd` is 4 chars before `.`, partial match — **blocked**

SAP RFC destination passwords can legally contain these characters. The inconsistency with the other three rules is the primary indicator this is unintentional.

**Recommended fix**: Replace the character class with `\S{4,}` and add a `(?!\s)` guard if needed:

```python
"pattern": re.compile(
    r'\bpasswd\s*=\s*'
    r'(?!["\']?\{\{|["\']?\$\{|<|\s*$)'
    r'["\']?\S{4,}',
    re.IGNORECASE,
),
```

No credential values are shown above. The vulnerable pattern can be reconstructed from the character class analysis.

---

### F-02 — Missing `${VAR}` test for `sap_rfc_passwd` (confidence: 72) — Notes only

TC-12 covers `${VAR}` exclusion for `sap_inline_password`. No equivalent test exists for `sap_rfc_passwd`. The exclusion lookahead `(?!\s*$|["\']?\$\{|...)` is present in the pattern and correctly excludes shell vars, but the gap in test coverage leaves this unverified in the test suite.

---

### F-03 — MultiEdit all-clean path not tested (confidence: 65) — Notes only

TC-10 covers MultiEdit with one clean + one credential edit → block. No test covers MultiEdit where all edits are clean → should exit 0. Low risk: the logic (`"\n".join(new_strings)` → `_scan()`) is straightforward, but the path is not exercised.

---

### F-04 — `_WORKSPACE_ROOT` defined but unused (confidence: 60) — Notes only

`_WORKSPACE_ROOT = "/opt/claude/CCAS"` is defined on line 21 but is never referenced. The CLAUDE.md `_safe_path()` containment rule applies to scripts that open files via CLI arguments — this hook receives `file_path` only for error reporting, not file I/O, so a containment guard is not strictly required. However, the dead constant adds noise. Either remove it or wire it into a path-scoping comment.

---

## Positive Observations

- **Output policy correctly implemented**: stderr output verified to contain only `file_path:line_number` and rule metadata — no matched credential text leaks.
- **BLOCKING_RULE_NAMES via set comprehension**: dynamic derivation from `SAP_CREDENTIAL_PATTERNS` eliminates the class of orphaned/stale entries that a hardcoded set would risk.
- **Fail-open error handling**: malformed JSON, empty input, and non-targeted tool names all return exit 0, preventing hook failures from blocking legitimate writes.
- **Jinja2/shell/placeholder exclusions**: all four rules correctly exclude `{{ var }}`, `${VAR}`, and `<placeholder>` forms — verified by TC-02, TC-04, TC-06, TC-08, TC-11, TC-12.
- **Edit/MultiEdit content field**: `_extract_content()` correctly uses `new_string` for Edit and `new_string` per edit for MultiEdit — `old_string` is never scanned.
- **All 12 unit tests pass**: 12/12 confirmed by live test run.
- **No credentials in artefacts**: test file uses string concatenation to construct credential-containing payloads without embedding literals — correct technique.
- **Script syntax valid**: `python3 -m py_compile` exits 0.

---

## Summary

The implementation is functionally correct and meets all five acceptance criteria. One finding reaches the ≥80 confidence threshold (F-01: RFC passwd character class gap) and requires a Builder loop. The fix is a one-line change to the `sap_rfc_passwd` pattern. The remaining three findings are advisory (< 80 confidence) and are routed to build notes only.
