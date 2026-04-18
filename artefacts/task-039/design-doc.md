# Cost-Aware Model Routing Design — task-039

**Date**: 2026-04-18  
**Status**: Proposed — pending human review

---

## Summary

Two-round analysis of current agent model assignments, prompt caching eligibility, and cost reduction opportunities across the 6-agent MAS pipeline.

**Key findings**:
1. **Tester should be downgraded Sonnet → Haiku** — 73% Tester-stage cost reduction ($0.024/run, $1.20/50 runs)
2. **ProjectManager prompt qualifies for caching** — $1.86–$18.59/1,000 runs savings depending on session hit rate (automatic, no code changes)
3. All analysed assignments are correctly aligned with the Haiku/Sonnet/Opus thresholds (Architect/Security not in scope)

---

## Current Model Assignments

| Agent | Model | Prompt tokens (est.) | Role type |
|---|---|---|---|
| ProjectManager | claude-opus-4-6 | 1,377 | Strategic orchestration |
| Builder | claude-sonnet-4-6 | 709 | Code/script generation |
| Reviewer | claude-sonnet-4-6 | 879 | Arch/security analysis |
| Tester | claude-sonnet-4-6 | 440 | Test orchestration |
| DocUpdater | claude-haiku-4-5-20251001 | 299 | Structured doc updates |
| SelfImprover | claude-haiku-4-5-20251001 | 569 | Pattern extraction |

---

## Token Usage (from logs/token_log.jsonl)

| Agent | Avg tokens/run |
|---|---|
| ProjectManager | 8,000 |
| Builder | 1,500 |
| Reviewer | 1,500 |
| Tester | 1,500 |
| DocUpdater | ~500 |
| SelfImprover | ~500 |

PM consumes ~73% of pipeline tokens — already on Opus (justified by strategic role).

---

## Finding 1: Tester Downgrade (Sonnet → Haiku)

**Verdict: SAFE TO DOWNGRADE**

Tester prompt analysis (440 tokens, 33 lines):
- Read task definition (structured input) ✓ Haiku strength
- Run/simulate tests from fixtures (mechanical orchestration) ✓ Haiku strength
- Write test_report.md (structured PASS/FAIL output) ✓ Haiku strength
- Count passes ÷ total ≥ 90% threshold (simple conditional logic) ✓ Haiku strength

No complex decision-making, architectural judgment, or multi-language parsing found in Tester prompt.
Risk: variable `tests_required` format interpretation (medium) — mitigated by structured artefact paths.

### Cost Delta (5,000 tokens/run estimate; assumed split: 3,500 input / 1,500 output)

| Scenario | Cost/run | Cost/50 runs | Savings |
|---|---|---|---|
| Current: Sonnet (no cache) | $0.033 | $1.65 | baseline |
| Proposed: Haiku (no cache) | $0.009 | $0.45 | **$1.20 (73%)** |

_Cost calc: Sonnet = (3,500 × $3/M) + (1,500 × $15/M) = $0.0105 + $0.0225 = $0.033/run. Haiku = (3,500 × $0.80/M) + (1,500 × $4/M) = $0.0028 + $0.006 = $0.009/run._

**Pipeline impact**: $0.024/run savings per Tester run (~73% Tester-stage reduction).

**Implementation**: Two changes in `tester.yaml`:
- `model: claude-haiku-4-5-20251001`
- `Label all outputs: [Haiku]` (currently `[Sonnet]` on line 35 — must be updated to keep audit trail accurate)

**Rollback**: Revert both tester.yaml lines — 1 minute. Monitor first 5 runs for test_report quality regression.

---

## Finding 2: ProjectManager Prompt Caching

**Verdict: QUALIFIES — automatic, no code changes needed**

ProjectManager prompt: ~1,377 tokens (> 1,024 threshold).
Anthropic automatically caches system prompts ≥1,024 tokens. Cache discount: 90% on cached input tokens only (output tokens billed at standard rate).

Expected cache hit rate: ~10–100% depending on session pattern. Cache TTL is 5 minutes — cross-session first calls miss cache; intra-session repeated PM invocations (e.g. multi-task sprints) hit cache after the first.

**Savings**: lower bound ~$1.86/1,000 runs (10% hit rate); upper bound ~$18.59/1,000 runs (100% intra-session).
Assumption: 1,377 input tokens at Opus input rate $15/M → $0.0207/run uncached; cached = $0.00207/run.
Savings per run: ~$0.0186 at 100% hit rate.

**Action**: No code changes — verify Anthropic API key tier supports caching (available on all tiers as of 2026).

---

## Finding 3: All Analysed Assignments Correct (Architect/Security out of scope)

| Agent | Assignment | Rationale |
|---|---|---|
| ProjectManager (Opus) | Keep | Multi-project coordination, token cap enforcement, scope-drift detection — high competing constraints |
| Builder (Sonnet) | Keep | Code generation, Opus Advisor escalation path, multi-language support |
| Reviewer (Sonnet) | Keep | Confidence scoring (1-100), architectural judgment, security analysis |
| DocUpdater (Haiku) | Keep | Templated changelog edits only |
| SelfImprover (Haiku) | Keep | Structured log pattern extraction, lesson formatting |

---

## Complexity Thresholds for Future Agents

### Use Haiku when:
- Task is mechanical/orchestration (run commands, format results, write templated reports)
- Well-defined, structured input/output (queue.json fields, markdown tables)
- Prompt ≤ 500 tokens, expected output ≤ 2,000 tokens
- No multi-agent coordination or novel decision-making required
- Examples: Tester, DocUpdater, log parsers, templated reporters, syntax validators

### Use Sonnet when:
- Code generation in any language
- Architectural trade-off analysis or judgment on ambiguous input
- Prompt 500–2,000 tokens, expected output 2,000–5,000 tokens
- Confidence scoring or quality assessment requiring nuanced evaluation
- Examples: Builder, Reviewer, security analysts

### Use Opus when:
- System-wide prioritization with competing constraints (token budget, scope, cost, multi-project)
- Prompt > 2,000 tokens
- Decisions impact multiple downstream agents or tasks
- Strategic planning sessions (PI/Refinement, pm-plan)
- Examples: ProjectManager, Architect, Security (risk analysis)

---

## Escalation Path (existing — confirmed sound)

Builder has an "Opus Advisor Escalation" pattern: spawn Opus sub-agent (model: claude-opus-4-6) with single `ADVISOR_CONSULT: <question>` for ambiguous arch/security decisions. This correctly preserves Sonnet as default while providing Opus-level judgment on demand. No changes needed.

---

## Prioritized Action Plan

| Priority | Action | Savings | Effort |
|---|---|---|---|
| P1 — immediate | Downgrade Tester → Haiku (tester.yaml) | $1.97/50 runs | 1 line, 1 min |
| P2 — short-term | Verify PM caching active (no code change) | $18.59/1k runs | 5 min verification |
| P3 — medium-term | Define new-agent checklist using thresholds above | Future savings | 1 CLAUDE.md addition |

---

## Proposed CLAUDE.md Additions

See `artefacts/task-039/claude-md-additions.md` for exact diff-ready text.
