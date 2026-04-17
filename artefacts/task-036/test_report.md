# Test Report: task-036

## Result: PASS

## Tests Run

### T1 — YAML parse check
```
python3 -c "import yaml; yaml.safe_load(open('.claude/agents/reviewer.yaml')); print('OK')"
→ OK

python3 -c "import yaml; yaml.safe_load(open('.claude/agents/builder.yaml')); print('OK')"
→ OK
```
PASS

### T2 — reviewer.yaml findings format includes confidence field
```
grep "confidence:" .claude/agents/reviewer.yaml
→ <file>:<line> — <issue> — <recommendation> — confidence: N (1-100)
→ confidence: 1-100. Represents certainty that the finding is a real issue (not a false positive).
```
PASS

### T3 — builder.yaml >= 80 loop logic present
```
grep "confidence >= 80" .claude/agents/builder.yaml
→ - confidence >= 80: loop back to fix the issue before re-submitting.
```
PASS

### T4 — builder.yaml < 80 build_notes routing present
```
grep "build_notes.md" .claude/agents/builder.yaml
→ - confidence < 80: log the finding to build_notes.md under "Low-confidence Findings" only — do not loop.
```
PASS

### T5 — CLAUDE.md confidence note present
```
grep "Reviewer confidence scoring" CLAUDE.md
→ **Reviewer confidence scoring**: each finding in review.md includes `confidence: N (1-100)` ...
```
PASS

### T6 — M-1 consistency check (same wording across all 3 files)
reviewer.yaml: "real issue (not a false positive)", ">= 80", "routed to build_notes.md only (no loop required)"
CLAUDE.md: "real issue (not a false positive)", ">= 80", "routed to build_notes.md only (no loop required)"
builder.yaml: ">= 80", "log the finding to build_notes.md", "do not loop"
PASS — threshold semantics identical; canonical definition matches in reviewer.yaml and CLAUDE.md verbatim

### T7 — Policy schema integrity (5 required fields intact)
reviewer.yaml: allowed_tools ✓, max_tokens_per_run ✓, require_human_approval ✓, audit_logging ✓, external_calls_allowed ✓
builder.yaml: allowed_tools ✓, max_tokens_per_run ✓, require_human_approval ✓, audit_logging ✓, external_calls_allowed ✓
PASS

## Summary
7/7 tests passed. No regressions. M-1 wording divergence found and fixed during review stage.
