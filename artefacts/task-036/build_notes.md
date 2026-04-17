# Build Notes: task-036

## What was built
Added confidence scoring (1-100) to the Reviewer agent output format, and wired the threshold
into Builder so it only loops on findings with confidence ≥ 80.

## Files changed
- `.claude/agents/reviewer.yaml` — findings format extended with `confidence: N` field + threshold rules
- `.claude/agents/builder.yaml` — new "Reviewer Confidence Threshold" section added
- `CLAUDE.md` — "Reviewer confidence scoring" note added above Built-in Claude Code agents section

## M-1 consistency verification
All three files define the same threshold (≥80 loop / <80 build_notes only) and the same
confidence semantics (certainty of real defect, 1-100 scale). reviewer.yaml is the canonical
source; CLAUDE.md and builder.yaml mirror it.

## Assumptions
- Confidence is a subjective score the Reviewer assigns at write time; no formula enforced.
- "loop" means Builder must fix the finding before re-submitting; logged-only findings may be
  addressed at Builder's discretion.

## How to test
1. Run a Reviewer invocation on a task with known findings — verify review.md includes
   `confidence: N` on each finding line.
2. Invoke Builder with a mixed set of findings (some ≥80, some <80) — verify only ≥80 findings
   trigger a fix loop; <80 findings appear in build_notes.md under "Low-confidence Findings".

## Known limitations
- No automated enforcement — relies on Reviewer and Builder agents following their prompts.
- Confidence values are subjective; calibration improves over time via lessons.md.
