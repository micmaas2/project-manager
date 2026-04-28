# task-047: Improvement Proposals — security-guidance PreToolUse Hook

## Proposal 1

**Target file**: `CLAUDE.md`

**Change**: Update the line in the Security principles section from:
```
PreToolUse hooks for known-bad patterns: for security patterns with no legitimate use in the codebase (e.g. eval, os.system, innerHTML, pickle), prefer a PreToolUse blocking hook over a review-phase finding. Blocking at edit time prevents the pattern from ever entering the codebase; review-phase tools catch it after the fact. Use `security-guidance` (BL-101) as the reference implementation.
```

To:
```
PreToolUse hooks for known-bad patterns: for security patterns with no legitimate use in the codebase (e.g. eval, os.system, innerHTML, unsafe deserialization), prefer a PreToolUse blocking hook over a review-phase finding. Blocking at edit time prevents the pattern from ever entering the codebase; review-phase tools catch it after the fact. The local hook at `hooks/security_reminder_hook.py` (installed from BL-101) documents rules and deployment patterns in `artefacts/task-047/extension-guide.md`.
```

**Rationale**: Now that task-047 is complete with a working hook implementation and comprehensive extension guide, the generic "reference implementation" note should be updated to point to the actual local hook and its documentation. This makes the reference actionable rather than abstract.

**Status**: APPROVED

---

## Proposal 2

**Target file**: `.claude/agents/builder.yaml`

**Change**: Add a new checkpoint in the Builder prompt's pre-submission section. Locate the existing "Shell script pre-submission check" section and add after it:

```
Hook installation pre-submission check (for PreToolUse hooks): Before writing artefacts that will trigger the hook during testing, run a benign test payload first to verify the hook registration is correct. Example: write a file containing only `x = 1 + 1` (clean Python) and confirm the hook does not fire. Only after that verification should the Builder write artefacts that may contain patterns the hook blocks (eval, os.system, etc.). This prevents the hook from blocking its own installation artefacts and reduces the risk of silent guard misconfigurations.
```

**Rationale**: task-047 encountered a real operational issue: the security hook fired on the build_notes.md containing `exec(` during the Builder's own artefact creation, demonstrating that artefact files can trigger security guards. While the session handled this by bypassing and documenting the block, a future Builder installing a hook should test the hook with benign payloads first before writing content that matches the blocked patterns. This becomes a reusable pattern for any hook installation task.

**Status**: APPROVED

---

## Proposal 3

**Target file**: `tasks/lessons.md`

**Change**: Add a new pattern entry at the end of the lessons table (this is separate from Proposals 1 and 2 — it's a lessons entry, not a CLAUDE.md change):

```
| 2026-04-28 | SelfImprover | **Copy external hook/script dependencies locally before patching**: The security-guidance hook initially referenced an absolute plugin path; when code-quality-reviewer identified issues (broad exec() substring match, world-readable state files), the solution was to copy the hook locally to `hooks/security_reminder_hook.py` and patch there, eliminating path-drift risk and enabling git-tracked improvements. When a security tool or utility is sourced from a plugin marketplace, copy it locally first — this enables patching, reduces path fragility, and keeps security tools under project control. | All future security hook or marketplace utility installations |
```

**Rationale**: The "copy external dependency locally before patching" pattern emerged naturally from task-047's workflow and is reusable for any marketplace hook or utility. Documenting it in lessons.md makes it available for future Builder sessions that install similar marketplace tools.

**Status**: APPROVED
