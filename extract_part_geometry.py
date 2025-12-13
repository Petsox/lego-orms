import os
import json
import xml.etree.ElementTree as ET

PARTS_ROOT = "web/parts"
OUT_FILE = "web/res/part_geometry.json"

PIXELS_PER_STUD = 8  # keep consistent with renderer


def safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def parse_part_xml(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    part_number = root.findtext(".//PartNumber")
    if not part_number:
        return None, None

    da = root.find(".//DisplayArea")
    if da is None:
        return None, None

    width = safe_float(da.findtext("Width"))
    height = safe_float(da.findtext("Height"))

    if width <= 0 or height <= 0:
        return None, None

    # BlueBrick uses center-origin display areas
    origin_x = width / 2
    origin_y = height / 2

    return part_number.strip(), {
        "width": width * PIXELS_PER_STUD,
        "height": height * PIXELS_PER_STUD,
        "origin": {
            "x": origin_x * PIXELS_PER_STUD,
            "y": origin_y * PIXELS_PER_STUD
        }
    }


def extract_all_parts():
    parts = {}

    for root_dir, _, files in os.walk(PARTS_ROOT):
        for filename in files:
            if not filename.lower().endswith(".xml"):
                continue

            xml_path = os.path.join(root_dir, filename)

            try:
                key, data = parse_part_xml(xml_path)
                if key and data:
                    parts[key] = data
            except Exception as e:
                print("❌ Failed:", xml_path)
                print("   ", e)

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(parts, f, indent=2)

    print(f"✅ Extracted {len(parts)} parts → {OUT_FILE}")


if __name__ == "__main__":
    extract_all_parts()
