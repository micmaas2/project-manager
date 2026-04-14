"""
Unit tests for scripts/token-dashboard.py
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent
_SCRIPT = _REPO_ROOT / "scripts" / "token-dashboard.py"


def run_dashboard(workspace_root: Path, extra_args: list[str] | None = None) -> subprocess.CompletedProcess:
    """Run token-dashboard.py against a custom workspace root."""
    cmd = [sys.executable, str(_SCRIPT), "--workspace-root", str(workspace_root)]
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(cmd, capture_output=True, text=True)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
def _make_queue(tmp_path: Path, tasks: list[dict]) -> None:
    q = {"tasks": tasks}
    (tmp_path / "tasks").mkdir(exist_ok=True)
    (tmp_path / "tasks" / "queue.json").write_text(json.dumps(q))


def _make_log(tmp_path: Path, entries: list[dict]) -> None:
    (tmp_path / "logs").mkdir(exist_ok=True)
    lines = "\n".join(json.dumps(e) for e in entries)
    (tmp_path / "logs" / "token_log.jsonl").write_text(lines + "\n" if lines else "")


@pytest.fixture()
def workspace(tmp_path):
    """Minimal workspace: empty queue + empty log."""
    _make_queue(tmp_path, [])
    _make_log(tmp_path, [])
    return tmp_path


# ---------------------------------------------------------------------------
# Test 1: Empty log → "(no token log entries)"
# ---------------------------------------------------------------------------
def test_empty_log(workspace):
    result = run_dashboard(workspace)
    assert result.returncode == 0
    assert "no token log entries" in result.stdout


# ---------------------------------------------------------------------------
# Test 2: Single entry at 50% → row present, no WARN
# ---------------------------------------------------------------------------
def test_single_entry_no_warn(tmp_path):
    _make_queue(tmp_path, [{"id": "task-001", "token_estimate": 8000}])
    _make_log(tmp_path, [
        {"task_id": "task-001", "agent": "Builder", "token_estimate": 4000},
    ])
    result = run_dashboard(tmp_path)
    assert result.returncode == 0
    assert "task-001" in result.stdout
    assert "Builder" in result.stdout
    assert "WARN" not in result.stdout
    assert "50%" in result.stdout


# ---------------------------------------------------------------------------
# Test 3: Multiple tasks → multiple rows, sorted by task_id
# ---------------------------------------------------------------------------
def test_multiple_tasks(tmp_path):
    _make_queue(tmp_path, [
        {"id": "task-001", "token_estimate": 8000},
        {"id": "task-002", "token_estimate": 6000},
    ])
    _make_log(tmp_path, [
        {"task_id": "task-002", "agent": "Builder",        "token_estimate": 2000},
        {"task_id": "task-001", "agent": "ProjectManager", "token_estimate": 3000},
        {"task_id": "task-001", "agent": "ProjectManager", "token_estimate": 1000},  # cumulative: 4000
    ])
    result = run_dashboard(tmp_path)
    assert result.returncode == 0
    lines = result.stdout.splitlines()
    # task-001 row should appear before task-002 (sorted)
    idx_001 = next(i for i, l in enumerate(lines) if "task-001" in l)
    idx_002 = next(i for i, l in enumerate(lines) if "task-002" in l)
    assert idx_001 < idx_002
    # Grand total: 4000 + 2000 = 6000
    assert "6,000" in result.stdout or "6000" in result.stdout
    assert "2 task" in result.stdout


# ---------------------------------------------------------------------------
# Test 4: >80% threshold → row contains WARN
# ---------------------------------------------------------------------------
def test_warn_threshold(tmp_path):
    _make_queue(tmp_path, [{"id": "task-003", "token_estimate": 10000}])
    _make_log(tmp_path, [
        {"task_id": "task-003", "agent": "Builder", "token_estimate": 8500},  # 85%
    ])
    result = run_dashboard(tmp_path)
    assert result.returncode == 0
    assert "WARN" in result.stdout
    assert "task-003" in result.stdout
    assert "85%" in result.stdout


# ---------------------------------------------------------------------------
# Test 5: Missing log file → exit 0 with "(no token log entries)"
# ---------------------------------------------------------------------------
def test_missing_log_file(tmp_path):
    _make_queue(tmp_path, [])
    # Do NOT create logs/ at all
    result = run_dashboard(tmp_path)
    assert result.returncode == 0
    assert "no token log entries" in result.stdout


# ---------------------------------------------------------------------------
# Test 6: Malformed JSON line is skipped gracefully
# ---------------------------------------------------------------------------
def test_malformed_line_skipped(tmp_path):
    _make_queue(tmp_path, [{"id": "task-001", "token_estimate": 8000}])
    (tmp_path / "logs").mkdir()
    log_file = tmp_path / "logs" / "token_log.jsonl"
    log_file.write_text(
        '{"task_id":"task-001","agent":"Builder","token_estimate":3000}\n'
        'NOT_VALID_JSON\n'
        '{"task_id":"task-001","agent":"Builder","token_estimate":1000}\n'
    )
    result = run_dashboard(tmp_path)
    assert result.returncode == 0
    # Valid lines processed: 3000 + 1000 = 4000 → 50% of 8000
    assert "task-001" in result.stdout
    assert "4,000" in result.stdout or "4000" in result.stdout


# ---------------------------------------------------------------------------
# Test 7: --last-n limits lines read
# ---------------------------------------------------------------------------
def test_last_n_flag(tmp_path):
    _make_queue(tmp_path, [{"id": "task-001", "token_estimate": 10000}])
    _make_log(tmp_path, [
        {"task_id": "task-001", "agent": "Builder", "token_estimate": 5000},
        {"task_id": "task-001", "agent": "Builder", "token_estimate": 5000},
    ])
    # With --last-n 1, only last entry (5000) is counted
    result = run_dashboard(tmp_path, ["--last-n", "1"])
    assert result.returncode == 0
    # Grand total line should show 5,000 (only 1 of the 2 entries processed)
    grand_total_line = next(l for l in result.stdout.splitlines() if "Grand total" in l)
    assert "5,000" in grand_total_line or "5000" in grand_total_line
