#!/usr/bin/env python3
"""
validate_votes.py — sanity-check the extracted Lehi vote JSONs.

Reads every meeting_minutes/votes/<year>/<week>/*.json and writes a human-readable
report to meeting_minutes/votes/_validation_report.txt covering:

  1. Motion totals + body counts (Council / RDA / MBA).
  2. Motion-type distribution.
  3. Per-year observed-voter roster — every name that cast a recorded vote that year,
     with counts. Confirms the Mayor is NOT a routine voter (he should appear only on
     the handful of explicit tie-breaks, flagged separately).
  4. Tally-vs-result mismatches — where the count of NAMED members disagrees with the
     minutes' own PRINTED tally ("4 in favor, 1 opposed" / "carried: 4 - 0"). These are
     logged verbatim, never auto-corrected (a mismatch flags a source typo or a parse
     miss to hand-review).
  5. Outcome-vs-count consistency — a "Pass" whose aye count does not exceed its nay
     count (or vice-versa), oriented with the Mayor's tie-break folded in.
  6. Roster-size check — recorded motions where the seated voters (aye+nay+abstain+
     absent+recuse) != 5 (Lehi has 5 at-large seats; deviations flag vacancies or a
     parse miss).
  7. The full contested-vote list (any Nay / Abstain / Recuse) — the analytical signal.

Run:  python3 meeting_minutes/validate_votes.py
"""
import json
import os
from collections import Counter, defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOTES_DIR = os.path.join(REPO, "meeting_minutes", "votes")
REPORT = os.path.join(VOTES_DIR, "_validation_report.txt")

MAYOR_NAMES = {"Mark Johnson", "Paul Binns"}
COUNCIL_SIZE = 5


def iter_jsons():
    for dirpath, _, files in os.walk(VOTES_DIR):
        for fn in sorted(files):
            if fn.endswith(".json") and not fn.startswith("_"):
                yield os.path.join(dirpath, fn)


