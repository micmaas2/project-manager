# Build Notes — task-050

**Builder**: [Sonnet]
**Date**: 2026-04-29

## Changes Made

### 1. tasks/lessons.md — schema updated
- Added `Confidence` and `Scope` columns to the header row and separator.
- Existing rows left untouched (retroactive scoring is out of scope per task definition).

### 2. .claude/agents/self-improver.yaml — output format updated
- Updated `Format:` line to include `| Confidence | Scope |` columns.
- Added inline definitions for both fields directly below the format line.

## Design Notes

**Confidence field (1-100)**:
Represents how certain the lesson is applicable to future work.
- 90-100: proven pattern (occurred in 3+ tasks with same failure mode)
- 70-89: high likelihood (occurred 2+ times or has clear root cause)
- 50-69: moderate (single occurrence, plausible generalization)
- 1-49: speculative (edge case, context-dependent)

**Scope field**:
Free-text describing which project or agent class the lesson applies to.
Examples: "project_manager", "all projects", "all Builder tasks", "pi-homelab", "pensieve"

## No-touch decisions
- Existing lessons rows: not modified (out of scope).
- No other agent YAMLs modified.
- No CLAUDE.md changes (no new governance rule introduced — the field definitions are self-contained in self-improver.yaml).
