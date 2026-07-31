#!/usr/bin/env python3
"""Closing-pass step 4 — resolve ordinances/index.csv → enacting Council motion, ONLY where
the motion is uniquely identifiable.

Summit's tally-primary Council minutes DO print the ordinance number in the enacting motion
text ("Christopher Robinson made a motion to adopt Ordinance No. 962 ..."). For each
catalogued ordinance this fills `motion_id` (the per-county summit_county.db motion_id, which
the repo-root search-layer loader offsets by the entity fed_index) and `match_confidence`
ONLY when exactly one Council motion references that ordinance number in an ordinance context.
Ambiguous or absent (e.g. pre-2023 adoptions that predate the Granicus Council coverage floor,
or the two continuously-amended development CODES with no single enacting motion) stay BLANK —
never forced.

DERIVED + idempotent — rerun after build_db.py. Only motion_id/match_confidence are written;
every other column is preserved verbatim.
"""
import csv, os, re, sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
COUNTY = os.path.dirname(HERE)
DB = os.path.join(HERE, "summit_county.db")
IDX = os.path.join(COUNTY, "ordinances", "index.csv")


def main():
    db = sqlite3.connect(DB)
    council = db.execute(
        "SELECT m.motion_id, m.motion_text FROM motion m JOIN body b ON b.body_id=m.body_id "
        "WHERE b.kind='council'").fetchall()

    rows = list(csv.DictReader(open(IDX, encoding="utf-8")))
    cols = rows[0].keys() if rows else []
    linked = 0
    for r in rows:
        ono = (r.get("ordinance_no") or "").strip()
        r["motion_id"] = ""
        r["match_confidence"] = ""
        if not ono:
            continue
        # ordinance-number in an ordinance CONTEXT (avoids bare section-number collisions)
        pat = re.compile(r"\bordinance\s*(?:no\.?|#)?\s*" + re.escape(ono) + r"\b", re.I)
        hits = [mid for mid, txt in council if pat.search(txt or "")]
        if len(hits) == 1:
            r["motion_id"] = str(hits[0])
            r["match_confidence"] = "high"
            linked += 1
        # len!=1 → ambiguous or not in the Council coverage era → left blank (honest)

    with open(IDX, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(cols))
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print("ordinances catalogued: %d | uniquely motion-linked: %d" % (len(rows), linked))
    for r in rows:
        if r["motion_id"]:
            print("  Ord %-5s -> motion_id %s" % (r["ordinance_no"], r["motion_id"]))
    db.close()


if __name__ == "__main__":
    main()
