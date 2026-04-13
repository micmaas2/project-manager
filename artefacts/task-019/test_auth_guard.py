"""
Unit tests for telegram_listener.py auth guard (task-019, BL-060)

Tests _process_update() chat_id validation:
- Authorized chat_id → message processed normally
- Unauthorized chat_id → dropped with WARNING logged, no processing

Run locally (sys.modules-based injection, no Pi4 deps needed):
  python3 -m pytest artefacts/task-019/test_auth_guard.py -v

Or from Pi4 (full package available):
  python3 /path/to/test_auth_guard.py -v
"""
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock


# ---------------------------------------------------------------------------
# Build fake module tree so `from src.X import Y` works without the real pkg
# ---------------------------------------------------------------------------

AUTHORIZED_CHAT_ID = 7761755508
UNAUTHORIZED_CHAT_ID = 9999999999

_mock_settings = MagicMock()
_mock_settings.telegram_chat_id = AUTHORIZED_CHAT_ID


def _install_fake_modules():
    """Inject mock modules into sys.modules before telegram_listener is imported."""

    # Helper: ensure a parent module exists in sys.modules
    def ensure_pkg(name):
        if name not in sys.modules:
            sys.modules[name] = MagicMock()

    # src package tree
    ensure_pkg("src")
    ensure_pkg("src.integration")
    ensure_pkg("src.orchestration")
    ensure_pkg("src.utils")

    # src.config — settings singleton
    config_mod = MagicMock()
    config_mod.settings = _mock_settings
    sys.modules["src.config"] = config_mod

    # src.integration.telegram_bot
    tgbot_mod = MagicMock()
    tgbot_mod.TelegramBot = MagicMock
    sys.modules["src.integration.telegram_bot"] = tgbot_mod

    # Mixin classes — each must be a real class so TelegramListener MRO works
    mixins = [
        "CallbackHandlerMixin",
        "FactsCommandsMixin",
        "MomentumCommandsMixin",
        "PlanningCommandsMixin",
        "ScheduleCommandsMixin",
        "StatusCommandsMixin",
        "SyncCommandsMixin",
        "TaskCommandsMixin",
    ]
    tc_mod = MagicMock()
    for name in mixins:
        # Must be a real type, not a MagicMock, for class inheritance
        setattr(tc_mod, name, type(name, (), {}))
    sys.modules["src.integration.telegram_commands"] = tc_mod

    # src.orchestration.coordinator
    coord_mod = MagicMock()
    coord_mod.Coordinator = MagicMock
    sys.modules["src.orchestration.coordinator"] = coord_mod

    # src.utils.error_messages
    err_mod = MagicMock()
    err_mod.ErrorMessageFormatter = MagicMock
    err_mod.format_telegram_error = MagicMock(return_value="error")
    sys.modules["src.utils.error_messages"] = err_mod


_install_fake_modules()

# Now safe to import the module under test
import importlib
import importlib.util
import pathlib

# Try to locate telegram_listener.py — works both locally (via Pi4 path if mounted)
# and when run from the project_manager workspace where the file was copied to tmp.
_LISTENER_CANDIDATES = [
    "/opt/mas/src/integration/telegram_listener.py",      # Pi4 (native or mounted)
    "/tmp/telegram_listener.py",                           # Copied for CI
]

_listener_path = None
for _p in _LISTENER_CANDIDATES:
    if pathlib.Path(_p).exists():
        _listener_path = _p
        break

if _listener_path is None:
    raise FileNotFoundError(
        "telegram_listener.py not found at any candidate path. "
        "Run on Pi4 or copy the file to /tmp/telegram_listener.py"
    )

_spec = importlib.util.spec_from_file_location(
    "src.integration.telegram_listener", _listener_path
)
_tl_module = importlib.util.module_from_spec(_spec)
sys.modules["src.integration.telegram_listener"] = _tl_module
_spec.loader.exec_module(_tl_module)

TelegramListener = _tl_module.TelegramListener


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_text_update(chat_id: int, text: str = "/help") -> dict:
    return {
        "update_id": 1001,
        "message": {
            "message_id": 42,
            "chat": {"id": chat_id, "type": "private"},
            "from": {"id": chat_id, "username": "testuser"},
            "text": text,
        },
    }


def _make_callback_update(chat_id: int) -> dict:
    return {
        "update_id": 1002,
        "callback_query": {
            "id": "cq_001",
            "from": {"id": chat_id, "username": "testuser"},
            "data": "some_action",
        },
    }


