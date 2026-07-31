#!/usr/bin/env python3
"""Date-collision detector (G8b, 2026-07-31): find meetings whose full motion-text
signature is IDENTICAL to another meeting of the same entity+body on a DIFFERENT
date — the fingerprint of a mis-dated duplicate ingest (filename date-format
misparse, approval-date-as-meeting-date, PMN re-posts). Read-only; run against
gov.db after any ingest wave and work each hit at the source documents.

Not every hit is a defect: two meetings CAN legitimately print identical motion
sets (e.g. bare "approve minutes + adjourn" sessions), so every hit needs source
verification before any fix (the 2026-07-31 triage confirmed midvale x4, magna
PC, weber 2021-06-01, holladay 2025-05-01 as real; see TODO G8).
"""
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "gov.db")
MIN_MOTIONS = 2   # 1-motion signatures collide constantly and honestly


def main():
    db = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    rows = db.execute("""
        WITH sig AS (
          SELECT m.city, b.name AS body, mt.meeting_date AS date,
                 COUNT(*) AS n_motions,
                 GROUP_CONCAT(m.motion_text, '␞') AS signature,
                 GROUP_CONCAT(DISTINCT m.source_file) AS sources
          FROM motion m
          JOIN meeting mt ON mt.meeting_id = m.meeting_id
          JOIN body b ON b.body_id = m.body_id
          GROUP BY m.city, b.name, mt.meeting_date
          HAVING n_motions >= ?
        )
        SELECT a.city, a.body, a.date, b.date, a.n_motions, a.sources, b.sources
        FROM sig a JOIN sig b
          ON a.city = b.city AND a.body = b.body
         AND a.signature = b.signature AND a.date < b.date
        ORDER BY a.city, a.date
    """, (MIN_MOTIONS,)).fetchall()
    if not rows:
        print("No same-signature different-date meeting pairs found "
              f"(min {MIN_MOTIONS} motions).")
        return 0
    print(f"{len(rows)} same-signature pair(s) — VERIFY EACH AT SOURCE before fixing:")
    for city, body, d1, d2, n, s1, s2 in rows:
        print(f"\n  {city} [{body}] {d1} <-> {d2}  ({n} motions)")
        print(f"    {d1}: {s1[:90]}")
        print(f"    {d2}: {s2[:90]}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
