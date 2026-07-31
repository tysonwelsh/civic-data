"""build_elections.py — derive Washington County's structured contest×candidate layer
from the canonical county canvass long file.

Input:  washco_results_long.csv          (canonical tidy long — Washington County
        Clerk precinct crosstabs, 2018-2025; see normalize_canvass.py + sources.csv)
Output: election_results_by_contest.csv  (one row per contest × candidate, votes
        summed across precincts; MUNICIPAL council/mayor contests only — the same
        contract as salt_lake_county/elections/: this file loads into gov.db
        `election_result` via scripts/build_cities_db.py load_election_result()).

Modeled on salt_lake_county/elections/build_elections.py. Differences, all
source-driven:
  - jurisdiction_slug: 'st_george' is the only held city in Washington County;
    every other municipality's council/mayor contest is included with
    jurisdiction_slug='' (the schema's documented "other" value) — the contest
    string keeps the municipality name verbatim.
  - district: St George (and every Washington County municipality) elects
    at-large; Council contests get district='At-Large' ('At-Large Special' for
    the special-2-year-seat contests), Mayor ''. Seat detail stays verbatim in
    `contest`.
  - n_precincts counts NONZERO precincts: the county crosstab prints every
    precinct row for every contest (zeros outside the jurisdiction), so raw
    appearance-counting would return the county-wide precinct count. A precinct
    with genuinely zero votes cast in-contest is therefore not counted — an
    honest measurement limit of the crosstab format, documented here.
  - Pseudo-candidate columns (OVER VOTES / UNDER VOTES / WITHDREW / Withdrawn /
    Cancelled / Disqualified) are excluded from ranking; named 'Write-in'
    columns are kept (they are published tallies).
  - seats (vote_for) is '' — the machine-readable exports do not publish it
    (the official summary PDFs do; see VERIFICATION.md).

DERIVED + idempotent. Never hand-edit the output; rerun this.
"""
import csv
import os
import re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "washco_results_long.csv")
OUT = os.path.join(HERE, "election_results_by_contest.csv")

# Non-municipal-governance guard, checked BEFORE the Council/Mayor test:
# special-service districts ("Dammeron Valley Fire SSD", "New Harmony Valley
# Fire SSD Board Member", "Northwestern Fire SSD Board Member", "Gunlock Water
# Board Member"), school boards, bond/ballot questions, and the 2025 export's
# "Cancelled" column group.
NON_MUNICIPAL_RE = re.compile(
    r"\bSSD\b|BOARD MEMBER|SCHOOL|TRUSTEE|IMPROVEMENT|WATER|SEWER|"
    r"BOND|PROPOSITION|CANCELLED|HOUSE|SENATE|COMMISSION|JUDICIAL|COUNTY\b")

PSEUDO_CANDIDATE_RE = re.compile(
    r"^(OVER ?VOTES|UNDER ?VOTES|WITHDREW|WITHDRAWN|CANCELLED|DISQUALIFIED)$",
    re.IGNORECASE)


def parse_contest(contest):
    """(jurisdiction_slug, office, district) for a municipal council/mayor
    contest; ('', '', '') if not one. Only st_george maps to a repo slug."""
    up = " ".join(contest.upper().split())
    if NON_MUNICIPAL_RE.search(up):
        return None
    if "MAYOR" in up:
        office, district = "Mayor", ""
    elif "COUNCIL" in up:
        office = "Council"
        district = "At-Large Special" if "SPECIAL" in up else "At-Large"
    else:
        return None
    juris = "st_george" if "ST GEORGE" in up else ""
    return juris, office, district


def main():
    agg = defaultdict(lambda: {"votes": 0, "precincts": set(), "source": ""})
    for r in csv.DictReader(open(SRC, newline="", encoding="utf-8")):
        parsed = parse_contest(r["contest"])
        if parsed is None:
            continue
        if PSEUDO_CANDIDATE_RE.match(r["candidate"].strip()):
            continue
        key = (r["year"], r["election_type"], r["contest"], r["candidate"])
        a = agg[key]
        v = int(r["votes"]) if r["votes"] else 0
        a["votes"] += v
        if v > 0:
            a["precincts"].add(r["precinct"])   # NONZERO precincts (see header)
        a["source"] = r["source_file"]

    by_contest = defaultdict(list)
    for (year, etype, contest, cand), a in agg.items():
        by_contest[(year, etype, contest)].append((cand, a))

    rows = []
    for (year, etype, contest), cands in by_contest.items():
        juris, office, district = parse_contest(contest)
        cands.sort(key=lambda ca: ca[1]["votes"], reverse=True)
        for rank, (cand, a) in enumerate(cands, start=1):
            rows.append({
                "year": year, "election_type": etype, "contest": contest,
                "jurisdiction_slug": juris, "office": office, "district": district,
                "seats": "", "candidate": cand, "party": "",
                "votes": a["votes"], "rank_in_contest": rank,
                "n_precincts": len(a["precincts"]),
                "suppressed": "false", "source_file": a["source"],
            })

    rows.sort(key=lambda x: (x["year"], x["election_type"], x["jurisdiction_slug"],
                             x["office"], x["district"], x["contest"],
                             x["rank_in_contest"]))
    cols = ["year", "election_type", "contest", "jurisdiction_slug", "office",
            "district", "seats", "candidate", "party", "votes", "rank_in_contest",
            "n_precincts", "suppressed", "source_file"]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    n_sg = sum(1 for r in rows if r["jurisdiction_slug"] == "st_george")
    print(f"Wrote {OUT}: {len(rows)} contest x candidate rows, "
          f"{len(by_contest)} municipal council/mayor contests "
          f"({n_sg} st_george-tagged rows)")


if __name__ == "__main__":
    main()
