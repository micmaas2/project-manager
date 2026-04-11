"""Unit tests for scripts/pm-priority.py"""

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

# Load the script via importlib (handles the non-package path)
_SCRIPT = Path(__file__).parent.parent.parent / "scripts" / "pm-priority.py"
spec = importlib.util.spec_from_file_location("pm_priority", _SCRIPT)
pm_priority = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pm_priority)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

BACKLOG_MD = """\
# Backlog

| ID | Epic | Title | Project | Priority | Status | Added |
|---|---|---|---|---|---|---|
| BL-001 | EPIC-003 | Some old done task | project_manager | P1 | done | 2026-01-01 |
| BL-004 | EPIC-003 | Multi-project priority ranking in PM | project_manager | P2 | in_progress | 2026-04-05 |
| BL-050 | EPIC-003 | Python token-cap-enforcer script | project_manager | P2 | in_progress | 2026-04-11 |
| BL-059 | EPIC-003 | Fix mas-frontend Docker healthcheck | pi-homelab | P1 | in_progress | 2026-04-11 |
| BL-099 | EPIC-003 | A P3 item | other | P3 | new | 2026-04-11 |
"""

QUEUE = {
    "tasks": [
        {
            "id": "task-001",
            "title": "something (BL-099)",
            "project": "other",
            "status": "pending",
            "created": "2026-04-01",
        },
        {
            "id": "task-002",
            "title": "pm rank (BL-004, S-003-1)",
            "project": "project_manager",
            "status": "pending",
            "created": "2026-04-05",
        },
        {
            "id": "task-003",
            "title": "token cap (BL-050)",
            "project": "project_manager",
            "status": "pending",
            "created": "2026-04-11",
        },
        {
            "id": "task-004",
            "title": "healthcheck fix (BL-059)",
            "project": "pi-homelab",
            "status": "pending",
            "created": "2026-04-11",
        },
        {
            "id": "task-005",
            "title": "paused task (BL-059)",
            "project": "pi-homelab",
            "status": "paused",
            "created": "2026-04-10",
        },
        {
            "id": "task-done",
            "title": "done task (BL-001)",
            "project": "project_manager",
            "status": "done",
            "created": "2026-01-01",
        },
    ]
}


_FIXTURE_DIR = Path(__file__).parent  # artefacts/task-015/ — inside workspace


def _make_temp(suffix: str, content_writer) -> Path:
    """Write a temp file inside the workspace and return its path (auto-cleaned on test exit)."""
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=suffix, delete=False, dir=_FIXTURE_DIR
    )
    content_writer(tmp)
    tmp.close()
    # Register cleanup so files are removed even if the test fails
    import atexit
    atexit.register(lambda p=tmp.name: Path(p).unlink(missing_ok=True))
    return Path(tmp.name)


def make_queue_file(tasks_subset: list[dict]) -> Path:
    """Write a temporary queue.json inside the workspace and return its path."""
    return _make_temp(".json", lambda f: json.dump({"tasks": tasks_subset}, f))


def make_backlog_file(content: str = BACKLOG_MD) -> Path:
    return _make_temp(".md", lambda f: f.write(content))


# ---------------------------------------------------------------------------
# Helper: run main() capturing stdout
# ---------------------------------------------------------------------------

def run_main(queue_path: Path, backlog_path: Path, status: str = None) -> str:
    old_argv = sys.argv
    args = ["pm-priority.py", "--queue", str(queue_path), "--backlog", str(backlog_path)]
    if status:
        args += ["--status", status]
    sys.argv = args
    buf = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buf
    try:
        pm_priority.main()
    finally:
        sys.stdout = old_stdout
        sys.argv = old_argv
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestLoadBacklogPriorities(unittest.TestCase):
    def test_parses_known_priorities(self):
        bf = make_backlog_file()
        prio = pm_priority.load_backlog_priorities(bf)
        self.assertEqual(prio["BL-004"], "P2")
        self.assertEqual(prio["BL-050"], "P2")
        self.assertEqual(prio["BL-059"], "P1")
        self.assertEqual(prio["BL-099"], "P3")

    def test_missing_file_returns_empty(self):
        prio = pm_priority.load_backlog_priorities(Path("/nonexistent/file.md"))
        self.assertEqual(prio, {})


