"""Local JSON stores: the shared blocklist and per-agent interaction history.

Phase-1 stand-ins for what later becomes an on-chain blocklist registry and
indexer-backed history. Both files live in the project's data/ directory
(override with the NEARGUARD_DATA environment variable). Blocklist reports
must carry evidence -- an entry without it is not accepted.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(os.environ.get(
    "NEARGUARD_DATA", Path(__file__).resolve().parent.parent / "data"))


def _load(name):
    path = DATA_DIR / name
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save(name, data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / name).write_text(json.dumps(data, indent=2) + "\n")


# --- blocklist ------------------------------------------------------------

def load_blocklist():
    return _load("blocklist.json")


def blocklist_entry(account_id):
    """Return the blocklist entry for account_id, or None."""
    return load_blocklist().get(account_id)


def report_to_blocklist(account_id, reason, evidence, reported_by):
    """Append a report to the shared blocklist. Evidence is required."""
    if not evidence:
        raise ValueError("blocklist reports must attach evidence")
    entry = {
        "reason": reason,
        "evidence": evidence,
        "reported_by": reported_by,
        "reported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    data = load_blocklist()
    data[account_id] = entry
    _save("blocklist.json", data)
    return entry


# --- interaction history ----------------------------------------------------

def load_history():
    return _load("history.json")


def get_interaction(agent_id, receiver_id):
    """Return {count, total_near, last} for agent->receiver, or None."""
    return load_history().get(agent_id, {}).get(receiver_id)


def record_interaction(agent_id, receiver_id, amount_near):
    data = load_history()
    entry = data.setdefault(agent_id, {}).setdefault(
        receiver_id, {"count": 0, "total_near": "0", "last": None})
    entry["count"] += 1
    entry["total_near"] = str(float(entry["total_near"]) + float(amount_near))
    entry["last"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    _save("history.json", data)
    return entry
