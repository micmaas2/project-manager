"""
Daily Facts Agent - Delivers interesting facts daily via Telegram
Supports ML-driven personalization based on user ratings
"""

import logging
import re
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from src.agents.base_agent import BaseAgent
from src.config import get_settings
from src.data.database import get_db
from src.data.models import DailyFact, UserFactPreferences
from src.utils.llm_client import LLMClient

logger = logging.getLogger(__name__)


class DailyFactsAgent(BaseAgent):
    """
    Delivers daily interesting facts via Telegram

    Features:
    - LLM-generated facts with personalization
    - Categories: Science, Dutch/European History, Philosophy
    - ML learns from user ratings
    - Length adjustment based on feedback
    - Smart category rotation
    """

    def __init__(self):
        super().__init__(name="daily_facts", description="Delivers personalized daily facts via Telegram")
        self.llm_client = LLMClient()
        self.settings = get_settings()

        # Default categories: Born on This Day (quotes and discoveries)
        self.available_categories = ["born_today_quote", "born_today_discovery"]

        logger.info("Daily Facts Agent initialized")

    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process daily facts requests

        Actions:
        - get_daily_fact: Get today's fact (generate if needed)
        - generate_fact: Generate new fact with specific category
        - rate_fact: Rate a fact (1-5 stars + length feedback)
        - set_category_preference: Set preferred category (quotes vs discoveries)
        - get_history: Get past facts
        - update_preferences: Manually update user preferences
        """
        action = request.get("action")

        try:
            if action == "get_daily_fact":
                return await self._get_daily_fact(category=request.get("category"))

            elif action == "generate_fact":
                return await self._generate_fact_with_llm(
                    category=request.get("category"), force_new=request.get("force_new", False)
                )

            elif action == "rate_fact":
                return await self._rate_fact(
                    fact_id=request.get("fact_id"),
                    rating=request.get("rating"),
                    length_feedback=request.get("length_feedback"),
                )

            elif action == "set_category_preference":
                return await self._set_category_preference(
                    fact_id=request.get("fact_id"), preferred_category=request.get("preferred_category")
                )

            elif action == "get_history":
                return await self._get_facts_history(days=request.get("days", 7), limit=request.get("limit", 10))

            elif action == "update_preferences":
                return await self._update_user_preferences(preferences=request.get("preferences", {}))

            else:
                return {"success": False, "error": f"Unknown action: {action}", "agent": self.name}

        except Exception as e:
            return await self.handle_error(e, {"action": action})

    async def _get_daily_fact(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Get today's fact, generating if needed

        Args:
            category: Optional specific category to generate

        Returns:
            Dict with fact data and formatted message
        """
        logger.info("Getting daily fact")

        with get_db() as db:
            # Check if we already have a fact for today
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

            existing_fact = (
                db.query(DailyFact)
                .filter(DailyFact.created_at >= today_start)
                .order_by(DailyFact.created_at.desc())
                .first()
            )

            if existing_fact:
                logger.info(f"Found existing fact for today: {existing_fact.id}")
                fact_dict = existing_fact.to_dict()
            else:
                # Generate new fact
                logger.info("No fact for today, generating new one")
                new_fact_result = await self._generate_fact_with_llm(category)

                if not new_fact_result.get("success"):
                    return new_fact_result

                fact_dict = new_fact_result.get("fact")

        # Format for Telegram
        message = self._format_fact_message(fact_dict)

        return {"success": True, "agent": self.name, "fact": fact_dict, "message": message}

    async def _generate_fact_with_llm(self, category: Optional[str] = None, force_new: bool = False) -> Dict[str, Any]:
        """
        Generate a new interesting fact using LLM with learned preferences

        Args:
            category: Optional category override
            force_new: Force generation even if one exists today

        Returns:
            Dict with generated fact data
        """
        # Load user preferences
        preferences = await self._get_user_preferences()

        # Select category based on rotation + user ratings
        if not category:
            category = self._select_best_category(preferences)

        logger.info(f"Generating fact for category: {category}")

        # Get preferred word count range
        min_words = preferences.get("preferred_word_count_min", 50)
        max_words = preferences.get("preferred_word_count_max", 150)

        # Change 3: Get recently featured person names to exclude from LLM prompt
        excluded_persons = self._get_recent_person_names(days=7)
        logger.info(f"Excluding {len(excluded_persons)} recently featured persons: {excluded_persons}")

        # BL-065 fix: Fetch verified born-today candidates from Wikipedia to prevent
        # LLM date hallucination (LLM was inserting today's date as birth date regardless
        # of the person's actual birth date).
        candidates = self._get_born_today_candidates()

        # Build LLM prompt with excluded persons and verified candidates
        prompt = self._build_fact_generation_prompt(
            category, min_words, max_words,
            excluded_persons=excluded_persons,
            candidates=candidates,
        )

        # Call LLM
        messages = [
            {"role": "system", "content": "You are a knowledgeable educator who shares fascinating, verified facts."},
            {"role": "user", "content": prompt},
        ]

        response = await self.llm_client.chat(messages, max_tokens=400)

        # Parse response
        fact_data = self._parse_llm_response(response, category)

        # Change 3 (cont): Check if LLM ignored the exclusion list; retry once with stronger message
        person_name = fact_data.get("person_name", "")
        if person_name and excluded_persons and person_name.strip().lower() in excluded_persons:
            logger.warning(
                f"LLM returned recently featured person '{person_name}' despite exclusion list. Retrying once."
            )
            # M-1: pass full excluded_persons list AND strong_exclusion for the offending person
            retry_prompt = self._build_fact_generation_prompt(
                category,
                min_words,
                max_words,
                excluded_persons=excluded_persons,
                strong_exclusion=person_name.strip().lower(),
                candidates=candidates,
            )
            retry_messages = [
                {
                    "role": "system",
                    "content": "You are a knowledgeable educator who shares fascinating, verified facts.",
                },
                {"role": "user", "content": retry_prompt},
            ]
            retry_response = await self.llm_client.chat(retry_messages, max_tokens=400)
            fact_data = self._parse_llm_response(retry_response, category)
            person_name = fact_data.get("person_name", "")
            logger.info(f"Retry yielded person: '{person_name}'")

        # Save to database — include person_name in generation_params (Change 3)
        with get_db() as db:
            fact = DailyFact(
                fact_text=fact_data.get("fact_text", response),
                category=fact_data.get("category", category),
                source=fact_data.get("source"),
                word_count=len(fact_data.get("fact_text", "").split()),
                tags=[category],
                generation_params={
                    # C-1: normalise to lowercase so dedup comparisons are case-insensitive
                    "person_name": fact_data.get("person_name", "").strip().lower(),
                    "min_words": min_words,
                    "max_words": max_words,
                    "category": category,
                },
            )
            db.add(fact)
            db.flush()
            db.refresh(fact)

            fact_dict = fact.to_dict()

        logger.info(f"Generated fact {fact_dict['id']}: {fact_dict['category']}, person: '{person_name}'")

        return {"success": True, "agent": self.name, "fact": fact_dict, "message": "Fact generated successfully"}

    # Keywords that identify intellectuals/scientists — used to sort them first.
    _INTELLECTUAL_KEYWORDS: frozenset = frozenset({
        "physicist", "scientist", "mathematician", "philosopher", "biologist",
        "inventor", "engineer", "economist", "writer", "novelist", "poet",
        "playwright", "composer", "psychologist", "physician", "astronomer",
        "chemist", "sociologist", "physiologist", "geneticist", "immunologist",
        "cryptologist", "naturalist", "psychoanalyst", "author", "journalist",
        "logician", "theologian", "historian", "linguist", "architect",
        "botanist", "zoologist", "geologist", "anthropologist",
    })

    def _get_born_today_candidates(self, max_candidates: int = 12) -> list:
        """Fetch real born-on-this-day candidates from Wikipedia REST API.

        BL-065 fix: Provides ground-truth birth dates so the LLM prompt lists
        only people who were actually born on today's date, eliminating the
        hallucination where the model inserted today's date as a person's birth
        date regardless of their actual birthday.

        Sorting strategy: Wikipedia returns entries newest-first (dominated by
        modern athletes). We parse ALL entries, flag intellectuals/scientists
        by keyword, then sort (intellectuals first, oldest first within each
        group) and take the top max_candidates.

        Falls back to [] on any network/parse error — caller falls back to the
        original free-form LLM prompt in that case (zero regression on failure).
        """
        import json
        import urllib.request

        today = datetime.now(timezone.utc)
        url = (
            f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/"
            f"births/{today.month}/{today.day}"
        )
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "MAS-DailyFacts/1.0 (mas.femic.nl)"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())

            births = data.get("births", [])
            raw_candidates = []
            for birth in births:
                pages = birth.get("pages", [])
                if not pages:
                    continue
                page = pages[0]
                raw_description = page.get("description", "")
                description = raw_description.lower()
                is_intellectual = any(
                    kw in description for kw in self._INTELLECTUAL_KEYWORDS
                )
                # Strip ASCII control chars (0x00-0x1F except tab/newline) from
                # both description and extract before including in LLM prompt
                # (prevents prompt injection via structured-field smuggling).
                clean_description = "".join(
                    ch for ch in raw_description
                    if ord(ch) >= 32 or ch in "\n\t"
                )
                raw_extract = page.get("extract", "")[:300]
                extract = "".join(
                    ch for ch in raw_extract
                    if ord(ch) >= 32 or ch in "\n\t"
                )
                year = birth.get("year") or 9999  # unknowns sort last
                raw_candidates.append({
                    "year": birth.get("year"),
                    "name": page.get("titles", {}).get("normalized", ""),
                    "description": clean_description,
                    "extract": extract,
                    "_intellectual": is_intellectual,
                    "_sort_key": (0 if is_intellectual else 1, year),
                })

            # Sort: intellectuals first, oldest-first within each group
            raw_candidates.sort(key=lambda c: c["_sort_key"])

            # Strip internal sort fields before returning
            candidates = []
            for c in raw_candidates[:max_candidates]:
                candidates.append({
                    "year": c["year"],
                    "name": c["name"],
                    "description": c["description"],
                    "extract": c["extract"],
                })

            intellectual_count = sum(
                1 for c in raw_candidates[:max_candidates] if c["_intellectual"]
            )
            logger.info(
                f"Wikipedia born-today: {len(candidates)} candidates for "
                f"{today.month}/{today.day} "
                f"({intellectual_count} intellectuals, "
                f"{len(candidates) - intellectual_count} other)"
            )
            return candidates

        except Exception as e:
            logger.warning(
                f"Wikipedia born-today API failed ({e}); "
                f"falling back to LLM-only mode"
            )
            return []

    def _build_fact_generation_prompt(
        self,
        category: str,
        min_words: int,
        max_words: int,
        excluded_persons: Optional[List[str]] = None,
        strong_exclusion: Optional[str] = None,
        candidates: Optional[list] = None,
    ) -> str:
        """Build LLM prompt for fact generation - Born on This Day in Dutch

        Args:
            category: Fact category to generate
            min_words: Minimum word count for the fact
            max_words: Maximum word count for the fact
            excluded_persons: List of recently featured person names to avoid (Change 1)
            strong_exclusion: Single person name to exclude with a stronger warning after a retry (Change 1)
            candidates: Verified born-today people from Wikipedia (BL-065 fix). When
                non-empty, the prompt lists these candidates so the LLM selects from
                people who actually share today's birth date rather than hallucinating.
        """

        # Get today's date (month and day only, not year) — use UTC for consistency
        today = datetime.now(timezone.utc)
        month_day = today.strftime("%d %B")  # e.g., "15 January"

        # BL-065 fix: when Wikipedia candidates are available, constrain the LLM
        # to choose from verified born-today people instead of free-form guessing.
        if candidates:
            cand_lines = "\n".join(
                f"- {c['name']} ({c['year']}): {c['description']}"
                for c in candidates[:7]
                if c.get("name")
            )
            subject_guidance = (
                f"Choose ONE person from the following verified list of people "
                f"born on {month_day}. Prefer scientists, philosophers, or mathematicians. "
                f"If the list contains no obvious fit for your category, pick the most "
                f"intellectually notable person.\n\n"
                f"Verified born on {month_day}:\n{cand_lines}\n"
            )
        else:
            # Fallback: original free-form guidance (Wikipedia unavailable)
            subject_guidance = f"Find a notable scientist or philosopher born on {month_day} (any year).\n"

        category_detail = {
            "born_today_quote": (
                f"Share one of their most meaningful or thought-provoking quotes WITH context.\n"
                f"Include: Name, birth/death years, brief bio, why the quote matters."
            ),
            "born_today_discovery": (
                f"Focus on their major discovery, achievement, or contribution to science/philosophy.\n"
                f"Include: Name, birth/death years, what they discovered, why it's significant."
            ),
        }

        guidance = f"LANGUAGE: DUTCH\n{subject_guidance}\n{category_detail.get(category, category_detail['born_today_quote'])}"

        # Change 1: Build exclusion block when recently featured persons are known
        exclusion_block = ""
        if strong_exclusion:
            exclusion_block += (
                f"\nYOU MUST NOT feature {strong_exclusion}. "
                f"This person was already featured recently. Choose a completely different person.\n"
            )
        if excluded_persons:
            names_str = ", ".join(excluded_persons)
            exclusion_block += (
                f"\nIMPORTANT: Do NOT feature any of these recently featured persons: {names_str}. "
                f"Pick a DIFFERENT person born on {month_day}.\n"
            )

        prompt = f"""Generate a fact IN DUTCH about a scientist or philosopher born on {month_day}.

{guidance}
{exclusion_block}
Requirements:
- WRITE ENTIRELY IN DUTCH (Nederlandse taal)
- Must be historically accurate and verifiable
- Length: {min_words}-{max_words} words
- Make it engaging and accessible
- Include birth/death years
- International scope (not limited to Dutch figures)

Format your response as:
FACT: [the complete fact in Dutch]
CATEGORY: {category}
SOURCE: [brief source, e.g., "Wikipedia" or field of study]
PERSON: [Full name of the person featured]

Example for born_today_quote:
FACT: Albert Einstein (1879-1955), geboren op 14 maart, zei: "Verbeelding is belangrijker dan kennis." Deze uitspraak weerspiegelt zijn overtuiging dat creativiteit de basis vormt voor wetenschappelijke doorbraken. Einstein ontwikkelde de relativiteitstheorie door gedachte-experimenten, niet alleen door wiskundige berekeningen.
CATEGORY: born_today_quote
SOURCE: Theoretische natuurkunde
PERSON: Albert Einstein

Now generate a new fact in Dutch for {category}:"""

        return prompt

    def _parse_llm_response(self, response: str, default_category: str) -> Dict[str, str]:
        """Parse LLM response into structured data.

        M-2: Use regex to capture each field up to the next field label or end-of-string
        so that multi-line FACT text is captured in full rather than truncated at the first
        newline.  The same pattern is applied to CATEGORY, SOURCE, and PERSON for
        consistency — those are typically single-line but may also contain embedded newlines.
        """
        text = response.strip()
        fact_data = {"fact_text": "", "category": default_category, "source": None, "person_name": ""}

        # Shared sentinel: a field ends when the next labelled field starts or the string ends.
        # re.DOTALL lets '.' match newlines inside a field value (multi-line FACT support).
        # re.MULTILINE is intentionally NOT used: with DOTALL active, $ matches end-of-line
        # rather than end-of-string, causing the lazy .*? to stop at line 1. Use (?:^|\n)
        # for line-start anchoring and \Z for end-of-string in the lookahead instead.
        def _extract(label: str) -> str:
            m = re.search(
                rf"(?:^|\n){label}:\s*(.*?)(?=\n(?:FACT|CATEGORY|PERSON|SOURCE):|\Z)",
                text,
                re.DOTALL | re.IGNORECASE,
            )
            return m.group(1).strip() if m else ""

        fact_text = _extract("FACT")
        if fact_text:
            fact_data["fact_text"] = fact_text

        category = _extract("CATEGORY")
        if category:
            fact_data["category"] = category.lower()

        source = _extract("SOURCE")
        if source:
            fact_data["source"] = source

        person_name = _extract("PERSON")
        if person_name:
            fact_data["person_name"] = person_name

        # Fallback: use entire response if FACT field was not found
        if not fact_data["fact_text"]:
            fact_data["fact_text"] = text

        return fact_data

    def _get_recent_person_names(self, days: int = 7) -> list:
        """Return person names from facts generated in the last N days.

        Change 4: New helper that reads person_name from generation_params JSON
        column so the LLM prompt can exclude recently featured persons.
        No DB migration required — generation_params is an existing JSON column.
        """
        try:
            with get_db() as db:
                cutoff = datetime.now(timezone.utc) - timedelta(days=days)
                facts = db.query(DailyFact).filter(DailyFact.created_at >= cutoff).all()
                names = []
                for f in facts:
                    params = f.generation_params or {}
                    name = params.get("person_name", "")
                    if name:
                        # C-1: normalise returned names so dedup set is always lowercase
                        names.append(name.strip().lower())
                return names
        except Exception as e:
            # C-2: on any DB failure, log a warning and return empty list so generation continues
            logger.warning(f"Could not load recent person names for dedup: {e}")
            return []

    def _select_best_category(self, preferences: Dict[str, Any]) -> str:
        """
        Select next category based on rotation and user ratings

        Strategy:
        1. Get category ratings from preferences
        2. Rotate through categories but weight by rating
        3. Ensure variety (don't repeat same category too often)
        """
        category_ratings = preferences.get("category_ratings", {})

        # Get recent facts to avoid repetition
        with get_db() as db:
            recent_facts = db.query(DailyFact).order_by(DailyFact.created_at.desc()).limit(3).all()

            recent_categories = [f.category for f in recent_facts]

        # Score each category
        category_scores = {}
        for cat in self.available_categories:
            # Base score from user rating (default 3.0)
            rating_score = category_ratings.get(cat, 3.0)

            # Penalty if used recently (-1 for each recent use)
            recency_penalty = recent_categories.count(cat) * 1.0

            category_scores[cat] = rating_score - recency_penalty

        # Select highest scoring category
        best_category = max(category_scores, key=category_scores.get)

        logger.info(f"Category selection scores: {category_scores}, selected: {best_category}")

        return best_category

    async def _rate_fact(
        self, fact_id: int, rating: Optional[int] = None, length_feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Rate a fact and update user preferences

        Args:
            fact_id: ID of the fact to rate
            rating: 1-5 star rating
            length_feedback: 'too_short', 'perfect', or 'too_long'
        """
        if rating and not (1 <= rating <= 5):
            return {"success": False, "error": "Rating must be between 1 and 5", "agent": self.name}

        with get_db() as db:
            fact = db.query(DailyFact).filter(DailyFact.id == fact_id).first()

            if not fact:
                return {"success": False, "error": f"Fact not found: {fact_id}", "agent": self.name}

            # Update fact ratings
            if rating:
                fact.user_rating = rating
                fact.was_read = True

            if length_feedback:
                fact.length_rating = length_feedback

            db.flush()

            # Update user preferences based on rating
            if rating:
                await self._update_preferences_from_rating(fact, rating, length_feedback)

        logger.info(f"Rated fact {fact_id}: {rating}/5, length: {length_feedback}")

        return {
            "success": True,
            "agent": self.name,
            "message": f"Thank you for rating! Your preferences have been updated.",
        }

    async def _update_preferences_from_rating(
        self, fact: DailyFact, rating: int, length_feedback: Optional[str] = None
    ) -> None:
        """
        Update user preferences based on rating

        NOTE: Star ratings now only track fact quality, NOT category preference
        Category preference is set separately via _set_category_preference
        """
        with get_db() as db:
            # Get or create preferences
            prefs = db.query(UserFactPreferences).first()
            if not prefs:
                prefs = UserFactPreferences()
                db.add(prefs)

            # Track total ratings (for fact quality tracking)
            prefs.total_facts_rated = (prefs.total_facts_rated or 0) + 1
            prefs.last_rating_date = datetime.now(timezone.utc)

            # Update length preferences (only if feedback provided)
            if length_feedback and fact.word_count:
                current_min = prefs.preferred_word_count_min or 50
                current_max = prefs.preferred_word_count_max or 150

                if length_feedback == "too_short":
                    prefs.preferred_word_count_min = max(fact.word_count + 10, current_min)
                    prefs.preferred_word_count_max = max(fact.word_count + 30, current_max)
                elif length_feedback == "too_long":
                    prefs.preferred_word_count_min = min(fact.word_count - 30, current_min)
                    prefs.preferred_word_count_max = min(fact.word_count - 10, current_max)
                # 'perfect' - no change needed

            db.flush()

            logger.info(
                f"Updated preferences: fact_quality_rating={rating}, "
                f"word_range={prefs.preferred_word_count_min}-{prefs.preferred_word_count_max}"
            )

    async def _set_category_preference(self, fact_id: int, preferred_category: str) -> Dict[str, Any]:
        """
        Set category preference (separate from fact quality rating)

        Args:
            fact_id: ID of the fact being rated
            preferred_category: Preferred category ('born_today_quote' or 'born_today_discovery')

        Returns:
            Success dict
        """
        if preferred_category not in self.available_categories:
            return {
                "success": False,
                "error": f"Invalid category: {preferred_category}",
                "agent": self.name
            }

        with get_db() as db:
            # Get or create preferences
            prefs = db.query(UserFactPreferences).first()
            if not prefs:
                prefs = UserFactPreferences()
                db.add(prefs)

            # Update category ratings
            category_ratings = prefs.category_ratings or {}

            # Increase preferred category rating, decrease others
            for cat in self.available_categories:
                if cat == preferred_category:
                    # Boost preferred category
                    current = category_ratings.get(cat, 3.0)
                    category_ratings[cat] = min(5.0, current + 0.5)
                else:
                    # Slightly decrease others
                    current = category_ratings.get(cat, 3.0)
                    category_ratings[cat] = max(1.0, current - 0.2)

            prefs.category_ratings = category_ratings
            db.flush()

            logger.info(f"Updated category preference: {preferred_category}, ratings={category_ratings}")

        return {
            "success": True,
            "agent": self.name,
            "message": f"Category preference updated: {preferred_category}"
        }

    async def _get_facts_history(self, days: int = 7, limit: int = 10) -> Dict[str, Any]:
        """Get past facts"""
        logger.info(f"Getting facts history for {days} days (limit {limit})")

        with get_db() as db:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

            facts = (
                db.query(DailyFact)
                .filter(DailyFact.created_at >= cutoff_date)
                .order_by(DailyFact.created_at.desc())
                .limit(limit)
                .all()
            )

            facts_list = [f.to_dict() for f in facts]

        return {
            "success": True,
            "agent": self.name,
            "facts": facts_list,
            "count": len(facts_list),
            "message": f"Found {len(facts_list)} facts from the last {days} days",
        }

    async def _get_user_preferences(self) -> Dict[str, Any]:
        """Get current user preferences"""
        with get_db() as db:
            prefs = db.query(UserFactPreferences).first()

            if prefs:
                return prefs.to_dict()
            else:
                # Return defaults
                return {
                    "category_ratings": {},
                    "preferred_word_count_min": 50,
                    "preferred_word_count_max": 150,
                    "preferred_complexity": "medium",
                    "total_facts_rated": 0,
                }

    async def _update_user_preferences(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Manually update user preferences"""
        with get_db() as db:
            prefs = db.query(UserFactPreferences).first()
            if not prefs:
                prefs = UserFactPreferences()
                db.add(prefs)

            # Update fields
            if "category_ratings" in preferences:
                prefs.category_ratings = preferences["category_ratings"]
            if "preferred_word_count_min" in preferences:
                prefs.preferred_word_count_min = preferences["preferred_word_count_min"]
            if "preferred_word_count_max" in preferences:
                prefs.preferred_word_count_max = preferences["preferred_word_count_max"]
            if "preferred_complexity" in preferences:
                prefs.preferred_complexity = preferences["preferred_complexity"]

            db.flush()
            db.refresh(prefs)

            return {
                "success": True,
                "agent": self.name,
                "preferences": prefs.to_dict(),
                "message": "Preferences updated successfully",
            }

    def _format_fact_message(self, fact: Dict[str, Any]) -> str:
        """Format fact for Telegram delivery"""
        category = fact.get("category", "General").replace("_", " ").title()
        fact_text = fact.get("fact_text", "No fact available")
        source = fact.get("source", "")
        fact_id = fact.get("id")

        # Emoji mapping for categories
        category_emoji = {
            "science": "🔬",
            "neuroscience": "🧠",
            "space": "🚀",
            "history": "📜",
            "dutch": "🇳🇱",
            "european": "🇪🇺",
            "philosophy": "💭",
            "psychology": "🧠",
            "nature": "🌿",
        }

        # Find matching emoji
        emoji = "🧠"  # default
        for key, em in category_emoji.items():
            if key in category.lower():
                emoji = em
                break

        message = f"""{emoji} *Daily Fact - {category}*

{fact_text}

📚 Category: {category}
"""

        if source:
            message += f"📖 Source: {source}\n"

        return message
