import xml.etree.ElementTree as ET
import re

SWITCH_PART_IDS = {"2861", "2859", "7996"}
KEYWORDS = ("SWITCH", "TURNOUT", "POINT", "SLIP")


def is_switch_part(part_number: str) -> bool:
    if not part_number:
        return False

    name = part_number.upper()

    # Keyword-based (future-proof)
    if any(k in name for k in KEYWORDS):
        return True

    # Numeric part detection (BlueBrick reality)
    m = re.search(r"\b(\d{4})\b", name)
    return bool(m and m.group(1) in SWITCH_PART_IDS)


def extract_switches_from_bbm(path: str):
    tree = ET.parse(path)
    root = tree.getroot()

    switches = []

    # 🔑 Namespace-safe Brick search
    for brick in root.findall(".//{*}Brick"):
        brick_id = brick.get("id")

        part_number_el = brick.find("{*}PartNumber")
        if brick_id is None or part_number_el is None:
            continue

        part_number = part_number_el.text or ""

        if is_switch_part(part_number):
            switches.append({
                "id": int(brick_id),
                "name": part_number.strip()
            })

    return switches
