# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

This is the workspace for the multi-agent automation system. Structure: `.claude/agents/` (agent YAMLs), `tasks/` (queue + schema), `hooks/` (git hooks), `artefacts/` (agent outputs), `logs/` (audit + token logs).

---

## Workspace Context

This directory (`project_manager`) is part of the `/opt/claude/` multi-project workspace.
Full project registry: `docs/project-registry.md` (authoritative — update there first when adding or onboarding a project during a PM planning session).

| Directory | GitHub | Purpose |
|---|---|---|
| `/opt/claude/project_manager` | micmaas2/project-manager | This MAS orchestration system |
| `/opt/claude/CCAS/` | (no root git — 6 subrepos below) | SAP infrastructure automation (Ansible-based) |
| `/opt/claude/pi-homelab/` | micmaas2/pi-homelab | Raspberry Pi / Home Assistant deployment |
| `/opt/claude/pensieve/` | micmaas2/pensieve | TBD |
| `/opt/claude/genealogie/` | micmaas2/genealogie | Genealogy tooling |
| `/opt/claude/performance_HPT/` | micmaas2/performance-twin | Performance / HPT tooling |
| `/opt/claude/project1/` | (no remote) | Generic project skeleton |
| Pi4: `/opt/mas/` | micmaas2/mas_personal_assistant (private) | Personal assistant — Telegram bot, FastAPI, PostgreSQL, React (mas.femic.nl) |

**Existing projects may already have plans, requirements, and in-progress work.**
When a project is added or first onboarded, PM runs a discovery scan (see `manager.yaml`) and
registers all existing artifacts in `docs/project-registry.md` before scheduling any tasks.

**No build system, tests, or source code** currently exist in this directory. When code is added, update this file with relevant commands.

---

## Project Goal

Build an incremental hierarchical multi-agent system to generate automations and scripts, accelerate delivery, and replace manual work. Start with MVP1: analyze one workflow and deliver one working automation.

---

## Git Branching Strategy

```
main (production)     ← Stable, tested, approved releases only
  ↑
develop (integration) ← Active development; all features merge here
  ↑
feature/* (work)      ← New features, bug fixes, planned work
```

**Branch naming**: `feature/description`, `bugfix/description`, `phase-X/week-Y-task`

**Workflow**:
1. Create feature branch from `develop`; NEVER commit directly to `develop` or `main`
2. Merge to `develop` when complete and tested
3. `main` updated ONLY after testing in `develop` + user acceptance:
   ```bash
   git checkout main && git merge develop -m "Release: description"
   git tag -a v1.x.x -m "Release version 1.x.x" && git push origin main --tags
   ```

**Git remote**: SSH-based (`git@github.com:micmaas2/project-manager.git`). Run `git remote -v` before adding — it already exists. HTTPS will fail.

**Releasing to main**: `git push origin develop:main` — pre-commit hook blocks direct commits on main/develop, so local merge always fails. Use refspec push only.
If main has GitHub API commits that develop lacks (diverged), use `--force-with-lease` after syncing via a feature branch: `git checkout -b feature/sync && git checkout origin/main -- <file> && git commit ... && merge into develop`, then `git push origin develop:main --force-with-lease`.

**Merging feature branches with conflicts into develop**: conflict-free `git merge --no-ff -m "..."` on develop works. When a merge has conflicts, `git commit` after resolution is blocked — abort on develop, resolve on a `feature/sync-X` branch, then `git push origin feature/sync-X:develop` and pull. Avoid `git stash` when branches have diverged — cascading conflicts.

**Git hooks** (in `hooks/`, symlinked to `.git/hooks/`):
- `pre-commit` — branch protection (blocks main/develop) + sensitive file detection
- `commit-msg` — enforces `[AREA]` message format; receives commit file as `$1`

NEVER put message-format validation in `pre-commit` — it does not receive `$1` reliably.

**Pre-Commit Hooks**: ALWAYS active — NEVER use `git commit --no-verify`

**Documentation**: Always update `CLAUDE.md`, `README.md`, `CHANGELOG.md` with changes (enforced by hooks).

**Commit format**:
```
[AREA] Brief description

- Detailed change 1
- Detailed change 2
```
Areas: `ROLE`, `DOCS`, `TEST`, `FIX`, `REFACTOR`, `PLAYBOOK`, `JENKINS`, `INVENTORY`, `AGENT`

---

## Model Policy (Token Governance)

- **Sonnet 4.6** — default for execution, building, reviewing (80–90% of work)
- **Opus 4.6** — only for ProjectManager (plan/scope), Architect (design), Security (risk analysis)
- **Haiku 4.5** — DocUpdater, SelfImprover, revise-claude-md, Tester (BugHunter), and any agent doing templated/structured work with no complex reasoning required
  - Haiku uses a date-pinned ID (`claude-haiku-4-5-20251001`) because multiple Haiku 4.5 patch builds existed at release. Opus 4.6 and Sonnet 4.6 have single authoritative builds — no date suffix needed. Add a date suffix to any model field only when multiple patch builds for that version co-exist; update all affected YAMLs together.
