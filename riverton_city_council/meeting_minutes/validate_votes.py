#!/usr/bin/env python3
"""
validate_votes.py — sanity-check the extracted Riverton council vote JSONs.

Reads meeting_minutes/votes/<year>/<week>/*.json -> votes/_validation_report.txt:
  1. Motion totals + motion-type distribution.
  2. Per-year observed-voter roster (confirms the 5-member bench; the Mayor should
     appear ONLY on flagged tie-break motions).
  3. MAYOR TIE-BREAK flags — every motion where the source recorded the Mayor voting.
  4. >5-VOTER flags — any ordinary motion whose seated voters exceed 5 (would mean the
     Mayor was miscounted, or a parse error).
  5. Outcome-vs-count consistency.
  6. Roster-size deviations (seated != 5 on a named roll call).
  7. Full contested-vote list (any Nay / Abstain / Recuse) — the analytical signal.

Run:  python3 meeting_minutes/validate_votes.py
"""
import json
import os
from collections import Counter, defaultdict

REPO = os.path.dirname(os.path.abspath(__file__))
VOTES_DIR = os.path.join(REPO, "votes")
REPORT = os.path.join(VOTES_DIR, "_validation_report.txt")

MAYOR_NAMES = {"Trent Staggs", "Tish Buroker"}   # Buroker is Mayor 2026+ (councilmember before)
ROSTER = {"Tish Buroker", "Spencer Haymond", "Tawnee McCay", "Troy McDougal",
          "Andy Pierucci", "Alexander Johnson", "Shannon Smith",
          "Sheldon Stewart", "Claude Wells"}
COUNCIL_SIZE = 5
LABEL = "Riverton City Council"


def iter_jsons():
    for dp, _, files in os.walk(VOTES_DIR):
        for fn in sorted(files):
            if fn.endswith(".json") and not fn.startswith("_"):
                yield os.path.join(dp, fn)


def main():
    meetings = motions = mtgs_with_motion = 0
    body_counts = Counter()
    type_counts = Counter()
    per_year_voters = defaultdict(Counter)
    tiebreaks = []
    six_voter = []
    outcome_issues = []
    size_issues = []
    contested = []
    unknown = Counter()
    named = tally_only = 0

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
            if v.get("names_recorded"):
                named += 1
            else:
                tally_only += 1
            for nm in all_voters:
                per_year_voters[year][nm] += 1
                if nm not in ROSTER and nm not in MAYOR_NAMES:
                    unknown[nm] += 1

            for tb in v.get("mayor_tiebreak", []):
                per_year_voters[year][tb["member"]] += 1
                tiebreaks.append(
                    f"{mtg['date']} m{v['motion_no']} {v['result']}: {tb['member']} "
                    f"tie-break {tb['vote'].upper()} :: {v['motion'][:70]}")

            if len(all_voters) > COUNCIL_SIZE:
                six_voter.append(
                    f"{mtg['date']} m{v['motion_no']}: {len(all_voters)} voters (>{COUNCIL_SIZE})"
                    f" :: aye={aye} nay={nay}")

            if nay or abstain or recuse or v.get("mayor_tiebreak"):
                contested.append(
                    f"{mtg['date']} m{v['motion_no']} {v['result']} | AYE={aye} NAY={nay} "
                    f"ABSTAIN={abstain} RECUSE={recuse} ABSENT={absent} "
                    f"TIEBREAK={v.get('mayor_tiebreak')} :: {v['motion'][:70]}")

            if not v.get("names_recorded"):
                continue
            n_aye, n_nay = len(aye), len(nay)
            outcome = (v["result"].split()[0] if v["result"] else "").lower()
            tb_aye = sum(1 for t in v.get("mayor_tiebreak", []) if t["vote"] == "aye")
            tb_nay = sum(1 for t in v.get("mayor_tiebreak", []) if t["vote"] == "nay")
            if outcome.startswith("pass") and (n_aye + tb_aye) <= (n_nay + tb_nay):
                outcome_issues.append(
                    f"{mtg['date']} m{v['motion_no']}: PASS but aye={n_aye}(+{tb_aye}) "
                    f"<= nay={n_nay}(+{tb_nay}) :: {v['result']}")
            if outcome.startswith("fail") and (n_aye + tb_aye) > (n_nay + tb_nay):
                outcome_issues.append(
                    f"{mtg['date']} m{v['motion_no']}: FAIL but aye>{n_nay} :: {v['result']}")
            seated = len(all_voters)
            if seated != COUNCIL_SIZE:
                size_issues.append(
                    f"{mtg['date']} m{v['motion_no']}: {seated} seated (expected "
                    f"{COUNCIL_SIZE}) :: {v['motion'][:55]}")

    L = []
    w = L.append
    w(f"{LABEL} — vote extraction validation report")
    w("=" * 72)
    w(f"Meeting JSONs            : {meetings}")
    w(f"Meetings with >=1 motion : {mtgs_with_motion}")
    w(f"Motions extracted        : {motions}  (named roll calls {named} / tally-only {tally_only})")
    w("")
    w("Body counts:")
    for b in sorted(body_counts):
        w(f"   {b:8s} {body_counts[b]}")
    w("\nMotion-type distribution:")
    for t, c in type_counts.most_common():
        w(f"   {t:26s} {c}")
    w("\n" + "-" * 72)
    w("PER-YEAR OBSERVED-VOTER ROSTER (name -> recorded votes that year).")
    w("Expected bench: Stewart, McDougal, Buroker, Wells, McCay (2020-2022);")
    w("Pierucci replaces Stewart (2023); Haymond replaces Wells (2024);")
    w("Pierucci, McDougal, Johnson, Smith, Haymond (2026+). Mayor only on tie-breaks.")
    w("-" * 72)
    for year in sorted(per_year_voters):
        w(f"\n{year}:")
        for nm, c in per_year_voters[year].most_common():
            flag = "   <-- MAYOR (tie-break only)" if nm in MAYOR_NAMES and nm not in ROSTER \
                else ("   <-- NON-ROSTER (investigate)" if nm not in ROSTER
                      and nm not in MAYOR_NAMES else "")
            w(f"   {nm:22s} {c}{flag}")
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

    section("MAYOR TIE-BREAK FLAGS (source recorded the Mayor voting)", tiebreaks)
    section(f">{COUNCIL_SIZE}-VOTER FLAGS", six_voter)
    section("OUTCOME-VS-COUNT INCONSISTENCIES", outcome_issues)
    section(f"ROSTER-SIZE DEVIATIONS (named roll calls, seated != {COUNCIL_SIZE})", size_issues)
    section("CONTESTED VOTES (any Nay/Abstain/Recuse/tie-break) — the signal", contested)

    os.makedirs(VOTES_DIR, exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print(f"Wrote {REPORT}")
    print(f"meetings={meetings} motions={motions} named={named} tally_only={tally_only} "
          f"contested={len(contested)} tiebreaks={len(tiebreaks)} "
          f"six_voter={len(six_voter)} outcome_issues={len(outcome_issues)} "
          f"size_dev={len(size_issues)} non_roster={len(unknown)}")


if __name__ == "__main__":
    main()
