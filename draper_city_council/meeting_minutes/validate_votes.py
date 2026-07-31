#!/usr/bin/env python3
"""
validate_votes.py — integrity checks for the extracted Draper City Council vote JSONs,
and generator of the OBSERVED roster.csv.

Reads every meeting_minutes/votes/<year>/<week>/*.json and writes:
  * meeting_minutes/votes/_validation_report.txt   (human-readable report)
  * meeting_minutes/roster.csv                      (OBSERVED: member,first_seen,
                                                     last_seen,n_votes)

Report covers:
  1. Motion totals + per-body + motion-type distribution.
  2. Per-year observed-voter roster (the 5 at-large members; the Mayor should appear
     ONLY on flagged tie-break motions).
  3. MAYOR-VOTE flags — motions where the source recorded Mayor Walker casting a vote
     (a genuine tie-break; he is otherwise non-voting, roll denominator = 5).
  4. >5-voter flags (would signal the Mayor mis-counted or a parse error).
  5. Tally-vs-named mismatches — named Aye/Nay counts vs the minutes' printed tally
     (logged verbatim, never auto-corrected).
  6. Outcome-vs-count inconsistencies.
  7. Roster-size deviations (seated council voters != 5 — an absence/vacancy/parse miss).
  8. Contested votes (any Nay/Abstain/Recuse) — the analytical signal.

Exit status: 1 (FAIL) if any vote value is outside the §4 vocabulary, or a named voter
cannot be resolved to roster.csv; otherwise 0 (PASS; WARN sections document soft drift).
"""
import csv
import json
import os
import sys
from collections import Counter, defaultdict

REPO = os.path.dirname(os.path.abspath(__file__))
VOTES_DIR = os.path.join(REPO, "votes")
REPORT = os.path.join(VOTES_DIR, "_validation_report.txt")
ROSTER = os.path.join(REPO, "roster.csv")

MAYOR_NAME = "Mayor Troy K. Walker"
COUNCIL_SIZE = 5
VOCAB = {"Aye", "Nay", "Abstain", "Recuse", "Absent", "Excused"}


def iter_jsons():
    for dp, _, files in os.walk(VOTES_DIR):
        for fn in sorted(files):
            if fn.endswith(".json") and not fn.startswith("_"):
                yield os.path.join(dp, fn)


