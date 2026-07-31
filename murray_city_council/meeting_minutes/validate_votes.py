#!/usr/bin/env python3
"""
validate_votes.py — sanity-check the extracted Murray City Council vote JSONs.

Reads every meeting_minutes/votes/<year>/<week>/*.json and writes a human-readable
report to meeting_minutes/votes/_validation_report.txt.

HARD checks (nonzero exit if any fail):
  * every named voter resolves to the council roster (no invented / off-roster names);
  * every vote value is in the §4 vocabulary (Aye|Nay|Abstain|Recuse|Absent|Excused);
  * no roll call seats more than 5 members (mayor does NOT vote — max = 5 districts).
SOFT checks (reported, never auto-corrected — faithful-capture anomalies):
  * named aye/nay vs the minutes' own printed tally;
  * outcome-vs-count consistency;
  * roster-size deviations; the full contested-vote list.
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

REPO = os.path.dirname(os.path.abspath(__file__))
VOTES_DIR = os.path.join(REPO, "votes")
REPORT = os.path.join(VOTES_DIR, "_validation_report.txt")

ROSTER = {
    "Kat Martinez", "Philip Markham", "Paul Pickett", "David Rodgers", "Dale Cox",
    "Pamela Cotter", "Rosalba Dominguez", "Scott Goodman", "Clark Bullen",
    "Diane Turner", "Brett Hales", "Garry Hrechkosy", "Adam Hock",
}
VOCAB = {"Aye", "Nay", "Abstain", "Recuse", "Absent", "Excused"}
COUNCIL_SIZE = 5


def iter_jsons():
    for dp, _, files in os.walk(VOTES_DIR):
        for fn in sorted(files):
            if fn.endswith(".json") and not fn.startswith("_"):
                yield os.path.join(dp, fn)


def main():
    meetings = motions = named = tally = 0
    type_counts = Counter()
    result_counts = Counter()
    per_year = defaultdict(Counter)
    off_roster = Counter()
    bad_vocab = []
    six_voter = []
    tally_mismatch = []
    outcome_issues = []
    size_issues = []
    contested = []

    for jp in sorted(iter_jsons()):
        with open(jp, encoding="utf-8") as f:
            mtg = json.load(f)
        meetings += 1
        year = mtg["date"][:4]
        for v in mtg["votes"]:
            motions += 1
            type_counts[v["motion_type"]] += 1
            result_counts[v["result"]] += 1
            buckets = {"Aye": v["aye"], "Nay": v["nay"], "Abstain": v["abstain"],
                       "Absent": v["absent"], "Excused": v["excused"], "Recuse": v["recuse"]}
            allv = [n for b in buckets.values() for n in b]

            if v["names_recorded"]:
                named += 1
                for lab, names in buckets.items():
                    if lab not in VOCAB:
                        bad_vocab.append(f"{mtg['date']} m{v['motion_no']}: label {lab}")
                    for nm in names:
                        per_year[year][nm] += 1
                        if nm not in ROSTER:
                            off_roster[nm] += 1
            else:
                tally += 1

            if len(allv) > COUNCIL_SIZE:
                six_voter.append(f"{mtg['date']} m{v['motion_no']} {v['result']}: "
                                 f"{len(allv)} seated :: {allv}")

            if v["nay"] or v["abstain"] or v["recuse"]:
                contested.append(
                    f"{mtg['date']} m{v['motion_no']} {v['result']} | "
                    f"NAY={v['nay']} ABSTAIN={v['abstain']} RECUSE={v['recuse']} "
                    f"ABSENT={v['absent']} :: {v['motion'][:70]}")

            if not v["names_recorded"]:
                continue
            a, nn = len(v["aye"]), len(v["nay"])
            # printed tally (skip synthesized bare 'N-M' and nomination 'Vote:'/'wins')
            if not re.fullmatch(r"\d+-\d+", v["result"]) and "Vote:" not in v["result"] \
                    and "wins" not in v["result"]:
                m = re.search(r"(\d+)\s*-\s*(\d+)", v["result"])
                if m:
                    pa, pn = int(m.group(1)), int(m.group(2))
                    if a != pa or nn != pn:
                        tally_mismatch.append(
                            f"{mtg['date']} m{v['motion_no']}: named {a}-{nn} vs printed "
                            f"{pa}-{pn} :: {v['result']} :: {v['motion'][:55]}")
            outcome = "Fail" if re.search(r"fail", v["result"], re.I) else "Pass"
            if outcome == "Pass" and nn and a <= nn:
                outcome_issues.append(f"{mtg['date']} m{v['motion_no']}: PASS but "
                                      f"aye={a}<=nay={nn} :: {v['result']}")
            if outcome == "Fail" and a > nn:
                outcome_issues.append(f"{mtg['date']} m{v['motion_no']}: FAIL but "
                                      f"aye={a}>nay={nn} :: {v['result']}")
            seated = len(allv)
            if seated != COUNCIL_SIZE:
                size_issues.append(f"{mtg['date']} m{v['motion_no']}: {seated} seated "
                                   f"(expected {COUNCIL_SIZE}) :: {v['result']}")

    L = []
    w = L.append
    w("Murray City Council — vote extraction validation report")
    w("=" * 72)
    w(f"Meeting JSONs      : {meetings}")
    w(f"Motions extracted  : {motions}  (named {named} / tally-only {tally})")
    w(f"Distinct results   : {len(result_counts)}")
    w("")
    w("Motion-type distribution:")
    for t, c in type_counts.most_common():
        w(f"   {t:26s} {c}")
    w("")
    w("-" * 72)
    w("PER-YEAR OBSERVED-VOTER ROSTER (name -> named vote rows that year).")
    w("Note: Brett Hales is the D5 COUNCILMEMBER (2020-2021), distinct from Mayor Hales.")
    w("-" * 72)
    for year in sorted(per_year):
        w(f"\n{year}:")
        for nm, c in per_year[year].most_common():
            flag = "   <-- OFF-ROSTER" if nm not in ROSTER else ""
            w(f"   {nm:22s} {c}{flag}")
    w("")
    w("=" * 72)
    w("HARD CHECKS")
    w("=" * 72)
    w(f"Off-roster named voters : {len(off_roster)}   {dict(off_roster)}")
    w(f"Bad vote values         : {len(bad_vocab)}")
    for x in bad_vocab:
        w("   " + x)
    w(f">5-voter roll calls     : {len(six_voter)}")
    for x in six_voter:
        w("   " + x)
    w("")
    w("=" * 72)
    w("SOFT CHECKS (faithful-capture anomalies — reported, never auto-corrected)")
    w("=" * 72)
    w(f"Tally-vs-named mismatches: {len(tally_mismatch)}")
    for x in tally_mismatch:
        w("   " + x)
    w(f"Outcome-vs-count issues  : {len(outcome_issues)}")
    for x in outcome_issues:
        w("   " + x)
    w(f"Roster-size deviations   : {len(size_issues)} (absence/vacancy/synth-tally — reviewed)")
    w("")
    w("-" * 72)
    w(f"CONTESTED VOTES (any Nay / Abstain / Recuse) — the signal: {len(contested)}")
    w("-" * 72)
    for x in contested:
        w("   " + x)
    w("")

    os.makedirs(VOTES_DIR, exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")

    hard = len(off_roster) + len(bad_vocab) + len(six_voter)
    print(f"Wrote {REPORT}")
    print(f"meetings={meetings} motions={motions} named={named} tally={tally} "
          f"contested={len(contested)}")
    print(f"HARD: off_roster={len(off_roster)} bad_vocab={len(bad_vocab)} "
          f"six_voter={len(six_voter)}  ||  SOFT: tally_mismatch={len(tally_mismatch)} "
          f"outcome={len(outcome_issues)} size_dev={len(size_issues)}")
    if hard:
        print("VALIDATION FAILED (hard errors present)")
        sys.exit(1)
    print("VALIDATION PASSED (0 hard errors)")


if __name__ == "__main__":
    main()
