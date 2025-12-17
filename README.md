# LEGO-ORMS — Train Switch Control System

LEGO-ORMS is a **web-based control system for LEGO train switches**, designed to work with **BlueBrick layouts**, a **Raspberry Pi**, and **TrixBrix servo motors**.

The system automatically discovers switches from a `Layout.bbm` file, lets you **assign servos and angles**, **rename switches**, **hide unused ones**, and control everything from a **responsive web UI** that works on desktop, tablets, and phones.

This project is designed to be:
- reliable
- simple to operate
- safe for hardware
- easy to extend

---

## ✨ Features

- 🔍 **Automatic switch discovery** from `Layout.bbm` (BlueBrick)
- 💾 **Persistent configuration** via `switch_config.json`
- 🎛 **Web-based control panel**
- 🧭 **Servo calibration UI** (angles + channel)
- 🏷 **User-defined switch names**
- 👁 **Hide / unhide switches** without deleting them
- ⚠️ Safety checks:
  - prevents duplicate servo channels
  - prevents toggling unconfigured switches
- 📱 **Responsive UI** (desktop, tablet, phone)
- 🔌 Direct control via **Adafruit ServoKit**

---

## 📦 Requirements

### Hardware

- Raspberry Pi (tested on Pi 4)
- PCA9685 servo driver (tested with Waveshare Servo Driver HAT Raspberry Pi, 16 channels, 12 bit, I2C)
- TrixBrix servo motors
- LEGO train switches or TrixBrix switches
- LAN connection (Wi-Fi or Ethernet) to the Raspberry Pi

### Software

- Python **3.8+**
- BlueBrick (to create `Layout.bbm`)
- Modern web browser

## 🐍 Python Dependencies

Install with:

```bash
pip install flask adafruit-circuitpython-servokit
```

---

# 🚀 Getting Started
## 1️⃣ Prepare the layout

- Create or edit your layout in BlueBrick

- Save it as Layout.bbm

- Place it in the project root directory

- Switches are detected automatically based on BlueBrick part numbers. If IDs are missing find them in the BlueBrick app and add them to **SWITCH_PART_IDS** or **KEYWORDS** in `bbm_switch_extractor`

## 2️⃣ Start the server

```bash
sudo python3 server.py
```

### On startup:

- Layout.bbm is parsed

- All switches are added to switch_config.json (if missing)

- Existing calibration is preserved

- Server runs on port 80 by default.

## 3️⃣ Open the Web UI

From any device on the same network:

```url
http://<raspberry-pi-ip>/
```

# 🎛 Using the Interface

## Main screen

- Each visible switch appears as a button

- Click → toggle the switch

- Shift + click → open calibration

## Calibration panel

- Assign servo channel (0–15)

- Set angle for both directions

- Give the switch a friendly name

- Hide the switch if not needed

## Hidden switches

- Access via “Hidden switches” button

- Unhide switches at any time

- Hidden switches remain fully configurable

# 📡 Wi-Fi Configuration (AP + DHCP)

LEGO-ORMS can run as a self-contained Wi-Fi access point with DHCP, allowing phones, tablets, or laptops to connect directly to the Raspberry Pi without an existing network.

This is fully automated at server startup.

## 🧾 wifi.ini

Wi-Fi behavior is configured declaratively via `wifi.ini` in the project root.

```ini
[wifi]
mode = ap
country = CZ
interface = wlan0

[ap]
ssid = LEGO-ORMS
psk = changeThisNow
channel = 6

ip = 10.0.0.1
netmask = 255.255.255.0
dhcp_start = 10.0.0.10
dhcp_end = 10.0.0.100
lease_time = 12h
```

**Fields**

- `mode`

- - `ap` → Raspberry Pi acts as Wi-Fi access point (DHCP server)

- `ssid` / `psk`

- - Network name and password

- `ip`

- - IP address of the Pi in AP mode

- `dhcp_start` / `dhcp_end`

- - Address range handed out to clients

## 📦 Required system packages

Run once:

```bash
sudo apt update
sudo apt install -y hostapd dnsmasq
```

Unmask services (required on Raspberry Pi OS):

```bash
sudo systemctl unmask hostapd dnsmasq
```

# 🚀 Automatic Startup (systemd)

LEGO-ORMS is designed to run automatically at boot using systemd.

## 📁 systemd service file

edit `lego-orms.service` in main directory and copy it to `/etc/systemd/system/` like so:

```bash
sudo cp lego-orms.service /etc/systemd/system/
```

**⚠️ Important**

- The service must run as root to manage Wi-Fi, networking, GPIO, and I²C

- Do not specify a User= directive

# 🙌 Acknowledgements

[Alban Nanty](https://bluebrick.lswproject.com/) (BlueBrick layout creation studio)

[Adafruit](https://www.adafruit.com/) (ServoKit & PCA9685)

[TrixBrix](https://trixbrix.eu/) (for custom injection molded and 3D Printed tracks)

[LEGO](https://www.lego.com/) (for the trains, obviously)