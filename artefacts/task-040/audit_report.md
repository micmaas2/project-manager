# Agent Model Usage Audit — task-040

**Date**: 2026-04-18  
**Status**: Final — all agents audited across 2 rounds  
**Scope**: All `.claude/agents/*.yaml`, built-in subagents, ad-hoc model references in CLAUDE.md and PM skills

---

## Agent YAML Inventory

| Agent | YAML file | Model | Label | Assignment verdict |
|---|---|---|---|---|
| ProjectManager | manager.yaml | claude-opus-4-6 | [Opus] | ✅ Appropriate |
| Builder | builder.yaml | claude-sonnet-4-6 | [Sonnet] | ✅ Appropriate |
| Reviewer | reviewer.yaml | claude-sonnet-4-6 | [Sonnet] | ✅ Appropriate — do NOT downgrade |
| **Tester** | tester.yaml | claude-sonnet-4-6 | [Sonnet] | ⚠️ **Could downgrade → Haiku** |
| DocUpdater | doc-updater.yaml | claude-haiku-4-5-20251001 | [Haiku] | ✅ Appropriate |
| SelfImprover | self-improver.yaml | claude-haiku-4-5-20251001 | [Haiku] | ✅ Appropriate |

---

## Built-In Subagent Inventory

| Agent | Invocation | Model (per CLAUDE.md) | Assignment verdict |
|---|---|---|---|
| code-quality-reviewer | `Agent(subagent_type=code-quality-reviewer)` | Sonnet | ✅ Appropriate — security/quality analysis |
| docs-readme-writer | `Agent(subagent_type=docs-readme-writer)` | Haiku | ✅ Appropriate — templated doc writes |
| revise-claude-md | `Skill(skill=claude-md-management:revise-claude-md)` | Haiku | ✅ Appropriate — structured CLAUDE.md edits |
| claude-md-improver | `Skill(skill=claude-md-management:claude-md-improver)` | Haiku | ✅ Appropriate — templated audit |

**Note**: Built-in subagent models are fixed by type — no `model` parameter override exists on the `Agent` tool.

---

## Ad-Hoc Model References

| Location | Reference | Model | Context |
|---|---|---|---|
| builder.yaml (lines 44–53) | Opus Advisor Escalation | claude-opus-4-6 | Fallback for ambiguous arch/security decisions |
| reviewer.yaml (line 88) | Opus Advisor Escalation | claude-opus-4-6 | Same escalation pattern |
| CLAUDE.md (line 140) | Opus Advisor Escalation | claude-opus-4-6 | Policy definition — M-1 source |

**Verdict**: Escalation pattern is consistent across all 3 locations. Opus is appropriate for one-off strategic advisor calls — not a cost concern since it's rarely triggered.

**No model references found in PM skill files** (pm-run.md, pm-start.md, pm-plan.md, pm-propose.md, pm-close.md). Skills delegate model selection to agent YAML definitions entirely.

---

## Downgrade Opportunities

### ✅ Opportunity 1: Tester (Sonnet → Haiku) — RECOMMENDED

**Rationale**: Tester prompt is 440 tokens (33 lines). Task is mechanical orchestration:
- Read task definition → structured input
- Run/simulate tests from fixtures → templated execution
- Write test_report.md (PASS/FAIL) → structured output
- No confidence scoring, architectural judgment, or multi-agent coordination

**Cost delta** (1,500 tokens/run actual; 70% input / 30% output split):
| Scenario | Cost/run | Cost/50 runs | Savings |
|---|---|---|---|
| Current: Sonnet | $0.0099 | $0.495 | baseline |
| Proposed: Haiku | $0.0027 | $0.135 | **$0.360 (73%)** |

**Pipeline impact**: $0.0066/run savings (1.98% of full $0.3323 pipeline cost)

**Correction vs task-039**: task-039 estimated savings at $0.024/run (based on assumed 5,000 tokens). Actual token_log.jsonl data shows 1,500 tokens/run → savings are $0.0066/run. Direction unchanged; magnitude revised downward.

**Implementation** (2 lines in tester.yaml):
```yaml
model: claude-haiku-4-5-20251001
# ...
Label all outputs: [Haiku]   # currently [Sonnet] — must update for audit trail accuracy
```

