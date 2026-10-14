#!/opt/hermes/.venv/bin/python
"""
Script Otomatisasi Pengisian Timebox task.idn.id
Blok: Project & Belajar Mandiri (09.00 - 17.00 WIB)
Sumber Data: Google Spreadsheet Logbook Programmer (Sheet 'Andryan Zulfi')
Fallback: Google Calendar API / Rutinitas Terjadwal IDN Academy
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
GOOGLE_TOKEN_PATH = "/opt/data/google_token.json"
SPREADSHEET_ID = "1SrVE7CQNai_Rq1Alehpya51sDdyaWHR4U9GdfSI3W0U"
SHEET_NAME = "Andryan Zulfi"

DEFAULT_ROUTINES = {
    0: {  # Senin
        "pagi": ("Belajar Firmware Router Fisik TOTOLINK & Rust", "Fokus belajar firmware router fisik TOTOLINK dan Rust sesuai materi di spreadsheet."),
        "siang": ("Project (Invoice Pintar / NARA / Project Lainnya)", "Pengerjaan development project (Invoice Pintar, NARA, atau project lainnya)."),
        "sore": ("Belajar / Persiapan Sharing Session & Workshop", "Belajar materi pendukung serta persiapan sharing session dan workshop."),
        "extra": ("Meeting Mingguan NARA (17.00 - 17.50 WIB)", "Evaluasi progress mingguan & koordinasi tim NARA.")
    },
    1: {  # Selasa
        "pagi": ("Belajar Firmware Router Fisik TOTOLINK & Rust", "Fokus belajar firmware router fisik TOTOLINK dan Rust sesuai materi di spreadsheet."),
        "siang": ("Project (Invoice Pintar / NARA / Project Lainnya)", "Pengerjaan development project (Invoice Pintar, NARA, atau project lainnya)."),
        "sore": ("Belajar / Persiapan Sharing Session & Workshop", "Belajar materi pendukung serta persiapan sharing session dan workshop.")
    },
    2: {  # Rabu
        "pagi": ("Belajar Firmware Router Fisik TOTOLINK & Rust", "Fokus belajar firmware router fisik TOTOLINK dan Rust sesuai materi di spreadsheet."),
        "siang": ("Project NARA", "Fokus pengerjaan development fitur dan modul Project NARA."),
        "sore": ("Belajar / Persiapan Sharing Session & Workshop", "Belajar materi pendukung serta persiapan sharing session dan workshop."),
        "extra": ("Sharing Session (17.00 - 18.00 WIB)", "Mengikuti sesi sharing session / presentasi ilmu & teknologi IDN Academy.")
    },
    3: {  # Kamis
        "pagi": ("Belajar Firmware Router Fisik TOTOLINK & Rust & Monitoring Mentor", "Belajar materi Embedded Router dan sesi monitoring tugas bersama mentor."),
        "siang": ("Project NARA", "Fokus pengerjaan development fitur dan modul Project NARA."),
        "sore": ("Belajar / Persiapan Sharing Session & Workshop", "Belajar materi pendukung serta persiapan sharing session dan workshop.")
    },
    4: {},  # Jumat (Libur)
    5: {  # Sabtu
        "pagi": ("Belajar Firmware Router Fisik TOTOLINK & Rust", "Fokus belajar firmware router fisik TOTOLINK dan Rust sesuai materi di spreadsheet."),
        "siang": ("Project (Invoice Pintar / NARA / Project Lainnya)", "Pengerjaan development project (Invoice Pintar, NARA, atau project lainnya)."),
        "sore": ("Belajar / Persiapan Sharing Session & Workshop", "Belajar materi pendukung serta persiapan sharing session dan workshop.")
    },
    6: {  # Minggu
        "pagi": ("Belajar Firmware Router Fisik TOTOLINK & Rust", "Fokus belajar firmware router fisik TOTOLINK dan Rust sesuai materi di spreadsheet."),
        "siang": ("Meeting Tambahan Project NARA", "Meeting tambahan koordinasi dan sinkronisasi progress Project NARA."),
        "sore": ("Belajar / Persiapan Sharing Session & Workshop", "Belajar materi pendukung serta persiapan sharing session dan workshop.")
    }
}


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
        return None
    real_path = os.path.realpath(COOKIE_FILE)
    try:
        with open(real_path) as f:
            data = json.load(f)
    except Exception:
        return None

    cookie_header = data.get("cookie_header", "")
    headers = {
        "Cookie": cookie_header,
        "Origin": "https://task.idn.id",
        "Referer": "https://task.idn.id/dashboard/time/box",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0"
    }

    # Cek keabsahan sesi
    try:
        test_res = requests.get("https://task.idn.id/api/auth/me", headers=headers, timeout=8)
        if test_res.status_code == 200:
            return headers
        elif test_res.status_code == 401:
            new_header = refresh_task_idn_token(data, real_path)
            if new_header:
                headers["Cookie"] = new_header
                return headers
    except Exception as e:
        print(f"Error checking auth: {e}", file=sys.stderr)

    return headers


def get_logbook_data(target_date_str):
    if not os.path.exists(GOOGLE_TOKEN_PATH):
        return None
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_PATH)
        service = build("sheets", "v4", credentials=creds, cache_discovery=False)
        res = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"'{SHEET_NAME}'!A40:F70"
        ).execute()

        rows = res.get("values", [])
        for row in rows:
            if len(row) > 0 and str(row[0]).strip() == target_date_str:
                col_c = row[2] if len(row) > 2 else ""
                col_d = row[3] if len(row) > 3 else ""
                return {"task_c": col_c, "output_d": col_d}
    except Exception as e:
        print(f"Error fetching sheets logbook: {e}", file=sys.stderr)
    return None


def parse_schedule_details(target_date, weekday):
    logbook_info = get_logbook_data(target_date.strftime("%Y-%m-%d"))
    routine = DEFAULT_ROUTINES.get(weekday, {})

    pagi_title = routine.get("pagi", ("Belajar Embedded Router", ""))[0]
    pagi_desc = routine.get("pagi", ("", ""))[1]
    siang_title = routine.get("siang", ("Project", ""))[0]
    siang_desc = routine.get("siang", ("", ""))[1]
    sore_title = routine.get("sore", ("Belajar / Persiapan Sharing Session & Workshop", ""))[0]
    sore_desc = routine.get("sore", ("", ""))[1]
    extra_item = routine.get("extra", None)

    if logbook_info:
        task_c = logbook_info["task_c"]
        output_d = logbook_info["output_d"]

        # Parse bagian pagi dari Column C & D
        c_lines = [l.strip() for l in task_c.splitlines() if l.strip()]
        for line in c_lines:
            if "Belajar Firmware Router" in line or "Embedded Router" in line:
                pagi_title = line.replace("(Belajar) ", "").strip()
            elif "Mengerjakan Project NARA" in line:
                siang_title = "Project NARA"
            elif "Meeting Tambahan Project NARA" in line:
                siang_title = "Meeting Tambahan Project NARA"
            elif "Mengerjakan Project" in line:
                siang_title = "Project (Invoice Pintar / NARA / Project Lainnya)"

        # Parse rincian output dari Column D
        d_sections = output_d.split("\n\n")
        for sec in d_sections:
            sec_clean = sec.strip()
            if sec_clean.startswith("(Embedded Router)"):
                points = [p.strip() for p in sec_clean.splitlines()[1:] if p.strip()]
                if points:
                    pagi_desc = "; ".join(points[:3])
            elif sec_clean.startswith("(Project NARA)"):
                points = [p.strip() for p in sec_clean.splitlines()[1:] if p.strip()]
                if points:
                    siang_desc = " ".join(points)
            elif sec_clean.startswith("(Project)"):
                points = [p.strip() for p in sec_clean.splitlines()[1:] if p.strip()]
                if points:
                    siang_desc = " ".join(points)
            elif sec_clean.startswith("(Meeting NARA)"):
                points = [p.strip() for p in sec_clean.splitlines()[1:] if p.strip()]
                if points:
                    siang_desc = " ".join(points)
            elif sec_clean.startswith("(Sharing Session"):
                points = [p.strip() for p in sec_clean.splitlines()[1:] if p.strip()]
                if points:
                    extra_item = ("Sharing Session (17.00 - 18.00 WIB)", " ".join(points))

    return {
        "pagi_title": pagi_title,
        "pagi_desc": pagi_desc,
        "siang_title": siang_title,
        "siang_desc": siang_desc,
        "sore_title": sore_title,
        "sore_desc": sore_desc,
        "extra_item": extra_item
    }


def build_report_html(details):
    pagi_title = details["pagi_title"].replace("&", "&amp;")
    pagi_desc = details["pagi_desc"].replace("&", "&amp;")
    siang_title = details["siang_title"].replace("&", "&amp;")
    siang_desc = details["siang_desc"].replace("&", "&amp;")
    sore_title = details["sore_title"].replace("&", "&amp;")
    sore_desc = details["sore_desc"].replace("&", "&amp;")

    lines = [
        f"<p>* 🕘 09.00 – 12.00 WIB (Blok Pagi): {pagi_title}</p>",
        f"<p>  Fokus: {pagi_desc}</p>",
        "<p>* 🥪 12.00 – 13.30 WIB: Istirahat &amp; Ishoma Dzuhur</p>",
        f"<p>* 🕜 13.30 – 15.00 WIB (Blok Siang): {siang_title}</p>",
        f"<p>  Fokus: {siang_desc}</p>",
        "<p>* ☕ 15.00 – 16.00 WIB: Istirahat &amp; Ishoma Ashar</p>",
        f"<p>* 🕓 16.00 – 17.00 WIB (Blok Sore): {sore_title}</p>",
        f"<p>  Fokus: {sore_desc}</p>"
    ]

    if details["extra_item"]:
        extra_title = details["extra_item"][0].replace("&", "&amp;")
        extra_desc = details["extra_item"][1].replace("&", "&amp;")
        lines.append(f"<p>* 🕔 {extra_title}</p>")
        lines.append(f"<p>  Fokus: {extra_desc}</p>")

    return "".join(lines)


def main():
    tz = ZoneInfo("Asia/Jakarta")
    now = datetime.now(tz)

    if len(sys.argv) > 1 and sys.argv[1].strip():
        try:
            target_date = datetime.strptime(sys.argv[1].strip(), "%Y-%m-%d").replace(tzinfo=tz)
        except ValueError:
            target_date = now
    else:
        target_date = now

    date_str = target_date.strftime("%Y-%m-%d")
    weekday = target_date.weekday()
    indonesian_days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    day_name = indonesian_days[weekday]

    # Hari Jumat libur
    if weekday == 4:
        print(f"ℹ️ {day_name}, {date_str} adalah hari libur (tidak ada blok timebox Project & Belajar Mandiri).")
        return

    headers = get_task_idn_headers()
    if not headers:
        print("❌ Gagal autentikasi ke task.idn.id: File cookie tidak ditemukan atau token tidak valid.", file=sys.stderr)
        sys.exit(1)

    # Ambil list timebox hari ini
    tb_url = f"https://task.idn.id/api/time/timebox?date={date_str}"
    try:
        tb_res = requests.get(tb_url, headers=headers, timeout=10)
    except Exception as e:
        print(f"❌ Error fetching timebox: {e}", file=sys.stderr)
        sys.exit(1)

    if tb_res.status_code != 200:
        print(f"❌ HTTP Error {tb_res.status_code} saat membaca timebox task.idn.id", file=sys.stderr)
        sys.exit(1)

    entries = tb_res.json().get("entries", [])
    target_entry = None
    for e in entries:
        if e.get("title") == "Project & Belajar Mandiri":
            target_entry = e
            break

    if not target_entry:
        print(f"⚠️ Tidak ditemukan entry 'Project & Belajar Mandiri' di timebox task.idn.id untuk tanggal {date_str}.")
        return

    entry_id = target_entry["id"]
    details = parse_schedule_details(target_date, weekday)
    html_report = build_report_html(details)

    # Patch reportNote ke task.idn.id
    patch_url = f"https://task.idn.id/api/time/timebox/{entry_id}"
    patch_payload = {
        "reportNote": html_report
    }

    patch_headers = headers.copy()
    patch_headers["Content-Type"] = "application/json"

    try:
        res = requests.patch(patch_url, headers=patch_headers, json=patch_payload, timeout=10)
        if res.status_code == 200:
            print(f"✅ *Auto-Fill Timebox Berhasil!*")
            print(f"📅 Tanggal: {day_name}, {date_str}")
            print(f"📌 Entry: Project & Belajar Mandiri (ID: {entry_id})")
            print(f"\n📝 *Rincian Agenda Terisi:*")
            print(f"• *Blok Pagi (09.00–12.00):* {details['pagi_title']}")
            print(f"• *Blok Siang (13.30–15.00):* {details['siang_title']}")
            print(f"• *Blok Sore (16.00–17.00):* {details['sore_title']}")
            if details["extra_item"]:
                print(f"• *Tambahan:* {details['extra_item'][0]}")
        else:
            print(f"❌ Gagal update timebox: Status {res.status_code} - {res.text}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error patching timebox: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
