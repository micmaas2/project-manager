# CLAUDE.md — Claude Project Manager

Multi-agent PM system for orchestrating work across managed projects on this server.
Git: `https://oauth2:TOKEN@localhost:8443/claude/claude-project-manager.git` — `http.sslVerify=false` set in repo config; use `git push origin <branch>` directly
Project registry: `docs/project-registry.md` (update there first when adding projects).

---

## Workspace

| Project | Path | Purpose | Status |
|---------|------|---------|--------|
| claude-project-manager | /datadisk/claude/claude-project-manager | This PM system | active |
| pbs-azure-subscription | /datadisk/claude/pbs-azure-subscription | Azure subscription analysis | active |

No Raspberry Pi, Telegram, n8n, or external webhook integrations exist in this system.

---

## Session Startup (mandatory, in order)

1. **Lessons** — Read `tasks/lessons.md`; surface 3 most recent rows before any decision.
2. **Queue** — Read `tasks/queue.json`; resume `paused` tasks first; identify `done` tasks lacking `artefacts/<id>/improvement_proposals.md` → queue SelfImprover catch-up.
3. **Phase gate** — Check `tasks/epics.md`; if all current-phase stories are `done`, present human gate before queueing next phase.
4. **Plan mode** — Enter plan mode for any task with 3+ steps or architectural decisions.
5. **ExitPlanMode denial** — if the user denies ExitPlanMode, use AskUserQuestion to clarify intent before re-attempting; they may be redirecting to a side task first.
6. **Summary** — Present lessons, paused/catch-up work, MVP status, and proposed work. **Await user confirmation before executing.**

Run `/pm-start` to execute this sequence.

---

## Model Policy / Token Governance

| Model | Use | Label |
|-------|-----|-------|
| Opus (`claude-opus-4-5`) | ProjectManager (planning/scope), Architect (design) — use sparingly | `[Opus]` |
| Sonnet (`claude-sonnet-4-6`) | Builder, Reviewer, Tester | `[Sonnet]` |
| Haiku (`claude-haiku-4-5`) | DocUpdater, SelfImprover, status checks, scope checks, simple lookups | `[Haiku]` |

- **Per-agent max**: 10,000 tokens/run
- **Project cap**: 500,000 tokens/run — hard fail above this
- **Preflight**: token estimate required before every task execution
- **Artefact stop**: agents stop after one deliverable; continuation requires explicit user approval
- **Default to Haiku** for any task that does not require reasoning over complex context
- **Token log**: PM appends `{"timestamp":…,"agent":…,"task_id":…,"token_estimate":…}` to `logs/token_log.jsonl` at each agent handoff (same pattern as audit.jsonl). `logs/` is gitignored.
- **80% cap alert (preflight)**: before starting a task, sum all agent token estimates for that task. If total > 400,000 (80% of 500k cap), halt with: `ALERT: Task <id> estimated tokens (<n>) exceed 80% of project cap. Reduce scope or split task before proceeding.` (This is an estimate-based check; post-run actuals are reported by `/pm-tokens` from token_log.jsonl.)

---

## Agent Roles & Spawn Order

```
Manager (Opus) → Architect (Opus, optional) → Builder (Sonnet)
  → [Reviewer (Sonnet) + code-quality-reviewer (built-in)] parallel
  → Tester (Sonnet)
  → [DocUpdater (Haiku) + docs-readme-writer (built-in)] parallel
  → SelfImprover (Haiku)
  → (end-of-session) revise-claude-md built-in
```

| Agent | File | Model | Stops At |
|-------|------|-------|----------|
| project-manager | `.claude/agents/project-manager.yaml` | Opus | Approved task plan |
| architect | `.claude/agents/architect.yaml` | Opus | `artefacts/<id>/architecture.md` |
| builder | `.claude/agents/builder.yaml` | Sonnet | Implementation + status → review |
| reviewer | `.claude/agents/reviewer.yaml` | Sonnet | `artefacts/<id>/review.md` |
| tester | `.claude/agents/tester.yaml` | Sonnet | `artefacts/<id>/test_report.md` |
| doc-updater | `.claude/agents/doc-updater.yaml` | Haiku | `artefacts/<id>/doc_update.md` |
| self-improver | `.claude/agents/self-improver.yaml` | Haiku | `tasks/lessons.md` row + proposals |
| code-quality-reviewer | `~/.claude/agents/code-quality-reviewer.md` | Sonnet | Review report (built-in, global) |
| docs-readme-writer | `~/.claude/agents/docs-readme.writer.md` | Haiku | README/module docs (built-in, global) |

**Architect is optional**: skip for simple tasks (script fixes, doc updates, config changes).

