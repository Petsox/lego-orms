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

    # Configure AP mode + security
    run([
        "nmcli", "con", "modify", con_name,
        "802-11-wireless.mode", "ap",
        "802-11-wireless.band", "bg",
        "wifi-sec.key-mgmt", "wpa-psk",
        "wifi-sec.psk", psk,
        "ipv4.method", "shared",
        "ipv6.method", "ignore"
    ])

    # Bring AP up
    run(["nmcli", "con", "up", con_name])

    print("[wifi] AP ready via NetworkManager")


def load_ini():
    p = configparser.ConfigParser()
    p.read(WIFI_INI)
    return p


if __name__ == "__main__":
    ensure_wifi_config()
