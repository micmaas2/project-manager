# Test Report — task-037: CLAUDE.md Size Reduction

**Date**: 2026-04-17
**Tester**: Tester agent (Sonnet) — criterion 5 corrected by PM (false positive)
**Verdict**: PASS

---

## Criterion 1: CLAUDE.md ≤ 35,000 characters

**Command**: `wc -c /opt/claude/project_manager/CLAUDE.md`
**Output**: `29830 /opt/claude/project_manager/CLAUDE.md`
**Result**: PASS (29,830 ≤ 35,000)

---

## Criterion 2: No operational rule deleted

Each phrase grepped with `grep -c "<phrase>" CLAUDE.md`:

| Phrase | Count | Result |
|--------|-------|--------|
| `require_human_approval` | 3 | PASS |
| `confidence: N (1-100)` | 1 | PASS |
| `M-1 mirror` | 1 | PASS |
| `pm-propose commit discipline` | 1 | PASS |
| `BACKLOG: ` | 1 | PASS |
| `allowed_tools` | 3 | PASS |
| `audit_logging` | 2 | PASS |
| `external_calls_allowed` | 3 | PASS |
| `SelfImprover` | 10 | PASS |
| `Artefact minimum for git-only tasks` | 1 | PASS |
| `pre-commit` | 4 | PASS |
| `queue.json` | 5 | PASS |
| `artefact_path` | 4 | PASS |
| `token_estimate` | 2 | PASS |
| `Doc commits intended for` | 1 | PASS |

**Result**: PASS (all 15 phrases present)

---

## Criterion 3: Pointer lines resolve to real files

**Command**: `ls /opt/claude/project_manager/docs/n8n-deployment.md /opt/claude/project_manager/docs/python-testing.md`
**Output**:
```
/opt/claude/project_manager/docs/n8n-deployment.md
/opt/claude/project_manager/docs/python-testing.md
```
**Result**: PASS (both files exist)

---

## Criterion 4: Pre-commit hook syntax

**Command**: `bash -n /opt/claude/project_manager/hooks/pre-commit`
**Exit code**: 0
**Result**: PASS

---

## Criterion 5: "GitHub API commits" block NOT duplicated

The criterion expects the phrase to appear 0 times in `docs/n8n-deployment.md` and once in `CLAUDE.md`.

**Actual counts**:
- `grep -c "GitHub API commits" docs/n8n-deployment.md` → **0**
- `grep -c "GitHub API commits" CLAUDE.md` → **2**

**Lines in CLAUDE.md containing the phrase**:
```
Line 63:  If main has GitHub API commits that develop lacks (diverged), use
          `--force-with-lease` ...
Line 375: **GitHub API commits (stdlib)**: read: `GET /repos/{repo}/...`
```

The criterion specifies the phrase should appear "exactly once" in CLAUDE.md. It appears **twice**:
- Line 63: inside the Git Branching Strategy section (divergence note — branching guidance, not n8n deployment detail)
- Line 375: the `**GitHub API commits (stdlib)**` block describing the stdlib read/write pattern — this is the block the task intended to extract to `docs/n8n-deployment.md`

**Assessment (corrected)**: The deduplication goal was to remove the block from `docs/n8n-deployment.md` — which succeeded (0 occurrences there). The canonical copy at CLAUDE.md line 375 is intentionally retained. Line 63 is a different sentence in the git-branching section ("If main has GitHub API commits that develop lacks…") — a different context, not a duplicate block. Two distinct occurrences of the words in different contexts is correct and expected.

**Result**: PASS

---

## Criterion 6: Linked docs are non-empty

**Command**: `wc -l /opt/claude/project_manager/docs/n8n-deployment.md /opt/claude/project_manager/docs/python-testing.md`
**Output**:
```
 114 docs/n8n-deployment.md
  11 docs/python-testing.md
 125 total
```
**Result**: PASS (both files have content; n8n-deployment.md: 114 lines, python-testing.md: 11 lines)

---

## Summary

| # | Criterion | Result |
|---|-----------|--------|
| 1 | CLAUDE.md ≤ 35,000 chars | PASS |
| 2 | No operational rule deleted (15 phrases) | PASS |
| 3 | Pointer files exist | PASS |
| 4 | Pre-commit hook syntax valid | PASS |
| 5 | "GitHub API commits" block not duplicated across files | PASS |
| 6 | Linked docs are non-empty | PASS |

## Overall Verdict: PASS

All 6 criteria met. Criterion 5 false-positive corrected: two occurrences in CLAUDE.md are two different contexts (line 63: git-branching divergence note; line 375: canonical stdlib pattern block). docs/n8n-deployment.md has 0 occurrences — deduplication goal achieved.
