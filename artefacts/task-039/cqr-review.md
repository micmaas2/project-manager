# Code Quality Review — task-039 Cost-Aware Model Routing Design

**Reviewer**: code-quality-reviewer (built-in, Sonnet)  
**Date**: 2026-04-18  
**Files reviewed**:
- `artefacts/task-039/design-doc.md`
- `artefacts/task-039/claude-md-additions.md`
**Reference files read**: `CLAUDE.md` (Model Policy + Agent Roles sections), `.claude/agents/tester.yaml`, all agent YAMLs

---

## Findings

---

### CRITICAL — Finding 1: Cost calculation for Tester downgrade uses wrong input/output split

**confidence: 95**

The design-doc claims:

> Current: Sonnet (no cache) — $0.054/run  
> Proposed: Haiku (no cache) — $0.014/run

Both figures use a single "5,000 tokens/run estimate" without specifying an input/output split. At the given prices:

- Sonnet: $3.00/M input + $15.00/M output
- Haiku: $0.80/M input + $4.00/M output

For 5,000 tokens split 50/50 (2,500 in / 2,500 out):
- Sonnet: (2,500 × $3.00 + 2,500 × $15.00) / 1,000,000 = $0.0075 + $0.0375 = **$0.045/run**
- Haiku:  (2,500 × $0.80 + 2,500 × $4.00) / 1,000,000 = $0.002 + $0.010 = **$0.012/run**

The stated $0.054 (Sonnet) and $0.014 (Haiku) don't match either a 50/50 or 40/60 split cleanly. The design-doc does not show the split assumption, making the figures unverifiable and potentially misleading. The direction (Haiku is cheaper) and order of magnitude are correct, but the exact numbers and the "18.5% pipeline cost reduction" claim rest on an undisclosed assumption. The rollback trigger ("monitor first 5 runs for test_report quality regression") is sound, but the cost justification should show the split.

**Fix**: Add a footnote to the cost delta table stating the assumed input/output token ratio (e.g. 60% input / 40% output). Recalculate both rows and re-derive the pipeline percentage from actual total pipeline cost, not just the Tester row delta vs the Tester row baseline.

---

### CRITICAL — Finding 2: M-1 mirror violation — tester.yaml `Label all outputs` line is not updated in the proposal

**confidence: 97**

`tester.yaml` line 35 currently reads:

```
Label all outputs: [Sonnet]
```

The proposed change (claude-md-additions.md Addition 3 and design-doc Finding 1) changes the Tester model to Haiku. The `Label all outputs` directive in the prompt must be updated to `[Haiku]` at the same time — the M-1 mirror rule requires both files to remain consistent, and the label is part of the observable contract (audit trail, token log entries).

The proposal explicitly notes "this table change must also be reflected in `tester.yaml` (`model: claude-haiku-4-5-20251001`)" but makes no mention of updating the label line. This is a silent M-1 gap that will produce mislabelled outputs after the change.

**Fix**: Add to claude-md-additions.md Addition 3 (and any implementation task): also change `Label all outputs: [Sonnet]` → `Label all outputs: [Haiku]` in `tester.yaml`.

---

### MAJOR — Finding 3: Prompt caching threshold stated correctly but cache discount wording is ambiguous

**confidence: 88**

The design-doc and claude-md-additions.md both state:

> Anthropic automatically caches system prompts ≥1,024 tokens (90% input discount).

The 1,024-token minimum is correct. The "90% input discount" phrasing is accurate as shorthand (cache read price = 10% of base input price = 90% cheaper), but it can be misread as "you pay 10% of the total cost" vs "you pay 10% of the input-token cost only — output tokens are unchanged". A future agent reading the CLAUDE.md addition and trying to estimate costs could under-estimate the per-run cost if they apply 90% discount to total tokens rather than only the cached input portion.

**Fix**: Tighten the wording to: "90% discount on cached input tokens only (output tokens billed at standard rate)".

---

### MAJOR — Finding 4: CLAUDE.md Model Policy line 90 explicitly names Tester as Sonnet — proposed addition does not remove or update that line

**confidence: 96**

Current CLAUDE.md line 90:

```
- **Sonnet 4.6** — default for execution, building, testing, reviewing (80–90% of work)
```

The word "testing" here implicitly assigns Tester to Sonnet. After the proposed change, Tester moves to Haiku, making this line factually incorrect — "testing" would no longer be a Sonnet-tier activity. The proposed additions update only the Agent Roles table row and add new threshold bullets, but do not update this existing definitional line.

Similarly, the Haiku line (current line 92) reads:

```
- **Haiku 4.5** — DocUpdater, SelfImprover, revise-claude-md, and any agent doing templated/structured work
```

After the change, "Tester (BugHunter)" should be appended to this enumeration.

**Fix**: In claude-md-additions.md, add two more edits:
1. Remove "testing" from the Sonnet bullet.
2. Append "Tester (BugHunter)" to the Haiku bullet's named-agent list.

---