class TestExtractBlId(unittest.TestCase):
    def test_single_bl(self):
        self.assertEqual(pm_priority.extract_bl_id("Fix X (BL-059)"), "BL-059")

    def test_first_bl_in_multiple(self):
        self.assertEqual(pm_priority.extract_bl_id("task (BL-004, S-003-1)"), "BL-004")

    def test_no_bl(self):
        self.assertIsNone(pm_priority.extract_bl_id("no bl here (S-003-1)"))

    def test_zero_padded(self):
        self.assertEqual(pm_priority.extract_bl_id("task (BL-001)"), "BL-001")


class TestRanking(unittest.TestCase):
    def setUp(self):
        self.qf = make_queue_file(QUEUE["tasks"])
        self.bf = make_backlog_file()

    def _ranked_ids(self, status=None):
        out = run_main(self.qf, self.bf, status)
        ids = []
        for line in out.splitlines():
            if line.startswith("|") and not line.startswith("| Rank") and not line.startswith("|---"):
                cols = [c.strip() for c in line.split("|")]
                if len(cols) >= 3 and cols[2].startswith("task-"):
                    ids.append(cols[2])
        return ids

    def test_paused_first(self):
        """Paused tasks always appear first, regardless of project or priority."""
        ids = self._ranked_ids()
        self.assertEqual(ids[0], "task-005", f"Expected paused task first, got: {ids}")

    def test_pm_before_other_projects(self):
        """project_manager tasks come before other projects."""
        ids = self._ranked_ids()
        # task-002 and task-003 are project_manager; task-001 (other) and task-004 (pi-homelab) must come after
        pm_indices = [i for i, t in enumerate(ids) if t in ("task-002", "task-003")]
        other_indices = [i for i, t in enumerate(ids) if t in ("task-001", "task-004")]
        self.assertTrue(
            max(pm_indices) < min(other_indices),
            f"PM tasks {pm_indices} should all precede other tasks {other_indices}. Order: {ids}",
        )

    def test_oldest_created_wins_within_same_tier(self):
        """Within project_manager, oldest created date ranks first."""
        ids = self._ranked_ids()
        pm_ids = [t for t in ids if t in ("task-002", "task-003")]
        # task-002 created 2026-04-05 should precede task-003 created 2026-04-11
        self.assertEqual(pm_ids, ["task-002", "task-003"], f"PM task order: {pm_ids}")

    def test_done_tasks_excluded_by_default(self):
        """Done tasks are excluded from default status filter."""
        ids = self._ranked_ids()
        self.assertNotIn("task-done", ids)

    def test_custom_status_filter(self):
        """--status flag filters correctly."""
        ids = self._ranked_ids(status="done")
        self.assertEqual(ids, ["task-done"])

    def test_output_contains_header(self):
        out = run_main(self.qf, self.bf)
        self.assertIn("| Rank | Task ID | Project | Priority | Status | Title |", out)

    def test_priority_column_shows_value(self):
        """Priority column shows P1/P2/P3 for tasks with known BL-NNN."""
        out = run_main(self.qf, self.bf)
        # task-004 (BL-059, P1) should show P1 in output
        lines = [l for l in out.splitlines() if "task-004" in l]
        self.assertTrue(lines, "task-004 not found in output")
        self.assertIn("P1", lines[0])


class TestEmptyQueue(unittest.TestCase):
    def test_empty_queue_no_error(self):
        qf = make_queue_file([])
        bf = make_backlog_file()
        out = run_main(qf, bf)
        self.assertIn("no tasks", out.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
