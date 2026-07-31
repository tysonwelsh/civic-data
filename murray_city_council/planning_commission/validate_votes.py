#!/usr/bin/env python3
"""
validate_votes.py — sanity-check the extracted Murray Planning Commission vote JSONs.

Reads planning_commission/votes/<year>/<week>/*.json -> _validation_report.txt.

HARD checks (nonzero exit on failure):
  * every named voter resolves to the commissioner roster;
  * every vote value is in the §4 vocabulary (Aye|Nay|Abstain|Recuse|Absent|Excused);
  * no roll call seats more than 7 members (the PC has 7 commissioners).
SOFT checks (reported, never auto-corrected):
  * named aye/nay vs the minutes' own printed tally; contested-vote list.

NOTE the coverage seam: NAMED roll calls exist only in 2022; 2020-2021 are TALLY-ONLY
by source ("A voice vote was made, motion passed 7-0" — no per-member names). Blank-member
motions there are a source-format limit, not an extraction miss.
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
    "Phil Markham", "Scot Woodbury", "Travis Nay", "Maren Patterson", "Lisa Milkavich",
    "Sue Wilson", "Ned Hacker", "Jeremy Lowry", "Jake Pehrson", "Michael Richards",
    # 2023-2026 commissioners (2026-07-16 pmn_backfill promotion; verified against
    # attendance blocks — staff like Phil Markham/CED Director and David Rodgers/
    # Senior Planner never vote and are excluded from the extractor's canon)
    "Pete Hristou", "Michael Henrie", "Aaron Hildreth", "Peter Klinge", "Katie Rogers",
}
VOCAB = {"Aye", "Nay", "Abstain", "Recuse", "Absent", "Excused"}
PC_SIZE = 7


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
    named_by_year = Counter()
    tally_by_year = Counter()
    off_roster = Counter()
    bad_vocab = []
    over_seat = []
    tally_mismatch = []
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
                named_by_year[year] += 1
                for lab, names in buckets.items():
                    if lab not in VOCAB:
                        bad_vocab.append(f"{mtg['date']} m{v['motion_no']}: {lab}")
                    for nm in names:
                        per_year[year][nm] += 1
                        if nm not in ROSTER:
                            off_roster[nm] += 1
            else:
                tally += 1
                tally_by_year[year] += 1

            if len(allv) > PC_SIZE:
                over_seat.append(f"{mtg['date']} m{v['motion_no']} {v['result']}: "
                                 f"{len(allv)} seated :: {allv}")
            if v["nay"] or v["abstain"] or v["recuse"]:
                contested.append(f"{mtg['date']} m{v['motion_no']} {v['result']} | "
                                 f"NAY={v['nay']} ABSTAIN={v['abstain']} RECUSE={v['recuse']} "
                                 f":: {v['motion'][:70]}")
            if v["names_recorded"]:
                a, nn = len(v["aye"]), len(v["nay"])
                m = re.search(r"(\d+)\s*-\s*(\d+)", v["result"])
                if m and (a != int(m.group(1)) or nn != int(m.group(2))):
                    tally_mismatch.append(
                        f"{mtg['date']} m{v['motion_no']}: named {a}-{nn} vs printed "
                        f"{m.group(1)}-{m.group(2)} :: {v['result']}")

    L = []
    w = L.append
    w("Murray Planning Commission — vote extraction validation report")
    w("=" * 72)
    w(f"Meeting JSONs      : {meetings}")
    w(f"Motions extracted  : {motions}  (named {named} / tally-only {tally})")
    w(f"Distinct results   : {len(result_counts)}")
    w("")
    w("Named vs tally-only by year (named roll calls exist only in 2022 — source seam):")
    for y in sorted(set(named_by_year) | set(tally_by_year)):
        w(f"   {y}: named {named_by_year[y]:3d} / tally-only {tally_by_year[y]:3d}")
    w("")
    w("Motion-type distribution:")
    for t, c in type_counts.most_common():
        w(f"   {t:26s} {c}")
    w("")
    w("-" * 72)
    w("PER-YEAR OBSERVED-VOTER ROSTER (named vote rows only — 2022):")
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
    w(f">7-voter roll calls     : {len(over_seat)}")
    for x in over_seat:
        w("   " + x)
    w("")
    w("=" * 72)
    w("SOFT CHECKS")
    w("=" * 72)
    w(f"Tally-vs-named mismatches: {len(tally_mismatch)}")
    for x in tally_mismatch:
        w("   " + x)
    w("")
    w(f"CONTESTED VOTES (any Nay / Abstain / Recuse) — the signal: {len(contested)}")
    for x in contested:
        w("   " + x)
    w("")

    os.makedirs(VOTES_DIR, exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")

    hard = len(off_roster) + len(bad_vocab) + len(over_seat)
    print(f"Wrote {REPORT}")
    print(f"meetings={meetings} motions={motions} named={named} tally={tally} "
          f"contested={len(contested)}")
    print(f"HARD: off_roster={len(off_roster)} bad_vocab={len(bad_vocab)} "
          f"over_seat={len(over_seat)}  ||  SOFT: tally_mismatch={len(tally_mismatch)}")
    if hard:
        print("VALIDATION FAILED (hard errors present)")
        sys.exit(1)
    print("VALIDATION PASSED (0 hard errors)")


if __name__ == "__main__":
    main()
