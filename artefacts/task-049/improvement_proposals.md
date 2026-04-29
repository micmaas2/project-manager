# Improvement Proposals — task-049

**Task**: Hooks-over-prompts audit — implement top 3 rules as hooks (BL-088)
**SelfImprover**: Haiku [Haiku]
**Date**: 2026-04-29

---

## Proposal 1

**Target file**: `CLAUDE.md`

**Change**: In the "PreToolUse hooks for known-bad patterns" section, append the following guidance after the existing paragraph:

```
**Multi-condition hook rules must use correlated regexes, not independent scans**: when a rule
requires two patterns to co-occur within the same logical unit (function call, block, expression),
use a single regex that enforces co-occurrence — never two separate `re.search` calls on the same
content. Independent scans can match in unrelated locations and produce false positives.
```

**Rationale**: task-049 CQR Finding 1 (conf 85) caught the independent-scan anti-pattern before shipping. The fix was non-trivial (required understanding regex grouping across call boundaries). This rule prevents future hook authors from repeating the same design mistake without guidance.

**Status**: APPROVED

---

## Proposal 2

**Target file**: `CLAUDE.md`

**Change**: In the "Workflow guard hook" bullet (Governance section), append a note about Write-only enforcement for document-level invariants:

```
**Document-level invariant hooks enforce on Write only**: Edit/MultiEdit calls deliver diff
fragments — a hook checking that two fields both appear in a document must use `Write` only,
where the full document is available. Return `(None, None)` early for Edit/MultiEdit to avoid
false positives on valid multi-step edits.
```

**Rationale**: Hook 3 required a Builder fix loop (CQR conf 88) specifically because this constraint was not documented. Future workflow-guard hooks will face the same ambiguity. The rule prevents a false-block pattern that is both non-obvious and high-friction (it breaks valid two-step edits).

**Status**: APPROVED

---

## Proposal 3

**Target file**: `CLAUDE.md`

**Change**: In the "PreToolUse hooks for known-bad patterns" section, add a bullet covering blocking-rule dedup bypass:

```
**Blocking rules must bypass session dedup — advisory dedup is a security hole for hard-stop rules**:
deduplication (suppressing repeated fires for the same file+rule) is correct for advisory rules
to avoid noise, but incorrect for blocking rules — dedup allows a second violation after the first
block is acknowledged. Maintain a `BLOCKING_RULE_NAMES` constant; blocking rules always fire
regardless of dedup state.
```

**Rationale**: CQR Finding 3 (conf 82) identified this gap in task-049. The dedup mechanism is correct for advisory warnings and silently wrong for blocking rules. Without an explicit policy note, future hook authors will copy the dedup pattern from advisory hooks and apply it to blocking hooks, creating a security regression.

**Status**: APPROVED
