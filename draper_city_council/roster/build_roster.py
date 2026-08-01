#!/usr/bin/env python3
"""build_roster.py — rolling council-roster for Draper (a slowly-changing-
dimension / interval table of who holds each at-large council + mayor seat over time).

THIN DRIVER: this file holds only Draper-specific DATA (the curated TENURES seat
assignments, the name maps, the at-large district row) + config; all generic mechanics
live in ../../scripts/roster_lib.py. Modeled on the bluffdale/nephi drivers (the
AT-LARGE template).

DERIVED LAYER — regenerable, never hand-edited. Canonical inputs:
  1. election_results/draper_results_by_candidate.csv  (winners -> `elected` terms)
  2. cities.db  role table (city='draper')             (observed vote bounds)
  3. meeting_minutes/minutes/**                          (oaths / appointment / resignation)
  4. roster/roster_overrides.csv                         (hand corrections; applied LAST)

Usage:
  python3 roster/build_roster.py            # regenerate the CSVs
  python3 roster/build_roster.py --demo     # regenerate + print the demo queries
  python3 roster/build_roster.py --check    # regenerate + run validations only

Cardinal rule (repo CLAUDE.md): NEVER fabricate. Unknown seat-holder / date ->
UNKNOWN + confidence=low + a note, never a guess. Honest gaps are data.

STRUCTURAL FACTS (verified in source):
  * 5 AT-LARGE council seats on staggered 4-year terms + a separately-elected,
    NON-VOTING Mayor (Utah council-mayor / executive-mayor form). A council roll
    caps at 5 (never 6). -> non_voting_mayor=True; the MAYOR rows carry BLANK vote
    bounds. Mayor Troy K. Walker's ONE cities.db council vote (2024-10-15, the
    Ordinance #1625 tie-break, roll of 6) is his only vote-row and does not smear.
  * COHORTS: Cohort A = 3 seats (2015/2019/2023 cycles, terms Jan-2016/2020/2024);
    Cohort B = 2 seats (2017/2021/2025); Mayor on the B calendar (Walker won
    2013/2017/2021/2025; mayor since Jan 2014, after Darrell H. Smith 2010-2013).
    Within-cohort seat numbers (A1/A2/A3, B1/B2) are a stable labelling of the
    person-chains, NOT source-attested (flagged in notes).
  * OATH / SEATING dates (first documented meeting of each term, present-block anchored):
    2020-01-14 (2019 winners Vawdrey/F.Lowry/Roberts), 2022-01-11 (2021: T.Lowery +
    Mayor Walker), 2024-01-09 (2023 winners F.Lowry/Roberts/Johnson), 2026-01-06
    (2025: Dahlin + the canceled-race certifications T.Lowery/Green + Mayor Walker).

  * PUZZLE (a) SEAT COUNT — RESOLVED, no council-size change. Recent county cycles look
    like only 4 seats (3+1+3+1) because the 2025 REGULAR 2-seat 4-year Council race was
    CANCELED as UNCONTESTED under Utah Code (one of three candidates withdrew, leaving two
    for two) and Tasha Lowery + Mike Green were CERTIFIED elected WITHOUT appearing on the
    ballot -> that contest never entered the Salt Lake County SOVC (Res #25-49, adopted
    2025-10-07 after a 2025-09-16 continuance: "canceling the race for the 4-year At-Large
    City Council seats and certifying Tasha Lowery and Mike Green as elected"). The council
    has ALWAYS been 5 (roll = 5 every meeting in cities.db).
    CLOSED 2026-07-31: the race is NO LONGER absent from election_results. It is now carried
    there as a CANCELED-UNCONTESTED race row + two is_winner by_candidate rows (all tally
    columns BLANK — no ballot, no votes), sourced from the city's own adopted instrument
    (packets/text/2025-10-07_Council_exh3636839_Resolution_25-49_…txt), the millcreek-2023 /
    alta-2025 convention. So both crosschecks now resolve from the elections layer itself;
    the reverse-crosscheck exceptions below are retained as documentation, not as a crutch.

  * PUZZLE (b) MIKE GREEN CONTINUITY — RESOLVED, NOT a winner-marking defect. Green won
    2017 (B seat), and his cities.db `is_winner=False` for 2021 is CORRECT: 2021 was a
    VOTE-FOR-1 for a single open B seat, which Tasha Lowery won (Green placed 3rd). Green
    RETAINED his OWN B2 seat (not on the 2021 ballot — the broken B-cohort stagger, see
    election_results/CLAUDE.md "2021 filled only 1 council seat"), served continuously
    2020-01-14..2025-12-16 (734 votes), and was RE-ELECTED in 2025 via the same canceled-
    uncontested certification as Tasha Lowery (Res #25-49). The precise mechanism that kept
    his 2017-anchored seat off the 2021 ballot (the mid-term vacancy that broke the B
    stagger) is NOT cleanly documented in the 2020+ window -> his B2 t1 is medium + FLAGGED.
    No fabricated win; the Aug-2022 "reappointing Mike Green" (Res #22-43) is the AUDIT
    COMMITTEE, not the council (a red herring).

  * PUZZLE (c) 2025 by_candidate "duplication" — NOT a defect. Dahlin appears in the 2025
    primary (advancer) AND general (winner); Brad Byington's is_winner=True at 32% is his
    PRIMARY-ADVANCER flag (the documented is_winner="rank<=2N advances" convention), and
    is_winner=False in the general (lost 44.39%). Dahlin is the single 2025 general winner.

  * A2 mid-term vacancy chain (DOCUMENTED): Cal Roberts (won 2019 & 2023) RESIGNED late
    2024 (last council vote 2024-11-12; the 2024-11-19 roll had only 4 voters). Res #24-60
    (minutes 2024-11-19) filled "the vacancy ... created by the resignation of Cal Roberts"
    by appointing Marsha Vawdrey, oath administered the same night. Dahlin then won the 2025
    2-YEAR UNEXPIRED remainder of that seat (verbatim "(2 YEAR TERM)"), seated 2026-01-06.
    Vawdrey's earlier A3 term (won 2015 & 2019) ended 2024-01-09 when Johnson was seated —
    her cities.db vote GAP (2023-12-06 -> 2024-12-03) is exactly this out-then-appointed-back
    signature.

  * 2021 was Draper's RCV pilot; the stored council figures are FIRST-CHOICE (winner
    Tasha Lowery is the RCV final). It does not affect seat identity here.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.dirname(HERE)              # draper_city_council/
REPO_ROOT = os.path.dirname(CITY_DIR)         # civic-data/
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import roster_lib
from roster_lib import RosterConfig

ELECTIONS = os.path.join(CITY_DIR, "election_results", "draper_results_by_candidate.csv")
CITIES_DB = os.path.join(REPO_ROOT, "cities.db")
OVERRIDES = os.path.join(HERE, "roster_overrides.csv")
TERMS_OUT = os.path.join(HERE, "council_terms.csv")
DISTRICTS_OUT = os.path.join(HERE, "district_versions.csv")

CITY = "draper"
DATA_FLOOR = "2020-01-01"       # repo minutes floor; elections reach back to 2007
GEOM_REF = "geo/city_boundary.geojson"

TENURES = [
    # ==== Seat AL-A1  (Fred Lowry — cohort A, 3-seat) =========================
    dict(body="Council", seat_id="AL-A1", person_name="Fred Lowry", person_key="fred_lowry",
         start_date="2020-01-14", start_event="elected", election_year="2019",
         end_event="reelected", confidence="high",
         sources="election:2019 (Council winner, 4,027 rank2 of the vote-for-3); minutes:2020-01-14 (present block: 'Councilmembers Mike Green, Tasha Lowery, Fred Lowry, Cal Roberts, and Marsha Vawdrey')",
         note="Cohort A (3-seat: 2015/2019/2023). Fred Lowry (fred_lowry) is DISTINCT from Tasha Lowery (tasha_lowery) — different surnames (Lowry vs Lowery); resolve by full name. Within-cohort A1/A2/A3 numbering is a labelling of person-chains, not source-attested."),
    dict(body="Council", seat_id="AL-A1", person_name="Fred Lowry", person_key="fred_lowry",
         start_date="2024-01-09", start_event="reelected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (Council winner, 4,443 rank1); minutes:2024-01-09 (present block: 'Bryn Heather Johnson, Tasha Lowery, Fred Lowry, and Cal Roberts')",
         note="Cohort A."),

    # ==== Seat AL-A2  (Roberts -> Vawdrey(appt) -> Dahlin) ====================
    dict(body="Council", seat_id="AL-A2", person_name="Cal Roberts", person_key="cal_roberts",
         start_date="2020-01-14", start_event="elected", election_year="2019",
         end_event="reelected", confidence="high",
         sources="election:2019 (Council winner, 3,885 rank3 of the vote-for-3); minutes:2020-01-14 (present block)",
         note="Cohort A."),
    dict(body="Council", seat_id="AL-A2", person_name="Cal Roberts", person_key="cal_roberts",
         start_date="2024-01-09", start_event="reelected", election_year="2023",
         end_event="resigned", confidence="high",
         sources="election:2023 (Council winner, 4,377 rank2); minutes:2024-01-09 (oath/present); minutes:2024-11-19 (Res #24-60 'the vacancy ... created by the resignation of Cal Roberts')",
         note="RESIGNED mid-term late 2024 — last council vote 2024-11-12; the 2024-11-19 roll had only 4 voters; Res #24-60 declared the vacancy that night. Exact resignation date undocumented (bounded 2024-11-12..2024-11-19); chained to the successor's same-night seating (no separate VACANT row for the <1-week gap)."),
    dict(body="Council", seat_id="AL-A2", person_name="Marsha Vawdrey", person_key="marsha_vawdrey",
         start_date="2024-11-19", start_event="appointed", election_year="",
         end_event="unknown", confidence="high",
         sources="minutes:2024-11-19 (Res #24-60 'Councilmember Johnson moved to appoint Marsha Vawdrey to fill the vacancy ...'; 'The Oath of Office was administered to Marsha Vawdrey by City Recorder'); votes:2024-12-03..2025-12-16",
         note="INTERIM APPOINTEE filling Cal Roberts' resignation vacancy on AL-A2. Same person as the AL-A3 elected member (2015 & 2019) — different seat, different tenure, no overlap (her A3 term ended 2024-01-09; her cities.db vote gap 2023-12-06->2024-12-03 is the out-then-appointed-back signature). Superseded by the elected Dahlin at the 2026-01-06 seating; she was not a 2025 candidate -> end mechanism unknown."),
    dict(body="Council", seat_id="AL-A2", person_name="Kathryn Dahlin", person_key="kathryn_dahlin",
         start_date="2026-01-06", start_event="elected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Council winner of the '(2 YEAR TERM) (Vote for 1)' unexpired seat, 4,518 = 55.61% v. Brad Byington 3,606); minutes:2026-01-06 (present + voting)",
         note="Won the 2-YEAR UNEXPIRED remainder (2026-2028) of Cal Roberts' AL-A2 term (Roberts won 2023 for 2024-2028, resigned 2024). The 2025 by_candidate is CLEAN under the primary-advancer convention (Byington is_winner=True at 32% is his PRIMARY advancer flag, is_winner=False in the general) — NOT a duplication defect."),

    # ==== Seat AL-A3  (Vawdrey -> Johnson) ====================================
    dict(body="Council", seat_id="AL-A3", person_name="Marsha Vawdrey", person_key="marsha_vawdrey",
         start_date="2020-01-14", start_event="elected", election_year="2019",
         end_event="unknown", confidence="high",
         sources="election:2019 (Council winner, 4,377 rank1 of the vote-for-3); minutes:2020-01-14 (present block); minutes:2024-01-09 (replaced at seating by Johnson)",
         note="Cohort A. Also won 2015 (Council winner 3,883 rank1) — that 2016-2020 term is wholly pre-floor and not separately rostered (this 2019-anchored row covers 2020-2024). NOT a 2023 candidate -> did not seek re-election; term ended 2024-01-09; mechanism unrecorded -> end_event=unknown. (She RE-APPEARS on AL-A2 as the 2024 interim appointee to Roberts' vacancy — different seat.)"),
    dict(body="Council", seat_id="AL-A3", person_name="Bryn Johnson", person_key="bryn_johnson",
         start_date="2024-01-09", start_event="elected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (Council winner, 3,429 rank3; ballot name BRYN HEATHER JOHNSON); minutes:2024-01-09 (present block: 'Bryn Heather Johnson ...')",
         note="Cohort A. Succeeded Vawdrey on AL-A3."),

    # ==== Seat AL-B1  (Tasha Lowery — cohort B, 2-seat) =======================
    dict(body="Council", seat_id="AL-B1", person_name="Tasha Lowery", person_key="tasha_lowery",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="reelected", confidence="medium",
         sources="election:2017 (Council winner, 5,213 rank1 of the vote-for-2); votes:2020-01-14.. (observed serving at the data floor)",
         note="PRE-FLOOR term start: the Jan-2018 seating predates the 2020 minutes floor; start 2018-01 inferred from the cohort-B cycle (medium). Cohort B (2-seat: 2017/2021/2025). Tasha Lowery (tasha_lowery) is DISTINCT from Fred Lowry (fred_lowry)."),
    dict(body="Council", seat_id="AL-B1", person_name="Tasha Lowery", person_key="tasha_lowery",
         start_date="2022-01-11", start_event="reelected", election_year="2021",
         end_event="reelected", confidence="high",
         sources="election:2021 (Council winner of the single open seat '(Vote for 1)', 3,105 = 36.95% first-choice — 2021 was the RCV pilot; winner is the RCV final); minutes:2022-01-11 (present block: 'Mayor Troy K. Walker, and Councilmembers Mike Green, Tasha Lowery, Fred Lowry ...')",
         note="2021 was Draper's RCV pilot; the stored 3,105 is the first-choice figure. Only ONE B seat was on the 2021 ballot (broken B-cohort stagger)."),
    dict(body="Council", seat_id="AL-B1", person_name="Tasha Lowery", person_key="tasha_lowery",
         start_date="2026-01-06", start_event="reelected", election_year="2025",
         end_event="serving", confidence="high",
         sources="minutes:2025-10-07 (Res #25-49 'canceling the race for the 4-year At-Large City Council seats and certifying Tasha Lowery and Mike Green as elected' — one of three candidates withdrew, leaving two for two seats -> uncontested race canceled under Utah Code); minutes:2026-01-06 (serving)",
         note="RE-ELECTED 2025 via the canceled-uncontested certification (Res #25-49) — this regular 2-seat B race NEVER entered the county SOVC. It IS carried in election_results since 2026-07-31 as a canceled-uncontested race row + an is_winner by_candidate row with BLANK tallies (sourced from the resolution, not a ballot), so this tenure now has an election anchor as well as the minutes anchor."),

    # ==== Seat AL-B2  (Mike Green — cohort B, 2-seat) =========================
    dict(body="Council", seat_id="AL-B2", person_name="Mike Green", person_key="mike_green",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="reelected", confidence="medium",
         sources="election:2017 (Council winner, 4,779 rank2 of the vote-for-2); votes:2020-01-14..2025-12-16 (734 council votes, continuous)",
         note="PRE-FLOOR term start (Jan-2018, cohort-B cycle; medium). THE GREEN CONTINUITY PUZZLE — RESOLVED: Green's cities.db is_winner=False for 2021 is CORRECT (2021 was VOTE-FOR-1; Tasha Lowery won the single open seat, Green placed 3rd, 1,565). Green RETAINED his own B2 seat, which was NOT on the 2021 ballot (the broken B-cohort stagger — election_results/CLAUDE.md: '2021 filled only 1 council seat'), and served continuously through 2025-12-16. The exact mid-term event that took B2 off the 2021 cycle is NOT documented in the 2020+ window -> this term is medium + FLAGGED. The Aug-2022 'reappointing Mike Green' (Res #22-43) is the AUDIT COMMITTEE, not the council. NEVER fabricated a win."),
    dict(body="Council", seat_id="AL-B2", person_name="Mike Green", person_key="mike_green",
         start_date="2026-01-06", start_event="reelected", election_year="2025",
         end_event="serving", confidence="high",
         sources="minutes:2025-09-16 & 2025-10-07 (Res #25-49 certifying 'Tasha Lowery and Mike Green as elected'; uncontested 4-year race canceled); minutes:2026-01-06 (serving)",
         note="RE-ELECTED 2025 alongside Tasha Lowery via the canceled-uncontested certification (Res #25-49). Absent from the county SOVC (canceled races don't file), but carried in election_results since 2026-07-31 as a canceled-uncontested race row + an is_winner by_candidate row with BLANK tallies (sourced from the resolution, not a ballot)."),

    # ==== Seat MAYOR  (Troy K. Walker — NON-VOTING) ===========================
    dict(body="Mayor", seat_id="MAYOR", person_name="Troy K. Walker", person_key="troy_walker",
         start_date="2018-01-01", start_event="reelected", election_year="2017",
         end_event="reelected", confidence="medium",
         sources="election:2017 (Mayor winner, 54.7%; also won 2013 -> mayor since Jan 2014); minutes:2022-01-11 (replaced at seating)",
         note="PRE-FLOOR term start (Jan-2018 predates the 2020 floor; medium). Mayor since Jan 2014 (won 2013); his 2014-2018 term and predecessor Darrell H. Smith (2010-2013, won 2009) are wholly pre-floor -> not rostered. NON-VOTING mayor (executive-mayor form) -> vote bounds BLANK; his single cities.db council vote (2024-10-15, the Ordinance #1625 tie-break) does not smear."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Troy K. Walker", person_key="troy_walker",
         start_date="2022-01-11", start_event="reelected", election_year="2021",
         end_event="reelected", confidence="high",
         sources="election:2021 (Mayor winner, 5,360, uncontested 100%); minutes:2022-01-11 (present block: 'Mayor Troy K. Walker ...')",
         note="Non-voting mayor -> blank vote bounds."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Troy K. Walker", person_key="troy_walker",
         start_date="2026-01-06", start_event="reelected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Mayor winner, 5,910 = 72.35% v. Rutherford 2,259); minutes:2026-01-06 (serving, though absent 2026-01-06 with Johnson as Mayor Pro Tem)",
         note="Fourth mayoral term overall (won 2013/2017/2021/2025). Non-voting -> blank vote bounds."),
]

SEAT_ORDER = ["AL-A1", "AL-A2", "AL-A3", "AL-B1", "AL-B2", "MAYOR"]
SEAT_DISTRICT = {s: "At-Large" for s in SEAT_ORDER}

# canonical UPPER-CASE election name token -> person_key
NAME_TO_KEY = {
    "LOWRY": "fred_lowry",      # Fred Lowry (distinct spelling from LOWERY)
    "LOWERY": "tasha_lowery",   # Tasha Lowery
    "ROBERTS": "cal_roberts",
    "VAWDREY": "marsha_vawdrey",
    "JOHNSON": "bryn_johnson",
    "GREEN": "mike_green",
    "DAHLIN": "kathryn_dahlin",
    "WALKER": "troy_walker",
}

# cities.db person.name_key -> our person_key.
DB_KEY = {
    "flowry": "fred_lowry",
    "tlowery": "tasha_lowery",
    "roberts": "cal_roberts",
    "vawdrey": "marsha_vawdrey",
    "johnson": "bryn_johnson",
    "green": "mike_green",
    "dahlin": "kathryn_dahlin",
    "troykwalker": "troy_walker",   # 1 council vote (2024-10-15 tie-break); MAYOR row blanked by non_voting_mayor
}

ATLARGE = dict(
    district_id="At-Large", plan_id="current",
    effective_start=DATA_FLOOR, effective_end="",
    geometry_ref=GEOM_REF, adopted_by="Draper municipal at-large council structure",
    source_url="", confidence="high",
    note=("DEGENERATE: Draper's 5-member council + mayor are all elected AT-LARGE — no "
          "wards/districts (geo/CLAUDE.md). This single row covers the whole city (Draper "
          "straddles Salt Lake + Utah counties; Salt Lake County administers the entire "
          "election). geometry_ref points at the existing city-limits artifact. "
          "effective_start = repo data floor; the at-large structure predates it."),
)

CFG = RosterConfig(
    non_voting_mayor=True,
    # H-C (2026-07-19) documented reverse-crosscheck exceptions — the CANCELED-
    # UNCONTESTED class: the regular 2025 4-year 2-seat B race was CANCELED under Utah
    # Code 20A-1-206(3) and Lowery + Green certified elected by Res #25-49 (minutes
    # 2025-09-16 & 2025-10-07); the race NEVER entered the county SOVC.
    # SUPERSEDED-BUT-RETAINED 2026-07-31: election_results now carries that race (a
    # canceled-uncontested row + two is_winner by_candidate rows with BLANK tallies,
    # built from the resolution), so both winners DO have is_winner rows and these two
    # exceptions should no longer fire. Kept as documentation of the class.
    reverse_crosscheck_exceptions={
        ("2025", "Council", "tasha_lowery"): "canceled-uncontested B race; certified elected via Res #25-49 (never on the SOVC)",
        ("2025", "Council", "mike_green"): "canceled-uncontested B race; certified elected via Res #25-49 (never on the SOVC)",
    },
    city=CITY, city_dir=CITY_DIR, repo_root=REPO_ROOT, data_floor=DATA_FLOOR,
    geom_ref=GEOM_REF, elections_path=ELECTIONS, cities_db_path=CITIES_DB,
    overrides_path=OVERRIDES, terms_out=TERMS_OUT, districts_out=DISTRICTS_OUT,
    seat_district=SEAT_DISTRICT, name_to_key=NAME_TO_KEY, db_key=DB_KEY,
    seat_order=SEAT_ORDER,
    # municipal GENERAL winners only, and only the 2019+ cycles the automated layer can
    # map (Draper election data reaches back to 2007). The 2017 cycle seats three rostered
    # PRE-FLOOR tenures (T.Lowery AL-B1, Green AL-B2, Walker MAYOR — cited manually,
    # confidence medium); the 2025 regular 2-seat Council race was CANCELED-uncontested and
    # never entered the SOVC, so T.Lowery/Green 2025 are minutes-anchored (reverse-crosscheck
    # documented exceptions). Restricting to >=2019 avoids forever-unmappable 2007-2017 flags.
    keep_election_row=lambda r: ("general" in r["election_type"].lower()
                                 and int(r["year"]) >= 2019),
    contest_key=lambda office, district: office,   # office (Council/Mayor) == body
    crosscheck_field="body", winners_have_district=False,
    elected_events=("elected", "became-mayor", "reelected"),
    atlarge=ATLARGE,
)


def demo():
    def line(r):
        end = r["end_date"] or "—(serving)"
        return (f"  {r['seat_id']:<6} {r['person_name']:<16} {r['start_date']} -> {end:<12} "
                f"[{r['start_event']}/{r['end_event']}] conf={r['confidence']}")

    print("\n(a) CURRENT roster (end_date empty):")
    for r in roster_lib.load_terms(CFG):
        if not r["end_date"] and r["end_event"] == "serving":
            print(line(r))

    print("\n(b) Roster AS OF 2025-06-01 (council):")
    for r in roster_lib.roster_as_of(CFG, "2025-06-01", body="Council"):
        print(line(r))
    print("    Mayor:")
    for r in roster_lib.roster_as_of(CFG, "2025-06-01", body="Mayor"):
        print(line(r))


if __name__ == "__main__":
    rows = roster_lib.build(CFG, TENURES)
    n_high = sum(1 for r in rows if r["confidence"] == "high")
    n_med = sum(1 for r in rows if r["confidence"] == "medium")
    n_low = sum(1 for r in rows if r["confidence"] == "low")
    print(f"Wrote {TERMS_OUT} ({len(rows)} tenures: {n_high} high / {n_med} medium / {n_low} low)")
    print(f"Wrote {DISTRICTS_OUT} (1 district — At-Large, degenerate)")
    if "--demo" in sys.argv:
        demo()
