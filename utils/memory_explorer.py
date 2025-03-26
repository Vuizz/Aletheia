import os
import json
import difflib

VERSIONED_DIR = "memory/versions"

def list_snapshots():
    files = sorted(f for f in os.listdir(VERSIONED_DIR) if f.endswith(".json"))
    return files

def load_snapshot(filename):
    path = os.path.join(VERSIONED_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def compare_belief_states(snapshot1, snapshot2):
    keys = ["recent_events", "active_narratives", "reasoning_chain", "scenarios", "report"]
    diffs = {}
    for key in keys:
        a = json.dumps(snapshot1.get(key, {}), indent=2)
        b = json.dumps(snapshot2.get(key, {}), indent=2)
        diff = list(difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm="", n=2))
        if diff:
            diffs[key] = "\n".join(diff)
    return diffs

def print_diff_summary(diffs):
    for section, diff in diffs.items():
        print(f"\n=== Δ {section.upper()} ===")
        print(diff)