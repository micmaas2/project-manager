# Feasibility Report: Git Worktrees for Parallel Agent Isolation

**Task**: task-065
**Agent**: Builder [Sonnet]
**Date**: 2026-05-06
**Git version tested**: 2.47.3
**Repo**: /opt/claude/project_manager

---

## Overview

This report evaluates whether `git worktree` provides sufficient isolation for running multiple
agents in parallel against the same git repository. The investigation includes empirical testing
on the actual project repo (Pi: linux, git 2.47.3) covering index independence, branch
exclusivity, conflict failure modes, and stale-entry cleanup.

**Verdict**: RECOMMENDED — with one mandatory design constraint: each parallel agent must
operate on a dedicated branch. Git enforces single-worktree-per-branch at the OS level;
violating this constraint requires `--force` and silently produces overlapping linear commits
(see Conflict Risks).

---

## Worktree Behavior

A git worktree (`git worktree add <path> <branch>`) checks out a branch into a new filesystem
directory that shares the same underlying repository. Key mechanics confirmed empirically:

| Property | Behavior |
|---|---|
| Object store (commits, blobs, trees) | **Shared** — all worktrees read/write from one `.git/objects/` |
| `refs/heads/*` (branch pointers) | **Shared** — a branch moved in one worktree is immediately visible to all |
| `HEAD` | **Per-worktree** — stored in `.git/worktrees/<id>/HEAD`, not `.git/HEAD` |
| Staging index | **Per-worktree** — stored in `.git/worktrees/<id>/index` |
| Working tree files | **Per-worktree** — separate filesystem path per worktree |
| Config (`.git/config`) | **Shared** via `$GIT_COMMON_DIR` pointing back to main |
| `refs/bisect`, `refs/worktree`, `refs/rewritten` | **Per-worktree** (git design; not tested) |

Each linked worktree has a private sub-directory at `.git/worktrees/<id>/` containing its own
`HEAD`, `index`, and `logs/`. A `.git` file at the root of the linked worktree path points to
this private sub-directory.

```
.git/
├── HEAD              ← main worktree
├── index             ← main worktree
├── objects/          ← SHARED across all worktrees
├── refs/             ← SHARED (except bisect/worktree/rewritten)
└── worktrees/
    └── wt-agent-1/
        ├── HEAD      ← agent-1 worktree only
        ├── index     ← agent-1 worktree only
        ├── gitdir    ← pointer to /tmp/wt-agent-1/.git
        └── commondir ← points back to ../.. (shared config)
```

---

## Isolation Guarantees

**Confirmed by empirical test on this repo:**

1. **Index is fully independent per worktree.** Changes staged in worktree A are invisible
   to worktree B. Tested: `git add` and `git status` in `/tmp/wt-test` showed no effect on
   `/tmp/wt-test2`.

2. **Working tree files are fully independent.** A file created and committed in worktree A
   does not appear in worktree B's working directory (different filesystem path). Tested:
   `test_isolation.txt` committed in `wt-test` was absent in `wt-test2` (`ls` confirmed).

3. **A branch cannot be checked out in two worktrees simultaneously (without --force).**
   Git enforces: `fatal: '<branch>' is already used by worktree at '<path>'`. This is the
   primary isolation guarantee — each branch belongs to exactly one active worktree.

4. **Two worktrees on different branches operate fully independently.** Commits on
   `test-worktree-isolation` and `test-wt-agent2` branches did not interfere. Git objects
   (commits, blobs) are shared but ref pointers diverge safely.

5. **Git hooks fire per-commit in each worktree.** The project pre-commit and commit-msg hooks
   executed normally in linked worktrees (confirmed: `[pre-commit] All checks passed`).

**What is NOT isolated:**

- `refs/heads/*` — branch pointers are global. If agent A merges branch X into develop, agent
  B sees the updated develop immediately (on next `git fetch` or local branch operation).
- The object store — all commits from all worktrees go into the same `.git/objects/`. No
  performance or security isolation at the object level.
- `.git/config` — shared. An agent that modifies repo config affects all worktrees.

---

## Conflict Risks

### Risk 1: Same Branch, Multiple Worktrees (HIGH — use --force required, still dangerous)

**Scenario**: two agents inadvertently operate on the same branch (e.g. both use `develop`).

**Finding**: Without `--force`, git refuses to create the second worktree.
With `--force`, both worktrees share the same branch pointer. Silent data loss occurs when
both agents modify the **same file**:

