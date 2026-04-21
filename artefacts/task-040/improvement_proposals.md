# Improvement Proposals — task-040: Agent Model Usage Audit

**Generated**: 2026-04-19  
**Agent**: SelfImprover [Haiku]

---

## Proposal 1

**Target file**: `CLAUDE.md` — Model Policy section  
**Change**:

In the Model Policy section, replace:

```
- **Haiku 4.5** — DocUpdater, SelfImprover, revise-claude-md, and any agent doing templated/structured work with no complex reasoning required
```

with:

```
- **Haiku 4.5** — DocUpdater, SelfImprover, revise-claude-md, and any agent doing templated/structured work with no complex reasoning required. Agent YAMLs use the pinned date-stamped version (`claude-haiku-4-5-20251001`) for deployment stability; update both `doc-updater.yaml` and `self-improver.yaml` together when a new Haiku 4.5 patch is released.
```

**Rationale**: The audit found `doc-updater.yaml` and `self-improver.yaml` both use `claude-haiku-4-5-20251001` while CLAUDE.md only says `Haiku 4.5`. No pinning policy exists, so when a newer patch releases there is no guidance on what triggers an update or that both YAMLs must be updated together. Adding a one-line pinning strategy closes the documentation gap and prevents silent version drift.  
**Status**: APPROVED

---

## Proposal 2

**Target file**: `CLAUDE.md` — Model Policy section  
**Change**:

Add a note after the Tester row in the Agent Roles & Spawn Order table (or in a comment adjacent to `tester.yaml`) clarifying the planned downgrade:

In the table row for Tester, change the Model column from `Sonnet` to `Sonnet (→ Haiku, task-042)` to signal the pending downgrade is tracked and intentional — not an oversight.

**Rationale**: The audit confirmed Tester is the only downgrade opportunity (P1, $0.0066/run). The implementation is deferred to task-042. Without a marker in the table, a future audit would re-examine the same question and reach the same conclusion redundantly. A brief annotation closes the loop without requiring task-042 to be completed first.  
**Status**: APPROVED

---

## Proposal 3

**Target file**: `CLAUDE.md` — Governance / Model Policy section  
**Change**:

Add a new bullet under Model Policy:

```
- **Model audit cadence**: Run `task-040`-style audits whenever a new model version is released or after 10+ tasks are added. Audit methodology: (1) list all YAML agents + built-ins separately; (2) compare against current policy table; (3) use actual `logs/token_log.jsonl` data for cost projections — never assumed token counts.
```

**Rationale**: The audit process itself was not documented anywhere. The finding that built-in subagent models cannot be overridden (they are fixed by type) is audit-methodology knowledge that would be rediscovered from scratch on the next audit. Recording the methodology and the distinction between YAML agents vs built-ins saves future audit time and prevents the repeated mistake of treating built-ins as configurable.  
**Status**: APPROVED
