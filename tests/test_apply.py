import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.vendor.apply import apply_due

PLAN = Path(__file__).resolve().parents[1] / "plan" / "changes.json"
WITA = timezone(timedelta(hours=8))


def t(s):
    return datetime.fromisoformat(s)


def columns(db):
    return [r[1] for r in sqlite3.connect(db).execute("PRAGMA table_info(products)")]


def test_nothing_due_before_the_first_time(tmp_path):
    db = tmp_path / "v.db"
    assert apply_due(db, PLAN, t("2026-11-19T02:33:59+08:00")) == []
    assert columns(db) == ["id", "name", "price"]


def test_two_changes_on_one_day_apply_at_their_own_times(tmp_path):
    db = tmp_path / "v.db"
    assert apply_due(db, PLAN, t("2026-11-19T03:00:00+08:00")) == ["c001"]
    assert apply_due(db, PLAN, t("2026-11-19T16:00:00+08:00")) == []
    assert apply_due(db, PLAN, t("2026-11-19T17:00:00+08:00")) == ["c002"]
    assert columns(db) == ["id", "name", "amount", "note"]


def test_days_with_no_change_apply_nothing(tmp_path):
    db = tmp_path / "v.db"
    apply_due(db, PLAN, t("2026-11-19T23:00:00+08:00"))
    assert apply_due(db, PLAN, t("2026-11-23T12:00:00+08:00")) == []


def test_running_twice_does_not_apply_again(tmp_path):
    db = tmp_path / "v.db"
    now = t("2026-11-26T12:00:00+08:00")
    assert apply_due(db, PLAN, now) == ["c001", "c002", "c003"]
    assert apply_due(db, PLAN, now) == []


def test_a_late_run_catches_up_in_order(tmp_path):
    db = tmp_path / "v.db"
    # the scheduler was down for a week: everything due is applied, oldest first
    assert apply_due(db, PLAN, t("2026-12-01T00:00:00+08:00")) == ["c001", "c002", "c003"]
    price = sqlite3.connect(db).execute("SELECT amount FROM products WHERE id=1").fetchone()[0]
    assert price == 1999  # 19.99 dollars became 1999 cents


def test_a_time_without_offset_is_rejected(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text('[{"id":"x","not_before":"2026-11-19T02:34:00","migration":"0002_add_note.sql"}]')
    with pytest.raises(ValueError):
        apply_due(tmp_path / "v.db", bad, t("2026-11-21T00:00:00+08:00"))


def test_the_note_column_is_dropped_in_december(tmp_path):
    db = tmp_path / "v.db"
    apply_due(db, PLAN, t("2026-12-02T00:00:00+08:00"))
    assert "note" in columns(db)
    assert apply_due(db, PLAN, t("2026-12-04T00:00:00+08:00")) == ["c004"]
    assert "note" not in columns(db)
