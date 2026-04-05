#!/usr/bin/env bash
# audit-summary.sh — Print a summary of agent actions from logs/audit.jsonl
# Grouped by agent name and action type.
# Usage: ./audit-summary.sh [path/to/audit.jsonl]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_LOG="${SCRIPT_DIR}/../../logs/audit.jsonl"
LOG_FILE="${1:-${DEFAULT_LOG}}"

# Preflight: require jq
if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: jq is required but not installed. Install jq >= 1.6 and retry." >&2
  exit 1
fi

# Handle missing or empty log file
if [[ ! -f "${LOG_FILE}" ]]; then
  echo "Audit log not found: ${LOG_FILE}"
  echo "No entries to summarise."
  exit 0
fi

if [[ ! -s "${LOG_FILE}" ]]; then
  echo "Audit log is empty: ${LOG_FILE}"
  echo "No entries to summarise."
  exit 0
fi

# Parse and summarise: group by agent + action, count occurrences.
# Uses jq to emit TSV (safe against spaces in field values), then counts
# with sort|uniq -c and formats with awk.
echo "=== Audit Log Summary ==="
echo "File: ${LOG_FILE}"
echo ""

# jq filters out malformed/non-JSON lines via try; emits agent<TAB>action per valid entry
valid_entries=$(jq -Rr 'try (fromjson | [.agent, .action] | @tsv)' "${LOG_FILE}")

printf "%-6s %-25s %s\n" "Count" "Action" "Agent"
printf "%-6s %-25s %s\n" "-----" "------------------------" "-------------------------"

echo "${valid_entries}" \
  | sort \
  | uniq -c \
  | sort -rn \
  | while IFS= read -r line; do
      count=$(echo "${line}" | awk '{print $1}')
      agent=$(echo "${line}" | awk '{print $2}')
      action=$(echo "${line}" | awk '{print $3}')
      printf "%-6s %-25s %s\n" "${count}" "${action}" "${agent}"
    done

echo ""
total=$(echo "${valid_entries}" | grep -c . 2>/dev/null || echo 0)
echo "Total entries: ${total}"
