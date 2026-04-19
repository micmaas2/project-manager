# Test Report — task-042: Model Version Pins Review and Update

[Haiku]

**Date**: 2026-04-19
**Tester**: BugHunter (Haiku)
**Task**: task-042 (BL-098)

---

## Test Results

### AC1: All pins audited across CLAUDE.md + all `.claude/agents/*.yaml`

**PASS**

Evidence — `grep -n "^model:" .claude/agents/*.yaml` output:

```
builder.yaml:2:      model: claude-sonnet-4-6
doc-updater.yaml:2:  model: claude-haiku-4-5-20251001
manager.yaml:2:      model: claude-opus-4-6
reviewer.yaml:2:     model: claude-sonnet-4-6
self-improver.yaml:2:model: claude-haiku-4-5-20251001
tester.yaml:2:       model: claude-haiku-4-5-20251001
```

All 6 agent YAMLs have explicit model fields. `decision.md` contains a pre-change audit table listing all 6 YAMLs plus both CLAUDE.md sections (Model Policy + Agent Roles table). Coverage is complete.

---

### AC2: Decision documented — explicit versions vs aliases, with rationale

**PASS**

`artefacts/task-042/decision.md` exists and contains:
- Explicit decision statement: "All model fields use explicit versioned IDs. No family aliases."
- Numbered rationale (4 points): no surprise upgrades, reproducibility, deliberate upgrades, current state already explicit.
- Additional rationale explaining why Opus/Sonnet lack date suffix while Haiku has `20251001`.
- Forward-looking consistency rule for new model fields.

Rationale is substantive and addresses the alias vs. explicit-pin tradeoff directly.

---

### AC3: All pins updated consistently

**PASS**

Post-change state verified:

| File | Model field | Tier | Consistent |
|------|-------------|------|------------|
| `manager.yaml` | `claude-opus-4-6` | Opus | ✓ |
| `builder.yaml` | `claude-sonnet-4-6` | Sonnet | ✓ |
| `reviewer.yaml` | `claude-sonnet-4-6` | Sonnet | ✓ |
| `tester.yaml` | `claude-haiku-4-5-20251001` | Haiku | ✓ |
| `doc-updater.yaml` | `claude-haiku-4-5-20251001` | Haiku | ✓ |
| `self-improver.yaml` | `claude-haiku-4-5-20251001` | Haiku | ✓ |

Confirmed: `grep -c "claude-sonnet-4-6" tester.yaml` → `0`. No residual Sonnet reference in tester.yaml.

tester.yaml Label line also updated: `Label all outputs: [Haiku]` (was `[Sonnet]`).

---

### AC4: M-1 mirror verified — CLAUDE.md model policy matches all agent YAML model fields

**PASS**

CLAUDE.md evidence (confirmed by file read):
- Line 90: `**Sonnet 4.6** — default for execution, building, reviewing` — matches builder.yaml and reviewer.yaml (`claude-sonnet-4-6`) ✓
- Line 91: `**Opus 4.6** — only for ProjectManager` — matches manager.yaml (`claude-opus-4-6`) ✓
- Line 92: `**Haiku 4.5** — DocUpdater, SelfImprover, revise-claude-md, Tester (BugHunter)` — matches tester.yaml, doc-updater.yaml, self-improver.yaml (`claude-haiku-4-5-20251001`) ✓
- Line 119 (Agent Roles table): `Tester (BugHunter) | YAML | Haiku` — matches tester.yaml ✓

`build_notes.md` states: **M-1 status: PASS** — 6/6 YAMLs match CLAUDE.md. No orphan entries.

Count check: 6 YAML model fields, 6 entries in M-1 verification table — counts are equal.

---

## Additional Regression Checks

Per CLAUDE.md M-1 pattern requirement, checked for removed rules:

- Sonnet bullet in CLAUDE.md: "testing" correctly removed from role list (was "building, testing, reviewing") — consistent with tester.yaml model change.
- Label bullet updated to include `[Haiku]` — all 3 tiers now covered.
- No orphan entries found: every agent referenced in CLAUDE.md policy has a corresponding YAML with matching tier.

---

## Overall Verdict

**PASS**

All 4 acceptance criteria met. Model pins are consistent, documented, and M-1 verified across all 6 agent YAMLs and CLAUDE.md.
