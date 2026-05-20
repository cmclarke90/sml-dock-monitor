#!/usr/bin/env python3
"""
SML Dock Monitor — rotating display
Data source: SmithMountainLakeLevel.com personal API (XML)
Refreshes every 3 hours out of respect for the hosted server.

View 1: Lake level rounded to nearest foot  e.g.  790
View 2: Deficit from full pond              e.g.   -5
View 3: Water temperature                   e.g.  61°F
View 4: Time of last data reading           e.g.  2:08
Rotates every 30 seconds with a 1-second blank between views.
"""

import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import board
import busio
from adafruit_ht16k33.segments import Seg7x4

# ── Configuration ─────────────────────────────────────────────────────────────

API_URL     = "http://SmithMountainLakeLevel.com/CurrentLevel.xml"
FULL_POND   = 795.0
REFRESH_SEC = 10800  # 3 hours — please do not reduce, per data owner's request
ROTATE_SEC  = 30
PAUSE_SEC   = 1

HEADERS = {"User-Agent": "SML-Dock-Monitor/1.0"}

# ── Segment bitmasks ───────────────────────────────────────────────────────────

DIGITS        = [0x3F,0x06,0x5B,0x4F,0x66,0x6D,0x7D,0x07,0x7F,0x6F]
DEGREE_SYMBOL = 0x63
LETTER_F      = 0x71

# ── Data Fetching ──────────────────────────────────────────────────────────────

def get_sml_data():
    """
    Fetch current lake level and water temperature from SmithMountainLakeLevel.com.
    Returns dict with level_ft, temp_f, diff, change_rate, and timestamps.
    Raises requests.RequestException on network failure.
    """
    r = requests.get(API_URL, headers=HEADERS, timeout=10)
    r.raise_for_status()
    root = ET.fromstring(r.text)

    level_ft    = float(root.find('LakeLevel').text)
    level_ts    = root.find('EffectiveDateTime').text
    temp_f      = float(root.find('LakeTemperature').text)
    temp_ts     = root.find('TemperatureEffectiveDateTime').text
    change_rate = float(root.find('LevelChangeRateFeetPerHour').text)

    return {
        "level_ft":    level_ft,
        "level_ts":    level_ts,
        "diff":        level_ft - FULL_POND,
        "change_rate": change_rate,
        "temp_f":      temp_f,
        "temp_ts":     temp_ts,
    }

# ── Display Views ──────────────────────────────────────────────────────────────

def show_level(data, display):
    """Lake level rounded to nearest foot. e.g. 790"""
    display.fill(0)
    display.colon = False
    display.print(str(round(data['level_ft'])))

def show_deficit(data, display):
    """Deficit from full pond rounded to nearest foot. e.g. -5"""
    display.fill(0)
    display.colon = False
    display.print(str(round(data['diff'])))

def show_temp(data, display):
    """Temperature with degree symbol and F. e.g. 61°F
    If temp is outside 0-99 range (bad reading), shows dashes."""
    display.fill(0)
    display.colon = False
    temp = round(data['temp_f'])

    if temp < 0 or temp > 99:
        print(f"  Warning: Ignoring out-of-range temp ({temp}°F)")
        display.print("----")
        return

    tens = temp // 10
    ones = temp % 10
    display.set_digit_raw(0, DIGITS[tens])
    display.set_digit_raw(1, DIGITS[ones])
    display.set_digit_raw(2, DEGREE_SYMBOL)
    display.set_digit_raw(3, LETTER_F)
    display.show()

def show_time(data, display):
    """Time of last reading in 12-hour format with colon. e.g. 2:08"""
    display.fill(0)
    try:
        dt = datetime.fromisoformat(data['level_ts'])
        hour_12 = dt.hour % 12 or 12  # converts 0 to 12 for midnight
        minute  = dt.minute

        hour_tens = hour_12 // 10
        hour_ones = hour_12 % 10
        min_tens  = minute // 10
        min_ones  = minute % 10

        # Single digit hours get a blank first digit so 2:08 not 02:08
        display.set_digit_raw(0, DIGITS[hour_tens] if hour_12 >= 10 else 0x00)
        display.set_digit_raw(1, DIGITS[hour_ones])
        display.set_digit_raw(2, DIGITS[min_tens])
        display.set_digit_raw(3, DIGITS[min_ones])
        display.colon = True
        display.show()

    except Exception as e:
        print(f"  Warning: Could not parse timestamp ({e})")
        display.colon = False
        display.print("----")

def show_blank(display):
    display.fill(0)
    display.colon = False

def rotate_display(data, display, total_seconds):
    """Cycle through all four views with a blank pause between each."""
    elapsed = 0
    view = 0
    views = [show_level, show_deficit, show_temp, show_time]

    while elapsed < total_seconds:
        views[view](data, display)
        time.sleep(ROTATE_SEC)
        elapsed += ROTATE_SEC

        show_blank(display)
        time.sleep(PAUSE_SEC)
        elapsed += PAUSE_SEC

        view = (view + 1) % len(views)

# ── Main Loop ──────────────────────────────────────────────────────────────────

def main():
    print("=" * 50)
    print("  SML Dock Monitor")
    print(f"  Full pond : {FULL_POND} ft")
    print(f"  Refresh   : every {REFRESH_SEC}s ({REFRESH_SEC // 3600}h)")
    print(f"  Rotation  : every {ROTATE_SEC}s")
    print("=" * 50)

    i2c = busio.I2C(board.SCL, board.SDA)
    display = Seg7x4(i2c, address=0x70)

    last_data = None

    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{now}] Fetching...")

        # Show last known level while fetching so display never goes blank
        if last_data:
            show_level(last_data, display)

        try:
            data = get_sml_data()
            last_data = data

            sign = "+" if data["diff"] >= 0 else ""
            direction = "rising" if data["change_rate"] > 0 else "falling" if data["change_rate"] < 0 else "stable"
            print(f"  Lake level : {data['level_ft']:.2f} ft  ({sign}{data['diff']:.2f} vs full pond)")
            print(f"  Change     : {data['change_rate']:+.2f} ft/hr ({direction})")
            print(f"  Water temp : {data['temp_f']:.1f} °F")
            print(f"  Level time : {data['level_ts']}")
            print(f"  Temp time  : {data['temp_ts']}")

            rotate_display(data, display, REFRESH_SEC)

        except requests.RequestException as e:
            print(f"  Network error: {e}")
            if last_data:
                print("  Showing last known values...")
                rotate_display(last_data, display, REFRESH_SEC)
            else:
                print("  No data yet — retrying in 60s")
                time.sleep(60)

        except Exception as e:
            print(f"  Unexpected error: {e}")
            if last_data:
                print("  Showing last known values...")
                rotate_display(last_data, display, REFRESH_SEC)
            else:
                time.sleep(60)


if __name__ == "__main__":
    main()
