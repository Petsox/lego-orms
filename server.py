#!/usr/bin/env python3
import json
import os
import threading
from flask import Flask, request, jsonify, send_from_directory
from adafruit_servokit import ServoKit
from layout_loader import load_layout  # Your BBM loader
from pathlib import Path

# -----------------------------------
# CONFIG
# -----------------------------------

SWITCH_CONFIG_FILE = "switch_config.json"
LAYOUT_FILE = "Layout.bbm"

SERVO_MIN = 58
SERVO_MAX = 100

kit = ServoKit(channels=16)
app = Flask(__name__, static_folder="static")

lock = threading.Lock()

# -----------------------------------
# LOAD / SAVE SWITCH CONFIG
# -----------------------------------

def load_switch_config():
    if not os.path.exists(SWITCH_CONFIG_FILE):
        return {}

    with open(SWITCH_CONFIG_FILE, "r") as f:
        return json.load(f)

def save_switch_config(data):
    with open(SWITCH_CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

switch_config = load_switch_config()

# -----------------------------------------------------------------
# LAYOUT HANDLING
# -----------------------------------------------------------------

layout = load_layout(LAYOUT_FILE)

# Extract switches from loaded layout
def get_switches():
    return [item for item in layout["items"] if item["type"] == "switch"]

# -----------------------------------
# SERVO CONTROL
# -----------------------------------

def move_servo(servo_id, angle):
    if servo_id < 0 or servo_id > 15:
        print(f"ERROR: servo_id {servo_id} out of range")
        return False
    try:
        kit.servo[servo_id].angle = angle
        return True
    except Exception as e:
        print(f"Servo movement error: {e}")
        return False

# Auto-detect left/right position by sampling angle extremes
def auto_calibrate_switch(switch_id):
    global switch_config

    print(f"Auto-calibrating switch {switch_id}")

    servo_id = switch_config.get(switch_id, {}).get("servo_id", None)
    if servo_id is None:
        return {"error": "servo_id not assigned"}

    # Try moving to both extremes
    move_servo(servo_id, SERVO_MIN)
    move_servo(servo_id, SERVO_MAX)

    # Default mapping
    config = {
        "servo_id": servo_id,
        "angle_straight": SERVO_MIN,
        "angle_turnout": SERVO_MAX
    }

    switch_config[switch_id] = config
    save_switch_config(switch_config)

    return config

# -----------------------------------
# API ROUTES
# -----------------------------------

@app.route("/api/layout")
def api_layout():
    """ Returns full track layout including switch positions """
    return jsonify({
        "layout": layout,
        "switch_config": switch_config
    })

@app.route("/api/switch/<switch_id>/toggle")
def api_switch_toggle(switch_id):
    """Toggle a switch between its two states"""

    if switch_id not in switch_config:
        return jsonify({"error": "switch not calibrated"}), 400

    cfg = switch_config[switch_id]
    current = cfg.get("last_state", "straight")

    if current == "straight":
        angle = cfg["angle_turnout"]
        new_state = "turnout"
    else:
        angle = cfg["angle_straight"]
        new_state = "straight"

    move_servo(cfg["servo_id"], angle)
    cfg["last_state"] = new_state
    save_switch_config(switch_config)

    return jsonify({"switch_id": switch_id, "state": new_state})

@app.route("/api/switch/<switch_id>/set_angle", methods=["POST"])
def api_switch_set_angle(switch_id):
    """Direct angle control for calibration UI"""
    data = request.get_json()
    angle = data.get("angle")

    servo_id = data.get("servo_id", None)

    if servo_id is not None:
        # Update mapping
        switch_config.setdefault(switch_id, {})
        switch_config[switch_id]["servo_id"] = servo_id
        save_switch_config(switch_config)

    cfg = switch_config.get(switch_id)
    if cfg is None:
        return jsonify({"error": "switch not configured"}), 400

    move_servo(cfg["servo_id"], angle)
    return jsonify({"ok": True})

@app.route("/api/switch/<switch_id>/auto_calibrate")
def api_switch_auto_calibrate(switch_id):
    """Runs auto-detection and stores angles"""
    result = auto_calibrate_switch(switch_id)
    return jsonify(result)

@app.route("/web/")
def index():
    return send_from_directory("static", "index.html")

# -----------------------------------
# LAUNCH
# -----------------------------------

if __name__ == "__main__":
    print("Starting server on http://0.0.0.0:80")
    app.run(host="0.0.0.0", port=80, debug=False)
