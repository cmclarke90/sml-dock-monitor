# Wiring Guide

## Overview

The Adafruit 1.2" 7-segment display (product #1269) uses an HT16K33 backpack
that communicates over I2C. Four wires run from the Pi's GPIO header to the
display backpack via a STEMMA QT cable.

---

## Components

| Item | Notes |
|---|---|
| Raspberry Pi Zero 2 W | I2C on GPIO pins 3 (SDA) and 5 (SCL) |
| Adafruit 1.2" 7-seg + HT16K33 backpack | Product #1269, yellow |
| STEMMA QT cable | JST SH 4-pin connector into backpack port; female Dupont ends onto Pi GPIO |

---

## Pin Connections

| Pi GPIO Pin | Pi Label | Wire Color | Backpack Label |
|---|---|---|---|
| Pin 1 | 3.3V | Red | VCC (or 3V) |
| Pin 3 | SDA | Blue | SDA |
| Pin 5 | SCL | Yellow | SCL |
| Pin 6 | GND | Black | GND |

Note: The backpack accepts 3.3V or 5V on VCC. Use Pin 1 (3.3V), not Pin 2 (5V), to match the Pi Zero 2 W's logic level.

---

## I2C Address

The HT16K33 backpack defaults to address 0x70 with no solder jumpers bridged. This is the only display in this build, so no address changes are needed.

Confirm the display is detected after wiring:

    i2cdetect -y 1

Expected output — 70 should appear in the grid:

         0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
    00:          -- -- -- -- -- -- -- -- -- -- -- -- --
    10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    70: 70 -- -- -- -- -- -- --

If 70 does not appear, check:
- I2C is enabled (sudo raspi-config → Interface Options → I2C)
- All four wires are seated firmly
- VCC is connected (display will not respond without power)

---

## Enable I2C on the Pi

If not already done:

    sudo raspi-config
    # Interface Options → I2C → Enable → Finish
    sudo reboot

---

## Critical Display Notes

These were discovered through testing and are easy to get wrong:

- Use BigSeg7x4, not Seg7x4 in code. Product #1269 is the 1.2" display. Seg7x4 targets the 0.56" variant. Digits render on either class, but the ampm dot and colon only behave correctly with BigSeg7x4.

- No per-digit decimal point LEDs. The decimal point segments are physically absent on this display face. Calling display.print("790.5") silently drops the decimal. The script uses the ampm dot as a decimal indicator instead.

- ampm dot is present and functional. It is a small standalone dot in the top-right area of the display face — not a digit segment.

- Colon syntax. Use display.colon[1] = True, not display.colon = True. The indexed form is required for BigSeg7x4; the bare property silently fails.

- top_left_dot and bottom_left_dot are also present and working — these are the two individual LED segments that together form the colon.

---

## Future: Adding a Second Display

If a second HT16K33 display is added to the I2C bus (e.g. for a two-display build showing level and temp simultaneously), both displays share the same four wires but must have different I2C addresses.

The HT16K33 supports 8 addresses via solder jumpers on the backpack (A0, A1, A2):

| Display | Address | Jumper |
|---|---|---|
| Display 1 | 0x70 | Default (no jumper) |
| Display 2 | 0x71 | Bridge A0 |

Both displays then share SDA, SCL, VCC, and GND — I2C is a bus, so multiple devices coexist as long as addresses are unique.
