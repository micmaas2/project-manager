# Project Manager — Multi-Agent Automation System

A hierarchical multi-agent system that builds automations and scripts across projects.
One orchestrator (ProjectManager) oversees specialist Builder, Reviewer, and Tester agents.

## Architecture

```
ProjectManager (Opus 4.6)
  └── Builder    (Sonnet 4.6) — generates scripts/playbooks
  └── Reviewer   (Sonnet 4.6) — checks quality and arch compliance
  └── Tester     (Sonnet 4.6) — validates and reports
```

State is file-based. All agents read/write `tasks/queue.json` and `artefacts/<task_id>/`.
If a rate limit is hit mid-run, the task is marked `paused` and resumes when you re-run the orchestrator.

## Directory Layout

```
.claude/agents/     Agent YAML definitions
tasks/              queue.json, todo.md, lessons.md
artefacts/          Agent outputs (one subdir per task)
logs/               audit.jsonl, token_log.jsonl
scripts/            Generated automation scripts
docs/               Architecture decisions
hooks/              pre-commit hook (symlinked to .git/hooks/)
```

## Adding a Task

Add an entry to `tasks/queue.json` with status `pending`, then run the ProjectManager agent.

## Branching

```
main      ← stable releases only
develop   ← integration branch
feature/* ← all work starts here
```

Never commit directly to `main` or `develop`. The pre-commit hook enforces this.

## Commit Format

```
[AREA] Brief description
```

Areas: `ROLE`, `DOCS`, `TEST`, `FIX`, `REFACTOR`, `PLAYBOOK`, `JENKINS`, `INVENTORY`, `AGENT`
