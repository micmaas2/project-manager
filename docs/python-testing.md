# Python Testing Patterns

**Testing hyphenated-filename scripts**: Use `importlib.util.spec_from_file_location("module_name", path)` for any script with hyphens in its name — direct Python import fails. See `artefacts/task-005/test_migrate_vault.py`.

**Testing Docker-only packages**: Pre-populate `sys.modules` with `MagicMock` entries for transitive imports; use `type(name, (), {})` (not `MagicMock`) for mixin classes (Python MRO). Load via `importlib.util.spec_from_file_location`. See `artefacts/task-019/test_auth_guard.py`.

**Testing unwritable paths as root**: `chmod 0o444` does NOT prevent root from writing. To simulate an unwritable directory in tests, replace it with a regular file (so `touch <dir>/<file>` fails with "Not a directory"). Document this pattern at the top of any test file that uses it.

**Fixture files for path-guarded scripts**: when writing tests for scripts that use `_safe_path()` workspace-root validation, place fixture files under `artefacts/<task-id>/_fixtures/` — not in `tmp_path` (which resolves to `/tmp`, outside the workspace root and therefore rejected by the path guard).

**Installing non-stdlib test dependencies on Raspberry Pi OS**: `pip install <tool>` fails with a PEP 668 error on system Python. Use `pip install <tool> --break-system-packages` for hook-dependency tools (ruff, shellcheck, etc.) or note the correct install command in the test report prerequisites.

**Task unit tests**: run with `python3 -m pytest artefacts/<task-id>/test_*.py -v`.
