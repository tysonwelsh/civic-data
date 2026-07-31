#!/usr/bin/env python3
"""
validate_votes.py — independent QA for the Emigration Canyon Planning Commission votes.

Re-reads votes/*.json + all_votes.csv and reports (never mutates):
  1. Motion totals; named-dissent vs tally-only; motion-type mix; meetings/year.
  2. JSON member/placeholder rows reconcile 1:1 with all_votes.csv.
  3. body == PlanningCommission for every row.
  4. Distinct movers/voters vs the observed commissioner roster (unmapped surnames are
     reported but allowed — PC minutes are born-digital and name commissioners verbatim).
  5. Contested-motion list (named Nay / Abstain).

Exit 0 = PASS (JSON<->CSV reconcile, body consistent).
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

    motions = named = tally_only = contested = 0
    mtype = collections.Counter()
    by_year = collections.Counter()
    voters = collections.Counter()
    csv_expected = 0
    contested_list = []
    unmapped = collections.Counter()
    with_motions = 0

    for o in meetings:
        by_year[o["date"][:4]] += 1
        if o["votes"]:
            with_motions += 1
        for v in o["votes"]:
            motions += 1
            mtype[v["motion_type"]] += 1
            members = [(nm, "Nay") for nm in v.get("nay", [])] + \
                      [(nm, "Abstain") for nm in v.get("abstain", [])]
            for nm in ([v.get("mover"), v.get("seconder")] + v.get("nay", []) +
                       v.get("abstain", [])):
                if nm:
                    voters[nm] += 1
                    if nm not in FULLNAMES:
                        unmapped[nm] += 1
            if v["names_recorded"] and members:
                named += 1
                csv_expected += len(members)
                contested += 1
                contested_list.append(
                    f"{o['date']} m{v['motion_no']} {v['result']}  "
                    f"nay={v.get('nay')} abstain={v.get('abstain')} :: {v['motion'][:55]}")
            else:
                tally_only += 1
                csv_expected += 1

    csv_rows = list(csv.DictReader(open(ALL_VOTES, encoding="utf-8")))
    csv_count = len(csv_rows)
    bad_body = sum(1 for r in csv_rows if r["body"] != "PlanningCommission")

    w("Emigration Canyon PLANNING COMMISSION — vote extraction validation")
    w("=" * 60); w()
    w(f"Meetings (JSON)         : {len(meetings)}")
    w(f"Meetings with >=1 motion: {with_motions}")
    w(f"Motions                 : {motions}")
    w(f"  named-dissent motions : {named}")
    w(f"  tally-only motions    : {tally_only}")
    w(f"Contested motions       : {contested}")
    w()
    w(f"CSV rows                : {csv_count}")
    w(f"Expected (from JSON)    : {csv_expected}   "
      f"[{'OK' if csv_count == csv_expected else 'MISMATCH'}]")
    w(f"body != PlanningCommission : {bad_body}")
    w()
    w("Motion-type distribution:")
    for k, c in mtype.most_common():
        w(f"    {k:28} {c}")
    w()
    w("Meetings per year:")
    for y, c in sorted(by_year.items()):
        w(f"    {y}: {c}")
    w()
    w("Distinct named participants (mover/seconder/voter):")
    for nm, c in voters.most_common():
        flag = "" if nm in FULLNAMES else "  (unmapped surname — kept verbatim)"
        w(f"    {nm:22} {c}{flag}")
    w()
    w(f"Contested motions ({len(contested_list)}):")
    for l in contested_list:
        w("    - " + l)

    os.makedirs(VOTES_DIR, exist_ok=True)
    open(REPORT, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    passed = (csv_count == csv_expected) and bad_body == 0
    print("\n".join(lines[:24]))
    print(f"\nfull report -> {REPORT}")
    print("RESULT:", "PASS" if passed else "FAIL")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