- **Pattern**: Opus plans, Sonnet executes, Haiku documents and tests
- **Default to Haiku** for any agent that does not require reasoning over complex context
- **Complexity thresholds for model selection**:
  - Haiku: mechanical/orchestration tasks; structured input/output; prompt ≤500 tokens; no trade-off analysis
  - Sonnet: code generation; architectural judgment; confidence scoring; prompt 500–2,000 tokens
  - Opus: system-wide prioritization with competing constraints; prompt >2,000 tokens; decisions affecting multiple downstream agents
- **Prompt caching**: Anthropic automatically caches system prompts ≥1,024 tokens (90% discount on cached input tokens only; output tokens billed at standard rate). ProjectManager qualifies (~1,377 tokens). No code changes required — verify API tier supports caching before first production run.
- **Label** all outputs and tool calls with `[Sonnet]`, `[Opus]`, or `[Haiku]`
- **Label update on model change**: when a YAML agent's model field is changed, update the `Label all outputs` line in that agent's YAML in the same commit — a stale label (e.g. `[Sonnet]` after downgrade to Haiku) silently breaks audit integrity
- **Model audit cadence**: Run task-040-style audits whenever a new model version is released or after 10+ tasks are added. Audit methodology: (1) list all YAML agents + built-ins separately; (2) compare against current policy table; (3) use actual `logs/token_log.jsonl` data for cost projections — never assumed token counts.
- **Token limits**: max 10,000 tokens per agent run; project cap 500k tokens/run (fail threshold)
- **Artefact stop**: agents stop after delivering a plan, script, test report, or review — continuation requires explicit approval
- **Preflight**: every task requires a token estimate before execution

---

## Agent Roles & Spawn Order

Spawn sequence: Manager → Architect/Security → Builder → [Reviewer + code-quality-reviewer] → Tester → [DocUpdater + docs-readme-writer] → SelfImprover

| Agent | Type | Model | Focus | Stop At |
|-------|------|-------|-------|---------|
| ProjectManager | YAML | Opus | Scope/MVP/coordination | Approved MVP plan |
| Architect | YAML | Opus | Modular design | Arch diagram |
| Security | YAML | Sonnet | Secrets/auth/validation | Security OK |
| Builder (ScriptBuilder / TaskAutomator / DeliveryOptimizer) | YAML | Sonnet | Code/impl | Script/patch |
| Reviewer | YAML | Sonnet | Quality/arch-compliance | Approved review |
| code-quality-reviewer | built-in | Sonnet | Security, quality, best-practices | Review report |
| Tester (BugHunter) | YAML | Haiku | Tests/regression | 90% pass |
| DocUpdater | YAML | Haiku | Docs/changelog | Updated docs |
| docs-readme-writer | built-in | Haiku | README/module docs | Docs written |
| SelfImprover | YAML | Haiku | Lessons/proposals | proposals.md written |
| revise-claude-md | built-in | Haiku | CLAUDE.md session learnings | CLAUDE.md updated |

**Reviewer confidence scoring**: each finding in review.md includes `confidence: N (1-100)` — Builder loops only on findings >= 80; findings < 80 are routed to build_notes.md only (no loop required). Definition: confidence = certainty the finding is a real issue (not a false positive). M-1 mirror: this definition must match reviewer.yaml and builder.yaml verbatim.

**Built-in Claude Code agents** (invoke via `Agent` tool with `subagent_type`):
- `code-quality-reviewer` — security + quality review; runs parallel to Reviewer; for any regex using `re.DOTALL`, flag use of `$` as a stop anchor (use `\Z` instead) and require a multi-line fixture in Tester; for any documentation that recommends one format as "preferred" (e.g. fine-grained PAT over classic), verify ALL code snippets use that preferred format first — if both forms are valid, add a comment noting both formats; when recommending git hardening patterns (e.g. adding `--` to git commands), verify against git documentation that the syntax is correct for the specific invocation context — index refspecs (`:filename`) and positional file arguments have different disambiguation rules
- `docs-readme-writer` — README/module docs; runs parallel to DocUpdater
- `claude-md-management:revise-claude-md` — apply session learnings to CLAUDE.md (session end); invoke via `Skill` tool, NOT `Agent` tool (`subagent_type` does not work for `claude-md-management:*`)
- `claude-md-management:claude-md-improver` — full CLAUDE.md audit (on demand); invoke via `Skill` tool
- **Explore-type subagents cannot write files**: when DocUpdater/docs-readme-writer are spawned as `subagent_type: Explore`, they return proposed content but cannot apply edits. The parent agent must read the agent's output and apply the file changes directly — do not wait for the Explore agent to write.

