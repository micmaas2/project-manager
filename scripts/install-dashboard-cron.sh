#!/usr/bin/env bash
# install-dashboard-cron.sh — installs a crontab entry to run the
# dashboard generator every 15 minutes.
#
# Usage: ./install-dashboard-cron.sh
# Idempotent: running multiple times will not duplicate the entry.

set -euo pipefail

CRON_CMD="/opt/claude/project_manager/scripts/generate-dashboard.sh"
CRON_LOG="/opt/claude/project_manager/logs/dashboard.log"
CRON_ENTRY="*/15 * * * * ${CRON_CMD} >> ${CRON_LOG} 2>&1"

# Ensure log directory exists
mkdir -p "$(dirname "${CRON_LOG}")"

# Load existing crontab (suppress error if none exists)
EXISTING_CRON="$(crontab -l 2>/dev/null || true)"

if echo "${EXISTING_CRON}" | grep -qF "${CRON_CMD}"; then
  echo "[install-dashboard-cron] Entry already present in crontab — no change made."
else
  # Append new entry
  (echo "${EXISTING_CRON}"; echo "${CRON_ENTRY}") | crontab -
  echo "[install-dashboard-cron] Crontab entry installed:"
  echo "  ${CRON_ENTRY}"
fi

echo "[install-dashboard-cron] Current crontab:"
crontab -l
