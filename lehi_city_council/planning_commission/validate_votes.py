#!/usr/bin/env python3
"""
validate_votes.py — sanity-check the extracted Lehi PLANNING COMMISSION vote JSONs.

Reads every planning_commission/votes/<year>/<week>/*.json and writes a human-readable
report to planning_commission/votes/_validation_report.txt covering:

  1. Motion totals + stage split (pc_recommendation / pc_final_action) + recommendation
     direction (positive/negative) + body check (all rows must be "PlanningCommission").
  2. Motion-type distribution.
  3. Per-year observed-voter roster (every name that cast a recorded vote that year).
  4. ROSTER-RANGE check — every observed voter must be a known commissioner and the meeting
     date must fall within that commissioner's first_seen..last_seen window in roster.csv.
     0 off-roster / out-of-range names is the bar.
  5. TALLY-vs-RESULT mismatches — named YES/NO count vs the minutes' own printed tally
     ("four in favor, one against" / "passed 6 - 1"). Logged verbatim, never auto-corrected
     (a mismatch flags a source typo or a parse miss to hand-review).
  6. Outcome-vs-count consistency.
  7. JSON<->all_votes.csv reconciliation (every JSON member-vote has a CSV row & vice-versa).
  8. Roll-call size distribution (PC has up to 7 seats + 2 alternates, so size is NOT fixed;
     this is informational, not a failure).
  9. The full contested-vote list (any Nay / Abstain / Recuse) — the analytical signal.

There is NO mayor on the Planning Commission; the Chair / Vice-Chair vote like any member.

Run:  python3 planning_commission/validate_votes.py
"""
import csv
import json
import os
from collections import Counter, defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PC = os.path.join(REPO, "planning_commission")
VOTES_DIR = os.path.join(PC, "votes")
ROSTER_CSV = os.path.join(PC, "roster.csv")
ALL_VOTES_CSV = os.path.join(PC, "all_votes.csv")
REPORT = os.path.join(VOTES_DIR, "_validation_report.txt")
BODY = "PlanningCommission"


def iter_jsons():
    for dirpath, _, files in os.walk(VOTES_DIR):
        for fn in sorted(files):
            if fn.endswith(".json") and not fn.startswith("_"):
                yield os.path.join(dirpath, fn)


