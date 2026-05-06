# Review: task-065 — Git Worktrees Feasibility Report

**Reviewer**: Reviewer [Sonnet]
**Date**: 2026-05-06
**Artefact**: artefacts/task-065/feasibility_report.md

---

## Acceptance Criteria Verification

### AC 1: Report covers worktree behavior, isolation guarantees, conflict risks, cleanup strategy
**PASS** — All four areas are covered with dedicated sections. Empirical test evidence is cited
for isolation guarantees. Five distinct conflict risks are enumerated and rated. The cleanup
section covers routine, crash-recovery, session-end, and lock-based scenarios.

### AC 2: Recommendation — use or skip worktrees for parallel agents
**PASS** — Clear RECOMMENDED verdict with six numbered rationale points. Required constraints
are listed explicitly (one branch per agent, task-ID-based paths, no --force, cleanup on both
paths).

### AC 3: If recommended — sketch integration design for BL-090
**PASS** — Section "Integration Design Sketch (for BL-090, Loop Operator)" provides:
- Agent lifecycle pseudocode (provision, execute, complete success, complete failure)
- Parallel execution model ASCII diagram with merge serializer
- queue.json integration with notes-field schema
- EnterWorktree/ExitWorktree tool usage note
- Merge conflict mitigation strategies

All three acceptance criteria are fully met.

---

## Findings

### Finding 1: EnterWorktree/ExitWorktree description is speculative
**Description**: The report states EnterWorktree "provisions the worktree and set agent cwd"
and ExitWorktree "cleans up on completion". These are Claude Code built-in deferred tools
whose actual parameter schemas and behavior have not been verified in this report. The report
recommends preferring them over raw `git worktree` shell calls, but if their semantics differ
from what is described (e.g. EnterWorktree may not run `git worktree add` internally), the
integration design sketch could mislead BL-090 implementors.

**confidence**: 72 (the tools exist in this environment as deferred tools, but their schemas
are unverified; the risk is real but the impact is limited because the sketch is explicitly
labelled as a sketch — implementors should verify tool schemas before using them)

### Finding 2: Lock-based queue.json serialization is not designed here
**Description**: Risk 4 (hooks accessing shared files) mentions TOCTOU on `queue.json` and
notes "serialize queue.json updates through a lock file". The cleanup strategy and integration
design sketch do not include a lock-file design or pointer to an existing locking pattern.
The existing `python3 -c "import json; ..."` atomic-write pattern prevents corrupted reads
from a single writer but does not prevent two concurrent agents from both reading stale state
and then both writing. This gap leaves Risk 4 partially unmitigated.

**confidence**: 65 (the report correctly identifies the risk and calls out the mitigation;
the absence of a designed lock mechanism is a completeness gap, not an error — but BL-090
implementors must resolve this before parallel queue writes are safe)

### Finding 3: `git worktree remove --force` on failure path may lose uncommitted work
**Description**: The failure/timeout cleanup path uses `git worktree remove --force <wt_path>`.
If an agent has uncommitted staged changes at crash time, `--force` silently discards them.
The report notes this is intentional (failed agent = discard), but does not address the case
where an agent crashes after writing artefact files but before committing — those artefacts
would be lost. The recommendation does not suggest a pre-cleanup artefact flush (e.g. `git
stash` or a rescue copy to `/tmp/rescue-<task_id>/`).

**confidence**: 58 (this is a real edge case but "artefacts lost on agent crash" may be
acceptable given the task-retry model; the report does not discuss the retry/rescue pattern)

### Finding 4: No explicit mention of `$GIT_DIR` / `$GIT_WORK_TREE` environment variable behavior
**Description**: When `spawn_agent(cwd=wt_path)` is called, git commands inside the agent
work correctly only if they resolve `.git` via the `.git` file at `wt_path` (which points
to `.git/worktrees/<id>/`). If any agent subprocess sets `GIT_DIR` or `GIT_WORK_TREE`
environment variables explicitly, it could bypass the per-worktree isolation. The report
does not flag this as a risk or note that agents must not override these environment variables.

**confidence**: 55 (this is a known git footgun in CI environments; in the Claude Code agent
model it is less likely since agents use file-system cwd rather than explicit GIT_DIR, but
worth documenting for BL-090)

---

## Summary

The report is well-structured, empirically grounded, and covers all required acceptance
criteria. The recommendation is sound and the integration sketch is actionable for BL-090.
All findings are below the confidence ≥ 80 threshold — no blocking issues were identified.

Findings 1–4 are informational gaps worth noting in BL-090 design notes but do not
invalidate the report's conclusions or require a builder loop.

---

## VERDICT: APPROVED

[Sonnet]
