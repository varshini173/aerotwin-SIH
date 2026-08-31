"""
FastAPI Backend — AeroTwin MALE UAV Engine Digital Twin
===========================================================
Single source of truth for engine state. Runs a background asyncio task
that ticks the engine simulator (~1 Hz), pushes samples through
preprocessing -> feature engineering -> ML prediction -> digital twin ->
mission assessment -> SQLite storage, and broadcasts the resulting state
over WebSocket to all connected frontend clients.

Run:
    uvicorn main:app --reload
Docs:
    http://127.0.0.1:8000/docs
"""

from __future__ import annotations

import asyncio
import json
import os
import threading
import time
from typing import Optional

import serial
from serial.tools import list_ports
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from digital_twin.twin_state import DigitalTwin
from features.feature_engineering import build_feature_vector, feature_dict
from mission.mission_assessment import assess_mission
from prediction.predictor import Predictor
from preprocessing.preprocess import Preprocessor
from simulator.engine_simulator import EngineSimulator, Scenario
from simulator.hardware_ingest import HardwareIngest
from storage.db import HistoryStore

# Set USE_HARDWARE=1 (env var) to source telemetry from a real Arduino UNO
# (via hardware/serial_bridge/bridge.py) POSTing to /api/engine/ingest,
# instead of the synthetic simulator. Everything downstream
# (preprocessing/features/ML/twin/mission) is unchanged either way.
USE_HARDWARE = os.environ.get("USE_HARDWARE", "0") == "1"

app = FastAPI(title="AeroTwin UAV Engine Digital Twin API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------
# Global engine subsystem instances (single-engine prototype)
# ---------------------------------------------------------------------
simulator = HardwareIngest() if USE_HARDWARE else EngineSimulator()
preprocessor = Preprocessor()
predictor = Predictor()
twin = DigitalTwin()
store = HistoryStore()

# ---------------------------------------------------------------------
# Serial connection manager — backs the frontend's ARDUINO connect modal.
# Reads the Arduino's JSON lines directly in a background thread (the
# same job hardware/serial_bridge/bridge.py does standalone) and feeds
# them into whichever object is currently `simulator` via .receive().
# ---------------------------------------------------------------------
class SerialManager:
    def __init__(self):
        self._ser: Optional[serial.Serial] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.port: Optional[str] = None
        self.error: Optional[str] = None

    @property
    def connected(self) -> bool:
        return self._ser is not None and self._thread is not None and self._thread.is_alive()

    def list_ports(self):
        return [
            {"port": p.device, "description": p.description or "Unknown device"}
            for p in list_ports.comports()
        ]

    def connect(self, port: str, baud: int = 115200) -> bool:
        self.disconnect()  # ensure any previous connection is torn down first
        self.error = None
        try:
            self._ser = serial.Serial(port, baud, timeout=2)
        except serial.SerialException as e:
            self._ser = None
            self.error = str(e)
            return False

        self.port = port
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()
        return True

    def _read_loop(self):
        time.sleep(2)  # Arduino resets on serial connect; give it a moment to boot
        while not self._stop_event.is_set():
            try:
                line = self._ser.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue
                try:
                    sample = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(simulator, HardwareIngest):
                    simulator.receive(sample)
            except serial.SerialException as e:
                self.error = str(e)
                break
            except Exception:
                continue

    def disconnect(self):
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=3)
        if self._ser is not None:
            try:
                self._ser.close()
            except Exception:
                pass
        self._ser = None
        self._thread = None
        self.port = None


serial_manager = SerialManager()

TICK_INTERVAL_SECONDS = 1.0

_engine_running = True
_mission_params = {"duration_hours": 2.0, "expected_load_percent": 60.0}
_latest_state: dict = {}
_connections: list[WebSocket] = []
_current_source = "arduino" if USE_HARDWARE else "software"
_current_run_id = simulator.state.run_id
store.start_run(_current_run_id)


