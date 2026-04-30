# Improvement Proposals — task-052 (CCAS SAP credential PreToolUse blocking hook)

## Proposal 1

**Target file**: CLAUDE.md — Shell script pre-submission check section

**Change**: Add the following bullet after the existing `grep -E '\.(yml|yaml)$'` bullet:

```
- When writing credential-detection regex patterns that match free-form password values (e.g. RFC passwords, HDBUSERSTORE keys): use `\S+` or a broad character class rather than a narrow ASCII subset. SAP RFC passwords, database keys, and API tokens routinely contain `.`, `/`, `:`, `@`, and other non-alphanumeric characters. Narrow patterns like `[A-Za-z0-9!@#$%]` silently miss valid credentials and create a false sense of coverage. Default to `\S+` (any non-whitespace) for password captures; narrow only when the credential format is documented and fixed (e.g. a UUID, a 40-hex-char hash).
```

**Rationale**: task-052 Reviewer F1 (conf 85) caught `sap_rfc_passwd` using a narrow character class that missed RFC passwords containing `.`, `/`, `:`. This is a recurring class of regex defect: the builder uses "likely" characters rather than the full set. A standing guidance in the pre-submission checklist prevents this without requiring a Reviewer loop.

**Status**: APPROVED

---

## Proposal 2

**Target file**: CLAUDE.md — Governance, Security & Observability section

**Change**: Add the following sentence after the existing **PreToolUse hooks for known-bad patterns** paragraph:

```
**Ansible Vault tag exclusion in credential hooks**: regex patterns detecting inline secrets (passwords, keys, tokens) must exclude the `!vault |` Ansible Vault tag prefix. A value beginning with `!vault |` is already encrypted and stored in Vault; blocking it is a false positive that prevents legitimate playbook edits. Add a negative lookahead `(?!.*!vault)` or a pre-check `if '!vault' in content_line: continue` to every credential-detection rule that matches YAML values. Document this exclusion in the hook's inline comments.
```

**Rationale**: task-052 CQR F1 (conf 95) found that `sap_inline_password` and `sap_hdbuserstore_password` falsely blocked legitimate Ansible Vault references. The fix was applied, but the pattern (Vault-tag exclusion) applies to any future credential hook written for YAML-heavy repos (CCAS, pi-homelab). Documenting it in CLAUDE.md prevents the same false-positive loop on the next hook.

**Status**: APPROVED

---

## Proposal 3

**Target file**: CLAUDE.md — Shell script pre-submission check section

**Change**: Add the following bullet (dynamic test counter pattern) after the `hardcoded total` issue was caught by CQR:

```
- If a test file counts tests with a hardcoded total (e.g. `total = 12`): replace with a dynamic count derived from the test list itself (e.g. `total = len(TEST_CASES)`). Hardcoded totals silently under-count when new test cases are appended — the count passes green while coverage is incomplete. Only use a hardcoded total when the test suite is intentionally fixed and the count is asserted as an invariant.
```

**Rationale**: task-052 CQR F2 (conf 90) caught `total = 12` hardcoded in the test file; TC-13 (the `!vault` regression test) was added but the counter was not updated. Dynamic counters derived from `len(TEST_CASES)` are maintenance-free and self-correct when tests are added or removed.

**Status**: APPROVED

---

## Proposal 4

**Target file**: CLAUDE.md — Governance, Security & Observability section

**Change**: Add the following note after the **Workflow guard hook** paragraph:

```
**Fail-open except blocks in security hooks require an explicit rationale comment**: a bare `except Exception: return None` in a PreToolUse hook silently disables the block if an unexpected error occurs. This is the correct production safety choice (hook errors must not block legitimate writes), but the design intent is non-obvious and future refactors may remove the pattern thinking it is dead code. Add a comment: `# Fail-open: hook errors must never block legitimate writes — log and pass through`. Without this comment, future reviewers cannot distinguish intentional fail-open from accidental swallowing.
```

**Rationale**: task-052 CQR F3 (conf 85) flagged a bare `except` block with no comment. The fail-open pattern is correct for hooks, but must be explicitly documented at the call site or future maintainers may add logging, re-raise, or convert it to fail-closed. This is the same "comment-at-call-site" principle already applied to budget enforcement guards.

**Status**: APPROVED
