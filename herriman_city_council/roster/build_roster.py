#!/usr/bin/env python3
"""build_roster.py — rolling council-roster for HERRIMAN (a slowly-changing-dimension /
interval table of who holds each council + mayor seat over time).

Herriman is a **DISTRICT city with a VOTING MAYOR** (the Millcreek model): **4 single-member
council districts (D1..D4) + a separately-elected Mayor who is a FULL voting member** of the
council. A complete roll call tops out at **5** (4 district members + the Mayor), never 4 —
`non_voting_mayor=False`, the Mayor is modelled as a real voting seat (kept in DB_KEY, gets
clamped vote bounds like any councilmember). Verified at source: Mayor David Watts casts a
decisive Nay on 2020-01-08 (roll of 5); Mayor Lorin Palmer votes in every roll 2022+.

THIN DRIVER: this file holds only Herriman-specific DATA (the curated TENURES, name maps, the
2022-redistricting facts) + config; all generic mechanics live in ../../scripts/roster_lib.py.
Modelled on the west_jordan driver (the DISTRICT + redistricting + precinct-crosscheck template),
minus West Jordan's at-large seats and non-voting mayor.

DERIVED LAYER — regenerable, never hand-edited. Canonical inputs:
  1. election_results/herriman_results_by_candidate.csv  (winners -> elected/reelected; 2017+ rostered)
  2. cities.db  role table (city='herriman', body='Council')  (observed vote bounds; incl. the mayor)
  3. meeting_minutes/minutes/**  (oath/seating dates, Ord. 2022-08 redistricting, the 2025 D4 vacancy)
  4. roster/roster_overrides.csv  (hand corrections; applied LAST, win ties)
  5. geo/precinct_to_district.csv  (read DIRECTLY since 2026-07-19: roster_lib.write_precincts
     accepts a map with no source_year column via the explicit precinct_source_default token
     -- the H-A hardening; the old source_year-wrapper sidecar is RETIRED.)

Outputs (idempotent — re-running reproduces them byte-for-byte):
  roster/council_terms.csv      one row per seat-tenure (4 districts + MAYOR)
  roster/district_versions.csv  boundary interval table — 4 districts x 2 plans + a citywide Mayor row
  roster/district_precincts.csv versioned precinct->district composition (plan-scoped; districts only)

Usage:
  python3 roster/build_roster.py            # regenerate the CSVs
  python3 roster/build_roster.py --demo     # regenerate + print the demo queries
  python3 roster/build_roster.py --check    # regenerate + validations + precinct cross-check

Cardinal rule (repo CLAUDE.md): NEVER fabricate. Unknown seat-holder / boundary / date ->
explicit VACANT / gap + confidence + a note, never a guess.

Provenance / confidence model (Herriman):
  high   = an in-file election win (2019/2021/2023/2025) seated at a documented January meeting/oath
           and corroborated by the cities.db named-vote record, OR the fully-documented 2025 D4
           resignation->appointment->special-election chain.
  medium = a Cycle-A HOLDOVER serving at the 2020 floor whose SEATING election (2017) predates the
           minutes floor: service is vote-documented from 2020-01-08 but the Jan-2018 term origin is
           below the floor (Clint Smith D2, Sherrie Ohrn D3, Mayor David Watts — three rows).
  low    = genuinely unknown / not-acquired (flagged) — the prior-plan (pre-2022) district +
           precinct geometry is an honest GAP (not on disk); no low rows in council_terms.

STRUCTURAL FACTS (verified in source):
  * VOTING MAYOR (roll of 5). 2020-01-08 minutes: Mayor David Watts presides AND votes (Aye on one
    motion, a decisive Nay on another); "Mayor Watts welcomed Steven Shields as a new City
    Councilmember, representing District 4." non_voting_mayor=False.
  * THE AT-LARGE -> DISTRICT TRANSITION IS WHOLLY PRE-FLOOR (a flagged finding). The task hypothesized
    a 2017/2019 at-large->district switch to model as separate chains. The ELECTION RECORD shows the
    switch actually happened 2009->2011: Herriman elected 2 AT-LARGE council seats in 2007 & 2009,
    then numbered "Council 1/2/4" DISTRICT contests from 2011 onward (election_results/CLAUDE.md).
    That is ~9 years below the 2020 data floor, so there are NO at-large-era tenures in the roster
    window and NO at-large seats are modelled — the entire rostered record is stable 4-district +
    Mayor. (Documented here so a reader doesn't expect at-large chains.)
  * THE 2025 D4 mid-term vacancy (the headline documented case). Steven Shields (D4, elected 2019 &
    2023) served his LAST meeting 2023... 2025-04-23 (Mayor Palmer "noted it would be Councilmember
    Shields' last meeting"; Shields gave farewell remarks; his last cities.db D4 vote is 2025-04-23).
    At a 2025-05-15 SPECIAL meeting the Council interviewed applicants and adopted a resolution "to
    fill the vacant Herriman City Council District 4 seat, with the term beginning May 15, 2025, and
    ending January 5, 2026," appointing Terrah Anderson (present + congratulated on her appointment
    2025-05-28, her first vote). Anderson then WON the Nov-2025 D4 2-year SHORT-TERM special (1,431,
    uncontested) -> reseated 2026-01-14 for the remainder. Yields an explicit VACANT D4
    [2025-04-24, 2025-05-15).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.dirname(HERE)                 # herriman_city_council/
REPO_ROOT = os.path.dirname(CITY_DIR)            # civic-data/
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import roster_lib
from roster_lib import RosterConfig, Redistrict

ELECTIONS = os.path.join(CITY_DIR, "election_results", "herriman_results_by_candidate.csv")
PRECINCTS_BYP_SRC = os.path.join(CITY_DIR, "election_results", "herriman_results_by_precinct.csv")
PRECINCT_MAP = os.path.join(CITY_DIR, "geo", "precinct_to_district.csv")  # canonical geo map (H-A: sidecar retired 2026-07-19)
CITIES_DB = os.path.join(REPO_ROOT, "cities.db")
OVERRIDES = os.path.join(HERE, "roster_overrides.csv")
TERMS_OUT = os.path.join(HERE, "council_terms.csv")
DISTRICTS_OUT = os.path.join(HERE, "district_versions.csv")
PRECINCTS_OUT = os.path.join(HERE, "district_precincts.csv")

CITY = "herriman"
DATA_FLOOR = "2020-01-01"
GEOM_REF = "geo/districts.geojson"

# The real redistricting event (spot-checked against source minutes 2022-03-09):
#   Ordinance No 2022-08 "realigning the Council District boundaries," adopted 2022-03-09 (work
#   meeting #2) on a 5-0 roll — Henderson (mover), Hodges (second), Ohrn, Shields, AND Mayor Lorin
#   Palmer all Aye (a VOTING-mayor roll of 5). First used for the 2023 D1/D4 district elections;
#   the pre-2022 lines governed the 2019 elections. Redistricting driven by the 2020 Census
#   (Herriman pop. 55,144; ideal district ~13,786; discussed 2022-01-12).
REDISTRICT_ORD = "Ordinance 2022-08"
REDISTRICT_ADOPTED = "2022-03-09"
PLAN_OLD = "plan_pre2022"
PLAN_NEW = "plan_2022"
PLAN_SWITCH = "2022-03-09"
SRC_URL = ("meeting_minutes/minutes/2022/2022-03-07/2022-03-09_city-council-work-meeting-2.md "
           "(Ordinance No 2022-08 realigning the Council District boundaries, adopted 2022-03-09, "
           "passed 5-0 incl. Mayor Palmer)")

SEAT_DISTRICT = {
    "D1": "District 1", "D2": "District 2", "D3": "District 3", "D4": "District 4",
    "MAYOR": "Citywide",
}

TENURES = [
    # ============================ D1 (Cycle B: 2019 / 2023) — Henderson, continuous ============
    dict(body="Council", seat_id="D1", person_name="Jared Henderson", person_key="jared_henderson",
         start_date="2020-01-08", start_event="elected", election_year="2019", end_event="reelected",
         confidence="high",
         sources="election:2019 (District 1 winner, unopposed 601/100%); minutes:present 2020-01-08 "
                 "(first documented 2020 council meeting); votes:2020-01-08.. (cities.db, Council/D1)",
         note="Elected D1 2019 (this is the term active at the 2020 floor; his earlier 2015 D1 term "
              "is wholly pre-floor and not separately rostered). Re-elected 2023 -> continuous."),
    dict(body="Council", seat_id="D1", person_name="Jared Henderson", person_key="jared_henderson",
         start_date="2024-01-10", start_event="reelected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 1 winner, def. Chris Roberts 54.42%); minutes:2024-01-10 "
                 "(first documented 2024 council meeting; 2023-cycle seating); votes:continuous through "
                 "2026-05-27 (cities.db, Council/D1)",
         note="Re-elected D1 2023 (first D1 term on the plan_2022 lines; seated 2024-01-10). Serving."),

    # ============================ D2 (Cycle A: 2017 / 2021 / 2025) ============================
    dict(body="Council", seat_id="D2", person_name="Clint Smith", person_key="clint_smith",
         start_date="2018-01-01", start_event="elected", election_year="2017", end_event="did-not-run",
         confidence="medium",
         sources="election:2017 (District 2 winner, def. Jared D. Richardson 50.91%); votes:2020-01-08.."
                 "2021-12-08 (cities.db, Council/D2); minutes:2022-01-12 (replaced at 2021-cycle seating)",
         note="Cycle-A HOLDOVER at the 2020 floor: the Jan-2018 oath predates the 2020 minutes floor "
              "-> start 2018-01-01 inferred from the cycle (medium); service is vote-documented from "
              "2020-01-08. Did NOT seek D2 re-election in 2021 (ran for MAYOR 2021 instead and lost to "
              "Palmer) -> term ended Jan 2022, mechanism = ran-for-other-office -> did-not-run."),
    dict(body="Council", seat_id="D2", person_name="Teddy Hodges", person_key="teddy_hodges",
         start_date="2022-01-12", start_event="elected", election_year="2021", end_event="reelected",
         confidence="high",
         sources="election:2021 (District 2 winner, def. Aly Escobar 69.19%); minutes:present 2022-01-12 "
                 "(first documented 2022 council meeting); votes:2022-01-12.. (cities.db, Council/D2)",
         note="Elected D2 2021. Re-elected 2025 -> continuous."),
    dict(body="Council", seat_id="D2", person_name="Teddy Hodges", person_key="teddy_hodges",
         start_date="2026-01-14", start_event="reelected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (District 2 winner, unopposed 1,959/100%); minutes:2026-01-14 (first "
                 "documented 2026 council meeting; 2025-cycle seating); votes:continuous (cities.db, D2)",
         note="Re-elected D2 2025. Serving."),

    # ============================ D3 (Cycle A: 2017 / 2021 / 2025) ============================
    dict(body="Council", seat_id="D3", person_name="Sherrie Ohrn", person_key="sherrie_ohrn",
         start_date="2018-01-01", start_event="elected", election_year="2017", end_event="reelected",
         confidence="medium",
         sources="election:2017 (District 3 winner, def. Cody Stromberg 50.42% — a +9 squeaker); "
                 "votes:2020-01-08.. (cities.db, Council/D3)",
         note="Cycle-A HOLDOVER at the 2020 floor: Jan-2018 oath predates the minutes floor -> start "
              "2018-01-01 inferred (medium); service vote-documented from 2020-01-08. Re-elected 2021."),
    dict(body="Council", seat_id="D3", person_name="Sherrie Ohrn", person_key="sherrie_ohrn",
         start_date="2022-01-12", start_event="reelected", election_year="2021", end_event="did-not-run",
         confidence="high",
         sources="election:2021 (District 3 winner, unopposed 1,178/100%); minutes:present 2022-01-12; "
                 "votes:2022-01-12..2025-12-10 (cities.db, Council/D3)",
         note="Re-elected D3 2021. NOT a candidate in 2025 (Basham won D3) -> served the full term, did "
              "not seek re-election; end date is the successor's 2026-01-14 seating (precise), mechanism "
              "(retire vs decline) unstated -> did-not-run. Last cities.db D3 vote 2025-12-10."),
    dict(body="Council", seat_id="D3", person_name="Matt Basham", person_key="matt_basham",
         start_date="2026-01-14", start_event="elected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (District 3 winner, def. Heather Garcia 56.94%); minutes:2026-01-14 "
                 "(first documented 2026 council meeting); votes:2026-01-14.. (cities.db, Council/D3)",
         note="Elected D3 2025 (seated 2026-01-14). Serving."),

    # ============================ D4 (Cycle B: 2019 / 2023 + 2025 mid-term special) ============
    dict(body="Council", seat_id="D4", person_name="Steven Shields", person_key="steven_shields",
         start_date="2020-01-08", start_event="elected", election_year="2019", end_event="reelected",
         confidence="high",
         sources="election:2019 (District 4 winner, def. Darryl Fenn 68.94%); minutes:2020-01-08 ('Mayor "
                 "Watts welcomed Steven Shields as a new City Councilmember, representing District 4'); "
                 "votes:2020-01-08.. (cities.db, Council/D4)",
         note="Elected D4 2019 (seated at the 2020 floor). Re-elected 2023."),
    dict(body="Council", seat_id="D4", person_name="Steven Shields", person_key="steven_shields",
         start_date="2024-01-10", start_event="reelected", election_year="2023", end_event="resigned",
         confidence="high",
         vacate_date="2025-04-24", vacate_confidence="high",
         vacate_source="minutes:2025-04-23 (Mayor Palmer 'noted it would be Councilmember Shields' last "
                       "meeting'; Shields offered farewell remarks; last cities.db D4 vote 2025-04-23); "
                       "minutes:2025-05-15 SPECIAL ('fill the vacant Herriman City Council District 4 "
                       "seat, with the term beginning May 15, 2025')",
         sources="election:2023 (District 4 winner, def. Matt Bello 65.61%); minutes:2024-01-10 (2023-"
                 "cycle seating); votes:2024-01-10..2025-04-23 (cities.db, Council/D4)",
         note="Re-elected D4 2023 (term to Jan 2028). LEFT MID-TERM: 2025-04-23 was his documented last "
              "meeting -> explicit VACANT D4 [2025-04-24, 2025-05-15) until the appointment."),
    dict(body="Council", seat_id="D4", person_name="Terrah Anderson", person_key="terrah_anderson",
         start_date="2025-05-15", start_event="appointed", election_year="", end_event="succeeded-by-elected",
         confidence="high",
         sources="minutes:2025-05-15 SPECIAL (Council interviewed 4 applicants and adopted a resolution "
                 "'to appoint a qualified individual to fill the vacant Herriman City Council District 4 "
                 "seat, with the term beginning May 15, 2025, and ending January 5, 2026' -> Terrah "
                 "Anderson; welcomed/congratulated on her appointment 2025-05-28); votes:2025-05-28.. "
                 "(cities.db, Council/D4)",
         note="APPOINTED to the D4 vacancy 2025-05-15 (resolution term May 15 2025 - Jan 5 2026). She had "
              "previously served on the Herriman Planning Commission (2023-2025 — one person, two bodies; "
              "her PC votes are body='PlanningCommission' and do NOT leak into these Council bounds). The "
              "appointment ends when her elected 2-year term is seated 2026-01-14."),
    dict(body="Council", seat_id="D4", person_name="Terrah Anderson", person_key="terrah_anderson",
         start_date="2026-01-14", start_event="elected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (District 4 '2 Year Term' short-term SPECIAL winner, unopposed 1,431/100% "
                 "— filling the unexpired Shields term to Jan 2028); minutes:2026-01-14 (2025-cycle "
                 "seating); votes:continuous through 2026-05-27 (cities.db, Council/D4)",
         note="Won the Nov-2025 D4 2-YEAR SHORT-TERM special (the off-cycle contest that filled Shields' "
              "unexpired seat; see election_results/CLAUDE.md). Same person as the May-2025 appointee "
              "above; vote bounds are clamped per tenure. Serving."),

    # ============================ MAYOR (Cycle A: 2017 / 2021 / 2025) — VOTING ============
    dict(body="Mayor", seat_id="MAYOR", person_name="David Watts", person_key="david_watts",
         start_date="2018-01-01", start_event="elected", election_year="2017", end_event="did-not-run",
         confidence="medium",
         sources="election:2017 (Mayor winner, def. Coralee Wessman-Moser 53.59%); minutes:2020-01-08 "
                 "('Presiding: Mayor David Watts'; casts an Aye and a decisive Nay — a VOTING mayor, roll "
                 "of 5); votes:2020-01-08..2021-12-08 (cities.db, Council — mayoral votes)",
         note="Cycle-A HOLDOVER at the 2020 floor: Jan-2018 oath predates the minutes floor -> start "
              "2018-01-01 inferred (medium). The Herriman Mayor is a FULL voting council member "
              "(non_voting_mayor=False). NOT a candidate for Mayor in 2021 (Palmer won) -> term ended "
              "Jan 2022, did-not-run."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Lorin Palmer", person_key="lorin_palmer",
         start_date="2022-01-12", start_event="elected", election_year="2021", end_event="reelected",
         confidence="high",
         sources="election:2021 (Mayor winner, def. Clint Smith 63.21%); minutes:2022-01-12+ (presiding "
                 "and voting as Mayor Palmer, roll of 5); votes:2022-01-12.. (cities.db, Council — mayoral)",
         note="Elected Mayor 2021. He had served on the Herriman Planning Commission (2020-2021) BEFORE "
              "becoming Mayor (one person, two bodies — his PC votes are body='PlanningCommission' and do "
              "not leak into these mayoral Council bounds). Re-elected 2025."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Lorin Palmer", person_key="lorin_palmer",
         start_date="2026-01-14", start_event="reelected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (Mayor winner, def. Ty R. Brady 75.23%); minutes:2026-01-14 (2025-cycle "
                 "seating); votes:continuous through 2026-05-27 (cities.db, Council — mayoral)",
         note="Re-elected Mayor 2025. Continues as a VOTING mayor. Serving."),
]

# canonical UPPER-CASE election name token -> our person_key. No two Herriman general winners
# (2017+) share a surname, so no disambiguators are needed. Only WINNERS pass through canon_key.
NAME_TO_KEY = {
    "HENDERSON": "jared_henderson", "SMITH": "clint_smith", "OHRN": "sherrie_ohrn",
    "SHIELDS": "steven_shields", "WATTS": "david_watts", "HODGES": "teddy_hodges",
    "PALMER": "lorin_palmer", "BASHAM": "matt_basham", "ANDERSON": "terrah_anderson",
}

# cities.db person.name_key -> our person_key (council voters, INCLUDING the voting mayors
# Watts + Palmer). OCR-junk / PC-only rows are never mapped.
DB_KEY = {
    "jaredhenderson": "jared_henderson", "clintsmith": "clint_smith",
    "sherrieohrn": "sherrie_ohrn", "stevenshields": "steven_shields",
    "davidwatts": "david_watts", "lorinpalmer": "lorin_palmer",
    "teddyhodges": "teddy_hodges", "terrahanderson": "terrah_anderson",
    "mattbasham": "matt_basham",
}


def seat_for_contest(office, district):
    """election (office, district) -> the STABLE seat_id used as the cross-check key
    (crosscheck_field='seat_id'). Herriman: 4 numbered districts + a citywide Mayor."""
    if office == "Mayor":
        return "MAYOR"
    d = district.strip()
    if d in ("1", "2", "3", "4"):
        return "D" + d
    return None


REDISTRICT = Redistrict(
    plan_old=PLAN_OLD, plan_new=PLAN_NEW, plan_switch=PLAN_SWITCH,
    ord=REDISTRICT_ORD, adopted=REDISTRICT_ADOPTED,
    districts=["District 1", "District 2", "District 3", "District 4"],
    geom_ref=GEOM_REF, source_url=SRC_URL, data_floor=DATA_FLOOR,
    current_note=(f"CURRENT post-2020-census boundaries. {REDISTRICT_ORD} ('realigning the Council "
                  "District boundaries') adopted " + REDISTRICT_ADOPTED + " on a 5-0 roll (Henderson "
                  "mover / Hodges second; Ohrn, Shields, AND Mayor Palmer all Aye — a voting-mayor roll "
                  "of 5). geometry_ref is Herriman's OFFICIAL 4-district FeatureServer layer in "
                  "geo/districts.geojson; precinct->district in geo/precinct_to_district.csv. First used "
                  "for the 2023 district elections."),
    prior_adopted_by="prior plan (pre-2022 boundaries)",
    prior_note=("Prior-plan (pre-2022) district boundaries NOT acquired -> honest GAP (blank geometry_ref, "
                "confidence low). In force through the 2019 elections. effective_start = data floor. The "
                "at-large era (2007/2009, 2 at-large seats) predates even this and is wholly pre-floor "
                "(the district map itself dates to the 2011 cycle)."),
    citywide_rows=[
        ("MAYOR", "citywide", "the separately-elected VOTING Mayor (David Watts 2018-2022 -> Lorin "
                              "Palmer 2022+)"),
    ],
    citywide_adopted_by="Herriman City (citywide mayor)",
    citywide_note_template=("{who}: represents the ENTIRE city on every date, unchanged by the 2022 "
                            "redistricting. Herriman's Mayor is a FULL VOTING council member (roll of 5) "
                            "— only the 4 numbered districts are geographic."),
    precinct_hi_source="current",
    precinct_source_default="current",   # H-A: geo map has no source_year column; explicit token
    precinct_hi_note=("current post-2020-census precinct->district read directly from geo/precinct_to_district.csv "
                      "(no source_year column — the configured precinct_source_default token 'current' "
                      "applies; H-A hardening 2026-07-19, wrapper sidecar retired). "
                      "Official 4-district layer; districts only (the Mayor is city-wide)."),
    precinct_med_note="",
    precinct_prior_note=("Prior-plan (pre-2022) precinct->district composition NOT acquired -> honest GAP."),
    crosscheck_districts=("1", "2", "3", "4"),
    precinct_prefix="HER", geo_seat_prefix="D",
    plan_switch_year="2023", citywide_seats=(),
)

CFG = RosterConfig(
    non_voting_mayor=False,     # Herriman's Mayor VOTES (roll of 5) — a real voting seat
    city=CITY, city_dir=CITY_DIR, repo_root=REPO_ROOT, data_floor=DATA_FLOOR,
    geom_ref=GEOM_REF, elections_path=ELECTIONS, cities_db_path=CITIES_DB,
    overrides_path=OVERRIDES, terms_out=TERMS_OUT, districts_out=DISTRICTS_OUT,
    seat_district=SEAT_DISTRICT, name_to_key=NAME_TO_KEY, db_key=DB_KEY,
    seat_order=["D1", "D2", "D3", "D4", "MAYOR"],
    # municipal GENERAL winners, 2017+ (the cycles the roster spans). Herriman's election data
    # reaches to 2007 but 2007/2009 are AT-LARGE and 2011-2015 are pre-floor district cycles not
    # rostered; including them would print forever-unmappable cross-check flags.
    keep_election_row=lambda r: (r["election_type"].strip().lower() == "municipal general"
                                 and int(r["year"]) >= 2017),
    contest_key=seat_for_contest, crosscheck_field="seat_id",
    winners_have_district=True,
    elected_events=("elected", "reelected", "became-mayor"),
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

    print("\n(b) Roster AS OF 2025-05-01 (during the D4 vacancy — Shields left, Anderson not yet appointed):")
    for r in roster_lib.roster_as_of(CFG, "2025-05-01", body="Council"):
        print(line(r))
    for r in roster_lib.roster_as_of(CFG, "2025-05-01", body="Mayor"):
        print(line(r))

    print("\n(c) Address+date -> representatives (via geo/address_to_district.py — 1 district + Mayor):")
    addr = "5355 W Herriman Main St, Herriman, UT 84096"   # City Hall -> D2
    for d in ("2026-02-01", "2020-06-01"):
        res = roster_lib.representatives_for_address(CFG, addr, d, latlon=(40.5141, -112.0330))
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
          f"(4 districts x 2 plans + citywide Mayor; redistricting {REDISTRICT_ORD})")
    print(f"Wrote {os.path.relpath(PRECINCTS_OUT, CITY_DIR)} "
          f"(plan_2022 precinct map + plan_pre2022 gap rows; districts only)")
    if "--check" in sys.argv:
        print("\nValidation: PASS (no overlaps; sources+confidence present; voting-mayor + gap/vacate guards clear).")
        print("Precinct cross-check:")
        roster_lib.precinct_crosscheck(CFG, verbose=True)
    if "--demo" in sys.argv:
        demo()
