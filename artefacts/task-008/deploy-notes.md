# Deploy Notes — task-008: Laptop Capture

**Script**: `scripts/capture.py`
**Requires**: Python 3.10+ (stdlib only — no pip installs needed)

---

## Setup (one-time, per laptop)

### 1. Create a GitHub PAT

Go to https://github.com/settings/tokens → "Fine-grained tokens" → New token:
- Repository access: `micmaas2/project-manager` + `micmaas2/pensieve`
- Permissions: Contents → Read and write

Copy the token. **Store it securely** (e.g. macOS Keychain, pass, or 1Password).

### 2. Add to shell profile

```bash
# ~/.zshrc or ~/.bashrc
export GITHUB_TOKEN="ghp_your_token_here"
```

Then reload: `source ~/.zshrc`

### 3. Add a shell alias (optional, for convenience)

```bash
# ~/.zshrc
alias capture='python3 /path/to/project_manager/scripts/capture.py'
```

---

## Usage

### Backlog item (picked up by PM at next session start)

```bash
# Basic
python3 scripts/capture.py backlog "Investigate rate limiting on n8n webhook"

# Dry-run (shows what would be committed, makes one read call to GitHub)
python3 scripts/capture.py backlog "Test item" --dry-run
```

The item lands in `tasks/telegram-inbox.md` on `main` — same file that the Telegram
n8n workflow commits to. PM processes it at the start of the next session.

### Pensieve note (article / URL capture)

```bash
# URL + optional note
python3 scripts/capture.py pensieve "Great article on RAG chunking" \
    --url "https://example.com/article" \
    --note "Key insight: 256 token chunks outperform 512 for retrieval precision"

# Quick note (no URL)
python3 scripts/capture.py pensieve "Idea: use vector embeddings for backlog dedup"
```

The note lands in `captures/YYYY-MM-DD-<slug>.md` in the `micmaas2/pensieve` repo
on `main`. It does **not** automatically sync to the Pi4 Obsidian vault — a future
webhook (task-009 or a Pi4-side sync) will handle that path.

---

## What gets created

### Backlog entry (telegram-inbox.md)

```
- 2026-04-07: Investigate rate limiting on n8n webhook
```

### Pensieve note (captures/2026-04-07-great-article-on-rag.md)

```markdown
---
title: "Great article on RAG chunking"
date: 2026-04-07
source: laptop-capture
url: "https://example.com/article"
tags: []
---

Key insight: 256 token chunks outperform 512 for retrieval precision
```

---

## Demo script (end-to-end)

```bash
# 1. Set token
export GITHUB_TOKEN="ghp_..."

# 2. Dry-run first
python3 scripts/capture.py backlog "Demo: laptop capture test" --dry-run

# 3. Live capture
python3 scripts/capture.py backlog "Demo: laptop capture test"

# 4. Verify in GitHub
open https://github.com/micmaas2/project-manager/blob/main/tasks/telegram-inbox.md
```

---

## Limitations

- **Pensieve → vault sync**: Notes land in the `micmaas2/pensieve` GitHub repo, not
  directly in the Pi4 Obsidian vault. Vault sync requires either a Pi4-side git pull
  cron or the n8n webhook path (task-009).
- **Dry-run makes one read call**: The dry-run flag skips writes but still reads the
  current file from GitHub to show the full diff. Requires `GITHUB_TOKEN` to be set.
- **No offline queue**: If GitHub is unreachable the script fails; there is no local
  draft queue. For offline use, write the item to a local file and run the script when
  back online.
