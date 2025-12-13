import os
import json
import xml.etree.ElementTree as ET

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARTS_ROOT = os.path.join(BASE_DIR, "web", "parts")
OUT_FILE = os.path.join(BASE_DIR, "web", "res", "part_geometry.json")

PIXELS_PER_STUD = 8


def extract_first_brick(xml_text):
    start = xml_text.find("<Brick")
    end = xml_text.find("</Brick>")
    if start == -1 or end == -1:
        return None
    return xml_text[start:end + len("</Brick>")]


def parse_part_xml(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        raw = f.read()

    brick_xml = extract_first_brick(raw)
    if not brick_xml:
        return None, None

    try:
        root = ET.fromstring(brick_xml)
    except ET.ParseError:
        return None, None

    part = root.findtext("PartNumber")
    da = root.find("DisplayArea")

    if not part or da is None:
        return None, None

    try:
        w = float(da.findtext("Width"))
        h = float(da.findtext("Height"))
    except Exception:
        return None, None

    return part.strip(), {
        "width": w * PIXELS_PER_STUD,
        "height": h * PIXELS_PER_STUD,
        "origin": {
            "x": (w / 2) * PIXELS_PER_STUD,
            "y": (h / 2) * PIXELS_PER_STUD
        }
    }


def extract_all():
    parts = {}

    for root, _, files in os.walk(PARTS_ROOT):
        for f in files:
            if not f.lower().endswith(".xml"):
                continue

            path = os.path.join(root, f)
            key, data = parse_part_xml(path)
            if key and data:
                parts[key] = data

    return parts


if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)

    data = extract_all()
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Wrote {len(data)} parts → {OUT_FILE}")
