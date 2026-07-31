#!/usr/bin/env python3
"""
validate_votes.py — sanity-check the extracted South Salt Lake votes and build roster.csv.

Reads every <dataset>/votes/<year>/<week>/*.json and writes a report to
<dataset>/votes/_validation_report.txt covering:

  1. Motion totals + per-body counts + motion-type distribution + vote-mode split.
  2. Per-year OBSERVED-voter roster (name -> recorded votes). SSL's council roster evolves
     2020-2026; this surfaces who was seated each year (max tally = 7, Mayor never votes).
  3. >7-VOTER flags — any motion whose seated voters exceed 7 (would mean the Mayor was
     counted or a parse error).
  4. MAYOR-IN-ROLL flags — any vote row attributed to a Mayor/known executive (should be 0).
  5. Outcome-vs-count consistency (a Pass whose ayes don't beat nays, etc.).
  6. Roster-size deviations (seated != 7) — vacancy / absence / parse miss.
  7. The full contested-vote list (any Nay / Abstain / Recuse) — the analytical signal.

Also writes <dataset>/roster.csv (OBSERVED seats: name, first_seen, last_seen,
meetings_present, n_vote_rows).

Run:  python3 validate_votes.py
"""
import csv, json, os, re, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VOTES_DIR = ROOT / "votes"
REPORT = VOTES_DIR / "_validation_report.txt"
ROSTER_CSV = ROOT / "roster.csv"
MINUTES_DIR = ROOT / "minutes"
# expected voting seats per body: council/RDA = 7 (5 districts + 2 at-large; Mayor NON-voting),
# Planning Commission runs up to 8 commissioners. Used only for anomaly flagging.
BODY_MAX = {"Council": 7, "RDA": 7, "PlanningCommission": 8}
MAX_TALLY = 8   # global ceiling for the >N-voter parse-explosion check
MAYOR_TOKENS = {"wood", "cherie"}   # SSL executive mayor — must never appear in a roll call


def iter_jsons():
    for jp in sorted(VOTES_DIR.rglob("*.json")):
        if not jp.name.startswith("_"):
            yield jp


