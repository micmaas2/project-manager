# /pm-status — Current System Status

Read and display current state across queue, kanban, epics, and token spend.

## Steps

**1. Queue summary**
Read tasks/queue.json. Count tasks grouped by status field. List any tasks with status=in_progress or status=paused — include id, title, assigned_to, and resume_from (if set).

**2. Kanban**
Read tasks/kanban.md and print it as-is.

**3. Phase status**
Read tasks/epics.md. Find the epic with status=in_progress. For each of its stories, list: story id, title, status.

**4. Token spend**
Read logs/token_log.jsonl if it exists (skip silently if absent). Read the last 50 lines. Sum token_estimate grouped by task_id. Print per-task totals, then grand total.
