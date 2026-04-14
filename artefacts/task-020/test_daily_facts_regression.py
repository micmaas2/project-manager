"""
Tests for task-020: MAS daily facts birth-date regression fix (BL-065)

Root cause: LLM hallucinated birth dates by inserting today's date into facts
regardless of the person's actual birthday.

Fix: Wikipedia REST API provides verified born-today candidates which are passed
to the LLM prompt, constraining it to people who actually share today's birth date.
"""

import importlib.util
import json
import logging
import sys
import types
from io import BytesIO
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest

# ── pre-inject Docker-only dependencies ─────────────────────────────────────

def _mock_module(name: str, **attrs) -> types.ModuleType:
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    return m

# src hierarchy
for mod in [
    "src", "src.agents", "src.agents.base_agent",
    "src.config", "src.data", "src.data.database", "src.data.models",
    "src.utils", "src.utils.llm_client",
]:
    sys.modules.setdefault(mod, _mock_module(mod))

# BaseAgent — concrete base class (not a mock) so MRO works
class _BaseAgent:
    def __init__(self, name, description):
        self.name = name

    async def handle_error(self, e, ctx):
        return {"success": False, "error": str(e)}

sys.modules["src.agents.base_agent"].BaseAgent = _BaseAgent

# Settings, DB, models
sys.modules["src.config"].get_settings = MagicMock(return_value=MagicMock())
sys.modules["src.data.database"].get_db = MagicMock()
sys.modules["src.data.models"].DailyFact = MagicMock
sys.modules["src.data.models"].UserFactPreferences = MagicMock
sys.modules["src.utils.llm_client"].LLMClient = MagicMock

# ── load the patched agent module ────────────────────────────────────────────

_AGENT_PATH = str(
    __file__.replace("test_daily_facts_regression.py", "daily_facts_agent_patched.py")
)
spec = importlib.util.spec_from_file_location("daily_facts_agent_patched", _AGENT_PATH)
_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_mod)
DailyFactsAgent = _mod.DailyFactsAgent

# ── helpers ──────────────────────────────────────────────────────────────────

def _make_agent() -> DailyFactsAgent:
    agent = DailyFactsAgent.__new__(DailyFactsAgent)
    agent.name = "daily_facts"
    agent.llm_client = MagicMock()
    agent.settings = MagicMock()
    agent.available_categories = ["born_today_quote", "born_today_discovery"]
    return agent


_WIKI_RESPONSE = {
    "births": [
        {
            "year": 1743,
            "pages": [{"titles": {"normalized": "Thomas Jefferson"}, "description": "American statesman", "extract": "Thomas Jefferson was an American statesman."}],
        },
        {
            "year": 1852,
            "pages": [{"titles": {"normalized": "Frank Bellamy"}, "description": "English illustrator", "extract": "Frank Bellamy was an English illustrator\x00 with control chars\x01."}],
        },
        {
            "year": 1519,
            "pages": [],  # no pages — should be skipped
        },
    ]
}

# ── Test 1: Wikipedia API happy path ─────────────────────────────────────────

def test_get_born_today_candidates_happy_path():
    """_get_born_today_candidates() parses Wikipedia response correctly."""
    agent = _make_agent()
    fake_body = json.dumps(_WIKI_RESPONSE).encode()

    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=MagicMock(read=MagicMock(return_value=fake_body)))
    cm.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=cm):
        with patch("urllib.request.Request", return_value=MagicMock()):
            candidates = agent._get_born_today_candidates()

    assert len(candidates) == 2  # third entry has no pages → skipped
    assert candidates[0]["name"] == "Thomas Jefferson"
    assert candidates[0]["year"] == 1743
    assert "statesman" in candidates[0]["description"]

# ── Test 2: Control-char stripping ───────────────────────────────────────────