# ---------------------------------------------------------------------
# Core tick pipeline (shared by background loop AND REST "peek" calls)
# ---------------------------------------------------------------------
def run_pipeline_tick() -> dict:
    global _latest_state

    raw_sample = simulator.tick()
    result = preprocessor.process(raw_sample)
    cleaned, stats = result["cleaned"], result["stats"]

    features = feature_dict(cleaned, stats)
    vector = build_feature_vector(cleaned, stats)
    prediction = predictor.predict(vector, features["combined_degradation_index"])

    mission = assess_mission(
        rul_hours=prediction["rulHours"],
        health=prediction["health"],
        degradation=prediction["degradation"],
        fault_risk=prediction["faultRisk"],
        mission_duration_hours=_mission_params["duration_hours"],
        expected_load_percent=_mission_params["expected_load_percent"],
    )

    sensors = {
        "rpm": cleaned["rpm"],
        "temperature": cleaned["temperature"],
        "vibration": cleaned["vibration"],
        "pressure": cleaned["pressure"],
        "load": cleaned["load"],
        "scenario": raw_sample["scenario"],
    }
    state = twin.update(sensors, prediction, mission)
    state["runId"] = _current_run_id
    state["features"] = features

    store.insert_sample(_current_run_id, state)
    _latest_state = state
    return state


# ---------------------------------------------------------------------
# Background broadcast loop
# ---------------------------------------------------------------------
async def engine_loop():
    while True:
        if _engine_running:
            state = run_pipeline_tick()
            dead = []
            for ws in _connections:
                try:
                    await ws.send_text(json.dumps(state))
                except Exception:
                    dead.append(ws)
            for ws in dead:
                if ws in _connections:
                    _connections.remove(ws)
        await asyncio.sleep(TICK_INTERVAL_SECONDS)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(engine_loop())


# ---------------------------------------------------------------------
# REST models
# ---------------------------------------------------------------------
class ScenarioRequest(BaseModel):
    scenario: str  # one of Scenario enum values


class MissionRequest(BaseModel):
    duration_hours: float
    expected_load_percent: Optional[float] = 60.0


class IngestRequest(BaseModel):
    rpm: Optional[float] = None
    temperature: Optional[float] = None
    vibration: Optional[float] = None
    pressure: Optional[float] = None
    load: Optional[float] = None

class SourceRequest(BaseModel):
    source: str  # "software" or "arduino"


class SerialConnectRequest(BaseModel):
    port: str
    baud: int = 115200

# ---------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------
@app.get("/")
def root():
    return {
        "name": "AeroTwin UAV Engine Digital Twin API",
        "status": "ok",
        "docs": "/docs",
        "websocket": "/ws/engine",
    }


@app.get("/api/engine/status")
def get_status():
    return _latest_state or run_pipeline_tick()


@app.get("/api/engine/prediction")
def get_prediction():
    state = _latest_state or run_pipeline_tick()
    return {
        "health": state.get("health"),
        "degradation": state.get("degradation"),
        "faultRisk": state.get("faultRisk"),
        "faultType": state.get("faultType"),
        "anomalyScore": state.get("anomalyScore"),
        "rulHours": state.get("rulHours"),
        "timeToCriticalMinutes": state.get("timeToCriticalMinutes"),
        "status": state.get("status"),
    }


@app.get("/api/engine/mission-risk")
def get_mission_risk():
    state = _latest_state or run_pipeline_tick()
    return {
        "missionRisk": state.get("missionRisk"),
        "missionReadiness": state.get("missionReadiness"),
        "recommendation": state.get("recommendation"),
        "params": _mission_params,
    }


@app.get("/api/engine/history")
def get_history(run_id: Optional[str] = None, limit: int = 300):
    rid = run_id or _current_run_id
    return {"runId": rid, "samples": store.get_recent(rid, limit=limit)}


@app.get("/api/engine/runs")
def get_runs():
    return {"runs": store.list_runs()}


@app.get("/api/engine/runs/{run_id}")
def get_run_detail(run_id: str):
    return {"runId": run_id, "samples": store.get_run_samples(run_id)}


@app.post("/api/engine/start")
def start_engine():
    global _engine_running
    _engine_running = True
    return {"running": _engine_running}


@app.post("/api/engine/reset")
def reset_engine():
    global _current_run_id, _engine_running, _current_source
    store.end_run(_current_run_id, twin._prev_status)
    simulator.reset()
    preprocessor.reset()
    twin.reset()
    _current_source = "arduino" if USE_HARDWARE else "software"
    _current_run_id = simulator.state.run_id
    store.start_run(_current_run_id)
    _engine_running = True

    # Pre-warm the rolling preprocessing buffer so rolling stats (std/roc)
    # aren't spiky on the very first ticks a client sees after reset.
    for _ in range(5):
        run_pipeline_tick()

    return {"runId": _current_run_id, "running": True}


@app.post("/api/engine/scenario")
def set_scenario(req: ScenarioRequest):
    try:
        Scenario(req.scenario)
    except ValueError:
        valid = [s.value for s in Scenario]
        return {"error": f"invalid scenario '{req.scenario}'", "valid": valid}
    simulator.set_scenario(req.scenario)
    return {"scenario": req.scenario}

