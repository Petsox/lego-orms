import configparser
import os
import subprocess
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WIFI_INI = os.path.join(BASE_DIR, "wifi.ini")

HOSTAPD_CONF = "/etc/hostapd/hostapd.conf"
DNSMASQ_CONF = "/etc/dnsmasq.d/lego-orms.conf"


def run(cmd):
    subprocess.run(cmd, check=False)


def ensure_wifi_config():
    cfg = load_ini()
    mode = cfg["wifi"]["mode"].strip().lower()

    print(f"[wifi] Mode: {mode}")

    if mode == "ap":
        setup_ap(cfg)
    else:
        print("[wifi] Client mode not implemented here")


def setup_ap(cfg):
    print("[wifi] Setting up AP + DHCP")

    # RELEASE wlan0 COMPLETELY
    run(["systemctl", "stop", "NetworkManager"])
    run(["systemctl", "stop", "wpa_supplicant"])
    run(["systemctl", "stop", "wpa_supplicant@wlan0"])
    run(["systemctl", "stop", "dhcpcd"])

    run(["ip", "link", "set", "wlan0", "down"])
    run(["ip", "link", "set", "wlan0", "up"])

    write_hostapd(cfg)
    write_dnsmasq(cfg)
    setup_ip_and_nat(cfg)

    run(["systemctl", "unmask", "hostapd"])
    run(["systemctl", "enable", "hostapd"])
    run(["systemctl", "enable", "dnsmasq"])

    run(["systemctl", "restart", "dnsmasq"])
    run(["systemctl", "restart", "hostapd"])

    print("[wifi] AP ready")


def write_hostapd(cfg):
    ap = cfg["ap"]
    wifi = cfg["wifi"]

    content = f"""
interface={wifi['interface']}
driver=nl80211
ssid={ap['ssid']}
hw_mode=g
channel={ap['channel']}
country_code={wifi['country']}
ieee80211n=1
wmm_enabled=1
wpa=2
wpa_passphrase={ap['psk']}
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
""".strip()

    with open(HOSTAPD_CONF, "w") as f:
        f.write(content + "\n")


def write_dnsmasq(cfg):
    ap = cfg["ap"]
    wifi = cfg["wifi"]

    content = f"""
interface={wifi['interface']}
dhcp-range={ap['dhcp_start']},{ap['dhcp_end']},{ap['lease_time']}
""".strip()

    with open(DNSMASQ_CONF, "w") as f:
        f.write(content + "\n")


def setup_ip_and_nat(cfg):
    ap = cfg["ap"]
    iface = cfg["wifi"]["interface"]

    run(["ip", "addr", "flush", "dev", iface])
    run(["ip", "addr", "add", f"{ap['ip']}/24", "dev", iface])
    run(["ip", "link", "set", iface, "up"])

    # Enable forwarding
    with open("/proc/sys/net/ipv4/ip_forward", "w") as f:
        f.write("1")

    # NAT
    run([
        "iptables", "-t", "nat", "-A", "POSTROUTING",
        "-o", "eth0", "-j", "MASQUERADE"
    ])


def load_ini():
    p = configparser.ConfigParser()
    p.read(WIFI_INI)
    return p


if __name__ == "__main__":
    ensure_wifi_config()
