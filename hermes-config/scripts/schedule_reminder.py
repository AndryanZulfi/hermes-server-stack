#!/usr/bin/env python3
"""
Pengingat Jadwal Sesi IDN Academy.
Sumber jadwal: Google Calendar (andryanzulfi2007@gmail.com).
Dengan fallback otomatis ke jadwal rutin jika API token expired/offline.
"""
import os
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Pastikan menggunakan venv Hermes yang memiliki googleapiclient
VENV_PYTHON = "/opt/hermes/.venv/bin/python"
if sys.executable != VENV_PYTHON and os.path.exists(VENV_PYTHON):
    os.execv(VENV_PYTHON, [VENV_PYTHON] + sys.argv)

TOKEN_PATH = "/opt/data/google_token.json"

# Fallback rutinitas harian jika Google Calendar API tidak dapat diakses
DEFAULT_ROUTINES = {
    # 0 = Senin
    0: {
        "pagi": [("09.00 - 12.00 WIB", "Blok Pagi: Invoice Pintar", "Prioritas #1: eksekusi to-do list Notion & pengerjaan fitur utama.")],
        "siang": [("13.30 - 15.00 WIB", "Blok Siang: Tugas Rust & Lab QEMU", "Prioritas #2: riset jaringan, implementasi code Rust.")],
        "sore": [
            ("16.00 - 17.00 WIB", "Blok Sore: Project NARA", "Development fokus mengejar target mingguan NARA."),
            ("17.00 - 17.50 WIB", "Meeting Mingguan NARA", "Evaluasi progress mingguan & koordinasi tim NARA.")
        ]
    },
    # 1 = Selasa
    1: {
        "pagi": [("09.00 - 12.00 WIB", "Blok Pagi: Invoice Pintar", "Selesaikan fitur utama & perbaikan bug.")],
        "siang": [("13.30 - 15.00 WIB", "Blok Siang: Tugas Rust & Lab QEMU", "Lanjutan pengerjaan tugas & lab sistem sebelum monitoring.")],
        "sore": [("16.00 - 17.00 WIB", "Blok Sore: Latihan Delivery Workshop Golang", "Simulasi membawakan materi, melatih analogi konsep, dan persiapan workshop.")]
    },
    # 2 = Rabu
    2: {
        "pagi": [("09.00 - 12.00 WIB", "Blok Pagi: Invoice Pintar", "Selesaikan fitur utama & perbaikan bug.")],
        "siang": [("13.30 - 15.00 WIB", "Blok Siang: Tugas Rust & Lab QEMU", "Finalisasi tugas sistem & lab sebelum hari monitoring.")],
        "sore": [("16.00 - 17.00 WIB", "Blok Sore: Latihan Delivery Workshop Golang", "Simulasi membawakan materi, melatih analogi konsep, dan persiapan workshop.")]
    },
    # 3 = Kamis
    3: {
        "pagi": [("09.00 - 12.00 WIB", "Blok Pagi: Monitoring Mentor (Rust & QEMU)", "Review tugas Rust & QEMU bersama Mas Asad.")],
        "siang": [("13.30 - 15.00 WIB", "Blok Siang: Invoice Pintar / Follow-up Mentor", "Lanjutan pengerjaan Invoice Pintar atau follow-up evaluasi mentor.")],
        "sore": [("16.00 - 17.00 WIB", "Blok Sore: Latihan Delivery Workshop Golang", "Simulasi membawakan materi, melatih analogi konsep, dan persiapan workshop.")]
    },
    # 4 = Jumat (Libur)
    4: {},
    # 5 = Sabtu
    5: {
        "pagi": [("09.00 - 12.00 WIB", "Blok Pagi: Invoice Pintar", "Prioritas #1: eksekusi to-do list Notion & pengerjaan fitur utama.")],
        "siang": [("13.30 - 15.00 WIB", "Blok Siang: Tugas Rust & Lab QEMU", "Prioritas #2: riset jaringan, implementasi code Rust.")],
        "sore": [("16.00 - 17.00 WIB", "Blok Sore: Project NARA", "Development fokus mengejar target mingguan NARA.")]
    },
    # 6 = Minggu
    6: {
        "pagi": [("09.00 - 12.00 WIB", "Blok Pagi: Invoice Pintar", "Prioritas #1: eksekusi to-do list Notion & pengerjaan fitur utama.")],
        "siang": [("13.30 - 15.00 WIB", "Blok Siang: Tugas Rust & Lab QEMU", "Prioritas #2: riset jaringan, implementasi code Rust.")],
        "sore": [("16.00 - 17.00 WIB", "Blok Sore: Project NARA", "Development fokus mengejar target mingguan NARA.")]
    }
}

