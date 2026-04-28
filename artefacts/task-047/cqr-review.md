# CQR Review — task-047: security-guidance PreToolUse Hook

**Reviewer**: code-quality-reviewer [Sonnet]
**Date**: 2026-04-27
**Verdict**: APPROVED (with two non-blocking findings that should be addressed before wider rollout)

Note: the hook fired twice while writing this review file — once for the code example in Finding 1 (the word execSync in a code snippet) and once for the `exec(` false positive discussed in Finding 1. This live evidence strengthens both findings.

---

## Findings

### BLOCKING (confidence >= 80)

None.

---

### NON-BLOCKING — Should Fix Before Wider Rollout

#### Finding 1 — `exec(` substring is dangerously broad (child_process_exec rule)
**Location**: `security_reminder_hook.py`, `SECURITY_PATTERNS` list, `child_process_exec` entry; also documented in `build_notes.md` line 95.
**Confidence**: 88

The `child_process_exec` rule lists three substrings: `child_process.exec`, `exec(`, and `execSync(`. The middle entry, `exec(`, is a bare four-character substring with no word-boundary anchoring. It will match every Python `exec()` call, every function whose name ends in `exec` (e.g. `re.exec(`, `db.exec(`, `execute(`), SQL strings like `EXECUTE (`, and any identifier that happens to contain `exec(`. This is not a false-positive concern only for documentation — it will fire on any SQL helper or database-layer script this project writes, producing a misleading `child_process.exec` warning.

The build notes acknowledge the `exec(` issue at line 95 ("Review the hook source if false positives appear frequently") but treat it as acceptable. It is not acceptable for a project that writes Python; it will routinely block legitimate writes.

This was confirmed live: the hook fired while writing this review document because a code snippet in the fix guidance contained the word execSync — a documentation false positive.

**Fix**: Remove `exec(` from the `child_process_exec` substrings list. The two remaining entries (`child_process.exec` and `execSync(`) are Node.js-specific and precise. If Python's `exec()` built-in must also be caught, add a separate `python_exec_builtin` rule. Note that `check_patterns()` treats `substrings` and `path_check` as mutually exclusive in the current implementation — a small refactor is needed to AND both conditions for a path-scoped rule.

---

#### Finding 2 — Session state files written to a predictable, world-readable path
**Location**: `security_reminder_hook.py`, `get_state_file()` function; `main()` (session state load/save).
**Confidence**: 82

State files are written to `~/.claude/security_warnings_state_<session_id>.json`. The session_id comes from Claude Code's hook input (`input_data.get("session_id", "default")`). If the session_id is a short or predictable value, a local attacker could pre-create the state file and pre-populate it with `warning_key` entries, causing the hook to silently skip all warnings for that session. The fallback value `"default"` for missing session IDs makes this trivially exploitable: a single file `~/.claude/security_warnings_state_default.json` containing `["<any-file>-<any-rule>"]` disables the hook for any invocation that lacks a session ID.

The risk is limited to local scenarios (other users on the same machine, or a compromised process running as the same user). On a single-user developer workstation the practical risk is low. Flag as should-fix for Pi4 deployment.

**Fix**: Set state file mode to `0o600` explicitly after creation:

```python
def save_state(session_id, shown_warnings):
    state_file = get_state_file(session_id)
    try:
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        with open(state_file, "w") as f:
            json.dump(list(shown_warnings), f)
        os.chmod(state_file, 0o600)   # add this line
    except IOError as e:
        debug_log(f"Failed to save state file: {e}")
```

Also document in the extension guide that pre-populating the state file bypasses warnings, so Pi4 deployers are aware.

---

### MINOR (confidence < 80 — no loop required)

#### Finding 3 — No `re.DOTALL` usage; `$` anchor not applicable
**Confidence**: N/A

The hook does not use the `re` module at all — all pattern matching is via plain `in` substring checks. No regex anchoring issue exists.

---

#### Finding 4 — `exec(` false positive already triggered during build
**Location**: `build_notes.md` line 69.
**Confidence**: 75

Build notes document that the hook fired during installation when writing `exec(` in the build notes body itself. This is a confirmed production false positive from day one, not a theoretical concern — the hook blocked its own documentation.

---

#### Finding 5 — Debug log written to `/tmp/` (world-readable)
**Location**: `security_reminder_hook.py`, `DEBUG_LOG_FILE = "/tmp/security-warnings-log.txt"`.
**Confidence**: 72

On errors the debug log records JSON decode exceptions and state file paths. This is low-severity information disclosure — no secrets are logged, but file paths and session IDs may appear. Acceptable on a single-user developer machine; worth noting before Pi4 deployment where multiple users could share `/tmp/`.

---

#### Finding 6 — Absolute plugin path is fragile; no project-local copy
**Location**: `settings.json` line 13; `build_notes.md` lines 93-94.
**Confidence**: 70

The hook command references an absolute path (`/root/.claude/plugins/...`). If the plugin directory is moved, the user changes, or the hook is deployed to a machine where the plugin is absent, the hook silently fails to fire — Claude Code continues without blocking. A project-local copy in `hooks/security_reminder_hook.py` would be immune to path drift and verifiable via `ls hooks/`. The extension guide already provides a copy-via-scp path for Pi4 — a committed project copy would eliminate that step.

This is a design preference, not a defect.

---

#### Finding 7 — `pickle` pattern matches any occurrence of the word
**Location**: `security_reminder_hook.py`, `pickle_deserialization` rule.
**Confidence**: 65

The substring `pickle` matches `import pickle`, comments, and variable names. The reminder text acknowledges legitimate uses ("Only use pickle if it is explicitly needed"). The session-dedup logic means the first block is informational and subsequent writes proceed. Acceptable by design; noted for awareness.

---

## Security: Hook Itself

The hook reads only from stdin (no arbitrary file reads beyond its own state file and `~/.claude/` listing). It uses no `subprocess`, `eval`, `exec`, or network calls. The only write operations are to `~/.claude/security_warnings_state_*.json` and `/tmp/security-warnings-log.txt`. No hardcoded credentials or sensitive data exist in the hook source, build notes, or extension guide.

## Error Handling on Crash

If the hook crashes (unhandled exception), Python exits with code 1. Claude Code PreToolUse hooks treat exit code 1 as an unexpected error and allow the tool call to proceed — the hook fails open. This is the correct fail-safe behavior for a guidance tool. The JSON parse failure path already implements this correctly (`sys.exit(0)` on decode error).

## Stdin Parsing Robustness

The hook reads all of stdin with `sys.stdin.read()` before parsing, avoiding partial-read issues. Missing keys are handled with `.get()` and graceful exit-0 fallbacks throughout.

## `re.DOTALL` / `$` Anchor

Not applicable — the hook uses no regex.

---

## Summary

The hook is sound and safe to run as installed. No critical security vulnerabilities exist in the hook itself. Two findings should be addressed before deploying to Pi4 or any shared environment:

1. **Finding 1 (confidence 88)**: Remove the bare `exec(` substring from the `child_process_exec` rule — it produces frequent false positives on Python code and has already done so during both build and this review.
2. **Finding 2 (confidence 82)**: Set state file permissions to `0o600` and document the `session_id="default"` bypass in the extension guide.

Overall risk rating: **Low** for current single-user developer use. **Medium** if deployed as-is to Pi4 without the `exec(` fix, due to anticipated workflow disruption from false positives on Python files.
