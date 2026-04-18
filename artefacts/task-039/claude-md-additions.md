# Proposed CLAUDE.md Additions — task-039

These additions extend the existing "Model Policy" section in CLAUDE.md. Insert after the current `**Default to Haiku**` line.

---

## Addition 1: Complexity Thresholds

Insert after `**Default to Haiku** for any agent that does not require reasoning over complex context`:

```
**Complexity thresholds for model selection**:
- Haiku: mechanical/orchestration tasks; structured input/output; prompt ≤500 tokens; no trade-off analysis
- Sonnet: code generation; architectural judgment; confidence scoring; prompt 500–2,000 tokens
- Opus: system-wide prioritization with competing constraints; prompt >2,000 tokens; decisions affecting multiple downstream agents
```

---

## Addition 2: Prompt Caching Note

Insert after the complexity thresholds:

```
**Prompt caching**: Anthropic automatically caches system prompts ≥1,024 tokens (90% discount on cached input tokens only; output tokens billed at standard rate). ProjectManager qualifies (~1,377 tokens). No code changes required — verify API tier supports caching before first production run.
```

---

## Addition 3: Tester Model Assignment (update existing table + model policy bullets)

In the Agent Roles & Spawn Order table, change the Tester row:

```
| Tester (BugHunter) | YAML | ~~Sonnet~~ **Haiku** | Tests/regression | 90% pass |
```

In the Model Policy section, update the Sonnet and Haiku bullets:
- Sonnet bullet: remove "testing" from the role list (`80–90% of work` — building, reviewing, **not** testing)
- Haiku bullet: append `Tester (BugHunter)` to the named agents list

**`tester.yaml` changes required** (two lines):
- `model: claude-haiku-4-5-20251001`
- `Label all outputs: [Haiku]` (line 35 — currently says `[Sonnet]`)

---

## Summary of changes to CLAUDE.md

1. Add complexity threshold bullet points under Model Policy
2. Add prompt caching note (with corrected discount scope wording) under Model Policy  
3. Update Tester row model from `Sonnet` → `Haiku` in Agent Roles table
4. Update Sonnet bullet: remove "testing"; update Haiku bullet: add Tester
5. Update `tester.yaml`: model field + label line (separate file changes)
