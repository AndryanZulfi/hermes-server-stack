#!/opt/hermes/.venv/bin/python
"""
Workflow Pengelolaan & Pengiriman Timebox Harian IDN Academy
Fungsi:
1. 07.30 WIB: Auto-fill timebox, siapkan caption & state pending untuk review Zulfi.
2. 08.00, 08.30, 09.00, 09.30, dst: Pengecekan approval & reminder setiap 30 menit.
   - Jika jam 09.00 tiba & sudah approved: otomatis kirim ke grup IDN Academy Programmer.
   - Jika jam 09.00 tiba & BELUM approved (pending): tahan pengiriman, ingatkan Zulfi di review group.
3. approve: Handler konfirmasi dari chat jika Zulfi sudah konfirmasi benar/sesuai.
"""

import sys
import os
import json
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# Path & Identifiers
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

STATE_FILE = "/opt/data/profiles/idn-programmer/cache/timebox_approval_state.json"
IMAGE_PATH = "/opt/data/timebox-latest.png"
BRIDGE_URL = "http://localhost:3000"

REVIEW_GROUP_JID = "120363430531430052@g.us"       # Group Zulfi / review
ACADEMY_GROUP_JID = "120363413164988159@g.us"      # Group IDN Academy Programmer 2026-2027

HARI_INDO = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
BULAN_INDO = [
    "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember"
]


def get_current_time():
    return datetime.now(ZoneInfo("Asia/Jakarta"))


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading state: {e}", file=sys.stderr)
    return {}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def send_whatsapp_text(chat_id, message):
    try:
        res = requests.post(
            f"{BRIDGE_URL}/send",
            json={"chatId": chat_id, "message": message},
            timeout=15
        )
        return res.status_code == 200
    except Exception as e:
        print(f"Error sending text to {chat_id}: {e}", file=sys.stderr)
        return False


def send_whatsapp_media(chat_id, file_path, caption=""):
    try:
        res = requests.post(
            f"{BRIDGE_URL}/send-media",
            json={
                "chatId": chat_id,
                "filePath": file_path,
                "mediaType": "image",
                "caption": caption
            },
            timeout=30
        )
        return res.status_code == 200
    except Exception as e:
        print(f"Error sending media to {chat_id}: {e}", file=sys.stderr)
        return False


def build_formal_caption(now=None):
    # Format caption resmi permintaan Zulfi untuk grup IDN Academy Programmer
    return "Selamat pagi, berikut timebox Andryan untuk hari ini"


def init_draft_state():
    """Dipanggil saat draf 07.30 selesai diunduh & dikirim ke grup review."""
    now = get_current_time()
    today_str = now.strftime("%Y-%m-%d")

    # Jika hari Jumat -> Libur rutin
    if now.weekday() == 4:
        state = {
            "date": today_str,
            "status": "holiday",
            "updated_at": now.isoformat()
        }
        save_state(state)
        print("Hari ini hari Jumat (Libur rutin). State diset holiday.")
        return state

    caption = build_formal_caption(now)
    state = {
        "date": today_str,
        "status": "pending",
        "draft_sent_at": now.isoformat(),
        "approved_at": None,
        "sent_at": None,
        "reminder_count": 0,
        "last_reminder_at": None,
        "image_path": IMAGE_PATH,
        "caption": caption
    }
    save_state(state)
    print(f"Draft state initialized for {today_str} (pending approval).")
    return state


def approve_draft():
    """Dipanggil ketika Zulfi mengonfirmasi draf di chat ini."""
    now = get_current_time()
    today_str = now.strftime("%Y-%m-%d")
    state = load_state()

    if state.get("date") != today_str:
        state = init_draft_state()

    if state.get("status") == "sent":
        return {
            "action": "already_sent",
            "message": "Timebox hari ini sudah terkirim sebelumnya ke grup IDN Academy Programmer."
        }

    state["approved_at"] = now.isoformat()

    # Ketika Zulfi konfirmasi (jam 07.30 atau kapan pun), LANGSUNG kirim ke grup IDN Academy Programmer
    caption = build_formal_caption(now)
    img_path = state.get("image_path", IMAGE_PATH)

    success = send_whatsapp_media(ACADEMY_GROUP_JID, img_path, caption)
    if success:
        state["status"] = "sent"
        state["sent_at"] = now.isoformat()
        save_state(state)
        # Notif balik ke review group
        send_whatsapp_text(
            REVIEW_GROUP_JID,
            f"✅ *Laporan Pengiriman Timebox:*\nFoto timebox hari ini telah resmi terkirim ke grup *IDN Academy Programmer 2026-2027* pukul {now.strftime('%H.%M')} WIB."
        )
        return {
            "action": "dispatched",
            "message": "Draf disetujui dan foto timebox telah langsung dikirimkan ke grup IDN Academy Programmer 2026-2027! 🚀"
        }
    else:
        save_state(state)
        return {
            "action": "failed_dispatch",
            "message": "Draf disetujui tetapi gagal mengirim media ke grup IDN Academy Programmer. Silakan cek koneksi bridge."
        }


