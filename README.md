# Hermes Agent Server Infrastructure Stack

Production infrastructure blueprint and Docker orchestration for **Hermes Agent** and supporting microservices on `deb-zlf`.

## Architecture Overview

```
                        [ Internet / Tailnet ]
                                  │
                                  ▼
                        [ Tailscale Gateway ]
                 ┌────────────────┼────────────────┐
                 ▼                ▼                ▼
            :443 (HTTPS)     :8443 (HTTPS)    :8444 (HTTPS)
             [ 9router ]       [ Honcho ]     [ Galaxy View ]
                 │                │                │
                 └────────┬───────┴────────────────┘
                          ▼
                  [ Hermes Agent ]
                  (Core Brain :8642)
                          │
         ┌────────────────┴────────────────┐
         ▼                                 ▼
   [ hermes-skills ]             [ Monitoring Stack ]
 (Decoupled Submodule)         (Prometheus :9090, Grafana :3001)
```

## Directory Structure

* **`9router-hermes/`**: Core agent orchestration:
  * `9router`: LLM reverse proxy and routing gateway (port 20128).
  * `hermes`: Autonomous AI Agent gateway and runtime environment (ports 8642, 9119).
* **`galaxy-view/`**: Real-time interactive neural skill constellation map with 285 Agency specialists and Hermes skills (port 8899 / Tailscale :8444).
* **`skills/`**: Git submodule pointing to [`hermes-skills`](https://github.com/AndryanZulfi/hermes-skills.git).
* **`honcho/`**: Git submodule pointing to [`honcho`](https://github.com/plastic-labs/honcho.git) (ports 8000, 8443).
* **`hermes-config/`**: Portable seed templates for zero-touch configuration:
  * `memories/`: Persistent user persona (`USER.md`) and operational context (`MEMORY.md`).
  * `user.md` & `SOUL.md`: Identity and behavioral directives.
  * `plugins/`: Loaded plugins (`agency-agents-router`, `galaxy-telemetry`).
  * `cron/`: Scheduled jobs (`jobs.json`).
  * `config.yaml.template`: Sanitized Hermes agent configuration.
* **`monitoring/`**: Observability telemetry stack (Prometheus :9090, Grafana :3001, cAdvisor, Node Exporter).

---

## 1-Click Deployment (Zero-Touch Setup)

When setting up on a fresh machine:

```bash
# 1. Clone repository with submodules
git clone --recursive https://github.com/AndryanZulfi/hermes-server-stack.git
cd hermes-server-stack

# 2. Run bootstrap script (sets up memories, skills, plugins, cron, galaxy-view)
./setup.sh

# 3. Configure secrets in .env
# Edit 9router-hermes/.env with your LLM API keys and credentials
nano 9router-hermes/.env

# 4. Launch all services
docker compose -f 9router-hermes/docker-compose.yml up -d
docker compose -f galaxy-view/docker-compose.yml up -d
docker compose -f honcho/docker-compose.yml up -d
```

---

## Managing Galaxy View (Gravity View)

The interactive skill visualizer is containerized under `galaxy-view`:
* **Port Internal:** `http://localhost:8899`
* **Tailscale Serve:** `https://deb-zlf.tail38902e.ts.net:8444/`
* **Features:** 360° celestial orbit, unified PointerEvents drag-and-drop, real-time telemetry integration with Hermes Agent.

```bash
cd galaxy-view
docker compose up -d --build
```

---

## Syncing & Backups

To sync your skills and configurations across devices:

```bash
# Push skills updates
git -C skills add -A && git -C skills commit -m "update skills" && git -C skills push

# Push stack and configuration updates
git add -A && git commit -m "update server stack & configs" && git push
```
