#!/usr/bin/env python3
"""
task-046: One-time setup script for Uptime-Kuma monitoring of MAS /health endpoint.

Configures:
1. An admin account (first-time setup only)
2. A Telegram notification channel using the MAS bot
3. An HTTP monitor for the /api/health endpoint

Usage:
    python3 setup-uptime-kuma.py

Prerequisites:
    pip3 install uptime-kuma-api --break-system-packages
    Uptime-Kuma running on http://localhost:3001

Note: run once; subsequent runs will detect existing monitors/notifications.
"""

import sys
import os
from uptime_kuma_api import UptimeKumaApi, MonitorType, NotificationType

KUMA_URL = "http://localhost:3001"
ADMIN_USER = "admin"
ADMIN_PASS = os.environ.get("KUMA_ADMIN_PASS", "changeme123!")

# From /opt/mas/.env
TELEGRAM_BOT_TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN", "REDACTED_TELEGRAM_TOKEN"
)
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "7761755508")

# Internal Docker network URL — more reliable than external DNS (mas.femic.nl has no public record)
# Uptime-Kuma must be connected to the mas_mas-network Docker network (see deploy-notes.md)
MONITOR_URL = "http://mas-backend:8000/health"
MONITOR_NAME = "MAS Backend /health"
# Alert after 2 failed checks (each check = 60s interval → ~2 min; Uptime-Kuma
# default retry is 3 → approx 3 min before alert fires, well within the 5-min SLO)
CHECK_INTERVAL = 60  # seconds
MAX_RETRIES = 3


def setup():
    api = UptimeKumaApi(KUMA_URL)

    # Step 1: Login (or setup admin on first run)
    print("[1/4] Connecting to Uptime-Kuma...")
    try:
        api.login(ADMIN_USER, ADMIN_PASS)
        print("      Logged in as admin.")
    except Exception as e:
        if "need_setup" in str(e).lower() or "setup" in str(e).lower():
            print("      First-time setup detected — creating admin account...")
            api.setup(ADMIN_USER, ADMIN_PASS)
            api.login(ADMIN_USER, ADMIN_PASS)
            print("      Admin account created and logged in.")
        else:
            print(f"      ERROR: {e}")
            sys.exit(1)

    # Step 2: Create Telegram notification
    print("[2/4] Configuring Telegram notification...")
    existing_notifs = api.get_notifications()
    existing_names = [n.get("name") for n in existing_notifs]

    notif_id = None
    if "MAS Telegram Alert" in existing_names:
        notif_id = next(n["id"] for n in existing_notifs if n["name"] == "MAS Telegram Alert")
        print(f"      Telegram notification already exists (id={notif_id}), skipping.")
    else:
        result = api.add_notification(
            type=NotificationType.TELEGRAM,
            name="MAS Telegram Alert",
            isDefault=True,
            applyExisting=True,
            telegramBotToken=TELEGRAM_BOT_TOKEN,
            telegramChatID=TELEGRAM_CHAT_ID,
        )
        notif_id = result["id"]
        print(f"      Telegram notification created (id={notif_id}).")

    # Step 3: Create HTTP monitor
    print("[3/4] Creating HTTP monitor for MAS /api/health...")
    existing_monitors = api.get_monitors()
    existing_monitor_names = [m.get("name") for m in existing_monitors]

    if MONITOR_NAME in existing_monitor_names:
        print(f"      Monitor '{MONITOR_NAME}' already exists, skipping.")
    else:
        result = api.add_monitor(
            type=MonitorType.HTTP,
            name=MONITOR_NAME,
            url=MONITOR_URL,
            interval=CHECK_INTERVAL,
            maxretries=MAX_RETRIES,
            notificationIDList={str(notif_id): True},
            keyword="healthy",  # Expect {"status":"healthy"} in body
            accepted_statuscodes=["200"],
        )
        monitor_id = result["monitorID"]
        print(f"      Monitor created (id={monitor_id}).")
        # Resume (start) the monitor
        api.resume_monitor(monitor_id)
        print("      Monitor started.")

    # Step 4: Done
    print("[4/4] Setup complete.")
    print(f"      Uptime-Kuma UI: http://192.168.1.10:3001")
    print(f"      Monitoring: {MONITOR_URL}")
    print(f"      Alerts sent to Telegram chat: {TELEGRAM_CHAT_ID}")
    api.disconnect()


if __name__ == "__main__":
    setup()
