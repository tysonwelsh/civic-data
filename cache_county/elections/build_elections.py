"""build_elections.py — derive the county's structured contest×candidate layer
from the canonical Cache County municipal canvass long file.

Input:  cache_municipal_results_long.csv  (canonical tidy long — Cache County
        Clerk canvass PDFs 2021-2023 + the Enhanced Voting state portal 2025,
        precinct × candidate; see parse_canvass.py + sources.csv.)
Output: election_results_by_contest.csv   (one row per contest × candidate,
        MUNICIPAL council/mayor contests only, jurisdiction_slug-tagged for
        every Cache municipality — 'logan' is the held city. Conforms to
        scripts/build_cities_db.py load_election_result(): 14 columns identical
        to salt_lake_county/elections/election_results_by_contest.csv.)

Aggregation (differs from SLCo only where the sources differ — documented):
- A contest with precinct='Electionwide' rows (summary-grain PDFs; the 2025
  portal's own summary totals) takes its votes FROM those rows — for 2025 the
  portal summary is authoritative and its precinct breakdown undercounts by a
  small unassigned bucket (1-3 votes; see VERIFICATION.md), the same artifact
  the logan city module documented. Contests without Electionwide rows sum
  their precinct rows (proven exact against the official summary PDFs).
- n_precincts counts real precincts only (never 'Electionwide').
- Aggregate pseudo-candidates are excluded from ranking ('Write-In Totals',
  'Not Assigned', bare 'Write-in', 'Write-in: Not Assigned', 'Write-In:
  Invalid') — they aggregate or bucket other rows and would corrupt
  rank_in_contest (the SLCo pseudo-candidate lesson). NAMED write-ins stay:
  'Write-In: David E. Lee' WON the 2023 Amalga 2yr seat.
- 'CANDIDATE DISQUALIFIED' (2021 primary Lewiston, the source's own text) is
  kept verbatim; the four printed rows aggregate to one 0-vote row.

DERIVED + idempotent. Never hand-edit the output; rerun this. Logan's audited
winner/margin layer stays in logan_city_council/election_results/ (gov.db
election_race); this table is the honest underlying county-grain tallies.
RCV NOTE: no contest in this canvass was tabulated by RCV — Nibley's 2021 RCV
election was self-administered and is ABSENT from the county canvass (see
VERIFICATION.md); rank_in_contest here is always plurality order.
"""
import csv
import os
import re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "cache_municipal_results_long.csv")
OUT = os.path.join(HERE, "election_results_by_contest.csv")

# Cache municipalities. Most-specific first: NORTH LOGAN and RIVER HEIGHTS
# before LOGAN / any bare token could shadow them. 'logan' is the held city.
CITY_PATTERNS = [
    ("north_logan",   [r"NORTH LOGAN"]),
    ("logan",         [r"\bLOGAN\b"]),
    ("river_heights", [r"RIVER HEIGHTS"]),
    ("hyde_park",     [r"HYDE PARK"]),
    ("amalga",        [r"AMALGA"]),
    ("clarkston",     [r"CLARKSTON"]),
    ("cornish",       [r"CORNISH"]),
    ("hyrum",         [r"HYRUM"]),
    ("lewiston",      [r"LEWISTON"]),
    ("mendon",        [r"MENDON"]),
    ("millville",     [r"MILLVILLE"]),
    ("newton",        [r"NEWTON"]),
    ("nibley",        [r"NIBLEY"]),
    ("paradise",      [r"PARADISE"]),
    ("providence",    [r"PROVIDENCE"]),
    ("richmond",      [r"RICHMOND"]),
    ("smithfield",    [r"SMITHFIELD"]),
    ("trenton",       [r"TRENTON"]),
    ("wellsville",    [r"WELLSVILLE"]),
]

# School-district / special-district / ballot-measure contests never become a
# municipal office row even when they carry a place name.
NON_MUNICIPAL_RE = re.compile(
    r"SCHOOL|BOND|PROPOSITION|TRUSTEE|IMPROVEMENT|SEWER|WATER|SERVICE AREA|"
    r"RECREATION|CEMETERY|FIRE")

