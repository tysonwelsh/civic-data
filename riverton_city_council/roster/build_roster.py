#!/usr/bin/env python3
"""build_roster.py — rolling council-roster for RIVERTON (a slowly-changing-dimension /
interval table of who holds each council + mayor seat over time). Riverton is a
**six-member-council city**: **5 geographic council districts (D1..D5)** legislate, and a
separately-elected **Mayor** chairs the council but votes ONLY to break a tie (the Park City
model) -> `non_voting_mayor=True` (MAYOR rows carry EMPTY vote bounds; a full council roll
tops out at 5). The districts were **redrawn after the 2020 Census (Ordinance No. 22-07,
adopted 2022-02-15)** and — the headline hazard — **D3 and D4 were RENUMBERED (swapped)** at
that redraw.

THIN DRIVER: Riverton-specific DATA + config; generic mechanics live in
../../scripts/roster_lib.py. District template: west_jordan_city_council/roster/.

DERIVED LAYER — regenerable, never hand-edited. Canonical inputs:
  1. election_results/riverton_results_by_candidate.csv  (winners; 2007-2025, incl. recovered 2019/2021)
  2. cities.db  role table (city='riverton', body='Council')  (observed vote bounds)
  3. meeting_minutes/minutes/**  (the 22-07 renumber, the Stewart->Pierucci D1 vacancy, seatings)
  4. roster/roster_overrides.csv  (hand corrections; applied LAST, win ties)

Usage:
  python3 roster/build_roster.py            # regenerate the CSVs
  python3 roster/build_roster.py --demo     # regenerate + print the demo queries
  python3 roster/build_roster.py --check    # regenerate + validations

Cardinal rule (repo CLAUDE.md): NEVER fabricate. Unknown seat-holder / date / boundary ->
explicit VACANT/gap + confidence + a note, never a guess.

THE D3 <-> D4 RENUMBER (Ordinance No. 22-07, adopted 2022-02-15) — how this roster models it:
  seat_id here is the **CURRENT (post-2022) district number** (the numbering used by the
  current city GIS, the current roster, and the 2023/2025 elections). Two people held the
  swapped pair continuously across 2022:
    * TISH BUROKER — CURRENT seat D3 (won by her successor Alexander Johnson 2025). She was
      ELECTED under the label "District 4" in 2017 & 2021 (pre-2022 numbering). -> her D3 rows
      carry district="District 3" (current) with a note recording the "District 4" ballot label.
    * TAWNEE McCAY — CURRENT seat D4 (won by her successor Shannon Smith 2025). She was ELECTED
      under the label "District 3" in 2017 & 2021. -> her D4 rows carry district="District 4"
      (current) with a note recording the "District 3" ballot label.
  Consequence: the built-in election cross-check prints EXPECTED "winner not in roster" warnings
  for McCay-2017/2021 (labeled D3) and Buroker-2017/2021 (labeled D4) — they map to their
  CURRENT seats (D4 / D3), not the ballot-label number. These 4 warnings are the documented
  renumber, not a defect (see election_results/CLAUDE.md). D1/D2/D5 are unaffected.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.dirname(HERE)                 # riverton_city_council/
REPO_ROOT = os.path.dirname(CITY_DIR)            # civic-data/
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import roster_lib
from roster_lib import RosterConfig, Redistrict

ELECTIONS = os.path.join(CITY_DIR, "election_results", "riverton_results_by_candidate.csv")
CITIES_DB = os.path.join(REPO_ROOT, "cities.db")
OVERRIDES = os.path.join(HERE, "roster_overrides.csv")
TERMS_OUT = os.path.join(HERE, "council_terms.csv")
DISTRICTS_OUT = os.path.join(HERE, "district_versions.csv")
PRECINCTS_OUT = os.path.join(HERE, "district_precincts.csv")
PRECINCT_MAP = os.path.join(CITY_DIR, "geo", "precinct_to_district.csv")   # canonical geo map (H-A 2026-07-19)
PRECINCTS_BYP_SRC = os.path.join(CITY_DIR, "election_results", "riverton_results_by_precinct.csv")

CITY = "riverton"
DATA_FLOOR = "2020-01-01"
GEOM_REF = "geo/districts.geojson"

PLAN_OLD = "plan_pre2022"
PLAN_NEW = "plan_2022"
PLAN_SWITCH = "2022-02-15"          # Ordinance No. 22-07 adopted (2022-02-15 council meeting)
REDISTRICT_ORD = "Ordinance No. 22-07"

SEAT_DISTRICT = {
    "D1": "District 1", "D2": "District 2", "D3": "District 3", "D4": "District 4",
    "D5": "District 5", "MAYOR": "Citywide",
}

TENURES = [
    # ============================ D1 (Cohort B: 2019 / 2023) — Stewart -> Pierucci ============
    dict(body="Council", seat_id="D1", person_name="Sheldon Stewart", person_key="sheldon_stewart",
         start_date="2020-01-06", start_event="elected", election_year="2019", end_event="resigned",
         confidence="high",
         vacate_date="2022-12-14", vacate_confidence="high",
         vacate_source="minutes:2022-12-13 (City Manager 'explained that Councilmember Stewart's resignation would "
                       "be [effective]...'); his last cities.db D1 vote is 2022-12-13",
         sources="election:2019 (District 1 winner, 498, 100.0%; also won 2011 & 2015 — long-serving incumbent); "
                 "votes:2020-03-17..2022-12-13 (cities.db, D1); minutes:2022-12-13 (resignation)",
         note="Elected D1 (2019, in the recovered election file); term seated at the Jan-2020 statutory term-start "
              "(the recovered minutes corpus begins 2020-02-17, so no January-2020 oath doc is on disk). RESIGNED "
              "late 2022 -> explicit VACANT interval until Pierucci's appointment (2023-01-03)."),
    dict(body="Council", seat_id="D1", person_name="Andy Pierucci", person_key="andy_pierucci",
         start_date="2023-01-03", start_event="appointed", election_year="", end_event="succeeded-by-elected",
         confidence="high",
         sources="minutes:2023-01-03 ('Andy Pierucci was appointed to serve as the District 1 Councilmember through "
                 "the end of 2023'); votes:2023-01-03..2023-12-19 (cities.db, D1)",
         note="APPOINTED to the D1 vacancy 2023-01-03 to serve through 2023, THEN won the 2023 general for the full "
              "next term (see below). first_vote/last_vote clamped to this appointed window."),
    dict(body="Council", seat_id="D1", person_name="Andy Pierucci", person_key="andy_pierucci",
         start_date="2024-01-02", start_event="elected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 1 winner, 416, 100.0%); minutes:2024-01-02 (first documented 2024 meeting; "
                 "seated for the full term); votes:2024-01-02..2026-06-02 (cities.db, D1)",
         note="Elected D1 2023 (full term) after the ~1-year interim appointment above. Currently serving."),

    # ============================ D2 (Cohort B: 2019 / 2023) — continuous McDougal ============
    dict(body="Council", seat_id="D2", person_name="Troy McDougal", person_key="troy_mcdougal",
         start_date="2020-01-06", start_event="elected", election_year="2019", end_event="reelected",
         confidence="high",
         sources="election:2019 (District 2 winner, as 'Troy D McDougal', 1,174, 64.08%); votes:2020-03-17.. "
                 "(cities.db, D2)",
         note="Elected D2 2019; re-elected 2023 -> continuous service (statutory Jan-2020 term-start; corpus begins "
              "2020-02-17)."),
    dict(body="Council", seat_id="D2", person_name="Troy McDougal", person_key="troy_mcdougal",
         start_date="2024-01-02", start_event="reelected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 2 winner, 945, 51.16%); minutes:2024-01-02 (seated); votes:continuous "
                 "through 2026-06-02 (cities.db, D2)",
         note="Re-elected D2 2023. Currently serving."),

    # ============================ D3 (CURRENT numbering = Buroker's seat; renumbered from "D4") ==
    dict(body="Council", seat_id="D3", person_name="Tish Buroker", person_key="tish_buroker",
         start_date="2018-01-01", start_event="elected", election_year="2017", end_event="reelected",
         confidence="medium",
         sources="election:2017 (winner labeled 'District 4', as 'Tish R. Buroker', 1,213, 53.18%); "
                 "votes:2020-03-17.. (cities.db)",
         note="PRE-FLOOR term start: won in 2017 under the ballot label 'District 4' (term began Jan 2018, predates "
              "the 2020 minutes floor) -> medium. Her seat's CURRENT number is D3 (renumbered D4->D3 at the 2022 "
              "Ord. 22-07 redraw; her successor Alexander Johnson holds D3). Join on PERSON across 2022, not the "
              "bare district number."),
    dict(body="Council", seat_id="D3", person_name="Tish Buroker", person_key="tish_buroker",
         start_date="2022-01-04", start_event="reelected", election_year="2021", end_event="became-mayor",
         confidence="high",
         sources="election:2021 (winner labeled 'District 4', as 'Tish Buroker', 1,160, 100.0% — recovered from raw "
                 "SOVC); minutes:2022-01-04 (seated); votes:2022-01-04..2025-12-16 (cities.db)",
         note="Re-elected 2021 (ballot label 'District 4'; her CURRENT seat is D3 post-renumber). Won the 2025 "
              "MAYORALTY and moved to the Mayor's chair at the 2026-01-20 seating (end_event=became-mayor); her "
              "council term expired at the same cycle boundary (clean handoff to Johnson, no mid-term vacancy)."),
    dict(body="Council", seat_id="D3", person_name="Alexander Johnson", person_key="alexander_johnson",
         start_date="2026-01-20", start_event="elected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (District 3 winner, as 'Alexander A. Johnson', 1,546, 68.77%); minutes:2026-01-20 "
                 "(seated); votes:2026-01-20..2026-06-02 (cities.db)",
         note="Elected D3 2025 (current numbering) — succeeded Buroker on this seat. Currently serving."),

    # ============================ D4 (CURRENT numbering = McCay's seat; renumbered from "D3") ===
    dict(body="Council", seat_id="D4", person_name="Tawnee McCay", person_key="tawnee_mccay",
         start_date="2018-01-01", start_event="elected", election_year="2017", end_event="reelected",
         confidence="medium",
         sources="election:2017 (winner labeled 'District 3', 994, 52.76%); votes:2020-03-17.. (cities.db)",
         note="PRE-FLOOR term start: won in 2017 under the ballot label 'District 3' (term began Jan 2018) -> medium. "
              "Her seat's CURRENT number is D4 (renumbered D3->D4 at the 2022 Ord. 22-07 redraw; her successor "
              "Shannon Smith holds D4). Join on PERSON across 2022."),
    dict(body="Council", seat_id="D4", person_name="Tawnee McCay", person_key="tawnee_mccay",
         start_date="2022-01-04", start_event="reelected", election_year="2021", end_event="unknown",
         confidence="high",
         sources="election:2021 (winner labeled 'District 3', 863, 100.0% — recovered from raw SOVC; the 2021 slice "
                 "was privacy-suppressed and re-parsed); minutes:2022-01-04 (seated); votes:2022-01-04..2025-12-16 "
                 "(cities.db)",
         note="Re-elected 2021 (ballot label 'District 3'; CURRENT seat D4 post-renumber). Term expired Jan 2026; "
              "not a 2025 candidate (Smith won the seat) -> end_event=unknown (served the full term; the "
              "retire-vs-decline mechanism is unrecorded, the end date is the successor's seating)."),
    dict(body="Council", seat_id="D4", person_name="Shannon Smith", person_key="shannon_smith",
         start_date="2026-01-20", start_event="elected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (District 4 winner, 1,987, 70.99%); minutes:2026-01-20 (seated); votes:2026-01-20.."
                 "2026-06-02 (cities.db)",
         note="Elected D4 2025 (current numbering) — succeeded McCay on this seat. Currently serving."),

    # ============================ D5 (Cohort B: 2019 / 2023) — Wells -> Haymond ============
    dict(body="Council", seat_id="D5", person_name="Claude Wells", person_key="claude_wells",
         start_date="2020-01-06", start_event="elected", election_year="2019", end_event="unknown",
         confidence="high",
         sources="election:2019 (District 5 winner, 846, 55.26%); votes:2020-03-17..2023-12-06 (cities.db, D5)",
         note="Elected D5 2019; served the full term. Not a 2023 candidate (Haymond won) -> end_event=unknown (end "
              "date = successor's Jan-2024 seating; the retire-vs-decline mechanism is unrecorded)."),
    dict(body="Council", seat_id="D5", person_name="Spencer Haymond", person_key="spencer_haymond",
         start_date="2024-01-02", start_event="elected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 5 winner, 1,142, 62.82%); minutes:2024-01-02 (seated); votes:2024-01-02.."
                 "2026-06-02 (cities.db, D5)",
         note="Elected D5 2023. Currently serving."),

    # ============================ MAYOR (chairs council; votes only to break a tie) ============
    dict(body="Mayor", seat_id="MAYOR", person_name="Trent Staggs", person_key="trent_staggs",
         start_date="2018-01-01", start_event="elected", election_year="2017", end_event="reelected",
         confidence="medium",
         sources="election:2017 (Mayor winner, 5,427, 59.66%; also won 2013 as D4 councilmember — pre-floor, not "
                 "rostered); minutes:presides 2020+ as 'Mayor Staggs'",
         note="PRE-FLOOR mayoral term start (won 2017, term began Jan 2018) -> medium. Mayor votes ONLY to break a "
              "tie -> EMPTY vote bounds (non_voting_mayor); his single recorded council tie-break (2025-12-16, Res. "
              "25-62) is not counted as council membership."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Trent Staggs", person_key="trent_staggs",
         start_date="2022-01-04", start_event="reelected", election_year="2021", end_event="unknown",
         confidence="high",
         sources="election:2021 (Mayor winner, 4,973, 100.0% — recovered from raw SOVC); minutes:presides 2022+; "
                 "the sole tie-break 2025-12-16 (Resolution No. 25-62, skate-facility removal, 2-2 -> Staggs Aye)",
         note="Re-elected Mayor 2021. Term expired Jan 2026; not a 2025 mayoral candidate (Buroker won) -> "
              "end_event=unknown. EMPTY vote bounds (non_voting_mayor)."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Tish Buroker", person_key="tish_buroker",
         start_date="2026-01-20", start_event="elected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (Mayor winner, 7,687, 70.07%); minutes:2026-01-20 (seated as Mayor); votes only to "
                 "break a tie (non_voting_mayor)",
         note="Elected Mayor 2025 (having served the D3/'District 4' council seat 2018-2025 — same person). EMPTY "
              "vote bounds. Currently serving."),
]

# canonical UPPER-CASE election name token -> our person_key (WINNERS only pass through here).
# BUROKER + McCAY are the renumbered pair; both resolve to one person_key each across the swap.
NAME_TO_KEY = {
    "STEWART": "sheldon_stewart", "MCDOUGAL": "troy_mcdougal", "BUROKER": "tish_buroker",
    "MCCAY": "tawnee_mccay", "JOHNSON": "alexander_johnson", "SMITH": "shannon_smith",
    "WELLS": "claude_wells", "HAYMOND": "spencer_haymond", "PIERUCCI": "andy_pierucci",
    "STAGGS": "trent_staggs",
}

# cities.db person.name_key -> our person_key (council voters). trentstaggs (the tie-break-only
# Mayor, 1 role vote) is EXCLUDED — his MAYOR rows are emptied by non_voting_mayor; tishburoker
# IS mapped for her 2020-2025 D3 council votes (her MAYOR row is emptied).
DB_KEY = {
    "sheldonstewart": "sheldon_stewart", "claudewells": "claude_wells",
    "tawneemccay": "tawnee_mccay", "tishburoker": "tish_buroker",
    "troymcdougal": "troy_mcdougal", "andypierucci": "andy_pierucci",
    "spencerhaymond": "spencer_haymond", "alexanderjohnson": "alexander_johnson",
    "shannonsmith": "shannon_smith",
}


def seat_for_contest(office, district):
    """election (office, district-LABEL) -> the CURRENT district label used as the cross-check
    key. NOTE the D3<->D4 renumber: a 2017/2021 winner labeled 'District 3'/'District 4' maps
    to CURRENT 'District 3'/'District 4' here, which for McCay/Buroker is the OPPOSITE of their
    current seat -> the cross-check prints 4 EXPECTED renumber warnings (documented)."""
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
    source_url="meeting_minutes/minutes/2022/2022-02-14/2022-02-15_city-council.md (Ordinance No. 22-07 "
               "— Amending the Council District Boundaries; moved by Councilmember Buroker, adopted 2022-02-15); "
               "geo/districts.geojson (current) + geo/districts_pre2022.geojson (prior 2019 lines)",
    data_floor=DATA_FLOOR,
    current_note="CURRENT post-2020-census boundaries (Ordinance No. 22-07, adopted 2022-02-15). geometry_ref = "
                 "geo/districts.geojson. First used for the 2023 (D1/D2/D5) and 2025 (D3/D4) district elections. "
                 "NOTE: 'District 3' here = Buroker's old seat (renumbered from the pre-2022 'District 4'); "
                 "'District 4' = McCay's old seat (from pre-2022 'District 3').",
    prior_adopted_by="prior plan (pre-2022 / 2019 district lines)",
    prior_geom_ref="geo/districts_pre2022.geojson",
    prior_confidence="high",
    prior_note="Prior-plan (pre-2022) district boundaries = the retained 2019 GIS layer "
               "geo/districts_pre2022.geojson (authoritative, not reconstructed) -> high. In force through the "
               "2019/2021 elections. NOTE the D3<->D4 label SWAP: in this prior plan 'District 3' = McCay's area "
               "and 'District 4' = Buroker's area — the OPPOSITE of the current plan (see Ord. 22-07). "
               "effective_start = data floor.",
    citywide_rows=[
        ("MAYOR", "citywide", "the separately-elected Mayor (Trent Staggs -> Tish Buroker), who chairs the "
                              "council and votes only to break a tie"),
    ],
    citywide_adopted_by="Riverton City (citywide mayoral office)",
    citywide_note_template="{who}: represents the ENTIRE city on every date, unchanged by the 2022 redistricting. "
                           "Only the 5 numbered council districts are geographic.",
    # Precinct layer ENABLED 2026-07-19 (H-A). geo/precinct_to_district.csv has NO source_year
    # column, so write_precincts falls back to the EXPLICIT precinct_source_default token (fail-loud
    # if unset). Token 'current' == precinct_hi_source -> every current-plan (plan_2022) precinct row
    # is confidence=high (the map is centroid-in-district off Riverton's OFFICIAL current district
    # FeatureServer). Because the token is not a year, per-precinct MISMATCH detection stays dormant
    # (the documented "token-not-a-year" limitation); the aggregate winner cross-check runs live.
    # Only current-plan (2023+) cycles are graded; pre-2022 cycles fall under plan_old (old precinct
    # numbering + the D3<->D4 ballot swap) -> honest GAP, never graded, so the renumber can't corrupt it.
    precinct_hi_source="current",
    precinct_source_default="current",
    precinct_hi_note=("current post-2020-census precinct->district read directly from "
                      "geo/precinct_to_district.csv (no source_year column -> precinct_source_default "
                      "token 'current'; H-A 2026-07-19). Official Riverton current district layer; "
                      "districts only (the Mayor is city-wide)."),
    precinct_med_note="",
    precinct_prior_note=("Prior-plan (pre-2022) precinct->district composition NOT acquired -> honest "
                         "GAP (blank). Under the pre-2022 numbering 'District 3'=McCay's area and "
                         "'District 4'=Buroker's area — the OPPOSITE of the current plan (Ord. 22-07 "
                         "D3<->D4 swap)."),
    crosscheck_districts=("1", "2", "3", "4", "5"),
    precinct_prefix="RIV", geo_seat_prefix="D",
    plan_switch_year="2023", citywide_seats=(),
)

CFG = RosterConfig(
    non_voting_mayor=True,
    city=CITY, city_dir=CITY_DIR, repo_root=REPO_ROOT, data_floor=DATA_FLOOR,
    geom_ref=GEOM_REF, elections_path=ELECTIONS, cities_db_path=CITIES_DB,
    overrides_path=OVERRIDES, terms_out=TERMS_OUT, districts_out=DISTRICTS_OUT,
    seat_district=SEAT_DISTRICT, name_to_key=NAME_TO_KEY, db_key=DB_KEY,
    seat_order=["D1", "D2", "D3", "D4", "D5", "MAYOR"],
    # general winners from 2017 on (2017 seats the earliest in-window pre-floor terms; pre-2017
    # winners' terms all ended before the 2020 floor -> excluded to avoid forever-unmappable warnings).
    keep_election_row=lambda r: ("general" in r["election_type"].lower() and int(r["year"]) >= 2017),
    contest_key=seat_for_contest, crosscheck_field="district",
    winners_have_district=True,
    elected_events=("elected", "reelected"),
    # H-C reverse-crosscheck DOCUMENTED exceptions (2026-07-19). crosscheck_field='district', so the
    # keys are (year, current-district-label, person_key). These are the MIRROR of the 4 EXPECTED
    # forward "winner not in roster" warnings from the D3<->D4 RENUMBER (Ordinance No. 22-07, adopted
    # 2022-02-15): the roster uses CURRENT numbering (Buroker=D3, McCay=D4) while the 2017/2021 ballots
    # (and the by_candidate file) label Buroker=District 4 and McCay=District 3. Person↔district joins
    # across 2022 go on PERSON identity, not the bare number (corroborated by geo/districts_pre2022.geojson).
    # Roster is correct — see the module docstring, CLAUDE.md, and election_results/CLAUDE.md.
    reverse_crosscheck_exceptions={
        ("2017", "District 3", "tish_buroker"): "D3<->D4 renumber (Ord. 22-07, 2022-02-15): Buroker holds CURRENT D3 but was elected 2017 under the ballot label 'District 4' (by_candidate has her as District 4) — join on person; pre-2022 GIS corroborates",
        ("2021", "District 3", "tish_buroker"): "D3<->D4 renumber (Ord. 22-07, 2022-02-15): Buroker holds CURRENT D3 but was elected 2021 under the ballot label 'District 4' (by_candidate has her as District 4) — join on person; pre-2022 GIS corroborates",
        ("2017", "District 4", "tawnee_mccay"): "D3<->D4 renumber (Ord. 22-07, 2022-02-15): McCay holds CURRENT D4 but was elected 2017 under the ballot label 'District 3' (by_candidate has her as District 3) — join on person; pre-2022 GIS corroborates",
        ("2021", "District 4", "tawnee_mccay"): "D3<->D4 renumber (Ord. 22-07, 2022-02-15): McCay holds CURRENT D4 but was elected 2021 under the ballot label 'District 3' (by_candidate has her as District 3) — join on person; pre-2022 GIS corroborates",
    },
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

    print("\n(b) Roster AS OF 2022-12-20 (D1 vacant after Stewart's resignation):")
    for r in roster_lib.roster_as_of(CFG, "2022-12-20", body="Council"):
        print(line(r))
    for r in roster_lib.roster_as_of(CFG, "2022-12-20", body="Mayor"):
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
          f"(5 districts x 2 plans [real prior geometry] + Mayor citywide; redistricting {REDISTRICT_ORD})")
    print(f"Wrote {os.path.relpath(PRECINCTS_OUT, CITY_DIR)} "
          f"(plan_2022 precinct map + plan_pre2022 gap rows; districts only)")
    if "--check" in sys.argv:
        print("\nValidation: PASS (no overlaps; sources+confidence present; non-voting-mayor + gap/vacate guards clear).")
        print("(The 4 'winner not in roster' cross-check warnings above for McCay-2017/2021 + Buroker-2017/2021 "
              "are the EXPECTED D3<->D4 renumber — see the module docstring.)")
        print("Precinct cross-check:")
        roster_lib.precinct_crosscheck(CFG, verbose=True)
    if "--demo" in sys.argv:
        demo()