**Grep tool vs Bash grep**: use the `Grep` tool (not `grep` via Bash) when the search pattern contains backticks or special shell characters — Bash eval will fail with `unexpected EOF while looking for matching backtick`.

**`xargs grep` exits 123 when find returns no files** — `find ... | xargs grep -lE "..."` returns exit code 123 (not 1) when find produces no results; append `|| true` (or `2>/dev/null` for stderr only) to prevent Bash tool error output. Code 123 means no input reached grep, not a failed match.

**Multi-file text replacement**: `sed -i '...' "$f"` inside bash for-loops fails in the Bash tool (sed reports `$f: No such file or directory`). Use `python3 -c "p='path'; t=open(p).read(); open(p,'w').write(t.replace('old','new'))"` inline instead — reliable across all shell contexts.

**Append-only table schema additions**: when a task adds columns to an append-only markdown table (lessons.md, backlog.md, etc.), Builder must queue a backfill backlog item at build time — existing rows become structurally mismatched and break table rendering. Do not leave the backfill for SelfImprover to propose.

**Shell script pre-submission check** (Builder must verify before handing off to Reviewer): See `docs/shell-presubmit.md` for the full checklist (syntax check, cron/daemon guards, path containment, secret env vars, exit order, pipefail patterns, staged index reading, YAML custom tags, credential regex, dynamic test counts, SystemExit handling).

**Review doc redaction rule**: when a Reviewer documents the "original vulnerable code" in a finding, replace the actual credential value with `<REDACTED>` — never quote a live token, password, or key verbatim, even inside a code block. The vulnerable pattern can be reconstructed from git diff; an exposed live credential cannot be un-leaked.

**Prompt writing discipline**: All agent prompts MUST use imperative voice addressed to the agent itself ("You will", "Do not", "Stop if"). Never narrate what other agents do — instead state this agent's responsibility relative to other agents' outputs. Orchestration sequencing (waiting, parallelism) belongs in design docs, not embedded in agent prompts. When this rule is added or updated, apply it retroactively to ALL existing agent YAMLs in the same commit — search for prompts that open with a noun phrase or passive construction (e.g. `"Update project documentation after..."`, `"Extract learnings from..."`) and rewrite to imperative voice (`"You are the X agent. You update..."`).

**Opus advisor escalation**: For ambiguous arch/security decisions, spawn Opus sub-agent (model: claude-opus-4-6) with single `ADVISOR_CONSULT: <question>` + Context + Options. Note in `build_notes.md` under "Advisor Consults". Triggers: architecture tradeoff with no clear winner; security decision outside established patterns; scope ambiguity. Do NOT use for routine decisions.

**Cross-file rule mirroring (M-1 pattern)**: Enumerated rules that appear in both CLAUDE.md and agent YAMLs can silently accumulate orphan entries. When editing either file, verify rule counts and text match in both directions. Also verify that the `Label all outputs:` directive in each agent YAML matches the tiers listed in the CLAUDE.md Label bullet (Model Policy section) — this is a second M-1 mirror that model-pin checks do not cover. Tester must include a regression guard for any task that modifies mirrored content: (a) rule-count equality check across all copies, (b) absence check for any rule that was removed. **M-1 task scope rule**: every task that fixes or adds a mirrored rule must list ALL N target files in its acceptance criteria and verify all N copies in a single commit — a task that updates N-1 of N copies is incomplete and will be returned by Reviewer.

**Tool-invocation corrections must propagate to agent YAMLs in the same commit**: when CLAUDE.md is updated to correct a tool invocation pattern (e.g. "use Skill tool, not Agent tool for `claude-md-management:*`"), search all `.claude/agents/*.yaml` files for the old pattern and update the affected prompts in the same commit. A correction that lives only in CLAUDE.md leaves agent prompts generating broken instructions until the next audit cycle.

**M-1 copy-paste rule**: when mirroring a definition across CLAUDE.md and agent YAMLs, copy-paste verbatim — never paraphrase. Unicode vs ASCII symbol variants (`≥` vs `>=`) and synonym substitutions ("issue" vs "defect") both silently break the M-1 verbatim-match contract. This applies equally to skill checklist items (`.claude/commands/*.md`) that reproduce CLAUDE.md rules — open the exact source line and copy-paste; do not rephrase from memory.

**Agent YAML policy schema**: the pre-commit hook enforces that every `.claude/agents/*.yaml` contains all 5 required policy fields (`allowed_tools`, `max_tokens_per_run`, `require_human_approval`, `audit_logging`, `external_calls_allowed`). A commit that adds or modifies an agent YAML without all 5 fields will be rejected. Additionally, if `allowed_tools` contains `Write`, `Edit`, or `Bash`, `require_human_approval` must be `true` — a semantic value check blocks the commit if it is `false`.

**PM Skills** (`.claude/commands/`): `/pm-start` `/pm-run` `/pm-status` `/pm-plan` `/pm-propose` `/pm-close` `/pm-lessons` — and `skill-creator` (Marketplace, for new/revised PM skills).

