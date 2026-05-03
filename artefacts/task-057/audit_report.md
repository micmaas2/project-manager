# Audit Report: task-057
## PM System Audit — CLAUDE.md, Agent YAMLs, Skills Quality Review (BL-078)

**Date**: 2026-05-03
**Agent**: Builder [Sonnet]
**Scope**: CLAUDE.md, `.claude/agents/*.yaml` (6 files), `.claude/commands/*.md` (7 files)

---

## Summary Table

| Severity | Count | Notes |
|---|---|---|
| Critical | 2 | Policy violation + broken invocation pattern |
| Major | 7 | M-1 mirror gaps, missing checklist items, require_human_approval violations |
| Minor | 5 | Stale references, prompt writing discipline gaps |

**Total findings**: 14
**NEW: findings to register as BL items**: 9 (all Critical + Major)

---

## Dimension A — Agent YAML Policy Compliance

---

### Finding 1 — CRITICAL
**NEW:** `reviewer.yaml` — `require_human_approval` is `false` despite Write + Bash in `allowed_tools`

**File**: `.claude/agents/reviewer.yaml`

**Description**: CLAUDE.md policy states `require_human_approval: TRUE if Bash/Write/Edit in tools`. reviewer.yaml has both `Write` (writes review.md) and `Bash` (runs shellcheck, yamllint, py_compile) in `allowed_tools`, but `require_human_approval: false`. This is a direct violation of the policy schema enforced by the pre-commit hook.

**Evidence**:
```yaml
allowed_tools:
  - Read
  - Write
  - Bash   # restricted to: bash -n, shellcheck, yamllint ...
require_human_approval: false  # ← should be true
```

**Fix recommendation**: Set `require_human_approval: true` in `reviewer.yaml`. Add a comment explaining Bash is restricted to static analysis commands only (the same comment pattern as `tester.yaml`).

---

### Finding 2 — CRITICAL
**NEW:** `manager.yaml` — invokes `revise-claude-md` via `subagent_type` which CLAUDE.md explicitly states does not work

**File**: `.claude/agents/manager.yaml` (line 68)

**Description**: manager.yaml step 11 instructs: `invoke revise-claude-md (built-in Agent tool, subagent_type=claude-md-management:revise-claude-md)`. CLAUDE.md explicitly states: "`subagent_type` does not work for `claude-md-management:*`" and "`invoke via Skill tool, NOT Agent tool`". This means `revise-claude-md` silently fails or errors when manager.yaml's step 11 is followed. The correct invocation is `Skill` tool.

**Fix recommendation**: Replace the `Agent tool, subagent_type=claude-md-management:revise-claude-md` instruction with `Skill tool (skill: claude-md-management:revise-claude-md)` in manager.yaml step 11.

---

### Finding 3 — MAJOR
**NEW:** `builder.yaml` — M-1 confidence definition missing verbatim text; only behavior rules present, not the definition

**File**: `.claude/agents/builder.yaml`

**Description**: CLAUDE.md states: "M-1 mirror: this definition must match reviewer.yaml and builder.yaml verbatim." The required definition is: `confidence = certainty the finding is a real issue (not a false positive)`. reviewer.yaml correctly includes "Represents certainty that the finding is a real issue (not a false positive)". builder.yaml contains only the behavioral rules (≥80 loop / <80 log) but omits the definition sentence entirely.

**Evidence**:
- CLAUDE.md: `Definition: confidence = certainty the finding is a real issue (not a false positive).`
- reviewer.yaml: `confidence: 1-100. Represents certainty that the finding is a real issue (not a false positive).` ✓
- builder.yaml: No definition sentence found. ✗

**Fix recommendation**: Add the definition sentence to builder.yaml's `## Reviewer Confidence Threshold` section, verbatim: `Definition: confidence = certainty the finding is a real issue (not a false positive).`

---

### Finding 4 — MAJOR
**NEW:** `doc-updater.yaml` — `require_human_approval: false` despite Write + Edit in `allowed_tools`

**File**: `.claude/agents/doc-updater.yaml`