def test_get_born_today_candidates_strips_control_chars():
    """Extract field has null bytes and control chars removed."""
    agent = _make_agent()
    fake_body = json.dumps(_WIKI_RESPONSE).encode()

    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=MagicMock(read=MagicMock(return_value=fake_body)))
    cm.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=cm):
        with patch("urllib.request.Request", return_value=MagicMock()):
            candidates = agent._get_born_today_candidates()

    bellamy = next(c for c in candidates if c["name"] == "Frank Bellamy")
    # \x00 and \x01 must be stripped
    assert "\x00" not in bellamy["extract"]
    assert "\x01" not in bellamy["extract"]
    assert "control chars" in bellamy["extract"]

# ── Test 3: Wikipedia API failure falls back gracefully ───────────────────────

def test_get_born_today_candidates_fallback_on_error(caplog):
    """Network error → returns [] and logs warning. No exception propagates."""
    agent = _make_agent()

    with patch("urllib.request.urlopen", side_effect=Exception("connection refused")):
        with patch("urllib.request.Request", return_value=MagicMock()):
            with caplog.at_level(logging.WARNING):
                candidates = agent._get_born_today_candidates()

    assert candidates == []
    assert any("falling back to LLM-only mode" in r.message for r in caplog.records)

# ── Test 4: Prompt WITH candidates references candidate names ─────────────────

def test_build_prompt_with_candidates_contains_names():
    """When candidates provided, prompt lists them and drops free-form 'Find' guidance."""
    agent = _make_agent()
    cands = [
        {"year": 1743, "name": "Thomas Jefferson", "description": "American statesman", "extract": ""},
        {"year": 1919, "name": "Iris Murdoch", "description": "Irish-British novelist", "extract": ""},
    ]
    prompt = agent._build_fact_generation_prompt(
        "born_today_quote", 50, 150, candidates=cands
    )
    assert "Thomas Jefferson" in prompt
    assert "Iris Murdoch" in prompt
    assert "Verified born on" in prompt
    # Free-form fallback phrase must NOT appear when candidates given
    assert "Find a notable scientist" not in prompt

# ── Test 5: Prompt WITHOUT candidates falls back to free-form guidance ────────

def test_build_prompt_without_candidates_uses_fallback():
    """When candidates=[], prompt contains the original free-form guidance."""
    agent = _make_agent()
    prompt = agent._build_fact_generation_prompt(
        "born_today_discovery", 50, 150, candidates=[]
    )
    assert "Find a notable scientist" in prompt
    assert "Verified born on" not in prompt

# ── Test 6: Dedup (task-012) preserved alongside candidates ───────────────────

def test_build_prompt_dedup_preserved_with_candidates():
    """excluded_persons block still appears when both candidates and exclusions given."""
    agent = _make_agent()
    cands = [{"year": 1743, "name": "Thomas Jefferson", "description": "statesman", "extract": ""}]
    excluded = ["albert einstein", "isaac newton"]
    prompt = agent._build_fact_generation_prompt(
        "born_today_quote", 50, 150,
        excluded_persons=excluded,
        candidates=cands,
    )
    assert "Thomas Jefferson" in prompt            # candidates present
    assert "albert einstein" in prompt             # dedup still present
    assert "isaac newton" in prompt
    assert "Do NOT feature any of these" in prompt

# ── Test 7: Regression — _parse_llm_response still extracts PERSON ────────────

def test_parse_llm_response_extracts_person():
    """task-012 PERSON field extraction is not broken by the BL-065 changes."""
    agent = _make_agent()
    raw = (
        "FACT: Marie Curie (1867-1934), geboren op 7 november, ontdekte polonium.\n"
        "CATEGORY: born_today_discovery\n"
        "SOURCE: Scheikunde\n"
        "PERSON: Marie Curie"
    )
    result = agent._parse_llm_response(raw, "born_today_discovery")
    assert result["person_name"] == "Marie Curie"
    assert "polonium" in result["fact_text"]
    assert result["category"] == "born_today_discovery"