### Known Gotchas

- **Global agent filenames are case- and punctuation-sensitive**: `docs-readme.writer.md` uses a period (`.`) before "writer", not a hyphen. Referencing it as `docs-readme-writer.md` causes a silent invocation failure. Before referencing any global agent in a design doc or agent prompt, verify the exact filename with `ls ~/.claude/agents/`.

### Prompt Writing Discipline

All agent prompts MUST use imperative voice addressed to the agent itself ("You will", "Do not", "Stop if"). Never narrate what other agents do — instead state this agent's responsibility relative to other agents' outputs.

**BAD**: "Reviewer checks all criteria and writes review.md"
**GOOD**: "If you receive artefacts/<task_id>/review.md with a FAIL verdict, address all Critical and Major issues before re-submitting."

Orchestration sequencing (waiting, parallelism) belongs in design docs (e.g., `artefacts/task-001/review_stage_design.md`), not embedded in agent prompts. If a prompt references orchestration, it must include: "PM/orchestrating layer will coordinate this."

### Skill Authoring Rules

Skills are executable command prompts (`.claude/commands/*.md`) that may contain procedural steps with angle-bracket placeholders (e.g., `<phase>`, `<branch-name>`, `<stories>`).

- **Every angle-bracket placeholder must include an explicit resolution instruction** in its step text, naming the source file to read and the lookup pattern. Do not assume the reader will infer where the data lives.
  - **BAD**: `Use the phase label identified from tasks/epics.md in place of <phase>.` (implies earlier context; silent failure if context missing)
  - **GOOD**: `Read tasks/epics.md and identify the current in-progress MVP phase label (e.g. MVP2) — this is the phase whose stories are not yet all done. Use this phase label in place of <phase>.` (explicit source, explicit meaning)
- **Test all placeholders manually** before committing: simulate a user running the skill with no prior context (fresh terminal session) and verify every `<placeholder>` can be resolved without ambiguity.
- Placeholder names must be specific to the data scope (e.g., `<branch-name>` not `<branch>`; `<phase>` not `<n>`).
- **Security filter ordering: inline, not post-hoc** — When a skill collects items into a buffer and then filters, the filter MUST be inlined as a per-item guard during collection. A post-hoc filter is logically bypassed when the buffer already contains sensitive data. Fix: "Before appending any line to `<buffer>`, inspect for sensitive patterns (password, secret, api_key, etc.) and skip if found."

---

## Pipeline (Always-On)

```
Builder
  → [Reviewer + code-quality-reviewer] — parallel; combine before feeding Builder
  → Tester (90% pass SLO)
  → [DocUpdater + docs-readme-writer] — parallel
  → SelfImprover
```

No pipeline stage may be skipped. Reviewer and CodeQualityReviewer always combine findings before looping Builder.
- **Evidence tasks exception**: if a task's acceptatiecriteria requires `combined_review_evidence.md`, list both `review.md` and `combined_review_evidence.md` as Reviewer deliverables in the PM prompt. Single-file artefact-stop rule is suspended for these tasks.
- **Meta-validation placeholder pattern**: for tasks that validate the pipeline itself, instruct Builder Round 1 to deliberately omit one required section (labelled `[PLACEHOLDER]`). This guarantees the review loop runs at least once, satisfying AC-1, without manufacturing a false defect.

**Tester SLO rules**: Pass rate = (tests passing) / (tests run, excluding skipped) × 100. ERROR (timeout or setup failure) counts as FAIL. Use `artefacts/task-002/test_report_template.md` as the report format.

- **File ownership split**: when DocUpdater and docs-readme-writer run in parallel, the PM must assign file ownership in each agent's prompt: DocUpdater → `CHANGELOG.md`; docs-readme-writer → `README.md`. This prevents overwrite conflicts when both agents target the same file.
- **Doc stage authority**: see `artefacts/task-004/doc_stage_design.md` for full orchestration rules, file ownership table, and override procedure.

### Template Authoring Rules

When creating artefact templates with numeric fields or denominators:
- Use scope-explicit placeholder names, not ambiguous terms
  - **BAD**: `<total>` (does it include skipped? all tests ever? unclear)
  - **GOOD**: `<run>` (tests run, excluding skipped — define once at top)
- Define each placeholder's meaning in a comment or header on first appearance
- Verify all usages of a placeholder refer to the same scope (grep the template before committing)

---

## MVP Phases & Scope Discipline

**Phase gate**: all stories in phase N must be `done` before phase N+1 tasks are queued.

