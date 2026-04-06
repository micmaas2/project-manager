#!/usr/bin/env bash
# generate-dashboard.sh — Project Dashboard generator
# Reads queue.json, backlog.md, maintenance-schedule.md and produces a
# markdown dashboard, writing it locally and optionally pushing to Pi4.
#
# Usage:
#   ./generate-dashboard.sh            # generate + push to Pi4 via SSH
#   ./generate-dashboard.sh --local-only  # generate local copy only (no SSH)

set -euo pipefail

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PM_DIR="/opt/claude/project_manager"
QUEUE_JSON="${PM_DIR}/tasks/queue.json"
BACKLOG_MD="${PM_DIR}/tasks/backlog.md"
MAINT_MD="${PM_DIR}/docs/maintenance-schedule.md"
PREVIEW_DIR="${PM_DIR}/artefacts/task-006"
PREVIEW_FILE="${PREVIEW_DIR}/dashboard-preview.md"

PI4_VAULT_PATH="/opt/obsidian-vault/Dashboard.md"

# ---------------------------------------------------------------------------
# Flags
# ---------------------------------------------------------------------------
LOCAL_ONLY=false
for arg in "$@"; do
  if [[ "${arg}" == "--local-only" ]]; then
    LOCAL_ONLY=true
  fi
done

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
no_data_section() {
  local section="${1}"
  echo "_No data available for ${section}._"
}

# ---------------------------------------------------------------------------
# Timestamp
# ---------------------------------------------------------------------------
TIMESTAMP="$(date '+%Y-%m-%d %H:%M')"

# ---------------------------------------------------------------------------
# Section 1: Queue Status table + Active Tasks + Recently Completed + Next Up
# ---------------------------------------------------------------------------
build_queue_sections() {
  if [[ ! -f "${QUEUE_JSON}" ]]; then
    cat <<EOF
## Queue Status

$(no_data_section "Queue Status (file not found)")

## Active Tasks

$(no_data_section "Active Tasks (file not found)")

## Recently Completed

$(no_data_section "Recently Completed (file not found)")

## Next Up (Pending)

$(no_data_section "Next Up (file not found)")
EOF
    return
  fi

  # Count per status
  local pending in_progress paused review test done_count
  pending="$(jq '[.tasks[] | select(.status=="pending")] | length' "${QUEUE_JSON}")"
  in_progress="$(jq '[.tasks[] | select(.status=="in_progress")] | length' "${QUEUE_JSON}")"
  paused="$(jq '[.tasks[] | select(.status=="paused")] | length' "${QUEUE_JSON}")"
  review="$(jq '[.tasks[] | select(.status=="review")] | length' "${QUEUE_JSON}")"
  test="$(jq '[.tasks[] | select(.status=="test")] | length' "${QUEUE_JSON}")"
  done_count="$(jq '[.tasks[] | select(.status=="done")] | length' "${QUEUE_JSON}")"

  cat <<EOF
## Queue Status

| Status | Count |
|---|---|
| pending | ${pending} |
| in_progress | ${in_progress} |
| paused | ${paused} |
| review | ${review} |
| test | ${test} |
| done | ${done_count} |
EOF

  # Active Tasks (in_progress)
  echo ""
  echo "## Active Tasks"
  echo ""
  local active_tasks
  active_tasks="$(jq -r '.tasks[] | select(.status=="in_progress") | "- **\(.id)** [\(.project)] \(.title) — \(.assigned_to)"' "${QUEUE_JSON}")"
  if [[ -z "${active_tasks}" ]]; then
    echo "_No tasks currently in progress._"
  else
    echo "${active_tasks}"
  fi

  # Recently Completed (last 5 done, most recent first by updated field)
  echo ""
  echo "## Recently Completed"
  echo ""
  local recent_done
  recent_done="$(jq -r '[.tasks[] | select(.status=="done")] | sort_by(.updated) | reverse | .[0:5][] | "- **\(.id)** \(.title) [\(.updated[0:10])]"' "${QUEUE_JSON}")"
  if [[ -z "${recent_done}" ]]; then
    echo "_No completed tasks._"
  else
    echo "${recent_done}"
  fi

  # Next Up (pending)
  echo ""
  echo "## Next Up (Pending)"
  echo ""
  local pending_tasks
  pending_tasks="$(jq -r '.tasks[] | select(.status=="pending") | "- **\(.id)** [\(.project)] \(.title)"' "${QUEUE_JSON}")"
  if [[ -z "${pending_tasks}" ]]; then
    echo "_No pending tasks._"
  else
    echo "${pending_tasks}"
  fi
}

