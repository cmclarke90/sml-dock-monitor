# Wiring Guide

> To be completed in Phase 2 once hardware arrives.

## Components

- Raspberry Pi Zero 2 W
- 2x HT16K33 4-digit 7-segment display (0.56")
- 5V 2.5A micro USB power supply

## I2C Addressing

Two displays on the same I2C bus require different addresses.
The HT16K33 supports 8 addresses via solder jumpers (A0, A1, A2):

| Display | Shows | Address | Jumper setting |
|---|---|---|---|
| Display 1 | Lake level | 0x70 | Default (no jumper) |
| Display 2 | Water temp | 0x71 | Bridge A0 |

## Pi Zero 2 W GPIO Pinout (I2C)

| Pi Pin | Label | Display wire |
|---|---|---|
| Pin 1 | 3.3V | VCC |
| Pin 3 | SDA | SDA |
| Pin 5 | SCL | SCL |
| Pin 6 | GND | GND |

Both displays share the same 4 wires — I2C is a bus, so multiple
devices share SDA/SCL as long as they have different addresses.

## Wiring Diagram

> To be added in Phase 2.
