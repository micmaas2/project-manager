"""Unit tests for migrate-vault.py."""

import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Adjust path so we can import the script from the same directory
import importlib.util
import sys

_spec = importlib.util.spec_from_file_location(
    "migrate_vault", os.path.join(os.path.dirname(__file__), "migrate-vault.py")
)
mv = importlib.util.module_from_spec(_spec)
sys.modules["migrate_vault"] = mv
_spec.loader.exec_module(mv)


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _read_fixture(name: str) -> str:
    with open(os.path.join(FIXTURES_DIR, name), encoding="utf-8") as fh:
        return fh.read()


class TestTagNormalization(unittest.TestCase):
    """normalize_tag converts various tag formats to hyphenated lowercase."""

    def test_camel_case(self):
        self.assertEqual(mv.normalize_tag("#aiAgents"), "ai-agents")

    def test_already_lowercase(self):
        self.assertEqual(mv.normalize_tag("#claude"), "claude")

    def test_already_hyphenated(self):
        self.assertEqual(mv.normalize_tag("#social-media"), "social-media")

    def test_strips_hash(self):
        self.assertEqual(mv.normalize_tag("#anthropic"), "anthropic")

    def test_mixed_case(self):
        self.assertEqual(mv.normalize_tag("#MachineLearning"), "machine-learning")


class TestIsOldFormat(unittest.TestCase):
    """is_old_format correctly identifies old vs new notes."""

    def test_old_format_detected(self):
        content = _read_fixture("old_thought.md")
        self.assertTrue(mv.is_old_format(content))

    def test_new_format_not_detected(self):
        content = _read_fixture("already_new.md")
        self.assertFalse(mv.is_old_format(content))

    def test_old_link_detected(self):
        content = _read_fixture("old_link_linkedin.md")
        self.assertTrue(mv.is_old_format(content))


class TestParseOldFormat(unittest.TestCase):
    """parse_old_format extracts all fields from old-format notes."""

    def test_thought_fields(self):
        content = _read_fixture("old_thought.md")
        fields = mv.parse_old_format(content)
        self.assertEqual(fields["title"], "Claude Code Skills")
        self.assertEqual(fields["date"], "2026-03-29")
        self.assertEqual(fields["category"], "Inbox")
        self.assertEqual(fields["source"], "thought")
        self.assertEqual(fields["channel"], "telegram")
        self.assertIn("claude", fields["tags"])
        self.assertIn("coding", fields["tags"])
        self.assertIn("ai", fields["tags"])
        self.assertIn("skills", fields["tags"])
        self.assertIn("Claude code skills", fields["raw_capture"])

    def test_link_fields(self):
        content = _read_fixture("old_link_linkedin.md")
        fields = mv.parse_old_format(content)
        self.assertEqual(fields["source"], "link")
        self.assertIn("linkedin.com", fields["raw_capture"])


class TestOldThoughtMigration(unittest.TestCase):
    """Migrating an old thought note produces correct YAML frontmatter."""

    def test_thought_written_as_yaml(self):
        content = _read_fixture("old_thought.md")
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(content)
            tmppath = tmp.name

        try:
            mv.migrate_note(tmppath, dry_run=False, client=None)
            with open(tmppath, encoding="utf-8") as fh:
                result = fh.read()

            self.assertTrue(result.startswith("---\n"), "must start with YAML front matter")
            self.assertIn("title: ", result)
            self.assertIn("date: 2026-03-29", result)
            self.assertIn("source: thought", result)
            self.assertIn("channel: telegram", result)
            self.assertIn("tags: [", result)
            # Thought notes should NOT have Key Points or Analysis sections
            self.assertNotIn("## Key Points", result)
            self.assertNotIn("## Analysis", result)
            # Raw capture preserved
            self.assertIn("Claude code skills", result)
        finally:
            os.unlink(tmppath)

    def test_dry_run_does_not_write(self):
        content = _read_fixture("old_thought.md")
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(content)
            tmppath = tmp.name

        try:
            mv.migrate_note(tmppath, dry_run=True, client=None)
            with open(tmppath, encoding="utf-8") as fh:
                result = fh.read()
            self.assertEqual(result, content, "dry-run must not modify the file")
        finally:
            os.unlink(tmppath)


class TestLinkedinNeedsReview(unittest.TestCase):
    """LinkedIn link notes get needs-review tag; content preserved beyond frontmatter."""

    def test_linkedin_gets_needs_review(self):
        content = _read_fixture("old_link_linkedin.md")
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(content)
            tmppath = tmp.name

        try:
            mv.migrate_note(tmppath, dry_run=False, client=None)
            with open(tmppath, encoding="utf-8") as fh:
                result = fh.read()
            self.assertIn("needs-review", result)
            # Original summary preserved
            self.assertIn("LinkedIn post", result)
        finally:
            os.unlink(tmppath)


class TestAlreadyNewFormatSkipped(unittest.TestCase):
    """New-format notes are skipped and left unchanged."""

    def test_new_format_file_unchanged(self):
        content = _read_fixture("already_new.md")
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(content)
            tmppath = tmp.name

        try:
            result = mv.migrate_note(tmppath, dry_run=False, client=None)
            self.assertFalse(result, "should return False for already-new note")
            with open(tmppath, encoding="utf-8") as fh:
                on_disk = fh.read()
            self.assertEqual(on_disk, content, "file must not be modified")
        finally:
            os.unlink(tmppath)


class TestUrlEnrichment(unittest.TestCase):
    """Non-LinkedIn URL notes are re-enriched via Claude API when client is available."""

    def test_enrichment_called_for_non_linkedin_url(self):
        content = _read_fixture("old_link_url.md")
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(content)
            tmppath = tmp.name

        mock_client = MagicMock()
        enriched = {
            "title": "Enriched Title",
            "summary": "Enriched summary.",
            "key_points": ["Point A", "Point B"],
            "analysis": "Deep analysis.",
            "tags": ["anthropic", "learning", "ai"],
            "topic": "ai",
        }

        try:
            with patch.object(mv, "fetch_page_content", return_value="page text") as mock_fetch:
                with patch.object(mv, "reenrich_via_claude", return_value=enriched) as mock_enrich:
                    mv.migrate_note(tmppath, dry_run=False, client=mock_client)
                    mock_fetch.assert_called_once()
                    mock_enrich.assert_called_once()

            with open(tmppath, encoding="utf-8") as fh:
                result = fh.read()

            self.assertIn("Enriched Title", result)
            self.assertIn("## Key Points", result)
            self.assertIn("Point A", result)
            self.assertIn("## Analysis", result)
            self.assertIn("Deep analysis.", result)
        finally:
            os.unlink(tmppath)

    def test_needs_review_when_fetch_fails(self):
        content = _read_fixture("old_link_url.md")
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(content)
            tmppath = tmp.name

        mock_client = MagicMock()
        try:
            with patch.object(mv, "fetch_page_content", return_value=None):
                mv.migrate_note(tmppath, dry_run=False, client=mock_client)

            with open(tmppath, encoding="utf-8") as fh:
                result = fh.read()
            self.assertIn("needs-review", result)
        finally:
            os.unlink(tmppath)


class TestPrivateIpBlocked(unittest.TestCase):
    """fetch_page_content refuses private IP URLs without making a network call."""

    def test_localhost_blocked(self):
        result = mv.fetch_page_content("http://localhost/secret")
        self.assertIsNone(result)

    def test_private_192_blocked(self):
        result = mv.fetch_page_content("http://192.168.1.1/admin")
        self.assertIsNone(result)

    def test_private_10_blocked(self):
        result = mv.fetch_page_content("http://10.0.0.1/data")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
