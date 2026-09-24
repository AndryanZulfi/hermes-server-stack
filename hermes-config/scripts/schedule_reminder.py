#!/usr/bin/env python3
"""
Pengingat Jadwal 5 Menit Sebelum Sesi IDN Academy.
Zona waktu: Asia/Jakarta (WIB)
"""
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

def main():
    tz = ZoneInfo("Asia/Jakarta")
    now = datetime.now(tz)
    weekday = now.weekday()  # 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun

    # Hari Jumat (4) libur penuh
    if weekday == 4:
        sys.exit(0)

    # Deteksi sesi berdasarkan jam atau argumen
    arg_session = sys.argv[1].lower() if len(sys.argv) > 1 else None

    if arg_session:
        session = arg_session
    else:
        hour = now.hour
        if hour < 11:
            session = "pagi"
        elif 12 <= hour < 15:
            session = "siang"
        else:
            session = "sore"

    if session == "pagi":
        if weekday == 3:  # Kamis
            msg = (
                "🔔 *Pengingat Jadwal (08.55 WIB)*\n\n"
                "5 menit lagi pukul 09.00 WIB!\n"
                "🎯 *Agenda:* Monitoring Tugas Rust & QEMU dengan Mentor (09.00 - 12.00 WIB)\n\n"
                "💡 *Tips:* Siapkan catatan progres seminggu ini, kendala yang dihadapi, dan pertanyaan seputar konsep jaringan/Rust untuk mentor."
            )
        else:
            msg = (
                "🔔 *Pengingat Jadwal (08.55 WIB)*\n\n"
                "5 menit lagi pukul 09.00 WIB!\n"
                "🎯 *Agenda:* Deep Work Project Invoice Pintar (09.00 - 12.00 WIB)\n\n"
                "💡 *Tips:* Buka to-do list fitur di Notion dan fokus selesaikan fitur prioritas utama hari ini."
            )

    elif session == "siang":
        if weekday == 3:  # Kamis
            msg = (
                "🔔 *Pengingat Jadwal (13.25 WIB)*\n\n"
                "5 menit lagi pukul 13.30 WIB!\n"
                "🎯 *Agenda:* Invoice Pintar / Follow-up Feedback Mentor (13.30 - 15.00 WIB)\n\n"
                "💡 *Tips:* Kerjakan perbaikan berdasarkan feedback monitoring pagi tadi atau lanjutkan fitur invoice pintar."
            )
        else:
            msg = (
                "🔔 *Pengingat Jadwal (13.25 WIB)*\n\n"
                "5 menit lagi pukul 13.30 WIB!\n"
                "🎯 *Agenda:* Tugas Rust & Lab QEMU/OpenWRT (13.30 - 15.00 WIB)\n\n"
                "💡 *Tips:* Fokus riset sistem, networking, dan implementasi kode Rust."
            )

    elif session == "sore":
        if weekday in (0, 5, 6):  # Senin, Sabtu, Minggu
            extra = "\n\n📌 *Catatan:* Pukul 17.00 - 17.50 WIB ada *Meeting Progres NARA*!" if weekday == 0 else ""
            msg = (
                "🔔 *Pengingat Jadwal (15.55 WIB)*\n\n"
                "5 menit lagi pukul 16.00 WIB!\n"
                "🎯 *Agenda:* Project NARA (16.00 - 17.00 WIB)\n\n"
                "💡 *Tips:* Kejar target mingguan development NARA." + extra
            )
        else:  # Selasa, Rabu, Kamis
            msg = (
                "🔔 *Pengingat Jadwal (15.55 WIB)*\n\n"
                "5 menit lagi pukul 16.00 WIB!\n"
                "🎯 *Agenda:* Latihan Delivery Workshop Golang (16.00 - 17.00 WIB)\n\n"
                "💡 *Tips:* Latih cara membawakan materi, buat analogi konsep sederhana, dan transisi antar-topik."
            )
    else:
        sys.exit(0)

    print(msg)

if __name__ == "__main__":
    main()
