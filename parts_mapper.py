import re
from pathlib import Path

def normalize(name: str) -> str:
    name = name.upper()
    name = re.sub(r"^(TB|TS)\s+", "", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip()

def build_parts_map(parts_root="web/parts"):
    root = Path(parts_root)
    mapping = {}

    for img in root.rglob("*.gif"):
        key = normalize(img.stem)
        mapping[key] = "/" + str(img.relative_to("web"))

    return mapping
