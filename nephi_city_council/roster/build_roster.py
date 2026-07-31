#!/usr/bin/env python3
"""build_roster.py — rolling council-roster for Nephi (a slowly-changing-
dimension / interval table of who holds each at-large council + mayor seat over time).

THIN DRIVER: this file holds only Nephi-specific DATA (the curated TENURES seat
assignments, the name maps, the at-large district row) + config; all generic
mechanics live in ../scripts/roster_lib.py (canon_key, election/vote-bounds/
override reconciliation, end-date chaining, validation, the CSV writers, and the
as-of / address / demo query helpers). See that module's docstring to add a city.

DERIVED LAYER — regenerable, never hand-edited. Canonical inputs:
  1. election_results/nephi_results_by_candidate.csv   (winners -> `elected` terms)
  2. cities.db  role table (city='nephi')              (observed vote bounds; appointee detection)
  3. meeting_minutes/minutes/**                         (appointment / oath / became-mayor events)
  4. roster/roster_overrides.csv                        (hand corrections; applied LAST, wins ties)

Outputs (idempotent — re-running reproduces them byte-for-byte):
  roster/council_terms.csv      one row per seat-tenure
  roster/district_versions.csv  boundary interval table (DEGENERATE for Nephi — at-large)

Usage:
  python3 roster/build_roster.py            # regenerate the CSVs
  python3 roster/build_roster.py --demo     # regenerate + print the 3 demo queries
  python3 roster/build_roster.py --check    # regenerate + run validations only

Cardinal rule (repo CLAUDE.md): NEVER fabricate. Unknown seat-holder / date ->
UNKNOWN + confidence=low + a note, never a guess. Honest gaps are data.

Provenance / confidence model:
  high   = anchored to an election result OR a minutes-documented appointment/oath/departure
  medium = inferred from attendance / vote bounds only (e.g. a pre-2020-floor term start)
  low    = guess / genuinely unknown (must be flagged, never silently filled)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.dirname(HERE)              # nephi_city_council/
REPO_ROOT = os.path.dirname(CITY_DIR)         # civic-data/
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import roster_lib
from roster_lib import RosterConfig, TERM_COLUMNS

ELECTIONS = os.path.join(CITY_DIR, "election_results", "nephi_results_by_candidate.csv")
CITIES_DB = os.path.join(REPO_ROOT, "cities.db")
OVERRIDES = os.path.join(HERE, "roster_overrides.csv")
TERMS_OUT = os.path.join(HERE, "council_terms.csv")
DISTRICTS_OUT = os.path.join(HERE, "district_versions.csv")

CITY = "nephi"
DATA_FLOOR = "2020-01-01"       # repo minutes floor; at-large structure predates it
GEOM_REF = "geo/city_boundary.geojson"   # existing city-limits artifact (repo-relative)

# ---------------------------------------------------------------------------
# LAYER 1-3 (reconciled).  Each tenure below is anchored to a cited source.
# Seat model: Nephi runs a 5-member AT-LARGE council on STAGGERED 4-year terms.
#   Cohort A (3 seats) elected the 2019 / 2023 cycle -> seat_id AL-A1..A3
#   Cohort B (2 seats) elected the 2021 / 2025 cycle -> seat_id AL-B1..B2
#   Mayor (1 seat)     elected the 2021 / 2025 cycle -> seat_id MAYOR
# Within-cohort seat numbers are a stable labelling of the person-chain on that
# seat; where two same-cohort newcomers arrive together (Travis Worwood + Cowan,
# 2023) the split between AL-A2 and AL-A3 is a labelling choice, flagged in `note`.
#
# `end_date` / `end_event` are computed by chaining (next tenure on the seat), so
# they are left blank here except where a departure needs an explicit reason that
# chaining can't infer (e.g. lost-election vs did-not-run).
# ---------------------------------------------------------------------------
TENURES = [
    # ---- Seat AL-A1  (Seely -> [vacancy] -> Parady) --------------------------
    dict(body="Council", seat_id="AL-A1", person_name="Justin Seely", person_key="justin_seely",
         start_date="2020-01-07", start_event="elected", election_year="2019",
         end_event="became-mayor", confidence="high",
         sources="election:2019 (Council winner, rank1); minutes:2022-01-04 (oath ceremony — Seely sworn as Mayor, council seat vacated)",
         note="Re-elected incumbent (Deseret marked 'inc.'). Vacated this seat on being sworn Mayor 2022-01-04; see body=Mayor."),
    dict(body="Council", seat_id="AL-A1", person_name="JD Parady", person_key="jd_parady",
         start_date="2022-01-18", start_event="appointed", election_year="",
         end_event="reelected", confidence="high",
         sources="appt:2022-01-18 (minutes — 'JOHN D. PARADY APPOINTED TO THE CITY COUNCIL', unanimous written ballot of Callaway/Memmott/Ostler/Worwood, oath administered)",
         note="Appointed to fill the seat Seely vacated (Seely->Mayor). ~2-week vacancy 2022-01-04..2022-01-18 (Seely sworn Mayor to Parady oath). Then won the seat outright in 2023."),
    dict(body="Council", seat_id="AL-A1", person_name="JD Parady", person_key="jd_parady",
         start_date="2024-01-02", start_event="elected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (Council winner, rank3); minutes:2024-01-02 (oath — 'newly elected council members Shari Cowan, Travis L. Worwood, and JD Parady')",
         note="Transitioned appointed->elected on the same seat (continuous service)."),

    # ---- Seat AL-A2  (Ostler -> Travis Worwood) -----------------------------
    dict(body="Council", seat_id="AL-A2", person_name="Larry Ostler", person_key="larry_ostler",
         start_date="2020-01-07", start_event="elected", election_year="2019",
         end_event="lost", confidence="high",
         sources="election:2019 (Council winner, rank2); election:2023 (ran, rank4 — lost); minutes:2024-01-02 (replaced at oath)",
         note="Re-elected incumbent 2019. Ran again 2023 and lost (rank 4 of 6). Term expired Jan 2024."),
    dict(body="Council", seat_id="AL-A2", person_name="Travis Worwood", person_key="travis_worwood",
         start_date="2024-01-02", start_event="elected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (Council winner, rank1); minutes:2024-01-02 (oath)",
         note="DISTINCT from Skip Worwood (AL-B1): different person — was Nephi City Treasurer (resigned that role 2022-01-18) before winning council 2023. Seat number within the 2023 cohort (AL-A2 vs AL-A3) is a labelling choice: Travis Worwood + Shari Cowan arrived together; person-tenure is exact, the A2/A3 split is not source-attested."),

    # ---- Seat AL-A3  (Memmott -> Cowan) -------------------------------------
    dict(body="Council", seat_id="AL-A3", person_name="Nathan Memmott", person_key="nathan_memmott",
         start_date="2020-01-07", start_event="elected", election_year="2019",
         end_event="unknown", confidence="high",
         sources="election:2019 (Council winner, rank3); minutes:2023-12-05 (still serving), 2024-01-02 (replaced at oath)",
         note="Re-elected incumbent 2019. Served the full 4-year term (present through 2023-12-05). NOT a candidate in the 2023 election -> did not seek re-election; term expired Jan 2024. Departure mechanism (retire vs decline) unrecorded -> end_event=unknown."),
    dict(body="Council", seat_id="AL-A3", person_name="Shari Cowan", person_key="shari_cowan",
         start_date="2024-01-02", start_event="elected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (Council winner, rank2); minutes:2024-01-02 (oath)",
         note="Seat number within the 2023 cohort (AL-A3 vs AL-A2) is a labelling choice (see AL-A2 note); person-tenure is exact."),

    # ---- Seat AL-B1  (Skip Worwood -> Douglas) ------------------------------
    dict(body="Council", seat_id="AL-B1", person_name="Skip Worwood", person_key="skip_worwood",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="reelected", confidence="medium",
         sources="votes:2020-02-04..2024-12-17 (observed serving); minutes:2020-01-07 (already seated at data floor); minutes:2022-01-04 (oath — re-elected 2021)",
         note="PRE-FLOOR term: 2017 election predates the 2019 election-data floor and the 2020 minutes floor; term-start 2018-01 inferred from Nephi's 4-year staggered cohort-B cycle (confidence medium). Cohort B (2 seats). DISTINCT from Travis Worwood."),
    dict(body="Council", seat_id="AL-B1", person_name="Skip Worwood", person_key="skip_worwood",
         start_date="2022-01-04", start_event="elected", election_year="2021",
         end_event="lost", confidence="high",
         sources="election:2021 (Council winner, rank1); minutes:2022-01-04 (oath — 'newly elected council members Skip F. Worwood and Jeramie Callaway'); election:2025 (ran, rank3 general — lost); minutes:2026-01-20 (replaced)",
         note="Re-elected 2021. Ran again 2025, lost the general (rank 3 of 4). Term expired Jan 2026."),
    dict(body="Council", seat_id="AL-B1", person_name="Tate Douglas", person_key="tate_douglas",
         start_date="2026-01-20", start_event="elected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Council winner, rank1 general; also advanced from the Aug-2025 primary); minutes:2026-01-20 (seated)",
         note="Ignore the duplicate 2025 primary is_winner rows (advance != seat); seating is from the municipal general."),

    # ---- Seat AL-B2  (Kent Jones -> Callaway) -------------------------------
    dict(body="Council", seat_id="AL-B2", person_name="Kent Jones", person_key="kent_jones",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="unknown", confidence="medium",
         sources="votes:2020-02-04..2021-11-02 (observed serving); minutes:2020-01-07 (already seated at data floor); minutes:2022-01-04 (replaced at oath)",
         note="PRE-FLOOR term: elected 2017 (inferred from cohort-B cycle — predates the 2019 election-data floor); term-start 2018-01 inferred, confidence medium. NOT a candidate in the 2021 election -> did not seek re-election; term expired Jan 2022, seat won by Callaway. Departure mechanism unrecorded -> end_event=unknown. Never appears in the election dataset (only years 2019+ are covered)."),
    dict(body="Council", seat_id="AL-B2", person_name="Jeramie Callaway", person_key="jeramie_callaway",
         start_date="2022-01-04", start_event="elected", election_year="2021",
         end_event="reelected", confidence="high",
         sources="election:2021 (Council winner, rank2); minutes:2022-01-04 (oath)",
         note="Cohort B."),
    dict(body="Council", seat_id="AL-B2", person_name="Jeramie Callaway", person_key="jeramie_callaway",
         start_date="2026-01-20", start_event="elected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Council winner, rank2 general); minutes:2026-01-20 (seated)",
         note="Re-elected 2025 (continuous service on AL-B2)."),

    # ---- Seat MAYOR  (Nielson -> Seely) -------------------------------------
    dict(body="Mayor", seat_id="MAYOR", person_name="Glade Nielson", person_key="glade_nielson",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="lost", confidence="medium",
         sources="minutes:2020-01-07..2021 (presiding as Mayor); minutes:2022-01-04 ('Out-Going Mayor Glade R. Nielson'); election:2021 (ran Mayor, lost to Seely)",
         note="PRE-FLOOR term: Mayor elected 2017 (inferred; predates the 2019 election-data floor), term-start 2018-01 inferred (medium). Lost the 2021 Mayor race to Seely (965-673); term ended 2022-01-04. NOTE: the cities.db role table mislabels Nielson as body=Council with 2 votes — those 2 are his mayoral TIE-BREAK votes, not council membership."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Justin Seely", person_key="justin_seely",
         start_date="2022-01-04", start_event="became-mayor", election_year="2021",
         end_event="reelected", confidence="high",
         sources="election:2021 (Mayor winner, def. Nielson 965-673); minutes:2022-01-04 (oath as Mayor)",
         note="Moved up from council seat AL-A1 (see Council rows). Mayor does NOT vote except to break a tie."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Justin Seely", person_key="justin_seely",
         start_date="2026-01-20", start_event="reelected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Mayor winner, UNOPPOSED, 1298 votes); minutes:2026-01-20 (term)",
         note="Re-elected 2025 unopposed; term start = first 2026 council meeting (re-oath not separately captured in minutes header)."),
]

# Seat model: all council seats + mayor are elected AT-LARGE -> one district.
SEAT_DISTRICT = {s: "At-Large" for s in
                 ("AL-A1", "AL-A2", "AL-A3", "AL-B1", "AL-B2", "MAYOR")}

# canonical UPPER-CASE election name -> person_key (surname or first name).
NAME_TO_KEY = {
    "JUSTIN": "justin_seely", "SEELY": "justin_seely",
    "LARRY": "larry_ostler", "OSTLER": "larry_ostler",
    "NATHAN": "nathan_memmott", "MEMMOTT": "nathan_memmott",
    "SKIP": "skip_worwood",
    "TRAVIS": "travis_worwood",
    "JERAMIE": "jeramie_callaway", "CALLAWAY": "jeramie_callaway",
    "SHARI": "shari_cowan", "COWAN": "shari_cowan",
    "TATE": "tate_douglas", "DOUGLAS": "tate_douglas",
    "PARADY": "jd_parady",
}
# Worwood needs the first name to disambiguate Skip (cohort B) vs Travis (cohort A).
DISAMBIGUATORS = {"WORWOOD": {"TRAVIS": "travis_worwood", "SKIP": "skip_worwood"}}

# cities.db person.name_key -> our person_key
DB_KEY = {
    "justindseely": "justin_seely", "kentjones": "kent_jones",
    "larryostler": "larry_ostler", "nathanmemmott": "nathan_memmott",
    "skipworwood": "skip_worwood", "gladernielson": "glade_nielson",
    "jdparady": "jd_parady", "jeramiecallaway": "jeramie_callaway",
    "sharicowan": "shari_cowan", "travislworwood": "travis_worwood",
    "tatedouglas": "tate_douglas",
}

ATLARGE = dict(
    district_id="At-Large", plan_id="current",
    effective_start=DATA_FLOOR, effective_end="",
    geometry_ref=GEOM_REF, adopted_by="Nephi Municipal Code (at-large council structure)",
    source_url="", confidence="high",
    note=("DEGENERATE: Nephi's council is elected entirely AT-LARGE — no wards/districts and no "
          "RCV. This single row covers the whole city. district-versioning here is a scaffold; "
          "the sub-district address->representative join must be validated on a district-based "
          "city (West Jordan / Ogden / Provo). geometry_ref points at the existing city-limits "
          "artifact. effective_start = repo data floor; the at-large structure predates it."),
)

CFG = RosterConfig(
    non_voting_mayor=True,
    city=CITY, city_dir=CITY_DIR, repo_root=REPO_ROOT, data_floor=DATA_FLOOR,
    geom_ref=GEOM_REF, elections_path=ELECTIONS, cities_db_path=CITIES_DB,
    overrides_path=OVERRIDES, terms_out=TERMS_OUT, districts_out=DISTRICTS_OUT,
    seat_district=SEAT_DISTRICT, name_to_key=NAME_TO_KEY, db_key=DB_KEY,
    disambiguators=DISAMBIGUATORS,
    keep_election_row=lambda r: "general" in r["election_type"].lower(),
    contest_key=lambda office, district: office,   # office (Council/Mayor) == body
    crosscheck_field="body", winners_have_district=False,
    elected_events=("elected", "became-mayor", "reelected"),
    atlarge=ATLARGE,
)


# ---------------------------------------------------------------------------
# Demo queries (Nephi presentation)
# ---------------------------------------------------------------------------
def demo():
    def line(r):
        end = r["end_date"] or "—(serving)"
        return (f"  {r['seat_id']:<6} {r['person_name']:<16} {r['start_date']} -> {end:<12} "
                f"[{r['start_event']}/{r['end_event']}] conf={r['confidence']}")

    print("\n(a) CURRENT council roster (end_date empty):")
    for r in roster_lib.load_terms(CFG):
        if not r["end_date"] and r["end_event"] == "serving":
            print(line(r))

    print("\n(b) Roster AS OF 2022-07-01 (council):")
    for r in roster_lib.roster_as_of(CFG, "2022-07-01", body="Council"):
        print(line(r))
    print("    Mayor:")
    for r in roster_lib.roster_as_of(CFG, "2022-07-01", body="Mayor"):
        print(line(r))

    print("\n(c) address+date -> representative (through district_versions):")
    for d in ("2022-07-01", "2026-06-01"):
        dist, reps = roster_lib.representatives_for_address(CFG, "21 East 100 North, Nephi UT", d)
        who = ", ".join(f"{x['person_name']}({x['body']})" for x in reps)
        print(f"  '21 E 100 N' on {d}: district={dist} -> {who}")


if __name__ == "__main__":
    rows = roster_lib.build(CFG, TENURES)
    n_high = sum(1 for r in rows if r["confidence"] == "high")
    n_med = sum(1 for r in rows if r["confidence"] == "medium")
    n_low = sum(1 for r in rows if r["confidence"] == "low")
    print(f"Wrote {TERMS_OUT} ({len(rows)} tenures: {n_high} high / {n_med} medium / {n_low} low)")
    print(f"Wrote {DISTRICTS_OUT} (1 district — At-Large, degenerate)")
    if "--demo" in sys.argv:
        demo()
