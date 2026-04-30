# Code Quality Review — task-052: SAP Credential PreToolUse Hook

**Reviewer**: code-quality-reviewer (built-in, Sonnet)
**Date**: 2026-04-30
**Verdict**: NEEDS_REVISION

Files reviewed:
- `/opt/claude/CCAS/hooks/sap_credential_hook.py`
- `/opt/claude/CCAS/.claude/settings.json`
- `/opt/claude/project_manager/artefacts/task-052/test_sap_credential_hook.py`

---

## Finding 1 — MAJOR | confidence: 95

**Ansible `!vault` tag causes false-positive BLOCK on `sap_inline_password` and `sap_hdbuserstore_password`**

**Location**: `sap_credential_hook.py`, `SAP_CREDENTIAL_PATTERNS`, rules `sap_inline_password` and `sap_hdbuserstore_password`

**Description**: When a developer correctly secures a credential using Ansible Vault (the recommended approach), the YAML key looks like:

```yaml
hana_password: !vault |
  $ANSIBLE_VAULT;1.1;AES256
  6162616261...
```

The line `hana_password: !vault |` matches the `sap_inline_password` pattern because `!vault` is 6+ non-space characters and the negative lookahead does not include `!vault`. The hook will block writing the exact secure pattern it is trying to enforce. The same problem exists for `hdbuserstore` with a trailing `!vault` token.

**Verified**: `hana_password: !vault |` — matched=True (False-positive confirmed via dynamic test). The `btp_client_secret` rule is not affected (requires `\S{8,}`; `!vault` is 6 chars).

**Risk**: Developers writing `!vault`-encrypted variables in Ansible playbooks will be blocked by the hook, defeating the enforcement intent and likely causing hook bypass attempts.

**Fix**: Add `!vault` to the negative lookahead in the two affected patterns.

`sap_inline_password` — change:
```python
r'(?!["\']?\{\{|["\']?\$\{|<|vault\s*\|)'
```
to:
```python
r'(?!["\']?\{\{|["\']?\$\{|<|!vault|vault\s*\|)'
```

`sap_hdbuserstore_password` — change:
```python
r'(?!["\']?\{\{|["\']?\$\{|<)\S{4,}'
```
to:
```python
r'(?!["\']?\{\{|["\']?\$\{|<|!vault)\S{4,}'
```

Add a corresponding test case (TC-13) to `test_sap_credential_hook.py`:
```python
# TC-13: hana_password with Ansible !vault tag → exit 0
hana_vault = "hana_" + "password: !vault |"
check(
    "TC-13 Write hana_password !vault tag → ALLOW",
    _make_write("/opt/claude/CCAS/vars.yml", hana_vault),
    0,
)
```

---

## Finding 2 — MINOR | confidence: 85

**stdin parse failure exits 0 (permissive fail-open) — design decision undocumented**

**Location**: `sap_credential_hook.py`, line 121 (`sys.exit(0)` in the `except` block)

**Description**: When `json.loads` raises any exception (malformed JSON, truncated stdin, encoding error), the hook exits 0, allowing the tool call through. This is a fail-open design. The alternative — exit 2 (block) — is deny-by-default and eliminates any bypass via deliberately malformed input.

The current choice is defensible (a broken hook should not halt all editing), but the rationale is not documented anywhere in the code. An undocumented tradeoff invites future contributors to "fix" it incorrectly.

**Fix**: Add a comment at the except block explaining the choice:

```python
except (json.JSONDecodeError, Exception) as exc:
    _debug_log(f"JSON parse error: {exc}")
    # Fail open: a parse error means we cannot determine whether a credential
    # is present. Blocking on parse error would halt all editing when the hook
    # environment is broken. Log the error and allow through.
    sys.exit(0)
```

---

## Finding 3 — MINOR | confidence: 70

**`sap_rfc_passwd` character class excludes tilde — false negative for `~`-prefixed passwords**

**Location**: `sap_credential_hook.py`, `sap_rfc_passwd` pattern, character class `[A-Za-z0-9!@#$%^&*()\-_+=|]`

**Description**: Passwords beginning with `~` are not uncommon (some SAP tools generate them). `passwd=~TildePassw0rd` does not match the pattern because `~` is not in the character class and the lookahead does not exclude it, so the regex engine sees `~` as the first character and fails to advance. A password like `passwd=Pass~word9` is caught only because `Pass` (4 chars) matches before the `~`.

**Risk**: Low. This is a narrow false-negative, not a false positive. The fix would be to use `\S+` instead of the character class, but that risks over-matching comments or documentation fragments. The current character class is the safer tradeoff; the gap should be documented.

**Fix option A** (document-only): Add a comment above the pattern noting that `~`-prefixed passwords are not caught.

