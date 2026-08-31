# AeroTwin — Real Hardware Integration (Arduino UNO)

This folder + the backend changes let you plug a real Arduino UNO with 5
potentiometers into the existing AeroTwin pipeline **without changing
anything** in preprocessing, feature engineering, the ML models, the
digital twin, mission assessment, or the frontend. They all keep working
exactly as before — they just now receive real sensor data instead of
simulated data.

## How it works

- `arduino_uno_potentiometer/arduino_uno_potentiometer.ino` — reads **5
  potentiometers** on A0–A4 (RPM, Temperature, Vibration, Pressure, Load)
  and prints one JSON line over USB serial per second.
- `serial_bridge/bridge.py` — runs on your laptop, reads those serial
  lines, and forwards each one as an HTTP POST to the backend's
  `/api/engine/ingest` endpoint. (The UNO can't POST over WiFi itself, so
  this bridge sits in the middle — it's the only reason a "bridge"
  script exists at all.)
- `backend/simulator/hardware_ingest.py` — a `HardwareIngest` class with
  the same `tick()` interface as `EngineSimulator`, but it returns
  whatever sample was last POSTed instead of generating synthetic values.
- `backend/main.py` — the `POST /api/engine/ingest` endpoint `bridge.py`
  calls once per second. A `USE_HARDWARE` env var switches which source
  (`EngineSimulator` vs `HardwareIngest`) the background loop reads from.

## Wiring — 5 potentiometers

Each potentiometer has 3 pins:
- One outer pin -> Arduino `5V` (all 5 pots can share the same 5V rail)
- Other outer pin -> Arduino `GND` (all 5 pots can share the same GND rail)
- Middle pin (wiper) -> its own analog pin — this is the only wire unique
  to each potentiometer:

| Pin | Reads |
|---|---|
| A0 | RPM |
| A1 | Temperature |
| A2 | Vibration |
| A3 | Pressure |
| A4 | Load |

Only have 1–4 potentiometers on hand? Open the `.ino` file and set the
`ENABLE_RPM` / `ENABLE_TEMPERATURE` / `ENABLE_VIBRATION` / `ENABLE_PRESSURE`
/ `ENABLE_LOAD` flags near the top to `true` only for the knob(s) you
actually have wired — leave the rest `false`. You don't need to delete or
comment out any code. A disabled channel's pin is never read (so it can't
pick up floating-pin noise) and its key is left out of the JSON; the
backend fills in a healthy baseline value for any field the JSON doesn't
include (see "Honest limitations" below), so only the channel(s) you
enabled will actually move on the dashboard — a partial rig still works
correctly. No Python or backend changes needed either way — `bridge.py`
forwards whatever fields the board sends, and `hardware_ingest.py` merges
them in.

**If you only wire up one potentiometer but every dashboard value still
seems to move:** that's a floating-pin symptom — double check every
`ENABLE_*` flag for the sensors you *don't* have wired is set to `false`
(not just commented past). An analog pin with nothing connected to it
doesn't read as zero; it drifts on its own, and if its flag is left
`true` that drift gets sent and shown as if it were real movement.

## Running in hardware mode

1. Flash `arduino_uno_potentiometer.ino` via the Arduino IDE (select
   Board: "Arduino Uno", the correct Port, then Upload).
2. Close the Arduino IDE's Serial Monitor if it's open (only one program
   can read the serial port at a time — this trips people up constantly).
3. Install the bridge's dependencies:
   `pip install -r serial_bridge/requirements.txt`
   (or `pip install pyserial requests` directly)
4. Start the backend in hardware mode instead of the normal way:

   **macOS/Linux:**
   ```bash
   cd backend
   USE_HARDWARE=1 uvicorn main:app --reload
   ```

   **Windows (PowerShell):**
   ```powershell
   cd backend
   $env:USE_HARDWARE="1"; uvicorn main:app --reload
   ```

5. Run the bridge: `python bridge.py --port <your-port>`
   (Windows: check Device Manager for the COM port, e.g. `COM5`.
   macOS: `ls /dev/cu.*`. Linux: usually `/dev/ttyUSB0` or `/dev/ttyACM0`.)
6. Start the frontend as normal (`npm run dev` in `frontend/`). The
   dashboard doesn't need any changes — it just now shows real sensor
   data flowing through the same charts, ML predictions, and mission
   risk logic.
7. Check `GET /api/engine/hardware-status` (or the Overview page's
   **Hardware Status** panel, which should say "RECEIVING LIVE DATA") to
   confirm the board is actively sending. Turn any knob and watch that
   sensor's own card and chart move.

   Note: the **Health / Degradation / Fault Risk / RUL / Mission Risk**
   numbers are computed by the ML models from *all* channels combined, so
   turning even one knob far enough will nudge those too — that's the
   digital twin fusing the inputs as designed, not a bug. What should
   stay perfectly flat is any raw sensor card for a channel whose
   `ENABLE_*` flag you left `false`.

Leave `USE_HARDWARE` unset (or `0`) to go back to the normal software
simulator for demos where you don't have hardware on hand.

## Calibration — read this before trusting any numbers

The potentiometer ranges in the sketch are mapped to match the ranges
the ML models were trained on (see `ml/training/train_models.py`), but a
potentiometer's raw resistance curve isn't a real sensor's actual
physical response curve. Treat this as "the pipeline responds to real
input" rather than "these are physically accurate engine readings" until
you swap in genuine sensors (e.g. an MPU6050 for vibration, a thermistor
for temperature) on the pins you want to upgrade.

## Bench testing

You don't need a running engine or a flying drone to test this — turning
the 5 knobs by hand is enough to see real data flow end-to-end through
the dashboard, from serial line -> bridge -> backend -> ML models ->
digital twin -> frontend charts.

## Honest limitations of this setup

If all 5 potentiometers are wired, all 5 channels are real, live sensor
data. If you've only wired a subset, the remaining channel(s) sit at
their **healthy baseline values** (4200 RPM, 72°C, 1.2 mm/s, 4.2 bar, 55%
load) rather than zero — zero would otherwise read as a false critical
fault to the ML pipeline regardless of what your wired knob is doing.
