/*
  AeroTwin — Arduino UNO Potentiometer Bridge
  =================================================
  Reads up to 5 potentiometers (RPM, Temperature, Vibration, Pressure, Load)
  and prints one JSON line per second over USB Serial. A Python script on
  your laptop (serial_bridge/bridge.py) reads this and forwards it to the
  AeroTwin backend's /api/engine/ingest endpoint — the UNO has no WiFi, so
  it can't POST directly over WiFi.

  WIRING — each potentiometer has 3 pins:
    - One outer pin  -> Arduino 5V   (all pots can share the same 5V rail)
    - Other outer pin -> Arduino GND (all pots can share the same GND rail)
    - Middle pin (wiper) -> the analog pin listed below (each pot needs
      its OWN wiper connection — this is the only per-pot wire)

    A0 -> RPM knob
    A1 -> Temperature knob
    A2 -> Vibration knob
    A3 -> Pressure knob
    A4 -> Load knob

  ============================================================
  ONLY HAVE 1-4 POTENTIOMETERS? -> Edit ONLY the block below.
  ============================================================
  Set each ENABLE_ flag to true ONLY for the knob(s) you actually have
  wired up. Leave the rest false. You do NOT need to touch anything
  else in this file, delete any lines, or comment anything out.

  Why this matters: an Arduino analog pin with nothing physically
  connected to it ("floating") doesn't read as zero — it picks up
  stray electrical noise and drifts around on its own. If that pin
  still gets read and sent, the dashboard shows that channel jittering
  as if it were a real sensor, which is what makes it *look* like
  "every parameter moves" even though you only turned one knob. Setting
  a flag to false means that pin is never read at all, and the key is
  left out of the JSON entirely — the backend then locks that channel
  at a healthy baseline value instead of showing noise (see
  backend/simulator/hardware_ingest.py). Only the channel(s) you set to
  true will move on the dashboard.
*/
const bool ENABLE_RPM         = false;
const bool ENABLE_TEMPERATURE = false;
const bool ENABLE_VIBRATION   = false;
const bool ENABLE_PRESSURE    = true;   // <- example: only Pressure wired up
const bool ENABLE_LOAD        = false;

// ============================================================
// Nothing below this line needs to change for a partial rig.
// ============================================================

const int PIN_RPM = A0;
const int PIN_TEMP = A1;
const int PIN_VIBRATION = A2;
const int PIN_PRESSURE = A3;
const int PIN_LOAD = A4;

const unsigned long SEND_INTERVAL_MS = 1000;  // matches backend's 1Hz tick
unsigned long lastSendTime = 0;

// Map each pot's raw 0-1023 ADC range onto a physically-plausible sensor
// range. These match backend/simulator/engine_simulator.py's BASELINE and
// clamp ranges so real hardware values land in the same territory the ML
// models were trained on.
const float RPM_MIN = 500.0,          RPM_MAX = 7500.0;
const float TEMP_MIN = 20.0,          TEMP_MAX = 160.0;
const float VIBRATION_MIN = 0.1,      VIBRATION_MAX = 12.0;
const float PRESSURE_MIN = 0.5,       PRESSURE_MAX = 8.0;
const float LOAD_MIN = 0.0,           LOAD_MAX = 100.0;

void setup() {
  Serial.begin(115200);
  while (!Serial) { ; }  // wait for serial port on boards that need it
}

void loop() {
  unsigned long now = millis();
  if (now - lastSendTime < SEND_INTERVAL_MS) {
    return;
  }
  lastSendTime = now;

  // Build the JSON line field-by-field. A disabled channel's analog pin
  // is never read (avoids floating-pin noise) and its key is left out of
  // the JSON (the backend then holds that channel at a healthy baseline
  // instead of showing noise as if it were real sensor movement).
  Serial.print("{");
  bool wroteField = false;

  if (ENABLE_RPM) {
    float rpm = mapFloat(analogRead(PIN_RPM), 0, 1023, RPM_MIN, RPM_MAX);
    Serial.print("\"rpm\": ");
    Serial.print(rpm, 1);
    wroteField = true;
  }

  if (ENABLE_TEMPERATURE) {
    float temperature = mapFloat(analogRead(PIN_TEMP), 0, 1023, TEMP_MIN, TEMP_MAX);
    if (wroteField) Serial.print(", ");
    Serial.print("\"temperature\": ");
    Serial.print(temperature, 2);
    wroteField = true;
  }

  if (ENABLE_VIBRATION) {
    float vibration = mapFloat(analogRead(PIN_VIBRATION), 0, 1023, VIBRATION_MIN, VIBRATION_MAX);
    if (wroteField) Serial.print(", ");
    Serial.print("\"vibration\": ");
    Serial.print(vibration, 3);
    wroteField = true;
  }

  if (ENABLE_PRESSURE) {
    float pressure = mapFloat(analogRead(PIN_PRESSURE), 0, 1023, PRESSURE_MIN, PRESSURE_MAX);
    if (wroteField) Serial.print(", ");
    Serial.print("\"pressure\": ");
    Serial.print(pressure, 3);
    wroteField = true;
  }

  if (ENABLE_LOAD) {
    float load = mapFloat(analogRead(PIN_LOAD), 0, 1023, LOAD_MIN, LOAD_MAX);
    if (wroteField) Serial.print(", ");
    Serial.print("\"load\": ");
    Serial.print(load, 1);
    wroteField = true;
  }

  Serial.println("}");
}

float mapFloat(long x, long inMin, long inMax, float outMin, float outMax) {
  return outMin + (outMax - outMin) * (float)(x - inMin) / (float)(inMax - inMin);
}