**Description**: CLAUDE.md policy: `require_human_approval: TRUE if Bash/Write/Edit in tools`. doc-updater has Write and Edit in allowed_tools but `require_human_approval: false`. This violates the stated policy schema — the pre-commit hook enforcing this would reject a future edit that adds a field but not the flag correction.

**Fix recommendation**: Set `require_human_approval: true` in `doc-updater.yaml`.

---

### Finding 5 — MAJOR
**NEW:** `manager.yaml` — prompt instructs Bash commands (git, python3 scripts) but Bash is absent from `allowed_tools`

**File**: `.claude/agents/manager.yaml`

**Description**: manager.yaml's prompt instructs the agent to run shell commands:
- Step 3: `git -C <project> branch -a`
- Step 4: `command -v <tool> >/dev/null 2>&1`
- Step 5: `python3 scripts/token_cap_enforcer.py --task-id <task_id>`

None of these are executable without the `Bash` tool, which is absent from `allowed_tools`. This means the agent will either fail or use workarounds. If Bash is intentionally excluded (PM should delegate to Builder), then the prompt must be updated to instruct PM to delegate these steps.

**Fix recommendation**: Either (a) add `Bash` to `manager.yaml`'s `allowed_tools` and set `require_human_approval: true`, or (b) replace the prompt's direct Bash invocations with delegation instructions to Builder (which already has Bash). Preferred: option (b), since CLAUDE.md states "NEVER write code or scripts — delegate to Builder".

---

### Finding 6 — MINOR
`self-improver.yaml` — `require_human_approval: true` even though no Bash present; policy only requires `true` when Bash/Write/Edit present

**File**: `.claude/agents/self-improver.yaml`

**Description**: CLAUDE.md policy states `require_human_approval: TRUE if Bash/Write/Edit in tools`. self-improver has Write and Edit in allowed_tools, so `require_human_approval: true` is actually correct. This is NOT a violation — the current setting is correct. Finding retained as a documentation confirmation: the `true` setting is deliberate and correct because Write/Edit are present.

**Verdict**: PASS — no action needed.

---

### Finding 7 — MINOR
Agent Roles table in CLAUDE.md lists `Architect` and `Security` as YAML agents, but no YAMLs exist

**File**: `CLAUDE.md` (line 117–118)

**Description**: The Agent Roles table lists `Architect | YAML | Opus` and `Security | YAML | Sonnet` but neither `.claude/agents/architect.yaml` nor `.claude/agents/security.yaml` exists. These are referenced as intended future agents or are implicitly handled by ProjectManager/Builder. The table creates a misleading picture of the current agent inventory.

**Fix recommendation**: Either create stub YAMLs for Architect and Security, or update the table notes to indicate these roles are "not yet implemented" or "handled by ProjectManager/Builder". Minor because these agents are only invoked optionally (Opus advisor escalation pattern).

---

## Dimension B — Skills Quality

---

### Finding 8 — CRITICAL → downgraded to MAJOR
**NEW:** `pm-close.md` — missing execution-mode preamble

**File**: `.claude/commands/pm-close.md`

**Description**: CLAUDE.md Skill authoring rules: "Apply [execution-mode preamble] to pm-run, pm-close, pm-propose, and any future execution-only skill." pm-run.md ✓ and pm-propose.md ✓ both have the required preamble. pm-close.md does NOT contain `**Execution mode**: do not enter plan mode.` This means pm-close can spontaneously enter plan mode during a sprint close, interrupting the merge/push sequence at a dangerous point.

**Evidence**: `head -5 pm-close.md` shows only the title header and "Run at end of every sprint..." with no execution mode directive.

**Fix recommendation**: Add the standard execution mode preamble as the second line of pm-close.md:
```
**Execution mode**: do not enter plan mode. This skill executes already-planned work. Proceed directly to the Steps below without calling EnterPlanMode.
```

---

### Finding 9 — MAJOR
**NEW:** `pm-start.md` — missing 2 of 6 CLAUDE.md mandatory session checklist items: ExitPlanMode denial and ExitPlanMode mid-skill recovery

**File**: `.claude/commands/pm-start.md`

