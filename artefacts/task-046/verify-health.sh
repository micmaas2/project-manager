#!/usr/bin/env bash
# verify-health.sh — task-046: MAS backend /health endpoint verification
#
# Usage:
#   ./verify-health.sh               # check https://mas.femic.nl/api/health (default)
#   HEALTH_URL=http://... ./verify-health.sh  # override URL for local testing
#
# Exit codes:
#   0 — HTTP 200 received (endpoint healthy)
#   1 — Non-200 HTTP status or connection failure

set -euo pipefail

HEALTH_URL="${HEALTH_URL:-https://mas.femic.nl/api/health}"
TIMEOUT=10

echo "Checking MAS /health endpoint: ${HEALTH_URL}"

HTTP_CODE=$(curl \
  --silent \
  --output /dev/null \
  --write-out "%{http_code}" \
  --max-time "${TIMEOUT}" \
  "${HEALTH_URL}" 2>/dev/null) || HTTP_CODE="000"

if [[ "${HTTP_CODE}" == "200" ]]; then
  echo "OK — HTTP ${HTTP_CODE}: endpoint is healthy"
  exit 0
else
  echo "FAIL — HTTP ${HTTP_CODE}: endpoint returned non-200 (or connection failed)"
  exit 1
fi
