#!/usr/bin/env python3
"""build_roster.py — rolling council-roster for EMIGRATION CANYON (a slowly-changing-
dimension / interval table of who holds each at-large council + mayor seat over time).

THIN DRIVER: this file holds only Emigration-Canyon-specific DATA (the curated TENURES
seat assignments, the name maps, the degenerate at-large district row) + config; all
generic mechanics live in ../../scripts/roster_lib.py. Modeled on the alta/nephi drivers
(the AT-LARGE / VOTING-MAYOR template) — with the peer-selected-mayor twist handled by a
separate MAYOR role-chain overlaid on the five at-large council seats.

DERIVED LAYER — regenerable, never hand-edited. Canonical inputs:
  1. election_results/emigration_canyon_results_by_candidate.csv (winners -> `elected`/`reelected` terms)
  2. cities.db  role table (city='emigration_canyon', body='Council')  (observed vote bounds; MAYOR INCLUDED)
  3. meeting_minutes/minutes/**                                  (present blocks, seatings, appointments, mayor selection)
  4. roster/roster_overrides.csv                                 (hand corrections; applied LAST)

Usage:
  python3 roster/build_roster.py            # regenerate the CSVs
  python3 roster/build_roster.py --demo     # regenerate + print the demo queries
  python3 roster/build_roster.py --check    # regenerate + run validations only

Cardinal rule (repo CLAUDE.md): NEVER fabricate. Unknown seat-holder / date ->
UNKNOWN/VACANT + confidence=low/medium + a note, never a guess. Honest gaps are data.

STRUCTURAL FACTS (verified in source):
  * ONE 5-member, ALL-AT-LARGE council throughout a FORM CHANGE: Emigration Canyon
    incorporated as a **Metro Township** (effective 2017-01-01) and converted to a **CITY**
    effective 2024-05-01 (H.B. 35). Same body; the vintage is carried in each minutes doc's
    provenance. No districts -> district_versions is a single DEGENERATE row.
  * The MAYOR is PEER-SELECTED (one of the five at-large members, chosen by the council) and
    PRESIDES AND VOTES (the Millcreek pattern — mayor counted in the five, max roll = 5), NOT
    an executive non-voting mayor -> `non_voting_mayor=False`: the MAYOR rows carry REAL
    cities.db vote bounds and the mayor sits in `db_key`. Because the mayor is one of the five,
    the MAYOR seat is a ROLE OVERLAY (a separate role-chain), and the mayor ALSO holds an
    at-large council seat at the same time (his votes/bounds appear on both rows).
  * TWO MAYORS in the recovered record: **Joe Smolka** (2017 -> departed end of 2025) ->
    **David Brems** (peer-selected at the 2026-01-20 reorganization). Smolka presided every
    recovered meeting (township + city eras) through 2025-12-15; Brems was sworn Mayor
    2026-01-20 (referred to as "mayor-elect" already in the 2025-12-15 minutes).
  * DATA FLOOR 2017, but recovered minutes begin **2018-10** — PMN purged its 2017 (+ scattered
    2018-mid-2019) file store upstream (HONEST GAP, logged in minutes_unrecovered.csv). Members
    who were serving at the first recovered meeting (2018-10-25) but are NOT on the 2016 initial
    slate (Staggers/Raile/Smolka/Bowen/Christensen) joined by appointment in that purged window
    -> that PRE-ELECTION segment starts at 2018-10-25 (first observed), confidence=medium. Brems
    (AL-2) & Hawkes (AL-3) then WON the Nov-2019 general (3-seat at-large race, with Harris AL-4)
    and were sworn to ELECTED terms 2020-01-23 -> a second, high-confidence tenure per member
    (the 2019 contest was recovered 2026-07-17 into *_races.csv; the county SOVC had privacy-
    suppressed the candidate rows, so it is absent from *_results_by_candidate.csv). Smolka & Bowen
    ARE 2016 founders (+ 2017 re-election in-data) on the OTHER, staggered cohort (not up in 2019)
    -> start 2017-01-01, medium (continuous service across the 2019 + 2021 no-township-contest
    cycles inferred).
  * NARRATIVE-TALLY council: cities.db carries NAMED council votes only for the five people who
    ever cast a recorded contested/dissent vote (Brems, Smolka, Harris, Hawkes, Pinon); Bowen,
    Paine, Hook, Griffith never appear in a named roll (majority stays unnamed) -> their
    first_vote/last_vote are honestly BLANK. A blank bound here is a source ceiling, not a gap.

  * The five at-large SEAT chains (seat numbers are LABELS for the person-chains — all at-large,
    so within-body seat numbering is not source-attested; flagged in notes). Reconstructed from
    the meeting-by-meeting present blocks:
      AL-1  Smolka (2017 -> 2025-12-15) -> [VACANT] -> Griffith (appointed 2026-01-20)
      AL-2  Brems  (2018-10 -> present; peer-selected MAYOR 2026-01-20, keeps this seat)
      AL-3  Hawkes (2018-10 -> present; Deputy Mayor throughout)
      AL-4  Paine (2018-10 -> 2019-06) -> Hook (2019-08 -> 2019-12) -> Harris (2020-01 -> present)
      AL-5  Bowen  (2017 -> 2021-12) -> Pinon (appointed 2022-01 -> present; elected 2025)
  * The Nov-2025 / Jan-2026 reorganization (all documented at 2026-01-20):
      - Pinon sworn to his 2025-elected term; Brems sworn as (peer-selected) Mayor;
      - Smolka departed MID-TERM (last meeting 2025-12-15; "Mid-Term Vacancy Public Notice"
        2026-01-05) -> his AT-LARGE seat (AL-1) was advertised, applicants interviewed, and
        filled by WRITTEN-BALLOT appointment of Griffith ("the majority vote was for Nicholas
        Griffith ... administered the Oath of Office to Nicholas Griffith"). Griffith did NOT
        win a 2025 election (only Pinon's seat was on the 2025 ballot). An explicit VACANT
        interval [2025-12-16, 2026-01-20) spans the empty seat (medium — the exact effective
        resignation date is unstated, and the window contains the 2026-01-01/2026-01-05 notices
        logged as un-recovered).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.dirname(HERE)              # emigration_canyon_city_council/
REPO_ROOT = os.path.dirname(CITY_DIR)         # civic-data/
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import roster_lib
from roster_lib import RosterConfig

ELECTIONS = os.path.join(CITY_DIR, "election_results",
                         "emigration_canyon_results_by_candidate.csv")
CITIES_DB = os.path.join(REPO_ROOT, "cities.db")
OVERRIDES = os.path.join(HERE, "roster_overrides.csv")
TERMS_OUT = os.path.join(HERE, "council_terms.csv")
DISTRICTS_OUT = os.path.join(HERE, "district_versions.csv")

CITY = "emigration_canyon"
DATA_FLOOR = "2017-01-01"        # metro-township incorporation (recovered minutes begin 2018-10)
GEOM_REF = "geo/city_boundary.geojson"

TENURES = [
    # ==== Seat AL-1  (Smolka -> [VACANT] -> Griffith; Smolka was the peer-selected MAYOR) ====
    dict(body="Council", seat_id="AL-1", person_name="Joe Smolka", person_key="joe_smolka",
         start_date="2017-01-01", start_event="elected", election_year="2017",
         end_event="resigned", confidence="medium",
         vacate_date="2025-12-16", vacate_confidence="medium",
         vacate_source="minutes:2025-12-15 (last presided as Mayor); 'Mid-Term Vacancy Public Notice - Council Member At-Large' 2026-01-05 (minutes_unrecovered.csv); seat filled by Griffith 2026-01-20",
         sources="election:2017 (Council At-Large winner, 338 rank1); 2016 initial township slate (Staggers/Raile/Smolka/Bowen/Christensen — election_results/CLAUDE.md external cross-check); minutes:2018-10-25..2025-12-15 (present as Mayor every recovered meeting)",
         note="PRE-FLOOR start: 2016 founder + 2017 re-election; took office at the 2017-01-01 incorporation; recovered minutes begin 2018-10 (PMN purged the 2017 store) -> medium. Continuous service across the 2019 (no Emigration SOVC rows) + 2021 (no township council contest) cycles is inferred. Also the PEER-SELECTED voting MAYOR the entire time (see MAYOR row) — his votes/bounds appear on both. Departed MID-TERM end of 2025; his at-large seat went to Griffith by appointment 2026-01-20. Seat numbers are labels of the person-chains (all at-large)."),
    dict(body="Council", seat_id="AL-1", person_name="Nicholas Griffith", person_key="nicholas_griffith",
         start_date="2026-01-20", start_event="appointed", election_year="",
         end_event="serving", confidence="high",
         sources="minutes:2026-01-20 ('After each council member submitting a written vote, the majority vote was for Nicholas Griffith'; 'City Recorder Diana Baun then administered the Oath of Office to Nicholas Griffith'); 'Mid-Term Vacancy Public Notice - Council Member At-Large' 2026-01-05",
         note="APPOINTED by council written ballot to fill the mid-term at-large vacancy created by Smolka's departure — NOT elected (did not win the 2025 election; only Pinon's seat was on the 2025 ballot — election_results/CLAUDE.md). Interviewed against Camille Erickson & Janet Haskell; present as Council Member 2026-01-20 -> ."),

    # ==== Seat AL-2  (David Brems — continuous; peer-selected MAYOR from 2026) ================
    dict(body="Council", seat_id="AL-2", person_name="David Brems", person_key="david_brems",
         start_date="2018-10-25", start_event="appointed", election_year="",
         end_event="reelected", confidence="medium",
         sources="minutes:2018-10-25..2019-12-12 (present as Council Member every recovered meeting)",
         note="PRE-FLOOR origin: NOT on the 2016 initial slate (Staggers/Raile/Smolka/Bowen/Christensen) -> joined by appointment in the purged 2017–mid-2018 window; first observed at the data floor 2018-10-25 (earlier PMN purged) -> start_event=appointed, medium. WON the Nov-2019 general and was sworn to an ELECTED term 2020-01-23 (next row) — the prior 'appointed 2018' label covers only THIS pre-election segment."),
    dict(body="Council", seat_id="AL-2", person_name="David Brems", person_key="david_brems",
         start_date="2020-01-23", start_event="reelected", election_year="2019",
         end_event="reelected", confidence="high",
         sources="election:2019 (Council At-Large winner, 271 — 3-seat race, canvass-confirmed by the 2019-11-19 Township Board of Canvassers; election_results/emigration_canyon_races.csv year=2019, RECOVERED 2026-07-17 — the SLCo SOVC had privacy-suppressed the candidate rows); minutes:2020-01-23 ('Nichole Watt administered the Oath of Office to re-elect Council Members Jennifer Hawkes and David Brems and newly elected Council Member Catherine Harris')",
         note="RE-ELECTED at the Nov-2019 general (271 votes; Hawkes 300 + Harris 241 also elected in the 3-seat at-large race) and sworn to a new term 2020-01-23 — a DOCUMENTED elected term (minutes oath), NOT the prior appointment. The 2019 win was recovered 2026-07-17 into emigration_canyon_races.csv (the county SOVC had privacy-suppressed the candidate rows, so it is absent from *_results_by_candidate.csv and the forward crosscheck). Re-elected again 2023 (next row)."),
    dict(body="Council", seat_id="AL-2", person_name="David Brems", person_key="david_brems",
         start_date="2024-01-23", start_event="reelected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (Council At-Large winner, 277; tied with Hawkes, both seated in the 3-seat race); minutes:2024-01-23 (first meeting of the term, present)",
         note="Won the 2023 general. Became PEER-SELECTED MAYOR 2026-01-20 while RETAINING this at-large council seat — the mayoralty is a role overlay (see MAYOR row), not a separate membership, so this AL-2 tenure continues uninterrupted."),

    # ==== Seat AL-3  (Jennifer Hawkes — continuous; Deputy Mayor) =============================
    dict(body="Council", seat_id="AL-3", person_name="Jennifer Hawkes", person_key="jennifer_hawkes",
         start_date="2018-10-25", start_event="appointed", election_year="",
         end_event="reelected", confidence="medium",
         sources="minutes:2018-10-25..2019-12-12 (present as Council Member; Deputy Mayor from ~2020)",
         note="PRE-FLOOR origin: not on the 2016 initial slate -> joined by appointment pre-floor; first observed 2018-10-25 (earlier PMN purged) -> medium. Serves as DEPUTY MAYOR throughout the recovered record. WON the Nov-2019 general and was sworn to an ELECTED term 2020-01-23 (next row) — the prior 'appointed 2018' label covers only THIS pre-election segment."),
    dict(body="Council", seat_id="AL-3", person_name="Jennifer Hawkes", person_key="jennifer_hawkes",
         start_date="2020-01-23", start_event="reelected", election_year="2019",
         end_event="reelected", confidence="high",
         sources="election:2019 (Council At-Large winner, 300 — TOP vote-getter, 3-seat race, canvass-confirmed by the 2019-11-19 Township Board of Canvassers; election_results/emigration_canyon_races.csv year=2019, RECOVERED 2026-07-17 — the SLCo SOVC had privacy-suppressed the candidate rows); minutes:2020-01-23 ('Nichole Watt administered the Oath of Office to re-elect Council Members Jennifer Hawkes and David Brems and newly elected Council Member Catherine Harris')",
         note="RE-ELECTED at the Nov-2019 general (300 votes, top vote-getter of the 3-seat at-large race) and sworn to a new term 2020-01-23 — a DOCUMENTED elected term (minutes oath), NOT the prior appointment. The win was recovered 2026-07-17 into emigration_canyon_races.csv (county SOVC had privacy-suppressed the rows). Continues as Deputy Mayor. Re-elected again 2023 (next row)."),
    dict(body="Council", seat_id="AL-3", person_name="Jennifer Hawkes", person_key="jennifer_hawkes",
         start_date="2024-01-23", start_event="reelected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (Council At-Large winner, 277; tied with Brems, both seated); minutes:2024-01-23 (present, Deputy Mayor)",
         note="2023 general winner. Continues as Deputy Mayor."),

    # ==== Seat AL-4  (Paine -> Hook -> Harris) ===============================================
    dict(body="Council", seat_id="AL-4", person_name="Robert Paine", person_key="robert_paine",
         start_date="2018-10-25", start_event="appointed", election_year="",
         end_event="resigned", confidence="medium",
         sources="minutes:2018-10-25..2019-06-19 (present as Council Member, 6 recovered meetings)",
         note="PRE-FLOOR origin (not on the 2016 slate; first observed 2018-10-25). Departed mid-2019 (last meeting 2019-06-19); replaced by Hook 2019-08-22 (appointment — no 2019 Emigration rows in the SOVC). Mechanism unstated -> resigned/departed. medium."),
    dict(body="Council", seat_id="AL-4", person_name="Steve Hook", person_key="steve_hook",
         start_date="2019-08-22", start_event="appointed", election_year="",
         end_event="resigned", confidence="medium",
         sources="minutes:2019-08-22..2019-12-12 (present as Council Member, 5 recovered meetings)",
         note="APPOINTED to the Paine vacancy (first present 2019-08-22; no 2019 election in the SOVC). Brief tenure — departed after 2019-12-12; Harris seated 2020-01-23. Appointment/departure inferred from the present blocks -> medium."),
    dict(body="Council", seat_id="AL-4", person_name="Catherine Harris", person_key="catherine_harris",
         start_date="2020-01-23", start_event="elected", election_year="2019",
         end_event="reelected", confidence="high",
         sources="election:2019 (Council At-Large winner, 241 — 3-seat race, canvass-confirmed by the 2019-11-19 Township Board of Canvassers; election_results/emigration_canyon_races.csv year=2019, RECOVERED 2026-07-17 — the SLCo SOVC had privacy-suppressed the candidate rows); minutes:2020-01-23 ('Nichole Watt administered the Oath of Office to ... newly elected Council Member Catherine Harris')",
         note="ELECTED (NEWLY) at the Nov-2019 general (241 votes, 3-seat at-large race) and sworn 2020-01-23 — she WON the AL-4 seat that the appointed Hook (2019-08..2019-12) had briefly held; she was NOT herself appointed. The earlier 'appointed 2020-01-23' label predated the 2019-race recovery (2026-07-17 into emigration_canyon_races.csv; the county SOVC had privacy-suppressed the rows). Re-elected 2023 (next row)."),
    dict(body="Council", seat_id="AL-4", person_name="Catherine Harris", person_key="catherine_harris",
         start_date="2024-01-23", start_event="reelected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (Council At-Large winner, 298 rank1 — top vote-getter); minutes:2024-01-23 (present)",
         note="2023 general top vote-getter (298). Continuous service since her 2020 appointment."),

    # ==== Seat AL-5  (Bowen -> Pinon) ========================================================
    dict(body="Council", seat_id="AL-5", person_name="Gary Bowen", person_key="gary_bowen",
         start_date="2017-01-01", start_event="elected", election_year="2017",
         end_event="unknown", confidence="medium",
         sources="election:2017 (Council At-Large winner, 320 rank2); 2016 initial township slate (external cross-check); minutes:2018-10-25..2021-12-14 (present as Council Member)",
         note="PRE-FLOOR start: 2016 founder + 2017 re-election; recovered minutes begin 2018-10 -> medium. Departed end of 2021 (last meeting 2021-12-14); replaced by Pinon 2022-01-25 (appointment — no 2021 township council contest in the SOVC). Mechanism unstated (did-not-run/resigned) -> unknown. Continuous service across the 2021 no-contest cycle inferred."),
    dict(body="Council", seat_id="AL-5", person_name="Robert Pinon", person_key="robert_pinon",
         start_date="2022-01-25", start_event="appointed", election_year="",
         end_event="reelected", confidence="medium",
         sources="minutes:2022-01-25..2025-12-15 (present as Council Member; first present 2022-01-25 replacing Bowen)",
         note="APPOINTED to the Bowen vacancy (first present 2022-01-25; no 2021 township council contest in the SOVC) -> medium. Re-elected 2025 (next row)."),
    dict(body="Council", seat_id="AL-5", person_name="Robert Pinon", person_key="robert_pinon",
         start_date="2026-01-20", start_event="reelected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Council At-Large winner, 324; general — the only seat on the 2025 ballot); minutes:2026-01-20 ('administered the Oath of Office to Council Member Robert Pinon and Mayor David Brems')",
         note="Won the 2025 general (only one seat was up); sworn to the new term 2026-01-20 alongside Mayor Brems. Same seat as his 2022 appointment (no gap)."),

    # ==== Seat MAYOR  (Smolka -> Brems; peer-selected, the Mayor VOTES) ======================
    dict(body="Mayor", seat_id="MAYOR", person_name="Joe Smolka", person_key="joe_smolka",
         start_date="2017-01-01", start_event="became-mayor", election_year="",
         end_event="resigned", confidence="medium",
         sources="minutes:2018-10-25..2025-12-15 ('Mayor Smolka, Chair, presided' at every recovered meeting, township + city eras)",
         note="PEER-SELECTED voting Mayor (one of the five at-large members, chosen by the council; presides AND votes — max roll 5, the Millcreek pattern). Held the mayoralty continuously across the township->city conversion (2024-05-01). Selection date pre-floor (2017; earlier minutes purged) -> medium start. ALSO holds council seat AL-1 (his votes/bounds appear on both rows). Departed MID-TERM end of 2025 (last presided 2025-12-15); the mayoralty passed to Brems at the 2026-01-20 reorganization (clean handoff — no meeting occurred in the interim; the mid-term VACANCY was on his COUNCIL seat, filled by Griffith)."),
    dict(body="Mayor", seat_id="MAYOR", person_name="David Brems", person_key="david_brems",
         start_date="2026-01-20", start_event="became-mayor", election_year="",
         end_event="serving", confidence="high",
         sources="minutes:2026-01-20 ('City Recorder Diana Baun ... administered the Oath of Office to ... Mayor David Brems'; 'Mayor David Brems, presiding'); minutes:2025-12-15 (already referred to as the 'mayor-elect')",
         note="PEER-SELECTED as Mayor at the 2026-01-20 reorganization, succeeding the departed Smolka. Retains his AL-2 council seat (the mayoralty is a role overlay). Voting Mayor (max roll 5)."),
]

SEAT_ORDER = ["AL-1", "AL-2", "AL-3", "AL-4", "AL-5", "MAYOR"]
SEAT_DISTRICT = {s: "At-Large" for s in SEAT_ORDER}

# canonical UPPER-CASE election name token -> person_key. Election names are verbatim
# UPPER-CASE ('DAVID PAUL BREMS', 'CATHERINE M HARRIS', 'ROBERTO PINON'); canon_key splits
# into tokens and matches the surname. No shared surnames (two Roberts differ: PAINE vs PINON).
NAME_TO_KEY = {
    "SMOLKA": "joe_smolka",
    "BOWEN": "gary_bowen",
    "BREMS": "david_brems",
    "HAWKES": "jennifer_hawkes",
    "HARRIS": "catherine_harris",
    "PINON": "robert_pinon",
    "PAINE": "robert_paine",
    "HOOK": "steve_hook",
    "GRIFFITH": "nicholas_griffith",
}

# cities.db person.name_key -> our person_key. The MAYOR (Smolka / Brems) IS in this map
# because the Emigration Canyon mayor VOTES on council motions (non_voting_mayor=False).
# Only five people ever cast a NAMED council vote (narrative-tally council); Bowen/Paine/Hook/
# Griffith carry no db name_key yet (their bounds are honestly blank) — mapped here anyway so
# a future refresh that names them is picked up automatically (unknown keys are ignored).
DB_KEY = {
    "davidbrems": "david_brems",
    "joesmolka": "joe_smolka",
    "catherineharris": "catherine_harris",
    "jenniferhawkes": "jennifer_hawkes",
    "robertpinon": "robert_pinon",
    "garybowen": "gary_bowen",
    "robertpaine": "robert_paine",
    "stevehook": "steve_hook",
    "nicholasgriffith": "nicholas_griffith",
}

ATLARGE = dict(
    district_id="At-Large", plan_id="current",
    effective_start=DATA_FLOOR, effective_end="",
    geometry_ref=GEOM_REF, adopted_by="Emigration Canyon at-large council structure",
    source_url="", confidence="high",
    note=("DEGENERATE: Emigration Canyon's five council members are all elected AT-LARGE — "
          "no wards/districts, no address->district tool (single-polygon canyon boundary; "
          "geo/CLAUDE.md). This single row covers the whole city. geometry_ref points at the "
          "existing city-boundary artifact. effective_start = incorporation (2017-01-01); the "
          "at-large structure spans both the metro-township and city eras unchanged."),
)

CFG = RosterConfig(
    non_voting_mayor=False,        # the Emigration Canyon Mayor is peer-selected AND VOTES
    city=CITY, city_dir=CITY_DIR, repo_root=REPO_ROOT, data_floor=DATA_FLOOR,
    geom_ref=GEOM_REF, elections_path=ELECTIONS, cities_db_path=CITIES_DB,
    overrides_path=OVERRIDES, terms_out=TERMS_OUT, districts_out=DISTRICTS_OUT,
    seat_district=SEAT_DISTRICT, name_to_key=NAME_TO_KEY, db_key=DB_KEY,
    seat_order=SEAT_ORDER,
    # municipal GENERAL winners only (drops the 2025 municipal primary). Every general winner
    # PRESENT in *_results_by_candidate.csv (2017 Smolka/Bowen, 2023 Harris/Hawkes/Brems, 2025
    # Pinon) maps to an elected/reelected tenure. The 2019 winners (Hawkes/Brems/Harris — the
    # 3-seat at-large race) carry election_year=2019 tenures citing *_races.csv, but are ABSENT
    # from *_results_by_candidate.csv (the county SOVC privacy-suppressed those candidate rows;
    # the contest was recovered 2026-07-17 into *_races.csv) so they are not forward-crosschecked
    # — by design, not a gap. Griffith (appointed) + Pinon (pre-2025 appointment) carry blank
    # election_year and are likewise excluded from the forward crosscheck.
    keep_election_row=lambda r: "general" in r["election_type"].lower(),
    contest_key=lambda office, district: office,   # office (Council) == body; at-large, no district
    crosscheck_field="body", winners_have_district=False,
    winner_offices=("Council",),                   # no separately-elected Mayor exists in the data
    elected_events=("elected", "reelected", "became-mayor"),
    atlarge=ATLARGE,
)


def demo():
    def line(r):
        end = r["end_date"] or "—(serving)"
        return (f"  {r['seat_id']:<6} {r['person_name']:<18} {r['start_date']} -> {end:<12} "
                f"[{r['start_event']}/{r['end_event']}] conf={r['confidence']}")

    print("\n(a) CURRENT roster (end_date empty, end_event=serving):")
    for r in roster_lib.load_terms(CFG):
        if not r["end_date"] and r["end_event"] == "serving":
            print(line(r))

    print("\n(b) Roster AS OF 2020-06-01 (township era — Hook->Harris seam just past; Smolka Mayor):")
    for r in roster_lib.roster_as_of(CFG, "2020-06-01", body="Council"):
        print(line(r))
    print("    Mayor:")
    for r in roster_lib.roster_as_of(CFG, "2020-06-01", body="Mayor"):
        print(line(r))

    print("\n(c) Roster AS OF 2026-01-01 (mid-vacancy: Smolka gone, AL-1 VACANT, Brems not yet Mayor):")
    for r in roster_lib.roster_as_of(CFG, "2026-01-01", body="Council"):
        print(line(r))
    print("    Mayor:")
    for r in roster_lib.roster_as_of(CFG, "2026-01-01", body="Mayor"):
        print(line(r))


if __name__ == "__main__":
    rows = roster_lib.build(CFG, TENURES)
    n_high = sum(1 for r in rows if r["confidence"] == "high")
    n_med = sum(1 for r in rows if r["confidence"] == "medium")
    n_low = sum(1 for r in rows if r["confidence"] == "low")
    nvac = sum(1 for r in rows if r["person_name"] == "VACANT")
    print(f"Wrote {TERMS_OUT} ({len(rows)} tenures: {n_high} high / {n_med} medium / "
          f"{n_low} low; {nvac} VACANT interval(s))")
    print(f"Wrote {DISTRICTS_OUT} (1 district — At-Large, degenerate)")
    if "--check" in sys.argv:
        print("\nValidation: PASS (no overlaps; every row has sources+confidence).")
    if "--demo" in sys.argv:
        demo()
