import xml.etree.ElementTree as ET
import re

SWITCH_PART_IDS = {"2861", "2859", "7996"}
KEYWORDS = ("SWITCH", "TURNOUT", "POINT", "SLIP")


def is_switch_part(partname: str) -> bool:
    if not partname:
        return False

    name = partname.upper()

    if any(k in name for k in KEYWORDS):
        return True

    m = re.search(r"\b(\d{4})\b", name)
    return bool(m and m.group(1) in SWITCH_PART_IDS)


def extract_switches_from_bbm(path: str):
    tree = ET.parse(path)
    root = tree.getroot()

    switches = []

    for part in root.iter("Part"):
        part_id = part.get("id")
        partname = part.get("partname")

        if not part_id or not partname:
            continue

        if is_switch_part(partname):
            switches.append({
                "id": int(part_id),
                "name": partname
            })

    return switches
