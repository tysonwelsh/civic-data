#!/usr/bin/env python3
"""validate_votes.py — Copperton COUNCIL vote-extraction integrity report (never mutates).
Writes votes/_validation_report.txt and prints PASS/FAIL. Checks:
  - all_votes.csv rebuilds to the same row count as the per-meeting JSON
  - no named roll call exceeds 5 (4 Council Members + the VOTING Mayor)
  - every named voter is on the observed roster (no fabricated names)
  - named vs tally-only motion counts by year (the source-format signal)
  - contested motions (any Nay/Abstain/Recuse) listed
  - mayor-vote rows counted (the mayor is a voting member)
"""
import os, csv, json, glob, collections, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ALL_VOTES = os.path.join(ROOT, "all_votes.csv")
VOTES_DIR = os.path.join(ROOT, "votes")
ROSTER = os.path.join(ROOT, "roster.csv")
REPORT = os.path.join(VOTES_DIR, "_validation_report.txt")
MAX_TALLY = 5


def main():
    out = []
    def p(*a):
        line = " ".join(str(x) for x in a); out.append(line); print(line)

    rows = list(csv.DictReader(open(ALL_VOTES, encoding="utf-8")))
    jfiles = glob.glob(os.path.join(VOTES_DIR, "**", "*.json"), recursive=True)
    roster = set(r["member"] for r in csv.DictReader(open(ROSTER, encoding="utf-8")))
    fails = []

    # rebuild count from JSON
    j_rows = 0
    for jf in jfiles:
        obj = json.load(open(jf, encoding="utf-8"))
        for v in obj["votes"]:
            named = sum(len(v.get(k, [])) for k in ("aye", "nay", "abstain", "recuse"))
            j_rows += named if named else 1
    p("meetings (json):", len(jfiles))
    p("motions:", len(set((r["date"], r["motion_no"]) for r in rows)))
    p("csv rows:", len(rows), "| json-implied rows:", j_rows,
      "->", "OK" if len(rows) == j_rows else "MISMATCH")
    if len(rows) != j_rows:
        fails.append("csv/json row mismatch")

    # named vs tally-only by year
    by_motion = collections.defaultdict(list)
    for r in rows:
        by_motion[(r["date"], r["motion_no"])].append(r)
    named_by_yr = collections.Counter(); tally_by_yr = collections.Counter()
    for (d, _), v in by_motion.items():
        yr = d[:4]
        if any(x["member"] and x["vote"] in ("Aye", "Nay") for x in v):
            named_by_yr[yr] += 1
        else:
            tally_by_yr[yr] += 1
    p("\nnamed-rollcall vs tally-only motions by year:")
    for yr in sorted(set(named_by_yr) | set(tally_by_yr)):
        p(f"  {yr}: named {named_by_yr[yr]:3d} / tally-only {tally_by_yr[yr]:3d}")

    # max tally
    over = []
    for k, v in by_motion.items():
        n = sum(1 for x in v if x["member"])
        if n > MAX_TALLY:
            over.append((k, n))
    p("\nmax named roll size:", max((sum(1 for x in v if x['member']) for v in by_motion.values()), default=0),
      "(ceiling", str(MAX_TALLY) + ")", "->", "OK" if not over else "OVER")
    if over:
        fails.append(f"{len(over)} motions exceed max tally"); p("  OVER:", over[:5])

    # off-roster
    off = sorted(set(r["member"] for r in rows if r["member"] and r["member"] not in roster))
    p("off-roster named voters:", off if off else "none", "->", "OK" if not off else "FAIL")
    if off:
        fails.append("off-roster names")

    # mayor votes
    p("\nobserved roster (%d):" % len(roster))
    for r in csv.DictReader(open(ROSTER, encoding="utf-8")):
        p(f"  {r['member']:20s} {r['role']:16s} {r['first_seen']}..{r['last_seen']}  n={r['n_meetings']}")
    mayor_rows = sum(1 for r in rows if r["member"] == "Sean Clayton")
    p("Sean Clayton (Mayor/chair) named-vote rows:", mayor_rows)

    # contested
    contested = [(k, v) for k, v in by_motion.items()
                 if any(x["vote"] in ("Nay", "Abstain", "Recuse") for x in v)]
    p("\ncontested motions (Nay/Abstain/Recuse):", len(contested))
    for k, v in sorted(contested):
        voters = [(x["member"], x["vote"]) for x in v if x["member"]]
        p(f"  {k[0]} m{k[1]} [{v[0]['result']}] {v[0]['motion'][:55]} | {voters}")

    p("\nRESULT:", "PASS" if not fails else "FAIL " + "; ".join(fails))
    os.makedirs(VOTES_DIR, exist_ok=True)
    open(REPORT, "w", encoding="utf-8").write("\n".join(out) + "\n")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
