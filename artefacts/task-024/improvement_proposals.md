# Improvement Proposals — task-024

## Proposal 1
**Target file**: `CLAUDE.md`
**Change**: Add to the PM Skills table a note that new PM skills should be authored
using the `skill-creator` plugin for eval-driven development before shipping:
```
| `skill-creator` | Marketplace | Eval-driven skill authoring; run for new/revised PM skills |
```
Insert after the existing PM Skills table in the "PM Skills" section.
**Rationale**: Without this pointer, future skill authors will continue hand-authoring
without evals — repeating the quality gap identified in this review.
**Status**: APPROVED
