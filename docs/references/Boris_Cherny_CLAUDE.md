# CLAUDE.md - Boris Cherny's Claude Code Workflow

## Workflow Orchestration

### 1. Plan Mode Default
- Enter plan mode for ANY non-trivial task (3+ steps).
- If something goes sideways, STOP and re-plan immediately.
- Write detailed specs upfront to reduce ambiguity.

### 2. Subagent Strategy
- Use subagents liberally to keep main context window clean.
- One task per subagent for focused execution.
- For complex problems, throw more compute at it (/spawn [name]).

### 3. Self-Improvement Loop
- After ANY correction: "Update CLAUDE.md so you don’t make that mistake again."
- Write rules that prevent repetition; commit to git.
- Ruthlessly iterate until mistake rate drops.

### 4. Verification Before Done
- Never mark complete without proof it works.
- Ask: “Would a staff engineer approve this?”
- Run tests, check logs, demonstrate correctness.

### 5. Demand Elegance (Balanced)
- Pause and ask “Is there a more elegant way?”
- Skip for simple fixes—don’t over-engineer.

### 6. Autonomous Bug Fixing
- On bug report: Just fix it (zero context switching).

## Task Management
1. Plan First: Write to tasks/todo.md.
2. Verify Plan: Check before starting.
3. Track Progress: Mark complete as you go.
4. Explain Changes: High-level summary per step.
5. Document Results: Add review to todo.md.
6. Capture Lessons: Update lessons.md (or CLAUDE.md).

## Core Principles
- **Simplicity First**: Minimal code; delete lines if possible.
- **No Laziness**: Root causes only—no band-aids.
- **Minimal Impact**: Touch only necessities; no side effects.

## Project Norms (Customize Here)
- Run in parallel: 3–5 sessions via git worktree.
- Slash commands: /plan, /verify, /techdebt.
- Hooks: PostToolUse for formatting; pre-allow safe perms.
- Learning: Explain WHY in changes; use ASCII diagrams.

## Activation
Start every session: "Follow CLAUDE.md strictly. Analyze context and plan next steps."
