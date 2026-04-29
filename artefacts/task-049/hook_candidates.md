# Hook Candidates — task-049

Three CLAUDE.md must-always-follow rules selected for PreToolUse hook enforcement.

---

## Candidate 1: `re.DOTALL` + `$` as stop anchor in Python code

**Rule text (CLAUDE.md)**:
> for any regex using `re.DOTALL`, flag use of `$` as a stop anchor (use `\Z` instead) and require a multi-line fixture in Tester

**Why hook > prompt**:
- Appeared in task-011 Tester lesson and task-044 CQR finding — demonstrably forgotten under pressure.
- The consequence is a silent truncation bug (multi-line captures silently reduced to first line) that only surfaces at runtime with multi-line data.
- Pattern is mechanical: both `re.DOTALL` and `$` must appear in a `.py` file. No false positives from documentation or other file types.
- Review-phase tools (Reviewer, CQR) are supposed to catch this, but both missed it in task-011 (only the Tester's multi-line fixture caught it). A PreToolUse hook prevents the pattern from entering at all.

**Hook type**: PreToolUse (block, exit 2)

**Detection pattern**:
- File ends with `.py`
- Content contains `re.DOTALL` via `re.compile(...)` call
- Content contains `$` not followed by `{` (avoids false-positives on shell-style `${VAR}`)

**Implemented in**: `hooks/security_reminder_hook.py` (added to `REGEX_SECURITY_PATTERNS`)

---

## Candidate 2: `git commit` with hook-bypass flag

**Rule text (CLAUDE.md)**:
> Pre-Commit Hooks: ALWAYS active — NEVER use `git commit --no-verify`

**Why hook > prompt**:
- The bypass flag defeats ALL pre-commit controls: branch protection, credential scanning, agent YAML policy-schema consistency. A prompt rule can be overridden under pressure; a PreToolUse block cannot.
- The pattern is binary: `git commit` + the bypass flag. There is no legitimate use of this combination in this codebase (CLAUDE.md states this explicitly).
- It appeared in no lessons.md entry because it was never detected — if it were used, the controls would have been silently bypassed and no trace would appear in lessons. This is a preventive hook, not a corrective one.
- The Bash tool is the only route Claude can use to run git commands. A PreToolUse hook on Bash with a regex check covers 100% of Claude-originated bypass attempts.

**Hook type**: PreToolUse (block, exit 2) on Bash tool

**Detection pattern**:
- Tool is `Bash`
- Command matches `git\s+commit\b[^;\n]*--no-verify`

**Implemented in**: `hooks/workflow_guard_hook.py`

---

## Candidate 3: `queue.json` task marked `done` without non-empty `artefact_path`

**Rule text (CLAUDE.md)**:
> a task may not be set to `status: done` without a non-empty `artefact_path`. If no code was produced, set the path and create a `verification.md`

**Why hook > prompt**:
- Violated at least twice (task-003, task-006/007 artefact ID conflicts mentioned in lessons.md); SelfImprover is blocked without an artefact directory.
- The pattern is deterministic: `"status": "done"` in `tasks/queue.json` without a non-empty `"artefact_path"` in the same content block.
- A review-phase tool can only catch this after the queue.json write has occurred. A PreToolUse block prevents the invalid state from ever persisting.
- The hook check is narrow: it only fires on queue.json edits that set status to done — no false positives on other queue.json updates (in_progress, paused, etc.).

**Hook type**: PreToolUse (block, exit 2) on Edit/Write to `tasks/queue.json`

**Detection pattern**:
- File path ends with `tasks/queue.json` or `/queue.json`
- Content contains `"status": "done"`
- Content does NOT contain a non-empty `"artefact_path": "..."` value

**Implemented in**: `hooks/workflow_guard_hook.py`
