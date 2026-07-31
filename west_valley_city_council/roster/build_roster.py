#!/usr/bin/env python3
"""build_roster.py — rolling council-roster for WEST VALLEY CITY (a slowly-changing-dimension /
interval table of who holds each council + mayor seat over time). West Valley City is a **MIXED
Council-Mayor city**: **4 geographic council districts** (D1..D4) + **2 city-wide AT-LARGE seats**
(AL1, AL2) + a **separately-elected Mayor who DOES vote** on council motions. A full council roll
call is **7** (Mayor included). Council votes exist from **2020**; the Salt Lake County election
record used here runs **2019+**. The 4 districts were **redrawn after the 2020 Census** (Ordinance
22-10, adopted 2022-03-15).

THIN DRIVER: this file holds only West-Valley-specific DATA (the curated TENURES, the name maps,
the 2022-redistricting facts + prose) + config; all generic mechanics live in
../../scripts/roster_lib.py (canon_key, election/vote-bounds/override reconciliation, end-date
chaining + VACANT insertion, validation incl. the gap/vacate guards, the CSV writers, and the
as-of / address / precinct-crosscheck query helpers). West Valley is the fleet's SECOND MIXED
(districts + at-large) roster after West Jordan (west_jordan_city_council/) — but WVC differs on
the headline structural fact: **its Mayor VOTES** (non_voting_mayor=False), and its two at-large
seats are TWO separate staggered "Vote-for-1" seats (not one grouped Vote-for-N field), so each
at-large seat maps cleanly onto its own cycle.

DERIVED LAYER — regenerable, never hand-edited. Canonical inputs:
  1. election_results/west_valley_results_by_candidate.csv (winners -> `elected`/`reelected`; 2019+)
  2. cities.db  role table (city='west_valley', body='Council')  (observed vote bounds)
  3. meeting_minutes/minutes/**  (oath/seating dates, the redistricting ordinance, the two mid-term
     appointments — Whetstone D3 2022 + Wood D4 2025)
  4. roster/roster_overrides.csv  (hand corrections; applied LAST, win ties)

Outputs (idempotent — re-running reproduces them byte-for-byte):
  roster/council_terms.csv        one row per seat-tenure (4 district + 2 at-large + MAYOR)
  roster/district_versions.csv    boundary interval table — REAL 4 districts x 2 plans + At-Large + Mayor
  roster/district_precincts.csv   versioned precinct->district composition (plan-scoped, districts only)
  (The two per-city precinct SIDECARS — _precinct_to_district.csv + _precinct_votes.csv — were
   RETIRED 2026-07-11: roster_lib now reads the canonical geo/precinct_to_district.csv and
   election_results/*_results_by_precinct.csv directly (multi-year precinct_hi_source +
   blank/suppressed vote guard), so no collapse/clean sidecar is needed.)

Usage:
  python3 roster/build_roster.py            # regenerate the CSVs
  python3 roster/build_roster.py --demo     # regenerate + print the demo queries
  python3 roster/build_roster.py --check    # regenerate + validations + precinct cross-check

Cardinal rule (repo CLAUDE.md): NEVER fabricate. Unknown seat-holder / boundary / date ->
explicit VACANT/gap + confidence + a note, never a guess.

Provenance / confidence model (West Valley):
  high   = an in-file election win (2019/2021/2023/2025) seated at a documented first-of-year
           meeting and corroborated by the cities.db named-vote record, OR one of the two fully-
           documented mid-term appointments (Whetstone D3 Res. 22-11; Wood D4 Res. 25-11).
  medium = a 2017-cycle HOLDOVER serving at the 2020 data floor whose SEATING election predates the
           2019 election-data floor — service is vote-documented from 2020-01-07 but the term's
           origin is below the floor (four rows: Bigelow MAYOR, Nordfelt AL2, Buhler D2, Fitisemanu D4).
  low    = genuinely unknown / not-acquired (flagged) — here only in the prior-plan
           district/precinct GAP rows (plan_pre2022 geometry is not on disk).

West Valley seat model (STABLE ids — a redistricting redraws boundaries, it does NOT renumber seats):
  D1..D4  four geographic district seats
  AL1..AL2  two city-wide AT-LARGE seats  (ANALYTICAL ids — see note below)
  MAYOR    separately-elected Mayor (VOTES — counted in the 7-member roll)
Staggered 4-year cycles (odd calendar years), as the county SOVC records them:
  A  At-Large(seat 1) + D1 + D3            elected 2019 / 2023  -> terms seated Jan 2020 / 2024
  B  Mayor + At-Large(seat 2) + D2 + D4    elected 2021 / 2025  -> terms seated Jan 2022 / 2026

AT-LARGE seat ids are an ANALYTICAL construct — but a MILD one. WVC's two at-large seats are each a
separate single-winner "Vote for 1" contest on its OWN staggered cycle (unlike West Jordan's one
grouped Vote-for-3 field). So the mapping is naturally 1:1 and stable:
  AL1 = the 2019/2023 at-large seat — Don Christensen throughout (won 2019 + 2023).
  AL2 = the 2021/2025 at-large seat — Lars Nordfelt throughout (2017-cycle holdover in 2020, then
        won 2021 + 2025).
The county ballot labels both contests simply "At-Large" (no ballot seat number), so the election
cross-check keys on the district LABEL ("At-Large"), not the analytical seat id — but because each
at-large winner sits in a DIFFERENT year, (year, "At-Large", person) is already unambiguous and each
winner lands on the right AL id anyway.

KNOWN nuances handled honestly (never fabricated around):
  * THE MAYOR VOTES (the headline structural fact — OPPOSITE of West Jordan / South Jordan). A full
    WVC council roll call names SEVEN voters INCLUDING the Mayor. Verbatim, 2022-03-15 (Ordinance
    22-10, the redistricting itself): the roll names all six councilmembers AND "Mayor Lang  Yes"
    — 7-0 Unanimous. So `non_voting_mayor=False`: MAYOR-body rows CARRY vote bounds and both mayors
    (Bigelow, Lang) ARE in DB_KEY. (Verified: every full roll = 7 distinct voters, mayor included.)
  * KAREN LANG — ONE PERSON, TWO BODIES (District 3 -> Mayor). Lang won D3 in 2019 (seated 2020-01-07),
    then won the MAYOR seat in 2021 and took office 2022-01-04 — vacating D3 mid-term. One karen_lang
    key spans both bodies, but first_vote/last_vote are CLAMPED to each tenure's own [start_date,
    end_date) window (roster_lib.clamp_vote_bounds), so her D3 row shows only D3-era votes
    (2020-01-07 .. 2021-12-14) while her Mayor rows carry their own mayor-era bounds (2022-01-04 ..
    2025-12-09, then 2026-01-13 .. 2026-05-26) — the cross-body smear is gone structurally, not by
    annotation. The authoritative service interval is always start_date/end_date. Her D3 departure
    created the documented D3 vacancy below.
  * THE D3 MID-TERM VACANCY (Lang -> VACANT -> Whetstone appointed -> Whetstone elected). When Lang
    became Mayor (2022-01-04) her D3 seat fell vacant "with the election of Karen Lang as Mayor"
    (minutes 2022-01-18). At the 2022-01-18 Regular meeting the Council appointed **William Whetstone**
    to D3 by **Resolution 22-11** ("appoint William Whetstone as Councilmember for District 3 ... to
    serve until the January following the next general election"), 6-0 (he acted as councilmember by
    that meeting's adjournment). Whetstone then WON D3 outright at the 2023 general and was seated
    2024-01-02. -> explicit VACANT interval D3 [2022-01-04, 2022-01-18).
  * THE D4 MID-TERM VACANCY (Fitisemanu -> VACANT -> Wood appointed -> Wood elected). Jake Fitisemanu
    (D4, re-elected 2021) left mid-term: "This vacancy was created when Jake Fitisemanu was elected to
    State House District 30 in the 2024 General Election" (minutes 2025-01-28); his last cities.db D4
    vote is 2024-12-10. At the 2025-01-28 Regular meeting the Council appointed **Cindy Wood** to D4 by
    **Resolution 25-11** (oath administered that night). Wood then WON D4 at the 2025 general and was
    seated 2026-01-13. -> explicit VACANT interval D4 [2024-12-11, 2025-01-28). (Cindy Wood is also
    the one person who spans the appointed Planning Commission and the elected Council — see the
    repo CLAUDE.md.)
  * FOUR 2017-CYCLE HOLDOVERS at the 2020 floor (the only `medium` rows). In Jan 2020 the four B-cycle
    seats (Mayor, At-Large seat 2, D2, D4) were held by Ron Bigelow (Mayor), Lars Nordfelt (AL2), Steve
    Buhler (D2), and Jake Fitisemanu (D4) — all seated by the 2017 election, which is BELOW the 2019
    election-data floor. Their SERVICE is fully vote-documented from 2020-01-07, but the term origin is
    below the floor -> medium (no fabricated seating date/election). Bigelow did not run in 2021 (Lang
    won Mayor); Buhler ran for Mayor 2021 and lost, leaving D2 (Harmon won). Nordfelt + Fitisemanu each
    won their own seat in 2021 (continuous service, next high row).
  * SPARSE named rolls. WVC records named roll-calls mainly on substantive items (routine/consent
    business often passes on a tally-only voice vote), so a member's first/last NAMED vote can lag/
    precede real service. The authoritative interval is always start_date/end_date, not the vote bounds.
  * RDA / MBA are NOT separate roster seats. WVC's Redevelopment Agency (RDA) and Municipal Building
    Authority (MBA) are real, separately-meeting bodies — but the SAME councilmembers sit as their
    boards (one person, extra roles). The roster is COUNCIL-based: load_vote_bounds reads ONLY
    cities.db body='Council', and no RDA/MBA seat is created.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.dirname(HERE)                 # west_valley_city_council/
REPO_ROOT = os.path.dirname(CITY_DIR)            # civic-data/
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import roster_lib
from roster_lib import RosterConfig, Redistrict

ELECTIONS = os.path.join(CITY_DIR, "election_results", "west_valley_results_by_candidate.csv")
PRECINCTS_BYP_SRC = os.path.join(CITY_DIR, "election_results", "west_valley_results_by_precinct.csv")
GEO_PRECINCT_MAP = os.path.join(CITY_DIR, "geo", "precinct_to_district.csv")
CITIES_DB = os.path.join(REPO_ROOT, "cities.db")
OVERRIDES = os.path.join(HERE, "roster_overrides.csv")
TERMS_OUT = os.path.join(HERE, "council_terms.csv")
DISTRICTS_OUT = os.path.join(HERE, "district_versions.csv")
PRECINCTS_OUT = os.path.join(HERE, "district_precincts.csv")

CITY = "west_valley"
DATA_FLOOR = "2020-01-01"            # data floor (city standard: 2020)
GEOM_REF = "geo/precincts.geojson + geo/precinct_to_district.csv"

# The real redistricting event (spot-checked against source minutes 2022-03-15):
#   Ordinance 22-10, "AMEND TITLE 2, CHAPTER 3 OF THE WEST VALLEY CITY MUNICIPAL CODE, MAKING
#   ADJUSTMENTS IN THE WEST VALLEY CITY COUNCIL DISTRICT BOUNDARIES." Adopted 2022-03-15 on a
#   7-0 UNANIMOUS roll call (motion Harmon "Option 1" / second Huynh): Fitisemanu, Whetstone,
#   Harmon, Huynh, Christensen, Nordfelt, and Mayor Lang all Yes. Built on 2020 Census data (each
#   proposed district within 1% of the ideal population). First used for the 2023 (D1/D3) and 2025
#   (D2/D4) district elections; 2019 (D1/D3) + 2021 (D2/D4) used the prior lines. West Valley
#   redistricts by ORDINANCE (Municipal Code Title 2 Ch. 3 / §2-3-103).
REDISTRICT_ORD = "Ordinance 22-10"
REDISTRICT_ADOPTED = "2022-03-15"
PLAN_OLD = "plan_pre2022"   # pre-2022 boundaries, in force through the 2021 elections (not on disk)
PLAN_NEW = "plan_2022"      # Ordinance 22-10; in force for the 2023 elections onward
PLAN_SWITCH = "2022-03-15"  # documented adoption of the 2020-census boundaries
SRC_URL = ("meeting_minutes/minutes/2022/2022-03-14/2022-03-15_council-regular-meeting.md "
           "(Ordinance 22-10, amending Municipal Code Title 2 Ch. 3 West Valley City Council "
           "District Boundaries, Option 1, passed 7-0)")

SEAT_DISTRICT = {
    "D1": "District 1", "D2": "District 2", "D3": "District 3", "D4": "District 4",
    "AL1": "At-Large", "AL2": "At-Large", "MAYOR": "Citywide",
}

# ---------------------------------------------------------------------------
# LAYER 1-3 (reconciled). Each tenure anchored to a cited source. Ordered by seat.
#   Documented seating dates: 2020-01-07 (first documented 2020 council meeting; 2019-cycle members +
#   the four 2017-cycle holdovers), 2022-01-04 (first documented 2022 meeting; 2021-cycle seated),
#   2024-01-02 (first documented 2024 meeting; 2023-cycle seated), 2026-01-13 (first documented 2026
#   meeting; 2025-cycle seated), plus 2022-01-18 (D3 appointment, Res. 22-11) and 2025-01-28 (D4
#   appointment, Res. 25-11).
# ---------------------------------------------------------------------------
TENURES = [
    # ============================ D1 (A cycle: 2019 / 2023) — continuous Huynh ============================
    dict(body="Council", seat_id="D1", person_name="Tom Huynh", person_key="tom_huynh",
         start_date="2020-01-07", start_event="elected", election_year="2019", end_event="reelected",
         confidence="high",
         sources="election:2019 (District 1 winner, def. Christiana Tavo 65.64%); minutes:present 2020-01-07 "
                 "(first documented 2020 council meeting); votes:2020-01-07.. (cities.db, D1)",
         note="Elected D1 2019 (last D1 term on the OLD plan_pre2022 lines). Re-elected 2023 -> continuous."),
    dict(body="Council", seat_id="D1", person_name="Tom Huynh", person_key="tom_huynh",
         start_date="2024-01-02", start_event="reelected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 1 winner, def. Marni Lefevre 54.52%); minutes:2024-01-02 (present, "
                 "first documented 2024 council meeting); votes:continuous through 2026-05-26 (cities.db, D1)",
         note="Re-elected D1 2023 (first D1 term on the plan_2022 lines; seated 2024-01-02). Currently serving."),

    # ============================ D2 (B cycle: holdover -> 2021 / 2025) ============================
    dict(body="Council", seat_id="D2", person_name="Steve Buhler", person_key="steve_buhler",
         start_date="2020-01-07", start_event="in-office", election_year="", end_event="ran-for-mayor",
         confidence="medium",
         sources="minutes:present 2020-01-07 (first documented 2020 council meeting, as Councilmember District 2); "
                 "votes:2020-01-07..2021-12-14 (cities.db, D2); election:2021 (LOST the Mayor race to Karen Lang, "
                 "41.46%)",
         note="2017-CYCLE HOLDOVER at the 2020 data floor: his D2 seating election predates the 2019 election-data "
              "floor and is NOT in the loaded data -> medium (service vote-documented from 2020-01-07; term origin "
              "below the floor, no fabricated seating date/election). Ran for MAYOR in 2021 and lost -> left the D2 "
              "seat Jan 2022 (Harmon won D2). Clean cycle-boundary handoff (no vacancy)."),
    dict(body="Council", seat_id="D2", person_name="Scott Harmon", person_key="scott_harmon",
         start_date="2022-01-04", start_event="elected", election_year="2021", end_event="reelected",
         confidence="high",
         sources="election:2021 (District 2 winner, as 'Scott Harmon', def. Chris Bell 59.39%); minutes:present "
                 "2022-01-04 (first documented 2022 council meeting); votes:2022-01-04.. (cities.db, D2)",
         note="Elected D2 2021 (last D2 term on the OLD plan_pre2022 lines; seated 2022-01-04). Re-elected 2025."),
    dict(body="Council", seat_id="D2", person_name="Scott Harmon", person_key="scott_harmon",
         start_date="2026-01-13", start_event="reelected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (District 2 winner, as 'Scott L. Harmon', def. Danny George Jr 61.53%); minutes:"
                 "2026-01-13 (present, first documented 2026 council meeting); votes:continuous through 2026-05-26",
         note="Re-elected D2 2025 (first D2 term on the plan_2022 lines; seated 2026-01-13). Ballot name 'Scott L. "
              "Harmon' (2025) vs 'Scott Harmon' (2021) — same person. Currently serving."),

    # ============================ D3 (A cycle + the 2022 mid-term vacancy) ============================
    dict(body="Council", seat_id="D3", person_name="Karen Lang", person_key="karen_lang",
         start_date="2020-01-07", start_event="elected", election_year="2019", end_event="became-mayor",
         confidence="high",
         vacate_date="2022-01-04", vacate_confidence="high",  # D3 vacant when her Mayor term begins
         vacate_source="minutes:2022-01-18 ('a midterm vacancy has occurred in District 3 with the election of "
                       "Karen Lang as Mayor ... the office of Councilmember District 3 unfilled with a remaining "
                       "term of two years'); Lang presides as MAYOR from 2022-01-04 (first documented 2022 meeting)",
         sources="election:2019 (District 3 winner, def. Kaletta L. Lynch 70.32%); minutes:present 2020-01-07; "
                 "votes:2020-01-07..2021-12-14 (cities.db, D3 — clamped to this tenure's [2020-01-07, 2022-01-04) "
                 "window; her later MAYOR seat carries its own mayor-era bounds)",
         note="Elected D3 2019. LEFT D3 MID-TERM to become MAYOR (won the 2021 Mayor race; took office 2022-01-04) "
              "-> explicit VACANT interval D3 [2022-01-04, 2022-01-18) until Whetstone's appointment. ONE PERSON, "
              "TWO BODIES: first_vote/last_vote are clamped to THIS D3 tenure's own window (2020-01-07..2021-12-14); "
              "her later MAYOR rows carry their own mayor-era bounds, so there is no cross-body smear. The "
              "authoritative interval is this D3 tenure's start/end."),
    dict(body="Council", seat_id="D3", person_name="William Whetstone", person_key="william_whetstone",
         start_date="2022-01-18", start_event="appointed", election_year="", end_event="succeeded-by-elected",
         confidence="high",
         sources="minutes:2022-01-18 Regular ('RESOLUTION 22-11, APPOINT WILLIAM WHETSTONE AS COUNCILMEMBER FOR "
                 "DISTRICT 3 ... TO SERVE UNTIL THE JANUARY FOLLOWING THE NEXT GENERAL ELECTION'; passed 6-0; he "
                 "acts as councilmember by the meeting's adjournment); votes:2022-01-25.. (cities.db, D3)",
         note="APPOINTED to the D3 vacancy 2022-01-18 by Resolution 22-11 to fill the ~2 years remaining on Lang's "
              "term. He then WON D3 outright at the 2023 general and was seated 2024-01-02 (next row) -> this "
              "appointed tenure ends when the elected term begins."),
    dict(body="Council", seat_id="D3", person_name="William Whetstone", person_key="william_whetstone",
         start_date="2024-01-02", start_event="elected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 3 winner, as 'Will Whetstone', def. Heidi Roggenbuck 56.57%); minutes:"
                 "2024-01-02 (present, first documented 2024 council meeting); votes:continuous through 2026-05-26",
         note="Elected D3 2023 (first D3 term on the plan_2022 lines; seated 2024-01-02, following his ~2-year "
              "appointed interim). Ballot name 'Will Whetstone' vs roster 'William Whetstone' — same person. Serving. "
              "(Whetstone did not file any campaign-finance disclosures — a documented gap in campaign_finance/.)"),

    # ============================ D4 (B cycle: holdover -> 2021 + the 2024 mid-term vacancy) ============================
    dict(body="Council", seat_id="D4", person_name="Jake Fitisemanu", person_key="jake_fitisemanu",
         start_date="2020-01-07", start_event="in-office", election_year="", end_event="reelected",
         confidence="medium",
         sources="minutes:present 2020-01-07 (first documented 2020 council meeting, as Councilmember District 4); "
                 "votes:2020-01-07.. (cities.db, D4)",
         note="2017-CYCLE HOLDOVER at the 2020 data floor: his D4 seating election predates the 2019 election-data "
              "floor -> medium (service vote-documented from 2020-01-07; term origin below the floor). Won D4 again "
              "in 2021 (continuous service, next row). first_vote/last_vote are clamped to THIS tenure's "
              "[2020-01-07, 2022-01-04) window (2020-01-07..2021-12-14); his re-elected D4 term carries its own bounds."),
    dict(body="Council", seat_id="D4", person_name="Jake Fitisemanu", person_key="jake_fitisemanu",
         start_date="2022-01-04", start_event="reelected", election_year="2021", end_event="resigned",
         confidence="high",
         vacate_date="2024-12-11", vacate_confidence="high",  # VACANT begins the day AFTER his last day served (2024-12-10)
         vacate_source="minutes:2025-01-28 Regular ('This vacancy was created when Jake Fitisemanu was elected to "
                       "State House District 30 in the 2024 General Election. The vacancy, governed by Utah State "
                       "Code 20A-1-510, lasts until the end of the year'); his last cities.db D4 vote is 2024-12-10",
         sources="election:2021 (District 4 winner, as 'Jake Fitisemanu Jr', def. Darrell R. Curtis 53.45%); "
                 "minutes:present 2022-01-04; votes:2022-01-04..2024-12-10 (cities.db, D4)",
         note="Re-elected D4 2021 (first D4 term on the OLD plan_pre2022 lines through 2022-03-15, then the new "
              "lines; seated 2022-01-04). LEFT MID-TERM: elected to Utah State House District 30 at the 2024 general "
              "and departed (last D4 vote 2024-12-10) -> explicit VACANT interval D4 [2024-12-11, 2025-01-28) until "
              "Wood's appointment."),
    dict(body="Council", seat_id="D4", person_name="Cindy Wood", person_key="cindy_wood",
         start_date="2025-01-28", start_event="appointed", election_year="", end_event="succeeded-by-elected",
         confidence="high",
         sources="minutes:2025-01-28 Regular ('RESOLUTION NO. 25-11, APPOINT CINDY WOOD AS Councilmember for "
                 "District [4]'; the City Recorder administered the oath of office that night); votes:2025-02-11.. "
                 "(cities.db, D4)",
         note="APPOINTED to the D4 vacancy 2025-01-28 by Resolution 25-11 to fill the remainder of Fitisemanu's term. "
              "She then WON D4 outright at the 2025 general and was seated 2026-01-13 (next row) -> this appointed "
              "tenure ends when the elected term begins. Cindy Wood also served on the appointed Planning Commission "
              "before this Council term (one person, two bodies — see repo CLAUDE.md)."),
    dict(body="Council", seat_id="D4", person_name="Cindy Wood", person_key="cindy_wood",
         start_date="2026-01-13", start_event="elected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (District 4 winner, def. Amitonu Wesley Amosa 63.51%); minutes:2026-01-13 (present, "
                 "first documented 2026 council meeting); votes:continuous through 2026-05-26 (cities.db, D4)",
         note="Elected D4 2025 (first D4 term on the plan_2022 lines; seated 2026-01-13, following her ~1-year "
              "appointed interim). first_vote/last_vote are clamped to THIS tenure's window (2026-01-13..2026-05-26); "
              "her earlier appointed D4 term carries its own bounds. Currently serving."),

    # ============================ AL1 (At-Large seat, A cycle: 2019 / 2023) — continuous Christensen ============================
    dict(body="Council", seat_id="AL1", person_name="Don Christensen", person_key="don_christensen",
         start_date="2020-01-07", start_event="elected", election_year="2019", end_event="reelected",
         confidence="high",
         sources="election:2019 (At-Large 'Vote for 1' winner, def. Darrell R Curtis 56.66%); minutes:present "
                 "2020-01-07; votes:2020-01-07.. (cities.db, at-large)",
         note="Won the 2019 At-Large seat (a single-winner Vote-for-1 contest). AL1 is the ANALYTICAL id for the "
              "2019/2023 at-large cycle; Christensen holds it throughout. Re-elected 2023 -> continuous."),
    dict(body="Council", seat_id="AL1", person_name="Don Christensen", person_key="don_christensen",
         start_date="2024-01-02", start_event="reelected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (At-Large 'Vote for 1' winner, def. Sophia Hawes-Tingey 58.41%); minutes:2024-01-02 "
                 "(present); votes:continuous through 2026-05-26 (cities.db, at-large)",
         note="Re-elected At-Large 2023 (seated 2024-01-02). Currently serving."),

    # ============================ AL2 (At-Large seat, B cycle: holdover -> 2021 / 2025) — continuous Nordfelt ============================
    dict(body="Council", seat_id="AL2", person_name="Lars Nordfelt", person_key="lars_nordfelt",
         start_date="2020-01-07", start_event="in-office", election_year="", end_event="reelected",
         confidence="medium",
         sources="minutes:present 2020-01-07 (first documented 2020 council meeting, as Councilmember At-Large); "
                 "votes:2020-01-07.. (cities.db, at-large)",
         note="2017-CYCLE HOLDOVER at the 2020 data floor: his At-Large seating election predates the 2019 election-"
              "data floor -> medium (service vote-documented from 2020-01-07; term origin below the floor, no "
              "fabricated seating date/election). Re-elected At-Large 2021 (continuous, next row). AL2 is the "
              "ANALYTICAL id for the 2021/2025 at-large cycle; Nordfelt holds it throughout."),
    dict(body="Council", seat_id="AL2", person_name="Lars Nordfelt", person_key="lars_nordfelt",
         start_date="2022-01-04", start_event="reelected", election_year="2021", end_event="reelected",
         confidence="high",
         sources="election:2021 (At-Large 'Vote for 1' winner, def. Jim Vesock 59.59%); minutes:present 2022-01-04; "
                 "votes:continuous (cities.db, at-large)",
         note="Re-elected At-Large 2021 (seated 2022-01-04). Re-elected again 2025."),
    dict(body="Council", seat_id="AL2", person_name="Lars Nordfelt", person_key="lars_nordfelt",
         start_date="2026-01-13", start_event="reelected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (At-Large 'Vote for 1' winner, def. Heidi Roggenbuck 54.82%); minutes:2026-01-13 "
                 "(present, first documented 2026 council meeting); votes:continuous through 2026-05-26",
         note="Re-elected At-Large 2025 (seated 2026-01-13). Currently serving. (2025 also had a qualified write-in, "
              "Ryan Mahoney, 167 votes; Nordfelt won outright by 1,281 — no coin-toss/runoff occurred.)"),

    # ============================ MAYOR (Mayor VOTES: holdover -> 2021 / 2025) ============================
    dict(body="Mayor", seat_id="MAYOR", person_name="Ron Bigelow", person_key="ron_bigelow",
         start_date="2020-01-07", start_event="in-office", election_year="", end_event="did-not-run",
         confidence="medium",
         sources="minutes:present/presiding 2020-01-07 (first documented 2020 council meeting, as Mayor Bigelow); "
                 "votes:2020-01-07..2021-12-14 (cities.db, Mayor VOTES — he is named in the 7-member roll calls)",
         note="2017-CYCLE HOLDOVER Mayor at the 2020 data floor: his Mayor election predates the 2019 election-data "
              "floor -> medium (service vote-documented from 2020-01-07; term origin below the floor). WVC's Mayor "
              "VOTES on council motions (non_voting_mayor=False) so this row CARRIES vote bounds. Did not run in "
              "2021 -> Karen Lang won the open Mayor seat. Clean cycle-boundary handoff."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Karen Lang", person_key="karen_lang",
         start_date="2022-01-04", start_event="elected", election_year="2021", end_event="reelected",
         confidence="high",
         sources="election:2021 (Mayor winner, def. Steve Buhler 58.54%); minutes:presiding/voting 2022-01-04+ "
                 "(as 'Mayor Lang'; e.g. 2022-03-15 Ord. 22-10 roll call names 'Mayor Lang  Yes' in the 7-0); "
                 "votes:2022-01-04..2025-12-09 (cities.db, clamped to this Mayor tenure's window)",
         note="Elected Mayor 2021 (took office 2022-01-04). PREVIOUSLY held District 3 (2020-2022, see the D3 rows) "
              "-> her one karen_lang key spans BOTH bodies, but first_vote/last_vote are clamped to each tenure's "
              "own window, so this Mayor row carries only mayor-era bounds (2022-01-04..2025-12-09) and her D3 era "
              "stays on the D3 rows. The Mayor VOTES, so this row legitimately carries bounds. Re-elected Mayor 2025."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Karen Lang", person_key="karen_lang",
         start_date="2026-01-13", start_event="reelected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (Mayor winner, def. June Freeman Hesleph 75.40%); minutes:presiding/voting 2026-01-13 "
                 "(first documented 2026 council meeting); votes:continuous through 2026-05-26 (cities.db, Mayor votes)",
         note="Re-elected Mayor 2025 (seated 2026-01-13). Continues to preside AND vote on council motions. "
              "Currently serving."),
]

# canonical UPPER-CASE election name token -> our person_key. No two WEST VALLEY general winners share
# a surname, so no disambiguators are needed. (Bigelow + Buhler are 2017-cycle holdovers BELOW the
# 2019 election-data floor, so they never pass through canon_key — but they are listed here for
# completeness / robustness.)
NAME_TO_KEY = {
    "HUYNH": "tom_huynh", "HARMON": "scott_harmon", "LANG": "karen_lang",
    "WHETSTONE": "william_whetstone", "FITISEMANU": "jake_fitisemanu", "WOOD": "cindy_wood",
    "CHRISTENSEN": "don_christensen", "NORDFELT": "lars_nordfelt",
    "BIGELOW": "ron_bigelow", "BUHLER": "steve_buhler",
}

# cities.db person.name_key -> our person_key (all 10 council voters — the Mayor VOTES in WVC, so
# BOTH mayors are included, unlike the non-voting-mayor cities West Jordan / South Jordan).
DB_KEY = {
    "tomhuynh": "tom_huynh", "scottharmon": "scott_harmon", "karenlang": "karen_lang",
    "williamwhetstone": "william_whetstone", "jakefitisemanu": "jake_fitisemanu",
    "cindywood": "cindy_wood", "donchristensen": "don_christensen",
    "larsnordfelt": "lars_nordfelt", "ronbigelow": "ron_bigelow", "stevebuhler": "steve_buhler",
}


def seat_for_contest(office, district):
    """election (office, district) -> the DISTRICT LABEL used as the cross-check key (crosscheck_field
    ='district'). West Valley is MIXED: 4 geographic districts + 2 city-wide at-large seats (each a
    single-winner 'Vote for 1' contest, ballot-labelled just 'At-Large' with no seat number — keying on
    the LABEL lets each year's at-large winner map without a fake seat number; the YEAR already
    disambiguates AL1 from AL2) + a citywide Mayor (who votes)."""
    if office == "Mayor":
        return "Citywide"
    d = district.strip()
    if d in ("1", "2", "3", "4"):
        return "District " + d
    if d == "At-Large":
        return "At-Large"
    return None


REDISTRICT = Redistrict(
    plan_old=PLAN_OLD, plan_new=PLAN_NEW, plan_switch=PLAN_SWITCH,
    ord=REDISTRICT_ORD, adopted=REDISTRICT_ADOPTED,
    districts=["District 1", "District 2", "District 3", "District 4"],
    geom_ref=GEOM_REF, source_url=SRC_URL, data_floor=DATA_FLOOR,
    current_note=(f"CURRENT post-2020-census boundaries. {REDISTRICT_ORD} ('amend Title 2, Chapter 3 of "
                  "the West Valley City Municipal Code, making adjustments in the West Valley City Council "
                  "District Boundaries') adopted " + REDISTRICT_ADOPTED + " on a 7-0 UNANIMOUS roll call "
                  "(motion Harmon 'Option 1' / second Huynh; all six councilmembers + Mayor Lang Yes), built "
                  "on 2020 Census data (each district within 1% of ideal population). WVC has NO council-"
                  "district polygon on disk (the gisportal.wvc-ut.gov FeatureServer was not acquired); the "
                  "authoritative geometry is the SLCo precinct layer geo/precincts.geojson aggregated by "
                  "district via geo/precinct_to_district.csv (derived from the 2023 + 2025 district-contest "
                  "precincts). First used for the 2023 (D1/D3) and 2025 (D2/D4) district elections."),
    prior_adopted_by="prior plan (pre-2022 boundaries)",
    prior_geom_ref="geo/council_districts_pre2022.geojson",
    prior_confidence="low",
    prior_note=("Prior-plan (pre-2022) district boundaries RECONSTRUCTED 2026-07-19 (scripts/build_prior_"
                "district_map.py --city west_valley_city_council --years 2019,2021) by dissolving the current-"
                "vintage SLCo precinct shapes (geo/precincts.geojson) by the pre-2022 precinct->district "
                "assignment read from the 2019 (D1/D3) + 2021 (D2/D4) district-contest precinct rows — the same "
                "derivation used for the CURRENT plan_2022 map. geometry_ref=geo/council_districts_pre2022.geojson. "
                "APPROXIMATE (medium): the OLD assignment applied over CURRENT precinct shapes — faithful where the "
                "county moved only district lines along stable precincts, approximate where precincts were reshaped "
                "in 2022. 64/74 old WVC precinct codes carry current geometry; 10 renumbered/retired codes are HONEST "
                "edge holes (WVC068/070/071/072/073/074/076/077/078/079 — mostly the D2 SW-corner, 6 of D2's 20). "
                "1 conflict: WVC038 appears under 2019 D1 and 2021 D2 -> resolved to D2 (latest). In force for the "
                "2019/2021 elections. effective_start = data floor. Probed the SL County 2020-vintage VistaBallotAreas "
                "layer to firm up the holes; not acquirable as a simple open endpoint (UGRC serves only the current "
                "vintage) -> holes left as honest gaps. "
                "VALIDATION 2026-07-19 (LM-wave follow-up): West Valley publishes NO combined council-district GIS "
                "layer (its AGOL org VuwCBhloG26S6mpc carries only a City Boundary; the SLCo-hosted "
                "West_Valley_City_Council_District_1/District_3/At_Large services are the CURRENT plan only). No "
                "authoritative PRIOR layer exists to validate against. A fragmentation control PROVES precinct "
                "renumbering beyond the known holes: dissolving CURRENT precinct shapes by the CURRENT assignment "
                "yields clean 1-2-piece districts, but this pre-2022 dissolve yields up to 8-piece fragments "
                "(D2=8) -> old WVC codes were renumbered between the SOVC vintage and the current UGRC shapes (the "
                "millcreek defect). Geometry confidence DOWNGRADED medium->low. The district_precincts precinct-CODE "
                "composition stays medium (a faithful SOVC record, geometry-independent). See "
                "scripts/roster_boundary_recon.md. (Also corrects the earlier note that said the pre-2022 map was "
                "'NOT reconstructable' — a partial dissolve exists but is renumbering-corrupted, hence low.)"),
    citywide_rows=[
        ("At-Large", "citywide", "the two at-large councilmembers (AL1 Christensen, AL2 Nordfelt)"),
        ("MAYOR", "citywide", "the separately-elected Mayor (Bigelow -> Lang) — who DOES vote on council motions"),
    ],
    citywide_adopted_by="West Valley City (city-wide seats)",
    citywide_note_template=("{who}: represent(s) the ENTIRE city on every date, unchanged by the 2022 "
                            "redistricting. West Valley's TWO at-large council seats + the Mayor are city-wide "
                            "(only the 4 numbered districts are geographic). geometry_ref = full city extent. "
                            "Unlike West Jordan / South Jordan, the WVC Mayor VOTES on council legislation."),
    precinct_hi_source=("2023", "2025"),   # both current-plan source_years -> all rows high (roster_lib multi-year)
    precinct_hi_note=("post-redistrict precinct->district from the current (post-2020-census) West Valley map — "
                      "the 70 mapped WVC precincts assigned via the 2023 (D1/D3) + 2025 (D2/D4) district-contest "
                      "precinct rows (geo/precinct_to_district.csv; no overlap between districts). Districts only "
                      "— the 2 at-large seats + Mayor are city-wide and have no precinct->district composition. "
                      "(WVC067 has a GIS polygon but no district-race votes -> unmapped sliver, honest gap.)"),
    precinct_med_note="",   # unused — every plan_2022 row shares the one current-map source token
    precinct_prior_note=("Reconstructed pre-2022 precinct->district composition (64/74 WVC precincts present, from "
                         "the 2019 D1/D3 + 2021 D2/D4 SOVC district contests; WVC038 conflict resolved to the 2021 "
                         "D2 assignment; 10 renumbered/retired codes are honest holes, absent here). medium — "
                         "current-vintage precinct shapes. See scripts/roster_boundary_recon.md."),
    # ALL four districts are now in the automated check (2026-07-11). D2 + D3 were formerly excluded
    # because the 2025 D2 ballot spells the winner 'SCOTT L. HARMON' and the 2023 D3 ballot
    # 'WILL WHETSTONE', while the vote record / roster use 'Scott Harmon' / 'William Whetstone' — a
    # name-FORMAT mismatch, NOT a data discrepancy. roster_lib's canon_key winner compare
    # (_winner_matches) resolves both names before comparing, so no per-city exclusion is needed and
    # all four districts RECONCILE.
    crosscheck_districts=("1", "2", "3", "4"),
    precinct_prefix="WVC", geo_seat_prefix="D",
    plan_switch_year="2023", citywide_seats=("AL1", "AL2"),
)

CFG = RosterConfig(
    non_voting_mayor=False,   # WVC's Mayor VOTES — the headline structural fact (verified: 7-member rolls)
    city=CITY, city_dir=CITY_DIR, repo_root=REPO_ROOT, data_floor=DATA_FLOOR,
    geom_ref=GEOM_REF, elections_path=ELECTIONS, cities_db_path=CITIES_DB,
    overrides_path=OVERRIDES, terms_out=TERMS_OUT, districts_out=DISTRICTS_OUT,
    seat_district=SEAT_DISTRICT, name_to_key=NAME_TO_KEY, db_key=DB_KEY,
    seat_order=["D1", "D2", "D3", "D4", "AL1", "AL2", "MAYOR"],
    keep_election_row=lambda r: r["election_type"].strip().lower() == "municipal general",
    contest_key=seat_for_contest, crosscheck_field="district",
    winners_have_district=True,
    elected_events=("elected", "reelected"),
    redistrict=REDISTRICT, precincts_out=PRECINCTS_OUT,
    precinct_map_path=GEO_PRECINCT_MAP, precincts_byprecinct_path=PRECINCTS_BYP_SRC,
    prior_precinct_map_path=os.path.join(CITY_DIR, "geo", "precinct_to_district_pre2022.csv"),
)


# ---------------------------------------------------------------------------
# Precinct SIDECARS RETIRED 2026-07-11. The two per-city adapters (_write_precinct_to_district
# collapsing geo/precinct_to_district.csv's per-row 2023/2025 source_years to a single token, and
# _write_clean_byprecinct dropping suppressed/blank by-precinct rows) are gone: roster_lib now reads
# geo/precinct_to_district.csv and election_results/west_valley_results_by_precinct.csv directly, via
# a multi-year precinct_hi_source (both 2023 & 2025 -> high) and an in-library blank/suppressed vote
# guard. No sidecar files are generated anymore.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Demo queries (West Valley presentation)
# ---------------------------------------------------------------------------
def demo():
    def line(r):
        end = r["end_date"] or "—(serving)"
        return (f"    {r['seat_id']:<6} {r['person_name']:<20} {r['start_date']} -> {end:<12}"
                f" [{r['start_event']}/{r['end_event']}] conf={r['confidence']}")

    print("\n(a) CURRENT council roster + mayor (end_date empty, end_event=serving):")
    for r in roster_lib.load_terms(CFG):
        if not r["end_date"] and r["end_event"] == "serving":
            print(line(r))

    print("\n(b) Roster AS OF 2022-01-10 (during the D3 vacancy — Lang became Mayor, Whetstone not yet appointed):")
    for r in roster_lib.roster_as_of(CFG, "2022-01-10", body="Council"):
        print(line(r))
    for r in roster_lib.roster_as_of(CFG, "2022-01-10", body="Mayor"):
        print(line(r))

    print("\n(c) Roster AS OF 2025-01-15 (during the D4 vacancy — Fitisemanu left, Wood not yet appointed):")
    for r in roster_lib.roster_as_of(CFG, "2025-01-15", body="Council"):
        print(line(r))

    print("\n(d) Address+date -> representatives (via geo/address_to_district.py — 1 district + 2 at-large + Mayor):")
    # A West Valley address -> its District 1-4 member + BOTH at-large members + the (voting) Mayor.
    # City Hall (3600 Constitution Blvd) resolves to a district; we pass a lat/lon fallback so the
    # demo runs OFFLINE (the geocoder needs network; point-in-polygon is offline).
    addr = "3600 S Constitution Blvd, West Valley City, UT 84119"
    for d in ("2026-02-01", "2020-06-01"):
        res = roster_lib.representatives_for_address(CFG, addr, d, latlon=(40.6942, -111.9581))
        who = ", ".join(f"{x['person_name']}({x['seat_id']})" for x in res["reps"])
        loc = (f"District {res['district']} via {res.get('precinct')} "
               f"[{res.get('method')}]") if res.get("district") else f"[{res.get('gap','?')}]"
        print(f"  '{addr}'")
        print(f"    on {d} (plan={res['plan']}): {loc}")
        print(f"    -> your reps: {who or '(none — see gap)'}")

    print("\n(e) Precinct-map cross-check (district_precincts vs election outcomes; districts only — at-large is city-wide):")
    roster_lib.precinct_crosscheck(CFG, verbose=True)


if __name__ == "__main__":
    rows = roster_lib.build(CFG, TENURES)
    n = {c: sum(1 for r in rows if r["confidence"] == c) for c in ("high", "medium", "low")}
    nvac = sum(1 for r in rows if r["start_event"] == "vacated")
    print(f"Wrote {os.path.relpath(TERMS_OUT, CITY_DIR)} "
          f"({len(rows)} tenures incl. {nvac} VACANT: {n['high']} high / {n['medium']} medium / {n['low']} low)")
    print(f"Wrote {os.path.relpath(DISTRICTS_OUT, CITY_DIR)} "
          f"(4 districts x 2 plans + At-Large + Mayor; redistricting {REDISTRICT_ORD})")
    print(f"Wrote {os.path.relpath(PRECINCTS_OUT, CITY_DIR)} "
          f"(plan_2022 precinct map + plan_pre2022 gap rows; districts only)")
    if "--check" in sys.argv:
        print("\nValidation: PASS (no overlaps; sources+confidence present; gap/vacate guards clear; "
              "Mayor VOTES so MAYOR rows correctly carry vote bounds).")
        print("Precinct cross-check:")
        roster_lib.precinct_crosscheck(CFG, verbose=True)
    if "--demo" in sys.argv:
        demo()
