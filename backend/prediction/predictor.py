"""
AI / ML Prediction Layer
==========================
Loads the trained models (Isolation Forest, Random Forest fault classifier,
Gradient Boosting RUL regressor) saved by ml/training/train_models.py and
turns a feature vector into the full set of decision-support outputs:

  * anomaly score + normal/abnormal flag
  * predicted fault class + fault risk (0-100%)
  * engine health score (0-100%)
  * degradation score (0-100%)
  * estimated RUL (hours) + estimated time to critical condition (minutes)

These are prototype, explainable, decision-support estimates — NOT
certified predictions. See docs/README.md Limitations.
"""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np

SAVED_MODELS_DIR = Path(__file__).resolve().parents[1] / "saved_models"


class Predictor:
    def __init__(self):
        self.scaler = joblib.load(SAVED_MODELS_DIR / "scaler.joblib")
        self.iso_forest = joblib.load(SAVED_MODELS_DIR / "isolation_forest.joblib")
        self.fault_clf = joblib.load(SAVED_MODELS_DIR / "fault_classifier.joblib")
        self.label_encoder = joblib.load(SAVED_MODELS_DIR / "label_encoder.joblib")
        self.rul_reg = joblib.load(SAVED_MODELS_DIR / "rul_regressor.joblib")

        # For scaling the anomaly decision_function output into a 0-100 score.
        # Calibrated from the training set's healthy/faulty score distributions
        # (see ml/training/train_models.py) so a typical healthy sample maps to
        # a low score and typical faulty samples map to a high score.
        self._score_lo, self._score_hi = -0.20, 0.12

    def predict(self, feature_vector: list[float], degradation_index: float) -> dict:
        X = np.array(feature_vector, dtype=float).reshape(1, -1)
        X_scaled = self.scaler.transform(X)

        # --- Anomaly detection -----------------------------------------
        raw_score = float(self.iso_forest.decision_function(X_scaled)[0])
        is_anomaly = bool(self.iso_forest.predict(X_scaled)[0] == -1)
        # Map decision_function (~ -0.15 healthy-boundary .. +0.15 very normal)
        # onto an intuitive 0-100 anomaly score where HIGHER = more anomalous.
        anomaly_score = _clip(
            100 * (self._score_hi - raw_score) / (self._score_hi - self._score_lo), 0, 100
        )

        # --- Fault classification ---------------------------------------
        proba = self.fault_clf.predict_proba(X_scaled)[0]
        pred_idx = int(np.argmax(proba))
        fault_type = self.label_encoder.inverse_transform([pred_idx])[0]
        # Fault risk = 1 - P(NONE), i.e. probability something is wrong
        none_idx = list(self.label_encoder.classes_).index("NONE")
        fault_risk = _clip(100 * (1 - proba[none_idx]), 0, 100)
        if fault_type == "NONE":
            # still report the most likely *fault* class as a secondary signal
            fault_probs = {c: float(p) for c, p in zip(self.label_encoder.classes_, proba) if c != "NONE"}
            secondary = max(fault_probs, key=fault_probs.get) if fault_probs else "NONE"
        else:
            secondary = fault_type

        # --- RUL / time to critical ---------------------------------------
        rul_hours = float(self.rul_reg.predict(X_scaled)[0])
        rul_hours = max(0.0, rul_hours)
        time_to_critical_minutes = rul_hours * 60.0

        # --- Degradation score (0-100) -------------------------------------
        # Blends the engineered combined_degradation_index (physical trend
        # signal) with the anomaly score and fault risk, so it reflects both
        # "how far from baseline" and "how much the ML models agree
        # something is wrong" rather than a single raw number.
        degradation = _clip(
            100 * (0.5 * _clip(degradation_index, 0, 1) + 0.3 * (anomaly_score / 100) + 0.2 * (fault_risk / 100)),
            0,
            100,
        )

        # --- Engine health score (0-100) -----------------------------------
        # Health is the inverse of degradation, further penalized by fault
        # risk so a confidently-diagnosed fault drags health down faster
        # than ambiguous drift alone.
        health = _clip(100 - degradation - 0.15 * fault_risk, 0, 100)

        status = _status_from_health(health)

        return {
            "anomalyScore": round(anomaly_score, 2),
            "isAnomaly": is_anomaly,
            "faultType": fault_type if fault_type != "NONE" else "NONE",
            "predictedFaultIfAny": secondary,
            "faultRisk": round(fault_risk, 2),
            "health": round(health, 2),
            "degradation": round(degradation, 2),
            "rulHours": round(rul_hours, 3),
            "timeToCriticalMinutes": round(time_to_critical_minutes, 1),
            "status": status,
        }


def _status_from_health(health: float) -> str:
    if health >= 90:
        return "HEALTHY"
    if health >= 70:
        return "NORMAL"
    if health >= 40:
        return "DEGRADING"
    if health >= 20:
        return "WARNING"
    return "CRITICAL"


def _clip(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))
