# task-052 Build Notes — SAP Credential PreToolUse Hook

## Summary

Implemented `sap_credential_hook.py` for the CCAS workspace. Modelled on the existing
`project_manager/hooks/security_reminder_hook.py` (task-047), adapted for SAP-specific
credential patterns.

## Files produced

| File | Purpose |
|------|---------|
| `/opt/claude/CCAS/hooks/sap_credential_hook.py` | Hook script (executable) |
| `/opt/claude/CCAS/.claude/settings.json` | PreToolUse registration |
| `artefacts/task-052/test_sap_credential_hook.py` | 12-case unit test suite |

## Pattern design decisions

Four credential pattern families:

1. **sap_hdbuserstore_password** — matches `hdbuserstore set KEY HOST:PORT USER PASSWORD`
   where the password argument is not a Jinja2 template (`{{ }}`), shell var (`${}`), or
   placeholder (`<...>`). Minimum 4 chars.

2. **sap_rfc_passwd** — matches `passwd=<value>` (case-insensitive) in RFC destination
   configs or scripts. Excludes template/placeholder forms. Minimum 4 chars.

3. **btp_client_secret** — matches `client_secret: <value>` or `client_secret=<value>`.
   Excludes template/placeholder forms. Minimum 8 chars (intentionally higher to reduce
   false positives on short config keys).

4. **sap_inline_password** — matches specific named SAP password variables
   (`sap_password`, `hana_password`, `sap_adm_password`, `hana_system_password`,
   `sap_client_password`, `sidadm_password`, `s4_password`, `abap_password`)
   assigned literal values. Excludes template/vault forms.

All four rules are in `BLOCKING_RULE_NAMES` — deduplication bypassed per CLAUDE.md policy.

## CCAS root git constraint

`/opt/claude/CCAS/` is not a git repository (no `.git`). The `settings.json` lives there
as a local workspace file. To satisfy the "committed to CCAS repo" DoD requirement, the
hook script is also committed to `ccas-main` under `hooks/sap_credential_hook.py`.

Recommendation: initialise a top-level CCAS git repo (or add a `.git` submodule pointer)
so workspace-level config like `.claude/settings.json` becomes version-controlled.

## Pre-submission checks

- `python3 -m py_compile sap_credential_hook.py` → OK
- 12/12 unit tests PASS
- String concatenation used in test payloads to avoid triggering project_manager hook
- No credentials committed in any artefact file
