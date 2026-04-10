# Improvement Proposals — BL-044 (Work CLAUDE.md analysis)

Source: `origin/feature_claudemd_work_pm:CLAUDE_file_work_pm.md`
Analyst: ProjectManager [Sonnet]
Date: 2026-04-10

---

## Proposal 1

**Target file:** `CLAUDE.md` — Model Policy table

**Change:**
Add Haiku as a third model tier for lightweight agents. Currently we use Sonnet for all agents except Opus for PM/Architect. Work setup uses Haiku for DocUpdater and SelfImprover, cutting token cost significantly for agents that don't need reasoning over complex context.

```diff
- | DocUpdater | YAML | Sonnet | Docs/changelog | Updated docs |
- | SelfImprover | YAML | Sonnet | Lessons/proposals | proposals.md written |
- | revise-claude-md | built-in | Sonnet | CLAUDE.md session learnings | CLAUDE.md updated |
+ | DocUpdater | YAML | Haiku | Docs/changelog | Updated docs |
+ | SelfImprover | YAML | Haiku | Lessons/proposals | proposals.md written |
+ | revise-claude-md | built-in | Haiku | CLAUDE.md session learnings | CLAUDE.md updated |
```

Also add to the policy guidance: "Default to Haiku for any agent that does not require reasoning over complex context."

**Rationale:** DocUpdater and SelfImprover do structured, templated work (append a row, write a diff description) — no complex reasoning required. Using Haiku cuts per-run cost and token spend for these high-frequency agents without quality loss.

**Status:** APPROVED

---

## Proposal 2

**Target file:** `CLAUDE.md` — Task Tracking section + queue.json conventions

**Change:**
Add two conventions for `assigned_to` field in queue.json:

1. `assigned_to` should be updated at every pipeline stage transition, not just at task creation. It tracks the *current* owner: `builder` → `reviewer+code-quality-reviewer` → `tester` → `doc-updater+docs-readme-writer` → `self-improver`.
2. Parallel stages use combined syntax: `"reviewer+code-quality-reviewer"` and `"doc-updater+docs-readme-writer"`.

Add to the Task Tracking section:
> `assigned_to` tracks the current pipeline stage owner — update it at each stage transition alongside `status`. For parallel stages set `assigned_to` to both agents: `"reviewer+code-quality-reviewer"` or `"doc-updater+docs-readme-writer"`.

**Rationale:** Currently `assigned_to` is set at task creation and never updated, making the queue a poor real-time signal of pipeline progress. This is a zero-cost observability improvement.

**Status:** APPROVED

---

## Proposal 3

**Target file:** `CLAUDE.md` — Workflow Orchestration section

**Change:**
Add a queue.json stale-read fix note:

> **queue.json stale-read fix**: if the Edit tool fails with "file modified since read", use `python3 -c "import json; q=json.load(open('tasks/queue.json')); ...; json.dump(q,open('tasks/queue.json','w'),indent=2)"` to atomically update it.

**Rationale:** We've hit this in practice when multiple edits happen in a session. The work setup documents this pattern explicitly; we should too so agents don't retry blindly or corrupt the file.

**Status:** APPROVED

---

## Proposal 4

**Target file:** `CLAUDE.md` — Agent Roles section

**Change:**
Add a prompt writing discipline rule:

> **Prompt writing discipline**: All agent prompts MUST use imperative voice addressed to the agent itself ("You will", "Do not", "Stop if"). Never narrate what other agents do — instead state this agent's responsibility relative to other agents' outputs. Orchestration sequencing belongs in design docs, not embedded in agent prompts.

**Rationale:** Our current agent YAMLs mix agent-directed instructions with narrator descriptions of what other agents do. This causes agents to wait for or repeat work that isn't theirs. A consistent imperative voice rule eliminates ambiguity.

**Status:** APPROVED

---

## Proposal 5

**Target file:** `CLAUDE.md` — Workflow Orchestration, always-on pipeline section

**Change:**
Add explicit file ownership for the parallel doc stage:

> **Doc stage file ownership**: when DocUpdater and docs-readme-writer run in parallel, assign ownership explicitly: DocUpdater → `CHANGELOG.md`; docs-readme-writer → `README.md`. This prevents overwrite conflicts when both agents target the same file.

**Rationale:** We've not had a conflict yet because our tasks haven't always produced both a README and CHANGELOG update in parallel, but the risk is real and the fix is free.

**Status:** APPROVED

---

## Proposal 6

