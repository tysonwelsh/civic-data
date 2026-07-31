#!/usr/bin/env python3
"""
validate_votes.py — integrity checks for the extracted Draper Planning Commission vote
JSONs, and generator of the OBSERVED roster.csv.

Reads planning_commission/votes/<year>/<week>/*.json and writes:
  * planning_commission/votes/_validation_report.txt
  * planning_commission/roster.csv   (OBSERVED: member,first_seen,last_seen,n_votes)

The PC is an APPOINTED body (6 members + alternates) — roster size is NOT fixed at a
constant, so this validator does not flag a "wrong denominator"; instead it reports the
observed roster, the recommendation-vs-final-action split, tally-vs-named mismatches, and
the contested/recusal signal. Every named grid lists the full commission (present +
absent/recused), so grids of 8-9 rows are normal.

Exit status: 1 (FAIL) if any vote value is outside the §4 vocabulary or a named voter is
not resolvable to roster.csv; else 0 (PASS).
"""
import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict

REPO = os.path.dirname(os.path.abspath(__file__))
VOTES_DIR = os.path.join(REPO, "votes")
REPORT = os.path.join(VOTES_DIR, "_validation_report.txt")
ROSTER = os.path.join(REPO, "roster.csv")
VOCAB = {"Aye", "Nay", "Abstain", "Recuse", "Absent", "Excused"}


def iter_jsons():
    for dp, _, files in os.walk(VOTES_DIR):
        for fn in sorted(files):
            if fn.endswith(".json") and not fn.startswith("_"):
                yield os.path.join(dp, fn)


def main():
    meetings = motions = mtgs_with_motion = 0
    type_counts = Counter()
    rec_counts = Counter()
    per_year = defaultdict(Counter)
    first_seen, last_seen, nvotes = {}, {}, Counter()
    tally_mm, outcome_issues, contested = [], [], []
    case_motions = 0
    bad_values = []

    for jp in sorted(iter_jsons()):
        with open(jp, encoding="utf-8") as f:
            mtg = json.load(f)
        meetings += 1
        if mtg["votes"]:
            mtgs_with_motion += 1
        year = mtg["date"][:4]
        for v in mtg["votes"]:
            motions += 1
            type_counts[v["motion_type"]] += 1
            # recommendation-vs-final-action label from the result string
            m = re.search(r"(Positive Recommendation|Negative Recommendation|Recommendation|"
                          r"Approved \(Final Action\)|Denied \(Final Action\)|Pass|Fail)",
                          v["result"])
            rec_counts[m.group(1) if m else "other"] += 1
            if v.get("case_numbers"):
                case_motions += 1
            aye, nay = v["aye"], v["nay"]
            abstain, absent, recuse = v["abstain"], v["absent"], v["recuse"]
            for nm in aye + nay + abstain + absent + recuse:
                per_year[year][nm] += 1
                nvotes[nm] += 1
                if nm not in first_seen or mtg["date"] < first_seen[nm]:
                    first_seen[nm] = mtg["date"]
                if nm not in last_seen or mtg["date"] > last_seen[nm]:
                    last_seen[nm] = mtg["date"]
            if nay or abstain or recuse:
                contested.append(
                    f"{mtg['date']} m{v['motion_no']} {v['result']} | NAY={nay} "
                    f"ABSTAIN={abstain} RECUSE={recuse} :: {v['motion'][:70]}")
            if not v.get("names_recorded"):
                continue
            n_aye, n_nay = len(aye), len(nay)
            pt = v.get("printed_tally")
            if pt and sorted([n_aye, n_nay]) != sorted([pt[0], pt[1]]):
                tally_mm.append(f"{mtg['date']} m{v['motion_no']}: named aye={n_aye} "
                                f"nay={n_nay} vs printed {pt[0]}-{pt[1]} :: {v['result']} "
                                f":: {v['motion'][:50]}")
            if "Fail" in v["result"] and n_aye > n_nay:
                outcome_issues.append(f"{mtg['date']} m{v['motion_no']}: FAIL but "
                                      f"aye={n_aye}>nay={n_nay} :: {v['result']}")

    members = sorted(nvotes)
    with open(ROSTER, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["member", "first_seen", "last_seen", "n_votes"])
        for m in members:
            w.writerow([m, first_seen[m], last_seen[m], nvotes[m]])

    roster_set = set(members)
    av = os.path.join(REPO, "all_votes.csv")
    if os.path.exists(av):
        for r in csv.DictReader(open(av)):
            if r["vote"] and r["vote"] not in VOCAB:
                bad_values.append(f"{r['date']} m{r['motion_no']}: bad vote '{r['vote']}'")
            if r["member"] and r["member"] not in roster_set:
                bad_values.append(f"{r['date']} m{r['motion_no']}: off-roster '{r['member']}'")

    L = []
    w = L.append
    w("Draper Planning Commission — vote extraction validation report")
    w("=" * 72)
    w(f"Meeting JSONs             : {meetings}  (with >=1 motion: {mtgs_with_motion})")
    w(f"Motions extracted         : {motions}   (with a case number: {case_motions})")
    w("")
    w("Motion-type distribution:")
    for t, c in type_counts.most_common():
        w(f"   {t:28s} {c}")
    w("")
    w("Recommendation vs final-action (from result string):")
    for t, c in rec_counts.most_common():
        w(f"   {t:28s} {c}")
    w("")
    w("-" * 72)
    w("PER-YEAR OBSERVED COMMISSIONERS (appointed body; size varies):")
    w("-" * 72)
    for year in sorted(per_year):
        w(f"\n{year}:")
        for nm, c in per_year[year].most_common():
            w(f"   {nm:28s} {c}")
    w("")
    for title, items, note in [
        (f"TALLY-VS-NAMED MISMATCHES: {len(tally_mm)}", tally_mm,
         "Named counts vs the minutes' printed tally — source typo or parse miss; not fixed."),
        (f"OUTCOME-VS-COUNT INCONSISTENCIES: {len(outcome_issues)}", outcome_issues, ""),
        (f"CONTESTED / NON-AYE VOTES (Nay/Abstain/Recuse) — the signal: {len(contested)}",
         contested, "Recusals are common (a commissioner with a conflict); Nay is real dissent."),
    ]:
        w("-" * 72)
        w(title)
        if note:
            w(note)
        w("-" * 72)
        for ln in items or ["   (none)"]:
            w("   " + ln if not ln.startswith("   ") else ln)
        w("")

    os.makedirs(VOTES_DIR, exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")

    print(f"Wrote {REPORT}")
    print(f"Wrote {ROSTER} ({len(members)} observed commissioners)")
    print(f"meetings={meetings} motions={motions} case_motions={case_motions}")
    print(f"contested={len(contested)} tally_mismatch={len(tally_mm)} "
          f"outcome_issues={len(outcome_issues)}")
    if bad_values:
        print(f"FAIL: {len(bad_values)} vocabulary/roster violations:")
        for b in bad_values[:20]:
            print("  ", b)
        sys.exit(1)
    print("PASS (vocabulary + roster-resolvable)")


if __name__ == "__main__":
    main()
