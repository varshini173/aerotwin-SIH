# AeroTwin — Bug Fix Changelog

Three fixes applied after live-testing the backend (not just code review). All
three were confirmed present by actually running the pipeline, and confirmed
fixed the same way — before/after tick output, not just re-reading the code.

---

## Fix 1 — Missing buffer warm-up on source switch / Arduino connect
**File:** `backend/main.py`
**Functions:** `set_source()`, `connect_serial()`

`reset_engine()` already ran 5 priming ticks after clearing the rolling
buffers, specifically to stop the first few post-reset samples from looking
spuriously degraded (empty rolling-stats window -> noisy std/roc -> unstable
ML output). `set_source()` and `connect_serial()` reset the exact same
buffers but were missing that warm-up loop, so switching Software<->Arduino,
or clicking Connect in the Arduino modal, could show a few seconds of
misleading "DEGRADING" / elevated fault-risk output before settling.

**Fix:** added the same `for _ in range(5): run_pipeline_tick()` warm-up to
both functions, right after `preprocessor.reset()` / `twin.reset()`.

---

## Fix 2 — Contradictory "High fault risk: NONE" alert
**File:** `backend/digital_twin/twin_state.py`
**Function:** `_evaluate_alerts()`

`faultRisk` is computed as `1 - P(NONE)`, so it can read "high" purely from
probability mass being spread across multiple fault classes even while
`NONE` is still the single most likely class. The alert logic fired
regardless of which class was actually predicted, producing messages like
"CRITICAL: High fault risk: NONE." — confirmed live during testing.

**Fix:** fault-risk alerts now only fire when `faultType != "NONE"`, i.e.
when the model has actually identified a specific fault class.

---

## Fix 3 — Locked/unwired sensor channels read as anomalous (persistent, not transient)
**File:** `backend/simulator/hardware_ingest.py`

The most significant of the three. With a partial hardware rig (e.g. only
Pressure wired to A3), the other four channels are held at an exact constant
value forever (rpm=4200.0, temperature=72.0, etc. every single tick). That
means their rolling standard deviation and rate-of-change are EXACTLY zero,
every tick, indefinitely.

The ML models were trained on synthetic data (`ml/training/train_models.py`)
where even healthy ("NONE") samples had realistic sensor noise baked in via
`EngineSimulator`'s jitter — so a perfectly flat, zero-variance signal never
appeared in training data at all. Verified by running 30 consecutive ticks
against the exact baseline: faultRisk stayed pinned at 81.0% / faultType
"PROGRESSIVE_DEGRADATION" / status "NORMAL" the entire time, with zero
variation — i.e. this isn't a one-off, it's a standing false positive for
the entire duration any channel stays unwired.

**Fix:** `HardwareIngest` now tracks which channels have ever received a
real sample (`_received_keys`). Channels that HAVE received real hardware
data are returned exactly as-is (no synthetic noise added — never touch
real sensor readings). Channels that have NOT received real data get small
physically-realistic jitter around their healthy baseline (matching the
noise magnitude used in `EngineSimulator`'s own "normal" scenario), so they
stay statistically consistent with what the models were actually trained on
instead of looking like an impossible perfect flat line.

**Verified after fix:** same 30-tick test now shows faultRisk fluctuating
normally in the 0-10% range with faultType "NONE" — matching how the
software simulator behaves in its own Normal scenario.

---

## Known remaining issue (not fixed here, by request — separate follow-up)
Even with all three fixes applied, `status` can still flicker between
NORMAL/DEGRADING/HEALTHY tick-to-tick when sensor values are steady, because
the fault classifier takes raw single-tick sensor values as direct inputs
(alongside the moving averages), so one noisy sample can cross a decision
boundary. Not incorrect, just visually jumpy for a live demo. Recommended
follow-up: add a smoothing/hysteresis step so displayed `status` only
changes after N consecutive ticks agree, without touching the trained model.
