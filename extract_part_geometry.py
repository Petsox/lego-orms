import os
import json
import xml.etree.ElementTree as ET

PIXELS_PER_STUD = 8
XML_ROOT = "web/res/parts_xml"
OUT_FILE = "web/res/part_geometry.json"


def parse_part(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    part = {}

    # Part number
    part_number = root.findtext(".//PartNumber")
    if not part_number:
        return None, None

    # Display area (geometry)
    da = root.find(".//DisplayArea")
    if da is not None:
        width = float(da.findtext("Width"))
        height = float(da.findtext("Height"))
    else:
        return None, None

    # Origin = center of display area
    origin_x = width / 2
    origin_y = height / 2

    part["width"] = width * PIXELS_PER_STUD
    part["height"] = height * PIXELS_PER_STUD
    part["origin"] = {
        "x": origin_x * PIXELS_PER_STUD,
        "y": origin_y * PIXELS_PER_STUD
    }

    return part_number.strip(), part


def build_geometry():
    data = {}

    for root_dir, _, files in os.walk(XML_ROOT):
        for f in files:
            if not f.endswith(".xml"):
                continue
            path = os.path.join(root_dir, f)
            try:
                key, part = parse_part(path)
                if key and part:
                    data[key] = part
            except Exception as e:
                print("Error parsing", path, e)

    with open(OUT_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Wrote {len(data)} parts → {OUT_FILE}")


if __name__ == "__main__":
    build_geometry()
