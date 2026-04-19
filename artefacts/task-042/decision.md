# Decision: Model Version Pin Strategy — task-042

[Sonnet]

## Decision: Explicit Version Pins (no family aliases)

**All model fields use explicit versioned IDs.** No family aliases (e.g. `claude-sonnet`, `claude-haiku`) anywhere.

---

## Audit — Pre-change state

| File | Model field | Status |
|------|-------------|--------|
| `manager.yaml` | `claude-opus-4-6` | Explicit, no date pin — OK |
| `builder.yaml` | `claude-sonnet-4-6` | Explicit, no date pin — OK |
| `reviewer.yaml` | `claude-sonnet-4-6` | Explicit, no date pin — OK |
| `tester.yaml` | `claude-sonnet-4-6` | **Needs update → Haiku** |
| `doc-updater.yaml` | `claude-haiku-4-5-20251001` | Explicit with date pin — OK |
| `self-improver.yaml` | `claude-haiku-4-5-20251001` | Explicit with date pin — OK |
| `CLAUDE.md` Model Policy | "Sonnet 4.6", "Opus 4.6", "Haiku 4.5" | Family names only — no pin notes |
| `CLAUDE.md` Agent table | Tester row: "Sonnet" | **Needs update → Haiku** |

---

## Rationale for Explicit Version Pins

**Stability wins.** The codebase is an active MAS (multi-agent system) where behaviour consistency matters:

1. **No surprise upgrades**: Anthropic silently updates aliases (e.g. `claude-sonnet` → latest minor). A mid-sprint upgrade can change confidence scoring, output format, or reasoning style — breaking M-1 mirror invariants or the 90% Tester pass threshold.

2. **Reproducibility**: Audit logs record `task_id → agent → action`. Without pinned versions, reproducing a past run's behaviour is impossible even with identical prompts.

3. **Deliberate upgrades**: Explicit pins mean version upgrades are a conscious commit, visible in git history. This is the correct governance model for a system that runs autonomously.

4. **Current state already explicit**: All six YAMLs already use explicit IDs. The decision documents and locks the existing practice.

**Why not date-pin Opus and Sonnet** (unlike Haiku's `claude-haiku-4-5-20251001`)?

The Haiku date pin (`20251001`) was introduced because multiple Haiku 4.5 builds existed at the time. Opus 4.6 and Sonnet 4.6 currently have single authoritative builds — adding a date suffix would add noise without benefit. If Anthropic releases a patch build that requires pinning, update then.

**Consistency rule going forward**: when adding or updating a model field, use the most specific ID available from the Anthropic API reference at that time. Do not use family aliases.

---

## Changes Applied

### tester.yaml
- `model:` changed from `claude-sonnet-4-6` → `claude-haiku-4-5-20251001`
- `Label all outputs:` changed from `[Sonnet]` → `[Haiku]`

### CLAUDE.md — Model Policy section
- **Sonnet bullet**: removed "testing" from role list
- **Haiku bullet**: added `Tester (BugHunter)` to named agents list
- **Added** complexity threshold bullet (from task-039)
- **Added** prompt caching note (from task-039)
- **Added** label bullet updated: `[Sonnet]`, `[Opus]`, or `[Haiku]` (was `[Sonnet]` or `[Opus]` only)

### CLAUDE.md — Agent Roles table
- Tester row: `Sonnet` → `Haiku`

---

## M-1 Mirror Verification

After changes:

| CLAUDE.md model policy bullet | Matching YAML `model:` field |
|-------------------------------|------------------------------|
| "Sonnet 4.6 — building, reviewing" | builder.yaml: `claude-sonnet-4-6` ✓ |
| "Sonnet 4.6 — building, reviewing" | reviewer.yaml: `claude-sonnet-4-6` ✓ |
| "Opus 4.6 — ProjectManager" | manager.yaml: `claude-opus-4-6` ✓ |
| "Haiku 4.5 — DocUpdater, SelfImprover, revise-claude-md, Tester" | doc-updater.yaml: `claude-haiku-4-5-20251001` ✓ |
| "Haiku 4.5 — DocUpdater, SelfImprover, revise-claude-md, Tester" | self-improver.yaml: `claude-haiku-4-5-20251001` ✓ |
| "Haiku 4.5 — DocUpdater, SelfImprover, revise-claude-md, Tester" | tester.yaml: `claude-haiku-4-5-20251001` ✓ |
| Agent table: Tester → Haiku | tester.yaml: `claude-haiku-4-5-20251001` ✓ |

**Count**: 6 YAMLs × 1 model field = 6 pins. All 6 match CLAUDE.md policy bullets. M-1 PASS.
