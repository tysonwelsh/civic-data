#!/usr/bin/env python3
"""
validate_votes.py — sanity-check the extracted Magna council vote JSONs.

Writes votes/_validation_report.txt covering motion totals, per-body counts, motion-type
mix, per-year observed-voter roster, the form-of-government seam (pre-2026 the elected
Chair titled "Mayor" — Peay then Barney — is a VOTING member; 2026+ Mayor Sudbury is
NON-voting), >5-voter / mayor-vote flags, tally-vs-named mismatches on full roll calls,
outcome-vs-count consistency, roster-size deviations, and the contested-vote list.
"""
import json, os
from collections import Counter, defaultdict

REPO = os.path.dirname(os.path.abspath(__file__))
VOTES_DIR = os.path.join(REPO, "votes")
REPORT = os.path.join(VOTES_DIR, "_validation_report.txt")

ROSTER = {"Trish Hull", "Steve Prokopis", "Brint Peel", "Eric Barney", "Audrey Pierce",
          "Mick Sudbury", "Eric Ferguson", "Dan Peay", "Michael Jensen", "Megan Olsen",
          "Terry George"}
# people who held the presiding "Mayor"/Chair title; VOTING before 2026, non-voting after
CHAIR_MAYORS = {"Dan Peay", "Eric Barney"}   # elected voting chairs (<=2025)
CITY_MAYOR = "Mick Sudbury"                   # directly-elected, NON-voting (2026+)
COUNCIL_SIZE = 5


def iter_jsons():
    for dp, _, files in os.walk(VOTES_DIR):
        for fn in sorted(files):
            if fn.endswith(".json") and not fn.startswith("_"):
                yield os.path.join(dp, fn)


def main():
    meetings = motions = mtgs_with_motion = 0
    body_counts = Counter(); type_counts = Counter()
    per_year = defaultdict(Counter)
    mayor_votes = []; six = []; tally_mm = []; outcome_iss = []; size_iss = []
    contested = []; unknown = Counter()

    for jp in sorted(iter_jsons()):
        mtg = json.load(open(jp, encoding="utf-8"))
        meetings += 1
        if mtg["votes"]:
            mtgs_with_motion += 1
        year = mtg["date"][:4]
        city_era = mtg["date"] >= "2026-01-01"
        for v in mtg["votes"]:
            motions += 1
            body_counts[v.get("body", "Council")] += 1
            type_counts[v["motion_type"]] += 1
            aye, nay, ab, absent, rec = v["aye"], v["nay"], v["abstain"], v["absent"], v["recuse"]
            voters = aye + nay + ab + absent + rec
            for nm in voters:
                per_year[year][nm] += 1
                if nm not in ROSTER:
                    unknown[nm] += 1
            if v.get("mayor_voted"):
                mayor_votes.append(f"{mtg['date']} m{v['motion_no']} {v['result']} :: {v['motion'][:70]}")
            if len(voters) > COUNCIL_SIZE:
                six.append(f"{mtg['date']} m{v['motion_no']}: {len(voters)} voters :: aye={aye} nay={nay}")
            if nay or ab or rec:
                contested.append(f"{mtg['date']} [{v.get('body')}] m{v['motion_no']} {v['result']} | "
                                 f"AYE={aye} NAY={nay} ABSTAIN={ab} ABSENT={absent} :: {v['motion'][:75]}")
            if not v.get("names_recorded"):
                continue
            na, nn = len(aye), len(nay)
            pt = v.get("printed_tally")
            if pt and sorted([na, nn]) != sorted(list(pt)):
                tally_mm.append(f"{mtg['date']} m{v['motion_no']}: named {na}-{nn} vs printed "
                                f"{pt[0]}-{pt[1]} :: {v['result']} :: {v['motion'][:50]}")
            out = v["result"].split()[-1] if v["result"] else ""
            if out == "Pass" and nn and na <= nn:
                outcome_iss.append(f"{mtg['date']} m{v['motion_no']}: PASS but aye{na}<=nay{nn} :: {v['result']}")
            seated = len(voters)
            if seated and seated != COUNCIL_SIZE:
                size_iss.append(f"{mtg['date']} m{v['motion_no']}: {seated} seated (exp {COUNCIL_SIZE}) "
                                f":: {v['motion'][:50]}")

    L = []; w = L.append
    w("Magna City / Metro Township Council — vote extraction validation report")
    w("=" * 74)
    w(f"Meeting JSONs             : {meetings}")
    w(f"Meetings with >= 1 motion : {mtgs_with_motion}")
    w(f"Motions extracted         : {motions}")
    w("\nBody counts:")
    for b in sorted(body_counts):
        w(f"   {b:16s} {body_counts[b]}")
    w("\nMotion-type distribution:")
    for t, c in type_counts.most_common():
        w(f"   {t:28s} {c}")
    w("\n" + "-" * 74)
    w("PER-YEAR OBSERVED-VOTER ROSTER (name -> recorded vote rows that year).")
    w("SEAM: the presiding 'Mayor' is a VOTING chair <=2025 (Peay 2018-23, Barney 24-25)")
    w("and the NON-voting executive Mayor Sudbury 2026+. Max council tally = 5 both eras.")
    w("-" * 74)
    for year in sorted(per_year):
        w(f"\n{year}:")
        for nm, c in per_year[year].most_common():
            flag = "  <-- NON-ROSTER (investigate)" if nm not in ROSTER else \
                   ("  <-- chair/Mayor (voting this era)" if nm in CHAIR_MAYORS else
                    ("  <-- Mayor (should be non-voting)" if nm == CITY_MAYOR and year >= "2026" else ""))
            w(f"   {nm:20s} {c}{flag}")
    if unknown:
        w("\nNON-ROSTER NAMES receiving a vote row:")
        for nm, c in unknown.most_common():
            w(f"   {nm} ({c})")
    for title, items, note in [
        (f"MAYOR-VOTE FLAGS (city-era Mayor Sudbury recorded voting): {len(mayor_votes)}", mayor_votes,
         "Sudbury is non-voting from 2026 — any hit is a real recorded event to review."),
        (f">{COUNCIL_SIZE}-VOTER FLAGS: {len(six)}", six, ""),
        (f"TALLY-VS-NAMED MISMATCHES (full roll calls): {len(tally_mm)}", tally_mm, ""),
        (f"OUTCOME-VS-COUNT INCONSISTENCIES: {len(outcome_iss)}", outcome_iss, ""),
        (f"ROSTER-SIZE DEVIATIONS (named rolls seated != {COUNCIL_SIZE}): {len(size_iss)}", size_iss,
         "Expected on any motion with a member absent/excused."),
        (f"CONTESTED VOTES (any Nay/Abstain/Recuse) — the signal: {len(contested)}", contested, ""),
    ]:
        w("\n" + "-" * 74); w(title)
        if note:
            w(note)
        w("-" * 74)
        for ln in items or ["   (none)"]:
            w("   " + ln if not ln.startswith("   ") else ln)

    os.makedirs(VOTES_DIR, exist_ok=True)
    open(REPORT, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"Wrote {REPORT}")
    print(f"meetings={meetings} (with_motion={mtgs_with_motion}) motions={motions} body={dict(body_counts)}")
    print(f"contested={len(contested)} mayor_votes={len(mayor_votes)} six={len(six)} "
          f"tally_mm={len(tally_mm)} outcome_iss={len(outcome_iss)} size_dev={len(size_iss)} "
          f"non_roster={len(unknown)}")


if __name__ == "__main__":
    main()
