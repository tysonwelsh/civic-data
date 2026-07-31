#!/usr/bin/env python3
"""build_roster.py — rolling council-roster for KEARNS (a slowly-changing-dimension /
interval table of who holds each council + mayor seat over time).

Kearns spans a **metro-township -> CITY (HB35) seam** with a **district-count change**, and
the presiding officer VOTES in BOTH eras (the Millcreek pattern) but is a DIFFERENT KIND of
officer on each side:

  * TOWNSHIP era (data floor 2017 -> the 2026 city seating): a **5-member council**, DISTRICTS
    1-5, that ELECTED ITS OWN CHAIR from among the five, styled "Mayor" per S.B.175 ("Mayor
    Kelly Bush, Chair, presided"). The chair is a peer-selected HAT worn by a district member
    (Kelly Bush held District 5 AND chaired throughout the recovered record) — NOT a separate
    seat. Max roll = 5 (the five district members; the chair is one of them and VOTES).
  * CITY era (Jan 2026 ->): a **directly-elected executive Mayor + 4 DISTRICT councilmembers**.
    THE MAYOR VOTES (verified 2026-05-11: "Vote was 5-0" with only 4 councilmembers -> the 5th
    vote is Mayor Jesse Valdez, Utah's first Hispanic mayor). Max city roll = 5 INCLUDING the
    voting mayor.

Both eras top out at 5, and the presiding officer votes in both -> **non_voting_mayor=False**.
The SEAM restructures 5 township districts (D1-D5) into 4 city districts (D1-D4) + a directly-
elected citywide Mayor. Districts D1-D4 carry across the seam CONTINUOUSLY (Schaeffer D1 and
Butterfield D3 — elected to township districts in 2023 — simply continue as city D1/D3, present
and NOT re-sworn at 2026-01-12; only Longtin D2, Colby D4, and Mayor Valdez took the oath). The
TOWNSHIP 5th district (D5, Bush's, which carried the chair-"Mayor" hat) is ABOLISHED at the seam;
Bush ran for the new directly-elected city Mayor in 2025 and LOST to Valdez, so her council
service ends at the 2026 seating. The city MAYOR seat is a NEW office (Valdez), distinct from the
township D5 chair — they are modeled as SEPARATE seats (no false continuity; Bush != Valdez).

THIN DRIVER: this file holds only Kearns-specific DATA (the curated TENURES, name maps, the
township->city restructure facts) + config; all generic mechanics live in
../../scripts/roster_lib.py. Modeled on the herriman driver (DISTRICT + VOTING-MAYOR +
redistrict + precinct-crosscheck template), plus the white_city / copperton HB35-seam handling.

DERIVED LAYER — regenerable, never hand-edited. Canonical inputs:
  1. election_results/kearns_results_by_candidate.csv  (winners -> elected/reelected; 2016+)
     NOTE: kearns_races.csv is the authoritative human file; the by_candidate long form carries
     the is_winner flag roster_lib reads. Both are parsed from the RAW SLCo SOVC (the shared
     county long file is corrupt for Kearns — see election_results/CLAUDE.md).
  2. cities.db  role/vote tables (city='kearns', body='Council')  (observed NAMED-vote bounds)
  3. meeting_minutes/minutes/**  (oath/seating dates, the Ruby Brown D3 appointment, the seam)
  4. roster/roster_overrides.csv  (hand corrections; applied LAST, win ties)
  5. roster/_precinct_to_district.csv  (a source_year sidecar over geo/precinct_to_district.csv —
     the canonical geo file carries NO source_year column that roster_lib.write_precincts()
     requires; see roster/CLAUDE.md "library-fit" note. A roster-layer derived file, NOT a geo/
     edit. Clean 2025-SOVC precincts (D2, D4) -> source_year=2025 (high); the D1/D3 unsplit
     residual precincts -> source_year=residual (medium, honest gap).)

Outputs (idempotent — re-running reproduces them byte-for-byte):
  roster/council_terms.csv      one row per seat-tenure (D1-D5 township + D1-D4 city + MAYOR)
  roster/district_versions.csv  boundary interval table — 4 city districts x 2 plans + the abolished
                                township D5's own plan_township gap row (H-H) + citywide Mayor
  roster/district_precincts.csv versioned precinct->district composition (plan-scoped; districts only)

Usage:
  python3 roster/build_roster.py            # regenerate the CSVs
  python3 roster/build_roster.py --demo     # regenerate + print the demo queries
  python3 roster/build_roster.py --check    # regenerate + validations + precinct cross-check

Cardinal rule (repo CLAUDE.md): NEVER fabricate. Unknown seat-holder / boundary / date ->
explicit gap + confidence + a note, never a guess. Honest gaps are data.

Provenance / confidence model (Kearns):
  high   = an in-data election win (2019/2021/2023/2025) seated at a DOCUMENTED January oath/
           first-meeting and corroborated by the recovered minutes (present roster) + cities.db.
  medium = a pre-2019 FOUNDING term (2016 / 2017 township elections) whose Jan-2017 / Jan-2018
           seating falls in the 2017-01..2018-06 PMN-purge gap (earliest recovered minutes
           2018-07-09): the election win is fact, the continuous service across the purge gap is
           inferred; ALSO Ruby Brown's D3 appointment (present by 2018-07-09; the exact appoint
           date is unrecoverable, in the purge gap).
  low    = none in council_terms; the township 5-district GEOMETRY (incl. abolished D5) + the
           prior-plan precinct composition are honest GAPs (not on disk) in district_versions.

STRUCTURAL FACTS (verified in source):
  * VOTING presiding officer in BOTH eras (roll of 5). Township: "Mayor Kelly Bush, Chair,
    presided" and votes as one of five (2018-07-09+; cities.db kellybush = 11 named Council
    votes). City: 2026-05-11 "Vote was 5-0" with 4 councilmembers -> Mayor Valdez is the 5th.
    non_voting_mayor=False.
  * The township chair is PEER-SELECTED each cycle ("Council Member Peterson nominated Council
    Member Bush as Kearns Metro Township Mayor" — 2024-01-08). Bush held it across the whole
    recovered record, so the "Mayor <Name>, Chair" in township rolls is always Bush in her D5
    seat — NOT a distinct executive. (The 2022-02-14 ordinance extended the mayor/vice-chair
    term from 1 year to the full elected council term.)
  * The ONLY mid-term council vacancy in the record is D3: Steve Perry (elected 2016) VACATED
    mid-term at an undeterminable date inside the 2017-01..2018-06 purge gap; RUBY BROWN was
    APPOINTED to fill it (already seated by the earliest recovered minutes 2018-07-09) and then
    LOST the 2019 D3 election to Chrystal Butterfield (68.25%). Brown's exact appointment date is
    unrecoverable (purge gap) -> her start is her first documented presence 2018-07-09 (medium),
    and Perry's end_date is the chaining artifact of that date, NOT his true last day (noted).
  * The 5->4 district restructure at the seam. Township D1-D4 continue as city D1-D4; township D5
    (Bush) is ABOLISHED (Bush ran for the new elected Mayor 2025 and lost). The directly-elected
    MAYOR (Valdez) is a NEW city seat. Modeled as separate seats — no false Bush->Valdez continuity.
  * Documented seatings in the loaded window: 2020-01-13 (2019 cycle), 2022-01-10 (2021 cycle),
    2024-01-08 (2023 cycle oath), 2026-01-12 (2025 city oath: Longtin D2, Colby D4, Mayor Valdez).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.dirname(HERE)                 # kearns_city_council/
REPO_ROOT = os.path.dirname(CITY_DIR)            # civic-data/
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import roster_lib
from roster_lib import RosterConfig, Redistrict

ELECTIONS = os.path.join(CITY_DIR, "election_results", "kearns_results_by_candidate.csv")
PRECINCTS_BYP_SRC = os.path.join(CITY_DIR, "election_results", "kearns_results_by_precinct.csv")
PRECINCT_MAP = os.path.join(HERE, "_precinct_to_district.csv")   # source_year sidecar (see header)
CITIES_DB = os.path.join(REPO_ROOT, "cities.db")
OVERRIDES = os.path.join(HERE, "roster_overrides.csv")
TERMS_OUT = os.path.join(HERE, "council_terms.csv")
DISTRICTS_OUT = os.path.join(HERE, "district_versions.csv")
PRECINCTS_OUT = os.path.join(HERE, "district_precincts.csv")

CITY = "kearns"
DATA_FLOOR = "2017-01-01"        # Kearns Metro Township effective 2017-01-01 (full history; 2017-01..2018-06 PMN-purged; earliest recovered minutes 2018-07-09)
GEOM_REF = "geo/districts.geojson"

# The township->city RESTRUCTURE, modeled as the redistricting event (5 township districts ->
# 4 city districts + a directly-elected citywide Mayor). HB35 city conversion took legal effect
# 2024-05-01; the 4-district plan took effect FOR REPRESENTATION when the city council first
# seated under it (2026-01-12, the documented city-era oath). Township 5-district geometry is a GAP.
RESTRUCTURE_ORD = "Utah HB35 (2024) city conversion + city district plan"
RESTRUCTURE_ADOPTED = "2024-05-01"
PLAN_OLD = "plan_township"       # 5-district metro-township map (D1-D5) — geometry NOT on disk (gap)
PLAN_NEW = "plan_city2026"       # 4-district city map (geo/districts.geojson; D1/D3 unsplit residual)
PLAN_SWITCH = "2026-01-12"       # first city council seated under the 4-district plan
SRC_URL = ("meeting_minutes/minutes/2026/2026-01-12/2026-01-12_city-council-meeting.md "
           "(first CITY council meeting; oath to Mayor Jesse Valdez + District 2 Longtin + "
           "District 4 Colby; Districts 1/3 Schaeffer/Butterfield carried over from the 2023 "
           "township election, not re-sworn)")

SEAT_DISTRICT = {
    "D1": "District 1", "D2": "District 2", "D3": "District 3", "D4": "District 4",
    "D5": "District 5", "MAYOR": "Citywide",
}
SEAT_ORDER = ["D1", "D2", "D3", "D4", "D5", "MAYOR"]

TENURES = [
    # ================= D1 (Cohort A: 2016 founding / 2019 / 2023) — Schaeffer, continuous =====
    dict(body="Council", seat_id="D1", person_name="Patrick Schaeffer", person_key="patrick_schaeffer",
         start_date="2017-01-01", start_event="elected", election_year="2016", end_event="reelected",
         confidence="medium",
         sources="election:2016 (Metro Township Council Seat 1 winner, def. H. Brett Helsten 52.07%); "
                 "minutes:2018-07-09 (earliest recovered — present; the 2017-01..2018-06 seating window "
                 "is PMN-purged)",
         note="FOUNDING metro-township term (Cohort A, 3-yr initial term Jan-2017..Jan-2020). The "
              "Jan-2017 seating falls in the 2017-01..2018-06 PMN-purge gap -> start inferred from the "
              "founding election (medium); present from the earliest recovered minutes 2018-07-09."),
    dict(body="Council", seat_id="D1", person_name="Patrick Schaeffer", person_key="patrick_schaeffer",
         start_date="2020-01-13", start_event="reelected", election_year="2019", end_event="reelected",
         confidence="high",
         sources="election:2019 (District 1 winner, def. Samuel J Higginson 50.84%); minutes:2020-01-13 "
                 "(first 2020 meeting; present as a 2019-cycle member); votes:2019-09-09..2022-01-10 "
                 "(cities.db, Council/D1 — named-roll era)",
         note="Re-elected D1 2019 (seated at the first documented 2020 meeting)."),
    dict(body="Council", seat_id="D1", person_name="Patrick Schaeffer", person_key="patrick_schaeffer",
         start_date="2024-01-08", start_event="reelected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 1 winner, def. Jesse Valdez 50.36%); minutes:2024-01-08 (oath "
                 "administered to Bush, Schaeffer, Butterfield as Metro Township Council members); "
                 "minutes:2026-01-12 (present as CITY District 1 councilmember — carried over, NOT "
                 "re-sworn); votes:through 2026 (cities.db, Council/D1)",
         note="Re-elected township D1 2023 (term to Jan 2028); CONTINUES across the 2026 city seam as "
              "city District 1 — same seat_id, one continuous tenure (the seam redraws boundaries, it "
              "does not reseat him). Serving."),

    # ================= D2 (Cohort B: 2016 founding / 2017 / 2021) — Peterson -> Longtin ========
    dict(body="Council", seat_id="D2", person_name="Alan Peterson", person_key="alan_peterson",
         start_date="2017-01-01", start_event="elected", election_year="2016", end_event="reelected",
         confidence="medium",
         sources="election:2016 (Metro Township Council Seat 2 winner, unopposed 100%); minutes:2018-07-09 "
                 "(earliest recovered — present)",
         note="FOUNDING metro-township term (Cohort B, SHORT 1-yr initial term Jan-2017..Jan-2018 to set "
              "the stagger; seats 2 & 4 were re-elected in 2017). Seating in the PMN-purge gap -> medium."),
    dict(body="Council", seat_id="D2", person_name="Alan Peterson", person_key="alan_peterson",
         start_date="2018-01-01", start_event="reelected", election_year="2017", end_event="reelected",
         confidence="medium",
         sources="election:2017 (Metro Township Council Seat 2 winner, unopposed 100%); minutes:2018-07-09 "
                 "(present); votes:2019-09-09.. (cities.db, Council/D2 — named-roll era)",
         note="Re-elected 2017 to the first full 4-yr term (Jan-2018..Jan-2022). The Jan-2018 seating is "
              "still in the 2017-01..2018-06 purge gap -> start inferred (medium); vote-documented 2019+."),
    dict(body="Council", seat_id="D2", person_name="Alan Peterson", person_key="alan_peterson",
         start_date="2022-01-10", start_event="reelected", election_year="2021", end_event="did-not-run",
         confidence="high",
         sources="election:2021 (District 2 winner, def. Royce Gibson 51.85%); minutes:2022-01-10 (first "
                 "2022 meeting; present); votes:..2023-08-14 (cities.db, Council/D2)",
         note="Re-elected D2 2021 (term Jan-2022..Jan-2026, running to the city seam). NOT a candidate in "
              "the 2025 city D2 race (Longtin won) -> term ended at the 2026-01-12 city seating; mechanism "
              "(retire vs decline) unstated -> did-not-run."),
    dict(body="Council", seat_id="D2", person_name="Lyndsay Longtin", person_key="lyndsay_longtin",
         start_date="2026-01-12", start_event="elected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (CITY Council District 2 winner, def. T Jordan Hansen 58.01%); "
                 "minutes:2026-01-12 (oath — 'Lyndsay Longtin - District 2 Council Member')",
         note="First CITY-era District 2 councilmember (elected 2025, seated at the 2026-01-12 city oath). "
              "No named vote yet in cities.db (city-era minutes are narrative-tally) -> blank bounds "
              "(source limit, not a gap). Serving."),

    # ================= D3 (Cohort A: 2016 Perry -> appt. Brown -> 2019 Butterfield / 2023) =====
    dict(body="Council", seat_id="D3", person_name="Steve Perry", person_key="steve_perry",
         start_date="2017-01-01", start_event="elected", election_year="2016", end_event="vacated",
         confidence="medium",
         sources="election:2016 (Metro Township Council Seat 3 winner, def. Christopher James Geertsen "
                 "73.82%)",
         note="FOUNDING metro-township term (Cohort A). VACATED mid-term at an UNDETERMINABLE date inside "
              "the 2017-01..2018-06 PMN-purge gap (his successor Ruby Brown is already seated by the "
              "earliest recovered minutes 2018-07-09). end_date here is the CHAINING ARTIFACT of Brown's "
              "first documented presence (2018-07-09), NOT Perry's true last day — the handoff is "
              "unrecoverable. Perry casts no named vote (pre-named-roll era) -> blank bounds. Not modeled "
              "as an explicit VACANT interval because the vacancy window cannot be dated (never fabricated)."),
    dict(body="Council", seat_id="D3", person_name="Ruby Brown", person_key="ruby_brown",
         start_date="2018-07-09", start_event="appointed", election_year="", end_event="lost",
         confidence="medium",
         sources="minutes:2018-07-09..2019-12 (present as the seated D3 member — 'RUBY BROWN' in every "
                 "recovered 2018-2019 roll); votes:2019-09-09..2019-10-14 (cities.db, Council/D3, 3 named "
                 "votes); election:2019 (LOST District 3 to Chrystal Butterfield, 68.25% — Brown was the "
                 "runner-up)",
         note="APPOINTED to fill Steve Perry's mid-term D3 vacancy. The exact appointment date is "
              "UNRECOVERABLE (it falls in the 2017-01..2018-06 purge gap); start_date is her first "
              "documented presence (2018-07-09) -> medium. LOST the 2019 D3 election to Butterfield -> "
              "term ends at Butterfield's 2020-01-13 seating."),
    dict(body="Council", seat_id="D3", person_name="Chrystal Butterfield", person_key="chrystal_butterfield",
         start_date="2020-01-13", start_event="elected", election_year="2019", end_event="reelected",
         confidence="high",
         sources="election:2019 (District 3 winner, def. Ruby Brown 68.25%); minutes:2020-01-13 (first "
                 "2020 meeting; present as 'CRYSTAL BUTTERFIELD'); votes:2020-04-06..2022-01-10 "
                 "(cities.db, Council/D3)",
         note="Elected D3 2019 (defeating the appointed incumbent Ruby Brown); seated at the first "
              "documented 2020 meeting."),
    dict(body="Council", seat_id="D3", person_name="Chrystal Butterfield", person_key="chrystal_butterfield",
         start_date="2024-01-08", start_event="reelected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 3 winner, def. Christopher James Geertsen 72.22%); "
                 "minutes:2024-01-08 (oath — Bush, Schaeffer, Butterfield); minutes:2026-01-12 (present as "
                 "CITY District 3 councilmember — carried over, NOT re-sworn)",
         note="Re-elected township D3 2023 (term to Jan 2028); CONTINUES across the 2026 city seam as city "
              "District 3 — one continuous tenure. Serving."),

    # ================= D4 (Cohort B: 2016 founding / 2017 / 2021) — Snow -> Colby ==============
    dict(body="Council", seat_id="D4", person_name="Tina Snow", person_key="tina_snow",
         start_date="2017-01-01", start_event="elected", election_year="2016", end_event="reelected",
         confidence="medium",
         sources="election:2016 (Metro Township Council Seat 4 winner, unopposed 100%); minutes:2018-07-09 "
                 "(earliest recovered — present)",
         note="FOUNDING metro-township term (Cohort B, SHORT 1-yr initial term Jan-2017..Jan-2018). "
              "Seating in the PMN-purge gap -> medium."),
    dict(body="Council", seat_id="D4", person_name="Tina Snow", person_key="tina_snow",
         start_date="2018-01-01", start_event="reelected", election_year="2017", end_event="reelected",
         confidence="medium",
         sources="election:2017 (Metro Township Council Seat 4 winner, plurality over write-ins 25.86%); "
                 "minutes:2018-07-09 (present); votes:2019-09-09.. (cities.db, Council/D4)",
         note="Re-elected 2017 to the first full 4-yr term (Jan-2018..Jan-2022). Jan-2018 seating still in "
              "the purge gap -> start inferred (medium); vote-documented 2019+."),
    dict(body="Council", seat_id="D4", person_name="Tina Snow", person_key="tina_snow",
         start_date="2022-01-10", start_event="reelected", election_year="2021", end_event="did-not-run",
         confidence="high",
         sources="election:2021 (District 4 winner, unopposed 100%); minutes:2022-01-10 (present); "
                 "votes:..2022-01-10 (cities.db, Council/D4, named-roll era)",
         note="Re-elected D4 2021 (term Jan-2022..Jan-2026, running to the city seam). Did NOT run for city "
              "D4 in 2025 — she ran for the new CITY MAYOR office instead and LOST to Valdez (runner-up, "
              "57.64% Valdez); her D4 term ended at the 2026-01-12 city seating. Recorded as did-not-run "
              "(for the D4 seat)."),
    dict(body="Council", seat_id="D4", person_name="Lorrin Colby Jr.", person_key="lorrin_colby",
         start_date="2026-01-12", start_event="elected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (CITY Council District 4 winner, def. Roger C Snow 57.78%); "
                 "minutes:2026-01-12 (oath — 'Lorrin Colby, Jr. - District 4 Council Member'); "
                 "votes:2026-05-11 (cities.db, Council/D4, 1 named vote)",
         note="First CITY-era District 4 councilmember (elected 2025, seated at the 2026-01-12 city oath). "
              "Serving."),

    # ================= D5 (Cohort A: 2016 / 2019 / 2023) — Bush; the township chair-'Mayor' =====
    # D5 is ABOLISHED at the 2026 city seam (5->4 district restructure); Bush ran for the new elected
    # city Mayor and LOST. Her council service ends at the seam. She is NOT the city Mayor (Valdez is).
    dict(body="Council", seat_id="D5", person_name="Kelly Bush", person_key="kelly_bush",
         start_date="2017-01-01", start_event="elected", election_year="2016", end_event="reelected",
         confidence="medium",
         sources="election:2016 (Metro Township Council Seat 5 winner, def. Brian Richards 52.13%); "
                 "minutes:2018-07-09 (earliest recovered — present; 'Mayor Kelly Bush, Chair, presided')",
         note="FOUNDING metro-township term (Cohort A, 3-yr initial term Jan-2017..Jan-2020). Seating in "
              "the PMN-purge gap -> medium. Bush is the peer-selected Chair titled 'Mayor' (S.B.175) and "
              "VOTES as one of the five district members (roll of 5) — this is her District-5 seat, NOT a "
              "separate executive office."),
    dict(body="Council", seat_id="D5", person_name="Kelly Bush", person_key="kelly_bush",
         start_date="2020-01-13", start_event="reelected", election_year="2019", end_event="reelected",
         confidence="high",
         sources="election:2019 (District 5 winner, def. Brian Richards 69.3%); minutes:2020-01-13 (first "
                 "2020 meeting; 'Mayor Kelly Bush, Chair, presided'); votes:2019-09-09..2022-01-10 "
                 "(cities.db, Council/D5)",
         note="Re-elected D5 2019; continued as the peer-selected chair/'Mayor' (voting)."),
    dict(body="Council", seat_id="D5", person_name="Kelly Bush", person_key="kelly_bush",
         start_date="2024-01-08", start_event="reelected", election_year="2023", end_event="seat-abolished",
         end_date="2026-01-12",   # H-F (2026-07-19): chain_end_dates now KEEPS an explicit
         # end_date on a terminal tenure whose end_event is terminating (seat-abolished) —
         # there is no successor to chain from, and blanking it wrongly resurrected D5 in
         # v_council_current. The old roster_overrides.csv pin is RETIRED (same value, now
         # derived from this curated fact). See scripts/roster_HARDENING.md 2026-07-19.
         confidence="high",
         sources="election:2023 (District 5 winner, unopposed 100%); minutes:2024-01-08 (oath to Bush; "
                 "'Council Member Peterson nominated Council Member Bush as Kearns Metro Township Mayor'); "
                 "election:2025 (ran for the new CITY MAYOR office and LOST to Valdez, 57.64%); "
                 "minutes:2026-01-12 (city council seats WITHOUT a District 5 — D5 abolished by the 5->4 "
                 "restructure; Bush not among the city officials)",
         note="Last township D5 / chair-'Mayor' term. The 2026 HB35 city conversion RESTRUCTURED the 5 "
              "township districts into 4 city districts + a directly-elected Mayor, so seat D5 was "
              "ABOLISHED; Bush sought the new elected Mayor office in 2025 and LOST to Jesse Valdez. Her "
              "council service ends at the 2026-01-12 city seating. end_event=seat-abolished (the seat "
              "ceased to exist; she is NOT the city Mayor)."),

    # ================= MAYOR (city era only: 2025) — Valdez, directly-elected, VOTING ==========
    dict(body="Mayor", seat_id="MAYOR", person_name="Jesse Valdez", person_key="jesse_valdez",
         start_date="2026-01-12", start_event="elected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (CITY Mayor winner — Michael Jesse Xon Valdez, def. Tina Marie Snow "
                 "57.64%, 1,932 votes; externally verified); minutes:2026-01-12 (oath — 'Jesse Valdez - "
                 "Mayor'; presided); minutes:2026-05-11 ('Vote was 5-0' with 4 councilmembers -> the 5th "
                 "vote is the Mayor's — a VOTING mayor)",
         note="First DIRECTLY-ELECTED city Mayor (HB35 city, Utah's first Hispanic mayor). VOTES (roll of "
              "5, non_voting_mayor=False). A NEW citywide office created at the 2026 seam — NOT a "
              "continuation of the township chair-'Mayor' (that was Kelly Bush in her D5 seat; Bush lost "
              "this race to Valdez). No named vote yet attributable to Valdez in cities.db (narrative-tally "
              "era) -> blank bounds. Serving."),
]

# canonical UPPER-CASE election-name token -> person_key. Among WINNERS (the only names canon_key
# sees) every surname is unique. (Runner-up ROGER C SNOW shares SNOW with winner Tina Snow, but he
# never wins, so he is never resolved as a winner — no disambiguator needed.)
NAME_TO_KEY = {
    "SCHAEFFER": "patrick_schaeffer", "PETERSON": "alan_peterson", "PERRY": "steve_perry",
    "SNOW": "tina_snow", "BUSH": "kelly_bush", "BUTTERFIELD": "chrystal_butterfield",
    "BROWN": "ruby_brown", "LONGTIN": "lyndsay_longtin", "COLBY": "lorrin_colby",
    "VALDEZ": "jesse_valdez",
}

# cities.db person.name_key -> our person_key (only members with NAMED Council votes appear;
# Steve Perry vacated before the named-roll era, and Valdez/Longtin have cast no named vote yet
# (city-era narrative-tally) -> absent from the vote table, never mapped).
DB_KEY = {
    "patrickschaeffer": "patrick_schaeffer", "alanpeterson": "alan_peterson",
    "tinasnow": "tina_snow", "kellybush": "kelly_bush",
    "chrystalbutterfield": "chrystal_butterfield", "rubybrown": "ruby_brown",
    "lorrincolbyjr": "lorrin_colby",
}


def seat_for_contest(office, district):
    """election (office, district) -> the STABLE seat_id used as the cross-check key
    (crosscheck_field='seat_id'). Kearns: township districts 1-5 + city districts 1-4 (both
    map D<n>) + a citywide Mayor."""
    if office == "Mayor":
        return "MAYOR"
    d = district.strip()
    if d in ("1", "2", "3", "4", "5"):
        return "D" + d
    return None


REDISTRICT = Redistrict(
    plan_old=PLAN_OLD, plan_new=PLAN_NEW, plan_switch=PLAN_SWITCH,
    ord=RESTRUCTURE_ORD, adopted=RESTRUCTURE_ADOPTED,
    districts=["District 1", "District 2", "District 3", "District 4"],   # the 4 CITY districts
    # H-H (2026-07-19): the PRIOR (township) plan had FIVE districts — D5 (Bush's, the
    # chair-'Mayor' seat) was ABOLISHED at the 5->4 restructure. districts_old gives the
    # abolished D5 its own honest plan_township gap row in district_versions +
    # district_precincts instead of folding it invisibly into D1-D4's gap prose.
    districts_old=["District 1", "District 2", "District 3", "District 4", "District 5"],
    geom_ref=GEOM_REF, source_url=SRC_URL, data_floor=DATA_FLOOR,
    current_note=("CURRENT city 4-district plan, effective for representation at the 2026-01-12 city "
                  "seating (HB35 conversion legally effective 2024-05-01). geometry_ref is "
                  "geo/districts.geojson. ⚠ Only Districts 2 and 4 are authoritatively resolved (2025 "
                  "SLCo SOVC precinct->contest); Districts 1 and 3 are an UNSPLIT RESIDUAL ('1/3' — the "
                  "2025 ballot omitted D1/D3 so the D1-vs-D3 line is undetermined). precinct->district in "
                  "geo/precinct_to_district.csv, read through roster/_precinct_to_district.csv."),
    prior_adopted_by="prior plan (metro-township 5-district map)",
    prior_note=("Prior TOWNSHIP plan: 5 districts (D1-D5). Its geometry is NOT on disk -> honest GAP "
                "(blank geometry_ref, confidence low). The township 5-district map was never acquired. "
                "In force through the 2023 township elections. Never reconstructed."),
    prior_note_by_district={
        "District 5": ("Prior TOWNSHIP plan district 5 — ABOLISHED at the 2026 HB35 5->4 city "
                       "restructure (Kelly Bush's seat, the peer-selected chair-'Mayor'); no "
                       "successor plan_city2026 row exists for it BY DESIGN. Geometry NOT on disk "
                       "-> honest GAP (blank geometry_ref, confidence low); the township map was "
                       "never acquired. In force through the 2023 township elections."),
    },
    citywide_rows=[
        ("MAYOR", "current", "the directly-elected VOTING city Mayor (Jesse Valdez, 2026+)"),
    ],
    citywide_adopted_by="Kearns City (directly-elected mayor, HB35)",
    citywide_note_template=("{who}: represents the ENTIRE city. ⚠ effective_start on this row is the data "
                            "floor by library convention, but the DIRECTLY-ELECTED citywide Mayor office "
                            "only began at the 2026 city conversion; in the township era there was no "
                            "elected mayor — the presiding 'Mayor' was a peer-selected Chair holding "
                            "council District 5 (Bush). Kearns's city Mayor is a FULL VOTING member "
                            "(roll of 5)."),
    precinct_hi_source="2025",   # sidecar rows with source_year=2025 (clean D2/D4) earn confidence=high
    precinct_hi_note=("current city precinct->district from the 2025 SLCo SOVC precinct->contest "
                      "assignment, read through the roster/_precinct_to_district.csv source_year sidecar "
                      "(the canonical geo file carries no source_year column roster_lib requires — see "
                      "CLAUDE.md). Authoritative for Districts 2 and 4."),
    precinct_med_note=("D1/D3 UNSPLIT RESIDUAL: the 2025 ballot omitted Districts 1 and 3, so these "
                       "precincts are assigned only to 'District 1/3' (the D1-vs-D3 line is undetermined) "
                       "-> confidence medium, an honest residual, not a clean assignment."),
    precinct_prior_note=("Prior-plan (township 5-district) precinct->district composition NOT acquired -> "
                         "honest GAP."),
    crosscheck_districts=("2", "4"),      # only D2/D4 have clean precinct data + a 2025 by-precinct contest
    precinct_prefix="KRN", geo_seat_prefix="D",
    plan_switch_year="2025", citywide_seats=(),
)

CFG = RosterConfig(
    non_voting_mayor=False,     # Kearns's presiding officer VOTES in BOTH eras (roll of 5)
    city=CITY, city_dir=CITY_DIR, repo_root=REPO_ROOT, data_floor=DATA_FLOOR,
    geom_ref=GEOM_REF, elections_path=ELECTIONS, cities_db_path=CITIES_DB,
    overrides_path=OVERRIDES, terms_out=TERMS_OUT, districts_out=DISTRICTS_OUT,
    seat_district=SEAT_DISTRICT, name_to_key=NAME_TO_KEY, db_key=DB_KEY,
    seat_order=SEAT_ORDER,
    # municipal GENERAL winners, all Kearns years (2016 founding through 2025 city). Every winner
    # maps to a tenure -> the forward cross-check runs clean (0 drift).
    keep_election_row=lambda r: r["election_type"].strip().lower() == "municipal general",
    contest_key=seat_for_contest, crosscheck_field="seat_id",
    winners_have_district=True,
    elected_events=("elected", "reelected"),
    redistrict=REDISTRICT, precincts_out=PRECINCTS_OUT,
    precinct_map_path=PRECINCT_MAP, precincts_byprecinct_path=PRECINCTS_BYP_SRC,
)


def demo():
    def line(r):
        end = r["end_date"] or "—(serving)"
        return (f"    {r['seat_id']:<6} {r['person_name']:<22} {r['start_date']} -> {end:<12}"
                f" [{r['start_event']}/{r['end_event']}] {r['body']:<7} conf={r['confidence']}")

    print("\n(a) CURRENT council roster + mayor (end_date empty, end_event=serving):")
    for r in roster_lib.load_terms(CFG):
        if not r["end_date"] and r["end_event"] == "serving":
            print(line(r))

    print("\n(b) Roster AS OF 2019-06-01 (township era — Ruby Brown appointed to D3, Bush chairing):")
    for r in roster_lib.roster_as_of(CFG, "2019-06-01", body="Council"):
        print(line(r))

    print("\n(c) Address+date -> representatives (city era via geo/address_to_district.py):")
    addr = "5350 S 4220 W, Kearns, UT 84118"   # Kearns Library
    for d in ("2026-03-01", "2019-06-01"):
        res = roster_lib.representatives_for_address(CFG, addr, d)
        who = ", ".join(f"{x['person_name']}({x['seat_id']})" for x in res["reps"])
        loc = (f"District {res['district']} via {res.get('precinct')} [{res.get('method')}]"
               if res.get("district") else f"[{res.get('gap', '?')}]")
        print(f"  '{addr}'\n    on {d} (plan={res['plan']}): {loc}\n    -> your reps: {who or '(none — see gap)'}")

    print("\n(e) Precinct-map cross-check (district_precincts vs election outcomes; D2/D4 only):")
    roster_lib.precinct_crosscheck(CFG, verbose=True)


if __name__ == "__main__":
    rows = roster_lib.build(CFG, TENURES)
    n = {c: sum(1 for r in rows if r["confidence"] == c) for c in ("high", "medium", "low")}
    nvac = sum(1 for r in rows if r["start_event"] == "vacated")
    print(f"Wrote {os.path.relpath(TERMS_OUT, CITY_DIR)} "
          f"({len(rows)} tenures incl. {nvac} VACANT: {n['high']} high / {n['medium']} medium / {n['low']} low)")
    print(f"Wrote {os.path.relpath(DISTRICTS_OUT, CITY_DIR)} "
          f"(4 city districts x 2 plans + abolished-D5 plan_township gap row + citywide Mayor; "
          f"township->city restructure {RESTRUCTURE_ORD})")
    print(f"Wrote {os.path.relpath(PRECINCTS_OUT, CITY_DIR)} "
          f"(plan_city2026 precinct map + plan_township gap rows; districts only)")
    if "--check" in sys.argv:
        print("\nValidation: PASS (no overlaps; sources+confidence present; voting-mayor + gap/vacate guards clear).")
        print("Precinct cross-check:")
        roster_lib.precinct_crosscheck(CFG, verbose=True)
    if "--demo" in sys.argv:
        demo()