**Plugin marketplace**: official Anthropic plugins at `/root/.claude/plugins/marketplaces/claude-plugins-official/plugins/` — browse with `ls` for available commands, agents, and skills; check `README.md` in each plugin dir.

**Skill authoring rules**: Skills are executable command prompts (`.claude/commands/*.md`).
- Every angle-bracket placeholder must include an explicit resolution instruction naming the source file and lookup pattern — do not assume the reader will infer where data lives.
- Test all placeholders manually before committing: simulate a fresh session with no prior context and verify every `<placeholder>` can be resolved without ambiguity.
- **Security filter ordering: inline, not post-hoc** — inspect for sensitive patterns (password, secret, api_key, etc.) per-item before appending to any buffer; a post-hoc filter is logically bypassed when the buffer already contains sensitive data.
- **Execution-only preamble**: skills with no scope ambiguity (task already fully specified, deterministic pipeline) must include: `**Execution mode**: do not enter plan mode. This skill executes already-planned work. Proceed directly to the Steps below without calling EnterPlanMode.` Apply to pm-run, pm-close, pm-propose, and any future execution-only skill.

Agent definitions live in `.claude/agents/[name].yaml`. Required fields: `name`, `prompt`, `policy`, `owner`, `incident_owner`.

**Policy schema per agent** (5 required fields): `allowed_tools`, `max_tokens_per_run`, `require_human_approval` (TRUE if Bash/Write/Edit in tools), `audit_logging`, `external_calls_allowed`.

---

## MVP Phases & Scope Discipline

1. **MVP1**: Setup + ScriptBuilder (script generation/test)
2. **MVP2**: Team — Automator + Reviewer
3. **MVP3**: Manager + DeliveryOptimizer
4. **MVP4**: Production (hooks, scheduling, monitoring)

**Human gate**: approve each MVP phase end before proceeding.

**MVP template** (required for every task):
```
Doel: <1 sentence>
Niet in scope: <short list>
Acceptatiecriteria: 1) ... 2) ... 3) ...
SLOs: latency < X ms; tests >= 90%
max_tokens_per_run: 8000
Security/arch impact: <note>
  See docs/mvp-template-checklist.md for the full Security/arch impact conditions.
No external deps: true/false  (if true: stdlib/built-ins only; no pip/npm installs)
Prerequisites: [tool >= version, ...]
Tests: unit/integration/regression
Rollback plan: <steps + owner>
Privacy DPIA: yes/no + note
Cost estimate: EUR ...
  - If cost estimate is based on caching: state lower bound (realistic hit rate) AND upper bound (100% hit rate); document cache TTL caveat (Anthropic: 5 min)
  - If cost estimate involves token counts: state assumed input/output split explicitly (e.g. 3,500 input / 1,500 output per run)
Definition of Done: <checklist>
  - If this task changes or adds an LLM model string: verify the model string appears in
    cost_tracker (or equivalent pricing table); add the pricing entry before closing the task.
  - [ ] No credentials or sensitive values are committed in artefact files. If a credential
    (password, token, key) is mentioned in build_notes.md or other docs, redact it to
    `<redacted — see ENV_VAR_NAME>` or `<set-via-env>`.
Incident owner: <Name / Role>
```

ProjectManager enforces all scope. Work outside MVP is rejected or backlogged.

---

## Governance, Security & Observability

**Runtime policy**: all agent actions pass a policy layer checking `allowed_tools`, `max_tokens_per_run`, `external_calls_allowed`, `require_human_approval`. Non-compliant actions are blocked and logged.

**Security principles**:
- Least privilege for tools and API scopes
- Secrets only via central vault; never in prompts or logs
- RBAC for agent spawn and policy changes
- Prompt sanitization; adversarial tests for prompt injection
- Runbook verification commands that read secret files: always pipe through `head -c N` or `grep -c`; add a warning note discouraging bare `cat` on recorded/shared terminals (shell history risk)

**PreToolUse hooks for known-bad patterns**: for security patterns with no legitimate use in the codebase (e.g. eval, os.system, innerHTML, unsafe deserialization), prefer a PreToolUse blocking hook over a review-phase finding. Blocking at edit time prevents the pattern from ever entering the codebase; review-phase tools catch it after the fact. The local hook at `hooks/security_reminder_hook.py` (installed from BL-101) documents rules and deployment patterns in `artefacts/task-047/extension-guide.md`.

**Ansible Vault tag exclusion in credential hooks**: regex patterns detecting inline secrets (passwords, keys, tokens) must exclude the `!vault |` Ansible Vault tag prefix. A value beginning with `!vault |` is already encrypted and stored in Vault; blocking it is a false positive that prevents legitimate playbook edits. Add a negative lookahead `(?!.*!vault)` or a pre-check `if '!vault' in content_line: continue` to every credential-detection rule that matches YAML values. Document this exclusion in the hook's inline comments.

