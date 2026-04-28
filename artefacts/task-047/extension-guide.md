# Extension Guide: security-guidance PreToolUse Hook

## Overview

The `security-guidance` hook is a PreToolUse hook that intercepts every `Edit`, `Write`, and `MultiEdit` tool call in Claude Code. Before any file write executes, it checks the target file path and the content being written against a set of known-dangerous patterns and blocks the write with a warning if a match is found.

### Patterns blocked

| Pattern | Risk |
|---------|------|
| `eval(` | Arbitrary code execution |
| `os.system` / `from os import system` | Command injection |
| `pickle` | Arbitrary code execution via deserialization |
| `.innerHTML =` / `.innerHTML=` | XSS |
| `dangerouslySetInnerHTML` | XSS (React) |
| `document.write` | XSS |
| `new Function` | Code injection |
| `child_process.exec` / `execSync` | Command injection (Node.js) |
| `.github/workflows/*.yml` path | GitHub Actions command injection |

The hook blocks on first occurrence per session per file, then allows the same pattern through (to avoid blocking legitimate code reviews or fixes). Set `ENABLE_SECURITY_REMINDER=0` to disable entirely for a session.

---

## Deploying to project_manager (already done)

`/opt/claude/project_manager/.claude/settings.json` already contains the hook. No further action needed.

---

## The JSON snippet to add to any project settings.json

Add the `hooks` key to an existing `settings.json`, or create a new one with this content:

```json
{
  "permissions": {
    "defaultMode": "plan"
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /root/.claude/plugins/marketplaces/claude-plugins-official/plugins/security-guidance/hooks/security_reminder_hook.py"
          }
        ]
      }
    ]
  }
}
```

If the project's settings.json already has other keys, add only the `hooks` block — preserve existing `permissions`, `enabledPlugins`, etc.

---

## Deploying to pensieve (`/opt/claude/pensieve`)

The current `/opt/claude/pensieve/.claude/settings.json` only has `defaultMode: plan`. Add the hooks block from the snippet above, then commit:

```bash
# Edit the file
# Then commit on a feature branch
git -C /opt/claude/pensieve checkout -b feature/security-hook
git -C /opt/claude/pensieve add .claude/settings.json
git -C /opt/claude/pensieve commit -m "[AGENT] install security-guidance PreToolUse hook"
```

Verify: open a Claude Code session in `/opt/claude/pensieve` and attempt to write a file containing `os.system(` — the hook should block it with a warning before the write executes.

---

## Deploying to MAS (`/opt/mas` on Pi4)

MAS runs on Pi4 at `192.168.1.10`. The hook script must exist on Pi4 at the same path as on the local host.

### Step 1 — Check if the plugin exists on Pi4

```bash
ssh pi4 "ls /root/.claude/plugins/marketplaces/claude-plugins-official/plugins/security-guidance/hooks/ 2>/dev/null || echo MISSING"
```

If `MISSING`, copy the hook script to Pi4:

```bash
ssh pi4 "mkdir -p /root/.claude/plugins/marketplaces/claude-plugins-official/plugins/security-guidance/hooks/"
scp \
  /root/.claude/plugins/marketplaces/claude-plugins-official/plugins/security-guidance/hooks/security_reminder_hook.py \
  pi4:/root/.claude/plugins/marketplaces/claude-plugins-official/plugins/security-guidance/hooks/security_reminder_hook.py
```

### Step 2 — Create or update MAS settings.json on Pi4

```bash
# Check current contents
ssh pi4 "cat /opt/mas/.claude/settings.json 2>/dev/null || echo MISSING"
```

If missing, create it:

```bash
ssh pi4 "mkdir -p /opt/mas/.claude"
# Then write the JSON snippet from the section above to /opt/mas/.claude/settings.json
# using python3 or a heredoc to avoid shell quoting issues with nested JSON
```

If it already has content, merge the `hooks` key using Python to avoid JSON corruption:

```bash
ssh pi4 "python3 -c \"
import json, pathlib
p = pathlib.Path('/opt/mas/.claude/settings.json')
d = json.loads(p.read_text()) if p.exists() else {}
d.setdefault('hooks', {}).setdefault('PreToolUse', [])
entry = {
  'matcher': 'Edit|Write|MultiEdit',
  'hooks': [{'type': 'command', 'command': 'python3 /root/.claude/plugins/marketplaces/claude-plugins-official/plugins/security-guidance/hooks/security_reminder_hook.py'}]
}
if entry not in d['hooks']['PreToolUse']:
    d['hooks']['PreToolUse'].append(entry)
p.write_text(json.dumps(d, indent=2))
print('Done')
\""
```

### Step 3 — Commit on MAS repo

The MAS repo is at `micmaas2/mas_personal_assistant` (private). Commit via SSH on Pi4:

```bash
ssh pi4 "cd /opt/mas && git checkout -b feature/security-hook && git add .claude/settings.json && git commit -m '[AGENT] install security-guidance PreToolUse hook'"
```

### Step 4 — Verify on Pi4

```bash
ssh pi4 "printf '{\"session_id\":\"t1\",\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"/tmp/test.py\",\"content\":\"import os\\nos.system(\\\\\"id\\\\\")\"}}' | python3 /root/.claude/plugins/marketplaces/claude-plugins-official/plugins/security-guidance/hooks/security_reminder_hook.py; echo \"Exit: \$?\""
# Expected: exit 2 + os_system_injection warning on stderr
```

---

## Testing After Deployment (local)

Use the following stdin-based test to confirm the hook is wired correctly without needing a full Claude Code session:

```bash
HOOK="/root/.claude/plugins/marketplaces/claude-plugins-official/plugins/security-guidance/hooks/security_reminder_hook.py"

# Should BLOCK (exit 2) — os.system pattern
printf '{"session_id":"t1","tool_name":"Write","tool_input":{"file_path":"/tmp/t.py","content":"os.system(\"id\")"}}' \
  | python3 "$HOOK"
echo "Expected exit 2, got: $?"

# Should ALLOW (exit 0) — clean content
printf '{"session_id":"t2","tool_name":"Write","tool_input":{"file_path":"/tmp/t.py","content":"x = 1"}}' \
  | python3 "$HOOK"
echo "Expected exit 0, got: $?"
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Hook not firing | settings.json not found or malformed JSON | Run `python3 -m json.tool .claude/settings.json` to validate |
| Hook fires but does not block | Script exits 0 on error (JSON parse failure) | Check `/tmp/security-warnings-log.txt` |
| Same warning shown twice | State file missing or unwritable | Check `~/.claude/security_warnings_state_*.json` permissions |
| False positive on legitimate code | Pattern too broad (e.g. `eval(` matching other names) | Set `ENABLE_SECURITY_REMINDER=0` for that session |

Hook debug log: `/tmp/security-warnings-log.txt` (written on errors only).

**Hook not firing after plugin update**: the absolute plugin path (`/root/.claude/plugins/.../security_reminder_hook.py`) breaks if the plugin directory is moved, reinstalled, or updated. Use the local project copy (`hooks/security_reminder_hook.py`) instead — it is stable across plugin updates. Copy with:

```bash
cp /root/.claude/plugins/marketplaces/claude-plugins-official/plugins/security-guidance/hooks/security_reminder_hook.py hooks/security_reminder_hook.py
```

Then update `settings.json` to use the local path:

```json
"command": "python3 /opt/claude/project_manager/hooks/security_reminder_hook.py"
```

**False positives on `.execute(` SQL calls or function names containing `exec(`**: the upstream hook includes a broad `exec(` substring in the `child_process_exec` pattern. The local copy in this repo removes it, keeping only the more specific `child_process.exec` and `execSync(` patterns. If you see unexpected blocks, verify you are using the patched local copy at `hooks/security_reminder_hook.py`.
