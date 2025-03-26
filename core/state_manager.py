import json
import os
from datetime import datetime
import logging

STATE_PATH = "memory/belief_state.json"
VERSIONED_DIR = "memory/versions"
LOG_PATH = "logs/aletheia.log"

# Set up logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

DEFAULT_STATE = {
    "active_narratives": [],
    "positioning": {},
    "recent_events": [],
    "reasoning_chain": [],
    "scenarios": [],
    "report": "",
    "raw_event_output": ""
}

def load_state():
    if not os.path.exists(STATE_PATH):
        return DEFAULT_STATE
    with open(STATE_PATH, 'r') as f:
        return json.load(f)

def save_state(state):
    os.makedirs(VERSIONED_DIR, exist_ok=True)

    # Save current version
    with open(STATE_PATH, 'w') as f:
        json.dump(state, f, indent=2)

    # Save versioned copy
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
    version_path = os.path.join(VERSIONED_DIR, f"belief_state_{timestamp}.json")
    with open(version_path, 'w') as f:
        json.dump(state, f, indent=2)

    # Log snapshot
    logging.info("Belief state saved. Versioned copy: %s", version_path)
