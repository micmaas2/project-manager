# /pm-close — Sprint / MVP Close Procedure

Run at end of every sprint and at every MVP phase gate. Execute steps in order.

## Steps

**1. Verify clean working tree**
Run `git status`. If any uncommitted changes exist: stop and tell the user to commit or discard them before closing. Do not proceed until tree is clean.

**2. Proposal review**
Run /pm-propose (invoke the pm-propose skill — follow all steps in pm-propose.md).

**3. Bake learnings**
Invoke the revise-claude-md built-in agent (subagent_type: claude-md-management:revise-claude-md).
Commit any resulting CLAUDE.md changes on the current branch with message `[DOCS] revise-claude-md: session learnings`.

**4. Merge feature branch**
Read the current branch name: run `git branch --show-current`. Do not hardcode a branch name.
If on a feature/* branch:
- Run `git checkout develop`.
- Run `git merge feature/<branch-name> --no-ff -m "[RELEASE] Merge feature/<branch-name> → develop"`.
  Replace <branch-name> with the value read from `git branch --show-current` in the step above.

**5. Push develop**
Run `git push origin develop`.

**6. Delete feature branch**
Run `git branch -d feature/<branch-name>`.
Run `git branch -r | grep feature/<branch-name>` — if the remote branch still exists, run `git push origin --delete feature/<branch-name>`.

**7. Phase gate check**
Read tasks/epics.md. Find the epic with status=in_progress. If all its stories have status=done: announce the phase gate has been reached and await explicit human approval before queuing any next-phase work.
