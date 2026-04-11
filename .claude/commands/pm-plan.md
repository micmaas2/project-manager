# /pm-plan — PI/Refinement Planning Session

Guide the user through a repeatable planning session: review epics and stories, prioritize backlog items, draft MVP templates, and commit a sprint plan to queue.json.

Run in order. Do not skip steps. Await explicit user confirmation before committing anything to queue.json.

---

## Steps

**1. Fetch state**
Run `git fetch origin`.
Read the following files to build current state — read them in this order:
- `tasks/epics.md` — epics, stories, and their statuses
- `tasks/backlog.md` — all BL-NNN items with priority and status columns
- `tasks/queue.json` — active queue: find the highest numeric task ID by scanning all `"id"` fields (format: `"task-NNN"`); the next task ID = that number + 1, zero-padded to three digits (e.g. task-014)
- `tasks/lessons.md` — read last 5 rows; surface any lessons that are relevant to prioritization or MVP design decisions

**2. Report current state**
Display a concise summary:

```
## EPIC-003 — <title from epics.md>  [<status>]

| Story ID | Title | Status |
|---|---|---|
<rows from epics.md for the in_progress epic>

## Backlog — prioritizable items
| ID | Title | Project | Priority | Status |
|---|---|---|---|---|
<rows from backlog.md where status is NOT done, blocked-manual, blocked-ssh, or archived>
```

Do not truncate or omit any rows. If all backlog items are done/blocked, state that explicitly.

**3. Ask for planning intent**
Ask the user:
> "Which backlog items do you want to plan for this sprint? List IDs (e.g. BL-009, BL-031) or say 'suggest' to get a ranked recommendation."

If the user says **"suggest"**: rank items from the filtered backlog by (a) P1 before P2 before P3, then (b) project dependencies (items that unblock other items first), then (c) oldest added date. Present the top 5 with a one-line rationale for each. Wait for user confirmation of which items to proceed with.

If the user lists IDs: verify each ID exists in backlog.md (column 1). If any ID is not found: report the missing ID and stop — do not proceed until corrected.

**4. Draft MVP templates**
For each confirmed backlog item, draft an MVP template. Populate each field using this mapping:

| Field | Source |
|---|---|
| `doel` | Derive a one-sentence goal from the BL item title (column 3 of backlog.md) + project context; ask user to confirm if ambiguous |
| `niet_in_scope` | List obvious exclusions based on the title; ask user to add/remove |
| `acceptatiecriteria` | Draft 2–4 measurable acceptance criteria; present to user for approval |
| `security_arch_impact` | Apply MVP template checklist from CLAUDE.md §MVP template: outbound HTTP, path construction, LLM output, YAML interpolation, external IDs |
| `tests_required` | Describe test type (unit/integration/regression) and what each test covers |
| `definition_of_done` | Always include: "review.md contains APPROVED", "test_report.md contains PASS"; add task-specific items |
| `rollback_plan` | Describe rollback steps and who owns them |
| `incident_owner` | Default: "Michel Maas" unless user specifies otherwise |
| `privacy_dpia` | Ask: does this task process personal data? If yes, note what data, scope, and safeguards |
| `cost_estimate` | Ask user; default "EUR 0" for pure-code tasks with no API spend |
| `prerequisites` | List tools, packages, credentials, or access required before the task can run; leave `[]` if none |
| `token_estimate` | Estimate tokens for the full pipeline (Builder + Reviewer + Tester + DocUpdater + SelfImprover). Default budget: 8000 for medium tasks; 5000 for small (docs/config); 12000 for large (multi-file code). Present to user for adjustment |

Present the drafted template to the user and ask: "Does this look correct? Reply YES to accept, or give corrections."
Apply corrections and re-present until the user confirms YES.

**5. Assign task IDs and artefact paths**
For each confirmed item:
- Task ID: start from the next ID computed in Step 1 (e.g. task-014), increment by 1 for each subsequent item.
- Artefact path: `artefacts/task-NNN/` — before assigning, run `ls artefacts/` and check if the path already exists. If it does, use a descriptive suffix (e.g. `artefacts/task-014-bl009/`).
- BL item status to set: `in_progress` (task being planned now)
- Story ID: if the BL item maps to a story in epics.md, record the story ID (match by cross-referencing BL item title against story titles in epics.md); otherwise leave null.

**6. Present sprint plan for confirmation**
Display the full sprint plan as a table:

```
## Sprint Plan — <today's date from system clock as YYYY-MM-DD>

| Task ID | BL ID | Title | Project | Priority | Token Est |
|---|---|---|---|---|---|
<one row per planned task>

Total estimated tokens: <sum>
```

If total estimated tokens > 400,000: warn the user before proceeding:
`WARN: total estimated tokens (<n>) exceed 80% of project cap (500k). Consider splitting the sprint.`

Ask: "Confirm this sprint plan? Reply YES to commit to queue.json."

**7. Commit to queue.json**
Only after user confirms YES:

For each new task:
1. Read `tasks/queue.json` (fresh read — do not reuse prior reads; the file may have changed).
2. Append a new task object to the `tasks` array using this schema:
```json
{
  "id": "<task-NNN>",
  "title": "<title from BL item>",
  "project": "<project column from backlog.md>",
  "target_project_path": "<look up in CLAUDE.md workspace table: match project short name to Path column>",
  "epic_id": "EPIC-003",
  "story_id": "<story ID or null>",
  "assigned_to": "builder",
  "status": "pending",
  "artefact_path": "<artefacts/task-NNN/ or descriptive suffix>",
  "created": "<today's date as YYYY-MM-DD, from system clock>",
  "updated": "<ISO8601 timestamp, from system clock>",
  "token_estimate": <number>,
  "resume_from": null,
  "notes": [],
  "mvp_template": { <confirmed fields from Step 4> }
}
```
3. Write the updated queue.json. Validate it is syntactically valid JSON before writing (parse with `python3 -c "import json, sys; json.load(sys.stdin)"` if needed).

**8. Update tracking files**
On a feature branch (`feature/pm-plan-<YYYY-MM-DD>`, where YYYY-MM-DD comes from the system clock):

a. **backlog.md**: for each planned BL item, update its `Status` column from its current value to `in_progress`. Lookup: column 7 (Status) of the matching BL-NNN row in `tasks/backlog.md`.

b. **kanban.md**: add each new task to the **Ready** section. Format: `- **<task-id>** <title> (<BL-ID>)`. Read `tasks/kanban.md` first; find the `## Ready` section and append below existing entries.

c. **epics.md**: if any task maps to a story, update that story's status to `in_progress` and record the task ID. Lookup: find the story row in `tasks/epics.md` by Story ID; update `Status` column and `Queue Task` column.

Commit all four file changes together (queue.json + backlog.md + kanban.md + epics.md) with message:
```
[AGENT] pm-plan: queue <task-NNN> through <task-MMM> (<BL-IDs>)
```

Merge the feature branch to develop via fast-forward:
```bash
git checkout develop && git merge --ff-only feature/pm-plan-<YYYY-MM-DD>
```

**9. Summary**
Print:
```
## Planning session complete

Tasks queued: <count>
- <task-id>: <title> (<token_estimate> tokens)
...
Total tokens this sprint: <sum>

Next step: run /pm-run to start executing the queue.
```
