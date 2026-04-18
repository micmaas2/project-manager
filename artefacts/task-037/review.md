# Review — task-037 CLAUDE.md Size Reduction

**Reviewer**: Reviewer agent (Sonnet)
**Date**: 2026-04-17
**Artefact path**: artefacts/task-037/

---

## Verdict: APPROVED — minor findings only (no Builder loop required)

All critical criteria pass. Two minor findings are noted below; both have confidence < 80 and are routed to build_notes.md only.

---

## Checklist Results

| Criterion | Result |
|---|---|
| File size ≤ 35,000 chars | PASS (29,784 chars) |
| `require_human_approval` present | PASS |
| `confidence: N (1-100)` present | PASS |
| `M-1 mirror` present | PASS |
| `pm-propose commit discipline` present | PASS |
| `BACKLOG: ` present | PASS |
| `allowed_tools` present | PASS |
| `audit_logging` present | PASS |
| `external_calls_allowed` present | PASS |
| `SelfImprover` present | PASS |
| `Artefact minimum for git-only tasks` present | PASS |
| n8n section pointer (`See docs/n8n-deployment.md`) | PASS |
| Python testing pointer (`See docs/python-testing.md`) | PASS |
| docs/n8n-deployment.md complete, not truncated | PASS |
| docs/python-testing.md complete, not truncated | PASS |
| n8n section retains 5 key operational rules | PASS |

---

## Finding 1 — M-1 verbatim mismatch (pre-existing, not introduced by task-037)

**description**: CLAUDE.md defines the confidence field as `confidence = certainty the finding is a real issue (not a false positive)`. reviewer.yaml uses `Represents certainty that the finding is a real issue (not a false positive)` (no `confidence =` prefix). builder.yaml uses a different structural form again. The M-1 contract states these must match verbatim, but this divergence pre-dates task-037 — the task preserved the existing state. Task-037 did not introduce or worsen this issue.

**severity**: minor (pre-existing, no regression introduced)

**confidence: 72 (1-100)**

*Routed to build_notes.md only — no Builder loop required.*

---

## Finding 2 — n8n-deployment.md omits `GitHub API commits (stdlib)` section from pointer coverage

**description**: CLAUDE.md line 375 retains the `GitHub API commits (stdlib)` rule inline in the n8n section, but docs/n8n-deployment.md line 22 also contains the same rule. This creates a minor duplication rather than a clean move. The inline copy in CLAUDE.md is not wrong (it is operational context), but the duplication could cause drift if either copy is updated independently.

**severity**: minor

**confidence: 60 (1-100)**

*Routed to build_notes.md only — no Builder loop required.*

---

## Summary

The task-037 Builder successfully reduced CLAUDE.md from 39,310 to 29,784 characters (a 24% reduction), with all required rules preserved, pointer lines in place, and both extracted docs complete. No critical or major findings. No Builder loop required.
