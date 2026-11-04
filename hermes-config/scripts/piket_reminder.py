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
import datetime
from zoneinfo import ZoneInfo

OMPRENG_ROSTER = [
    "Ridho, Hanif, Fajru",
    "Naufal, Adly, Farid",
    "Daffa, Rafif, Eko",
    "Andryan, Hilman, Yazid",
    "Angga, Rizal, Kahfi",
]

DAPUR_ROSTER = [
    "Sysadmin (Adel, Nopal)",
    "Networking (Fajru, Hanif, Ridho)",
    "Media (Yazid, Kahfi)",
    "Programming (Andryan, Hilman)",
    "Cysec (Angga, Rizal)",
    "Daffa, Rafif (akdev1)",
    "Farid, Eko (aldev2)",
]

def get_ompreng(target_date):
    if target_date == datetime.date(2026, 11, 4):
        return "Farid, Eko"
    anchor = datetime.date(2026, 11, 5)
    delta = (target_date - anchor).days
    return OMPRENG_ROSTER[delta % len(OMPRENG_ROSTER)]

def get_dapur(target_date):
    anchor = datetime.date(2026, 11, 1)  # Cysec (idx 4)
    if target_date <= anchor:
        return DAPUR_ROSTER[4]
    cur = anchor + datetime.timedelta(days=1)
    weekend_count = 0
    while cur <= target_date:
        if cur.weekday() in (5, 6):  # 5=Sabtu, 6=Minggu
            weekend_count += 1
        cur += datetime.timedelta(days=1)
    return DAPUR_ROSTER[(4 + weekend_count) % len(DAPUR_ROSTER)]

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
            f"👥 Petugas: *{petugas}*\n\n"
            f"Jangan lupa merapat ke dapur untuk piket bantu dapur pagi ini ya! Semangat! 👍"
        )
        return

    petugas = get_ompreng(today)

    if mode == "pagi":
        print(
            f"🔔 *Pengingat Piket Cuci Ompreng — Pagi*\n"
            f"⏰ Waktu: 07.30 WIB\n"
            f"👥 Petugas: *{petugas}*\n\n"
            f"Semangat dan jangan lupa cuci omprengnya ya! 👍"
        )
    elif mode == "siang":
        print(
            f"🔔 *Pengingat Piket Cuci Ompreng — Siang*\n"
            f"⏰ Waktu: 12.50 WIB\n"
            f"👥 Petugas: *{petugas}*\n\n"
            f"Jangan lupa cuci omprengnya setelah makan siang ya! 👍"
        )
    elif mode == "malam":
        print(
            f"🔔 *Pengingat Piket Cuci Ompreng — Malam*\n"
            f"⏰ Waktu: 20.45 WIB\n"
            f"👥 Petugas: *{petugas}*\n\n"
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
