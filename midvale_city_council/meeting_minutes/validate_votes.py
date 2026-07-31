#!/usr/bin/env python3
"""
validate_votes.py — sanity-check the extracted Midvale vote JSONs (both bodies; the body is
inferred from the parent directory). Writes votes/_validation_report.txt covering:

  1. Motion totals, per-body counts, motion-type distribution.
  2. Per-year observed-voter roster (name -> recorded votes). Midvale's roster CHANGES across
     2020-2026 (no hard-coded roster) — this table IS the evidence of who served when.
  3. MAYOR-VOTE flags (council): motions where the source recorded the Mayor casting a vote
     (a genuine tie-break — the Mayor is otherwise non-voting; max ordinary tally = 5).
  4. OVERSIZE roll calls: named voters exceeding the expected chamber size (council 5 district
     members; PC ~5-7 commissioners) — a parse leak or a real quirk to eyeball.
  5. Outcome-vs-count inconsistencies (a Pass whose ayes don't beat nays, etc.).
  6. Contested votes (any Nay / Abstain / Recuse) — the analytical signal.
  7. RARE names (appear <= 1 time) — likely OCR garble to spot-check, never auto-fixed.

Run:  python3 validate_votes.py
"""
import json, os, re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BODY = "pc" if ROOT.name == "planning_commission" else "council"
LABEL = "Planning & Zoning Commission" if BODY == "pc" else "City Council"
VOTES_DIR = ROOT / "votes"
REPORT = VOTES_DIR / "_validation_report.txt"
EXPECTED_SIZE = 5 if BODY == "council" else 7   # council 5 districts; PC up to 7 seats


def iter_jsons():
    for dp, _, files in os.walk(VOTES_DIR):
        for fn in sorted(files):
            if fn.endswith(".json") and not fn.startswith("_"):
                yield os.path.join(dp, fn)


def main():
    meetings = motions = mtgs_with_motion = 0
    body_counts = Counter(); type_counts = Counter()
    per_year = defaultdict(Counter)
    name_freq = Counter()
    mayor_votes = []; oversize = []; outcome_issues = []; contested = []

    for jp in sorted(iter_jsons()):
        mtg = json.load(open(jp, encoding="utf-8"))
        meetings += 1
        if mtg["votes"]:
            mtgs_with_motion += 1
        year = mtg["date"][:4]
        for v in mtg["votes"]:
            motions += 1
            body_counts[v.get("body", LABEL)] += 1
            type_counts[v["motion_type"]] += 1
            aye, nay = v["aye"], v["nay"]
            ab, absent, rec = v["abstain"], v["absent"], v["recuse"]
            voters = aye + nay + ab + absent + rec
            for nm in voters:
                per_year[year][nm] += 1
                name_freq[nm] += 1

            if v.get("mayor_voted"):
                mayor_votes.append(
                    f"{mtg['date']} [{v['body']}] m{v['motion_no']} {v['result']} "
                    f"mayor={v.get('mayor')} :: {v['motion'][:60]}")
            # non-absent seated voters (a tie-break legitimately makes 6 on council)
            seated = len(aye) + len(nay) + len(ab) + len(rec)
            if seated > EXPECTED_SIZE + (1 if v.get("mayor_voted") else 0):
                oversize.append(
                    f"{mtg['date']} [{v['body']}] m{v['motion_no']}: {seated} yes/no/abst "
                    f"voters :: aye={aye} nay={nay}")
            if nay or ab or rec:
                contested.append(
                    f"{mtg['date']} [{v['body']}] m{v['motion_no']} {v['result']} | "
                    f"AYE={aye} NAY={nay} ABSTAIN={ab} RECUSE={rec} ABSENT={absent} "
                    f":: {v['motion'][:70]}")
            if v.get("names_recorded"):
                na, nn = len(aye), len(nay)
                out = v["result"].split()[-1] if v["result"] else ""
                if out == "Pass" and nn and na <= nn and not v.get("mayor_voted"):
                    outcome_issues.append(f"{mtg['date']} m{v['motion_no']}: PASS but "
                                          f"aye={na}<=nay={nn} :: {v['result']}")
                if out == "Fail" and na > nn:
                    outcome_issues.append(f"{mtg['date']} m{v['motion_no']}: FAIL but "
                                          f"aye={na}>nay={nn} :: {v['result']}")

    rare = [(n, c) for n, c in name_freq.items() if c <= 1]

    L = []; w = L.append
    w(f"Midvale {LABEL} — vote extraction validation report")
    w("=" * 72)
    w(f"Meeting JSONs             : {meetings}")
    w(f"Meetings with >= 1 motion : {mtgs_with_motion}")
    w(f"Motions extracted         : {motions}")
    w(f"Distinct observed voters  : {len(name_freq)}")
    w("")
    w("Body counts:")
    for b in sorted(body_counts):
        w(f"   {b:18s} {body_counts[b]}")
    w("")
    w("Motion-type distribution:")
    for t, c in type_counts.most_common():
        w(f"   {t:26s} {c}")
    w("")
    w("-" * 72)
    w("PER-YEAR OBSERVED-VOTER ROSTER (name -> recorded vote rows that year).")
    w("Midvale's roster changes across 2020-2026; this table is the who-served-when record.")
    w("-" * 72)
    for year in sorted(per_year):
        w(f"\n{year}:")
        for nm, c in per_year[year].most_common():
            w(f"   {nm:26s} {c}")
    w("")
    w("-" * 72)
    w(f"MAYOR-VOTE FLAGS (council tie-breaks): {len(mayor_votes)}")
    w("-" * 72)
    for ln in mayor_votes or ["   (none — Mayor non-voting on all ordinary motions)"]:
        w("   " + ln if not ln.startswith("   ") else ln)
    w("")
    w("-" * 72)
    w(f"OVERSIZE ROLL CALLS (> {EXPECTED_SIZE} decisive voters): {len(oversize)}")
    w("-" * 72)
    for ln in oversize or ["   (none)"]:
        w("   " + ln if not ln.startswith("   ") else ln)
    w("")
    w("-" * 72)
    w(f"OUTCOME-VS-COUNT INCONSISTENCIES: {len(outcome_issues)}")
    w("-" * 72)
    for ln in outcome_issues or ["   (none)"]:
        w("   " + ln if not ln.startswith("   ") else ln)
    w("")
    w("-" * 72)
    w(f"RARE NAMES (<=1 occurrence — spot-check for OCR garble): {len(rare)}")
    w("-" * 72)
    for nm, c in sorted(rare):
        w(f"   {nm}")
    w("")
    w("-" * 72)
    w(f"CONTESTED VOTES (any Nay / Abstain / Recuse) — the signal: {len(contested)}")
    w("-" * 72)
    for ln in contested or ["   (none)"]:
        w("   " + ln if not ln.startswith("   ") else ln)
    w("")

    REPORT.write_text("\n".join(L))
    print("\n".join(L[:40]))
    print(f"\n... full report -> {REPORT}")


if __name__ == "__main__":
    main()