def check_and_tick():
    """
    Checker cron job (berjalan setiap 30 menit dari jam 08.00 s/d 11.30).
    Jadwal cron: 0,30 8-11 * * 0,1,2,3,4,6
    Target batas kirim otomatis: 08.30 WIB.
    """
    now = get_current_time()
    today_str = now.strftime("%Y-%m-%d")

    # Hari Jumat libur
    if now.weekday() == 4:
        return

    state = load_state()
    if state.get("date") != today_str:
        # Belum ada state untuk hari ini, lewati
        return

    status = state.get("status")
    current_minutes = now.hour * 60 + now.minute
    target_minutes = 8 * 60 + 30  # 08.30 WIB

    # 1. Jika sudah sent atau holiday, tidak ada yang perlu dilakukan
    if status in ["sent", "holiday"]:
        return

    # 2. Jika status SUDAH APPROVED
    if status == "approved":
        if current_minutes >= target_minutes:
            caption = build_formal_caption(now)
            img_path = state.get("image_path", IMAGE_PATH)
            success = send_whatsapp_media(ACADEMY_GROUP_JID, img_path, caption)
            if success:
                state["status"] = "sent"
                state["sent_at"] = now.isoformat()
                save_state(state)
                send_whatsapp_text(
                    REVIEW_GROUP_JID,
                    f"✅ *Laporan Pengiriman Timebox:*\nFoto timebox hari ini telah resmi terkirim ke grup *IDN Academy Programmer 2026-2027* pukul {now.strftime('%H.%M')} WIB."
                )
                print(f"Timebox sent to academy group at {now.strftime('%H:%M')}")
        return

    # 3. Jika status MASIH PENDING (Zulfi belum konfirmasi)
    if status == "pending":
        # Tepat jam 08.30 WIB
        if now.hour == 8 and now.minute >= 25 and now.minute <= 35:
            msg = (
                "⚠️ *Pengingat Timebox (08.30 WIB)*\n\n"
                "Waktu pengiriman timebox pukul 08.30 WIB sudah tiba, namun pengiriman ke grup *IDN Academy Programmer 2026-2027* **ditahan sementara** karena draf belum dikonfirmasi oleh Zulfi.\n\n"
                "Mohon cek draf foto timebox di atas dan balas chat ini (apakah jadwal sudah sesuai / ada perbaikan) agar bisa langsung segera dikirimkan."
            )
            send_whatsapp_text(REVIEW_GROUP_JID, msg)
            state["reminder_count"] = state.get("reminder_count", 0) + 1
            state["last_reminder_at"] = now.isoformat()
            save_state(state)
            print("Held delivery at 08.30 WIB because pending approval. Sent warning.")
            return

        # Cek debouncing: minimal 25 menit dari reminder / draft terakhir
        last_time_str = state.get("last_reminder_at") or state.get("draft_sent_at")
        if last_time_str:
            try:
                last_dt = datetime.fromisoformat(last_time_str)
                if (now - last_dt).total_seconds() < 25 * 60:
                    print("Skipping reminder, less than 25 minutes since last notice.")
                    return
            except Exception:
                pass

        if current_minutes < target_minutes:
            # Jam 08.00
            msg = (
                f"🔔 *Pengingat Konfirmasi Timebox ({now.strftime('%H.%M')} WIB)*\n\n"
                "Halo Zulfi, mengingatkan kembali untuk pengecekan draf timebox hari ini. Apakah jadwal sudah sesuai atau ada yang perlu diperbaiki sebelum jadwal kirim pukul 08.30 WIB nanti?\n\n"
                "👉 Silakan balas chat ini ya."
            )
            send_whatsapp_text(REVIEW_GROUP_JID, msg)
            state["reminder_count"] = state.get("reminder_count", 0) + 1
            state["last_reminder_at"] = now.isoformat()
            save_state(state)
            print(f"Sent reminder at {now.strftime('%H:%M')} WIB.")
        else:
            # Jam 09.00, 09.30, 10.00, dst (setelah 08.30 tapi belum dijawab)
            msg = (
                f"🔔 *Pengingat Konfirmasi Timebox ({now.strftime('%H.%M')} WIB)*\n\n"
                "Pengiriman timebox ke grup IDN Academy Programmer masih tertahan menunggu konfirmasi Zulfi.\n\n"
                "👉 Mohon balas chat ini jika sudah oke agar bisa langsung segera dikirimkan."
            )
            send_whatsapp_text(REVIEW_GROUP_JID, msg)
            state["reminder_count"] = state.get("reminder_count", 0) + 1
            state["last_reminder_at"] = now.isoformat()
            save_state(state)
            print(f"Sent post-08:30 reminder at {now.strftime('%H:%M')} WIB.")


def update_draft_note(new_note):
    """Memperbarui state jika ada revisi draf."""
    state = load_state()
    state["status"] = "pending"
    state["caption"] = build_formal_caption(get_current_time())
    save_state(state)
    print("Draft updated and reset to pending.")


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "tick"

    if action == "init":
        init_draft_state()
    elif action == "tick":
        check_and_tick()
    elif action == "approve":
        res = approve_draft()
        print(json.dumps(res, indent=2))
    elif action == "status":
        st = load_state()
        print(json.dumps(st, indent=2))
    else:
        print(f"Unknown action: {action}")
