# Reviewer Report — task-016: token_cap_enforcer.py

**[Sonnet]**
**Status: APPROVED**

---

## Acceptance Criteria Verification

### AC1: Script accepts `--task-id` argument; reads `tasks/queue.json`
**PASS**

`argparse` defines `--task-id` (required) and `--queue` (default `tasks/queue.json`). The queue file
is read via `queue_path.read_text()` / `json.loads()`. Both arguments are present and functional.

---

### AC2: If `token_estimate > 400000`: prints ALERT message and exits code 1
**PASS**

Line 89–94 checks `estimate > _CAP_THRESHOLD` (400,000) and prints:
```
ALERT: Task <id> estimated tokens (<n>) exceed 80% of project cap (400k). Reduce scope or split task before proceeding.
```
then calls `sys.exit(1)`.

Minor deviation from the spec wording: the spec says `(400k)` and the script outputs `(400k)` — exact
match. The spec message omits the trailing sentence ("Reduce scope...") but CLAUDE.md includes that
sentence in the 80% cap alert requirement — so this is correct and more complete than the spec.

---

### AC3: If `token_estimate <= 400000`: prints `OK: <id> token_estimate=<n>` and exits 0
**PASS**

Line 96–97: `print(f"OK: {args.task_id} token_estimate={int(estimate)}")` followed by `sys.exit(0)`.
Boundary case (exactly 400,000) correctly falls through to the OK branch (strict `>` comparison).

---

### AC4: `manager.yaml` step 5 references `scripts/token_cap_enforcer.py` explicitly by path
**PASS**

`manager.yaml` line 55–57:
```
5. Token cap preflight: run `python3 scripts/token_cap_enforcer.py --task-id <task_id>`.
   If exit code is non-zero, halt immediately with the printed ALERT message.
   Do NOT spawn Builder or any agent until this is resolved.
```
The path `scripts/token_cap_enforcer.py` is explicit and correct. Instructions are clear and
actionable for the ProjectManager agent.

---

## Security Checklist

| Check | Result |
|---|---|
| No outbound HTTP | PASS — stdlib only; no `urllib`, `requests`, or socket calls |
| Path validation for `--queue` | PASS — `_safe_path()` resolves and asserts containment within `_WORKSPACE_ROOT` |
| No external dependencies | PASS — only `argparse`, `json`, `sys`, `pathlib` |
| No shell injection | PASS — no subprocess, no shell expansion |
| Sensitive data in output | PASS — only task IDs and numeric estimates printed |

---

## Edge Case Coverage

| Case | Handled? | Notes |
|---|---|---|
| Missing queue file | YES — exit 1, message to stderr |
| Invalid JSON | YES — exit 1, `JSONDecodeError` caught |
| Task ID not found | YES — exit 1, message to stderr |
| `token_estimate` is `null`/absent | YES — exit 0 with `token_estimate=none` |
| `token_estimate` is non-numeric | YES — exit 1, type check at line 82 |
| `token_estimate` exactly at threshold | YES — exit 0 (correct boundary) |
| `--queue` path outside workspace | YES — `_safe_path()` blocks and exits 1 |
| Float estimates | YES — `isinstance(estimate, (int, float))` accepted; cast to `int` for display |

---

## Test Coverage Assessment

The test file (`test_token_cap_enforcer.py`) covers all major paths via subprocess invocation:
- Below threshold → OK + exit 0
- Above threshold → ALERT + exit 1
- Exactly at threshold → OK + exit 0
- One above threshold → ALERT + exit 1
- No estimate field → OK + exit 0
- Task not found → exit 1
- Queue file missing → exit 1
- Invalid JSON → exit 1
- Multi-task queue with correct task selection

Coverage is thorough. All 9 test cases map directly to edge cases in the implementation.

One minor gap: no test for `token_estimate` set to a non-numeric type (e.g. `"high"`). This is
handled in the script (lines 82–87) but not tested. This is a low-severity gap — the path is
defensive code and the type guard works correctly.

---

## Findings

**Finding 1 (LOW) — `_WORKSPACE_ROOT` is computed from script file location, not CWD**

`_WORKSPACE_ROOT = Path(__file__).resolve().parent.parent` resolves correctly when invoked as
`python3 scripts/token_cap_enforcer.py` from the repo root (parent of `scripts/` is repo root).
If the script were symlinked or invoked from a different install path, the root could shift.
This is acceptable for the current workspace layout and is not a blocker.

**Finding 2 (LOW) — No test for non-numeric `token_estimate`**

The type-guard at line 82 is correct but untested. Recommend adding a test case in a follow-up:
```python
_make_queue([{"id": "task-x", "token_estimate": "high"}], q)
# expect exit 1 and "not a number" in stderr
```
Not a blocker for approval.

**Finding 3 (INFO) — ALERT message goes to stdout, not stderr**

The ALERT message is printed to stdout (not stderr), which allows the ProjectManager agent to
capture and surface it in its own output. This is intentional and correct for the use case — the
manager reads stdout to relay the message. Errors (missing file, bad JSON, etc.) correctly go to
stderr. No action needed.

---

## Summary

The script is well-structured, handles all specified edge cases, uses stdlib only, and includes
proper path validation. The `manager.yaml` step 5 update is clear and actionable. All four
acceptance criteria are met. The test suite is comprehensive.

**Decision: APPROVED — no changes required before handoff to Tester.**
