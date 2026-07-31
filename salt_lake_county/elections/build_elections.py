"""build_elections.py — derive the county's structured contest×candidate layer
from the canonical Salt Lake County municipal SOVC long file.

Input:  slco_municipal_results_long.csv   (canonical county-wide tidy long — the
        Salt Lake County Clerk SOVC, precinct × candidate × vote-method; 246k rows,
        2007-2025, EVERY SLCo municipality. Provenance: see CLAUDE.md.)
Output: election_results_by_contest.csv   (one row per contest × candidate, votes
        summed across precinct + vote-method; MUNICIPAL council/mayor contests only —
        the growth-relevant governance offices — jurisdiction-tagged for the 7 held
        Salt Lake County cities. This is what loads into gov.db `election_result`.)

DERIVED + idempotent. Never hand-edit the output; rerun this. City-level winner /
margin logic stays in each city's audited `election_results/<slug>_races.csv`
(loaded to gov.db `election_race`); this table is the honest underlying tallies.
"""
import csv
import os
import re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "slco_municipal_results_long.csv")
OUT = os.path.join(HERE, "election_results_by_contest.csv")

# The Salt Lake County cities held in this repo. Order matters: match the most
# specific name first so "SOUTH JORDAN" / "WEST JORDAN" never fall through to a
# shorter token, and "SALT LAKE CITY" is not confused with "SOUTH SALT LAKE".
# Each entry lists EVERY naming era the county clerk has used for that city's
# contests (T1.2 fix, 2026-07-12): full names (2021+ "CITY OF KEARNS MAYOR"),
# abbreviated names (2011 "S Salt Lake City Coun 1", "CTTNWD HGHTS CTY COUN 1",
# "WEST VLY CTY COUN AT LG"), and the 2019 3-letter SHEET CODES ("SJD Council 2",
# "KRN Council 3", "WVC At-Large") that full-name filters silently missed —
# 2019 and 2011-era contests were absent from the derived layer entirely.
CITY_PATTERNS = [
    ("south_jordan",  [r"SOUTH JORDAN", r"\bSJD\b"]),
    ("west_jordan",   [r"WEST JORDAN", r"\bWJD\b"]),
    ("west_valley",   [r"WEST VALLEY", r"WEST VLY", r"\bWVC\b"]),
    ("south_salt_lake", [r"SOUTH SALT ?LAKE", r"\bS SALT LAKE\b", r"\bSSL\b"]),  # MUST precede slc ('SALT LAKE CITY' would match 'SOUTH SALT LAKE CITY')
    ("salt_lake_city_slc", [r"SALT LAKE CITY", r"\bSLC\b"]),   # remapped to 'slc' below
    ("taylorsville",  [r"TAYLORSVILLE", r"\bTAY\b"]),
    ("millcreek",     [r"MILLCREEK", r"\bMIL\b"]),
    ("sandy",         [r"\bSANDY\b", r"\bSAN\b"]),
    ("murray",        [r"\bMURRAY\b", r"\bMUR\b"]),
    ("herriman",      [r"HERRIMAN", r"\bHER\b"]),
    ("draper",        [r"DRAPER", r"\bDRP\b"]),
    ("riverton",      [r"RIVERTON", r"\bRIV\b"]),
    ("alta",          [r"\bALTA\b(?! CANYON)", r"\bALT\b"]),   # Town of Alta; exclude ALTA CANYON rec district
    ("midvale",       [r"MIDVALE", r"\bMID\b"]),
    ("cottonwood_heights", [r"COTTONWOOD HEIGHTS", r"COTTONWOOD HTS", r"CTTNWD", r"\bCOT\b"]),
    ("holladay",      [r"HOLLADAY", r"\bHOL\b"]),
    ("bluffdale",     [r"BLUFFDALE", r"\bBLF\b"]),
    ("white_city",    [r"WHITE CITY", r"\bWHT\b"]),
    ("magna",         [r"\bMAGNA\b(?! WATER)", r"\bMAG\b"]),   # Town/City of Magna; MAGNA WATER district also caught by the district-body guard
    ("copperton",     [r"COPPERTON", r"\bCOP\b"]),
    ("emigration_canyon", [r"EMIGRATION", r"\bEMG\b"]),
    ("kearns",        [r"KEARNS", r"\bKRN\b"]),   # 2026-07-12: safe to include — the 2025 "merged candidates" report was a misread of legitimate PRIMARY candidates (see TODO); KEARNS IMPROVEMENT DISTRICT is caught by the district-body guard
]
SLUG_FIX = {"salt_lake_city_slc": "slc"}

# Special-district / school-board contests that must never be tagged as a city
# council/mayor office, even when they carry a city's name ("KEARNS IMPROVEMENT
# DISTRICT TRUSTEE AT-LARGE", "MAGNA WATER", "Kearns Oquirrh Park Brd Trust",
# "ASPEN PEAKS SCHOOL BOARD"). Checked BEFORE jurisdiction matching.
DISTRICT_BODY_RE = re.compile(
    r"TRUSTEE|BRD TRUST|IMPROVEMENT|IMPRV|SEWER|RECREATION|SERVICE AREA|WATER|"
    r"PARKSREC|\bPARKS?\b|SCHOOL")


