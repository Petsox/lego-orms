import xml.etree.ElementTree as ET
from pathlib import Path

SWITCH_KEYWORDS = ("SWITCH", "TURNOUT", "POINT")

def load_layout(path: str):
    tree = ET.parse(path)
    root = tree.getroot()

    bricks = root.findall(".//Brick")

    items = []
    switches = []

    min_x = min_y = float("inf")

    for b in bricks:
        part = (b.findtext("PartNumber") or "").strip()
        bid = b.get("id")

        da = b.find("DisplayArea")
        if da is None:
            continue

        x = float(da.findtext("X", "0"))
        y = float(da.findtext("Y", "0"))
        w = float(da.findtext("Width", "0"))
        h = float(da.findtext("Height", "0"))

        rot = float(b.findtext("Orientation", "0")) % 360

        min_x = min(min_x, x)
        min_y = min(min_y, y)

        item = {
            "id": bid,
            "part": part,
            "x": x,
            "y": y,
            "w": w,
            "h": h,
            "rot": rot
        }

        items.append(item)

        if any(k in part.upper() for k in SWITCH_KEYWORDS):
            switches.append(item)

    # normalize coords
    for i in items:
        i["x"] -= min_x
        i["y"] -= min_y

    return {
        "items": items,
        "switches": switches
    }
