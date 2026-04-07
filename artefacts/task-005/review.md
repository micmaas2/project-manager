# Review — task-005: migrate-vault.py

**Status**: APPROVED  
**Reviewer**: Sonnet 4.6 (code-quality pass)  
**Date**: 2026-04-07  

## Scope compliance

All acceptatiecriteria met:
- [x] Migrates old-format notes to YAML frontmatter
- [x] Normalises concatenated/camelCase tags to hyphenated lowercase
- [x] Non-LinkedIn URL notes: fetch + Claude API re-enrichment
- [x] LinkedIn / unresolvable URLs: adds `needs-review` tag, preserves existing content
- [x] `--dry-run` flag: prints planned changes, no writes
- [x] pylint 10.00/10, flake8 clean
- [x] Runs on Pi4 via `python3 migrate-vault.py --vault /opt/obsidian-vault [--dry-run]`

## Security

- [x] `ANTHROPIC_API_KEY` from env var; never hardcoded
- [x] Private IP block: `localhost`, `127.x`, `10.x`, `192.168.x`, `172.16-31.x`
- [x] `requests.get(timeout=10)` — no hanging requests
- [x] Vault path safety check: `os.path.realpath` prevents path traversal
- [x] No writes outside vault_path

## Code quality

- [x] All functions single-responsibility; helpers extracted (`_extract_section`, `_apply_bold_field`)
- [x] Graceful error handling: broad `except Exception` only on external calls (HTTP, Claude API)
- [x] `Optional[str]` / `Optional[dict]` return types for functions that can fail
- [x] `--dry-run` correctly threaded through to `migrate_note`

## Notes

- `importlib.util` used in tests to handle hyphenated filename — correct approach
- Claude API model: `claude-haiku-4-5-20251001` (cheapest) — appropriate
- Topic derivation for thought notes: first non-action tag, stripped of hyphens — reasonable
