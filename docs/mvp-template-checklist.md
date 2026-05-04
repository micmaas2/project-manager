# MVP Template — Security/Arch Impact Checklist

When filling the `Security/arch impact:` field of an MVP template, verify each applicable item:

  - If outbound HTTP: private IP ranges blocked (localhost, 127.x, 10.x, 192.168.x, 172.16-31.x)?
  - If outbound HTTP: request timeout set?
  - If any user-controlled value (topic, category, tag, filename) is used in a file path:
      - Validate against allowlist or strict regex (e.g. [a-z0-9-]+) before path construction
      - Assert finalPath.startsWith(ALLOWED_ROOT) after construction (use path.resolve to collapse ..)
  - If LLM output is used as a structured field (slug, enum, filename): prompt character-set
    constraint and validation regex in code must be identical — document both in the artefact
  - If any field value from external data (email headers, API responses, user input) is
    interpolated into YAML/JSON/Markdown: escape strings before interpolation (e.g. replace
    " with \" in YAML double-quoted scalars; strip ASCII control chars 0x00-0x1F, not just \n)
  - If any free-text field from an external API (description, extract, title, etc.) is embedded
    in an LLM prompt: strip ASCII control chars 0x00–0x1F (excluding \t and \n) — apply to ALL
    fields passed to the prompt, not only to those written to files
  - If an external ID (e.g. message ID, record ID) is passed to a downstream step: validate
    it is non-null/non-empty at point of use; throw a descriptive error if absent
  - If the script runs under cron or systemd (no interactive terminal):
      - Log writability guard: verify/create log file before first write; exit to stderr if unwritable
      - Concurrency lock: use `flock -n` on a lock file at startup; skip (exit 0) if lock held
      - SSH/auth identity: export `GIT_SSH_COMMAND` or equivalent explicitly — cron env has no agent
      - Log rotation: document logrotate config as a **required** deploy step, not optional
  - If the task rotates a credential or secret (PAT, API key, token):
      - Rollback section must include "Estimated time-to-restore: N-M minutes"
      - Estimate covers worst-case manual steps (e.g. generate new token + 2 config updates)
  - If the task implements a budget enforcement or rate-limiting gate: add a
    "comment-at-call-site" checklist item ensuring all guard calls carry explicit notes
    explaining why the guard must remain at the current scope level (e.g. outside try/except).
    Maintenance traps where guards are inadvertently moved to a scope they do not protect
    against are non-obvious failures.
