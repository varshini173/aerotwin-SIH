#!/usr/bin/env bash
# ============================================================
# AeroTwin — One-click hardware-mode launcher (macOS / Linux)
# Run this from wherever this file lives:
#   chmod +x start_hardware.sh && ./start_hardware.sh
# It will:
#   1. Set up the backend venv if it doesn't exist yet
#   2. Start the backend in hardware mode (USE_HARDWARE=1)
#   3. Ask you for your Arduino's serial port and start the
#      serial bridge
#   4. Start the frontend
#   5. Open the dashboard in your browser
# Press Ctrl+C to stop all three.
# ============================================================
set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cleanup() {
    echo "Stopping AeroTwin..."
    kill $BACKEND_PID $BRIDGE_PID $FRONTEND_PID 2>/dev/null
    exit 0
}
trap cleanup INT TERM

echo "=== Setting up backend venv (if needed) ==="
cd "$ROOT/backend"
if [ ! -d venv ]; then
    python3 -m venv venv
fi
. venv/bin/activate
pip install -q -r requirements.txt

echo
echo "=== [1/3] Starting backend in hardware mode ==="
USE_HARDWARE=1 uvicorn main:app --reload &
BACKEND_PID=$!

sleep 3

echo
echo "=== [2/3] Starting serial bridge ==="
echo "Check your Arduino's port first if unsure:"
echo "  macOS:  ls /dev/cu.*"
echo "  Linux:  ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null"
read -p "Enter your Arduino's serial port (e.g. /dev/cu.usbmodem14101): " PORT
cd "$ROOT/backend/hardware/serial_bridge"
pip install -q -r requirements.txt
python bridge.py --port "$PORT" &
BRIDGE_PID=$!

echo
echo "=== [3/3] Starting frontend ==="
cd "$ROOT/frontend"
npm install
npm run dev &
FRONTEND_PID=$!

sleep 4

if command -v open >/dev/null 2>&1; then
    open http://localhost:5173/
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open http://localhost:5173/
fi

echo
echo "AeroTwin is running in hardware mode. On the Overview page, the"
echo "Hardware Status panel should say RECEIVING LIVE DATA within a few seconds."
echo "Press Ctrl+C to stop all three processes."
wait