**Description**: CLAUDE.md defines 6 mandatory session checklist items under "Session start — mandatory checklist". pm-start.md implements only 4 of them. Missing from pm-start:
1. **ExitPlanMode denial** — "if the user denies ExitPlanMode, use AskUserQuestion to clarify intent before re-attempting"
2. **ExitPlanMode mid-skill recovery** — "if plan mode activates unexpectedly during a PM skill run, write a minimal plan file..."

Additionally, pm-start step 4 (Queue review) only *lists* tasks missing improvement_proposals.md but does NOT run SelfImprover for them. CLAUDE.md item 4 says "run SelfImprover for that task". The skill leaves a catch-up action to user initiative.

**Fix recommendation**: Add ExitPlanMode denial and mid-skill recovery instructions to pm-start.md (can be in a "Recovery procedures" section at the end). Update step 4 to explicitly instruct running SelfImprover for each missing improvement_proposals.md found, not just reporting.

---

### Finding 10 — MAJOR
**NEW:** `pm-start.md` — step 2 Telegram inbox promotion uses `—` (no epic) but CLAUDE.md step 0 hardcodes `EPIC-003` as the default epic, which is now stale

**File**: `CLAUDE.md` (Workflow Orchestration step 0) and `.claude/commands/pm-start.md`

**Description**: CLAUDE.md session checklist item 2 says: "Promote each item below the header to `tasks/backlog.md` (next BL ID, **EPIC-003**, project_manager, P2, new, today)". However, EPIC-003 is an old in_progress multi-project coordination epic. The current active epic is EPIC-008. pm-start.md correctly uses `—` (no epic; assigned during /pm-plan), but CLAUDE.md still hardcodes `EPIC-003`. This creates a documentation inconsistency that can mislead agents following CLAUDE.md over pm-start.md.

**Fix recommendation**: Update CLAUDE.md session checklist item 2 to replace `EPIC-003` with `—` (no epic; assigned during /pm-plan) to match pm-start.md's correct behavior.

---

### Finding 11 — MINOR
`pm-plan.md` — angle-bracket placeholders in the JSON template are template variables (intentional), not resolution-instruction gaps

**File**: `.claude/commands/pm-plan.md`

**Description**: pm-plan.md contains numerous `<placeholder>` items in the queue.json template section (e.g., `"id": "<task-NNN>"`, `"title": "<title from BL item>"`). Upon inspection, all placeholders in the JSON template body ARE accompanied by resolution instructions in the Step 4 table above them (source file, lookup pattern). The placeholders in the JSON template are fill-in-the-blank markers, not free-form placeholders.

**Verdict**: PASS — all placeholders have resolution instructions. No action needed.

---

### Finding 12 — MINOR
`pm-start.md` — no security filter ordering (inspect-per-item) in Telegram inbox promotion step

**File**: `.claude/commands/pm-start.md`

**Description**: CLAUDE.md skill authoring rule: "Security filter ordering: inline, not post-hoc — inspect for sensitive patterns (password, secret, api_key, etc.) per-item before appending to any buffer." pm-start step 2 promotes Telegram inbox items to backlog.md without any mention of filtering sensitive content before append. In practice, the Telegram inbox items are user-controlled and could contain credential-like text. However, since pm-start only reads plaintext and appends to a markdown table (not executing code or writing to configs), the risk is lower than in build contexts.

**Fix recommendation**: Add a one-line note to pm-start step 2: "Before appending each item, scan for credential patterns (token, password, api_key, secret); reject items containing such patterns with a warning."

---

## Dimension C — CLAUDE.md Quality

---

### Finding 13 — MAJOR
**NEW:** CLAUDE.md "Reviewer confidence scoring" M-1 mirror incomplete: builder.yaml lacks the verbatim definition sentence

**File**: `CLAUDE.md` (line 128) and `.claude/agents/builder.yaml`

**Description**: (Cross-reference with Finding 3.) CLAUDE.md explicitly calls out "M-1 mirror: this definition must match reviewer.yaml and builder.yaml verbatim." The definition sentence is present in reviewer.yaml but absent from builder.yaml. This is a CLAUDE.md quality issue in addition to being an agent YAML issue.

