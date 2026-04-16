# task-033 — Build Notes

## Root Cause

**The n8n → Pi4 vault write pipeline was functioning correctly throughout the reported gap period (2026-04-09 onwards).**

Files were present on disk at `/opt/obsidian-vault/` on Pi4, including entries from 2026-04-10 through 2026-04-16. The missing-file symptom was an **Obsidian app sync issue**: the Obsidian mobile/desktop client lost its connection to the vault (iCloud/remote sync desync) and was not reflecting files that existed on Pi4.

**Fix applied**: User deleted the vault from Obsidian app and re-added it, triggering a full resync. New files immediately appeared.

## Evidence

Post-resync vault check:
```
find /opt/obsidian-vault -name '*.md' -newer /opt/obsidian-vault -maxdepth 3 | sort | tail -10
/opt/obsidian-vault/Ideas/Ai/2026-04-13-claude-code-met-lokaal-model-op-eigen-server.md
/opt/obsidian-vault/Inbox/Productivity/2026-04-16-backlog.md
/opt/obsidian-vault/Links/Ai/2026-04-10-rtk-90-token-reduction-for-claude-code.md
/opt/obsidian-vault/Links/Ai/2026-04-15-master-claude-chat-cowork-and-code.md
/opt/obsidian-vault/Links/Ai/2026-04-15-playwright-mcp-server-integration.md
/opt/obsidian-vault/Links/Ai/2026-04-16-claude-code-optimization-repository.md
/opt/obsidian-vault/Links/Ai/2026-04-16-claude-code-optimization-repository-with-agents.md
/opt/obsidian-vault/Links/Research/2026-04-14-ksu-onder-de-bogen-aura-library.md
/opt/obsidian-vault/Research/Ai/2026-04-14-claudemd-karpathy-derived-llm-coding-principles.md
```

Files spanning the full reported gap period are present. n8n sub-workflow (task-029) continues to write correctly.

## No Code Changes Required

No n8n workflow edits were made. No path guards or sanitization were altered. Pipeline is intact.

## Recommendation

When "files missing from Obsidian" is reported again, first check Pi4 vault directly via SSH before assuming an n8n failure:
```bash
ssh pi4 "find /opt/obsidian-vault -name '*.md' -newer /opt/obsidian-vault -maxdepth 3 | sort | tail -5"
```
If files are present on Pi4 but not in the app → Obsidian sync issue. Fix: delete + re-add vault in app.
