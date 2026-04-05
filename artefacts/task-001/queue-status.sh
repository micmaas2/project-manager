#!/usr/bin/env bash
# queue-status.sh
# Reads tasks/queue.json and prints a task count summary grouped by status.
# Part of task-001: Queue status reporter script
# Acceptance criteria:
#   1. Exits 0 and prints counts for all 6 statuses
#   2. Handles empty queue gracefully (zero counts, no errors)
#   3. Passes bash -n and shellcheck with no warnings

set -euo pipefail

QUEUE_FILE="${1:-tasks/queue.json}"

# Validate the queue file exists and is readable
if [[ ! -f "${QUEUE_FILE}" ]]; then
    echo "Error: queue file not found: ${QUEUE_FILE}" >&2
    exit 1
fi

# Parse counts using jq; fall back to 0 if jq is unavailable or file is malformed
if ! command -v jq >/dev/null 2>&1; then
    echo "Error: jq is required but not installed." >&2
    exit 1
fi

# Extract task array; handle missing/null .tasks gracefully
task_count=$(jq '.tasks | if . == null then 0 else length end' "${QUEUE_FILE}" 2>/dev/null) || task_count=0

count_status() {
    local status="$1"
    jq --arg s "${status}" \
        '[.tasks[]? | select(.status == $s)] | length' \
        "${QUEUE_FILE}" 2>/dev/null || echo 0
}

pending=$(count_status "pending")
in_progress=$(count_status "in_progress")
paused=$(count_status "paused")
review=$(count_status "review")
test=$(count_status "test")
done_count=$(count_status "done")

echo "Queue Status Report"
echo "==================="
printf "%-15s %s\n" "Status" "Count"
printf "%-15s %s\n" "------" "-----"
printf "%-15s %d\n" "pending"     "${pending}"
printf "%-15s %d\n" "in_progress" "${in_progress}"
printf "%-15s %d\n" "paused"      "${paused}"
printf "%-15s %d\n" "review"      "${review}"
printf "%-15s %d\n" "test"        "${test}"
printf "%-15s %d\n" "done"        "${done_count}"
echo "-------------------"
printf "%-15s %d\n" "TOTAL"       "${task_count}"