def _make_empty_update() -> dict:
    return {"update_id": 1003}


def _make_listener() -> TelegramListener:
    """Create a TelegramListener with all external I/O mocked."""
    listener = object.__new__(TelegramListener)
    listener.bot = MagicMock()
    listener.bot.send_message_sync = MagicMock()
    listener.coordinator = MagicMock()
    listener.last_update_id = None
    listener.running = False
    listener._handle_command = AsyncMock()
    listener._handle_query = AsyncMock()
    listener._handle_callback_query = AsyncMock()
    return listener


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestAuthGuard(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        # Reset settings to authorized state before each test
        _mock_settings.telegram_chat_id = AUTHORIZED_CHAT_ID
        self.listener = _make_listener()

    # AC1 + AC3: Authorized chat_id → processed normally ----------------

    async def test_authorized_chat_id_processes_command(self):
        """Authorized chat_id must reach _handle_command unchanged."""
        await self.listener._process_update(_make_text_update(AUTHORIZED_CHAT_ID, "/tasks"))
        self.listener._handle_command.assert_awaited_once_with("/tasks", AUTHORIZED_CHAT_ID)

    async def test_authorized_chat_id_processes_query(self):
        """Authorized chat_id natural language must reach _handle_query."""
        await self.listener._process_update(
            _make_text_update(AUTHORIZED_CHAT_ID, "what is my schedule?")
        )
        self.listener._handle_query.assert_awaited_once_with(
            "what is my schedule?", AUTHORIZED_CHAT_ID
        )

    # AC2: Unauthorized chat_id → dropped + WARNING logged ---------------

    async def test_unauthorized_chat_id_drops_message(self):
        """Unauthorized chat_id must NOT reach _handle_command or _handle_query."""
        await self.listener._process_update(_make_text_update(UNAUTHORIZED_CHAT_ID, "/tasks"))
        self.listener._handle_command.assert_not_awaited()
        self.listener._handle_query.assert_not_awaited()

    async def test_unauthorized_chat_id_logs_warning(self):
        """Unauthorized chat_id must emit a WARNING with 'Unauthorized chat_id'."""
        with self.assertLogs("src.integration.telegram_listener", level="WARNING") as cm:
            await self.listener._process_update(_make_text_update(UNAUTHORIZED_CHAT_ID, "/tasks"))
        self.assertTrue(
            any("Unauthorized chat_id" in line for line in cm.output),
            f"Expected 'Unauthorized chat_id' in WARNING, got: {cm.output}",
        )

    async def test_unauthorized_chat_id_warning_includes_id_value(self):
        """WARNING log must include the numeric chat_id for audit traceability."""
        with self.assertLogs("src.integration.telegram_listener", level="WARNING") as cm:
            await self.listener._process_update(_make_text_update(UNAUTHORIZED_CHAT_ID, "/tasks"))
        self.assertTrue(
            any(str(UNAUTHORIZED_CHAT_ID) in line for line in cm.output),
            f"Expected {UNAUTHORIZED_CHAT_ID} in WARNING log, got: {cm.output}",
        )

    # Fail-open: guard inactive when telegram_chat_id is None -----------

    async def test_no_enforcement_when_chat_id_not_configured(self):
        """If settings.telegram_chat_id is None, all senders are allowed (fail-open)."""
        _mock_settings.telegram_chat_id = None
        await self.listener._process_update(_make_text_update(UNAUTHORIZED_CHAT_ID, "/help"))
        self.listener._handle_command.assert_awaited_once()

    # callback_query path is not affected by message-level guard ----------

    async def test_callback_query_still_dispatched(self):
        """callback_query updates bypass the message chat_id guard entirely."""
        await self.listener._process_update(_make_callback_update(UNAUTHORIZED_CHAT_ID))
        self.listener._handle_callback_query.assert_awaited_once()
        self.listener._handle_command.assert_not_awaited()

    # Silent no-op for structurally invalid updates ----------------------

    async def test_empty_update_is_silently_ignored(self):
        """Updates with neither message nor callback_query are safely ignored."""
        await self.listener._process_update(_make_empty_update())
        self.listener._handle_command.assert_not_awaited()
        self.listener._handle_query.assert_not_awaited()


if __name__ == "__main__":
    unittest.main(verbosity=2)
