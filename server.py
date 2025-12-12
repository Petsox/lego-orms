from flask import Flask, jsonify, request
from layout_loader import load_layout
from parts_mapper import build_parts_map
import json, os

app = Flask(__name__, static_folder="web", static_url_path="")

LAYOUT = load_layout("Layout.bbm")
PARTS = build_parts_map()

CONFIG_FILE = "switch_config.json"
if not os.path.exists(CONFIG_FILE):
    json.dump({}, open(CONFIG_FILE, "w"))

@app.route("/")
def root():
    return app.send_static_file("index.html")

@app.route("/api/layout")
def api_layout():
    return jsonify(LAYOUT)

@app.route("/api/parts")
def api_parts():
    return jsonify(PARTS)

@app.route("/api/switch_config")
def api_switch_config():
    with open("switch_config.json", "r") as f:
        return jsonify(json.load(f))

@app.route("/api/update_switch_config", methods=["POST"])
def api_update_switch_config():
    data = request.json
    if not data or "id" not in data:
        return jsonify({"error": "Invalid request"}), 400

    sid = str(data["id"])
    channel = int(data.get("channel", 0))
    angle0 = int(data.get("angle0", 58))
    angle1 = int(data.get("angle1", 100))

    # Load existing config
    with open("switch_config.json", "r") as f:
        cfg = json.load(f)

    if "switches" not in cfg:
        cfg["switches"] = {}

    # Update / create entry
    cfg["switches"][sid] = {
        "channel": channel,
        "angle0": angle0,
        "angle1": angle1
    }

    # Save back to disk
    with open("switch_config.json", "w") as f:
        json.dump(cfg, f, indent=2)

    return jsonify({"status": "ok"})

@app.route("/api/switch/<sid>/toggle")
def toggle_switch(sid):
    cfg = json.load(open(CONFIG_FILE))
    cfg[sid] = 1 - cfg.get(sid, 0)
    json.dump(cfg, open(CONFIG_FILE, "w"), indent=2)
    return {"id": sid, "state": cfg[sid]}

if __name__ == "__main__":
    print("Server running on :80")
    app.run(host="0.0.0.0", port=80)
