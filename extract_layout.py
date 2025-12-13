import json
import os
import xml.etree.ElementTree as ET

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BBM_FILE = os.path.join(BASE_DIR, "Layout.bbm")
OUT_FILE = os.path.join(BASE_DIR, "web", "res", "layout.json")


def extract_layout():
    tree = ET.parse(BBM_FILE)
    root = tree.getroot()

    items = []

    for brick in root.findall(".//Brick"):
        try:
            brick_id = int(brick.attrib.get("id"))
            part = brick.findtext("PartNumber", "").strip()
            orientation = int(brick.findtext("Orientation", "0"))

            da = brick.find("DisplayArea")
            if da is None:
                continue

            x = float(da.findtext("X"))
            y = float(da.findtext("Y"))
            w = float(da.findtext("Width"))
            h = float(da.findtext("Height"))

            items.append({
                "id": brick_id,
                "part": part,
                "x": x,
                "y": y,
                "w": w,
                "h": h,
                "orientation": orientation
            })

        except Exception as e:
            print("⚠️ Skipped brick:", e)

    return {"items": items}


if __name__ == "__main__":
    if not os.path.exists(BBM_FILE):
        print("❌ Layout.bbm not found")
        exit(1)

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)

    data = extract_layout()
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Wrote {len(data['items'])} items → {OUT_FILE}")