**Fix recommendation**: Same as Finding 3 — add the verbatim definition to builder.yaml. No CLAUDE.md change required (the rule is correct; it is the YAML that is missing the text).

---

### Finding 14 — MINOR
CLAUDE.md stale task references are contextually appropriate (not stale by content)

**File**: `CLAUDE.md`

**Description**: CLAUDE.md references: `task-008` (artefact path suffix example), `task-029` (pensieve branch example), `task-040` (model audit cadence example), `task-047` (extension-guide.md location), `task-049` (workflow guard hook). All five references:
- task-008 through task-049: artefact directories confirmed present in `artefacts/`
- task-047: `artefacts/task-047/extension-guide.md` confirmed present
- task-029: pensieve branch `feature/task-029-capture-subworkflow` still active

None of these are stale in the sense that the referenced artefacts are missing. They serve as concrete examples, not operational pointers that would break if old.

**Verdict**: PASS — references are contextually stable. No action needed.

---

### Finding 15 — MINOR
`doc-updater.yaml` and `self-improver.yaml` prompts violate CLAUDE.md "Prompt writing discipline" rule (imperative voice addressed to agent)

**File**: `.claude/agents/doc-updater.yaml`, `.claude/agents/self-improver.yaml`

**Description**: CLAUDE.md states: "All agent prompts MUST use imperative voice addressed to the agent itself ('You will', 'Do not', 'Stop if'). Never narrate what other agents do."

- doc-updater.yaml opens with: "Update project documentation after a Tester PASS." — third-person directive, not imperative voice addressed to the agent.
- self-improver.yaml opens with: "Extract learnings from a completed pipeline run. Run after every Tester PASS." — same issue.

builder.yaml, reviewer.yaml, manager.yaml, and tester.yaml all start with "You are the X agent..." — correct.

**Fix recommendation**: Rewrite doc-updater.yaml and self-improver.yaml opening lines to begin with "You are the X agent." followed by imperative voice instructions. Example: `You are the DocUpdater agent. You update project documentation after a Tester PASS.`

---

## NEW: BL Items to Register

Based on Critical and Major findings, the following BL items require registration in `tasks/backlog.md`. Next BL number after BL-121 = **BL-122**.

| BL ID | Finding | Priority | Title |
|---|---|---|---|
| BL-122 | Finding 2 (Critical) | P1 | project_manager: Fix manager.yaml — revise-claude-md invocation uses wrong tool (subagent_type); must use Skill tool |
| BL-123 | Finding 1 (Critical) | P1 | project_manager: Fix reviewer.yaml — require_human_approval must be true (has Write+Bash in allowed_tools) |
| BL-124 | Finding 3+13 (Major) | P2 | project_manager: Fix builder.yaml M-1 mirror gap — add verbatim confidence definition sentence |
| BL-125 | Finding 4 (Major) | P2 | project_manager: Fix doc-updater.yaml — require_human_approval must be true (has Write+Edit) |
| BL-126 | Finding 5 (Major) | P2 | project_manager: Fix manager.yaml — Bash commands in prompt but Bash absent from allowed_tools; delegate or add tool |
| BL-127 | Finding 8 (Major) | P2 | project_manager: Add execution-mode preamble to pm-close.md |
| BL-128 | Finding 9 (Major) | P2 | project_manager: pm-start.md missing 2 session checklist items: ExitPlanMode denial + recovery; catch-up SelfImprover should run not just list |
| BL-129 | Finding 10 (Major) | P2 | project_manager: Fix CLAUDE.md stale EPIC-003 reference in session checklist inbox item — replace with dash (no epic) |

---

## Definition of Done Verification

- [x] All 6 agent YAMLs audited for policy field compliance
- [x] All 7 skills audited for execution mode preamble, placeholder resolution, security filter ordering
- [x] CLAUDE.md audited for stale task references, M-1 consistency, and checklist completeness
- [x] audit_report.md produced with findings categorized Critical/Major/Minor + fix recommendation per finding
- [ ] NEW: findings registered as BL items in tasks/backlog.md (next step)