| Phase | Stories |
|-------|---------|
| MVP1 | Repo structure, git hooks, CLAUDE.md, queue schema, agent YAMLs, commands |
| MVP2 | Parallel review stage wired; Tester validated against a real task |
| MVP3 | DocUpdater + SelfImprover; proposal loop end-to-end |
| MVP4 | Token monitoring; /pm-onboard; scope drift P1 automation |

**MVP template** (required for every task in queue.json):
```
doel: <1 sentence>
niet_in_scope: [...]
acceptatiecriteria: [1. ... 2. ... 3. ...]
slos: { test_pass_rate_pct: 90 }
max_tokens_per_run: 8000
security_arch_impact: <note>
no_external_deps: true/false
prerequisites: [...]
tests_required: unit|integration|regression|unit+integration
rollback_plan: <steps>
definition_of_done: [...]
incident_owner: <name>
privacy_dpia: yes/no + note
cost_estimate: EUR ...
```

---

## Task Tracking

| File | Purpose |
|------|---------|
| `tasks/queue.json` | Active task queue (schema-validated) |
| `tasks/queue.schema.json` | JSON Schema for queue.json |
| `tasks/backlog.md` | Backlog + `[DRIFT]` items |
| `tasks/epics.md` | Epic > Story hierarchy |
| `tasks/kanban.md` | Kanban view (auto-refreshed by `/pm-status`) |
| `tasks/lessons.md` | Append-only lessons table |
| `artefacts/<task-id>/` | All artefacts per task |
| `logs/audit.jsonl` | Append-only audit trail |
| `logs/token_log.jsonl` | Per-run token accounting |

When marking a task `done` in queue.json: also mark corresponding backlog entries `done` in the same commit.
Artefact path assignment: run `ls artefacts/` before assigning — use descriptive suffix if path exists.
`assigned_to` tracks the current pipeline stage owner — update it at each stage transition (`builder` → `reviewer` → `tester` → etc.) alongside `status`.
For parallel stages set `assigned_to` to both agents: `"reviewer+code-quality-reviewer"` or `"doc-updater+docs-readme-writer"`.
**queue.json stale-read fix**: if the Edit tool fails with "file modified since read", use `python3 -c "import json; q=json.load(open('tasks/queue.json')); ...; json.dump(q,open('tasks/queue.json','w'),indent=2)"` to atomically update it.

---

## Scope Enforcement

**Trigger points**: task pickup (PM), file-not-in-spec (Builder sentinel), review checklist item 4 (Reviewer), ad-hoc request (PM).

```
Work item → in acceptatiecriteria? YES → proceed
          → in niet_in_scope?      YES → DRIFT (hard reject)
          → in higher MVP phase?   YES → DRIFT (phase gate)
          → ambiguous?                 → escalate to human
```

**On drift detected**:
1. STOP implementation of drifted item.
2. Append to `tasks/backlog.md`: `| BL-NNN | [DRIFT] <desc> | EPIC-XXX | <project> | P3 | backlog | <date> | <task_id> by <agent> |`
3. Add to `scope_drift_log[]` in task's queue.json entry.
4. P1 (security/blocking): halt pipeline immediately. P2/P3: surface at next gate. P4: silent backlog.

**P1 escalation format** (use exactly when halting for P1 drift):
```
🚨 P1 SCOPE DRIFT — PIPELINE HALTED
Detecting agent : <agent-name>
Task ID         : <task-id>
Drift item      : <one-sentence description of the out-of-scope work detected>
Classification  : P1 — <reason: security | blocking-prerequisite | data-loss-risk>
Backlog entry   : BL-NNN appended to tasks/backlog.md
Recommended action: Review scope with PM before resuming. Run `/pm-scope` to triage.
```

Replace each `<...>` with the actual values at detection time. Do NOT continue any pipeline work after emitting this message.

---

## Self-Improvement Loop

```
Pipeline PASS
  → SelfImprover (Haiku): append tasks/lessons.md row; write improvement_proposals.md if significant
  → End-of-session: collect all proposals, deduplicate, present to human
  → User: APPROVE: P1, P3 / REJECT: P2
  → Apply approved immediately; log rejected with reason in lessons.md
  → revise-claude-md built-in → commit
```

**Proposal format** (`artefacts/<id>/improvement_proposals.md`):
```
## Proposal N
**Target file:** <path>
**Change:** diff or description
**Rationale:** why this prevents recurrence
**Status:** REQUIRES_HUMAN_APPROVAL
```

**Dedup rules**: skip if proposed text already in target file; skip if same lesson in lessons.md; merge duplicates across tasks before presenting.

**pm-propose scan**: use `find artefacts -name "improvement_proposals.md" | xargs grep -l "REQUIRES_HUMAN_APPROVAL"` — `grep -rl` on the whole artefacts dir produces false positives from Tester test files that assert on the string.

