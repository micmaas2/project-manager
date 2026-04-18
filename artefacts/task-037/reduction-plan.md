# CLAUDE.md Reduction Plan — task-037

## Current state
- File: `/opt/claude/project_manager/CLAUDE.md`
- **Current size**: 39,310 chars (499 lines)
- **Target**: ≤35,000 chars
- **Required savings**: ≥4,310 chars

## Sections targeted

| Section | Lines | Current chars (est.) | Proposed chars | Approach | Est. savings |
|---|---|---|---|---|---|
| n8n Workflow Deployment (Pi4) | 369–486 | ~5,800 | ~1,300 | Move bulk to `docs/n8n-deployment.md`; keep 5 key operational rules + pointer | ~4,500 |
| Python Testing Patterns | 489–499 | ~1,500 | ~100 | Move all to `docs/python-testing.md`; keep pointer only | ~1,400 |
| Git merge-conflict pattern | 65–71 | ~600 | ~350 | Condense 5-step numbered list to 2-line summary with essential commands | ~250 |

**Estimated total savings**: ~6,150 chars → projected result ~33,160 chars (well under 35,000)

## Hard constraints observed
- MVP template fields block: NOT touched
- M-1 mirror definitions: NOT touched  
- Reviewer confidence scoring definition: NOT touched
- All operational rules, policy fields, agent roles: preserved
- Every moved section gets a pointer line in CLAUDE.md

## Linked docs to create
- `docs/n8n-deployment.md` — full n8n deploy sequence, import gotchas, workflow JSON patterns, Pi4 Docker patterns
- `docs/python-testing.md` — all Python testing patterns
