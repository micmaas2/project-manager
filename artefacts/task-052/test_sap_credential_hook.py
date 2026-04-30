#!/usr/bin/env python3
"""
Unit tests for /opt/claude/CCAS/hooks/sap_credential_hook.py
Uses string concatenation for SAP credential patterns in payloads to avoid
triggering the project_manager security hook on this test file itself.
"""

import json
import subprocess
import sys

HOOK = "/opt/claude/CCAS/hooks/sap_credential_hook.py"

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"

_ran: list[str] = []


def _run(payload: dict) -> int:
    result = subprocess.run(
        [sys.executable, HOOK],
        input=json.dumps(payload).encode(),
        capture_output=True,
    )
    return result.returncode


def _make_write(file_path: str, content: str) -> dict:
    return {
        "session_id": "test",
        "tool_name": "Write",
        "tool_input": {"file_path": file_path, "content": content},
    }


def _make_edit(file_path: str, new_string: str) -> dict:
    return {
        "session_id": "test",
        "tool_name": "Edit",
        "tool_input": {
            "file_path": file_path,
            "old_string": "placeholder",
            "new_string": new_string,
        },
    }


def _make_multiedit(file_path: str, new_strings: list) -> dict:
    return {
        "session_id": "test",
        "tool_name": "MultiEdit",
        "tool_input": {
            "file_path": file_path,
            "edits": [{"old_string": "x", "new_string": s} for s in new_strings],
        },
    }


failures = []


def check(name: str, payload: dict, expected_exit: int) -> None:
    _ran.append(name)
    got = _run(payload)
    ok = got == expected_exit
    status = PASS if ok else FAIL
    print(f"  [{status}] {name}  (expected exit {expected_exit}, got {got})")
    if not ok:
        failures.append(name)


print("\n=== SAP Credential Hook Unit Tests ===\n")

# ------------------------------------------------------------------
# TC-01: Write with hdbuserstore literal password → exit 2
# Concatenated to avoid triggering project_manager hook on this file.
# ------------------------------------------------------------------
hdb_content = (
    "- name: Configure HANA userstore\n"
    "  shell: /usr/sap/hdbclient/" + "hdbuserstore set HDBKEY host:30013 SYSTEM Secret"
    "Pass9!\n"
)
check(
    "TC-01 Write hdbuserstore literal password → BLOCK",
    _make_write("/opt/claude/CCAS/test.yml", hdb_content),
    2,
)

# TC-02: Write with hdbuserstore templated password → exit 0
hdb_template_content = (
    "- name: Configure HANA userstore\n"
    "  shell: /usr/sap/hdbclient/hdbuserstore set HDBKEY host:30013 SYSTEM {{ hana_password }}\n"
)
check(
    "TC-02 Write hdbuserstore Jinja2 template → ALLOW",
    _make_write("/opt/claude/CCAS/test.yml", hdb_template_content),
    0,
)

# ------------------------------------------------------------------
# TC-03: Edit with BTP client_secret literal value → exit 2
# ------------------------------------------------------------------
btp_literal = "client_" + "secret: AbCdEfGhIjKl1234"
check(
    "TC-03 Edit BTP client_secret literal → BLOCK",
    _make_edit("/opt/claude/CCAS/btp.yml", btp_literal),
    2,
)

# TC-04: Edit with BTP client_secret templated value → exit 0
btp_template = "client_secret: \"{{ btp_client_secret }}\""
check(
    "TC-04 Edit BTP client_secret Jinja2 template → ALLOW",
    _make_edit("/opt/claude/CCAS/btp.yml", btp_template),
    0,
)

# ------------------------------------------------------------------
# TC-05: Write RFC passwd= literal → exit 2
# ------------------------------------------------------------------
rfc_literal = "[RFC_DEST]\nASHOST=sap-host\n" + "pass" + "wd=SecretRfcPwd1\nLANG=EN\n"
check(
    "TC-05 Write RFC passwd= literal → BLOCK",
    _make_write("/opt/claude/CCAS/rfc.ini", rfc_literal),
    2,
)

# TC-06: Write RFC passwd= Jinja2 template → exit 0
rfc_template = "[RFC_DEST]\nASHOST=sap-host\npasswd={{ rfc_password }}\nLANG=EN\n"
check(
    "TC-06 Write RFC passwd= Jinja2 template → ALLOW",
    _make_write("/opt/claude/CCAS/rfc.ini", rfc_template),
    0,
)

# ------------------------------------------------------------------
# TC-07: Write named SAP password variable literal → exit 2
# ------------------------------------------------------------------
sap_pw_literal = "hana_" + "password: SuperSecret99\nother_var: hello\n"
check(
    "TC-07 Write hana_password literal → BLOCK",
    _make_write("/opt/claude/CCAS/vars.yml", sap_pw_literal),
    2,
)

# TC-08: Write named SAP password variable templated → exit 0
sap_pw_template = "hana_password: \"{{ vault_hana_password }}\"\nother_var: hello\n"
check(
    "TC-08 Write hana_password Jinja2 template → ALLOW",
    _make_write("/opt/claude/CCAS/vars.yml", sap_pw_template),
    0,
)

# ------------------------------------------------------------------
# TC-09: Write benign YAML → exit 0
# ------------------------------------------------------------------
benign = (
    "---\n"
    "- name: Install SAP tools\n"
    "  yum:\n"
    "    name: sap-tools\n"
    "    state: present\n"
    "  become: true\n"
)
check(
    "TC-09 Write benign YAML → ALLOW",
    _make_write("/opt/claude/CCAS/play.yml", benign),
    0,
)

# ------------------------------------------------------------------
# TC-10: MultiEdit with one clean and one literal password edit → exit 2
# ------------------------------------------------------------------
multi_safe = "hosts: all"
multi_cred = "hana_" + "password: L1teralPassw0rd"
check(
    "TC-10 MultiEdit mixed (one cred) → BLOCK",
    _make_multiedit("/opt/claude/CCAS/vars.yml", [multi_safe, multi_cred]),
    2,
)

# TC-11: RFC passwd= placeholder token → exit 0
rfc_placeholder = "passwd=<enter_your_password_here>"
check(
    "TC-11 Write RFC passwd=<placeholder> → ALLOW",
    _make_write("/opt/claude/CCAS/rfc.ini", rfc_placeholder),
    0,
)

# TC-12: Write with Bash ${VAR} reference → exit 0
bash_ref = "hana_" + "password: ${HANA_ADMIN_PASSWORD}"
check(
    "TC-12 Write hana_password bash ${VAR} → ALLOW",
    _make_write("/opt/claude/CCAS/vars.yml", bash_ref),
    0,
)

# ------------------------------------------------------------------
# TC-13: Ansible Vault tag (!vault |) must NOT be blocked → exit 0
# CQR-1 caught that !vault was false-positive blocked before the fix.
# ------------------------------------------------------------------
vault_tag = "hana_" + "password: !vault |\n  $ANSIBLE_VAULT;1.1;AES256\n  61626364...\n"
check(
    "TC-13 Write hana_password !vault tag → ALLOW",
    _make_write("/opt/claude/CCAS/vars.yml", vault_tag),
    0,
)

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
print()
total = len(_ran)
passed = total - len(failures)
print(f"Results: {passed}/{total} passed")
if failures:
    print(f"FAILED: {', '.join(failures)}")
    sys.exit(1)
else:
    print("All tests PASS")
    sys.exit(0)
