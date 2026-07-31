#!/usr/bin/env python3
"""
Filter the COUNTY CANONICAL Salt Lake County election canvass down to **Salt Lake City
Council and Mayoral races only**, normalize the messy contest names, and produce
analysis-ready tables.

Source (re-pointed 2026-07-19, the deferred "re-point the 7 city election pipelines"
item — SLC slice): ../../salt_lake_county/elections/slco_municipal_results_long.csv,
the canonical SLCo Clerk SOVC in tidy long form (2007-2025, every municipality,
primaries + generals). This replaced the folder's redundant per-year
{year}_municipal_{primary|general}.csv raw copies, which were proven byte-identical
to the canonical filtered by (year, election_type) — modulo the county's later
lead-(v) `precinct='Cumulative'` relabel of 638 zero-vote report-template rows —
and then deleted (backups: _backups/2026-07-19-pv-tierb-low/lead-tu-slc/).
The regenerated slc_races.csv was proven BYTE-IDENTICAL across the re-point before
the 2019-primary scope extension. The county canonical is read-only input here;
its own provenance is salt_lake_county/elections/CLAUDE.md + raw/SOURCES.md.

Contest naming is inconsistent across years -- e.g. "SALT LAKE CITY COUNCIL
DISTRICT 1", "... CNCL DIST 1" (2017), "... COUNCIL #4" (2007), "Salt Lake City
Council 2" (2011), "SLC Mayor" (2019). Must match SLC proper, NOT
"SOUTH SALT LAKE" / "SSL".

Outputs:
  slc_results_by_precinct.csv   filtered precinct x candidate rows (geographic analysis)
                                (rows with precinct='Cumulative' are the workbook's own
                                zero-vote rollup label, not a precinct -- see the county
                                elections CLAUDE.md)
  slc_results_by_candidate.csv  race x candidate totals: votes, pct, rank, is_winner
  slc_races.csv                 one row per race: winner, runner-up, margin, turnout
                                (the headline file -- sort by margin_pct for closest races)
                                Written in the repo-wide 25-col superset header
                                (SCHEMA_SPEC.md 9, adopted 2026-07-07); the columns this
                                pipeline cannot derive from the long file stay BLANK
                                (= the county didn't publish it here, never inferred).

Usage:  python3 clean_elections.py   (add --report for a summary)
"""

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent
CANONICAL = (BASE.parent.parent / "salt_lake_county" / "elections"
             / "slco_municipal_results_long.csv")


def normalize_contest(contest):
    """Map a raw contest label to (office, district, canonical) for SLC races, else None."""
    u = contest.strip().upper()
    if not (u.startswith("SALT LAKE CITY") or u.startswith("SLC ")):
        return None                      # excludes SOUTH SALT LAKE / SSL / county
    if "SCHOOL" in u:
        return None
    if "MAYOR" in u:
        return ("Mayor", "", "Salt Lake City Mayor")
    if "COUNCIL" in u or "CNCL" in u:
        nums = re.findall(r"\d+", u)
        d = nums[-1] if nums else ""
        return ("Council", d, f"Salt Lake City Council District {d}" if d
                else "Salt Lake City Council")
    return None


def is_tally_row(candidate):
    """True for non-candidate aggregate rows that must not count as a candidate."""
    return candidate.strip().lower() in {"total", "totals", ""}