**Fail-open except blocks in security hooks require an explicit rationale comment**: a bare `except Exception: return None` in a PreToolUse hook silently disables the block if an unexpected error occurs. This is the correct production safety choice (hook errors must not block legitimate writes), but the design intent is non-obvious and future refactors may remove the pattern thinking it is dead code. Add a comment: `# Fail-open: hook errors must never block legitimate writes — log and pass through`. Without this comment, future reviewers cannot distinguish intentional fail-open from accidental swallowing.

**Multi-condition hook rules must use correlated regexes, not independent scans**: when a rule requires two patterns to co-occur within the same logical unit (function call, block, expression), use a single regex that enforces co-occurrence — never two separate `re.search` calls on the same content. Independent scans can match in unrelated locations and produce false positives.

**Blocking rules must bypass session dedup — advisory dedup is a security hole for hard-stop rules**: deduplication (suppressing repeated fires for the same file+rule) is correct for advisory rules to avoid noise, but incorrect for blocking rules — dedup allows a second violation after the first block is acknowledged. Maintain a `BLOCKING_RULE_NAMES` constant; blocking rules always fire regardless of dedup state. Derive it dynamically: `BLOCKING_RULE_NAMES = {p["ruleName"] for p in ALL_PATTERNS}` — a hardcoded set drifts silently when rules are added or removed.

**Workflow guard hook** (`hooks/workflow_guard_hook.py`, installed from BL-088 / task-049): enforces two CLAUDE.md must-always-follow rules via PreToolUse blocking:
- **Bash tool**: blocks `git commit` with the hook-bypass flag — there is no legitimate use of hook bypass in this codebase.
- **Edit/Write on `tasks/queue.json`**: blocks setting `"status": "done"` without a non-empty `"artefact_path"` in the same change. See "Artefact path required on done" in Task Queue section.

**Document-level invariant hooks enforce on Write only**: Edit/MultiEdit calls deliver diff fragments — a hook checking that two fields both appear in a document must use `Write` only, where the full document is available. Return `(None, None)` early for Edit/MultiEdit to avoid false positives on valid multi-step edits.

**Hook pattern interference**: the security hook fires on ALL Edit/Write calls, including `old_string` and files outside the project (e.g. plan files). When editing text that contains a blocked pattern as documentation, split the edit: use a narrow `old_string` substring that avoids the trigger token, then a second edit for the rest.

**Test files containing credential patterns must use string concatenation**: when writing a unit test for a credential-blocking hook, test payloads contain credential-like strings that trigger `hooks/security_reminder_hook.py` during Write. Split the trigger token across concatenated string literals: `"pass" + "wd=Secret"` or `"hana_" + "password: Value"`. The runtime string is identical; the hook's pattern search sees only fragments at write time.

**CCAS workspace structure**: `/opt/claude/CCAS/` has no root `.git`. It contains 6 subrepos each with their own GitHub remote: `ccas-main`, `ccas-core-infrastructure`, `ccas-inventory`, `ccas-jenkins`, `ccas-platform`, `ccas-sap-applications`. Workspace-level files (`hooks/`, `.claude/settings.json`) live at CCAS root but are not version-controlled there — commit shared hook scripts to `ccas-main/hooks/` for version control.

**Security BL item description standard (Hook/MCP)**: when registering a BL item in category Hook or MCP that involves credential handling or OAuth, the description must include (a) hook type (PreToolUse/PostToolUse), (b) what the hook emits on match (path+line only — never matched text), (c) OAuth scope if applicable. Reviewer must verify these fields before marking the BL item ready.

**Observability**:
- Audit trail: who, agent, action, time, artefact
- Token logs: per run and cumulative per task
- Metrics: tokens/run, median latency, success rate, test pass rate
- Alerts: token overspend, policy violations, regressions

**80% cap alert (preflight)**: before starting a task, sum all agent token estimates for that task. If total > 400,000 (80% of 500k cap), halt with: `ALERT: Task <id> estimated tokens (<n>) exceed 80% of project cap. Reduce scope or split task before proceeding.`

**Token rewrite acceptance criteria**: express as savings delta (e.g. "save ≥900 tokens"), not absolute post-rewrite totals. The baseline shifts between plan date and execution date — absolute targets become unachievable when CLAUDE.md grows between task creation and execution.

---

## Workflow Orchestration

