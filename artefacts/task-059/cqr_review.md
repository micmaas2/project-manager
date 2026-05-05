# code-quality-reviewer: task-059 batch (BL-122, BL-124, BL-126, BL-127, BL-128, BL-129)

Reviewer: code-quality-reviewer [Sonnet]
Date: 2026-05-05
Scope: Six config/docs fixes across manager.yaml, builder.yaml, pm-close.md, pm-start.md, CLAUDE.md

---

## Overall Verdict: CHANGES REQUESTED

Two blocking issues (both previously identified by the Reviewer at confidence >= 80) plus one
pre-existing M-1 violation surfaced by this batch and one low-confidence observation.

---

## Critical Issues (Must Fix)

None. No security vulnerabilities, data-loss risks, or system failures introduced.

---

## Major Issues (Should Fix)

### Issue 1 — M-1 mirror: reviewer.yaml confidence definition is still a paraphrase

**Location**: `.claude/agents/reviewer.yaml`, lines 77–80 (Field Definitions block)

**Risk**: CLAUDE.md line 128 states verbatim: "M-1 mirror: this definition must match
reviewer.yaml and builder.yaml verbatim." Task-060 fixed builder.yaml correctly. The canonical
definition in both CLAUDE.md and builder.yaml is:

```
Definition: confidence = certainty the finding is a real issue (not a false positive).
```

reviewer.yaml currently reads:

```
confidence: 1-100. Represents certainty that the finding is a real issue (not a false positive).
```

This is a paraphrase, not a verbatim copy. The M-1 copy-paste rule (CLAUDE.md line ~165) forbids
paraphrase. The mirror is half-fixed — builder.yaml matches CLAUDE.md, reviewer.yaml does not.

**Fix**: Replace lines 77–80 of reviewer.yaml Field Definitions block with:
```yaml
  ### Field Definitions
  Definition: confidence = certainty the finding is a real issue (not a false positive).
  Builder loops only on findings with confidence >= 80.
  Findings with confidence < 80 are routed to build_notes.md only (no loop required).
```

Confidence: 95

---

### Issue 2 — pm-start.md step 6: recovery bullet is a paraphrase of CLAUDE.md line 271

**Location**: `.claude/commands/pm-start.md`, step 6 (line 30)

**Risk**: The M-1 copy-paste rule requires verbatim copy. Current text:
```
If plan mode activates unexpectedly during this skill run, write a minimal plan file
summarising remaining steps, call ExitPlanMode, then continue after approval.
```

CLAUDE.md line 271:
```
if plan mode activates unexpectedly during a PM skill run (e.g. /pm-propose), write a minimal
plan file summarising remaining steps, call ExitPlanMode, then continue the skill after approval.
```

Two diffs: (a) "this skill run" vs "a PM skill run (e.g. /pm-propose)"; (b) "continue after
approval" vs "continue the skill after approval". The second divergence is operationally relevant
— omitting "the skill" leaves ambiguity about what should be continued.

The denial bullet on line 29 is semantically correct (only capitalisation of "if" → "If" differs,
which is acceptable at sentence start).

**Fix**: Replace step 6 recovery bullet in pm-start.md with:
```markdown
- If plan mode activates unexpectedly during a PM skill run (e.g. /pm-propose), write a minimal plan file summarising remaining steps, call ExitPlanMode, then continue the skill after approval.
```

Confidence: 82

---

## Minor Issues (Consider Fixing)

### Issue 3 — Pre-existing: pm-run.md preamble diverges from canonical form

**Location**: `.claude/commands/pm-run.md`, line 3 (pre-existing, not introduced by this batch)

**Risk**: CLAUDE.md line 169 defines the canonical execution-mode preamble as:
```
**Execution mode**: do not enter plan mode. This skill executes already-planned work.
Proceed directly to the Steps below without calling EnterPlanMode.
```

pm-run.md reads:
```
**Execution mode**: do not enter plan mode. This skill executes a task that is already
planned and queued. Proceed directly to the Steps below without calling EnterPlanMode.
```

The body sentence diverges. pm-close.md and pm-propose.md both match the canonical form exactly.
This was not introduced by the current batch but is now surfaced because pm-close.md was brought
into compliance — pm-run.md is now the odd one out.

**Fix**: Update pm-run.md line 3 to the canonical form. Backlog item recommended.

Confidence: 75 (pre-existing, out of scope for this batch — route to backlog)

---

### Issue 4 — manager.yaml Bash scope: no usage restriction in prompt

**Location**: `.claude/agents/manager.yaml` (no specific line — absent text)

**Risk**: builder.yaml constrains Bash explicitly: "Bash commands are ONLY permitted to write
files inside artefacts/<task_id>/. Never run commands that delete files, modify files outside
that directory, or access the network." manager.yaml has no equivalent constraint despite now
having Bash in allowed_tools. Legitimate manager Bash usage is narrow and read-oriented
(command -v checks, git -C branch enumeration, python3 scripts/token_cap_enforcer.py) — a
scope note would close the gap against prompt-injection abuse.

The immediate risk is low: manager.yaml is Opus-gated (require_human_approval: true) and the
operations described in the prompt are safe. But the absence of an explicit scope line means
future prompt edits could silently broaden Bash usage without a policy audit.

**Suggested addition** to manager.yaml prompt (after "NEVER write code or scripts"):
```
NEVER run Bash commands that write or delete files outside tasks/queue.json and logs/.
Bash is permitted only for: command -v prerequisite checks, git -C read operations,
and python3 scripts/token_cap_enforcer.py.
```

Confidence: 65 (quality concern, not a blocking defect)

---

## Positive Observations

- **task-059 (BL-122)**: manager.yaml line 68 fix is correct and matches the CLAUDE.md pattern
  precisely. The parenthetical "(skill name: revise-claude-md) — do NOT use Agent tool or
  subagent_type for claude-md-management:*" mirrors the error-prone invocation pattern documented
  in CLAUDE.md.

- **task-061 (BL-126)**: policy schema is fully compliant. All 5 required fields present; Bash
  added to allowed_tools with require_human_approval: true already set — the semantic policy
  constraint is satisfied with no additional change needed.

- **task-062 (BL-127)**: pm-close.md preamble exactly matches the canonical form in CLAUDE.md
  line 169. Placement immediately after the title and before the run description is correct.

- **task-063 (BL-128)**: pm-start.md step renumbering is clean (1–7 sequential). "Next step
  suggestion" references no hard-coded step numbers, so the renumbering does not create stale
  cross-references.

- **task-064 (BL-129)**: CLAUDE.md line 267 change from EPIC-003 to `—` is consistent with
  pm-start.md step 2 column spec, eliminating a cross-file inconsistency.

---

## Summary

The six-fix batch is largely correct. Five of the six tasks pass without issue. The batch
introduced no security vulnerabilities and correctly satisfies the policy schema for the
manager.yaml Bash addition.

Two blocking findings remain — both are minor one-line corrections to M-1 mirror violations:
(1) reviewer.yaml Field Definitions must be updated to the verbatim canonical confidence
definition, and (2) the pm-start.md step 6 recovery bullet must match CLAUDE.md line 271 word
for word. Both were identified by the Reviewer at confidence >= 80 and confirmed here
independently.

One pre-existing M-1 violation in pm-run.md is surfaced for awareness — recommend backlogging
rather than blocking this batch.

Overall risk rating: **Low** — all issues are policy/wording compliance gaps, not functional
defects or security vulnerabilities. The two blocking findings are single-line text fixes.