```
Initial: HEAD → commit A  (shared.txt = "version A")
Agent 1 modifies shared.txt → "version 1" → commits B
Agent 2 modifies shared.txt → "version 2" (working from "version A" base) → commits C (parent = B)

Result: shared.txt = "version 2" in C.
        Agent 1's change ("version 1") is silently gone — no conflict marker, no warning.
```

This is **silent data loss**. The overwrite is permanent and git history shows two clean
commits — no indication anything was clobbered. This scenario is only possible when `--force`
is used AND both agents write to the same file.

**Mitigation**: enforce one-branch-per-agent at worktree creation time. Do not use `--force`.
The OS-level refusal is the correct safety gate.

### Risk 2: Branch Pointer Drift (MEDIUM — race condition on shared refs)

**Scenario**: agent A merges its feature branch into `develop` while agent B is mid-task on
a `develop`-derived branch.

**Finding**: `refs/heads/develop` is global. After agent A merges, agent B's branch base is
stale. Agent B's eventual merge-to-develop will require a conflict resolution step that a
fully automated agent cannot handle.

**Mitigation**: agents never commit directly to `develop` — they work on isolated feature
branches and the merge-to-develop step is a human gate (or a serialized final merge step).
This matches the existing project branching strategy.

### Risk 3: Stale Worktree Metadata (LOW — automatic detection)

**Scenario**: a worktree's directory is deleted (e.g. `rm -rf /tmp/wt-agent-1`) without
running `git worktree remove`.

**Finding** (empirically confirmed):
- `git worktree list` immediately shows the entry as `prunable`.
- `git worktree prune --verbose` removes the stale metadata entry from
  `.git/worktrees/` automatically.
- No manual cleanup required; prune is safe to run at any time.

### Risk 4: Hooks Access Shared Files (MEDIUM — project-specific)

**Scenario**: two agents commit simultaneously; hooks read/write shared files.

**Finding**: this project's `hooks/workflow_guard_hook.py` inspects the `file_path` and
`content` parameters passed via stdin — it does **not** independently open `queue.json` from
disk. The actual TOCTOU risk is specific to *concurrent Write tool calls targeting
`tasks/queue.json`*: two agents could each read the current queue state, both decide to update
it, and whichever writes second silently overwrites the first's change.

**Mitigation**: serialize queue.json updates through a lock file or atomic Python write
(already used: `python3 -c "import json; ..."` pattern). Each agent's worktree operating on
its own task and writing to a distinct artefact path reduces contention further — the hook's
diff-inspection logic is not affected by concurrent commits to different branches.

### Risk 5: Worktree Path Collisions (LOW — naming convention fixes this)

**Scenario**: two agents are assigned worktree paths that collide.

**Mitigation**: use task-id-based paths: `/tmp/wt-<task_id>`. Task IDs are unique by
construction.

### Risk 6: /tmp Security and Persistence (MEDIUM — requires explicit hardening)

**Finding 1 — world-readable directory**: `/tmp` has mode 1777 (world-readable on Linux). If
the checked-out working tree contains sensitive files (credentials, tokens, config with
secrets), any local process can read them. Immediately after `git worktree add`, set the
worktree directory permissions:

```bash
git worktree add /tmp/wt-<task_id> <branch>
chmod 700 /tmp/wt-<task_id>
```

**Finding 2 — volatile storage**: `/tmp` is typically a tmpfs mount — a system reboot deletes
all worktree directories while branch refs and `queue.json` entries with `status: in_progress`
remain. This creates orphaned state. The pm-start crash recovery path (check worktree path
exists, prune if absent) handles this correctly, but **must run at every session start** — not
only after known crashes.

---

## Cleanup Strategy

### Routine Cleanup (per agent completion)

```bash
# Agent completion: explicit cleanup
git worktree remove /tmp/wt-<task_id>
git branch -D agent/<task_id>
```

### Stale Entry Recovery (if agent crashed or directory deleted)

```bash
# Detect stale entries
git worktree list --verbose  # shows "prunable" annotation

# Clean all stale entries
git worktree prune --verbose
```

### Session-End Sweep (pm-close or cron)

```bash
# Remove all temp worktrees older than 1 day
git worktree prune --expire=1.day
git worktree list  # verify only main worktree remains
```

### Lock Mechanism (for long-running agents)

Use the atomic form that locks at creation time to eliminate the window between `add` and
`lock`:

```bash
# Atomic: provision and lock in one step (preferred)
git worktree add --lock --reason "agent task-<id> in progress" /tmp/wt-<task_id> <branch>

# Unlock before remove
git worktree unlock /tmp/wt-<task_id>
git worktree remove /tmp/wt-<task_id>
```

---

