# Test Report — task-027
**Agent**: Tester [Sonnet]
**Date**: 2026-04-14

---

## Test Suite: test_healthcheck.py

Run: `python3 -m pytest artefacts/task-027/test_healthcheck.py -v`

| Test | Description | Result |
|------|-------------|--------|
| test_all_pass | All 4 checks green → exit 0, no [FAIL] | PASS |
| test_missing_hook_symlink | Remove pre-commit symlink → exit 1, [FAIL] HOOKS | PASS |
| test_invalid_queue_json | queue.json missing required "tasks" key → exit 1, [FAIL] SCHEMA | PASS |
| test_malformed_yaml | YAML with unclosed bracket → exit 1, [FAIL] YAML + filename | PASS |
| test_yaml_missing_policy_field | YAML with only 2/5 policy fields → exit 1, [FAIL] YAML | PASS |
| test_unwritable_logs | logs/ replaced with file (dir touch fails) → exit 1, [FAIL] LOGS | PASS |
| test_idempotent | Two consecutive runs → same exit code + identical output | PASS |

**Total: 7/7 PASS**

---

## Acceptance Criteria Verification

| Criterion | Evidence | Verdict |
|-----------|----------|---------|
| Script exits 0 when all checks pass; exits 1 with labelled output on failure | test_all_pass (0), tests 2–6 (1 + labels) | PASS |
| Four checks: hooks symlinks, queue.json schema, agent YAML parse, logs/ writability | test_missing_hook_symlink, test_invalid_queue_json, test_malformed_yaml/test_yaml_missing_policy_field, test_unwritable_logs | PASS |
| `bash -n` exits 0; script is idempotent | `bash -n scripts/pm-healthcheck.sh` exit 0; test_idempotent | PASS |

**Overall: PASS**

---

## Notes

- Tests run as root; chmod-based unwritable simulation replaced with file-instead-of-dir pattern (root bypasses DAC).
- 3 real `queue.schema.json` bugs discovered and fixed as part of this task (story_id nullable, assigned_to enum, token_estimate max).
