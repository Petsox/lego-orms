import os
import xml.etree.ElementTree as ET
import json

PIXELS_PER_STUD = 8

PARTS_DIR = "web/res/parts_xml"   # adjust if needed
OUT_FILE = "web/res/part_origin.json"


def parse_part_origin(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Default origin (0,0)
    ox = 0.0
    oy = 0.0

    # Try to infer origin from ConnexionList comment:
    # "the center of this part in stud is x = ... and y = ..."
    for comment in root.iter():
        if isinstance(comment.tag, str):
            continue

    # Fallback: use first connexion position (most reliable anchor)
    conn = root.find(".//ConnexionList/connexion/position")
    if conn is not None:
        ox = float(conn.find("x").text)
        oy = float(conn.find("y").text)

    return {
        "x": ox * PIXELS_PER_STUD,
        "y": oy * PIXELS_PER_STUD
    }


def build_origin_table():
    table = {}

    for fname in os.listdir(PARTS_DIR):
        if not fname.endswith(".xml"):
            continue

        part_id = fname.split(".")[0]  # "2859.8.xml" → "2859"
        path = os.path.join(PARTS_DIR, fname)

        try:
            table[part_id] = parse_part_origin(path)
        except Exception as e:
            print(f"Failed to parse {fname}: {e}")

    with open(OUT_FILE, "w") as f:
        json.dump(table, f, indent=2)

    print(f"Wrote {OUT_FILE} with {len(table)} entries")


if __name__ == "__main__":
    build_origin_table()
