# Test Report — task-040: Agent Model Usage Audit (BL-099)

**[Haiku]**  
**Date**: 2026-04-19  
**Tester**: BugHunter (Tester agent)  
**Artefact under test**: `artefacts/task-040/audit_report.md`

---

## Acceptance Criteria Results

| # | Criterion | Verdict | Evidence |
|---|-----------|---------|----------|
| AC1 | All `.claude/agents/*.yaml` reviewed; current model listed per agent | **PASS** | See detail below |
| AC2 | Each assignment rated: appropriate / could-downgrade / must-upgrade with rationale | **PASS** | See detail below |
| AC3 | Estimated token-cost savings per downgrade opportunity | **PASS** | See detail below |
| AC4 | Findings committed as markdown report at `artefacts/task-040/audit_report.md` | **PASS** | File exists at expected path |

---

## AC1 — YAML Inventory Coverage

**Method**: Glob `.claude/agents/*.yaml` → 6 files found. Cross-checked each against the audit report inventory table.

| YAML file | Actual model (from file) | Reported model (audit_report.md) | Match |
|-----------|--------------------------|----------------------------------|-------|
| manager.yaml | `claude-opus-4-6` | `claude-opus-4-6` | ✅ |
| builder.yaml | `claude-sonnet-4-6` | `claude-sonnet-4-6` | ✅ |
| reviewer.yaml | `claude-sonnet-4-6` | `claude-sonnet-4-6` | ✅ |
| tester.yaml | `claude-sonnet-4-6` | `claude-sonnet-4-6` | ✅ |
| doc-updater.yaml | `claude-haiku-4-5-20251001` | `claude-haiku-4-5-20251001` | ✅ |
| self-improver.yaml | `claude-haiku-4-5-20251001` | `claude-haiku-4-5-20251001` | ✅ |

All 6 YAML files present in report; all model values verified accurate. **AC1: PASS**

---

## AC2 — Assignment Verdicts with Rationale

Each of the 6 YAML agents has a verdict in the inventory table:

| Agent | Verdict | Rationale present |
|-------|---------|-------------------|
| ProjectManager | Appropriate | Yes — multi-project priority, competing-constraint optimisation |
| Builder | Appropriate | Yes — implicit (Sonnet execution role per policy) |
| Reviewer | Appropriate — do NOT downgrade | Yes — confidence scoring, security analysis, architectural judgment |
| Tester | Could downgrade → Haiku | Yes — mechanical orchestration, structured output, no judgment required |
| DocUpdater | Appropriate | Yes — templated doc writes |
| SelfImprover | Appropriate | Yes — structured CLAUDE.md edits |

Additional "not recommended" verdicts are provided for Reviewer→Haiku and PM→Sonnet downgrades, each with detailed rationale. **AC2: PASS**

---

## AC3 — Cost Savings Estimates for Downgrade Opportunities

One downgrade opportunity identified: **Tester (Sonnet → Haiku)**

Savings data present in report:

| Metric | Value |
|--------|-------|
| Savings per run | $0.0066 |
| Savings per 50 runs | $0.360 (73%) |
| Pipeline impact | 1.98% of full pipeline cost |
| Correction note | Revised down from task-039 estimate ($0.024/run → $0.0066/run) with actual token_log.jsonl data |

Cost methodology documented (70/30 input/output split, Haiku/Sonnet/Opus rates). Full pipeline baseline table included. **AC3: PASS**

---

## AC4 — Report File Exists at Expected Path

`artefacts/task-040/audit_report.md` confirmed present via `ls artefacts/task-040/`. Directory also contains `review.md` and `cqr-review.md` from Reviewer stage. **AC4: PASS**

---

## Additional Observations (informational, not blocking)

1. **Built-in subagent inventory**: The report covers 4 built-in subagents (code-quality-reviewer, docs-readme-writer, revise-claude-md, claude-md-improver) beyond the 6 YAMLs — thoroughness beyond minimum AC1 scope.
2. **Haiku version string inconsistency**: Housekeeping finding noted (doc-updater.yaml / self-improver.yaml use `claude-haiku-4-5-20251001`; CLAUDE.md policy says `Haiku 4.5`). Actionable — P3 recommendation to add pinning strategy note.
3. **No model references in PM skill files**: Verified explicitly; clean finding.

---

## Overall Verdict

**PASS**

All 4 acceptance criteria met. The audit report is accurate, complete, and internally consistent. One actionable downgrade recommendation (Tester→Haiku, P1, $0.0066/run savings) with rollback plan documented.
