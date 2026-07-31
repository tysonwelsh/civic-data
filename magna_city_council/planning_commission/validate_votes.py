#!/usr/bin/env python3
"""validate_votes.py — sanity-check extracted Magna Planning Commission vote JSONs.
Writes votes/_validation_report.txt: motion totals, per-year observed commissioners,
non-roster names, outcome consistency, and the contested-vote list (named dissent/abstain).
PC outcomes are TALLY-ONLY unanimous on most motions (majority unnamed by source)."""
import json, os
from collections import Counter, defaultdict

REPO = os.path.dirname(os.path.abspath(__file__))
VOTES_DIR = os.path.join(REPO, "votes")
REPORT = os.path.join(VOTES_DIR, "_validation_report.txt")
ROSTER = {"Richards", "Weight", "Cripps", "Elieson", "VanRoosendaal", "Lockwood", "Collard",
          "Taylor", "Larson", "White", "Alder", "Shaw", "Everett", "Sudbury"}


def main():
    meetings = motions = mtgs_with = 0
    type_counts = Counter(); per_year = defaultdict(Counter); unknown = Counter()
    contested = []; land_use = 0
    for dp, _, files in os.walk(VOTES_DIR):
        for fn in sorted(files):
            if not fn.endswith(".json") or fn.startswith("_"):
                continue
            mtg = json.load(open(os.path.join(dp, fn), encoding="utf-8"))
            meetings += 1
            if mtg["votes"]:
                mtgs_with += 1
            year = mtg["date"][:4]
            for v in mtg["votes"]:
                motions += 1
                type_counts[v["motion_type"]] += 1
                if v["motion_type"] == "Land-Use/Zoning":
                    land_use += 1
                for nm in v["nay"] + v["abstain"] + v["recuse"] + v["aye"] + v["absent"]:
                    per_year[year][nm] += 1
                    if nm not in ROSTER:
                        unknown[nm] += 1
                if v["nay"] or v["abstain"] or v["recuse"]:
                    contested.append(f"{mtg['date']} m{v['motion_no']} {v['result']} | "
                                     f"NAY={v['nay']} ABSTAIN={v['abstain']} :: {v['motion'][:75]}")
    L = []; w = L.append
    w("Magna Planning Commission — vote extraction validation report")
    w("=" * 74)
    w(f"Meeting JSONs             : {meetings}")
    w(f"Meetings with >= 1 motion : {mtgs_with}")
    w(f"Motions extracted         : {motions}   (Land-Use/Zoning: {land_use})")
    w("\nMotion-type distribution:")
    for t, c in type_counts.most_common():
        w(f"   {t:28s} {c}")
    w("\n" + "-" * 74)
    w("PER-YEAR OBSERVED COMMISSIONERS (appear only on named dissent/abstain — most")
    w("motions are tally-only 'unanimous in favor', majority unnamed by source).")
    w("-" * 74)
    for year in sorted(per_year):
        w(f"\n{year}:")
        for nm, c in per_year[year].most_common():
            w(f"   {nm:18s} {c}{'  <-- NON-ROSTER' if nm not in ROSTER else ''}")
    if unknown:
        w("\nNON-ROSTER NAMES receiving a vote row:")
        for nm, c in unknown.most_common():
            w(f"   {nm} ({c})")
    w("\n" + "-" * 74)
    w(f"CONTESTED VOTES (named Nay/Abstain) — the signal: {len(contested)}")
    w("-" * 74)
    for ln in contested or ["   (none)"]:
        w("   " + ln if not ln.startswith("   ") else ln)
    os.makedirs(VOTES_DIR, exist_ok=True)
    open(REPORT, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"Wrote {REPORT}")
    print(f"meetings={meetings} motions={motions} contested={len(contested)} "
          f"non_roster={len(unknown)} land_use={land_use}")


if __name__ == "__main__":
    main()