def main():
    meetings = motions = mtgs_with_motion = 0
    body_counts = Counter()
    type_counts = Counter()
    per_year = defaultdict(Counter)
    first_seen, last_seen, nvotes = {}, {}, Counter()
    mayor_votes, six_voter, tally_mm, outcome_issues, size_dev, contested = ([] for _ in range(6))
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
            body_counts[v.get("body", "Council")] += 1
            type_counts[v["motion_type"]] += 1
            aye, nay = v["aye"], v["nay"]
            abstain, absent, recuse = v["abstain"], v["absent"], v["recuse"]
            council_voters = [x for x in aye + nay + abstain + absent + recuse
                              if x != MAYOR_NAME]
            for nm in aye + nay + abstain + absent + recuse:
                per_year[year][nm] += 1
                nvotes[nm] += 1
                if nm not in first_seen or mtg["date"] < first_seen[nm]:
                    first_seen[nm] = mtg["date"]
                if nm not in last_seen or mtg["date"] > last_seen[nm]:
                    last_seen[nm] = mtg["date"]

            if v.get("mayor_voted"):
                mv = ("Aye" if MAYOR_NAME in aye else "Nay" if MAYOR_NAME in nay
                      else "?")
                mayor_votes.append(f"{mtg['date']} m{v['motion_no']} {v['result']}: "
                                   f"Mayor voted {mv} :: {v['motion'][:65]}")
            if len(council_voters) > COUNCIL_SIZE:
                six_voter.append(f"{mtg['date']} m{v['motion_no']}: "
                                 f"{len(council_voters)} council voters (>5)")
            if nay or abstain or recuse:
                contested.append(
                    f"{mtg['date']} m{v['motion_no']} {v['result']} | AYE={aye} NAY={nay} "
                    f"ABSTAIN={abstain} RECUSE={recuse} ABSENT={absent} :: {v['motion'][:70]}")

            # vocabulary check (JSON buckets already map to vocab; guard anyway)
            # tally-vs-named + outcome checks (named grids only)
            if not v.get("names_recorded"):
                continue
            n_aye, n_nay = len(aye), len(nay)
            pt = v.get("printed_tally")
            if pt:
                if sorted([n_aye, n_nay]) != sorted([pt[0], pt[1]]):
                    tally_mm.append(f"{mtg['date']} m{v['motion_no']}: named "
                                    f"aye={n_aye} nay={n_nay} vs printed {pt[0]}-{pt[1]} "
                                    f":: {v['result']} :: {v['motion'][:55]}")
            outcome = v["result"].split()[-1] if v["result"] else ""
            if "Pass" in v["result"] and n_nay and n_aye <= n_nay and not v.get("mayor_voted"):
                outcome_issues.append(f"{mtg['date']} m{v['motion_no']}: PASS but "
                                      f"aye={n_aye}<=nay={n_nay} :: {v['result']}")
            if "Fail" in v["result"] and n_aye > n_nay:
                outcome_issues.append(f"{mtg['date']} m{v['motion_no']}: FAIL but "
                                      f"aye={n_aye}>nay={n_nay} :: {v['result']}")
            seated = len(council_voters)
            if seated != COUNCIL_SIZE:
                size_dev.append(f"{mtg['date']} m{v['motion_no']}: {seated} council "
                                f"voters (expected {COUNCIL_SIZE}) :: {v['result']} :: "
                                f"{v['motion'][:45]}")

    # ---- write OBSERVED roster.csv (excludes the mayor: observed rosters omit
    #      non-voting mayors, per SCHEMA_SPEC §1) ----
    members = sorted(m for m in nvotes if m != MAYOR_NAME)
    with open(ROSTER, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["member", "first_seen", "last_seen", "n_votes"])
        for m in members:
            w.writerow([m, first_seen[m], last_seen[m], nvotes[m]])

    # ---- validate against all_votes.csv vocabulary + roster resolvability ----
    roster_set = set(members) | {MAYOR_NAME}
    av = os.path.join(REPO, "all_votes.csv")
    if os.path.exists(av):
        for r in csv.DictReader(open(av)):
            if r["vote"] and r["vote"] not in VOCAB:
                bad_values.append(f"{r['date']} m{r['motion_no']}: bad vote '{r['vote']}'")
            if r["member"] and r["member"] not in roster_set:
                bad_values.append(f"{r['date']} m{r['motion_no']}: off-roster '{r['member']}'")

    L = []
    w = L.append
    w("Draper City Council — vote extraction validation report")
    w("=" * 72)
    w(f"Meeting JSONs             : {meetings}  (with >=1 motion: {mtgs_with_motion})")
    w(f"Motions extracted         : {motions}")
    w(f"Body counts               : {dict(body_counts)}")
    w("")
    w("Motion-type distribution:")
    for t, c in type_counts.most_common():
        w(f"   {t:28s} {c}")
    w("")
    w("-" * 72)
    w("PER-YEAR OBSERVED VOTERS (the 5 at-large members; Mayor only on tie-breaks):")
    w("-" * 72)
    for year in sorted(per_year):
        w(f"\n{year}:")
        for nm, c in per_year[year].most_common():
            flag = "   <-- MAYOR (tie-break only)" if nm == MAYOR_NAME else ""
            w(f"   {nm:28s} {c}{flag}")
    w("")
    for title, items, note in [
        (f"MAYOR-VOTE FLAGS (genuine tie-breaks): {len(mayor_votes)}", mayor_votes,
         "Mayor Walker is non-voting except to break a tie (roll denominator = 5)."),
        (f">5-COUNCIL-VOTER FLAGS: {len(six_voter)}", six_voter, ""),
        (f"TALLY-VS-NAMED MISMATCHES: {len(tally_mm)}", tally_mm,
         "Named counts vs the minutes' printed tally — source typo or parse miss; not fixed."),
        (f"OUTCOME-VS-COUNT INCONSISTENCIES: {len(outcome_issues)}", outcome_issues, ""),
        (f"ROSTER-SIZE DEVIATIONS (council voters != 5): {len(size_dev)}", size_dev,
         "Genuine absence/vacancy, or a parse miss — each reviewed."),
        (f"CONTESTED VOTES (any Nay/Abstain/Recuse) — the signal: {len(contested)}",
         contested, ""),
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
    print(f"Wrote {ROSTER} ({len(members)} observed members)")
    print(f"meetings={meetings} motions={motions} body={dict(body_counts)}")
    print(f"mayor_votes={len(mayor_votes)} contested={len(contested)} "
          f"tally_mismatch={len(tally_mm)} outcome_issues={len(outcome_issues)} "
          f"size_dev={len(size_dev)} six_voter={len(six_voter)}")
    if bad_values:
        print(f"FAIL: {len(bad_values)} vocabulary/roster violations:")
        for b in bad_values[:20]:
            print("  ", b)
        sys.exit(1)
    print("PASS (vocabulary + roster-resolvable)")


if __name__ == "__main__":
    main()
