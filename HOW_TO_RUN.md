# AeroTwin — How to Run

Two servers, run in two separate terminals: the Python backend (FastAPI,
port 8000) and the React frontend (Vite, port 5173). Start the backend
first — the frontend connects to it immediately on load.

---

## 1. Backend (Terminal 1)

**Windows (PowerShell):**
```powershell
cd aerotwin\backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**macOS / Linux:**
```bash
cd aerotwin/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

You should see `Uvicorn running on http://127.0.0.1:8000`. Leave this
terminal running. Test it worked by opening
http://127.0.0.1:8000/api/engine/status in a browser — you should get JSON
back, not an error.

> Every time you come back later, you only need to re-activate the venv
> (`venv\Scripts\Activate.ps1` or `source venv/bin/activate`) and re-run the
> `uvicorn` command — no need to `pip install` again unless requirements.txt
> changed.

---

## 2. Frontend (Terminal 2 — open a NEW terminal, leave the backend running)

```bash
cd aerotwin/frontend
npm install
npm run dev
```

Vite will print a local URL — open **http://localhost:5173** in your
browser. That's the dashboard. It talks to the backend at
`http://127.0.0.1:8000` automatically (configured in
`frontend/src/services/api.js`) — no extra setup needed as long as both
are running on the same machine with the default ports.

> `npm install` only needs to be run once (or again if `package.json`
> changes). After that, `npm run dev` is all you need.

---

## 3. Using the dashboard (software simulator — no Arduino needed)

With both servers running, the dashboard should show live data
immediately, sourced from the built-in software engine simulator. Use the
on-screen controls to trigger scenarios (overheating, vibration, etc.) and
watch Health / Fault Risk / Degradation respond.

---

## 4. Switching to real Arduino hardware (optional, once wiring is done)

This needs a THIRD terminal, in addition to the two above, plus the
Arduino UNO plugged in via USB with the corrected sketch already flashed.

**Step A — Restart the backend in hardware mode** (stop Terminal 1 with
Ctrl+C, then):

Windows (PowerShell):
```powershell
$env:USE_HARDWARE="1"; uvicorn main:app --reload --port 8000
```
macOS/Linux:
```bash
USE_HARDWARE=1 uvicorn main:app --reload --port 8000
```

**Step B — Find your Arduino's port:**
- Windows: Device Manager → Ports (COM & LPT) → note the COMx number
- macOS: `ls /dev/cu.*`
- Linux: `ls /dev/ttyUSB*` or `ls /dev/ttyACM*`

**Step C — Run the serial bridge (Terminal 3):**
```bash
cd aerotwin/backend/hardware/serial_bridge
pip install pyserial requests
python bridge.py --port COM5              # Windows example
python bridge.py --port /dev/cu.usbmodem14101   # macOS example
python bridge.py --port /dev/ttyUSB0      # Linux example
```

You should see lines like `{'pressure': 4.532}  ->  OK (accepted)`
printing continuously. If you see `REJECTED: ...`, re-check that the
backend in Terminal 1 was restarted with `USE_HARDWARE=1` set.

Then, in the dashboard itself, switch the data source to **Arduino** (or
use the Connect button in the Arduino modal) to start displaying the live
readings.

---

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Frontend loads but shows no data / connection error | Backend isn't running, or isn't on port 8000 — check Terminal 1 |
| `npm install` fails | Check Node.js version (`node -v`) — needs Node 18+ |
| `pip install` fails | Check Python version (`python --version`) — needs Python 3.10+ |
| Bridge prints `REJECTED` | Backend wasn't restarted with `USE_HARDWARE=1` |
| Other sensor graphs move when turning one knob | Re-flash the `.ino` (see `backend/hardware/arduino_uno_potentiometer/`) — see project chat history / README there |
