# Architecture

## Data flow (per ~1 second tick)

1. **`backend/simulator/engine_simulator.py`** — `EngineSimulator.tick()`
   advances a stateful simulation one step, smoothing sensor values toward a
   scenario-specific target with bounded noise. Returns a raw sample dict.
2. **`backend/preprocessing/preprocess.py`** — `Preprocessor.process()`
   validates/clips the sample against physical sensor bounds, forward-fills
   missing values, pushes into a rolling 20-sample buffer per sensor, and
   computes rolling mean/std/rate-of-change/moving-average.
3. **`backend/features/feature_engineering.py`** — `build_feature_vector()`
   turns the cleaned sample + rolling stats into a fixed 14-dim numeric
   feature vector (raw values, moving averages, rates of change, RPM
   variability, baseline deviations, combined degradation index).
4. **`backend/prediction/predictor.py`** — `Predictor.predict()` loads the
   three trained models (`backend/saved_models/*.joblib`) and computes:
   anomaly score + flag, fault type + fault risk, engine health,
   degradation, RUL hours, time-to-critical minutes, and status.
5. **`backend/mission/mission_assessment.py`** — `assess_mission()` compares
   predicted capability against the currently configured mission duration
   and expected load to produce a mission risk/readiness verdict.
6. **`backend/digital_twin/twin_state.py`** — `DigitalTwin.update()` merges
   all of the above into one state dict, evaluates alert rules, and appends
   any new alerts to a rolling feed.
7. **`backend/storage/db.py`** — `HistoryStore.insert_sample()` persists the
   full state row to SQLite for the History/Replay page.
8. **`backend/main.py`** — the background `engine_loop()` task runs steps
   1–7 every second and broadcasts the resulting JSON state to every
   connected WebSocket client at `/ws/engine`. All REST endpoints read from
   the same `_latest_state` / SQLite store, so REST and WebSocket clients
   always see consistent data.

## Frontend architecture

- **`src/hooks/useEngineSocket.js`** — a single reusable hook opens (and
  auto-reconnects) the WebSocket, exposes `{state, connected, history}`.
  Each page instantiates its own subscription with the history-buffer size
  it needs for its charts.
- **`src/services/api.js`** — thin fetch wrapper for all REST calls
  (scenario control, mission evaluation, run history/replay).
- **`src/pages/*.jsx`** — one component per nav item (Overview, Digital
  Twin, Live Monitoring, Mission Readiness, History), composed from shared
  components in `src/components/` and chart wrappers in `src/charts/`.
- **`src/components/Sidebar.jsx` / `Header.jsx`** — layout shell, preserved
  from the original Stitch design (glassmorphic dark theme, cyan/emerald/
  amber/rose status colors, Inter + JetBrains Mono typography).

## Why these design choices

- **SQLite over CSV** for history: the History/Replay page needs to query by
  `run_id` and paginate without loading an ever-growing file into memory.
- **Isolation Forest fit on healthy-only data**: makes the "abnormal
  behavior" signal explainable and independent of the supervised fault
  classifier, so the two can be cross-checked in the alert logic.
- **Gradient Boosting for RUL**: handles the non-linear relationship between
  multi-sensor degradation state and remaining time better than plain linear
  regression, while staying fast enough to retrain in seconds for a demo.
- **Single global engine instance in `main.py`**: this is a single-engine
  hackathon prototype by design (see README Limitations) — multi-engine
  support is listed under Future Scope.
