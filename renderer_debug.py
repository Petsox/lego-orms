import json
import time

LOGFILE = "render_debug.jsonl"

def log_render_item(data):
    entry = {
        "ts": time.time(),
        **data
    }
    with open(LOGFILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
