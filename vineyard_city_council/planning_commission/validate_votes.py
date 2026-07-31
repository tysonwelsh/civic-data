#!/usr/bin/env python3
"""Validate the Planning Commission vote extraction. Writes votes/_validation_report.txt.

Checks:
  1. Roll-call tally: for names_recorded motions whose `result` carries an explicit
     numeric N:N, the N:N must match the named aye/nay counts (abstains tolerated on the
     'no' side). Mismatches are listed with file + both numbers; a source typo is FLAGGED,
     not fixed (cardinal rule).
  2. Roster integrity: every commissioner observed in a vote is on roster.csv, and the
     vote's date lies within that commissioner's [first_seen, last_seen] tenure range.
  3. JSON <-> all_votes.csv reconciliation (member-vote row counts agree).
  4. Tally-only motions (names_recorded=false) are counted/listed as expected.
"""
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VOTES_DIR = ROOT / "votes"
ROSTER_CSV = ROOT / "roster.csv"
ALL_VOTES_CSV = ROOT / "all_votes.csv"
REPORT = VOTES_DIR / "_validation_report.txt"


def parse_tally(result):
    m = re.search(r"(\d+)\s*:\s*(\d+)", result)
    return (int(m.group(1)), int(m.group(2))) if m else None


def main():
    roster = {}
    with ROSTER_CSV.open() as f:
        for r in csv.DictReader(f):
            roster[r["commissioner"]] = (r["first_seen"], r["last_seen"])

    files = sorted(p for p in VOTES_DIR.rglob("*.json") if not p.name.startswith("_"))
    lines = []
    motions = member_rows = mismatches = tally_only = 0
    off_roster = out_of_range = 0
    contested = recommendations = final_actions = procedural = 0

    for jf in files:
        d = json.loads(jf.read_text())
        date = d["date"]
        for v in d["votes"]:
            motions += 1
            res = v["result"]
            if "recommend" in res.lower():
                recommendations += 1
            elif "(Final Action)" in res:
                final_actions += 1
            else:
                procedural += 1
            aye, nay, ab = len(v["aye"]), len(v["nay"]), len(v["abstain"])
            member_rows += aye + nay + ab + len(v["absent"]) + len(v["recuse"])
            if v["nay"] or v["abstain"]:
                contested += 1
            if not v["names_recorded"]:
                tally_only += 1
            else:
                tally = parse_tally(res)
                if tally and not (tally[0] == aye and tally[1] in (nay, nay + ab)):
                    mismatches += 1
                    lines.append(f"TALLY_MISMATCH {date} m{v['motion_no']}: result "
                                 f"'{res}' stated {tally[0]}:{tally[1]} vs named "
                                 f"aye={aye} nay={nay} abstain={ab}  src={jf.name}")
            # roster checks
            for k in ("aye", "nay", "abstain", "absent", "recuse"):
                for nm in v[k]:
                    if nm not in roster:
                        off_roster += 1
                        lines.append(f"OFF_ROSTER {date} m{v['motion_no']}: {nm}  src={jf.name}")
                        continue
                    lo, hi = roster[nm]
                    if not (lo <= date <= hi):
                        out_of_range += 1
                        lines.append(f"OUT_OF_RANGE {date} m{v['motion_no']}: {nm} "
                                     f"(tenure {lo}..{hi})  src={jf.name}")

    # JSON <-> CSV reconcile
    with ALL_VOTES_CSV.open() as f:
        csv_rows = sum(1 for _ in csv.DictReader(f))
    reconcile = "OK" if csv_rows == member_rows else f"MISMATCH json={member_rows} csv={csv_rows}"

    status = ("PASS" if (mismatches == 0 and off_roster == 0 and out_of_range == 0
                         and reconcile == "OK") else "FAIL")
    header = [
        "VINEYARD PLANNING COMMISSION — VOTE EXTRACTION VALIDATION",
        "=" * 60,
        f"status: {status}",
        f"meetings (json): {len(files)}",
        f"motions: {motions}",
        f"  recommendations: {recommendations}  final_actions: {final_actions}  "
        f"procedural: {procedural}",
        f"member-vote rows: {member_rows}  (csv reconcile: {reconcile})",
        f"contested (any nay/abstain): {contested}",
        f"tally-only motions (names_recorded=false): {tally_only}",
        f"tally mismatches: {mismatches}",
        f"off-roster commissioners: {off_roster}",
        f"out-of-range votes: {out_of_range}",
        "",
        "Expected tally-only meetings: motions recorded only as 'ALL WERE IN FAVOR' /",
        "'THE MOTION CARRIED/PASSED UNANIMOUSLY' with NO per-member name list keep empty",
        "member lists and N:N=0:0 (count not stated in the source — never invented).",
        "",
        "DETAIL:",
        "-" * 60,
    ]
    REPORT.write_text("\n".join(header + (lines or ["(none)"])) + "\n", encoding="utf-8")
    print("\n".join(header[:13]))
    print(f"detail rows: {len(lines)} (see {REPORT})")


if __name__ == "__main__":
    main()
