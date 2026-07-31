#!/usr/bin/env python3
"""
extract_backfill_votes.py — integrate the recovered Riverton PLANNING COMMISSION
minutes from ../pmn_backfill/ into planning_commission/all_votes.csv.

WHY
    The pmn_backfill diff (2026-07-13) recovered 2 PC meetings the audited layer
    was missing:
      - 2023-11-09 — Granicus-only (PMN never carried its minutes; fetched from
        rivertoncity.granicus.com DocumentViewer, pdftotext -layout).
      - 2026-06-25 — a PMN-listed meeting newer than the audited harvest.
    Same clerk grammar the audited PC parser reads (named roll call ONLY on
    divided votes; "unanimous consent" prints no names — the honest tally-only
    convention is preserved: the majority is NEVER guessed), so this REUSES
    extract_votes.parse_meeting(...) over the text sidecars and merges the
    result, tagged with provenance.

NOTE  roster.csv (meetings_present / vote_rows) is built by the audited
    extract_votes.py from the minutes_index series only; these two backfill
    meetings are not counted there (documented, not a loss of vote data).

PROVENANCE (trailing 14th all_votes.csv column, flows into the db)
    minutes      — audited PC minutes (extract_votes.py)
    pmn_minutes  — recovered meetings (this script)

RUN (after extract_votes.py):
    python3 planning_commission/extract_votes.py
    python3 planning_commission/extract_backfill_votes.py
Idempotent: rebuilds the merged all_votes.csv from canonical rows + a fresh parse.
"""
import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
PMN = REPO / "pmn_backfill"
ALL_VOTES = HERE / "all_votes.csv"
REPORT = HERE / "votes" / "_backfill_extract_report.txt"

sys.path.insert(0, str(HERE))
import extract_votes as ev  # reuse the audited Riverton PC parser

CANON_PROVENANCE = "minutes"
BACKFILL_PROVENANCE = "pmn_minutes"
BODY = "PlanningCommission"
COLS = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
        "result", "mover", "seconder", "member", "vote", "source", "provenance"]


def main():
    if not ALL_VOTES.exists():
        sys.exit("run extract_votes.py first — canonical all_votes.csv is missing")
    canon_rows, structured = [], set()
    with open(ALL_VOTES, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("provenance", "") == BACKFILL_PROVENANCE:
                continue                                    # idempotent
            canon_rows.append(r)
            structured.add(r["date"])

    recovered = []
    with open(PMN / "index.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["body"] != BODY:
                continue
            if r["date"] in structured:                     # already audited
                continue
            recovered.append(r)

    back_rows = []
    parsed = motions = 0
    for r in sorted(recovered, key=lambda x: x["date"]):
        stem = Path(r["path"]).stem
        path = PMN / "text" / f"{stem}.txt"
        if not path.exists():
            print(f"MISSING text sidecar: {path}", file=sys.stderr)
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        votes = ev.parse_meeting(text)
        for k, v in enumerate(votes, start=1):
            v["motion_no"] = k
        if not votes:
            continue
        parsed += 1
        rel_source = f"pmn_backfill/text/{stem}.txt"
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
        f.write("Riverton PC backfill (pmn_backfill -> planning_commission/all_votes.csv)\n")
        f.write(f"recovered meetings parsed : {parsed}\n")
        f.write(f"recovered motions         : {motions}\n")
        f.write(f"recovered rows            : {len(back_rows)}\n")
        f.write(f"canonical rows            : {len(canon_rows)}\n")
        f.write(f"merged total rows         : {len(out)}\n")

    print(f"merged all_votes.csv: {len(canon_rows)} canonical + {len(back_rows)} recovered "
          f"(pmn_minutes) rows; {parsed} PC meetings / {motions} motions")

    if ev.UNKNOWN_SURNAMES:
        print("WARNING unknown surnames (not in CANON, dropped):",
              dict(sorted(ev.UNKNOWN_SURNAMES.items(), key=lambda x: -x[1])),
              file=sys.stderr)


if __name__ == "__main__":
    main()
