# Task-056 Build Notes — genealogie SQLite schema validator pre-commit hook

## Side-effects check on db.py

File: `/opt/claude/genealogie/genealogy-mas/db.py`

| Import | Side effect? | Assessment |
|--------|-------------|------------|
| `re`, `sqlite3`, `json`, `datetime` | None | stdlib, safe |
| `from models.suggestion import ...` | None | pure dataclass/enum module |
| `from models.person_status import ...` | None | pure dataclass/enum module |
| `from config import DB_PATH, SYNC_VERSION` | Reads `.env` via `python-dotenv` | Harmless; `DB_PATH` resolved to disk path |

**Conclusion**: db.py has no side effects beyond sqlite3 calls via `DB_PATH`. `init_db()` only does SQLite DDL (`CREATE TABLE IF NOT EXISTS`, `ALTER TABLE ADD COLUMN`). Safe for dry-run approach.

**Design choice**: full dry-run via exec() with `sys.modules` patching — preferred over static SQL extraction because it validates the actual Python logic (including migration loop) rather than just the SQL strings.

## Implementation notes

### DB_PATH patching strategy

`config.py` sets `DB_PATH = str(_HERE / "data" / "genealogy.db")`. Since db.py imports it via `from config import DB_PATH`, prepending `DB_PATH = ":memory:"` to the source would be overwritten by the import. Instead, `validate_db.py` injects a mock `config` module into `sys.modules` before exec'ing the staged source. The mock sets `config.DB_PATH = ":memory:"` so `_get_conn()` in db.py connects to an in-memory SQLite database.

Models (`models.suggestion`, `models.person_status`) are also mocked to avoid requiring the genealogy-mas package to be on sys.path during hook execution.

### Ruff compliance

During integration testing, ruff caught two issues in validate_db.py:
1. Unused `import sqlite3` — removed (sqlite3 is used only by db.py's own code when exec'd)
2. Missing blank line between module docstring and imports — added

Both were fixed before commit.

## Commands run and output

```
$ python3 -m py_compile /opt/claude/genealogie/hooks/validate_db.py
# → Syntax OK

$ python3 /opt/claude/genealogie/hooks/validate_db.py /opt/claude/genealogie/genealogy-mas/db.py
db.py: syntax OK
db.py: init_db() dry-run OK (:memory:)

$ bash -n /opt/claude/genealogie/hooks/pre-commit
# → Shell syntax OK

$ bash hooks/pre-commit  (with hooks/validate_db.py staged)
All checks passed!
# Exit: 0

# Syntax error test
$ python3 validate_db.py <broken-syntax.py>
db.py: syntax error: SyntaxError: '(' was never closed
# Exit: 1

# Runtime error test (bad SQL in init_db)
$ python3 validate_db.py <bad-sql.py>
db.py: init_db() dry-run failed: near "INVALID": syntax error
# Exit: 1
```

## Disk isolation verification

`/opt/claude/genealogie/genealogy-mas/data/genealogy.db` last modified: 2026-03-29 (unchanged during testing). No disk DB file was created by the validator.

## Review loop fixes (post-review)

### F-2 (Reviewer, confidence 90) — Remove dead `@classmethod __call__` methods

The three mock enum subclasses (`SuggestionStatus`, `SuggestionType`, `AkteStatus`) each had a
`@classmethod __call__` that was never invoked by Python's type machinery. `SuggestionStatus("pending")`
dispatches through `_Enum.__init__` inheritance, not through `cls.__call__`. All three classmethods
removed in commit `5c079d3`.

### F-1 (CQR, Major) — Add `except SystemExit` before `except Exception`

`SystemExit` inherits from `BaseException`, not `Exception`. If the exec'd `db.py` calls `sys.exit()`
at module level, the `SystemExit` propagated past the `except Exception` clause — `init_db()` would
never be called but the hook might exit 0 silently.

Fix added explicit `except SystemExit` handler before `except Exception`:
- `sys.exit(non-zero)` → prints diagnostic message and exits 1 (hard failure)
- `sys.exit(0)` → prints warning and exits 0 (treats as pass, dry-run skipped)

Also applied ruff format corrections (long `print` calls split to multi-line) before the pre-commit
hook accepted the commit.

## Acceptance criteria verification

| # | Criterion | Status |
|---|-----------|--------|
| 1 | `hooks/pre-commit` appended at `/opt/claude/genealogie/hooks/pre-commit` | PASS |
| 2 | When db.py staged: py_compile + init_db() dry-run; exits non-zero if either fails | PASS (tested both failure modes) |
| 3 | When db.py not staged: grep pattern returns empty → block skipped → exits 0 | PASS |
| 4 | Dry-run isolation: `DB_PATH` patched to `':memory:'` via sys.modules mock | PASS (genealogy.db mtime unchanged) |
