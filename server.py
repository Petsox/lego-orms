from flask import Flask, jsonify, request, send_from_directory
from adafruit_servokit import ServoKit
from bbm_switch_extractor import extract_switches_from_bbm
import json, os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LAYOUT_BBM = os.path.join(BASE_DIR, "Layout.bbm")
SWITCH_CONFIG_FILE = os.path.join(BASE_DIR, "switch_config.json")

kit = ServoKit(channels=16)

if not os.path.exists(SWITCH_CONFIG_FILE):
    json.dump({}, open(SWITCH_CONFIG_FILE, "w"))

def load_switch_config():
    if not os.path.exists(SWITCH_CONFIG_FILE):
        with open(SWITCH_CONFIG_FILE, "w") as f:
            json.dump({"switches": {}}, f, indent=2)


    with open(SWITCH_CONFIG_FILE, "r") as f:
        return json.load(f)


def save_switch_config(cfg):
    with open(SWITCH_CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


def ensure_switches_from_layout():
    cfg = load_switch_config()
    switches = cfg.setdefault("switches", {})

    layout_switches = extract_switches_from_bbm(LAYOUT_BBM)
    changed = False

    for sw in layout_switches:
        sid = str(sw["id"])

        if sid not in switches:
            switches[sid] = {
                "name": sw["name"],
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

print("Switch config after merge:")
print(json.dumps(load_switch_config(), indent=2))

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

@app.route("/api/update_switch_config", methods=["POST"])
def api_update_switch_config():
    data = request.json
    if not data or "id" not in data:
        return jsonify({"error": "Invalid request"}), 400

    sid = str(data["id"])
    channel = int(data.get("channel", 0))
    angle0 = int(data.get("angle0", 58))
    angle1 = int(data.get("angle1", 100))

    # Load config
    with open("switch_config.json", "r") as f:
        cfg = json.load(f)

    # Normalize structure
    if "switches" not in cfg or isinstance(cfg["switches"], list):
        cfg["switches"] = {}

    cfg["switches"][sid] = {
        "channel": channel,
        "angle0": angle0,
        "angle1": angle1
    }

    # Save
    with open("switch_config.json", "w") as f:
        json.dump(cfg, f, indent=2)

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
