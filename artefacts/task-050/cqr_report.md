# Code Quality Review — task-050

**Reviewer**: code-quality-reviewer [Sonnet]
**Date**: 2026-04-29
**Scope**: lessons.md header update + self-improver.yaml output format update

---

## Critical Issues (Must Fix)

None.

---

## Major Issues (Should Fix)

### M-1: CLAUDE.md lessons format spec is stale — missing the two new columns

**Location**: `CLAUDE.md`, Task Queue & Resume section, line referencing lessons.md format:
```
- Lessons → `tasks/lessons.md` (append-only table: `| Date | Agent | Lesson | Applied To |`)
```

**Risk**: CLAUDE.md is the authoritative governance document read by ProjectManager and other agents at session start. The format string there is now 2 columns short of the actual table. Any agent (e.g. manager.yaml) that infers the schema from CLAUDE.md — or any operator auditing the file — will see a mismatched definition. This is a textbook M-1 mirror violation: a format defined in both CLAUDE.md and self-improver.yaml must be identical in both places.

**Fix**: Update the CLAUDE.md line to:
```
- Lessons → `tasks/lessons.md` (append-only table: `| Date | Agent | Lesson | Applied To | Confidence | Scope |`)
```

---

## Minor Issues (Consider Fixing)

### m-1: Confidence scale boundary (1=speculative) is asymmetric with the prose description

**Location**: `self-improver.yaml`, line 29:
```
- `Confidence`: integer 1-100 — how certain is this lesson applicable to future work? (1=speculative, 100=proven pattern)
```
And `build_notes.md` design notes define sub-ranges (90-100, 70-89, 50-69, 1-49) but these ranges do **not** appear in the YAML prompt.

**Risk**: The sub-range guidance that helps SelfImprover calibrate scores (i.e. what distinguishes a 75 from a 55) is documented in `build_notes.md` but not surfaced in the agent's own prompt. Future runs will use only the coarse `1=speculative, 100=proven` anchors, which is underspecified for consistent scoring across agents. This is not a correctness bug, but calibration will drift.

**Fix (optional)**: Add the sub-range table from build_notes.md directly into the self-improver.yaml field definition, e.g.:
```yaml
  - `Confidence`: integer 1-100 — how certain is this lesson applicable to future work?
    90-100: proven pattern (3+ tasks, same failure mode); 70-89: high (2+ occurrences or clear root cause);
    50-69: moderate (single occurrence, plausible generalization); 1-49: speculative (edge case, context-dependent)
```

### m-2: Existing lesson rows are missing the new columns — table is now structurally inconsistent

**Location**: `tasks/lessons.md`, all rows before this task's additions.

**Risk**: Markdown tables with ragged column counts render incorrectly in most Markdown viewers and break any tooling that parses lessons.md as structured data. The build_notes.md correctly notes this is "out of scope", but it should be explicitly flagged here so a follow-up task backfills the two new fields (even with placeholder values like `—` or `N/A`) before any tooling is built on top of lessons.md.

**Fix**: Queue a follow-up backlog item to backfill existing rows with `| — | — |` for the two new columns, or document the accepted inconsistency period explicitly in the task's Definition of Done.

### m-3: `Scope` field definition is free-text with no validation constraint

**Location**: `self-improver.yaml`, line 30:
```
- `Scope`: project scope this lesson applies to (e.g. "project_manager", "pi-homelab", "all projects", "all Builder tasks")
```

**Risk**: Free-text scope values will accumulate synonyms over time ("all Builder tasks" vs "all builders" vs "Builder"). This undermines any future filter/search on lessons.md by scope. Not blocking for now, but the format should note that values should prefer the canonical project names from CLAUDE.md's workspace table.

**Fix (optional)**: Add a parenthetical constraint: `(use canonical project names from the workspace table: project_manager, pi-homelab, pensieve, CCAS, performance_HPT, or "all projects" / "all Builder tasks" for cross-project lessons)`

---

## Positive Observations

- **Column order is consistent**: the format string in self-improver.yaml (`| ISO-date | Agent | Lesson | Applied To | Confidence | Scope |`) exactly matches the header row in lessons.md (`| Date | Agent | Lesson | Applied To | Confidence | Scope |`). No transposition errors.
- **YAML syntax is valid**: no indentation errors introduced; the block scalar (`prompt: |`) and inline bullet lists are correctly formatted.
- **Inline definitions are well-placed**: putting `Confidence` and `Scope` definitions immediately after the format line (lines 29-30) gives SelfImprover the definitions at the exact point of use — no forward reference needed.
- **No other agent YAML references the lessons.md column schema**: manager.yaml only reads lessons.md narratively (step 1, step 36) without enumerating columns, so there is no secondary M-1 exposure in the YAML layer. The only M-1 gap is in CLAUDE.md (see M-1 above).
- **Correct no-touch decision**: existing rows were left unmodified, avoiding unnecessary diff noise and schema-breaking retroactive edits during an in-flight pipeline.

---

## Summary

The task-050 changes are structurally sound and syntactically correct. The YAML prompt is valid, column order is consistent between the two modified files, and no other agent YAMLs introduce secondary M-1 exposures. One **major** issue requires a fix before closing: the lessons.md format string in CLAUDE.md is stale by two columns, which is a direct M-1 mirror violation. Two minor issues are advisory: the Confidence sub-range calibration table is buried in build_notes.md rather than the agent prompt, and existing lessons.md rows are now structurally ragged (missing the two new columns). The ragged rows should be tracked as a follow-up backlog item rather than blocking this task.

**Overall risk rating**: Low — one targeted CLAUDE.md line edit resolves the only blocking gap.
