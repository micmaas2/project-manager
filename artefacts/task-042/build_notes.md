# Build Notes — task-042: Model Version Pins Review and Update

[Sonnet]

## What was built and why

Audited all model version pins across CLAUDE.md and 6 agent YAMLs. Applied a consistent explicit-pin strategy and propagated the Tester→Haiku decision from task-039/040.

## Actions taken

### 1. Audit (read-only)
- Read all 6 `.claude/agents/*.yaml` files
- Read CLAUDE.md Model Policy section (lines 88–103) and Agent Roles table (lines 111–122)
- Read `artefacts/task-039/claude-md-additions.md` for exact CLAUDE.md changes

### 2. Pin strategy decision
- **Decision: explicit version pins** (see `decision.md` for full rationale)
- No family aliases anywhere; Opus/Sonnet use short explicit IDs; Haiku uses date-pinned ID

### 3. tester.yaml — 2 changes
- Line 2: `model: claude-sonnet-4-6` → `model: claude-haiku-4-5-20251001`
- Line 35: `Label all outputs: [Sonnet]` → `Label all outputs: [Haiku]`

### 4. CLAUDE.md — Model Policy section — 4 changes from task-039 + 1 consistency fix
- **Sonnet bullet**: removed "testing" from role list (was "building, testing, reviewing" → now "building, reviewing")
- **Haiku bullet**: added "Tester (BugHunter)" to named agents list
- **Pattern line**: updated to "Haiku documents and tests" (from "Haiku documents")
- **Added** complexity threshold bullet (3 sub-items: Haiku/Sonnet/Opus thresholds)
- **Added** prompt caching note (discount scope, qualification threshold, no-code-changes note)
- **Label bullet**: updated from `[Sonnet]` or `[Opus]` → `[Sonnet]`, `[Opus]`, or `[Haiku]` (consistency — Haiku agents label outputs too)

### 5. CLAUDE.md — Agent Roles table — 1 change
- Tester row: `Sonnet` → `Haiku`

## Files changed
- `/opt/claude/project_manager/.claude/agents/tester.yaml`
- `/opt/claude/project_manager/CLAUDE.md`

## M-1 Verification result

All 6 YAML model fields now match CLAUDE.md policy bullets:

| YAML file | model field | CLAUDE.md tier |
|-----------|-------------|----------------|
| manager.yaml | claude-opus-4-6 | Opus 4.6 ✓ |
| builder.yaml | claude-sonnet-4-6 | Sonnet 4.6 ✓ |
| reviewer.yaml | claude-sonnet-4-6 | Sonnet 4.6 ✓ |
| tester.yaml | claude-haiku-4-5-20251001 | Haiku 4.5 ✓ |
| doc-updater.yaml | claude-haiku-4-5-20251001 | Haiku 4.5 ✓ |
| self-improver.yaml | claude-haiku-4-5-20251001 | Haiku 4.5 ✓ |

**M-1 status: PASS** — 6/6 YAMLs match CLAUDE.md. No orphan entries.

Agent Roles table Tester row: `Haiku` — matches tester.yaml `claude-haiku-4-5-20251001` ✓

Label line consistency: all 3 tiers (Sonnet/Opus/Haiku) now referenced in the Label bullet ✓

## Assumptions made

- No Architect or Security YAML exists (only referenced in CLAUDE.md as planned agents — not yet created). If created, they must use `claude-opus-4-6` and `claude-sonnet-4-6` respectively per policy.
- The `claude-haiku-4-5-20251001` date pin is authoritative for Haiku 4.5 — no newer patch build requires a different ID.

## Known limitations

- Architect and Security YAMLs do not exist yet. When created, their model pins must be verified against this policy.
- Task-039's Addition 3 specified updating the Label bullet; the original CLAUDE.md only listed `[Sonnet]` or `[Opus]`. The Label bullet update adds `[Haiku]` — this is consistent with Haiku agents already labelling their outputs in doc-updater.yaml and self-improver.yaml.
