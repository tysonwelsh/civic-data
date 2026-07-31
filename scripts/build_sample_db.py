#!/usr/bin/env python3
"""Build gov-sample.db — a small, committable slice of gov.db so a stranger can
try queries in thirty seconds without the 1.6 GB artifact (G6, 2026-07-31).

Default slice: one mid-size city (vineyard) + one MPO (wfrc_mpo) so both the vote
spine and the data-forward regional layers are demonstrable. Repo-wide reference
rows (entity, entity_relationship, crosswalks, caveat incl. '*' rows, build_info)
are copied whole. FTS: fts_minutes only (subset); the other FTS tables need the
full db. Regenerate after any federation whose slice-entity data changed:

  python3 scripts/build_sample_db.py [slug ...]
"""
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "gov.db")
OUT = os.path.join(ROOT, "gov-sample.db")
DEFAULT_SLICE = ["vineyard", "wfrc_mpo"]
COPY_WHOLE = {"entity", "entity_relationship", "motion_type_crosswalk",
              "body_crosswalk", "vote_values", "build_info"}


def main():
    slice_ = sys.argv[1:] or DEFAULT_SLICE
    if os.path.exists(OUT):
        os.remove(OUT)
    src = sqlite3.connect(f"file:{SRC}?mode=ro", uri=True)
    out = sqlite3.connect(OUT)
    ph = ",".join("?" * len(slice_))

    tables = src.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'fts_%'").fetchall()
    for name, sql in tables:
        out.execute(sql)
        cols = [r[1] for r in src.execute(f"PRAGMA table_info([{name}])")]
        if name in COPY_WHOLE or "city" not in cols:
            rows = src.execute(f"SELECT * FROM [{name}]").fetchall()
        else:
            rows = src.execute(
                f"SELECT * FROM [{name}] WHERE city IN ({ph}) OR city='*'",
                slice_).fetchall()
        if rows:
            out.executemany(
                f"INSERT INTO [{name}] VALUES ({','.join('?' * len(cols))})", rows)
        print(f"  {name}: {len(rows)}")
    for name, sql in src.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='view'").fetchall():
        out.execute(sql)
    out.execute("CREATE VIRTUAL TABLE fts_minutes USING fts5("
                "text, city UNINDEXED, dataset UNINDEXED, date UNINDEXED, "
                "path UNINDEXED)")
    n = 0
    for row in src.execute(
            f"SELECT text, city, dataset, date, path FROM fts_minutes "
            f"WHERE city IN ({ph})", slice_):
        out.execute("INSERT INTO fts_minutes VALUES (?,?,?,?,?)", row)
        n += 1
    print(f"  fts_minutes: {n}")
    out.execute("INSERT INTO build_info VALUES ('sample_note', "
                "'SAMPLE db — entities: %s; fts_minutes only; full data in gov.db')"
                % "+".join(slice_))
    out.commit()
    out.execute("VACUUM")
    out.close()
    mb = os.path.getsize(OUT) / 1e6
    print(f"Wrote {OUT} ({mb:.1f} MB, slice: {', '.join(slice_)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
