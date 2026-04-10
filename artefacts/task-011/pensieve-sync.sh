#!/usr/bin/env bash
# pensieve-sync.sh — Pull micmaas2/pensieve into /opt/obsidian-vault on Pi4.
# Runs every 15 minutes via cron. SSH key auth only; no secrets in script.

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
VAULT_DIR="/opt/obsidian-vault"
LOG_FILE="/var/log/pensieve-sync.log"
GIT_REMOTE="origin"
GIT_BRANCH="main"

# SSH identity for git operations in cron environment (no SSH agent available).
# Update the path below to match the deploy key on this host.
# Alternative: configure Host github.com in /root/.ssh/config with IdentityFile
# and StrictHostKeyChecking no — then remove this export entirely.
export GIT_SSH_COMMAND="ssh -i /root/.ssh/id_rsa -o StrictHostKeyChecking=no"

# ---------------------------------------------------------------------------
# Concurrency lock — prevent overlapping instances
# ---------------------------------------------------------------------------
exec 9>/var/lock/pensieve-sync.lock
if ! flock -n 9; then
    # Cannot log to LOG_FILE yet (guard runs after this), so write to stderr only
    printf '[%s] [WARN] another instance running, skipping\n' \
        "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" >&2
    exit 0
fi

# ---------------------------------------------------------------------------
# Log file guard — must run before any log write
# ---------------------------------------------------------------------------
if [[ ! -f "${LOG_FILE}" ]]; then
    touch "${LOG_FILE}" 2>/dev/null || { printf 'ERROR: cannot create log file %s\n' "${LOG_FILE}" >&2; exit 1; }
fi
if [[ ! -w "${LOG_FILE}" ]]; then
    printf 'ERROR: log file %s is not writable\n' "${LOG_FILE}" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Logging helper
# ---------------------------------------------------------------------------
log() {
    local level="$1"
    shift
    printf '[%s] [%s] %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "${level}" "$*" >> "${LOG_FILE}"
}

log_and_exit() {
    log "ERROR" "$*"
    exit 1
}

# ---------------------------------------------------------------------------
# Sanitize git output lines before logging.
# Strips ANSI escape codes and non-printable characters (except TAB/LF).
# ---------------------------------------------------------------------------
sanitize_line() {
    local raw="$1"
    # Remove ANSI escape sequences (ESC [ ... m and similar)
    local stripped
    stripped="$(printf '%s' "${raw}" | sed 's/\x1b\[[0-9;]*[a-zA-Z]//g; s/\x1b[^[[][a-zA-Z]//g')"
    # Strip remaining non-printable characters (keep \t = 0x09)
    printf '%s' "${stripped}" | tr -d '\000-\010\013-\037\177'
}

# ---------------------------------------------------------------------------
# Pre-flight checks
# ---------------------------------------------------------------------------
if [[ ! -d "${VAULT_DIR}" ]]; then
    log_and_exit "Vault directory '${VAULT_DIR}' does not exist. Run initial clone first (see deploy-notes.md)."
fi

if [[ ! -d "${VAULT_DIR}/.git" ]]; then
    log_and_exit "'${VAULT_DIR}' is not a git repository. Run initial clone first (see deploy-notes.md)."
fi

cd "${VAULT_DIR}"

# Confirm the remote is configured (fail early rather than on git fetch)
if ! git remote get-url "${GIT_REMOTE}" > /dev/null 2>&1; then
    log_and_exit "Remote '${GIT_REMOTE}' not configured in ${VAULT_DIR}."
fi

# ---------------------------------------------------------------------------
# Stash any unexpected local changes so the pull cannot fail due to them.
# The vault is append-only from the n8n side, so local modifications are
# unexpected — stash them non-destructively and log a warning.
# ---------------------------------------------------------------------------
STASH_APPLIED=false

if ! git diff --quiet || ! git diff --cached --quiet; then
    log "WARN" "Unexpected local changes detected; stashing before pull."
    if git stash push --include-untracked -m "pensieve-sync auto-stash $(date -u '+%Y-%m-%dT%H:%M:%SZ')"; then
        STASH_APPLIED=true
    else
        log_and_exit "git stash failed — aborting to avoid data loss."
    fi
fi

# ---------------------------------------------------------------------------
# Fetch + pull
# ---------------------------------------------------------------------------
log "INFO" "Starting sync: ${VAULT_DIR} <- ${GIT_REMOTE}/${GIT_BRANCH}"

# Fetch first (network failure surfaces here, before we touch working tree)
# Capture git output to a temp file so we can log it AND check the exit code
# (piping directly loses the exit code under set -o pipefail when the
#  consumer always exits 0 — using a temp file avoids that).
TMPLOG=$(mktemp)
trap 'rm -f "${TMPLOG}"' EXIT

if ! git fetch "${GIT_REMOTE}" "${GIT_BRANCH}" > "${TMPLOG}" 2>&1; then
    while IFS= read -r line; do log "GIT" "$(sanitize_line "${line}")"; done < "${TMPLOG}"
    # Restore stash before aborting
    if [[ "${STASH_APPLIED}" == "true" ]]; then
        git stash pop || log "WARN" "Stash pop failed after fetch error — manual recovery needed."
    fi
    log_and_exit "git fetch failed (network/auth error)."
fi
while IFS= read -r line; do log "GIT" "$(sanitize_line "${line}")"; done < "${TMPLOG}"

# Determine current HEAD so we can report what changed
BEFORE_SHA=$(git rev-parse HEAD)

# Fast-forward only — never create a merge commit
if ! git merge --ff-only "${GIT_REMOTE}/${GIT_BRANCH}" > "${TMPLOG}" 2>&1; then
    while IFS= read -r line; do log "GIT" "$(sanitize_line "${line}")"; done < "${TMPLOG}"
    if [[ "${STASH_APPLIED}" == "true" ]]; then
        if git stash pop > /dev/null 2>&1; then
            # Check for conflict markers left by the stash pop
            if ! git diff --check > /dev/null 2>&1; then
                log "ERROR" "stash pop introduced conflict markers — manual intervention required"
                exit 1
            fi
        else
            log "WARN" "Stash pop failed after merge error — manual recovery needed."
        fi
    fi
    log_and_exit "git merge --ff-only failed. Local branch may have diverged from remote."
fi
while IFS= read -r line; do log "GIT" "$(sanitize_line "${line}")"; done < "${TMPLOG}"

AFTER_SHA=$(git rev-parse HEAD)

# ---------------------------------------------------------------------------
# Restore stash if we created one
# ---------------------------------------------------------------------------
if [[ "${STASH_APPLIED}" == "true" ]]; then
    if git stash pop; then
        log "WARN" "Auto-stash restored after pull. Investigate unexpected local changes."
    else
        log "WARN" "Stash pop failed after successful pull — stash entry still present. Inspect with 'git stash list'."
    fi
fi

# ---------------------------------------------------------------------------
# Report outcome
# ---------------------------------------------------------------------------
if [[ "${BEFORE_SHA}" == "${AFTER_SHA}" ]]; then
    log "INFO" "Already up to date (HEAD=${AFTER_SHA:0:10}). Nothing to do."
else
    COMMIT_COUNT=$(git rev-list --count "${BEFORE_SHA}..${AFTER_SHA}")
    log "INFO" "Sync complete: pulled ${COMMIT_COUNT} new commit(s). ${BEFORE_SHA:0:10}..${AFTER_SHA:0:10}"
fi

exit 0
