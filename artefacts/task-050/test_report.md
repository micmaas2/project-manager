# Test Report — task-050

| Test | Status | Notes |
|------|--------|-------|
| T1-format-line | PASS | `Format:` line in self-improver.yaml contains exactly `| ISO-date | Agent | Lesson | Applied To | Confidence | Scope |`; field definitions for `Confidence` (integer 1-100) and `Scope` are present immediately following on lines 29-31 |
| T2-lessons-header | PASS | Header row is `| Date | Agent | Lesson | Applied To | Confidence | Scope |`; separator row contains 6 pipe-separated fields (`|------|-------|--------|------------|------------|-------|`) |
| T3-claude-md-m1 | PASS | CLAUDE.md append-only table string matches lessons.md header exactly: `| Date | Agent | Lesson | Applied To | Confidence | Scope |` — same 6 columns, same names |
| T4-yaml-syntax | PASS | `python3 -c "import yaml; yaml.safe_load(...)"` returned `YAML_OK` — file is valid YAML |
| T5-policy-fields | PASS | All 5 required fields present: `allowed_tools`, `max_tokens_per_run`, `require_human_approval` (true), `audit_logging` (true), `external_calls_allowed` (false) |

## Verdict: PASS

All 5 acceptance criteria verified. The self-improver.yaml and lessons.md are consistent with the 6-column schema including `Confidence` and `Scope`. CLAUDE.md M-1 mirror is aligned. YAML is valid and all policy fields are present.
