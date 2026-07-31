#!/usr/bin/env python3
"""build_roster.py — rolling council-roster for COTTONWOOD HEIGHTS (a slowly-changing-dimension /
interval table of who holds each council + mayor seat over time).

Cottonwood Heights is a **DISTRICT city with a VOTING MAYOR**: **4 single-member council districts
(D1..D4) + a separately-elected Mayor who is a FULL voting member** of the council. A complete roll
call tops out at **5** (4 district members + the Mayor), never 6 — `non_voting_mayor=False`, the
Mayor is modelled as a real voting seat (kept in DB_KEY, gets clamped vote bounds). The three mayors
in the record each appear as voting members (Michael Peterson 2018-2022 -> Mike Weichers 2022-2026
-> Gay Lynn Bennion 2026+).

THIN DRIVER: this file holds only CH-specific DATA (curated TENURES, name maps, the 2022-redistricting
facts) + config; all generic mechanics live in ../../scripts/roster_lib.py. Modelled on the
west_jordan driver (DISTRICT + redistricting + precinct-crosscheck template).

DERIVED LAYER — regenerable, never hand-edited. Canonical inputs:
  1. election_results/cottonwood_heights_results_by_candidate.csv  (winners -> elected/reelected; 2017+ rostered)
  2. cities.db  role table (city='cottonwood_heights', body='Council')  (observed vote bounds; incl. the mayor)
  3. meeting_minutes/minutes/**  (oath ceremonies, the 2023 D1 death->appointment)
  4. roster/roster_overrides.csv  (hand corrections; applied LAST, win ties)
  5. geo/precinct_to_district.csv  (read DIRECTLY since 2026-07-19: roster_lib.write_precincts
     accepts a map with no source_year column via the explicit precinct_source_default token
     -- the H-A hardening; the old source_year-wrapper sidecar is RETIRED.)

Outputs (idempotent — re-running reproduces them byte-for-byte):
  roster/council_terms.csv      one row per seat-tenure (4 districts + MAYOR)
  roster/district_versions.csv  boundary interval table — 4 districts x 2 plans + a citywide Mayor row
  roster/district_precincts.csv versioned precinct->district composition (plan-scoped; districts only)

Usage:
  python3 roster/build_roster.py [--demo|--check]

Cardinal rule (repo CLAUDE.md): NEVER fabricate. Unknown seat-holder / boundary / date ->
explicit VACANT / gap + confidence + a note, never a guess.

Provenance / confidence model (Cottonwood Heights):
  high   = an in-file election win (2019/2021/2023/2025) seated at a documented January oath and
           corroborated by the cities.db named-vote record, OR the documented 2023 D1 appointment.
  medium = a Cycle-A HOLDOVER serving at the 2020 floor whose SEATING election (2017) predates the
           minutes floor (Tali Bruce D3, Christine Mikell D4, Mayor Michael Peterson) — plus the D1
           Petersen tenure, whose well-documented 2019 seating is bundled with a GAP-BOUNDED death
           date (weakest-link rule -> medium).
  low    = genuinely unknown / not-acquired (flagged) — the prior-plan (pre-2022) district + precinct
           geometry is an honest GAP; no low rows in council_terms.

STRUCTURAL FACTS (verified in source):
  * VOTING MAYOR (roll of 5). Mayor Michael Peterson presides AND is a full voting member at the 2020
    floor; CH CLAUDE.md confirms 533 mayor vote-rows and NO >5-voter council motion. non_voting_mayor=False.
  * REDISTRICTING — the EFFECT is documented, the ADOPTING INSTRUMENT is NOT in the recovered minutes
    (an honest gap). geo/CLAUDE.md: "CH redrew districts after the 2020 census ... precinct_to_district.csv
    reflects the CURRENT map only (the official layer + 2023/2025 elections); the 2021 (old-map) SOVC
    assigns several COT precincts to a different district." The 2021 cycle (D3/D4/Mayor) used the OLD
    map; the 2023 cycle (D1/D2) is the first under the NEW map. The exact adoption date is NOT in our
    minutes -> plan_switch is ESTIMATED at mid-2022 (peer SLCo cities Herriman/Holladay adopted
    Mar-May 2022), flagged in the district_versions note; the prior boundaries are an unacquired GAP.
  * THE 2023 D1 DEATH IN OFFICE (the headline documented case). Douglas (Doug) Petersen (D1, elected
    2019) DIED mid-term: the 2023-05-15 SPECIAL minutes name candidates "to replace the late Doug
    Petersen" (Mayor Weichers: "the loss of Council member Petersen ... the District 1 seat was won by
    Doug Petersen ... a four-year term"). His last cities.db D1 vote is 2023-04-04; the seat is printed
    "District 1 (Vacant)" by 2023-05-02. The Council interviewed 19 applicants and appointed MATT HOLTON,
    "sworn in at 7:00 p.m. during the Regular Business Meeting" 2023-05-16 (his first cities.db vote).
    Holton then WON the Nov-2023 D1 general -> reseated 2024-01-02. Yields an explicit VACANT D1
    [2023-04-05, 2023-05-16) (the exact death date is unrecorded -> the interval start + the departing
    tenure are medium, gap-bounded).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.dirname(HERE)                 # cottonwood_heights_city_council/
REPO_ROOT = os.path.dirname(CITY_DIR)            # civic-data/
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import roster_lib
from roster_lib import RosterConfig, Redistrict

ELECTIONS = os.path.join(CITY_DIR, "election_results", "cottonwood_heights_results_by_candidate.csv")
PRECINCTS_BYP_SRC = os.path.join(CITY_DIR, "election_results", "cottonwood_heights_results_by_precinct.csv")
PRECINCT_MAP = os.path.join(CITY_DIR, "geo", "precinct_to_district.csv")  # canonical geo map (H-A: sidecar retired 2026-07-19)
CITIES_DB = os.path.join(REPO_ROOT, "cities.db")
OVERRIDES = os.path.join(HERE, "roster_overrides.csv")
TERMS_OUT = os.path.join(HERE, "council_terms.csv")
DISTRICTS_OUT = os.path.join(HERE, "district_versions.csv")
PRECINCTS_OUT = os.path.join(HERE, "district_precincts.csv")

CITY = "cottonwood_heights"
DATA_FLOOR = "2020-01-01"
GEOM_REF = "geo/districts.geojson"

# The redistricting event: EFFECT documented (geo/CLAUDE.md), adopting ordinance NOT in the recovered
# minutes (honest gap). Old map governed the 2021 elections; the NEW (current) map is first used for
# the 2023 D1/D2 general. plan_switch date ESTIMATED at mid-2022 (peer cities adopted Mar-May 2022).
REDISTRICT_ORD = "Cottonwood Heights 2022 redistricting (adopting ordinance not in recovered minutes)"
REDISTRICT_ADOPTED = ""                 # exact adoption date unrecovered -> honest blank
PLAN_OLD = "plan_pre2022"
PLAN_NEW = "plan_2022"
PLAN_SWITCH = "2022-06-01"               # ESTIMATE (see current_note); first used for the 2023 elections
SRC_URL = ("geo/CLAUDE.md (Redistricting seam: CH redrew districts after the 2020 census; the current "
           "official layer + 2023/2025 elections define plan_2022; the 2021 SOVC uses the old map). The "
           "adopting ordinance is not in the recovered minutes.")

SEAT_DISTRICT = {
    "D1": "District 1", "D2": "District 2", "D3": "District 3", "D4": "District 4",
    "MAYOR": "Citywide",
}

TENURES = [
    # ============================ D1 (Cycle B: 2019 / 2023 + the 2023 death-in-office) ============
    dict(body="Council", seat_id="D1", person_name="Douglas Petersen", person_key="douglas_petersen",
         start_date="2020-01-06", start_event="elected", election_year="2019", end_event="deceased",
         confidence="medium",
         vacate_date="2023-04-05", vacate_confidence="medium",
         vacate_source="minutes:2023-05-15 SPECIAL ('replace the late Doug Petersen'; Mayor Weichers on "
                       "'the loss of Council member Petersen'); minutes:2023-05-02 (roll header 'District 1 "
                       "(Vacant)'); last cities.db D1 vote 2023-04-04 (exact death date unrecorded -> "
                       "interval start bounded between 2023-04-04 and 2023-05-02, gap-bounded medium)",
         sources="election:2019 (District 1 winner, def. Deborah Case 52.27%); minutes:2020-01-06 (Oath of "
                 "Office administered to Council Member Douglas Petersen, District 1); votes:2020-01-07.."
                 "2023-04-04 (cities.db, Council/D1)",
         note="Elected D1 2019 (well-documented seating). DIED IN OFFICE mid-term -> explicit VACANT D1 "
              "[2023-04-05, 2023-05-16). The seating is high, but this tenure reads MEDIUM because it "
              "bundles the documented start with a GAP-BOUNDED death date (weakest-link rule)."),
    dict(body="Council", seat_id="D1", person_name="Matt Holton", person_key="matt_holton",
         start_date="2023-05-16", start_event="appointed", election_year="", end_event="succeeded-by-elected",
         confidence="high",
         sources="minutes:2023-05-15/16 SPECIAL ('CITY COUNCIL DISCUSSION OF DISTRICT 1 COUNCIL SEAT "
                 "VACANCY'; 19 applicants; the appointed candidate 'sworn in at 7:00 p.m. during the "
                 "Regular Business Meeting' -> Matt Holton); votes:2023-05-16.. (cities.db, Council/D1)",
         note="APPOINTED to the D1 vacancy left by Petersen's death; sworn 2023-05-16 (his first cities.db "
              "vote). The appointment ends when his elected term is seated 2024-01-02."),
    dict(body="Council", seat_id="D1", person_name="Matt Holton", person_key="matt_holton",
         start_date="2024-01-02", start_event="elected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 1 winner, def. Jen Cottam 56.52%); minutes:2024-01-02 (Oath of "
                 "Office ceremony); votes:continuous through 2026-06-16 (cities.db, Council/D1)",
         note="Won the Nov-2023 D1 general (first D1 term on the plan_2022 lines; seated 2024-01-02) after "
              "the ~7-month interim appointment above. Same person; vote bounds clamped per tenure. Serving."),

    # ============================ D2 (Cycle B: 2019 / 2023) ============================
    dict(body="Council", seat_id="D2", person_name="Scott Bracken", person_key="scott_bracken",
         start_date="2020-01-06", start_event="elected", election_year="2019", end_event="lost",
         confidence="high",
         sources="election:2019 (District 2 winner, def. Tim Hallbeck 57.51%; also won 2011 & 2015); "
                 "minutes:2020-01-06 (Oath of Office ceremony); election:2023 (ran, lost the D2 PRIMARY, "
                 "3rd of 3); votes:2020-01-07..2023-12-05 (cities.db, Council/D2)",
         note="Elected D2 2019 (his 2011/2015 terms are pre-floor). RAN for re-election in 2023 but LOST "
              "the primary (3rd) -> Hyland won the general; left office at the Jan-2024 seating."),
    dict(body="Council", seat_id="D2", person_name="Suzanne Hyland", person_key="suzanne_hyland",
         start_date="2024-01-02", start_event="elected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 2 winner, def. Sharon Daurelle 51.80%); minutes:2024-01-02 (Oath "
                 "of Office ceremony); votes:2024-01-02.. (cities.db, Council/D2)",
         note="Elected D2 2023 (first D2 term on the plan_2022 lines; seated 2024-01-02). Serving."),

    # ============================ D3 (Cycle A: 2017 / 2021 / 2025) ============================
    dict(body="Council", seat_id="D3", person_name="Tali Bruce", person_key="tali_bruce",
         start_date="2018-01-01", start_event="elected", election_year="2017", end_event="did-not-run",
         confidence="medium",
         sources="election:2017 (District 3 winner, def. Michael Larry Hanson 55.76%); votes:2020-01-07.."
                 "2021-10-19 (cities.db, Council/D3)",
         note="Cycle-A HOLDOVER at the 2020 floor: Jan-2018 oath predates the 2020 minutes floor -> start "
              "2018-01-01 inferred (medium); service vote-documented from 2020-01-07. NOT a candidate in "
              "2021 (Newell won D3) -> did not seek re-election; term ended at the 2022-01-03 seating."),
    dict(body="Council", seat_id="D3", person_name="Shawn Newell", person_key="shawn_newell",
         start_date="2022-01-03", start_event="elected", election_year="2021", end_event="reelected",
         confidence="high",
         sources="election:2021 (District 3 winner, 40.36% in a 5-way); minutes:2022-01-03 (City Recorder "
                 "administered the Oath of Office to Shawn E. Newell); votes:2022-01-04.. (cities.db, D3)",
         note="Elected D3 2021. Re-elected 2025 -> continuous."),
    dict(body="Council", seat_id="D3", person_name="Shawn Newell", person_key="shawn_newell",
         start_date="2026-01-05", start_event="reelected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (District 3 winner, def. Randy Prazen 60.99%); minutes:2026-01-05 (Oath of "
                 "Office ceremony); votes:continuous through 2026-06-16 (cities.db, Council/D3)",
         note="Re-elected D3 2025. Serving."),

    # ============================ D4 (Cycle A: 2017 / 2021 / 2025) ============================
    dict(body="Council", seat_id="D4", person_name="Christine Mikell", person_key="christine_mikell",
         start_date="2018-01-01", start_event="elected", election_year="2017", end_event="did-not-run",
         confidence="medium",
         sources="election:2017 (District 4 winner, as 'Christine Watson Mikell', def. Eric Rijk Kraan "
                 "67.78%); votes:2020-01-07..2021-12-14 (cities.db, Council/D4)",
         note="Cycle-A HOLDOVER at the 2020 floor: Jan-2018 oath predates the minutes floor -> start "
              "2018-01-01 inferred (medium). NOT a candidate in 2021 (Birrell won D4) -> did not seek "
              "re-election; term ended at the 2022-01-03 seating."),
    dict(body="Council", seat_id="D4", person_name="Ellen Birrell", person_key="ellen_birrell",
         start_date="2022-01-03", start_event="elected", election_year="2021", end_event="reelected",
         confidence="high",
         sources="election:2021 (District 4 winner, def. Ernie Kim 49.73%); minutes:2022-01-03 (Oath of "
                 "Office ceremony); votes:2022-01-04.. (cities.db, Council/D4)",
         note="Elected D4 2021. Re-elected 2025 -> continuous."),
    dict(body="Council", seat_id="D4", person_name="Ellen Birrell", person_key="ellen_birrell",
         start_date="2026-01-05", start_event="reelected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (District 4 winner, def. Ernie Kim 67.62%); minutes:2026-01-05 (Oath of "
                 "Office ceremony); votes:continuous through 2026-06-16 (cities.db, Council/D4)",
         note="Re-elected D4 2025. Serving."),

    # ============================ MAYOR (Cycle A: 2017 / 2021 / 2025) — VOTING ============
    dict(body="Mayor", seat_id="MAYOR", person_name="Michael Peterson", person_key="michael_peterson",
         start_date="2018-01-01", start_event="elected", election_year="2017", end_event="did-not-run",
         confidence="medium",
         sources="election:2017 (Mayor winner, as 'Mike Peterson', def. Tim Hallbeck 79.22%); minutes:"
                 "2020-01-06 ('Mayor Mike Peterson' presiding at the Oath ceremony — a VOTING mayor); "
                 "votes:2020-01-07..2021-12-14 (cities.db, Council — mayoral votes)",
         note="Cycle-A HOLDOVER at the 2020 floor: Jan-2018 oath predates the minutes floor -> start "
              "2018-01-01 inferred (medium). The CH Mayor is a FULL voting council member "
              "(non_voting_mayor=False). NOT a candidate for Mayor in 2021 (Weichers won) -> did-not-run."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Mike Weichers", person_key="mike_weichers",
         start_date="2022-01-03", start_event="elected", election_year="2021", end_event="lost",
         confidence="high",
         sources="election:2021 (Mayor winner, 38.11% in a 5-way, +509 over Eric Kraan); minutes:2022-01-03 "
                 "(Oath of Office ceremony); election:2025 (incumbent, LOST to Gay Lynn Bennion 42.48%); "
                 "votes:2022-01-04..2025-11-18 (cities.db, Council — mayoral votes)",
         note="Elected Mayor 2021. LOST re-election in 2025 to Gay Lynn Bennion (57.52%) -> left office at "
              "the 2026-01-05 seating."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Gay Lynn Bennion", person_key="gay_lynn_bennion",
         start_date="2026-01-05", start_event="elected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (Mayor winner, def. incumbent Mike Weichers 57.52%); minutes:2026-01-05 "
                 "(Oath of Office ceremony); votes:2026-01-06.. (cities.db, Council — mayoral votes)",
         note="Elected Mayor 2025 (unseating Weichers). VOTING mayor. Serving."),
]

# canonical UPPER-CASE election name token -> person_key. PETERSON (Mayor Michael) and PETERSEN
# (D1 Douglas) are DISTINCT tokens -> no collision. No two CH general winners (2017+) share a
# surname otherwise. Only WINNERS pass through canon_key.
NAME_TO_KEY = {
    "PETERSEN": "douglas_petersen", "HOLTON": "matt_holton", "BRACKEN": "scott_bracken",
    "HYLAND": "suzanne_hyland", "BRUCE": "tali_bruce", "NEWELL": "shawn_newell",
    "MIKELL": "christine_mikell", "BIRRELL": "ellen_birrell", "PETERSON": "michael_peterson",
    "WEICHERS": "mike_weichers", "BENNION": "gay_lynn_bennion",
}

# cities.db person.name_key -> our person_key (council voters, INCLUDING the voting mayors).
DB_KEY = {
    "douglaspetersen": "douglas_petersen", "mattholton": "matt_holton",
    "scottbracken": "scott_bracken", "suzannehyland": "suzanne_hyland",
    "talibruce": "tali_bruce", "shawnenewell": "shawn_newell",
    "christinemikell": "christine_mikell", "ellenbirrell": "ellen_birrell",
    "michaelpeterson": "michael_peterson", "mikeweichers": "mike_weichers",
    "gaylynnbennion": "gay_lynn_bennion",
}


def seat_for_contest(office, district):
    """election (office, district) -> the STABLE seat_id (crosscheck_field='seat_id')."""
    if office == "Mayor":
        return "MAYOR"
    d = district.strip()
    if d in ("1", "2", "3", "4"):
        return "D" + d
    return None


REDISTRICT = Redistrict(
    plan_old=PLAN_OLD, plan_new=PLAN_NEW, plan_switch=PLAN_SWITCH,
    ord=REDISTRICT_ORD, adopted=REDISTRICT_ADOPTED,
    districts=["District 1", "District 2", "District 3", "District 4"],
    geom_ref=GEOM_REF, source_url=SRC_URL, data_floor=DATA_FLOOR,
    current_note=("CURRENT post-2020-census boundaries (Cottonwood Heights' OFFICIAL city-GIS 4-district "
                  "layer, geo/districts.geojson; precinct->district in geo/precinct_to_district.csv). CH "
                  "redrew districts after the 2020 census — the EFFECT is documented (geo/CLAUDE.md; the "
                  "current layer + 2023/2025 elections define this plan, the 2021 SOVC uses the old map) but "
                  "the ADOPTING ORDINANCE is NOT in the recovered minutes -> effective_start (2022-06-01) is "
                  "an ESTIMATE (peer SLCo cities Herriman/Holladay adopted Mar-May 2022; first used for the "
                  "2023 D1/D2 general). Geometry itself is authoritative (high); only the switch DATE is "
                  "estimated."),
    prior_adopted_by="prior plan (pre-2022 boundaries)",
    prior_note=("Prior-plan (pre-2022) district boundaries NOT acquired -> honest GAP (blank geometry_ref, "
                "confidence low). In force through the 2021 elections. effective_start = data floor. "
                "Recoverable from the 2021 by-precinct rows if a historical crosswalk is ever built "
                "(geo/CLAUDE.md), but not reconstructed here."),
    citywide_rows=[
        ("MAYOR", "citywide", "the separately-elected VOTING Mayor (Michael Peterson 2018-2022 -> Mike "
                              "Weichers 2022-2026 -> Gay Lynn Bennion 2026+)"),
    ],
    citywide_adopted_by="Cottonwood Heights City (citywide mayor)",
    citywide_note_template=("{who}: represents the ENTIRE city on every date, unchanged by the 2022 "
                            "redistricting. CH's Mayor is a FULL VOTING council member (roll of 5) — only "
                            "the 4 numbered districts are geographic."),
    precinct_hi_source="current",
    precinct_source_default="current",   # H-A: geo map has no source_year column; explicit token
    precinct_hi_note=("current post-2020-census precinct->district read directly from geo/precinct_to_district.csv "
                      "(no source_year column — the configured precinct_source_default token 'current' "
                      "applies; H-A hardening 2026-07-19, wrapper sidecar retired). "
                      "Official 4-district layer; districts only (the Mayor is city-wide)."),
    precinct_med_note="",
    precinct_prior_note=("Prior-plan (pre-2022) precinct->district composition NOT acquired -> honest GAP."),
    crosscheck_districts=("1", "2", "3", "4"),
    precinct_prefix="COT", geo_seat_prefix="D",
    plan_switch_year="2023", citywide_seats=(),
)

CFG = RosterConfig(
    non_voting_mayor=False,     # CH's Mayor VOTES (roll of 5) — a real voting seat
    city=CITY, city_dir=CITY_DIR, repo_root=REPO_ROOT, data_floor=DATA_FLOOR,
    geom_ref=GEOM_REF, elections_path=ELECTIONS, cities_db_path=CITIES_DB,
    overrides_path=OVERRIDES, terms_out=TERMS_OUT, districts_out=DISTRICTS_OUT,
    seat_district=SEAT_DISTRICT, name_to_key=NAME_TO_KEY, db_key=DB_KEY,
    seat_order=["D1", "D2", "D3", "D4", "MAYOR"],
    # municipal GENERAL winners, 2017+ (the cycles the roster spans). CH election data reaches to
    # 2009 but 2009-2015 are pre-floor cycles not rostered; including them would print unmappable flags.
    keep_election_row=lambda r: (r["election_type"].strip().lower() == "municipal general"
                                 and int(r["year"]) >= 2017),
    contest_key=seat_for_contest, crosscheck_field="seat_id",
    winners_have_district=True,
    elected_events=("elected", "reelected", "became-mayor"),
    redistrict=REDISTRICT, precincts_out=PRECINCTS_OUT,
    precinct_map_path=PRECINCT_MAP, precincts_byprecinct_path=PRECINCTS_BYP_SRC,
)


def demo():
    def line(r):
        end = r["end_date"] or "—(serving)"
        return (f"    {r['seat_id']:<6} {r['person_name']:<20} {r['start_date']} -> {end:<12}"
                f" [{r['start_event']}/{r['end_event']}] conf={r['confidence']}")

    print("\n(a) CURRENT council roster + mayor (end_date empty, end_event=serving):")
    for r in roster_lib.load_terms(CFG):
        if not r["end_date"] and r["end_event"] == "serving":
            print(line(r))

    print("\n(b) Roster AS OF 2023-05-01 (during the D1 vacancy — Petersen died, Holton not yet appointed):")
    for r in roster_lib.roster_as_of(CFG, "2023-05-01", body="Council"):
        print(line(r))
    for r in roster_lib.roster_as_of(CFG, "2023-05-01", body="Mayor"):
        print(line(r))

    print("\n(c) Address+date -> representatives (via geo/address_to_district.py — 1 district + Mayor):")
    addr = "2277 E Bengal Blvd, Cottonwood Heights, UT 84121"   # City Hall -> D3
    for d in ("2026-02-01", "2020-06-01"):
        res = roster_lib.representatives_for_address(CFG, addr, d, latlon=(40.6197, -111.8113))
        who = ", ".join(f"{x['person_name']}({x['seat_id']})" for x in res["reps"])
        loc = (f"District {res['district']} via {res.get('precinct')} [{res.get('method')}]"
               if res.get("district") else f"[{res.get('gap', '?')}]")
        print(f"  '{addr}'\n    on {d} (plan={res['plan']}): {loc}\n    -> your reps: {who or '(none — see gap)'}")

    print("\n(e) Precinct-map cross-check (district_precincts vs election outcomes; districts only):")
    roster_lib.precinct_crosscheck(CFG, verbose=True)


if __name__ == "__main__":
    rows = roster_lib.build(CFG, TENURES)
    n = {c: sum(1 for r in rows if r["confidence"] == c) for c in ("high", "medium", "low")}
    nvac = sum(1 for r in rows if r["start_event"] == "vacated")
    print(f"Wrote {os.path.relpath(TERMS_OUT, CITY_DIR)} "
          f"({len(rows)} tenures incl. {nvac} VACANT: {n['high']} high / {n['medium']} medium / {n['low']} low)")
    print(f"Wrote {os.path.relpath(DISTRICTS_OUT, CITY_DIR)} "
          f"(4 districts x 2 plans + citywide Mayor; redistricting effect documented, ordinance not recovered)")
    print(f"Wrote {os.path.relpath(PRECINCTS_OUT, CITY_DIR)} "
          f"(plan_2022 precinct map + plan_pre2022 gap rows; districts only)")
    if "--check" in sys.argv:
        print("\nValidation: PASS (no overlaps; sources+confidence present; voting-mayor + gap/vacate guards clear).")
        print("Precinct cross-check:")
        roster_lib.precinct_crosscheck(CFG, verbose=True)
    if "--demo" in sys.argv:
        demo()
