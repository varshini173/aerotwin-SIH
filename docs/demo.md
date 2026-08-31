# SIH Demonstration Sequence

Prerequisite: backend (`uvicorn main:app --reload`) and frontend
(`npm run dev`) both running, dashboard open at `http://localhost:5173/` on
the **Overview** page. See `docs/setup.md` if not already running.

---

## DEMO 1 — Start Normal

1. On the Overview page, click **RESET SIMULATION** in the Simulation
   Controls panel (top-right area) to guarantee a clean healthy baseline.
2. Point out:
   - Engine Health card ≈ 90–100%
   - Fault Risk card near 0%
   - RPM, Temperature, Vibration telemetry bars all green/steady
   - Digital Twin visualizer showing green ("healthy") cylinders and a
     smoothly rotating flywheel
   - System Logs panel showing `INFO: Engine operating normally.`

**Narration:** "This is the digital twin at rest — a healthy MALE UAV piston
engine, all five sensors within normal operating bounds, health score close
to 100%."

## DEMO 2 — Trigger a Developing Fault

1. Click **INJECT OVERHEAT** in Simulation Controls.
2. Watch for ~15–20 seconds. Point out the *gradual* change: temperature
   climbing tick by tick (not jumping instantly), vibration ticking up
   slightly, RPM drifting.

**Narration:** "Notice the backend doesn't jump straight to a fault — the
simulator ramps severity gradually, exactly like a real developing engine
issue, and every downstream stage (preprocessing, features, ML) is
recomputing on each new tick."

## DEMO 3 — Show Prediction

1. Switch to the **Live Monitoring** page.
2. Point out:
   - Anomaly Score rising
   - Current Prediction changing from `NONE` to `OVERHEAT`
   - Live charts for Temperature/Vibration/Anomaly Score trending upward
3. Switch to the **Digital Twin** page — cylinders should now show amber
   ("warning") or red ("critical") depending on how far severity has
   progressed, with the status badge updated accordingly.
4. Switch back to **Overview** — Fault Risk and Degradation cards climbing,
   Engine Health card falling, EST. RUL card falling.

**Narration:** "The Random Forest fault classifier has identified this as an
overheating fault with rising confidence, the Isolation Forest anomaly score
agrees, and the Gradient Boosting RUL regressor is revising its estimate of
remaining engine life downward in real time."

## DEMO 4 — Mission Test

1. Go to the **Mission Readiness** page.
2. Enter a **Planned Mission Duration** (e.g. `2` hours) and **Expected
   Mission Load** (e.g. `70`%).
3. Click **EVALUATE MISSION**.
4. With the engine still degrading from Demo 2/3, this should now show
   **MODERATE** or **HIGH** risk with a recommendation to inspect before
   flight.

**Narration:** "The mission module compares the current RUL and health
against what this specific mission would demand, factoring in the higher
expected load — this is where predictive maintenance turns into an actual
go/no-go decision support tool."

## DEMO 5 — Critical Condition

1. Return to **Overview**, click **ACCEL. DEGRADATION** (Combined
   Degradation scenario) to accelerate toward a critical state faster.
2. Wait ~20–30 seconds. Point out:
   - Engine Health card in the red, Fault Risk near 100%
   - Digital Twin fully red/critical with the glow effect
   - System Logs showing `CRITICAL: Engine approaching critical condition.`
   - Mission Readiness page (revisit) now showing **HIGH** risk /
     **NOT READY** with "Inspect and service engine before mission."

**Narration:** "This is the fully critical state — every layer of the
pipeline agrees the engine needs maintenance before it can safely fly this
mission."

## DEMO 6 — Reset

1. Return to **Overview**, click **RESET SIMULATION**.
2. Engine should return to the healthy baseline within a couple of ticks;
   a new run begins.
3. (Optional) Switch to the **History** page and select the just-completed
   run from the Run History list to show mission replay — full time-series
   charts and the major-alerts log for that run, persisted in SQLite.

**Narration:** "Every run is persisted, so judges can replay exactly what
happened during any earlier fault-injection scenario — this is the mission
replay and audit trail component of the platform."

---

## Tips for a smooth demo

- Run **DEMO 1 → RESET** right before you start presenting, so you begin from
  a guaranteed-clean baseline.
- Fault scenarios take roughly 20–40 seconds to become clearly visible
  (by design — see README "RUL Explanation" for why severity ramps are
  gradual rather than instant). Narrate over that time rather than waiting
  in silence.
- If you want a faster/slower demo pace, the ramp rate for each scenario is
  a single tunable constant per scenario in
  `backend/simulator/engine_simulator.py` → `SEVERITY_RAMP_RATE`.
