# Build Notes — task-037 CLAUDE.md Size Reduction

## Final char count
- Before: 39,310 chars
- After: 29,784 chars
- Savings: 9,526 chars (24.2% reduction)
- Target was ≤35,000 — PASS (margin: 5,216 chars)

## Sections modified / moved

### Moved to docs/n8n-deployment.md
**Original section**: "n8n Workflow Deployment (Pi4)" (lines 369–486, ~5,800 chars)

Moved: Pi4 Python packages, Pi4 root-owned git repo pattern, Docker compose --build/--no-deps patterns, docker-compose env file symlink, credential-placeholder patching, full deploy sequence, all import gotchas, quick health check commands, delete workflow commands, updating JSON programmatically, testing n8n Code nodes, HTTP timeout, timezone, finding Telegram chat_id, all workflow JSON patterns.

Kept in CLAUDE.md: SSH alias + PAT location, vault location rule, Pensieve repo active branch rule, dashboard-preview.md rule, GitHub API commits (stdlib), main/develop divergence rule. Plus pointer line to docs/n8n-deployment.md.

### Moved to docs/python-testing.md
**Original section**: "Python Testing Patterns" (lines 489–499, ~1,500 chars)

Moved: all 4 patterns (hyphenated filenames, Docker-only packages, unwritable paths, path-guarded fixtures).

Kept in CLAUDE.md: 1-line section with pointer + "run tests with: pytest" command.

### Condensed in CLAUDE.md
**Git merge-conflict pattern**: reduced from 5-step numbered list + warning to 2-line summary. All essential information preserved (abort, resolve on feature/sync-X, push via refspec, pull, avoid stash).

## Rules carefully preserved
- **Reviewer confidence scoring** (M-1 mirror): verbatim, untouched — line 120
- **M-1 copy-paste rule**: untouched — line 144
- **Cross-file rule mirroring (M-1 pattern)**: untouched — line 142
- **require_human_approval** policy field: present in 3 places — lines 146, 159, 219
- **pm-propose commit discipline**: untouched — line 270
- **BACKLOG: routing prefix**: untouched — line 244
- **MVP template fields block**: completely untouched — lines 172–211
- All agent roles, model policies, governance rules: untouched
- Session start mandatory checklist: untouched
- Task tracking rules: untouched

## Verification results
- `wc -c CLAUDE.md`: 29,784 — PASS (≤35,000)
- `bash -n hooks/pre-commit`: exit 0 — PASS
- `require_human_approval`: FOUND (3 occurrences)
- `confidence: N (1-100)`: FOUND
- `M-1 mirror`: FOUND
- `pm-propose commit discipline`: FOUND
- `BACKLOG: `: FOUND

## Files created
- `docs/n8n-deployment.md` — full n8n reference (Pi4 patterns, deploy sequence, import gotchas, workflow JSON patterns)
- `docs/python-testing.md` — all Python testing patterns

---

## Fix Loop Results

### Fixes Applied

| Fix | File | Description | Status |
|-----|------|-------------|--------|
| 1a | `docs/n8n-deployment.md` | Added "Without this, compose exits with "env file /opt/mas/.env not found"." to docker-compose env file section | APPLIED |
| 1b | `docs/n8n-deployment.md` | Added "plan for the full dependency chain build time, not just the target service." to `--build` section | APPLIED |
| 1c | `CLAUDE.md` | Added example branch name + "Doc commits intended for `main` must target the correct branch." to Pensieve note | APPLIED |
| 2 | `docs/n8n-deployment.md` | Removed duplicate `**GitHub API commits (stdlib)**` block (canonical copy remains in CLAUDE.md) | APPLIED |
| 3 | `CLAUDE.md` | Reformatted both pointer lines to `See \`docs/X.md\` for: ...` format | APPLIED |
| 4 | `docs/n8n-deployment.md` | Changed `## Deleting a workflow` to `## Deleting a workflow (soft-archive via REST — excluded from future exports)` | APPLIED |
| 5 | `docs/n8n-deployment.md` | Added "Document the pagination requirement in \`deploy-notes.md\`." after nextCursor sentence | APPLIED |

### Final char count
- `wc -c CLAUDE.md`: **29,830** — PASS (≤35,000; margin: 5,170 chars)

### Grep checks (CLAUDE.md)
- `require_human_approval`: **3 occurrences** — PASS
- `confidence: N (1-100)`: **1 occurrence** — PASS
- `M-1 mirror`: **1 occurrence** — PASS
