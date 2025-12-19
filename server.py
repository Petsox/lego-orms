from flask import Flask, jsonify, request, send_from_directory
from adafruit_servokit import ServoKit
from bbm_switch_extractor import extract_switches_from_bbm
from bbm_layout_extractor import extract_layout_from_bbm, build_layout_cache
import json, os, wifi, sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LAYOUT_BBM = os.path.join(BASE_DIR, "Layout.bbm")
SWITCH_CONFIG_FILE = os.path.join(BASE_DIR, "switch_config.json")
LAYOUT_CACHE_FILE = os.path.join(BASE_DIR, "layout_cache.json")

kit = ServoKit(channels=16)

try:
    wifi_ok = wifi.ensure_wifi_config()
    if not wifi_ok:
        print("Wi-Fi configuration updated")
except Exception as e:
    print("Wi-Fi setup failed:", e)
    # Optional: stop server if Wi-Fi is critical
    # sys.exit(1)

if not os.path.exists(SWITCH_CONFIG_FILE):
    json.dump({}, open(SWITCH_CONFIG_FILE, "w"))

def load_switch_config():
    if not os.path.exists(SWITCH_CONFIG_FILE):
        with open(SWITCH_CONFIG_FILE, "w") as f:
            json.dump({"switches": {}}, f, indent=2)


    with open(SWITCH_CONFIG_FILE, "r") as f:
        return json.load(f)

def ensure_layout_cache():
    if not os.path.exists(LAYOUT_CACHE_FILE):
        print("Layout cache missing, generating…")
        return build_layout_cache(LAYOUT_BBM, LAYOUT_CACHE_FILE)

    bbm_mtime = os.path.getmtime(LAYOUT_BBM)
    cache_mtime = os.path.getmtime(LAYOUT_CACHE_FILE)

    if bbm_mtime > cache_mtime:
        print("Layout.bbm changed, regenerating layout cache…")
        return build_layout_cache(LAYOUT_BBM, LAYOUT_CACHE_FILE)

    with open(LAYOUT_CACHE_FILE, "r") as f:
        return json.load(f)

def save_switch_config(cfg):
    with open(SWITCH_CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

def find_switch_using_channel(cfg, channel, exclude_sid=None):
    for sid, sw in cfg.get("switches", {}).items():
        if sid == exclude_sid:
            continue
        if sw.get("channel") == channel:
            return sid, sw
    return None, None

def ensure_switches_from_layout():
    cfg = load_switch_config()
    switches = cfg.setdefault("switches", {})

    layout_switches = extract_switches_from_bbm(LAYOUT_BBM)
    layout_ids = {str(sw["id"]) for sw in layout_switches}

    config_ids = set(switches.keys())
    changed = False

    # 🔴 REMOVE switches no longer in layout
    for sid in list(config_ids):
        if sid not in layout_ids:
            print(f"Removing switch {sid} (no longer in Layout.bbm)")
            del switches[sid]
            changed = True

    # 🟢 ADD new switches from layout
    for sw in layout_switches:
        sid = str(sw["id"])
        if sid not in switches:
            switches[sid] = {
                "name": sw["name"],
                "user_name": "",
                "hidden": False,
                "channel": None,
                "angle0": 65,
                "angle1": 105,
                "state": 0
            }
            changed = True

    if changed:
        save_switch_config(cfg)

    return cfg


app = Flask(__name__, static_folder="web", static_url_path="")
ensure_switches_from_layout()
ensure_layout_cache()

@app.route("/")
def root():
    return app.send_static_file("index.html")

@app.route("/api/switch_config")
def api_switch_config():
    with open("switch_config.json", "r") as f:
        return jsonify(json.load(f))
    
@app.route("/res/<path:filename>")
def serve_res(filename):
    return send_from_directory("web/res", filename)
    
@app.route("/api/switches")
def get_switches():
    cfg = load_switch_config()
    return jsonify(cfg["switches"])

@app.route("/api/layout")
def api_layout():
    with open(LAYOUT_CACHE_FILE, "r") as f:
        return jsonify(json.load(f))

@app.route("/api/update_switch_config", methods=["POST"])
def api_update_switch_config():
    data = request.json
    if not data or "id" not in data:
        return jsonify({"error": "Invalid request"}), 400

    sid = str(data["id"])
    cfg = load_switch_config()

    if sid not in cfg.get("switches", {}):
        return jsonify({"error": "Switch not found"}), 400

    sw = cfg["switches"][sid]

    # Extract fields
    hidden = bool(data.get("hidden", sw.get("hidden", False)))
    user_name = (data.get("user_name") or sw.get("user_name") or "").strip()

    channel = data.get("channel", sw.get("channel"))
    angle0 = data.get("angle0", sw.get("angle0", 65))
    angle1 = data.get("angle1", sw.get("angle1", 105))

    # 🔑 HARD RULE: hidden switches must never keep a channel
    if hidden:
        sw["hidden"] = True
        sw["user_name"] = user_name
        sw["channel"] = None

        cfg["switches"][sid] = sw
        save_switch_config(cfg)
        return jsonify({"status": "ok"})

    # 🔴 From here on, switch is NOT hidden → full validation

    if channel is None:
        return jsonify({"error": "Channel is required"}), 400

    channel = int(channel)

    other_sid, other_sw = find_switch_using_channel(
        cfg, channel, exclude_sid=sid
    )

    if other_sw:
        other_name = (
            other_sw.get("user_name")
            or other_sw.get("name")
            or f"Switch {other_sid}"
        )
        return jsonify({
            "error": "Channel already in use",
            "message": f"Channel {channel} is already used by {other_name}"
        }), 400

    sw["hidden"] = False
    sw["user_name"] = user_name
    sw["channel"] = channel
    sw["angle0"] = int(angle0)
    sw["angle1"] = int(angle1)

    cfg["switches"][sid] = sw
    save_switch_config(cfg)

    return jsonify({"status": "ok"})


@app.route("/api/switch/<sid>/toggle")
def api_toggle_switch(sid):
    sid = str(sid)

    # Load config
    with open("switch_config.json", "r") as f:
        cfg = json.load(f)

    if "switches" not in cfg or sid not in cfg["switches"]:
        return jsonify({"error": "Switch not configured"}), 400

    sw = cfg["switches"][sid]

    channel = int(sw["channel"])
    angle0 = int(sw.get("angle0", 65))
    angle1 = int(sw.get("angle1", 105))
    state = int(sw.get("state", 0))

    # Toggle state
    new_state = 1 - state
    angle = angle1 if new_state else angle0

    print(
        f"SERVO MOVE → switch={sid}, channel={channel}, angle={angle}"
    )

    # 🔥 ACTUAL SERVO COMMAND
    kit.servo[channel].angle = angle

    # Save new state
    sw["state"] = new_state
    cfg["switches"][sid] = sw

    with open("switch_config.json", "w") as f:
        json.dump(cfg, f, indent=2)

    return jsonify({
        "id": sid,
        "state": new_state,
        "channel": channel,
        "angle": angle
    })


if __name__ == "__main__":
    print("Server running on :80")
    app.run(host="0.0.0.0", port=80)
