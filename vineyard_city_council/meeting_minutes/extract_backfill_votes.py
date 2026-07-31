#!/usr/bin/env python3
"""
extract_backfill_votes.py — integrate the recovered standalone Vineyard RDA
(Redevelopment Agency) minutes from ../pmn_backfill/ into meeting_minutes/all_votes.csv.

WHY
    Vineyard's structured RDA record is tiny — 15 council-embedded motions
    (2024-08 → 2025-06). The RDA actually met as a standalone board for years;
    Utah Public Notice holds 43 standalone RDA minutes (2018-12 → 2026-05) that
    were recovered into ../pmn_backfill/ (status='recovered'). They are full
    roll-call minutes in Vineyard's own format, so this REUSES
    extract_votes.process_file(..., default_body='RDA') over them and merges the
    result, tagged with provenance.

PROVENANCE (added to all_votes.csv, flows into the db)
    minutes      — audited council/RDA/PC minutes (extract_votes.py)
    pmn_minutes  — recovered standalone RDA minutes (this script)

RUN (after extract_votes.py):
    python3 meeting_minutes/extract_votes.py
    python3 meeting_minutes/extract_backfill_votes.py
Idempotent: rebuilds the merged all_votes.csv from canonical rows + a fresh parse.
"""
import os
import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
PMN = REPO / "pmn_backfill"
ALL_VOTES = HERE / "all_votes.csv"
REPORT = HERE / "votes" / "_backfill_extract_report.txt"

sys.path.insert(0, str(HERE))
import extract_votes as ev  # reuse the audited Vineyard parser

CANON_PROVENANCE = "minutes"
BACKFILL_PROVENANCE = "pmn_minutes"
COLS = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
        "result", "mover", "seconder", "member", "vote", "source", "provenance"]


def main():
    if not ALL_VOTES.exists():
        sys.exit("run extract_votes.py first — canonical all_votes.csv is missing")
    canon_rows = []
    structured_rda_dates = set()
    with open(ALL_VOTES, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("provenance", "") == BACKFILL_PROVENANCE:
                continue                                   # idempotent
            canon_rows.append(r)
            if r["body"] == "RDA":
                structured_rda_dates.add(r["date"])        # dedup overlap

    recovered = []
    with open(PMN / "index.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["body"] != "RDA" or r.get("status") != "recovered":
                continue
            if not r.get("text_path", "").strip():
                continue
            if r["date"] in structured_rda_dates:          # already council-embedded
                continue
            recovered.append(r)

    back_rows = []
    parsed = motions = 0
    skipped_novote = []
    for r in sorted(recovered, key=lambda x: x["date"]):
        date = r["date"]
        path = PMN / r["text_path"]
        if not path.exists():
            continue
        votes = ev.process_file(path, default_body="RDA")
        if not votes:
            skipped_novote.append(r["text_path"])
            continue
        parsed += 1
        rel_source = f"pmn_backfill/{r['text_path']}"
        for v in votes:
            motions += 1
            base = {
                "date": date, "year": date[:4], "title": "Vineyard Redevelopment Agency",
                "body": v["body"], "motion_no": v["motion_no"], "motion": v["motion"],
                "motion_type": v["motion_type"], "result": v["result"],
                "mover": v["mover"], "seconder": v["seconder"],
                "source": rel_source, "provenance": BACKFILL_PROVENANCE,
            }
            for key, vote in (("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
                              ("absent", "Absent"), ("recuse", "Recuse")):
                for member in v[key]:
                    back_rows.append(dict(base, member=member, vote=vote))

    out = []
    for r in canon_rows:
        r = dict(r)
        if not r.get("provenance"):
            r["provenance"] = CANON_PROVENANCE
        out.append(r)
    out += back_rows
    out.sort(key=lambda r: (r["date"], r["body"], int(r["motion_no"]), r.get("member", "")))
    with open(ALL_VOTES, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in out:
            w.writerow({c: r.get(c, "") for c in COLS})

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("Vineyard RDA backfill (pmn_backfill -> meeting_minutes/all_votes.csv)\n")
        f.write(f"recovered RDA meetings parsed : {parsed}\n")
        f.write(f"recovered RDA motions         : {motions}\n")
        f.write(f"recovered member rows         : {len(back_rows)}\n")
        f.write(f"canonical rows (minutes)      : {len(canon_rows)}\n")
        f.write(f"merged total rows             : {len(out)}\n")
        f.write(f"parsed-to-zero-vote files     : {len(skipped_novote)}\n")
        for s in skipped_novote:
            f.write(f"    novote: {s}\n")

    print(f"merged all_votes.csv: {len(canon_rows)} canonical + {len(back_rows)} recovered "
          f"(pmn_minutes) rows; {parsed} RDA meetings / {motions} motions; "
          f"{len(skipped_novote)} no-vote files")


if __name__ == "__main__":
    main()
