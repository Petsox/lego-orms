import configparser
import os
import subprocess
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WIFI_INI = os.path.join(BASE_DIR, "wifi.ini")

WPA_CONF = "/etc/wpa_supplicant/wpa_supplicant.conf"
DNSMASQ_CONF = "/etc/dnsmasq.d/lego-orms.conf"
HOSTAPD_CONF = "/etc/hostapd/lego-orms.conf"


def ensure_wifi_config():
    cfg = load_wifi_ini()
    mode = cfg["wifi"]["mode"]

    print(f"[wifi] Mode: {mode}")

    if mode == "client":
        ensure_client_wifi(cfg)
    elif mode == "ap":
        ensure_ap_wifi(cfg)
    else:
        raise RuntimeError("Invalid wifi mode in wifi.ini")

    return True


# -------------------------------------------------------
# CLIENT MODE
# -------------------------------------------------------

def ensure_client_wifi(cfg):
    print("[wifi] Ensuring client Wi-Fi")
    stop_ap_services()

    desired = build_wpa_block(cfg["wifi"])

    current = ""
    if os.path.exists(WPA_CONF):
        with open(WPA_CONF) as f:
            current = f.read()

    if desired in current:
        print("[wifi] Client Wi-Fi OK")
        return

    backup(WPA_CONF)
    with open(WPA_CONF, "w") as f:
        f.write(desired + "\n")

    subprocess.run(["wpa_cli", "-i", cfg["wifi"]["interface"], "reconfigure"], check=False)
    print("[wifi] Client Wi-Fi updated")


# -------------------------------------------------------
# AP + DHCP MODE
# -------------------------------------------------------

def ensure_ap_wifi(cfg):
    print("[wifi] Ensuring AP + DHCP")

    stop_client_wifi()

    write_hostapd(cfg)
    write_dnsmasq(cfg)
    configure_static_ip(cfg)

    subprocess.run(["systemctl", "enable", "hostapd"], check=False)
    subprocess.run(["systemctl", "enable", "dnsmasq"], check=False)
    subprocess.run(["systemctl", "restart", "dnsmasq"], check=False)
    subprocess.run(["systemctl", "restart", "hostapd"], check=False)

    print("[wifi] AP + DHCP active")


# -------------------------------------------------------
# FILE GENERATORS
# -------------------------------------------------------

def write_hostapd(cfg):
    ap = cfg["ap"]
    content = f"""
interface={cfg['wifi']['interface']}
ssid={ap['ssid']}
wpa_passphrase={ap['psk']}
channel={ap['channel']}
country_code={cfg['wifi']['country']}
hw_mode=g
wpa=2
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
""".strip()

    backup(HOSTAPD_CONF)
    with open(HOSTAPD_CONF, "w") as f:
        f.write(content)

    subprocess.run(
        ["sed", "-i", f"s|#DAEMON_CONF=.*|DAEMON_CONF={HOSTAPD_CONF}|", "/etc/default/hostapd"],
        check=False,
    )


def write_dnsmasq(cfg):
    ap = cfg["ap"]
    content = f"""
interface={cfg['wifi']['interface']}
dhcp-range={ap['dhcp_start']},{ap['dhcp_end']},{ap['lease_time']}
""".strip()

    backup(DNSMASQ_CONF)
    with open(DNSMASQ_CONF, "w") as f:
        f.write(content)


def configure_static_ip(cfg):
    ap = cfg["ap"]
    iface = cfg["wifi"]["interface"]

    subprocess.run(
        ["ip", "addr", "flush", "dev", iface],
        check=False
    )

    subprocess.run(
        ["ip", "addr", "add", f"{ap['ip']}/24", "dev", iface],
        check=False
    )

    subprocess.run(
        ["ip", "link", "set", iface, "up"],
        check=False
    )


# -------------------------------------------------------
# HELPERS
# -------------------------------------------------------

def stop_ap_services():
    subprocess.run(["systemctl", "stop", "hostapd"], check=False)
    subprocess.run(["systemctl", "stop", "dnsmasq"], check=False)


def stop_client_wifi():
    subprocess.run(["systemctl", "stop", "wpa_supplicant"], check=False)


def backup(path):
    if os.path.exists(path):
        shutil.copy(path, path + ".bak")


def load_wifi_ini():
    parser = configparser.ConfigParser()
    parser.read(WIFI_INI)

    if "wifi" not in parser:
        raise RuntimeError("wifi.ini missing [wifi] section")

    return parser


def build_wpa_block(wifi):
    return f"""
country={wifi['country']}
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={{
    ssid="{wifi['ssid']}"
    psk="{wifi['psk']}"
}}
""".strip()


if __name__ == "__main__":
    ensure_wifi_config()
