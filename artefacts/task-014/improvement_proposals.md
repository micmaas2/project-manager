# Improvement Proposals — task-014

## Proposal 1: Enforce `require_human_approval: true` for agents with Write/Edit tools

**Target file**: `.claude/agents/manager.yaml` (and check all agent YAMLs)

**Change**: Update the policy block in manager.yaml from `require_human_approval: false` to `require_human_approval: true`. Review all `.claude/agents/*.yaml` files and set this flag to `true` for any agent with `write`, `edit`, `bash`, or `rm` in its `allowed_tools`.

**Rationale**: task-014 discovered that ProjectManager has `require_human_approval: false` despite having Write/Edit tools, meaning it can silently modify production files (queue.json, backlog.md) without a human review gate. The CLAUDE.md comment on line 168 documents the rule ("set to TRUE for any agent that has Bash in allowed_tools") but this is not enforced in the actual agent YAMLs. Agents with file-write capabilities should require explicit human approval before execution.

**Status**: REQUIRES_HUMAN_APPROVAL

## Proposal 2: Add automated M-1 consistency check to pre-commit hooks

**Target file**: `hooks/pre-commit` (and CLAUDE.md line 142 to reference the new check)

**Change**: Add a `make lint-agents` target or extend pre-commit to run a Python script that: (1) extracts rule counts from CLAUDE.md (lines 142+), (2) extracts rule counts from all `.claude/agents/*.yaml` files, (3) compares counts, (4) raises an error if mismatched. Example: if CLAUDE.md documents 10 agent policies and manager.yaml only has 9 fields, the check fails with a clear message. This prevents the manual M-1 mirroring from drifting.

**Rationale**: task-014's architecture review noted that "The M-1 pattern (mirrored rules between CLAUDE.md and agent YAMLs) is manual and error-prone." This has been a known issue since task-007 (documented in lessons.md row 17). An automated check at pre-commit time would catch drifts immediately rather than relying on human memory during future edits.

**Status**: REQUIRES_HUMAN_APPROVAL

## Proposal 3: Add runtime token cap guard before agent spawn

**Target file**: `.claude/agents/manager.yaml` (add a policy enforcement step before `Builder` is spawned)

**Change**: Before spawning each agent, sum `token_estimate` for the current task. If total exceeds 400,000 (80% of 500k cap), halt with a structured error: `ALERT: Task <task_id> estimated tokens (<N>) exceed 80% of project cap (400k). Reduce scope or split task before proceeding.` This should be enforced at the Python/script level (e.g., in the manager skill or a shared token guard callable from manager.yaml).

**Rationale**: task-014 identified that "project_manager defines a 500k token cap in CLAUDE.md but has no runtime enforcement; mas_agent has budget config fields but `check_budget()` is report-only (no blocking)." The 500k cap exists as documentation only — a runaway agent can silently exceed budget. This proposal adds a hard check at task launch time, preventing overspend before it happens. CLAUDE.md already documents the 80% preflight alert (line 241) but does not implement it.

**Status**: REQUIRES_HUMAN_APPROVAL
