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

# Parse and summarise: group by agent + action, count occurrences
echo "=== Audit Log Summary ==="
echo "File: ${LOG_FILE}"
echo ""

jq -r '.agent + "\t" + .action' "${LOG_FILE}" \
  | sort \
  | uniq -c \
  | sort -rn \
  | awk '{printf "  %-5s %-25s %s\n", $1, $3, $2}' \
  | sed 's/^//' \
  | { echo "Count  Action                    Agent"; echo "-----  ------------------------  -------------------------"; cat; }

echo ""
echo "Total entries: $(wc -l < "${LOG_FILE}")"