**Fix option B** (extend char class): Add `~` to the character class: `[A-Za-z0-9!@#$%^&*()\-_+=|~]`

---

## Finding 4 — MINOR | confidence: 60

**`sap_inline_password` missing `sap_hana_password` variant**

**Location**: `sap_credential_hook.py`, `sap_inline_password` alternation group, line 80

**Description**: The `sap_inline_password` pattern covers `hana_password`, `hana_system_password`, and `sap_client_password`, but not `sap_hana_password`, which is the conventional variable name used by the `community.sap_install` and `redhat.sap_install` Ansible collections (e.g. `sap_hana_install_master_password`, often shortened to `sap_hana_password` in group_vars).

**Risk**: Low — this is a coverage gap, not a correctness issue. The other patterns still catch many forms.

**Fix**: Add `sap_hana_password` to the alternation:
```python
r'\b(?:sap_password|hana_password|sap_hana_password|sap_adm_password|hana_system_password|'
```

---

## Finding 5 — MINOR | confidence: 90

**Test file `total = 12` hardcoded — will silently under-count if TCs are added**

**Location**: `test_sap_credential_hook.py`, line 201

**Description**: The total is hard-coded as `total = 12`. When TC-13 and any future test cases are added, the developer must remember to update this constant. If forgotten, the results line reads `12/12 passed` even when 13 tests ran, hiding the discrepancy.

**Fix**: Replace the hardcoded constant with a dynamic count derived from the `failures` list and a counter incremented by `check()`:

```python
total_run = 0

def check(name: str, payload: dict, expected_exit: int) -> None:
    global total_run
    total_run += 1
    got = _run(payload)
    ok = got == expected_exit
    status = PASS if ok else FAIL
    print(f"  [{status}] {name}  (expected exit {expected_exit}, got {got})")
    if not ok:
        failures.append(name)

# ... tests ...

passed = total_run - len(failures)
print(f"Results: {passed}/{total_run} passed")
```

---

## Explicit checklist from review instructions

| Check | Result |
|---|---|
| Hook ever logs/emits matched credential text | CLEAN — emits `file_path:line_number` only; description and rule name are static strings |
| All 4 credential rules in `BLOCKING_RULE_NAMES` | PASS — set is built dynamically from `SAP_CREDENTIAL_PATTERNS`; all 4 rules confirmed present |
| Regex excludes Jinja2 `{{ var }}` | PASS — verified for all 4 patterns |
| Regex excludes shell vars `${VAR}` | PASS — verified for all 4 patterns |
| Regex excludes placeholders `<...>` | PASS — verified for all 4 patterns |
| `_WORKSPACE_ROOT` constant defined | PASS — line 21: `_WORKSPACE_ROOT = "/opt/claude/CCAS"` |
| Test file uses string concatenation for credential patterns | PASS — all 6 blocking test cases concatenate across the trigger token |
| `_extract_content` handles MultiEdit correctly | PASS — joins all `new_string` values; `get("new_string", "")` handles missing keys gracefully |
| stdin parse failure exits 0 | PRESENT but undocumented (Finding 2) |
| Ansible `!vault` tag exclusion | MISSING — causes false-positive BLOCK (Finding 1) |

---

## Positive Observations

- Output policy is correctly implemented: no path in `main()`, `_scan()`, or `_debug_log()` ever emits the matched text. The description and rule name fields are static, not derived from matched content.
- `BLOCKING_RULE_NAMES` is built dynamically from `SAP_CREDENTIAL_PATTERNS` rather than a parallel hardcoded set, eliminating the risk of the two falling out of sync.
- The negative lookahead design (excluding Jinja2, shell vars, and placeholders) correctly handles the primary use cases verified across all 12 existing test cases.
- String concatenation in test cases is applied consistently across all credential-triggering test payloads, preventing the test file itself from triggering the project_manager security hook.
- `_extract_content` handles the missing `edits` key for MultiEdit gracefully (returns `""`, allowing the hook to exit 0 cleanly).
- `settings.json` hook configuration is minimal and correct: only the three tools that write file content are intercepted.

---

## Summary

The hook is structurally sound: output policy, BLOCKING_RULE_NAMES completeness, and the core exclusion logic all meet the requirements stated in CLAUDE.md. One major issue requires a fix before the hook is safe for production use: the `!vault` tag false positive will block developers from writing Ansible vault-encrypted variables, which is the primary secure storage pattern in this codebase. The remaining findings are minor quality improvements.

**Overall risk rating: Medium** (blocked by Finding 1; all other findings are low-severity)

**Required before closing task-052**: Fix Finding 1 (add `!vault` to lookahead in `sap_inline_password` and `sap_hdbuserstore_password`) and add TC-13 to the test file.
