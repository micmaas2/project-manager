# Maintenance Schedule

Cross-project recurring activities tracked by ProjectManager.
**Owner**: Michel Maas
**Last updated**: 2026-04-05

---

## How to use this document

- **Status**: `ok` | `due` | `overdue` | `blocked` | `auto` (runs automatically)
- **Last run** / **Next due**: update after each run
- PM reads this at planning sessions and flags overdue items
- To run a Pi5 activity: execute the command on Pi5 directly
- To run a Pi4 activity: `ssh pi4 <command>` (requires SSH fix — see Blocked section)

---

## Weekly

| # | Activity | Project | Command / Action | Last run | Next due | Status |
|---|---|---|---|---|---|---|
| W-1 | Audit log review | project_manager | `bash artefacts/task-002/audit-summary.sh` | 2026-04-05 | 2026-04-12 | ok |
| W-2 | Queue status check | project_manager | `bash artefacts/task-001/queue-status.sh` | 2026-04-05 | 2026-04-12 | ok |
| W-3 | HA automation health check | pi-homelab | HA UI → Settings → Automations → check for errors/disabled | 2025-11-29 | 2026-04-12 | due |
| W-4 | Pensieve workflow health | pensieve | n8n UI → check all active workflows ran without errors | — | 2026-04-12 | due |

---

## Monthly

| # | Activity | Project | Command / Action | Last run | Next due | Status |
|---|---|---|---|---|---|---|
| M-1 | Pi 5 full patch run | pi-homelab | `sudo bash /opt/claude/pi-homelab/scripts/patch-pi5.sh` | 2026-03-12 | 2026-04-12 | due |
| M-2 | Pi 4 full patch run | pi-homelab | `bash /opt/claude/pi-homelab/scripts/patch-pi4.sh` (from Pi5) | 2026-03-12 | 2026-04-12 | blocked |
| M-3 | Pi 4 Docker stack check | pi-homelab | `ssh pi4 'docker ps; docker stats --no-stream'` | 2026-03-12 | 2026-04-12 | blocked |
| M-4 | Let's Encrypt cert expiry check | pi-homelab | `ssh pi4 'sudo certbot certificates'` or check Nginx PM UI | — | 2026-04-12 | blocked |
| M-5 | fail2ban review (Pi 4) | pi-homelab | `ssh pi4 'sudo fail2ban-client status sshd'` | — | 2026-04-12 | blocked |
| M-6 | Backlog / PI planning session | project_manager | PM planning session — review `tasks/backlog.md`, reprioritise | 2026-04-05 | 2026-05-05 | ok |
| M-7 | HA backup verification | pi-homelab | HA UI → Settings → System → Backups — confirm latest backup exists | — | 2026-04-12 | due |
| M-8 | UniFi controller update check | pi-homelab | UniFi UI → Settings → Firmware Updates | — | 2026-04-12 | due |
| M-9 | Pensieve capture stats | pensieve | Check n8n execution logs for last 30 days — count captures, errors | — | 2026-05-05 | due |
| M-10 | Genealogie dependency check | genealogie | `pip list --outdated` in `/opt/claude/genealogie/genealogy-mas/` | — | 2026-05-05 | due |

---

## Quarterly

| # | Activity | Project | Command / Action | Last run | Next due | Status |
|---|---|---|---|---|---|---|
| Q-1 | Pi 4 Docker compose security review | pi-homelab | Review all `/opt/*/docker-compose.yml` on Pi4 — ports, root containers, secrets | 2026-03-12 | 2026-06-05 | ok |
| Q-2 | Pi security hardening review | pi-homelab | Re-check SSH config, UFW rules, sudoers, fail2ban config on both Pis | — | 2026-07-05 | due |
| Q-3 | CCAS inventory review | ccas | Review `ccas-inventory/environments/development/` for stale host_vars | — | 2026-07-05 | due |
| Q-4 | SSH key audit | all | List all `~/.ssh/authorized_keys` on Pi4 + Pi5; remove stale entries | — | 2026-07-05 | due |
| Q-5 | EEPROM firmware check (Pi 4 + Pi 5) | pi-homelab | Pi5: `sudo rpi-eeprom-update` / Pi4: `ssh pi4 sudo rpi-eeprom-update` | 2026-03-12 | 2026-06-05 | ok |
| Q-6 | GitLab CE version check (Pi 4) | pi-homelab | Check gitlab/gitlab-ce current vs latest; assess upgrade | 2026-03-12 | 2026-06-05 | ok |
| Q-7 | Grafana version check (Pi 4) | pi-homelab | Check grafana/grafana current vs latest | 2026-03-12 | 2026-06-05 | ok |
| Q-8 | Pensieve dependency audit | pensieve | Review n8n version, node packages; check for deprecation notices | — | 2026-07-05 | due |

