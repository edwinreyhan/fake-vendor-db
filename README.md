# fake-vendor-db

A **fake vendor database** for a data-engineering practice project. It is synthetic and public on purpose:
no real data, no secrets. A scheduled workflow changes its schema and values on a **plan**, so an ingest job
that reads it breaks on dates we choose.

- The database is `data/vendor.db` (SQLite). Raw URL: `https://raw.githubusercontent.com/edwinreyhan/fake-vendor-db/main/data/vendor.db`
- The plan is `plan/changes.json`. Times carry an offset (`+08:00` = WITA).
- Each change is one SQL file in `migrations/`.
- `.github/workflows/vendor.yml` runs every 15 minutes (GitHub may start it late), applies every change that is due and not applied yet, and commits the database only when it changed.
- The plan file also holds an answer key (`kind`, `truth`). It is public. An ingest job or an AI fixer should not read it: they should work from the data only.

Run locally: `python -m src.vendor.apply` and `python -m pytest -q`. Simulate a clock: `python simulate.py`.