## Recommendation

**Use git worktrees for parallel agent isolation. RECOMMENDED.**

Rationale:

1. **Index isolation is genuine and OS-enforced.** Each agent's staging area is separate.
   An agent cannot accidentally `git add` files staged by another agent.

2. **Branch exclusivity is OS-enforced.** Without `--force`, git prevents two agents from
   sharing a branch. This is the primary protection against silent data loss.

3. **Zero overhead.** Worktrees share the object store — no disk duplication. Creation
   (`git worktree add`) takes < 1 second. Deletion is equally fast.

4. **Hook-compatible.** Project hooks fired correctly in linked worktrees. No special
   worktree-aware hook configuration is needed.

5. **Prune is reliable.** Stale entries (from crashed agents) are auto-detected and cleaned
   with a single `git worktree prune` call.

6. **Fits existing branching strategy.** Agents already use feature branches. Worktrees
   formalize the isolation — one worktree = one feature branch = one agent task.

**Required constraints** (must be enforced by the loop operator, BL-090):
- Each agent receives a unique branch name: `agent/<task_id>`.
- Worktree path uses task ID: `/tmp/wt-<task_id>`.
- Do NOT use `--force` when creating worktrees — let git refuse duplicate branches.
- Cleanup on both success and failure paths.

---

## Integration Design Sketch (for BL-090, Loop Operator)

This sketch describes how the loop operator (BL-090) should integrate worktrees.
Implementation of BL-090 is out of scope here.

### Agent Lifecycle with Worktrees

```
SPAWN agent for task-<id>:
  1. branch  = f"agent/task-{task_id}"
  2. wt_path = f"/tmp/wt-{task_id}"

  # Provision
  git branch {branch} develop              # branch from develop
  git worktree add --lock --reason "agent {task_id} in progress" {wt_path} {branch}
  # --lock is atomic with add: eliminates the add→lock race window; no --force

  # Execute
  spawn_agent(cwd=wt_path, task_id=task_id)
  # Agent runs entirely inside wt_path; uses git -C {wt_path} for all operations

  # Complete (success path)
  push {branch} to origin                  # optional, for PR creation
  merge {branch} into develop              # serialized; one at a time
  git worktree unlock {wt_path}
  git worktree remove {wt_path}
  git branch -D {branch}

  # Complete (failure / timeout path)
  git worktree unlock {wt_path}            # if locked
  git worktree remove --force {wt_path}
  git branch -D {branch}
  log_failure(task_id)
```

### Parallel Execution Model

```
Loop Operator
│
├── task-066 → branch: agent/task-066 → wt: /tmp/wt-task-066
│                └── Agent runs; commits artefacts to agent/task-066
│
├── task-067 → branch: agent/task-067 → wt: /tmp/wt-task-067
│                └── Agent runs; commits artefacts to agent/task-067
│
└── Merge serializer (queue-based):
      when task-066 done: merge agent/task-066 → develop
      when task-067 done: merge agent/task-067 → develop
      (conflicts resolved before merging; develop not touched during parallel work)
```

### queue.json Integration

The loop operator updates `queue.json` per task lifecycle. The `notes` field tracks
worktree metadata:

```json
{
  "id": "task-066",
  "status": "in_progress",
  "notes": [
    "worktree: /tmp/wt-task-066",
    "branch: agent/task-066"
  ]
}
```

On crash recovery, pm-start reads `notes` for any task with `status: in_progress`, checks
if the worktree path exists, and either resumes or runs `git worktree prune` + branch cleanup.

### EnterWorktree / ExitWorktree Tool Usage

`EnterWorktree` and `ExitWorktree` are Claude Code session tools for interactive worktree
switching within a single agent session. They do not implement the lifecycle described in this
design (branch-from-develop, task-scoped path, lock, cleanup). BL-090 must use raw
`git worktree` shell calls for provisioning and cleanup. `EnterWorktree` may be useful for an
agent entering an already-provisioned worktree by path
(`EnterWorktree(path=/tmp/wt-task-066)`), but it does not replace the provisioning or cleanup
steps.

### Merge Conflict Mitigation

To minimize conflicts when merging parallel agent branches back to develop:
1. Agents write to task-scoped artefact paths (`artefacts/<task_id>/`). These paths are
   unique per task and will never conflict.
2. Agents that must modify shared files (`tasks/queue.json`, `CHANGELOG.md`) serialize
   through a file lock or are excluded from parallel execution.
3. The merge serializer processes one branch at a time — never two merges simultaneously.

---

*Report generated by Builder [Sonnet] for task-065.*
