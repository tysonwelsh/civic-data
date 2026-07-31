#!/usr/bin/env python3
"""
extract_backfill_votes.py — integrate the recovered 2021-2022 West Jordan Planning
Commission minutes (../pmn_backfill/) into the structured all_votes.csv.

WHY
    The audited PC record (extract_votes.py) starts 2022-07-19 — the city's portal
    had no standalone PC minutes before that. Utah Public Notice DID, and 28
    standalone PC "Regular Meeting" minutes (2021-04-06 → 2022-07-05, pmn body 396)
    were recovered into ../pmn_backfill/. They are the SAME minutes format the
    audited extractor already parses, so this REUSES extract_votes.extract_meeting()
    over them and merges the result, tagged with provenance.

PROVENANCE (added to all_votes.csv, flows into the db)
    minutes      — audited PrimeGov minutes (extract_votes.py)
    pmn_minutes  — recovered from Utah Public Notice (this script)

    Like the audited WJ PC data, only NAMED rows are emitted (WJ PC is tally-only:
    the aye majority is never named, so all_votes.csv holds dissent/abstain/recuse/
    absent rows only). Tally-only recovered motions add no member rows — matching
    the city's own convention.

RUN (after extract_votes.py):
    python3 planning_commission/extract_votes.py
    python3 planning_commission/extract_backfill_votes.py
Idempotent: rebuilds the merged all_votes.csv from the canonical rows + a fresh
parse of pmn_backfill each run.
"""
import os
import csv
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PMN_INDEX = os.path.join(REPO, "pmn_backfill", "index.csv")
PMN_TEXT = os.path.join(REPO, "pmn_backfill", "text")
ALL_VOTES = os.path.join(HERE, "all_votes.csv")
ROSTER = os.path.join(HERE, "roster.csv")
REPORT = os.path.join(HERE, "votes", "_backfill_extract_report.txt")

sys.path.insert(0, HERE)
import extract_votes as ev  # reuse the audited WJ PC parser

CANON_PROVENANCE = "minutes"
BACKFILL_PROVENANCE = "pmn_minutes"
# recovered-minutes provenance keyed on the pmn_backfill index `source` column:
#   pmn           -> pmn_minutes    (Utah Public Notice attachment)
#   city_website  -> citysite_minutes (city CMS: assets.westjordan.utah.gov docs,
#                    discovered via the WordPress wjc/v1 data-meeting API)
SOURCE_PROVENANCE = {"pmn": "pmn_minutes", "city_website": "citysite_minutes"}
COLS = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
        "result", "mover", "seconder", "member", "vote", "source", "provenance"]


def main():
    if not os.path.exists(ALL_VOTES):
        sys.exit("run extract_votes.py first — canonical all_votes.csv is missing")
    canon_rows, canon_dates = [], set()
    with open(ALL_VOTES, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("provenance", "") in set(SOURCE_PROVENANCE.values()):
                continue                       # idempotent: drop prior backfill rows
            canon_dates.add(r["date"])
            canon_rows.append(r)

    # PC minutes in pmn_backfill (body 396), dates not already structured
    pc = []
    with open(PMN_INDEX, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if not r["title"].startswith("Planning Commission"):
                continue
            if r["date"] in canon_dates:
                continue
            pc.append(r)

    # roster.csv extension over the recovered span.
    #   extract_votes.py builds roster.csv from the AUDITED minutes only (min date
    #   2020-09-29). The recovered standalone PC minutes (2020-01-07 .. 2022-07-05,
    #   0 date-overlap with the audited index) name/seat the same commissioners
    #   EARLIER, so the audited roster's first_seen/last_seen/n_meetings are stale
    #   once the backfill is merged (validate_votes.py then flags out-of-range).
    #   Mirror extract_votes.py exactly: attendance (PRESENT headers) extends
    #   first_seen/last_seen AND increments n_meetings; any role appearance
    #   (mover/seconder/named dissent/abstain/recuse/absent) extends the span only.
    #   Idempotent: extract_votes.py rewrites roster.csv fresh (audited-only) each
    #   run; this re-reads it and folds the recovered meetings back in.
    roster = {}  # name -> [first_seen, last_seen, n_meetings]
    if os.path.exists(ROSTER):
        with open(ROSTER, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                roster[r["commissioner"]] = [r["first_seen"], r["last_seen"],
                                             int(r["n_meetings"])]

    def _extend(name, date, present):
        if not name:
            return
        if name not in roster:
            roster[name] = [date, date, 0]
        roster[name][0] = min(roster[name][0], date)
        roster[name][1] = max(roster[name][1], date)
        if present:
            roster[name][2] += 1

    back_rows = []
    parsed = motions = named_motions = 0
    missing = []
    for r in sorted(pc, key=lambda x: x["date"]):
        date = r["date"]
        fname = f"pc_{date}_{r['pmn_file_id']}.txt"
        path = os.path.join(PMN_TEXT, fname)
        if not os.path.exists(path):
            missing.append(fname)
            continue
        rel_source = f"pmn_backfill/text/{fname}"
        provenance = SOURCE_PROVENANCE.get(r.get("source", ""), BACKFILL_PROVENANCE)
        # attendance first (counted even for meetings that carry no extractable vote)
        for name in ev.parse_attendance(path):
            _extend(name, date, present=True)
        votes = ev.extract_meeting(path, rel_source)
        if not votes:
            continue
        parsed += 1
        year = date[:4]
        for v in votes:
            motions += 1
            if v["names_recorded"]:
                named_motions += 1
            # role appearances extend the tenure span (never n_meetings)
            for name in [v["mover"], v["seconder"], *v["aye"], *v["nay"],
                         *v["abstain"], *v["absent"], *v["recuse"]]:
                _extend(name, date, present=False)
            base = {
                "date": date, "year": year, "title": "Planning Commission",
                "body": "PlanningCommission", "motion_no": v["motion_no"],
                "motion": v["motion"], "motion_type": v["motion_type"],
                "result": v["result"], "mover": v["mover"], "seconder": v["seconder"],
                "source": rel_source, "provenance": provenance,
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
    out.sort(key=lambda r: (r["date"], int(r["motion_no"]), r.get("member", "")))
    with open(ALL_VOTES, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in out:
            w.writerow({c: r.get(c, "") for c in COLS})

    # roster.csv rewritten with the recovered span folded in (audited + recovered)
    with open(ROSTER, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["commissioner", "first_seen", "last_seen", "n_meetings"])
        for name in sorted(roster, key=lambda n: (roster[n][0], n)):
            fs, ls, n = roster[name]
            w.writerow([name, fs, ls, n])

    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("West Jordan PC backfill (pmn_backfill -> all_votes.csv)\n")
        f.write(f"recovered meetings parsed : {parsed}\n")
        f.write(f"recovered motions         : {motions} ({named_motions} name >=1 member)\n")
        f.write(f"recovered member rows     : {len(back_rows)}\n")
        f.write(f"canonical rows (minutes)  : {len(canon_rows)}\n")
        f.write(f"merged total rows         : {len(out)}\n")
        f.write(f"roster commissioners      : {len(roster)} "
                f"(first_seen/last_seen/n_meetings folded over recovered span)\n")
        if missing:
            f.write(f"MISSING text files        : {len(missing)}\n")
            for m in missing:
                f.write(f"    {m}\n")

    print(f"merged all_votes.csv: {len(canon_rows)} canonical + {len(back_rows)} recovered "
          f"(pmn_minutes / citysite_minutes) member rows; {parsed} meetings / {motions} motions "
          f"({named_motions} named). missing files: {len(missing)}")


if __name__ == "__main__":
    main()
