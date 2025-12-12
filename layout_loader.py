import json
from pathlib import Path


def load_layout(path: str):
    """
    Loads a BlockBench .bbm layout file.
    Extracts switches, track pieces, and their coordinates.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Layout file not found: {path}")

    with open(file_path, "r") as f:
        data = json.load(f)

    elements = data.get("elements", [])
    items = []

    min_x = float("inf")
    min_y = float("inf")

    # First pass: find bounding box
    for el in elements:
        name = el.get("name", "").lower()

        # Only keep elements we understand
        if any(k in name for k in ["switch", "track", "curve", "point", "turnout"]):
            origin = el.get("origin", [0, 0, 0])
            x = origin[0]
            y = origin[2]  # z is "forward" in BBM
            
            min_x = min(min_x, x)
            min_y = min(min_y, y)

    # Second pass: extract normalized items
    for el in elements:
        raw_name = el.get("name", "")
        name = raw_name.lower()

        origin = el.get("origin", [0, 0, 0])
        x = origin[0]
        y = origin[2]

        # UI uses normalized coordinates
        nx = x - min_x
        ny = y - min_y

        if "switch" in name or "point" in name or "turnout" in name:
            items.append({
                "type": "switch",
                "id": raw_name,
                "x": nx,
                "y": ny
            })
        elif "track" in name or "curve" in name or "straight" in name:
            items.append({
                "type": "track",
                "id": raw_name,
                "x": nx,
                "y": ny
            })

    # Final result
    return {
        "items": items,
        "meta": {
            "count": len(items),
            "file": path
        }
    }


if __name__ == "__main__":
    # Debug test
    layout = load_layout("Layout.bbm")
    print(json.dumps(layout, indent=4))
