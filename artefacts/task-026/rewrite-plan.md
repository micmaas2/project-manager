# Token Reduction Rewrite Plan
**Task**: task-026 — BL-049
**Agent**: Builder [Sonnet]
**Date**: 2026-04-14
**Method**: character-count / 4 ≈ Claude tokens (±10%)

---

## 1. Current Token Inventory

### CLAUDE.md (8,815 tokens total)

| Section | Current Tokens | % of Total |
|---------|---------------|------------|
| n8n Workflow Deployment (Pi4) | 2,066 | 23% |
| Workflow Orchestration | 1,940 | 22% |
| Agent Roles & Spawn Order | 1,722 | 20% |
| Git Branching Strategy | 694 | 8% |
| MVP Phases & Scope Discipline | 674 | 8% |
| Task Queue & Resume | 637 | 7% |
| Workspace Context | 358 | 4% |
| Governance, Security & Observability | 247 | 3% |
| Model Policy (Token Governance) | 222 | 3% |
| CI/CD & Release | 110 | 1% |
| Project Goal | 58 | 1% |
| **TOTAL** | **8,815** | |

### Agent YAMLs (4,794 tokens total)

| File | Total Tokens | Prompt Tokens | Prompt % |
|------|-------------|--------------|----------|
| manager.yaml | 1,523 | 1,448 | 95% |
| reviewer.yaml | 993 | 893 | 89% |
| builder.yaml | 738 | 645 | 87% |
| self-improver.yaml | 605 | 529 | 87% |
| tester.yaml | 544 | 456 | 83% |
| doc-updater.yaml | 391 | 315 | 80% |
| **TOTAL** | **4,794** | **3,886** | |

### Grand Total
| Source | Current | Target | Reduction |
|--------|---------|--------|-----------|
| CLAUDE.md | 8,815 | ~7,060 | ~1,755 (-20%) |
| Agent YAMLs | 4,794 | ~4,450 | ~344 (-7%) |
| **Grand total** | **13,609** | **~11,510** | **~2,099 (-15%)** |

---

## 2. Top-5 Sections by Reduction Potential

### Rank 1 — n8n Workflow Deployment (Pi4)
**Current**: 2,066 tokens | **Target**: ~1,450 | **Reduction**: ~616 tokens (30%)

**Why it's bloated**: This section conflates three concerns — n8n operational gotchas, Python testing patterns (which apply to *all* projects), and GitHub API usage. It also contains two near-duplicate entries for hyphenated filenames.

**Specific rewrites**:

| # | Location | Issue | Strategy | Est. Saving |
|---|----------|-------|----------|-------------|
| 1a | Lines 27–30 (hyphenated filenames) | Two bullets say identical thing | Merge into one bullet; drop the "Hyphenated script filenames" header, keep "Testing hyphenated-filename scripts" | ~50 tokens |
| 1b | Lines 32–36 (Testing Docker-only packages) | 5-step prose procedure | Condense to 2 lines: pattern name + `sys.modules` pre-injection + canonical example reference | ~80 tokens |
| 1c | Line 38 (Task unit tests) | "test files live in artefacts/..." duplicates queue schema | Delete — already in Task Queue schema and known from artefact layout | ~30 tokens |
| 1d | Lines 42 (GitHub API stdlib) | Long one-liner with full API path templates | Trim to: pattern + 1 example; remove duplicate "No requests needed" | ~40 tokens |
| 1e | Lines 54–61 (Import gotchas) | Credential IDs bullet is 3 lines inline | Break into 2-line bullet + "Patch with Python before import" | ~100 tokens |
| 1f | Lines 27–42 (Python testing block) | Pi4-specific section holds general testing rules | **Move** to new `## Python Testing Patterns` section (no token saving, improves navigation + search surface) | 0 (structural) |
| 1g | Line 63 (Pending deployments) | Will become stale; single item | Convert to a TODO comment in deploy-notes.md; delete from CLAUDE.md once deployed | ~25 tokens |
| 1h | Line 9 (dashboard-preview.md cron) | Long explanation of cron behaviour already in pm-start.md | Shorten to 1 line: "dashboard-preview.md: cron-updated every 15 min — commit on feature branch before pm-close" | ~50 tokens |

