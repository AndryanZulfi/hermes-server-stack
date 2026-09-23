#!/usr/bin/env python3
"""
Daily Reflection Helper Script
Saves reflection entries locally to /opt/data/refleksi/
and exposes parameters for Notion Database 'Notes' sync.
"""

import os
import sys
import json
from datetime import datetime, timezone, timedelta

WIB = timezone(timedelta(hours=7))
REFLEKSI_DIR = "/opt/data/refleksi"
NOTION_CATEGORY_REFLEKSI_ID = "3e4132f7-ca42-817d-ad0f-d13ea95e67e9"
NOTION_NOTES_DB_ID = "d99132f7-ca42-8318-8019-010461339720"

def save_reflection(aha_moment: str, friction: str, micro_tweak: str, raw_notes: str = "") -> dict:
    os.makedirs(REFLEKSI_DIR, exist_ok=True)
    now = datetime.now(WIB)
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S WIB")
    title = f"Refleksi - {date_str}"

    body_md = f"""## 1. Aha! Moment (Pemahaman Kunci)
{aha_moment.strip()}

## 2. The Friction / Root Cause (Hambatan & Akar Masalah)
{friction.strip()}

## 3. The Micro-Tweak (1 Perbaikan untuk Besok)
{micro_tweak.strip()}
"""
    if raw_notes.strip():
        body_md += f"\n## Catatan Tambahan\n{raw_notes.strip()}\n"

    local_path = os.path.join(REFLEKSI_DIR, f"{date_str}.md")
    with open(local_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n*Dicatat pada:* {time_str}\n\n" + body_md)

    return {
        "title": title,
        "date": date_str,
        "time": time_str,
        "local_path": local_path,
        "markdown": body_md,
        "notion_db_id": NOTION_NOTES_DB_ID,
        "category_id": NOTION_CATEGORY_REFLEKSI_ID
    }

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: save_reflection.py <aha_moment> <friction> <micro_tweak> [raw_notes]")
        sys.exit(1)
    res = save_reflection(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "")
    print(json.dumps(res, indent=2))
