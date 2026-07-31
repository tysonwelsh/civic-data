#!/usr/bin/env python3
"""
extract_backfill_votes.py — integrate the recovered 2020 (Jan-Aug) South Jordan
City Council minutes from ../pmn_backfill/ into all_votes.csv.

WHY
    SJ's structured council record starts 2020-08-18 (no portal retains earlier
    minutes). Utah Public Notice DID: 13 council minutes across 8 dates (2020 Jan-Jul
    + a 2023-01-24 budget meeting) were recovered into ../pmn_backfill/, filling the
    documented 2020 Jan-Jul gap. Same minutes format the audited parser reads, so this
    REUSES parse_meeting(load_lines(...)) over them and merges, tagged with provenance.

PROVENANCE  minutes (audited) | pmn_minutes (recovered, this script)
    SJ records narrative tallies (majority unnamed) — recovered rows are the named
    dissent/absent rows + one placeholder row per tally-only motion, exactly as the
    audited data does. body (Council/RDA/MBA) is detected by parse_meeting itself.

RUN (after extract_votes.py):
    python3 meeting_minutes/extract_votes.py
    python3 meeting_minutes/extract_backfill_votes.py
Idempotent.
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
import extract_votes as ev

CANON_PROVENANCE = "minutes"
BACKFILL_PROVENANCE = "pmn_minutes"
COLS = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
        "result", "mover", "seconder", "member", "vote", "source", "provenance"]


def main():
    if not ALL_VOTES.exists():
        sys.exit("run extract_votes.py first")
    canon_rows, council_dates = [], set()
    with open(ALL_VOTES, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("provenance", "") == BACKFILL_PROVENANCE:
                continue
            canon_rows.append(r)
            council_dates.add(r["date"])

    recovered = []
    with open(PMN / "index.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["date"] in council_dates:          # already structured on that date
                continue
            recovered.append(r)

    back_rows = []
    parsed = motions = 0
    for r in sorted(recovered, key=lambda x: (x["date"], x.get("text_path", ""))):
        tp = r.get("text_path", "")
        path = PMN / tp if tp else None
        if not path or not path.exists():
            continue
        votes = ev.parse_meeting(ev.load_lines(path))
        for k, v in enumerate(votes, start=1):
            v["motion_no"] = k
        if not votes:
            continue
        parsed += 1
        rel_source = f"pmn_backfill/{tp}"
        for v in votes:
            motions += 1
            base = {
                "date": r["date"], "year": r["date"][:4], "title": r["title"],
                "body": v["body"], "motion_no": v["motion_no"], "motion": v["motion"],
                "motion_type": v["motion_type"], "result": v["result"],
                "mover": v.get("mover") or "", "seconder": v.get("seconder") or "",
                "source": rel_source, "provenance": BACKFILL_PROVENANCE,
            }
            emitted = False
            for key, vote in (("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
                              ("absent", "Absent"), ("recuse", "Recuse")):
                for member in v.get(key, []):
                    back_rows.append(dict(base, member=member, vote=vote))
                    emitted = True
            if not emitted:
                back_rows.append(dict(base, member="", vote=""))

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
        f.write("South Jordan 2020 council backfill (pmn_backfill -> all_votes.csv)\n")
        f.write(f"recovered meetings parsed : {parsed}\n")
        f.write(f"recovered motions         : {motions}\n")
        f.write(f"recovered rows            : {len(back_rows)}\n")
        f.write(f"canonical rows            : {len(canon_rows)}\n")
        f.write(f"merged total rows         : {len(out)}\n")

    print(f"merged all_votes.csv: {len(canon_rows)} canonical + {len(back_rows)} recovered "
          f"(pmn_minutes) rows; {parsed} meetings / {motions} motions")


if __name__ == "__main__":
    main()
