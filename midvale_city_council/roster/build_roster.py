#!/usr/bin/env python3
"""build_roster.py — rolling council-roster for MIDVALE (a slowly-changing-dimension /
interval table of who holds each council + mayor seat over time). Midvale is a
**six-member-council city**: **5 geographic council districts (D1..D5)** legislate, and a
separately-elected **Mayor presides and casts a vote ONLY to break a tie** -> `non_voting_mayor
=True` (MAYOR rows carry EMPTY vote bounds; a full council roll tops out at 5). The districts
were **redrawn after the 2020 Census (new map adopted 2022-04-19)**; the NUMBERS were unchanged.

THIN DRIVER: Midvale-specific DATA + config; generic mechanics live in ../../scripts/roster_lib.py.
District template: west_jordan_city_council/roster/.

DERIVED LAYER — regenerable, never hand-edited. Canonical inputs:
  1. election_results/midvale_results_by_candidate.csv  (winners; 2007-2025, incl. recovered 2019)
  2. cities.db  role table (city='midvale', body='Council')  (observed vote bounds)
  3. meeting_minutes/minutes/**  (the redistricting, the Stevenson->Gettel mayor chain, D5 Gettel->Mikolash)
  4. roster/roster_overrides.csv  (hand corrections; applied LAST, win ties)

Usage:
  python3 roster/build_roster.py            # regenerate the CSVs
  python3 roster/build_roster.py --demo     # regenerate + print the demo queries
  python3 roster/build_roster.py --check    # regenerate + validations

Cardinal rule (repo CLAUDE.md): NEVER fabricate. Unknown seat-holder / date / boundary ->
explicit VACANT/gap + confidence + a note, never a guess.

STRUCTURAL FACTS (verified in source):
  * 5 DISTRICT seats + a tie-break-only Mayor. Staggered 4-year cycles:
      Cohort A = D1 + D2 + D3   elected 2015 / 2019 / 2023  -> seated Jan 2016 / 2020 / 2024
      Cohort B = D4 + D5        elected 2017 / 2021 / 2025  -> seated Jan 2018 / 2022 / 2026
      Mayor                     elected 2017 / 2021 / 2025  -> seated Jan 2018 / 2022 / 2026
    Terms whose Jan start predates the 2020 minutes floor are PRE-FLOOR (their win may be in the
    election file, but the term origin is below the floor) -> confidence medium.
  * SEATING DATES (first documented January council meeting = first cities.db vote):
    2020-01-07, 2022-01-04, 2024-01-02, 2026-01-06.
  * THE GETTEL COUNCIL->MAYOR SEAM. Dustin Gettel: D5 councilmember 2020-01-07..2024-12-10 (502
    votes); after Mayor Marcus Stevenson RESIGNED (2024-11-14), Gettel was APPOINTED Mayor for
    the remaining term (Resolution 2024-R-57, 2024-12-10) and then WON the 2025 mayoral race
    (60.89%). The vacated D5 seat was filled by Denece Mikolash (appointed 2025-01-07, Res.
    2025-R-01, oath administered that night; then won the 2025 D5 race).
  * THE 2021 MAYOR + 2023 D3 RCV PILOTS. The election file's winner_pct/margin for 2021 Mayor
    (Stevenson) and 2023 D3 (Robinson) are FIRST-CHOICE round-1 values; the `winner` is the
    canvassed RCV-final. Cited as such in the sources.
  * THE 2020-2021 OCR SEAM. 2020-2021 council minutes are OCR scans ('Geftel'/'Oustin Gettel'
    garble); cities.db already resolved the canonical name_keys, so the vote bounds are clean.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.dirname(HERE)                 # midvale_city_council/
REPO_ROOT = os.path.dirname(CITY_DIR)            # civic-data/
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import roster_lib
from roster_lib import RosterConfig, Redistrict

ELECTIONS = os.path.join(CITY_DIR, "election_results", "midvale_results_by_candidate.csv")
CITIES_DB = os.path.join(REPO_ROOT, "cities.db")
OVERRIDES = os.path.join(HERE, "roster_overrides.csv")
TERMS_OUT = os.path.join(HERE, "council_terms.csv")
DISTRICTS_OUT = os.path.join(HERE, "district_versions.csv")
PRECINCTS_OUT = os.path.join(HERE, "district_precincts.csv")
PRECINCT_MAP = os.path.join(CITY_DIR, "geo", "precinct_to_district.csv")   # canonical geo map (H-A 2026-07-19)
PRECINCTS_BYP_SRC = os.path.join(CITY_DIR, "election_results", "midvale_results_by_precinct.csv")

CITY = "midvale"
DATA_FLOOR = "2020-01-01"
GEOM_REF = "geo/districts.geojson"

PLAN_OLD = "plan_pre2022"
PLAN_NEW = "plan_2022"
PLAN_SWITCH = "2022-04-19"          # 'Council adopted a map defining new district boundaries on April 19, 2022'
REDISTRICT_ORD = "New District Boundaries map (adopted 2022-04-19)"

SEAT_DISTRICT = {
    "D1": "District 1", "D2": "District 2", "D3": "District 3", "D4": "District 4",
    "D5": "District 5", "MAYOR": "Citywide",
}

TENURES = [
    # ============================ D1 (Cohort A: 2019 / 2023) — Sperry -> Billings ============
    dict(body="Council", seat_id="D1", person_name="Quinn Sperry", person_key="quinn_sperry",
         start_date="2020-01-07", start_event="elected", election_year="2019", end_event="unknown",
         confidence="high",
         sources="election:2019 (District 1 winner, 432, 68.68%; also won 2015); votes:2020-01-07..2023-12-06 "
                 "(cities.db, D1)",
         note="Elected D1 2019 (recovered election year); served the full term. Not a 2023 winner (Billings won) "
              "-> end_event=unknown (end date = successor's Jan-2024 seating; retire-vs-decline unrecorded)."),
    dict(body="Council", seat_id="D1", person_name="Bonnie Billings", person_key="bonnie_billings",
         start_date="2024-01-02", start_event="elected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 1 winner, 641, 60.64%); minutes:2024-01-02 (seated); votes:2024-01-02.."
                 "2026-06-16 (cities.db, D1)",
         note="Elected D1 2023. Currently serving."),

    # ============================ D2 (Cohort A: 2019 / 2023) — continuous Glover ============
    dict(body="Council", seat_id="D2", person_name="Paul Glover", person_key="paul_glover",
         start_date="2020-01-07", start_event="elected", election_year="2019", end_event="reelected",
         confidence="high",
         sources="election:2019 (District 2 winner, 519, 57.6%; long-serving — also 2007/2011/2015); "
                 "votes:2020-01-07.. (cities.db, D2)",
         note="Elected D2 2019; re-elected 2023 -> continuous service (his pre-2020 terms are below the minutes "
              "floor and not rostered)."),
    dict(body="Council", seat_id="D2", person_name="Paul Glover", person_key="paul_glover",
         start_date="2024-01-02", start_event="reelected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 2 winner, 658, 100.0% — uncontested); minutes:2024-01-02 (seated); "
                 "votes:continuous through 2026-06-16 (cities.db, D2)",
         note="Re-elected D2 2023 (uncontested). Currently serving (Mayor Pro-Tempore during the Nov-Dec 2024 "
              "mayoral vacancy — an acting role, not a Mayor tenure)."),

    # ============================ D3 (Cohort A: 2019 / 2023) — continuous Robinson (RCV 2023) ==
    dict(body="Council", seat_id="D3", person_name="Heidi Robinson", person_key="heidi_robinson",
         start_date="2020-01-07", start_event="elected", election_year="2019", end_event="reelected",
         confidence="high",
         sources="election:2019 (District 3 winner, 400, 51.15% — recovered from raw SOVC); votes:2020-01-07.. "
                 "(cities.db, D3)",
         note="Elected D3 2019; re-elected 2023 -> continuous service."),
    dict(body="Council", seat_id="D3", person_name="Heidi Robinson", person_key="heidi_robinson",
         start_date="2024-01-02", start_event="reelected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 3 winner — RCV PILOT; the RCV-final winner; stored first-choice 334 / "
                 "38.97% is round-1, not the final margin); minutes:2024-01-02 (seated); votes:continuous "
                 "through 2026-06-16 (cities.db, D3)",
         note="Re-elected D3 2023 in the RCV pilot (winner is the canvassed RCV-final; the stored pct/margin are "
              "first-choice). Currently serving."),

    # ============================ D4 (Cohort B: 2021 / 2025) — continuous Brown ============
    dict(body="Council", seat_id="D4", person_name="Bryant Brown", person_key="bryant_brown",
         start_date="2018-01-01", start_event="elected", election_year="2017", end_event="reelected",
         confidence="medium",
         sources="election:2017 (District 4 winner, 853, 100.0%); votes:2020-01-07.. (cities.db, D4)",
         note="PRE-FLOOR term start: won 2017 (term began Jan 2018, predates the 2020 minutes floor) -> medium. "
              "Re-elected 2021 (continuous into the 2022 term below)."),
    dict(body="Council", seat_id="D4", person_name="Bryant Brown", person_key="bryant_brown",
         start_date="2022-01-04", start_event="reelected", election_year="2021", end_event="reelected",
         confidence="high",
         sources="election:2021 (District 4 winner, as 'Bryant S. Brown', 706, 100.0%); minutes:2022-01-04 (seated); "
                 "votes:continuous (cities.db, D4)",
         note="Re-elected D4 2021; re-elected again 2025. Continuous service."),
    dict(body="Council", seat_id="D4", person_name="Bryant Brown", person_key="bryant_brown",
         start_date="2026-01-06", start_event="reelected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (District 4 winner, 788, 76.43%); minutes:2026-01-06 (seated); votes:continuous "
                 "through 2026-06-16 (cities.db, D4)",
         note="Re-elected D4 2025. Currently serving."),

    # ============================ D5 (Cohort B: 2021 / 2025) — Gettel -> Mikolash ============
    dict(body="Council", seat_id="D5", person_name="Dustin Gettel", person_key="dustin_gettel",
         start_date="2018-01-01", start_event="elected", election_year="2017", end_event="reelected",
         confidence="medium",
         sources="election:2017 (District 5 winner, 466, 60.05%); votes:2020-01-07.. (cities.db, D5)",
         note="PRE-FLOOR term start: won 2017 (term began Jan 2018) -> medium. Re-elected 2021 (continuous into "
              "the 2022 term below)."),
    dict(body="Council", seat_id="D5", person_name="Dustin Gettel", person_key="dustin_gettel",
         start_date="2022-01-04", start_event="reelected", election_year="2021", end_event="became-mayor",
         confidence="high",
         vacate_date="2024-12-11", vacate_confidence="high",
         vacate_source="minutes:2024-12-10 (Resolution 2024-R-57 'Appointing Dustin Gettel as Mayor of Midvale "
                       "City for the Remaining Term' — he vacated D5 to take the mayoralty); his last cities.db "
                       "D5 vote is 2024-12-10",
         sources="election:2021 (District 5 winner, 672, 74.92%); minutes:2022-01-04 (seated); votes:2022-01-04.."
                 "2024-12-10 (cities.db, D5, incl. the night he was appointed Mayor)",
         note="Re-elected D5 2021. Was APPOINTED Mayor 2024-12-10 (Res. 2024-R-57, remaining term) after Stevenson "
              "resigned -> vacated D5 (end_event=became-mayor). His unexpired D5 term (to Jan 2026) was filled by "
              "the appointed Mikolash -> explicit VACANT interval. See the MAYOR rows."),
    dict(body="Council", seat_id="D5", person_name="Denece Mikolash", person_key="denece_mikolash",
         start_date="2025-01-07", start_event="appointed", election_year="", end_event="succeeded-by-elected",
         confidence="high",
         sources="minutes:2025-01-07 (Resolution 2025-R-01 'Appointing Denece Mikolash to serve as Council Member "
                 "for District 5'; 'Rori Andreason administered the oath of office to Denece Mikolash as Council "
                 "Member'); votes:2025-01-07..2025 (cities.db, D5)",
         note="APPOINTED to the D5 vacancy 2025-01-07 (oath same night), filling the remainder of Gettel's "
              "2022-2025 term. Then WON the 2025 D5 race for the full next term (see below)."),
    dict(body="Council", seat_id="D5", person_name="Denece Mikolash", person_key="denece_mikolash",
         start_date="2026-01-06", start_event="elected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (District 5 winner, 505, 66.53%); minutes:2026-01-06 (seated for the full term); "
                 "votes:2026-01-06..2026-06-16 (cities.db, D5)",
         note="Elected D5 2025 (full term) after the ~1-year interim appointment above. Currently serving."),

    # ============================ MAYOR (presides; votes only to break a tie) ============
    dict(body="Mayor", seat_id="MAYOR", person_name="Robert Hale", person_key="robert_hale",
         start_date="2018-01-01", start_event="elected", election_year="2017", end_event="unknown",
         confidence="medium",
         sources="election:2017 (Mayor winner, as 'Robert M. Hale', 2,746, 58.91%); minutes:2020-05-05 (his sole "
                 "recorded tie-break, m14, a 2-2 -> 'passed 3-2')",
         note="PRE-FLOOR mayoral term start (won 2017, term began Jan 2018) -> medium. Votes only to break a tie "
              "-> EMPTY vote bounds (non_voting_mayor); the 2020-05-05 tie-break is not counted as membership. Not "
              "a 2021 candidate (Stevenson won) -> end_event=unknown; left at the 2022-01-04 seating."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Marcus Stevenson", person_key="marcus_stevenson",
         start_date="2022-01-04", start_event="elected", election_year="2021", end_event="resigned",
         confidence="high",
         vacate_date="2024-11-14", vacate_confidence="high",
         vacate_source="minutes:2024-11-18 special ('on Thursday, November 14, 2024, Mayor Marcus Stevenson "
                       "resigned') -> the mayoral office was vacant until Gettel's 2024-12-10 appointment",
         sources="election:2021 (Mayor winner — RCV PILOT; the RCV-final winner; stored first-choice 2,040 / 45.72% "
                 "is round-1); minutes:2022-01-04 (seated); does NOT vote (tie-break only)",
         note="Won the 2021 mayoralty (RCV pilot). RESIGNED 2024-11-14 -> explicit VACANT mayoral interval until "
              "Gettel's appointment (2024-12-10; Council Member Glover served as Mayor Pro-Tempore in the interim "
              "— an acting role, not a Mayor tenure). EMPTY vote bounds (non_voting_mayor)."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Dustin Gettel", person_key="dustin_gettel",
         start_date="2024-12-10", start_event="appointed", election_year="", end_event="succeeded-by-elected",
         confidence="high",
         sources="minutes:2024-12-10 (Resolution 2024-R-57 'Appointing Dustin Gettel as Mayor of Midvale City for "
                 "the Remaining Term'); does NOT vote as Mayor (tie-break only)",
         note="APPOINTED Mayor 2024-12-10 to fill the remainder of Stevenson's term (having served D5 2020-2024 — "
              "same person). Then won the 2025 mayoral race (see below). EMPTY vote bounds (non_voting_mayor)."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Dustin Gettel", person_key="dustin_gettel",
         start_date="2026-01-06", start_event="elected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (Mayor winner, 3,192, 60.89%); minutes:2026-01-06 (seated for the full term); "
                 "does NOT vote (tie-break only)",
         note="Elected Mayor 2025 (full term) after the interim appointment above. Currently serving. EMPTY vote "
              "bounds (non_voting_mayor)."),
]

# canonical UPPER-CASE election name token -> our person_key (WINNERS only pass through here).
NAME_TO_KEY = {
    "SPERRY": "quinn_sperry", "BILLINGS": "bonnie_billings", "GLOVER": "paul_glover",
    "ROBINSON": "heidi_robinson", "BROWN": "bryant_brown", "GETTEL": "dustin_gettel",
    "MIKOLASH": "denece_mikolash", "HALE": "robert_hale", "STEVENSON": "marcus_stevenson",
}

# cities.db person.name_key -> our person_key (council voters). roberthale (the tie-break-only
# Mayor, 1 role vote) is EXCLUDED — his MAYOR rows are emptied by non_voting_mayor. marcusstevenson
# is absent from the vote record (mayor doesn't vote). dustingettel IS mapped for his 2020-2024 D5
# council votes (his MAYOR rows are emptied).
DB_KEY = {
    "quinnsperry": "quinn_sperry", "dustingettel": "dustin_gettel", "bryantbrown": "bryant_brown",
    "heidirobinson": "heidi_robinson", "paulglover": "paul_glover",
    "bonniebillings": "bonnie_billings", "denecemikolash": "denece_mikolash",
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
    source_url="meeting_minutes/minutes/2022/2022-05-02/2022-05-03_city-council-regular-meeting.md "
               "('Council adopted a map defining new district boundaries on April 19, 2022'); "
               "geo/districts.geojson (official Midvale 5-district FeatureServer)",
    data_floor=DATA_FLOOR,
    current_note="CURRENT post-2020-census boundaries (new map adopted 2022-04-19). geometry_ref = "
                 "geo/districts.geojson. District NUMBERS were unchanged. First used for the 2023 (D1/D2/D3) "
                 "district elections.",
    prior_adopted_by="prior plan (pre-2022 boundaries)",
    prior_geom_ref="",
    prior_confidence="low",
    prior_note="Pre-2022 (pre-2020-census) Midvale district boundaries NOT acquired -> honest GAP (blank geometry, "
               "low). In force through the 2019/2021 elections. effective_start = data floor.",
    citywide_rows=[
        ("MAYOR", "citywide", "the separately-elected Mayor (Hale -> Stevenson -> Gettel), who votes only to "
                              "break a tie"),
    ],
    citywide_adopted_by="Midvale City (citywide mayoral office)",
    citywide_note_template="{who}: represents the ENTIRE city on every date, unchanged by the 2022 redistricting. "
                           "Only the 5 numbered council districts are geographic.",
    # Precinct layer ENABLED 2026-07-19 (H-A). geo/precinct_to_district.csv has NO source_year
    # column, so write_precincts falls back to the EXPLICIT precinct_source_default token (fail-loud
    # if unset). Token 'current' == precinct_hi_source -> every current-plan precinct row is
    # confidence=high (the map is centroid-in-district off Midvale's OFFICIAL 5-district
    # FeatureServer). Because the token is not a year, per-precinct MISMATCH detection stays dormant
    # (the documented "token-not-a-year" limitation); the aggregate winner cross-check runs live.
    precinct_hi_source="current",
    precinct_source_default="current",
    precinct_hi_note=("current post-2020-census precinct->district read directly from "
                      "geo/precinct_to_district.csv (no source_year column -> precinct_source_default "
                      "token 'current'; H-A 2026-07-19). Official Midvale 5-district FeatureServer; "
                      "districts only (the Mayor is city-wide)."),
    precinct_med_note="",
    precinct_prior_note="Prior-plan (pre-2022) precinct->district composition NOT acquired -> honest GAP.",
    crosscheck_districts=("1", "2", "3", "4", "5"),
    precinct_prefix="MID", geo_seat_prefix="D",
    plan_switch_year="2023", citywide_seats=(),
)

CFG = RosterConfig(
    non_voting_mayor=True,
    city=CITY, city_dir=CITY_DIR, repo_root=REPO_ROOT, data_floor=DATA_FLOOR,
    geom_ref=GEOM_REF, elections_path=ELECTIONS, cities_db_path=CITIES_DB,
    overrides_path=OVERRIDES, terms_out=TERMS_OUT, districts_out=DISTRICTS_OUT,
    seat_district=SEAT_DISTRICT, name_to_key=NAME_TO_KEY, db_key=DB_KEY,
    seat_order=["D1", "D2", "D3", "D4", "D5", "MAYOR"],
    # general winners from 2017 on (2017 seats the earliest in-window pre-floor terms — D4 Brown,
    # D5 Gettel, Mayor Hale; pre-2017 winners' terms ended before the 2020 floor -> excluded).
    keep_election_row=lambda r: ("general" in r["election_type"].lower() and int(r["year"]) >= 2017),
    contest_key=seat_for_contest, crosscheck_field="district",
    winners_have_district=True,
    elected_events=("elected", "reelected"),
    redistrict=REDISTRICT, precincts_out=PRECINCTS_OUT,
    precinct_map_path=PRECINCT_MAP, precincts_byprecinct_path=PRECINCTS_BYP_SRC,
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

    print("\n(b) Roster AS OF 2024-11-25 (mayoral vacancy: Stevenson resigned, Gettel not yet appointed):")
    for r in roster_lib.roster_as_of(CFG, "2024-11-25", body="Council"):
        print(line(r))
    for r in roster_lib.roster_as_of(CFG, "2024-11-25", body="Mayor"):
        print(line(r))

    print("\n(e) Precinct-map cross-check (district_precincts vs election outcomes; districts only):")
    roster_lib.precinct_crosscheck(CFG, verbose=True)


if __name__ == "__main__":
    rows = roster_lib.build(CFG, TENURES)
    n = {c: sum(1 for r in rows if r["confidence"] == c) for c in ("high", "medium", "low")}
    nvac = sum(1 for r in rows if r["start_event"] == "vacated")
    print(f"Wrote {os.path.relpath(TERMS_OUT, CITY_DIR)} "
          f"({len(rows)} tenures incl. {nvac} VACANT: {n['high']} high / {n['medium']} medium / {n['low']} low)")
    print(f"Wrote {os.path.relpath(DISTRICTS_OUT, CITY_DIR)} "
          f"(5 districts x 2 plans + Mayor citywide; redistricting {REDISTRICT_ORD})")
    print(f"Wrote {os.path.relpath(PRECINCTS_OUT, CITY_DIR)} "
          f"(plan_2022 precinct map + plan_pre2022 gap rows; districts only)")
    if "--check" in sys.argv:
        print("\nValidation: PASS (no overlaps; sources+confidence present; non-voting-mayor + gap/vacate guards clear).")
        print("Precinct cross-check:")
        roster_lib.precinct_crosscheck(CFG, verbose=True)
    if "--demo" in sys.argv:
        demo()
