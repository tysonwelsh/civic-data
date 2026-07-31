#!/usr/bin/env python3
"""Load the Utah County development pipeline (development/applications.csv) into
utah_county.db and link each action to its Planning Commission motion.

Unlike Salt Lake County — where build_applications.py DERIVES applications.csv from a
Legistar matter stream — Utah County has no matter API. The land-use actions were
compiled by the development-module agent into development/applications.csv (32 rows,
county PC agenda items 2025-2026) with a blank motion_id. This closing pass:

  1. loads every action into the standard `application` table (a stable app_key), and
  2. links it to the enacting PC motion by (meeting_date, motion_no) WHERE THAT JOIN IS
     UNIQUE — writing motion_id back into development/applications.csv (the federated
     loader offsets it) AND setting motion.application_id on the county-local motion.

Never forces an ambiguous or absent join: rows with a blank motion_no (continued items
that carried no formal motion) stay unlinked with an empty motion_id — honest.

DERIVED + idempotent: clears the application table and resets motion.application_id on
each run, then reloads. Runs AFTER build_db.py + ingest_pc_votes.py (the PC motions must
exist to link against).
"""
import csv, os, sqlite3, hashlib
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
COUNTY = os.path.dirname(HERE)
DB = os.path.join(HERE, "utah_county.db")
APPS = os.path.join(COUNTY, "development", "applications.csv")
PC_BODY = "Planning Commission"


def app_key(r):
    h = hashlib.md5((r.get("title", "") or "").encode("utf-8")).hexdigest()[:8]
    return "UCDEV-%s-%s-%s" % (r.get("date", ""), (r.get("motion_no") or "x"), h)


def main():
    db = sqlite3.connect(DB)

    # ---- idempotent reset ----
    db.execute("DELETE FROM application")
    db.execute("UPDATE motion SET application_id=NULL, app_match_method='', app_confidence=''")

    body_row = db.execute("SELECT body_id FROM body WHERE name=?", (PC_BODY,)).fetchone()
    pc_body_id = body_row[0] if body_row else None

    # (date, motion_no) -> [motion_id] within the PC body
    lk = defaultdict(list)
    for mid, d, mno in db.execute(
            "SELECT m.motion_id, mt.meeting_date, m.motion_no FROM motion m "
            "JOIN meeting mt ON mt.meeting_id=m.meeting_id JOIN body b ON b.body_id=m.body_id "
            "WHERE b.name=?", (PC_BODY,)):
        lk[(d, str(mno))].append(mid)

    rows = list(csv.DictReader(open(APPS, encoding="utf-8")))
    fieldnames = rows[0].keys() if rows else []

    unique = ambiguous = nomotion = 0
    for i, r in enumerate(rows, start=1):
        key = app_key(r)
        db.execute("INSERT INTO application VALUES (?,?,?,?,?,?)",
                   ("utah_county", i, key, pc_body_id,
                    (r.get("applicant") or "").strip(), (r.get("dev_type") or "").strip()))
        mno = (r.get("motion_no") or "").strip()
        r["motion_id"] = ""     # reset (idempotent rewrite)
        if not mno:
            nomotion += 1
            continue
        mids = lk.get((r.get("date", ""), mno), [])
        if len(mids) == 1:
            mid = mids[0]
            r["motion_id"] = str(mid)
            db.execute("UPDATE motion SET application_id=?, app_match_method=?, app_confidence=? "
                       "WHERE motion_id=?", (i, "date_motion_no", "high", mid))
            unique += 1
        elif len(mids) > 1:
            ambiguous += 1     # never force
        else:
            nomotion += 1

    db.commit()

    # rewrite applications.csv with motion_id filled (all other columns preserved)
    with open(APPS, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(fieldnames))
        w.writeheader()
        w.writerows(rows)

    linked = db.execute("SELECT COUNT(*) FROM motion WHERE application_id IS NOT NULL").fetchone()[0]
    print("development/applications.csv loaded into utah_county.db:")
    print("  %d applications; motion links: unique=%d ambiguous=%d unlinked(no motion_no/absent)=%d"
          % (len(rows), unique, ambiguous, nomotion))
    print("  motions carrying application_id: %d" % linked)
    fk = db.execute("PRAGMA foreign_key_check").fetchall()
    print("  foreign_key_check: %d issues" % len(fk))
    db.close()


if __name__ == "__main__":
    main()
