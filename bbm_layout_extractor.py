import xml.etree.ElementTree as ET
from bbm_switch_extractor import is_switch_part
import json
import os
from datetime import datetime


def extract_layout_from_bbm(path: str):
    tree = ET.parse(path)
    root = tree.getroot()

    bricks = []

    for brick in root.findall(".//{*}Brick"):
        brick_id = brick.get("id")

        da = brick.find("{*}DisplayArea")
        part_el = brick.find("{*}PartNumber")
        orient_el = brick.find("{*}Orientation")

        if brick_id is None or da is None:
            continue

        try:
            x = float(da.find("{*}X").text)
            y = float(da.find("{*}Y").text)
            w = float(da.find("{*}Width").text)
            h = float(da.find("{*}Height").text)
        except Exception:
            continue

        orientation = float(orient_el.text) if orient_el is not None else 0.0
        rot_deg = orientation / 10.0

        part_number = part_el.text.strip() if part_el is not None else ""

        bricks.append({
            "id": int(brick_id),
            "part": part_number,
            "x": x,
            "y": y,
            "w": w,
            "h": h,
            "rotation": rot_deg,
            "is_switch": is_switch_part(part_number)
        })

    return bricks

def build_layout_cache(bbm_path, cache_path):
    layout = extract_layout_from_bbm(bbm_path)

    data = {
        "meta": {
            "source": os.path.basename(bbm_path),
            "generated_at": datetime.utcnow().isoformat(),
            "stud_px": 8
        },
        "bricks": layout
    }

    with open(cache_path, "w") as f:
        json.dump(data, f, indent=2)

    return data
