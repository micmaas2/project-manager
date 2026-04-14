"""
Unit tests for scripts/pm-healthcheck.sh
Tests mock each failure condition and verify exit code + label.
"""
import json
import os
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path to script under test
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).parent.parent.parent  # artefacts/task-027/../../
_SCRIPT = _REPO_ROOT / "scripts" / "pm-healthcheck.sh"


def run_healthcheck(workspace_root: Path) -> subprocess.CompletedProcess:
    """Run pm-healthcheck.sh against a custom workspace root."""
    return subprocess.run(
        ["bash", str(_SCRIPT), "--workspace-root", str(workspace_root)],
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# Fixture: minimal valid workspace
# ---------------------------------------------------------------------------
@pytest.fixture()
def workspace(tmp_path):
    """
    Build a minimal workspace under tmp_path — mirroring the real repo layout.
    All checks pass by default; individual tests break specific parts.

    Note: tmp_path resolves inside /tmp, which is outside the _WORKSPACE_ROOT
    used in pm-healthcheck.sh's Python inline — this is OK since the script
    uses its own --workspace-root flag, not _safe_path() validation.
    """
    # .git/hooks/ symlinks
    git_hooks = tmp_path / ".git" / "hooks"
    git_hooks.mkdir(parents=True)
    hooks_src = tmp_path / "hooks"
    hooks_src.mkdir()
    for hook in ("pre-commit", "commit-msg"):
        src = hooks_src / hook
        src.write_text("#!/usr/bin/env bash\n")
        (git_hooks / hook).symlink_to(src)

    # tasks/queue.json + schema
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["tasks"],
        "additionalProperties": False,
        "properties": {
            "$schema": {"type": "string"},
            "tasks": {"type": "array"},
        },
    }
    (tasks / "queue.schema.json").write_text(json.dumps(schema))
    (tasks / "queue.json").write_text(json.dumps({"tasks": []}))

    # .claude/agents/ with one valid YAML
    agents = tmp_path / ".claude" / "agents"
    agents.mkdir(parents=True)
    valid_yaml = textwrap.dedent("""\
        name: TestAgent
        model: claude-sonnet-4-6
        prompt: |
          Test agent prompt.
        policy:
          allowed_tools: [Read]
          max_tokens_per_run: 10000
          require_human_approval: false
          audit_logging: true
          external_calls_allowed: false
        owner: "Test"
        incident_owner: "Test"
    """)
    (agents / "test-agent.yaml").write_text(valid_yaml)

    # logs/ writable
    logs = tmp_path / "logs"
    logs.mkdir()

    return tmp_path


# ---------------------------------------------------------------------------
# Test 1: All checks pass
# ---------------------------------------------------------------------------
def test_all_pass(workspace):
    result = run_healthcheck(workspace)
    assert result.returncode == 0, f"Expected exit 0, got {result.returncode}\n{result.stdout}"
    assert "[FAIL]" not in result.stdout
    assert "ALL CHECKS PASSED" in result.stdout


# ---------------------------------------------------------------------------
# Test 2: Missing hook symlink triggers exit 1 with HOOKS label
# ---------------------------------------------------------------------------
def test_missing_hook_symlink(workspace):
    link = workspace / ".git" / "hooks" / "pre-commit"
    link.unlink()  # remove the symlink

    result = run_healthcheck(workspace)
    assert result.returncode == 1
    assert "[FAIL] HOOKS" in result.stdout
    assert "pre-commit" in result.stdout


# ---------------------------------------------------------------------------
# Test 3: Invalid queue.json triggers exit 1 with SCHEMA label
# ---------------------------------------------------------------------------
def test_invalid_queue_json(workspace):
    # Write a queue.json that violates the "required: tasks" constraint
    (workspace / "tasks" / "queue.json").write_text(json.dumps({"wrong_key": []}))

    result = run_healthcheck(workspace)
    assert result.returncode == 1
    assert "[FAIL] SCHEMA" in result.stdout


# ---------------------------------------------------------------------------
# Test 4: Malformed YAML triggers exit 1 with YAML label
# ---------------------------------------------------------------------------
def test_malformed_yaml(workspace):
    bad_yaml = "name: BadAgent\nprompt: |\n  text\npolicy:\n  bad: [unclosed\n"
    (workspace / ".claude" / "agents" / "bad-agent.yaml").write_text(bad_yaml)

    result = run_healthcheck(workspace)
    assert result.returncode == 1
    assert "[FAIL] YAML" in result.stdout
    assert "bad-agent.yaml" in result.stdout


# ---------------------------------------------------------------------------
# Test 5: Missing policy fields in YAML triggers exit 1 with YAML label
# ---------------------------------------------------------------------------
def test_yaml_missing_policy_field(workspace):
    incomplete_yaml = textwrap.dedent("""\
        name: IncompleteAgent
        model: claude-sonnet-4-6
        prompt: |
          Prompt text.
        policy:
          allowed_tools: [Read]
          max_tokens_per_run: 10000
          # missing: require_human_approval, audit_logging, external_calls_allowed
        owner: "Test"
        incident_owner: "Test"
    """)
    (workspace / ".claude" / "agents" / "incomplete.yaml").write_text(incomplete_yaml)

    result = run_healthcheck(workspace)
    assert result.returncode == 1
    assert "[FAIL] YAML" in result.stdout
    assert "incomplete.yaml" in result.stdout


# ---------------------------------------------------------------------------
# Test 6: Unwritable logs/ triggers exit 1 with LOGS label
# ---------------------------------------------------------------------------
def test_unwritable_logs(workspace):
    # Replace logs/ directory with a regular file so touch inside it fails
    # (chmod alone won't work when tests run as root — root bypasses DAC)
    logs = workspace / "logs"
    shutil.rmtree(logs)
    logs.write_text("not a directory\n")  # now logs is a file, not a dir

    result = run_healthcheck(workspace)
    assert result.returncode == 1
    assert "[FAIL] LOGS" in result.stdout


# ---------------------------------------------------------------------------
# Test 7: Idempotency — running twice gives same result
# ---------------------------------------------------------------------------
def test_idempotent(workspace):
    r1 = run_healthcheck(workspace)
    r2 = run_healthcheck(workspace)
    assert r1.returncode == r2.returncode == 0
    assert r1.stdout == r2.stdout