def get_calendar_events_today(now):
    tz = now.tzinfo
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat()

    if not os.path.exists(TOKEN_PATH):
        return None, "File token Google Calendar tidak ditemukan."

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds = Credentials.from_authorized_user_file(TOKEN_PATH)
        service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        events_res = service.events().list(
            calendarId="primary",
            timeMin=start_of_day,
            timeMax=end_of_day,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        return events_res.get("items", []), None
    except Exception as e:
        return None, str(e)

def parse_iso(dt_str, tz):
    if not dt_str:
        return None
    if dt_str.endswith("Z"):
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    else:
        dt = datetime.fromisoformat(dt_str)
    return dt.astimezone(tz)

def main():
    tz = ZoneInfo("Asia/Jakarta")
    now = datetime.now(tz)
    weekday = now.weekday()  # 0=Mon, ..., 6=Sun

    # Deteksi sesi
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

    session_windows = {
        "pagi": (now.replace(hour=8, minute=50, second=0), now.replace(hour=12, minute=30, second=0), "08.55 WIB", "09.00 WIB"),
        "siang": (now.replace(hour=13, minute=15, second=0), now.replace(hour=15, minute=30, second=0), "13.25 WIB", "13.30 WIB"),
        "sore": (now.replace(hour=15, minute=45, second=0), now.replace(hour=18, minute=0, second=0), "15.55 WIB", "16.00 WIB"),
    }

    win_start, win_end, reminder_label, start_target = session_windows.get(
        session,
        (now, now + timedelta(hours=3), now.strftime("%H.%M WIB"), "sebentar lagi")
    )

    events, err = get_calendar_events_today(now)

    # Hari Jumat libur jika tidak ada event
    if weekday == 4 and (not events or len(events) == 0):
        sys.exit(0)

    header = f"🔔 *Pengingat Jadwal ({reminder_label})*\n\n5 menit lagi pukul {start_target}!"

    # Skenario 1: Kalender berhasil diambil via API
    if err is None and events is not None:
        session_events = []
        other_today_events = []

        for ev in events:
            start_raw = ev.get("start", {}).get("dateTime") or ev.get("start", {}).get("date")
            end_raw = ev.get("end", {}).get("dateTime") or ev.get("end", {}).get("date")
            if not start_raw:
                continue
            st = parse_iso(start_raw, tz)
            et = parse_iso(end_raw, tz) if end_raw else st + timedelta(hours=1)

            if (st <= win_end and et >= win_start):
                session_events.append((st, et, ev))
            else:
                other_today_events.append((st, et, ev))

        if session_events:
            body_lines = ["\n🎯 *Agenda Sesi Ini (dari Google Calendar):*"]
            for st, et, ev in session_events:
                summary = ev.get("summary", "Tanpa Judul")
                desc = ev.get("description", "").strip()
                time_str = f"{st.strftime('%H.%M')} - {et.strftime('%H.%M')} WIB"
                body_lines.append(f"• *{summary}* ({time_str})")
                if desc:
                    first_desc = desc.split("\n")[0]
                    body_lines.append(f"  _{first_desc}_")
            agenda_text = "\n".join(body_lines)
        else:
            agenda_text = f"\n🎯 *Agenda Sesi Ini:* Tidak ada event khusus di Google Calendar untuk sesi {session}."

        after_events = [e for e in other_today_events if e[0] > win_end]
        after_text = ""
        if after_events:
            after_lines = ["\n\n📌 *Agenda Berikutnya Hari Ini:*"]
            for st, et, ev in after_events[:2]:
                summary = ev.get("summary", "Tanpa Judul")
                time_str = f"{st.strftime('%H.%M')} WIB"
                after_lines.append(f"• {summary} ({time_str})")
            after_text = "\n".join(after_lines)

        print(f"{header}\n{agenda_text}{after_text}")
        return

    # Skenario 2: Token Google API expired / offline -> Gunakan Fallback Jadwal Rutinitas
    routine_today = DEFAULT_ROUTINES.get(weekday, {})
    session_items = routine_today.get(session, [])

    if session_items:
        body_lines = ["\n🎯 *Agenda Sesi Ini (Jadwal Rutin IDN Academy):*"]
        for time_str, title, desc in session_items:
            body_lines.append(f"• *{title}* ({time_str})")
            if desc:
                body_lines.append(f"  _{desc}_")
        agenda_text = "\n".join(body_lines)
    else:
        agenda_text = f"\n🎯 *Agenda Sesi Ini:* Sesi bebas / tidak ada jadwal blok untuk sesi {session}."

    # Agenda berikutnya di hari ini jika ada
    after_text = ""
    if session == "pagi":
        siang_items = routine_today.get("siang", [])
        if siang_items:
            after_text = f"\n\n📌 *Agenda Berikutnya Hari Ini:*\n• {siang_items[0][1]} ({siang_items[0][0]})"
    elif session == "siang":
        sore_items = routine_today.get("sore", [])
        if sore_items:
            after_text = f"\n\n📌 *Agenda Berikutnya Hari Ini:*\n• {sore_items[0][1]} ({sore_items[0][0]})"

    auth_warning = "\n\n⚠️ _(Catatan: Token Google Calendar sedang expired / butuh refresh, menampilkan jadwal rutin harian)_"
    print(f"{header}\n{agenda_text}{after_text}{auth_warning}")

if __name__ == "__main__":
    main()
