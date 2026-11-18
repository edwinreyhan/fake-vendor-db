"""Fake clock: run the workflow every 15 minutes (plus a 7-minute start delay) and print what happens per WITA day."""
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.vendor.apply import apply_due

WITA = timezone(timedelta(hours=8))
PLAN = Path("plan/changes.json")
db = Path(tempfile.mkdtemp()) / "v.db"
now = datetime(2026, 11, 18, 0, 7, tzinfo=WITA)
end = datetime(2026, 11, 28, 0, 0, tzinfo=WITA)
per_day = {}
while now < end:
    for cid in apply_due(db, PLAN, now):
        per_day.setdefault(now.date(), []).append((cid, now))
    now += timedelta(minutes=15)
day = datetime(2026, 11, 18, tzinfo=WITA).date()
while day < end.date():
    items = per_day.get(day, [])
    text = ", ".join(f"{c} applied {n:%H:%M}" for c, n in items) or "no change"
    print(f"{day}  {len(items)} change(s)  {text}")
    day += timedelta(days=1)
