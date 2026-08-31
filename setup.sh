#!/usr/bin/env bash
# ============================================================
# AeroTwin - One-time setup (macOS / Linux)
# Run this ONCE after extracting the project:
#   chmod +x setup.sh && ./setup.sh
# ============================================================
set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo
echo "=== Setting up backend (Python) ==="
cd "$ROOT/backend"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo
echo "=== Setting up frontend (Node) ==="
cd "$ROOT/frontend"
npm install

echo
echo "=== Setup complete! ==="
echo "Run ./start.sh any time to launch the app."
