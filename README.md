# RepeaterWatch

A web dashboard for monitoring a MeshCore repeater node running on a Raspberry Pi. Displays radio stats, sensor data (environmental, power, lightning), packet history, and provides a firmware flash interface and serial terminal.

## Requirements

- Raspberry Pi (tested on Pi 4/5, aarch64)
- Python 3.11+
- MeshCore node connected via serial
- `lgpio` system package (for GPIO): `sudo apt install python3-lgpio`

## Installation

### 1. Create a service user and clone the repo

```bash
sudo useradd -r -s /usr/sbin/nologin -d /opt/RepeaterWatch meshcoremon
sudo mkdir -p /opt/RepeaterWatch
sudo chown meshcoremon:meshcoremon /opt/RepeaterWatch
sudo -u meshcoremon git clone https://github.com/jjkroell/RepeaterWatch.git /opt/RepeaterWatch
cd /opt/RepeaterWatch
```

### 2. Create a Python virtual environment and install dependencies

```bash
sudo -u meshcoremon python3 -m venv /opt/RepeaterWatch/venv
sudo -u meshcoremon /opt/RepeaterWatch/venv/bin/pip install -r requirements.txt
```

> **Note:** `lgpio` must be installed via apt and symlinked into the venv:
> ```bash
> sudo apt install python3-lgpio
> SITE=$(python3 -c "import site; print(site.getsitepackages()[0])")
> VSITE=/opt/RepeaterWatch/venv/lib/python3.*/site-packages
> sudo ln -s $SITE/lgpio.py $VSITE/
> sudo ln -s $SITE/_lgpio*.so $VSITE/
> ```

### 3. Configure

```bash
sudo -u meshcoremon cp /opt/RepeaterWatch/.env.example /opt/RepeaterWatch/.env
sudo -u meshcoremon nano /opt/RepeaterWatch/.env
```

Key settings to update in `.env`:

| Variable | Description |
|---|---|
| `MESHCORE_SERIAL_PORT` | Serial port for MeshCore radio (e.g. `/dev/ttyV0`) |
| `MESHCORE_DB_PATH` | Path to SQLite database file |
| `MESHCORE_SECRET_KEY` | Random string for Flask session signing |
| `MESHCORE_PASSWORD_HASH` | bcrypt password hash (set via `setup_auth.py`) |

### 4. Set a login password

```bash
sudo -u meshcoremon /opt/RepeaterWatch/venv/bin/python3 /opt/RepeaterWatch/setup_auth.py
```

This will prompt for a password, bcrypt-hash it, and write it to `.env`. Leave the password blank (or run with `--clear`) to disable the login gate entirely.

### 5. Install and start the systemd service

```bash
sudo cp /opt/RepeaterWatch/systemd/meshcore-monitor.service /etc/systemd/system/RepeaterWatch.service
sudo systemctl daemon-reload
sudo systemctl enable --now RepeaterWatch
sudo systemctl status RepeaterWatch
```

The dashboard will be available at `http://<pi-ip>:5000`.

### 6. Sudoers configuration (firmware flash feature)

The firmware flash feature requires the `meshcoremon` user to stop and restart `SerialMux` and `mctomqtt` without a password prompt:

```bash
sudo visudo -f /etc/sudoers.d/meshcoremon
```

Contents:

```
meshcoremon ALL=(ALL) NOPASSWD: /usr/bin/systemctl stop SerialMux, /usr/bin/systemctl stop mctomqtt, /usr/bin/systemctl start SerialMux, /usr/bin/systemctl start mctomqtt
```

## Changing the password

```bash
sudo -u meshcoremon /opt/RepeaterWatch/venv/bin/python3 /opt/RepeaterWatch/setup_auth.py
sudo systemctl restart RepeaterWatch
```

To disable login:

```bash
sudo -u meshcoremon /opt/RepeaterWatch/venv/bin/python3 /opt/RepeaterWatch/setup_auth.py --clear
sudo systemctl restart RepeaterWatch
```

## Configuration reference

All configuration is via environment variables in `/opt/RepeaterWatch/.env`. See `.env.example` for the full list with defaults.

| Variable | Default | Description |
|---|---|---|
| `MESHCORE_SERIAL_PORT` | `/dev/ttyV0` | MeshCore radio serial port |
| `MESHCORE_SERIAL_BAUD` | `115200` | Serial baud rate |
| `MESHCORE_POLL_INTERVAL` | `300` | Polling interval in seconds |
| `MESHCORE_DB_PATH` | `meshcore.db` | SQLite database path |
| `MESHCORE_RETENTION_DAYS` | `30` | Days of data to retain |
| `MESHCORE_HOST` | `0.0.0.0` | Flask bind address |
| `MESHCORE_PORT` | `5000` | Flask port |
| `MESHCORE_SECRET_KEY` | — | Flask session secret (required for auth) |
| `MESHCORE_PASSWORD_HASH` | — | bcrypt hash of login password |
| `MESHCORE_FLASH_SERIAL_PORT` | — | Serial port for firmware flashing |
| `MESHCORE_TERMINAL_SERIAL_PORT` | `/dev/ttyV2` | Serial port for terminal |
| `MESHCORE_RADIO_RESET_GPIO` | `4` | GPIO pin for radio reset |
| `MESHCORE_USB_RELAY_GPIO` | `17` | GPIO pin for USB relay |
| `MESHCORE_SENSOR_POLL` | `1` | Enable sensor polling (`0` to disable) |
| `MESHCORE_AS3935_IRQ_GPIO` | `18` | GPIO pin for AS3935 lightning sensor IRQ |
| `MESHCORE_AS3935_AFE_MODE` | `indoor` | AS3935 mode (`indoor` or `outdoor`) |
| `MESHCORE_BQ24074_CHG_GPIO` | `19` | GPIO for BQ24074 charge status |
| `MESHCORE_BQ24074_PGOOD_GPIO` | `13` | GPIO for BQ24074 power good |
| `MESHCORE_BQ24074_CE_GPIO` | `6` | GPIO for BQ24074 charge enable |
