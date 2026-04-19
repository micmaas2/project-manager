# Review — task-040: Agent Model Usage Audit

**Reviewer**: Reviewer agent [Sonnet]  
**Date**: 2026-04-18  
**Artefact reviewed**: `artefacts/task-040/audit_report.md`  
**Verdict**: CONDITIONAL PASS — 2 findings require correction before task is marked done

---

## Acceptance Criteria Check

| Criterion | Status | Notes |
|---|---|---|
| 1. All `.claude/agents/*.yaml` reviewed; current model listed per agent | ✅ PASS | All 6 YAML agents listed with correct model strings (verified against source files) |
| 2. Each assignment rated: appropriate / could-downgrade / must-upgrade with rationale | ✅ PASS | All 6 agents rated; 2 rejections include counter-rationale |
| 3. Estimated token-cost savings per downgrade opportunity quantified | ⚠️ PARTIAL | Savings direction correct; two internal numeric inconsistencies found (findings below) |
| 4. Findings committed as markdown report in artefact | ✅ PASS | Report present at `artefacts/task-040/audit_report.md` |

---

## Findings

### Finding 1 — Pipeline Total Cost Incorrect (arithmetic error)
**confidence: 95**

The pipeline cost table states:

| Agent | Cost/run |
|---|---|
| ProjectManager | $0.2640 |
| Builder | $0.0099 |
| Reviewer | $0.0099 |
| Tester | $0.0099 |
| DocUpdater | $0.0009 |
| SelfImprover | $0.0009 |
| **Total (current)** | **$0.3323** |

The actual sum of the six table rows is **$0.2955**, not $0.3323. The discrepancy is $0.0368. This error propagates to the "Total (Tester→Haiku)" and "Delta" rows and to the percentage statement "1.98% of full $0.3323 pipeline cost." The stated percentage (1.98%) is also slightly off — at the corrected total of $0.2955, the $0.0066 savings represents 2.23%.

**Required fix**: Replace $0.3323 with $0.2955, $0.3257 with $0.2889, and recalculate the percentage claim.

---

### Finding 2 — Internal Inconsistency in Haiku Cost Figures
**confidence: 88**

The report states Haiku cost/run = **$0.0027** in the per-scenario table, but reports savings of **$0.0066/run**. These two numbers are mutually inconsistent:

- If Haiku = $0.0027 → savings = $0.0099 − $0.0027 = **$0.0072** (not $0.0066)
- If savings = $0.0066 → implied Haiku cost = $0.0099 − $0.0066 = **$0.0033** (not $0.0027)

The actual Haiku cost at official pricing ($0.80/M input, $4.00/M output, 70/30 split, 1500 tokens) is **$0.0026**, giving savings of **$0.0073/run**.

The report appears to have applied two different Haiku price assumptions in different sections. The direction and recommendation remain sound; only the numeric precision is affected.

**Required fix**: Standardise on one Haiku cost value. Using official pricing: Haiku = $0.0026/run, savings = $0.0073/run (73.7%). Update both the scenario table and the savings figure consistently.

---

## Non-Blocking Observations

### Observation A — Tester prompt complexity higher than "mechanical orchestration"
**confidence: 55**

The audit characterises the Tester as doing "mechanical orchestration." The Tester YAML (50 lines) includes: interpreting `review.md` findings, determining which failures to pass back to Builder with actionable notes, judging edge-case adequacy, and deciding PASS/FAIL threshold application. These involve moderate contextual judgment. The downgrade to Haiku is still likely appropriate (the 90% threshold and structured PASS/FAIL output dominate), but the rationale slightly undersells the complexity. This is a wording concern only — it does not change the recommendation.

**No change required.** Builder may optionally strengthen the rationale in the report.

### Observation B — Tester `require_human_approval: true` not discussed
**confidence: 45**

The Tester policy sets `require_human_approval: true` because it executes Bash. A Haiku-class agent still needs this gate. The report does not note whether Haiku handles Bash policy enforcement correctly — but this is a deployment concern for task-042, not an audit concern for task-040.

**No change required.**

### Observation C — Haiku version string inconsistency finding is correct
**confidence: 90**

Verified: `doc-updater.yaml` and `self-improver.yaml` both use `claude-haiku-4-5-20251001`; CLAUDE.md says `Haiku 4.5` (no pin). The report's housekeeping finding and recommended one-line CLAUDE.md update are accurate. The recommendation to add a pinning strategy note is valid.

**No change required here** — the fix is correctly deferred to task-042.

---

## Summary

The report correctly identifies all 6 agents, produces sound ratings, and the strategic recommendation (Tester → Haiku) is well-supported. Two arithmetic errors require correction before the artefact is considered final: the pipeline total ($0.3323 should be $0.2955) and the internally inconsistent Haiku cost/savings figures. Both are in the cost section only — conclusions and ratings are unaffected.

**Builder action required**: Fix Finding 1 and Finding 2 in `artefacts/task-040/audit_report.md`, then resubmit for review sign-off.
