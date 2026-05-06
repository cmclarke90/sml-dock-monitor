# SML Dock Monitor

A Raspberry Pi-based display showing real-time Smith Mountain Lake
water level and temperature. Designed to sit on a dock or countertop.

## What It Shows

- **Lake level** — current AEP forebay reading in feet, with delta vs. full pond (795.0 ft)
- **Water temperature** — Becky's Creek sensor reading in °F

Both values update automatically every 5 minutes.

## Data Source

All data comes from the [SML+ app](https://app.sml.plus) API — a community-built
sensor network for Smith Mountain Lake, VA.

- Lake level source: AEP (Appalachian Power), updates every ~5 minutes
- Water temp source: Becky's Creek physical sensor, updates hourly

No API key required.

## Hardware

| Part | Notes |
|---|---|
| Raspberry Pi Zero 2 W | Main compute board |
| 2x HT16K33 4-digit 7-segment display | One per stat, I2C |
| 32GB microSD | OS + script |
| 5V 2.5A micro USB power supply | CanaKit or equivalent |
| IP65 project enclosure | Weatherproofing (Phase 3) |

## Project Phases

- ✅ **Phase 1** — Data validation (Python script, runs on any machine)
- 🔲 **Phase 2** — Pi + display prototype (indoors, no enclosure)
- 🔲 **Phase 3** — Enclosure + weatherproofing
- 🔲 **Phase 4** — Deploy to dock

## Setup

### Requirements

```bash
pip3 install requests
```

### Phase 2 (on Pi, adds display support)

```bash
pip3 install adafruit-circuitpython-ht16k33
```

### Run

```bash
python3 src/sml_monitor.py
```

### Run on Boot (Phase 2)

Create a systemd service so the script starts automatically:

```ini
# /etc/systemd/system/sml-monitor.service
[Unit]
Description=SML Dock Monitor
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/sml-dock-monitor/src/sml_monitor.py
Restart=always
RestartSec=30
User=pi

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable sml-monitor
sudo systemctl start sml-monitor
```

## Wiring

See [docs/wiring.md](docs/wiring.md).

## License

MIT