**Total estimated saving**: ~375 tokens after structural move

---

### Rank 2 — Workflow Orchestration
**Current**: 1,940 tokens | **Target**: ~1,630 | **Reduction**: ~310 tokens (16%)

**Why it's bloated**: Step 6b is a single paragraph containing 8 embedded rules that are hard to scan. The Telegram inbox promotion procedure (step 0, item 2) is duplicated verbatim in `pm-start.md`.

**Specific rewrites**:

| # | Location | Issue | Strategy | Est. Saving |
|---|----------|-------|----------|-------------|
| 2a | Step 0 item 2 (Telegram inbox) | Full procedure duplicated in pm-start.md | Replace with: "Promote any items below the header in `origin/main:tasks/telegram-inbox.md` to backlog (see `/pm-start`)" | ~100 tokens |
| 2b | Step 6b (entire block) | 8 rules in one 150-word sentence | Extract into a bulleted sub-list; does not reduce tokens but eliminates parsing burden | ~0 tokens (readability) |
| 2c | Step 6b scanning pattern | The `find … xargs grep` command is 40+ words | Keep command; shorten surrounding prose to 1 sentence | ~50 tokens |
| 2d | Task tracking file list | 8-item list with format definitions inline | Move improvement_proposals.md format into the SelfImprover section (or agent YAML); reference from here | ~60 tokens |
| 2e | "PM Planning Session" paragraph (after step 10) | Duplicates manager.yaml Planning Session Mode | Reduce to 1 sentence pointer | ~50 tokens |

**Total estimated saving**: ~260 tokens

---

### Rank 3 — Agent Roles & Spawn Order
**Current**: 1,722 tokens | **Target**: ~1,460 | **Reduction**: ~262 tokens (15%)

**Why it's bloated**: The PM Skills table duplicates the skills themselves; the policy schema YAML block is enforced by the hook but still occupies 11 lines; the Opus advisor escalation block covers a rarely-triggered edge case at length.

**Specific rewrites**:

| # | Location | Issue | Strategy | Est. Saving |
|---|----------|-------|----------|-------------|
| 3a | PM Skills table (8 rows) | Duplicates `.claude/commands/*.md` headers | Replace with 1 line: "PM Skills (`.claude/commands/`): `/pm-start` `/pm-run` `/pm-status` `/pm-plan` `/pm-propose` `/pm-close` `/pm-lessons`" | ~100 tokens |
| 3b | Opus advisor escalation (7 lines) | Already in reviewer.yaml and manager.yaml | Condense to 2 lines: "For ambiguous arch/security decisions: spawn Opus sub-agent, single ADVISOR_CONSULT question, note in build_notes.md under 'Advisor Consults'." | ~80 tokens |
| 3c | Policy schema YAML block (11 lines) | Enforced by hook; also in every agent YAML | Replace with 1 line: "Policy schema: 5 required fields — `allowed_tools`, `max_tokens_per_run`, `require_human_approval`, `audit_logging`, `external_calls_allowed`." | ~60 tokens |
| 3d | Plugin marketplace line | Single sentence — keep as-is | No change | 0 |

**Total estimated saving**: ~240 tokens

---

### Rank 4 — Git Branching Strategy
**Current**: 694 tokens | **Target**: ~560 | **Reduction**: ~134 tokens (19%)

**Why it's bloated**: The merge-conflict resolution pattern (9 steps) is verbose. The "force-with-lease" divergence explanation has a 3-step procedure embedded in prose.

**Specific rewrites**:

