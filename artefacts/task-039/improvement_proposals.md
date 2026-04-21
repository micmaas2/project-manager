# Improvement Proposals — task-039: Cost-Aware Model Routing Design

## Proposal 1

**Target file**: `CLAUDE.md` — MVP template section, `Cost estimate` field guidance

**Change**: Add a sub-bullet under the `Cost estimate` field in the MVP template:

```
Cost estimate: EUR ...
  - If cost estimate is based on caching: state lower bound (realistic hit rate) AND upper bound (100% hit rate); document cache TTL caveat (Anthropic: 5 min)
  - If cost estimate involves token counts: state assumed input/output split explicitly (e.g. 3,500 input / 1,500 output per run)
```

**Rationale**: task-039 review found the PM caching savings figure ($18.59/1,000 runs) was an upper bound only — the 5-minute TTL means cross-session calls miss cache and reduce real savings by up to 67%. Reviewer F2 (confidence 85) required a mandatory fix. Without a template prompt, future Builders will repeat the same single-figure presentation. This proposal makes the range requirement explicit at the point where cost estimates are authored.

**Status**: APPROVED

---

## Proposal 2

**Target file**: `CLAUDE.md` — Model Policy section, existing label rule

**Change**: Extend the existing label rule to explicitly cover the audit-trail risk of model changes:

Current text:
```
- **Label** all outputs and tool calls with `[Sonnet]` or `[Opus]`
```

Proposed addition (new bullet immediately after):
```
- **Label update on model change**: when a YAML agent's model field is changed, update the `Label all outputs` line in that agent's YAML in the same commit — a stale label (e.g. `[Sonnet]` after downgrade to Haiku) silently breaks audit integrity
```

**Rationale**: task-039 review Finding 1 (Reviewer conf 92 / CQR conf 97) caught that `tester.yaml` line 35 would still read `Label all outputs: [Sonnet]` after the model was changed to Haiku. The fix was mandatory and correct, but the pattern that triggered the gap — label fields not updated alongside model field changes — is not currently documented as a rule. Adding this bullet prevents the same oversight in future agent model migrations.

**Status**: APPROVED
