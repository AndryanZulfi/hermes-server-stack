#!/usr/bin/env bash
set -e

# Resolusi default jika tidak diset di compose
SCREEN_RES="${RESOLUTION:-1600x900x24}"
DISPLAY="${DISPLAY:-:99}"
export DISPLAY

echo "=== 1. Starting Xvfb (Virtual Display $DISPLAY at $SCREEN_RES) ==="
Xvfb "$DISPLAY" -screen 0 "$SCREEN_RES" -ac +extension GLX +render -noreset &
sleep 1

echo "=== 2. Starting Openbox (Window Manager) ==="
openbox &
sleep 1

echo "=== 3. Starting x11vnc server ==="
x11vnc -display "$DISPLAY" -forever -shared -nopw -rfbport 5900 &
sleep 1

echo "=== 4. Starting noVNC (Websocket Proxy on Port 6080) ==="
websockify --web /usr/share/novnc 6080 localhost:5900 &
sleep 1

echo "=== 5. Starting Munder Difflin ==="
# Flag --no-sandbox wajib untuk Electron di dalam container Docker root
export ELECTRON_EXTRA_LAUNCH_ARGS="--no-sandbox --disable-dev-shm-usage"

# Jalankan Munder Difflin (mode preview/electron out)
exec npx electron . --no-sandbox
