#!/usr/bin/env python3
"""
Manajer Anggota & Kontrol Akses (RBAC) IDN Academy.
Mengatur registrasi nomor HP perkenalan anggota dan validasi hak akses:
- Admin (Andryan / Zulfi): Full control
- Ketua Aktif: Berdasarkan jadwal rotasi 2 mingguan (Sabtu - Jumat)
- Peserta Biasa / Akdev: Hanya interaksi biasa, tidak boleh ubah aturan/jadwal.
- Akdev tidak memiliki jatah giliran ketua.
"""

import sys
import json
import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

DATA_PATHS = [
    Path("/opt/data/data/idn_members.json"),
    Path("/opt/data/profiles/idn-academy/data/idn_members.json")
]

ADMIN_PHONE = "6288803918389"
ADMIN_LID = "224983305470121@lid"
ANCHOR_DATE = datetime.date(2026, 9, 26)  # Angga (index 6)

ROSTER_KETUA = [
    ("Hilman", "62895336902593"),
    ("Hanif", "6285692214982"),
    ("Rizal", "6282157461646"),
    ("Andryan", "6288803918389"),
    ("Fajru", "62887437239818"),
    ("Ridho", "6285811538319"),
    ("Angga", "6285156500314"),
    ("Adly", "6285179518681"),
    ("Naufal", "6281328117870"),
    ("Yazid", "6282112162443"),
    ("Kahfi", "6285751202762"),
]

def load_data():
    for p in DATA_PATHS:
        if p.exists():
            try:
                return json.loads(p.read_text())
            except Exception:
                pass
    return {"members": {}, "ketua_schedule": []}

def save_data(data):
    for p in DATA_PATHS:
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        except Exception:
            pass

def get_active_ketua(target_date=None):
    if target_date is None:
        tz = ZoneInfo("Asia/Jakarta")
        target_date = datetime.datetime.now(tz).date()
    delta_days = (target_date - ANCHOR_DATE).days
    period = delta_days // 14
    idx = (6 + period) % len(ROSTER_KETUA)
    return ROSTER_KETUA[idx]

def check_permission(phone_or_lid):
    clean = str(phone_or_lid).replace("@s.whatsapp.net", "").replace("@lid", "").strip()
    if clean in (ADMIN_PHONE, ADMIN_LID, "224983305470121"):
        return True, "admin", "Andryan (Zulfi)"
    
    ketua_name, ketua_phone = get_active_ketua()
    if clean == ketua_phone:
        return True, "ketua", ketua_name
    
    data = load_data()
    # Check if this phone belongs to ketua_name in registered data
    member_info = data.get("members", {}).get(ketua_name)
    if member_info and member_info.get("phone") == clean:
        return True, "ketua", ketua_name

    return False, "member", None

def register_member(name, phone):
    data = load_data()
    clean_phone = str(phone).replace("@s.whatsapp.net", "").replace("@lid", "").replace("+", "").strip()
    
    # Matching name case-insensitive
    target_key = None
    for k in data.get("members", {}):
        if k.lower() == name.lower():
            target_key = k
            break
    
    if not target_key:
        target_key = name.capitalize()
        category = "akdev" if "akdev" in name.lower() else "regular"
        data.setdefault("members", {})[target_key] = {
            "phone": clean_phone,
            "category": category,
            "verified": True
        }
    else:
        data["members"][target_key]["phone"] = clean_phone
        data["members"][target_key]["verified"] = True
    
    save_data(data)
    
    ketua_name, _ = get_active_ketua()
    is_ketua = (target_key.lower() == ketua_name.lower())
    
    return {
        "success": True,
        "name": target_key,
        "phone": clean_phone,
        "is_active_ketua": is_ketua,
        "category": data["members"][target_key].get("category", "regular")
    }

def main():
    if len(sys.argv) < 2:
        name, phone = get_active_ketua()
        print(f"Ketua aktif saat ini: {name} ({phone})")
        return

    cmd = sys.argv[1].lower()
    if cmd == "check":
        phone = sys.argv[2] if len(sys.argv) > 2 else ""
        allowed, role, name = check_permission(phone)
        print(json.dumps({"allowed": allowed, "role": role, "name": name}))
    elif cmd == "register":
        if len(sys.argv) < 4:
            print("Usage: member_manager.py register <name> <phone>")
            sys.exit(1)
        name = sys.argv[2]
        phone = sys.argv[3]
        res = register_member(name, phone)
        print(json.dumps(res))
    elif cmd == "status":
        tz = ZoneInfo("Asia/Jakarta")
        today = datetime.datetime.now(tz).date()
        k_name, k_phone = get_active_ketua(today)
        data = load_data()
        print(f"Tanggal: {today.isoformat()}")
        print(f"Ketua Aktif: {k_name} ({k_phone})")
        print("\nDaftar Member:")
        for m, inf in data.get("members", {}).items():
            print(f"- {m}: {inf.get('phone')} (kat: {inf.get('category')})")

if __name__ == "__main__":
    main()