# ---------------------------------------------------------------------------
# Section 2: Maintenance — Due Soon
# Extract rows from the maintenance schedule tables where Status column
# contains "due", "overdue", or "blocked", and show the Next due date.
# We look at the table rows (lines starting with |) that have a "Next due"
# column. The column order in Weekly/Monthly tables is:
#   | # | Activity | Project | Command | Last run | Next due | Status |
# Quarterly table has a similar structure.
# We capture rows where Status (last column before trailing |) is due/overdue/blocked.
# ---------------------------------------------------------------------------
build_maintenance_section() {
  echo "## Maintenance — Due Soon"
  echo ""

  if [[ ! -f "${MAINT_MD}" ]]; then
    no_data_section "Maintenance (file not found)"
    return
  fi

  # Parse table rows with awk:
  # - Skip header rows (containing "Activity" or "---")
  # - Split on "|", trim whitespace
  # - Status is the last non-empty field before trailing pipe
  # - Collect rows where status matches due/overdue/blocked (case-insensitive)
  # - Print: Activity — due NextDue
  local results
  results="$(awk -F'|' '
    /^\|/ && !/Activity/ && !/^[[:space:]]*\|[[:space:]]*-/ {
      # Reset and build array of trimmed fields (skip index 0 which is before first |)
      delete fields
      n = 0
      for (i = 2; i <= NF; i++) {
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", $i)
        if ($i != "") {
          fields[n++] = $i
        }
      }
      # Need at least 5 fields: #, Activity, Project, ..., Status
      if (n >= 5) {
        status = fields[n-1]
        if (status ~ /^(due|overdue|blocked)$/) {
          # Find "Next due" field — it is the second-to-last field in
          # weekly/monthly tables (fields[n-2]), or "Next planned" for quarterly
          next_due = fields[n-2]
          activity = fields[1]
          print "- " activity " — due " next_due
        }
      }
    }
  ' "${MAINT_MD}" | head -5)"

  if [[ -z "${results}" ]]; then
    echo "_No items due soon._"
  else
    echo "${results}"
  fi
}

# ---------------------------------------------------------------------------
# Section 3: Top Backlog (P1, not yet queued)
# Parse backlog.md table rows with Priority=P1 and Status in new/discovered/planned
# Exclude items whose IDs are already present in queue.json.
# ---------------------------------------------------------------------------
build_backlog_section() {
  echo "## Top Backlog (P1, not yet queued)"
  echo ""

  if [[ ! -f "${BACKLOG_MD}" ]]; then
    no_data_section "Backlog (file not found)"
    return
  fi

  # Collect task IDs already in queue (to exclude them)
  local queued_ids=""
  if [[ -f "${QUEUE_JSON}" ]]; then
    queued_ids="$(jq -r '.tasks[].id' "${QUEUE_JSON}" | tr '\n' '|' | sed 's/|$//')"
  fi

  # Parse the Backlog Items table
  # Columns: | ID | Epic | Title | Project | Priority | Status | Added |
  local results
  results="$(awk -F'|' -v queued="${queued_ids}" '
    /^\|/ && !/ID/ && !/^[[:space:]]*\|[[:space:]]*-/ {
      delete fields
      n = 0
      for (i = 2; i <= NF; i++) {
        gsub(/^[[:space:]]+|[[:space:]]+$/, "", $i)
        if ($i != "") {
          fields[n++] = $i
        }
      }
      # Expect: ID, Epic, Title, Project, Priority, Status, Added (7 fields)
      if (n >= 6) {
        id       = fields[0]
        title    = fields[2]
        project  = fields[3]
        priority = fields[4]
        status   = fields[5]

        # Only P1 items
        if (priority != "P1") next

        # Only new/discovered/planned status
        if (status !~ /^(new|discovered|planned)$/) next

        # Skip if already in queue
        if (queued != "" && id ~ queued) next

        print "- " id ": " title " [" project "]"
      }
    }
  ' "${BACKLOG_MD}" | head -5)"

  if [[ -z "${results}" ]]; then
    echo "_No P1 backlog items pending._"
  else
    echo "${results}"
  fi
}

# ---------------------------------------------------------------------------
# Assemble dashboard
# ---------------------------------------------------------------------------
build_dashboard() {
  echo "# Project Dashboard"
  echo "_Last updated: ${TIMESTAMP}_"
  echo ""
  build_queue_sections
  echo ""
  build_maintenance_section
  echo ""
  build_backlog_section
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
  # Ensure preview dir exists
  mkdir -p "${PREVIEW_DIR}"

  # Generate dashboard content
  local dashboard
  dashboard="$(build_dashboard)"

  # Write local preview
  printf '%s\n' "${dashboard}" > "${PREVIEW_FILE}"
  echo "[generate-dashboard] Local preview written to ${PREVIEW_FILE}" >&2

  # Optionally push to Pi4
  if [[ "${LOCAL_ONLY}" == "false" ]]; then
    echo "[generate-dashboard] Pushing to Pi4 at ${PI4_VAULT_PATH}..." >&2
    printf '%s\n' "${dashboard}" \
      | ssh -o BatchMode=yes -o ConnectTimeout=10 pi4 \
          "cat > ${PI4_VAULT_PATH}"
    echo "[generate-dashboard] Pi4 write complete." >&2
  else
    echo "[generate-dashboard] --local-only: skipping SSH push." >&2
  fi
}

main "$@"
