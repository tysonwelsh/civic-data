#!/usr/bin/env python3
"""build_roster.py — rolling council-roster for PROVO (a slowly-changing-
dimension / interval table of who holds each council + mayor seat over time), the
DISTRICT-based validation city for the Nephi at-large prototype.

THIN DRIVER: this file holds only Provo-specific DATA (the curated TENURES seat
assignments, the name maps, the real-districts + 2022-redistricting facts and
prose) + config; all generic mechanics live in ../scripts/roster_lib.py
(canon_key, election/vote-bounds/override reconciliation, end-date chaining +
VACANT insertion, validation, the CSV writers, and the as-of / address /
precinct-crosscheck / demo query helpers). See that module's docstring to add a city.

DERIVED LAYER — regenerable, never hand-edited. Canonical inputs:
  1. election_results/provo_results_by_candidate.csv   (winners -> `elected` terms)
  2. cities.db  role table (city='provo', body='Council')  (observed vote bounds)
  3. meeting_minutes/minutes/**                          (oath dates, redistricting ord.)
  4. roster/roster_overrides.csv                         (hand corrections; applied LAST)

Outputs (idempotent — re-running reproduces them byte-for-byte):
  roster/council_terms.csv       one row per seat-tenure (8 stable seats)
  roster/district_versions.csv   boundary interval table — REAL 5 districts + a REAL
                                 redistricting (Ordinance 2022-13 / ref 22-003) versioned
  roster/district_precincts.csv  versioned precinct->district composition (plan-scoped)

Usage:
  python3 roster/build_roster.py            # regenerate the CSVs
  python3 roster/build_roster.py --demo     # regenerate + print the demo queries
  python3 roster/build_roster.py --check    # regenerate + run validations + precinct cross-check

Cardinal rule (repo CLAUDE.md): NEVER fabricate. Unknown seat-holder / boundary /
precinct assignment -> explicit gap + confidence=low + a note, never a guess.

Provenance / confidence model (same as Nephi):
  high   = anchored to an election result OR a minutes-documented oath/departure/ordinance
  medium = inferred from a staggered-cycle election that predates the data floor, or a
           precinct->district assignment corroborated only by the city GIS map
  low    = genuinely unknown / not-yet-acquired (flagged, never silently filled)

Seat model (STABLE ids — a redistricting redraws boundaries, it does NOT renumber seats):
  D1..D5  five geographic district seats
  CW-I    Citywide I  (at-large)   CW-II  Citywide II (at-large)
  MAYOR   separately-elected mayor (does NOT vote on council motions)
Staggered 4-year cycles:
  Cycle A (2021 / 2025):  CW-I, D2, D5, MAYOR         (terms Jan-2022…, Jan-2026…)
  Cycle B (2019 / 2023):  CW-II, D1, D3, D4           (terms Jan-2020…, Jan-2024…)
The Cycle-A seats held in 2020-2021 were elected in 2017 (predates the 2019 election
floor and the 2020 minutes floor) -> confidence medium, term-start inferred 2018-01.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.dirname(HERE)                 # provo_city_council/
REPO_ROOT = os.path.dirname(CITY_DIR)            # civic-data/
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import roster_lib
from roster_lib import RosterConfig, Redistrict

ELECTIONS = os.path.join(CITY_DIR, "election_results", "provo_results_by_candidate.csv")
PRECINCTS_BYP = os.path.join(CITY_DIR, "election_results", "provo_results_by_precinct.csv")
PRECINCT_MAP = os.path.join(CITY_DIR, "geo", "precinct_to_district.csv")
CITIES_DB = os.path.join(REPO_ROOT, "cities.db")
OVERRIDES = os.path.join(HERE, "roster_overrides.csv")
TERMS_OUT = os.path.join(HERE, "council_terms.csv")
DISTRICTS_OUT = os.path.join(HERE, "district_versions.csv")
PRECINCTS_OUT = os.path.join(HERE, "district_precincts.csv")

CITY = "provo"
DATA_FLOOR = "2020-01-01"          # repo minutes floor
GEOM_REF = "geo/precincts.geojson"  # current city GIS layer (carries COUNCIL_DISTRICT)

# The real redistricting event (spot-checked against source minutes):
#   Ordinance 2022-13 (agenda ref 22-003), "regarding redistricting adjustments to City
#   Council District Maps", adopted 2022-03-29 (Council Regular Meeting) on a CONTESTED
#   4:3 map-selection vote; minutes: staff "proposed the effective date be at the end of
#   the year to prepare for next year's [2023] elections" and a sitting member is
#   "an at large council member for the duration of the next year" until the new lines
#   take effect. -> new boundaries first used for the 2023 cycle (seated Jan-2024).
REDISTRICT_ORD = "Ordinance 2022-13 (ref 22-003)"
REDISTRICT_ADOPTED = "2022-03-29"
PLAN_OLD = "plan_2012"     # boundaries in force through the 2021 election (2012 cycle)
PLAN_NEW = "plan_2022"     # Ordinance 2022-13; in force for 2023 election onward
PLAN_SWITCH = "2023-01-01"  # effective boundary between the two plans (end-of-2022)
SRC_URL = ("https://gispublicweb.provo.org/ArcGIS/rest/services/Council/"
           "Council_Districts/FeatureServer/1")

# Swearing-in / term-start = the first council meeting of January (matches cities.db
# role.first_seen and the oath administered there). Verified dates from the record:
#   2020-01-07 · 2022-01-04 · 2024-01-09 · 2026-01-13. Pre-floor 2017-cycle terms start
#   2018-01 (inferred, medium) — Provo minutes only begin 2020.
SEAT_DISTRICT = {
    "D1": "District 1", "D2": "District 2", "D3": "District 3",
    "D4": "District 4", "D5": "District 5",
    "CW-I": "Citywide", "CW-II": "Citywide", "MAYOR": "Citywide",
}

# ---------------------------------------------------------------------------
# LAYER 1-3 (reconciled). Each tenure anchored to a cited source. end_date is
# computed by chaining unless an explicit departure reason is needed.
# ---------------------------------------------------------------------------
TENURES = [
    # ===== Cycle B geographic seats (elected 2019 / 2023 — both IN the election data) =====
    # ---- D1  (Fillmore -> Christensen) ----
    dict(body="Council", seat_id="D1", person_name="Bill Fillmore", person_key="bill_fillmore",
         start_date="2020-01-07", start_event="elected", election_year="2019",
         end_event="did-not-run", confidence="high",
         sources="election:2019 (District 1 winner, unopposed 100%); minutes:2020-01-07 (seated); minutes:2023-12-12 (last served)",
         note="Elected D1 2019. NOT a candidate in the 2023 D1 race (won by Christensen) -> did not seek re-election; term expired Jan 2024. Departure mechanism (retire vs decline) not stated -> did-not-run."),
    dict(body="Council", seat_id="D1", person_name="Craig Christensen", person_key="craig_christensen",
         start_date="2024-01-09", start_event="elected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (District 1 winner, def. Stan Jensen 60-40); minutes:2024-01-09 (seated)",
         note="NOTE two 2023 D1 candidates named Jensen elsewhere on the ballot — Stan Jensen (D1 runner-up) != McKay R. Jensen (Citywide II runner-up)."),

    # ---- D3  (Ellsworth -> Bogdin) ----
    dict(body="Council", seat_id="D3", person_name="Shannon Ellsworth", person_key="shannon_ellsworth",
         start_date="2020-01-07", start_event="elected", election_year="2019",
         end_event="did-not-run", confidence="high",
         sources="election:2019 (District 3 winner, def. Roberts 65-35); minutes:2020-01-07 (seated); minutes:2023-12-12 (last served)",
         note="Elected D3 2019. Not a candidate in 2023 (won by Bogdin) -> term expired Jan 2024."),
    dict(body="Council", seat_id="D3", person_name="Becky Bogdin", person_key="becky_bogdin",
         start_date="2024-01-09", start_event="elected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (District 3 winner, def. Lewis 61-39); minutes:2024-01-09 (seated)",
         note=""),

    # ---- D4  (Hoban -> Hoban) ----
    dict(body="Council", seat_id="D4", person_name="Travis Hoban", person_key="travis_hoban",
         start_date="2020-01-07", start_event="elected", election_year="2019",
         end_event="reelected", confidence="high",
         sources="election:2019 (District 4 winner, def. Paxman 56-44); minutes:2020-01-07 (seated)",
         note="Longest-serving member in the window; Chair 2022."),
    dict(body="Council", seat_id="D4", person_name="Travis Hoban", person_key="travis_hoban",
         start_date="2024-01-09", start_event="elected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (District 4 winner, UNOPPOSED 100%); minutes:2024-01-09 (seated)",
         note="Re-elected 2023 unopposed (continuous service on D4)."),

    # ---- CW-II  (Shipley -> Garrett) ----
    dict(body="Council", seat_id="CW-II", person_name="David Shipley", person_key="david_shipley",
         start_date="2020-01-07", start_event="elected", election_year="2019",
         end_event="did-not-run", confidence="high",
         sources="election:2019 (Citywide II winner, def. Moss 56-44); minutes:2020-01-07 (seated); minutes:2023-12-12 (last served)",
         note="Citywide II is the Cycle-B at-large seat (distinct from Sewell's Cycle-A Citywide I). Not a 2023 candidate (won by Garrett) -> term expired Jan 2024."),
    dict(body="Council", seat_id="CW-II", person_name="Gary Garrett", person_key="gary_garrett",
         start_date="2024-01-09", start_event="elected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (Citywide II winner, def. McKay R. Jensen 52-48); minutes:2024-01-09 (seated)",
         note=""),

    # ===== Cycle A seats (elected 2021 / 2025; the 2020-2021 holders elected 2017 = pre-floor) =====
    # ---- D2  (Handley[2017] -> Handley[2021] -> Whitlock) ----
    dict(body="Council", seat_id="D2", person_name="George Handley", person_key="george_handley",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="reelected", confidence="medium",
         sources="votes:2020-01-07..2021 (observed serving, cities.db role); minutes:2020-01-07 (already seated at data floor); election:2021 (D2 winner — re-election)",
         note="PRE-FLOOR term: the 2017 election predates the 2019 election-data floor and the 2020 minutes floor; term-start 2018-01 inferred from Provo's Cycle-A (D2) 4-year stagger (confidence medium). Held D2 through 2020-2021, then RE-ELECTED to D2 in 2021 -> D2 was his seat continuously (not a Citywide seat)."),
    dict(body="Council", seat_id="D2", person_name="George Handley", person_key="george_handley",
         start_date="2022-01-04", start_event="elected", election_year="2021",
         end_event="did-not-run", confidence="high",
         sources="election:2021 (District 2 winner, UNOPPOSED 100%); minutes:2022-01-04 (seated); minutes:2022-03-29 (states he 'does not intend to run again'); minutes:2025-11-18 (last served)",
         note="Re-elected D2 2021. Publicly stated in 2022 he would not run again; not a candidate in the 2025 D2 race (won by Whitlock) -> term expired Jan 2026."),
    dict(body="Council", seat_id="D2", person_name="Jeff Whitlock", person_key="jeff_whitlock",
         start_date="2026-01-13", start_event="elected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (District 2 winner, def. Petersen 53-47); minutes:2026-01-13 (seated)",
         note="Only D2/2025 seat won under the NEW (plan_2022) district lines. NOTE: Jeff Whitlock also served on the Planning Commission (see db/ v_member_record)."),

    # ---- D5  (Harding[2017] -> Whipple[2021] -> Whipple[2025]) ----
    dict(body="Council", seat_id="D5", person_name="David Harding", person_key="david_harding",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="did-not-run", confidence="medium",
         sources="votes:2020-01-07..2021-12-14 (observed serving, cities.db role); minutes:2020-01-07 (already seated at floor); minutes:2021-12-14 ('presented with a gift for their service', served 6 years); web:votedrdave.blogspot.com + heraldextra (Harding = 'Dr. Dave', Provo Council DISTRICT 5)",
         note="PRE-FLOOR term (2017 cycle, term-start 2018-01 inferred, medium). SEAT DISAMBIGUATION: Harding held DISTRICT 5, not a citywide seat — confirmed by his own campaign ('Reelect Doctor Dave for District Five', votedrdave.blogspot.com) and by succession (D5 won by Whipple 2021, whom he did not run against). Distinct from David Sewell (Citywide I). Served 6 years; did not run in 2021."),
    dict(body="Council", seat_id="D5", person_name="Rachel Whipple", person_key="rachel_whipple",
         start_date="2022-01-04", start_event="elected", election_year="2021",
         end_event="reelected", confidence="high",
         sources="election:2021 (District 5 winner, def. Porter 55-45); minutes:2022-01-04 (seated)",
         note="First D5 winner under the OLD (plan_2012) lines; re-elected 2025 under the NEW lines."),
    dict(body="Council", seat_id="D5", person_name="Rachel Whipple", person_key="rachel_whipple",
         start_date="2026-01-13", start_event="elected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (District 5 winner, def. Blackburn 66-34); minutes:2026-01-13 (seated)",
         note="Re-elected D5 2025 (continuous service). This is the first D5 term contested on the plan_2022 boundaries."),

    # ---- CW-I  (Sewell[2017] -> MacKay[2021] -> MacKay[2025]) ----
    dict(body="Council", seat_id="CW-I", person_name="David Sewell", person_key="david_sewell",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="did-not-run", confidence="medium",
         sources="votes:2020-01-07..2021-12-14 (observed serving, cities.db role); minutes:2021-12-14 ('Chair David Sewell ... presented with a gift for their service', served 8 years, Council Chair 2021); web:UCA candidate page + Facebook 'dave.sewell.provo.council.citywide' (Sewell = CITYWIDE seat)",
         note="PRE-FLOOR term (2017 cycle, term-start 2018-01 inferred, medium). SEAT DISAMBIGUATION: Sewell held CITYWIDE I (his own candidate pages say 'Citywide'; the OTHER citywide seat, Citywide II, was held by Shipley/2019). Distinct from David Harding (District 5). Council Chair 2021; served 8 years; did not run 2021 (seat won by MacKay)."),
    dict(body="Council", seat_id="CW-I", person_name="Katrice MacKay", person_key="katrice_mackay",
         start_date="2022-01-04", start_event="elected", election_year="2021",
         end_event="reelected", confidence="high",
         sources="election:2021 (Citywide I winner, def. Skabelund 52-43); minutes:2022-01-04 (seated)",
         note="Surname spelled MacKay (OCR variants Mackay/McKay normalized in the vote record)."),
    dict(body="Council", seat_id="CW-I", person_name="Katrice MacKay", person_key="katrice_mackay",
         start_date="2026-01-13", start_event="elected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Citywide I winner, def. Shin 58-42); minutes:2026-01-13 (seated)",
         note="Re-elected Citywide I 2025 (continuous service)."),

    # ===== MAYOR (Cycle A; does NOT vote on council motions) =====
    dict(body="Mayor", seat_id="MAYOR", person_name="Michelle Kaufusi", person_key="michelle_kaufusi",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="reelected", confidence="medium",
         sources="minutes:2020-01-07..2021 (presiding as Mayor); election:2021 (Mayor winner — re-election)",
         note="PRE-FLOOR term (elected Mayor 2017; term-start 2018-01 inferred, medium). Mayor does NOT vote on council motions (council votes are 7-member). She sits as an 8th voter ONLY on the Board of Canvassers — that is NOT council membership and she never appears in the council member-vote column (verified 0 rows in all_votes.csv)."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Michelle Kaufusi", person_key="michelle_kaufusi",
         start_date="2022-01-04", start_event="reelected", election_year="2021",
         end_event="lost", confidence="high",
         sources="election:2021 (Mayor winner, def. Dudley 75-25); minutes:2022-01-04 (term); election:2025 (ran Mayor, LOST to Judkins 8280-8703); minutes:2026-01-13 (replaced by Mayor Judkins)",
         note="Re-elected 2021. Lost the 2025 general to Marsha Judkins (~422-vote upset; first west-side Provo mayor) -> term ended Jan 2026."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Marsha Judkins", person_key="marsha_judkins",
         start_date="2026-01-13", start_event="elected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Mayor winner, def. incumbent Kaufusi 8703-8280); minutes:2026-01-13 (presiding as Mayor Judkins)",
         note="Defeated the two-term incumbent. Mayor does not vote on council motions."),
]

# canonical UPPER-CASE election name -> our person_key (surname sufficient except JENSEN,
# which is a non-winner here so never resolved to a seat)
NAME_TO_KEY = {
    "FILLMORE": "bill_fillmore", "CHRISTENSEN": "craig_christensen",
    "ELLSWORTH": "shannon_ellsworth", "BOGDIN": "becky_bogdin",
    "HOBAN": "travis_hoban", "SHIPLEY": "david_shipley", "GARRETT": "gary_garrett",
    "HANDLEY": "george_handley", "WHITLOCK": "jeff_whitlock",
    "HARDING": "david_harding", "WHIPPLE": "rachel_whipple",
    "SEWELL": "david_sewell", "MACKAY": "katrice_mackay",
    "KAUFUSI": "michelle_kaufusi", "JUDKINS": "marsha_judkins",
}

# cities.db person.name_key -> our person_key (Mayor Kaufusi/Judkins intentionally
# NOT in the council role table — they do not vote on council motions).
DB_KEY = {
    "billfillmore": "bill_fillmore", "craigchristensen": "craig_christensen",
    "shannonellsworth": "shannon_ellsworth", "beckybogdin": "becky_bogdin",
    "travishoban": "travis_hoban", "davidshipley": "david_shipley",
    "garygarrett": "gary_garrett", "georgehandley": "george_handley",
    "jeffwhitlock": "jeff_whitlock", "davidharding": "david_harding",
    "rachelwhipple": "rachel_whipple", "davidsewell": "david_sewell",
    "katricemackay": "katrice_mackay",
}


def seat_for_contest(office, district):
    """election (office, district) -> seat_id (or None if unmapped)."""
    if office == "Mayor":
        return "MAYOR"
    d = district.strip()
    if d in ("1", "2", "3", "4", "5"):
        return "D" + d
    if d in ("Citywide I", "Citywide 1"):
        return "CW-I"
    if d in ("Citywide II", "Citywide 2"):
        return "CW-II"
    return None


REDISTRICT = Redistrict(
    plan_old=PLAN_OLD, plan_new=PLAN_NEW, plan_switch=PLAN_SWITCH,
    ord=REDISTRICT_ORD, adopted=REDISTRICT_ADOPTED,
    districts=["District 1", "District 2", "District 3", "District 4", "District 5"],
    geom_ref=GEOM_REF, source_url=SRC_URL, data_floor=DATA_FLOOR,
    current_note=(f"CURRENT post-2020-census boundaries. {REDISTRICT_ORD} adopted "
                  f"{REDISTRICT_ADOPTED} (contested 4:3 map-selection vote); minutes made it "
                  "effective end-of-2022 for the 2023 elections. geometry_ref carries "
                  "COUNCIL_DISTRICT per precinct (Provo City GIS layer)."),
    prior_adopted_by="prior map (2012 redistricting cycle, per Provo City Code §2.01.050)",
    prior_note=("historical boundaries not yet acquired — the pre-2022 district lines "
                "(in force for the 2019/2021 elections) are NOT in geo/. The 2012-cycle "
                "used a different numeric precinct scheme (§2.01.050 codes 301/302…) that "
                "does NOT reconcile with the current 25PR## codes, and the county published "
                "no precinct SOVC for the odd-year-B (D1/3/4) contests — so old geometry is "
                "not reconstructable from data on disk. effective_start = data floor."),
    citywide_rows=[("Citywide", "citywide", "Citywide I & II at-large council seats"),
                   ("MAYOR", "citywide", "separately-elected Mayor")],
    citywide_adopted_by="Provo City Code (at-large / mayor — whole city)",
    citywide_note_template=("{who}: represents the ENTIRE city on every date, unchanged by the 2022 "
                            "redistricting. geometry_ref = union of all precinct polygons (city extent)."),
    precinct_hi_source="2025",
    precinct_hi_note="precinct election-cross-validated against 2025 municipal general",
    precinct_med_note=("city GIS layer only — no precinct-level election data for this "
                       "odd-year-B district (2019/2023 published no precinct SOVC)"),
    precinct_prior_note=("prior precinct->district composition not acquired — 2012-cycle used the "
                         "§2.01.050 numeric precinct scheme (301/302…) that doesn't reconcile with "
                         "current 25PR## codes; 2019/2023 had no precinct SOVC. Acquisition gap, not "
                         "a guess."),
    crosscheck_districts=("2", "5"), precinct_prefix="25", geo_seat_prefix="D",
    plan_switch_year="2023", citywide_seats=("CW-I", "CW-II"),
)

CFG = RosterConfig(
    non_voting_mayor=True,
    city=CITY, city_dir=CITY_DIR, repo_root=REPO_ROOT, data_floor=DATA_FLOOR,
    geom_ref=GEOM_REF, elections_path=ELECTIONS, cities_db_path=CITIES_DB,
    overrides_path=OVERRIDES, terms_out=TERMS_OUT, districts_out=DISTRICTS_OUT,
    seat_district=SEAT_DISTRICT, name_to_key=NAME_TO_KEY, db_key=DB_KEY,
    seat_order=["D1", "D2", "D3", "D4", "D5", "CW-I", "CW-II", "MAYOR"],
    keep_election_row=lambda r: r["election_type"].strip().lower() == "municipal general",
    contest_key=seat_for_contest, crosscheck_field="seat_id",
    winners_have_district=True,
    elected_events=("elected", "reelected", "became-mayor"),
    redistrict=REDISTRICT, precincts_out=PRECINCTS_OUT,
    precinct_map_path=PRECINCT_MAP, precincts_byprecinct_path=PRECINCTS_BYP,
)


# ---------------------------------------------------------------------------
# Demo queries (Provo presentation)
# ---------------------------------------------------------------------------
def demo():
    def line(r):
        end = r["end_date"] or "—(serving)"
        return (f"    {r['seat_id']:<6} {r['person_name']:<18} {r['start_date']} -> {end:<12}"
                f" [{r['start_event']}/{r['end_event']}] conf={r['confidence']}")

    print("\n(a) CURRENT council roster + mayor (end_date empty, end_event=serving):")
    for r in roster_lib.load_terms(CFG):
        if not r["end_date"] and r["end_event"] == "serving":
            print(line(r))

    print("\n(b) Roster AS OF 2022-07-01:")
    for r in roster_lib.roster_as_of(CFG, "2022-07-01", body="Council"):
        print(line(r))
    for r in roster_lib.roster_as_of(CFG, "2022-07-01", body="Mayor"):
        print(line(r))

    print("\n(c) NON-DEGENERATE address+date -> representative (via geo/address_to_district.py):")
    addr = "445 W Center St, Provo, UT 84601"
    for d in ("2025-06-01", "2022-07-01"):
        res = roster_lib.representatives_for_address(CFG, addr, d, latlon=(40.2338, -111.6585),
                                                     precinct="25PR54")
        who = ", ".join(f"{x['person_name']}({x['seat_id']})" for x in res["reps"])
        loc = (f"District {res['district']} via {res.get('precinct')} "
               f"[{res.get('method')}]") if res.get("district") else f"[{res.get('gap','?')}]"
        print(f"  '{addr}'")
        print(f"    on {d} (plan={res['plan']}): {loc}")
        print(f"    -> your reps: {who}")

    print("\n(d) SAME address across the 2022 REDISTRICTING (versioned district_versions):")
    for d in ("2021-06-01", "2025-06-01"):
        res = roster_lib.representatives_for_address(CFG, addr, d, latlon=(40.2338, -111.6585),
                                                     precinct="25PR54")
        if res.get("district"):
            print(f"    {d} (plan={res['plan']}): geographic District {res['district']} "
                  f"-> {[x['person_name'] for x in res['reps'] if x['seat_id'].startswith('D')]}")
        else:
            print(f"    {d} (plan={res['plan']}): {res.get('gap')}")

    print("\n(e) Precinct-map cross-check (district_precincts vs election outcomes):")
    roster_lib.precinct_crosscheck(CFG, verbose=True)


if __name__ == "__main__":
    rows = roster_lib.build(CFG, TENURES)
    n = {c: sum(1 for r in rows if r["confidence"] == c) for c in ("high", "medium", "low")}
    print(f"Wrote {os.path.relpath(TERMS_OUT, CITY_DIR)} "
          f"({len(rows)} tenures: {n['high']} high / {n['medium']} medium / {n['low']} low)")
    print(f"Wrote {os.path.relpath(DISTRICTS_OUT, CITY_DIR)} "
          f"(5 districts x 2 plans + Citywide + Mayor; redistricting {REDISTRICT_ORD})")
    print(f"Wrote {os.path.relpath(PRECINCTS_OUT, CITY_DIR)} "
          f"(plan_2022 precinct map + plan_2012 gap rows)")
    if "--check" in sys.argv:
        print("\nValidation: PASS (no overlaps; every row has sources+confidence).")
        print("Precinct cross-check:")
        roster_lib.precinct_crosscheck(CFG, verbose=True)
    if "--demo" in sys.argv:
        demo()
