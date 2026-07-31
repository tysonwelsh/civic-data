#!/usr/bin/env python3
"""build_roster.py — rolling council-roster for WEST JORDAN (a slowly-changing-dimension /
interval table of who holds each council + mayor seat over time). West Jordan is a **MIXED
Council-Mayor city**: **4 geographic council districts** (D1..D4) + **3 city-wide AT-LARGE seats**
(AL1..AL3) + a **separately-elected strong Mayor who does NOT vote** on council motions (adopted
at the 2019 election — West Jordan's first strong-mayor cycle; the Mayor presides/appoints the
executive but casts no council vote). A full council roll call tops out at **7** (never 8). Council
votes exist from **2020** (named roll-calls on substantive items; routine/consent business often
passes without a named roll), while the Salt Lake County election record runs **2019+** (the first
strong-mayor election). The 4 districts were **redrawn after the 2020 Census** (Resolution No.
22-011, adopted 2022-04-13).

THIN DRIVER: this file holds only West-Jordan-specific DATA (the curated TENURES, the name maps,
the 2022-redistricting facts + prose) + config; all generic mechanics live in
../../scripts/roster_lib.py (canon_key, election/vote-bounds/override reconciliation, end-date
chaining + VACANT insertion, validation incl. the gap/vacate guards, the CSV writers, and the
as-of / address / precinct-crosscheck query helpers). The pure-district reference templates are
south_jordan_city_council/ and taylorsville_city_council/ (both: 5 districts + non-voting mayor +
2022 redistricting + precinct/address join); West Jordan differs by ADDING the 3 at-large seats,
which are validated through the election cross-check (not the precinct cross-check).

DERIVED LAYER — regenerable, never hand-edited. Canonical inputs:
  1. election_results/west_jordan_results_by_candidate.csv (winners -> `elected`/`reelected`; 2019+)
  2. cities.db  role table (city='west_jordan', body='Council')  (observed vote bounds)
  3. meeting_minutes/minutes/**  (oath dates, the redistricting resolution, the 2023 D2 vacancy)
  4. roster/roster_overrides.csv  (hand corrections; applied LAST, win ties)

Outputs (idempotent — re-running reproduces them byte-for-byte):
  roster/council_terms.csv        one row per seat-tenure (4 district + 3 at-large + MAYOR)
  roster/district_versions.csv    boundary interval table — REAL 4 districts x 2 plans + At-Large + Mayor
  roster/district_precincts.csv   versioned precinct->district composition (plan-scoped, districts only)
  (The two precinct SIDECARS were RETIRED 2026-07-11 — roster_lib now reads the canonical
   geo/precinct_to_district.csv + election_results/*_by_precinct.csv directly: a multi-year
   precinct_hi_source tuple keeps every current-plan row `high`, and a built-in blank/suppressed
   vote guard replaces the defensive by-precinct copy.)

Usage:
  python3 roster/build_roster.py            # regenerate the CSVs
  python3 roster/build_roster.py --demo     # regenerate + print the demo queries
  python3 roster/build_roster.py --check    # regenerate + validations + precinct cross-check

Cardinal rule (repo CLAUDE.md): NEVER fabricate. Unknown seat-holder / boundary / date ->
explicit VACANT/gap + confidence + a note, never a guess.

Provenance / confidence model (West Jordan):
  high   = an in-file election win (2019/2021/2023/2025) seated at a documented first-of-year
           meeting/oath and corroborated by the cities.db named-vote record, OR the fully-
           documented 2023 D2 resignation->appointment chain (Res. 23-070).
  medium = an AT-LARGE HOLDOVER serving at the 2020 data floor whose SEATING election predates the
           2019 election floor (pre-strong-mayor era) — service is vote-documented from 2020-01-08
           but the term's origin is below the floor (the win is not in the data; only two rows,
           Whitelock AL1 + Lamb AL3).
  low    = genuinely unknown / not-acquired (flagged) — NONE remain: the prior-plan
           district/precinct rows were RECONSTRUCTED to `medium` 2026-07-11 (approximate;
           see the Redistrict prior_note / scripts/roster_boundary_recon.md).

West Jordan seat model (STABLE ids — a redistricting redraws boundaries, it does NOT renumber
seats):
  D1..D4  four geographic district seats
  AL1..AL3  three city-wide AT-LARGE seats  (ANALYTICAL ids — see note below)
  MAYOR    separately-elected strong Mayor (does NOT vote)
Staggered 4-year cycles (odd calendar years), as the county SOVC actually records them:
  A  Mayor + D1 + D2 + D3 + D4         elected 2019 / 2023  -> terms seated Jan 2020 / 2024
  B  At-Large (grouped Vote-for-3)      elected 2021 / 2025  -> terms seated Jan 2022 / 2026

AT-LARGE seat ids are an ANALYTICAL construct. The three at-large seats are legally
INTERCHANGEABLE and are filled TOGETHER in one grouped "Vote for 3" field (top-3 win all three) —
there is no ballot seat number. AL1/AL2/AL3 are assigned to MAXIMIZE person-continuity so the
chains read cleanly: AL1 = Kayleen Whitelock throughout (she serves continuously 2020->present);
AL2 = Green(2019/2021) -> Harris(2025); AL3 = Lamb(holdover) -> Bloom(2021) -> Wignall(2025). The
Green->Harris and Bloom->Wignall pairings are arbitrary (any assignment yields the same clean
cycle-boundary handoffs); the election cross-check keys on the district LABEL ("At-Large"), not the
analytical seat id, so it is agnostic to which winner lands on which AL id.

KNOWN nuances handled honestly (never fabricated around):
  * NON-VOTING STRONG MAYOR. Dirk Burton (first strong mayor; the form was adopted at the 2019
    election) presides and appoints the executive staff but does NOT vote on council motions. He is
    ABSENT from every cities.db council role and from every vote roll (verified: 0 council meetings
    exceed 7 distinct voters). Verbatim, 2025-02-25 (Ord. 25-03 annexation): the minutes list Mayor
    Dirk Burton under STAFF (not COUNCIL) and the roll names exactly the seven councilmembers -
    "YES: Zach Jacob, Chad Lamb, Bob Bedore, Pamela Bloom, Kelvin Green, Kent Shelton, Kayleen
    Whitelock ... The motion passed 7-0." `non_voting_mayor=True` empties every MAYOR-body vote-bound
    and dirk_burton is not in DB_KEY.
  * TWO AT-LARGE HOLDOVERS at the 2020 floor. In Jan 2020 the three at-large seats were held by
    Green (won the 2019 single at-large seat), Whitelock, and Lamb (Mayor Pro Tem) — the latter two
    seated by a pre-2019 (pre-strong-mayor) at-large election below the election floor. Their SERVICE
    is fully vote-documented from 2020-01-08, but the term origin is below the floor -> medium, no
    fabricated seating date/election.
  * THE 2019 SINGLE-SEAT AT-LARGE (transition). 2019 was the first strong-mayor election; the county
    SOVC shows a SINGLE at-large seat that year (Vote for 1, won by Green), not the grouped Vote-for-3
    field seen from 2021 on. Green's 2019 at-large term ran ~2 years (2020->2022) to sync all three
    at-large seats onto the consolidated 2021/2025 cycle; he was re-elected to a full term in 2021.
  * THE IN-WINDOW D2 VACANCY (the headline documented case). Melissa Worthen (D2, elected 2019) was
    honored as "Outgoing District 2 Council Member" on 2020-... 2023-10-25 (her last meeting / last
    cities.db vote) and left mid-term. At a 2023-11-29 SPECIAL meeting the Council filled the mid-term
    D2 vacancy by **Resolution No. 23-070**, appointing **Robert (Rob) Bennett** (selected over Bob
    Bedore by a documented coin toss after a tied electronic vote; oath administered that same night).
    Bedore had ALREADY won the D2 seat at the 2023 general (Nov) but could not be seated until January,
    so Bennett filled the ~6-week interim. This yields an explicit VACANT interval D2 [2023-10-26,
    2023-11-29). Bedore was seated 2024-01-10.
  * ONE PERSON, TWO SEATS (non-contiguous). Chad Lamb held an AT-LARGE seat 2020->2022 (Mayor Pro
    Tem; lost the 2021 grouped at-large race, 4th) then won **D1** in 2023 (seated 2024-01-10). One
    chad_lamb key spans both; the seats (AL3, D1) do not overlap. (Also: Kelvin Green won the single
    at-large 2019 then the grouped at-large 2021 — one continuous AL2 chain.)
  * SPARSE-ROLL vote naming. West Jordan records named roll-calls mainly on substantive items;
    routine/consent items often pass without a named roll, so a member's first/last NAMED vote can
    lag/precede real service. The authoritative interval is always start_date/end_date; the vote
    bounds are now CLAMPED to each tenure's own [start,end) window (roster_lib.clamp_vote_bounds).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.dirname(HERE)                 # west_jordan_city_council/
REPO_ROOT = os.path.dirname(CITY_DIR)            # civic-data/
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import roster_lib
from roster_lib import RosterConfig, Redistrict

ELECTIONS = os.path.join(CITY_DIR, "election_results", "west_jordan_results_by_candidate.csv")
PRECINCTS_BYP_SRC = os.path.join(CITY_DIR, "election_results", "west_jordan_results_by_precinct.csv")
GEO_PRECINCT_MAP = os.path.join(CITY_DIR, "geo", "precinct_to_district.csv")
CITIES_DB = os.path.join(REPO_ROOT, "cities.db")
OVERRIDES = os.path.join(HERE, "roster_overrides.csv")
TERMS_OUT = os.path.join(HERE, "council_terms.csv")
DISTRICTS_OUT = os.path.join(HERE, "district_versions.csv")
PRECINCTS_OUT = os.path.join(HERE, "district_precincts.csv")

CITY = "west_jordan"
DATA_FLOOR = "2020-01-01"            # data floor (city standard: 2020)
GEOM_REF = "geo/council_districts.geojson"

# The real redistricting event (spot-checked against source minutes 2022-04-13):
#   Resolution No. 22-011, "adopting new City Council Districts for the City of West Jordan."
#   Adopted 2022-04-13 (Business Item 8a) on a 5-0 roll call (motion Worthen / second Green; Bloom
#   stepped out + McConnehey absent): Council Chair Whitelock, Vice Chair Green, Jacob, Pack, Worthen
#   all Yes. (An earlier Ordinance 21-44, 2021-11-16, amended the redistricting CODE Title 1 Ch.15;
#   Res. 22-011 adopts the actual MAP.) First used for the 2023 (D1..D4) elections; 2019 used the
#   prior lines. West Jordan redistricts by RESOLUTION (like Taylorsville/SLC, unlike South Jordan).
REDISTRICT_ORD = "Resolution 22-011"
REDISTRICT_ADOPTED = "2022-04-13"
PLAN_OLD = "plan_pre2022"   # pre-2022 boundaries, in force through the 2019 elections (RECONSTRUCTED 2026-07-11, medium)
PLAN_NEW = "plan_2022"      # Resolution 22-011; in force for the 2023 elections onward
PLAN_SWITCH = "2022-04-13"  # documented adoption of the 2020-census boundaries
SRC_URL = ("meeting_minutes/minutes/2022/2022-04-11/2022-04-13_city-council-regular-meeting.md "
           "(Business Item 8a: Resolution No. 22-011 adopting new City Council Districts, passed 5-0)")

SEAT_DISTRICT = {
    "D1": "District 1", "D2": "District 2", "D3": "District 3", "D4": "District 4",
    "AL1": "At-Large", "AL2": "At-Large", "AL3": "At-Large", "MAYOR": "Citywide",
}

# ---------------------------------------------------------------------------
# LAYER 1-3 (reconciled). Each tenure anchored to a cited source. Ordered by seat.
#   Documented seating dates: 2020-01-08 (first documented 2020 council meeting; oath of office
#   reported — 2019-cycle members + the two at-large holdovers), 2022-01-12 (first documented 2022
#   meeting; 2021 at-large seated), 2024-01-10 (first documented 2024 meeting; the "City Council Oath
#   of Office Ceremony" was the prior week — 2023-cycle), 2026-01-13 (first documented 2026 meeting;
#   oath ceremonies "in the last week" — 2025 at-large), plus 2023-11-29 (D2 appointment, Res. 23-070).
# ---------------------------------------------------------------------------
TENURES = [
    # ============================ D1 (A cycle: 2019 / 2023) ============================
    dict(body="Council", seat_id="D1", person_name="Christopher M. McConnehey", person_key="chris_mcconnehey",
         start_date="2020-01-08", start_event="elected", election_year="2019", end_event="did-not-run",
         confidence="high",
         sources="election:2019 (District 1 winner, def. Marilyn Richards 50.68% — a +54-vote squeaker); "
                 "minutes:present 2020-01-08 (first documented 2020 council meeting; oath of office reported); "
                 "votes:2020-01-08..2023-12-20 (cities.db, D1)",
         note="Elected D1 2019 (first strong-mayor cycle). Did not seek re-election in D1 2023 -> Lamb won. "
              "(Ran for an at-large seat in 2025 as 'Chris McConnehey' and lost, 5th of 6 — a later, different "
              "contest; not this D1 term.) Clean cycle-boundary handoff."),
    dict(body="Council", seat_id="D1", person_name="Chad Lamb", person_key="chad_lamb",
         start_date="2024-01-10", start_event="elected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 1 winner, def. Rulon Green 64.54%); minutes:2024-01-10 (first documented "
                 "2024 meeting; 'City Council Oath of Office Ceremony' held the prior week); votes:2024-01-10.."
                 "2026-05-12 (cities.db, D1)",
         note="Elected D1 2023 (first D1 term on the plan_2022 lines; seated 2024-01-10). SAME PERSON as the "
              "AL3 at-large HOLDOVER (2020-2022) below — non-contiguous (he lost the 2021 grouped at-large race, "
              "then won D1 2023). first_vote/last_vote are CLAMPED to this D1 tenure's window (2024-01-10.."
              "2026-05-12); his earlier AL3 holdover row carries its own 2020-01-08..2021-12-15 bounds. "
              "Currently serving (Council Chair 2025; Jacob chaired 2024)."),

    # ============================ D2 (A cycle + the 2023 mid-term vacancy) ============================
    dict(body="Council", seat_id="D2", person_name="Melissa Worthen", person_key="melissa_worthen",
         start_date="2020-01-08", start_event="elected", election_year="2019", end_event="resigned",
         confidence="high",
         vacate_date="2023-10-26", vacate_confidence="high",  # VACANT begins the day AFTER her last day served (2023-10-25)
         vacate_source="minutes:2023-10-25 (special recognition, 'Outgoing District 2 Council Member' — Council "
                       "Office Director recognized 'Council Member Melissa Worthen for her service on the City "
                       "Council for the past four years ... deeply missed ... her new adventures'; her last "
                       "cities.db D2 vote is 2023-10-25); minutes:2023-11-29 SPECIAL ('FILLING MID-TERM VACANCY "
                       "FOR DISTRICT TWO')",
         sources="election:2019 (District 2 winner, def. John Price 81.92%); minutes:present 2020-01-08; "
                 "votes:2020-01-08..2023-10-25 (cities.db, D2)",
         note="Elected D2 2019. LEFT MID-TERM: honored as 'Outgoing District 2 Council Member' on 2023-10-25 (her "
              "last meeting/vote) and departed before her term's Jan-2024 end -> explicit VACANT interval D2 "
              "[2023-10-26, 2023-11-29). Documented in-window departure."),
    dict(body="Council", seat_id="D2", person_name="Robert Bennett", person_key="rob_bennett",
         start_date="2023-11-29", start_event="appointed", election_year="", end_event="succeeded-by-elected",
         confidence="high",
         sources="minutes:2023-11-29 SPECIAL ('FILLING MID-TERM VACANCY FOR DISTRICT TWO'; Resolution No. 23-070 "
                 "'appointing Robert Bennett to fill the mid-term vacancy in West Jordan City Council District 2'; "
                 "selected over Bob Bedore by a documented COIN TOSS after a tied electronic vote; 'City Recorder "
                 "Tangee Sloan administered the Oath of Office to Robert Bennett'); votes:2023-11-29..2023-12-20 "
                 "(cities.db, D2, 5 votes)",
         note="APPOINTED to the D2 vacancy 2023-11-29 by Resolution No. 23-070 (oath same night). Bedore had ALREADY "
              "won the D2 seat at the 2023 general (Nov) but could not be seated until January, so Bennett filled the "
              "~6-week interim; his appointment ends when the elected Bedore is seated 2024-01-10. (Bennett later ran "
              "for an at-large seat in 2025 and lost — a different, later contest.)"),
    dict(body="Council", seat_id="D2", person_name="Bob Bedore", person_key="bob_bedore",
         start_date="2024-01-10", start_event="elected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 2 winner, def. Gary Leany 54.17%); minutes:2024-01-10 (first documented "
                 "2024 meeting; oath ceremony the prior week; present as 'Bob Bedore'); votes:2024-01-10..2026-05-12 "
                 "(cities.db, D2)",
         note="Elected D2 2023 (first D2 term on the plan_2022 lines; seated 2024-01-10 after the ~6-week Bennett "
              "interim appointment). Currently serving (Council Chair 2026)."),

    # ============================ D3 (A cycle: 2019 / 2023) — continuous Jacob ============================
    dict(body="Council", seat_id="D3", person_name="Zach Jacob", person_key="zach_jacob",
         start_date="2020-01-08", start_event="elected", election_year="2019", end_event="reelected",
         confidence="high",
         sources="election:2019 (District 3 winner, def. Amy L Martz 57.47%); minutes:present 2020-01-08; "
                 "votes:2020-01-08.. (cities.db, D3)",
         note="Elected D3 2019 (last D3 term on the OLD plan_pre2022 lines). Re-elected 2023 -> continuous service."),
    dict(body="Council", seat_id="D3", person_name="Zach Jacob", person_key="zach_jacob",
         start_date="2024-01-10", start_event="reelected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 3 winner, def. Sterling Morris 65.81%); minutes:2024-01-10 (first documented "
                 "2024 meeting; Council Chair for 2024); votes:continuous through 2026-05-12 (cities.db, D3)",
         note="Re-elected D3 2023 (first D3 term on the plan_2022 lines; seated 2024-01-10). Currently serving."),

    # ============================ D4 (A cycle: 2019 / 2023) ============================
    dict(body="Council", seat_id="D4", person_name="David Pack", person_key="david_pack",
         start_date="2020-01-08", start_event="elected", election_year="2019", end_event="lost",
         confidence="high",
         sources="election:2019 (District 4 winner, as 'David Pack', def. Pamela Berry 57.19%); election:2023 "
                 "(LOST D4 to Kent Shelton, rank 2, as 'David F. Pack'); minutes:present 2020-01-08; "
                 "votes:2020-01-08..2023-12-20 (cities.db, D4)",
         note="Elected D4 2019. LOST re-election in 2023 to Kent Shelton (rank 2) -> left office Jan 2024. Clean "
              "cycle-boundary handoff (no vacancy)."),
    dict(body="Council", seat_id="D4", person_name="Kent Shelton", person_key="kent_shelton",
         start_date="2024-01-10", start_event="elected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 4 winner, def. incumbent David F. Pack 57.19%); minutes:2024-01-10 (first "
                 "documented 2024 meeting; oath ceremony the prior week); votes:2024-01-10..2026-05-12 (cities.db, D4)",
         note="Elected D4 2023 (first D4 term on the plan_2022 lines; seated 2024-01-10). Previously served on the "
              "West Jordan Planning Commission (2020-2023; present at the 2020-01-07 PC meeting per the 2026-07-17 "
              "citysite recovery — earlier than the 2022 audited-PC floor) before this council term — one person, "
              "two bodies (see the db person/role tables). Currently serving."),

    # ============================ AL1 (At-Large) — Whitelock, continuous ============================
    dict(body="Council", seat_id="AL1", person_name="Kayleen Whitelock", person_key="kayleen_whitelock",
         start_date="2020-01-08", start_event="in-office", election_year="", end_event="reelected",
         confidence="medium",
         sources="minutes:present 2020-01-08 (first documented 2020 council meeting; seconded motions as "
                 "'Councilmember Whitelock'); votes:2020-01-08.. (cities.db, at-large)",
         note="AT-LARGE HOLDOVER at the 2020 data floor: her SEATING at-large election predates the 2019 strong-"
              "mayor election floor (pre-strong-mayor era) and is NOT in the loaded data -> medium (service is "
              "vote-documented from 2020-01-08; the term origin is below the floor, no fabricated seating date). "
              "Re-elected in the 2021 grouped at-large race (see next). AL1 is an analytical id (see header); "
              "Whitelock is assigned AL1 throughout because she serves continuously to present. Council Chair 2022."),
    dict(body="Council", seat_id="AL1", person_name="Kayleen Whitelock", person_key="kayleen_whitelock",
         start_date="2022-01-12", start_event="reelected", election_year="2021", end_event="reelected",
         confidence="high",
         sources="election:2021 (At-Large grouped 'Vote for 3' — rank 1 of 6, 22.24%, a WINNER); minutes:present "
                 "2022-01-12 (first documented 2022 council meeting); votes:continuous (cities.db, at-large)",
         note="Re-elected at-large 2021 (top of the grouped Vote-for-3 field). Seated 2022-01-12. Re-elected 2025."),
    dict(body="Council", seat_id="AL1", person_name="Kayleen Whitelock", person_key="kayleen_whitelock",
         start_date="2026-01-13", start_event="reelected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (At-Large grouped 'Vote for 3' — rank 1 of 6, 17.96%, a WINNER); minutes:present "
                 "2026-01-13 (first documented 2026 council meeting; plain member — Wignall is the 2026 Vice Chair); "
                 "votes:continuous through 2026-05-12",
         note="Re-elected at-large 2025 (first at-large term on the current cycle's plan). Currently serving "
              "(Vice Chair 2025; a plain member in 2026)."),

    # ============================ AL2 (At-Large) — Green(2019/2021) -> Harris(2025) ============================
    dict(body="Council", seat_id="AL2", person_name="Kelvin Green", person_key="kelvin_green",
         start_date="2020-01-08", start_event="elected", election_year="2019", end_event="reelected",
         confidence="high",
         sources="election:2019 (At-Large SINGLE-seat 'Vote for 1' winner, 46.77%, def. Mikey Smith); minutes:"
                 "present 2020-01-08 (Vice Chair Green in later 2020+ minutes); votes:2020-01-08.. (cities.db, at-large)",
         note="Won the 2019 SINGLE at-large seat (2019 was West Jordan's first strong-mayor election; the county "
              "SOVC shows one at-large seat that year, Vote for 1, not the grouped Vote-for-3 field seen from 2021). "
              "This 2019 at-large term ran ~2 years (2020->2022) to sync all three at-large seats onto the "
              "consolidated 2021/2025 cycle; he was re-elected to a full term in 2021 (see next)."),
    dict(body="Council", seat_id="AL2", person_name="Kelvin Green", person_key="kelvin_green",
         start_date="2022-01-12", start_event="reelected", election_year="2021", end_event="did-not-run",
         confidence="high",
         sources="election:2021 (At-Large grouped 'Vote for 3' — rank 2 of 6, 19.85%, a WINNER); minutes:present "
                 "2022-01-12 (Vice-Chair Green); votes:2022-01-12..2025-12-16 (cities.db, at-large)",
         note="Re-elected at-large 2021 (grouped Vote-for-3). Did not seek re-election in 2025 -> Harris won. Left "
              "office Jan 2026 (last cities.db vote 2025-12-16). Clean cycle-boundary handoff."),
    dict(body="Council", seat_id="AL2", person_name="Annette Harris", person_key="annette_harris",
         start_date="2026-01-13", start_event="elected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (At-Large grouped 'Vote for 3' — rank 2 of 6, 17.67%, a WINNER; ext. cross-check: "
                 "West Jordan City newsroom Dec-2025 confirms Harris/Whitelock/Wignall); minutes:present 2026-01-13; "
                 "votes:2026-01-13..2026-05-12 (cities.db, at-large)",
         note="Elected at-large 2025 (grouped Vote-for-3). Seated 2026-01-13 (oath ceremonies the prior week). "
              "Assigned AL2 as a clean cycle-boundary handoff from Green (analytical id — see header). Serving."),

    # ============================ AL3 (At-Large) — Lamb(holdover) -> Bloom(2021) -> Wignall(2025) ============================
    dict(body="Council", seat_id="AL3", person_name="Chad Lamb", person_key="chad_lamb",
         start_date="2020-01-08", start_event="in-office", election_year="", end_event="lost",
         confidence="medium",
         sources="minutes:2020-01-08 (present as 'Mayor Pro Tem Chad Lamb', chaired the first 2020 meeting); "
                 "votes:2020-01-08..2021.. (cities.db, at-large); election:2021 (LOST the grouped at-large race, rank 4)",
         note="AT-LARGE HOLDOVER at the 2020 data floor (Mayor Pro Tem in early 2020): his SEATING at-large election "
              "predates the 2019 strong-mayor floor (pre-strong-mayor era) and is NOT in the loaded data -> medium "
              "(service is vote-documented from 2020-01-08; term origin below the floor). LOST the 2021 grouped "
              "at-large race (4th of 6, 18.41%) -> left this seat Jan 2022. SAME PERSON as D1 Lamb (elected 2023) — "
              "non-contiguous; the vote bounds on this row are CLAMPED to the AL3 window (2020-01-08..2021-12-15), and "
              "his later D1 tenure carries its own bounds. AL3 is an analytical id."),
    dict(body="Council", seat_id="AL3", person_name="Pamela Bloom", person_key="pamela_bloom",
         start_date="2022-01-12", start_event="elected", election_year="2021", end_event="did-not-run",
         confidence="high",
         sources="election:2021 (At-Large grouped 'Vote for 3' — rank 3 of 6, 19.70%, the seat-3 WINNER, +326 over "
                 "Chad Lamb; ext. cross-check: West Jordan Journal 'two incumbents, one newcomer'); minutes:present "
                 "2022-01-12; votes:2022-01-12..2025-12-16 (cities.db, at-large)",
         note="Elected at-large 2021 (won the third/last at-large seat, unseating holdover Lamb). Did not appear in "
              "the 2025 at-large field -> did not run. Left office Jan 2026 (last cities.db vote 2025-12-16). Assigned "
              "AL3 as a clean handoff from Lamb (analytical id — see header)."),
    dict(body="Council", seat_id="AL3", person_name="Jessica Wignall", person_key="jessica_wignall",
         start_date="2026-01-13", start_event="elected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (At-Large grouped 'Vote for 3' — rank 3 of 6, 16.65%, the seat-3 WINNER, +79 over "
                 "Sergio Sotelo; ext. cross-check: West Jordan City newsroom Dec-2025); minutes:present 2026-01-13 "
                 "(Vice Chair Jessica Wignall); votes:2026-01-13..2026-05-12 (cities.db, at-large)",
         note="Elected at-large 2025 (won the third/last at-large seat by 79 votes over Sotelo). Seated 2026-01-13. "
              "Assigned AL3 as a clean cycle-boundary handoff from Bloom (analytical id — see header). Serving "
              "(Vice Chair 2026)."),

    # ============================ MAYOR (strong mayor — does NOT vote) ============================
    dict(body="Mayor", seat_id="MAYOR", person_name="Dirk Burton", person_key="dirk_burton",
         start_date="2020-01-08", start_event="elected", election_year="2019", end_event="reelected",
         confidence="high",
         sources="election:2019 (Mayor winner, def. incumbent Jim Riding 52.13% — West Jordan's FIRST strong-mayor "
                 "election); minutes:presiding/appointing 2020-01-08+ (as 'Mayor Dirk Burton'; e.g. selected the "
                 "Police Chief); does NOT appear in any vote roll",
         note="Elected the FIRST strong Mayor 2019 (the strong-mayor form was adopted at the 2019 election). "
              "Presides and appoints the executive staff but does NOT vote on council motions (MAYOR vote bounds "
              "emptied by non_voting_mayor; dirk_burton is absent from cities.db). Re-elected 2023."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Dirk Burton", person_key="dirk_burton",
         start_date="2024-01-10", start_event="reelected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (Mayor winner, def. Kayleen Whitelock 60.47%); minutes:presiding 2024-01-10+ (listed "
                 "under STAFF, not COUNCIL; e.g. 2025-02-25 the 7-0 roll names only the councilmembers)",
         note="Re-elected Mayor 2023. Continues to preside; does not vote on council motions (MAYOR vote bounds "
              "empty). Currently serving."),
]

# canonical UPPER-CASE election name token -> our person_key. GREEN appears as both a WINNER (Kelvin
# Green, at-large) and a 2023 D1 LOSER (Rulon Green) — but only WINNERS pass through canon_key in the
# cross-check, and the only at-large/winner GREEN is Kelvin, so GREEN -> kelvin_green is unambiguous.
# No two WEST JORDAN general winners share a surname, so no disambiguators are needed.
NAME_TO_KEY = {
    "MCCONNEHEY": "chris_mcconnehey", "WORTHEN": "melissa_worthen", "JACOB": "zach_jacob",
    "PACK": "david_pack", "LAMB": "chad_lamb", "BEDORE": "bob_bedore", "SHELTON": "kent_shelton",
    "WHITELOCK": "kayleen_whitelock", "GREEN": "kelvin_green", "BLOOM": "pamela_bloom",
    "HARRIS": "annette_harris", "WIGNALL": "jessica_wignall", "BURTON": "dirk_burton",
    "BENNETT": "rob_bennett",
}

# cities.db person.name_key -> our person_key (council voters only). dirk_burton is DELIBERATELY
# EXCLUDED — he is the non-voting strong Mayor and is absent from the cities.db person table.
DB_KEY = {
    "chrismcconnehey": "chris_mcconnehey", "melissaworthen": "melissa_worthen",
    "zachjacob": "zach_jacob", "davidpack": "david_pack", "chadlamb": "chad_lamb",
    "bobbedore": "bob_bedore", "kentshelton": "kent_shelton",
    "kayleenwhitelock": "kayleen_whitelock", "kelvingreen": "kelvin_green",
    "pamelabloom": "pamela_bloom", "annetteharris": "annette_harris",
    "jessicawignall": "jessica_wignall", "robbennett": "rob_bennett",
}


def seat_for_contest(office, district):
    """election (office, district) -> the DISTRICT LABEL used as the cross-check key (crosscheck_field
    ='district'). West Jordan is MIXED: 4 geographic districts + 3 city-wide at-large seats (a grouped
    Vote-for-3, so a single 'At-Large' contest seats three interchangeable AL ids — keying on the
    LABEL lets all three winners map without a fake seat number) + a citywide strong Mayor."""
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
    current_note=(f"CURRENT post-2020-census boundaries. {REDISTRICT_ORD} ('adopting new City Council "
                  "Districts for the City of West Jordan') adopted " + REDISTRICT_ADOPTED + " on a 5-0 roll "
                  "call (motion Worthen / second Green; Bloom + McConnehey absent): Whitelock, Green, Jacob, "
                  "Pack, Worthen all Yes. geometry_ref is the city's authoritative 4-district GIS layer in "
                  "geo/council_districts.geojson (ArcGIS Council_Districts FeatureServer; agrees with the "
                  "2023 election-derived precinct map on 86% of shared precincts vs 69% for 2019 -> current "
                  "vintage); precinct->district in geo/precinct_to_district.csv. First used for the 2023 "
                  "district elections."),
    prior_adopted_by="prior plan (pre-2022 boundaries)",
    prior_geom_ref="geo/council_districts_pre2022.geojson",
    prior_confidence="low",
    prior_note=("Prior-plan (pre-2022) district boundaries RECONSTRUCTED 2026-07-11 by dissolving current-vintage "
                "precinct shapes by the pre-2022 (2012-cycle) precinct->district assignment (geometry_ref = "
                "geo/council_districts_pre2022.geojson; all 68 WJD precincts present, 0 holes, 0 conflicts). "
                "In force through the 2019 elections. effective_start = data floor. "
                "VALIDATION 2026-07-19 (LM-wave follow-up): probed West Jordan's own ArcGIS org "
                "(services1.arcgis.com/yznraL2FyB2Sm732) — it publishes NO pre-2022 boundary layer; "
                "Council_Districts / Council_Districts_22 / WJC_Council_2025 are ALL the current 2022+ plan "
                "(87-99% centroid-agree with the current precinct assignment, only 59-69% with the pre-2022 "
                "assignment). A fragmentation control PROVES precinct renumbering: dissolving CURRENT precinct "
                "shapes by the CURRENT assignment yields clean 1-2-piece districts, but this pre-2022 dissolve "
                "yields 3-5-piece fragments -> old WJD codes were partially renumbered between the 2019 SOVC "
                "vintage and the current UGRC precinct shapes (the same millcreek defect, milder here). No "
                "authoritative prior layer exists to replace it -> geometry confidence DOWNGRADED medium->low. "
                "The district_precincts precinct-CODE composition stays medium (a faithful SOVC record of which "
                "old code voted in which district, geometry-independent). See scripts/roster_boundary_recon.md."),
    citywide_rows=[
        ("At-Large", "citywide", "the three at-large councilmembers (AL1 Whitelock, AL2 Green->Harris, AL3 "
                                 "Bloom->Wignall)"),
        ("MAYOR", "citywide", "the separately-elected strong Mayor Dirk Burton"),
    ],
    citywide_adopted_by="West Jordan City (city-wide seats)",
    citywide_note_template=("{who}: represent(s) the ENTIRE city on every date, unchanged by the 2022 "
                            "redistricting. West Jordan's THREE at-large council seats + the Mayor are city-wide "
                            "(only the 4 numbered districts are geographic). geometry_ref = full city extent. "
                            "The Mayor does not vote on council legislation."),
    precinct_hi_source=("2023", "gis"),   # BOTH current-plan source_year values in geo/precinct_to_district.csv
                                          # (2023: 92 rows, gis: 4 rows) earn confidence=high — no collapse sidecar
    precinct_hi_note=("post-redistrict precinct->district from the current (post-2020-census) West Jordan map "
                      "— the 96 WJD precincts assigned via the city Council_Districts GIS layer + the 2023 "
                      "district-contest precinct rows (geo/precinct_to_district.csv; 0 splits). Districts only "
                      "— the 3 at-large seats + Mayor are city-wide and have no precinct->district composition."),
    precinct_med_note="",   # unused — every plan_2022 row shares the one current-map source token
    precinct_prior_note=("Reconstructed pre-2022 (2012-cycle) precinct->district composition (68/68 WJD precincts, "
                         "from the pre-2022 SOVC district contests); medium — current-vintage precinct shapes. "
                         "See scripts/roster_boundary_recon.md."),
    crosscheck_districts=("1", "2", "3", "4"),   # the 4 geographic districts (at-large is not precinct-scoped)
    precinct_prefix="WJD", geo_seat_prefix="D",
    plan_switch_year="2023", citywide_seats=("AL1", "AL2", "AL3"),
)

CFG = RosterConfig(
    non_voting_mayor=True,
    city=CITY, city_dir=CITY_DIR, repo_root=REPO_ROOT, data_floor=DATA_FLOOR,
    geom_ref=GEOM_REF, elections_path=ELECTIONS, cities_db_path=CITIES_DB,
    overrides_path=OVERRIDES, terms_out=TERMS_OUT, districts_out=DISTRICTS_OUT,
    seat_district=SEAT_DISTRICT, name_to_key=NAME_TO_KEY, db_key=DB_KEY,
    seat_order=["D1", "D2", "D3", "D4", "AL1", "AL2", "AL3", "MAYOR"],
    keep_election_row=lambda r: r["election_type"].strip().lower() == "municipal general",
    contest_key=seat_for_contest, crosscheck_field="district",
    winners_have_district=True,
    elected_events=("elected", "reelected"),
    redistrict=REDISTRICT, precincts_out=PRECINCTS_OUT,
    precinct_map_path=GEO_PRECINCT_MAP, precincts_byprecinct_path=PRECINCTS_BYP_SRC,
    prior_precinct_map_path=os.path.join(CITY_DIR, "geo", "precinct_to_district_pre2022.csv"),
)


# ---------------------------------------------------------------------------
# Demo queries (West Jordan presentation)
# ---------------------------------------------------------------------------
def demo():
    def line(r):
        end = r["end_date"] or "—(serving)"
        return (f"    {r['seat_id']:<6} {r['person_name']:<26} {r['start_date']} -> {end:<12}"
                f" [{r['start_event']}/{r['end_event']}] conf={r['confidence']}")

    print("\n(a) CURRENT council roster + mayor (end_date empty, end_event=serving):")
    for r in roster_lib.load_terms(CFG):
        if not r["end_date"] and r["end_event"] == "serving":
            print(line(r))

    print("\n(b) Roster AS OF 2023-11-15 (during the D2 vacancy — Worthen left, Bennett not yet appointed):")
    for r in roster_lib.roster_as_of(CFG, "2023-11-15", body="Council"):
        print(line(r))
    for r in roster_lib.roster_as_of(CFG, "2023-11-15", body="Mayor"):
        print(line(r))

    print("\n(c) Address+date -> representatives (via geo/address_to_district.py — 1 district + 3 at-large + Mayor):")
    # A West Jordan address -> its District 1-4 member + all THREE at-large members + the (non-voting)
    # Mayor. City Hall (8000 S Redwood Rd) resolves to a district; we pass a lat/lon fallback so the
    # demo runs OFFLINE (the geocoder needs network; point-in-polygon is offline).
    addr = "8000 S Redwood Rd, West Jordan, UT 84088"
    for d in ("2026-02-01", "2020-06-01"):
        res = roster_lib.representatives_for_address(CFG, addr, d, latlon=(40.6097, -111.9391))
        who = ", ".join(f"{x['person_name']}({x['seat_id']})" for x in res["reps"])
        loc = (f"District {res['district']} via {res.get('precinct')} "
               f"[{res.get('method')}]") if res.get("district") else f"[{res.get('gap','?')}]"
        print(f"  '{addr}'")
        print(f"    on {d} (plan={res['plan']}): {loc}")
        print(f"    -> your reps: {who or '(none — see gap)'}")

    print("\n(d) SAME address across the 2022 REDISTRICTING (versioned district_versions):")
    for d in ("2020-06-01", "2026-02-01"):
        res = roster_lib.representatives_for_address(CFG, addr, d, latlon=(40.6097, -111.9391))
        if res.get("district"):
            reps = [x["person_name"] for x in res["reps"] if x["seat_id"].startswith("D")]
            print(f"    {d} (plan={res['plan']}): geographic District {res['district']} -> {reps}")
        else:
            print(f"    {d} (plan={res['plan']}): {res.get('gap')}")

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
        print("\nValidation: PASS (no overlaps; sources+confidence present; non-voting-mayor + gap/vacate guards clear).")
        print("Precinct cross-check:")
        roster_lib.precinct_crosscheck(CFG, verbose=True)
    if "--demo" in sys.argv:
        demo()
