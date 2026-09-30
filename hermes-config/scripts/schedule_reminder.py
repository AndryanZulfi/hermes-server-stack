#!/usr/bin/env python3
"""
Pengingat Jadwal Sesi IDN Academy (Dynamic Google Calendar).
Sumber kebenaran jadwal: Google Calendar (andryanzulfi2007@gmail.com).
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

def get_calendar_events_today(now):
    tz = now.tzinfo
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat()

    if not os.path.exists(TOKEN_PATH):
        return []

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
        return events_res.get("items", [])
    except Exception as e:
        print(f"[Warning] Gagal mengambil calendar: {e}", file=sys.stderr)
        return []

def parse_iso(dt_str, tz):
    if not dt_str:
        return None
    # Menghapus 'Z' atau parse ISO standar
    if dt_str.endswith("Z"):
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    else:
        dt = datetime.fromisoformat(dt_str)
    return dt.astimezone(tz)

def main():
    tz = ZoneInfo("Asia/Jakarta")
    now = datetime.now(tz)
    weekday = now.weekday()  # 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun

    # Hari Jumat (4) libur penuh jika tidak ada event di kalender
    # Namun tetap cek kalender jika ada event mendesak
    events = get_calendar_events_today(now)
    if weekday == 4 and not events:
        sys.exit(0)

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

    # Filter event kalender yang relevan dengan window sesi ini
    session_events = []
    other_today_events = []

    for ev in events:
        start_raw = ev.get("start", {}).get("dateTime") or ev.get("start", {}).get("date")
        end_raw = ev.get("end", {}).get("dateTime") or ev.get("end", {}).get("date")
        if not start_raw:
            continue
        st = parse_iso(start_raw, tz)
        et = parse_iso(end_raw, tz) if end_raw else st + timedelta(hours=1)

        # Apakah event beririsan dengan sesi ini?
        if (st <= win_end and et >= win_start):
            session_events.append((st, et, ev))
        else:
            other_today_events.append((st, et, ev))

    header = f"🔔 *Pengingat Jadwal ({reminder_label})*\n\n5 menit lagi pukul {start_target}!"

    if session_events:
        body_lines = ["\n🎯 *Agenda Sesi Ini (dari Google Calendar):*"]
        for st, et, ev in session_events:
            summary = ev.get("summary", "Tanpa Judul")
            desc = ev.get("description", "").strip()
            time_str = f"{st.strftime('%H.%M')} - {et.strftime('%H.%M')} WIB"
            body_lines.append(f"• *{summary}* ({time_str})")
            if desc:
                # Ambil 1-2 baris deskripsi
                first_desc = desc.split("\n")[0]
                body_lines.append(f"  _{first_desc}_")
        agenda_text = "\n".join(body_lines)
    else:
        # Fallback jika tidak ada event spesifik di sesi ini
        agenda_text = f"\n🎯 *Agenda Sesi Ini:* Tidak ada event khusus di Google Calendar untuk sesi {session}."

    # Tambahkan catatan jika ada event lain setelah sesi ini hari ini
    after_events = [e for e in other_today_events if e[0] > win_end]
    after_text = ""
    if after_events:
        after_lines = ["\n\n📌 *Agenda Berikutnya Hari Ini:*"]
        for st, et, ev in after_events[:2]:
            summary = ev.get("summary", "Tanpa Judul")
            time_str = f"{st.strftime('%H.%M')} WIB"
            after_lines.append(f"• {summary} ({time_str})")
        after_text = "\n".join(after_lines)

    msg = f"{header}\n{agenda_text}{after_text}"
    print(msg)

if __name__ == "__main__":
    main()
