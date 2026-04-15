## Proposal 1: Time-to-Restore in Secret Rotation Runbook Rollback Sections

**Target file**: CLAUDE.md (new entry in secret-rotation-tasks section or addition to existing runbook guidelines)

**Change**: Add a requirement to the MVP template for any secret-rotation or credential-rotation task:
- Rollback/recovery section must include an explicit "Estimated time-to-restore: N-M minutes" statement
- The estimate should account for manual steps (e.g., GitHub UI, credential re-entry) and cover worst-case timing
- Include a brief explanation of what contributes to the estimate ("new token generation + 2 config updates")

**Rationale**: code-quality-reviewer identified M-1 in task-032: the rollback section warned of "no automatic rollback" but omitted quantified downtime. An operator under pressure deciding whether to escalate needs this estimate. The fix was simple (one added sentence) but this is a pattern that should be baked into the template for all future credential-rotation tasks to prevent re-discovery.

**Status**: REQUIRES_HUMAN_APPROVAL

---

## Proposal 2: Document Preferred Format in All Code Examples (Not Just Text)

**Target file**: CLAUDE.md (new pattern in code-quality guidelines or Builder acceptance criteria)

**Change**: When a runbook or guide recommends one option as "preferred" (e.g., "Fine-grained PATs are preferred"), ALL code snippets and examples in that document must illustrate the preferred form first. If multiple forms are valid, the comment or surrounding text must explicitly note both.

**Rationale**: code-quality-reviewer flagged L-1: task-032 recommends fine-grained PATs as preferred but Step 2's bash snippet only shows classic format (`ghp_<YOUR_NEW_TOKEN>`). A first-time operator following the "preferred" recommendation could be confused by an example that doesn't match. This is low-severity but recurs in any multi-option documentation. Baking this into the Builder/Reviewer checklist prevents the gap.

**Status**: REQUIRES_HUMAN_APPROVAL

---

## Proposal 3: Terminal History Hygiene Warning for Sensitive Command Verification

**Target file**: CLAUDE.md (new pattern in security guidelines for ops runbooks)

**Change**: For any runbook step that reads a secret file for verification (e.g., `cat /opt/n8n/github-pat`), add an explicit note:
- Document the safe form (with the pipe or head command that leaks minimal info)
- Include a warning: "Never run `[command without pipe]` on a shared or recorded terminal; the full secret could be exposed in shell history or screen-share."

**Rationale**: code-quality-reviewer noted L-2: Step 4c's safe command (`head -c 4`) is correct, but the surrounding verification section doesn't warn against accidentally running the full command without the pipe. While low-severity (operator must explicitly remove the safety), this is a good operational hygiene pattern for any secret-verification step. Including it in the template prevents silent exposure windows.

**Status**: REQUIRES_HUMAN_APPROVAL
