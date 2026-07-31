#!/usr/bin/env python3
"""build_elections.py — derive Weber County's contest×candidate layer from the
canonical long file (SLCo model; loads into gov.db `election_result`).

Input:  weber_results_long.csv   (canonical tidy long — precinct-grain canvass
        rows AND official contest-grain summary rows, per source; see
        normalize_weber.py + VERIFICATION.md)
Output: election_results_by_contest.csv — one row per contest × candidate,
        columns exactly as scripts/build_cities_db.py::load_election_result
        expects: year, election_type, contest, jurisdiction_slug, office,
        district, seats, candidate, party, votes, rank_in_contest,
        n_precincts, suppressed, source_file.

OFFICIAL-SUMMARY PRIMACY (the Weber sharp edge): Weber's published precinct
grain suppresses <15-voter precincts, so precinct sums UNDERCOUNT the
certified totals (verified per contest in VERIFICATION.md). Within each
(year, election_type, contest, seats) group, candidate votes therefore come
from the official contest-grain summary rows (precinct='') when the county
published one; the precinct rows contribute n_precincts. Elections with no
usable summary fall back to precinct sums — never mixed, never imputed.

Scope kept here: municipal council/mayor contests (every Weber municipality;
jurisdiction_slug tags the repo-held city 'ogden' — others carry '' per the
loader's contract), county offices (Commission + row offices, incl. partisan
primaries), and countywide/county-administered ballot measures. Special
districts / school boards / judicial retention are excluded (present in the
long file for odd-year canvasses; filter there if needed).

DERIVED + idempotent — never hand-edit the output.
"""
import csv
import os
import re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "weber_results_long.csv")
OUT = os.path.join(HERE, "election_results_by_contest.csv")

# ballot measures (kept, office='') — checked BEFORE the district-body guard
MEASURE_RE = re.compile(
    r"JUSTICE CENTER BOND|WEBER LIBRARY BOND|BALLOT PROPOSITION 19|"
    r"^OGDEN VALLEY CITY$|^FORM OF GOVERNMENT OGDEN VALLEY CITY$|"
    r"^CITY COUNCIL QUESTION$")
# special-district / school / judicial / state-referendum contests: excluded
DISTRICT_BODY_RE = re.compile(
    r"TRUSTEE|IMPROVEMENT|SEWER|WATER|FIRE DISTRICT|FIRE - |NORTH VIEW FIRE|"
    r"SCHOOL|JUSTICE COURT|RETAINED|REFERENDUM|PROPOSITION|BOND|CEMETERY|"
    r"AMENDMENT", re.I)

COUNTY_OFFICE = [
    (re.compile(r"COUNTY (COMMISSION(ER)?|COMM)\b", re.I), "Commission"),
    (re.compile(r"COUNTY ASSESSOR", re.I), "Assessor"),
    (re.compile(r"COUNTY ATTORNEY", re.I), "Attorney"),
    (re.compile(r"(COUNTY )?CLERK/AUDITOR", re.I), "Clerk/Auditor"),
    (re.compile(r"COUNTY RECORDER", re.I), "Recorder/Surveyor"),
    (re.compile(r"COUNTY SHERIFF", re.I), "Sheriff"),
    (re.compile(r"COUNTY TREASURER", re.I), "Treasurer"),
    (re.compile(r"COMMISSIONER SEAT", re.I), "Commission"),
]

# Weber municipalities, most-specific first (NORTH/SOUTH OGDEN and OGDEN
# VALLEY before OGDEN). Only 'ogden' is a repo-held entity.
CITY_PATTERNS = [
    ("", r"NORTH OGDEN"), ("", r"SOUTH OGDEN"), ("", r"OGDEN VALLEY"),
    ("ogden", r"\bOGDEN\b"),
    ("", r"\bROY\b"), ("", r"PLEASANT VIEW"), ("", r"RIVERDALE"),
    ("", r"WASHINGTON TERR"), ("", r"HARRISVILLE"), ("", r"FARR WEST"),
    ("", r"PLAIN CITY"), ("", r"\bHOOPER\b"), ("", r"WEST HAVEN"),
    ("", r"\bUINTAH\b"), ("", r"HUNTSVILLE"), ("", r"MARRIOTT"),
]

PARTY_SUFFIX = re.compile(r"\(([A-Z]{2,4})\)\s*$")
PARTY_PREFIX = re.compile(r"^(REP|DEM|LIB|IAP|CON|UUP|GRN|UTF) ")


