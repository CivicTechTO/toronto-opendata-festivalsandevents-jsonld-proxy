"""
Render the upstream feed downtime notice into the public landing page and README.

Reads ``docs/feed_status.json`` and replaces the content between the
``FEED_STATUS_NOTICE`` marker comments in both files. When the feed is down a
notice (with the outage start time) is shown; when it is healthy the block is
cleared. This keeps the notices in lock-step with the feed status automatically.
"""

import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from status import load_status

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
README_PATH = os.path.join(ROOT, "README.md")
INDEX_PATH = os.path.join(ROOT, "docs", "index.html")

TZ = ZoneInfo("America/Toronto")
START = "<!-- FEED_STATUS_NOTICE:START -->"
END = "<!-- FEED_STATUS_NOTICE:END -->"


def format_dt(iso):
    """Format an ISO timestamp as e.g. 'May 23, 2026 4:05 AM EDT' in Toronto time."""
    dt = datetime.fromisoformat(iso).astimezone(TZ)
    return dt.strftime("%B %-d, %Y %-I:%M %p %Z")


def build_notices(status):
    """Return (readme_block, html_block) for the current status, marker-wrapped."""
    if status.get("status") == "down":
        when = format_dt(status["down_since"]) if status.get("down_since") else "an earlier"
        readme = (
            f"{START}\n"
            f"> ⚠️ **Feed temporarily unavailable.** The City of Toronto’s upstream "
            f"Festivals & Events data source has been returning an “Access Denied” "
            f"response and is not serving data as of the **{when}** run. The published "
            f"feeds reflect the last successfully retrieved data and are not being "
            f"updated until the source is restored. The daily workflow skips gracefully "
            f"(rather than failing) while the source is down. This notice is removed "
            f"automatically when normal operation resumes.\n"
            f"{END}"
        )
        html = (
            f"{START}\n"
            f'  <div class="notice">\n'
            f"    <strong>⚠️ Feed temporarily unavailable.</strong>\n"
            f"    The City of Toronto's upstream Festivals &amp; Events data source has been\n"
            f'    returning an "Access Denied" response and is not serving data as of the\n'
            f"    <strong>{when}</strong> run. The feeds below reflect the last successfully\n"
            f"    retrieved data and are no longer being updated until the source is restored.\n"
            f"    This notice is removed automatically when normal operation resumes.\n"
            f"  </div>\n"
            f"  {END}"
        )
        return readme, html

    # Healthy: clear the notice but keep the markers for the next outage.
    return f"{START}\n{END}", f"{START}\n  {END}"


def patch(path, replacement):
    with open(path, encoding="utf-8") as f:
        text = f.read()

    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if not pattern.search(text):
        print(f"⚠️ Notice markers not found in {path} — skipping")
        return

    # Use a function replacement so backslashes/escapes in the text are literal.
    new = pattern.sub(lambda _: replacement, text)
    if new != text:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new)
        print(f"✏️ Updated notice in {os.path.relpath(path, ROOT)}")
    else:
        print(f"✓ Notice already current in {os.path.relpath(path, ROOT)}")


def main():
    status = load_status()
    readme_block, html_block = build_notices(status)
    patch(README_PATH, readme_block)
    patch(INDEX_PATH, html_block)


if __name__ == "__main__":
    main()
