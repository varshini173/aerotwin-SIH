"""
Engine Simulator for MALE UAV Aero Piston Engine Digital Twin
================================================================
Generates realistic, gradually-evolving time-series telemetry for a piston
engine: RPM, Temperature, Vibration, Pressure, Load.

This module is intentionally decoupled from FastAPI/ML code so that it can
later be swapped for a real Arduino UNO sensor-ingest module without touching any
downstream (preprocessing / features / ML / digital twin) code — both must
only produce/consume the same telemetry sample schema.

Design notes
------------
* State is *stateful*, not i.i.d. random: each tick nudges the previous
  value toward a scenario-specific target with bounded noise, so charts
  show smooth, physically-plausible trends instead of jitter.
* Scenarios progress in *severity stages* (0.0 -> 1.0) so the caller can
  watch a fault develop gradually rather than jump instantly to CRITICAL.
* All physical baselines are documented and easy to tune.
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field, asdict
from enum import Enum


class Scenario(str, Enum):
    NORMAL = "NORMAL"
    OVERHEAT = "OVERHEAT"
    VIBRATION = "VIBRATION"
    RPM_INSTABILITY = "RPM_INSTABILITY"
    PRESSURE_ABNORMALITY = "PRESSURE_ABNORMALITY"
    COMBINED_DEGRADATION = "COMBINED_DEGRADATION"
    PROGRESSIVE_DEGRADATION = "PROGRESSIVE_DEGRADATION"


# Healthy baseline operating point
BASELINE = {
    "rpm": 4200.0,
    "temperature": 72.0,
    "vibration": 1.2,
    "pressure": 4.2,
    "load": 55.0,
}

# How fast each scenario's severity ramps per tick (severity 0->1)
# Smaller = slower/more gradual fault development.
SEVERITY_RAMP_RATE = {
    Scenario.NORMAL: 0.0,
    Scenario.OVERHEAT: 0.015,
    Scenario.VIBRATION: 0.018,
    Scenario.RPM_INSTABILITY: 0.02,
    Scenario.PRESSURE_ABNORMALITY: 0.016,
    Scenario.COMBINED_DEGRADATION: 0.012,
    Scenario.PROGRESSIVE_DEGRADATION: 0.006,  # slowest — long realistic decay
}


@dataclass
class EngineSimulatorState:
    scenario: Scenario = Scenario.NORMAL
    severity: float = 0.0  # 0 (just started / healthy) -> 1 (fully critical)
    tick: int = 0
    rpm: float = BASELINE["rpm"]
    temperature: float = BASELINE["temperature"]
    vibration: float = BASELINE["vibration"]
    pressure: float = BASELINE["pressure"]
    load: float = BASELINE["load"]
    run_id: str = field(default_factory=lambda: f"run_{int(time.time())}")


class EngineSimulator:
    """Stateful, tick-based engine telemetry generator."""

    def __init__(self, seed: int | None = None):
        self._rng = random.Random(seed)
        self.state = EngineSimulatorState()

    # ------------------------------------------------------------------
    # Public control API
    # ------------------------------------------------------------------
    def set_scenario(self, scenario: str) -> None:
        scenario_enum = Scenario(scenario)
        self.state.scenario = scenario_enum
        self.state.severity = 0.0  # restart severity ramp for the new scenario

    def reset(self) -> None:
        self.state = EngineSimulatorState()

    # ------------------------------------------------------------------
    # Core tick
    # ------------------------------------------------------------------
    def tick(self) -> dict:
        """Advance the simulation by one time step (~1s) and return the
        latest raw telemetry sample as a plain dict."""
        s = self.state
        s.tick += 1

        ramp = SEVERITY_RAMP_RATE[s.scenario]
        if ramp > 0:
            s.severity = min(1.0, s.severity + ramp)
        else:
            # Recover gradually toward healthy when in NORMAL mode
            s.severity = max(0.0, s.severity - 0.03)

        target = self._targets_for_scenario(s.scenario, s.severity)

        # Exponential smoothing toward target + small physically-bounded noise
        alpha = 0.12  # how quickly sensors move toward their target each tick
        s.rpm = self._smooth(s.rpm, target["rpm"], alpha, noise=18.0)
        s.temperature = self._smooth(s.temperature, target["temperature"], alpha, noise=0.35)
        s.vibration = self._smooth(s.vibration, target["vibration"], alpha, noise=0.06)
        s.pressure = self._smooth(s.pressure, target["pressure"], alpha, noise=0.05)
        s.load = self._smooth(s.load, target["load"], alpha, noise=1.2)

        # Physical clamps (sensor range limits)
        s.rpm = clamp(s.rpm, 500, 7500)
        s.temperature = clamp(s.temperature, 20, 160)
        s.vibration = clamp(s.vibration, 0.1, 12.0)
        s.pressure = clamp(s.pressure, 0.5, 8.0)
        s.load = clamp(s.load, 0, 100)

        return {
            "tick": s.tick,
            "scenario": s.scenario.value,
            "severity": round(s.severity, 4),
            "rpm": round(s.rpm, 1),
            "temperature": round(s.temperature, 2),
            "vibration": round(s.vibration, 3),
            "pressure": round(s.pressure, 3),
            "load": round(s.load, 1),
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _smooth(self, current: float, target: float, alpha: float, noise: float) -> float:
        moved = current + alpha * (target - current)
        # Small physically-bounded jitter (sensor noise), scaled down as we
        # approach steady state so trends stay readable.
        jitter = self._rng.uniform(-noise, noise) * 0.35
        return moved + jitter

    def _targets_for_scenario(self, scenario: Scenario, severity: float) -> dict:
        """Return the target operating point sensors are being driven
        toward, given the scenario and how far the fault has progressed."""
        b = BASELINE

        if scenario == Scenario.NORMAL:
            return dict(b)

        if scenario == Scenario.OVERHEAT:
            return {
                "rpm": b["rpm"] + 60 * severity,
                "temperature": b["temperature"] + 55 * severity,   # -> ~127C
                "vibration": b["vibration"] + 0.8 * severity,
                "pressure": b["pressure"] - 0.3 * severity,
                "load": b["load"] + 15 * severity,
            }

        if scenario == Scenario.VIBRATION:
            return {
                "rpm": b["rpm"] + 40 * severity,
                "temperature": b["temperature"] + 10 * severity,
                "vibration": b["vibration"] + 6.5 * severity,      # -> ~7.7 mm/s
                "pressure": b["pressure"] - 0.15 * severity,
                "load": b["load"] + 5 * severity,
            }

        if scenario == Scenario.RPM_INSTABILITY:
            # RPM instability is modeled as oscillation amplitude growth,
            # applied on top of a target using a sinusoid for realism.
            oscillation = math.sin(self.state.tick / 3.0) * (900 * severity)
            return {
                "rpm": b["rpm"] + oscillation,
                "temperature": b["temperature"] + 8 * severity,
                "vibration": b["vibration"] + 1.5 * severity,
                "pressure": b["pressure"] - 0.2 * severity,
                "load": b["load"] + 8 * severity,
            }

        if scenario == Scenario.PRESSURE_ABNORMALITY:
            return {
                "rpm": b["rpm"] - 30 * severity,
                "temperature": b["temperature"] + 12 * severity,
                "vibration": b["vibration"] + 0.6 * severity,
                "pressure": b["pressure"] - 2.4 * severity,        # -> ~1.8 bar
                "load": b["load"] + 5 * severity,
            }

        if scenario == Scenario.COMBINED_DEGRADATION:
            return {
                "rpm": b["rpm"] + 500 * severity * math.sin(self.state.tick / 4.0),
                "temperature": b["temperature"] + 40 * severity,
                "vibration": b["vibration"] + 5.0 * severity,
                "pressure": b["pressure"] - 1.6 * severity,
                "load": b["load"] + 20 * severity,
            }

        if scenario == Scenario.PROGRESSIVE_DEGRADATION:
            # Slow multi-parameter creep — the "long haul" wear scenario.
            return {
                "rpm": b["rpm"] - 120 * severity,
                "temperature": b["temperature"] + 30 * severity,
                "vibration": b["vibration"] + 3.5 * severity,
                "pressure": b["pressure"] - 1.0 * severity,
                "load": b["load"] + 10 * severity,
            }

        return dict(b)


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))
