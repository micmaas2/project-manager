# Review — task-039: Cost-Aware Model Routing Design

**Reviewer**: Reviewer agent (Sonnet)  
**Date**: 2026-04-18  
**Artefacts reviewed**:
- `artefacts/task-039/design-doc.md`
- `artefacts/task-039/claude-md-additions.md`

---

## Verdict: CONDITIONAL PASS

The design doc is substantively sound and covers the key findings clearly. Three findings require Builder attention before this can be fully approved; one finding is mandatory (confidence ≥80), two are advisory.

---

## Acceptance Criteria Assessment

### AC1: Threshold criteria with concrete examples per agent type — PASS

The design doc defines three tiers (Haiku / Sonnet / Opus) with explicit criteria (prompt size bands, task type descriptors) and per-agent examples. Each agent in the current pipeline is mapped to a tier with rationale. The thresholds in `design-doc.md` and `claude-md-additions.md` are consistent with each other.

### AC2: Prompt caching approach documented — PARTIAL PASS

Caching is documented for ProjectManager (the largest prompt, ~1,377 tokens). However the analysis does not address the other agents that may also qualify:
- Builder prompt: 709 tokens — below the 1,024 threshold (correctly excluded)
- Reviewer prompt: 879 tokens — below threshold (correctly excluded)
- SelfImprover prompt: 569 tokens (correctly excluded)

No agent other than PM exceeds the threshold, so the analysis is correct by omission — but this is not stated explicitly. A sentence confirming "no other agent prompt exceeds 1,024 tokens" would close the gap.

**Cache hit rate caveat** (advisory): The claim of "~100% hit rate after first invocation per session" is accurate for within-session calls but does not note the 5-minute cache TTL. For PM invocations more than 5 minutes apart (cross-session or multi-step planning), the hit rate will be lower. The stated savings figure ($18.59/1,000 runs) is therefore an upper bound, not a conservative estimate.

### AC3: Estimated cost savings quantified — PASS

Savings are expressed in absolute ($) and percentage terms per scenario. Both P1 (Tester downgrade) and P2 (PM caching) are quantified separately. Methodology (input/output split, per-token pricing assumptions) is implied but not stated — for auditability a footnote with the pricing constants used would strengthen this, but is not blocking.

### AC4: CLAUDE.md additions reviewable — PASS WITH CAVEAT

The proposed additions in `claude-md-additions.md` are clear and insertion-point specific. One inconsistency requires fixing (see Finding 1 below).

---

## Findings

### Finding 1 — MANDATORY (confidence: 92)

**Inconsistency: tester.yaml `Label all outputs` tag not updated**

`claude-md-additions.md` proposes updating the Tester row in the Agent Roles table from Sonnet → Haiku, and updating `tester.yaml` model field. However, `tester.yaml` line 35 reads:

```
Label all outputs: [Sonnet]
```

If the model is changed to Haiku, this label becomes incorrect — outputs will still be tagged `[Sonnet]` but the model will be `claude-haiku-4-5-20251001`. The `claude-md-additions.md` does not mention this line.

**Required fix**: `claude-md-additions.md` (and/or `tester.yaml` when the change is applied) must update the label to `[Haiku]`.

---

### Finding 2 — MANDATORY (confidence: 85)

**Cache TTL not acknowledged — savings figure is an upper bound**

The PM caching savings of ~$18.59/1,000 runs assumes ~100% cache hit rate. The Anthropic prompt cache TTL is 5 minutes. Cross-session PM invocations (the common case) will incur full input pricing on the first call of each session. The doc states "~100% after first invocation per session" but a planning session involving multiple PM invocations spaced more than 5 minutes apart will miss cache repeatedly.

The savings figure should be presented as an upper bound with a realistic lower bound (e.g. assume 1 cached call per 3-call PM session = ~33% hit rate → $6/1,000 runs). Overstating savings could lead to incorrect prioritization.

**Required fix**: Add a note to Finding 2 in `design-doc.md` acknowledging the 5-minute TTL and revising the savings to a range (lower/upper bound).

---

### Finding 3 — ADVISORY (confidence: 65)

**Prompt size bands in CLAUDE.md addition are ambiguous at boundary**

The complexity thresholds addition proposes:
- Haiku: prompt ≤500 tokens
- Sonnet: prompt 500–2,000 tokens
- Opus: prompt >2,000 tokens

The boundary at exactly 500 tokens is covered by both Haiku and Sonnet criteria (≤500 and 500–2,000). This is ambiguous. Recommend `<500` / `500–2,000` or explicitly note "at 500 tokens, default to Haiku unless task type warrants Sonnet."

Not blocking, but a clean rule set is less likely to produce inconsistent future model assignments.

---

### Finding 4 — ADVISORY (confidence: 60)

**No monitoring/regression plan for Tester downgrade**

The doc notes "Monitor first 5 runs for test_report quality regression" in the rollback section, but does not define what constitutes a quality regression for Tester output. Since Tester writes structured PASS/FAIL reports, a simple check would be: does test_report.md parse correctly, and is pass% calculated correctly? Without specifying the regression signal, monitoring guidance is vague.

Not blocking — the rollback itself (revert tester.yaml, 1 minute) is adequate.

---

## Summary

| Finding | Confidence | Action required |
|---|---|---|
| F1: tester.yaml label not updated | 92 | Mandatory — Builder must fix |
| F2: cache TTL not acknowledged, savings overstated | 85 | Mandatory — Builder must fix |
| F3: boundary ambiguity at 500-token threshold | 65 | Advisory — build_notes.md only |
| F4: no regression signal for Tester monitoring | 60 | Advisory — build_notes.md only |

**Mandatory fixes (≥80 confidence)**: F1 and F2.  
After those are resolved, this design doc is approved for implementation.
