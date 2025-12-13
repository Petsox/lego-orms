import os
import json
import xml.etree.ElementTree as ET

PARTS_ROOT = "web/parts"
OUT_FILE = "web/res/part_geometry.json"
PIXELS_PER_STUD = 8


def extract_first_brick(xml_text):
    """
    BlueBrick XML files sometimes contain junk or multiple roots.
    We extract only the first <Brick>...</Brick> block.
    """
    start = xml_text.find("<Brick")
    end = xml_text.find("</Brick>")
    if start == -1 or end == -1:
        return None
    return xml_text[start:end + len("</Brick>")]


def parse_part_xml(xml_path):
    with open(xml_path, "r", encoding="utf-8", errors="ignore") as f:
        raw = f.read()

    brick_xml = extract_first_brick(raw)
    if not brick_xml:
        return None, None

    try:
        root = ET.fromstring(brick_xml)
    except ET.ParseError:
        return None, None

    part_number = root.findtext("PartNumber")
    if not part_number:
        return None, None

    da = root.find("DisplayArea")
    if da is None:
        return None, None

    try:
        width = float(da.findtext("Width"))
        height = float(da.findtext("Height"))
    except Exception:
        return None, None

    if width <= 0 or height <= 0:
        return None, None

    return part_number.strip(), {
        "width": width * PIXELS_PER_STUD,
        "height": height * PIXELS_PER_STUD,
        "origin": {
            "x": (width / 2) * PIXELS_PER_STUD,
            "y": (height / 2) * PIXELS_PER_STUD
        }
    }


def extract_all_parts():
    parts = {}

    for root_dir, _, files in os.walk(PARTS_ROOT):
        for file in files:
            if not file.lower().endswith(".xml"):
                continue

            path = os.path.join(root_dir, file)

            try:
                key, data = parse_part_xml(path)
                if key and data:
                    parts[key] = data
            except Exception as e:
                print("✖ Failed:", path, e)

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(parts, f, indent=2)

    print(f"✔ Extracted {len(parts)} parts → {OUT_FILE}")


if __name__ == "__main__":
    extract_all_parts()
