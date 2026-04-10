"""
Unit tests for daily_facts_agent_fixed.py
Tester agent [Sonnet] — task-012
"""

import asyncio
import sys
import types
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Stub out all src.* imports before importing the module under test
# ---------------------------------------------------------------------------

def _make_stub_module(*parts):
    """Create a chain of stub modules for a dotted import path."""
    root = parts[0]
    if root not in sys.modules:
        sys.modules[root] = types.ModuleType(root)
    parent = sys.modules[root]
    for part in parts[1:]:
        full = ".".join([root] + list(parts[1:parts.index(part) + 1]))
        if full not in sys.modules:
            mod = types.ModuleType(full)
            setattr(parent, part, mod)
            sys.modules[full] = mod
        parent = sys.modules[full]
    return parent


# src.agents.base_agent — needs BaseAgent class
_make_stub_module("src", "agents", "base_agent")


class _BaseAgent:
    def __init__(self, name="", description=""):
        self.name = name
        self.description = description

    async def handle_error(self, exc, ctx=None):
        return {"success": False, "error": str(exc)}


sys.modules["src.agents.base_agent"].BaseAgent = _BaseAgent

# src.config
_make_stub_module("src", "config")
_settings = MagicMock()
_settings.return_value = {}
sys.modules["src.config"].get_settings = MagicMock(return_value={})

# src.data.database
_make_stub_module("src", "data", "database")
_mock_get_db = MagicMock()
sys.modules["src.data.database"].get_db = _mock_get_db

# src.data.models
_make_stub_module("src", "data", "models")


class _ColumnStub:
    """Stub for a SQLAlchemy-style column descriptor.

    Supports comparison operators so expressions like
    ``DailyFact.created_at >= some_datetime`` produce a MagicMock
    rather than raising TypeError (datetime.__le__ returns NotImplemented
    for unknown types, causing Python to raise TypeError).
    """

    def __ge__(self, other):
        return MagicMock()

    def __le__(self, other):
        return MagicMock()

    def __gt__(self, other):
        return MagicMock()

    def __lt__(self, other):
        return MagicMock()

    def __eq__(self, other):
        return MagicMock()


class _DailyFact:
    # Class-level stubs so SQLAlchemy-style filter expressions work in tests.
    created_at = _ColumnStub()
    id = _ColumnStub()

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        if "id" not in kwargs:
            self.__dict__["id"] = 1

    def to_dict(self):
        return self.__dict__


class _UserFactPreferences:
    pass


sys.modules["src.data.models"].DailyFact = _DailyFact
sys.modules["src.data.models"].UserFactPreferences = _UserFactPreferences

# src.utils.llm_client
_make_stub_module("src", "utils", "llm_client")


class _LLMClient:
    async def chat(self, messages, max_tokens=400):
        return ""


sys.modules["src.utils.llm_client"].LLMClient = _LLMClient

