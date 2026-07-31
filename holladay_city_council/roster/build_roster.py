#!/usr/bin/env python3
"""build_roster.py — rolling council-roster for HOLLADAY (a slowly-changing-dimension / interval
table of who holds each council + mayor seat over time).

Holladay is a **5-DISTRICT city with a VOTING MAYOR** (Council-Manager form): **five single-member
council districts (D1..D5) + a separately-elected Mayor who is a FULL voting member** of the council
(the executive is an appointed City Manager). A complete named roll therefore tops out at **6**
("... Mayor Dahle-Aye"), never 5 — `non_voting_mayor=False`, the Mayor is modelled as a real voting
seat (kept in DB_KEY, gets clamped vote bounds). 365 mayor vote-rows in the record.

THIN DRIVER: this file holds only Holladay-specific DATA (curated TENURES, name maps, the 2022
redistricting facts) + config; all generic mechanics live in ../../scripts/roster_lib.py. Modelled
on the west_jordan driver (DISTRICT + redistricting + precinct-crosscheck template).

DERIVED LAYER — regenerable, never hand-edited. Canonical inputs:
  1. election_results/holladay_results_by_candidate.csv  (winners -> elected/reelected; 2017+ rostered)
  2. cities.db  role table (city='holladay', body='Council')  (observed vote bounds; incl. the mayor)
  3. meeting_minutes/minutes/**  (seating dates, Ord. 2022-09 redistricting, the D3->Mayor move)
  4. roster/roster_overrides.csv  (hand corrections; applied LAST, win ties)
  5. geo/precinct_to_district.csv  (read DIRECTLY since 2026-07-19: roster_lib.write_precincts
     accepts a map with no source_year column via the explicit precinct_source_default token
     -- the H-A hardening; the old source_year-wrapper sidecar is RETIRED.)

Outputs (idempotent — re-running reproduces them byte-for-byte):
  roster/council_terms.csv      one row per seat-tenure (5 districts + MAYOR)
  roster/district_versions.csv  boundary interval table — 5 districts x 2 plans + a citywide Mayor row
  roster/district_precincts.csv versioned precinct->district composition (plan-scoped; districts only)

Usage:
  python3 roster/build_roster.py [--demo|--check]

Cardinal rule (repo CLAUDE.md): NEVER fabricate. Unknown seat-holder / boundary / date ->
explicit VACANT / gap + confidence + a note, never a guess.

Provenance / confidence model (Holladay):
  high   = an in-file election win (2019/2021/2023/2025) seated at a documented January meeting and
           corroborated by the cities.db named-vote record; OR an UNCONTESTED 2023 seat (D2 Durham,
           D5 Gray) that SLCo omits from the SOVC but which is documented (election_results/CLAUDE.md)
           + seated + roster-corroborated.
  medium = a Cycle-A HOLDOVER serving at the 2020 floor whose SEATING election (2017) predates the
           minutes floor (Sabrina Petersen D1, Paul Fotheringham D3, Mayor Rob Dahle) — three rows.
  low    = genuinely unknown / not-acquired (flagged) — the prior-plan (pre-2022) district + precinct
           geometry is an honest GAP; no low rows in council_terms.

STRUCTURAL FACTS (verified in source):
  * VOTING MAYOR (roll of 6). 2026-01-08 roll: "Council Member Bradley-Yes; ... Mayor <Name>" — the
    Mayor is a full voting member; CH... Holladay CLAUDE.md confirms 365 mayor vote-rows.
    non_voting_mayor=False.
  * REDISTRICTING — Ordinance 2022-09 "Amending the Holladay City Municipal Council District
    Boundaries," adopted 2022-05-05 on a unanimous roll (Durham mover / Gibbons second; Brewer,
    Fotheringham, Quinn, Gibbons AND Mayor Rob Dahle all Aye — a voting-mayor roll of 6). Driven by
    the 2020 Census (discussed 2022-04-21). First used for the 2023 (Cycle B) district elections;
    the pre-2022 lines governed the 2021 elections.
  * D3 COUNCILMEMBER -> MAYOR (the headline transition). Paul Fotheringham held D3 (elected 2017 &
    2021) and was elected MAYOR in 2025 (def. Daren Watts 57.04%) -> his D3 tenure ends `became-mayor`
    at the 2026-01-08 seating and a MAYOR tenure begins (Natalie Bradley won the open D3 2025). One
    `paul_fotheringham` key spans D3 (body=Council) and MAYOR (body=Mayor); the vote-bound clamp
    confines each tenure's first_vote/last_vote to its own window.
  * D5 Gibbons -> Gray, with FOUR post-departure `gibbons` vote rows that are a SOURCE (clerk) error,
    NOT an extraction artifact (re-diagnosed 2026-07-29 against the primary minutes; the earlier
    "EXTRACTION ARTIFACTS / mis-parsed roll / OCR" wording here was WRONG). Daniel Gibbons (D5,
    elected 2019) was succeeded by Emily Gray (elected 2023, UNCONTESTED — declared elected, seated
    2024-01-04, her first continuous vote). gov.db carries four `gibbons` Council votes AFTER Gray's
    seating (2024-02-15, -03-21, -04-25, -12-12). Every one of them sits on the SAME motion type —
    "moved to adjourn the Closed Session" — inside the clerk's boilerplate closed-session paragraph,
    and the minutes VERBATIM print Gibbons in that roll, e.g. 2024-12-12: "The Council roll call vote
    was as follows: Council Members Durham, Fotheringham, Quinn, Gibbons, Brewer and Mayor Dahle in
    favor." That is the 2023 slate pasted forward: the clerk updated Gibbons->Gray in the closed-
    session template on some 2024 dates (2024-09-19, -10-03, -10-24, and all of 2025) but not on
    these four. The same stale name also appears as a SECONDER on 2024-06-13. The extractor is
    faithful — no motion in this city exceeds a named roll of 6 (verified); the "7th name" is a
    per-MEETING count (6 real voters + the stale template name), never a 7-name roll call.
    The rows are therefore RETAINED verbatim (cardinal rule 2 — city-faithful values are never
    overwritten); the tenure is NOT extended (the clamp confines Gibbons' last_vote to 2023-11-16).
    Treat these four `gibbons` rows as non-service when analyzing who held D5.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.dirname(HERE)                 # holladay_city_council/
REPO_ROOT = os.path.dirname(CITY_DIR)            # civic-data/
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import roster_lib
from roster_lib import RosterConfig, Redistrict

ELECTIONS = os.path.join(CITY_DIR, "election_results", "holladay_results_by_candidate.csv")
PRECINCTS_BYP_SRC = os.path.join(CITY_DIR, "election_results", "holladay_results_by_precinct.csv")
PRECINCT_MAP = os.path.join(CITY_DIR, "geo", "precinct_to_district.csv")  # canonical geo map (H-A: sidecar retired 2026-07-19)
CITIES_DB = os.path.join(REPO_ROOT, "cities.db")
OVERRIDES = os.path.join(HERE, "roster_overrides.csv")
TERMS_OUT = os.path.join(HERE, "council_terms.csv")
DISTRICTS_OUT = os.path.join(HERE, "district_versions.csv")
PRECINCTS_OUT = os.path.join(HERE, "district_precincts.csv")

CITY = "holladay"
DATA_FLOOR = "2020-01-01"
GEOM_REF = "geo/council_districts.geojson"

# The real redistricting event (spot-checked against source minutes 2022-05-05):
#   Ordinance 2022-09 "Amending the Holladay City Municipal Council District Boundaries," adopted
#   2022-05-05 on a unanimous roll incl. Mayor Rob Dahle (a voting-mayor roll of 6). First used for
#   the 2023 district elections; the pre-2022 lines governed the 2021 elections.
REDISTRICT_ORD = "Ordinance 2022-09"
REDISTRICT_ADOPTED = "2022-05-05"
PLAN_OLD = "plan_pre2022"
PLAN_NEW = "plan_2022"
PLAN_SWITCH = "2022-05-05"
SRC_URL = ("meeting_minutes/minutes/2022/2022-05-02/2022-05-05_city-council-meeting_861651.md "
           "(Ordinance 2022-09 Amending the Holladay City Municipal Council District Boundaries, "
           "adopted 2022-05-05 by a unanimous roll incl. Mayor Rob Dahle)")

SEAT_DISTRICT = {
    "D1": "District 1", "D2": "District 2", "D3": "District 3", "D4": "District 4",
    "D5": "District 5", "MAYOR": "Citywide",
}

TENURES = [
    # ============================ D1 (Cycle A: 2017 / 2021 / 2025) ============================
    dict(body="Council", seat_id="D1", person_name="Sabrina Petersen", person_key="sabrina_petersen",
         start_date="2018-01-01", start_event="elected", election_year="2017", end_event="did-not-run",
         confidence="medium",
         sources="election:2017 (District 1 winner, unopposed 1,230/100%; also 2009 & 2013); votes:"
                 "2020-01-09..2021-12-16 (cities.db, Council/D1)",
         note="Cycle-A HOLDOVER at the 2020 floor: Jan-2018 oath predates the 2020 minutes floor -> start "
              "2018-01-01 inferred (medium); service vote-documented from 2020-01-09. NOT a candidate in "
              "2021 (Brewer won D1) -> did not seek re-election; term ended at the 2022-01-20 seating."),
    dict(body="Council", seat_id="D1", person_name="Ty Brewer", person_key="ty_brewer",
         start_date="2022-01-20", start_event="elected", election_year="2021", end_event="did-not-run",
         confidence="high",
         sources="election:2021 (District 1 winner, as 'D. Ty Brewer', def. Melissa Blackham Hilton 52.46%); "
                 "minutes:2022-01-20 (first documented 2022 council meeting; 2021-cycle seating); votes:"
                 "2022-01-20..2025-12-18 (cities.db, Council/D1)",
         note="Elected D1 2021. NOT a candidate in 2025 (Sundwall won D1) -> served the full term, did not "
              "seek re-election; end date is the successor's 2026-01-08 seating (precise), mechanism unstated."),
    dict(body="Council", seat_id="D1", person_name="David Sundwall", person_key="david_sundwall",
         start_date="2026-01-08", start_event="elected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (District 1 winner, as 'David Hammon Sundwall', def. Grant Jacob Bilstad "
                 "67.42%); minutes:2026-01-08 (first documented 2026 council meeting; present list names "
                 "Sundwall); votes:2026-01-08.. (cities.db, Council/D1)",
         note="Elected D1 2025 (seated 2026-01-08). Serving."),

    # ============================ D2 (Cycle B: 2019 / 2023) — Durham, continuous ============
    dict(body="Council", seat_id="D2", person_name="Matt Durham", person_key="matt_durham",
         start_date="2020-01-09", start_event="elected", election_year="2019", end_event="reelected",
         confidence="high",
         sources="election:2019 (District 2 winner, unopposed 962/100%); minutes:present 2020-01-09 (first "
                 "documented 2020 council meeting); votes:2020-01-09.. (cities.db, Council/D2)",
         note="Elected D2 2019. Re-elected 2023 (uncontested) -> continuous."),
    dict(body="Council", seat_id="D2", person_name="Matt Durham", person_key="matt_durham",
         start_date="2024-01-04", start_event="reelected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 2 UNCONTESTED — SLCo omits uncontested municipal seats from the "
                 "SOVC, so there is NO by-candidate row; Durham drew a single candidate and was declared "
                 "elected to a Jan-2028 term, corroborated by the 2026 roster — see election_results/"
                 "CLAUDE.md); minutes:2024-01-04 (first documented 2024 council meeting); votes:continuous "
                 "through 2026-04-16 (cities.db, Council/D2)",
         note="Re-elected D2 2023 UNCONTESTED (first D2 term on the plan_2022 lines; seated 2024-01-04). "
              "The win is documented but not in election_results (uncontested) -> no forward cross-check "
              "row; confidence high on the documented seating + roster corroboration. Serving."),

    # ============================ D3 (Cycle A: 2017 / 2021 / 2025) — Fotheringham -> Bradley ====
    dict(body="Council", seat_id="D3", person_name="Paul Fotheringham", person_key="paul_fotheringham",
         start_date="2018-01-01", start_event="elected", election_year="2017", end_event="reelected",
         confidence="medium",
         sources="election:2017 (District 3 winner, as 'Paul S Fotheringham', def. Dennis Roach 67.27%); "
                 "votes:2020-01-09.. (cities.db, Council/D3)",
         note="Cycle-A HOLDOVER at the 2020 floor: Jan-2018 oath predates the minutes floor -> start "
              "2018-01-01 inferred (medium); service vote-documented from 2020-01-09. Re-elected 2021."),
    dict(body="Council", seat_id="D3", person_name="Paul Fotheringham", person_key="paul_fotheringham",
         start_date="2022-01-20", start_event="reelected", election_year="2021", end_event="became-mayor",
         confidence="high",
         sources="election:2021 (District 3 winner, unopposed 867/100%); minutes:2022-01-20 (2021-cycle "
                 "seating); election:2025 (won MAYOR — vacates D3); votes:2022-01-20..2026-01-08 (cities.db, "
                 "Council/D3, clamped)",
         note="Re-elected D3 2021. ELECTED MAYOR in 2025 -> left D3 at the 2026-01-08 seating (became-mayor). "
              "Same person as the MAYOR tenure below; the vote-bound clamp confines this D3 row to its own "
              "window (his mayoral council votes fall on the MAYOR tenure)."),
    dict(body="Council", seat_id="D3", person_name="Natalie Bradley", person_key="natalie_bradley",
         start_date="2026-01-08", start_event="elected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (District 3 winner, as 'Natalie Bellamy Bradley', def. Bailee Jones 60.54% "
                 "— the OPEN D3 seat Fotheringham vacated to run for Mayor); minutes:2026-01-08 (present "
                 "list names Bradley); votes:2026-01-08.. (cities.db, Council/D3)",
         note="Elected D3 2025 (seated 2026-01-08). Serving."),

    # ============================ D4 (Cycle B: 2019 / 2023) — Quinn, continuous ============
    dict(body="Council", seat_id="D4", person_name="Drew Quinn", person_key="drew_quinn",
         start_date="2020-01-09", start_event="elected", election_year="2019", end_event="reelected",
         confidence="high",
         sources="election:2019 (District 4 winner, def. B. Peter Monson 78.00%); minutes:present 2020-01-09; "
                 "votes:2020-01-09.. (cities.db, Council/D4)",
         note="Elected D4 2019. Re-elected 2023 -> continuous."),
    dict(body="Council", seat_id="D4", person_name="Drew Quinn", person_key="drew_quinn",
         start_date="2024-01-04", start_event="reelected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 4 winner, def. Matthew Collin Tracy 72.26%); minutes:2024-01-04 "
                 "(2023-cycle seating); votes:continuous through 2026-04-16 (cities.db, Council/D4)",
         note="Re-elected D4 2023 (first D4 term on the plan_2022 lines; seated 2024-01-04). Serving."),

    # ============================ D5 (Cycle B: 2019 / 2023) — Gibbons -> Gray ============
    dict(body="Council", seat_id="D5", person_name="Daniel Gibbons", person_key="daniel_gibbons",
         start_date="2020-01-09", start_event="elected", election_year="2019", end_event="did-not-run",
         confidence="high",
         sources="election:2019 (District 5 winner, as 'Daniel Bay Gibbons', def. Lori A. Khodadad 55.11%); "
                 "minutes:present 2020-01-09; votes:2020-01-09..2023-11-16 (cities.db, Council/D5, clamped)",
         note="Elected D5 2019. NOT a candidate in 2023 (Gray won D5 uncontested) -> did not seek "
              "re-election; term ended at the 2024-01-04 seating. NB: gov.db carries 4 'gibbons' Council "
              "votes AFTER 2024-01-04 (2024-02-15/-03-21/-04-25/-12-12) — re-diagnosed 2026-07-29 as a "
              "SOURCE (clerk) error, NOT an extraction artifact: all four are the boilerplate 'adjourn the "
              "Closed Session' roll, which the minutes VERBATIM print with the stale 2023 slate (Gibbons "
              "instead of Gray); the clerk did update the template on other 2024 dates. Rows RETAINED "
              "verbatim; NOT service; the clamp confines this row's last_vote to 2023-11-16. "
              "(See roster/CLAUDE.md + meeting_minutes/CLAUDE.md.)"),
    dict(body="Council", seat_id="D5", person_name="Emily Gray", person_key="emily_gray",
         start_date="2024-01-04", start_event="elected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 5 UNCONTESTED — SLCo omits uncontested seats from the SOVC, so "
                 "there is NO by-candidate row; Gray drew a single candidate, declared elected to a Jan-2028 "
                 "term, corroborated by the 2026 roster — see election_results/CLAUDE.md); minutes:2024-01-04 "
                 "(first documented 2024 council meeting; her first continuous vote); votes:2024-01-04.. "
                 "(cities.db, Council/D5)",
         note="Elected D5 2023 UNCONTESTED (first D5 term on the plan_2022 lines; seated 2024-01-04). The "
              "win is documented but not in election_results (uncontested) -> no forward cross-check row; "
              "confidence high on the documented seating + continuous vote record + roster. Serving."),

    # ============================ MAYOR (Cycle A: 2017 / 2021 / 2025) — VOTING (roll of 6) ====
    dict(body="Mayor", seat_id="MAYOR", person_name="Rob Dahle", person_key="rob_dahle",
         start_date="2018-01-01", start_event="elected", election_year="2017", end_event="reelected",
         confidence="medium",
         sources="election:2017 (Mayor winner, as 'Robert M. Dahle', unopposed 7,465/100%; first won 2013 "
                 "by +88); votes:2020-01-09.. (cities.db, Council — mayoral votes, roll of 6)",
         note="Cycle-A HOLDOVER at the 2020 floor: Jan-2018 oath predates the minutes floor -> start "
              "2018-01-01 inferred (medium). The Holladay Mayor is a FULL voting council member "
              "(non_voting_mayor=False). Re-elected 2021."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Rob Dahle", person_key="rob_dahle",
         start_date="2022-01-20", start_event="reelected", election_year="2021", end_event="did-not-run",
         confidence="high",
         sources="election:2021 (Mayor winner, as 'Robert M. Dahle', unopposed 4,533/100%); minutes:2022-01-20 "
                 "(2021-cycle seating); votes:2022-01-20..2025-12-18 (cities.db, Council — mayoral votes)",
         note="Re-elected Mayor 2021. NOT a candidate in 2025 (Fotheringham won) -> served the full term, "
              "did not seek re-election; end date is the successor's 2026-01-08 seating (precise)."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Paul Fotheringham", person_key="paul_fotheringham",
         start_date="2026-01-08", start_event="became-mayor", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (Mayor winner, as 'Paul S Fotheringham', def. Daren A. Watts 57.04%); "
                 "minutes:2026-01-08 ('Mayor Paul Fotheringham called the City Council Meeting to order'); "
                 "votes:2026-01-08.. (cities.db, Council — mayoral votes, clamped)",
         note="COUNCILMEMBER -> MAYOR: won the 2025 mayoralty from the D3 seat (see the D3 became-mayor row). "
              "Same person_key; the vote-bound clamp splits his D3-era and mayor-era council votes. VOTING "
              "mayor. Serving."),
]

# canonical UPPER-CASE election name token -> person_key. No two Holladay general winners (2017+)
# share a surname (PETERSEN is Sabrina only; no PETERSON in Holladay). Only WINNERS pass through
# canon_key. GRAY/DURHAM 2023 were uncontested (no winner rows), so they never reach canon_key.
NAME_TO_KEY = {
    "PETERSEN": "sabrina_petersen", "BREWER": "ty_brewer", "SUNDWALL": "david_sundwall",
    "DURHAM": "matt_durham", "FOTHERINGHAM": "paul_fotheringham", "BRADLEY": "natalie_bradley",
    "QUINN": "drew_quinn", "GIBBONS": "daniel_gibbons", "DAHLE": "rob_dahle",
}

# cities.db person.name_key -> our person_key. Holladay's db uses SURNAME-ONLY name_keys (the
# minutes print surname-only rolls). INCLUDES the voting mayors (dahle, fotheringham-as-mayor).
DB_KEY = {
    "petersen": "sabrina_petersen", "brewer": "ty_brewer", "sundwall": "david_sundwall",
    "durham": "matt_durham", "fotheringham": "paul_fotheringham", "bradley": "natalie_bradley",
    "quinn": "drew_quinn", "gibbons": "daniel_gibbons", "gray": "emily_gray",
    "dahle": "rob_dahle",
}


def seat_for_contest(office, district):
    """election (office, district) -> the STABLE seat_id (crosscheck_field='seat_id')."""
    if office == "Mayor":
        return "MAYOR"
    d = district.strip()
    if d in ("1", "2", "3", "4", "5"):
        return "D" + d
    return None


REDISTRICT = Redistrict(
    plan_old=PLAN_OLD, plan_new=PLAN_NEW, plan_switch=PLAN_SWITCH,
    ord=REDISTRICT_ORD, adopted=REDISTRICT_ADOPTED,
    districts=["District 1", "District 2", "District 3", "District 4", "District 5"],
    geom_ref=GEOM_REF, source_url=SRC_URL, data_floor=DATA_FLOOR,
    current_note=(f"CURRENT post-2020-census boundaries. {REDISTRICT_ORD} ('Amending the Holladay City "
                  "Municipal Council District Boundaries') adopted " + REDISTRICT_ADOPTED + " on a unanimous "
                  "roll incl. Mayor Rob Dahle (a voting-mayor roll of 6). geometry_ref is Holladay's OFFICIAL "
                  "5-district layer in geo/council_districts.geojson; precinct->district in "
                  "geo/precinct_to_district.csv. First used for the 2023 district elections."),
    prior_adopted_by="prior plan (pre-2022 boundaries)",
    prior_note=("Prior-plan (pre-2022) district boundaries NOT acquired -> honest GAP (blank geometry_ref, "
                "confidence low). In force through the 2021 elections. effective_start = data floor."),
    citywide_rows=[
        ("MAYOR", "citywide", "the separately-elected VOTING Mayor (Rob Dahle 2018-2026 -> Paul "
                              "Fotheringham 2026+)"),
    ],
    citywide_adopted_by="Holladay City (citywide mayor)",
    citywide_note_template=("{who}: represents the ENTIRE city on every date, unchanged by the 2022 "
                            "redistricting. Holladay's Mayor is a FULL VOTING council member (roll of 6) — "
                            "only the 5 numbered districts are geographic."),
    precinct_hi_source="current",
    precinct_source_default="current",   # H-A: geo map has no source_year column; explicit token
    precinct_hi_note=("current post-2020-census precinct->district read directly from geo/precinct_to_district.csv "
                      "(no source_year column — the configured precinct_source_default token 'current' "
                      "applies; H-A hardening 2026-07-19, wrapper sidecar retired). "
                      "Official 5-district layer; districts only (the Mayor is city-wide)."),
    precinct_med_note="",
    precinct_prior_note=("Prior-plan (pre-2022) precinct->district composition NOT acquired -> honest GAP."),
    crosscheck_districts=("1", "2", "3", "4", "5"),
    precinct_prefix="HOL", geo_seat_prefix="D",
    plan_switch_year="2023", citywide_seats=(),
)

CFG = RosterConfig(
    non_voting_mayor=False,     # Holladay's Mayor VOTES (roll of 6) — a real voting seat
    city=CITY, city_dir=CITY_DIR, repo_root=REPO_ROOT, data_floor=DATA_FLOOR,
    geom_ref=GEOM_REF, elections_path=ELECTIONS, cities_db_path=CITIES_DB,
    overrides_path=OVERRIDES, terms_out=TERMS_OUT, districts_out=DISTRICTS_OUT,
    seat_district=SEAT_DISTRICT, name_to_key=NAME_TO_KEY, db_key=DB_KEY,
    seat_order=["D1", "D2", "D3", "D4", "D5", "MAYOR"],
    # municipal GENERAL winners, 2017+ (the cycles the roster spans). Holladay election data reaches
    # to 2007 but 2007-2015 are pre-floor cycles not rostered.
    keep_election_row=lambda r: (r["election_type"].strip().lower() == "municipal general"
                                 and int(r["year"]) >= 2017),
    contest_key=seat_for_contest, crosscheck_field="seat_id",
    winners_have_district=True,
    elected_events=("elected", "reelected", "became-mayor"),
    # H-C reverse-crosscheck DOCUMENTED exceptions (2026-07-19). crosscheck_field='seat_id', so the
    # keys are (year, seat_id, person_key). The 2023 D2 (Durham) and D5 (Gray) seats were UNCONTESTED
    # -> SLCo omits uncontested municipal seats from the SOVC, so there is NO is_winner/by_candidate
    # row (verified: holladay_results_by_candidate.csv has 2023 rows only for the contested D4/Quinn
    # race; election_results/CLAUDE.md documents the omission; corroborated by the 2024-01-04 seating
    # + continuous vote record). Roster is correct; the forward check already reports 0 drift.
    reverse_crosscheck_exceptions={
        ("2023", "D2", "matt_durham"): "2023 District 2 UNCONTESTED -> SLCo omits uncontested seats from the SOVC (no by_candidate row); Durham drew a single candidate, declared re-elected, seated 2024-01-04 (continuous vote record) — see election_results/CLAUDE.md",
        ("2023", "D5", "emily_gray"): "2023 District 5 UNCONTESTED -> SLCo omits uncontested seats from the SOVC (no by_candidate row); Gray drew a single candidate, declared elected, seated 2024-01-04 (first continuous vote) — see election_results/CLAUDE.md",
    },
    redistrict=REDISTRICT, precincts_out=PRECINCTS_OUT,
    precinct_map_path=PRECINCT_MAP, precincts_byprecinct_path=PRECINCTS_BYP_SRC,
)


def demo():
    def line(r):
        end = r["end_date"] or "—(serving)"
        return (f"    {r['seat_id']:<6} {r['person_name']:<20} {r['start_date']} -> {end:<12}"
                f" [{r['start_event']}/{r['end_event']}] conf={r['confidence']}")

    print("\n(a) CURRENT council roster + mayor (end_date empty, end_event=serving):")
    for r in roster_lib.load_terms(CFG):
        if not r["end_date"] and r["end_event"] == "serving":
            print(line(r))

    print("\n(b) Roster AS OF 2025-06-01 (Dahle mayor; Fotheringham still D3; Gray D5):")
    for r in roster_lib.roster_as_of(CFG, "2025-06-01", body="Council"):
        print(line(r))
    for r in roster_lib.roster_as_of(CFG, "2025-06-01", body="Mayor"):
        print(line(r))

    print("\n(c) Address+date -> representatives (via geo/address_to_district.py — 1 district + Mayor):")
    addr = "4580 S 2300 E, Holladay, UT 84117"   # City Hall
    for d in ("2026-02-01", "2020-06-01"):
        res = roster_lib.representatives_for_address(CFG, addr, d, latlon=(40.6591, -111.8244))
        who = ", ".join(f"{x['person_name']}({x['seat_id']})" for x in res["reps"])
        loc = (f"District {res['district']} via {res.get('precinct')} [{res.get('method')}]"
               if res.get("district") else f"[{res.get('gap', '?')}]")
        print(f"  '{addr}'\n    on {d} (plan={res['plan']}): {loc}\n    -> your reps: {who or '(none — see gap)'}")

    print("\n(e) Precinct-map cross-check (district_precincts vs election outcomes; districts only):")
    roster_lib.precinct_crosscheck(CFG, verbose=True)


if __name__ == "__main__":
    rows = roster_lib.build(CFG, TENURES)
    n = {c: sum(1 for r in rows if r["confidence"] == c) for c in ("high", "medium", "low")}
    nvac = sum(1 for r in rows if r["start_event"] == "vacated")
    print(f"Wrote {os.path.relpath(TERMS_OUT, CITY_DIR)} "
          f"({len(rows)} tenures incl. {nvac} VACANT: {n['high']} high / {n['medium']} medium / {n['low']} low)")
    print(f"Wrote {os.path.relpath(DISTRICTS_OUT, CITY_DIR)} "
          f"(5 districts x 2 plans + citywide Mayor; redistricting {REDISTRICT_ORD})")
    print(f"Wrote {os.path.relpath(PRECINCTS_OUT, CITY_DIR)} "
          f"(plan_2022 precinct map + plan_pre2022 gap rows; districts only)")
    if "--check" in sys.argv:
        print("\nValidation: PASS (no overlaps; sources+confidence present; voting-mayor + gap/vacate guards clear).")
        print("Precinct cross-check:")
        roster_lib.precinct_crosscheck(CFG, verbose=True)
    if "--demo" in sys.argv:
        demo()