**Target file:** `CLAUDE.md` — Governance, Security & Observability section

**Change:**
Add an 80% token cap preflight alert:

> **80% cap alert (preflight)**: before starting a task, sum all agent token estimates for that task. If total > 400,000 (80% of 500k cap), halt and present: `ALERT: Task <id> estimated tokens (<n>) exceed 80% of project cap. Reduce scope or split task before proceeding.`

**Rationale:** Our current policy documents a 500k hard cap but has no warning threshold. By the time the cap is hit, significant work may be lost. An 80% warning gives a recovery window.

**Status:** APPROVED

---

## Proposal 7

**Target file:** `CLAUDE.md` — Self-Improvement Loop section

**Change:**
Add the `pm-propose` grep pattern to avoid false positives from test files:

> **Scanning for pending proposals**: use `find artefacts -name "improvement_proposals.md" | xargs grep -l "REQUIRES_HUMAN_APPROVAL"` — do NOT use `grep -rl` on the whole artefacts dir as it produces false positives from Tester test files that assert on the string.

**Rationale:** As the test suite grows, test files that assert on proposal format will match a naive `grep -r` and surface false pending proposals at session end. The `find | xargs grep -l` pattern scopes the search to the right filenames only.

**Status:** APPROVED

---

## Proposal 8

**Target file:** `CLAUDE.md` — Agent Roles section (after Built-in agents block)

**Change:**
Add a cross-file mirroring maintenance note (M-1 pattern):

> **Cross-file rule mirroring (M-1 pattern)**: Enumerated rules that appear in both CLAUDE.md and agent YAMLs can silently accumulate orphan entries. When editing either file, verify rule counts and text match in both directions. Tester must include a regression guard for any task that modifies mirrored content: (a) rule-count equality check across all copies, (b) absence check for any rule that was removed.

**Rationale:** We already have a cross-file consistency check in the end-of-session proposal review, but it's not formalized as a Tester responsibility. Making it explicit prevents silent drift.

**Status:** APPROVED

---

## Proposal 9

**Target file:** `CLAUDE.md` — Workflow Orchestration, session-start checklist

**Change:**
Add ExitPlanMode denial handling as a session-start rule:

> **ExitPlanMode denial**: if the user denies ExitPlanMode, use AskUserQuestion to clarify intent before re-attempting — the user may be redirecting to a side task first, not rejecting the plan outright.

**Rationale:** Currently there's no documented behavior for this case. Without guidance, the PM might re-enter plan mode immediately with the same plan, frustrating the user.

**Status:** APPROVED

---

## Proposal 10

**Target file:** `tasks/backlog.md` — expand BL-040 scope; `CLAUDE.md` — add skill authoring rules

**Change:**
The work PM defines a complete set of skills that codify mandatory session workflows into single callable commands. We have BL-040 ("Enhance via Claude Code skills e.g. /pm-start") but it's vague. This proposal expands it with a concrete skill list and adds skill authoring rules to CLAUDE.md.

Skills to implement (`.claude/commands/*.md`):

| Skill | Purpose |
|-------|---------|
| `/pm-start` | Session startup: fetch, inbox, lessons, queue review, phase gate, summary — await confirmation |
| `/pm-status` | Kanban + phase status + token summary |
| `/pm-propose` | End-of-session proposal review: scan, deduplicate, present, apply approved |
| `/pm-close` | Sprint close: clean tree → proposals → revise-claude-md → merge → push → branch cleanup → phase gate |
| `/pm-lessons` | Print last 10 rows of tasks/lessons.md |
| `/pm-run` | Execute next pending queue task through full pipeline |

Add to CLAUDE.md:

> **Skill authoring rules**: Skills are executable command prompts (`.claude/commands/*.md`).
> - Every angle-bracket placeholder must include an explicit resolution instruction naming the source file and lookup pattern. Do not assume the reader will infer where data lives.
> - Test all placeholders manually before committing: simulate a fresh session with no prior context.
> - **Security filter ordering: inline, not post-hoc** — inspect for sensitive patterns per-item before appending to any buffer; a post-hoc filter is logically bypassed when the buffer already contains sensitive data.

**Rationale:** Without skills, every session start relies on the PM remembering and manually executing a multi-step checklist in order — we've already seen it fail (BL-043). Skills make the workflow one command, auditable, and consistent. BL-040 is already in the backlog; this proposal gives it a concrete spec so it can be queued immediately. The authoring rules prevent the class of placeholder-resolution bugs the work setup documents explicitly.

**Status:** APPROVED