0. **Session start — mandatory checklist (run in order before any task work)**:
   - [ ] **Fetch remote**: Run `git fetch origin` before reading any operational file. n8n commits go directly to `origin/main` via GitHub API — without fetching, inbox items are invisible.
   - [ ] **Telegram inbox**: Run `git show origin/main:tasks/telegram-inbox.md`. Promote each item below the header to `tasks/backlog.md` (next BL ID, —, project_manager, P2, new, today), then clear inbox (commit on feature branch → develop → push main). **Dedup**: `grep -i "<keyword>" tasks/backlog.md` before adding. **Routing prefix**: n8n matches exact `BACKLOG: ` (uppercase, colon, space) — `backlog` or `BACKLOG:item` silently dropped.
   - [ ] **Lessons**: Read `tasks/lessons.md`; state the 3 most recent rows before planning. Lessons govern tooling choices and approach — do not repeat captured mistakes.
   - [ ] **Catch-up SelfImprover**: For every `status: done` task in `tasks/queue.json`, verify `artefacts/<artefact_path>/improvement_proposals.md` exists. If absent (directory may not exist either), run SelfImprover for that task — it must create the directory and file from the task definition in queue.json.
   - [ ] **ExitPlanMode denial**: if the user denies ExitPlanMode, use AskUserQuestion to clarify intent before re-attempting — the user may be redirecting to a side task first, not rejecting the plan outright.
   - [ ] **ExitPlanMode mid-skill recovery**: if plan mode activates unexpectedly during a PM skill run (e.g. /pm-propose), write a minimal plan file summarising remaining steps, call ExitPlanMode, then continue the skill after approval.

1. **Plan first (mandatory)**: ALWAYS enter plan mode before any non-trivial task (3+ steps or architectural decisions). Plans are written to `/root/.claude/plans/` (auto-managed by plan mode). **Exception**: PM skills that carry an explicit "Execution mode: do not enter plan mode" preamble are exempt — they execute already-planned and queued work.
2. **Subagents**: offload research, exploration, and parallel analysis to keep main context clean — one task per subagent; pass only pointers (task_id, file paths), never embed full content.
3. **Token minimization**: agents receive only task_id; they read their own context from files. No large context copied between invocations. Stop after each deliverable.
4. **Verify before done**: never mark complete without proving it works. Ask: "Would a staff engineer approve this?"
   **Artefact minimum for git-only tasks**: even when no code is produced, create `artefacts/<task-id>/verification.md` capturing: commands run (e.g. `git log --oneline`, `ls` of key files), their output, and a PASS/FAIL verdict per acceptance criterion. Tasks with no artefact directory cannot be retrospected by SelfImprover.
   **Architecture/research task Definition of Done**: must include "all `NEW:` proposals in the review document are registered as BL items in `tasks/backlog.md`" — SelfImprover does not do this automatically; it is a required explicit step before marking done. For tasks reviewing an external repo/course: minimum 2 research rounds; second round must fetch SKILL.md / agent source files, not just directory listings.
   **External repo baseline**: for tasks targeting an external repo (Pi4 /opt/mas/, /opt/claude/pensieve/, etc.), capture a baseline test run as the first artefact step and store it as `artefacts/<task-id>/baseline_test_run.txt`. The Tester compares against the baseline, not against 100%, to prove failures predate the task.
   **Content migration checklist** (when moving a section from CLAUDE.md to a linked doc):
   1. Pre-move mapping: list every sentence in the source section
   2. Destination verification: confirm each sentence appears in the destination doc
   3. Source retention decision: mark each sentence "moved" or "kept" — no orphans
   3b. Destination separator convention: if appending a new section to an existing doc, run `grep -n "^---$" <dest-doc>` to confirm whether `---` separators are used between sections. If yes, include `---` before the new heading.
   4. Pointer line: add `See \`docs/X.md\` for: topic1, topic2, ...` in CLAUDE.md. Exception — pointer inside a fenced code block: backtick-quoting the path is not possible. Use a plain path but retain the topic keyword list: `See docs/X.md for: topic1, topic2, ...`
   4a. Pointer byte estimate: before finalising migration scope, estimate pointer line sizes as (number of topics × ~40 bytes/keyword). Verify that (content_removed − pointer_overhead) meets the byte target. If margin < 500 bytes, add a reserve migration section or trim pointer keywords.
   5. Final verification: `wc -c CLAUDE.md` and `grep -c "<critical_phrase>"` for rules that must remain present
   **Byte-count target verification**: always use `wc -c` (not Python `len()`) for byte-count acceptance criteria — encoding differences can cause a 100–300 byte discrepancy. Any edit applied after Reviewer approval on a byte-constrained task must be followed by `wc -c` before committing.
