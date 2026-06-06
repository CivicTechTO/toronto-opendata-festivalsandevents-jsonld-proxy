"""
Tracks the availability of the upstream City of Toronto feed.

The status is persisted to ``docs/feed_status.json`` so it can drive the
downtime notices on the public landing page and README. Only the state and the
original "down since" timestamp are stored (no per-run timestamp), so a
sustained outage does not produce a daily no-op commit — the file only changes
when the feed transitions between healthy and unavailable.
"""

import os
import json
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
STATUS_PATH = os.path.normpath(os.path.join(HERE, "..", "docs", "feed_status.json"))


def load_status():
    """Return the persisted status dict, or an empty dict if none exists."""
    try:
        with open(STATUS_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save(status):
    os.makedirs(os.path.dirname(STATUS_PATH), exist_ok=True)
    with open(STATUS_PATH, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)
        f.write("\n")


def record_success():
    """Mark the feed as healthy, clearing any outage."""
    _save({"status": "ok", "down_since": None})


def record_outage():
    """
    Mark the feed as down. Preserves the original ``down_since`` timestamp
    across consecutive failing runs, only stamping it when an outage begins.
    """
    prev = load_status()
    down_since = prev.get("down_since") if prev.get("status") == "down" else None
    if not down_since:
        down_since = datetime.now(timezone.utc).isoformat()
    _save({"status": "down", "down_since": down_since})
