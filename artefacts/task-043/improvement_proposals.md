# Improvement Proposals — task-043

**Task**: Claude Code skills investigation — cross-project fit (BL-100)
**Agent**: SelfImprover [Haiku]
**Date**: 2026-04-19

---

## Proposal 1

**Target file**: `CLAUDE.md`
**Change**: Add a step to the PM project onboarding procedure (Workflow Orchestration section) requiring `claude-automation-recommender` to be run at the start of any new project session or onboarding. Specifically, add to the PM Planning Session paragraph:

```
**Project onboarding automation scan**: when onboarding a new project or beginning a session
on a project for the first time, invoke `claude-automation-recommender` (zero-install, read-only)
to surface top hooks, MCP servers, skills, and subagent recommendations for the detected tech
stack. Run before installing any hook or MCP server — its non-mutating design makes it safe at
any time with no side effects.
```

**Rationale**: `claude-automation-recommender` is uniquely positioned as the first step before any automation install because it is zero-install and non-mutating. Running it at onboarding time ensures each project gets a tailored automation roadmap without risk. This pattern was validated across all 7 managed projects in task-043 — all rated HIGH or MEDIUM fit. Without this rule in CLAUDE.md, the tool will be overlooked during onboarding (as it was for all existing projects).

**Status**: REQUIRES_HUMAN_APPROVAL

---

## Proposal 2

**Target file**: `CLAUDE.md`
**Change**: Add a note to the Security principles section (Governance, Security & Observability) recommending PreToolUse hooks for known high-severity pattern classes:

```
**PreToolUse hooks for known-bad patterns**: for security patterns with no legitimate use
in the codebase (e.g. eval, os.system, innerHTML, pickle), prefer a PreToolUse blocking
hook over a review-phase finding. Blocking at edit time prevents the pattern from ever
entering the codebase; review-phase tools catch it after the fact. Use `security-guidance`
(BL-101) as the reference implementation.
```

**Rationale**: task-043 deep-dive on `security-guidance` revealed that its exit-code-2 blocking mechanism is categorically stronger than post-write review. The existing security principles section focuses on code-level patterns but does not guide when to enforce via PreToolUse vs review. This distinction prevents future security tooling decisions from defaulting to review-only approaches when a blocking hook is available and appropriate.

**Status**: REQUIRES_HUMAN_APPROVAL
