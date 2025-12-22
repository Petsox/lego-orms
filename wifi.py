import configparser
import subprocess
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WIFI_INI = os.path.join(BASE_DIR, "wifi.ini")

HOSTAPD_CONF = "/etc/hostapd/hostapd.conf"
DNSMASQ_CONF = "/etc/dnsmasq.d/lego-orms.conf"


def run(cmd):
    print("[wifi]", " ".join(cmd))
    subprocess.run(cmd, check=False)


def ensure_wifi_config():
    cfg = load_ini()
    mode = cfg["wifi"]["mode"].strip().lower()

    print(f"[wifi] Mode: {mode}")

    if mode == "ap":
        setup_ap(cfg)
    else:
        print("[wifi] Client mode not implemented")


# --------------------------------------------------
# AP MODE (hostapd + dnsmasq)
# --------------------------------------------------

def setup_ap(cfg):
    wifi = cfg["wifi"]
    ap = cfg["ap"]

    iface = wifi.get("interface", "wlan0")

    # 🔥 RELEASE wlan0 FROM ALL CLIENT MANAGERS
    run(["systemctl", "stop", "NetworkManager"])
    run(["systemctl", "stop", "wpa_supplicant"])
    run(["systemctl", "stop", "wpa_supplicant@wlan0"])
    run(["systemctl", "stop", "dhcpcd"])

    run(["ip", "link", "set", iface, "down"])
    run(["ip", "link", "set", iface, "up"])

    write_hostapd_conf(wifi, ap, iface)
    write_dnsmasq_conf(wifi, ap, iface)
    configure_ip(ap, iface)

    # 📡 ENABLE SERVICES
    run(["systemctl", "unmask", "hostapd"])
    run(["systemctl", "enable", "hostapd"])
    run(["systemctl", "enable", "dnsmasq"])

    run(["systemctl", "restart", "dnsmasq"])
    run(["systemctl", "restart", "hostapd"])

    print("[wifi] AP READY (hostapd + dnsmasq)")
    
    # SET STATIC IP FOR BUILD-IN NIC

    run(["ip", "addr", "add", "192.168.1.185/24", "dev", "eth0"])
    run(["ip", "route", "replace", "default", "via", "192.168.1.1"])


# --------------------------------------------------
# FILE GENERATION
# --------------------------------------------------

def write_hostapd_conf(wifi, ap, iface):
    content = f"""
interface={iface}
driver=nl80211

ssid={ap['ssid']}
hw_mode=g
channel={ap['channel']}
country_code={wifi['country']}

ieee80211n=1
wmm_enabled=1

# WPA2 ONLY — NO WPA3 / NO WPS
wpa=2
wpa_passphrase={ap['psk']}
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
ieee80211w=0
wps_state=0
""".strip()

    with open(HOSTAPD_CONF, "w") as f:
        f.write(content + "\n")

    print(f"[wifi] Wrote {HOSTAPD_CONF}")


def write_dnsmasq_conf(wifi, ap, iface):
    content = f"""
interface={iface}
bind-interfaces
dhcp-range={ap['dhcp_start']},{ap['dhcp_end']},{ap['lease_time']}
""".strip()

    with open(DNSMASQ_CONF, "w") as f:
        f.write(content + "\n")

    print(f"[wifi] Wrote {DNSMASQ_CONF}")


def configure_ip(ap, iface):
    run(["ip", "addr", "flush", "dev", iface])
    run(["ip", "addr", "add", f"{ap['ip']}/24", "dev", iface])
    run(["ip", "link", "set", iface, "up"])


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def load_ini():
    p = configparser.ConfigParser()
    p.read(WIFI_INI)
    return p


if __name__ == "__main__":
    ensure_wifi_config()
