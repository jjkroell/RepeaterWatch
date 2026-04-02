#!/usr/bin/env python3
"""
Run on the Pi as:
  sudo python3 /opt/RepeaterWatch/patch_sensors.py

Adds two new API routes to routes.py:
  GET  /api/v1/sensors/config  — read enabled sensors from .env
  POST /api/v1/sensors/config  — save sensor toggles to .env
"""
import ast, os, shutil, sys

ROUTES   = "/opt/RepeaterWatch/api/routes.py"
ENV_PATH = "/opt/RepeaterWatch/.env"

def backup(p):
    shutil.copy(p, p + ".bak")
    print(f"  Backed up {p} -> {p}.bak")

def check_syntax(p):
    try:
        ast.parse(open(p).read())
        return True
    except SyntaxError as e:
        print(f"  Syntax error in {p}: {e}")
        return False

NEW_ROUTES = '''

@api.route("/sensors/config", methods=["GET"])
def sensors_config_get():
    """Return enabled/disabled state of each sensor from .env"""
    import os as _os
    env_path = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), ".env")
    keys = {
        "ina3221":  "MESHCORE_SENSOR_INA3221",
        "bme280":   "MESHCORE_SENSOR_BME280",
        "lis2dw12": "MESHCORE_SENSOR_LIS2DW12",
        "as3935":   "MESHCORE_SENSOR_AS3935",
        "bq24074":  "MESHCORE_SENSOR_BQ24074",
    }
    env_vals = {}
    if _os.path.exists(env_path):
        for line in open(env_path):
            s = line.strip()
            if "=" in s and not s.startswith("#"):
                k, _, v = s.partition("=")
                env_vals[k.strip()] = v.strip()
    cfg = {}
    for name, key in keys.items():
        cfg[name] = env_vals.get(key, _os.environ.get(key, "0")) == "1"
    poll = env_vals.get("MESHCORE_SENSOR_POLL",
                        _os.environ.get("MESHCORE_SENSOR_POLL", "0")) == "1"
    return jsonify({"sensors": cfg, "polling_enabled": poll})


@api.route("/sensors/config", methods=["POST"])
def sensors_config_post():
    """Write sensor toggles to .env, auto-update MESHCORE_SENSOR_POLL"""
    import os as _os
    env_path = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), ".env")
    keys = {
        "ina3221":  "MESHCORE_SENSOR_INA3221",
        "bme280":   "MESHCORE_SENSOR_BME280",
        "lis2dw12": "MESHCORE_SENSOR_LIS2DW12",
        "as3935":   "MESHCORE_SENSOR_AS3935",
        "bq24074":  "MESHCORE_SENSOR_BQ24074",
    }
    if not _os.path.exists(env_path):
        return jsonify({"error": ".env not found"}), 500
    data = request.get_json(force=True, silent=True) or {}
    sensors = data.get("sensors", {})
    for name in sensors:
        if name not in keys:
            return jsonify({"error": f"Unknown sensor: {name}"}), 400
    lines = open(env_path).readlines()

    def upsert(lines, key, value):
        found = False
        out = []
        for l in lines:
            if l.startswith(key + "="):
                out.append(f"{key}={value}\\n")
                found = True
            else:
                out.append(l)
        if not found:
            out.append(f"{key}={value}\\n")
        return out

    for name, key in keys.items():
        if name in sensors:
            lines = upsert(lines, key, "1" if sensors[name] else "0")

    env_vals = {}
    for l in lines:
        s = l.strip()
        if "=" in s and not s.startswith("#"):
            k, _, v = s.partition("=")
            env_vals[k.strip()] = v.strip()
    any_enabled = any(env_vals.get(v, "0") == "1" for v in keys.values())
    lines = upsert(lines, "MESHCORE_SENSOR_POLL", "1" if any_enabled else "0")
    open(env_path, "w").writelines(lines)
    return jsonify({"ok": True, "polling_enabled": any_enabled, "restart_required": True})

'''

print("[1/2] Patching api/routes.py ...")
src = open(ROUTES).read()
if "/sensors/config" in src:
    print("  /sensors/config already present — skipping")
else:
    backup(ROUTES)
    anchor = '@api.route("/sensors/status")'
    if anchor not in src:
        print(f"  ERROR: anchor not found: {anchor}")
        sys.exit(1)
    src = src.replace(anchor, NEW_ROUTES + "\n" + anchor, 1)
    open(ROUTES, "w").write(src)
    if check_syntax(ROUTES):
        print("  routes.py patched OK")
    else:
        shutil.copy(ROUTES + ".bak", ROUTES)
        print("  FAILED — rolled back")
        sys.exit(1)

print("[2/2] Verifying .env sensor keys ...")
all_keys = ["MESHCORE_SENSOR_INA3221","MESHCORE_SENSOR_BME280",
            "MESHCORE_SENSOR_LIS2DW12","MESHCORE_SENSOR_AS3935",
            "MESHCORE_SENSOR_BQ24074","MESHCORE_SENSOR_POLL"]
lines = open(ENV_PATH).readlines()
env_vals = {l.split("=",1)[0].strip(): True
            for l in lines if "=" in l and not l.startswith("#")}
changed = False
for key in all_keys:
    if key not in env_vals:
        lines.append(f"{key}=0\n")
        print(f"  Added: {key}=0")
        changed = True
if changed:
    open(ENV_PATH, "w").writelines(lines)
else:
    print("  .env already complete")

print("\nDone. Run: sudo systemctl restart RepeaterWatch")
