#!/usr/bin/env python3
"""
layout_loader.py

Parses BlueBrick-style Layout.bbm XML (the file you uploaded) and returns a dict:
{
  "items": [ {id, brick_id, part_number, x, y, width, height, orientation, ...}, ... ],
  "switches": [ same objects but only switches ],
  "meta": { "count": n, "switch_count": m, "file": path, "bounds": {...} }
}

This loader was written to match the Layout.bbm structure you provided:
 - pieces are stored in <Brick id="..."> with <DisplayArea><X>...</X><Y>...</Y>...
 - part type is in <PartNumber>
 - orientation in <Orientation>
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List

# ---------------------------------------------------------------------------
# Heuristic for detecting "switch" bricks: if the PartNumber contains any of
# these keywords we classify it as a switch/turnout/points piece.
# You can extend this list if you find other part names in your .bbm file.
# ---------------------------------------------------------------------------
_SWITCH_KEYWORDS = [
    "SWITCH",
    "POINT",
    "TURNOUT",
    "TRIPLE SWITCH",
    "4 STUD GAP TRIPLE SWITCH",
    "PASS-THOUGH CONNECTOR",  # sometimes special parts indicate junctions
]


def _is_switch_part(part_number: str) -> bool:
    if not part_number:
        return False
    pn = part_number.upper()
    for k in _SWITCH_KEYWORDS:
        if k in pn:
            return True
    return False


def _safe_float(text, default=0.0):
    try:
        return float(text)
    except Exception:
        return default


def load_layout(path: str) -> Dict[str, Any]:
    """
    Parse the Layout.bbm XML and return a structured dict.
    path: path to Layout.bbm file
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Layout file not found: {path}")

    tree = ET.parse(str(p))
    root = tree.getroot()

    # Find all Brick nodes; BlueBrick file uses <Brick id="..."> for placed pieces
    bricks = root.findall(".//Brick")

    items: List[Dict[str, Any]] = []
    min_x = float("inf")
    min_y = float("inf")
    max_x = float("-inf")
    max_y = float("-inf")

    for b in bricks:
        # brick id attribute (string)
        brick_id = b.get("id") or b.get("ID") or ""
        # part number / name
        part_number = (b.findtext("PartNumber") or "").strip()

        # DisplayArea is where the X/Y/Width/Height live in the files I inspected
        da = b.find("DisplayArea")
        if da is not None:
            x = _safe_float(da.findtext("X"))
            y = _safe_float(da.findtext("Y"))
            width = _safe_float(da.findtext("Width"))
            height = _safe_float(da.findtext("Height"))
        else:
            # fallback: sometimes other tags are used
            x = _safe_float(b.findtext("X"))
            y = _safe_float(b.findtext("Y"))
            width = _safe_float(b.findtext("Width"))
            height = _safe_float(b.findtext("Height"))

        orientation = _safe_float(b.findtext("Orientation"))

        # track bounding box extremes
        min_x = min(min_x, x)
        min_y = min(min_y, y)
        max_x = max(max_x, x + width)
        max_y = max(max_y, y + height)

        # id to expose to server/frontend: prefer brick_id else try PartNumber based id
        display_id = str(brick_id) if brick_id is not None else part_number

        item = {
            "id": display_id,            # string id (brick id) — use this for mapping
            "brick_id": brick_id,
            "part_number": part_number,
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "orientation": orientation,
        }

        items.append(item)

    # If no bricks, return empty but valid structure
    if not items:
        return {
            "items": [],
            "switches": [],
            "meta": {"count": 0, "switch_count": 0, "file": str(p), "bounds": None}
        }

    # Normalize coordinates so top-left becomes (0,0)
    # (useful for SVG placement)
    for it in items:
        it["x_norm"] = it["x"] - min_x
        it["y_norm"] = it["y"] - min_y
        # normalize orientation into 0..360
        try:
            it["rotation_deg"] = float(it.get("orientation", 0.0)) % 360.0
        except Exception:
            it["rotation_deg"] = 0.0

    # Auto-detect switches using PartNumber heuristics
    switches = [it for it in items if _is_switch_part(it.get("part_number", ""))]

    result = {
        "items": items,
        "switches": switches,
        "meta": {
            "count": len(items),
            "switch_count": len(switches),
            "file": str(p),
            "bounds": {
                "min_x": min_x,
                "min_y": min_y,
                "max_x": max_x,
                "max_y": max_y,
                "width": max_x - min_x,
                "height": max_y - min_y,
            }
        }
    }

    return result


# Quick CLI test if run directly
if __name__ == "__main__":
    import json
    import sys
    test_path = sys.argv[1] if len(sys.argv) > 1 else "Layout.bbm"
    layout = load_layout(test_path)
    print(json.dumps(layout["meta"], indent=2))
    # print first few items
    for it in layout["items"][:8]:
        print(f"{it['id']:>8}  {it['part_number'][:30]:30}  x={it['x_norm']:.2f} y={it['y_norm']:.2f} rot={it['rotation_deg']:.1f}")
