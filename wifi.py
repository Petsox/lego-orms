#!/usr/bin/env python3
import os
import subprocess
import json
from pathlib import Path

HOTSPOT_CONFIG = "hotspot.json"

DEFAULT_HOTSPOT_SETTINGS = {
    "ssid": "TrainController",
    "password": "Train1234",
    "interface": "wlan0",
    "channel": 6,
    "country": "US",
    "enabled": True
}

HOSTAPD_CONF = "/etc/hostapd/hostapd.conf"
DNSMASQ_CONF = "/etc/dnsmasq.d/hotspot.conf"
DHCPCD_CONF = "/etc/dhcpcd.conf"


# ---------------------------------------------------------
# CONFIG LOADING
# ---------------------------------------------------------

def load_hotspot_config():
    if not os.path.exists(HOTSPOT_CONFIG):
        with open(HOTSPOT_CONFIG, "w") as f:
            json.dump(DEFAULT_HOTSPOT_SETTINGS, f, indent=4)
        return DEFAULT_HOTSPOT_SETTINGS

    with open(HOTSPOT_CONFIG, "r") as f:
        return json.load(f)


# ---------------------------------------------------------
# SYSTEM COMMAND RUNNER
# ---------------------------------------------------------

def run(cmd):
    """Run a system command and return output."""
    print("RUN:", cmd)
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode()
    except subprocess.CalledProcessError as e:
        print("ERROR:", e.output.decode())
        return None


# ---------------------------------------------------------
# CHECK IF HOTSPOT SHOULD RUN
# ---------------------------------------------------------

def hotspot_should_run(config):
    """
    If enabled=true in config file → run hotspot.
    Later you may add: run hotspot only if home Wi-Fi is not available.
    """
    return config.get("enabled", True)


# ---------------------------------------------------------
# WRITE CONFIG FILES
# ---------------------------------------------------------

def write_hostapd_conf(cfg):
    text = f"""
interface={cfg['interface']}
driver=nl80211
ssid={cfg['ssid']}
hw_mode=g
channel={cfg['channel']}
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase={cfg['password']}
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
country_code={cfg['country']}
"""
    print("Writing:", HOSTAPD_CONF)
    with open(HOSTAPD_CONF, "w") as f:
        f.write(text)


def write_dnsmasq_conf(cfg):
    text = f"""
interface={cfg['interface']}
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
dhcp-option=3,192.168.4.1
dhcp-option=6,192.168.4.1
address=/#/192.168.4.1
    """
    print("Writing:", DNSMASQ_CONF)
    with open(DNSMASQ_CONF, "w") as f:
        f.write(text)


def patch_dhcpcd_conf(cfg):
    """
    Adds static IP settings for the hotspot interface if not present.
    """
    if not os.path.exists(DHCPCD_CONF):
        return

    with open(DHCPCD_CONF, "r") as f:
        lines = f.read()

    block = f"""
interface {cfg['interface']}
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant
"""

    if block not in lines:
        print("Patching:", DHCPCD_CONF)
        with open(DHCPCD_CONF, "a") as f:
            f.write(block)
    else:
        print("DHCPCD already configured.")


# ---------------------------------------------------------
# HOTSPOT CONTROL
# ---------------------------------------------------------

def start_hotspot():
    print("Starting hotspot...")
    run("sudo systemctl unmask hostapd")
    run("sudo systemctl enable hostapd")
    run("sudo systemctl restart hostapd")
    run("sudo systemctl restart dnsmasq")


def stop_hotspot():
    print("Stopping hotspot...")
    run("sudo systemctl stop hostapd")
    run("sudo systemctl stop dnsmasq")
    run("sudo systemctl disable hostapd")


# ---------------------------------------------------------
# MAIN STARTUP LOGIC
# ---------------------------------------------------------

def main():
    cfg = load_hotspot_config()
    print("Loaded config:", cfg)

    if not hotspot_should_run(cfg):
        print("Hotspot disabled in config.")
        stop_hotspot()
        return

    print("Configuring hotspot...")

    write_hostapd_conf(cfg)
    write_dnsmasq_conf(cfg)
    patch_dhcpcd_conf(cfg)

    print("Reloading services...")
    run("sudo systemctl restart dhcpcd")

    start_hotspot()
    print("Hotspot is active!")


if __name__ == "__main__":
    main()
