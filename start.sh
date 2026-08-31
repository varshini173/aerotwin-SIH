#!/usr/bin/env bash
# ============================================================
# AeroTwin - One-click start (macOS / Linux)
# Run ./setup.sh once first, then: chmod +x start.sh && ./start.sh
# Starts both backend and frontend, and opens the dashboard.
# Press Ctrl+C to stop both.
# ============================================================
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cleanup() {
    echo "Stopping AeroTwin..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}
trap cleanup INT TERM

cd "$ROOT/backend"
source venv/bin/activate
uvicorn main:app --reload &
BACKEND_PID=$!

sleep 3

cd "$ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

sleep 4

if command -v open >/dev/null 2>&1; then
    open http://localhost:5173/
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open http://localhost:5173/
fi

echo
echo "AeroTwin is running. Press Ctrl+C to stop both servers."
wait
