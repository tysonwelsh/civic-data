#!/usr/bin/env python3
"""build_roster.py — rolling council-roster for MILLCREEK (a slowly-changing-
dimension / interval table of who holds each council + mayor seat over time).

THIN DRIVER: this file holds only Millcreek-specific DATA (the curated TENURES
seat assignments, the name maps, the 4-district + 2022-redistricting facts and
prose) + config; all generic mechanics live in ../scripts/roster_lib.py
(canon_key, election/vote-bounds/override reconciliation, end-date chaining +
VACANT insertion, validation, the CSV writers, and the as-of / address /
precinct-crosscheck / demo query helpers). See that module's docstring to add a city.

Millcreek is a DISTRICT city built on the Provo template, with ONE structural
difference that drives every config choice: **THE MAYOR VOTES.** Millcreek is a
five-member council-mayor form — 4 district members (D1-D4) + a citywide Mayor who
is a full voting member (a complete roll call tops out at 5, e.g.
  "Council Member DeSirant voted yes, Council Member Jackson voted yes, Council
   Member Uipi voted yes, and Mayor Silvestrini voted yes. The motion passed
   unanimously."  (minutes 2023-12-11)
So `non_voting_mayor=False`: the MAYOR row carries REAL vote bounds and the mayor
sits in `db_key`; seat_ids are D1,D2,D3,D4,MAYOR (no at-large council seats).

DERIVED LAYER — regenerable, never hand-edited. Canonical inputs:
  1. election_results/millcreek_results_by_candidate.csv  (winners -> `elected`/`reelected` terms)
  2. cities.db  role table (city='millcreek', body='Council')  (observed vote bounds; mayor INCLUDED)
  3. meeting_minutes/minutes/**                            (oath/incorporation/appointment dates, redistricting ord.)
  4. roster/roster_overrides.csv                           (hand corrections; applied LAST)

Outputs (idempotent — re-running reproduces them byte-for-byte):
  roster/council_terms.csv       one row per seat-tenure (5 stable seats)
  roster/district_versions.csv   boundary interval table — REAL 4 districts + the 2022
                                 redistricting (Ordinance 22-23) versioned into two plans + Mayor
  roster/district_precincts.csv  versioned precinct->district composition (plan-scoped)

Usage:
  python3 roster/build_roster.py            # regenerate the CSVs
  python3 roster/build_roster.py --demo     # regenerate + print the demo queries
  python3 roster/build_roster.py --check    # regenerate + run validations + precinct cross-check

Cardinal rule (repo CLAUDE.md): NEVER fabricate. Unknown seat-holder / boundary /
precinct assignment -> explicit gap + confidence=low + a note, never a guess.

Provenance / confidence model:
  high   = anchored to an election result OR a minutes-documented oath/incorporation/
           appointment/departure/ordinance. **Millcreek's ENTIRE history is in-window**
           (incorporated Dec 28 2016; data floor 2016), so EVERY council_terms row is
           `high` — there is NO pre-floor inference (unlike the older cities' 2017-cycle
           terms). 0 medium / 0 low here; the prior-plan (plan_2016) district/precinct rows
           were RECONSTRUCTED to `medium` 2026-07-11 (approximate — see the Redistrict
           prior_note / scripts/roster_boundary_recon.md), so no `low` rows remain.

Seat model (STABLE ids — a redistricting redraws boundaries, it does NOT renumber seats):
  D1..D4  four geographic district seats
  MAYOR   the citywide Mayor — a FULL VOTING council member (not a separate non-voter)
Staggered 4-year cycles (every seat was on the founding 2016 ballot; D2/D4 drew short
initial terms and were re-filled in 2017, landing them on the B cycle):
  Cycle A (2016 / 2019 / 2023 / 2027):  MAYOR, D1, D3     (terms Jan-2020…, Jan-2024…)
  Cycle B (2016 / 2017 / 2021 / 2025):  D2, D4            (terms Jan-2018…, Jan-2022…, Jan-2026…)

Term-start = the first REGULAR council meeting of January (oath administered there;
verified 2018-01-08 · 2020-01-13 · 2022-01-10 (DeSirant/Uipi "Oaths of Office") ·
2024-01-09 · 2026-01-12). The FOUNDING council took office at INCORPORATION —
legally recorded 2016-12-28 (council-elect met 2016-12-05..27; first regular meeting
2017-01-09). first_vote in cities.db is ~2019-05-13 for the founders and 2022-07-26 for
DeSirant: that is the NAMED-ROLL-CALL SEAM (2017-2021 minutes are tally-only by source),
a recording limit — NOT the actual term start.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.dirname(HERE)                 # millcreek_city_council/
REPO_ROOT = os.path.dirname(CITY_DIR)            # civic-data/
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import roster_lib
from roster_lib import RosterConfig, Redistrict

ELECTIONS = os.path.join(CITY_DIR, "election_results", "millcreek_results_by_candidate.csv")
PRECINCTS_BYP = os.path.join(CITY_DIR, "election_results", "millcreek_results_by_precinct.csv")
# roster-local precinct map (derived from geo/precinct_to_district.csv, + a source_year
# column the shared builder needs: 'election-xcheck' where a post-2022 contested precinct
# election cross-validates the composition — D2/D3/D4 — vs 'gis-2022map' for D1, whose only
# post-2022 race (2023) was uncontested/cancelled so has no precinct-level election data).
PRECINCT_MAP = os.path.join(HERE, "precinct_to_district.csv")
CITIES_DB = os.path.join(REPO_ROOT, "cities.db")
OVERRIDES = os.path.join(HERE, "roster_overrides.csv")
TERMS_OUT = os.path.join(HERE, "council_terms.csv")
DISTRICTS_OUT = os.path.join(HERE, "district_versions.csv")
PRECINCTS_OUT = os.path.join(HERE, "district_precincts.csv")

CITY = "millcreek"
DATA_FLOOR = "2016-12-28"           # incorporation (the city's ENTIRE record starts here)
GEOM_REF = "geo/council_districts.geojson"   # the 4 district polygons, 2022-2032 vintage

# The real redistricting event (spot-checked against source minutes + the ordinances layer):
#   Ordinance 22-23, "AN ORDINANCE ADJUSTING CITY COUNCIL DISTRICT BOUNDARIES TO MAINTAIN
#   DISTRICTS OF SUBSTANTIALLY EQUAL POPULATION" (map 5 as Exhibit A), adopted 2022-05-09
#   (Pass, unanimous; mover Jackson / second Uipi). Public hearing 2022-04-11; the council
#   "needed to adopt a redistricting map by May 16, 2022" (2022-02-14). Decennial adjustment
#   after the 2020 census. Pre-2022 elections (2016/2017/2019/2021) used the ORIGINAL 2016
#   incorporation lines; 2023 (D1/D3/Mayor) and 2025 (D2/D4) onward use the 22-23 lines.
REDISTRICT_ORD = "Ordinance 22-23"
REDISTRICT_ADOPTED = "2022-05-09"
PLAN_OLD = "plan_2016"     # original incorporation lines (in force through the 2021 election)
PLAN_NEW = "plan_2022"     # Ordinance 22-23 (2022-2032); in force from adoption / for 2023+ elections
PLAN_SWITCH = "2022-05-09"  # effective boundary between the two plans (ordinance adoption)
SRC_URL = ("https://services9.arcgis.com/XRrSFvEwSsReIxuA/arcgis/rest/services/"
           "Millcreek_City_Council_Dist_2022/FeatureServer/2")

SEAT_DISTRICT = {
    "D1": "District 1", "D2": "District 2", "D3": "District 3", "D4": "District 4",
    "MAYOR": "Citywide",
}

# ---------------------------------------------------------------------------
# LAYER 1-3 (reconciled). Each tenure anchored to a cited source. end_date is
# computed by chaining unless an explicit departure (vacate_date) is needed.
# ---------------------------------------------------------------------------
FOUND_SRC = ("election:2016 (founding Nov-8-2016 general winner); minutes:2016-12-05..27 "
             "(seated as Council-Elect); city incorporated / took office 2016-12-28")

TENURES = [
    # ===== D1  (Silvia Catten — Cycle A; continuous 2016 -> present) =====
    dict(body="Council", seat_id="D1", person_name="Silvia Catten", person_key="silvia_catten",
         start_date="2016-12-28", start_event="elected", election_year="2016",
         end_event="reelected", confidence="high",
         sources=FOUND_SRC + " (District 1, def. Diane Angus 55.7-44.3)",
         note="Founding D1 councilmember. first_vote in cities.db is 2019-05-13 — the named-roll-call seam (2017-2021 minutes are tally-only by source), a recording limit, not the term start."),
    dict(body="Council", seat_id="D1", person_name="Silvia Catten", person_key="silvia_catten",
         start_date="2020-01-13", start_event="reelected", election_year="2019",
         end_event="reelected", confidence="high",
         sources="election:2019 (District 1 winner, UNOPPOSED 100%); minutes:2020-01-13 (first regular meeting of the term)",
         note="Re-elected D1 2019 unopposed (continuous service)."),
    dict(body="Council", seat_id="D1", person_name="Silvia Catten", person_key="silvia_catten",
         start_date="2024-01-09", start_event="reelected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (District 1 — cancelled-uncontested under UCA 20A-1-206, re-elected by default; no ballot printed); minutes:2024-01-09 (first regular meeting of the term)",
         note="2023 D1 race was CANCELLED (only the incumbent filed) -> re-elected by default; blank vote fields in election_results by design, NOT a data gap. Currently serving."),

    # ===== D2  (Marchant[2016 short -> 2017] -> DeSirant[2021 RCV -> 2025]) =====
    dict(body="Council", seat_id="D2", person_name="Dwight Marchant", person_key="dwight_marchant",
         start_date="2016-12-28", start_event="elected", election_year="2016",
         end_event="reelected", confidence="high",
         sources=FOUND_SRC + " (District 2, def. Dwayne Vance 54.3-45.7; SHORT initial term)",
         note="Founding D2 councilmember. D2/D4 drew SHORT initial terms at incorporation and were re-filled in the 2017 cycle (-> the B stagger)."),
    dict(body="Council", seat_id="D2", person_name="Dwight Marchant", person_key="dwight_marchant",
         start_date="2018-01-08", start_event="reelected", election_year="2017",
         end_event="did-not-run", confidence="high",
         sources="election:2017 (District 2 winner, def. Dwayne Vance 66.5-33.5); minutes:2018-01-08 (first regular meeting of the term); votes:2019-05-13..2021-12-13 (cities.db role, tally-only-era named votes)",
         note="Re-elected D2 2017. NOT a candidate in the 2021 D2 race (won by DeSirant) -> term expired Jan 2022 -> did-not-run. Served entirely in the tally-only era (only 14 named votes)."),
    dict(body="Council", seat_id="D2", person_name="Thom DeSirant", person_key="thom_desirant",
         start_date="2022-01-10", start_event="elected", election_year="2021",
         end_event="reelected", confidence="high",
         sources="election:2021 (District 2 RCV winner — final round 51.75%, def. first-choice leader Jeremiah Clark 1014-988 first-choice); minutes:2022-01-10 ('1.2 Council Member Oaths of Office: Thom DeSirant, Council District 2')",
         note="2021 D2 was RANKED-CHOICE: Clark led first choice but DeSirant won the runoff (is_winner reflects the final round). first_vote in cities.db is 2022-07-26 — the named-roll-call seam (seated Jan 2022; named rolls begin mid-2022), a recording limit not the term start."),
    dict(body="Council", seat_id="D2", person_name="Thom DeSirant", person_key="thom_desirant",
         start_date="2026-01-12", start_event="reelected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (District 2 winner, def. Angie Gray 59.3-40.7); minutes:2026-01-12 (first regular meeting of the term)",
         note="Re-elected D2 2025 (continuous service). First D2 term contested on the plan_2022 lines."),

    # ===== D3  (Cheri Jackson[2016->2019->2023] -> became MAYOR Nov 2025; Nicole Handy appointed) =====
    dict(body="Council", seat_id="D3", person_name="Cheri Jackson", person_key="cheri_jackson",
         start_date="2016-12-28", start_event="elected", election_year="2016",
         end_event="reelected", confidence="high",
         sources=FOUND_SRC + " (District 3, as 'Cheri M. Jackson', def. Jem Keller 58-42)",
         note="Founding D3 councilmember. Election name 'CHERI M. JACKSON' (2016) == 'CHERI JACKSON' (2019+) — same person."),
    dict(body="Council", seat_id="D3", person_name="Cheri Jackson", person_key="cheri_jackson",
         start_date="2020-01-13", start_event="reelected", election_year="2019",
         end_event="reelected", confidence="high",
         sources="election:2019 (District 3 winner, def. Jemina Keller 78.9-21.1); minutes:2020-01-13 (first regular meeting of the term)",
         note="Re-elected D3 2019."),
    dict(body="Council", seat_id="D3", person_name="Cheri Jackson", person_key="cheri_jackson",
         start_date="2024-01-09", start_event="reelected", election_year="2023",
         end_event="became-mayor", confidence="high",
         vacate_date="2025-11-10", vacate_confidence="high",
         vacate_source="minutes:2025-11-10 (Deputy Recorder Alex Wendt 'administered the Oath of Office to Mayor-Elect Cheri Jackson') — she left D3 to become Mayor",
         sources="election:2023 (District 3 winner, def. Scott Springer 76.2-13.8); minutes:2024-01-09 (seated); minutes:2025-11-03 (Resolution 25-38 appointing her Mayor); minutes:2025-11-10 (sworn in as Mayor -> vacated D3)",
         note="Elected D3 2023; the council APPOINTED her to fill the mid-term MAYORAL vacancy (Resolution 25-38, 2025-11-03) after founding Mayor Silvestrini resigned; sworn in as Mayor 2025-11-10, vacating D3 that day. See the MAYOR row below."),
    dict(body="Council", seat_id="D3", person_name="Nicole Handy", person_key="nicole_handy",
         start_date="2025-11-24", start_event="appointed", election_year="",
         end_event="serving", confidence="high",
         sources="minutes:2025-11-24 (Resolution 25-42 'Filling the Mid-Term Vacancy of Council District 3 with Nicole Handy'; paper ballots 'unanimously reflected Nicole Handy'; City Recorder 'administered the oath of office to Nicole Handy'); votes:2025-11-24.. (cities.db role first_seen)",
         note="APPOINTED to the D3 vacancy created when Jackson became Mayor (NOT elected — no D3 race in 2025). Next scheduled D3 election is 2027 (Cycle A)."),

    # ===== D4  (Bev Uipi — Cycle B; continuous 2016 -> present) =====
    dict(body="Council", seat_id="D4", person_name="Bev Uipi", person_key="bev_uipi",
         start_date="2016-12-28", start_event="elected", election_year="2016",
         end_event="reelected", confidence="high",
         sources=FOUND_SRC + " (District 4, def. Seraya Amirthalingam 60.3-39.7; SHORT initial term)",
         note="Founding D4 councilmember (SHORT initial term -> re-filled 2017 -> B stagger). Longest-serving member in the window."),
    dict(body="Council", seat_id="D4", person_name="Bev Uipi", person_key="bev_uipi",
         start_date="2018-01-08", start_event="reelected", election_year="2017",
         end_event="reelected", confidence="high",
         sources="election:2017 (District 4 winner, UNOPPOSED 100%); minutes:2018-01-08 (first regular meeting of the term)",
         note="Re-elected D4 2017 unopposed."),
    dict(body="Council", seat_id="D4", person_name="Bev Uipi", person_key="bev_uipi",
         start_date="2022-01-10", start_event="reelected", election_year="2021",
         end_event="reelected", confidence="high",
         sources="election:2021 (District 4 RCV winner — final round 56.9%, def. Bruce Parker; also led first choice 43.6%); minutes:2022-01-10 ('1.2 Council Member Oaths of Office: … Bev Uipi, Council District 4')",
         note="Re-elected D4 2021 (RCV; also the first-choice leader, so no divergence)."),
    dict(body="Council", seat_id="D4", person_name="Bev Uipi", person_key="bev_uipi",
         start_date="2026-01-12", start_event="reelected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (District 4 winner, def. Connor Jett Gale 82.0-18.0); minutes:2026-01-12 (first regular meeting of the term)",
         note="Re-elected D4 2025 (continuous service)."),

    # ===== MAYOR (Jeff Silvestrini[2016->2019->2023] -> resigned; Cheri Jackson appointed) =====
    # non_voting_mayor=False -> these rows carry REAL cities.db vote bounds (the mayor votes).
    dict(body="Mayor", seat_id="MAYOR", person_name="Jeff Silvestrini", person_key="jeff_silvestrini",
         start_date="2016-12-28", start_event="elected", election_year="2016",
         end_event="reelected", confidence="high",
         sources=FOUND_SRC + " (Mayor, UNOPPOSED 100% / 21,288 — primary runner-up Healey withdrew Aug-2016)",
         note="Founding Mayor. The Mayor is a FULL VOTING member of the council (max roll call = 5); Silvestrini appears in the vote record (615 votes in cities.db, first_vote 2019-05-13 = the named seam)."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Jeff Silvestrini", person_key="jeff_silvestrini",
         start_date="2020-01-13", start_event="reelected", election_year="2019",
         end_event="reelected", confidence="high",
         sources="election:2019 (Mayor winner, def. Angel Vice 75.0-25.0); minutes:2020-01-13 (first regular meeting of the term)",
         note="Re-elected Mayor 2019."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Jeff Silvestrini", person_key="jeff_silvestrini",
         start_date="2024-01-09", start_event="reelected", election_year="2023",
         end_event="resigned", confidence="high",
         sources="election:2023 (Mayor — cancelled-uncontested under UCA 20A-1-206, re-elected by default); minutes:2024-01-09 (seated); minutes:2025-10-13 ('reported on his midterm vacancy and the process'); minutes:2025-11-10 (last served; Jackson sworn in as successor Mayor)",
         note="2023 Mayor race CANCELLED (uncontested). RESIGNED mid-term autumn 2025 (health). His term ends 2025-11-10, when successor Jackson is sworn in the SAME meeting -> clean handoff, no VACANT interval. last_vote in cities.db 2025-11-10."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Cheri Jackson", person_key="cheri_jackson",
         start_date="2025-11-10", start_event="appointed", election_year="",
         end_event="serving", confidence="high",
         sources="minutes:2025-11-03 (Resolution 25-38, Filling the Mid-Term Vacancy of the Mayor — council paper-ballot appointment); minutes:2025-11-10 (Oath of Office administered to 'Mayor-Elect Cheri Jackson')",
         note="APPOINTED by the council (Resolution 25-38) to finish Silvestrini's term — Millcreek's 2nd (and first female) Mayor. NOT an election (no 2025 mayoral race; Mayor is a 2027-cycle seat). As Mayor she is still a VOTING member. Multi-tenure NOTE: first_vote/last_vote are now clamped to each tenure's own [start_date, end_date) window, so this MAYOR row reads 2025-11-10..2026-05-26 (her mayoral service only) while her three D3 rows carry their own per-term bounds — no longer one 2019-05-13..2026-05-26 span across both roles."),
]

# canonical UPPER-CASE election surname -> our person_key (surname sufficient — no shared
# surnames among winners; DeSirant may appear as 'THOM DESIRANT').
NAME_TO_KEY = {
    "CATTEN": "silvia_catten", "MARCHANT": "dwight_marchant", "DESIRANT": "thom_desirant",
    "JACKSON": "cheri_jackson", "UIPI": "bev_uipi", "HANDY": "nicole_handy",
    "SILVESTRINI": "jeff_silvestrini",
}

# cities.db person.name_key -> our person_key. The Mayor (Silvestrini / Jackson) IS in this
# map because the Millcreek mayor VOTES on council motions (unlike Provo/SLC/etc.).
DB_KEY = {
    "silviacatten": "silvia_catten", "dwightmarchant": "dwight_marchant",
    "thomdesirant": "thom_desirant", "cherijackson": "cheri_jackson",
    "bevuipi": "bev_uipi", "nicolehandy": "nicole_handy",
    "jeffsilvestrini": "jeff_silvestrini",
}


def seat_for_contest(office, district):
    """election (office, district) -> seat_id (or None if unmapped)."""
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
    current_note=(f"CURRENT post-2020-census boundaries ('Millcreek City Council Districts "
                  f"2022-2032'). {REDISTRICT_ORD} adopted {REDISTRICT_ADOPTED} "
                  "('AN ORDINANCE ADJUSTING CITY COUNCIL DISTRICT BOUNDARIES TO MAINTAIN "
                  "DISTRICTS OF SUBSTANTIALLY EQUAL POPULATION', map 5; Pass unanimous). "
                  "geometry_ref = the 4 district polygons in geo/council_districts.geojson."),
    prior_adopted_by="original 2016 incorporation district map (Millcreek City GIS 'City Council District Boundaries 2017-2022')",
    prior_geom_ref="geo/council_districts_pre2022.geojson",
    prior_confidence="high",
    prior_source_url="https://services9.arcgis.com/XRrSFvEwSsReIxuA/arcgis/rest/services/CityCouncilDistricts/FeatureServer/0",
    prior_note=("Prior-plan (plan_2016) — the ORIGINAL 2016 incorporation district map. AUTHORITATIVE "
                "geometry SOURCED 2026-07-19 from Millcreek's own city GIS (services9.arcgis.com/"
                "XRrSFvEwSsReIxuA, the SAME org that publishes the current 2022-2032 layer): "
                "CityCouncilDistricts FeatureServer layer 0, explicitly named 'City Council District "
                "Boundaries 2017-2022' (4 polygons, field DIST=District 1..4, DistrictRep carries the "
                "PRE-2022 members incl. Dwight Marchant D2 who left office Jan 2022 — confirming the "
                "vintage). Fetched with outSR=4326 into geo/council_districts_pre2022.geojson -> HIGH. "
                "Genuinely distinct from the current 2022-2032 plan (per-district IoU 0.58-0.92; the 2022 "
                "redistricting most changed D3/D4). In force for the 2016/2017/2019/2021 elections. "
                "effective_start = data floor (incorporation). This REPLACES the 2026-07-11 precinct-"
                "dissolve reconstruction, which was materially wrong (IoU ~0 vs this authoritative layer) "
                "because the MIL### precinct CODES were renumbered/reshaped between 2019 and the current "
                "2025 UGRC precinct vintage. See scripts/roster_boundary_recon.md."),
    citywide_rows=[("MAYOR", "citywide", "the citywide Mayor (a FULL VOTING council member)")],
    citywide_adopted_by="Millcreek incorporation (council-mayor form — whole city)",
    citywide_note_template=("{who}: represents the ENTIRE city on every date, unchanged by the "
                            "2022 redistricting. Millcreek has NO at-large COUNCIL seats — the "
                            "Mayor is the only citywide seat, and (unlike most cities) VOTES. "
                            "geometry_ref = union of the 4 district polygons (city extent)."),
    precinct_hi_source="election-xcheck",
    precinct_hi_note="precinct->district composition cross-validated against a post-2022 contested municipal general (2023 D3 / 2025 D2 / 2025 D4)",
    precinct_med_note=("city GIS layer (2022-2032 centroid-in-district) only — D1's sole post-2022 "
                       "race (2023) was cancelled-uncontested, so no precinct-level election corroboration"),
    precinct_prior_note=("plan_2016 (incorporation-era) precinct->district composition from the 2017+2019 SOVC "
                         "district contests (46 MIL precinct CODES); medium. This is the record of which old "
                         "precinct CODE voted in which district contest — NOT geographically joinable to the "
                         "current UGRC precinct shapes (the MIL### codes were renumbered/reshaped by 2025, so a "
                         "centroid-in-polygon against the authoritative 2017-2022 district layer disagrees on "
                         "36/44 codes). The plan_2016 boundary GEOMETRY is now the AUTHORITATIVE fetched layer "
                         "(geometry_ref, high); this precinct-code composition stays the SOVC-derived medium "
                         "layer. See scripts/roster_boundary_recon.md."),
    crosscheck_districts=("2", "3", "4"), precinct_prefix="", geo_seat_prefix="D",
    plan_switch_year="2022", citywide_seats=(),
)

CFG = RosterConfig(
    non_voting_mayor=False,   # CRITICAL: the Millcreek Mayor VOTES on council motions
    city=CITY, city_dir=CITY_DIR, repo_root=REPO_ROOT, data_floor=DATA_FLOOR,
    geom_ref=GEOM_REF, elections_path=ELECTIONS, cities_db_path=CITIES_DB,
    overrides_path=OVERRIDES, terms_out=TERMS_OUT, districts_out=DISTRICTS_OUT,
    seat_district=SEAT_DISTRICT, name_to_key=NAME_TO_KEY, db_key=DB_KEY,
    seat_order=["D1", "D2", "D3", "D4", "MAYOR"],
    keep_election_row=lambda r: r["election_type"].strip().lower() == "municipal general",
    contest_key=seat_for_contest, crosscheck_field="seat_id",
    winners_have_district=True,
    elected_events=("elected", "reelected", "became-mayor"),
    redistrict=REDISTRICT, precincts_out=PRECINCTS_OUT,
    precinct_map_path=PRECINCT_MAP, precincts_byprecinct_path=PRECINCTS_BYP,
    prior_precinct_map_path=os.path.join(CITY_DIR, "geo", "precinct_to_district_pre2022.csv"),
)


# ---------------------------------------------------------------------------
# Demo queries (Millcreek presentation)
# ---------------------------------------------------------------------------
def demo():
    def line(r):
        end = r["end_date"] or "—(serving)"
        return (f"    {r['seat_id']:<6} {r['person_name']:<18} {r['start_date']} -> {end:<12}"
                f" [{r['start_event']}/{r['end_event']}] conf={r['confidence']}")

    print("\n(a) CURRENT council roster + mayor (end_date empty, end_event=serving):")
    for r in roster_lib.load_terms(CFG):
        if not r["end_date"] and r["end_event"] == "serving":
            print(line(r))

    print("\n(b) Roster AS OF 2025-11-17 (mid-vacancy: Jackson is Mayor, D3 is VACANT):")
    for r in roster_lib.roster_as_of(CFG, "2025-11-17", body="Council"):
        print(line(r))
    for r in roster_lib.roster_as_of(CFG, "2025-11-17", body="Mayor"):
        print(line(r))

    print("\n(c) NON-DEGENERATE address+date -> representative (via geo/address_to_district.py):")
    addr = "3330 S 1300 E, Millcreek, UT 84106"          # Millcreek City Hall (District 2)
    latlon = (40.6981, -111.8541)                        # geocoded coords (agree w/ address -> D2)
    for d in ("2026-02-01", "2021-06-01"):
        res = roster_lib.representatives_for_address(CFG, addr, d, latlon=latlon, precinct="MIL001")
        who = ", ".join(f"{x['person_name']}({x['seat_id']})" for x in res["reps"])
        loc = (f"District {res['district']} [{res.get('method')}]"
               if res.get("district") else f"[{res.get('gap', '?')}]")
        print(f"  '{addr}'")
        print(f"    on {d} (plan={res['plan']}): {loc}")
        print(f"    -> your reps: {who}")

    print("\n(d) SAME address across the 2022 REDISTRICTING (versioned district_versions):")
    for d in ("2021-06-01", "2026-02-01"):
        res = roster_lib.representatives_for_address(CFG, addr, d, latlon=latlon, precinct="MIL001")
        if res.get("district"):
            print(f"    {d} (plan={res['plan']}): geographic District {res['district']} "
                  f"-> {[x['person_name'] for x in res['reps'] if x['seat_id'].startswith('D')]}")
        else:
            print(f"    {d} (plan={res['plan']}): {res.get('gap')}")

    print("\n(e) Precinct-map cross-check (district_precincts vs election outcomes):")
    roster_lib.precinct_crosscheck(CFG, verbose=True)


if __name__ == "__main__":
    rows = roster_lib.build(CFG, TENURES)
    n = {c: sum(1 for r in rows if r["confidence"] == c) for c in ("high", "medium", "low")}
    nvac = sum(1 for r in rows if r["person_name"] == "VACANT")
    print(f"Wrote {os.path.relpath(TERMS_OUT, CITY_DIR)} "
          f"({len(rows)} tenures: {n['high']} high / {n['medium']} medium / {n['low']} low; "
          f"{nvac} VACANT interval(s))")
    print(f"Wrote {os.path.relpath(DISTRICTS_OUT, CITY_DIR)} "
          f"(4 districts x 2 plans + Mayor; redistricting {REDISTRICT_ORD})")
    print(f"Wrote {os.path.relpath(PRECINCTS_OUT, CITY_DIR)} "
          f"(plan_2022 precinct map + plan_2016 gap rows)")
    if "--check" in sys.argv:
        print("\nValidation: PASS (no overlaps; every row has sources+confidence).")
        print("Precinct cross-check:")
        roster_lib.precinct_crosscheck(CFG, verbose=True)
    if "--demo" in sys.argv:
        demo()
