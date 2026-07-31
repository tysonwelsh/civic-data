#!/usr/bin/env python3
"""
validate_votes.py — sanity-check the extracted South Jordan council vote JSONs.

Reads every meeting_minutes/votes/<year>/<week>/*.json and writes a human-readable
report to meeting_minutes/votes/_validation_report.txt covering:

  1. Motion totals + per-body counts (Council / RDA) + motion-type distribution.
  2. Per-year observed-voter roster (name -> recorded votes that year). Confirms the five
     district members + Marlor, and that Mayor Ramsey is NOT a routine voter.
  3. MAYOR-VOTE flags — every motion the source itself recorded the Mayor casting a vote
     (a real event: tie-break or ceremonial). Listed individually.
  4. >5-VOTER / 6th-VOTE flags — any motion whose seated voters exceed the 5 district
     members (would signal the Mayor counted, or a parse error).
  5. Tally-vs-named mismatches — for FULL (tabular) roll calls, the named aye/nay counts
     vs the minutes' own printed tally. Logged verbatim, never auto-corrected.
  6. Outcome-vs-count consistency (a Pass whose ayes don't beat nays, etc.).
  7. Roster-size deviations (seated voters != 5) — vacancy / absence / parse miss.
  8. The full contested-vote list (any Nay / Abstain / Recuse) — the analytical signal.

Run:  python3 meeting_minutes/validate_votes.py
"""
import json
import os
from collections import Counter, defaultdict

REPO = os.path.dirname(os.path.abspath(__file__))
VOTES_DIR = os.path.join(REPO, "votes")
REPORT = os.path.join(VOTES_DIR, "_validation_report.txt")

MAYOR_NAMES = {"Dawn R. Ramsey"}
ROSTER = {"Patrick Harris", "Kathie Johnson", "Don Shelton", "Tamara Zander",
          "Jason McGuire", "Brad Marlor"}
COUNCIL_SIZE = 5


def iter_jsons():
    for dp, _, files in os.walk(VOTES_DIR):
        for fn in sorted(files):
            if fn.endswith(".json") and not fn.startswith("_"):
                yield os.path.join(dp, fn)


