#!/usr/bin/env python3
"""
validate_votes.py — sanity-check the extracted Riverton Planning Commission vote JSONs.

Reads planning_commission/votes/<year>/<week>/*.json -> votes/_validation_report.txt:
  1. Motion totals + motion-type / action-kind distribution.
  2. Per-year observed-commissioner roster (named votes + attendance).
  3. NON-ROSTER names that received a vote row (should be 0 — canon is closed).
  4. TALLY PLAUSIBILITY — any tally outside 1..8 voters, or a named-roll-call count that
     disagrees with the printed X-to-Y tally.
  5. Named-vs-unanimous split (Riverton names every member ONLY on divided votes).
  6. Full contested-vote list (any Nay / Abstain / Recuse, or a divided tally) — the signal.

Run:  python3 planning_commission/validate_votes.py
"""
import json
import os
from collections import Counter, defaultdict

REPO = os.path.dirname(os.path.abspath(__file__))
VOTES_DIR = os.path.join(REPO, "votes")
REPORT = os.path.join(VOTES_DIR, "_validation_report.txt")

ROSTER = {"Troy Rushton", "Shelly Cluff", "Darren Park", "Gary Cannon", "Brian Russell",
          "Evan Matheson", "Grant Lefgren", "Ed James", "Jon Gilchrist", "Natalia Brown",
          "Keith Breinholt", "Monique Beck", "Crystal Keele", "Joe Marzo", "Dennis Hansen",
          "Kent Hartley", "Chris Knudsen"}
LABEL = "Riverton Planning Commission"


def iter_jsons():
    for dp, _, files in os.walk(VOTES_DIR):
        for fn in sorted(files):
            if fn.endswith(".json") and not fn.startswith("_"):
                yield os.path.join(dp, fn)


def main():
    meetings = motions = mtgs_with_motion = 0
    type_counts = Counter()
    action_counts = Counter()
    per_year_voters = defaultdict(Counter)
    per_year_present = defaultdict(Counter)
    tally_issues = []
    contested = []
    unknown = Counter()
    named = unanimous = tally_only = died = 0

    for jp in sorted(iter_jsons()):
        with open(jp, encoding="utf-8") as f:
            mtg = json.load(f)
        meetings += 1
        if mtg["votes"]:
            mtgs_with_motion += 1
        year = mtg["date"][:4]
        for nm in mtg.get("present", []):
            per_year_present[year][nm] += 1
        for v in mtg["votes"]:
            motions += 1
            type_counts[v["motion_type"]] += 1
            action_counts[v.get("action_kind", "other")] += 1
            aye, nay = v["aye"], v["nay"]
            abstain, absent, recuse = v["abstain"], v["absent"], v["recuse"]
            all_voters = aye + nay + abstain + absent + recuse
            if v.get("names_recorded"):
                named += 1
            elif "Died" in (v["result"] or ""):
                died += 1
            elif v.get("tally_aye") is not None:
                tally_only += 1
            else:
                unanimous += 1
            for nm in all_voters:
                per_year_voters[year][nm] += 1
                if nm not in ROSTER:
                    unknown[nm] += 1

            ta, tn = v.get("tally_aye"), v.get("tally_nay")
            if ta is not None:
                tot = ta + tn
                if tot < 1 or tot > 8:
                    tally_issues.append(
                        f"{mtg['date']} m{v['motion_no']}: tally {ta}-to-{tn} "
                        f"({tot} voters, expected 1..8) :: {v['motion'][:55]}")
                if v.get("names_recorded"):
                    nn = len(aye) + len(nay) + len(abstain) + len(recuse)
                    printed = ta + tn  # abstentions may sit outside the X-to-Y
                    if nn not in (printed, printed + len(abstain)):
                        tally_issues.append(
                            f"{mtg['date']} m{v['motion_no']}: {nn} named vs printed "
                            f"{ta}-to-{tn} :: {v['motion'][:50]}")

            if nay or abstain or recuse or (ta is not None and tn and tn > 0):
                contested.append(
                    f"{mtg['date']} m{v['motion_no']} {v['result']} | AYE={aye} NAY={nay} "
                    f"ABSTAIN={abstain} RECUSE={recuse} :: {v['motion'][:70]}")

    L = []
    w = L.append
    w(f"{LABEL} — vote extraction validation report")
    w("=" * 72)
    w(f"Meeting JSONs            : {meetings}")
    w(f"Meetings with >=1 motion : {mtgs_with_motion}")
    w(f"Motions extracted        : {motions}")
    w(f"  named roll call (divided): {named}")
    w(f"  unanimous consent (unnamed): {unanimous}")
    w(f"  tally-only/other         : {tally_only}")
    w(f"  died (no second)         : {died}")
    w("\nMotion-type distribution:")
    for t, c in type_counts.most_common():
        w(f"   {t:26s} {c}")
    w("\nAction-kind distribution:")
    for t, c in action_counts.most_common():
        w(f"   {t:26s} {c}")

    w("\n" + "-" * 72)
    w("PER-YEAR OBSERVED COMMISSIONERS (attendance-present / named-vote counts).")
    w("-" * 72)
    for year in sorted(set(per_year_present) | set(per_year_voters)):
        w(f"\n{year}:")
        names = set(per_year_present[year]) | set(per_year_voters[year])
        for nm in sorted(names, key=lambda n: -per_year_present[year][n]):
            flag = "" if nm in ROSTER else "   <-- NON-ROSTER (investigate)"
            w(f"   {nm:22s} present={per_year_present[year][nm]:3d} "
              f"named_votes={per_year_voters[year][nm]:3d}{flag}")
    if unknown:
        w("\nNON-ROSTER NAMES that received a vote row (investigate):")
        for nm, c in unknown.most_common():
            w(f"   {nm}  ({c})")

    def section(title, items):
        w("\n" + "-" * 72)
        w(f"{title}: {len(items)}")
        w("-" * 72)
        for ln in items or ["   (none)"]:
            w("   " + ln if not ln.startswith("   ") else ln)

    section("TALLY-PLAUSIBILITY / named-vs-printed ISSUES", tally_issues)
    section("CONTESTED VOTES (any Nay/Abstain/Recuse or divided tally) — the signal", contested)

    os.makedirs(VOTES_DIR, exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print(f"Wrote {REPORT}")
    print(f"meetings={meetings} motions={motions} named={named} unanimous={unanimous} "
          f"tally_only={tally_only} died={died} contested={len(contested)} "
          f"tally_issues={len(tally_issues)} non_roster={len(unknown)}")


if __name__ == "__main__":
    main()
