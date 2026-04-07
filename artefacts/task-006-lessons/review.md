# Review — task-006: PM reads lessons.md at session start (S-002-3)

**Agent**: Builder (Sonnet 4.6)
**Date**: 2026-04-07
**Verdict**: APPROVED

---

## Changes Reviewed

| File | Change |
|---|---|
| `CLAUDE.md` | Added step 0b — lessons-read as mandatory session start action |
| `CLAUDE.md` | Documented lessons.md format in Task tracking section |
| `tasks/queue.json` | Updated task-006 artefact_path to `artefacts/task-006-lessons/` to avoid conflict with pre-existing Activity Dashboard artefacts |

---

## Checklist

### Correctness
- [x] Step 0b inserted after step 0 (Telegram inbox) and before step 1 (Plan first) — correct position in workflow
- [x] Instructs reading of `tasks/lessons.md` at session start
- [x] Specifies surfacing 3 most recent rows — concrete and actionable
- [x] Skip-if-missing guard present — safe for empty or absent file
- [x] Lessons.md format documented in Task tracking section: `| Date | Agent | Lesson | Applied To |`
- [x] artefact_path conflict resolved (Activity Dashboard was in task-006/, now lessons task uses task-006-lessons/)

### Scope compliance
- [x] No automated lesson application — strictly read + surface, human uses the context
- [x] No changes to agent YAMLs
- [x] No changes to queue/backlog schema
- [x] Touches only what was strictly necessary (2 lines in CLAUDE.md, 1 field in queue.json)

### Security
- [x] No security impact — read-only workflow documentation change

---

## Verdict

**APPROVED** — minimal, correct change. Step 0b is well-placed, concrete, and safe.