> **Maintenance note (M-1 pattern)**: Enumerated rules that mirror across CLAUDE.md and agent YAMLs (e.g., P1 classification criteria) can silently accumulate orphan entries in either file. When editing either CLAUDE.md or any agent YAML that contains mirrored rules, verify rule counts and text match in BOTH directions. Tester must include a regression guard for any task that modifies mirrored content: (a) a rule-count equality check across all copies, and (b) an absence check for the specific orphan rule that was removed. Human review alone is insufficient to catch silent count drift.

---

## Git Workflow

```
main (production)   ← stable, tested, approved only
  ↑
develop             ← active development; features merge here
  ↑
feature/*           ← new features, bug fixes, tasks
```

- Never commit directly to `main` or `develop` — this includes small changes (proposal applies, doc fixes); the pre-commit hook blocks all direct commits to `develop`; always use a `feature/*` branch
- Commit format: `[AREA] Brief description` — areas: `AGENT | PM | DOCS | TEST | FIX | REFACTOR | SCOPE | RELEASE`
- Always update CLAUDE.md, README.md, CHANGELOG.md with changes
- Pre-commit hooks: always active — NEVER use `--no-verify`
- Secret detection matches `*.env`, `secrets.json/yaml`, `passwords.txt`, `credentials.json`, `*.pem`, `*.key` — NOT generic words like "token" in filenames
- **`.claude/settings.local.json` is git-tracked but auto-modified by Claude Code** when skills are added to allowed tools — creates dirty tree at `/pm-close` Step 1. Fix: it is now gitignored. If it reappears as tracked, run `git rm --cached .claude/settings.local.json`.
- Global agents in `~/.claude/agents/` (`code-quality-reviewer`, `docs-readme-writer`) are available in all projects; invoke via `subagent_type` by name, no local copy needed
- Release: `git push origin develop:main` (pre-commit blocks local merge commits on main)

### Sprint / MVP Close Procedure

Run at the end of every sprint and at every MVP phase gate, in order:

1. **Ensure clean working tree** — commit or discard all uncommitted changes; confirm `git status` is clean.
2. **Run `/pm-propose`** — triage all pending improvement proposals; apply approved changes.
3. **Run `revise-claude-md`** — bake session learnings into CLAUDE.md.
4. **Merge feature branch → develop** — `git merge feature/<name> --no-ff`; use commit message `[RELEASE] Merge feature/<name> → develop (<phase> complete)`.
5. **Push develop** — `git push origin develop`.
6. **Delete feature branch** — `git branch -d feature/<name>`; check `git branch -r | grep feature` and delete any remote remnants.
7. **MVP phase gate** (if all phase stories done) — present gate to human before queuing next phase.

---

## Governance & Observability

- **Runtime policy**: all agent actions checked for `allowed_tools`, `max_tokens_per_run`, `external_calls_allowed`, `require_human_approval`. Non-compliant actions blocked and logged.
- **Secrets**: never in prompts or logs; no secrets in committed files
- **Audit trail**: `logs/audit.jsonl` — `{timestamp, agent, task_id, action, status}` per line
- **Token log**: `logs/token_log.jsonl` — `{timestamp, agent, task_id, token_estimate}` per line
- `logs/` is gitignored (runtime state)
- **Audit log bootstrap**: the PM must create `logs/audit.jsonl` (empty file) before the first agent runs. Use `touch logs/audit.jsonl` before invoking Builder. Agents that append to a non-existent file will fail silently.

---

## Slash Commands

| Command | Purpose |
|---------|---------|
| `/pm-start` | Session startup sequence |
| `/pm-plan` | Planning session: review backlog, queue next sprint |
| `/pm-status` | Kanban + token summary + phase status |
| `/pm-scope` | Show and triage `[DRIFT]` items |
| `/pm-run` | Execute next pending task through full pipeline |
| `/pm-propose` | End-of-session proposal review |
| `/pm-lessons` | Last 10 lessons |
| `/pm-tokens` | Token usage report — per-task and per-agent spend, cap remaining |
| `/pm-onboard <path>` | Onboard new managed project — discovery scan, registry update, TODO/FIXME backlog creation |
| `/pm-close` | Execute Sprint/MVP Close Procedure (clean tree, proposals, merge, push, branch cleanup, phase gate) |

---

## Rate Limit / Resume Flow

1. Agent hits rate limit → sets `status: "paused"`, `resume_from: "<step_name>"` → stops
2. User waits for limit to reset
3. User runs `/pm-start` → paused tasks surface and resume automatically
