#!/usr/bin/env python3
"""
Pengingat Jadwal Piket Cuci Ompreng dan Bantu Dapur IDN Academy.
Dijalankan via cronjob Hermes tanpa log/output tambahan.

Jadwal Pengingat:
- Ompreng Pagi: 07:30 WIB
- Ompreng Siang: 12:50 WIB
- Ompreng Malam: 20:45 WIB
- Bantu Dapur (Sabtu & Minggu): 07:00 WIB
"""

import sys
import json
import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

def load_member_phones():
    phones = {}
    paths = [
        Path("/opt/data/data/idn_members.json"),
        Path("/opt/data/profiles/idn-academy/data/idn_members.json")
    ]
    for p in paths:
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                for name, info in data.get("members", {}).items():
                    if info.get("phone"):
                        phones[name.lower()] = info["phone"]
                if "admin" in data and data["admin"].get("phone"):
                    phones["andryan"] = data["admin"]["phone"]
                    phones["zulfi"] = data["admin"]["phone"]
                break
            except Exception:
                pass
    if "naufal" in phones and "nopal" not in phones:
        phones["nopal"] = phones["naufal"]
    if "daffa" in phones and "dafa" not in phones:
        phones["dafa"] = phones["daffa"]
    return phones

MEMBER_PHONES = load_member_phones()

def format_person(name: str) -> str:
    phone = MEMBER_PHONES.get(name.lower().strip())
    if phone:
        return f"*{name}* (@{phone})"
    return f"*{name}*"

def format_group_names(names: list[str]) -> str:
    return ", ".join(format_person(n) for n in names)

OMPRENG_GROUPS = [
    ["Ridho", "Hanif", "Fajru"],
    ["Naufal", "Adly", "Farid"],
    ["Daffa", "Rafif", "Eko"],
    ["Andryan", "Hilman", "Yazid"],
    ["Angga", "Rizal", "Kahfi"],
]

DAPUR_GROUPS = [
    ("Sysadmin", ["Adel", "Naufal"]),
    ("Networking", ["Fajru", "Hanif", "Ridho"]),
    ("Media", ["Yazid", "Kahfi"]),
    ("Programming", ["Andryan", "Hilman"]),
    ("Cysec", ["Angga", "Rizal"]),
    ("akdev1", ["Daffa", "Rafif"]),
    ("akdev2", ["Farid", "Eko"]),
]

def get_ompreng(target_date):
    # Anchor: 5 Nov 2026 (Kamis) = Andryan, Hilman, Yazid (index 3)
    anchor = datetime.date(2026, 11, 5)
    delta = (target_date - anchor).days
    names = OMPRENG_GROUPS[(3 + delta) % len(OMPRENG_GROUPS)]
    return format_group_names(names)

def get_dapur(target_date):
    anchor = datetime.date(2026, 11, 1)  # Cysec (idx 4)
    if target_date <= anchor:
        label, names = DAPUR_GROUPS[4]
    else:
        cur = anchor + datetime.timedelta(days=1)
        weekend_count = 0
        while cur <= target_date:
            if cur.weekday() in (5, 6):  # 5=Sabtu, 6=Minggu
                weekend_count += 1
            cur += datetime.timedelta(days=1)
        label, names = DAPUR_GROUPS[(4 + weekend_count) % len(DAPUR_GROUPS)]

    if "akdev" in label:
        return f"{format_group_names(names)} ({label})"
    return f"{label} ({format_group_names(names)})"

def run_reminder(mode="auto"):
    tz = ZoneInfo("Asia/Jakarta")
    now = datetime.datetime.now(tz)
    today = now.date()

    if mode == "dapur":
        if today.weekday() not in (5, 6):
            return
        petugas = get_dapur(today)
        print(
            f"🍳 *Pengingat Piket Bantu Dapur*\n"
            f"⏰ Waktu: 07.00 WIB\n"
            f"👥 Petugas: {petugas}\n\n"
            f"Jangan lupa merapat ke dapur untuk piket bantu dapur pagi ini ya! Semangat! 👍"
        )
        return

    petugas = get_ompreng(today)

    if mode == "pagi":
        print(
            f"🔔 *Pengingat Piket Cuci Ompreng — Pagi*\n"
            f"⏰ Waktu: 07.30 WIB\n"
            f"👥 Petugas: {petugas}\n\n"
            f"Semangat dan jangan lupa cuci omprengnya ya! 👍"
        )
    elif mode == "siang":
        print(
            f"🔔 *Pengingat Piket Cuci Ompreng — Siang*\n"
            f"⏰ Waktu: 12.50 WIB\n"
            f"👥 Petugas: {petugas}\n\n"
            f"Jangan lupa cuci omprengnya setelah makan siang ya! 👍"
        )
    elif mode == "malam":
        print(
            f"🔔 *Pengingat Piket Cuci Ompreng — Malam*\n"
            f"⏰ Waktu: 20.45 WIB\n"
            f"👥 Petugas: {petugas}\n\n"
            f"Jangan lupa cuci omprengnya setelah makan malam ya! 👍"
        )
    else:
        h = now.hour
        if h < 11:
            run_reminder("pagi")
        elif h < 16:
            run_reminder("siang")
        else:
            run_reminder("malam")

def main():
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "auto"
    run_reminder(mode)

if __name__ == "__main__":
    main()
