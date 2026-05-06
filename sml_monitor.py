#!/usr/bin/env python3
"""
SML Dock Monitor
================
Fetches real-time Smith Mountain Lake data and displays it
on two Adafruit HT16K33 7-segment displays connected to a
Raspberry Pi Zero 2 W via I2C.

Data source: app.sml.plus (SML+ app API)
  - Lake level: AEP forebay reading, updates every ~5 minutes
  - Water temp: Becky's Creek sensor, updates hourly

Hardware (Phase 2):
  - Raspberry Pi Zero 2 W
  - 2x Adafruit 0.56" 4-digit 7-segment display w/ HT16K33 backpack
  - Connected via I2C (SDA/SCL)

Usage:
  python3 sml_monitor.py

Requirements:
  pip3 install requests
  # Phase 2 (on Pi):
  # pip3 install adafruit-circuitpython-ht16k33
"""

import time
import requests
from datetime import datetime

# ── Configuration ─────────────────────────────────────────────────────────────

API_URL       = "https://app.sml.plus/v5/sml/data/array24hrs.php"
FULL_POND     = 795.0          # Smith Mountain Lake full pond elevation (ft)
REFRESH_SEC   = 300            # How often to poll the API (5 minutes)
HEADERS       = {"User-Agent": "SML-Dock-Monitor/1.0"}

# ── Data Fetching ──────────────────────────────────────────────────────────────

def get_sml_data():
    """
    Fetch current lake level and water temperature from SML+ API.

    Response structure:
      data[0] = {"Average_Level": "792.83"}
      data[1] = {"Temp_Fahrenheit": "61.03", "Oberservation_Time": "...", ...}
      data[2] = {"AEP_Projection": "0.00"}
      data[3] = [{"Forbay_Actual_Feet": "790.14", "Last_Updated": "..."}, ...]

    Returns dict with level_ft, temp_f, diff, and timestamps.
    Raises requests.RequestException on network failure.
    """
    r = requests.get(API_URL, headers=HEADERS, timeout=10)
    r.raise_for_status()
    data = r.json()

    level_ft  = float(data[3][0]["Forbay_Actual_Feet"])
    level_ts  = data[3][0]["Last_Updated"]
    temp_f    = float(data[1]["Temp_Fahrenheit"])
    temp_ts   = data[1]["Oberservation_Time"]  # Note: typo in API ("Oberservation")
    avg_level = float(data[0]["Average_Level"])

    return {
        "level_ft":  level_ft,
        "level_ts":  level_ts,
        "avg_level": avg_level,
        "diff":      level_ft - FULL_POND,
        "temp_f":    temp_f,
        "temp_ts":   temp_ts,
    }

# ── Display ────────────────────────────────────────────────────────────────────

def update_displays(data):
    """
    Push values to the 7-segment displays.
    Phase 1: prints to console.
    Phase 2: will drive HT16K33 displays via I2C.
    """
    # TODO (Phase 2): initialize I2C and display objects
    # from busio import I2C
    # from board import SCL, SDA
    # from adafruit_ht16k33.segments import Seg7x4
    # i2c = I2C(SCL, SDA)
    # level_display = Seg7x4(i2c, address=0x70)
    # temp_display  = Seg7x4(i2c, address=0x71)
    # level_display.print(f"{data['level_ft']:.1f}")
    # temp_display.print(f"{data['temp_f']:.1f}")

    # Phase 1: console output
    sign = "+" if data["diff"] >= 0 else ""
    print(f"  Lake level: {data['level_ft']:.2f} ft  ({sign}{data['diff']:.2f} vs full pond)")
    print(f"  Water temp: {data['temp_f']:.1f} °F  (Becky's Creek)")
    print(f"  Level updated: {data['level_ts']}")
    print(f"  Temp updated:  {data['temp_ts']}")

# ── Main Loop ──────────────────────────────────────────────────────────────────

def main():
    print("=" * 50)
    print("  SML Dock Monitor")
    print(f"  Full pond: {FULL_POND} ft")
    print(f"  Refresh interval: {REFRESH_SEC}s")
    print("=" * 50)

    last_data = None

    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{now}] Fetching...")

        try:
            data = get_sml_data()
            last_data = data
            update_displays(data)

        except requests.RequestException as e:
            print(f"  Network error: {e}")
            if last_data:
                print("  Showing last known values:")
                update_displays(last_data)
            else:
                print("  No data available yet.")

        except Exception as e:
            print(f"  Unexpected error: {e}")

        print(f"  Next refresh in {REFRESH_SEC}s...")
        time.sleep(REFRESH_SEC)


if __name__ == "__main__":
    main()
