"""
Tests for scripts/cross-kanban.py (task-017).

Uses importlib to load the hyphenated-adjacent script safely.
Fixture queue.json files live under artefacts/task-017/_fixtures/ so that
_safe_path() workspace-root validation accepts them.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Load the module under test
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "cross-kanban.py"

spec = importlib.util.spec_from_file_location("cross_kanban", _SCRIPT_PATH)
cross_kanban = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cross_kanban)

# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------
_FIXTURES = Path(__file__).parent / "_fixtures"
_FIXTURES.mkdir(exist_ok=True)


def _write_fixture(name: str, data: dict) -> Path:
    path = _FIXTURES / name
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------
_MULTI_PROJECT_QUEUE = {
    "tasks": [
        {
            "id": "task-001",
            "title": "pm: Some pending task (BL-001)",
            "project": "project_manager",
            "status": "pending",
            "created": "2026-04-01",
        },
        {
            "id": "task-002",
            "title": "pm: An in_progress task (BL-002)",
            "project": "project_manager",
            "status": "in_progress",
            "created": "2026-04-02",
        },
        {
            "id": "task-003",
            "title": "ccas: Pending infra task (BL-010)",
            "project": "ccas",
            "status": "pending",
            "created": "2026-04-03",
        },
        {
            "id": "task-004",
            "title": "pensieve: Done task",
            "project": "pensieve",
            "status": "done",
            "created": "2026-04-04",
        },
        {
            "id": "task-005",
            "title": "pi-homelab: Paused task (BL-020)",
            "project": "pi-homelab",
            "status": "paused",
            "created": "2026-04-05",
        },
    ]
}

_EMPTY_QUEUE = {"tasks": []}

_ALL_DONE_QUEUE = {
    "tasks": [
        {
            "id": "task-001",
            "title": "done task",
            "project": "project_manager",
            "status": "done",
            "created": "2026-04-01",
        },
        {
            "id": "task-002",
            "title": "failed task",
            "project": "project_manager",
            "status": "failed",
            "created": "2026-04-02",
        },
    ]
}


# ---------------------------------------------------------------------------
# Helper: capture stdout output from main() with mocked sys.argv
# ---------------------------------------------------------------------------
def _run(queue_path: Path, capsys) -> str:
    sys.argv = ["cross-kanban.py", "--queue", str(queue_path)]
    cross_kanban.main()
    captured = capsys.readouterr()
    return captured.out


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_three_project_sections_present(capsys):
    """Active tasks from project_manager, ccas, and pi-homelab each get a section."""
    path = _write_fixture("multi_project.json", _MULTI_PROJECT_QUEUE)
    output = _run(path, capsys)

    assert "### project_manager" in output
    assert "### ccas" in output
    assert "### pi-homelab" in output


def test_done_project_omitted(capsys):
    """Projects with only done/failed tasks do not appear in output."""
    path = _write_fixture("multi_project.json", _MULTI_PROJECT_QUEUE)
    output = _run(path, capsys)

    assert "### pensieve" not in output


def test_tasks_in_correct_project_section(capsys):
    """Each task ID appears under the right project heading."""
    path = _write_fixture("multi_project.json", _MULTI_PROJECT_QUEUE)
    output = _run(path, capsys)

    lines = output.splitlines()

    def tasks_under_section(section_name: str) -> list[str]:
        in_section = False
        found = []
        for line in lines:
            if line.startswith(f"### {section_name}"):
                in_section = True
            elif line.startswith("### "):
                in_section = False
            elif in_section and "| task-" in line:
                found.append(line)
        return found

    pm_tasks = tasks_under_section("project_manager")
    assert any("task-001" in l for l in pm_tasks)
    assert any("task-002" in l for l in pm_tasks)

    ccas_tasks = tasks_under_section("ccas")
    assert any("task-003" in l for l in ccas_tasks)

    homelab_tasks = tasks_under_section("pi-homelab")
    assert any("task-005" in l for l in homelab_tasks)


def test_status_sort_order_within_project(capsys):
    """Within a project, paused/in_progress appear before pending."""
    path = _write_fixture("multi_project.json", _MULTI_PROJECT_QUEUE)
    output = _run(path, capsys)

    lines = output.splitlines()
    in_pm_section = False
    pm_rows = []
    for line in lines:
        if "### project_manager" in line:
            in_pm_section = True
        elif line.startswith("### "):
            in_pm_section = False
        elif in_pm_section and line.startswith("| ") and "task-" in line:
            pm_rows.append(line)

    statuses = [r.split("|")[1].strip() for r in pm_rows]
    # in_progress (rank 1) should come before pending (rank 4)
    assert statuses.index("in_progress") < statuses.index("pending")


def test_empty_queue_prints_no_active_tasks(capsys):
    """An empty queue prints 'No active tasks'."""
    path = _write_fixture("empty.json", _EMPTY_QUEUE)
    output = _run(path, capsys)

    assert "No active tasks" in output


def test_all_done_queue_prints_no_active_tasks(capsys):
    """A queue with only done/failed tasks prints 'No active tasks'."""
    path = _write_fixture("all_done.json", _ALL_DONE_QUEUE)
    output = _run(path, capsys)

    assert "No active tasks" in output


def test_header_present(capsys):
    """Output starts with the kanban header."""
    path = _write_fixture("multi_project.json", _MULTI_PROJECT_QUEUE)
    output = _run(path, capsys)

    assert "## Cross-Project Kanban" in output


def test_pipe_chars_escaped_in_title(capsys):
    """Pipe characters in task titles are escaped so table rows stay valid."""
    queue = {
        "tasks": [
            {
                "id": "task-x",
                "title": "title with | pipe",
                "project": "project_manager",
                "status": "pending",
                "created": "2026-04-01",
            }
        ]
    }
    path = _write_fixture("pipe_title.json", queue)
    output = _run(path, capsys)

    # The raw '|' in the title should be escaped as '\|'
    assert r"title with \| pipe" in output
