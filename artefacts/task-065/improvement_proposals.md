# Improvement Proposals: task-065 — Git Worktrees Feasibility Investigation

**Agent**: SelfImprover [Haiku]
**Date**: 2026-05-06
**Task**: task-065

---

## Proposal 1

**Target file**: `CLAUDE.md`

**Change**: Add a guidance note under Workflow Orchestration (or a new "Git Worktree Patterns" subsection) covering:

```
**Git worktree usage in parallel agent tasks** (see task-065 feasibility report):
- Use task-ID-based paths: `/tmp/wt-<task_id>`. Task IDs are unique by construction.
- Always `chmod 700 /tmp/wt-<task_id>` immediately after `git worktree add` — `/tmp` is
  world-readable (mode 1777). Do NOT skip this step when working trees may contain
  credentials or config with secrets.
- `/tmp` is volatile (tmpfs). On reboot, worktree directories are lost but `.git/worktrees/`
  entries and `queue.json` `status: in_progress` records remain. Run `git worktree prune` at
  every session start — not only after known crashes.
- Atomic provision: `git worktree add --lock --reason "agent <task_id> in progress" /tmp/wt-<task_id> <branch>`
  eliminates the add→lock race window. Never use `--force`.
- Cleanup: `git worktree unlock <path> && git worktree remove <path>` on both success and
  failure paths. On failure: `git worktree remove --force <path>` to discard uncommitted work.
```

**Rationale**: The /tmp world-readable risk and volatile-storage crash-recovery requirement were discovered empirically in task-065 and are non-obvious to future agents implementing BL-090. Without this guidance, the first BL-090 implementation is likely to omit `chmod 700` and skip the session-start prune, leaving sensitive files exposed and orphaned queue entries accumulating over reboots.

**Status**: REQUIRES_HUMAN_APPROVAL

---

## Proposal 2

**Target file**: `CLAUDE.md`

**Change**: Add a caveat to the "EnterWorktree / ExitWorktree" tool note (currently in the session-start checklist or tool hints section) clarifying:

```
**EnterWorktree / ExitWorktree tool scope**: These Claude Code session tools switch the agent's
working directory to an already-provisioned worktree. They do NOT run `git worktree add`,
create branches, set locks, or clean up on exit. BL-090 loop operator must use raw
`git worktree` shell calls for provisioning, locking, and cleanup.
EnterWorktree(path=...) is useful for directing an agent into an already-provisioned
worktree; ExitWorktree returns it. Treat them as `cd` equivalents, not lifecycle managers.
```

**Rationale**: task-065 Builder initially described EnterWorktree/ExitWorktree as capable of provisioning and cleanup (the Reviewer flagged this as Finding 1, confidence 72). The misconception is plausible because the tool names suggest a lifecycle scope. Capturing the correct scope in CLAUDE.md prevents the same overstated description from appearing in BL-090's design doc and causing an incorrect implementation. The correct scope was confirmed by fetching the tool schema during this task.

**Status**: REQUIRES_HUMAN_APPROVAL

---

## Proposal 3

**Target file**: `CLAUDE.md` (research task checklist / "Verify before done" section, step 4)

**Change**: Add the following sub-bullet to the research task Definition of Done block:

```
**Research/feasibility tasks must verify tool capabilities against actual schemas before
documenting them**: when a task describes the behavior of a Claude Code built-in deferred
tool (EnterWorktree, ExitWorktree, etc.), use `ToolSearch(query="select:<ToolName>")` to
load and confirm the actual parameter schema before writing the feasibility report. Documenting
capabilities from inference or naming convention without schema verification risks misleading
downstream implementors. Note confirmed schema in build_notes.md.
```

**Rationale**: Risk 1 (wrong example: same file instead of different file for silent data loss) and the EnterWorktree/ExitWorktree description inaccuracy both stem from the same root cause: Builder described expected behavior from names/context without empirical verification. The wrong example was caught by the Tester (Test 6 confirmed it was corrected in the final report). The tool scope issue was caught by the Reviewer. A verification step in the task Definition of Done for research tasks prevents these inaccuracies from reaching the report.

**Status**: REQUIRES_HUMAN_APPROVAL

[Haiku]