@app.post("/api/engine/source")
def set_source(req: SourceRequest):
    global simulator, _current_source, _current_run_id

    source = req.source.lower().strip()

    if source not in {"software", "arduino"}:
        return {
            "accepted": False,
            "error": "Invalid source. Use 'software' or 'arduino'."
        }

    if source == _current_source:
        return {
            "accepted": True,
            "source": _current_source,
            "message": "Source already active."
        }

    # Switch telemetry source
    if source == "arduino":
        simulator = HardwareIngest()
    else:
        simulator = EngineSimulator()
        serial_manager.disconnect()  # stop reading the port if it was open

    # Start a new run for the new source
    _current_source = source
    _current_run_id = simulator.state.run_id
    store.start_run(_current_run_id)

    # Reset downstream state so the new source starts cleanly
    preprocessor.reset()
    twin.reset()

    # Pre-warm the rolling preprocessing buffer (same fix as /api/engine/reset)
    # so rolling stats (std/roc) -- and therefore the anomaly/fault-risk
    # models -- aren't spiky/misleading on the first few ticks right after
    # switching sources.
    for _ in range(5):
        run_pipeline_tick()

    return {
        "accepted": True,
        "source": _current_source,
        "runId": _current_run_id
    }
@app.get("/api/engine/source")
def get_source():
    return {
        "source": _current_source,
        "hardware": _current_source == "arduino"
    }

@app.post("/api/engine/ingest")
def ingest_hardware_sample(req: IngestRequest):
    """Accept sensor readings from the Arduino UNO."""

    if _current_source != "arduino":
        return {
            "accepted": False,
            "reason": "Server is currently running in software simulator mode."
        }

    simulator.receive(req.model_dump(exclude_none=True))

    return {
        "accepted": True,
        "source": "arduino"
    }


@app.get("/api/engine/hardware-status")
def hardware_status():
    if _current_source != "arduino":
        return {"mode": "simulator"}

    return {
        "mode": "hardware",
        "connected": simulator.state.connected,
        "lastSampleTime": simulator.state.last_sample_time,
    }


@app.get("/api/engine/serial/ports")
def get_serial_ports():
    return {"ports": serial_manager.list_ports()}


@app.post("/api/engine/serial/connect")
def connect_serial(req: SerialConnectRequest):
    global simulator, _current_source, _current_run_id

    ok = serial_manager.connect(req.port, req.baud)
    if not ok:
        return {"connected": False, "error": serial_manager.error or "Could not open serial port."}

    # Switch telemetry source to arduino now that the port is open, the
    # same way POST /api/engine/source does.
    if not isinstance(simulator, HardwareIngest):
        simulator = HardwareIngest()
    _current_source = "arduino"
    _current_run_id = simulator.state.run_id
    store.start_run(_current_run_id)
    preprocessor.reset()
    twin.reset()

    # Pre-warm the rolling preprocessing buffer (same fix as /api/engine/reset)
    # so a fresh Arduino connection doesn't briefly show misleading
    # DEGRADING/elevated-risk readings before the buffer fills up.
    for _ in range(5):
        run_pipeline_tick()

    return {"connected": True, "port": req.port, "source": _current_source, "runId": _current_run_id}


@app.post("/api/engine/serial/disconnect")
def disconnect_serial():
    serial_manager.disconnect()
    return {"disconnected": True}


@app.post("/api/engine/mission")
def set_mission(req: MissionRequest):
    _mission_params["duration_hours"] = req.duration_hours
    _mission_params["expected_load_percent"] = req.expected_load_percent or 60.0
    state = _latest_state or run_pipeline_tick()
    mission = assess_mission(
        rul_hours=state.get("rulHours", 0),
        health=state.get("health", 0),
        degradation=state.get("degradation", 0),
        fault_risk=state.get("faultRisk", 0),
        mission_duration_hours=_mission_params["duration_hours"],
        expected_load_percent=_mission_params["expected_load_percent"],
    )
    return mission


# ---------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------
@app.websocket("/ws/engine")
async def ws_engine(websocket: WebSocket):
    await websocket.accept()
    _connections.append(websocket)
    try:
        if _latest_state:
            await websocket.send_text(json.dumps(_latest_state))
        while True:
            # Keep the connection open; we don't require inbound messages,
            # but read (with a timeout-free await) so disconnects raise.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in _connections:
            _connections.remove(websocket)
