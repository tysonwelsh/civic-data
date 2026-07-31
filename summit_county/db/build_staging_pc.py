#!/usr/bin/env python3
"""Closing-pass step 1 — transform the land_use/ Planning-Commission CSVs into the
db/staging_pc/ shape that build_db.py appends AFTER db/staging/ (Council).

Summit's two Planning Commissions (Snyderville Basin PC, Eastern Summit County PC) were
extracted by the land_use module into flat CSVs (motions_tally.csv = every PC motion,
tally-primary; all_votes.csv = the named rows on divided votes). This script rewrites them
into the SAME staging schema as the Council prose extractor (meetings.csv / motions.csv /
votes.csv) so build_db.py folds the PC into summit_county.db with HIGHER motion_ids —
Council ids (1..1820) never renumber (build_db reads db/staging/ first).

PC synthetic clip_ids live in a HIGH band (100001+) so they can never collide with the
Granicus Council clip_ids (max 1394); build_db keys meetings by clip_id alone.

DERIVED + idempotent — rerun after any land_use re-extraction; never hand-edit staging_pc/.
"""
import csv, os

HERE = os.path.dirname(os.path.abspath(__file__))
COUNTY = os.path.dirname(HERE)
LU = os.path.join(COUNTY, "land_use")
OUT = os.path.join(HERE, "staging_pc")
CLIP_BASE = 100001  # high band — never collides with Council Granicus clip_ids (max 1394)


def rd(name):
    return list(csv.DictReader(open(os.path.join(LU, name), encoding="utf-8")))


def main():
    os.makedirs(OUT, exist_ok=True)
    idx = rd("minutes_index.csv")
    motions = rd("motions_tally.csv")
    votes = rd("all_votes.csv")

    # meetings we can seat motions on: only those whose minutes text was extracted.
    # (14 minutes_exist_text_unrecovered rows stay honest gaps in minutes_index.csv.)
    meet_rows = [r for r in idx if r["minutes_status"] == "text_extracted"]

    # stable synthetic clip_id per (date, body_slug), deterministic sort
    keys = sorted({(r["date"], r["body_slug"]) for r in meet_rows})
    clip = {k: CLIP_BASE + i for i, k in enumerate(keys)}

    # every motion/vote meeting must be a seatable (text_extracted) meeting
    mkeys = {(r["date"], r["body_slug"]) for r in motions}
    missing = [k for k in mkeys if k not in clip]
    assert not missing, "motions reference non-text_extracted meetings: %r" % missing[:5]

    # meetings.csv
    with open(os.path.join(OUT, "meetings.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["clip_id", "date", "body", "meeting_type", "source_file", "minutes_status"])
        for r in meet_rows:
            k = (r["date"], r["body_slug"])
            w.writerow([clip[k], r["date"], r["body"], "Planning Commission",
                        r["md_path"], "final"])

    # motions.csv  (result_raw = verbatim tally; outcome = Pass/Fail/'' ; names_recorded 1/0)
    src_of = {(r["date"], r["body_slug"]): r["md_path"] for r in meet_rows}
    with open(os.path.join(OUT, "motions.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["clip_id", "date", "body", "motion_no", "motion_text", "motion_type",
                    "result_raw", "outcome", "mover", "seconder", "aye", "nay",
                    "names_recorded", "source_file"])
        for r in sorted(motions, key=lambda x: (x["date"], x["body_slug"], int(x["motion_no"]))):
            k = (r["date"], r["body_slug"])
            nr = 1 if r["names_recorded"].strip().lower() == "true" else 0
            w.writerow([clip[k], r["date"], r["body"], r["motion_no"], r["motion"], "",
                        r["tally"], r["result"], r["mover"], r["seconder"],
                        r["yes"], r["no"], nr, src_of[k]])

    # votes.csv  (named rows on divided votes only)
    with open(os.path.join(OUT, "votes.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["clip_id", "motion_no", "member", "vote_value"])
        for r in votes:
            k = (r["date"], r["body_slug"])
            if k not in clip:
                continue
            w.writerow([clip[k], r["motion_no"], r["member"], r["vote"]])

    print("staging_pc built: %d meetings, %d motions, %d named vote rows" %
          (len(meet_rows), len(motions), len(votes)))


if __name__ == "__main__":
    main()