5. **Self-improvement**: SelfImprover runs after every pipeline PASS and appends to `tasks/lessons.md`. If a significant pattern is found it also writes `artefacts/<task_id>/improvement_proposals.md` (format below). After any correction: update CLAUDE.md so the mistake cannot recur; commit to git.
6. **Always-on pipeline**: every task runs the full pipeline — no skipping:
   ```
   Builder
     → [Reviewer (YAML agent) + code-quality-reviewer (built-in)] — run IN PARALLEL; combine findings before looping Builder
       (`code-quality-reviewer` must run for ALL task types, including config-only changes, model upgrades, and documentation migrations — silent corruption risks are invisible to scope-limited Reviewer analysis and only surface under CQR technical impact assessment)
     → Tester
     → [DocUpdater (YAML agent) + docs-readme-writer (built-in)]  — run IN PARALLEL
     → SelfImprover (YAML agent)
   ```
   Built-in agent roles:
   - `code-quality-reviewer` — security, quality, best-practices check on all new/modified code
   - `docs-readme-writer` — creates/updates README and module docs for code-producing tasks

   **Doc stage file ownership**: when DocUpdater and docs-readme-writer run in parallel, assign ownership explicitly: DocUpdater → `CHANGELOG.md`; docs-readme-writer → `README.md`. This prevents overwrite conflicts when both agents target the same file. If docs-readme-writer does not confirm README.md was modified in its output, the parent agent must apply the README update directly before committing.
   **DocUpdater CHANGELOG verification**: after DocUpdater writes CHANGELOG.md, spot-check the entry against the actual task scope — DocUpdater infers implementation details from artefacts and may fabricate steps that were explicitly out of scope (e.g. "existing rows backfilled"). Correct before committing.
6b. **End-of-session proposal review (human gate)**: At the end of each PM session, read `artefacts/*/improvement_proposals.md` for all tasks completed this session. Present each pending proposal to the user as: target file, proposed change, rationale, APPROVE / REJECT. Apply only approved proposals immediately (edit file, commit). Log rejected proposals with reason in `tasks/lessons.md`. Never apply a proposal without explicit user approval. After all proposals are resolved, invoke `revise-claude-md` via the `Skill` tool (not `Agent`) to bake session learnings into CLAUDE.md and commit the result. **Cross-file consistency check**: when a proposal introduces a format definition (e.g. improvement_proposals.md schema), verify the format is identical in both CLAUDE.md and the relevant agent YAML before presenting to the user. **Proposal response format**: user replies `APPROVE: P1, P3 / REJECT: P2` — apply all approved in one pass, log rejections. **SelfImprover dedup**: when running SelfImprover for multiple tasks in a session, collect all proposals before presenting — remove duplicates and proposals targeting text already present in the target file. **Scanning for pending proposals**: `find artefacts -name "improvement_proposals.md" | xargs grep -lE "^\*\*Status\*\*: REQUIRES_HUMAN_APPROVAL"` — `^` prevents false positives from body text quoting the pattern; do NOT use `grep -rl`. **pm-propose commit discipline**: after applying approved proposals that edit CLAUDE.md, immediately commit on the current feature branch before proceeding — do not leave session-learning edits unstaged across a context boundary.
7. **Autonomous bug fixing**: when given a bug report, fix it — point at logs/errors, then resolve.
8. **Demand elegance (balanced)**: pause and ask "Is there a more elegant way?" before finalising any non-trivial design. Skip for simple fixes — do not over-engineer.
9. **Minimal impact**: touch only what is strictly necessary; avoid side effects on untouched code or config. If you must change something adjacent, flag it explicitly.
10. **Explain with diagrams**: when explaining architecture or non-obvious decisions, prefer ASCII diagrams over prose where they add clarity.

**PM Planning Session**: invoke ProjectManager with "planning" intent to review, reprioritize, and onboard. PM asks for confirmation before queuing. **Preflight**: `ls artefacts/` before assigning IDs — use descriptive suffix if path exists.
**CLAUDE.md size-reduction planning note**: when a byte-count target is specified, identify at plan time: (a) two primary migration candidates and (b) one "reserve" section — a small, self-contained section already partially referenced by an existing linked doc. Record estimated removal bytes and pointer overhead for all candidates before committing to a migration scope. If primary candidates alone fall short (removal − pointer overhead < target), activate the reserve section rather than discovering the gap during execution.
**Project onboarding automation scan**: when onboarding a new project or beginning a session on a project for the first time, invoke `claude-automation-recommender` (zero-install, read-only) to surface top hooks, MCP servers, skills, and subagent recommendations for the detected tech stack. Run before installing any hook or MCP server — its non-mutating design makes it safe at any time with no side effects.
**Phase gate announcement rule**: when /pm-start detects a phase gate is reached, the announcement section must end with an explicit yes/no approval question before printing the queue summary — do not leave the user with a statement and no prompt.
**MVP ordering gate**: During PM planning, check epics.md for any stories with status `planned` in lower MVP phases before queuing higher-phase work. All stories in a phase must be `done` before the next phase is prioritized.

