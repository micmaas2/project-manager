# Build Notes: task-048

**Date**: 2026-04-28  
**Source**: code-quality-reviewer findings < 80 confidence (routed here, no Builder loop required)

## Low-Confidence Findings (for future implementers)

### m-1: BL-104 PostToolUse trigger not specified (confidence: 72)
When implementing BL-104, the PostToolUse hook should trigger on the **Write tool** where `file_path` matches `artefacts/*`. Check: non-empty `mvp_template`, non-empty `artefact_path`, presence of at least one acceptance criterion. Do not trigger on every Write — scope to artefact paths only.

### m-2: BL-109 Docker MCP scope (confidence: 70)
BL-109 should be scoped to **read-only container health checks** (status queries only). "Auto-remediation of crashed services" (restart/exec) requires a separate human-gated decision. When implementing, request only read-only Docker MCP permissions; document the restart capability as out-of-scope for the initial adopt.

### m-3: BL-105 Hook placement (confidence: 68)
BL-105 (commit-msg BL-ID correlation) must be implemented in `hooks/commit-msg` (receives commit message via `$1`), **not** in `hooks/pre-commit`. Pre-commit does not receive `$1` reliably per CLAUDE.md architecture. Mirror the existing commit-msg hook structure.

### m-4: BL-108 Lovelace validation tool (confidence: 65)
`yamllint` validates YAML syntax but does not catch Lovelace-specific errors. For semantic Lovelace validation, use: `ssh pi4 'docker exec homeassistant python -m homeassistant --config /config --check'`. Document this as a required step in the BL-108 implementation plan.

### m-5: BL-106 Ansible idempotency caveat (confidence: 62)
`ansible-lint` catches common idempotency anti-patterns (e.g., `command:` vs `shell:`, missing `creates:` flags) but cannot guarantee full idempotency. True idempotency requires running the playbook twice against a real or mocked inventory. Document this caveat explicitly in the BL-106 implementation — do not market the hook as idempotency proof.
