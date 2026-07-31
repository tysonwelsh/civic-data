#!/usr/bin/env python3
"""build_roster.py — rolling council-roster for MAGNA (a slowly-changing-dimension /
interval table of who holds each council + mayor seat over time).

Magna is a **5-DISTRICT city with a PRESIDING-OFFICER VOTE FLIP at the 2024 HB35 seam** —
the single trickiest structural fact in the roster fleet:
  * TOWNSHIP ERA (2017-2025): a 5-member DISTRICT council with **no separately-elected
    mayor**; the council elects one of its five as **Chair, titled "Mayor" (S.B.175)** and
    **that Chair VOTES** as one of the five (Dan Peay, D3, through 2023; Eric Barney, D2,
    2024-2025). The "Mayor" title is a rotating ceremonial HAT on a sitting district member —
    NOT a distinct seat — so the Chair's votes are DISTRICT votes captured on his D-seat.
  * CITY ERA (2026+): the first directly-elected **executive Mayor (Mick Sudbury)** presides
    but **does NOT vote** (verified 2026: a 4-0 tally excludes the Mayor; cities.db shows
    ZERO Council votes for Sudbury after 2026-01-13). This is a genuinely NEW office created
    at the 2024-05-01 HB35 conversion.
  * Max council roll = 5 in BOTH eras.

MODELING THE VOTE FLIP (the core decision — see roster/CLAUDE.md for the full write-up):
  seat_id **MAYOR** is reserved for the directly-elected EXECUTIVE mayoralty, which exists
  ONLY from 2026 (one tenure: Sudbury, body='Mayor'). The TOWNSHIP-era voting Chairs are NOT
  put on the MAYOR seat — they are modelled on their DISTRICT seats (Peay=D3, Barney=D2,
  body='Council'), where their real votes already live. Consequences:
    - `non_voting_mayor=True` — the ONLY body='Mayor' tenure (Sudbury 2026+) is non-voting;
      validate() ENFORCES that its vote bounds are EMPTY (a fail-loud tripwire if the vote
      extractor ever mis-attributes a mayoral vote to him). VERIFIED: Sudbury casts 0 Council
      votes in 2026 (cities.db).
    - The township voting Chairs (Peay, Barney) are body='Council' district members, so the
      non_voting_mayor flag never touches them — they keep REAL clamped vote bounds (Peay
      2020-2023 on D3; Barney 2022-2025 on D2, incl. his 2024-2025 Chair-"Mayor"-hat votes).
  This inverts the white_city/copperton pattern (where the AT-LARGE chair's own seat became
  the MAYOR chain and non_voting_mayor=False because THEIR exec mayor also votes). Here the
  district structure makes the township chair a district member, and the exec mayor is
  non-voting, so True is both correct and a stronger guard. A per-TENURE voting flag would let
  a single MAYOR-seat chain span a voting-chair era + a non-voting-exec era without the
  district-seat split — flagged for scripts/roster_HARDENING.md (do NOT implement in the lib).

THIN DRIVER: Magna-specific DATA (curated TENURES, name maps, the 2022-redistricting facts) +
config; all generic mechanics live in ../../scripts/roster_lib.py. District template:
herriman_city_council/roster/ (precinct cross-check) + midvale (non_voting_mayor). HB35-seam
template: white_city / copperton.

DERIVED LAYER — regenerable, never hand-edited. Canonical inputs:
  1. election_results/magna_results_by_candidate.csv  (winners -> elected/reelected)
  2. cities.db  role table (city='magna', body='Council')  (observed NAMED-vote bounds)
  3. meeting_minutes/minutes/**  (oaths, the 2022 redistricting, the 2024 reorg, the 2026 seating)
  4. roster/roster_overrides.csv  (hand corrections; applied LAST, win ties)
  5. roster/_precinct_to_district.csv  (a roster-layer sidecar over geo/precinct_to_district.csv:
     the 14 RESOLVED precincts only, with source_year PRESERVED (2019/2025). The geo file's 4
     `confidence=none` blank-district rows (MAG001/008/009/017) cannot render as valid
     precinct->district rows — excluding them is honest (their current district is unknown), NOT
     a geo/ edit. See roster/CLAUDE.md "library-fit + mixed-vintage" note.)

Outputs (idempotent — re-running reproduces them byte-for-byte):
  roster/council_terms.csv      one row per seat-tenure (5 districts + the 2026+ exec MAYOR)
  roster/district_versions.csv  boundary interval table — 5 districts x 2 plans (2022 redistrict)
  roster/district_precincts.csv versioned precinct->district composition (plan-scoped; districts)

Usage:
  python3 roster/build_roster.py            # regenerate the CSVs
  python3 roster/build_roster.py --demo     # regenerate + print the demo queries
  python3 roster/build_roster.py --check    # regenerate + validations + precinct cross-check

Cardinal rule (repo CLAUDE.md): NEVER fabricate. Unknown seat-holder / boundary / date ->
explicit VACANT / gap + confidence + a note, never a guess. The 2017->mid-2018 PMN purge and the
dissent-only naming are HONEST source limits. The 2023 D1/D3/D5 cycle was NOT a gap: the election
was cancelled and the three unopposed candidates (Prokopis D1, Sudbury D3, Pierce D5) were
CERTIFIED ELECTED under Utah Code 20A-1-206 (Res 2023-09-02) — see election_results/magna_races.csv
year=2023 (cancelled_certification) and those seats' 2024-term tenures.

Provenance / confidence model (Magna):
  high   = an in-file election win seated at a documented January oath meeting + corroborated by
           the cities.db named-vote record (incl. the 2023 cancelled-certification 2024-term
           seatings — Prokopis D1, Sudbury D3, Pierce D5, deemed elected by Res 2023-09-02 and
           organized at the 2024-01-09 reorg), OR a minutes-documented appointment (Jensen D3
           2026-01-13 mid-term-vacancy selection + oath).
  medium = a FOUNDING / pre-floor term. Magna's council record begins 2018-07-17 (the 2017 ->
           mid-2018 minutes are a genuine PMN retention purge), so the 2016-founding and the
           2017 D2/D4 re-election terms (Jan-2017 / Jan-2018 starts) predate the minutes floor:
           the win is in the file, continuous service from the term start is inferred -> medium.
  low    = none in council_terms. The prior-plan (pre-2022) district + precinct geometry is an
           honest GAP (blank/low); the mixed-vintage current map's D1/D3/D5 precincts are
           medium (pre-2022-line-derived) — see the district layer.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.dirname(HERE)                 # magna_city_council/
REPO_ROOT = os.path.dirname(CITY_DIR)            # civic-data/
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import roster_lib
from roster_lib import RosterConfig, Redistrict

ELECTIONS = os.path.join(CITY_DIR, "election_results", "magna_results_by_candidate.csv")
PRECINCTS_BYP_SRC = os.path.join(CITY_DIR, "election_results", "magna_results_by_precinct.csv")
PRECINCT_MAP = os.path.join(HERE, "_precinct_to_district.csv")   # roster-layer sidecar (see header)
CITIES_DB = os.path.join(REPO_ROOT, "cities.db")
OVERRIDES = os.path.join(HERE, "roster_overrides.csv")
TERMS_OUT = os.path.join(HERE, "council_terms.csv")
DISTRICTS_OUT = os.path.join(HERE, "district_versions.csv")
PRECINCTS_OUT = os.path.join(HERE, "district_precincts.csv")

CITY = "magna"
DATA_FLOOR = "2017-01-01"          # metro township incorporated Jan 2017 (2017->mid-2018 PMN-purged; earliest recovered minutes 2018-07-17)
GEOM_REF = "geo/districts.geojson"  # precinct-DERIVED, mixed-vintage (no official Magna district GIS layer)

# The real redistricting event (spot-checked against source minutes 2022-04-26):
#   Resolution 22-04-01 "ADOPTING A NEW MAGNA METRO TOWNSHIP COUNCIL DISTRICT MAP" (Map 9),
#   adopted 2022-04-26 on a 3-1 roll (Hull mover / Prokopis second; Mayor/Chair Peay Aye — a
#   VOTING-chair roll — Council Member Pierce voting Nay). 2020-census reapportionment that "keeps
#   all the Council Members in their [districts]". First used for the 2025 D2/D4 district races
#   (MAG012 moved D5->D4, MAG013 moved D1->D4). The pre-2022 lines governed 2016/2019/2021.
REDISTRICT_ORD = "Resolution 22-04-01 (2022 Redistricting Map — Map 9)"
REDISTRICT_ADOPTED = "2022-04-26"
PLAN_OLD = "plan_pre2022"
PLAN_NEW = "plan_2022"
PLAN_SWITCH = "2022-04-26"
SRC_URL = ("meeting_minutes/minutes/2022/2022-04-26_council_100.md "
           "(Resolution 22-04-01 'ADOPTING A NEW MAGNA METRO TOWNSHIP COUNCIL DISTRICT MAP' / Map 9, "
           "adopted 2022-04-26, passed 3-1 with Council Member Pierce Nay)")

SEAT_DISTRICT = {
    "D1": "District 1", "D2": "District 2", "D3": "District 3", "D4": "District 4",
    "D5": "District 5", "MAYOR": "Citywide",
}

TENURES = [
    # ============================ D1 — Steve Prokopis (holds over into the city era) ==========
    dict(body="Council", seat_id="D1", person_name="Steve Prokopis", person_key="steve_prokopis",
         start_date="2017-01-01", start_event="elected", election_year="2016", end_event="reelected",
         confidence="medium",
         sources="election:2016 (District 1 founding winner, 57.85%); minutes:2018-07-17 (earliest "
                 "recovered — present); votes:2019-07-09.. (cities.db, Council/D1)",
         note="FOUNDING metro-township term (elected Nov-2016, term commenced Jan 2017). The 2017->"
              "mid-2018 minutes are a genuine PMN purge, so the Jan-2017 origin is pre-floor -> medium; "
              "service is documented from 2018-07-17. Re-elected 2019."),
    dict(body="Council", seat_id="D1", person_name="Steve Prokopis", person_key="steve_prokopis",
         start_date="2020-01-14", start_event="reelected", election_year="2019", end_event="reelected",
         confidence="high",
         sources="election:2019 (District 1 winner, unopposed 538/100%); minutes:2020-01-14 (oath — "
                 "'re-elected Council Member Steve Prokopis'); votes:2020..2023 (cities.db, Council/D1)",
         note="Re-elected D1 2019 (seated 2020-01-14). Term ran through 2023; RE-CERTIFIED for the 2024 "
              "term at the CANCELLED Nov-2023 township election (Res 2023-09-02) — see the next D1 row. "
              "NOT a held-over gap: the 2023 D1/D3/D5 cycle WAS resolved, by certification under Utah "
              "Code 20A-1-206, not cancelled as a cityhood side-effect."),
    dict(body="Council", seat_id="D1", person_name="Steve Prokopis", person_key="steve_prokopis",
         start_date="2024-01-09", start_event="reelected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 1 — CANCELLED-CERTIFICATION, Utah Code 20A-1-206, Res "
                 "2023-09-02: the sole declared candidate deemed elected eff. 2024-01-01; "
                 "election_results/magna_races.csv year=2023 D1 winner STEVE PROKOPIS, "
                 "cancelled_certification, no votes cast); minutes:2023-09-26 (Res 2023-09-02 adopted "
                 "verbatim — 'the three unopposed candidates ... are hereby deemed to be elected ... "
                 "Steve Prokopis, Audrey Pierce, and Mick Sudbury'; motion passed unanimously); "
                 "minutes:2024-01-09 (reorg — new term organized); votes:2024..2025 (cities.db, "
                 "Council/D1); minutes:2026-01-13 (present, still serving)",
         note="RE-CERTIFIED for the 2024 D1 term at the CANCELLED Nov-2023 township election: under Utah "
              "Code 20A-1-206 the three unopposed incumbents were deemed elected effective 2024-01-01 "
              "(Res 2023-09-02, adopted 2023-09-26). A NEW D1 term (not a held-over gap; the cycle was "
              "resolved by certification, not a cityhood cancellation). Prokopis held over without a new "
              "oath; the term organized at the 2024-01-09 reorg. D1 next up 2027. Serving."),

    # ============================ D2 — Peel -> Barney (township Chair-Mayor 2024-25) -> Olsen ==
    dict(body="Council", seat_id="D2", person_name="Brint Peel", person_key="brint_peel",
         start_date="2017-01-01", start_event="elected", election_year="2016", end_event="reelected",
         confidence="medium",
         sources="election:2016 (District 2 founding winner, 51.4%); minutes:2018-07-17 (present)",
         note="FOUNDING metro-township term (elected Nov-2016, term Jan 2017 — pre-floor purge -> "
              "medium). Re-elected 2017 (short founding-stagger term)."),
    dict(body="Council", seat_id="D2", person_name="Brint Peel", person_key="brint_peel",
         start_date="2018-01-01", start_event="reelected", election_year="2017", end_event="lost",
         confidence="medium",
         sources="election:2017 (District 2 winner, unopposed 513/100%); minutes:2018-07-17.. (present "
                 "through 2021); votes:2020-02-11 (only named vote — dissent-only-naming era); "
                 "minutes:2022-01-11 (replaced by Barney)",
         note="Re-elected D2 2017 (Jan-2018 term, pre-floor -> medium; service documented from "
              "2018-07-17, present in 24 of the 2021 minutes). RAN for D2 in 2021 and LOST to Eric "
              "Barney (32.7% v 59.72%) -> term ended at the 2022-01-11 seating. His lone named vote "
              "(2020-02-11) reflects the narrative-tally / dissent-only naming, NOT a short tenure."),
    dict(body="Council", seat_id="D2", person_name="Eric Barney", person_key="eric_barney",
         start_date="2022-01-11", start_event="elected", election_year="2021", end_event="lost",
         confidence="high",
         sources="election:2021 (District 2 winner, def. Brint Peel 59.72%); minutes:2022-01-11 (seated, "
                 "present); votes:2022-01-11..2025-06-10 (cities.db, Council/D2); minutes:2026-01-13 "
                 "(replaced by Olsen)",
         note="Elected D2 2021. Was the peer-selected township CHAIR titled 'Mayor' 2024-2025 (elected "
              "2024-01-09 reorg; 'in the second round, Council Member Barney received three votes, which "
              "makes him the new Mayor') — a VOTING Chair (verified: 7 Council Ayes in 2024). That "
              "Chair-'Mayor' role is a HAT on his D2 seat; his votes are captured here as D2 votes, NOT on "
              "the MAYOR seat. RAN for D2 in 2025 and LOST to Megan Olsen (31.59% v 68.41%) -> term ended "
              "at the 2026-01-13 city seating."),
    dict(body="Council", seat_id="D2", person_name="Megan Olsen", person_key="megan_olsen",
         start_date="2026-01-13", start_event="elected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (District 2 winner, def. incumbent Eric Barney 68.41%); minutes:2026-01-13 "
                 "(first CITY council meeting; present as Council Member Megan Olsen)",
         note="Elected D2 2025 (first CITY-era election). No named vote yet in cities.db (the "
              "narrative-tally source, not a gap). Serving."),

    # ============================ D3 — Peay (Chair-Mayor <=2023) -> Sudbury (appt) -> Jensen ===
    dict(body="Council", seat_id="D3", person_name="Dan Peay", person_key="dan_peay",
         start_date="2017-01-01", start_event="elected", election_year="2016", end_event="reelected",
         confidence="medium",
         sources="election:2016 (District 3 founding winner, 50.17%); minutes:2018-07-17 ('Mayor Peay, "
                 "Chair, presided')",
         note="FOUNDING metro-township term (elected Nov-2016, term Jan 2017 — pre-floor purge -> "
              "medium). Peer-selected township Chair titled 'Mayor' and VOTES. Re-elected 2019."),
    dict(body="Council", seat_id="D3", person_name="Dan Peay", person_key="dan_peay",
         start_date="2020-01-14", start_event="reelected", election_year="2019", end_event="retired",
         confidence="high",
         sources="election:2019 (District 3 winner, unopposed 470/100%); minutes:2020-01-14 (oath — "
                 "'Mayor Dan Peay'); votes:2020-07-14..2023-04-25 (cities.db, Council/D3 — incl. Nay/Aye "
                 "as the VOTING Chair); minutes:2023-12-12 (his documented LAST meeting — 'congratulating "
                 "Mayor Peay on his retirement and announcing his retirement')",
         note="Re-elected D3 2019 and continued as the VOTING Chair-'Mayor' through 2023. RETIRED end of "
              "2023 (last meeting 2023-12-12; the 2023 D1/D3/D5 township cycle was not held). Seat passed "
              "to the appointed Sudbury at the very next meeting (2024-01-09 reorg) -> ends there with no "
              "empty-seat meeting (no VACANT interval)."),
    dict(body="Council", seat_id="D3", person_name="Mick Sudbury", person_key="mick_sudbury",
         start_date="2024-01-09", start_event="elected", election_year="2023", end_event="became-mayor",
         confidence="high",
         sources="election:2023 (District 3 — CANCELLED-CERTIFICATION, Utah Code 20A-1-206, Res "
                 "2023-09-02: the sole declared candidate for the open D3 seat deemed elected eff. "
                 "2024-01-01; election_results/magna_races.csv year=2023 D3 winner MICK SUDBURY, "
                 "cancelled_certification, no votes cast); minutes:2023-09-26 (Res 2023-09-02 adopted "
                 "verbatim — 'deemed to be elected ... Mick Sudbury'; passed unanimously); "
                 "minutes:2024-01-09 (reorg — took office as the District 3 member, present + acting "
                 "from the opening roll; named 'District 3: Mick Sudbury' in Res. 2024-01-01's board "
                 "appointments); votes:2024-06-25..2025-06-10 (cities.db, Council/D3)",
         note="ELECTED to the open D3 seat at the CANCELLED Nov-2023 township election — a DECLARED "
              "CANDIDATE certified elected under Utah Code 20A-1-206 (Res 2023-09-02, adopted 2023-09-26; "
              "deemed elected eff. 2024-01-01), NOT an appointment. D3 was open because Dan Peay (the D3 "
              "incumbent + township Chair-'Mayor') retired end of 2023 and did not run; Sudbury was the "
              "sole declared D3 candidate. Took office at the 2024-01-09 reorg. Later WON the 2025 "
              "directly-elected Mayor race and became the (non-voting) executive Mayor 2026-01-13 -> "
              "vacated D3 (end_event=became-mayor; see seat MAYOR). His D3 votes are REAL (voting "
              "district member); his MAYOR bounds are EMPTY."),
    dict(body="Council", seat_id="D3", person_name="Michael Jensen", person_key="michael_jensen",
         start_date="2026-01-13", start_event="appointed", election_year="", end_event="serving",
         confidence="high",
         sources="minutes:2026-01-13 ('A. District 3 Council Member Mid-Term Vacancy Interviews and "
                 "Selection ... a District 3 council seat had become vacant because the District 3 council "
                 "member had been elected mayor'; 4 applicants (Jeff White, Michael Jensen, Dan Peay, Jen "
                 "...); 'Michael Jensen was announced as the winner. At that time he was given the Oath of "
                 "[Office]'); votes:2026-04-30.. (cities.db, Council/D3)",
         note="APPOINTED to the D3 mid-term vacancy created when Sudbury (D3) was elected Mayor. Selected "
              "from four applicants and sworn in at the 2026-01-13 city seating. The elected D3 seat is next "
              "up in 2027. Serving."),

    # ============================ D4 — Trish Hull -> Terry George =============================
    dict(body="Council", seat_id="D4", person_name="Trish Hull", person_key="trish_hull",
         start_date="2017-01-01", start_event="elected", election_year="2016", end_event="reelected",
         confidence="medium",
         sources="election:2016 (District 4 founding winner, 55.99%); minutes:2018-07-17 (present)",
         note="FOUNDING metro-township term (elected Nov-2016, term Jan 2017 — pre-floor purge -> "
              "medium). Re-elected 2017 (short founding-stagger term)."),
    dict(body="Council", seat_id="D4", person_name="Trish Hull", person_key="trish_hull",
         start_date="2018-01-01", start_event="reelected", election_year="2017", end_event="reelected",
         confidence="medium",
         sources="election:2017 (District 4 winner, unopposed 396/100%); votes:2018-09-18.. (cities.db, "
                 "Council/D4)",
         note="Re-elected D4 2017 (Jan-2018 term, pre-floor -> medium; service vote-documented from "
              "2018-09-18). Re-elected again 2021 -> continuous."),
    dict(body="Council", seat_id="D4", person_name="Trish Hull", person_key="trish_hull",
         start_date="2022-01-11", start_event="reelected", election_year="2021", end_event="lost",
         confidence="high",
         sources="election:2021 (District 4 winner, unopposed 100%); minutes:2022-01-11 (oath — "
                 "'re-elected Council Member Trish [Hull]'); votes:continuous through 2025-07-30 "
                 "(cities.db, Council/D4); minutes:2026-01-13 (replaced by George)",
         note="Re-elected D4 2021. RAN for D4 in 2025 (advanced through the primary) and LOST to Terry "
              "George (47.22% v 52.78%) -> term ended at the 2026-01-13 city seating. Also cast Magna's "
              "one CRA vote 2025-12-09 (body=CRA — does not affect these Council/D4 bounds)."),
    dict(body="Council", seat_id="D4", person_name="Terry George", person_key="terry_george",
         start_date="2026-01-13", start_event="elected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (District 4 winner, def. incumbent Trish Hull 52.78%); minutes:2026-01-13 "
                 "(present as Council Member Terry George; Mayor Pro Tem per geo/CLAUDE)",
         note="Elected D4 2025 (first CITY-era election). No named vote yet in cities.db (narrative-tally "
              "source, not a gap). Serving."),

    # ============================ D5 — Eric Ferguson -> Audrey Pierce (holds over) =============
    dict(body="Council", seat_id="D5", person_name="Eric Ferguson", person_key="eric_ferguson",
         start_date="2017-01-01", start_event="elected", election_year="2016", end_event="did-not-run",
         confidence="medium",
         sources="election:2016 (District 5 founding winner, 58.33%); minutes:2018-07-17 (present; "
                 "present through all of 2018)",
         note="FOUNDING metro-township term (elected Nov-2016, term Jan 2017 — pre-floor purge -> "
              "medium). NOT a candidate in 2019 (Audrey Pierce won D5 unopposed) -> did-not-run; term "
              "ended at the 2020-01-14 seating. Casts no NAMED vote in cities.db (tally-only founding era) "
              "-> no vote bounds; the source, not a gap."),
    dict(body="Council", seat_id="D5", person_name="Audrey Pierce", person_key="audrey_pierce",
         start_date="2020-01-14", start_event="elected", election_year="2019", end_event="reelected",
         confidence="high",
         sources="election:2019 (District 5 winner, unopposed 435/100%); minutes:2020-01-14 (oath — "
                 "'newly elected Council Member Audrey Pierce'); votes:2019-10-22..2023 (cities.db, Council/D5)",
         note="Elected D5 2019 (seated 2020-01-14; NEW to the seat — Ferguson did-not-run). Served as "
              "township Mayor Pro Tempore 2024-2025 (an acting/alternate role, NOT a Mayor tenure). Term "
              "ran through 2023; RE-CERTIFIED for the 2024 term (Res 2023-09-02) — see the next D5 row."),
    dict(body="Council", seat_id="D5", person_name="Audrey Pierce", person_key="audrey_pierce",
         start_date="2024-01-09", start_event="reelected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 5 — CANCELLED-CERTIFICATION, Utah Code 20A-1-206, Res "
                 "2023-09-02: the sole declared candidate deemed elected eff. 2024-01-01; "
                 "election_results/magna_races.csv year=2023 D5 winner AUDREY PIERCE, "
                 "cancelled_certification, no votes cast); minutes:2023-09-26 (Res 2023-09-02 adopted "
                 "verbatim — 'deemed to be elected ... Audrey Pierce'; passed unanimously); "
                 "minutes:2024-01-09 (reorg); votes:2024..2026-05-26 (cities.db, Council/D5); "
                 "minutes:2026-01-13 (present, still serving)",
         note="RE-CERTIFIED for the 2024 D5 term at the CANCELLED Nov-2023 township election: deemed "
              "elected effective 2024-01-01 under Utah Code 20A-1-206 (Res 2023-09-02, adopted "
              "2023-09-26). A NEW D5 term (not a held-over gap; the cycle was resolved by certification, "
              "not a cityhood cancellation). Pierce held over without a new oath; organized at the "
              "2024-01-09 reorg. Also served as township Mayor Pro Tempore 2024-2025. D5 next up 2027. "
              "Serving."),

    # ============================ MAYOR — the directly-elected EXECUTIVE mayoralty (2026+) =====
    # This seat exists ONLY from the 2024 HB35 cityhood's first mayoral election (2025 -> seated
    # 2026). In the township era there was NO separately-elected mayor; the presiding "Mayor" was a
    # peer-selected district councilmember (Peay D3, Barney D2) captured on their district seats
    # above. non_voting_mayor=True: the exec Mayor presides but does NOT vote (EMPTY bounds; enforced).
    dict(body="Mayor", seat_id="MAYOR", person_name="Mick Sudbury", person_key="mick_sudbury",
         start_date="2026-01-13", start_event="became-mayor", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (Mayor winner — first directly-elected Magna executive Mayor, 65.39%); "
                 "minutes:2026-01-13 ('Mayor Mick Sudbury, presiding, called the meeting to order'); "
                 "cities.db: ZERO Council votes as Mayor (non-voting — verified)",
         note="First directly-elected EXECUTIVE Mayor of Magna (a NEW office created at the 2024-05-01 "
              "HB35 conversion; the township era had no separately-elected mayor). SAME PERSON as D3 "
              "Sudbury (certified elected to D3 for the 2024 term, voted 2024-2025 as a district member) "
              "— but as executive Mayor he "
              "presides and does NOT vote: EMPTY first_vote/last_vote by non_voting_mayor (validate "
              "enforces it). This is the presiding-officer VOTE FLIP at the seam. Serving."),
]

# canonical UPPER-CASE election-name token -> our person_key. No two Magna general winners share a
# surname, so surname alone suffices (no disambiguators). Only WINNERS pass through canon_key.
NAME_TO_KEY = {
    "PROKOPIS": "steve_prokopis", "PEEL": "brint_peel", "PEAY": "dan_peay",
    "HULL": "trish_hull", "FERGUSON": "eric_ferguson", "PIERCE": "audrey_pierce",
    "BARNEY": "eric_barney", "OLSEN": "megan_olsen", "GEORGE": "terry_george",
    "SUDBURY": "mick_sudbury",
}

# cities.db person.name_key -> our person_key (Council voters ONLY — those who cast a NAMED vote).
# Ferguson (tally-only founding era), Olsen & George (no named vote yet) cast none -> absent from the
# db, never mapped (the narrative-tally source, not a gap). micksudbury IS mapped for his 2024-2025 D3
# council votes; his MAYOR (body='Mayor') tenure is emptied by non_voting_mayor.
DB_KEY = {
    "steveprokopis": "steve_prokopis", "brintpeel": "brint_peel", "danpeay": "dan_peay",
    "trishhull": "trish_hull", "audreypierce": "audrey_pierce", "ericbarney": "eric_barney",
    "micksudbury": "mick_sudbury", "michaeljensen": "michael_jensen",
}


def seat_for_contest(office, district):
    """election (office, district) -> the STABLE seat_id used as the cross-check key
    (crosscheck_field='seat_id'). Magna: 5 numbered districts + a citywide exec Mayor."""
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
    current_note=("CURRENT post-2020-census boundaries. " + REDISTRICT_ORD + " adopted "
                  + REDISTRICT_ADOPTED + " on a 3-1 roll (Hull mover / Prokopis second; VOTING Chair "
                  "Peay Aye; Pierce Nay). geometry_ref = geo/districts.geojson — a PRECINCT-DERIVED, "
                  "MIXED-VINTAGE map (Magna has NO official district GIS layer): D2/D4 are on the "
                  "current 2025 lines (high); D1/D3/D5 are still derived from 2019 (pre-2022) returns "
                  "because the 2023 D1/D3/D5 cycle was cancelled and 2025 ran only D2/D4 — see the "
                  "precinct layer + geo/CLAUDE.md."),
    prior_adopted_by="prior plan (founding pre-2022 boundaries)",
    prior_geom_ref="",
    prior_confidence="low",
    prior_note=("Prior-plan (founding pre-2022) district boundaries NOT acquired -> honest GAP (blank "
                "geometry_ref, low). In force for the 2016/2017/2019/2021 elections. effective_start = "
                "the 2017 incorporation/data floor."),
    citywide_rows=[],   # the exec-mayor office is 2026+ ONLY (no citywide district_versions row implying a
                        # pre-2026 mayoralty); the MAYOR council_terms tenure carries it. See CLAUDE.md.
    citywide_adopted_by="Magna City (citywide executive mayor)",
    citywide_note_template="{who}",
    precinct_hi_source="2025",   # source_year 2025 (current lines) -> high; 2019 (pre-2022 lines) -> medium
    precinct_hi_note=("current post-2020-census precinct->district (D2/D4) from the 2025 general, read "
                      "through the roster/_precinct_to_district.csv sidecar over geo/precinct_to_district.csv "
                      "(the 14 resolved precincts; 4 unresolved 'none' rows excluded as an honest gap)."),
    precinct_med_note=("D1/D3/D5 precinct->district derived from the 2019 general (PRE-2022 lines) — the "
                       "2023 D1/D3/D5 cycle was cancelled and 2025 ran only D2/D4, so the current-line "
                       "composition of these districts is not election-derivable -> medium (mixed-vintage)."),
    precinct_prior_note=("Founding (pre-2022) precinct->district composition NOT acquired -> honest GAP."),
    crosscheck_districts=("2", "4"),   # only D2/D4 have current-line (2025) by-precinct data
    precinct_prefix="MAG", geo_seat_prefix="D",
    plan_switch_year="2022", citywide_seats=(),
)

CFG = RosterConfig(
    non_voting_mayor=True,      # the 2026+ EXECUTIVE Mayor presides but does NOT vote (verified);
                                # township voting Chairs are modelled on their DISTRICT seats, so the
                                # flag never touches them. See the module header + CLAUDE.md.
    city=CITY, city_dir=CITY_DIR, repo_root=REPO_ROOT, data_floor=DATA_FLOOR,
    geom_ref=GEOM_REF, elections_path=ELECTIONS, cities_db_path=CITIES_DB,
    overrides_path=OVERRIDES, terms_out=TERMS_OUT, districts_out=DISTRICTS_OUT,
    seat_district=SEAT_DISTRICT, name_to_key=NAME_TO_KEY, db_key=DB_KEY,
    seat_order=["D1", "D2", "D3", "D4", "D5", "MAYOR"],
    # municipal GENERAL winners, all years (2016+) — every winner maps to a rostered tenure (0 drift).
    keep_election_row=lambda r: r["election_type"].strip().lower() == "municipal general",
    contest_key=seat_for_contest, crosscheck_field="seat_id",
    winners_have_district=True,
    elected_events=("elected", "reelected", "became-mayor"),
    # H-C reverse-crosscheck DOCUMENTED exceptions (2026-07-19). crosscheck_field='seat_id'.
    # The Nov-2023 township D1/D3/D5 election was CANCELLED under Utah Code 20A-1-206 (Res
    # 2023-09-02, adopted 2023-09-26, verbatim in the minutes) and the three unopposed candidates
    # certified elected eff. 2024-01-01. NO votes were cast, so magna_results_by_candidate.csv has
    # 0 rows for 2023 (the cancelled_certification rows live in magna_races.csv, not the by_candidate
    # file the crosscheck reads) — exactly the alta pattern. Roster is correct (see roster/CLAUDE.md
    # 'Correction 2026-07-17'); the forward check is 0-drift by design.
    reverse_crosscheck_exceptions={
        ("2023", "D1", "steve_prokopis"): "2023 D1 township election CANCELLED (Utah Code 20A-1-206; Res 2023-09-02, adopted 2023-09-26) — Prokopis re-certified elected, no votes cast; magna_races.csv cancelled_certification (no by_candidate tally rows exist)",
        ("2023", "D3", "mick_sudbury"): "2023 D3 township election CANCELLED (Utah Code 20A-1-206; Res 2023-09-02, adopted 2023-09-26) — Sudbury sole declared candidate deemed elected to the Peay-vacated seat, no votes cast; magna_races.csv cancelled_certification (no by_candidate tally rows exist)",
        ("2023", "D5", "audrey_pierce"): "2023 D5 township election CANCELLED (Utah Code 20A-1-206; Res 2023-09-02, adopted 2023-09-26) — Pierce re-certified elected, no votes cast; magna_races.csv cancelled_certification (no by_candidate tally rows exist)",
    },
    redistrict=REDISTRICT, precincts_out=PRECINCTS_OUT,
    precinct_map_path=PRECINCT_MAP, precincts_byprecinct_path=PRECINCTS_BYP_SRC,
)


def demo():
    def line(r):
        end = r["end_date"] or "—(serving)"
        return (f"    {r['seat_id']:<6} {r['person_name']:<18} {r['start_date']} -> {end:<12}"
                f" [{r['start_event']}/{r['end_event']}] {r['body']:<7} conf={r['confidence']}")

    print("\n(a) CURRENT council roster + exec Mayor (end_date empty, end_event=serving):")
    for r in roster_lib.load_terms(CFG):
        if not r["end_date"] and r["end_event"] == "serving":
            print(line(r))

    print("\n(b) Roster AS OF 2024-06-01 (township era — Barney is the VOTING Chair-'Mayor', from D2):")
    for r in roster_lib.roster_as_of(CFG, "2024-06-01", body="Council"):
        print(line(r))
    for r in roster_lib.roster_as_of(CFG, "2024-06-01", body="Mayor"):
        print(line(r))
    print("    (note: no body='Mayor' tenure before 2026 — the township presiding officer is a district member)")

    print("\n(c) Address+date -> representatives (via geo/address_to_district.py — 1 district + exec Mayor):")
    addr = "8952 W Magna Main St, Magna, UT 84044"   # Webster Center
    for d in ("2026-02-01", "2020-06-01"):
        res = roster_lib.representatives_for_address(CFG, addr, d)
        who = ", ".join(f"{x['person_name']}({x['seat_id']})" for x in res["reps"])
        loc = (f"District {res['district']} via {res.get('precinct')} [{res.get('method')}]"
               if res.get("district") else f"[{res.get('gap', '?')}]")
        print(f"  '{addr}'\n    on {d} (plan={res['plan']}): {loc}\n    -> your reps: {who or '(none — see gap)'}")

    print("\n(e) Precinct-map cross-check (district_precincts vs election outcomes; D2/D4 current-line only):")
    roster_lib.precinct_crosscheck(CFG, verbose=True)


if __name__ == "__main__":
    rows = roster_lib.build(CFG, TENURES)
    n = {c: sum(1 for r in rows if r["confidence"] == c) for c in ("high", "medium", "low")}
    nvac = sum(1 for r in rows if r["start_event"] == "vacated")
    print(f"Wrote {os.path.relpath(TERMS_OUT, CITY_DIR)} "
          f"({len(rows)} tenures incl. {nvac} VACANT: {n['high']} high / {n['medium']} medium / {n['low']} low)")
    print(f"Wrote {os.path.relpath(DISTRICTS_OUT, CITY_DIR)} "
          f"(5 districts x 2 plans; redistricting {REDISTRICT_ORD}; exec-mayor office is 2026+, in council_terms)")
    print(f"Wrote {os.path.relpath(PRECINCTS_OUT, CITY_DIR)} "
          f"(plan_2022 precinct map — D2/D4 high (2025 lines) / D1/D3/D5 medium (2019 pre-2022 lines) + "
          f"plan_pre2022 gap rows)")
    if "--check" in sys.argv:
        print("\nValidation: PASS (no overlaps; sources+confidence present; non-voting-mayor + gap/vacate guards clear).")
        print("Precinct cross-check:")
        roster_lib.precinct_crosscheck(CFG, verbose=True)
    if "--demo" in sys.argv:
        demo()
