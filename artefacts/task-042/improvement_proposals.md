# Improvement Proposals — task-042

[Haiku]

## Proposal 1

**Target file**: `CLAUDE.md` — Cross-file rule mirroring (M-1 pattern) section

**Change**:
Add a sentence explicitly extending the M-1 check to include the Label directive:

```
Current text (end of M-1 paragraph):
"When editing either file, verify rule counts and text match in both directions."

Proposed addition after that sentence:
"Also verify that the `Label all outputs:` directive in each agent YAML matches the tiers listed in the CLAUDE.md Label bullet (Model Policy section) — this is a second M-1 mirror that model-pin checks do not cover."
```

**Rationale**: task-042 found that `tester.yaml` had `Label all outputs: [Sonnet]` while the CLAUDE.md Label bullet only listed `[Sonnet]` and `[Opus]` — Haiku agents were already labelling `[Haiku]` in practice but the governance rule omitted it. The M-1 pattern section calls out model-tier fields but is silent on Label directives. This addition closes the gap so future model-tier audits also check label consistency.

**Status**: REQUIRES_HUMAN_APPROVAL

---

## Proposal 2

**Target file**: `CLAUDE.md` — Model Policy section

**Change**:
Add a pin-strategy note under the Haiku bullet (or as a new sub-bullet) explaining the date-suffix trigger:

```
Current Haiku bullet:
"**Haiku 4.5** — DocUpdater, SelfImprover, revise-claude-md, and any agent doing templated/structured work with no complex reasoning required"

Proposed addition (new sub-bullet or parenthetical):
"Haiku uses a date-pinned ID (`claude-haiku-4-5-20251001`) because multiple Haiku 4.5 patch builds existed at release. Opus 4.6 and Sonnet 4.6 have single authoritative builds — no date suffix needed. Add a date suffix to any model field only when multiple patch builds for that version co-exist; update all affected YAMLs together."
```

**Rationale**: `decision.md` documents this rationale, but it lives only in a task artefact. Future agents adding or upgrading model pins have no policy rule to follow — they may add spurious date suffixes to Sonnet/Opus or strip the Haiku pin. Surfacing the rule in CLAUDE.md Model Policy makes it discoverable at planning time.

**Status**: REQUIRES_HUMAN_APPROVAL
