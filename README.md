# RepeaterWatch

## Sudoers Configuration

The firmware flash feature requires the `meshcoremon` service user to stop and start `SerialMux` and `mctomqtt` via `systemctl`. Add a sudoers drop-in file so these specific commands run without a password prompt:

```bash
sudo visudo -f /etc/sudoers.d/meshcoremon
```

Contents:

```
meshcoremon ALL=(ALL) NOPASSWD: /usr/bin/systemctl stop SerialMux, /usr/bin/systemctl stop mctomqtt, /usr/bin/systemctl start SerialMux, /usr/bin/systemctl start mctomqtt, /usr/bin/systemctl restart RepeaterWatch, /usr/bin/systemctl reboot
```

---

## Node Swap

When swapping the physical MeshCore radio node, run the node swap script to update the serial port, hardware description, clear cached device info, and restart services automatically:

```bash
sudo python3 /opt/RepeaterWatch/setup_node.py
```

The script will:
1. Show available serial ports and let you select the new one
2. Prompt for an updated hardware description
3. Clear the cached device name, public key, firmware, and GPS from the database
4. Restart SerialMux with the new port
5. Restart RepeaterWatch to re-query the new node

The dashboard should populate with the new node info within 10 seconds of restart.

---

## Password Management

To set or change the dashboard password:

```bash
sudo -u meshcoremon /opt/RepeaterWatch/venv/bin/python3 /opt/RepeaterWatch/setup_auth.py
```

To disable password protection:

```bash
sudo -u meshcoremon /opt/RepeaterWatch/venv/bin/python3 /opt/RepeaterWatch/setup_auth.py --clear
```

---

## Notifications (ntfy.sh)

RepeaterWatch can send push notifications when the node goes offline or recovers. It uses [ntfy.sh](https://ntfy.sh) — a simple pub/sub notification service with free apps for iOS and Android.

### Using the public ntfy.sh server

No account or password needed. Just pick a unique topic name and set it in `.env`:

```
MESHCORE_NTFY_URL=https://ntfy.sh/<your-topic-here>
MESHCORE_NTFY_OFFLINE_THRESHOLD=3
```

Subscribe to the same topic in the ntfy app on your phone. For public server leave `MESHCORE_NTFY_USER` and `MESHCORE_NTFY_PASSWORD` blank.

### Using a self-hosted ntfy server

Install ntfy on the same Pi:

```bash
wget https://github.com/binwiederhier/ntfy/releases/download/v2.23.0/ntfy_2.23.0_linux_arm64.tar.gz
tar zxf ntfy_2.23.0_linux_arm64.tar.gz
sudo cp ntfy_2.23.0_linux_arm64/ntfy /usr/bin/
sudo mkdir -p /etc/ntfy /var/lib/ntfy
sudo cp ntfy_2.23.0_linux_arm64/server/server.yml /etc/ntfy/
sudo useradd --system --home-dir /var/lib/ntfy --shell /bin/false ntfy
sudo cp ntfy_2.23.0_linux_arm64/server/ntfy.service /etc/systemd/system/
```

Minimal `/etc/ntfy/server.yml`:

```yaml
listen-http: "0.0.0.0:8080"
auth-file: "/var/lib/ntfy/user.db"
auth-default-access: "deny-all"
cache-file: "/var/lib/ntfy/cache.db"
```

Create a user and start the service:

```bash
sudo systemctl daemon-reload && sudo systemctl enable --now ntfy
sudo ntfy user add --role=admin <your-username>
```

Then set in `/opt/RepeaterWatch/.env`:

```
MESHCORE_NTFY_URL=http://localhost:8080/<your-topic-here>
MESHCORE_NTFY_USER=<your-username>
MESHCORE_NTFY_PASSWORD=<your-password>
MESHCORE_NTFY_OFFLINE_THRESHOLD=3
```

### RepeaterWatch configuration (`/opt/RepeaterWatch/.env`)

| Variable | Default | Description |
|---|---|---|
| `MESHCORE_NTFY_URL` | *(empty)* | Full ntfy topic URL — leave blank to disable |
| `MESHCORE_NTFY_USER` | *(empty)* | Username for self-hosted auth (leave blank for public server) |
| `MESHCORE_NTFY_PASSWORD` | *(empty)* | Password for self-hosted auth |
| `MESHCORE_NTFY_OFFLINE_THRESHOLD` | `3` | Consecutive failed poll cycles before offline alert fires |

With the default 60-second poll interval, a threshold of 3 means you'll be notified after ~3 minutes of no response.

---

## Dashboard Overview

RepeaterWatch is a real-time web dashboard for monitoring a MeshCore LoRa repeater node. It polls the node over serial and exposes live data through a Flask/WebSocket backend.

### Tabs

#### MeshCore
Live node stats: device info, GPS coordinates, radio metrics (SNR, RSSI, airtime), power levels, packet counters, and channel activity charts. Time window selectable from 1 h to 7 days.

#### Raspberry Pi
Host system health: CPU temperature and load, memory and disk usage, plotted over time.

#### Sensors
Connected I²C/GPIO sensors (temperature, humidity, pressure, etc.) with time-series charts and a sensor management panel for adding or removing entries.

#### Neighbours
All nodes heard by the repeater, including:
- **Map** — Leaflet map showing neighbour positions relative to the repeater. Click the map to pan/zoom; click again to lock.
- **Table** — Neighbour list with last-seen time, distance, SNR, RSSI, and packet counts.
- **SNR History / RSSI History** — Time-series charts showing per-neighbour signal trends over the selected period. Each neighbour gets a consistent color derived from its public key.
  - Hover over a data point to see a tooltip for that specific neighbour.
  - **Click any data point** to open a detail modal showing the exact SNR and RSSI at that moment plus min/avg/max statistics over the loaded period.

Time window for neighbour history is selectable independently from other tabs (1 h / 6 h / 24 h / 7 d).

#### Tools
- **Repeater CLI** — Browser-based serial terminal for direct interaction with the MeshCore node. Supports command history (↑/↓). The stats poller pauses automatically on connect and resumes on disconnect. Sessions time out after 90 seconds of inactivity.
- **Firmware Update** — OTA firmware flash via the MeshCore bootloader.
- **Settings** — Manage stored neighbours, sensor config, and service control.

---

## Repeater CLI

The Tools tab includes a browser-based serial CLI for direct interaction with the MeshCore node. When connected, the stats poller automatically pauses so its background commands don't appear in the terminal output. The poller resumes when you disconnect.

