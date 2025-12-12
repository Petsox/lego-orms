from pathlib import Path
import re

CONN_RE = re.compile(
    r"<position>\s*<x>([-\d.]+)</x>\s*<y>([-\d.]+)</y>\s*</position>",
    re.IGNORECASE
)

STUD_TO_PX = 8.0

def parse_part_xml(xml_path):
    text = Path(xml_path).read_text(encoding="utf-8", errors="ignore")

    points = []
    for m in CONN_RE.finditer(text):
        x_stud = float(m.group(1))
        y_stud = float(m.group(2))
        points.append((x_stud * STUD_TO_PX, y_stud * STUD_TO_PX))

    if not points:
        return {}

    # Centroid of connection points = logical origin
    ox = sum(p[0] for p in points) / len(points)
    oy = sum(p[1] for p in points) / len(points)

    return {
        "origin": [ox, oy]
    }

def build_part_meta(parts_root="web/parts"):
    meta = {}
    for xml in Path(parts_root).rglob("*.xml"):
        part_id = xml.stem.split(".")[0]  # "2861.8" → "2861"
        data = parse_part_xml(xml)
        if data:
            meta[part_id] = data
    return meta
