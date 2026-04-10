# Code Quality Review — pensieve-sync.sh

Reviewer: code-quality-reviewer [Sonnet]
Date: 2026-04-10
Task: task-011
File: `artefacts/task-011/pensieve-sync.sh`

---

## Critical Issues (Must Fix)

None.

---

## Major Issues (Should Fix)

### M-1 — Log injection via unfiltered git output (lines 76, 83, 90, 96)

**Issue**: Git output lines are written verbatim to the log file using:
```bash
while IFS= read -r line; do log "GIT" "${line}"; done < "${TMPLOG}"
```
Git messages can contain newlines embedded as `\n` in commit subjects, ANSI escape codes (color output), or even carefully crafted strings with `]` characters that mimic log prefix syntax. While the threat model here is low (git output is from a trusted remote), a compromised or attacker-controlled repo commit message could inject lines that look like `[2026-04-10T...] [ERROR] Root access granted` into the log, misleading anyone auditing the log file.

**Risk**: Log forgery / audit trail pollution. Low likelihood given private repo, but a real pattern to close.

**Fix**: Strip ANSI escape codes and non-printable characters before logging:
```bash
while IFS= read -r line; do
    # Strip ANSI codes and non-printable chars (except TAB) before writing to log
    sanitized=$(printf '%s' "${line}" | sed 's/\x1b\[[0-9;]*m//g; s/[^[:print:][:blank:]]//g')
    log "GIT" "${sanitized}"
done < "${TMPLOG}"
```
Extract to a helper `log_git_output() { ... }` and call it in all four places to avoid duplication.

---

### M-2 — `git stash pop` after merge failure may silently create a conflict (lines 91–93)

**Issue**: When `git merge --ff-only` fails and `STASH_APPLIED=true`, the script calls:
```bash
git stash pop || log "WARN" "Stash pop failed after merge error..."
```
`git stash pop` applies stash entries using a merge. If the merge failure left the index in a partially modified state, `stash pop` can succeed with unresolved conflicts (exit code 0) while leaving conflict markers in vault files. The vault would then contain `<<<<<<< Updated upstream` markers with no further alerting.

**Risk**: Silent vault corruption that Obsidian will display to the user as raw conflict markers in notes.

**Fix**: After `stash pop` in error paths, check for conflicts:
```bash
if git stash pop; then
    if git diff --check > /dev/null 2>&1; then
        log "WARN" "Stash restored after merge error — no conflicts detected."
    else
        log "ERROR" "Stash pop created conflicts after merge error — manual recovery needed. Run: git stash list && git diff"
    fi
else
    log "WARN" "Stash pop failed after merge error — stash entry still present."
fi
```

---

## Minor Issues (Consider Fixing)

### m-1 — Log file creation failure is silent on first run (lines 18–22)

**Issue**: The `log()` function appends to `${LOG_FILE}` with `>>`. If the file does not exist and the script is running under an account that cannot create files in `/var/log/`, the `printf ... >>` silently fails (bash does not exit on append-redirect failure even under `set -e`). The deploy notes mention a `sudo touch` step, but if that step is skipped, every log call becomes a no-op with no operator feedback.

**Fix**: Add a startup guard that validates log writability and falls back to stderr:
```bash
# Validate log file is writable; fall back to stderr if not
if [[ ! -w "${LOG_FILE}" ]]; then
    printf '[WARN] Log file %s not writable; logging to stderr\n' "${LOG_FILE}" >&2
    LOG_FILE=/dev/stderr
fi
```
Place this immediately after the configuration block, before the first `log` call.

---

### m-2 — `git rev-list` uses unquoted SHA range (line 117)

**Issue**:
```bash
COMMIT_COUNT=$(git rev-list --count "${BEFORE_SHA}..${AFTER_SHA}")
```
Both `BEFORE_SHA` and `AFTER_SHA` come from `git rev-parse HEAD` which returns a 40-character hex string — not user-controlled input. This is safe in practice, but if ever refactored to accept input SHAs, the unquoted range construct could cause issues. The variables are already quoted, so no immediate action needed — but worth noting.

No fix required; already quoted. Low priority awareness note only.

---

### m-3 — No lock file; concurrent cron runs can race (line 40 onwards)

**Issue**: If a sync run takes longer than 15 minutes (e.g. slow network, large pull), the next cron invocation starts while the first is still in `git merge`. Two concurrent `git merge --ff-only` calls on the same repo will race and one will fail non-atomically, potentially leaving the index dirty.

**Risk**: Unlikely on a healthy network with a small vault, but not guarded against.

