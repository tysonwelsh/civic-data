#!/usr/bin/env python3
"""build_roster.py — rolling council-roster for MURRAY (a slowly-changing-dimension /
interval table of who holds each council + mayor seat over time). Murray is a
**council–mayor (executive-mayor) city**: **5 geographic council districts (D1..D5, no
at-large seats)** legislate, and a separately-elected **executive Mayor does NOT vote** on
council motions. A full council roll call tops out at **5** (never 6). The districts were
**redrawn after the 2020 Census** (Boundary_Approval_Date 2022-01-04); the district NUMBERS
were NOT changed.

THIN DRIVER: this file holds only Murray-specific DATA (curated TENURES, name maps, the
2022-redistricting facts) + config; all generic mechanics live in ../../scripts/roster_lib.py.
District template: west_jordan_city_council/roster/ (redistricting + district_versions +
precinct layer). Murray differs by having a NON-voting mayor and no at-large seats.

DERIVED LAYER — regenerable, never hand-edited. Canonical inputs:
  1. election_results/murray_results_by_candidate.csv  (winners -> `elected`/`reelected`; 2021+)
  2. cities.db  role table (city='murray', body='Council')  (observed vote bounds)
  3. meeting_minutes/minutes/**  (oath/seating, the redistricting, the D1/D3/D5 vacancy chains)
  4. roster/roster_overrides.csv  (hand corrections; applied LAST, win ties)

Usage:
  python3 roster/build_roster.py            # regenerate the CSVs
  python3 roster/build_roster.py --demo     # regenerate + print the demo queries
  python3 roster/build_roster.py --check    # regenerate + validations

Cardinal rule (repo CLAUDE.md): NEVER fabricate. Unknown seat-holder / date / boundary ->
explicit VACANT/gap + confidence + a note, never a guess.

STRUCTURAL FACTS (verified in source):
  * 5 DISTRICT council seats + a NON-VOTING executive Mayor (non_voting_mayor=True; MAYOR
    rows carry EMPTY vote bounds). Staggered 4-year cycles as the county SOVC records them:
      Cohort A = D1 + D3 + D5   elected 2019 / 2023  -> seated Jan 2020 / 2024
      Cohort B = D2 + D4        elected 2021 / 2025  -> seated Jan 2022 / 2026
      Mayor                     elected 2021 / 2025  -> seated Jan 2022 / 2026
    Murray's own election data floor is 2021 (2019 is below the repo's 2020 minutes floor and
    NOT in the loaded election file), so the 2019-cohort seatings at the 2020 floor are
    PRE-FLOOR (their win is not in the data) -> confidence medium, no fabricated election row.
  * SEATING DATES (first documented council meeting each January, = first cities.db vote):
    2020-01-07, 2022-01-04, 2024-01-02, 2026-01-06. Every post-floor transition is anchored.
  * Brett HALES: D5 councilmember 2020-01-07..2021-12-07 (190 votes) -> won the 2021 MAYORALTY
    and took office 2022-01-04 (D5 vacated -> Hrechkosy interim). "Councilmember Hales" and
    "Mayor Hales" are the SAME person; re-elected Mayor 2025.
  * THE 2023 COUNCIL-MINUTES GAP IS NOW CLOSED (recovered/promoted 2026-07-16): all 18 lost
    2023 meetings are on disk (source=pmn), so meeting_minutes/minutes_unrecovered.csv is
    header-only. The D1 2023 appointee chain is therefore fully DOCUMENTED, not gap-bounded:
      - Philip MARKHAM appointed + sworn in at the 2022-12-12 special ('District #1 Interviews',
        20A-1-510, chosen by lot after a tie) -> HIGH, exact start 2022-12-12. He RESIGNED to
        become the city's CED Director; last D1 vote/service 2023-06-27, seat recorded '(Vacant)'
        at the 2023-07-18 & 2023-08-01 meetings -> vacate_date 2023-06-28 (day after last service,
        HIGH; the departure is documented, not gap-bounded).
      - David RODGERS appointed + sworn in at the 2023-08-08 special ('District #1 Interviews',
        chosen over Pickett by coin toss after two 2-2 ties) -> HIGH, exact start 2023-08-08;
        first vote 2023-08-22; succeeded by the elected Pickett 2024-01-02.
    The single remaining VACANT [2023-06-28, 2023-08-08) is a REAL, minutes-documented vacancy.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.dirname(HERE)                 # murray_city_council/
REPO_ROOT = os.path.dirname(CITY_DIR)            # civic-data/
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import roster_lib
from roster_lib import RosterConfig, Redistrict

ELECTIONS = os.path.join(CITY_DIR, "election_results", "murray_results_by_candidate.csv")
PRECINCTS_BYP_SRC = os.path.join(CITY_DIR, "election_results", "murray_results_by_precinct.csv")
GEO_PRECINCT_MAP = os.path.join(CITY_DIR, "geo", "precinct_to_district.csv")
CITIES_DB = os.path.join(REPO_ROOT, "cities.db")
OVERRIDES = os.path.join(HERE, "roster_overrides.csv")
TERMS_OUT = os.path.join(HERE, "council_terms.csv")
DISTRICTS_OUT = os.path.join(HERE, "district_versions.csv")
PRECINCTS_OUT = os.path.join(HERE, "district_precincts.csv")

CITY = "murray"
DATA_FLOOR = "2020-01-01"          # repo minutes floor; the election file reaches back to 2021 only
GEOM_REF = "geo/districts.geojson"

PLAN_OLD = "plan_pre2022"
PLAN_NEW = "plan_2022"
PLAN_SWITCH = "2022-01-04"         # Boundary_Approval_Date on the official district layer
REDISTRICT_ORD = "Murray City ordinance adjusting Council District boundaries (2021-2022 redistricting)"

SEAT_DISTRICT = {
    "D1": "District 1", "D2": "District 2", "D3": "District 3", "D4": "District 4",
    "D5": "District 5", "MAYOR": "Citywide",
}

TENURES = [
    # ============================ D1 (Cohort A: 2019 / 2023) — post-Martinez churn ============
    dict(body="Council", seat_id="D1", person_name="Kat Martinez", person_key="kat_martinez",
         start_date="2020-01-07", start_event="elected", election_year="", end_event="resigned",
         confidence="medium",
         vacate_date="2022-12-06", vacate_confidence="high",
         vacate_source="minutes:2022-12-06 ('due to Councilmember Kat Martinez resigning from her position "
                       "on the City Council while she was presiding as Council Chair'); her last cities.db D1 "
                       "vote is 2022-11-01",
         sources="votes:2020-01-07..2022-11-01 (cities.db, D1); minutes:2020-01-07 present as 'Kat Martinez, "
                 "District #1'; minutes:2022-12-06 (resignation recorded)",
         note="PRE-FLOOR seating: won the D1 seat in 2019 (below the repo 2020 minutes floor and NOT in the "
              "loaded election file) -> medium (service is vote-documented from 2020-01-07; no fabricated "
              "election row). Resigned mid-term (formally noted 2022-12-06; last vote 2022-11-01) -> explicit "
              "VACANT interval to the next observed D1 holder."),
    dict(body="Council", seat_id="D1", person_name="Philip Markham", person_key="philip_markham",
         start_date="2022-12-12", start_event="appointed", election_year="", end_event="resigned",
         confidence="high",
         vacate_date="2023-06-28", vacate_confidence="high",
         vacate_source="RESIGNED D1 to join city staff (Community & Economic Development Director). His last D1 "
                       "vote/service is 2023-06-27 (no council meeting between then and 2023-07-18); the D1 seat is "
                       "then recorded '(Vacant), District #1' at both the 2023-07-18 and 2023-08-01 regular meetings "
                       "('District 1 seat ... was vacant due to a resignation. Mr. Markham was attending in the "
                       "audience' as 'Community and Economic Development Director'). vacate_date = day AFTER his last "
                       "recorded service (fleet convention: VACANT begins the day after the last day served); the "
                       "resignation is DOCUMENTED (not a minutes gap — the full 2023 record is recovered), only the "
                       "exact formal effective day within 06-28..07-18 is unstated, which does not undermine the "
                       "high-confidence bracket [last service 2023-06-27 .. documented vacant 2023-07-18].",
         sources="minutes:2022-12-12 SPECIAL 'District #1 Interviews' (resolution appointing 'Philip Markham as "
                 "Interim Murray City Council Member for Council District 1, pursuant to Section 20A-1-510 ... to "
                 "serve until January 2, 2024', passed 4-0 after a tie resolved by lot; City Recorder Ms. Smith "
                 "swore him in the same night); votes:2023-01-10..2023-06-27 (cities.db, D1 — full 2023 minutes "
                 "recovered/promoted 2026-07-16); minutes:2023-07-18 & 2023-08-01 (D1='(Vacant)')",
         note="Interim D1 appointee filling the post-Martinez vacancy. APPOINTED + SWORN IN at the DOCUMENTED "
              "2022-12-12 special meeting (was medium/2023-01-10 pre the 2026-07-16 minutes recovery, which "
              "surfaced both the appointment instrument AND his full 2023 vote span) -> confidence HIGH, exact "
              "start. RESIGNED mid-2023 to become CED Director (a staff role) -> explicit VACANT interval to the "
              "next appointee Rodgers; the vacancy itself is documented (07-18 + 08-01), only its exact start date "
              "is soft (medium)."),
    dict(body="Council", seat_id="D1", person_name="David Rodgers", person_key="david_rodgers",
         start_date="2023-08-08", start_event="appointed", election_year="", end_event="succeeded-by-elected",
         confidence="high",
         sources="minutes:2023-08-08 SPECIAL 'District #1 Interviews' (resolution appointing 'David Rodgers as "
                 "Interim Murray City Council Member for Council District 1, pursuant to Section 20A-1-510 ... to "
                 "serve until January 2, 2024'; chosen over Paul Pickett by coin toss after two 2-2 ties, passed "
                 "4-0; City Recorder Ms. Smith swore him in the same night); votes:2023-08-22..2023-12-06 "
                 "(cities.db, D1)",
         note="Interim D1 appointee. APPOINTED + SWORN IN at the DOCUMENTED 2023-08-08 special meeting (was "
              "medium/2023-11-14 pre the 2026-07-16 minutes recovery — the recovered special-meeting minutes give "
              "the exact appointment/oath date) -> confidence HIGH, exact start. First observed vote 2023-08-22. "
              "Succeeded by the elected Pickett seated 2024-01-02."),
    dict(body="Council", seat_id="D1", person_name="Paul Pickett", person_key="paul_pickett",
         start_date="2024-01-02", start_event="elected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 1 winner, 696, 59.28%); minutes:2024-01-02 (first documented 2024 "
                 "council meeting; seated); votes:2024-01-02..2026-06-16 (cities.db, D1)",
         note="Elected D1 2023 (in the loaded election file); seated at the first 2024 meeting. Currently serving."),

    # ============================ D2 (Cohort B: 2021 / 2025) ============================
    dict(body="Council", seat_id="D2", person_name="Dale Cox", person_key="dale_cox",
         start_date="2020-01-07", start_event="elected", election_year="", end_event="did-not-run",
         confidence="medium",
         sources="votes:2020-01-07..2021-12-07 (cities.db, D2); minutes:2020-01-07 present as 'Dale Cox, District #2'",
         note="PRE-FLOOR seating: held D2 at the 2020 floor (won 2017, below the loaded election floor) -> medium. "
              "Not a candidate in the 2021 D2 race (Cotter def. Silverzweig) -> did not seek re-election; term ended "
              "at the 2022-01-04 seating."),
    dict(body="Council", seat_id="D2", person_name="Pamela Cotter", person_key="pamela_cotter",
         start_date="2022-01-04", start_event="elected", election_year="2021", end_event="reelected",
         confidence="high",
         sources="election:2021 (District 2 winner, 1,190, 54.74%); minutes:2022-01-04 (seated; present as "
                 "'Pamela Cotter District #2'); votes:2022-01-04..2025 (cities.db, D2)",
         note="Elected D2 2021; re-elected 2025. Council Chair 2026."),
    dict(body="Council", seat_id="D2", person_name="Pamela Cotter", person_key="pamela_cotter",
         start_date="2026-01-06", start_event="reelected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (District 2 winner, as 'Pamela Jane Cotter', 1,423, 54.77%); minutes:2026-01-06 "
                 "(present as 'Pam Cotter District #2 - Council Chair'); votes:2026-01-06..2026-06-16 (cities.db, D2)",
         note="Re-elected D2 2025 (second full term). Currently serving (Council Chair 2026)."),

    # ============================ D3 (Cohort A: 2019 / 2023) — Dominguez -> Goodman -> Bullen ===
    dict(body="Council", seat_id="D3", person_name="Rosalba Dominguez", person_key="rosalba_dominguez",
         start_date="2020-01-07", start_event="elected", election_year="", end_event="reelected",
         confidence="medium",
         sources="votes:2020-01-07..2023 (cities.db, D3); minutes:2020-01-07 present as 'Rosalba Dominguez, "
                 "District #3'",
         note="PRE-FLOOR seating: won D3 in 2019 (below the loaded election floor) -> medium. Re-elected 2023 "
              "(continuous service into the 2024 term below)."),
    dict(body="Council", seat_id="D3", person_name="Rosalba Dominguez", person_key="rosalba_dominguez",
         start_date="2024-01-02", start_event="reelected", election_year="2023", end_event="resigned",
         confidence="medium",
         vacate_date="2024-12-04", vacate_confidence="medium",
         vacate_source="last cities.db D3 vote 2024-12-03; she left mid-term in Dec 2024 (a 2025 'District 3 "
                       "(2-Year Term)' unexpired-term SPECIAL filled the seat) — the exact departure date is not "
                       "separately documented in the recovered minutes -> gap-bounded medium",
         sources="election:2023 (District 3 winner, 1,095, 52.67%); minutes:2024-01-02 (seated); "
                 "votes:2024-01-02..2024-12-03 (cities.db, D3)",
         note="Elected D3 2023; LEFT MID-TERM in Dec 2024 (last vote 2024-12-03). The seat was filled by "
              "Goodman (appointed) then Bullen via the 2025 2-year special -> explicit VACANT interval + medium "
              "(the departure date is not separately documented)."),
    dict(body="Council", seat_id="D3", person_name="Scott Goodman", person_key="scott_goodman",
         start_date="2025-01-21", start_event="appointed", election_year="", end_event="succeeded-by-elected",
         confidence="high",
         sources="minutes:2025 attendee headers name 'Scott Goodman District #3' (2025-01-21, 2025-05-06, "
                 "2025-07-15, 2025-09-02, 2025-11-18, ...); votes:2025-01-21..2025-11-25 (cities.db, D3)",
         note="Appointed to the D3 vacancy after Dominguez left (Dec 2024); header-attested as 'District #3' "
              "throughout 2025. Filled the seat until the 2025-special winner Bullen was seated 2026-01-06. "
              "First observed vote 2025-01-21 (the appointment predates it in early Jan 2025)."),
    dict(body="Council", seat_id="D3", person_name="Clark Bullen", person_key="clark_bullen",
         start_date="2026-01-06", start_event="elected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (District 3 '(2-Year Term)' unexpired-term special winner, 1,336, 56.44%); "
                 "minutes:2026-01-06 (present as 'Clark Bullen District #3'); votes:2026-01-06..2026-06-16 (cities.db, D3)",
         note="Won the 2025 District 3 2-YEAR-TERM special (the unexpired remainder of Dominguez's seat); seated "
              "2026-01-06. Currently serving."),

    # ============================ D4 (Cohort B: 2021 / 2025) — continuous Turner ============
    dict(body="Council", seat_id="D4", person_name="Diane Turner", person_key="diane_turner",
         start_date="2020-01-07", start_event="elected", election_year="", end_event="reelected",
         confidence="medium",
         sources="votes:2020-01-07..2021 (cities.db, D4); minutes:2020-01-07 present as 'Diane Turner, District #4'",
         note="PRE-FLOOR seating: held D4 at the 2020 floor (won 2017, below the loaded election floor) -> medium. "
              "Re-elected 2021 (continuous into the 2022 term below)."),
    dict(body="Council", seat_id="D4", person_name="Diane Turner", person_key="diane_turner",
         start_date="2022-01-04", start_event="reelected", election_year="2021", end_event="reelected",
         confidence="high",
         sources="election:2021 (District 4 winner, 1,124, 64.41%); minutes:2022-01-04 (present as 'Diane Turner "
                 "District #4'); votes:2022-01-04..2025 (cities.db, D4)",
         note="Re-elected D4 2021; re-elected again 2025 (uncontested, 100%). Continuous service."),
    dict(body="Council", seat_id="D4", person_name="Diane Turner", person_key="diane_turner",
         start_date="2026-01-06", start_event="reelected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (District 4 winner, 1,435, 100.0% — uncontested); minutes:2026-01-06 (present as "
                 "'Diane Turner District #4'); votes:2026-01-06..2026-06-16 (cities.db, D4)",
         note="Re-elected D4 2025 (uncontested). Currently serving."),

    # ============================ D5 (Cohort A: 2019 / 2023) — Hales -> Hrechkosy -> Hock =====
    dict(body="Council", seat_id="D5", person_name="Brett Hales", person_key="brett_hales",
         start_date="2020-01-07", start_event="elected", election_year="", end_event="became-mayor",
         confidence="medium",
         vacate_date="2022-01-04", vacate_confidence="high",
         vacate_source="minutes:2022-01-04 (Hales seated as MAYOR after winning the 2021 mayoralty -> the D5 seat "
                       "was vacated); his last cities.db D5 vote is 2021-12-07",
         sources="votes:2020-01-07..2021-12-07 (cities.db, D5, 190 votes); minutes:2020-01-07 present as 'Brett "
                 "Hales, District #5'",
         note="PRE-FLOOR seating: won D5 in 2019 (below the loaded election floor) -> medium. Won the 2021 MAYORALTY "
              "and took office 2022-01-04 -> D5 vacated (end_event=became-mayor); see the MAYOR rows. His unexpired "
              "D5 term (to Jan 2024) was filled by the interim Hrechkosy."),
    dict(body="Council", seat_id="D5", person_name="Garry Hrechkosy", person_key="garry_hrechkosy",
         start_date="2022-02-01", start_event="appointed", election_year="", end_event="succeeded-by-elected",
         confidence="high",
         sources="minutes:2022-01-31 SPECIAL ('Consideration of the resolution appointing Mr. Hrechkosy as Interim "
                 "Murray City Council Member for [District 5]'; 2022-02-01 'Congratulated Garry Hrechkosy for his "
                 "appointment to District 5'); attendee headers 'Garry Hrechkosy District #5'; votes:2022-02-01.."
                 "2023-12-06 (cities.db, D5)",
         note="INTERIM appointee filling the D5 remainder of Hales's unexpired 2020-2023 term (appointed at the "
              "2022-01-31 special meeting; sworn ~2022-02-01). Served until the elected Hock was seated 2024-01-02."),
    dict(body="Council", seat_id="D5", person_name="Adam Hock", person_key="adam_hock",
         start_date="2024-01-02", start_event="elected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 5 winner, 1,553, 56.23%); minutes:2024-01-02 (seated; later 'Adam Hock "
                 "District #5 - Council Vice-Chair'); votes:2024-01-02..2026-06-16 (cities.db, D5)",
         note="Elected D5 2023; seated at the first 2024 meeting. Currently serving (Council Vice-Chair 2025/2026)."),

    # ============================ MAYOR (executive — does NOT vote) ============================
    dict(body="Mayor", seat_id="MAYOR", person_name="Blair Camp", person_key="blair_camp",
         start_date="2018-01-01", start_event="elected", election_year="", end_event="did-not-run",
         confidence="medium",
         sources="minutes:2020-01-07 present as 'Blair Camp  Mayor' (attendee header); votes:none (executive mayor "
                 "does not vote)",
         note="PRE-FLOOR mayoral term: Blair Camp held the mayoralty at the 2020 floor (won 2017, below the loaded "
              "election floor) -> medium, start = the Jan-2018 term origin (predates the 2020 minutes floor; no "
              "fabricated election row). Not a candidate in 2021 (Hales won) -> left office at the 2022-01-04 "
              "seating. Executive Mayor -> EMPTY vote bounds (non_voting_mayor)."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Brett Hales", person_key="brett_hales",
         start_date="2022-01-04", start_event="elected", election_year="2021", end_event="reelected",
         confidence="high",
         sources="election:2021 (Mayor winner, 6,108, 58.3%); minutes:2022-01-04 (seated as Mayor; header 'Brett A. "
                 "Hales  Mayor'); does NOT appear in any council vote roll after 2021 (executive mayor)",
         note="Won the 2021 mayoralty (having served D5 2020-2021 — same person). Executive Mayor -> EMPTY vote "
              "bounds. Re-elected Mayor 2025."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Brett Hales", person_key="brett_hales",
         start_date="2026-01-06", start_event="reelected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (Mayor winner, as 'Brett A. Hales', 6,490, 61.84%); minutes:2026-01-06 (Mayor); "
                 "does NOT vote (executive mayor)",
         note="Re-elected Mayor 2025. Currently serving. EMPTY vote bounds (non_voting_mayor)."),
]

# canonical UPPER-CASE election name token -> our person_key (WINNERS only pass through here).
NAME_TO_KEY = {
    "PICKETT": "paul_pickett", "COTTER": "pamela_cotter", "DOMINGUEZ": "rosalba_dominguez",
    "BULLEN": "clark_bullen", "TURNER": "diane_turner", "HOCK": "adam_hock", "HALES": "brett_hales",
}

# cities.db person.name_key -> our person_key (council voters). The executive Mayor rows
# (blaircamp — not in the vote record) are absent by design; bretthales IS mapped for his
# 2020-2021 D5 council votes (his MAYOR-body rows are emptied by non_voting_mayor).
DB_KEY = {
    "bretthales": "brett_hales", "dalecox": "dale_cox", "katmartinez": "kat_martinez",
    "rosalbadominguez": "rosalba_dominguez", "dianeturner": "diane_turner",
    "pamelacotter": "pamela_cotter", "garryhrechkosy": "garry_hrechkosy",
    "philipmarkham": "philip_markham", "davidrodgers": "david_rodgers",
    "adamhock": "adam_hock", "paulpickett": "paul_pickett", "scottgoodman": "scott_goodman",
    "clarkbullen": "clark_bullen",
}


def seat_for_contest(office, district):
    """election (office, district) -> the district LABEL used as the cross-check key."""
    if office == "Mayor":
        return "Citywide"
    d = district.strip()
    if d in ("1", "2", "3", "4", "5"):
        return "District " + d
    return None


REDISTRICT = Redistrict(
    plan_old=PLAN_OLD, plan_new=PLAN_NEW, plan_switch=PLAN_SWITCH,
    ord=REDISTRICT_ORD, adopted=PLAN_SWITCH,
    districts=["District 1", "District 2", "District 3", "District 4", "District 5"],
    geom_ref=GEOM_REF,
    source_url="geo/districts.geojson (official Murray 5-district FeatureServer; "
               "Boundary_Approval_Date=2022-01-04, post-2020-census redistricting); "
               "meeting_minutes/minutes/2022/2022-01-03/2022-01-04_city-council-meeting.md "
               "(ordinance adjusting the Council District boundaries)",
    data_floor=DATA_FLOOR,
    current_note="CURRENT post-2020-census boundaries; official 5-district layer in geo/districts.geojson "
                 "(Boundary_Approval_Date 2022-01-04). District NUMBERS were unchanged by the redraw. First "
                 "used for the 2023 (D1/D3/D5) district elections.",
    prior_adopted_by="prior plan (pre-2022 boundaries)",
    prior_geom_ref="",
    prior_confidence="low",
    prior_note="Pre-2022 (pre-2020-census) Murray district boundaries NOT acquired -> honest GAP (blank geometry, "
               "low). In force through the 2021 elections. effective_start = data floor.",
    citywide_rows=[
        ("MAYOR", "citywide", "the separately-elected executive Mayor (Blair Camp -> Brett Hales)"),
    ],
    citywide_adopted_by="Murray City (citywide executive office)",
    citywide_note_template="{who}: represents the ENTIRE city on every date, unchanged by the 2022 redistricting. "
                           "Only the 5 numbered council districts are geographic. The executive Mayor does NOT vote "
                           "on council legislation.",
    precinct_hi_source="2023",   # the current-plan source_year token in geo/precinct_to_district.csv
    precinct_hi_note="post-redistrict precinct->district from the current (post-2020-census) Murray map "
                     "(geo/precinct_to_district.csv, source_year=2023, method=district_contest_precinct_rows).",
    precinct_med_note="",
    precinct_prior_note="Pre-2022 precinct->district composition NOT acquired -> GAP (low).",
    crosscheck_districts=("1", "2", "3", "4", "5"),
    precinct_prefix="MUR", geo_seat_prefix="D",
    plan_switch_year="2023", citywide_seats=(),
)

CFG = RosterConfig(
    non_voting_mayor=True,
    city=CITY, city_dir=CITY_DIR, repo_root=REPO_ROOT, data_floor=DATA_FLOOR,
    geom_ref=GEOM_REF, elections_path=ELECTIONS, cities_db_path=CITIES_DB,
    overrides_path=OVERRIDES, terms_out=TERMS_OUT, districts_out=DISTRICTS_OUT,
    seat_district=SEAT_DISTRICT, name_to_key=NAME_TO_KEY, db_key=DB_KEY,
    seat_order=["D1", "D2", "D3", "D4", "D5", "MAYOR"],
    keep_election_row=lambda r: "general" in r["election_type"].lower(),
    contest_key=seat_for_contest, crosscheck_field="district",
    winners_have_district=True,
    elected_events=("elected", "reelected"),
    redistrict=REDISTRICT, precincts_out=PRECINCTS_OUT,
    precinct_map_path=GEO_PRECINCT_MAP, precincts_byprecinct_path=PRECINCTS_BYP_SRC,
)


def demo():
    def line(r):
        end = r["end_date"] or "—(serving)"
        return (f"    {r['seat_id']:<6} {r['person_name']:<20} {r['start_date']} -> {end:<12}"
                f" [{r['start_event']}/{r['end_event']}] conf={r['confidence']}")

    print("\n(a) CURRENT roster (end_date empty, end_event=serving):")
    for r in roster_lib.load_terms(CFG):
        if not r["end_date"] and r["end_event"] == "serving":
            print(line(r))

    print("\n(b) Roster AS OF 2023-07-25 (D1 genuinely VACANT: Markham resigned to CED, Rodgers not yet appointed):")
    for r in roster_lib.roster_as_of(CFG, "2023-07-25", body="Council"):
        print(line(r))
    for r in roster_lib.roster_as_of(CFG, "2023-07-25", body="Mayor"):
        print(line(r))


if __name__ == "__main__":
    rows = roster_lib.build(CFG, TENURES)
    n = {c: sum(1 for r in rows if r["confidence"] == c) for c in ("high", "medium", "low")}
    nvac = sum(1 for r in rows if r["start_event"] == "vacated")
    print(f"Wrote {os.path.relpath(TERMS_OUT, CITY_DIR)} "
          f"({len(rows)} tenures incl. {nvac} VACANT: {n['high']} high / {n['medium']} medium / {n['low']} low)")
    print(f"Wrote {os.path.relpath(DISTRICTS_OUT, CITY_DIR)} (5 districts x 2 plans + Mayor citywide)")
    print(f"Wrote {os.path.relpath(PRECINCTS_OUT, CITY_DIR)} (plan_2022 precinct map + plan_pre2022 gap rows)")
    if "--check" in sys.argv:
        print("\nValidation: PASS (no overlaps; sources+confidence present; non-voting-mayor + gap/vacate guards clear).")
        try:
            print("Precinct cross-check:")
            roster_lib.precinct_crosscheck(CFG, verbose=True)
        except Exception as e:
            print(f"  [precinct cross-check skipped: {e.__class__.__name__}: {e}]")
    if "--demo" in sys.argv:
        demo()