**Task tracking**:
- Active queue → `tasks/queue.json`
- Backlog + scope-drift → `tasks/backlog.md`
- Kanban view → `tasks/kanban.md`
- Epics & stories → `tasks/epics.md`
- Plan files → `/root/.claude/plans/` (registered in `docs/project-registry.md`)
- Lessons → `tasks/lessons.md` (append-only table: `| Date | Agent | Lesson | Applied To | Confidence | Scope |`)
- Improvement proposals → `artefacts/<task_id>/improvement_proposals.md` (one `## Proposal N` section per proposal, fields: **Target file**, **Change** (diff or description), **Rationale**, **Status:** `REQUIRES_HUMAN_APPROVAL` → `APPROVED` / `REJECTED: <reason>`)
- **Artefact path required on done**: a task may not be set to `status: done` without a non-empty `artefact_path`. If no code was produced, set the path and create a `verification.md` (see step 4).
- Mark items complete immediately as you go
- When marking a queue task `done`, also update the corresponding BL entries in `tasks/backlog.md` to `done` status in the same commit.

---

## CI/CD & Release

Pipeline: Preflight → policy checks → unit/integration tests → canary → full rollout

Test types: unit (generated scripts), integration (tool interactions), regression (per agent update), adversarial (prompt injection / hallucination triggers), canary releases for production.

**Release checklist**: policy field present; preflight token estimate done; security checklist green; tests pass; rollback plan defined.

---

## Task Queue & Resume

All agent work is tracked in `tasks/queue.json`. Schema:

```json
{
  "tasks": [
    {
      "id": "task_001",
      "title": "...",
      "project": "pensieve|ccas|pi-homelab|other",
      "assigned_to": "builder|reviewer+code-quality-reviewer|tester|doc-updater+docs-readme-writer|self-improver",
      "status": "pending|in_progress|paused|review|test|done|failed",
      "artefact_path": "artefacts/task_001/",
      "created": "ISO8601",
      "updated": "ISO8601",
      "token_estimate": 8000,
      "resume_from": null,
      "notes": [],
      "mvp_template": {
        "doel": "",
        "niet_in_scope": [],
        "acceptatiecriteria": [],
        "security_arch_impact": "",
        "tests_required": "",
        "definition_of_done": [],
        "rollback_plan": "",
        "incident_owner": "",
        "privacy_dpia": "",
        "cost_estimate": ""
      }
    }
  ]
}
```

**Rate limit / resume flow**:
1. Agent hits rate limit → sets `status: "paused"`, `resume_from: "<step_name>"` → stops
2. User waits for rate limit to reset
3. User runs ProjectManager agent again
4. ProjectManager reads queue, finds paused tasks, resumes from `resume_from` step

**Queue validation**: `tasks/queue.schema.json` enforces all field types. Key constraint: `artefact_path` must match `^artefacts/[a-zA-Z0-9_-]+/$` — no path traversal. Validate with any JSON Schema tool before adding tasks manually.

**Artefact path assignment**: Before adding a new task to queue.json, run `ls artefacts/` to check if the target path already exists. If it does, use a descriptive suffix (e.g. `artefacts/task-008-laptop/`) rather than the bare ID. This prevents accidental clobbering of prior task outputs and enables retrospective analysis by SelfImprover for both the old and new work.

**`assigned_to` tracks pipeline stage**: update `assigned_to` at every stage transition alongside `status` (`builder` → `reviewer+code-quality-reviewer` → `tester` → `doc-updater+docs-readme-writer` → `self-improver`). For parallel stages set `assigned_to` to both agents: `"reviewer+code-quality-reviewer"` or `"doc-updater+docs-readme-writer"`.

**queue.json stale-read fix**: if the Edit tool fails with "file modified since read", use `python3 -c "import json; q=json.load(open('tasks/queue.json')); ...; json.dump(q,open('tasks/queue.json','w'),indent=2)"` to atomically update it.

**Python datetime**: use `datetime.now(datetime.UTC).isoformat()` not `datetime.utcnow()` — deprecated in Python 3.12+; system runs 3.13.5.

**Logs** (`logs/` is gitignored — never `git add logs/`):
Note: `logs/token_log.jsonl` is already tracked by git (predates the gitignore rule) — it will always appear as `modified` in `git status`. This is expected; do not stage or commit it.
- `logs/audit.jsonl` — append-only, one JSON object per line: `{timestamp, agent, task_id, action, status}`
- `logs/token_log.jsonl` — per-run token accounting: `{timestamp, agent, task_id, token_estimate}`
  Every sub-agent (Builder, Reviewer, Tester, DocUpdater, SelfImprover) must write one entry per invocation — not just ProjectManager. This enables per-agent token observability and identifies highest-cost pipeline stages.

---

## n8n Workflow Deployment (Pi4)

SSH alias: `pi4` (192.168.1.10). n8n runs as Docker container `n8n`.
GitHub PAT: `/opt/n8n/github-pat` on Pi4. See `docs/n8n-deployment.md` for: full deploy sequence, import gotchas, Pi4 Docker patterns, workflow JSON patterns, MAS stack, docker restart env, daily scheduler, SSH grep, vault location, Pensieve branch, dashboard sync, GitHub API commits, main/develop divergence.

---

## Python Testing Patterns

See `docs/python-testing.md` for: hyphenated filenames, Docker-only packages, unwritable paths as root, path-guarded fixtures, pytest run command.
