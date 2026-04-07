"""Unit tests for scripts/capture.py — no network calls, no GitHub token required."""
import base64
import importlib.util
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

# Load capture.py from scripts/ without importing as a package
spec = importlib.util.spec_from_file_location(
    "capture", "scripts/capture.py"
)
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)


def _make_github_file(content: str) -> dict:
    """Simulate a GitHub API file response."""
    return {
        "content": base64.b64encode(content.encode()).decode(),
        "sha": "abc123",
    }


class TestCaptureBacklog(unittest.TestCase):
    def test_appends_item_with_today_date(self):
        existing = "# Telegram Backlog Inbox\n\nItems below...\n"
        file_info = _make_github_file(existing)
        committed = {}

        with patch.object(capture, "_get_file", return_value=file_info), \
             patch.object(capture, "_put_file", side_effect=lambda *a, **kw: committed.update({"args": a})):
            capture.capture_backlog("token", "owner/repo", "My test item", "main", dry_run=False)

        # _put_file(token, repo, path, message, content, sha, branch) — content is index 4
        new_content = committed["args"][4]
        self.assertIn("My test item", new_content)
        import datetime
        self.assertIn(datetime.date.today().isoformat(), new_content)

    def test_dry_run_does_not_call_put(self):
        file_info = _make_github_file("# header\n\n")
        put_called = []

        with patch.object(capture, "_get_file", return_value=file_info), \
             patch.object(capture, "_put_file", side_effect=lambda *a, **kw: put_called.append(True)):
            capture.capture_backlog("token", "owner/repo", "Dry item", "main", dry_run=True)

        self.assertEqual(put_called, [], "dry_run must not call _put_file")

    def test_trailing_newline_preserved(self):
        existing = "# header\n\n- 2026-01-01: old item\n"
        file_info = _make_github_file(existing)
        committed = {}

        with patch.object(capture, "_get_file", return_value=file_info), \
             patch.object(capture, "_put_file", side_effect=lambda *a, **kw: committed.update({"args": a})):
            capture.capture_backlog("token", "owner/repo", "New item", "main", dry_run=False)

        new_content = committed["args"][4]
        self.assertTrue(new_content.endswith("\n"), "Content should end with newline")
        # New item should follow old item with a single newline, not a blank line
        self.assertIn("- 2026-01-01: old item\n- 2026-04-07: New item", new_content)


class TestCapturePensieve(unittest.TestCase):
    def test_creates_note_with_frontmatter(self):
        committed = {}

        with patch.object(capture, "_get_file", side_effect=SystemExit), \
             patch.object(capture, "_put_file", side_effect=lambda *a, **kw: committed.update({"args": a})):
            capture.capture_pensieve(
                "token", "owner/repo", "Test Article", "https://example.com", "Key note", "main", dry_run=False
            )

        content = committed["args"][4]
        self.assertIn("title: \"Test Article\"", content)
        self.assertIn("source: laptop-capture", content)
        self.assertIn("url: \"https://example.com\"", content)
        self.assertIn("Key note", content)
        self.assertTrue(content.startswith("---"), "Must start with YAML frontmatter")

    def test_file_path_uses_slug(self):
        committed = {}

        with patch.object(capture, "_get_file", side_effect=SystemExit), \
             patch.object(capture, "_put_file", side_effect=lambda *a, **kw: committed.update({"args": a})):
            capture.capture_pensieve(
                "token", "owner/repo", "My Great Article!", None, None, "main", dry_run=False
            )

        file_path = committed["args"][2]
        self.assertRegex(file_path, r"^captures/\d{4}-\d{2}-\d{2}-[a-z0-9-]+\.md$")
        self.assertNotIn("!", file_path)

    def test_dry_run_does_not_call_put(self):
        put_called = []

        with patch.object(capture, "_get_file", side_effect=SystemExit), \
             patch.object(capture, "_put_file", side_effect=lambda *a, **kw: put_called.append(True)):
            capture.capture_pensieve(
                "token", "owner/repo", "Title", None, None, "main", dry_run=True
            )

        self.assertEqual(put_called, [], "dry_run must not call _put_file")


class TestMissingToken(unittest.TestCase):
    def test_exits_without_token(self):
        with patch.dict("os.environ", {"GITHUB_TOKEN": ""}, clear=False):
            with self.assertRaises(SystemExit) as ctx:
                import argparse
                with patch("sys.argv", ["capture.py", "backlog", "Test"]):
                    capture.main()
        self.assertEqual(ctx.exception.code, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
