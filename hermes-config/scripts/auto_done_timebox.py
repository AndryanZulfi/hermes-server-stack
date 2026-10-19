#!/opt/hermes/.venv/bin/python
"""
Script Otomatisasi Status 'Done' Task Timebox task.idn.id
Fungsi:
Menandai status task timebox menjadi 'done' secara otomatis
ketika waktu jadwal task tersebut telah lewat/selesai.
"""

import os
import sys
import json
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

VENV_PYTHON = "/opt/hermes/.venv/bin/python"
if sys.executable != VENV_PYTHON and os.path.exists(VENV_PYTHON):
    os.execv(VENV_PYTHON, [VENV_PYTHON] + sys.argv)

COOKIE_FILE = "/opt/data/task_idn_cookie.json"


def refresh_task_idn_token(data, real_path):
    headers = {
        "Cookie": data.get("cookie_header", ""),
        "Origin": "https://task.idn.id",
        "Referer": "https://task.idn.id/dashboard",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0"
    }
    try:
        res = requests.post("https://task.idn.id/api/auth/refresh", headers=headers, timeout=10)
        if res.status_code == 200:
            cookie_parts = []
            for k, v in res.cookies.items():
                cookie_parts.append(f"{k}={v}")
            new_header = "; ".join(cookie_parts)
            data["cookie_header"] = new_header
            with open(real_path, "w") as f:
                json.dump(data, f, indent=2)
            return new_header
    except Exception as e:
        print(f"Gagal refresh token: {e}", file=sys.stderr)
    return None


def get_task_idn_headers():
    if not os.path.exists(COOKIE_FILE):
        return None, None, None
    real_path = os.path.realpath(COOKIE_FILE)
    try:
        with open(real_path) as f:
            data = json.load(f)
    except Exception:
        return None, None, None

    cookie_header = data.get("cookie_header", "")
    headers = {
        "Cookie": cookie_header,
        "Content-Type": "application/json",
        "Origin": "https://task.idn.id",
        "Referer": "https://task.idn.id/dashboard/time/box",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0"
    }
    return headers, data, real_path


def main():
    tz = ZoneInfo("Asia/Jakarta")
    now = datetime.now(tz)
    date_str = now.strftime("%Y-%m-%d")
    current_minutes = now.hour * 60 + now.minute

    headers, data, real_path = get_task_idn_headers()
    if not headers:
        print("❌ Cookie task.idn.id tidak ditemukan.", file=sys.stderr)
        sys.exit(1)

    tb_url = f"https://task.idn.id/api/time/timebox?date={date_str}"
    try:
        tb_res = requests.get(tb_url, headers=headers, timeout=10)
    except Exception as e:
        print(f"❌ Error fetching timebox: {e}", file=sys.stderr)
        sys.exit(1)

    if tb_res.status_code == 401:
        new_header = refresh_task_idn_token(data, real_path)
        if new_header:
            headers["Cookie"] = new_header
            tb_res = requests.get(tb_url, headers=headers, timeout=10)
        else:
            print("❌ Token kedaluwarsa dan gagal refresh.", file=sys.stderr)
            sys.exit(1)

    if tb_res.status_code != 200:
        print(f"❌ HTTP Error {tb_res.status_code} saat membaca timebox.", file=sys.stderr)
        sys.exit(1)

    entries = tb_res.json().get("entries", [])
    updated = []

    for e in entries:
        slot = e.get("startSlot", 0)
        count = e.get("slotCount", 0)
        end_slot = slot + count
        end_minutes = end_slot * 30
        status = e.get("status")

        # Jika waktu saat ini sudah melewati waktu selesai task dan belum 'done'
        if current_minutes >= end_minutes and status != "done":
            entry_id = e.get("id")
            title = e.get("title")
            start_h, start_m = divmod(slot * 30, 60)
            end_h, end_m = divmod(end_minutes, 60)

            patch_url = f"https://task.idn.id/api/time/timebox/{entry_id}"
            try:
                p_res = requests.patch(patch_url, headers=headers, json={"status": "done"}, timeout=10)
                if p_res.status_code == 200:
                    updated.append(f"• {title} ({start_h:02d}:{start_m:02d}–{end_h:02d}:{end_m:02d})")
                else:
                    print(f"⚠️ Gagal update status ID {entry_id}: {p_res.status_code}", file=sys.stderr)
            except Exception as e:
                print(f"⚠️ Error patching task {entry_id}: {e}", file=sys.stderr)

    if updated:
        print(f"✅ [{now.strftime('%H:%M:%S')} WIB] Berhasil menandai 'done' {len(updated)} task lampau:")
        for u in updated:
            print(f"  {u}")
    else:
        # Jika tidak ada perubahan, senyap (watchdog pattern)
        pass


if __name__ == "__main__":
    main()
