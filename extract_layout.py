import json
import os
import xml.etree.ElementTree as ET

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BBM_FILE = os.path.join(BASE_DIR, "Layout.bbm")
OUT_FILE = os.path.join(BASE_DIR, "web", "res", "layout.json")


def bb_orientation_to_deg(o):
    try:
        return (int(o) / 7) % 360
    except Exception:
        return 0


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

            active_conn = int(
                brick.findtext("ActiveConnectionPointIndex", "0")
            )

            connections = []
            conns = brick.find("Connexions")
            if conns is not None:
                for c in conns.findall("Connexion"):
                    linked = c.findtext("LinkedTo")
                    if linked:
                        connections.append(int(linked))

            items.append({
                "id": brick_id,
                "part": part,
                "x": x,
                "y": y,
                "orientation": orientation,
                "rotation_deg": bb_orientation_to_deg(orientation),
                "active_connection": active_conn,
                "connections": connections
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
