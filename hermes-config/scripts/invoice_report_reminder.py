#!/usr/bin/env python3
"""
Pengingat harian pengiriman laporan update fitur invoice pintar.
Jadwal: 20:45 WIB setiap hari kecuali Jumat.
"""
from datetime import datetime
from zoneinfo import ZoneInfo
import sys

def main():
    tz = ZoneInfo("Asia/Jakarta")
    now = datetime.now(tz)
    
    # 4 = Friday in Python (0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun)
    if now.weekday() == 4:
        sys.exit(0)

    message = (
        "🔔 *Pengingat Laporan Harian*\n\n"
        "Halo Zulfi, sudah pukul 20.45 WIB.\n"
        "Jangan lupa untuk mengirim laporan pembuatan / update fitur *invoice pintar* hari ini."
    )
    print(message)

if __name__ == "__main__":
    main()
