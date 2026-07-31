#!/usr/bin/env python3
"""
Standalone validator for the Planning Commission vote extraction.

Re-reads the produced artifacts (does NOT re-parse minutes) and checks:
  1. all_votes.csv schema (the 13 standard columns, plus the documented optional
     `provenance` 14th column once the pmn/citysite backfill is merged) + constants.
  2. Every commissioner in all_votes.csv is in roster.csv AND the meeting date
     falls within [first_seen, last_seen] — applied to ALL rows, audited and recovered.
  3. JSON <-> CSV reconciliation: the votes/ JSON dir holds only the AUDITED layer, so
     it reconciles against the audited CSV rows (provenance minutes / blank); the
     recovered backfill rows (provenance pmn_minutes / citysite_minutes, no JSON of
     their own — see extract_backfill_votes.py) are counted and reported separately.
  4. Partial roll-call tally consistency: named nays fit the printed tally
     (WJ PC names only the dissent side; the aye majority is never listed).
  5. result-string encoding is one of the four documented forms.

Exit code 0 = PASS, 1 = FAIL. Prints a summary.

Run:  python3 validate_votes.py
"""
import csv
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ALL_VOTES = os.path.join(ROOT, "all_votes.csv")
ROSTER = os.path.join(ROOT, "roster.csv")
VOTES_DIR = os.path.join(ROOT, "votes")

SCHEMA = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
          "result", "mover", "seconder", "member", "vote", "source"]
# recovered-minutes provenance values (merged by extract_backfill_votes.py); rows
# carrying these are NOT represented in the votes/ JSON dir.
RECOVERED_PROV = {"pmn_minutes", "citysite_minutes"}
RESULT_RE = re.compile(
    r"^(Positive recommendation|Negative recommendation)( \d+:\d+| \(unanimous\)| \(failed\))$"
    r"|^\d+:\d+ (Approved|Denied) \(Final Action\)$"
    r"|^(Approved|Denied) \(Final Action\) \((?:unanimous|failed)\)$"
    r"|^\d+:\d+ (Pass|Fail)$"
    r"|^Pass \(unanimous\)$|^Fail$|^Failed \(no second\)$")


def main():
    errors = []
    warnings = []

    # --- roster ---
    roster = {}
    for r in csv.DictReader(open(ROSTER)):
        roster[r["commissioner"]] = (r["first_seen"], r["last_seen"], int(r["n_meetings"]))

    # --- all_votes.csv ---
    rows = list(csv.DictReader(open(ALL_VOTES)))
    with open(ALL_VOTES) as f:
        header = f.readline().strip().split(",")
    if header != SCHEMA and header != SCHEMA + ["provenance"]:
        errors.append(f"all_votes.csv header != schema: {header}")
    recovered_rows = sum(1 for r in rows if r.get("provenance") in RECOVERED_PROV)
    audited_rows = len(rows) - recovered_rows

    for r in rows:
        if r["body"] != "PlanningCommission":
            errors.append(f"{r['date']} body != PlanningCommission: {r['body']}")
        if r["title"] != "Planning Commission":
            errors.append(f"{r['date']} title != Planning Commission: {r['title']}")
        mem = r["member"]
        if mem not in roster:
            errors.append(f"{r['date']} off-roster member: {mem}")
        else:
            fs, ls, _ = roster[mem]
            if not (fs <= r["date"] <= ls):
                errors.append(f"{r['date']} {mem} out of range [{fs}..{ls}]")
        if r["vote"] not in ("Aye", "Nay", "Abstain", "Absent", "Recuse"):
            errors.append(f"{r['date']} bad vote token: {r['vote']}")

    # --- JSON reconciliation ---
    json_member_rows = 0
    json_motions = 0
    files = [f for f in glob.glob(os.path.join(VOTES_DIR, "**", "*.json"), recursive=True)]
    for f in files:
        d = json.load(open(f))
        if d.get("body") != "PlanningCommission":
            errors.append(f"{f}: body != PlanningCommission")
        if d.get("title") != "Planning Commission":
            errors.append(f"{f}: title != Planning Commission")
        for v in d["votes"]:
            json_motions += 1
            if not RESULT_RE.match(v["result"]):
                errors.append(f"{d['date']} motion#{v['motion_no']} bad result form: '{v['result']}'")
            if v["aye"]:
                warnings.append(f"{d['date']} motion#{v['motion_no']} has named ayes "
                                f"(unexpected for WJ PC): {v['aye']}")
            # tally consistency for partial roll calls
            if v["names_recorded"]:
                m = re.search(r"(\d+):(\d+)", v["result"])
                if m:
                    ta, tb = int(m.group(1)), int(m.group(2))
                    if len(v["nay"]) > max(ta, tb):
                        errors.append(f"{d['date']} motion#{v['motion_no']} named nays "
                                      f"{len(v['nay'])} exceed tally {ta}:{tb}")
            for k in ("aye", "nay", "abstain", "absent", "recuse"):
                json_member_rows += len(v[k])

    if json_member_rows != audited_rows:
        errors.append(f"JSON member rows {json_member_rows} != audited CSV rows "
                      f"{audited_rows} (recovered {recovered_rows} excluded)")

    # --- report ---
    print("PLANNING COMMISSION VOTE VALIDATION")
    print("=" * 50)
    print(f"meetings (JSON files)   : {len(files)}")
    print(f"motions (JSON)          : {json_motions}")
    print(f"member-vote rows (CSV)  : {len(rows)}  "
          f"(audited {audited_rows} == JSON {json_member_rows}; recovered {recovered_rows})")
    print(f"distinct commissioners  : {len(roster)}")
    print(f"errors                  : {len(errors)}")
    print(f"warnings                : {len(warnings)}")
    for w in warnings:
        print("  WARN:", w)
    for e in errors:
        print("  ERROR:", e)
    if errors:
        print("\nRESULT: FAIL")
        return 1
    print("\nRESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
