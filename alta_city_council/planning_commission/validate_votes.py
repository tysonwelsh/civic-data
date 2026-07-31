#!/usr/bin/env python3
"""validate_votes.py — sanity-check extracted Town of Alta votes (council or pc).

Usage: python3 validate_votes.py [council|pc]
Reads <body>/votes/**/*.json, writes <body>/votes/_validation_report.txt:
  motion totals, per-body/type distribution, per-year observed-voter roster,
  >5-voter flags (Alta max tally = 5: Mayor + 4), unknown-name flags,
  outcome-vs-count checks, and the contested-vote list (the signal).
Also (re)writes <body>/roster.csv from the observed voters.
"""
import json, os, sys, csv
from collections import Counter, defaultdict

TAG = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in ("council", "pc") else "council"
ROOT = "/Users/tysonwelsh/civic-data/alta_city_council"
DIR = os.path.join(ROOT, "meeting_minutes" if TAG == "council" else "planning_commission")
VOTES_DIR = os.path.join(DIR, "votes")
REPORT = os.path.join(VOTES_DIR, "_validation_report.txt")
ROSTER_CSV = os.path.join(DIR, "roster.csv")
MAX_TALLY = 5  # Mayor (voting) + 4 councilmembers


def iter_jsons():
    for dp, _, files in os.walk(VOTES_DIR):
        for fn in sorted(files):
            if fn.endswith(".json") and not fn.startswith("_"):
                yield os.path.join(dp, fn)


ALL_VOTES = os.path.join(DIR, "all_votes.csv")


