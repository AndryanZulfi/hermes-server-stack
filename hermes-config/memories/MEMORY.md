Infrastructure Tailscale URLs: 9router public endpoint at https://deb-zlf.tail38902e.ts.net/v1 (LLM gateway), Honcho API at https://deb-zlf.tail38902e.ts.net:8443 (port 8443 -> 8000). Both on deb-zlf host via Tailscale network.
§
Host deb-zlf (running 9router, hermes, honcho, Tailscale): IP 172.23.0.134 (user: zulfi, pass: zlf, pass root: zlf_16)
§
Google Workspace OAuth terhubung: token tersimpan di /opt/data/google_token.json dan kredensial di /opt/data/google_client_secret.json (Project ID: hermes-assistant-509114). Google Calendar, Google Sheets, dan Google Drive API aktif dan terverifikasi. Drive/Gmail/Docs memiliki scope token.
§
WhatsApp Groups: 'Group ku' (6288803918389-1617164069@g.us), COD area palmerah (120363410899436681@g.us), Kitchen IDN Academy (120363427693771326@g.us), IDN Academy 2026-2027 (120363427809492701@g.us), IDN Programmer (120363430531430052@g.us), Report & Log (120363414423509222@g.us). Bot: +6281283274820. IDN RBAC: Semua boleh chat di grup, ubah aturan HANYA Admin Zulfi (6288803918389) & Ketua Aktif (rotasi 2 mingguan ganti Sabtu; Akdev tidak dapat jatah ketua). Member kenalan dicatat di data/idn_members.json. Piket Ompreng: 5 kelompok rolling harian (07.30, 12.50, 20.45 WIB, anchor 5 Nov 2026: Andryan, Hilman, Yazid). Piket Bantu Dapur: 7 kelompok rolling weekend Sabtu-Minggu 07.00 WIB. Delivery pengingat piket diarahkan ke grup Kitchen IDN Academy. Scripts: piket_reminder.py, member_manager.py, rotate_ketua.py.
§
Hermes cron: LLM provider pinned via cron.model_provider: custom:9router in config.yaml. Docker env: ./hermes-data/.env (/opt/data/.env).
§
Project NARA: Repo https://github.com/AndryanZulfi/mockup-nara, branch `feat/nara-mvp-v2` (Fiber :8088 + Nuxt :3000).§Agents Office: /opt/data/agents-office cloned from ajsahni/agents-office, Hermes backend adapter ready (hermes-backend.mjs), Docker :4520 on ai-network. Default: Claude CLI backend. Hermes opt-in: env AGENTS_OFFICE_BACKEND=hermes (CLI hang issue pending fix).