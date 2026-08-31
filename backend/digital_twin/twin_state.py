"""
Digital Twin State
=====================
Maintains the single authoritative "current state" of the digital twin by
merging: raw sensors -> prediction outputs -> alerts -> mission context.
This is the object serialized to JSON for REST responses and WebSocket
broadcasts, and the frontend's Digital Twin visualization renders directly
from it.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field


ALERT_THRESHOLDS = {
    # (parameter, comparison) -> (warning_msg, severity)
}


@dataclass
class Alert:
    severity: str  # INFO | WARNING | HIGH | CRITICAL
    message: str
    parameter: str
    timestamp: str = field(default_factory=lambda: dt.datetime.now().strftime("%H:%M:%S"))

    def to_dict(self):
        return {
            "severity": self.severity,
            "message": self.message,
            "parameter": self.parameter,
            "timestamp": self.timestamp,
        }


class DigitalTwin:
    def __init__(self):
        self.alerts: list[Alert] = []
        self._prev_status = "HEALTHY"
        self._last_state: dict = {}

    def update(self, sensors: dict, prediction: dict, mission: dict | None = None) -> dict:
        timestamp = dt.datetime.now().isoformat(timespec="seconds")

        self._evaluate_alerts(sensors, prediction)

        state = {
            "timestamp": timestamp,
            "rpm": sensors["rpm"],
            "temperature": sensors["temperature"],
            "vibration": sensors["vibration"],
            "pressure": sensors["pressure"],
            "load": sensors["load"],
            "health": prediction["health"],
            "anomalyScore": prediction["anomalyScore"],
            "isAnomaly": prediction["isAnomaly"],
            "faultRisk": prediction["faultRisk"],
            "faultType": prediction["faultType"],
            "degradation": prediction["degradation"],
            "rulHours": prediction["rulHours"],
            "timeToCriticalMinutes": prediction["timeToCriticalMinutes"],
            "status": prediction["status"],
            "scenario": sensors.get("scenario", "NORMAL"),
            "alerts": [a.to_dict() for a in self.alerts[:20]],
        }
        if mission:
            state.update(
                {
                    "missionRisk": mission["missionRisk"],
                    "missionReadiness": mission["missionReadiness"],
                    "recommendation": mission["recommendation"],
                }
            )
        self._last_state = state
        self._prev_status = prediction["status"]
        return state

    def reset(self):
        self.alerts = []
        self._prev_status = "HEALTHY"
        self._last_state = {}

    # ------------------------------------------------------------------
    def _evaluate_alerts(self, sensors: dict, prediction: dict):
        new_alerts = []
        status = prediction["status"]

        if status != self._prev_status:
            if status in ("WARNING", "DEGRADING"):
                new_alerts.append(Alert("WARNING", f"Engine status changed to {status}.", "health"))
            elif status == "CRITICAL":
                new_alerts.append(Alert("CRITICAL", "Engine approaching critical condition.", "health"))
            elif status == "HEALTHY":
                new_alerts.append(Alert("INFO", "Engine operating normally.", "health"))

        if sensors["temperature"] > 110:
            new_alerts.append(Alert("HIGH", "Abnormal engine temperature detected.", "temperature"))
        elif sensors["temperature"] > 95:
            new_alerts.append(Alert("WARNING", "Temperature trend increasing.", "temperature"))

        if sensors["vibration"] > 7:
            new_alerts.append(Alert("HIGH", "Abnormal vibration levels detected.", "vibration"))
        elif sensors["vibration"] > 4:
            new_alerts.append(Alert("WARNING", "Vibration trend increasing.", "vibration"))

        # Only surface a fault-risk alert when the model has identified an
        # actual fault class. faultRisk = 1 - P(NONE), so it can read
        # "high" purely from probability spread across multiple fault
        # classes even while NONE is still the top prediction -- alerting
        # in that case produces a confusing "High fault risk: NONE."
        # message that names no real fault.
        if prediction["faultType"] != "NONE":
            if prediction["faultRisk"] > 70:
                new_alerts.append(Alert("CRITICAL", f"High fault risk: {prediction['faultType']}.", "faultRisk"))
            elif prediction["faultRisk"] > 40:
                new_alerts.append(Alert("HIGH", f"Elevated fault risk detected ({prediction['faultType']}).", "faultRisk"))

        if prediction["isAnomaly"] and prediction["anomalyScore"] > 60:
            new_alerts.append(Alert("HIGH", "Abnormal engine behavior detected.", "anomalyScore"))

        if new_alerts:
            self.alerts = new_alerts + self.alerts
            self.alerts = self.alerts[:50]
