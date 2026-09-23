#!/usr/bin/env python3
"""
Script pengingat piket dapur / mencuci ompreng ID-Networkers.
Dijalankan via cronjob Hermes:
- Pagi: 07:30 WIB
- Siang: 13:00 WIB
- Malam: 20:00 WIB

Urutan rolling piket per 5 hari:
1. Media (Kahfi & Yazid)
2. Network (Hanif, Fajru, Ridho)
3. Programmer (Andryan, Hilman)
4. Cyber Security (Angga, Rizal)
5. Sys Admin (Adel, Naufal)

Tanggal referensi: Sabtu, 19 September 2026 = Programmer
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo
import sys

REF_DATE = date(2026, 9, 19)

DUTY_CYCLE = [
    {"major": "Programmer", "members": "Andryan, Hilman"},
    {"major": "Cyber Security", "members": "Angga, Rizal"},
    {"major": "Sys Admin", "members": "Adel, Naufal"},
    {"major": "Media", "members": "Kahfi & Yazid"},
    {"major": "Network", "members": "Hanif, Fajru, Ridho"},
]

def main():
    tz = ZoneInfo("Asia/Jakarta")
    now = datetime.now(tz)
    today = now.date()
    current_hour = now.hour

    delta = (today - REF_DATE).days
    if delta < 0:
        sys.exit(0)

    duty = DUTY_CYCLE[delta % len(DUTY_CYCLE)]

    if current_hour < 11:
        session = "Sarapan Pagi"
    elif current_hour < 17:
        session = "Makan Siang"
    else:
        session = "Makan Malam"

    message = (
        f"🔔 *Piket Cuci Ompreng — {session}*\n"
        f"Petugas: *{duty['major']}* ({duty['members']})\n"
        f"Jangan lupa dicuci ya! 👍"
    )

    print(message)

if __name__ == "__main__":
    main()
