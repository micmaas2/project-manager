---
task: task-032
reviewer: code-quality-reviewer (Sonnet 4.6)
reviewed_file: /opt/claude/pensieve/docs/pat-rotation.md
date: 2026-04-15
verdict: PASS
---

# Code Quality Review — PAT Rotation Runbook

## Verdict: PASS

No blocking issues found. One medium and two low findings noted below.

---

## Security Scan — PAT Values

Pattern checked: `ghp_[a-zA-Z0-9]{36}` and `github_pat_[a-zA-Z0-9_]{82}`

Result: **No real PAT values present.** All token references in the document use placeholder form (`ghp_<YOUR_NEW_TOKEN>`). No HIGH finding.

---

## Findings

### MEDIUM

**M-1: Rollback section states "there is no automatic rollback" but does not quantify downtime**

- Location: `## Rollback`, step 2
- Issue: The rollback section correctly warns that once the old PAT is revoked, recovery requires generating a new token — there is no instant restore path. However, it does not state the expected time-to-restore (a manual GitHub UI operation + two config updates). An operator under pressure needs a worst-case estimate to decide whether to page someone.
- Recommendation: Add one sentence, e.g.: "Estimated time-to-restore: 5–10 minutes (new PAT generation + Steps 2–3). No automated fallback exists."

---

### LOW

**L-1: Step 2 (PAT file update) uses a placeholder token format that only covers classic PATs**

- Location: `### Step 2`, bash snippet — `echo "ghp_<YOUR_NEW_TOKEN>"`
- Issue: The `ghp_` prefix applies to classic PATs. Fine-grained PATs use the `github_pat_` prefix. The runbook already recommends fine-grained PATs as preferred (Step 1), but the bash example only illustrates the classic format. A first-time operator following the recommended path may be confused.
- Recommendation: Update the comment to: `# Replace with your token (ghp_... for classic, github_pat_... for fine-grained)` and add a second example line showing the fine-grained form.

**L-2: Step 4c verification command leaks token prefix to shell history but not the full token**

- Location: `### 4c`, bash command — `sudo cat /opt/n8n/github-pat | head -c 4`
- Issue: `head -c 4` is safe (shows only `ghp_` or `gith`), but the surrounding verification step does not warn against running `sudo cat /opt/n8n/github-pat` without the pipe — which would print the full token to a terminal with potential shell history or screen-share exposure. This is a low risk since the operator must deliberately remove the pipe, but a brief note would reinforce good hygiene.
- Recommendation: Add a note: "Never run `sudo cat /opt/n8n/github-pat` without the `head -c 4` pipe on a shared or recorded terminal."

---

## Completeness Assessment

| Required step | Present | Notes |
|---|---|---|
| Create new PAT | Yes | Step 1 — covers both fine-grained and classic paths |
| Update n8n credential | Yes | Step 3 — correct `token ` prefix explicitly documented |
| Revoke old PAT | Yes | Step 4 — with clear ordering note (revoke after verify) |
| Verify | Yes | Steps 4a (n8n manual test), 4b (E2E Telegram), 4c (PAT file) |

All four required rotation steps are present and in the correct order.

---

## Accuracy Assessment

**n8n credential `token ` prefix**: Step 3 correctly specifies `token ghp_<YOUR_NEW_TOKEN>` as the credential value and includes an explicit note that the `token ` prefix (with trailing space) is required. This matches the GitHub API authentication format for PATs. The troubleshooting table also reinforces this at the 401 row.

**Credential type**: Correctly identified as HTTP Header Auth with header name `Authorization`. This matches the CLAUDE.md documentation of the n8n credential setup.

**Workflow node names**: `GET telegram-inbox.md from GitHub` and `PUT telegram-inbox.md to GitHub` are referenced consistently across Steps 4a and the Affected Systems table.

**URL in troubleshooting table**: `https://api.github.com/repos/micmaas2/project-manager/contents/tasks/telegram-inbox.md` is the correct GitHub Contents API path for this repository and file.

No accuracy issues found.

---

## Positive Observations

- The ordering of revoke-after-verify (Step 4 placed after verification) is correct and reduces the window of outage risk. The rollback section reinforces this with "do Steps 1–3 before revoking."
- The troubleshooting table covers all realistic HTTP status codes (401, 403, 404) with distinct causes and targeted fixes — well-structured for an on-call operator.
- Fine-grained PATs are recommended as the preferred path with clear rationale ("limits blast radius to a single repo").
- Pre-rotation checklist is specific and actionable — no vague "ensure access" items.
- Quarterly reminder includes a concrete backlog integration path (BL item 2 weeks before expiry).
