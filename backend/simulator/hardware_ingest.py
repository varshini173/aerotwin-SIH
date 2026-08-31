"""
Hardware Ingest — Real Arduino UNO Sensor Source
=============================================
Drop-in replacement for EngineSimulator. Instead of generating synthetic
telemetry, this holds the most recent sample POSTed by a real Arduino UNO (via
the /api/engine/ingest endpoint in main.py) and hands it back on tick().

This keeps the exact same tick() -> dict contract as EngineSimulator, so
nothing downstream (preprocessing / features / ML / digital twin / mission
assessment) needs to change at all — main.py just swaps which object it
calls .tick() on.

Usage in main.py:
    if USE_HARDWARE:
        simulator = HardwareIngest()
    else:
        simulator = EngineSimulator()

The board pushes samples asynchronously (whenever it has new sensor data).
This class just returns whatever the latest received sample was; if no new
data has arrived recently, it holds the last-known-good sample instead of
crashing the pipeline (real WiFi/serial links drop out sometimes).
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field

STALE_AFTER_SECONDS = 5.0  # if no new sample arrives in this long, flag it stale

# Small physically-realistic jitter applied ONLY to channels that have never
# received a real hardware sample. The ML models (backend/saved_models/) were
# trained on synthetic data where even healthy ("NONE") samples had natural
# sensor noise -- an EXACTLY constant signal (zero std, zero rate-of-change)
# never appears in training data, so a perfectly locked channel is read as
# out-of-distribution / anomalous rather than healthy. This jitter keeps
# unwired channels statistically consistent with what the models expect,
# without ever touching a channel that IS receiving real sensor data.
NOISE = {
    "rpm": 18.0,
    "temperature": 0.35,
    "vibration": 0.06,
    "pressure": 0.05,
    "load": 1.2,
}

# Healthy baseline defaults — MUST match backend/simulator/engine_simulator.py's
# BASELINE so a partial sensor rig (e.g. only a temperature potentiometer)
# doesn't make the untouched channels look like a flat-lined/critical engine.
# Zero is not a neutral value here: pressure=0 or rpm=0 reads as a severe
# fault to the ML pipeline, not "no data yet". Any channel you haven't wired
# up sits at its healthy value until you wire and send that channel too.
DEFAULT_SAMPLE = {
    "rpm": 4200.0,
    "temperature": 72.0,
    "vibration": 1.2,
    "pressure": 4.2,
    "load": 55.0,
}


@dataclass
class HardwareIngestState:
    tick: int = 0
    run_id: str = field(default_factory=lambda: f"hw_run_{int(time.time())}")
    connected: bool = False
    last_sample_time: float = 0.0


class HardwareIngest:
    """Same public shape as EngineSimulator: .state, .tick(), .reset(),
    .set_scenario() (no-op here — scenarios don't apply to real hardware)."""

    def __init__(self):
        self.state = HardwareIngestState()
        self._latest_raw: dict = dict(DEFAULT_SAMPLE)
        self._received_keys: set[str] = set()  # channels that have ever gotten a REAL sample
        self._rng = random.Random()

    # ------------------------------------------------------------------
    # Called by the /api/engine/ingest endpoint whenever the board POSTs
    # ------------------------------------------------------------------
    def receive(self, payload: dict) -> None:
        """Store the latest sample sent by the Arduino UNO. Missing keys fall
        back to the previous value so a partial/glitchy payload doesn't
        wipe out the other sensors."""
        for key in DEFAULT_SAMPLE:
            if key in payload and payload[key] is not None:
                try:
                    self._latest_raw[key] = float(payload[key])
                    self._received_keys.add(key)
                except (TypeError, ValueError):
                    pass  # keep previous value for this sensor
        self.state.connected = True
        self.state.last_sample_time = time.time()

    # ------------------------------------------------------------------
    # Public control API (mirrors EngineSimulator)
    # ------------------------------------------------------------------
    def set_scenario(self, scenario: str) -> None:
        # No-op: scenarios are a synthetic-simulator concept only. Kept so
        # main.py / the frontend scenario dropdown don't need special-casing.
        pass

    def reset(self) -> None:
        self.state = HardwareIngestState()
        self._latest_raw = dict(DEFAULT_SAMPLE)
        self._received_keys = set()

    # ------------------------------------------------------------------
    # Core tick — called by the background loop at the same ~1Hz cadence
    # ------------------------------------------------------------------
    def tick(self) -> dict:
        self.state.tick += 1

        age = time.time() - self.state.last_sample_time if self.state.last_sample_time else None
        stale = age is None or age > STALE_AFTER_SECONDS
        if stale:
            self.state.connected = False

        sample = {}
        for key, base_value in self._latest_raw.items():
            if key in self._received_keys:
                # Real sensor data -- use exactly as received, no synthetic noise.
                sample[key] = base_value
            else:
                # No hardware wired up for this channel yet. Add small
                # realistic jitter around the healthy baseline (see NOISE
                # above) so it statistically resembles the noisy-but-healthy
                # signals the ML models were trained on, instead of an
                # impossibly perfect flat line.
                sample[key] = base_value + self._rng.uniform(-NOISE[key], NOISE[key])

        return {
            "tick": self.state.tick,
            "scenario": "LIVE_HARDWARE" if not stale else "LIVE_HARDWARE_STALE",
            "severity": 0.0,  # not applicable to real hardware; kept for schema compatibility
            "rpm": round(sample["rpm"], 1),
            "temperature": round(sample["temperature"], 2),
            "vibration": round(sample["vibration"], 3),
            "pressure": round(sample["pressure"], 3),
            "load": round(sample["load"], 1),
        }
