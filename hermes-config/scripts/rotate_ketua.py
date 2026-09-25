#!/usr/bin/env python3
import datetime
import json
import os
import signal
import subprocess
import sys
from zoneinfo import ZoneInfo

ADMIN_PHONE = "6288803918389"
ANCHOR_DATE = datetime.date(2026, 9, 26)  # Angga (index 6)

ROSTER = [
    ("Hilman", "62895336902593"),
    ("Hanif", "6285692214982"),
    ("Rizal", "6282157461646"),
    ("Andryan", "6288803918389"),
    ("Fajru", "62887437239818"),
    ("Ridho", "6285811538319"),
    ("Angga", "6285156500314"),
    ("Adly", "6285179518681"),
    ("Naufal", "6281328117870"),
    ("Yazid", "6282112162443"),
    ("Kahfi", "6285751202762"),
]

BASE_ROUTES = [
    {
        "name": "idn-academy-group",
        "platform": "whatsapp",
        "chat_id": "6288803918389-1617164069@g.us",
        "profile": "idn-academy",
        "enabled": True,
    },
    {
        "name": "cod-musang-area-palmerah",
        "platform": "whatsapp",
        "chat_id": "120363410899436681@g.us",
        "profile": "idn-academy",
        "enabled": True,
    },
    {
        "name": "idn-programmer-group",
        "platform": "whatsapp",
        "chat_id": "120363430531430052@g.us",
        "profile": "idn-programmer",
        "enabled": True,
    },
    {
        "name": "report-and-log-agent",
        "platform": "whatsapp",
        "chat_id": "120363414423509222@g.us",
        "profile": "default",
        "enabled": True,
    },
]

def get_active_ketua(target_date=None):
    if target_date is None:
        tz = ZoneInfo("Asia/Jakarta")
        target_date = datetime.datetime.now(tz).date()
    delta_days = (target_date - ANCHOR_DATE).days
    period = delta_days // 14
    idx = (6 + period) % len(ROSTER)
    return ROSTER[idx]

def sync_allowlist():
    tz = ZoneInfo("Asia/Jakarta")
    today = datetime.datetime.now(tz).date()
    name, phone = get_active_ketua(today)
    
    allowed_list = [ADMIN_PHONE]
    if phone != ADMIN_PHONE:
        allowed_list.append(phone)
    
    val_json = json.dumps(allowed_list)
    print(f"[{datetime.datetime.now(tz).isoformat()}] Ketua aktif: {name} ({phone})")
    print(f"Sinkronisasi whatsapp.allow_from = {val_json}")
    
    hermes_bin = "/opt/hermes/.venv/bin/hermes"
    
    # 1. Update allowlist & mention requirement di level gateway
    subprocess.run([hermes_bin, "config", "set", "whatsapp.allow_from", val_json], check=True)
    subprocess.run([hermes_bin, "config", "set", "whatsapp.require_mention", "true"], check=True)
    
    # 2. RBAC Routing: Pastikan DM dari ketua terisolasi ke profile idn-academy
    routes = list(BASE_ROUTES)
    if phone != ADMIN_PHONE:
        routes.append({
            "name": "active-ketua-dm",
            "platform": "whatsapp",
            "user_id": str(phone),
            "profile": "idn-academy",
            "enabled": True,
        })
    routes_json = json.dumps(routes)
    subprocess.run([hermes_bin, "config", "set", "gateway.profile_routes", routes_json], check=True)
    print("✓ RBAC profile routes berhasil diperbarui.")
    
    # 3. Reload/restart gateway dengan sinyal SIGUSR1 jika proses berjalan
    try:
        res = subprocess.run(["pgrep", "-f", "hermes gateway run"], capture_output=True, text=True)
        pids = [int(p) for p in res.stdout.strip().split() if p]
        for pid in pids:
            print(f"Mengirim SIGUSR1 ke gateway PID {pid}...")
            os.kill(pid, signal.SIGUSR1)
    except Exception as e:
        print(f"Catatan: tidak dapat mengirim sinyal ke gateway: {e}")
        
    print(f"✓ Berhasil update ketua aktif: {name} ({phone})")

if __name__ == "__main__":
    sync_allowlist()
