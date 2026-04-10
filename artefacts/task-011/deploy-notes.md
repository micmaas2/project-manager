# Deploy Notes — pensieve-sync.sh

Task: task-011  
Target host: Pi4 (192.168.1.10, ssh alias `pi4`)  
Script destination: `/usr/local/bin/pensieve-sync.sh`  
Log file: `/var/log/pensieve-sync.log`

---

## Prerequisites

- SSH key on Pi4 has read access to `git@github.com:micmaas2/pensieve.git`
- You can verify with: `ssh pi4 "ssh -T git@github.com"` — expect `Hi micmaas2!...`
- `git` >= 2.0 installed on Pi4: `ssh pi4 "git --version"`

### Deploy key for cron

Cron runs without an SSH agent, so the script exports `GIT_SSH_COMMAND` pointing to the
deploy key. The default path in the script is `/root/.ssh/id_rsa`. **Verify or update this**
before deploying:

```bash
ssh pi4 "ls -la /root/.ssh/id_rsa"
```

If the key lives at a different path (e.g. `/root/.ssh/pensieve_deploy_key`), edit the
`GIT_SSH_COMMAND` line in the script **before** copying it to Pi4:

```bash
# In pensieve-sync.sh, update:
export GIT_SSH_COMMAND="ssh -i /root/.ssh/pensieve_deploy_key -o StrictHostKeyChecking=no"
```

**Alternative — `/root/.ssh/config`**: if you prefer not to hardcode a path in the script,
configure the SSH client on Pi4 instead and remove the `GIT_SSH_COMMAND` export from the
script entirely:

```bash
ssh pi4 "sudo tee -a /root/.ssh/config > /dev/null <<'EOF'

Host github.com
    IdentityFile /root/.ssh/pensieve_deploy_key
    StrictHostKeyChecking no
EOF"
```

---

## Step 1 — Initial clone (skip if already cloned)

Check whether the vault is already a cloned pensieve repo:

```bash
ssh pi4 "ls /opt/obsidian-vault/.git 2>/dev/null && git -C /opt/obsidian-vault remote get-url origin || echo NOT_CLONED"
```

If NOT_CLONED, run the initial clone:

```bash
ssh pi4 "sudo git clone git@github.com:micmaas2/pensieve.git /opt/obsidian-vault"
```

If the directory already exists but is not a git repo (e.g. Obsidian created it empty):

```bash
ssh pi4 "sudo git -C /opt/obsidian-vault init && \
  sudo git -C /opt/obsidian-vault remote add origin git@github.com:micmaas2/pensieve.git && \
  sudo git -C /opt/obsidian-vault fetch origin main && \
  sudo git -C /opt/obsidian-vault checkout -b main --track origin/main"
```

Confirm the clone succeeded:

```bash
ssh pi4 "git -C /opt/obsidian-vault log --oneline -5"
```

---

## Step 2 — Create the log file with correct permissions

The cron job runs as root (or the deploying user). Pre-create the log file to
avoid permission errors on first run:

```bash
ssh pi4 "sudo touch /var/log/pensieve-sync.log && sudo chmod 644 /var/log/pensieve-sync.log"
```

---

## Step 3 — Copy the script to Pi4

From the build host (project_manager working directory):

```bash
scp artefacts/task-011/pensieve-sync.sh pi4:/tmp/pensieve-sync.sh
ssh pi4 "sudo cp /tmp/pensieve-sync.sh /usr/local/bin/pensieve-sync.sh && \
         sudo chmod +x /usr/local/bin/pensieve-sync.sh && \
         sudo chown root:root /usr/local/bin/pensieve-sync.sh"
```

---

## Step 4 — Add cron entry

Open root's crontab on Pi4:

```bash
ssh pi4 "sudo crontab -e"
```

Add this line:

```
*/15 * * * * /usr/local/bin/pensieve-sync.sh
```

Alternatively, install non-interactively:

```bash
ssh pi4 "( sudo crontab -l 2>/dev/null; echo '*/15 * * * * /usr/local/bin/pensieve-sync.sh' ) | sudo crontab -"
```

Confirm the entry was added:

```bash
ssh pi4 "sudo crontab -l | grep pensieve-sync"
```

---

## Step 5 — Configure log rotation (required)

Unbounded log growth will fill the filesystem over time. This step is **required**, not
optional. Add the logrotate config before enabling the cron job:

```bash
ssh pi4 "sudo tee /etc/logrotate.d/pensieve-sync > /dev/null <<'EOF'
/var/log/pensieve-sync.log {
    weekly
    rotate 4
    compress
    missingok
    notifempty
    copytruncate
}
EOF"
```

`copytruncate` is required so logrotate can rotate the file while the script may be writing to
it — it copies the current log to the rotated file then truncates the original in place,
avoiding a broken file descriptor in a concurrently running instance.

Verify the config is valid:

```bash
ssh pi4 "sudo logrotate --debug /etc/logrotate.d/pensieve-sync"
```

---

## Step 6 — Verify first run

Run the script manually as root to confirm it works before waiting for cron:

```bash
ssh pi4 "sudo /usr/local/bin/pensieve-sync.sh && echo EXIT_OK || echo EXIT_FAIL"
```

Check the log for a success or "already up to date" entry:

```bash
ssh pi4 "tail -20 /var/log/pensieve-sync.log"
```

Expected log output (already up to date):

```
[2026-04-10T09:30:00Z] [INFO] Starting sync: /opt/obsidian-vault <- origin/main
[2026-04-10T09:30:01Z] [GIT] From github.com:micmaas2/pensieve
[2026-04-10T09:30:01Z] [GIT]    abc1234..def5678  main -> origin/main
[2026-04-10T09:30:01Z] [INFO] Already up to date (HEAD=abc12345). Nothing to do.
```

Or with new commits:

```
[2026-04-10T09:30:01Z] [INFO] Sync complete: pulled 3 new commit(s). abc12345..def56789
```

---

## Rollback

To disable the sync:

```bash
# Remove cron entry
ssh pi4 "sudo crontab -l | grep -v pensieve-sync | sudo crontab -"

# Optionally remove the script
ssh pi4 "sudo rm /usr/local/bin/pensieve-sync.sh"
```

No vault data is modified destructively by the sync — it only fast-forwards
the local HEAD. The vault directory is left intact on rollback.