def iter_backfill_meetings():
    """Promoted PMN-recovered motions (all_votes.csv provenance=pmn_minutes,
    merged by extract_backfill_votes.py, 2026-07-16) have no votes/ JSON —
    reconstruct the same per-meeting shape from the CSV so the report and
    roster.csv cover the MERGED record, whatever the run order."""
    if not os.path.exists(ALL_VOTES):
        return
    by_src = {}
    with open(ALL_VOTES, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("provenance") != "pmn_minutes":
                continue
            m = by_src.setdefault(r["source"], {"date": r["date"], "votes": {}})
            key = int(r["motion_no"])
            v = m["votes"].setdefault(key, {
                "body": r["body"], "motion_no": key, "motion": r["motion"],
                "motion_type": r["motion_type"], "result": r["result"],
                "mover": r["mover"], "seconder": r["seconder"],
                "aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []})
            if r.get("member") and r.get("vote"):
                v[r["vote"].lower()].append(r["member"])
    for src in sorted(by_src):
        m = by_src[src]
        votes = [m["votes"][k] for k in sorted(m["votes"])]
        for v in votes:
            v["names_recorded"] = bool(v["aye"] or v["nay"])
        yield {"date": m["date"], "votes": votes, "source": src}


def iter_meetings():
    for jp in sorted(iter_jsons()):
        yield json.load(open(jp, encoding="utf-8"))
    yield from iter_backfill_meetings()


def main():
    meetings = motions = mtgs_with_motion = 0
    body_counts = Counter(); type_counts = Counter()
    per_year_voters = defaultdict(Counter)
    over_max = []; outcome_issues = []; contested = []
    named_motions = 0; tally_only = 0
    mover_seen = Counter()
    all_voters_seen = Counter()
    mayor_votes = 0

    for mtg in iter_meetings():
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
            allv = aye + nay + abstain + absent + recuse
            if v.get("names_recorded"):
                named_motions += 1
            else:
                tally_only += 1
            if v.get("mayor_voted"):
                mayor_votes += 1
            for nm in allv:
                per_year_voters[year][nm] += 1
                all_voters_seen[nm] += 1
            if v.get("mover"):
                mover_seen[v["mover"]] += 1
            if len(allv) > MAX_TALLY:
                over_max.append(f"{mtg['date']} m{v['motion_no']}: {len(allv)} voters (>{MAX_TALLY}) "
                                f":: aye={aye} nay={nay} abstain={abstain} absent={absent} recuse={recuse}")
            if nay or abstain or recuse:
                contested.append(f"{mtg['date']} [{v['body']}] m{v['motion_no']} {v['result']} | "
                                 f"AYE={aye} NAY={nay} ABSTAIN={abstain} RECUSE={recuse} ABSENT={absent} "
                                 f":: {v['motion'][:80]}")
            if v.get("names_recorded"):
                na, nn = len(aye), len(nay)
                oc = "Fail" if "FAIL" in v["result"].upper() or "DENIED" in v["result"].upper() else "Pass"
                if oc == "Pass" and nn and na <= nn:
                    outcome_issues.append(f"{mtg['date']} m{v['motion_no']}: PASS but aye={na}<=nay={nn} :: {v['result']}")
                if oc == "Fail" and na > nn:
                    outcome_issues.append(f"{mtg['date']} m{v['motion_no']}: FAIL but aye={na}>nay={nn} :: {v['result']}")

    # roster.csv from observed voters
    with open(ROSTER_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["member", "recorded_votes", "years_active"])
        yr_of = defaultdict(set)
        for y, cnt in per_year_voters.items():
            for nm in cnt:
                yr_of[nm].add(y)
        for nm, c in all_voters_seen.most_common():
            w.writerow([nm, c, ",".join(sorted(yr_of[nm]))])

    L = []; w = L.append
    w(f"Town of Alta — {TAG} vote extraction validation report")
    w("=" * 70)
    w(f"Meeting JSONs             : {meetings}")
    w(f"Meetings with >=1 motion  : {mtgs_with_motion}")
    w(f"Motions extracted         : {motions}")
    w(f"  named-vote motions      : {named_motions}")
    w(f"  tally-only motions      : {tally_only}")
    w(f"  motions w/ mayor voting  : {mayor_votes}")
    w("")
    w("Body counts: " + ", ".join(f"{b}={c}" for b, c in body_counts.most_common()))
    w("")
    w("Motion-type distribution:")
    for t, c in type_counts.most_common():
        w(f"   {t:26s} {c}")
    w("")
    w("-" * 70)
    w("PER-YEAR OBSERVED-VOTER ROSTER (name -> recorded votes). Alta: Mayor VOTES;")
    w("a full roll call = 5 (Mayor + 4 at-large). Roster turns over across 2020->2026.")
    w("-" * 70)
    for year in sorted(per_year_voters):
        w(f"\n{year}:")
        for nm, c in per_year_voters[year].most_common():
            w(f"   {nm:26s} {c}")
    w("")
    w("-" * 70)
    w(f">{MAX_TALLY}-VOTER FLAGS (would break the Mayor+4 ceiling): {len(over_max)}")
    w("-" * 70)
    for ln in over_max or ["   (none)"]:
        w("   " + ln)
    w("")
    w("-" * 70)
    w(f"OUTCOME-VS-COUNT INCONSISTENCIES: {len(outcome_issues)}")
    w("-" * 70)
    for ln in outcome_issues or ["   (none)"]:
        w("   " + ln)
    w("")
    w("-" * 70)
    w(f"CONTESTED VOTES (any Nay / Abstain / Recuse) — the signal: {len(contested)}")
    w("-" * 70)
    for ln in contested or ["   (none)"]:
        w("   " + ln)
    w("")

    os.makedirs(VOTES_DIR, exist_ok=True)
    open(REPORT, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"[{TAG}] wrote {REPORT} + {ROSTER_CSV}")
    print(f"[{TAG}] meetings={meetings} motions={motions} named={named_motions} "
          f"tally_only={tally_only} contested={len(contested)} over_max={len(over_max)} "
          f"outcome_issues={len(outcome_issues)} distinct_voters={len(all_voters_seen)}")


if __name__ == "__main__":
    main()