def main():
    meetings = motions = mtgs_with_motion = 0
    body_counts = Counter(); type_counts = Counter(); mode_counts = Counter()
    per_year_voters = defaultdict(Counter)
    over7 = []; mayor_hits = []; outcome_issues = []; size_issues = []; contested = []
    member_first = {}; member_last = {}; member_rows = Counter(); member_meetings = defaultdict(set)

    for jp in iter_jsons():
        mtg = json.loads(jp.read_text())
        meetings += 1
        if mtg["votes"]:
            mtgs_with_motion += 1
        year = (mtg["date"] or "")[:4]
        date = mtg["date"]
        for v in mtg["votes"]:
            motions += 1
            body_counts[v.get("body", "Council")] += 1
            type_counts[v["motion_type"]] += 1
            mode_counts[v.get("vote_mode", "?")] += 1
            aye, nay = v["aye"], v["nay"]
            abstain, absent, recuse = v["abstain"], v["absent"], v["recuse"]
            voters = aye + nay + abstain + absent + recuse
            seated = len(voters)
            for nm in voters:
                per_year_voters[year][nm] += 1
                member_rows[nm] += 1
                member_meetings[nm].add((v["body"], date))
                if date:
                    member_first[nm] = min(member_first.get(nm, date), date)
                    member_last[nm] = max(member_last.get(nm, date), date)
                if any(tok in nm.lower() for tok in MAYOR_TOKENS):
                    mayor_hits.append(f"{date} [{v['body']}] m{v['motion_no']}: {nm} in roll :: {v['motion'][:60]}")
            if seated > MAX_TALLY:
                over7.append(f"{date} [{v['body']}] m{v['motion_no']}: {seated} voters "
                             f"(>{MAX_TALLY}) aye={aye} nay={nay} :: {v['motion'][:55]}")
            if nay or abstain or recuse:
                contested.append(f"{date} [{v['body']}] m{v['motion_no']} {v['result']} | "
                                 f"AYE={aye} NAY={nay} ABSTAIN={abstain} RECUSE={recuse} "
                                 f"ABSENT={absent} :: {v['motion'][:70]}")
            outcome = v["result"].split()[-1] if v["result"] else ""
            na, nn = len(aye), len(nay)
            if outcome == "Pass" and nn and na <= nn:
                outcome_issues.append(f"{date} m{v['motion_no']}: PASS but aye={na}<=nay={nn} :: {v['result']} :: {v['motion'][:50]}")
            if outcome == "Fail" and na > nn:
                outcome_issues.append(f"{date} m{v['motion_no']}: FAIL but aye={na}>nay={nn} :: {v['result']} :: {v['motion'][:50]}")
            exp = BODY_MAX.get(v["body"], 7)
            if seated and seated != exp:
                size_issues.append(f"{date} [{v['body']}] m{v['motion_no']}: {seated} seated "
                                   f"(expected {exp}) aye={na} nay={nn} abstain={len(abstain)} "
                                   f"absent={len(absent)} recuse={len(recuse)} :: {v['motion'][:45]}")

    L = []; w = L.append
    w("South Salt Lake — vote extraction validation report")
    w("=" * 72)
    w(f"Meeting JSONs             : {meetings}")
    w(f"Meetings with >= 1 motion : {mtgs_with_motion}")
    w(f"Motions extracted         : {motions}")
    w("")
    w("Body counts:")
    for b in sorted(body_counts): w(f"   {b:20s} {body_counts[b]}")
    w("\nVote-mode split:")
    for m in sorted(mode_counts): w(f"   {m:20s} {mode_counts[m]}")
    w("\nMotion-type distribution:")
    for t, c in type_counts.most_common(): w(f"   {t:26s} {c}")
    w("\n" + "-" * 72)
    w("PER-YEAR OBSERVED-VOTER ROSTER (name -> recorded votes that year).")
    w("SSL council roster evolves; max tally = 7; Mayor (executive) never votes.")
    w("-" * 72)
    for year in sorted(per_year_voters):
        w(f"\n{year}:")
        for nm, c in per_year_voters[year].most_common():
            flag = "   <-- MAYOR? investigate" if any(t in nm.lower() for t in MAYOR_TOKENS) else ""
            w(f"   {nm:26s} {c}{flag}")
    w("\n" + "-" * 72)
    w(f"MAYOR-IN-ROLL FLAGS (executive should never be in a roll call): {len(mayor_hits)}")
    w("-" * 72)
    for ln in mayor_hits or ["   (none)"]: w("   " + ln)
    w("\n" + "-" * 72)
    w(f">{MAX_TALLY}-VOTER FLAGS: {len(over7)}")
    w("-" * 72)
    for ln in over7 or ["   (none)"]: w("   " + ln)
    w("\n" + "-" * 72)
    w(f"OUTCOME-VS-COUNT INCONSISTENCIES: {len(outcome_issues)}")
    w("-" * 72)
    for ln in outcome_issues or ["   (none)"]: w("   " + ln)
    w("\n" + "-" * 72)
    w(f"ROSTER-SIZE DEVIATIONS (seated != {MAX_TALLY}): {len(size_issues)}")
    w("An absent member (6 seated), a vacancy, or a parse miss. Reviewed.")
    w("-" * 72)
    for ln in size_issues[:200] or ["   (none)"]: w("   " + ln)
    if len(size_issues) > 200:
        w(f"   ... {len(size_issues)-200} more")
    w("\n" + "-" * 72)
    w(f"CONTESTED VOTES (any Nay / Abstain / Recuse) — the signal: {len(contested)}")
    w("-" * 72)
    for ln in contested or ["   (none)"]: w("   " + ln)
    w("")
    REPORT.write_text("\n".join(L) + "\n")

    # roster.csv (observed)
    with ROSTER_CSV.open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["name", "role", "first_seen", "last_seen", "meetings_present", "n_vote_rows"])
        for nm in sorted(member_rows, key=lambda x: (-member_rows[x], x)):
            wr.writerow([nm, "Council/Board Member (observed)", member_first.get(nm, ""),
                         member_last.get(nm, ""), len(member_meetings[nm]), member_rows[nm]])

    print(f"Wrote {REPORT}")
    print(f"Wrote {ROSTER_CSV} ({len(member_rows)} observed members)")
    print(f"meetings={meetings} motions={motions} body={dict(body_counts)} "
          f"mode={dict(mode_counts)}")
    print(f"contested={len(contested)} over7={len(over7)} mayor_hits={len(mayor_hits)} "
          f"outcome_issues={len(outcome_issues)} size_dev={len(size_issues)}")


if __name__ == "__main__":
    main()
