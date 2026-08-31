"""
Data Preprocessing
===================
Maintains a rolling time-series buffer of raw telemetry samples and derives
cleaned / smoothed series used by feature engineering.

Responsibilities:
* Validation      - reject/clip physically impossible values
* Missing value    - forward-fill from last known good sample
* Outlier handling - clip transient spikes beyond a hard sensor range
* Moving averages / rolling statistics
* Rate of change (first derivative) per sensor
"""

from __future__ import annotations

from collections import deque

SENSOR_KEYS = ["rpm", "temperature", "vibration", "pressure", "load"]

# Hard physical bounds used for outlier clipping / validation
VALID_RANGE = {
    "rpm": (0, 8000),
    "temperature": (-20, 200),
    "vibration": (0, 20),
    "pressure": (0, 10),
    "load": (0, 100),
}

WINDOW_SIZE = 20  # ~20 samples of rolling history (seconds, at 1Hz)


class Preprocessor:
    def __init__(self, window_size: int = WINDOW_SIZE):
        self.window_size = window_size
        self.buffers = {k: deque(maxlen=window_size) for k in SENSOR_KEYS}
        self._last_good: dict = {}

    def process(self, sample: dict) -> dict:
        """Validate + clean a raw sample, push into rolling buffers, and
        return the cleaned sample plus rolling statistics."""
        cleaned = {}
        for key in SENSOR_KEYS:
            val = sample.get(key)
            val = self._validate(key, val)
            cleaned[key] = val
            self.buffers[key].append(val)
            self._last_good[key] = val

        stats = self._rolling_stats()
        return {
            "cleaned": cleaned,
            "stats": stats,
        }

    # ------------------------------------------------------------------
    def _validate(self, key: str, val):
        lo, hi = VALID_RANGE[key]
        if val is None:
            # Missing value -> forward fill
            return self._last_good.get(key, (lo + hi) / 2)
        try:
            val = float(val)
        except (TypeError, ValueError):
            return self._last_good.get(key, (lo + hi) / 2)
        # Outlier clip to physical sensor bounds
        if val < lo or val > hi:
            val = max(lo, min(hi, val))
        return val

    def _rolling_stats(self) -> dict:
        stats = {}
        for key in SENSOR_KEYS:
            buf = list(self.buffers[key])
            if not buf:
                stats[key] = {"mean": 0.0, "std": 0.0, "roc": 0.0, "ma": 0.0}
                continue
            n = len(buf)
            mean = sum(buf) / n
            variance = sum((x - mean) ** 2 for x in buf) / n
            std = variance ** 0.5
            # Rate of change: difference between latest and previous sample
            roc = buf[-1] - buf[-2] if n >= 2 else 0.0
            # Moving average over last min(5, n) samples
            ma_window = buf[-5:]
            ma = sum(ma_window) / len(ma_window)
            stats[key] = {"mean": mean, "std": std, "roc": roc, "ma": ma}
        return stats

    def reset(self):
        for k in SENSOR_KEYS:
            self.buffers[k].clear()
        self._last_good = {}
