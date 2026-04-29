# Review — task-050
**Reviewer**: [Sonnet]
**Date**: 2026-04-29
**Task**: SelfImprover: add confidence score + project scope to lessons.md (BL-085)

---

## Acceptance Criteria Verification

### AC1: self-improver.yaml updated to output confidence + project_scope per lesson row
**PASS** — `.claude/agents/self-improver.yaml` line 28 now reads:
`Format: | ISO-date | Agent | Lesson | Applied To | Confidence | Scope |`
Field definitions for `Confidence` (lines 29–30) and `Scope` (lines 31–32) are present inline.

### AC2: lessons.md table schema updated with Confidence and Scope columns
**PASS** — `tasks/lessons.md` header row is:
`| Date | Agent | Lesson | Applied To | Confidence | Scope |`
Separator row is present and correctly extended.

### AC3: Format changes consistent between self-improver.yaml and lessons.md header
**PASS** — Both files use the same column order and labels. The YAML `Format:` template maps directly to the lessons.md header columns.

---

## Findings

## Finding 1
**Confidence**: 72 (advisory — does not require Builder loop)
**File**: `/opt/claude/project_manager/tasks/lessons.md`
**Issue**: Existing lesson rows (lines 7–onward) have no `Confidence` or `Scope` values. The separator row uses `|------------|-------|` for these columns but the existing data rows have only 4 pipe-separated fields, making the table malformed in any Markdown renderer that validates column count. Future SelfImprover runs appending well-formed 6-column rows will create a visual inconsistency, and tooling that parses the table by column index may silently misread values in the Confidence/Scope positions.
**Fix (advisory)**: Retroactively populate existing rows with `| - | - |` (unknown/legacy) placeholders to maintain table structural integrity. Build notes explicitly mark this out of scope for this task — acceptable to defer, but should be registered as a backlog item.

## Finding 2
**Confidence**: 55 (advisory — does not require Builder loop)
**File**: `/opt/claude/project_manager/.claude/agents/self-improver.yaml`
**Issue**: The `Scope` field definition says "project scope this lesson applies to (e.g. "project_manager", "pi-homelab", "all projects", "all Builder tasks")" but does not specify whether `all projects` is the preferred term when a lesson is truly global. Without a canonical "global" value, future SelfImprover runs may use heterogeneous strings (`all`, `all projects`, `global`, `*`) making grep-based filtering inconsistent.
**Fix (advisory)**: Add a note specifying the canonical string for global scope (e.g. `"all projects"` is the canonical form for cross-project lessons). Low urgency — current examples in build_notes.md already use `"all projects"`.

## Finding 3
**Confidence**: 48 (advisory — does not require Builder loop)
**File**: `/opt/claude/project_manager/.claude/agents/self-improver.yaml`
**Issue**: The `Confidence` field definition (`integer 1-100`) does not specify how SelfImprover should handle uncertainty — i.e., what score to default to when there is insufficient signal. The build_notes.md includes a useful scoring rubric (90-100 / 70-89 / 50-69 / 1-49) but this rubric was NOT added to the YAML prompt. SelfImprover will only see its own prompt at runtime, not build_notes.md, so the rubric is effectively invisible.
**Fix (advisory)**: Move the rubric from build_notes.md into the YAML `Confidence` field definition. This would improve consistency of scores across runs. Low priority — field is usable without a rubric.

---

## Summary

All three acceptance criteria pass. No high-confidence (≥80) findings. Three advisory findings are noted:

| # | Confidence | Nature | Action |
|---|------------|--------|--------|
| 1 | 72 | Existing rows lack Confidence/Scope — table structurally malformed | Defer to backlog |
| 2 | 55 | No canonical "global scope" string defined | Minor improvement |
| 3 | 48 | Confidence scoring rubric missing from YAML prompt | Minor improvement |

---

## Verdict: APPROVED

The Builder's changes are correct, consistent, and minimal in scope. The format is aligned between self-improver.yaml and lessons.md. Advisory findings 1–3 do not block approval and are noted for the SelfImprover and/or future backlog items.
