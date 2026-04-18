# Code Quality Review — task-037 CLAUDE.md Size Reduction

## Overall verdict: NEEDS_WORK (5 findings ≥80 confidence)

---

## Finding 1 — Content dropped during move (not relocated)
**severity**: major  
**confidence**: 97

Three actionable instructions were removed from CLAUDE.md and not added to docs/n8n-deployment.md:

**1a** — Docker compose error message: `docs/n8n-deployment.md` Pi4 docker-compose env file section missing: "Without this, compose exits with \"env file /opt/mas/.env not found\"."

**1b** — Docker compose `--build` time note: "plan for the full dependency chain build time, not just the target service" was removed.

**1c** — Pensieve branch commit instruction: "Doc commits intended for `main` must target the correct branch." was removed from the Pensieve branch note in CLAUDE.md.

**Fix**: Restore each sentence in its appropriate location (1a, 1b → docs/n8n-deployment.md; 1c → CLAUDE.md Pensieve branch line).

---

## Finding 2 — GitHub API commits block duplicated in both files
**severity**: minor  
**confidence**: 92

`GitHub API commits (stdlib)` block appears verbatim in both CLAUDE.md (retained) and docs/n8n-deployment.md (also added). Creates M-1 drift risk on future edits.

**Fix**: Remove from docs/n8n-deployment.md — keep CLAUDE.md as the single source.

---

## Finding 3 — Pointer line format inconsistency
**severity**: minor  
**confidence**: 88

n8n pointer uses mid-sentence prose; Python testing pointer leads with `See`. No canonical format for future linked docs.

**Fix**: Standardize both to `See \`docs/<name>.md\` for: <comma-separated topics>.`

---

## Finding 4 — n8n-deployment.md: "Deleting a workflow" heading missing parenthetical
**severity**: low  
**confidence**: 85

Original: "**Deleting a workflow** (soft-archive via REST — excluded from future exports)". New heading drops the parenthetical, losing the explanation of why export counts drop after deletion.

**Fix**: Add `(soft-archive via REST — excluded from future exports)` back to the heading or as a note directly under it.

---

## Finding 5 — REST API `limit=N`: pagination doc instruction dropped
**severity**: low  
**confidence**: 83

Original included: "Document the pagination requirement in `deploy-notes.md`." This was removed from docs/n8n-deployment.md.

**Fix**: Add the sentence back after the nextCursor loop instruction.

---

## Findings below 80 confidence (build_notes only — no Builder loop)

- **Finding 10** (confidence 78): conflict-merge 5-step list compressed to one sentence — step 5 (local pull) is implicit. Not a blocking issue.

---

## Security: PASS
All credential file paths preserved. No secrets exposed. Runbook guidance intact.

## Cross-references: PASS
No broken heading references. Pointer files resolve to real paths.

## Code block completeness: PASS
All fenced code blocks in both docs close correctly. No truncated content.
