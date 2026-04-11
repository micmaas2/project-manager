"""
Unit tests for scripts/token_cap_enforcer.py (task-016).

Covers:
  - Task below threshold  → exit 0, "OK:" message
  - Task above threshold  → exit 1, "ALERT:" message
  - Task at exact threshold (400000) → exit 0 (not strictly greater)
  - Task with no token_estimate → exit 0
  - Task not found in queue → exit 1
  - queue.json not found → exit 1
  - queue.json invalid JSON → exit 1

Note: _safe_path() in the script enforces that --queue must be inside the
workspace root, so fixture files live under artefacts/task-016/_fixtures/ (which
is inside the workspace) rather than /tmp.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

# Path to the script under test
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SCRIPT = _REPO_ROOT / "scripts" / "token_cap_enforcer.py"
# Fixture dir inside workspace so _safe_path() accepts it
_FIXTURE_DIR = Path(__file__).resolve().parent / "_fixtures"


def setup_module(module):
    _FIXTURE_DIR.mkdir(exist_ok=True)


def teardown_module(module):
    shutil.rmtree(_FIXTURE_DIR, ignore_errors=True)


def _run(task_id: str, queue_path: str | Path | None = None) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(_SCRIPT), "--task-id", task_id]
    if queue_path is not None:
        cmd += ["--queue", str(queue_path)]
    return subprocess.run(cmd, capture_output=True, text=True)


def _make_queue(name: str, tasks: list[dict]) -> Path:
    """Write a fixture queue.json inside the workspace-safe fixture dir."""
    path = _FIXTURE_DIR / name
    path.write_text(json.dumps({"tasks": tasks}))
    return path


class TestTokenCapEnforcer:
    def test_below_threshold_exits_0(self):
        q = _make_queue("below.json", [{"id": "task-001", "token_estimate": 5000}])
        result = _run("task-001", q)
        assert result.returncode == 0
        assert "OK: task-001 token_estimate=5000" in result.stdout

    def test_above_threshold_exits_1(self):
        q = _make_queue("above.json", [{"id": "task-002", "token_estimate": 450000}])
        result = _run("task-002", q)
        assert result.returncode == 1
        assert "ALERT: Task task-002 estimated tokens (450000) exceed" in result.stdout
        assert "80% of project cap" in result.stdout

    def test_exactly_at_threshold_exits_0(self):
        q = _make_queue("exact.json", [{"id": "task-003", "token_estimate": 400000}])
        result = _run("task-003", q)
        assert result.returncode == 0
        assert "OK: task-003 token_estimate=400000" in result.stdout

    def test_one_above_threshold_exits_1(self):
        q = _make_queue("one_above.json", [{"id": "task-004", "token_estimate": 400001}])
        result = _run("task-004", q)
        assert result.returncode == 1
        assert "ALERT:" in result.stdout

    def test_no_estimate_exits_0(self):
        q = _make_queue("no_est.json", [{"id": "task-005"}])
        result = _run("task-005", q)
        assert result.returncode == 0
        assert "token_estimate=none" in result.stdout

    def test_task_not_found_exits_1(self):
        q = _make_queue("notfound.json", [{"id": "task-999", "token_estimate": 1000}])
        result = _run("task-000", q)
        assert result.returncode == 1
        assert "not found" in result.stderr

    def test_queue_file_missing_exits_1(self):
        result = _run("task-001", _FIXTURE_DIR / "nonexistent.json")
        assert result.returncode == 1
        assert "not found" in result.stderr

    def test_invalid_json_exits_1(self):
        q = _FIXTURE_DIR / "bad.json"
        q.write_text("{ not valid json }")
        result = _run("task-001", q)
        assert result.returncode == 1
        assert "could not parse queue.json" in result.stderr

    def test_multiple_tasks_correct_one_selected(self):
        q = _make_queue("multi.json", [
            {"id": "task-low", "token_estimate": 1000},
            {"id": "task-high", "token_estimate": 500000},
        ])
        r_low = _run("task-low", q)
        assert r_low.returncode == 0
        assert "OK: task-low" in r_low.stdout

        r_high = _run("task-high", q)
        assert r_high.returncode == 1
        assert "ALERT: Task task-high" in r_high.stdout
