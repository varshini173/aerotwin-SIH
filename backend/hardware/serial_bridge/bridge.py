"""
AeroTwin Serial-to-Backend Bridge
====================================
Your Arduino UNO has no WiFi, so it can't POST to the backend directly
over WiFi. This script sits in the middle: it reads the
JSON lines the UNO prints over USB serial, and forwards each one as an
HTTP POST to the backend's /api/engine/ingest endpoint.

Run this on the SAME laptop the Arduino is plugged into (and that's
running the AeroTwin backend, or that can reach it over the network).

Setup:
    pip install pyserial requests

Before running this, start the backend in hardware mode:
    cd backend
    USE_HARDWARE=1 uvicorn main:app --reload      (macOS/Linux)
    $env:USE_HARDWARE="1"; uvicorn main:app --reload   (Windows PowerShell)

Then run this bridge:
    python bridge.py --port COM5          (Windows, check Device Manager)
    python bridge.py --port /dev/ttyUSB0  (Linux)
    python bridge.py --port /dev/cu.usbmodem14101   (macOS, check `ls /dev/cu.*`)
"""

from __future__ import annotations

import argparse
import json
import sys
import time

import requests
import serial  # pyserial

DEFAULT_BAUD = 115200
DEFAULT_BACKEND_URL = "http://localhost:8000/api/engine/ingest"


def main():
    parser = argparse.ArgumentParser(description="Forward Arduino UNO serial telemetry to AeroTwin backend")
    parser.add_argument("--port", required=True, help="Serial port, e.g. COM5, /dev/ttyUSB0, /dev/cu.usbmodem14101")
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD, help=f"Baud rate (default {DEFAULT_BAUD}, must match the .ino sketch)")
    parser.add_argument("--backend", default=DEFAULT_BACKEND_URL, help=f"Backend ingest URL (default {DEFAULT_BACKEND_URL})")
    args = parser.parse_args()

    print(f"Opening serial port {args.port} at {args.baud} baud...")
    try:
        ser = serial.Serial(args.port, args.baud, timeout=2)
    except serial.SerialException as e:
        print(f"Could not open serial port: {e}")
        print("Check that: the Arduino is plugged in, the port name is right, "
              "and the Arduino IDE's Serial Monitor is CLOSED (only one program can use the port at a time).")
        sys.exit(1)

    time.sleep(2)  # Arduino resets on serial connect; give it a moment to boot
    print(f"Connected. Forwarding to {args.backend}")
    print("Turn the potentiometer and watch values change. Ctrl+C to stop.\n")

    while True:
        try:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                continue  # timeout with no data, just keep looping

            try:
                sample = json.loads(line)
            except json.JSONDecodeError:
                print(f"[skip] not valid JSON: {line!r}")
                continue

            try:
                resp = requests.post(args.backend, json=sample, timeout=2)
                if resp.status_code != 200:
                    print(f"{sample}  ->  HTTP {resp.status_code}")
                    continue
                body = resp.json()
                if body.get("accepted") is True:
                    print(f"{sample}  ->  OK (accepted)")
                else:
                    # The backend responded but did NOT ingest the sample —
                    # most commonly because it's not running with
                    # USE_HARDWARE=1. Printing this loudly instead of a
                    # bare "OK" is the whole point: a silent false-OK here
                    # is exactly what makes "nothing moves on the dashboard"
                    # so confusing to debug.
                    reason = body.get("reason", "unknown reason")
                    print(f"{sample}  ->  REJECTED: {reason}")
            except requests.RequestException as e:
                print(f"[warn] backend unreachable: {e}")
            except ValueError:
                print(f"[warn] backend returned a non-JSON response (unexpected)")

        except KeyboardInterrupt:
            print("\nStopping.")
            break
        except UnicodeDecodeError:
            continue  # garbled byte on connect, ignore

    ser.close()


if __name__ == "__main__":
    main()
