import xml.etree.ElementTree as ET
from pathlib import Path

def parse_part_xml(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    meta = {}

    # Try common BlueBrick fields
    anchor_x = root.findtext(".//Anchor/X")
    anchor_y = root.findtext(".//Anchor/Y")

    pivot_x = root.findtext(".//Pivot/X")
    pivot_y = root.findtext(".//Pivot/Y")

    if anchor_x and anchor_y:
        meta["anchor"] = [float(anchor_x), float(anchor_y)]

    if pivot_x and pivot_y:
        meta["pivot"] = [float(pivot_x), float(pivot_y)]

    return meta


def build_part_meta(parts_root="web/parts"):
    meta = {}

    for xml in Path(parts_root).rglob("*.xml"):
        part_id = xml.stem  # e.g. "2861"
        data = parse_part_xml(xml)

        if data:
            meta[part_id] = data

    return meta