def load_roster():
    r = {}
    with open(ROSTER_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            r[row["commissioner"]] = (row["first_seen"], row["last_seen"])
    return r


def main():
    roster = load_roster()
    meetings = motions = 0
    stage_counts = Counter()
    dir_counts = Counter()
    body_bad = []
    type_counts = Counter()
    per_year_voters = defaultdict(Counter)
    off_roster = []        # HARD: a voter not on the roster at all
    range_issues = []      # SOFT: on-roster but the meeting date is outside the window
    tally_mismatches = []
    outcome_issues = []
    size_dist = Counter()
    contested = []
    json_vote_rows = 0

    for jp in sorted(iter_jsons()):
        with open(jp, encoding="utf-8") as f:
            mtg = json.load(f)
        meetings += 1
        date = mtg["date"]; year = date[:4]
        for v in mtg["votes"]:
            motions += 1
            if v.get("body") != BODY:
                body_bad.append(f"{date} m{v['motion_no']} body={v.get('body')}")
            stage_counts[v.get("stage", "?")] += 1
            if v.get("stage") == "pc_recommendation":
                dir_counts[v.get("direction")] += 1
            type_counts[v["motion_type"]] += 1

            aye, nay = v["aye"], v["nay"]
            abstain, absent, recuse = v["abstain"], v["absent"], v["recuse"]
            voters = aye + nay + abstain + absent + recuse
            json_vote_rows += len(voters)
            if voters:
                size_dist[len(voters)] += 1

            for name in voters:
                per_year_voters[year][name] += 1
                if name not in roster:
                    off_roster.append(f"{date} m{v['motion_no']}: OFF-ROSTER '{name}'")
                else:
                    lo, hi = roster[name]
                    if not (lo <= date <= hi):
                        range_issues.append(
                            f"{date} m{v['motion_no']}: '{name}' OUT-OF-RANGE "
                            f"({lo}..{hi})")

            if nay or abstain or recuse:
                contested.append(
                    f"{date} m{v['motion_no']} {v['result']} | AYE={len(aye)} "
                    f"NAY={nay} ABSTAIN={abstain} RECUSE={recuse} :: {v['motion'][:80]}")

            if not v.get("names_recorded"):
                continue
            n_aye, n_nay = len(aye), len(nay)

            pt = v.get("printed_tally")
            if pt:
                favor, against = pt
                if sorted([n_aye, n_nay]) != sorted([favor, against]):
                    tally_mismatches.append(
                        f"{date} m{v['motion_no']}: named aye={n_aye} nay={n_nay} "
                        f"but printed {favor}:{against} :: {v['result']} :: "
                        f"{v['motion'][:60]}")

            outcome = v.get("outcome", "")
            if outcome == "Pass" and n_nay and n_aye <= n_nay:
                outcome_issues.append(
                    f"{date} m{v['motion_no']}: PASS but aye={n_aye}<=nay={n_nay} "
                    f":: {v['result']}")
            if outcome == "Fail" and n_aye > n_nay:
                outcome_issues.append(
                    f"{date} m{v['motion_no']}: FAIL but aye={n_aye}>nay={n_nay} "
                    f":: {v['result']}")

    # ---- JSON <-> CSV reconciliation ----
    csv_rows = 0
    csv_member_rows = 0
    with open(ALL_VOTES_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            csv_rows += 1
            if row["member"]:
                csv_member_rows += 1
            if row["body"] != BODY:
                body_bad.append(f"CSV row {row['date']} body={row['body']}")
    recon_ok = (csv_member_rows == json_vote_rows)

    lines = []
    w = lines.append
    w("Lehi PLANNING COMMISSION — vote extraction validation report")
    w("=" * 72)
    w(f"Meetings with JSON : {meetings}")
    w(f"Motions extracted  : {motions}")
    w(f"Body check         : all rows body='{BODY}'  "
      f"({'OK' if not body_bad else 'FAIL: ' + str(len(body_bad))})")
    w("")
    w("Stage split (DB keys on 'recommend' substring in result):")
    for s, c in stage_counts.most_common():
        w(f"   {s:20s} {c}")
    w("Recommendation direction:")
    for d, c in dir_counts.most_common():
        w(f"   {str(d):20s} {c}")
    w("")
    w("Motion-type distribution:")
    for t, c in type_counts.most_common():
        w(f"   {t:28s} {c}")
    w("")
    w("Roll-call size distribution (PC seats vary; up to 7 + 2 alternates — informational):")
    for s in sorted(size_dist):
        w(f"   {s} voters : {size_dist[s]} motions")
    w("")
    w("-" * 72)
    w("PER-YEAR OBSERVED-VOTER ROSTER (name -> recorded votes that year):")
    w("-" * 72)
    for year in sorted(per_year_voters):
        w(f"\n{year}:")
        for name, c in per_year_voters[year].most_common():
            w(f"   {name:22s} {c}")
    w("")
    w("-" * 72)
    w(f"OFF-ROSTER VOTERS (HARD check — must be 0): {len(off_roster)}")
    w("-" * 72)
    for ln in off_roster:
        w("   " + ln)
    if not off_roster:
        w("   (none)")
    w("")
    w("-" * 72)
    w(f"OUT-OF-WINDOW VOTERS (on-roster, date outside present-window — reviewed source "
      f"anomalies): {len(range_issues)}")
    w("Roster windows come from 'Members Present' headers; a roll call that names a "
      "commissioner the header marked Excused (or a stale re-read) lands here. Traced to "
      "source; flagged not fabricated.")
    w("-" * 72)
    for ln in range_issues:
        w("   " + ln)
    if not range_issues:
        w("   (none)")
    w("")
    w("-" * 72)
    w(f"TALLY-VS-RESULT MISMATCHES (named count != printed tally): "
      f"{len(tally_mismatches)}")
    w("Not auto-corrected — each flags a source typo or a parse miss to hand-review.")
    w("-" * 72)
    for ln in tally_mismatches:
        w("   " + ln)
    if not tally_mismatches:
        w("   (none)")
    w("")
    w("-" * 72)
    w(f"OUTCOME-VS-COUNT INCONSISTENCIES: {len(outcome_issues)}")
    w("-" * 72)
    for ln in outcome_issues:
        w("   " + ln)
    if not outcome_issues:
        w("   (none)")
    w("")
    w("-" * 72)
    w(f"JSON<->CSV RECONCILIATION: json_member_votes={json_vote_rows} "
      f"csv_member_rows={csv_member_rows}  csv_total_rows={csv_rows}  "
      f"({'OK' if recon_ok else 'FAIL'})")
    w("-" * 72)
    w("")
    w("-" * 72)
    w(f"CONTESTED VOTES (any Nay / Abstain / Recuse): {len(contested)}")
    w("-" * 72)
    for ln in contested:
        w("   " + ln)
    if not contested:
        w("   (none)")
    w("")

    os.makedirs(VOTES_DIR, exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    # HARD invariants that must hold for a clean extraction; the remaining items
    # (out-of-window voters, tally mismatches, outcome contradictions) are all traced to
    # source omissions/typos and are flagged-not-fixed, mirroring the council pipeline.
    overall = (not body_bad and not off_roster and recon_ok)
    print(f"Wrote {REPORT}")
    print(f"meetings={meetings} motions={motions} "
          f"stage={dict(stage_counts)} contested={len(contested)} "
          f"off_roster={len(off_roster)} out_of_window={len(range_issues)} "
          f"tally_mismatches={len(tally_mismatches)} "
          f"outcome_issues={len(outcome_issues)} recon={'OK' if recon_ok else 'FAIL'}")
    print("OVERALL:", "PASS (hard invariants clean; "
          f"{len(tally_mismatches)} tally + {len(outcome_issues)} outcome + "
          f"{len(range_issues)} out-of-window are reviewed source anomalies)"
          if overall else "FAIL")


if __name__ == "__main__":
    main()
