# task-047: Build Notes — security-guidance PreToolUse Hook

## What Was Installed

**Hook**: `security-guidance` PreToolUse hook from the official Anthropic plugin marketplace.
**Source**: `/root/.claude/plugins/marketplaces/claude-plugins-official/plugins/security-guidance/hooks/security_reminder_hook.py`
**Registered in**: `/opt/claude/project_manager/.claude/settings.json`

### Hook registration (settings.json snippet)

```json
{
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

The hook fires on every `Edit`, `Write`, or `MultiEdit` tool call before the write is executed.

---

## How It Works

The hook reads the tool's JSON input from stdin and checks two things:
1. **File path** — for path-based rules (e.g. `.github/workflows/*.yml` triggers GitHub Actions injection warning)
2. **Content being written** — `new_string` for Edit/MultiEdit, `content` for Write

When a pattern is matched, the hook:
- Outputs a warning message to `stderr`
- Exits with code `2` — which tells Claude Code to **block the tool call** and show the message

The hook is session-aware: each warning is shown only once per `(file_path, rule_name)` pair per session. State is persisted in `~/.claude/security_warnings_state_<session_id>.json`.

Disable the hook per-session by setting `ENABLE_SECURITY_REMINDER=0` in the environment.

---

## Patterns Blocked

| Rule Name | Pattern Substring | Trigger |
|-----------|-------------------|---------|
| `github_actions_workflow` | Path matches `.github/workflows/*.yml` | GitHub Actions command injection warning |
| `child_process_exec` | `child_process.exec`, `execSync(` | Block + recommend safe alternative |
| `new_function_injection` | `new Function` | Block + warn code injection risk |
| `eval_injection` | `eval(` | Block + warn arbitrary code execution |
| `react_dangerously_set_html` | `dangerouslySetInnerHTML` | Block + warn XSS |
| `document_write_xss` | `document.write` | Block + warn XSS |
| `innerHTML_xss` | `.innerHTML =` or `.innerHTML=` | Block + warn XSS |
| `pickle_deserialization` | `pickle` | Block + warn arbitrary code execution |
| `os_system_injection` | `os.system`, `from os import system` | Block + warn command injection |

**Note**: `eval(` matches both Python's eval() and JavaScript's eval(). Variable names like `eval_something` may produce false positives — acceptable given the low base rate in this codebase.

---

## Verification — CONFIRMED ACTIVE

The hook was confirmed active during installation. When the Write tool was called with content containing `exec(` in the build notes text, the hook fired immediately and blocked the write with the `child_process_exec` warning.

**Exit code semantics**:
- `0` — pattern not found, tool call allowed to proceed
- `2` — pattern matched, tool call blocked, warning shown to Claude

**Manual test via stdin**:

```bash
# Test eval_injection pattern — expects exit code 2 + stderr warning
echo '{"session_id":"test","tool_name":"Write","tool_input":{"file_path":"/tmp/test.py","content":"x = eval_call(\"1+1\")"}}' \
  | python3 /path/to/security_reminder_hook.py

# Test clean file — expects exit code 0
echo '{"session_id":"test4","tool_name":"Write","tool_input":{"file_path":"/tmp/clean.py","content":"x = 1 + 1"}}' \
  | python3 /path/to/security_reminder_hook.py
```

Replace `/path/to/security_reminder_hook.py` with the absolute path shown in the installation section.

---

## Important Notes

- The hook uses an **absolute path** to the plugin script. This is intentional — `${CLAUDE_PLUGIN_ROOT}` is only expanded when a plugin is registered via `enabledPlugins`, not when registering hooks directly in settings.json.
- The hook blocks on first match per session per file, then allows the same pattern in the same file (deduplicated by `file_path + rule_name`).
- Debug log written to `/tmp/security-warnings-log.txt` for troubleshooting.
- The `child_process_exec` pattern includes `exec(` as a standalone substring — this can match Python function calls containing that string. Review the hook source if false positives appear frequently.
