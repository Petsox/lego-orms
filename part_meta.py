from pathlib import Path
import re


ANCHOR_RE = re.compile(
    r"<Anchor>\s*<X>([-\d.]+)</X>\s*<Y>([-\d.]+)</Y>\s*</Anchor>",
    re.IGNORECASE
)

PIVOT_RE = re.compile(
    r"<Pivot>\s*<X>([-\d.]+)</X>\s*<Y>([-\d.]+)</Y>\s*</Pivot>",
    re.IGNORECASE
)


def parse_part_xml(xml_path):
    text = Path(xml_path).read_text(encoding="utf-8", errors="ignore")

    meta = {}

    m = ANCHOR_RE.search(text)
    if m:
        meta["anchor"] = [float(m.group(1)), float(m.group(2))]

    m = PIVOT_RE.search(text)
    if m:
        meta["pivot"] = [float(m.group(1)), float(m.group(2))]

    return meta


def build_part_meta(parts_root="web/parts"):
    meta = {}

    for xml in Path(parts_root).rglob("*.xml"):
        part_id = xml.stem  # e.g. "2861"
        data = parse_part_xml(xml)
        if data:
            meta[part_id] = data

    return meta
