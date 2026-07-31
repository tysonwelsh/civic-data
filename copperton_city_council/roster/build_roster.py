#!/usr/bin/env python3
"""build_roster.py — rolling council-roster for the Town of Copperton (a slowly-changing-
dimension / interval table of who holds each at-large council + mayor seat over time).

THIN DRIVER: this file holds only Copperton-specific DATA (the curated TENURES seat
assignments, the name maps, the at-large district row) + config; all generic mechanics
live in ../scripts/roster_lib.py. Modeled on the bluffdale driver (the AT-LARGE template).

DERIVED LAYER — regenerable, never hand-edited. Canonical inputs:
  1. election_results/copperton_results_by_candidate.csv  (winners -> `elected` terms)
  2. cities.db  role table (city='copperton')            (observed NAMED-vote bounds)
  3. meeting_minutes/minutes/**                           (oath / appointment / resignation / canvass)
  4. roster/roster_overrides.csv                          (hand corrections; applied LAST)

Usage:
  python3 roster/build_roster.py            # regenerate the CSVs
  python3 roster/build_roster.py --demo     # regenerate + print the demo queries
  python3 roster/build_roster.py --check    # regenerate + run validations only

Cardinal rule (repo CLAUDE.md): NEVER fabricate. Unknown seat-holder / date ->
UNKNOWN + confidence=low + a note, never a guess. Honest gaps are data.

STRUCTURAL FACTS (verified in source minutes; see roster/CLAUDE.md for the full write-up):
  * ~800-pop town, SPARSE by design (~11-12 mtgs/yr) and almost entirely NARRATIVE-TALLY.
    Data floor 2017 (incorporated as a metro township 2017-01-01); the 2017-02 -> 2018-06
    record is a GENUINE PMN retention purge (unrecoverable — honest gap). Earliest recovered
    minutes: 2018-07-18.
  * 5 voting positions the ENTIRE time (max roll = 5). Metro Township 2017 -> TOWN (HB35)
    effective 2024-05-01; the first directly-elected Town Mayor (Sean Clayton) was seated
    2026-01-21. The presiding officer VOTES in BOTH eras (Chair titled "Mayor" per S.B.175;
    verified: 2018-07-18 'Mayor Clayton voting Aye' as the 5th roll; 2020-03-18 'Mayor
    Clayton voted Nay' in a 3-2) -> non_voting_mayor=False; kept in DB_KEY.
  * The presiding officer is PEER-SELECTED from the council (no separately-elected mayor in
    the township era). Sean Clayton chaired throughout; he won township seat 'At-Large B'
    (2019 canvass + 2023) and then the FIRST directly-elected Town Mayor race in 2025.
  * Seat model — 5 AT-LARGE seats (lettered A-E, town-wide — NOT districts), two cohorts:
    - Cohort A/B/C (3 seats, 2019 / 2023 cycle): AL-A (Bailey), MAYOR (=former At-Large B,
      Clayton), AL-C (Patrick->Stitzer).
    - Cohort D/E (2 seats, 2017 / 2021 / 2025 cycle): AL-D (Pazell->Olsen->McCalmon),
      AL-E (Severson->Pratt).
  * seat_id MAYOR = the PRESIDING-OFFICER chain (the former township At-Large B seat).
    Clayton carries it CONTINUOUSLY: body=Council (peer-selected Chair/"Mayor", VOTES) through
    2025, then body=Mayor (directly-elected Town Mayor) from 2026-01-21. Same person, so the
    chain closes without any absorbed/orphan seat.
  * Two documented mid-term vacancies (VACANT-interval convention):
    - Pazell (AL-D) RESIGNED (announced 2020-10-21, moved away) -> Olsen APPOINTED 2020-11-18
      (from applicants Green & Olsen; first vote 2020-12-16).
  * The 2019 A/B/C township general is ABSENT from the county SOVC archive, BUT the
    2019-11-19 minutes canvass documents the winners verbatim ("At Large A: Kathleen Bailey /
    At Large B: Sean Clayton / At Large C: Tessa Stitzer") -> those 2019 seatings are anchored
    to the MINUTES (high), not the missing CSV. The 2025 Town Mayor + seats D/E were
    UNOPPOSED and NOT tabulated by the county -> anchored to the 2026-01-21 oath (honest gap
    on the tally). Terms commence Jan 1 (2019-11-19 minutes).
  * SPARSE / TALLY-ONLY: 3-8 named votes per member over years. first_vote/last_vote are loose
    in-window activity bounds, NOT term boundaries. McCalmon casts no named vote yet (absent
    from cities.db) -> no vote bounds; that is the source, not a gap.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.dirname(HERE)              # copperton_city_council/
REPO_ROOT = os.path.dirname(CITY_DIR)         # civic-data/
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import roster_lib
from roster_lib import RosterConfig

ELECTIONS = os.path.join(CITY_DIR, "election_results", "copperton_results_by_candidate.csv")
CITIES_DB = os.path.join(REPO_ROOT, "cities.db")
OVERRIDES = os.path.join(HERE, "roster_overrides.csv")
TERMS_OUT = os.path.join(HERE, "council_terms.csv")
DISTRICTS_OUT = os.path.join(HERE, "district_versions.csv")

CITY = "copperton"
DATA_FLOOR = "2017-01-01"        # incorporated as a metro township Jan 2017 (2017-02..2018-06 PMN-purged; earliest recovered 2018-07-18)
GEOM_REF = "geo/city_boundary.geojson"

TENURES = [
    # ================= Seat MAYOR — the presiding-officer chain (former At-Large B) =================
    # Sean Clayton, peer-selected voting Chair/"Mayor" (body=Council) 2017-2025, then the
    # directly-elected executive Town Mayor (body=Mayor) from 2026. Same person throughout.
    dict(body="Council", seat_id="MAYOR", person_name="Sean Clayton", person_key="sean_clayton",
         start_date="2017-01-01", start_event="elected", election_year="2016", confidence="medium",
         end_event="reelected",
         sources="minutes:2018-07-18 (earliest recovered — present; 'Mayor Clayton, Chair, presided'; votes as the 5th roll 'Mayor Clayton voting Aye')",
         note="Founding metro-township council; the 2017-02->2018-06 record is a GENUINE PMN purge (honest gap). Chair titled 'Mayor' by courtesy (S.B.175, May 2018) and VOTES. seat_id MAYOR = the presiding-officer chain (the former township At-Large B seat)."),
    dict(body="Council", seat_id="MAYOR", person_name="Sean Clayton", person_key="sean_clayton",
         start_date="2020-01-01", start_event="reelected", election_year="2019", confidence="high",
         end_event="reelected",
         sources="minutes:2019-11-19 (canvass — 'At Large B: Sean Clayton'); minutes:2022-01-19 (elected Mayor of the township council)",
         note="2019 A/B/C general is absent from the county SOVC but the 2019-11-19 minutes canvass names the winner. Terms commence Jan 1 (per 2019-11-19 minutes)."),
    dict(body="Council", seat_id="MAYOR", person_name="Sean Clayton", person_key="sean_clayton",
         start_date="2024-01-17", start_event="reelected", election_year="2023", confidence="high",
         end_event="became-mayor",
         sources="election:2023 (Council 'At-Large B' winner, 98, unopposed); minutes:2024-01-17 (oath — Clayton, Stitzer, Bailey; 'the mayor's seat would become an elected office going forward')",
         note="Last township chair-mayor term; converts to the directly-elected Town Mayor at the 2024-05-01 HB35 seam (first mayor election 2025)."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Sean Clayton", person_key="sean_clayton",
         start_date="2026-01-21", start_event="became-mayor", election_year="2025", confidence="high",
         end_event="serving",
         sources="election:2025 (first Town Mayor — UNOPPOSED, NOT tabulated by the county; honest gap); minutes:2026-01-21 (oath — 'Mayor Sean Clayton')",
         note="Converted from peer-selected Chair/'Mayor' to the DIRECTLY-ELECTED executive Town Mayor (HB35). Ran unopposed so the county published no tally; the 2026-01-21 oath documents the seating. Continues to VOTE (max roll 5)."),

    # ================= Seat AL-A — Bailey (three terms) =================
    dict(body="Council", seat_id="AL-A", person_name="Kathleen Bailey", person_key="kathleen_bailey",
         start_date="2017-01-01", start_event="elected", election_year="2016", confidence="medium",
         end_event="reelected",
         sources="minutes:2018-07-18 (present)",
         note="Founding metro-township council (pre-data; 2017 purge gap). Cohort A/B/C."),
    dict(body="Council", seat_id="AL-A", person_name="Kathleen Bailey", person_key="kathleen_bailey",
         start_date="2020-01-01", start_event="reelected", election_year="2019", confidence="high",
         end_event="reelected",
         sources="minutes:2019-11-19 (canvass — 'At Large A: Kathleen Bailey')",
         note="2019 general absent from county SOVC; anchored to the minutes canvass. Terms commence Jan 1."),
    dict(body="Council", seat_id="AL-A", person_name="Kathleen Bailey", person_key="kathleen_bailey",
         start_date="2024-01-17", start_event="reelected", election_year="2023", confidence="high",
         end_event="serving",
         sources="election:2023 (Council 'At-Large A' winner, 118, unopposed); minutes:2024-01-17 (oath)",
         note="Long-serving member (Treasurer role)."),

    # ================= Seat AL-C — Patrick -> Stitzer =================
    dict(body="Council", seat_id="AL-C", person_name="Ron Patrick", person_key="ron_patrick",
         start_date="2017-01-01", start_event="elected", election_year="2016", confidence="medium",
         end_event="unknown",
         sources="minutes:2018-07-18 (present); minutes:2019-12-18 ('this is his final Council meeting')",
         note="Founding metro-township council (pre-data; 2017 purge gap). Did not continue on seat C — the 2019 canvass gave At-Large C to Stitzer; mechanism (lost vs did-not-file) unrecorded -> unknown. Ran 2021 for seat E as a write-in and lost by 1 vote (see AL-E)."),
    dict(body="Council", seat_id="AL-C", person_name="Tessa Stitzer", person_key="tessa_stitzer",
         start_date="2020-01-01", start_event="elected", election_year="2019", confidence="high",
         end_event="reelected",
         sources="minutes:2019-11-19 (canvass — 'At Large C: Tessa Stitzer'); minutes:2020-01-15 (serving)",
         note="2019 general absent from county SOVC but named in the minutes canvass; terms commence Jan 1 (seated 2020-01-01, present 2020-01-15)."),
    dict(body="Council", seat_id="AL-C", person_name="Tessa Stitzer", person_key="tessa_stitzer",
         start_date="2024-01-17", start_event="reelected", election_year="2023", confidence="high",
         end_event="serving",
         sources="election:2023 (Council 'At-Large C' winner, 143, unopposed); minutes:2024-01-17 (oath); minutes:2026-01-21 (Mayor Pro Tempore)",
         note="Deputy Mayor / Mayor Pro Tempore."),

    # ================= Seat AL-D — Pazell -> Olsen -> McCalmon =================
    dict(body="Council", seat_id="AL-D", person_name="Apollo Pazell", person_key="apollo_pazell",
         start_date="2018-01-01", start_event="elected", election_year="2017", confidence="medium",
         end_event="resigned",
         vacate_date="2020-10-21", vacate_confidence="high",
         vacate_source="minutes:2020-10-21 ('Council Member Apollo Pazell has resigned due to his [move]'; Council reviewed the process to fill the vacant seat)",
         sources="election:2017 (Council At-Large winner, 111, founding vote-for-2 D/E cycle); minutes:2018-07-18 (present, Deputy Mayor)",
         note="Elected 2017 (vote-for-2 founding D/E cohort) -> term start Jan 2018 (the pre-seating founding year 2017 is in the PMN purge gap -> not rostered, honest gap). RESIGNED Oct 2020 (moved away; last present/vote 2020-09-16) -> explicit VACANT interval to the Olsen appointment 2020-11-18."),
    dict(body="Council", seat_id="AL-D", person_name="Dave Olsen", person_key="dave_olsen",
         start_date="2020-11-18", start_event="appointed", election_year="", confidence="high",
         end_event="reelected",
         sources="appt:2020-11-18 (minutes — appointed to fill Pazell's vacancy, chosen from applicants Doug Green & David Olsen; first named vote 2020-12-16)",
         note="Appointed to fill Pazell's unexpired seat-D term; then won the seat in 2021."),
    dict(body="Council", seat_id="AL-D", person_name="Dave Olsen", person_key="dave_olsen",
         start_date="2022-01-19", start_event="elected", election_year="2021", confidence="high",
         end_event="unknown",
         sources="election:2021 (Council 'At-Large D' winner, 89, unopposed); minutes:2022-01-19 (oath — 'Oath of Office for Dave Olsen')",
         note="Transitioned appointed->elected on the same seat. NOT a candidate in 2025 (McCalmon took seat D); term ended 2026-01-21; mechanism unrecorded -> unknown. Last named vote 2024-10-16."),
    dict(body="Council", seat_id="AL-D", person_name="Linda McCalmon", person_key="linda_mccalmon",
         start_date="2026-01-21", start_event="elected", election_year="2025", confidence="high",
         end_event="serving",
         sources="minutes:2026-01-21 (oath — 'Council Member Linda McCalmon'); election:2025 UNOPPOSED, NOT tabulated by the county (honest gap)",
         note="2025 seat-D winner; ran unopposed so the county published no tally; seating documented by the 2026-01-21 oath. No named vote yet in cities.db (the source, not a gap)."),

    # ================= Seat AL-E — Severson -> Pratt =================
    dict(body="Council", seat_id="AL-E", person_name="Kevin Severson", person_key="kevin_severson",
         start_date="2018-01-01", start_event="elected", election_year="2017", confidence="medium",
         end_event="reelected",
         sources="election:2017 (Council At-Large winner, 96, founding vote-for-2 D/E cycle); minutes:2018-07-18 (present, votes)",
         note="Elected 2017 (vote-for-2 founding D/E cohort) -> term start Jan 2018 (2017 founding year in the PMN purge gap -> not rostered). Long-serving member."),
    dict(body="Council", seat_id="AL-E", person_name="Kevin Severson", person_key="kevin_severson",
         start_date="2022-01-19", start_event="reelected", election_year="2021", confidence="high",
         end_event="unknown",
         sources="election:2021 (Council 'At-Large E' winner, 63 — QUALIFIED WRITE-IN, def. Ronald Patrick 62 by 1 vote); minutes:2022-01-19 (excused that meeting — continuous service, re-elected 2021)",
         note="Won seat E in 2021 as a qualified write-in by a SINGLE vote over Ron Patrick. Re-election start anchored to the Jan-2022 seating (excused 2022-01-19, no separate oath captured). NOT a candidate in 2025 (Pratt took seat E); term ended 2026-01-21 -> unknown. Last named vote 2020-09-16 (sparse/tally-only)."),
    dict(body="Council", seat_id="AL-E", person_name="Jonathan Pratt", person_key="jonathan_pratt",
         start_date="2026-01-21", start_event="elected", election_year="2025", confidence="high",
         end_event="serving",
         sources="minutes:2026-01-21 (oath — 'Council Member Jonathan Pratt'; first named vote 2026-02-18); election:2025 UNOPPOSED, NOT tabulated by the county (honest gap)",
         note="2025 seat-E winner; succeeds Severson; ran unopposed so the county published no tally; seating documented by the 2026-01-21 oath."),
]

SEAT_DISTRICT = {s: "At-Large" for s in
                 ("MAYOR", "AL-A", "AL-C", "AL-D", "AL-E")}
SEAT_ORDER = ["MAYOR", "AL-A", "AL-C", "AL-D", "AL-E"]

# canonical UPPER-CASE election-name token -> person_key (surname suffices; no collisions)
NAME_TO_KEY = {
    "CLAYTON": "sean_clayton",
    "BAILEY": "kathleen_bailey",
    "STITZER": "tessa_stitzer",
    "PATRICK": "ron_patrick",
    "PAZELL": "apollo_pazell",
    "SEVERSON": "kevin_severson",
    "OLSEN": "dave_olsen",
    "MCCALMON": "linda_mccalmon",
    "PRATT": "jonathan_pratt",
}

# cities.db person.name_key -> our person_key (only members with NAMED votes appear;
# McCalmon casts no named vote yet -> absent from the db, never mapped).
DB_KEY = {
    "seanclayton": "sean_clayton",
    "kathleenbailey": "kathleen_bailey",
    "tessastitzer": "tessa_stitzer",
    "ronpatrick": "ron_patrick",
    "apollopazell": "apollo_pazell",
    "kevinseverson": "kevin_severson",
    "daveolsen": "dave_olsen",
    "jonathanpratt": "jonathan_pratt",
}

ATLARGE = dict(
    district_id="At-Large", plan_id="current",
    effective_start=DATA_FLOOR, effective_end="",
    geometry_ref=GEOM_REF, adopted_by="Copperton at-large council structure",
    source_url="", confidence="high",
    note=("DEGENERATE: Copperton's council + mayor are all elected AT-LARGE (seats lettered "
          "A-E are town-wide, NOT districts) in BOTH the metro-township and the post-2024 "
          "town era. This single row covers the whole town (single precinct COP001). "
          "geometry_ref points at the existing town-boundary artifact. effective_start = "
          "incorporation/data floor (Jan 2017); earliest recovered minutes 2018-07-18 (the "
          "2017-02..2018-06 record is PMN-purged)."),
)

CFG = RosterConfig(
    non_voting_mayor=False,       # the presiding officer VOTES in both eras (Millcreek pattern)
    # H-C reverse-crosscheck DOCUMENTED exceptions (2026-07-19) — legitimate tenure->no-winner-row
    # cases, verified against primary sources. crosscheck_field='body' (contest_key==office), so the
    # keys are (year, 'Council'/'Mayor', person_key). Floor year = 2017 (by_candidate has 2017/21/23),
    # so 2019 and 2025 are ABOVE the auto-exempt floor and need explicit cited entries.
    reverse_crosscheck_exceptions={
        # 2019 A/B/C township general is ABSENT from the county SOVC (the documented 2019 county-archive
        # drop, same as South Jordan/Millcreek/Taylorsville) — winners named verbatim in the 2019-11-19
        # minutes canvass, so the seatings are minutes-anchored and no by_candidate tally row exists.
        ("2019", "Council", "sean_clayton"): "2019 A/B/C township general absent from county SOVC (2019 archive drop); winner named in 2019-11-19 minutes canvass ('At Large B: Sean Clayton')",
        ("2019", "Council", "kathleen_bailey"): "2019 A/B/C township general absent from county SOVC (2019 archive drop); winner named in 2019-11-19 minutes canvass ('At Large A: Kathleen Bailey')",
        ("2019", "Council", "tessa_stitzer"): "2019 A/B/C township general absent from county SOVC (2019 archive drop); winner named in 2019-11-19 minutes canvass ('At Large C: Tessa Stitzer')",
        # 2025 first-Town election: all races UNOPPOSED -> election canceled under Utah Code 20A-1-206
        # (the county tabulated no votes, so there is no by_candidate row). Primary sources: the Town
        # Clerk's Certified List of Candidates (published 2025-06-09) + the 2025-10-15 minutes.
        ("2025", "Mayor", "sean_clayton"): "2025 Town Mayor race UNOPPOSED -> election canceled (20A-1-206), not tabulated; Certified Candidate List 2025-06-09 (Mayor: Sean Clayton) + 2025-10-15 minutes ('canceled election in which all candidates had run unopposed'); seated 2026-01-21 oath",
        ("2025", "Council", "linda_mccalmon"): "2025 Seat D UNOPPOSED -> election canceled (20A-1-206), not tabulated; Certified Candidate List 2025-06-09 ('At-Large Seat D: Linda Marie McCalmon'); seated 2026-01-21 oath",
        # Pratt: certified list (2025-06-09 snapshot) showed the open non-mayor seats as C ('No Candidate
        # Declarations' at that date) + D; the 2025-10-15 minutes then name Pratt 'Council Member Elect'
        # who 'begins service in January following a canceled election in which all candidates had run
        # unopposed' -> he was ELECTED unopposed (NOT appointed; the CF/COI note's 'appointed' inference
        # from the June snapshot is superseded by the later minutes). Town-era seat-letter (C vs the
        # roster's cohort label E) is an open modeling nuance flagged for the owner (see CLAUDE.md).
        ("2025", "Council", "jonathan_pratt"): "2025 council seat UNOPPOSED -> election canceled (20A-1-206), not on SOVC; 2025-10-15 minutes name Pratt 'Council Member Elect' who 'begins service in January following a canceled election in which all candidates had run unopposed'; seated 2026-01-21 oath",
    },
    city=CITY, city_dir=CITY_DIR, repo_root=REPO_ROOT, data_floor=DATA_FLOOR,
    geom_ref=GEOM_REF, elections_path=ELECTIONS, cities_db_path=CITIES_DB,
    overrides_path=OVERRIDES, terms_out=TERMS_OUT, districts_out=DISTRICTS_OUT,
    seat_district=SEAT_DISTRICT, seat_order=SEAT_ORDER,
    name_to_key=NAME_TO_KEY, db_key=DB_KEY,
    # Municipal GENERAL winners only (all Copperton rows are general — 2017/2021/2023; the town
    # has never triggered a primary). Chained by PERSON (bluffdale pattern).
    keep_election_row=lambda r: "general" in r["election_type"].lower(),
    contest_key=lambda office, district: office,   # office (Council/Mayor) == body
    crosscheck_field="body", winners_have_district=False,
    elected_events=("elected", "became-mayor", "reelected"),
    atlarge=ATLARGE,
)


def demo():
    def line(r):
        end = r["end_date"] or "—(serving)"
        return (f"  {r['seat_id']:<6} {r['person_name']:<16} {r['start_date']} -> {end:<12} "
                f"[{r['start_event']}/{r['end_event']}] {r['body']:<7} conf={r['confidence']}")

    print("\n(a) CURRENT roster (end_date empty):")
    for r in roster_lib.load_terms(CFG):
        if not r["end_date"] and r["end_event"] == "serving":
            print(line(r))

    print("\n(b) Roster AS OF 2021-06-01 (council):")
    for r in roster_lib.roster_as_of(CFG, "2021-06-01", body="Council"):
        print(line(r))


if __name__ == "__main__":
    rows = roster_lib.build(CFG, TENURES)
    n_high = sum(1 for r in rows if r["confidence"] == "high")
    n_med = sum(1 for r in rows if r["confidence"] == "medium")
    n_low = sum(1 for r in rows if r["confidence"] == "low")
    n_vac = sum(1 for r in rows if r["person_key"] == "vacant")
    print(f"Wrote {TERMS_OUT} ({len(rows)} tenures: {n_high} high / {n_med} medium / {n_low} low; {n_vac} VACANT)")
    print(f"Wrote {DISTRICTS_OUT} (1 district — At-Large, degenerate)")
    if "--demo" in sys.argv:
        demo()
