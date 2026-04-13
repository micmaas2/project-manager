# /pm-status — Current System Status

Read and display current state across queue, kanban, epics, and token spend.

## Steps

**1. Priority ranking**
Run `python3 scripts/pm-priority.py` (cwd: project_manager root). Print the output table as-is. If the script is absent, fall back to the manual queue summary below.

**2. Queue summary**
Read tasks/queue.json. Count tasks grouped by status field. List any tasks with status=in_progress or status=paused — include id, title, assigned_to, and resume_from (if set).

**3. Kanban**
Read tasks/kanban.md and print it as-is. Then run `python3 scripts/cross-kanban.py` (cwd: project_manager root) and print its output below the kanban.

**4. Phase status**
Read tasks/epics.md. Find the epic with status=in_progress. For each of its stories, list: story id, title, status.

**5. Token spend**
Read logs/token_log.jsonl if it exists (skip silently if absent). Read the last 50 lines. Sum token_estimate grouped by task_id. Print per-task totals, then grand total.

**Next step suggestion**
Print one line after the token summary:
- If any task has status=paused → `Suggested next: /pm-run  (resume paused task)`
- Else if any task has status=pending → `Suggested next: /pm-run  (execute next pending task)`
- Else if plannable backlog items exist (status: new) → `Suggested next: /pm-plan  (queue is empty — plan new work)`
- Else → `Suggested next: /pm-propose  (all tasks done — review improvement proposals)`
