#!/usr/bin/env python3
"""build_roster.py — rolling council-roster for the Town of Alta (a slowly-changing-
dimension / interval table of who holds each at-large town-council + mayor seat over time).

THIN DRIVER: this file holds only Alta-specific DATA (the curated TENURES seat
assignments, the name maps, the at-large district row) + config; all generic mechanics
live in ../../scripts/roster_lib.py. Modeled on the bluffdale/nephi drivers (the
AT-LARGE template).

DERIVED LAYER — regenerable, never hand-edited. Canonical inputs:
  1. election_results/alta_results_by_candidate.csv   (winners -> `elected` terms)
  2. cities.db  role table (city='alta')              (observed vote bounds)
  3. meeting_minutes/minutes/**                        (oaths / appointments / seatings)
  4. roster/roster_overrides.csv                       (hand corrections; applied LAST)

Usage:
  python3 roster/build_roster.py            # regenerate the CSVs
  python3 roster/build_roster.py --demo     # regenerate + print the demo queries
  python3 roster/build_roster.py --check    # regenerate + run validations only

Cardinal rule (repo CLAUDE.md): NEVER fabricate. Unknown seat-holder / date ->
UNKNOWN + confidence=low + a note, never a guess. Honest gaps are data.

STRUCTURAL FACTS (verified in source):
  * Utah TOWN form: a VOTING Mayor + 4 AT-LARGE councilmembers (no districts). A full
    roll call caps at 5 (Mayor + 4). The Mayor is an ordinary voting member -> the MAYOR
    row carries REAL vote bounds -> non_voting_mayor=False (root/meeting_minutes CLAUDE.md;
    cities.db role: Roger Bourke is the top voter). SPARSE BY DESIGN (~12 meetings/yr).
  * COHORTS: 4 seats on staggered 4-year terms, 2 filled each odd-year general.
    Cohort P (AL-1, AL-2) elects in 2021/2025; cohort Q (AL-3, AL-4) elects in 2019/2023.
    Mayor won 2021 (Roger Bourke). Within-cohort seat numbers are a labelling of the
    person-chains, NOT source-attested (flagged in notes).
  * SEATING dates (documented): 2022-01-12 (2021 winners Byrne/Anctil + Mayor Roger Bourke;
    Morgan named Mayor Pro Tem at this reorganization meeting), 2024-01-10 (2023 winners
    Morgan re-elected + Schilling; present block), 2026-01-14 (2025 winner Heimark seated,
    "welcomed Craig Heimark to the council following the transition from the treasurer
    position"). Pre-2022 holders predate these -> pre-floor, medium.
  * TWO MAYORS in span: Harris Sondak (Mayor 2020-2021, pre-floor) -> Roger Bourke
    (2022->present). TWO BOURKES: Roger Bourke (Mayor, voting) vs MARGARET Bourke (a
    2020-2021 councilmember) are DIFFERENT people -> disambiguated ROGER vs MARGARET.
  * 2021 TALLIES PRIVACY-SUPPRESSED (Alta's ~380-person precinct is below the county
    privacy floor): the 2021 winners (Byrne + Anctil council; Roger Bourke mayor) are known
    from external cross-check + minutes; the numeric votes are honestly BLANK, never
    fabricated (election_results/CLAUDE.md).

  * CRAIG HEIMARK — TREASURER-then-COUNCILMEMBER (a votes-pipeline FLAG). Heimark was
    appointed TOWN TREASURER (staff) 2022-05-11 (Res 2022-R-9) and served as Treasurer
    through 2025; he WON the 2025 council election and was seated 2026-01-14 (minutes:
    "Heimark's election to the town council (from role as Treasurer)"). His cities.db
    `craigheimark` role shows first_seen 2022-04-13 with a handful of 2022-2023 "votes"
    (2022=1, 2023=3) — those are TREASURER-ERA procedural mover/seconder mentions
    MISATTRIBUTED as council votes, NOT council membership. His real council service is
    2026-01-14 -> ; the tenure-window clamp keeps the stray 2022-2023 votes out. FLAGGED
    as a votes-pipeline issue (not fixed from the roster).

  * 2025 CYCLE was CANCELLED + CERTIFIED (Utah Code 20A-1-206; Res 2025-R-26, adopted
    2025-09-10) — NOT the earlier "county-file gap / the election occurred" reading. After
    candidate withdrawals the 2025 Town of Alta election was cancelled and the unopposed
    candidates deemed elected: Roger Bourke (Mayor, unopposed) + Carolyn Anctil and Craig
    Heimark for the two open at-large seats (John Byrne + Paul Moxley withdrew). Recovered
    2026-07-17 into election_results/alta_races.csv (year 2025, cancelled_certification; ALL
    vote/pct/turnout columns blank — no votes cast). All three are seated 2026-01-14. This
    RESOLVES the prior "whether Bourke was re-elected in 2025 is undetermined" note (he WAS
    certified re-elected -> the MAYOR chain is now SPLIT into a 2021 and a 2025 term) and
    reclassifies Heimark's/Anctil's 2026 terms from "won a county-gap election / inferred"
    to CERTIFIED-ELECTED (Anctil's AL-2 is likewise split into 2021 + 2025 terms). The
    *_results_by_candidate.csv still carries no 2025 rows, and keep_election_row is restricted
    to 2021/2023, so the forward crosscheck is unaffected.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.dirname(HERE)              # alta_city_council/
REPO_ROOT = os.path.dirname(CITY_DIR)         # civic-data/
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import roster_lib
from roster_lib import RosterConfig

ELECTIONS = os.path.join(CITY_DIR, "election_results", "alta_results_by_candidate.csv")
CITIES_DB = os.path.join(REPO_ROOT, "cities.db")
OVERRIDES = os.path.join(HERE, "roster_overrides.csv")
TERMS_OUT = os.path.join(HERE, "council_terms.csv")
DISTRICTS_OUT = os.path.join(HERE, "district_versions.csv")

CITY = "alta"
DATA_FLOOR = "2020-01-01"       # repo minutes floor; Alta election data begins 2021
GEOM_REF = "geo/city_boundary.geojson"

TENURES = [
    # ==== Seat AL-1  (cohort P; M.Bourke -> Byrne -> Heimark) =================
    dict(body="Council", seat_id="AL-1", person_name="Margaret Bourke", person_key="margaret_bourke",
         start_date="2018-01-01", start_event="elected", election_year="",
         end_event="lost", confidence="medium",
         sources="votes:2020-02-12..2021-12-08 (observed serving at the data floor); minutes:2020-02-12 (present: 'Council Member Margaret Bourke')",
         note="PRE-FLOOR term start: elected ~2017 (cohort-P cycle, term 2018-2022) inferred — Alta election_results begins 2021, so no in-data winner row (medium). MARGARET Bourke is a DIFFERENT person from Mayor ROGER Bourke. Ran for re-election in 2021 and LOST (2021 by_candidate: MARGARET E. BOURKE is_winner=False; tallies privacy-suppressed). Term ended at the 2022-01-12 seating of Byrne. Within-cohort AL-1/AL-2 numbering is a labelling of person-chains, not source-attested."),
    dict(body="Council", seat_id="AL-1", person_name="John Byrne", person_key="john_byrne",
         start_date="2022-01-12", start_event="elected", election_year="2021",
         end_event="unknown", confidence="high",
         sources="election:2021 (Council winner, rank1; tallies PRIVACY-SUPPRESSED — winner external/unofficial per election_results/CLAUDE.md); minutes:2022-01-12 (seated; reorganization meeting)",
         note="2021 numeric tallies were county-suppressed (Alta below the privacy floor) -> winners known, totals blank (never fabricated). Departed after the 2025 election (last council vote 2025-12-10; the 2026-01-14 minutes call him 'former Councilmember Byrne'); mechanism (did-not-run vs lost) unrecorded -> end_event=unknown."),
    dict(body="Council", seat_id="AL-1", person_name="Craig Heimark", person_key="craig_heimark",
         start_date="2026-01-14", start_event="elected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Council At-Large — CANCELLED-CERTIFICATION, Utah Code 20A-1-206, Res 2025-R-26: the 2025 Town of Alta election was CANCELLED (adopted 2025-09-10) and the two unopposed candidates for the two open at-large seats — Carolyn Anctil + Craig Heimark — deemed elected, John Byrne + Paul Moxley having withdrawn; election_results/alta_races.csv year=2025 Council, cancelled_certification, no votes cast); minutes:2025-09-10 ('a resolution to cancel the upcoming municipal election due to candidate withdrawals'); minutes:2025-12-09 ('Craig Heimark, Councilmember Elect'); minutes:2026-01-14 ('welcomed Craig Heimark to the council following the transition from the treasurer position'; 'Heimark's election to the town council (from role as Treasurer)')",
         note="CERTIFIED ELECTED to AL-1 at the CANCELLED 2025 election — a declared candidate deemed elected under Utah Code 20A-1-206 (Res 2025-R-26, adopted 2025-09-10), NOT an appointment and NOT a 'county-file gap where the election occurred' (that earlier framing is SUPERSEDED — the election was cancelled, so no votes exist; recovered 2026-07-17 into alta_races.csv). Took the AL-1 seat that Byrne vacated (Byrne + Moxley withdrew their declarations). Was TOWN TREASURER (staff) 2022-05-11..2025 — his cities.db 2022-2023 'votes' (4 total) are treasurer-era procedural misattributions, NOT council membership (FLAGGED as a votes-pipeline issue); real council service starts 2026-01-14. Seated 2026-01-14."),

    # ==== Seat AL-2  (cohort P; Curry -> Anctil) ==============================
    dict(body="Council", seat_id="AL-2", person_name="Cliff Curry", person_key="cliff_curry",
         start_date="2018-01-01", start_event="elected", election_year="",
         end_event="unknown", confidence="medium",
         sources="votes:2020-02-12..2021-12-08 (observed serving at the data floor); minutes:2020-02-12 (present: 'Council Member Cliff Curry')",
         note="PRE-FLOOR term start: elected ~2017 (cohort-P cycle, term 2018-2022) inferred — no in-data winner row (medium). Not a 2021 candidate -> did not seek re-election; term ended at the 2022-01-12 seating of Anctil; mechanism unrecorded -> end_event=unknown."),
    dict(body="Council", seat_id="AL-2", person_name="Carolyn Anctil", person_key="carolyn_anctil",
         start_date="2022-01-12", start_event="elected", election_year="2021",
         end_event="reelected", confidence="high",
         sources="election:2021 (Council winner, rank2; tallies PRIVACY-SUPPRESSED); minutes:2022-01-12 (seated)",
         note="2021 numeric tallies county-suppressed -> totals blank (never fabricated). Term ran through 2025; RE-CERTIFIED for the 2026 term at the CANCELLED 2025 election (Res 2025-R-26) — see the next AL-2 row."),
    dict(body="Council", seat_id="AL-2", person_name="Carolyn Anctil", person_key="carolyn_anctil",
         start_date="2026-01-14", start_event="reelected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Council At-Large — CANCELLED-CERTIFICATION, Utah Code 20A-1-206, Res 2025-R-26: the 2025 election was CANCELLED (adopted 2025-09-10) and Carolyn Anctil + Craig Heimark, the two unopposed candidates for the two open at-large seats, deemed elected (Byrne + Moxley withdrew); election_results/alta_races.csv year=2025 Council, cancelled_certification, no votes cast); minutes:2025-09-10 (cancellation resolution); minutes:2026-01-14 (present as Councilmember; Mayor Bourke references 'recent oath-of-office ceremonies for recently elected officials')",
         note="RE-CERTIFIED (re-elected) to AL-2 at the CANCELLED 2025 election — deemed elected under Utah Code 20A-1-206 (Res 2025-R-26, adopted 2025-09-10). CORRECTS the prior model: this was NOT a 'county-file gap' with a re-election merely inferred from continued service — the election was cancelled and Anctil certified elected (recovered 2026-07-17 into alta_races.csv). A NEW AL-2 term seated 2026-01-14 (her cohort-mate AL-1 seat went to Heimark after Byrne withdrew). Split into a per-term row (repo pattern for consecutive re-elections) now that the certification instrument is on disk. Serving."),

    # ==== Seat AL-3  (cohort Q; Davis -> Schilling) ===========================
    dict(body="Council", seat_id="AL-3", person_name="Sheridan Davis", person_key="sheridan_davis",
         start_date="2020-01-01", start_event="elected", election_year="",
         end_event="lost", confidence="medium",
         sources="votes:2020-02-12..2024-02-14 (observed serving); minutes:2020-02-12 (present: 'Council Member Sheridan Davis')",
         note="PRE-FLOOR origin: elected ~2019 (cohort-Q cycle, term 2020-2024) inferred — Alta election_results begins 2021, so no in-data winner row (medium); the 2020 term start is at the data floor. Ran for re-election in 2023 and LOST (2023 Council: SHERIDAN J. DAVIS 42 rank3, is_winner=False; Morgan 66 + Schilling 51 won). Term ended at the 2024-01-10 seating of Schilling (Davis not in that present block). His cities.db vote dated 2024-02-14 is a STRAY post-seating attribution (not in the 2024-01-10 present block) -> FLAGGED, tenure ends 2024-01-10."),
    dict(body="Council", seat_id="AL-3", person_name="Dan Schilling", person_key="dan_schilling",
         start_date="2024-01-10", start_event="elected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (Council winner, 51 rank2); minutes:2024-01-10 (present block: 'Councilmember Dan Schilling (virtual)')",
         note="Cohort Q. Succeeded Davis on AL-3."),

    # ==== Seat AL-4  (cohort Q; Morgan, re-elected) ===========================
    dict(body="Council", seat_id="AL-4", person_name="Elise Morgan", person_key="elise_morgan",
         start_date="2020-01-01", start_event="elected", election_year="",
         end_event="reelected", confidence="medium",
         sources="votes:2020-03-11..2023-.. (observed serving at the data floor); minutes:2022-01-12 (named Mayor Pro Tem)",
         note="PRE-FLOOR origin: elected ~2019 (cohort-Q cycle, term 2020-2024) inferred — no in-data winner row (medium); 2020 term start at the data floor. Named MAYOR PRO TEM at the 2022-01-12 reorganization. RE-ELECTED 2023 (see next row)."),
    dict(body="Council", seat_id="AL-4", person_name="Elise Morgan", person_key="elise_morgan",
         start_date="2024-01-10", start_event="reelected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (Council winner, 66 rank1); minutes:2024-01-10 (present block: 'Councilmember Elise Morgan')",
         note="Cohort Q. Continues as Mayor Pro Tem. Same seat as her pre-floor term (no gap)."),

    # ==== Seat MAYOR  (Sondak -> Roger Bourke; the Mayor VOTES) ===============
    dict(body="Mayor", seat_id="MAYOR", person_name="Harris Sondak", person_key="harris_sondak",
         start_date="2018-01-01", start_event="elected", election_year="",
         end_event="unknown", confidence="medium",
         sources="votes:2020-02-12..2021-12-08 (observed serving as voting Mayor); minutes:2020-02-12 (present: 'Mayor Harris Sondak')",
         note="PRE-FLOOR origin: Mayor 2020-2021; elected ~2017 (4-year mayoral term 2018-2022) inferred — Alta election_results begins 2021, so no in-data winner row (medium). WITHDREW from the 2021 mayoral race (Roger Bourke won uncontested — election_results/CLAUDE.md); term ended at the 2022-01-12 seating of Bourke; mechanism = withdrew/did-not-seek -> end_event=unknown."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Roger Bourke", person_key="roger_bourke",
         start_date="2022-01-12", start_event="elected", election_year="2021",
         end_event="reelected", confidence="high",
         sources="election:2021 (Mayor winner, uncontested; tallies PRIVACY-SUPPRESSED); minutes:2022-01-12 (presiding as Mayor; appoints Morgan Mayor Pro Tem)",
         note="The Mayor VOTES (Utah Town form; max roll 5) -> real vote bounds. Roger Bourke was a PLANNING COMMISSIONER before, not a councilmember; DIFFERENT person from the 2020-2021 councilmember MARGARET Bourke. 2021 mayoral tallies county-suppressed -> totals blank. Term ran through 2025; RE-CERTIFIED for the 2026 term at the CANCELLED 2025 election (Res 2025-R-26) — see the next MAYOR row."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Roger Bourke", person_key="roger_bourke",
         start_date="2026-01-14", start_event="reelected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Mayor — CANCELLED-CERTIFICATION, Utah Code 20A-1-206, Res 2025-R-26: the 2025 election was CANCELLED (adopted 2025-09-10) and Roger Bourke, unopposed for Mayor, deemed elected; election_results/alta_races.csv year=2025 Mayor, cancelled_certification, no votes cast); minutes:2025-09-10 (cancellation resolution); minutes:2026-01-14 (presiding as Mayor; references 'recent oath-of-office ceremonies for recently elected officials')",
         note="RE-CERTIFIED (re-elected) as Mayor at the CANCELLED 2025 election — unopposed, deemed elected under Utah Code 20A-1-206 (Res 2025-R-26, adopted 2025-09-10). RESOLVES the prior 'UNDETERMINED whether he was up/re-elected in 2025' note: he WAS certified re-elected (recovered 2026-07-17 into alta_races.csv). A NEW mayoral term seated 2026-01-14; the Mayor VOTES (real vote bounds). Serving."),
]

SEAT_ORDER = ["AL-1", "AL-2", "AL-3", "AL-4", "MAYOR"]
SEAT_DISTRICT = {s: "At-Large" for s in SEAT_ORDER}

# canonical UPPER-CASE election name token -> person_key
NAME_TO_KEY = {
    "BYRNE": "john_byrne",
    "ANCTIL": "carolyn_anctil",
    "MORGAN": "elise_morgan",
    "SCHILLING": "dan_schilling",
    "DAVIS": "sheridan_davis",
    "CURRY": "cliff_curry",
    "SONDAK": "harris_sondak",
    "HEIMARK": "craig_heimark",
    # BOURKE is ambiguous (Roger=Mayor / Margaret=council) -> disambiguators below.
}

# shared-surname disambiguation applied BEFORE the flat surname table (roster_lib.canon_key)
DISAMBIGUATORS = {
    "BOURKE": {"ROGER": "roger_bourke", "MARGARET": "margaret_bourke"},
}

# cities.db person.name_key -> our person_key
DB_KEY = {
    "margaretbourke": "margaret_bourke",
    "cliffcurry": "cliff_curry",
    "sheridandavis": "sheridan_davis",
    "elisemorgan": "elise_morgan",
    "harrissondak": "harris_sondak",
    "johnbyrne": "john_byrne",
    "carolynanctil": "carolyn_anctil",
    "danschilling": "dan_schilling",
    "rogerbourke": "roger_bourke",
    "craigheimark": "craig_heimark",   # 2022-2023 votes are treasurer-era (clamped out); real 2026+
}

ATLARGE = dict(
    district_id="At-Large", plan_id="current",
    effective_start=DATA_FLOOR, effective_end="",
    geometry_ref=GEOM_REF, adopted_by="Town of Alta at-large council structure",
    source_url="", confidence="high",
    note=("DEGENERATE: the Town of Alta's Mayor + 4 councilmembers are all elected "
          "AT-LARGE — no wards/districts, no address->district tool (geo/CLAUDE.md). "
          "This single row covers the whole town. geometry_ref points at the existing "
          "town-limits artifact. effective_start = repo data floor; the at-large "
          "structure predates it."),
)

CFG = RosterConfig(
    non_voting_mayor=False,        # the Alta Mayor VOTES (Utah Town form)
    # H-C (2026-07-19) documented reverse-crosscheck exceptions — the CANCELED-
    # CERTIFICATION class: the 2025 Town of Alta election was CANCELLED (Utah Code
    # 20A-1-206, Res 2025-R-26, adopted 2025-09-10) and the unopposed candidates deemed
    # elected. alta_races.csv carries the 2025 cancelled_certification rows (recovered
    # 2026-07-17), but NO candidate-tally rows exist in alta_results_by_candidate.csv
    # (no votes were cast), so load_election_winners can never see an is_winner row.
    # These tenures' sources cite the certification + Jan-2026 seating minutes verbatim.
    reverse_crosscheck_exceptions={
        ("2025", "Council", "craig_heimark"): "2025 election CANCELLED, certified elected (Res 2025-R-26; alta_races.csv cancelled_certification — no by_candidate tally rows exist)",
        ("2025", "Council", "carolyn_anctil"): "2025 election CANCELLED, certified re-elected (Res 2025-R-26; alta_races.csv cancelled_certification — no by_candidate tally rows exist)",
        ("2025", "Mayor", "roger_bourke"): "2025 election CANCELLED, certified re-elected Mayor (Res 2025-R-26; alta_races.csv cancelled_certification — no by_candidate tally rows exist)",
    },
    city=CITY, city_dir=CITY_DIR, repo_root=REPO_ROOT, data_floor=DATA_FLOOR,
    geom_ref=GEOM_REF, elections_path=ELECTIONS, cities_db_path=CITIES_DB,
    overrides_path=OVERRIDES, terms_out=TERMS_OUT, districts_out=DISTRICTS_OUT,
    seat_district=SEAT_DISTRICT, name_to_key=NAME_TO_KEY, db_key=DB_KEY,
    seat_order=SEAT_ORDER, disambiguators=DISAMBIGUATORS,
    # municipal GENERAL winners only, and only the 2021/2023 cycles present in the built
    # election data (Alta election_results begins 2021). Pre-floor holders (Sondak, Curry,
    # Davis, M.Bourke, Morgan-prefloor) predate the data; the 2025 winners (Heimark, and the
    # re-elected Anctil) are a county-file GAP -> both are minutes-anchored (reverse-crosscheck
    # documented exceptions). Restricting keep_election_row to {2021,2023} keeps the forward
    # crosscheck clean.
    keep_election_row=lambda r: ("general" in r["election_type"].lower()
                                 and int(r["year"]) in (2021, 2023)),
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

    print("\n(b) Roster AS OF 2023-06-01 (council):")
    for r in roster_lib.roster_as_of(CFG, "2023-06-01", body="Council"):
        print(line(r))
    print("    Mayor:")
    for r in roster_lib.roster_as_of(CFG, "2023-06-01", body="Mayor"):
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
