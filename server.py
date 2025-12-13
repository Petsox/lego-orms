from flask import Flask, jsonify, request, send_from_directory
from parts_mapper import build_parts_map
from adafruit_servokit import ServoKit
import json, os, subprocess, time

LAYOUT_BBM = "Layout.bbm"
LAYOUT_JSON = "web/res/layout.json"
EXTRACT_SCRIPT = "extract_layout.py"

def ensure_layout_json():
    if not os.path.exists(LAYOUT_BBM):
        print("⚠️ Layout.bbm not found")
        return

    regenerate = False

    if not os.path.exists(LAYOUT_JSON):
        regenerate = True
    else:
        bbm_time = os.path.getmtime(LAYOUT_BBM)
        json_time = os.path.getmtime(LAYOUT_JSON)
        if bbm_time > json_time:
            regenerate = True

    if regenerate:
        print("🔄 Generating layout.json from Layout.bbm")
        result = subprocess.run(
            ["python3", EXTRACT_SCRIPT],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print("❌ Layout extraction failed:")
            print(result.stderr)
        else:
            print("✅ Layout extracted successfully")

    else:
        print("✅ layout.json is up to date")

ensure_layout_json()

app = Flask(__name__, static_folder="web", static_url_path="")

PARTS = build_parts_map()
kit = ServoKit(channels=16)

CONFIG_FILE = "switch_config.json"
if not os.path.exists(CONFIG_FILE):
    json.dump({}, open(CONFIG_FILE, "w"))

@app.route("/")
def root():
    return app.send_static_file("index.html")

@app.route("/api/parts")
def api_parts():
    return jsonify(PARTS)

@app.route("/api/switch_config")
def api_switch_config():
    with open("switch_config.json", "r") as f:
        return jsonify(json.load(f))
    
@app.route("/res/<path:filename>")
def serve_res(filename):
    return send_from_directory("web/res", filename)
    
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
    ensure_layout_json()
    app.run(host="0.0.0.0", port=80)
