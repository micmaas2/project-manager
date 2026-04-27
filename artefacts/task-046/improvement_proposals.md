# task-046: Improvement Proposals

**Date**: 2026-04-27  
**Agent**: SelfImprover [Haiku]

---

## Proposal 1: Add mandatory credential-handling pattern to Builder YAML

**Target file**: `.claude/agents/builder.yaml`

**Change**: Add a new checklist item under "Pre-submission validation" or "Code review":
```
- For any script reading a credential (token, password, key, API key) from environment:
  Use `os.environ["KEY"]` with an exception handler, never `os.environ.get("KEY", fallback)`.
  Fallback defaults with hard-coded values are credential storage anti-patterns.
  Exception handler must log a descriptive error and exit; do not silently proceed with placeholder values.
  Example:
    TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
    if not TELEGRAM_BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN environment variable is required")
        sys.exit(1)
```

**Rationale**: task-046 and task-044/045 show a recurring pattern where credentials are hardcoded as fallback defaults in `os.environ.get()` calls. CQR caught a live Telegram bot token (confidence 98) and an admin password (confidence 85) in the same task. This indicates the anti-pattern is spreading; making it explicit in the Builder checklist prevents recurrence.

**Status**: REQUIRES_HUMAN_APPROVAL

---

## Proposal 2: Add pre-commit artefact credential scan to git hooks

**Target file**: `hooks/pre-commit`

**Change**: Add a credential pattern check that blocks commits if any file in `artefacts/` contains credential-like values:
```bash
# Scan artefacts/ for credential patterns
CRED_PATTERNS=(
  '[0-9]{10}:[A-Za-z0-9_-]{35}'      # Telegram bot token format
  'MasAdmin[0-9]+'                    # Known weak passwords
  'password.*[A-Za-z0-9]+'            # Common placeholders
)
for pattern in "${CRED_PATTERNS[@]}"; do
  if grep -r "$pattern" artefacts/ 2>/dev/null | grep -v 'Build notes' | grep -v '<redacted'; then
    echo "ERROR: Credential pattern detected in artefacts/. Redact and retry."
    exit 1
  fi
done
```

**Rationale**: task-046 CQR F3 (confidence 90) caught `MasAdmin2026!` exposed in build_notes.md. This was a manual setup password; but the presence of the literal value in a committed file established a dangerous pattern. A pre-commit hook prevents the pattern from entering the repo by catching credentials at the point of commit, before they can be pushed or exposed in git history.

**Status**: REQUIRES_HUMAN_APPROVAL

---

## Proposal 3: Document library version behavior gaps in code comments

**Target file**: `.claude/agents/builder.yaml`

**Change**: Add to the "Code quality" or "Documentation" checklist:
```
- When using a versioned library with known behavior gaps (features silently dropped, 
  API calls that do not persist parameters, etc.):
  1. State the library name and version in the comment
  2. State the specific limitation ("parameter X is silently dropped at runtime")
  3. Recommend the workaround (if any) or document the intended replacement behavior
  Example:
    # uptime-kuma-api v1.2.1 silently drops the keyword parameter.
    # HTTP 200 status check only; body content is not validated.
    keyword="healthy"  # Not persisted; included for future compatibility when library is upgraded
```

**Rationale**: task-046 build_notes.md documented that `keyword=` is dropped, but the inline code comment ("Expect `{"status":"healthy"}` in body") contradicted actual runtime behavior. When a library limitation is documented in notes but the code comment is incorrect, future maintainers see the code comment first and may assume body checking works. Versioned behavior gaps should be explicit in code so they are not missed during library upgrades or refactoring.

**Status**: REQUIRES_HUMAN_APPROVAL

---

## Proposal 4: Add artefact credential redaction to Definition of Done checklist

**Target file**: `CLAUDE.md` (MVP template section)

**Change**: Add a new item to the "Definition of Done" template:
```
- [ ] No credentials or sensitive values are committed in artefact files.
       If a credential (password, token, key) is mentioned in build_notes.md or 
       other docs, redact it to `<redacted — see ENV_VAR_NAME>` or `<set-via-env>`.
       Credentials in artefacts can be exposed if the repo is shared or pushed to public remotes.
```

**Rationale**: task-046 CQR F3 explicitly noted that even one-off setup passwords committed to git establish a dangerous pattern. Unlike code secrets which are caught by pre-commit hooks, documentation secrets require manual discipline. Adding it to the Definition of Done checklist for every task makes credential sanitization a required step before marking done.

**Status**: REQUIRES_HUMAN_APPROVAL
