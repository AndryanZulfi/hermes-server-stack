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
 (Decoupled Git Repo)          (Prometheus :9090, Grafana :3001)
```

## Directory Structure

* **`9router-hermes/`**: Core agent orchestration:
  * `9router`: LLM reverse proxy and routing gateway (port 20128).
  * `hermes`: Autonomous AI Agent gateway and runtime environment (ports 8642, 9119).
* **`honcho/`**: Dialectic memory engine and persistent cognitive graph (ports 8000, 8443).
* **`monitoring/`**: Observability telemetry stack (Prometheus :9090, Grafana :3001, cAdvisor, Node Exporter).
* **`galaxy-view/`**: Real-time interactive neural skill constellation map (port 8899 / Tailscale :8444).

## Disaster Recovery & Deployment

### 1. Prerequisites
```bash
# Create shared bridge network
docker network create ai-network 2>/dev/null || true
```

### 2. Configure Environment Files
Copy each `.env.example` to `.env` and fill in your respective API keys and credentials:
```bash
cp 9router-hermes/.env.example 9router-hermes/.env
cp monitoring/.env.example monitoring/.env
cp honcho/.env.template honcho/.env
```

### 3. Connect Hermes Skills
The skills ecosystem is decoupled in its own modular repository:
```bash
git clone https://github.com/AndryanZulfi/hermes-skills.git 9router-hermes/hermes-data/skills
```

### 4. Launch the Entire Stack
```bash
# 1. Start core LLM Router & Hermes Brain
cd 9router-hermes && docker compose up -d && cd ..

# 2. Start Honcho Memory
cd honcho && docker compose up -d && cd ..

# 3. Start Galaxy View Visualizer
cd galaxy-view && docker compose up -d && cd ..

# 4. Start Monitoring (Optional)
cd monitoring && docker compose up -d && cd ..
```
