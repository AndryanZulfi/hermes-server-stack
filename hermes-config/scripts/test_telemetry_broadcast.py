#!/usr/bin/env python3
import json
import urllib.request
import sys

URL = "http://hermes-galaxy-view:8899/api/telemetry"

transmissions = [
    {
        "action": "route_llm",
        "from": "hermes",
        "to": "service-9router",
        "target": "model-agy-combo",
        "label": "9Router: agy-combo",
        "detail": "Routing reasoning tokens via 9Router gateway to agy-combo",
        "color": "#8b5cf6",
        "duration_s": 25.0
    },
    {
        "action": "honcho_query",
        "from": "hermes",
        "to": "service-honcho",
        "target": "dep-honcho-db",
        "label": "Honcho: Cognitive Memory",
        "detail": "Querying dialectic user representations & profile",
        "color": "#10b981",
        "duration_s": 25.0
    },
    {
        "action": "skill_activated",
        "from": "hermes",
        "to": "service-skills",
        "target": "skill-realtime-agent-telemetry-ui",
        "label": "Skill: realtime-telemetry",
        "detail": "Rendering SVG & Canvas neural constellation",
        "color": "#a855f7",
        "duration_s": 25.0
    },
    {
        "action": "mcp_query",
        "from": "hermes",
        "to": "service-mcp",
        "target": "mcp-docker",
        "label": "MCP: Docker Engine",
        "detail": "Streaming telemetry stats & health for 12 containers",
        "color": "#3b82f6",
        "duration_s": 25.0
    },
    {
        "action": "agent_activated",
        "from": "hermes",
        "to": "service-agents",
        "target": "service-agents",
        "label": "Agent: DevOps Specialist",
        "detail": "Orchestrating multi-container network health",
        "color": "#ec4899",
        "duration_s": 25.0
    }
]

for tx in transmissions:
    req = urllib.request.Request(
        URL,
        data=json.dumps(tx).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        label = tx["label"]
        print(f"✓ Broadcasted {label} (HTTP {resp.status})")

# Verify active transmissions
with urllib.request.urlopen("http://hermes-galaxy-view:8899/api/active") as resp:
    data = json.loads(resp.read().decode())
    active_tx = data.get("transmissions", [])
    print(f"\n📡 Active Telemetry Transmissions on Galaxy View: {len(active_tx)}")
    for t in active_tx:
        print(f"  • [{t.get('action')}] {t.get('from')} ➔ {t.get('to')} ({t.get('label')})")