| # | Location | Issue | Strategy | Est. Saving |
|---|----------|-------|----------|-------------|
| 4a | Merge conflict pattern (numbered list) | 5-step procedure with explanatory prose | Keep numbered steps; strip explanation prose — steps are self-documenting | ~60 tokens |
| 4b | "Releasing to main" note | Explains hook bypass twice (prose + code comment) | Keep code block; remove prose duplication | ~40 tokens |
| 4c | `git stash` warning | 2 lines for a negative example | Reduce to: "Avoid `git stash` when branches have diverged — cascading conflicts." | ~30 tokens |

**Total estimated saving**: ~130 tokens

---

### Rank 5 — manager.yaml prompt
**Current**: 1,448 tokens | **Target**: ~1,290 | **Reduction**: ~158 tokens (11%)

**Why it's bloated**: Multi-Project Priority Order (5 lines) partially duplicates queue sort logic; Token Log format is a single-line JSON that could be referenced rather than repeated.

**Specific rewrites**:

| # | Location | Issue | Strategy | Est. Saving |
|---|----------|-------|----------|-------------|
| 5a | Multi-Project Priority Order (5 lines) | Duplicates queue.json sort documented in CLAUDE.md | Reduce to: "Priority: paused → project_manager tasks → P1 > P2 > P3 → oldest created." | ~40 tokens |
| 5b | Token Log + Audit Log format blocks | Both contain full JSON templates | Reference format from CLAUDE.md: "Log format: see CLAUDE.md §Logs." | ~60 tokens |
| 5c | Onboarding Scan step 3 note (warning) | "Never overwrite or discard existing project state" is implicit from step 5 (register, not replace) | Delete — implied by workflow | ~15 tokens |
| 5d | reviewer.yaml: Opus Advisor block (9 lines) | Already in manager.yaml and CLAUDE.md | Condense to 3 lines matching manager.yaml pattern | ~60 tokens |

**Total estimated saving**: ~175 tokens (manager + reviewer)

---

## 3. Aggregate Before/After Table

| Target | Before | After | Reduction | % |
|--------|--------|-------|-----------|---|
| CLAUDE.md § n8n | 2,066 | ~1,450 | ~616 | 30% |
| CLAUDE.md § Workflow Orchestration | 1,940 | ~1,630 | ~310 | 16% |
| CLAUDE.md § Agent Roles | 1,722 | ~1,460 | ~262 | 15% |
| CLAUDE.md § Git Branching | 694 | ~560 | ~134 | 19% |
| manager.yaml prompt | 1,448 | ~1,290 | ~158 | 11% |
| reviewer.yaml prompt | 893 | ~833 | ~60 | 7% |
| **Total** | **8,763** | **~7,223** | **~1,540** | **18%** |

---

## 4. Semantic Preservation Checklist

Before committing any rewrite, verify each item:
- [ ] All rules still present (count before vs after per section)
- [ ] All canonical example references preserved (artefact paths, file names)
- [ ] All security rules intact (path guard, prompt sanitization, SSRF blocks)
- [ ] All M-1 mirrored rules consistent across CLAUDE.md ↔ agent YAMLs
- [ ] All structural "STOP" points in agent prompts unchanged
- [ ] Token count improvement confirmed by re-running analysis script

---

## 5. Implementation Order (recommended)

1. **n8n section** — highest absolute saving; structural move of Python testing block
2. **Agent Roles section** — PM Skills table + policy schema reduction; low risk
3. **manager.yaml** — log format blocks + priority order
4. **Workflow Orchestration** — Telegram inbox dedup; risk: pm-start.md must be authoritative
5. **Git Branching** — prose trimming only; low risk, last

Each rewrite should be a separate commit on a feature branch with a regression check (rule count before/after).

---

## 6. Out of Scope

- Rewriting agent behaviour or logic
- Changing any security rule content
- Modifying queue.json schema
- Any changes to `.claude/commands/*.md` skills
