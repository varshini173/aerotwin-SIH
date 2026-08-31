"""
Storage Layer (SQLite)
=========================
Persists per-tick engine/prediction history for the History & Mission
Replay pages. Chosen over CSV because it lets the History page query by
run_id and time range efficiently without loading the whole file.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "history.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS telemetry_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    scenario TEXT,
    rpm REAL, temperature REAL, vibration REAL, pressure REAL, load REAL,
    health REAL, anomaly_score REAL, fault_risk REAL, fault_type TEXT,
    degradation REAL, rul_hours REAL, time_to_critical_minutes REAL,
    status TEXT, mission_risk TEXT, alerts_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_run_id ON telemetry_history(run_id);

CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    started_at TEXT,
    ended_at TEXT,
    final_status TEXT,
    scenario_summary TEXT
);
"""


class HistoryStore:
    def __init__(self, db_path: Path = DB_PATH):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def start_run(self, run_id: str):
        self.conn.execute(
            "INSERT OR IGNORE INTO runs (run_id, started_at) VALUES (?, datetime('now'))",
            (run_id,),
        )
        self.conn.commit()

    def end_run(self, run_id: str, final_status: str):
        self.conn.execute(
            "UPDATE runs SET ended_at = datetime('now'), final_status = ? WHERE run_id = ?",
            (final_status, run_id),
        )
        self.conn.commit()

    def insert_sample(self, run_id: str, state: dict):
        self.conn.execute(
            """
            INSERT INTO telemetry_history
                (run_id, timestamp, scenario, rpm, temperature, vibration, pressure, load,
                 health, anomaly_score, fault_risk, fault_type, degradation, rul_hours,
                 time_to_critical_minutes, status, mission_risk, alerts_json)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                run_id,
                state.get("timestamp"),
                state.get("scenario"),
                state.get("rpm"),
                state.get("temperature"),
                state.get("vibration"),
                state.get("pressure"),
                state.get("load"),
                state.get("health"),
                state.get("anomalyScore"),
                state.get("faultRisk"),
                state.get("faultType"),
                state.get("degradation"),
                state.get("rulHours"),
                state.get("timeToCriticalMinutes"),
                state.get("status"),
                state.get("missionRisk"),
                json.dumps(state.get("alerts", [])[:3]),
            ),
        )
        self.conn.commit()

    def list_runs(self, limit: int = 50) -> list[dict]:
        cur = self.conn.execute(
            "SELECT run_id, started_at, ended_at, final_status FROM runs ORDER BY started_at DESC LIMIT ?",
            (limit,),
        )
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    def get_run_samples(self, run_id: str) -> list[dict]:
        cur = self.conn.execute(
            "SELECT * FROM telemetry_history WHERE run_id = ? ORDER BY id ASC",
            (run_id,),
        )
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]
        for r in rows:
            try:
                r["alerts"] = json.loads(r.pop("alerts_json") or "[]")
            except Exception:
                r["alerts"] = []
        return rows

    def get_recent(self, run_id: str, limit: int = 200) -> list[dict]:
        cur = self.conn.execute(
            "SELECT * FROM telemetry_history WHERE run_id = ? ORDER BY id DESC LIMIT ?",
            (run_id, limit),
        )
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]
        rows.reverse()
        return rows
