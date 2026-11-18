"""Apply the scheduled changes that are due. Safe to run any number of times."""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

MIGRATIONS = Path(__file__).resolve().parents[2] / "migrations"


def init_db(db_path):
    """Create the database from the first migration, if the file does not exist."""
    if Path(db_path).exists():
        return
    con = sqlite3.connect(db_path)
    con.executescript((MIGRATIONS / "0001_create_products.sql").read_text())
    con.execute("CREATE TABLE _applied (id TEXT PRIMARY KEY, scheduled_at TEXT, applied_at TEXT)")
    con.commit()
    con.close()


def load_plan(plan_path):
    plan = json.loads(Path(plan_path).read_text())
    for e in plan:
        e["when"] = datetime.fromisoformat(e["not_before"])  # must carry an offset
        if e["when"].tzinfo is None:
            raise ValueError(f"{e['id']}: not_before needs a UTC offset, e.g. +08:00")
    return sorted(plan, key=lambda e: e["when"])


def apply_due(db_path, plan_path, now=None):
    """Apply every entry whose time has come and that is not applied yet, in order.
    Returns the ids applied in this run."""
    now = now or datetime.now(timezone.utc)
    init_db(db_path)
    con = sqlite3.connect(db_path)
    done = {r[0] for r in con.execute("SELECT id FROM _applied")}
    applied = []
    for e in load_plan(plan_path):
        if e["id"] in done or e["when"] > now:
            continue
        con.executescript((MIGRATIONS / e["migration"]).read_text())
        con.execute("INSERT INTO _applied VALUES (?, ?, ?)",
                    (e["id"], e["when"].isoformat(), now.isoformat()))
        con.commit()
        applied.append(e["id"])
    con.close()
    return applied


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/vendor.db")
    ap.add_argument("--plan", default="plan/changes.json")
    ap.add_argument("--now", help="ISO time with offset, for testing")
    a = ap.parse_args()
    Path(a.db).parent.mkdir(parents=True, exist_ok=True)
    now = datetime.fromisoformat(a.now) if a.now else None
    print("applied:", apply_due(a.db, a.plan, now) or "nothing due")