def to_float(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def load_filtered():
    """Yield normalized SLC council/mayor candidate rows from the county canonical.

    Rows are grouped by (year, election_type) and the groups iterated in sorted
    order (general before primary within a year -- matching the retired per-year
    files' glob order) with the canonical's row order preserved within each group,
    so the emitted precinct file and all tie-break-sensitive orderings are stable
    across the re-point.
    """
    groups = defaultdict(list)
    with open(CANONICAL, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            groups[(r.get("year", "").strip(),
                    r.get("election_type", "").strip())].append(r)
    for key in sorted(groups):
        for r in groups[key]:
            norm = normalize_contest(r.get("contest", ""))
            if not norm or is_tally_row(r.get("candidate", "")):
                continue
            office, district, canonical = norm
            yield {
                "year": r.get("year", "").strip(),
                "election_type": r.get("election_type", "").strip(),
                "office": office, "district": district, "contest": canonical,
                "precinct": r.get("precinct", "").strip(),
                "candidate": r.get("candidate", "").strip(),
                "votes": to_float(r.get("votes")),
                "raw_contest": r.get("contest", "").strip(),
            }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()

    rows = list(load_filtered())

    # ---- precinct x candidate (faithful, filtered) ----
    pcols = ["year", "election_type", "office", "district", "contest",
             "precinct", "candidate", "votes"]
    with open(BASE / "slc_results_by_precinct.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=pcols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({**r, "votes": int(r["votes"])})

    # ---- race x candidate totals ----
    race_key = lambda r: (r["year"], r["election_type"], r["office"], r["district"], r["contest"])
    by_cand = defaultdict(float)
    for r in rows:
        by_cand[(race_key(r), r["candidate"])] += r["votes"]

    races = defaultdict(list)            # race_key -> [(candidate, votes)]
    for (rk, cand), v in by_cand.items():
        races[rk].append((cand, v))

    cand_rows, race_rows = [], []
    for rk, cands in races.items():
        cands.sort(key=lambda x: -x[1])
        total = sum(v for _, v in cands) or 1
        for rank, (cand, v) in enumerate(cands, 1):
            cand_rows.append({
                "year": rk[0], "election_type": rk[1], "office": rk[2],
                "district": rk[3], "contest": rk[4], "candidate": cand,
                "votes": int(v), "pct": round(v / total * 100, 2),
                "rank": rank, "is_winner": rank == 1,
            })
        win, win_v = cands[0]
        run, run_v = cands[1] if len(cands) > 1 else ("", 0.0)
        race_rows.append({
            "year": rk[0], "election_type": rk[1], "office": rk[2], "district": rk[3],
            "contest": rk[4], "n_candidates": len(cands), "total_votes": int(total),
            "winner": win, "winner_votes": int(win_v),
            "winner_pct": round(win_v / total * 100, 2),
            "runner_up": run, "runner_up_votes": int(run_v),
            "margin_votes": int(win_v - run_v),
            "margin_pct": round((win_v - run_v) / total * 100, 2),
        })

    ccols = ["year", "election_type", "office", "district", "contest", "candidate",
             "votes", "pct", "rank", "is_winner"]
    cand_rows.sort(key=lambda r: (r["year"], r["election_type"], r["contest"], r["rank"]))
    with open(BASE / "slc_results_by_candidate.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ccols); w.writeheader(); w.writerows(cand_rows)

    # SCHEMA_SPEC.md 9 25-col superset (adopted 2026-07-07). Columns not derivable
    # from the county long files are left blank -- honest gaps, never inferred.
    rcols = ["year", "election_type", "office", "district", "contest",
             "contest_verbatim", "n_seats", "n_candidates", "voting_method",
             "total_votes", "total_first_choice_votes", "winner", "winner_votes",
             "winner_pct", "runner_up", "runner_up_votes", "margin_votes",
             "margin_pct", "registered_voters", "ballots_cast", "turnout_pct",
             "uncontested", "suppressed_precincts", "note", "source_file"]
    race_rows.sort(key=lambda r: (r["year"], r["election_type"], r["contest"]))
    with open(BASE / "slc_races.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rcols, restval="")
        w.writeheader(); w.writerows(race_rows)

    print(f"Filtered to SLC council/mayor: {len(rows)} precinct-candidate rows, "
          f"{len(cand_rows)} race-candidate rows, {len(race_rows)} races.")

    if args.report:
        gen = [r for r in race_rows if r["election_type"].endswith("general")]
        print("\nClosest SLC general-election races (by margin %):")
        for r in sorted(gen, key=lambda x: x["margin_pct"])[:10]:
            print(f"  {r['year']} {r['contest']:38s} {r['winner']} "
                  f"{r['winner_votes']}-{r['runner_up_votes']} "
                  f"(+{r['margin_pct']}%, {r['margin_votes']} votes)")


if __name__ == "__main__":
    main()
