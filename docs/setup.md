# Setup Guide

Tested on a normal Windows/macOS/Linux student laptop. No GitHub, no cloud
deployment, no real UAV engine required.

## Prerequisites

- Python 3.10+ (tested on 3.12)
- Node.js 18+ (tested on 22)
- npm (bundled with Node.js)

## 1. Backend Setup

```bash
cd backend
python -m venv venv
```

Activate the virtual environment:

```bash
# Windows (cmd/PowerShell)
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the server:

```bash
uvicorn main:app --reload
```

You should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

Verify it's working:
- Open `http://127.0.0.1:8000/` — should return a JSON status message.
- Open `http://127.0.0.1:8000/docs` — interactive Swagger API docs.

The trained ML models are already committed under `backend/saved_models/`,
so the backend loads them immediately — you do **not** need to retrain
before running the demo.

### (Optional) Retrain models from scratch

```bash
# from the project root, with the backend venv still active
pip install -r backend/requirements.txt   # if not already installed
python ml/training/train_models.py
```

This regenerates `ml/datasets/synthetic_training_data.csv`,
`ml/evaluation/metrics.json` / `metrics.md`, and overwrites
`backend/saved_models/*.joblib`. Takes under a minute on a laptop CPU.

## 2. Frontend Setup

Open a **second terminal** (keep the backend running in the first):

```bash
cd frontend
npm install
npm run dev
```

You should see:

```
VITE ready in ... ms
➜  Local:   http://localhost:5173/
```

Open `http://localhost:5173/` in your browser. The Overview page should load
and, within a second or two, start showing live-updating sensor values —
this confirms the WebSocket connection to the backend succeeded (the sidebar
"System Status: OK" badge and header "LIVE CONNECTION: ACTIVE" badge both
turn green/cyan once connected).

### Environment variables (optional)

By default the frontend talks to `http://127.0.0.1:8000` (REST) and
`ws://127.0.0.1:8000` (WebSocket). To point at a different backend host/port,
create `frontend/.env.local`:

```
VITE_API_BASE=http://127.0.0.1:8000
VITE_WS_BASE=ws://127.0.0.1:8000
```

## 3. Troubleshooting

| Symptom | Fix |
|---|---|
| Frontend shows "Backend Disconnected" | Confirm `uvicorn main:app --reload` is still running and reachable at port 8000. |
| CORS error in browser console | Confirm you're accessing the frontend at `http://localhost:5173` (the backend's CORS allow-list is scoped to that origin). |
| `ModuleNotFoundError` on backend start | Re-run `pip install -r requirements.txt` inside the activated venv. |
| Charts show no data initially | Wait 2–3 seconds after the WebSocket connects — the chart buffer fills as live ticks arrive. |
| Port 8000 or 5173 already in use | Stop the other process, or run uvicorn with `--port 8001` / vite with `--port 5174` and update `VITE_API_BASE`/`VITE_WS_BASE` accordingly. |

## 4. Running the Demo

See `docs/demo.md` for the exact SIH demonstration sequence.
