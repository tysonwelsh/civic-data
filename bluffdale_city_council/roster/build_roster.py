#!/usr/bin/env python3
"""build_roster.py — rolling council-roster for Bluffdale (a slowly-changing-
dimension / interval table of who holds each at-large council + mayor seat over time).

THIN DRIVER: this file holds only Bluffdale-specific DATA (the curated TENURES seat
assignments, the name maps, the at-large district row) + config; all generic mechanics
live in ../scripts/roster_lib.py. Modeled on the nephi driver (the at-large template).

DERIVED LAYER — regenerable, never hand-edited. Canonical inputs:
  1. election_results/bluffdale_results_by_candidate.csv  (winners -> `elected` terms)
  2. cities.db  role table (city='bluffdale')             (observed vote bounds)
  3. meeting_minutes/minutes/**                            (oath ceremonies — all four dated)
  4. roster/roster_overrides.csv                           (hand corrections; applied LAST)

Usage:
  python3 roster/build_roster.py            # regenerate the CSVs
  python3 roster/build_roster.py --demo     # regenerate + print the demo queries
  python3 roster/build_roster.py --check    # regenerate + run validations only

Cardinal rule (repo CLAUDE.md): NEVER fabricate. Unknown seat-holder / date ->
UNKNOWN + confidence=low + a note, never a guess. Honest gaps are data.

STRUCTURAL FACTS (verified in source):
  * 5 AT-LARGE council seats on staggered 4-year terms + a separately-elected Mayor.
    Cohort A = 3 seats (2015/2019/2023 cycles); Cohort B = 2 seats (2017/2021/2025);
    Mayor on the B cycle. Verified by the winner counts every cycle (3/2 alternating,
    2007-2025) and the January oath ceremonies.
  * The MAYOR does NOT vote in Council except to break a tie, but DOES vote as Chair of
    the in-session RDA/LBA boards (root CLAUDE.md; role table: Timothy has RDA-only
    votes; Hall's body='Council' role rows 2022-11-09..2025-05-14 are her mayoral
    TIE-BREAKS, not council membership) -> non_voting_mayor=True.
  * OATH DATES (all minutes-documented): 2020-01-06 (Crockett, Gaston, Hales, Kallas —
    "four City Council Members sworn in at the same time"); 2022-01-04 (Mayor Hall,
    Aston, Crockett); 2024-01-10 (Austin, Wilding, Lord); 2026-01-05 (Smith, Aston,
    Hall — Smith's legal name "David McKinley McLeod Smith").
  * ELECTION-RESULTS DEFECT — FOUND HERE, FIXED AT SOURCE 2026-07-12: the 2019 cohort-A
    general was a VOTE-FOR-3 (cohort A elects 3 in 2007/2015/2023 as well), but
    clean_elections.py carried N_SEATS=2, mis-flagging MARK R. HALES (1,044, 3rd of 5)
    is_winner=False. The independent roster audit (AUDIT.md F1) PROVED vote-for-3 from
    the raw SOVC (4,977 candidate votes vs 2,154 ballots cast — over the vote-for-2
    ceiling in every precinct); N_SEATS was corrected 2->3 in clean_elections.py and the
    election outputs regenerated (per repo doctrine: the fix lives in the elections
    build, never in this roster).
  * The 2019 SPECIAL: Traci Crockett's separate 2019 contest (1,140 v. Warren James
    907) was the 2-year UNEXPIRED remainder of a cohort-B seat won in 2017 by Alan
    Jackson, who left at an unrecoverable pre-floor date (pre-2020 minutes not held;
    zero Jackson votes in-window). Forced by term arithmetic: Crockett's 2021 win must
    be a full 2022-2025 term (her service ends Jan 2026 with no 2023 win), so her 2019
    win can only be the 2-year unexpired seat. Jackson's tenure + any interim appointee
    lie wholly pre-floor -> NOT rostered (honest gap, documented here and in CLAUDE.md).
  * 2021 was the RCV pilot (Aston seat 1, Crockett seat 2 — first-choice figures in the
    stored data; winners are the RCV final, per the races note).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.dirname(HERE)              # bluffdale_city_council/
REPO_ROOT = os.path.dirname(CITY_DIR)         # civic-data/
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import roster_lib
from roster_lib import RosterConfig

ELECTIONS = os.path.join(CITY_DIR, "election_results", "bluffdale_results_by_candidate.csv")
CITIES_DB = os.path.join(REPO_ROOT, "cities.db")
OVERRIDES = os.path.join(HERE, "roster_overrides.csv")
TERMS_OUT = os.path.join(HERE, "council_terms.csv")
DISTRICTS_OUT = os.path.join(HERE, "district_versions.csv")

CITY = "bluffdale"
DATA_FLOOR = "2020-01-01"       # repo minutes floor; elections reach back to 2007
GEOM_REF = "geo/city_boundary.geojson"

TENURES = [
    # ---- Seat AL-A1  (Kallas -> Austin) --------------------------------------
    dict(body="Council", seat_id="AL-A1", person_name="Dave Kallas", person_key="dave_kallas",
         start_date="2020-01-06", start_event="elected", election_year="2019",
         end_event="unknown", confidence="high",
         sources="election:2019 (Council winner, 1,120 rank1 of the vote-for-3); minutes:2020-01-06 (oath — 'Council Members Elect; Traci Crockett, Jeff Gaston, Mark Hales, and Dave Kallas'); minutes:2024-01-10 (replaced at oath)",
         note="Also won an unexpired cohort-A seat in 2017 (uncontested) — that 2018-2019 term is wholly pre-floor and not rostered. NOT a candidate in 2023 -> did not seek re-election; term expired 2024-01-10; mechanism unrecorded -> end_event=unknown. Within-cohort seat numbers (A1/A2/A3) are a labelling of person-chains, not source-attested."),
    dict(body="Council", seat_id="AL-A1", person_name="Steve Austin", person_key="steve_austin",
         start_date="2024-01-10", start_event="elected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (Council winner, 1,460 rank1); minutes:2024-01-10 (oath — 'Council Members Elect Steve Austin, Gregory Wilding and Alan Lord')",
         note="Cohort A. Seat pairing with the 2019 trio is a labelling choice (see AL-A1 Kallas note)."),

    # ---- Seat AL-A2  (Gaston -> Wilding) -------------------------------------
    dict(body="Council", seat_id="AL-A2", person_name="Jeff Gaston", person_key="jeff_gaston",
         start_date="2020-01-06", start_event="elected", election_year="2019",
         end_event="unknown", confidence="high",
         sources="election:2019 (Council winner, 1,054 rank2 of the vote-for-3); minutes:2020-01-06 (oath); minutes:2024-01-10 (replaced at oath)",
         note="NOT a candidate in 2023 -> did not seek re-election; term expired 2024-01-10; mechanism unrecorded -> end_event=unknown."),
    dict(body="Council", seat_id="AL-A2", person_name="Greg Wilding", person_key="greg_wilding",
         start_date="2024-01-10", start_event="elected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (Council winner, 1,429 rank2); minutes:2024-01-10 (oath)",
         note="Cohort A."),

    # ---- Seat AL-A3  (Hales -> Lord) -----------------------------------------
    dict(body="Council", seat_id="AL-A3", person_name="Mark Hales", person_key="mark_hales",
         start_date="2020-01-06", start_event="elected", election_year="2019",
         end_event="lost", confidence="high",
         sources="election:2019 (Council winner, 1,044 rank3 of the vote-for-3); minutes:2020-01-06 (oath — named a Council Member-Elect); election:2023 (ran, 1,387 rank4 — lost); minutes:2024-01-10 (replaced at oath)",
         note="The election dataset originally mis-flagged him is_winner=False (N_SEATS=2 for the 2019 vote-for-3 contest) — FIXED 2026-07-12 after the roster audit PROVED vote-for-3 from the raw SOVC (4,977 candidate votes vs 2,154 ballots cast; see AUDIT.md F1 + election_results/CLAUDE.md). Ran 2023 and lost (4th of 6)."),
    dict(body="Council", seat_id="AL-A3", person_name="Alan Lord", person_key="alan_lord",
         start_date="2024-01-10", start_event="elected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (Council winner, 1,397 rank3); minutes:2024-01-10 (oath)",
         note="Cohort A."),

    # ---- Seat AL-B1  (Aston, three consecutive terms) ------------------------
    dict(body="Council", seat_id="AL-B1", person_name="Wendy Aston", person_key="wendy_aston",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="reelected", confidence="medium",
         sources="election:2017 (Council winner, 708 — 2-seat race with Alan Jackson); votes:2020-04-08.. (observed serving at the data floor); minutes:2026-01-05 (her remarks — 'this is her third swearing in', i.e. 2018/2022/2026)",
         note="PRE-FLOOR term start: the Jan-2018 oath predates the 2020 minutes floor; start 2018-01 inferred from the cohort-B cycle (confidence medium). Her own 2026 'third swearing in' remark corroborates seatings in 2018, 2022 and 2026."),
    dict(body="Council", seat_id="AL-B1", person_name="Wendy Aston", person_key="wendy_aston",
         start_date="2022-01-04", start_event="reelected", election_year="2021",
         end_event="reelected", confidence="high",
         sources="election:2021 (Council winner — RCV pilot seat 1; stored 833 is the FIRST-CHOICE figure); minutes:2022-01-04 (oath — 'Council Members Elect, Wendy Aston and Traci Crockett')",
         note="2021 was Bluffdale's RCV pilot; winners are the RCV final, the stored counts are first-choice."),
    dict(body="Council", seat_id="AL-B1", person_name="Wendy Aston", person_key="wendy_aston",
         start_date="2026-01-05", start_event="reelected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Council winner, 1,959 rank1); minutes:2026-01-05 (oath — 'Wendy Watterson Aston')",
         note="Third consecutive term on AL-B1."),

    # ---- Seat AL-B2  (Crockett special -> Crockett full -> Smith) -------------
    dict(body="Council", seat_id="AL-B2", person_name="Traci Crockett", person_key="traci_crockett",
         start_date="2020-01-06", start_event="elected", election_year="2019",
         end_event="reelected", confidence="high",
         sources="election:2019 (winner of the separate single-seat contest, 1,140 v. Warren James 907 — the 2-YEAR UNEXPIRED remainder of a cohort-B seat); minutes:2020-01-06 (oath)",
         note="SPECIAL/UNEXPIRED term (2020-2021): forced by term arithmetic — her 2021 win must be the full 2022-2025 term (service ends Jan 2026, no 2023 win), so the 2019 win is the 2-year remainder. The seat was won in 2017 by ALAN JACKSON, who left at an unrecoverable pre-floor date (pre-2020 minutes not held; zero in-window votes); Jackson's tenure and any interim appointee are wholly pre-floor -> not rostered (honest gap)."),
    dict(body="Council", seat_id="AL-B2", person_name="Traci Crockett", person_key="traci_crockett",
         start_date="2022-01-04", start_event="reelected", election_year="2021",
         end_event="unknown", confidence="high",
         sources="election:2021 (Council winner — RCV pilot seat 2; stored 1,098 is the FIRST-CHOICE figure); minutes:2022-01-04 (oath); minutes:2026-01-05 (replaced at oath)",
         note="NOT a candidate in 2025 -> did not seek re-election; term expired 2026-01-05; mechanism unrecorded -> end_event=unknown. Last observed vote 2025-12-10 (RDA)."),
    dict(body="Council", seat_id="AL-B2", person_name="Mackey Smith", person_key="mackey_smith",
         start_date="2026-01-05", start_event="elected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Council winner, 1,860 rank2); minutes:2026-01-05 (oath — legal name 'David McKinley McLeod Smith')",
         note="Ballot/roster name 'Mackey Smith'; the 2026-01-05 oath prints his legal name David McKinley McLeod Smith — same person."),

    # ---- Seat MAYOR  (Timothy -> Hall) ----------------------------------------
    dict(body="Mayor", seat_id="MAYOR", person_name="Derk Timothy", person_key="derk_timothy",
         start_date="2018-01-01", start_event="reelected", election_year="2017",
         end_event="unknown", confidence="medium",
         sources="election:2017 (Mayor winner, unopposed 1,238; also won 2009 and 2013 — mayor since Jan 2010); minutes:2022-01-04 (Mayor Hall's tribute — '12 years of dedicated service'); minutes:2022-01-04 (replaced at oath)",
         note="PRE-FLOOR term start (Jan-2018 oath predates the 2020 minutes floor; medium). His earlier terms (2010-2013, 2014-2017) are wholly pre-floor -> not rostered. NOT a candidate in 2021 (Hall v. Roberts) -> did not seek re-election; mechanism unrecorded -> end_event=unknown. Mayor does NOT vote in Council except tie-breaks, but VOTES as RDA/LBA Chair (his role rows are RDA-only, 2020-06-10..2021-12-08)."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Natalie Hall", person_key="natalie_hall",
         start_date="2022-01-04", start_event="elected", election_year="2021",
         end_event="reelected", confidence="high",
         sources="election:2021 (Mayor winner — RCV pilot, 2,497 v. John Roberts 806, first round decisive); minutes:2022-01-04 (oath — 'Mayor Elect, Natalie Hall')",
         note="Her cities.db body='Council' role rows (2022-11-09..2025-05-14) are mayoral votes cast from the chair, not council membership (the Nephi-Nielson pattern): 2022-11-09 was a tie-break; 2025-05-14 was a recorded 'Mayor Hall-Yes' on a motion already passing 3-2 (AUDIT.md F2). She also votes as RDA/LBA Chair."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Natalie Hall", person_key="natalie_hall",
         start_date="2026-01-05", start_event="reelected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Mayor winner, 1,993 v. Connie Pavlakis 1,927); minutes:2026-01-05 (oath — 'Natalie Caudell Hall')",
         note="Re-elected 2025 (50.84%, a 66-vote margin)."),
]

SEAT_DISTRICT = {s: "At-Large" for s in
                 ("AL-A1", "AL-A2", "AL-A3", "AL-B1", "AL-B2", "MAYOR")}

# canonical UPPER-CASE election name token -> person_key
NAME_TO_KEY = {
    "KALLAS": "dave_kallas",
    "GASTON": "jeff_gaston",
    "HALES": "mark_hales",
    "CROCKETT": "traci_crockett",
    "ASTON": "wendy_aston",
    "AUSTIN": "steve_austin",
    "WILDING": "greg_wilding",
    "LORD": "alan_lord",
    "MACKEY": "mackey_smith", "SMITH": "mackey_smith",
    "HALL": "natalie_hall",
    "TIMOTHY": "derk_timothy",
}

# cities.db person.name_key -> our person_key (canonical rows only; the OCR junk
# variants — 'kauas', 'crocket', 'wuding', 'astin'/'auston', surname-only rows — carry
# ZERO votes and are never mapped).
DB_KEY = {
    "davekallas": "dave_kallas",
    "jeffgaston": "jeff_gaston",
    "markhales": "mark_hales",
    "tracicrockett": "traci_crockett",
    "wendyaston": "wendy_aston",
    "steveaustin": "steve_austin",
    "gregwilding": "greg_wilding",
    "alanlord": "alan_lord",
    "mackeysmith": "mackey_smith",
    "nataliehall": "natalie_hall",
    "derktimothy": "derk_timothy",
}

ATLARGE = dict(
    district_id="At-Large", plan_id="current",
    effective_start=DATA_FLOOR, effective_end="",
    geometry_ref=GEOM_REF, adopted_by="Bluffdale municipal at-large council structure",
    source_url="", confidence="high",
    note=("DEGENERATE: Bluffdale's 5-member council + mayor are all elected AT-LARGE — no "
          "wards/districts. This single row covers the whole city (the city straddles Salt "
          "Lake + Utah counties; the Utah-County sliver is Camp Williams, unpopulated). "
          "geometry_ref points at the existing city-limits artifact. effective_start = repo "
          "data floor; the at-large structure predates it."),
)

CFG = RosterConfig(
    non_voting_mayor=True,
    city=CITY, city_dir=CITY_DIR, repo_root=REPO_ROOT, data_floor=DATA_FLOOR,
    geom_ref=GEOM_REF, elections_path=ELECTIONS, cities_db_path=CITIES_DB,
    overrides_path=OVERRIDES, terms_out=TERMS_OUT, districts_out=DISTRICTS_OUT,
    seat_district=SEAT_DISTRICT, name_to_key=NAME_TO_KEY, db_key=DB_KEY,
    # municipal GENERAL winners only, and only the 2019+ cycles the automated layer can
    # map (Bluffdale's election data reaches back to 2007). The 2017 cycle seats two
    # rostered PRE-FLOOR tenures (Aston AL-B1, Timothy MAYOR — cited manually in their
    # sources, confidence medium) plus two wholly-pre-floor tenures deliberately NOT
    # rostered (Alan Jackson's B seat, vacated pre-floor; Kallas' 2018-19 unexpired A
    # seat) — including 2017 here would print two forever-unmappable cross-check flags.
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

    print("\n(b) Roster AS OF 2021-07-01 (council):")
    for r in roster_lib.roster_as_of(CFG, "2021-07-01", body="Council"):
        print(line(r))
    print("    Mayor:")
    for r in roster_lib.roster_as_of(CFG, "2021-07-01", body="Mayor"):
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
