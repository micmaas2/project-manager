# task-058 Build Notes

## [Sonnet] Builder

### Approach

Three sections migrated to linked docs:

1. **Shell presubmit** → `docs/shell-presubmit.md` (new file, 5,360 bytes)
   — Builder pre-submission checklist with 16 bullet points migrated verbatim.

2. **MVP template security sub-bullets** → `docs/mvp-template-checklist.md` (new file, 2,572 bytes)
   — 28-line Security/arch impact conditions from inside the template code block.

3. **n8n Pi4 operational notes** → appended to `docs/n8n-deployment.md` (existing file extended)
   — 9 Pi4 operational notes; already had a `See docs/n8n-deployment.md` pointer, extended to cover new topics.

### Size Calculation

| Step | Bytes |
|---|---|
| Starting size | 47,409 |
| Shell presubmit removed | −5,336 |
| MVP security sub-bullets removed | −2,423 |
| n8n Pi4 notes removed | −2,254 |
| Pointer lines added | +556 |
| Final size | 37,952 |

### Design Decisions

- MVP template `Security/arch impact:` heading line and `<note>` placeholder retained in CLAUDE.md — only the sub-bullets migrated. This preserves the template structure.
- DoD and cost estimate sub-bullets inside the template code block were NOT migrated — they are actively checked per-task and must remain visible in-line.
- n8n section header, SSH alias, and PAT path lines retained in CLAUDE.md — only the detailed operational notes moved to the existing deployment doc.

### Token Log

```json
{"timestamp": "2026-05-03T11:30:00+00:00", "agent": "builder", "task_id": "task-058", "token_estimate": 4000}
```
