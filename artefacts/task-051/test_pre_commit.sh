#!/usr/bin/env bash
# test_pre_commit.sh — Test suite for /opt/claude/CCAS/hooks/pre-commit
# Run from anywhere; does not modify any sub-repo state.
#
# Tests:
#   (a) Staged valid YAML     → exit 0     [SKIP: requires ansible-lint installed]
#   (b) Staged invalid YAML   → non-zero   [SKIP: requires ansible-lint installed]
#   (c) No YAML staged        → exit 0     [RUNS: mock ansible-lint]
#   (d) ansible-lint absent   → non-zero + correct message  [RUNS always]

set -euo pipefail

HOOK="/opt/claude/CCAS/hooks/pre-commit"
PASS=0
FAIL=0
SKIP=0

pass() { echo "  PASS: $1"; PASS=$((PASS+1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }
skip() { echo "  SKIP: $1 [requires ansible-lint installed]"; SKIP=$((SKIP+1)); }

echo "=== CCAS pre-commit hook test suite ==="
echo ""

# ---------------------------------------------------------------------------
# Helper: create a temp dir with a mock ansible-lint binary
# ---------------------------------------------------------------------------
make_mock_ansible_lint() {
  local exitcode="$1"
  local tmpdir
  tmpdir=$(mktemp -d)
  cat > "$tmpdir/ansible-lint" << EOF
#!/bin/bash
exit $exitcode
EOF
  chmod +x "$tmpdir/ansible-lint"
  echo "$tmpdir"
}

# ---------------------------------------------------------------------------
# Test (a): Staged valid YAML → ansible-lint exits 0 → hook exits 0
# ---------------------------------------------------------------------------
echo "Test (a): Staged valid YAML → expect exit 0"
if command -v ansible-lint >/dev/null 2>&1; then
  TMPDIR_REPO=$(mktemp -d)
  git -C "$TMPDIR_REPO" init -q
  cat > "$TMPDIR_REPO/site.yml" << 'YAML'
---
- name: Valid play
  hosts: all
  tasks: []
YAML
  git -C "$TMPDIR_REPO" add site.yml
  cd "$TMPDIR_REPO"
  if bash "$HOOK" 2>&1; then
    pass "Staged valid YAML exits 0"
  else
    fail "Staged valid YAML returned non-zero"
  fi
  cd /tmp
  rm -rf "$TMPDIR_REPO"
else
  skip "Test (a): Staged valid YAML — ansible-lint not installed"
fi

# ---------------------------------------------------------------------------
# Test (b): Staged invalid YAML → ansible-lint exits non-zero → hook exits non-zero
# ---------------------------------------------------------------------------
echo "Test (b): Staged invalid YAML → expect non-zero"
if command -v ansible-lint >/dev/null 2>&1; then
  TMPDIR_REPO=$(mktemp -d)
  git -C "$TMPDIR_REPO" init -q
  # Deliberately bad: no 'name', uses bare command instead of module
  cat > "$TMPDIR_REPO/bad.yml" << 'YAML'
---
- hosts: all
  tasks:
    - command: echo hello
YAML
  git -C "$TMPDIR_REPO" add bad.yml
  cd "$TMPDIR_REPO"
  if bash "$HOOK" 2>&1; then
    fail "Expected non-zero for invalid YAML, got 0"
  else
    pass "Staged invalid YAML blocks commit (non-zero exit)"
  fi
  cd /tmp
  rm -rf "$TMPDIR_REPO"
else
  skip "Test (b): Staged invalid YAML — ansible-lint not installed"
fi

# ---------------------------------------------------------------------------
# Test (c): No YAML staged → hook exits 0 (skips lint entirely)
# ---------------------------------------------------------------------------
echo "Test (c): No YAML staged → expect exit 0"
# Use a real sub-repo CWD (nothing staged), with mock ansible-lint in PATH
MOCK_DIR=$(make_mock_ansible_lint 0)
cd /opt/claude/CCAS/ccas-main
if PATH="$MOCK_DIR:$PATH" bash "$HOOK" 2>&1; then
  pass "No staged YAML exits 0"
else
  fail "No staged YAML returned non-zero (unexpected)"
fi
rm -rf "$MOCK_DIR"

# ---------------------------------------------------------------------------
# Test (d): ansible-lint absent → hook exits non-zero + correct message
# ---------------------------------------------------------------------------
echo "Test (d): ansible-lint absent → expect non-zero + error message"
EMPTY_DIR=$(mktemp -d)
OUTPUT=$(PATH="$EMPTY_DIR:$PATH" bash "$HOOK" 2>&1 || true)
EXIT_CODE=$(PATH="$EMPTY_DIR:$PATH" bash "$HOOK" 2>&1; echo $?)
# Re-run cleanly to capture exit code
set +e
PATH="$EMPTY_DIR:$PATH" bash "$HOOK" 2>/tmp/test_d_stderr
D_EXIT=$?
set -e
D_MSG=$(cat /tmp/test_d_stderr)
rm -rf "$EMPTY_DIR" /tmp/test_d_stderr

if [ "$D_EXIT" -ne 0 ]; then
  pass "ansible-lint absent exits non-zero (exit $D_EXIT)"
else
  fail "ansible-lint absent returned 0 (expected non-zero)"
fi

EXPECTED_MSG="ansible-lint not installed"
if echo "$D_MSG" | grep -q "$EXPECTED_MSG"; then
  pass "Error message contains: '$EXPECTED_MSG'"
else
  fail "Error message missing expected text. Got: $D_MSG"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "=== Results ==="
echo "  Passed: $PASS"
echo "  Failed: $FAIL"
echo "  Skipped: $SKIP (require ansible-lint installed)"
echo ""
if [ "$FAIL" -gt 0 ]; then
  echo "OVERALL: FAIL ($FAIL test(s) failed)"
  exit 1
else
  echo "OVERALL: PASS"
  exit 0
fi