def main():
    meetings = motions = 0
    mtgs_with_motion = 0
    body_counts = Counter()
    type_counts = Counter()
    per_year_voters = defaultdict(Counter)
    mayor_votes = []
    six_voter = []
    tally_mismatches = []
    outcome_issues = []
    size_issues = []
    contested = []
    unknown_names = Counter()

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
            all_voters = aye + nay + abstain + absent + recuse
            for nm in all_voters:
                per_year_voters[year][nm] += 1
                if nm not in ROSTER and nm not in MAYOR_NAMES:
                    unknown_names[nm] += 1

            if v.get("mayor_voted"):
                mname = v.get("mayor") or "Mayor"
                mv = ("Aye" if mname in aye else "Nay" if mname in nay
                      else "Absent" if mname in absent else "?")
                mayor_votes.append(
                    f"{mtg['date']} [{v.get('body')}] m{v['motion_no']} {v['result']}: "
                    f"{mname} voted {mv} :: {v['motion'][:70]}")

            if len(all_voters) > COUNCIL_SIZE:
                six_voter.append(
                    f"{mtg['date']} m{v['motion_no']}: {len(all_voters)} voters "
                    f"(> {COUNCIL_SIZE}) :: aye={aye} nay={nay} absent={absent} "
                    f"mayor_voted={v.get('mayor_voted')}")

            if nay or abstain or recuse:
                contested.append(
                    f"{mtg['date']} [{v.get('body')}] m{v['motion_no']} {v['result']} | "
                    f"AYE={aye} NAY={nay} ABSTAIN={abstain} RECUSE={recuse} "
                    f"ABSENT={absent} :: {v['motion'][:80]}")

            if not v.get("names_recorded"):
                continue
            n_aye, n_nay = len(aye), len(nay)

            pt = v.get("printed_tally")
            if pt:
                favor, against = pt
                if sorted([n_aye, n_nay]) != sorted([favor, against]):
                    tally_mismatches.append(
                        f"{mtg['date']} [{v.get('body')}] m{v['motion_no']}: named "
                        f"aye={n_aye} nay={n_nay} vs printed {favor}-{against} :: "
                        f"{v['result']} :: {v['motion'][:60]}")

            outcome = v["result"].split()[-1] if v["result"] else ""
            if outcome == "Pass" and n_nay and n_aye <= n_nay and not v.get("mayor_voted"):
                outcome_issues.append(
                    f"{mtg['date']} m{v['motion_no']}: PASS but aye={n_aye} <= nay={n_nay}"
                    f" :: {v['result']} :: {v['motion'][:60]}")
            if outcome == "Fail" and n_aye > n_nay:
                outcome_issues.append(
                    f"{mtg['date']} m{v['motion_no']}: FAIL but aye={n_aye} > nay={n_nay}"
                    f" :: {v['result']} :: {v['motion'][:60]}")

            seated = len(all_voters)
            if seated != COUNCIL_SIZE and not v.get("mayor_voted"):
                size_issues.append(
                    f"{mtg['date']} [{v.get('body')}] m{v['motion_no']}: {seated} seated "
                    f"(expected {COUNCIL_SIZE}) aye={n_aye} nay={n_nay} "
                    f"abstain={len(abstain)} absent={len(absent)} recuse={len(recuse)} "
                    f":: {v['motion'][:55]}")

    L = []
    w = L.append
    w("South Jordan City Council — vote extraction validation report")
    w("=" * 72)
    w(f"Meeting JSONs                : {meetings}")
    w(f"Meetings with >= 1 motion    : {mtgs_with_motion}")
    w(f"Motions extracted            : {motions}")
    w("")
    w("Body counts:")
    for b in sorted(body_counts):
        w(f"   {b:8s} {body_counts[b]}")
    w("")
    w("Motion-type distribution:")
    for t, c in type_counts.most_common():
        w(f"   {t:26s} {c}")
    w("")
    w("-" * 72)
    w("PER-YEAR OBSERVED-VOTER ROSTER (name -> recorded votes that year).")
    w("Expected voters: Harris, Johnson, Shelton, Zander, McGuire, Marlor.")
    w("Mayor Dawn R. Ramsey should appear ONLY on flagged mayor-vote motions.")
    w("-" * 72)
    for year in sorted(per_year_voters):
        w(f"\n{year}:")
        for nm, c in per_year_voters[year].most_common():
            flag = ""
            if nm in MAYOR_NAMES:
                flag = "   <-- MAYOR (should be flagged mayor-vote only)"
            elif nm not in ROSTER:
                flag = "   <-- NON-ROSTER NAME (investigate)"
            w(f"   {nm:22s} {c}{flag}")
    w("")
    if unknown_names:
        w("NON-ROSTER NAMES that received a vote row (investigate — possible bad map):")
        for nm, c in unknown_names.most_common():
            w(f"   {nm}  ({c})")
        w("")
    w("-" * 72)
    w(f"MAYOR-VOTE FLAGS (source recorded the Mayor casting a vote): {len(mayor_votes)}")
    w("A tie-break or ceremonial vote is a REAL event — Ramsey is otherwise non-voting.")
    w("-" * 72)
    for ln in mayor_votes or ["   (none)"]:
        w("   " + ln if not ln.startswith("   ") else ln)
    w("")
    w("-" * 72)
    w(f"6th-VOTE / >{COUNCIL_SIZE}-VOTER FLAGS: {len(six_voter)}")
    w("-" * 72)
    for ln in six_voter or ["   (none)"]:
        w("   " + ln if not ln.startswith("   ") else ln)
    w("")
    w("-" * 72)
    w(f"TALLY-VS-NAMED MISMATCHES (full roll calls only): {len(tally_mismatches)}")
    w("Not auto-corrected — each flags a source typo or a parse miss to hand-review.")
    w("-" * 72)
    for ln in tally_mismatches or ["   (none)"]:
        w("   " + ln if not ln.startswith("   ") else ln)
    w("")
    w("-" * 72)
    w(f"OUTCOME-VS-COUNT INCONSISTENCIES: {len(outcome_issues)}")
    w("-" * 72)
    for ln in outcome_issues or ["   (none)"]:
        w("   " + ln if not ln.startswith("   ") else ln)
    w("")
    w("-" * 72)
    w(f"ROSTER-SIZE DEVIATIONS (full roll calls with seated != {COUNCIL_SIZE}): "
      f"{len(size_issues)}")
    w("Expected: an absent member (4 seated) or a brief vacancy. All reviewed.")
    w("-" * 72)
    for ln in size_issues or ["   (none)"]:
        w("   " + ln if not ln.startswith("   ") else ln)
    w("")
    w("-" * 72)
    w(f"CONTESTED VOTES (any Nay / Abstain / Recuse) — the signal: {len(contested)}")
    w("-" * 72)
    for ln in contested or ["   (none)"]:
        w("   " + ln if not ln.startswith("   ") else ln)
    w("")

    os.makedirs(VOTES_DIR, exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")

    print(f"Wrote {REPORT}")
    print(f"meetings={meetings} (with motion={mtgs_with_motion}) motions={motions} "
          f"body={dict(body_counts)}")
    print(f"contested={len(contested)} mayor_votes={len(mayor_votes)} "
          f"six_voter={len(six_voter)} tally_mismatch={len(tally_mismatches)} "
          f"outcome_issues={len(outcome_issues)} size_dev={len(size_issues)} "
          f"non_roster={len(unknown_names)}")


if __name__ == "__main__":
    main()
