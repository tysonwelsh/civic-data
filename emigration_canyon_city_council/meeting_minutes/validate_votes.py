#!/usr/bin/env python3
"""
validate_votes.py — independent QA for the Emigration Canyon City Council vote layer.

Re-reads votes/*.json + all_votes.csv and reports (never mutates):
  1. Motion totals; named-dissent vs tally-only; unanimous; motion-type mix.
  2. JSON member/placeholder rows reconcile 1:1 with all_votes.csv.
  3. Off-roster voter names (should be ZERO).
  4. MAX-TALLY check: any printed tally with more than 5 total votes (the mayor VOTES,
     so a complete roll = 5).  Emigration is a 5-member at-large body incl. the mayor.
  5. Mayor-participation count (the mayor is a voting member — reported for transparency).
  6. Contested-motion list (any named Nay / Abstain, or a printed non-unanimous tally).

Exit 0 = PASS (no off-roster names, JSON<->CSV reconcile, no >5 tally).
Writes votes/_validation_report.txt.
"""
import os, re, csv, json, glob, collections, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
VOTES_DIR = os.path.join(ROOT, "votes")
ALL_VOTES = os.path.join(ROOT, "all_votes.csv")
REPORT = os.path.join(VOTES_DIR, "_validation_report.txt")
import extract_votes as E
FULLNAMES = set(E.SURNAME_TO_FULL.values())


def main():
    meetings = [json.load(open(f, encoding="utf-8"))
                for f in sorted(glob.glob(os.path.join(VOTES_DIR, "**", "*.json"),
                                          recursive=True))]
    lines = []
    def w(s=""): lines.append(s)

    motions = named = tally_only = unanim = contested = 0
    mtype = collections.Counter()
    by_year = collections.Counter()
    csv_expected = 0
    offroster, over5, contested_list = [], [], []
    mayor_motions = 0
    with_motions = 0

    for o in meetings:
        by_year[o["date"][:4]] += 1
        if o["votes"]:
            with_motions += 1
        for v in o["votes"]:
            motions += 1
            mtype[v["motion_type"]] += 1
            members = [(nm, "Aye") for nm in v.get("aye", [])] + \
                      [(nm, "Nay") for nm in v.get("nay", [])] + \
                      [(nm, "Abstain") for nm in v.get("abstain", [])] + \
                      [(nm, "Recuse") for nm in v.get("recuse", [])]
            if v.get("mayor_voted"):
                mayor_motions += 1
            if v["names_recorded"] and members:
                named += 1
                csv_expected += len(members)
                for nm, lab in members:
                    if nm not in FULLNAMES:
                        offroster.append(f"{o['date']} m{v['motion_no']}: {nm!r}")
            else:
                tally_only += 1
                csv_expected += 1
                if v.get("unanimous"):
                    unanim += 1
            t = v.get("tally")
            if t:
                if t[0] + t[1] > 5:
                    over5.append(f"{o['date']} m{v['motion_no']}: tally {t} sums >5")
                if t[1] > 0:
                    contested += 1
                    contested_list.append(
                        f"{o['date']} m{v['motion_no']} {v['result']}  "
                        f"nay={v.get('nay')} abstain={v.get('abstain')} :: {v['motion'][:55]}")
            elif members:
                contested += 1
                contested_list.append(
                    f"{o['date']} m{v['motion_no']} {v['result']}  "
                    f"nay={v.get('nay')} abstain={v.get('abstain')} :: {v['motion'][:55]}")

    csv_rows = list(csv.DictReader(open(ALL_VOTES, encoding="utf-8")))
    csv_count = len(csv_rows)
    bad_body = sum(1 for r in csv_rows if r["body"] != "Council")

    w("Emigration Canyon CITY COUNCIL — vote extraction validation")
    w("=" * 60); w()
    w(f"Meetings (JSON)         : {len(meetings)}")
    w(f"Meetings with >=1 motion: {with_motions}")
    w(f"Motions                 : {motions}")
    w(f"  named-dissent motions : {named}")
    w(f"  tally-only motions    : {tally_only}  (unanimous: {unanim})")
    w(f"Contested motions       : {contested}")
    w(f"Mayor-participation mtns : {mayor_motions}  (the mayor VOTES; counted in the 5)")
    w()
    w(f"CSV rows                : {csv_count}")
    w(f"Expected (from JSON)    : {csv_expected}   "
      f"[{'OK' if csv_count == csv_expected else 'MISMATCH'}]")
    w(f"body != Council         : {bad_body}")
    w()
    w("Motion-type distribution:")
    for k, c in mtype.most_common():
        w(f"    {k:28} {c}")
    w()
    w("Meetings per year:")
    for y, c in sorted(by_year.items()):
        w(f"    {y}: {c}")
    w()
    w(f">5-vote tally flags     : {len(over5)}  (expected 0 — max seat = 5, mayor votes)")
    for l in over5:
        w("    - " + l)
    w()
    w(f"Off-roster voter names  : {len(offroster)}  (expected 0)")
    for l in offroster:
        w("    - " + l)
    w()
    w(f"Contested motions ({len(contested_list)}):")
    for l in contested_list:
        w("    - " + l)

    os.makedirs(VOTES_DIR, exist_ok=True)
    open(REPORT, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    passed = (not offroster) and (csv_count == csv_expected) and bad_body == 0 \
        and not over5
    print("\n".join(lines[:26]))
    print(f"\nfull report -> {REPORT}")
    print("RESULT:", "PASS" if passed else "FAIL")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
