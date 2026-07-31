#!/usr/bin/env python3
"""validate_votes.py — Copperton PLANNING COMMISSION vote-extraction integrity report.
PC votes are tally-only (collective "Commissioners voted unanimous in favor"); named rows
appear only for a named abstention/dissent. Checks csv/json consistency, off-roster names,
per-year motion counts, and lists any named dissent. Never mutates.
"""
import os, csv, json, glob, collections, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ALL_VOTES = os.path.join(ROOT, "all_votes.csv")
VOTES_DIR = os.path.join(ROOT, "votes")
ROSTER = os.path.join(ROOT, "roster.csv")
REPORT = os.path.join(VOTES_DIR, "_validation_report.txt")


def main():
    out = []
    def p(*a):
        line = " ".join(str(x) for x in a); out.append(line); print(line)

    rows = list(csv.DictReader(open(ALL_VOTES, encoding="utf-8")))
    jfiles = glob.glob(os.path.join(VOTES_DIR, "**", "*.json"), recursive=True)
    roster = set(r["member"] for r in csv.DictReader(open(ROSTER, encoding="utf-8")))
    fails = []

    j_rows = 0
    for jf in jfiles:
        obj = json.load(open(jf, encoding="utf-8"))
        for v in obj["votes"]:
            named = sum(len(v.get(k, [])) for k in ("aye", "nay", "abstain", "recuse"))
            j_rows += named if named else 1
    by_motion = collections.defaultdict(list)
    for r in rows:
        by_motion[(r["date"], r["motion_no"])].append(r)

    p("meetings (json):", len(jfiles))
    p("meetings with >=1 recorded vote:", len(set(r["date"] for r in rows)))
    p("motions:", len(by_motion))
    p("csv rows:", len(rows), "| json-implied rows:", j_rows,
      "->", "OK" if len(rows) == j_rows else "MISMATCH")
    if len(rows) != j_rows:
        fails.append("csv/json row mismatch")

    yr = collections.Counter(k[0][:4] for k in by_motion)
    p("\nmotions by year:", dict(sorted(yr.items())))

    off = sorted(set(r["member"] for r in rows if r["member"] and r["member"] not in roster))
    p("off-roster named voters:", off if off else "none", "->", "OK" if not off else "FAIL")
    if off:
        fails.append("off-roster names")

    p("\nobserved commissioner roster (%d):" % len(roster))
    for r in csv.DictReader(open(ROSTER, encoding="utf-8")):
        p(f"  {r['member']:14s} {r['first_seen']}..{r['last_seen']}  n={r['n_meetings']}")

    dissent = [(k, v) for k, v in by_motion.items()
               if any(x["vote"] in ("Nay", "Abstain", "Recuse") for x in v)]
    p("\nnamed dissent (abstain/recuse/nay):", len(dissent))
    for k, v in sorted(dissent):
        voters = [(x["member"], x["vote"]) for x in v if x["member"]]
        p(f"  {k[0]} m{k[1]} {v[0]['motion'][:50]} | {voters}")

    p("\nRESULT:", "PASS" if not fails else "FAIL " + "; ".join(fails))
    os.makedirs(VOTES_DIR, exist_ok=True)
    open(REPORT, "w", encoding="utf-8").write("\n".join(out) + "\n")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