---

## Annual / Major Upgrades

| # | Activity | Project | Notes | Last done | Next planned | Status |
|---|---|---|---|---|---|---|
| A-1 | Debian OS major upgrade | pi-homelab | Pi 4: bookworm → trixie (when stable + HA tested). Pi 5: already trixie. | — | 2026-Q4 | planned |
| A-2 | SSH key rotation | all | Generate new keys for all Pi access; revoke old | — | 2026-Q4 | planned |
| A-3 | Home Assistant major version review | pi-homelab | Check HA breaking changes; test automations after | 2025-11 | 2026-Q2 | due |
| A-4 | Docker python:3.11-slim migration | pi-homelab | Migrate `python:3.11-slim-bullseye` → `bookworm` (BL-014) | — | 2026-Q2 | due |

---

## One-Time Pending (Blocked or Awaiting)

| # | Activity | Project | Blocked on | Action needed | Backlog ref |
|---|---|---|---|---|---|
| P-1 | Fix Pi4 SSH from work laptop | pi-homelab | User action on work laptop | `ssh -o IdentitiesOnly=yes -i ~/.ssh/<key> pi@80.115.166.2` — check which key with `ls ~/.ssh/id_*` on work laptop | BL-026 |
| P-2 | Pi 4 passwd hardening + remove nopasswd sudoers | pi-homelab | User: SSH to Pi4 and run `sudo passwd pi` + `sudo rm /etc/sudoers.d/010_pi-nopasswd` | Requires P-1 first | BL-012 |
| P-3 | Pi 5 security prereqs + apply-hardening.sh | pi-homelab | User: `ssh-copy-id pi@<pi5-ip>` from each laptop, then `sudo passwd pi`, remove nopasswd sudoers, then `sudo bash /opt/claude/pi-homelab/pi5/apply-hardening.sh` | Can be done now (no SSH needed from laptop) | BL-013 |
| P-4 | Pensieve: activate Gmail capture in n8n | pensieve | User: import `workflows/gmail-capture.json` via n8n UI and activate | — | BL-015 |
| P-5 | Pensieve: improved summaries + tagging + folder structure | pensieve | Ready to queue — awaiting task planning | — | BL-023/024/025 |

---

## Automation Status (auto-managed, no manual action needed)

| Activity | Project | Mechanism | Notes |
|---|---|---|---|
| Outdoor lighting on/off | pi-homelab | HA sun trigger | Sunrise/sunset daily |
| Air purifier mode | pi-homelab | HA state trigger + time | PM2.5, allergen, TV, time-based |
| Sonos volume | pi-homelab | HA state trigger | Source-based volume matrix |
| Stairway lighting | pi-homelab | HA time trigger | 19:00 on / 08:00 off |
| Virtual battery simulation | pi-homelab | HA numeric state trigger | Continuous charge/discharge tracking |
| SlimmeLezer monitoring | pi-homelab | HA state trigger | 5-min offline alert |
| Pensieve Telegram capture | pensieve | n8n webhook | Active (n8n on Pi4) |
| Let's Encrypt renewal | pi-homelab | Nginx Proxy Manager | Auto-renews 30 days before expiry |
| Git branch protection | project_manager | pre-commit hook | Active on all commits |

---

## Patch Run Checklist

When running a patch (M-1 or M-2), follow this sequence:
1. `--dry-run` first to see what will change
2. Full run (without `--dry-run`)
3. Check output for `Reboot required: true`
4. If reboot needed: schedule a low-traffic window and run `sudo reboot` (Pi5) or `ssh pi4 sudo reboot` (Pi4)
5. Verify all Docker stacks came back up after reboot: `docker ps`
6. Check HA is healthy: open `ha.femic.nl` or local IP
7. Update **Last run** and **Next due** columns in this file
