#!/usr/bin/env python3
"""
Independent validator for the St. George Planning Commission vote extraction.

Cross-checks (does NOT re-parse the minutes; it audits the emitted artifacts):

  1. Every `member` in all_votes.csv is on roster.csv          -> 0 off-roster
  2. Every member-vote falls within that commissioner's
     [first_seen, last_seen] roster span                        -> out-of-range list
  3. JSON <-> CSV reconcile: the per-meeting JSON member-vote
     counts sum to exactly the all_votes.csv row count
  4. Per-year commissioner sets are a subset of the roster
  5. result-string contract sanity (recommendation vs final action vs
     procedural) + PMN-vs-Revize parse-quality breakdown

Exit code 0 = PASS, 1 = FAIL. Writes the same summary to stdout.
"""

import csv
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ALL_VOTES_CSV = os.path.join(HERE, "all_votes.csv")
ROSTER_CSV = os.path.join(HERE, "roster.csv")
VOTES_DIR = os.path.join(HERE, "votes")
INDEX_CSV = os.path.join(HERE, "minutes_index.csv")


def load_roster():
    roster = {}
    with open(ROSTER_CSV, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            roster[r["commissioner"]] = (r["first_seen"], r["last_seen"],
                                         int(r["n_meetings"]))
    return roster


def load_source_format():
    fmt = {}
    with open(INDEX_CSV, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            fmt[r["path"]] = r.get("source", "")
    return fmt


def main():
    roster = load_roster()
    src_fmt = load_source_format()
    fails = []
    warns = []

    # --- load all_votes.csv ---
    csv_rows = []
    with open(ALL_VOTES_CSV, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            csv_rows.append(r)

    # body/title invariants
    bad_body = sum(1 for r in csv_rows if r["body"] != "PlanningCommission")
    bad_title = sum(1 for r in csv_rows if r["title"] != "Planning Commission")
    if bad_body:
        fails.append(f"{bad_body} rows with body != PlanningCommission")
    if bad_title:
        fails.append(f"{bad_title} rows with title != 'Planning Commission'")

    # 1) off-roster members
    off_roster = {}
    for r in csv_rows:
        if r["member"] not in roster:
            off_roster[r["member"]] = off_roster.get(r["member"], 0) + 1
    if off_roster:
        fails.append(f"off-roster members: {off_roster}")

    # 2) out-of-range votes
    out_of_range = []
    for r in csv_rows:
        m = r["member"]
        if m not in roster:
            continue
        first, last, _ = roster[m]
        if r["date"] < first or r["date"] > last:
            out_of_range.append((r["date"], m, f"[{first}..{last}]"))
    # dedupe
    out_of_range = sorted(set(out_of_range))

    # 3) JSON <-> CSV reconcile
    json_member_rows = 0
    json_motions = 0
    json_meetings = 0
    recs = finals = procs = contested = tally_only = 0
    for f in glob.glob(os.path.join(VOTES_DIR, "**", "*.json"), recursive=True):
        d = json.load(open(f, encoding="utf-8"))
        json_meetings += 1
        for v in d["votes"]:
            json_motions += 1
            nrows = (len(v["aye"]) + len(v["nay"]) + len(v["abstain"])
                     + len(v["absent"]) + len(v["recuse"]))
            json_member_rows += nrows
            if not v["names_recorded"]:
                tally_only += 1
            if v["nay"] or v["abstain"] or v["recuse"]:
                contested += 1
            rl = v["result"].lower()
            if "recommend" in rl:
                recs += 1
            elif "final action" in rl:
                finals += 1
            else:
                procs += 1
    if json_member_rows != len(csv_rows):
        fails.append(f"JSON member rows ({json_member_rows}) != CSV rows "
                     f"({len(csv_rows)})")

    # 4) per-year commissioner subset of roster
    per_year = {}
    for r in csv_rows:
        per_year.setdefault(r["year"], set()).add(r["member"])
    for y, members in sorted(per_year.items()):
        bad = members - set(roster)
        if bad:
            fails.append(f"{y}: members off roster {bad}")

    # 5) PMN vs Revize quality
    by_fmt = {"pmn": {"meetings": set(), "rows": 0},
              "revize": {"meetings": set(), "rows": 0}}
    for r in csv_rows:
        f = src_fmt.get(r["source"], "")
        if f in by_fmt:
            by_fmt[f]["meetings"].add(r["source"])
            by_fmt[f]["rows"] += 1

    status = "PASS" if not fails else "FAIL"
    print("St. George Planning Commission — validation")
    print("=" * 56)
    print(f"STATUS: {status}")
    print(f"roster commissioners: {len(roster)}")
    print(f"meetings (json): {json_meetings}")
    print(f"motions (json): {json_motions}")
    print(f"member-vote rows: csv={len(csv_rows)} json={json_member_rows}")
    print(f"recommendations={recs} final_actions={finals} procedural={procs}")
    print(f"contested={contested} tally_only_motions={tally_only}")
    print(f"off-roster members: {len(off_roster)}")
    print(f"out-of-range votes: {len(out_of_range)}")
    print("PMN  : rows={} meetings={}".format(
        by_fmt["pmn"]["rows"], len(by_fmt["pmn"]["meetings"])))
    print("Revize: rows={} meetings={}".format(
        by_fmt["revize"]["rows"], len(by_fmt["revize"]["meetings"])))
    print("-" * 56)
    if out_of_range:
        print("OUT OF RANGE (first 20):")
        for d, m, span in out_of_range[:20]:
            print(f"  {d} {m} {span}")
    if fails:
        print("FAILURES:")
        for f in fails:
            print("  " + f)
    if warns:
        print("WARNINGS:")
        for w in warns:
            print("  " + w)

    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