**Fix**: Add a flock-based lock at the top of the script:
```bash
LOCK_FILE="/var/lock/pensieve-sync.lock"
exec 9>"${LOCK_FILE}"
if ! flock -n 9; then
    log "WARN" "Another instance is running (lock held). Skipping this run."
    exit 0
fi
```
`flock` is available on Debian/Raspbian without additional packages.

---

### m-4 — Stash message includes command-substituted date; safe but redundant (line 56)

```bash
git stash push --include-untracked -m "pensieve-sync auto-stash $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
```
The date is useful but the stash message is only for human inspection via `git stash list`. The `$(...)` substitution runs before git sees the argument, which is correct — this is not a security issue. Minor observation: the same timestamp is already in the surrounding `log "WARN"` line, so the stash message date is redundant. Not harmful; leave as-is.

---

### m-5 — No maximum log file size guard (deploy-notes.md, line 148)

**Issue**: The deploy notes describe logrotate configuration as "optional." Running every 15 minutes, the log grows at approximately 2–5 lines per run × 96 runs/day = 200–500 lines/day. Without rotation, `/var/log/pensieve-sync.log` will grow without bound on a long-lived Pi4.

**Recommendation**: Promote the logrotate snippet from "optional" to a required deploy step, or add `daily` + size limit to the config:
```
/var/log/pensieve-sync.log {
    daily
    size 5M
    rotate 7
    compress
    missingok
    notifempty
    copytruncate
}
```
`copytruncate` avoids a race with the cron job holding the file open.

---

## Positive Observations

- **Shell safety is excellent**: `set -euo pipefail` is set on line 5. All variables are quoted. `IFS= read -r` is used for line reading. No unquoted expansions were found. This would pass shellcheck with zero warnings.

- **Correct exit-code capture from git**: The temp-file pattern (lines 72–82) correctly avoids the classic pipe-to-while gotcha where `git fetch | while read` hides the fetch exit code under `set -o pipefail`. The build notes explain the reasoning clearly — this is a well-considered design choice.

- **Fetch-before-merge discipline**: Splitting `git pull` into `git fetch` + `git merge --ff-only` (lines 75, 89) means network failures surface before the working tree is touched. The `--ff-only` flag enforces the append-only contract and refuses to create merge commits — correct and intentional.

- **Stash-before-pull non-destructive handling**: Rather than aborting on a dirty working tree (which would cause cron runs to silently fail if Obsidian creates metadata files), the script stashes, pulls, and restores. This is the right tradeoff for the stated use case and is clearly documented in build_notes.md.

- **Trap-based temp file cleanup**: `trap 'rm -f "${TMPLOG}"' EXIT` (line 73) ensures the temp file is always removed regardless of how the script exits — correct use of EXIT trap.

- **No secrets in script**: Authentication is entirely via SSH key. No credentials, tokens, or passwords appear anywhere in the script. The design note in build_notes.md (§6) is accurate.

- **Pre-flight checks are meaningful**: The three pre-flight checks (directory exists, is a git repo, remote is configured) fail fast with actionable error messages before any git operation runs. The error messages reference `deploy-notes.md` for remediation — operator-friendly.

- **Log format is consistent and machine-parseable**: `[ISO8601] [LEVEL] message` is grep-friendly and unambiguous for future log aggregation.

---

## Summary

The script is well-constructed and demonstrates genuine understanding of bash safety pitfalls. Shell hygiene is high: `set -euo pipefail`, universal quoting, safe line-reading, correct exit-code capture, and trap-based cleanup are all present and correct. The fetch-then-ff-merge pattern correctly isolates network failures from working-tree modifications, and the stash logic handles Obsidian-generated local changes non-destructively.

Two issues warrant fixing before production deployment:

1. **M-1 (log injection)**: Git output containing ANSI codes or newline-embedded strings is written verbatim to the log. Add a one-line sanitization step in the four `log "GIT"` loops — low effort, closes a real audit trail integrity risk.
2. **M-2 (stash pop after merge failure)**: `git stash pop` can succeed with exit code 0 while leaving conflict markers in vault files. Add a `git diff --check` guard after error-path stash pops to detect and loudly flag this condition before it silently corrupts notes.

Additionally, a flock-based concurrency lock (m-3) and a log-writability guard (m-1) would make the script more robust for a long-running cron deployment.

**Overall risk rating: Low** — no credentials exposure, no path construction from external input, no privilege escalation surface. The two major issues are edge-case rather than common-path risks given the private repo and controlled deployment environment.
