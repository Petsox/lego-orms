import configparser
import subprocess
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WIFI_INI = os.path.join(BASE_DIR, "wifi.ini")


def run(cmd):
    print("[wifi]", " ".join(cmd))
    subprocess.run(cmd, check=False)


def ensure_wifi_config():
    cfg = load_ini()
    mode = cfg["wifi"]["mode"].strip().lower()

    print(f"[wifi] Mode: {mode}")

    if mode == "ap":
        setup_ap_nm(cfg)
    else:
        print("[wifi] Client mode not implemented")


# -------------------------------
# NetworkManager AP implementation
# -------------------------------

def setup_ap_nm(cfg):
    wifi = cfg["wifi"]
    ap = cfg["ap"]

    iface = wifi.get("interface", "wlan0")
    ssid = ap["ssid"]
    psk = ap["psk"]
    band = ap.get("band", "bg")
    channel = ap.get("channel", "6")

    con_name = "lego-orms-ap"

    # Ensure NetworkManager is running
    run(["systemctl", "enable", "--now", "NetworkManager"])

    # Remove existing AP connection if present
    run(["nmcli", "con", "delete", con_name])

    # Create AP connection
    run([
        "nmcli", "con", "add",
        "type", "wifi",
        "ifname", iface,
        "con-name", con_name,
        "autoconnect", "yes",
        "ssid", ssid
    ])

    # Configure AP mode, WPA2-only, and custom IP/DHCP range
    run([
        "nmcli", "con", "modify", con_name,
        "802-11-wireless.mode", "ap",
        "802-11-wireless.band", band,
        "802-11-wireless.channel", channel,

        # 🔒 WPA2 only (no WPA3 / no WPS)
        "wifi-sec.key-mgmt", "wpa-psk",
        "wifi-sec.proto", "rsn",
        "wifi-sec.pairwise", "ccmp",
        "wifi-sec.group", "ccmp",
        "wifi-sec.psk", psk,
        "802-11-wireless-security.pmf", "disable",

        # 🌐 AP IP + DHCP
        "ipv4.method", "shared",
        "ipv4.addresses", "10.0.0.1/24",
        "ipv4.shared-dhcp-range", "10.0.0.10,10.0.0.50",
        "ipv4.never-default", "yes",
        "ipv6.method", "ignore"
    ])

    # Bring AP up
    run(["nmcli", "con", "up", con_name])

    print("[wifi] AP ready (10.0.0.1 / DHCP 10.0.0.10–10.0.0.50)")



def load_ini():
    p = configparser.ConfigParser()
    p.read(WIFI_INI)
    return p


if __name__ == "__main__":
    ensure_wifi_config()
