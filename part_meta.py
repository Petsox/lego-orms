import xml.etree.ElementTree as ET
from pathlib import Path
import re


def parse_part_xml(xml_path):
    """
    BlueBrick XML files are NOT strict XML.
    They often contain multiple top-level elements.
    This function safely extracts the first valid XML block.
    """
    text = Path(xml_path).read_text(encoding="utf-8", errors="ignore")

    # Try to extract the first XML root element
    # This matches <Something> ... </Something>
    match = re.search(r"(<[^!?][\s\S]*?</[^>]+>)", text)
    if not match:
        return {}

    xml_clean = match.group(1)

    try:
        root = ET.fromstring(xml_clean)
    except ET.ParseError:
        return {}

    meta = {}

    # Try common BlueBrick anchor fields
    def find_float(path):
        el = root.find(path)
        if el is not None and el.text:
            try:
                return float(el.text)
            except ValueError:
                pass
        return None

    ax = find_float(".//Anchor/X")
    ay = find_float(".//Anchor/Y")
    px = find_float(".//Pivot/X")
    py = find_float(".//Pivot/Y")

    if ax is not None and ay is not None:
        meta["anchor"] = [ax, ay]

    if px is not None and py is not None:
        meta["pivot"] = [px, py]

    return meta


def build_part_meta(parts_root="web/parts"):
    meta = {}

    for xml in Path(parts_root).rglob("*.xml"):
        part_id = xml.stem  # e.g. "2861"
        data = parse_part_xml(xml)
        if data:
            meta[part_id] = data

    return meta