**Rollback**: revert both lines — 1 minute. Monitor 5 runs.

---

### ❌ Not Recommended: Reviewer (Sonnet → Haiku)

The Reviewer's job requires:
1. **Confidence scoring (1-100)** — calibrated certainty that findings are real issues (drives Builder loop decisions)
2. **Security analysis** — 6 dimensions: secrets, permissions, privilege escalation, code execution, path traversal, input validation
3. **Architectural judgment** — scope boundary decisions, pattern recognition across files
4. **Out-of-scope distinction** — requires holding task spec + artefact in parallel

Haiku risk: miscalibrated confidence scores lead to wasted Builder cycles (false loop on 85-confidence non-issue) or missed defects (real vulnerability scored at 40, ignored). Security assessment depth is materially lower for multi-dimensional analysis.

**Verdict**: Keep Reviewer on Sonnet. CLAUDE.md policy already correctly classifies this.

---

### ❌ Not Recommended: Reviewer (ProjectManager Opus → Sonnet)

ProjectManager orchestrates multi-project priority, token cap enforcement, scope-drift detection, epic/story assignment, and plan-mode decisions. These are competing-constraint optimisation problems across sessions — exactly the Opus use case. Downgrading to Sonnet risks scope drift, mis-prioritization of P1 vs P2 tasks, and incorrect MVP gating decisions. Not justified at current usage volumes.

---

## Housekeeping Finding: Haiku Version String Inconsistency

| Location | Value |
|---|---|
| doc-updater.yaml (line 2) | `claude-haiku-4-5-20251001` (date-pinned) |
| self-improver.yaml (line 2) | `claude-haiku-4-5-20251001` (date-pinned) |
| CLAUDE.md model policy | `Haiku 4.5` (generic, no pin) |

The `20251001` date suffix is current (no newer Haiku 4.5.x patch as of knowledge cutoff). The inconsistency is a documentation clarity gap — CLAUDE.md policy should note the pinning strategy: "Haiku agents use pinned date-stamped version (`claude-haiku-4-5-20251001`) for stability; update YAMLs when a newer Haiku 4.5 patch is released."

This is a minor housekeeping item — no operational impact.

---

## Full Pipeline Cost Baseline

| Agent | Tokens | Model | Cost/run |
|---|---|---|---|
| ProjectManager | 8,000 | Opus | $0.2640 |
| Builder | 1,500 | Sonnet | $0.0099 |
| Reviewer | 1,500 | Sonnet | $0.0099 |
| Tester | 1,500 | Sonnet → Haiku | $0.0099 → $0.0026 |
| DocUpdater | 500 | Haiku | $0.0009 |
| SelfImprover | 500 | Haiku | $0.0009 |
| **Total (current)** | 13,000 | — | **$0.2955** |
| **Total (Tester→Haiku)** | 13,000 | — | **$0.2882** |
| **Delta** | — | — | **-$0.0073 (-2.5%)** |

_Cost calc: 70% input / 30% output split. Haiku: $0.80/M input, $4.00/M output. Sonnet: $3.00/M, $15.00/M. Opus: $15.00/M, $75.00/M._
_Tester Haiku: (1,050 × $0.80/M) + (450 × $4.00/M) = $0.00084 + $0.00180 = $0.0026/run._

**Observation**: ProjectManager (Opus) accounts for **89.3%** of total pipeline cost ($0.264 of $0.2955). The largest cost lever is PM token efficiency, not model swaps on cheaper agents. Future optimisation should focus on PM prompt compression and prompt caching (task-039 P2: $1.86–$18.59/1k runs at current cache hit rates).

---

## Prioritised Recommendations

| Priority | Action | Savings/run | Effort | Task |
|---|---|---|---|---|
| **P1** | Downgrade Tester → Haiku (2 YAML lines) | $0.0066 | 2 min | Apply in task-042 (model version review) |
| **P2** | Verify PM prompt caching active | $0.019 upper bound | 5 min verify | task-039 P2 |
| **P3** | Add Haiku pinning strategy note to CLAUDE.md | Housekeeping | 1 line | task-042 |
