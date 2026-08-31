"""
Feature Engineering
=====================
Turns cleaned sensor readings + rolling statistics (from Preprocessor) into
a fixed-length numeric feature vector consumed by the ML models. Feature
order here MUST exactly match the order used in ml/training/train_models.py.
"""

from __future__ import annotations

FEATURE_NAMES = [
    "rpm",
    "temperature",
    "vibration",
    "pressure",
    "load",
    "temp_ma",
    "vib_ma",
    "temp_roc",
    "vib_roc",
    "rpm_std",              # RPM variability (instability indicator)
    "pressure_deviation",   # deviation from healthy baseline
    "temp_deviation",       # deviation from healthy baseline
    "vib_deviation",        # deviation from healthy baseline
    "combined_degradation_index",
]

BASELINE = {
    "rpm": 4200.0,
    "temperature": 72.0,
    "vibration": 1.2,
    "pressure": 4.2,
    "load": 55.0,
}


def build_feature_vector(cleaned: dict, stats: dict) -> list[float]:
    """Build the model-ready feature vector from a cleaned sample + rolling
    stats dict (as produced by Preprocessor.process)."""

    temp_deviation = cleaned["temperature"] - BASELINE["temperature"]
    vib_deviation = cleaned["vibration"] - BASELINE["vibration"]
    pressure_deviation = cleaned["pressure"] - BASELINE["pressure"]

    # A simple, explainable combined degradation indicator: weighted sum of
    # normalized deviations + rates of change. Not the final degradation
    # score (that's computed downstream from ML + this feature) — this is
    # just an engineered *input* signal that helps the models see combined
    # multi-sensor drift.
    combined_degradation_index = (
        0.30 * max(0.0, temp_deviation) / 40.0
        + 0.30 * max(0.0, vib_deviation) / 6.0
        + 0.20 * max(0.0, -pressure_deviation) / 2.5
        + 0.20 * (abs(stats["rpm"]["std"]) / 500.0)
    )

    vector = [
        cleaned["rpm"],
        cleaned["temperature"],
        cleaned["vibration"],
        cleaned["pressure"],
        cleaned["load"],
        stats["temperature"]["ma"],
        stats["vibration"]["ma"],
        stats["temperature"]["roc"],
        stats["vibration"]["roc"],
        stats["rpm"]["std"],
        pressure_deviation,
        temp_deviation,
        vib_deviation,
        combined_degradation_index,
    ]
    return vector


def feature_dict(cleaned: dict, stats: dict) -> dict:
    vec = build_feature_vector(cleaned, stats)
    return dict(zip(FEATURE_NAMES, vec))
