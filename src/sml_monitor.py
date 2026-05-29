#!/usr/bin/env python3
"""
SML Dock Monitor
Data source: SmithMountainLakeLevel.com (XML, updated ~hourly)
Refresh: every 3 hours — please do not reduce, per data owner's request

Display rotation (20s each, 1s blank between):
  1. Lake level to one decimal    e.g.  7905 + ampm dot = 790.5
  2. Deficit from full pond       e.g.   _-47 + ampm dot = -4.7  (FULL if diff >= 0)
  3. Water temperature            e.g.  61°F
  4. Time of last reading         e.g.  9:05
"""

import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import board
import busio
from adafruit_ht16k33.segments import BigSeg7x4

# ── Configuration ─────────────────────────────────────────────────────────────

API_URL     = [protected]
FULL_POND   = 795.0
REFRESH_SEC = 10800  # 3 hours — please do not reduce, per data owner's request
ROTATE_SEC  = 20
PAUSE_SEC   = 1

HEADERS = [protected]

# ── Segment bitmasks ──────────────────────────────────────────────────────────

DIGITS        = [0x3F,0x06,0x5B,0x4F,0x66,0x6D,0x7D,0x07,0x7F,0x6F]
DEGREE_SYMBOL = 0x63
LETTER_F      = 0x71
LETTER_U      = 0x3E
LETTER_L      = 0x38
MINUS         = 0x40

# ── Data Fetching ──────────────────────────────────────────────────────────────

def get_sml_data():
    r = requests.get(API_URL, headers=HEADERS, timeout=10)
    r.raise_for_status()
    root = ET.fromstring(r.text)

    level_ft   = float(root.find('LakeLevel').text)
    temp_f     = float(root.find('LakeTemperature').text)
    level_time = root.find('EffectiveTime').text

    return {
        "level_ft":   level_ft,
        "diff":       level_ft - FULL_POND,
        "temp_f":     temp_f,
        "level_time": level_time,
    }

# ── Display Views ──────────────────────────────────────────────────────────────

def show_level(data, display):
    """Lake level to one decimal. 790.5 shown as 7905 + ampm dot."""
    display.fill(0)
    level_tenths = int(round(data['level_ft'] * 10))
    display.print(str(level_tenths))
    display.ampm = True
    display.show()

def show_deficit(data, display):
    """
    Deficit to one decimal, right-justified. -4.7 shown as _-47 + ampm dot.
    Shows FULL (no dot) if lake is at or above full pond.
    """
    display.fill(0)

    if data['diff'] >= 0:
        display.set_digit_raw(0, LETTER_F)
        display.set_digit_raw(1, LETTER_U)
        display.set_digit_raw(2, LETTER_L)
        display.set_digit_raw(3, LETTER_L)
        display.ampm = False
        display.show()
        return

    abs_val      = abs(data['diff'])
    tenths_total = round(abs_val * 10)
    whole        = tenths_total // 10
    tenth        = tenths_total % 10

    display.set_digit_raw(0, 0x00)
    display.set_digit_raw(1, MINUS)
    display.set_digit_raw(2, DIGITS[whole])
    display.set_digit_raw(3, DIGITS[tenth])
    display.ampm = True
    display.show()

def show_temp(data, display):
    """Temperature with degree symbol and F. e.g. 61°F"""
    display.fill(0)
    temp = round(data['temp_f'])

    if temp < 0 or temp > 99:
        print(f"  Warning: Ignoring out-of-range temp ({temp}°F)")
        display.ampm = False
        display.print("----")
        return

    tens = temp // 10
    ones = temp % 10
    display.set_digit_raw(0, DIGITS[tens])
    display.set_digit_raw(1, DIGITS[ones])
    display.set_digit_raw(2, DEGREE_SYMBOL)
    display.set_digit_raw(3, LETTER_F)
    display.ampm = False
    display.show()

def show_time(data, display):
    """Time of last reading in 12-hour format. e.g. 9:05"""
    display.fill(0)
    try:
        hour, minute = map(int, data['level_time'].split(':'))
        hour_12 = hour % 12 or 12

        display.set_digit_raw(0, DIGITS[hour_12 // 10] if hour_12 >= 10 else 0x00)
        display.set_digit_raw(1, DIGITS[hour_12 % 10])
        display.set_digit_raw(2, DIGITS[minute // 10])
        display.set_digit_raw(3, DIGITS[minute % 10])
        display.ampm = False
        display.colons[0] = True
        display.show()

    except Exception as e:
        print(f"  Warning: Could not parse time ({e})")
        display.print("----")

def show_blank(display):
    display.fill(0)
    display.ampm = False
    display.show()

def rotate_display(data, display, total_seconds):
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
    print(f"  Refresh   : every {REFRESH_SEC // 3600}h")
    print(f"  Rotation  : every {ROTATE_SEC}s")
    print("=" * 50)

    i2c = busio.I2C(board.SCL, board.SDA)
    display = BigSeg7x4(i2c)

    last_data = None

    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{now}] Fetching...")

        if last_data:
            show_level(last_data, display)

        try:
            data = get_sml_data()
            last_data = data

            sign = "+" if data["diff"] >= 0 else ""
            print(f"  Lake level : {data['level_ft']:.1f} ft  ({sign}{data['diff']:.1f} vs full pond)")
            print(f"  Water temp : {data['temp_f']:.1f} °F")
            print(f"  As of      : {data['level_time']}")

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