def main():
    meetings = motions = 0
    body_counts = Counter()
    type_counts = Counter()
    per_year_voters = defaultdict(Counter)     # year -> Counter(name -> votes)
    mayor_tiebreaks = []                        # (date, title, motion_no, mayor, vote)
    tally_mismatches = []
    outcome_issues = []
    size_issues = []
    contested = []

    for jp in sorted(iter_jsons()):
        with open(jp, encoding="utf-8") as f:
            mtg = json.load(f)
        meetings += 1
        date = mtg["date"]
        year = date[:4]
        title = mtg["title"]
        for v in mtg["votes"]:
            motions += 1
            body_counts[v.get("body", "Council")] += 1
            type_counts[v["motion_type"]] += 1

            aye, nay = v["aye"], v["nay"]
            abstain, absent, recuse = v["abstain"], v["absent"], v["recuse"]
            all_voters = aye + nay + abstain + absent + recuse

            for name in all_voters:
                per_year_voters[year][name] += 1

            if v.get("mayor_tiebreak"):
                mname = v.get("mayor")
                mvote = "Aye" if mname in aye else ("Nay" if mname in nay else "?")
                mayor_tiebreaks.append((date, title, v["motion_no"], mname, mvote))

            # contested = any nay/abstain/recuse among the recorded votes
            if nay or abstain or recuse:
                contested.append(
                    f"{date} [{v.get('body')}] m{v['motion_no']} {v['result']} | "
                    f"AYE={aye} NAY={nay} ABSTAIN={abstain} RECUSE={recuse} "
                    f"ABSENT={absent} :: {v['motion'][:90]}")

            if not v.get("names_recorded"):
                continue

            n_aye, n_nay = len(aye), len(nay)

            # 4. printed-tally vs named-count (unordered, abstain/absent excluded)
            pt = v.get("printed_tally")
            if pt:
                favor, against = pt
                if sorted([n_aye, n_nay]) != sorted([favor, against]):
                    tally_mismatches.append(
                        f"{date} m{v['motion_no']}: named aye={n_aye} nay={n_nay} "
                        f"but printed tally {favor}:{against} :: {v['result']} :: "
                        f"{v['motion'][:70]}")

            # 5. outcome vs counts
            outcome = v["result"].split()[-1] if v["result"] else ""
            if outcome == "Pass" and n_nay and n_aye <= n_nay:
                outcome_issues.append(
                    f"{date} m{v['motion_no']}: PASS but aye={n_aye} <= nay={n_nay} "
                    f":: {v['result']} :: {v['motion'][:70]}")
            if outcome == "Fail" and n_aye > n_nay:
                outcome_issues.append(
                    f"{date} m{v['motion_no']}: FAIL but aye={n_aye} > nay={n_nay} "
                    f":: {v['result']} :: {v['motion'][:70]}")

            # 6. roster size (Mayor counts toward the seated total only on a tie-break)
            if len(all_voters) != COUNCIL_SIZE:
                size_issues.append(
                    f"{date} [{v.get('body')}] m{v['motion_no']}: {len(all_voters)} "
                    f"voters (expected {COUNCIL_SIZE}) :: aye={n_aye} nay={n_nay} "
                    f"abstain={len(abstain)} absent={len(absent)} recuse={len(recuse)} "
                    f":: {v['motion'][:60]}")

    lines = []
    w = lines.append
    w("Lehi City Council — vote extraction validation report")
    w("=" * 72)
    w(f"Meetings with JSON : {meetings}")
    w(f"Motions extracted  : {motions}")
    w("")
    w("Body counts (RDA business is minuted in a SEPARATE record, so in-council RDA")
    w("brackets are back-to-back/empty -> RDA=0 here is expected; MBA = the standalone")
    w("Local Building Authority meetings):")
    for b in ("Council", "RDA", "MBA"):
        w(f"   {b:8s} {body_counts.get(b, 0)}")
    w("")
    w("Motion-type distribution:")
    for t, c in type_counts.most_common():
        w(f"   {t:28s} {c}")
    w("")
    w("-" * 72)
    w("PER-YEAR OBSERVED-VOTER ROSTER (name -> recorded votes that year).")
    w("The Mayor (Mark Johnson / Paul Binns) should NOT appear as a routine voter —")
    w("only on explicit tie-breaks (listed separately below).")
    w("-" * 72)
    for year in sorted(per_year_voters):
        w(f"\n{year}:")
        for name, c in per_year_voters[year].most_common():
            flag = "   <-- MAYOR (tie-break only)" if name in MAYOR_NAMES else ""
            w(f"   {name:22s} {c}{flag}")
    w("")
    w("-" * 72)
    w(f"MAYOR TIE-BREAK VOTES (Mayor cast a recorded vote): {len(mayor_tiebreaks)}")
    w("-" * 72)
    for d, t, mno, mname, mvote in mayor_tiebreaks:
        w(f"   {d} m{mno}: {mname} voted {mvote}  ({t})")
    w("")
    w("-" * 72)
    w(f"TALLY-VS-RESULT MISMATCHES (named count != minutes' printed tally): "
      f"{len(tally_mismatches)}")
    w("Not auto-corrected — each flags a source typo or a parse miss to hand-review.")
    w("-" * 72)
    for ln in tally_mismatches:
        w("   " + ln)
    if not tally_mismatches:
        w("   (none)")
    w("")
    w("-" * 72)
    w(f"OUTCOME-VS-COUNT INCONSISTENCIES: {len(outcome_issues)}")
    w("-" * 72)
    for ln in outcome_issues:
        w("   " + ln)
    if not outcome_issues:
        w("   (none)")
    w("")
    w("-" * 72)
    w(f"ROSTER-SIZE DEVIATIONS (seated voters != {COUNCIL_SIZE}): {len(size_issues)}")
    w("Usually a brief vacancy/oath-of-office period or a partial roll call; reviewed.")
    w("-" * 72)
    for ln in size_issues:
        w("   " + ln)
    if not size_issues:
        w("   (none)")
    w("")
    w("-" * 72)
    w(f"CONTESTED VOTES (any Nay / Abstain / Recuse) — the analytical signal: "
      f"{len(contested)}")
    w("-" * 72)
    for ln in contested:
        w("   " + ln)
    if not contested:
        w("   (none)")
    w("")

    os.makedirs(VOTES_DIR, exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Wrote {REPORT}")
    print(f"meetings={meetings} motions={motions} body={dict(body_counts)} "
          f"contested={len(contested)} tally_mismatches={len(tally_mismatches)} "
          f"outcome_issues={len(outcome_issues)} size_issues={len(size_issues)} "
          f"mayor_tiebreaks={len(mayor_tiebreaks)}")


if __name__ == "__main__":
    main()
