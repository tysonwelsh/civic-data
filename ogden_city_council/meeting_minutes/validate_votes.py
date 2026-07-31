#!/usr/bin/env python3
"""Validate extracted votes: per-member tally vs result, body counts, rosters, mismatches."""
import csv, json, re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VOTES = ROOT / "votes"
CSV = ROOT / "all_votes.csv"
REPORT = ROOT / "votes" / "_validation_report.txt"

ROSTER = {
    2020:{"Ben Nadolski","Angela Choberka","Bart E. Blair","Richard A. Hyer","Luis Lopez","Doug Stephens","Marcia L. White"},
    2021:{"Ben Nadolski","Angela Choberka","Bart E. Blair","Richard A. Hyer","Luis Lopez","Doug Stephens","Marcia L. White"},
    2022:{"Ben Nadolski","Angela Choberka","Bart E. Blair","Richard A. Hyer","Luis Lopez","Ken Richey","Marcia L. White"},
    2023:{"Ben Nadolski","Angela Choberka","Bart E. Blair","Richard A. Hyer","Luis Lopez","Ken Richey","Marcia L. White"},
    2024:{"Angela Choberka","Bart E. Blair","Dave Graf","Richard A. Hyer","Shaun Myers","Ken Richey","Marcia L. White"},
    2025:{"Angela Choberka","Bart E. Blair","Dave Graf","Richard A. Hyer","Shaun Myers","Ken Richey","Marcia L. White"},
    2026:{"Flor Lopez","Alicia Washington","Dave Graf","Richard A. Hyer","Shaun Myers","Ken Richey","Kevin Lundell"},
}
# Any name ever validly seated (to suppress false "off-roster" flags at year-boundary
# compilation splits, where a Dec meeting's vote lands in a Jan-dated file).
ALL_MEMBERS = set().union(*ROSTER.values())
MAYOR_NONVOTING = {2024:"Ben Nadolski",2025:"Ben Nadolski",2026:"Ben Nadolski",
                   2020:"Michael P. Caldwell",2021:"Michael P. Caldwell",
                   2022:"Michael P. Caldwell",2023:"Michael P. Caldwell"}

def main():
    rows = list(csv.DictReader(open(CSV)))
    L = []
    P = L.append

    # ---- counts ----
    motset = {}
    for r in rows:
        motset.setdefault((r["source"], r["motion_no"]), r)
    P(f"Meetings (JSON): {len(list(VOTES.rglob('*.json')))}")
    P(f"Motions total:   {len(motset)}")
    P(f"Member-vote rows:{len(rows)}")
    P("")
    P("Motions by body:")
    for b,c in Counter(r['body'] for r in motset.values()).most_common():
        P(f"  {b:8} {c}")
    P("")
    named = [r for r in rows if r['member']]
    P(f"Member-vote rows WITH a name: {len(named)}")
    P("Vote distribution: " + str(dict(Counter(r['vote'] for r in named))))
    P("")

    # ---- names_recorded:false but numeric tally tell ----
    P("== Motions with names recorded vs not (by year) ==")
    by_year_named = defaultdict(lambda:[0,0])
    for (src,mno),r in motset.items():
        yr = int(r['year'])
        has_names = any(rr['member'] for rr in rows if rr['source']==src and rr['motion_no']==mno)
        by_year_named[yr][0 if has_names else 1] += 1
    for yr in sorted(by_year_named):
        nm, anon = by_year_named[yr]
        P(f"  {yr}: named={nm}  tally-only(no names)={anon}")
    P("")

    # ---- per-member tally vs result mismatches ----
    P("== Tally-vs-result validation (named roll-calls only) ==")
    mismatches = []
    contested = 0
    for (src,mno),r in motset.items():
        memrows = [rr for rr in rows if rr['source']==src and rr['motion_no']==mno and rr['member']]
        if not memrows:
            continue
        yr = int(r['year'])
        aye = [m['member'] for m in memrows if m['vote']=='Aye']
        nay = [m['member'] for m in memrows if m['vote']=='Nay']
        absent = [m['member'] for m in memrows if m['vote']=='Absent']
        ab = [m['member'] for m in memrows if m['vote'] in ('Abstain','Recuse')]
        if nay or ab:
            contested += 1
        # result string like "7-0 Pass"
        mres = re.match(r"(\d+)-(\d+)", r['result'] or "")
        if mres:
            ra, rn = int(mres.group(1)), int(mres.group(2))
            if ra != len(aye) or rn != len(nay):
                mismatches.append((r['date'], r['body'], mno, r['result'],
                                   f"aye={len(aye)} nay={len(nay)}"))
        # roster sanity: total accounted should be <=7, and named voters in roster
        accounted = set(aye)|set(nay)|set(absent)|set(ab)
        # off-roster = a name that is not a valid council/board member in ANY year
        # (a true off-roster member; year-boundary compilation bleed is tolerated)
        offroster = [m for m in (set(aye)|set(nay)|set(ab)) if m not in ALL_MEMBERS]
        if offroster:
            mismatches.append((r['date'], r['body'], mno, "OFF-ROSTER", ",".join(offroster)))
        # year-boundary note (member valid historically but not in this year's roster)
        boundary = [m for m in (set(aye)|set(nay)|set(ab))
                    if m in ALL_MEMBERS and m not in ROSTER.get(yr,set())]
        if boundary:
            mismatches.append((r['date'], r['body'], mno, "YEAR-BOUNDARY?", ",".join(boundary)))
        mayor = MAYOR_NONVOTING.get(yr)
        if mayor and mayor in (set(aye)|set(nay)):
            mismatches.append((r['date'], r['body'], mno, "MAYOR-VOTED", mayor))
    P(f"Contested motions (any Nay/Abstain/Recuse): {contested}")
    P(f"Tally/result mismatches: {len(mismatches)}")
    for mm in mismatches[:60]:
        P("   " + " | ".join(str(x) for x in mm))
    if len(mismatches) > 60:
        P(f"   ... +{len(mismatches)-60} more")
    P("")

    # ---- per-year roster observed ----
    P("== Observed voters by year (from named votes) ==")
    seen = defaultdict(Counter)
    for r in named:
        seen[int(r['year'])][r['member']] += 1
    for yr in sorted(seen):
        P(f"  {yr}: " + ", ".join(f"{n}({c})" for n,c in seen[yr].most_common()))
    P("")

    # ---- contested motions listing ----
    P("== Contested motions (Nay/Abstain/Recuse present) ==")
    for (src,mno),r in sorted(motset.items(), key=lambda kv:(kv[1]['date'],kv[1]['motion_no'])):
        memrows = [rr for rr in rows if rr['source']==src and rr['motion_no']==mno and rr['member']]
        nay=[m['member'] for m in memrows if m['vote']=='Nay']
        ab=[m['member'] for m in memrows if m['vote'] in ('Abstain','Recuse')]
        if nay or ab:
            P(f"  {r['date']} [{r['body']}] m{mno} {r['result']} | NAY:{','.join(nay)} | AB/REC:{','.join(ab)} | {r['motion'][:70]}")

    REPORT.write_text("\n".join(L))
    print("\n".join(L[:40]))
    print(f"\n... full report -> {REPORT}")

if __name__ == "__main__":
    main()
