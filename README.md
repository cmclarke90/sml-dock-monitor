# SML Dock Monitor

A Raspberry Pi Zero 2 W dock display that shows real-time Smith Mountain Lake
water level and temperature on a 1.2" 7-segment LED display. Runs headlessly
as a systemd service, auto-starts on boot, and recovers gracefully from network
outages.

---

## What It Shows

The display cycles through four screens (20 seconds each, 1-second blank between):

| Screen | Example | What it means |
|---|---|---|
| Lake level | `7905` + dot | 790.5 ft elevation |
| vs. full pond | `_-47` + dot | 4.7 ft below full pond (795.0 ft) |
| Water temperature | `61°F` | Current temp |
| Time of last reading | `9:05` | 12-hour format with colon |

> "Full pond" on SML is 795.0 ft. If the lake is at or above that, screen 2 shows `FULL`.

---

## Hardware

| Item | Notes |
|---|---|
| Raspberry Pi Zero 2 W | Micro USB power |
| SanDisk 32GB microSD | Raspberry Pi OS Lite (Trixie) |
| CanaKit 5V 2.5A micro USB supply | |
| Adafruit 1.2" 7-segment + HT16K33 backpack | Yellow, product [#1269](https://www.adafruit.com/product/1269) |
| STEMMA QT cable | JST into backpack, female ends onto Pi GPIO |
| TICONN IP67 enclosure 5.9"×3.9"×2.8" | Outdoor enclosure |

### Wiring

Both the display backpack and the Pi use I2C. Connect via STEMMA QT cable:

| Pi GPIO Pin | Label | Wire color |
|---|---|---|
| Pin 1 | 3.3V | Red |
| Pin 3 | SDA | Blue |
| Pin 5 | SCL | Yellow |
| Pin 6 | GND | Black |

The HT16K33 backpack defaults to I2C address `0x70`. Confirm with `i2cdetect -y 1`.

### Critical hardware notes (hard-won)

- **Use `BigSeg7x4`, not `Seg7x4`** — product #1269 is the 1.2" display.
  `Seg7x4` is for the 0.56" display. Digits work on either class, but the
  `ampm` dot and colon properties only wire correctly on `BigSeg7x4`.
- **No per-digit decimal point LEDs** — the decimal point segments are
  physically absent on this display face. `display.print("790.5")` silently
  drops the decimal. The script works around this using the `ampm` dot.
- **`ampm` dot is present and working** — it's the small dot in the top-right
  corner. The script uses it as a stand-in decimal indicator.
- **Colon syntax** — use `display.colon[1] = True`, not `display.colon = True`.
  The latter works on `Seg7x4` but silently fails on `BigSeg7x4`.

---

## Data Source

- **URL:** [protected information]
- **Format:** XML, updated approximately hourly
- **Fields used:** `LakeLevel` (ft), `LakeTemperature` (°F), `EffectiveTime`
- **Refresh rate: every 3 hours** — mandatory, per the data owner's request.
  Do not reduce this value.

---

## Software

### Dependencies

Enable I2C on the Pi first:

```bash
sudo raspi-config  # Interface Options → I2C → Enable
```

Install Python packages:

```bash
pip3 install adafruit-circuitpython-ht16k33 adafruit-blinka --break-system-packages
```

