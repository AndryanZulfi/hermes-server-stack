Infrastructure Tailscale URLs: 9router public endpoint at https://deb-zlf.tail38902e.ts.net/v1 (LLM gateway), Honcho API at https://deb-zlf.tail38902e.ts.net:8443 (port 8443 -> 8000). Both on deb-zlf host via Tailscale network.
§
Host deb-zlf (running 9router, hermes, honcho, Tailscale): IP 172.23.0.134 (user: zulfi, pass: zlf, pass root: zlf_16)
§
Google Workspace OAuth terhubung: token tersimpan di /opt/data/google_token.json dan kredensial di /opt/data/google_client_secret.json (Project ID: hermes-assistant-509114). Google Calendar, Google Sheets, dan Google Drive API aktif dan terverifikasi. Drive/Gmail/Docs memiliki scope token.
§
WhatsApp Groups: 'Group ku' (6288803918389-1617164069@g.us), IDN Academy 'Cod musang area palmerah' (120363410899436681@g.us), 'IDN Academy 2026-2027' (120363427809492701@g.us), IDN Programmer (120363430531430052@g.us), 'Report & Log Agent' (120363414423509222@g.us). Bot sender: +6281283274820. Deliver format: 'whatsapp:<group_id>@g.us'. IDN Academy RBAC: 2-mode (data/group_mode.json default 'open'; scripts/group_mode.py admin-only switch; AGENTS.md rules; ketua rotate in /opt/data/scripts/rotate_ketua.py). Transport: group_policy=allowlist lets ALL group members chat; allow_from (admin+ketua) gates only DMs.
§
Hermes cron config gotcha: global LLM provider for cron must be pinned via `cron.model_provider: custom:9router` in config.yaml, otherwise agent-based cron jobs take bare 'custom' snapshot and fail auth against OpenRouter.
WhatsApp bridge: bot number is +6281283274820; group delivery uses target 'whatsapp:<group_id>@g.us'. "Cod musang area palmerah" group ID: 120363410899436681@g.us.
Docker setup: env_file points to ./hermes-data/.env (/opt/data/.env inside container) as single source of truth.
§
Project NARA: Repo https://github.com/AndryanZulfi/mockup-nara, branch `feat/nara-mvp-v2` (Fiber :8088 + Nuxt :3000).§Agents Office: /opt/data/agents-office cloned from ajsahni/agents-office, Hermes backend adapter ready (hermes-backend.mjs), Docker :4520 on ai-network. Default: Claude CLI backend. Hermes opt-in: env AGENTS_OFFICE_BACKEND=hermes (CLI hang issue pending fix).