# aggregate rows excluded from candidate ranking (kept in the long file)
PSEUDO = {"write-in totals", "not assigned", "write-in",
          "write-in: not assigned", "write-in: invalid"}


def parse_contest(contest):
    """(jurisdiction_slug, office, district) for a municipal council/mayor
    contest; ('', '', '') otherwise."""
    up = " ".join(contest.upper().split())
    if NON_MUNICIPAL_RE.search(up):
        return "", "", ""
    juris = ""
    for slug, pats in CITY_PATTERNS:
        if any(re.search(p, up) for p in pats):
            juris = slug
            break
    if not juris:
        return "", "", ""
    if "MAYOR" in up:
        return juris, "Mayor", ""
    if "COUNCIL" in up:
        # every Cache municipal council is at-large; seat-term variants are
        # separate contests ("- 2 Year" / "2yr" seats) — encoded in district
        # so same-year 4yr/2yr seats stay distinguishable.
        if re.search(r"2 ?-? ?(YEAR|YR)", up):
            return juris, "Council", "At-Large (2-year)"
        return juris, "Council", "At-Large"
    return "", "", ""


def party_of(candidate):
    m = re.search(r"\(([A-Z]{2,4})\)\s*$", candidate.strip())
    return m.group(1) if m else ""


def main():
    # per (year, etype, contest, candidate): electionwide + precinct-sum tallies
    agg = defaultdict(lambda: {"ew": 0.0, "has_ew": False, "ps": 0.0,
                               "precincts": set(), "source": "", "seats": "",
                               "suppressed": False})
    with open(SRC, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            juris, office, district = parse_contest(r["contest"])
            if not office:
                continue
            if r["candidate"].strip().lower() in PSEUDO:
                continue
            key = (r["year"], r["election_type"], r["contest"], r["candidate"])
            a = agg[key]
            v = 0.0
            try:
                v = float(r["votes"]) if r["votes"] != "" else 0.0
            except ValueError:
                pass
            if r["precinct"] == "Electionwide":
                a["ew"] += v
                a["has_ew"] = True
            else:
                a["ps"] += v
                if r["precinct"]:
                    a["precincts"].add(r["precinct"])
            a["source"] = r["source_file"]
            a["seats"] = r["vote_for"]
            if str(r["suppressed"]).lower() == "true":
                a["suppressed"] = True

    by_contest = defaultdict(list)
    for (year, etype, contest, cand), a in agg.items():
        by_contest[(year, etype, contest)].append((cand, a))

    rows = []
    for (year, etype, contest), cands in by_contest.items():
        juris, office, district = parse_contest(contest)
        for cand, a in cands:
            a["votes"] = a["ew"] if a["has_ew"] else a["ps"]
        cands.sort(key=lambda ca: ca[1]["votes"], reverse=True)
        for rank, (cand, a) in enumerate(cands, start=1):
            rows.append({
                "year": year, "election_type": etype,
                "contest": " ".join(contest.split()),
                "jurisdiction_slug": juris, "office": office,
                "district": district, "seats": a["seats"],
                "candidate": cand, "party": party_of(cand),
                "votes": int(round(a["votes"])),
                "rank_in_contest": rank,
                "n_precincts": len(a["precincts"]),
                "suppressed": "true" if a["suppressed"] else "false",
                "source_file": a["source"],
            })

    rows.sort(key=lambda x: (x["year"], x["election_type"],
                             x["jurisdiction_slug"], x["office"],
                             x["district"], x["rank_in_contest"]))
    cols = ["year", "election_type", "contest", "jurisdiction_slug", "office",
            "district", "seats", "candidate", "party", "votes",
            "rank_in_contest", "n_precincts", "suppressed", "source_file"]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    juris_n = defaultdict(int)
    for r in rows:
        juris_n[r["jurisdiction_slug"]] += 1
    print(f"Wrote {OUT}: {len(rows)} contest×candidate rows, "
          f"{len(by_contest)} contests")
    print("  per jurisdiction:", dict(sorted(juris_n.items())))


if __name__ == "__main__":
    main()
