"""
Model Training Script
========================
Generates a synthetic labeled dataset by driving the SAME engine simulator,
preprocessing, and feature-engineering pipeline used at inference time
through every fault scenario, then trains:

  1. IsolationForest        -> unsupervised anomaly detection (fit on
                                healthy/NORMAL data only)
  2. RandomForestClassifier -> supervised fault-type classification
  3. GradientBoostingRegressor -> RUL / time-to-critical-condition estimator

IMPORTANT — explicitly synthetic data
--------------------------------------
All training data is generated from the physics-inspired simulator in
backend/simulator/engine_simulator.py, NOT from a real UAV engine. This is
a student prototype: results characterize how well the ML pipeline learns
the simulator's fault signatures, not real-world engine reliability. See
docs/README.md "Limitations" section.

Run:
    python ml/training/train_models.py

Outputs:
    ml/datasets/synthetic_training_data.csv
    ml/evaluation/metrics.json, ml/evaluation/metrics.md
    backend/saved_models/*.joblib
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import (
    GradientBoostingRegressor,
    IsolationForest,
    RandomForestClassifier,
)
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    precision_score,
    r2_score,
    recall_score,
    root_mean_squared_error,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from simulator.engine_simulator import EngineSimulator, Scenario, SEVERITY_RAMP_RATE  # noqa: E402
from preprocessing.preprocess import Preprocessor  # noqa: E402
from features.feature_engineering import build_feature_vector, FEATURE_NAMES  # noqa: E402

DATASET_DIR = ROOT / "ml" / "datasets"
EVAL_DIR = ROOT / "ml" / "evaluation"
SAVED_MODELS_DIR = ROOT / "backend" / "saved_models"
for d in (DATASET_DIR, EVAL_DIR, SAVED_MODELS_DIR):
    d.mkdir(parents=True, exist_ok=True)

TICKS_PER_RUN = 700
RUNS_PER_SCENARIO = 6  # different random seeds per scenario for variety
CRITICAL_SEVERITY = 0.85
# Convention: 1 simulated tick == 1 simulated minute of engine operating
# time for the purpose of generating RUL ground truth. The live demo
# playback runs 1 tick/second (compressed) purely for demonstration speed —
# see docs/README.md "RUL explanation" for why this distinction matters.
TICKS_TO_HOURS = 1.0 / 60.0
MAX_RUL_HOURS = 12.0  # cap for healthy/NORMAL samples (no active fault)


def generate_dataset() -> pd.DataFrame:
    rows = []
    for scenario in Scenario:
        for run in range(RUNS_PER_SCENARIO):
            sim = EngineSimulator(seed=hash((scenario.value, run)) % (2**32))
            sim.set_scenario(scenario.value)
            pre = Preprocessor()
            ramp = SEVERITY_RAMP_RATE[scenario]

            for t in range(TICKS_PER_RUN):
                sample = sim.tick()
                result = pre.process(sample)
                vec = build_feature_vector(result["cleaned"], result["stats"])
                severity = sample["severity"]

                if scenario == Scenario.NORMAL or ramp <= 0:
                    rul_hours = MAX_RUL_HOURS
                else:
                    remaining_ticks = max(0.0, (CRITICAL_SEVERITY - severity) / ramp)
                    rul_hours = min(MAX_RUL_HOURS, remaining_ticks * TICKS_TO_HOURS)

                label = "NONE" if scenario == Scenario.NORMAL else scenario.value
                is_anomaly = 1 if severity > 0.35 else 0

                row = dict(zip(FEATURE_NAMES, vec))
                row.update(
                    {
                        "scenario": scenario.value,
                        "severity": severity,
                        "fault_label": label,
                        "is_anomaly": is_anomaly,
                        "rul_hours": rul_hours,
                        "run": f"{scenario.value}_{run}",
                        "tick": t,
                    }
                )
                rows.append(row)

    return pd.DataFrame(rows)


def train_and_evaluate(df: pd.DataFrame):
    X = df[FEATURE_NAMES].values
    metrics = {}

    # ------------------------------------------------------------------
    # 1. Scaler (shared)
    # ------------------------------------------------------------------
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # ------------------------------------------------------------------
    # 2. Isolation Forest — fit on healthy data only
    # ------------------------------------------------------------------
    healthy_mask = df["fault_label"] == "NONE"
    iso = IsolationForest(n_estimators=200, contamination=0.03, random_state=42)
    iso.fit(X_scaled[healthy_mask.values])

    # Evaluate anomaly detection against the synthetic is_anomaly label
    raw_scores = iso.decision_function(X_scaled)
    preds = (iso.predict(X_scaled) == -1).astype(int)  # 1 = anomaly
    y_true_anom = df["is_anomaly"].values
    metrics["anomaly_detection"] = {
        "accuracy": accuracy_score(y_true_anom, preds),
        "precision": precision_score(y_true_anom, preds, zero_division=0),
        "recall": recall_score(y_true_anom, preds, zero_division=0),
        "f1": f1_score(y_true_anom, preds, zero_division=0),
    }

    # ------------------------------------------------------------------
    # 3. Fault classifier (Random Forest)
    # ------------------------------------------------------------------
    le = LabelEncoder()
    y_class = le.fit_transform(df["fault_label"].values)
    Xc_train, Xc_test, yc_train, yc_test = train_test_split(
        X_scaled, y_class, test_size=0.25, random_state=42, stratify=y_class
    )
    clf = RandomForestClassifier(n_estimators=300, max_depth=14, random_state=42, class_weight="balanced")
    clf.fit(Xc_train, yc_train)
    yc_pred = clf.predict(Xc_test)
    metrics["fault_classification"] = {
        "accuracy": accuracy_score(yc_test, yc_pred),
        "precision_macro": precision_score(yc_test, yc_pred, average="macro", zero_division=0),
        "recall_macro": recall_score(yc_test, yc_pred, average="macro", zero_division=0),
        "f1_macro": f1_score(yc_test, yc_pred, average="macro", zero_division=0),
        "classes": list(le.classes_),
        "confusion_matrix": confusion_matrix(yc_test, yc_pred).tolist(),
    }

    # ------------------------------------------------------------------
    # 4. RUL / time-to-critical regressor
    # ------------------------------------------------------------------
    y_rul = df["rul_hours"].values
    Xr_train, Xr_test, yr_train, yr_test = train_test_split(
        X_scaled, y_rul, test_size=0.25, random_state=42
    )
    reg = GradientBoostingRegressor(
        n_estimators=250, max_depth=4, learning_rate=0.05, random_state=42
    )
    reg.fit(Xr_train, yr_train)
    yr_pred = reg.predict(Xr_test)
    metrics["rul_regression"] = {
        "mae_hours": mean_absolute_error(yr_test, yr_pred),
        "rmse_hours": root_mean_squared_error(yr_test, yr_pred),
        "r2": r2_score(yr_test, yr_pred),
    }

    return {
        "scaler": scaler,
        "isolation_forest": iso,
        "fault_classifier": clf,
        "label_encoder": le,
        "rul_regressor": reg,
    }, metrics


def main():
    print("Generating synthetic training dataset from simulator...")
    df = generate_dataset()
    dataset_path = DATASET_DIR / "synthetic_training_data.csv"
    df.to_csv(dataset_path, index=False)
    print(f"  -> {len(df)} rows written to {dataset_path}")

    print("Training models...")
    models, metrics = train_and_evaluate(df)

    print("Saving models to backend/saved_models/ ...")
    joblib.dump(models["scaler"], SAVED_MODELS_DIR / "scaler.joblib")
    joblib.dump(models["isolation_forest"], SAVED_MODELS_DIR / "isolation_forest.joblib")
    joblib.dump(models["fault_classifier"], SAVED_MODELS_DIR / "fault_classifier.joblib")
    joblib.dump(models["label_encoder"], SAVED_MODELS_DIR / "label_encoder.joblib")
    joblib.dump(models["rul_regressor"], SAVED_MODELS_DIR / "rul_regressor.joblib")
    with open(SAVED_MODELS_DIR / "feature_names.json", "w") as f:
        json.dump(FEATURE_NAMES, f, indent=2)

    metrics_path_json = EVAL_DIR / "metrics.json"
    with open(metrics_path_json, "w") as f:
        json.dump(metrics, f, indent=2)

    md = ["# Model Evaluation (synthetic simulator data)\n",
          "> All results are computed on data generated by the engine simulator,",
          "> **not** a real UAV engine. See docs/README.md Limitations.\n"]

    ad = metrics["anomaly_detection"]
    md.append("## Anomaly Detection (Isolation Forest)")
    md.append(f"- Accuracy: {ad['accuracy']:.3f}")
    md.append(f"- Precision: {ad['precision']:.3f}")
    md.append(f"- Recall: {ad['recall']:.3f}")
    md.append(f"- F1: {ad['f1']:.3f}\n")

    fc = metrics["fault_classification"]
    md.append("## Fault Classification (Random Forest)")
    md.append(f"- Accuracy: {fc['accuracy']:.3f}")
    md.append(f"- Precision (macro): {fc['precision_macro']:.3f}")
    md.append(f"- Recall (macro): {fc['recall_macro']:.3f}")
    md.append(f"- F1 (macro): {fc['f1_macro']:.3f}")
    md.append(f"- Classes: {fc['classes']}")
    md.append(f"- Confusion matrix: {fc['confusion_matrix']}\n")

    rr = metrics["rul_regression"]
    md.append("## RUL / Time-to-Critical Regression (Gradient Boosting)")
    md.append(f"- MAE: {rr['mae_hours']:.3f} hours")
    md.append(f"- RMSE: {rr['rmse_hours']:.3f} hours")
    md.append(f"- R^2: {rr['r2']:.3f}\n")

    with open(EVAL_DIR / "metrics.md", "w") as f:
        f.write("\n".join(md))

    print("Done.")
    print(json.dumps(metrics, indent=2, default=str))


if __name__ == "__main__":
    main()
