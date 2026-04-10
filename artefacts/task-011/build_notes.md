# Build Notes — task-011

Agent: Builder [Sonnet]  
Date: 2026-04-10

---

## Design Decisions

### 1. `--ff-only` merge strategy

`git pull` is split into `git fetch` + `git merge --ff-only` rather than a
plain `git pull`. Reasons:
- Network failure surfaces at fetch time before the working tree is touched.
- `--ff-only` refuses to create a merge commit if the local branch has
  diverged — this is a hard safety gate. The vault is supposed to be
  append-only from n8n, so divergence is an anomaly worth surfacing loudly.
- Separating fetch from merge lets us log the git output from each step
  independently.

### 2. Auto-stash for unexpected local changes

The vault is append-only from the n8n side, so local modifications are
unexpected. Rather than aborting on `git merge --ff-only` with a dirty
working tree, the script stashes first, pulls, then pops. This keeps the
cron run non-blocking while logging a WARN so the operator is aware.

The alternative (abort on dirty tree) would cause every cron run to fail
silently if Obsidian creates any local metadata file — chosen not to use.

### 3. Fetch failure aborts before touching working tree

If `git fetch` fails (network down, SSH auth error, GitHub unreachable), the
script logs ERROR and exits non-zero before `git merge` is ever called. The
working tree is never modified. The stash (if any) is restored before exit.

### 4. Temp-file pattern for logging git output with correct exit-code capture

Git command output is logged per-line (individually timestamped, tagged `[GIT]`)
by reading from a temp file, not by piping into a `while read` loop.

The piped approach `git fetch ... | while ...; done` is tempting but flawed:
under `set -o pipefail`, the exit code of the pipe is the exit code of the
last command — the `while` loop — which always exits 0. This means a failed
`git fetch` would not be detected.

The safe pattern used instead:
```bash
TMPLOG=$(mktemp)
trap 'rm -f "${TMPLOG}"' EXIT

if ! git fetch ... > "${TMPLOG}" 2>&1; then
    while IFS= read -r line; do log "GIT" "${line}"; done < "${TMPLOG}"
    log_and_exit "..."
fi
while IFS= read -r line; do log "GIT" "${line}"; done < "${TMPLOG}"
```

This correctly captures the git exit code in the `if !` condition, and the
temp file is cleaned up via `trap EXIT` regardless of how the script ends.

### 5. Hardcoded paths — no user-controlled values

`VAULT_DIR`, `LOG_FILE`, `GIT_REMOTE`, and `GIT_BRANCH` are compile-time
constants at the top of the script. There is no runtime input and no path
construction from external data, so path traversal is not a risk.

### 6. SSH key auth only — no secrets in script

The script makes no HTTP calls and contains no credentials. Authentication
for `git fetch` relies on the SSH agent / key that root's cron environment
has access to on Pi4. The deploy-notes remind the operator to verify SSH
access before deployment.

### 7. Log file pre-creation (deploy step)

The script appends to the log file with `>>` but does not create it with
`sudo`. If root runs the cron job, `/var/log/pensieve-sync.log` needs to
exist and be writable. The deploy-notes include an explicit `sudo touch` step
to avoid a silent failure on first run.

---

## Shellcheck compliance

The script was written to pass `shellcheck` with zero warnings:
- All variables are quoted.
- `set -euo pipefail` is set.
- No deprecated `[[ ]]` patterns.
- `IFS= read -r` used for safe line reading.
- Boolean flags use string comparison (`== "true"`) not `-eq`.
- Temp file used for git output capture instead of pipe-into-while (avoids
  SC2069 / lost exit code in pipeline pattern).
- `trap 'rm -f "${TMPLOG}"' EXIT` ensures temp file cleanup.

Run locally to verify: `shellcheck artefacts/task-011/pensieve-sync.sh`

---

## Out of scope (not built)

- Conflict resolution — the vault is append-only; n8n never edits existing files.
- Two-way sync (Pi4 → GitHub) — not required; Obsidian reads only.
- Obsidian plugin changes — out of scope per MVP template.
- Actual deployment to Pi4 — deploy-notes.md is the handoff document.