def parse_contest(contest):
    """(keep, jurisdiction_slug, office, district) for a by-contest row."""
    up = " ".join(contest.upper().split())
    if MEASURE_RE.search(up):
        return True, "", "", ""
    if DISTRICT_BODY_RE.search(up):
        return False, "", "", ""
    for pat, office in COUNTY_OFFICE:
        if pat.search(up):
            district = ""
            m = re.search(r"(?:SEAT|COMM(?:ISSION)?) ([A-C])\b", up)
            if m:
                district = f"Seat {m.group(1)}"
            return True, "", office, district
    juris = None
    for slug, pat in CITY_PATTERNS:
        if re.search(pat, up):
            juris = slug
            break
    if juris is None:
        return False, "", "", ""
    if "MAYOR" in up:
        return True, juris, "Mayor", ""
    # council-family contests across eras: COUNCIL / WARD / AT LARGE / SEAT /
    # DISTRICT forms ('Ogden Municipal Ward 4', 'Ogden At Large Seat C',
    # 'Hooper City District 2', 'Marriott At-Large')
    if not re.search(r"COUNCIL|WARD|AT.LARGE|AT LARGE|SEAT|DISTRICT", up):
        return False, "", "", ""
    district = ""
    m = re.search(r"AT.LARGE(?:\s+SEAT)?\s+([A-E])\b", up) or \
        re.search(r"SEAT\s+([A-E])\b", up)
    if m:
        district = f"At-Large {m.group(1)}"
    elif "AT-LARGE" in up or "AT LARGE" in up:
        district = "At-Large"
    else:
        m = re.search(r"(?:WARD|DISTRICT|SEAT)S?\s*#?\s*([\d& ]+\d|\d+)", up) or \
            re.search(r"COUNCIL\s+(\d+)\b", up)
        if m:
            district = " ".join(m.group(1).split())
    return True, juris, "Council", district


def party_of(candidate):
    m = PARTY_SUFFIX.search(candidate.strip())
    if m:
        return m.group(1)
    m = PARTY_PREFIX.match(candidate.strip())
    return m.group(1) if m else ""


def main():
    groups = defaultdict(lambda: {
        "summary": defaultdict(lambda: {"votes": 0, "src": "", "sup": False}),
        "precinct": defaultdict(lambda: {"votes": 0, "src": "", "sup": False}),
        "precincts": set(), "seats": "", "suppressed": False})
    with open(SRC, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            keep, juris, office, district = parse_contest(r["contest"])
            if not keep:
                continue
            key = (r["year"], r["election_type"], r["contest"], r["vote_for"])
            g = groups[key]
            g["seats"] = r["vote_for"] or g["seats"]
            grain = "summary" if r["precinct"] == "" else "precinct"
            a = g[grain][r["candidate"]]
            if r["votes"] != "":
                a["votes"] += int(r["votes"])
            a["src"] = r["source_file"]
            if r["suppressed"] == "True":
                a["sup"] = True
                g["suppressed"] = True
            if r["precinct"]:
                g["precincts"].add(r["precinct"])

    rows = []
    for (year, etype, contest, seats), g in groups.items():
        _, juris, office, district = parse_contest(contest)
        cands = g["summary"] if g["summary"] else g["precinct"]
        ranked = sorted(cands.items(), key=lambda kv: kv[1]["votes"],
                        reverse=True)
        for rank, (cand, a) in enumerate(ranked, start=1):
            rows.append({
                "year": year, "election_type": etype, "contest": contest,
                "jurisdiction_slug": juris, "office": office,
                "district": district, "seats": seats, "candidate": cand,
                "party": party_of(cand), "votes": a["votes"],
                "rank_in_contest": rank,
                "n_precincts": len(g["precincts"]),
                "suppressed": "true" if g["suppressed"] else "false",
                "source_file": a["src"],
            })

    rows.sort(key=lambda x: (x["year"], x["election_type"],
                             x["jurisdiction_slug"], x["office"], x["district"],
                             x["contest"], x["rank_in_contest"]))
    cols = ["year", "election_type", "contest", "jurisdiction_slug", "office",
            "district", "seats", "candidate", "party", "votes",
            "rank_in_contest", "n_precincts", "suppressed", "source_file"]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    n_contests = len({(r["year"], r["election_type"], r["contest"], r["seats"])
                      for r in rows})
    per = defaultdict(int)
    for r in rows:
        per[(r["year"], r["election_type"])] += 1
    print(f"Wrote {OUT}: {len(rows)} contest×candidate rows, "
          f"{n_contests} contests")
    for k in sorted(per):
        print("   %s %-18s %4d rows" % (k[0], k[1], per[k]))


if __name__ == "__main__":
    main()
