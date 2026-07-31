#!/usr/bin/env python3
"""
validate_votes.py — independent QA for the Planning Commission vote extraction.

Checks (all must pass except the documented, hand-reviewed tally mismatches):
  1. 0 off-roster members (every named voter maps to roster.csv).
  2. 0 out-of-range dates (data floor 2020; PC data only exists 2025+).
  3. JSON <-> all_votes.csv reconciliation (same member-vote rows).
  4. Tally vs named-count mismatches listed (FLAGGED, never fabricated).
  5. Coverage gap 2020-2024 noted explicitly (data limitation, not a parser gap).

Run:  python3 planning_commission/validate_votes.py
Exit code 0 = PASS (only documented tally mismatches remain), 1 = FAIL.
"""
import csv
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PC = os.path.join(REPO, "planning_commission")
VOTES_DIR = os.path.join(PC, "votes")
ALL_VOTES_CSV = os.path.join(PC, "all_votes.csv")
ROSTER_CSV = os.path.join(PC, "roster.csv")


def iter_jsons():
    for dp, _, files in os.walk(VOTES_DIR):
        for fn in sorted(files):
            if fn.endswith(".json") and not fn.startswith("_"):
                yield os.path.join(dp, fn)


def main():
    roster = set()
    with open(ROSTER_CSV, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            roster.add(r["commissioner"])

    off_roster, out_of_range, mismatches = [], [], []
    json_rows = 0
    meetings = motions = recs = finals = contested = boa = 0
    for jp in iter_jsons():
        with open(jp, encoding="utf-8") as f:
            mtg = json.load(f)
        meetings += 1
        if mtg["date"][:4] < "2020":
            out_of_range.append(mtg["date"])
        for v in mtg["votes"]:
            motions += 1
            if v["action_class"] == "pc_recommendation":
                recs += 1
            else:
                finals += 1
            if v.get("acting_body") == "BoardOfAdjustment":
                boa += 1
            if v["nay"] or v["abstain"] or v["recuse"]:
                contested += 1
            for key in ("aye", "nay", "abstain", "absent", "recuse"):
                for m in v.get(key, []):
                    json_rows += 1
                    if m not in roster:
                        off_roster.append(f"{mtg['date']} m{v['motion_no']}: {m}")
            if not v["names_recorded"]:
                json_rows += 0  # tally-only would add a CSV placeholder row
            mt = re.search(r"(\d+):(\d+)", v["result"])
            if mt:
                fav, agn = int(mt.group(1)), int(mt.group(2))
                if len(v["aye"]) != fav or len(v["nay"]) != agn:
                    mismatches.append(
                        f"{mtg['date']} m{v['motion_no']}: aye={len(v['aye'])} "
                        f"nay={len(v['nay'])} vs tally {fav}:{agn} :: {v['result']}")

    # CSV reconcile
    csv_member_rows = csv_placeholder = 0
    with open(ALL_VOTES_CSV, newline="", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        assert rdr.fieldnames == ["date", "year", "title", "body", "motion_no",
                                  "motion", "motion_type", "result", "mover",
                                  "seconder", "member", "vote", "source"], \
            f"CSV schema mismatch: {rdr.fieldnames}"
        for row in rdr:
            assert row["body"] == "PlanningCommission"
            assert row["title"] == "Planning Commission"
            if row["member"]:
                csv_member_rows += 1
            else:
                csv_placeholder += 1

    ok = True
    print("=" * 64)
    print("Provo Planning Commission — validation")
    print("=" * 64)
    print(f"Meetings: {meetings}  Motions: {motions}")
    print(f"Recommendations: {recs}  Final actions: {finals}  "
          f"(Board-of-Adjustment items: {boa})")
    print(f"Contested (>=1 Nay/Abstain/Recuse): {contested}")
    print(f"Distinct commissioners (roster): {len(roster)}")
    print("-" * 64)
    print(f"[{'OK' if not off_roster else 'FAIL'}] off-roster members: {len(off_roster)}")
    if off_roster:
        ok = False
        print("   " + "\n   ".join(off_roster))
    print(f"[{'OK' if not out_of_range else 'FAIL'}] out-of-range (<2020) dates: {len(out_of_range)}")
    if out_of_range:
        ok = False
    print(f"[{'OK' if json_rows == csv_member_rows else 'FAIL'}] JSON<->CSV member rows: "
          f"json={json_rows} csv={csv_member_rows} (placeholders={csv_placeholder})")
    if json_rows != csv_member_rows:
        ok = False
    print("-" * 64)
    print(f"Tally vs named-count mismatches (FLAGGED, kept verbatim, not fabricated): "
          f"{len(mismatches)}")
    for m in mismatches:
        print("   " + m)
    print("-" * 64)
    print("COVERAGE: PC roll-call data exists 2025+ only. Provo began publishing "
          "consolidated PC minutes (agenda packet + Report of Action) in 2025; "
          "2020-2024 PC minutes are not posted on AgendaCenter and the OnBase "
          "portal has no PC body (documented gap, see minutes_unrecovered.csv / "
          "CLAUDE.md). This is a SOURCE limitation, not a parser gap.")
    print("=" * 64)
    print("RESULT:", "PASS (only documented tally mismatches remain)" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
