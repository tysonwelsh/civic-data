#!/usr/bin/env python3
"""build_roster.py — rolling council-roster for White City (a slowly-changing-
dimension / interval table of who holds each at-large council + mayor seat over time).

THIN DRIVER: this file holds only White-City-specific DATA (the curated TENURES seat
assignments, the name maps, the at-large district row) + config; all generic mechanics
live in ../scripts/roster_lib.py. Modeled on the bluffdale driver (the AT-LARGE template).

DERIVED LAYER — regenerable, never hand-edited. Canonical inputs:
  1. election_results/white_city_results_by_candidate.csv  (winners -> `elected` terms)
  2. cities.db  role table (city='white_city')             (observed NAMED-vote bounds)
  3. meeting_minutes/minutes/**                             (oath / appointment / resignation)
  4. roster/roster_overrides.csv                            (hand corrections; applied LAST)

Usage:
  python3 roster/build_roster.py            # regenerate the CSVs
  python3 roster/build_roster.py --demo     # regenerate + print the demo queries
  python3 roster/build_roster.py --check    # regenerate + run validations only

Cardinal rule (repo CLAUDE.md): NEVER fabricate. Unknown seat-holder / date ->
UNKNOWN + confidence=low + a note, never a guess. Honest gaps are data.

STRUCTURAL FACTS (verified in source minutes; see roster/CLAUDE.md for the full write-up):
  * 5 voting positions the ENTIRE time (max roll = 5). Metro Township 2017 -> CITY
    (HB35) effective 2024-05-01; the directly-elected executive Mayor (Allan Perry) +
    council seated 2026-01-08. Data floor 2017 (metro township incorporated Jan 2017;
    2017 is agenda-only, earliest recovered minutes 2018-01-04).
  * The presiding officer VOTES in BOTH eras (Millcreek pattern, NOT the non-voting-mayor
    form) -> non_voting_mayor=False; the mayor/chair stays in DB_KEY.
  * Seat model — 5 AT-LARGE seats on two staggered cohorts:
    - Cohort A (3 seats, 2019 / 2023 grouped vote-for-N "At-Large" races): seats
      MAYOR (Flint), AL-A2 (Perry->Huish), AL-A3 (Cutler->Little->Shelton).
    - Cohort B (2 seats, 2017 / 2021 / 2025 cycle): AL-B1 (Price), AL-B2
      (Dickerson->Cardenaz->Mahoney).
  * seat_id MAYOR = the PRESIDING-OFFICER chain (see CLAUDE.md). Township era = the
    peer-selected voting Chair (courtesy-titled "Mayor" per S.B.175, VOTES, body=Council):
    Paulina Flint. City era = the directly-elected executive Mayor (body=Mayor): Allan
    Perry (2026). Flint ran for the executive mayoralty in 2025 and LOST to Perry, so the
    presiding seat passes Flint -> Perry. (Perry also held council seat AL-A2 2020-2024.)
  * BALLOT-STRUCTURE SEAM (flagged): the metro-township 2019 & 2023 council races were
    GROUPED "At-Large" vote-for-3 (like bluffdale). The 2025 city races were NUMBERED,
    single-seat LETTERED contests (Mayor / At-Large B / At-Large C). This driver models
    the reconciliation the bluffdale way (winners_have_district=False, chained by person,
    not by ballot letter) because a single city cannot be both grouped and numbered under
    roster_lib's one crosscheck flag; the lettered city seats map onto the cohort chains
    (city "B"=AL-B1 Price, city "C"=AL-B2 Mahoney; city "A"/"D"=AL-A2/AL-A3, up 2027).
  * TWO documented mid-term vacancies (VACANT-interval convention):
    - Dickerson (AL-B2) RESIGNED 2021-07-08 -> Cardenaz APPOINTED/sworn 2021-08-05
      (Resolution 2021-08-01, "TO FILL AN UNEXPIRED TERM").
    - Little (AL-A3) DIED Nov 2022 (car accident; last present 2022-10-13, vacancy noticed
      2022-12-01) -> Shelton APPOINTED/sworn 2023-01-05 (Resolution 23-01-02).
  * SPARSE / TALLY-ONLY: most motions print no per-member roll, so NAMED-vote bounds are
    thin (Flint 1 named vote, Cardenaz 1, etc.). first_vote/last_vote are loose in-window
    activity bounds, NOT term boundaries. Dickerson & Cutler cast zero named votes (not in
    cities.db) -> no vote bounds; that is the source, not a gap.
  * PRE-2019 layer (medium): the initial 5-member council (Dickerson, Flint, Price, Cutler,
    Perry — present 2018-01-04) was elected in the Nov-2016 even-year general (NOT in the
    odd-year election archive; there is no 2017 White City contest). Their 2017 term-start
    is the incorporation floor; the founding election is pre-data -> confidence medium.
    The 2021 cohort-B general is absent from the county SOVC (uncontested; Price/Cardenaz
    seatings are anchored to the 2022-01-06 oath instead) -> honest gap, not fabricated.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.dirname(HERE)              # white_city_city_council/
REPO_ROOT = os.path.dirname(CITY_DIR)         # civic-data/
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import roster_lib
from roster_lib import RosterConfig

ELECTIONS = os.path.join(CITY_DIR, "election_results", "white_city_results_by_candidate.csv")
CITIES_DB = os.path.join(REPO_ROOT, "cities.db")
OVERRIDES = os.path.join(HERE, "roster_overrides.csv")
TERMS_OUT = os.path.join(HERE, "council_terms.csv")
DISTRICTS_OUT = os.path.join(HERE, "district_versions.csv")

CITY = "white_city"
DATA_FLOOR = "2017-01-01"        # metro township incorporated Jan 2017 (agenda-only; earliest recovered minutes 2018-01-04)
GEOM_REF = "geo/city_boundary.geojson"

TENURES = [
    # ================= Seat MAYOR — the presiding-officer chain =================
    # Township era: Paulina Flint, peer-selected voting Chair (courtesy "Mayor", body=Council).
    # City era: Allan Perry, directly-elected executive Mayor (body=Mayor).
    dict(body="Council", seat_id="MAYOR", person_name="Paulina Flint", person_key="paulina_flint",
         start_date="2017-01-01", start_event="elected", election_year="2016", confidence="medium",
         end_event="reelected",
         sources="minutes:2018-01-04 (present; 'Council Member Flint, Chair, presided'); votes:2021-09-02 (only named vote — tally-only city)",
         note="Initial metro-township council (elected Nov-2016 even-year general — NOT in the odd-year election archive; 2017 is agenda-only). Cohort-A seat. Chair titled 'Mayor' by courtesy (S.B.175, May 2018) and VOTES. seat_id MAYOR labels the presiding-officer chain that becomes the executive mayoralty at the city seam."),
    dict(body="Council", seat_id="MAYOR", person_name="Paulina Flint", person_key="paulina_flint",
         start_date="2020-01-02", start_event="reelected", election_year="2019", confidence="high",
         end_event="reelected",
         sources="election:2019 (Council winner, 559 rank3 of the grouped vote-for-3); minutes:2020-01-02 (oath — 're-elected Council Members Paulina Flint and Allan Perry and newly elected Council Member Scott Little'; elected Mayor/Chair)",
         note="Peer-selected Mayor/Chair (voting)."),
    dict(body="Council", seat_id="MAYOR", person_name="Paulina Flint", person_key="paulina_flint",
         start_date="2024-01-04", start_event="reelected", election_year="2023", confidence="high",
         end_event="lost",
         sources="election:2023 (Council winner, 579 rank1 of the grouped vote-for-3); minutes:2024-01-04 (oath — 're-elected Council Members Paulina Flint and Greg Shelton'; re-elected Mayor)",
         note="Under HB35 the chair-mayoralty converted to a DIRECTLY-ELECTED executive Mayor; Flint ran for it in 2025 and LOST to Allan Perry (456 v 740), so the presiding seat passes to Perry 2026-01-08. Her council service ends there."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Allan Perry", person_key="allan_perry",
         start_date="2026-01-08", start_event="elected", election_year="2025", confidence="high",
         end_event="serving",
         sources="election:2025 (Mayor winner, 740 def. Paulina Flint 456, 61.9%); minutes:2026-01-08 (oath — 'the oath of office to ... Mayor Allan Perry')",
         note="First directly-elected executive Mayor (HB35 city). VOTES (max roll 5). Perry previously held council seat AL-A2 (2020-2024, see that seat) — the same person, two eras."),

    # ================= Seat AL-A2 — Perry (council) -> Huish =================
    dict(body="Council", seat_id="AL-A2", person_name="Allan Perry", person_key="allan_perry",
         start_date="2017-01-01", start_event="elected", election_year="2016", confidence="medium",
         end_event="reelected",
         sources="minutes:2018-01-04 (present)",
         note="Initial metro-township council (Nov-2016 founding, pre-data). Cohort A."),
    dict(body="Council", seat_id="AL-A2", person_name="Allan Perry", person_key="allan_perry",
         start_date="2020-01-02", start_event="reelected", election_year="2019", confidence="high",
         end_event="unknown",
         sources="election:2019 (Council winner, 589 rank2 of the grouped vote-for-3); minutes:2020-01-02 (oath — 're-elected ... Allan Perry')",
         note="NOT a candidate in the 2023 council race -> did not seek council re-election; term expired 2024-01-04 (mechanism unrecorded -> unknown). Later won the 2025 Mayor race (see seat MAYOR)."),
    dict(body="Council", seat_id="AL-A2", person_name="Tyler Huish", person_key="tyler_huish",
         start_date="2024-01-04", start_event="elected", election_year="2023", confidence="high",
         end_event="serving",
         sources="election:2023 (Council winner, 448 rank3 of the grouped vote-for-3); minutes:2024-01-04 (oath — newly elected Council Member Tyler Huish)",
         note="Within-cohort seat number A2 vs A3 (Huish and Shelton, 2023 co-arrivals) is a labelling choice, not source-attested; person-tenure is exact. City seat 'A'/'D' (up 2027) = AL-A2/AL-A3."),

    # ================= Seat AL-A3 — Cutler -> Little (died) -> Shelton =================
    dict(body="Council", seat_id="AL-A3", person_name="Cody Cutler", person_key="cody_cutler",
         start_date="2017-01-01", start_event="elected", election_year="2016", confidence="medium",
         end_event="lost",
         sources="minutes:2018-01-04 (present); election:2019 (ran, 532 rank4 — lost the grouped vote-for-3)",
         note="Initial metro-township council (Nov-2016 founding, pre-data). Lost his cohort-A seat to Scott Little in the 2019 vote-for-3. Casts no named vote in cities.db (tally-only era)."),
    dict(body="Council", seat_id="AL-A3", person_name="Scott Little", person_key="scott_little",
         start_date="2020-01-02", start_event="elected", election_year="2019", confidence="high",
         end_event="deceased",
         vacate_date="2022-12-01", vacate_confidence="high",
         vacate_source="minutes:2022-12-01 (council vacancy declared/noticed); minutes:2023-02-02 ('In November, 2022, Council Member Scott Little passed away unexpectedly')",
         sources="election:2019 (Council winner, 622 rank1 of the grouped vote-for-3); minutes:2020-01-02 (oath — newly elected Council Member Scott Little)",
         note="DIED unexpectedly Nov 2022 (car accident — 2022-11-10 minutes note the accident, excused; last present 2022-10-13; last named vote 2022-05-05). Exact death date not printed in minutes; the seat vacancy was NOTICED 2022-12-01 (applications closed 2022-12-22). Modeled vacate_date=2022-12-01 -> explicit VACANT interval to the Shelton appointment 2023-01-05."),
    dict(body="Council", seat_id="AL-A3", person_name="Greg Shelton", person_key="greg_shelton",
         start_date="2023-01-05", start_event="appointed", election_year="", confidence="high",
         end_event="reelected",
         sources="appt:2023-01-05 (minutes — Resolution 23-01-02 'APPOINTING GREG SHELTON TO FILL AN UNEXPIRED TERM'; oath administered; footnote 'Council Member Shelton was sworn in and acted on agenda items')",
         note="Appointed to fill Scott Little's unexpired cohort-A term (applicants Huish & Shelton interviewed; Shelton selected). Then won the seat outright in 2023."),
    dict(body="Council", seat_id="AL-A3", person_name="Greg Shelton", person_key="greg_shelton",
         start_date="2024-01-04", start_event="elected", election_year="2023", confidence="high",
         end_event="serving",
         sources="election:2023 (Council winner, 558 rank2 of the grouped vote-for-3); minutes:2024-01-04 (oath — 're-elected Council Members Paulina Flint and Greg Shelton')",
         note="Transitioned appointed->elected on the same seat (continuous service). Seat number A3 vs A2 is a labelling choice (see AL-A2)."),

    # ================= Seat AL-B1 — Price (three terms) =================
    dict(body="Council", seat_id="AL-B1", person_name="Linda Price", person_key="linda_price",
         start_date="2017-01-01", start_event="elected", election_year="2016", confidence="medium",
         end_event="reelected",
         sources="minutes:2018-01-04 (present)",
         note="Initial metro-township council (Nov-2016 founding, pre-data). Cohort B (2 seats, 2017/2021/2025 cycle)."),
    dict(body="Council", seat_id="AL-B1", person_name="Linda Price", person_key="linda_price",
         start_date="2022-01-06", start_event="reelected", election_year="2021", confidence="high",
         end_event="reelected",
         sources="minutes:2022-01-06 (oath — 're-elected Council Member Linda Price'); election:2021 ABSENT from the county SOVC (uncontested cohort-B general; honest gap — seating anchored to the oath)",
         note="The 2021 White City council general is not in the county SOVC (uncontested seats carry no tally sheet). The 2022-01-06 oath documents the seating -> confidence high on the seating, gap on the tally."),
    dict(body="Council", seat_id="AL-B1", person_name="Linda Price", person_key="linda_price",
         start_date="2026-01-08", start_event="reelected", election_year="2025", confidence="high",
         end_event="serving",
         sources="election:2025 (Council 'At-Large B' winner, 730, 70.4%); minutes:2026-01-08 (oath — 'Council Member Linda Price')",
         note="2025 was the FIRST city-era election with NUMBERED, single-seat LETTERED contests: this seat ran as 'At-Large B'. (The 2019/2023 township races were grouped vote-for-3.)"),

    # ================= Seat AL-B2 — Dickerson -> Cardenaz -> Mahoney =================
    dict(body="Council", seat_id="AL-B2", person_name="Kay Dickerson", person_key="kay_dickerson",
         start_date="2017-01-01", start_event="elected", election_year="2016", confidence="medium",
         end_event="resigned",
         vacate_date="2021-07-08", vacate_confidence="high",
         vacate_source="minutes:2021-07-08 (resignation letter read — 'I tender my resignation ... effective immediately'; Council moved to accept)",
         sources="minutes:2018-01-04 (present; later Mayor Pro Tem)",
         note="Initial metro-township council (Nov-2016 founding, pre-data). Cohort B. RESIGNED 2021-07-08 (letter 'effective immediately') -> explicit VACANT interval to the Cardenaz appointment 2021-08-05. Casts no named vote in cities.db (tally-only era)."),
    dict(body="Council", seat_id="AL-B2", person_name="Phillip Cardenaz", person_key="phillip_cardenaz",
         start_date="2021-08-05", start_event="appointed", election_year="", confidence="high",
         end_event="reelected",
         sources="appt:2021-08-05 (minutes — Resolution 2021-08-01 'APPOINTING PHILLIP CARDENAZ TO FILL AN UNEXPIRED TERM'; oath administered)",
         note="Appointed to fill Dickerson's unexpired cohort-B term (present & voting by 2021-09-02). Then won the seat in the (uncontested) 2021 general."),
    dict(body="Council", seat_id="AL-B2", person_name="Phillip Cardenaz", person_key="phillip_cardenaz",
         start_date="2022-01-06", start_event="elected", election_year="2021", confidence="high",
         end_event="lost",
         sources="minutes:2022-01-06 (oath — 'newly elected Council Member Phillip Cardenaz'); election:2021 ABSENT from county SOVC (uncontested); election:2025 (ran 'At-Large C', 536 — lost to Mahoney 635); minutes:2026-01-08 (replaced)",
         note="Won the 2021 cohort-B seat (uncontested; not in the county SOVC). Ran for city seat 'At-Large C' in 2025 and LOST to Neil Mahoney. Term ended 2026-01-08."),
    dict(body="Council", seat_id="AL-B2", person_name="Neil Mahoney", person_key="neil_mahoney",
         start_date="2026-01-08", start_event="elected", election_year="2025", confidence="high",
         end_event="serving",
         sources="election:2025 (Council 'At-Large C' winner, 635, def. incumbent Cardenaz 536); minutes:2026-01-08 (oath — 'Council Member Neil Mahoney')",
         note="2025 city-era numbered ballot seat 'At-Large C' = the cohort-B AL-B2 chain (Dickerson->Cardenaz->Mahoney)."),
]

SEAT_DISTRICT = {s: "At-Large" for s in
                 ("MAYOR", "AL-A2", "AL-A3", "AL-B1", "AL-B2")}
SEAT_ORDER = ["MAYOR", "AL-A2", "AL-A3", "AL-B1", "AL-B2"]

# canonical UPPER-CASE election-name token -> person_key (surname suffices; no collisions)
NAME_TO_KEY = {
    "FLINT": "paulina_flint",
    "PERRY": "allan_perry",
    "LITTLE": "scott_little",
    "CUTLER": "cody_cutler",
    "DICKERSON": "kay_dickerson",
    "PRICE": "linda_price",
    "CARDENAZ": "phillip_cardenaz",
    "SHELTON": "greg_shelton",
    "HUISH": "tyler_huish",
    "MAHONEY": "neil_mahoney",
}

# cities.db person.name_key -> our person_key (only members with NAMED votes appear;
# Dickerson & Cutler cast zero named votes -> absent from the db, never mapped).
DB_KEY = {
    "paulinaflint": "paulina_flint",
    "allanperry": "allan_perry",
    "scottlittle": "scott_little",
    "lindaprice": "linda_price",
    "phillipcardenaz": "phillip_cardenaz",
    "gregshelton": "greg_shelton",
    "tylerhuish": "tyler_huish",
    "neilmahoney": "neil_mahoney",
}

ATLARGE = dict(
    district_id="At-Large", plan_id="current",
    effective_start=DATA_FLOOR, effective_end="",
    geometry_ref=GEOM_REF, adopted_by="White City at-large council structure",
    source_url="", confidence="high",
    note=("DEGENERATE: White City's council + mayor are all elected AT-LARGE in BOTH the "
          "metro-township and the post-2024 city era — no wards/districts. This single row "
          "covers the whole city. geometry_ref points at the existing city-limits artifact. "
          "effective_start = incorporation/data floor (Jan 2017); the at-large structure "
          "predates recovered minutes (earliest 2018-01-04)."),
)

CFG = RosterConfig(
    non_voting_mayor=False,       # the presiding officer VOTES in both eras (Millcreek pattern)
    city=CITY, city_dir=CITY_DIR, repo_root=REPO_ROOT, data_floor=DATA_FLOOR,
    geom_ref=GEOM_REF, elections_path=ELECTIONS, cities_db_path=CITIES_DB,
    overrides_path=OVERRIDES, terms_out=TERMS_OUT, districts_out=DISTRICTS_OUT,
    seat_district=SEAT_DISTRICT, seat_order=SEAT_ORDER,
    name_to_key=NAME_TO_KEY, db_key=DB_KEY,
    # Municipal GENERAL winners only (all White City rows are general; years 2019/2023/2025).
    # Modeled the bluffdale way: winners_have_district=False, chained by PERSON, so the mixed
    # grouped(2019/2023) vs numbered-lettered(2025) ballots reconcile under one crosscheck.
    keep_election_row=lambda r: "general" in r["election_type"].lower(),
    contest_key=lambda office, district: office,   # office (Council/Mayor) == body
    crosscheck_field="body", winners_have_district=False,
    elected_events=("elected", "became-mayor", "reelected"),
    # H-C reverse-crosscheck DOCUMENTED exceptions (2026-07-19). crosscheck_field='body'.
    # The 2021 cohort-B township general (Price re-elected AL-B1, Cardenaz elected AL-B2) was
    # UNCONTESTED, so the county published no tally sheet and it is ABSENT from the by_candidate
    # file (which has only 2019/2023/2025). Both seatings are anchored to the 2022-01-06 oath (a
    # documented `high` seating; honest gap on the tally only). Floor year = 2019, so 2021 is above
    # the auto-exempt floor and needs explicit cited entries. Roster correct — see roster/CLAUDE.md.
    reverse_crosscheck_exceptions={
        ("2021", "Council", "linda_price"): "2021 cohort-B township general UNCONTESTED -> absent from the county SOVC (no tally sheet); re-election seating anchored to the 2022-01-06 oath ('re-elected Council Member Linda Price')",
        ("2021", "Council", "phillip_cardenaz"): "2021 cohort-B township general UNCONTESTED -> absent from the county SOVC (no tally sheet); election seating anchored to the 2022-01-06 oath ('newly elected Council Member Phillip Cardenaz')",
    },
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

    print("\n(b) Roster AS OF 2022-06-01 (council):")
    for r in roster_lib.roster_as_of(CFG, "2022-06-01", body="Council"):
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
