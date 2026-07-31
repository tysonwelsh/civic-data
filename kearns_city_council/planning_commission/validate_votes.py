#!/usr/bin/env python3
"""
validate_votes.py — independent QA for a Kearns vote layer (Council+CRA or PC).
Re-reads the per-meeting JSONs + all_votes.csv and reports (never mutates):

  1. Motion totals; per-body; named-vs-tally-only; unanimous-vs-contested; type dist.
  2. JSON member-vote rows reconcile 1:1 with all_votes.csv.
  3. MAX-TALLY check: any parsed tally (ayes+nays) > 5, or present_count > 5.
  4. Off-roster council voters (a named voter not on the fixed 8-name roster) — 0.
  5. Mayor-participation rows (presiding officer who VOTES).
  6. Contested list (any named Nay / Abstain / Recuse).
  7. Meetings with zero extracted motions (listed for manual review).

Exit 0 = PASS. Writes votes/_validation_report.txt.
"""
import os, re, csv, json, glob, collections, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
VOTES_DIR = os.path.join(ROOT, "votes")
ALL_VOTES = os.path.join(ROOT, "all_votes.csv")
REPORT = os.path.join(VOTES_DIR, "_validation_report.txt")
import extract_votes as E
BODY = E.BODY
FULLNAMES = set(E.SURNAME_TO_FULL.values())
MAYORS = E.MAYORS

def load():
    return [json.load(open(f, encoding="utf-8"))
            for f in sorted(glob.glob(os.path.join(VOTES_DIR, "**", "*.json"),
                                      recursive=True))]

def main():
    meetings = load(); L = []
    def w(s=""): L.append(s)
    motions = tally = unanimous = contested = mayor_rows = with_m = 0
    mtype = collections.Counter(); body_ct = collections.Counter()
    csv_expected = 0; over5 = []; offroster = []; contested_list = []; nomotion = []
    for o in meetings:
        if o["votes"]:
            with_m += 1
        else:
            nomotion.append(o["date"])
        for v in o["votes"]:
            motions += 1; mtype[v["motion_type"]] += 1; body_ct[v["body"]] += 1
            members = [(nm, lab) for g, lab in (("aye","Aye"),("nay","Nay"),
                       ("abstain","Abstain"),("absent","Absent"),("recuse","Recuse"))
                       for nm in v.get(g, [])]
            csv_expected += len(members) if members else 1
            if not members:
                tally += 1
            if v.get("tally_only", {}).get("unanimous"):
                unanimous += 1
            to = v.get("tally_only", {})
            a, n = to.get("ayes"), to.get("nays")
            if a is not None and n is not None and a + n > 5:
                over5.append(f"{o['date']} m{v['motion_no']}: tally {a}-{n} (>5)")
            pc = to.get("present_count")
            if pc and pc > 5:
                over5.append(f"{o['date']} m{v['motion_no']}: present_count={pc} (>5)")
            if v["nay"] or v["abstain"] or v["recuse"]:
                contested += 1
                contested_list.append(f"{o['date']} [{v['body']}] m{v['motion_no']} "
                    f"{v['result']} :: {v['motion'][:60]}")
            if v.get("mayor_voted"):
                mayor_rows += 1
            if BODY == "Council":
                for nm, lab in members:
                    if nm not in FULLNAMES:
                        offroster.append(f"{o['date']} m{v['motion_no']}: {nm!r}")
    csv_rows = list(csv.DictReader(open(ALL_VOTES, encoding="utf-8")))
    csv_count = len(csv_rows)
    valid_bodies = ("Council", "CRA") if BODY == "Council" else ("PlanningCommission",)
    bad_body = sum(1 for r in csv_rows if r["body"] not in valid_bodies)

    w(f"Kearns {BODY} — vote extraction validation"); w("=" * 56); w()
    w(f"Meetings (JSON)        : {len(meetings)}")
    w(f"Meetings with >=1 vote : {with_m}")
    w(f"Meetings with 0 motions: {len(nomotion)}  {nomotion}")
    w(f"Motions                : {motions}")
    w(f"  tally-only (no names): {tally}  (of which unanimous: {unanimous})")
    w(f"  with named dissent   : {motions - tally}")
    w(f"Body split             : " + " · ".join(f"{k} {c}" for k, c in body_ct.items()))
    w(f"Contested motions      : {contested}")
    w(f"Mayor-participation rows (presiding officer votes): {mayor_rows}")
    w()
    w(f"CSV rows               : {csv_count}")
    w(f"Expected (from JSON)   : {csv_expected}   "
      f"[{'OK' if csv_count == csv_expected else 'MISMATCH'}]")
    w(f"body out of range      : {bad_body}")
    w(f">5-tally / 6th-voter   : {len(over5)}   (expected 0 — max seat = 5)")
    for l in over5[:40]:
        w("   - " + l)
    w(f"Off-roster council names: {len(offroster)}   (expected 0)")
    for l in offroster[:40]:
        w("   - " + l)
    w()
    w("Motion-type distribution:")
    for k, c in mtype.most_common():
        w(f"   {k:28} {c}")
    w()
    w(f"Contested votes ({len(contested_list)}):")
    for l in contested_list:
        w("   - " + l)
    os.makedirs(VOTES_DIR, exist_ok=True)
    open(REPORT, "w", encoding="utf-8").write("\n".join(L) + "\n")
    passed = (not offroster) and csv_count == csv_expected and bad_body == 0 and not over5
    print("\n".join(L[:22]))
    print(f"\nfull report -> {REPORT}")
    print("RESULT:", "PASS" if passed else "FAIL")
    sys.exit(0 if passed else 1)

if __name__ == "__main__":
    main()