def parse_contest(contest):
    """(jurisdiction_slug, office, district) for a municipal council/mayor contest;
    ('', '', '') for anything else (other municipalities / non-governance offices)."""
    up = " ".join(contest.upper().split())
    if DISTRICT_BODY_RE.search(up):
        return "", "", ""            # special district / school board, not a city office
    # normalize the clerk's era variants to canonical tokens before matching:
    # 2011 "Coun"/"CNCL" -> COUNCIL; "@ Lg"/"AT LG" -> AT-LARGE
    up = re.sub(r"\bCNCL\b|\bCOUN\b", "COUNCIL", up)
    up = re.sub(r"@ ?LG\b|\bAT LG\b", "AT-LARGE", up)
    juris = ""
    for slug, pats in CITY_PATTERNS:
        if any(re.search(p, up) for p in pats):
            juris = SLUG_FIX.get(slug, slug)
            break
    if not juris:
        return "", "", ""
    if "MAYOR" in up:
        return juris, "Mayor", ""
    if "COUNCIL" in up:
        # district token: "DISTRICT N" | trailing "COUNCIL N" | "AT-LARGE"/"AT LARGE"
        # (+ optional seat letter: "COUNCIL AT-LARGE B" — White City / Copperton seats)
        if "AT-LARGE" in up or "AT LARGE" in up:
            m = re.search(r"AT.LARGE\s+([A-E])\b", up)
            district = f"At-Large {m.group(1)}" if m else "At-Large"
        else:
            m = re.search(r"DISTRICT\s*#?\s*(\d+)", up) or re.search(r"COUNCIL\s+(\d+)\b", up)
            district = m.group(1) if m else ""
        return juris, "Council", district
    # 2019 sheet-code seat forms with no office word: "COP A".."COP E" (Copperton
    # at-large seats) and bare "<CODE|city> At-Large" ("WVC At-Large", "West Valley
    # City @ Lg") — council seats by construction.
    m = re.search(r"^COP\s+([A-E])$", up)
    if m and juris == "copperton":
        return juris, "Council", f"At-Large {m.group(1)}"
    if "AT-LARGE" in up:
        return juris, "Council", "At-Large"
    return "", "", ""   # a held city but not a council/mayor office (e.g. a ballot prop)


def party_of(candidate):
    m = re.search(r"\(([A-Z]{2,4})\)\s*$", candidate.strip())
    return m.group(1) if m else ""


def main():
    # aggregate votes across precinct + vote_method per (year, etype, contest, candidate)
    agg = defaultdict(lambda: {"votes": 0.0, "precincts": set(), "source": "",
                               "seats": "", "suppressed": False})
    with open(SRC, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            juris, office, district = parse_contest(r["contest"])
            if not office:               # keep only held-city council/mayor contests
                continue
            key = (r["year"], r["election_type"], r["contest"], r["candidate"])
            a = agg[key]
            try:
                a["votes"] += float(r["votes"]) if r["votes"] else 0.0
            except ValueError:
                pass
            if r["precinct"] and r["precinct"] != "Cumulative":
                # 'Cumulative' = the family-C workbooks' all-zero trailing rollup
                # section (relabeled honestly upstream, 2026-07-19 lead (v));
                # it is a report-template artifact, not a precinct.
                a["precincts"].add(r["precinct"])
            a["source"] = r["source_file"]
            a["seats"] = r["vote_for"]
            if str(r["suppressed"]).lower() == "true":
                a["suppressed"] = True

    # rank candidates within each (year, etype, contest)
    by_contest = defaultdict(list)
    for (year, etype, contest, cand), a in agg.items():
        by_contest[(year, etype, contest)].append((cand, a))

    rows = []
    for (year, etype, contest), cands in by_contest.items():
        juris, office, district = parse_contest(contest)
        cands.sort(key=lambda ca: ca[1]["votes"], reverse=True)
        for rank, (cand, a) in enumerate(cands, start=1):
            seats = ""
            if a["seats"]:
                try:
                    seats = str(int(float(a["seats"])))
                except ValueError:
                    seats = a["seats"]
            rows.append({
                "year": year, "election_type": etype, "contest": contest,
                "jurisdiction_slug": juris, "office": office, "district": district,
                "seats": seats, "candidate": cand, "party": party_of(cand),
                "votes": int(round(a["votes"])),
                "rank_in_contest": rank,
                "n_precincts": len(a["precincts"]),
                "suppressed": "true" if a["suppressed"] else "false",
                "source_file": a["source"],
            })

    rows.sort(key=lambda x: (x["year"], x["election_type"], x["jurisdiction_slug"],
                             x["office"], x["district"], x["rank_in_contest"]))
    cols = ["year", "election_type", "contest", "jurisdiction_slug", "office",
            "district", "seats", "candidate", "party", "votes", "rank_in_contest",
            "n_precincts", "suppressed", "source_file"]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    juris_n = defaultdict(int)
    for r in rows:
        juris_n[r["jurisdiction_slug"]] += 1
    print(f"Wrote {OUT}: {len(rows)} contest×candidate rows, "
          f"{len(by_contest)} contests")
    print("  per held-city rows:", dict(sorted(juris_n.items())))


if __name__ == "__main__":
    main()
