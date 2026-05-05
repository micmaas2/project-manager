# /pm-close — Sprint / MVP Close Procedure

**Execution mode**: do not enter plan mode. This skill executes already-planned work. Proceed directly to the Steps below without calling EnterPlanMode.

Run at end of every sprint and at every MVP phase gate. Execute steps in order.

## Steps

**1. Verify clean working tree**
Run `git status`. If any uncommitted changes exist: stop and tell the user to commit or discard them before closing. Do not proceed until tree is clean.

**2. Proposal review**
Run /pm-propose (invoke the pm-propose skill — follow all steps in pm-propose.md).

**3. Bake learnings**
Invoke `revise-claude-md` via the `Skill` tool (not `Agent` tool — `subagent_type` does not work for `claude-md-management:*`).
Commit any resulting CLAUDE.md changes on the current branch with message `[DOCS] revise-claude-md: session learnings`.

**3b. Session counter + CLAUDE.md improver**
Read `docs/session-counter.json` (create it if absent with `{"closes": 0, "last_improver_run": null}`).
Increment `closes` by 1. Write back.

Print:
```
Session closes: <closes>
Next /claude-md-improver run: session <next_multiple_of_5>  (<5 - (closes % 5)> sessions away)
```

If `closes % 5 == 0`: run `/claude-md-improver` via the `Skill` tool on the following CLAUDE.md files in sequence:
- `CLAUDE.md` (project_manager)
- `/opt/claude/CCAS/CLAUDE.md` (if file exists)
- `/opt/claude/pi-homelab/CLAUDE.md` (if file exists)
- `/opt/claude/pensieve/CLAUDE.md` (if file exists)
- `/opt/claude/genealogie/CLAUDE.md` (if file exists)
- `/opt/claude/performance_HPT/CLAUDE.md` (if file exists)

Set `last_improver_run` to today's date (YYYY-MM-DD from system clock). Commit `docs/session-counter.json` with message `[DOCS] pm-close: session <closes>, ran claude-md-improver` (or omit "ran claude-md-improver" if not triggered). Commit to the current feature branch.

**4. Merge feature branch**
Read the current branch name: run `git branch --show-current`. Do not hardcode a branch name.
If on a feature/* branch:
- Run `git checkout develop`.
- Run `git merge feature/<branch-name> --no-ff -m "[RELEASE] Merge feature/<branch-name> → develop"`.
  Replace <branch-name> with the value read from `git branch --show-current` in the step above.

**5. Push develop**
Run `git push origin develop`.

**6. Delete feature branch(es)**
Run `git branch -d feature/<branch-name>` (delete the current session's branch).
Run `git branch -r | grep feature/<branch-name>` — if the remote branch still exists, run `git push origin --delete feature/<branch-name>`.

Then sweep all remaining merged local feature branches in one pass:
```
git branch --merged develop | grep "feature/" | xargs -r git branch -d
```
Print the list of branches deleted, or "No stale merged feature branches found" if none.
The `-r` flag in `xargs -r` makes this a no-op when no branches match.

**7. Phase gate check**
Read tasks/epics.md. Find the epic with status=in_progress. If all its stories have status=done: announce the phase gate has been reached and await explicit human approval before queuing any next-phase work.

**Next step suggestion**
Print one line after the phase gate check:
`Suggested next: /pm-start  (begin next session)`
