#!/usr/bin/env bash
# pm-healthcheck.sh — System health checks for the project-manager MAS.
# Exits 0 when all checks pass; exits 1 with labelled per-check output on failure.
#
# Checks:
#   1. HOOKS     — .git/hooks symlinks point to hooks/ sources
#   2. SCHEMA    — tasks/queue.json validates against tasks/queue.schema.json
#   3. YAML      — each .claude/agents/*.yaml parses cleanly + has 5 policy fields
#   4. LOGS      — logs/ directory exists and is writable
#
# Usage: bash scripts/pm-healthcheck.sh [--workspace-root <path>]
#        Default workspace root: directory of this script's parent (repo root)

set -euo pipefail

# ---------------------------------------------------------------------------
# Resolve workspace root
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_WORKSPACE_ROOT="${SCRIPT_DIR%/scripts}"   # one level up from scripts/

# Allow override for testing
while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace-root) _WORKSPACE_ROOT="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
PASS=0
FAIL=0

check_pass() { echo "[PASS] $1"; }
check_fail() { echo "[FAIL] $1"; FAIL=$((FAIL + 1)); }

# ---------------------------------------------------------------------------
# Check 1: Git hook symlinks
# ---------------------------------------------------------------------------
run_check_hooks() {
  local ok=1
  local hooks_dir="${_WORKSPACE_ROOT}/hooks"
  local git_hooks_dir="${_WORKSPACE_ROOT}/.git/hooks"

  for hook in pre-commit commit-msg; do
    local link="${git_hooks_dir}/${hook}"
    local target="${hooks_dir}/${hook}"

    if [[ ! -L "${link}" ]]; then
      check_fail "HOOKS: .git/hooks/${hook} is not a symlink (expected link → ${target})"
      ok=0
    elif [[ "$(readlink -f "${link}")" != "$(readlink -f "${target}")" ]]; then
      check_fail "HOOKS: .git/hooks/${hook} symlink target mismatch (got: $(readlink "${link}"), expected: ${target})"
      ok=0
    else
      check_pass "HOOKS: .git/hooks/${hook} → hooks/${hook}"
    fi
  done
  return $((1 - ok))
}

# ---------------------------------------------------------------------------
# Check 2: queue.json schema validation
# ---------------------------------------------------------------------------
run_check_schema() {
  local queue_file="${_WORKSPACE_ROOT}/tasks/queue.json"
  local schema_file="${_WORKSPACE_ROOT}/tasks/queue.schema.json"

  if [[ ! -f "${queue_file}" ]]; then
    check_fail "SCHEMA: tasks/queue.json not found"
    return 1
  fi
  if [[ ! -f "${schema_file}" ]]; then
    check_fail "SCHEMA: tasks/queue.schema.json not found"
    return 1
  fi

  local result
  result=$(python3 - "${queue_file}" "${schema_file}" <<'PYEOF'
import sys, json
try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema not installed")
    sys.exit(2)

queue_path, schema_path = sys.argv[1], sys.argv[2]
try:
    queue  = json.load(open(queue_path))
    schema = json.load(open(schema_path))
except json.JSONDecodeError as e:
    print(f"JSON parse error: {e}")
    sys.exit(1)

try:
    jsonschema.validate(queue, schema)
    print("OK")
    sys.exit(0)
except jsonschema.ValidationError as e:
    print(f"ValidationError: {e.message} (path: {list(e.absolute_path)})")
    sys.exit(1)
PYEOF
  )

  local rc=$?
  if [[ $rc -eq 0 ]]; then
    check_pass "SCHEMA: tasks/queue.json validates against schema"
  elif [[ $rc -eq 2 ]]; then
    check_fail "SCHEMA: jsonschema package not available — install with: pip3 install jsonschema"
    return 1
  else
    check_fail "SCHEMA: tasks/queue.json invalid — ${result}"
    return 1
  fi
}

# ---------------------------------------------------------------------------
# Check 3: Agent YAML parsing + required policy fields
# ---------------------------------------------------------------------------
_REQUIRED_POLICY_FIELDS="allowed_tools max_tokens_per_run require_human_approval audit_logging external_calls_allowed"

run_check_yaml() {
  local agents_dir="${_WORKSPACE_ROOT}/.claude/agents"
  local all_ok=1

  if [[ ! -d "${agents_dir}" ]]; then
    check_fail "YAML: .claude/agents/ directory not found"
    return 1
  fi

  local yaml_files
  mapfile -t yaml_files < <(find "${agents_dir}" -name "*.yaml" | sort)

  if [[ ${#yaml_files[@]} -eq 0 ]]; then
    check_fail "YAML: No .yaml files found in .claude/agents/"
    return 1
  fi

  for yaml_file in "${yaml_files[@]}"; do
    local fname
    fname="$(basename "${yaml_file}")"
    local result
    result=$(python3 - "${yaml_file}" ${_REQUIRED_POLICY_FIELDS} <<'PYEOF'
import sys, yaml as _yaml

path = sys.argv[1]
required_fields = sys.argv[2:]

try:
    with open(path) as f:
        doc = _yaml.safe_load(f)
except _yaml.YAMLError as e:
    print(f"YAMLError: {e}")
    sys.exit(1)

if not isinstance(doc, dict):
    print("Not a mapping at top level")
    sys.exit(1)

policy = doc.get("policy")
if not isinstance(policy, dict):
    print("Missing or invalid 'policy' key")
    sys.exit(1)

missing = [f for f in required_fields if f not in policy]
if missing:
    print(f"Missing policy fields: {missing}")
    sys.exit(1)

print("OK")
sys.exit(0)
PYEOF
    )
    local rc=$?
    if [[ $rc -eq 0 ]]; then
      check_pass "YAML: ${fname}"
    else
      check_fail "YAML: ${fname} — ${result}"
      all_ok=0
    fi
  done

  return $((1 - all_ok))
}

# ---------------------------------------------------------------------------
# Check 4: logs/ writability
# ---------------------------------------------------------------------------
run_check_logs() {
  local logs_dir="${_WORKSPACE_ROOT}/logs"

  if [[ ! -d "${logs_dir}" ]]; then
    check_fail "LOGS: logs/ directory not found"
    return 1
  fi

  local probe_file="${logs_dir}/.healthcheck_probe_$$"
  if touch "${probe_file}" 2>/dev/null; then
    rm -f "${probe_file}"
    check_pass "LOGS: logs/ is writable"
  else
    check_fail "LOGS: logs/ is not writable (touch failed)"
    return 1
  fi
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
echo "=== pm-healthcheck ==="
echo "Workspace: ${_WORKSPACE_ROOT}"
echo ""

run_check_hooks    || true
run_check_schema   || true
run_check_yaml     || true
run_check_logs     || true

echo ""
if [[ $FAIL -eq 0 ]]; then
  echo "RESULT: ALL CHECKS PASSED"
  exit 0
else
  echo "RESULT: ${FAIL} CHECK(S) FAILED"
  exit 1
fi