# ── Test 8: Regression — multi-line FACT captured in full (M-2) ───────────────

def test_parse_llm_response_multiline_fact():
    """Multi-line FACT text is captured completely (re.DOTALL, no MULTILINE)."""
    agent = _make_agent()
    raw = (
        "FACT: Line one of the fact.\n"
        "Line two continues here.\n"
        "CATEGORY: born_today_quote\n"
        "SOURCE: Wikipedia\n"
        "PERSON: Some Person"
    )
    result = agent._parse_llm_response(raw, "born_today_quote")
    assert "Line one" in result["fact_text"]
    assert "Line two" in result["fact_text"]

# ── Test 9: Strong exclusion preserved alongside candidates ───────────────────

def test_build_prompt_strong_exclusion_with_candidates():
    """strong_exclusion block still appears when candidates are also provided."""
    agent = _make_agent()
    cands = [{"year": 1743, "name": "Thomas Jefferson", "description": "statesman", "extract": ""}]
    prompt = agent._build_fact_generation_prompt(
        "born_today_quote", 50, 150,
        strong_exclusion="albert einstein",
        candidates=cands,
    )
    assert "YOU MUST NOT feature albert einstein" in prompt
    assert "Thomas Jefferson" in prompt

# ── Test 10: Intellectual-first, oldest-first sorting (BL-065 core fix) ──────

def test_get_born_today_candidates_intellectual_sorting():
    """Intellectuals sorted before non-intellectuals; oldest-first within each group."""
    agent = _make_agent()

    # Wikipedia returns newest-first: athlete (2000), scientist (1850), historian (1600)
    wiki_response = {
        "births": [
            {
                "year": 2000,
                "pages": [{"titles": {"normalized": "Modern Athlete"}, "description": "American footballer", "extract": ""}],
            },
            {
                "year": 1850,
                "pages": [{"titles": {"normalized": "Old Scientist"}, "description": "German physicist and mathematician", "extract": ""}],
            },
            {
                "year": 1600,
                "pages": [{"titles": {"normalized": "Ancient Historian"}, "description": "Italian historian and philosopher", "extract": ""}],
            },
        ]
    }
    import json
    from unittest.mock import MagicMock, patch

    fake_body = json.dumps(wiki_response).encode()
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=MagicMock(read=MagicMock(return_value=fake_body)))
    cm.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=cm):
        with patch("urllib.request.Request", return_value=MagicMock()):
            candidates = agent._get_born_today_candidates()

    names = [c["name"] for c in candidates]
    # Both intellectuals must appear before the athlete
    assert names.index("Ancient Historian") < names.index("Modern Athlete")
    assert names.index("Old Scientist") < names.index("Modern Athlete")
    # Oldest intellectual appears first
    assert names.index("Ancient Historian") < names.index("Old Scientist")
    # Internal _sort_key / _intellectual fields must NOT be exposed
    for c in candidates:
        assert "_sort_key" not in c
        assert "_intellectual" not in c

# ── Test 11: Control-char stripping applied to description field ──────────────

def test_get_born_today_candidates_strips_control_chars_from_description():
    """Description field also has control chars removed (prompt injection guard)."""
    import json
    from unittest.mock import MagicMock, patch

    agent = _make_agent()
    wiki_response = {
        "births": [
            {
                "year": 1900,
                "pages": [{"titles": {"normalized": "Test Person"}, "description": "physicist\x00with\x01control", "extract": ""}],
            },
        ]
    }
    fake_body = json.dumps(wiki_response).encode()
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=MagicMock(read=MagicMock(return_value=fake_body)))
    cm.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=cm):
        with patch("urllib.request.Request", return_value=MagicMock()):
            candidates = agent._get_born_today_candidates()

    assert len(candidates) == 1
    desc = candidates[0]["description"]
    assert "\x00" not in desc
    assert "\x01" not in desc
    assert "physicist" in desc