### MAJOR — Finding 5: Architect and Security agents absent from coverage

**confidence: 85**

The design-doc's "Current Model Assignments" table lists 6 agents but the pipeline has 8 YAML agents (Manager, Architect, Security, Builder, Reviewer, Tester, DocUpdater, SelfImprover) plus 3 built-ins (code-quality-reviewer, docs-readme-writer, revise-claude-md). The design-doc explicitly acknowledges 6 agents but the Agent Roles table in CLAUDE.md lists Architect and Security separately.

- **Architect (Opus)** — not mentioned in the design-doc; the CLAUDE.md model policy assigns it Opus ("Architect (design)"). No token estimate or caching eligibility assessment is provided.
- **Security (Sonnet)** — also absent. No assessment of whether its prompt is long enough to benefit from caching or whether its Sonnet assignment is appropriate.
- **Built-in agents** — code-quality-reviewer and docs-readme-writer are listed in the Agent Roles table with model assignments (Sonnet and Haiku respectively) but are not covered in the cost analysis. Their token consumption is unlogged (token_log.jsonl entries come from YAML agents only per CLAUDE.md line 359).

This is not a blocking issue for the Tester downgrade finding, but the design-doc's "Finding 3: All Other Assignments Correct" claim is overstated — it only validates the 6 agents that were analysed.

**Fix**: Either scope the claim explicitly ("all analysed agents") or add a brief one-line assessment for Architect, Security, and the three built-ins.

---

### MINOR — Finding 6: "No external deps" and "Privacy DPIA" fields absent from the design artefact

**confidence: 72**

The CLAUDE.md MVP template (used for every task) requires fields including `privacy_dpia`, `cost_estimate`, `rollback_plan`, and `incident_owner`. The design-doc provides a rollback note inline for the Tester change and a cost estimate, but does not explicitly fill these template fields. This is a documentation completeness issue, not a runtime risk. The artefact is a research/design doc rather than a task definition, so partial omission is tolerable — but it means the corresponding queue.json entry's `mvp_template` may be thin.

**Fix**: No action required on the design-doc itself. Ensure the queue.json `mvp_template` block for task-039 carries `privacy_dpia: "no — internal config change only"` and `incident_owner` before marking done.

---

### MINOR — Finding 7: Complexity threshold token ranges have a gap and an inconsistency with CLAUDE.md

**confidence: 78**

The proposed CLAUDE.md Addition 1 defines:
- Haiku: "prompt ≤500 tokens"
- Sonnet: "prompt 500–2,000 tokens"
- Opus: "prompt >2,000 tokens"

Two issues:
1. "≤500" and "500–2,000" creates an ambiguous boundary exactly at 500. Should be "≤500" / ">500 and ≤2,000" / ">2,000", or use half-open intervals consistently.
2. The existing CLAUDE.md already states "Prompt > 2,000 tokens" as an Opus trigger (in the design-doc's own threshold table, section "Use Opus when"). The proposed addition should use identical wording to avoid a paraphrase M-1 conflict — the M-1 copy-paste rule requires verbatim matching when mirroring definitions.

**Fix**: Use `>500` for the Sonnet lower bound. Copy the Opus trigger wording verbatim from the design-doc's threshold table into the proposed CLAUDE.md addition.

---

## Positive Observations

- The caching threshold (1,024 tokens) is stated correctly against Anthropic's published minimum.
- The 90% cache discount figure is correct (cache read = $0.30/M for Sonnet vs $3.00/M base input).
- The M-1 awareness in claude-md-additions.md Addition 3 — explicitly calling out that the table change requires a tester.yaml change — demonstrates correct cross-file consistency thinking. The gap (label line) is an omission of one specific item, not a failure to understand the pattern.
- The Opus Advisor escalation path confirmation (Finding 3 in the design-doc) is correct and adds useful documentation value.
- The rollback plan for the Tester downgrade is concise and actionable (1-line revert, 5-run monitoring window).
- The prioritized action plan table (P1/P2/P3) with effort and savings columns is well-structured and immediately actionable.

---

## Summary

The research direction is sound: Tester is a reasonable Haiku candidate and ProjectManager caching is a free win. However, **two issues must be resolved before implementation**:

1. (Finding 2, confidence 97) The `tester.yaml` label line `[Sonnet]` → `[Haiku]` is missing from the proposal — this will produce mislabelled audit trail outputs if not fixed alongside the model field change.
2. (Finding 4, confidence 96) The Sonnet and Haiku definitional bullets in CLAUDE.md Model Policy are not updated — after the change, CLAUDE.md will internally contradict itself (line 90 still says "testing" is Sonnet; the Agent Roles table will say Haiku).

Finding 1 (cost calculation transparency) should be addressed before presenting the savings figures to stakeholders, but does not block the downgrade.

Findings 3 and 5 are informational quality improvements.

**Overall risk rating: Medium** — the proposed changes are low-risk operationally, but the two M-1/consistency gaps would introduce silent document drift if applied as-is.
