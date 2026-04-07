# Improvement Proposals — task-008

**Agent**: SelfImprover [Sonnet]
**Date**: 2026-04-07
**Task**: Laptop backlog and Pensieve capture mechanism

---

## Proposal 1

**Target file**: `tasks/backlog.md`

**Change**: Add a new backlog entry for task-009: Pi4-side Obsidian vault sync. The entry should read:

```
| BL-NNN | task-009: Pi4 vault sync — pull pensieve GitHub repo into Obsidian vault on Pi4 | EPIC-003 | pi-homelab | P2 | new | 2026-04-07 |
```

**Rationale**: The deploy-notes.md for task-008 explicitly documents that Pensieve captures land in the `micmaas2/pensieve` GitHub repo but do NOT automatically sync to the Pi4 Obsidian vault. This vault-sync gap is a known, recurring pattern across tasks — it was first called out in task-008's review as a known limitation ("Vault sync requires Pi4-side pull or task-009 webhook"). Without a queued follow-up task, this gap will remain open indefinitely. The lesson added to lessons.md (2026-04-07) requires that a follow-up task is queued at build time whenever a sync gap is documented.

**Status**: APPROVED

---

## Proposal 2

**Target file**: `CLAUDE.md` — MVP template section

**Change**: Add `no_external_deps: true/false` as an optional field in the MVP template, with a note that scripts targeting arbitrary developer laptops or minimal environments should set this to `true` and Builder must enforce stdlib-only implementation when it is set.

Proposed diff in the MVP template block:

```
Prerequisites: [tool >= version, ...]
+No external deps: true/false (if true: stdlib/built-ins only; no pip/npm installs)
Tests: unit/integration/regression
```

**Rationale**: task-008 enforced stdlib-only as an implicit constraint ("Works without requiring Claude Code or SSH access"). This is a recurring design decision for any laptop-facing or cross-platform script. Making it an explicit MVP template field ensures Builder and Reviewer both check it consistently, rather than relying on it being inferred from the acceptance criteria prose.

**Status**: APPROVED
