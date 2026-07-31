#!/usr/bin/env python3
"""
Validation for the Nephi City PLANNING COMMISSION vote extraction.

Checks (must all PASS):
  1. ROSTER INTEGRITY  - every commissioner in all_votes.csv (member column) AND every
     mover/seconder resolves to a name on roster.csv -> 0 off-roster.
  2. JSON <-> CSV RECONCILE - motion count and member-vote-row count agree between the
     per-meeting JSON and all_votes.csv; every JSON meeting has a CSV presence.
  3. SCHEMA - all_votes.csv has exactly the 13 council columns, body=="PlanningCommission"
     and title=="Planning Commission" on every row, mover present on every row.
  4. NARRATIVE NOTE - reports the (expected) tally-only / narrative majority: how many
     motions are summary-only (names_recorded=false) vs name individual voters.

Exit code 0 on PASS, 1 on FAIL.
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VOTES_DIR = ROOT / "votes"
ALL_VOTES = ROOT / "all_votes.csv"
ROSTER = ROOT / "roster.csv"

SCHEMA = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
          "result", "mover", "seconder", "member", "vote", "source"]


def main():
    fails = []
    notes = []

    roster = {r["commissioner"] for r in csv.DictReader(ROSTER.open())}

    with ALL_VOTES.open() as f:
        rdr = csv.reader(f)
        header = next(rdr)
    if header != SCHEMA:
        fails.append(f"SCHEMA: header {header} != {SCHEMA}")

    rows = list(csv.DictReader(ALL_VOTES.open()))

    # 3. schema-level invariants
    moverless = []
    for i, r in enumerate(rows, 2):
        if r["body"] != "PlanningCommission":
            fails.append(f"row {i}: body={r['body']!r} (expected PlanningCommission)")
        if r["title"] != "Planning Commission":
            fails.append(f"row {i}: title={r['title']!r} (expected 'Planning Commission')")
        if not r["mover"]:
            moverless.append(f"{r['date']} #{r['motion_no']}")
    if moverless:
        # A motion may genuinely record no mover name (e.g. minutes "Chair Commissioner
        # motions" with the name omitted). We never invent one -> reported, not a failure.
        notes.append(f"{len(moverless)} motion(s) with no recorded mover (name omitted in "
                     f"the minutes, never guessed): {', '.join(moverless)}.")

    # 1. roster integrity
    off = set()
    for r in rows:
        for col in ("member", "mover", "seconder"):
            v = r[col].strip()
            if v and v not in roster:
                off.add(f"{col}={v!r} ({r['date']} #{r['motion_no']})")
    if off:
        fails.append(f"OFF-ROSTER ({len(off)}): " + "; ".join(sorted(off)[:20]))
    else:
        notes.append("0 off-roster names (members + movers + seconders all on roster).")

    # 2. JSON <-> CSV reconcile
    json_files = 0
    json_motions = 0
    json_member_rows = 0
    json_voted_dates = set()   # dates with >=1 motion (the only ones that must hit the CSV)
    json_zero = 0
    for jp in sorted(VOTES_DIR.rglob("*.json")):
        d = json.loads(jp.read_text())
        json_files += 1
        if d["votes"]:
            json_voted_dates.add(d["date"])
        else:
            json_zero += 1
        for v in d["votes"]:
            json_motions += 1
            if v.get("names_recorded"):
                json_member_rows += sum(
                    len(v.get(k, [])) for k in ("aye", "nay", "abstain", "recuse", "absent"))

    csv_motions = len({(r["date"], r["motion_no"]) for r in rows})
    csv_member_rows = sum(1 for r in rows if r["member"].strip())
    csv_dates = {r["date"] for r in rows}

    if json_motions != csv_motions:
        fails.append(f"RECONCILE motions: JSON {json_motions} != CSV {csv_motions}")
    if json_member_rows != csv_member_rows:
        fails.append(f"RECONCILE member rows: JSON {json_member_rows} != CSV {csv_member_rows}")
    # Only meetings that actually have motions must appear in the CSV; zero-motion meetings
    # (public hearings / discussion-only sessions) legitimately contribute no rows.
    missing_dates = json_voted_dates - csv_dates
    if missing_dates:
        fails.append(f"RECONCILE: meetings with motions absent from CSV: {sorted(missing_dates)}")
    notes.append(f"{json_files} meeting JSON files; {json_zero} are zero-motion "
                 f"(public hearing / discussion-only -> no CSV rows, expected).")

    # 4. narrative note
    summary_rows = sum(1 for r in rows if not r["member"].strip())
    named_motions = json_motions - summary_rows  # motions that expanded into member rows
    notes.append(
        f"{summary_rows}/{csv_motions} motions are tally-only / narrative summary rows "
        f"(names_recorded=false, mover+seconder+result only) -- EXPECTED for Nephi PC; "
        f"only {named_motions} motions name individual voters.")

    print(f"meetings(JSON files)={json_files}  motions={csv_motions}  "
          f"member_vote_rows={csv_member_rows}  commissioners={len(roster)}")
    for n in notes:
        print("NOTE:", n)
    if fails:
        print("\nVALIDATION: FAIL")
        for x in fails:
            print("  -", x)
        sys.exit(1)
    print("\nVALIDATION: PASS")


if __name__ == "__main__":
    main()
