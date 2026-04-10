# /pm-propose — End-of-Session Proposal Review

Collect, deduplicate, present, and apply improvement proposals. Run at session end.

## Steps

**1. Find pending proposals**
Run: `find artefacts -name "improvement_proposals.md"` to get the list of files.
For each file in that list: read it and collect all `## Proposal N` sections where Status = `REQUIRES_HUMAN_APPROVAL`.
Do NOT use `grep -r` or `grep -rl` across the whole artefacts directory — test files may contain the string as an assertion and produce false positives.

**2. Deduplicate**
For each collected proposal:
- Read the target file named in **Target file**. If the proposed Change text already appears verbatim in that file: skip this proposal (already applied).
- Read tasks/lessons.md. If the same lesson is already present: skip.
Remove duplicate proposals (same change targeting the same file) — keep only one.

**3. Present**
Renumber the remaining proposals sequentially (1, 2, 3, …). For each print:
- Target file
- Change (summary or diff)
- Rationale

**4. Await user response**
Wait for user reply in format: `APPROVE: 1, 3 / REJECT: 2` (numbers refer to the sequential list above).

**5. Apply approved**
For each approved proposal number:
- Edit the target file as specified in Change.
- Update the proposal's Status line from `REQUIRES_HUMAN_APPROVAL` to `APPROVED` in its improvement_proposals.md file.

**6. Log rejections**
For each rejected proposal number:
- Append a row to tasks/lessons.md: `| <today's date> | SelfImprover | Proposal rejected: <rationale> | <target file> |`
- Update the proposal's Status line to `REJECTED: <reason from user or "user rejected">`.

**7. Bake learnings**
After all proposals are resolved: invoke the revise-claude-md built-in agent (subagent_type: claude-md-management:revise-claude-md) to apply session learnings to CLAUDE.md.
