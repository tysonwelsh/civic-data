#!/usr/bin/env python3
"""
validate_votes.py — independent QA for the Planning Commission vote dataset.

Re-reads the per-meeting JSONs and all_votes.csv (does NOT re-parse the minutes)
and checks:

  1. every roll-call commissioner is on the roster (roster.csv);
  2. every roll-call vote falls within that commissioner's first_seen..last_seen
     attendance range (0 out-of-range expected);
  3. JSON member-vote rows reconcile 1:1 with all_votes.csv rows;
  4. result strings are well-formed and tag recommendation vs final action vs
     procedural per the required encoding;
  5. tally-vs-source-word mismatches are listed (source typos — not fabricated);
  6. study meetings with no recorded votes are counted (expected, not a gap).

Exit status 0 = PASS, 1 = FAIL.  Run:  python3 planning_commission/validate_votes.py
"""
import os, re, csv, json, glob, sys

PC = os.path.dirname(os.path.abspath(__file__))
VOTES_DIR = os.path.join(PC, "votes")
ALL_VOTES = os.path.join(PC, "all_votes.csv")
ROSTER = os.path.join(PC, "roster.csv")

GROUPS = (("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
          ("absent", "Absent"), ("recuse", "Recuse"))


def main():
    fails = []
    warns = []

    # roster
    roster = {}
    for r in csv.DictReader(open(ROSTER, encoding="utf-8")):
        roster[r["commissioner"]] = (r["first_seen"], r["last_seen"])

    # JSONs
    jfiles = sorted(glob.glob(os.path.join(VOTES_DIR, "**", "*.json"), recursive=True))
    json_rows = []          # (date,motion_no,member,vote)
    n_meetings = n_motions = n_named = n_tally = 0
    n_rec = n_final = n_proc = n_contested = 0
    study_no_votes = 0
    tally_mismatch = []
    offroster = []
    offrange = []
    badresult = []

    for jf in jfiles:
        d = json.load(open(jf, encoding="utf-8"))
        n_meetings += 1
        date = d["date"]
        if d["body"] != "PlanningCommission":
            fails.append(f"{jf}: body != PlanningCommission")
        if d.get("meeting_type") == "study" and not d["votes"]:
            study_no_votes += 1
        for v in d["votes"]:
            n_motions += 1
            cat = v.get("action_category")
            res = v["result"]
            # result-string well-formedness
            if cat == "recommendation":
                n_rec += 1
                if not re.match(r"(Positive|Negative) recommendation \d+:\d+$", res) \
                   and "(Continued)" not in res and "(Tabled)" not in res \
                   and "(Withdrawn)" not in res:
                    badresult.append(f"{date} m{v['motion_no']}: rec result {res!r}")
            elif cat == "final":
                n_final += 1
                if "recommend" in res.lower() or "forward" in res.lower():
                    badresult.append(f"{date} m{v['motion_no']}: final result has "
                                     f"'recommend' substring: {res!r}")
            else:
                n_proc += 1
            if v["names_recorded"]:
                n_named += 1
            else:
                n_tally += 1
            if v["nay"] or v["abstain"] or v["recuse"]:
                n_contested += 1
            # roster + range
            for grp, label in GROUPS:
                for nm in v[grp]:
                    if nm not in roster:
                        offroster.append(f"{date} m{v['motion_no']}: {nm}")
                    else:
                        lo, hi = roster[nm]
                        if not (lo <= date <= hi):
                            offrange.append(f"{date} {nm} outside {lo}..{hi}")
                    if grp != "absent":  # Absent isn't really a cast vote but keep row parity
                        json_rows.append((date, str(v["motion_no"]), nm, label))
                    else:
                        json_rows.append((date, str(v["motion_no"]), nm, label))
            # tally vs source word
            src = v.get("result_source") or ""
            if re.search(r"unanimous", src, re.I) and len(v["nay"]) > 0:
                tally_mismatch.append(f"{date} m{v['motion_no']}: src {src!r} but "
                                      f"{len(v['nay'])} Nay (roll call kept: {res})")

    # CSV
    csv_rows = []
    csv_member_rows = []
    cols_expected = ["date", "year", "title", "body", "motion_no", "motion",
                     "motion_type", "result", "mover", "seconder", "member",
                     "vote", "source"]
    with open(ALL_VOTES, encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        if rdr.fieldnames != cols_expected:
            fails.append(f"all_votes.csv columns {rdr.fieldnames} != {cols_expected}")
        for r in rdr:
            if r["body"] != "PlanningCommission":
                fails.append(f"CSV row body != PlanningCommission: {r['date']}")
            if r["title"] != "Planning Commission":
                fails.append(f"CSV row title != 'Planning Commission': {r['date']}")
            if r["member"]:
                csv_member_rows.append((r["date"], r["motion_no"], r["member"], r["vote"]))

    # reconcile JSON member-vote rows <-> CSV member rows
    from collections import Counter
    cj = Counter(json_rows)
    cc = Counter(csv_member_rows)
    if cj != cc:
        only_j = cj - cc
        only_c = cc - cj
        if only_j:
            fails.append(f"{sum(only_j.values())} member-vote rows in JSON not in CSV (e.g. {list(only_j)[:3]})")
        if only_c:
            fails.append(f"{sum(only_c.values())} member-vote rows in CSV not in JSON (e.g. {list(only_c)[:3]})")

    if offroster:
        fails.append(f"{len(offroster)} off-roster roll-call names: {offroster[:5]}")
    if offrange:
        fails.append(f"{len(offrange)} out-of-range votes: {offrange[:5]}")
    if badresult:
        fails.append(f"{len(badresult)} malformed result strings: {badresult[:5]}")

    print("=" * 60)
    print("Planning Commission vote dataset — validation")
    print("=" * 60)
    print(f"Meetings (JSON)        : {n_meetings}")
    print(f"Motions                : {n_motions}")
    print(f"  named roll-calls     : {n_named}")
    print(f"  tally-only           : {n_tally}")
    print(f"  recommendations      : {n_rec}")
    print(f"  final actions        : {n_final}")
    print(f"  procedural/appoint   : {n_proc}")
    print(f"  contested            : {n_contested}")
    print(f"JSON member-vote rows  : {len(json_rows)}")
    print(f"CSV member-vote rows   : {len(csv_member_rows)}")
    print(f"Study mtgs w/ no votes : {study_no_votes}")
    print(f"Distinct commissioners : {len(roster)}")
    print(f"Off-roster names       : {len(offroster)}")
    print(f"Out-of-range votes     : {len(offrange)}")
    print(f"Tally mismatches (src) : {len(tally_mismatch)}")
    for t in tally_mismatch:
        print(f"  - {t}")
    print()
    if fails:
        print("RESULT: FAIL")
        for fl in fails:
            print("  !! " + fl)
        sys.exit(1)
    print("RESULT: PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
