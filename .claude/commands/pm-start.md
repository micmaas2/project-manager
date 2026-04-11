# /pm-start — Session Startup

Run in order. Do not skip steps. Await user confirmation at the end before doing any task work.

## Steps

**1. Fetch remote**
Run `git fetch origin`.

**2. Telegram inbox**
Run `git show origin/main:tasks/telegram-inbox.md` to read the live inbox.
If items exist below the header line:
- Read tasks/backlog.md to find the highest BL-NNN ID currently present; next ID = that number + 1.
- For each inbox item: add a row to tasks/backlog.md — columns: next BL ID, EPIC-003, descriptive title, project_manager, P2, new, today's date (read from system clock as YYYY-MM-DD).
- Create a feature branch (`feature/promote-telegram-inbox-<YYYY-MM-DD>`), commit the backlog update and a cleared inbox (two-line header only), merge to develop.

**3. Lessons**
Read tasks/lessons.md. Print the last 3 table rows verbatim (skip header rows).

**4. Queue review**
Read tasks/queue.json.
- Count and list any tasks with status=paused (include resume_from value).
- For each task with status=done: check whether artefacts/<artefact_path>/improvement_proposals.md exists. Read artefact_path from that task's artefact_path field — do not assume it equals artefacts/<task_id>/. List any done tasks missing this file (SelfImprover catch-up needed).

**5. Phase gate check**
Read tasks/epics.md. Find the epic with status=in_progress. Check if all its stories have status=done. If yes: announce phase gate reached and await human approval before queuing next phase work.

**6. Summary**
Present: inbox items promoted (count), top 3 lessons, paused tasks, catch-up needed, phase status.
Await user confirmation before executing any task work.

**Next step suggestion**
After the summary, print one line:
- If paused tasks exist → `Suggested next: /pm-run  (resume paused task)`
- Else if pending tasks exist → `Suggested next: /pm-run  (execute next pending task)`
- Else if plannable backlog items exist (status: new) → `Suggested next: /pm-plan  (queue is empty — plan new work from backlog)`
- Else → `Suggested next: /pm-status  (nothing queued — review overall status)`