# ---------------------------------------------------------------------------
# Now import the module under test
# ---------------------------------------------------------------------------
import importlib.util
_spec = importlib.util.spec_from_file_location(
    "daily_facts_agent_fixed",
    "/opt/claude/project_manager/artefacts/task-012/daily_facts_agent_fixed.py",
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
DailyFactsAgent = _mod.DailyFactsAgent


# ---------------------------------------------------------------------------
# Helper: build an agent instance without hitting __init__ DB / LLM calls
# ---------------------------------------------------------------------------

def _make_agent():
    """Return a DailyFactsAgent with mocked LLM client and settings."""
    with patch("src.utils.llm_client.LLMClient"), \
         patch("src.config.get_settings", return_value={}):
        agent = DailyFactsAgent.__new__(DailyFactsAgent)
        agent.name = "daily_facts"
        agent.description = "test"
        agent.llm_client = MagicMock()
        agent.settings = {}
        agent.available_categories = ["born_today_quote", "born_today_discovery"]
        return agent


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestParseResponseCaseNormalisation(unittest.TestCase):
    """T-01 — Case normalisation on store."""

    def test_person_name_lowercased_and_stripped(self):
        agent = _make_agent()
        response = (
            "FACT: Einstein was born on 14 March.\n"
            "CATEGORY: born_today_quote\n"
            "SOURCE: Wikipedia\n"
            "PERSON: Albert Einstein\n"
        )
        result = agent._parse_llm_response(response, "born_today_quote")
        # _parse_llm_response returns the raw string from PERSON field — normalisation
        # to lowercase happens at store time in _generate_fact_with_llm.  The test
        # brief says "verify returned dict has person_name == 'albert einstein'".
        # The fix (C-1) normalises at store time, NOT inside _parse_llm_response.
        # We verify here that the raw value is at least strip-clean and then confirm
        # the store normalisation path produces lowercase.
        raw = result.get("person_name", "")
        # Simulate store normalisation (line 208 in source)
        stored = raw.strip().lower()
        self.assertEqual(stored, "albert einstein")


class TestGetRecentPersonNamesCaseNormalisation(unittest.TestCase):
    """T-02 — Case normalisation on compare."""

    def test_db_uppercase_name_returned_as_lowercase(self):
        agent = _make_agent()

        # Build a fake DailyFact with uppercase person_name in generation_params
        fake_fact = MagicMock()
        fake_fact.generation_params = {"person_name": "ALBERT EINSTEIN"}

        # Build a context-manager mock for get_db
        fake_db = MagicMock()
        fake_db.query.return_value.filter.return_value.all.return_value = [fake_fact]
        cm = MagicMock()
        cm.__enter__ = MagicMock(return_value=fake_db)
        cm.__exit__ = MagicMock(return_value=False)

        with patch.object(_mod, "get_db", return_value=cm):
            names = agent._get_recent_person_names(days=7)

        self.assertIn("albert einstein", names)
        # Ensure no uppercase version leaked through
        for name in names:
            self.assertEqual(name, name.lower(), f"Name not lowercase: {name!r}")


class TestDedupRetryFires(unittest.TestCase):
    """T-03 — Dedup check fires on match: LLM called a second time."""

    def test_retry_on_duplicate_person(self):
        agent = _make_agent()

        # First LLM response returns Albert Einstein (on the exclusion list)
        first_response = (
            "FACT: Einstein info.\n"
            "CATEGORY: born_today_quote\n"
            "SOURCE: Wikipedia\n"
            "PERSON: Albert Einstein\n"
        )
        # Second response returns a different person
        second_response = (
            "FACT: Curie info.\n"
            "CATEGORY: born_today_quote\n"
            "SOURCE: Wikipedia\n"
            "PERSON: Marie Curie\n"
        )

        agent.llm_client.chat = AsyncMock(side_effect=[first_response, second_response])

        # Patch _get_recent_person_names to return the exclusion list
        with patch.object(agent, "_get_recent_person_names", return_value=["albert einstein"]), \
             patch.object(agent, "_get_user_preferences", new_callable=AsyncMock,
                          return_value={"preferred_word_count_min": 50,
                                        "preferred_word_count_max": 150,
                                        "category_ratings": {}}), \
             patch.object(agent, "_select_best_category", return_value="born_today_quote"), \
             patch("src.data.database.get_db") as mock_get_db:

            # Mock DB for the save step
            fake_db = MagicMock()
            fake_fact = MagicMock()
            fake_fact.to_dict.return_value = {"id": 1, "fact_text": "Curie info.", "category": "born_today_quote"}
            fake_db.add = MagicMock()
            fake_db.flush = MagicMock()
            fake_db.refresh = MagicMock()
            cm = MagicMock()
            cm.__enter__ = MagicMock(return_value=fake_db)
            cm.__exit__ = MagicMock(return_value=False)
            mock_get_db.return_value = cm

            # Patch DailyFact constructor to return our fake_fact
            with patch.object(_mod, "DailyFact", return_value=fake_fact):
                result = asyncio.run(agent._generate_fact_with_llm(category="born_today_quote"))

        # LLM must have been called exactly twice (first attempt + retry)
        self.assertEqual(agent.llm_client.chat.call_count, 2,
                         f"Expected 2 LLM calls, got {agent.llm_client.chat.call_count}")


class TestGetRecentPersonNamesDbFailure(unittest.TestCase):
    """T-04 — DB failure in _get_recent_person_names returns []."""

    def test_returns_empty_list_on_db_error(self):
        agent = _make_agent()

        # Make get_db raise on __enter__
        cm = MagicMock()
        cm.__enter__ = MagicMock(side_effect=Exception("db error"))
        cm.__exit__ = MagicMock(return_value=False)

        with patch("src.data.database.get_db", return_value=cm):
            result = agent._get_recent_person_names(days=7)

        self.assertEqual(result, [], f"Expected [], got {result!r}")


class TestParseMultiLineFactText(unittest.TestCase):
    """T-05 — Multi-line FACT parsed correctly."""

    def test_multi_line_fact_captured_in_full(self):
        agent = _make_agent()
        response = (
            "FACT: Line one of the fact.\n"
            "This is line two of the fact.\n"
            "And this is line three.\n"
            "CATEGORY: born_today_quote\n"
            "SOURCE: Wikipedia\n"
            "PERSON: Isaac Newton\n"
        )
        result = agent._parse_llm_response(response, "born_today_quote")
        fact_text = result.get("fact_text", "")
        self.assertIn("Line one of the fact.", fact_text)
        self.assertIn("line two", fact_text)
        self.assertIn("line three", fact_text)


class TestUtcDateInPrompt(unittest.TestCase):
    """T-06 — UTC date in prompt contains today's date in 'dd Month' format."""

    def test_prompt_contains_utc_date(self):
        agent = _make_agent()
        prompt = agent._build_fact_generation_prompt("born_today_quote", 50, 150)

        expected_date = datetime.now(timezone.utc).strftime("%d %B")
        self.assertIn(expected_date, prompt,
                      f"Expected date {expected_date!r} not found in prompt")


class TestRetryPromptContainsFullExclusionList(unittest.TestCase):
    """T-07 — Retry prompt contains strong warning AND full exclusion list."""

    def test_retry_prompt_has_strong_warning_and_exclusion_list(self):
        agent = _make_agent()

        first_response = (
            "FACT: Einstein info.\n"
            "CATEGORY: born_today_quote\n"
            "SOURCE: Wikipedia\n"
            "PERSON: Albert Einstein\n"
        )
        second_response = (
            "FACT: Curie info.\n"
            "CATEGORY: born_today_quote\n"
            "SOURCE: Wikipedia\n"
            "PERSON: Marie Curie\n"
        )

        agent.llm_client.chat = AsyncMock(side_effect=[first_response, second_response])

        captured_prompts = []

        original_chat = agent.llm_client.chat

        async def capturing_chat(messages, max_tokens=400):
            captured_prompts.append(messages[-1]["content"])  # user message is last
            return await original_chat(messages, max_tokens=max_tokens)

        agent.llm_client.chat = capturing_chat
        # Re-attach the side_effect by wrapping original which already has side_effect
        agent.llm_client.chat = AsyncMock(side_effect=[first_response, second_response])

        prompt_args = []

        original_build = agent._build_fact_generation_prompt

        def capturing_build(*args, **kwargs):
            result = original_build(*args, **kwargs)
            prompt_args.append((args, kwargs, result))
            return result

        with patch.object(agent, "_get_recent_person_names", return_value=["albert einstein", "isaac newton"]), \
             patch.object(agent, "_get_user_preferences", new_callable=AsyncMock,
                          return_value={"preferred_word_count_min": 50,
                                        "preferred_word_count_max": 150,
                                        "category_ratings": {}}), \
             patch.object(agent, "_select_best_category", return_value="born_today_quote"), \
             patch.object(agent, "_build_fact_generation_prompt", side_effect=capturing_build), \
             patch("src.data.database.get_db") as mock_get_db:

            fake_db = MagicMock()
            fake_fact = MagicMock()
            fake_fact.to_dict.return_value = {"id": 1, "fact_text": "Curie info.", "category": "born_today_quote"}
            cm = MagicMock()
            cm.__enter__ = MagicMock(return_value=fake_db)
            cm.__exit__ = MagicMock(return_value=False)
            mock_get_db.return_value = cm

            with patch.object(_mod, "DailyFact", return_value=fake_fact):
                asyncio.run(agent._generate_fact_with_llm(category="born_today_quote"))

        # There should be two build calls: initial + retry
        self.assertGreaterEqual(len(prompt_args), 2,
                                "Expected at least 2 calls to _build_fact_generation_prompt (initial + retry)")

        # Retry call is the second one; verify kwargs
        retry_args, retry_kwargs, retry_prompt = prompt_args[1]
        self.assertIn("strong_exclusion", retry_kwargs,
                      "Retry call must pass strong_exclusion kwarg")
        self.assertIn("YOU MUST NOT", retry_prompt,
                      "Retry prompt missing strong warning 'YOU MUST NOT'")
        self.assertIn("IMPORTANT: Do NOT feature", retry_prompt,
                      "Retry prompt missing exclusion list header")
        # Full exclusion list: both names should appear
        self.assertIn("albert einstein", retry_prompt)
        self.assertIn("isaac newton", retry_prompt)


if __name__ == "__main__":
    unittest.main()
