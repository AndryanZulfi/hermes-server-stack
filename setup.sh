#!/usr/bin/env bash
# ==============================================================================
# Hermes Server Stack — 1-Click Bootstrap Setup
# Clones submodules, seeds configuration, memories, skills, plugins, and Galaxy View
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================================="
echo "🚀 Initializing Hermes Server Stack..."
echo "========================================================="

# 1. Update Submodules (Honcho + Skills)
echo "📦 [1/6] Updating Git submodules (Honcho, Skills)..."
git submodule update --init --recursive

# 2. Setup Data Directories
echo "📁 [2/6] Preparing runtime directories..."
mkdir -p 9router-hermes/hermes-data/memories
mkdir -p 9router-hermes/hermes-data/plugins
mkdir -p 9router-hermes/hermes-data/cron
mkdir -p 9router-hermes/hermes-data/scripts
mkdir -p 9router-hermes/hermes-data/home
mkdir -p 9router-data
mkdir -p honcho-data
mkdir -p honcho-db-data
mkdir -p monitoring/prometheus_data
mkdir -p monitoring/grafana_data

# 3. Seed Hermes Configuration, Memories, Persona, and Cron
echo "🧠 [3/6] Seeding memories, user profile, soul, and cron jobs..."
if [ ! -f 9router-hermes/hermes-data/memories/MEMORY.md ] && [ -f hermes-config/memories/MEMORY.md ]; then
  cp hermes-config/memories/MEMORY.md 9router-hermes/hermes-data/memories/
fi
if [ ! -f 9router-hermes/hermes-data/memories/USER.md ] && [ -f hermes-config/memories/USER.md ]; then
  cp hermes-config/memories/USER.md 9router-hermes/hermes-data/memories/
fi
if [ ! -f 9router-hermes/hermes-data/user.md ] && [ -f hermes-config/user.md ]; then
  cp hermes-config/user.md 9router-hermes/hermes-data/
fi
if [ ! -f 9router-hermes/hermes-data/SOUL.md ] && [ -f hermes-config/SOUL.md ]; then
  cp hermes-config/SOUL.md 9router-hermes/hermes-data/
fi
if [ ! -f 9router-hermes/hermes-data/cron/jobs.json ] && [ -f hermes-config/cron/jobs.json ]; then
  cp hermes-config/cron/jobs.json 9router-hermes/hermes-data/cron/
fi
if [ ! -f 9router-hermes/hermes-data/config.yaml ] && [ -f hermes-config/config.yaml.template ]; then
  cp hermes-config/config.yaml.template 9router-hermes/hermes-data/config.yaml
fi

# Seed Plugins & Scripts
echo "🔌 [4/6] Seeding plugins and automation scripts..."
if [ -d hermes-config/plugins ]; then
  cp -rn hermes-config/plugins/* 9router-hermes/hermes-data/plugins/ 2>/dev/null || true
fi
if [ -d hermes-config/scripts ]; then
  cp -rn hermes-config/scripts/* 9router-hermes/hermes-data/scripts/ 2>/dev/null || true
fi

# 4. Link Skills and Galaxy View
echo "🌌 [5/6] Linking Skills and Galaxy View..."
if [ ! -e 9router-hermes/hermes-data/skills ]; then
  if [ -d skills ]; then
    ln -s ../../skills 9router-hermes/hermes-data/skills 2>/dev/null || cp -r skills 9router-hermes/hermes-data/skills
  fi
fi

if [ ! -e 9router-hermes/hermes-data/galaxy-view ]; then
  if [ -d galaxy-view ]; then
    ln -s ../../galaxy-view 9router-hermes/hermes-data/galaxy-view 2>/dev/null || cp -r galaxy-view 9router-hermes/hermes-data/galaxy-view
  fi
fi

# 5. Seed Environment Files (.env)
echo "🔐 [6/6] Verifying environment configuration (.env)..."
if [ ! -f 9router-hermes/.env ] && [ -f 9router-hermes/.env.example ]; then
  cp 9router-hermes/.env.example 9router-hermes/.env
  echo "⚠️  Created 9router-hermes/.env from .env.example. Please review your API keys and tokens."
fi
if [ ! -f monitoring/.env ] && [ -f monitoring/.env.example ]; then
  cp monitoring/.env.example monitoring/.env
fi

# Set appropriate permissions for container mount
chmod -R 777 9router-hermes/hermes-data 2>/dev/null || true

echo "========================================================="
echo "✅ Setup complete! All configurations & components seeded."
echo "========================================================="
echo "To start all services, run:"
echo "  docker compose -f 9router-hermes/docker-compose.yml up -d"
echo "  docker compose -f galaxy-view/docker-compose.yml up -d"
echo "========================================================="
