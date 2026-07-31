#!/usr/bin/env python3
"""build_roster.py — rolling council-roster for OGDEN (a slowly-changing-dimension /
interval table of who holds each council + mayor seat over time). Ogden is a MIXED
district + at-large city with a NON-VOTING (strong-mayor) mayor — structurally the
Provo template (real districts + at-large + non-voting mayor + a post-2020-census
redistricting + precinct/address join) with the Logan/Millcreek council-chair->mayor
CROSSOVER (Ben Nadolski: voting D4 council chair 2020-2023, then Mayor 2024-01-02).

THIN DRIVER: this file holds only Ogden-specific DATA (the curated TENURES seat
assignments, the name maps, the 2022-redistricting facts + prose) + config; all generic
mechanics live in ../scripts/roster_lib.py (canon_key, election/vote-bounds/override
reconciliation, end-date chaining + VACANT insertion, validation, the CSV writers, and
the as-of / address / precinct-crosscheck / demo query helpers). See that module's
docstring to add a city.

DERIVED LAYER — regenerable, never hand-edited. Canonical inputs:
  1. election_results/ogden_results_by_candidate.csv  (municipal-general winners -> terms)
  2. cities.db  role table (city='ogden', body='Council')  (observed vote bounds)
  3. meeting_minutes/minutes/**                          (oath dates, redistricting ord.)
  4. roster/roster_overrides.csv                         (hand corrections; applied LAST)

Outputs (idempotent — re-running reproduces them byte-for-byte):
  roster/council_terms.csv       one row per seat-tenure (8 stable seats)
  roster/district_versions.csv   boundary interval table — REAL 4 districts + the 2022
                                 redistricting (Ordinance 2022-9) versioned + At-Large + Mayor
  roster/district_precincts.csv  versioned precinct->district composition (plan-scoped)
  (The _precinct_votes.csv SIDECAR was RETIRED 2026-07-11 — roster_lib's precinct_crosscheck now
   has a built-in blank/suppressed vote guard, so it reads the canonical
   election_results/ogden_results_by_precinct.csv directly.)

Usage:
  python3 roster/build_roster.py            # regenerate the CSVs
  python3 roster/build_roster.py --demo     # regenerate + print the demo queries
  python3 roster/build_roster.py --check    # regenerate + run validations + precinct cross-check

Cardinal rule (repo CLAUDE.md): NEVER fabricate. Unknown seat-holder / boundary /
precinct assignment -> explicit gap + confidence=low + a note, never a guess.

Provenance / confidence model (same as Provo/Nephi):
  high   = anchored to an in-data election result OR a minutes-documented oath/departure/ordinance
  medium = inferred from a staggered-cycle election that predates the data floor (2017-cycle
           B-seat incumbents seated at the 2020 floor), or a precinct assignment corroborated
           only by the city GIS map
  low    = genuinely unknown / not-yet-acquired (flagged, never silently filled)

Seat model (STABLE ids — a redistricting redraws boundaries, it does NOT renumber seats):
  D1..D4  four geographic district seats
  AL-A / AL-B / AL-C   three at-large ("At-Large Seat A/B/C") seats
  MAYOR   separately-elected mayor (strong-mayor form — does NOT vote on council motions)
Staggered 4-year cycles (election_results/CLAUDE.md, confirmed from source):
  A-cycle (2019 / 2023):  MAYOR, AL-C, D2, D4     (terms Jan-2020… / Jan-2024…)
  B-cycle (2021 / 2025):  AL-A, AL-B, D1, D3      (terms Jan-2022… / Jan-2026…)
The B-cycle seats held in 2020-2021 were elected in 2017 (predates the 2019 election
floor and the 2020 minutes floor) -> confidence medium, term-start inferred 2018-01.
The A-cycle 2019 winners ARE in the election data (floor is 2019 for elections) -> high.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.dirname(HERE)                 # ogden_city_council/
REPO_ROOT = os.path.dirname(CITY_DIR)            # civic-data/
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import roster_lib
from roster_lib import RosterConfig, Redistrict

ELECTIONS = os.path.join(CITY_DIR, "election_results", "ogden_results_by_candidate.csv")
PRECINCTS_BYP_SRC = os.path.join(CITY_DIR, "election_results", "ogden_results_by_precinct.csv")
PRECINCT_MAP = os.path.join(CITY_DIR, "geo", "precinct_to_district.csv")
CITIES_DB = os.path.join(REPO_ROOT, "cities.db")
OVERRIDES = os.path.join(HERE, "roster_overrides.csv")
TERMS_OUT = os.path.join(HERE, "council_terms.csv")
DISTRICTS_OUT = os.path.join(HERE, "district_versions.csv")
PRECINCTS_OUT = os.path.join(HERE, "district_precincts.csv")

CITY = "ogden"
DATA_FLOOR = "2020-01-01"                          # repo minutes/votes floor
GEOM_REF = "geo/council_districts.geojson"         # 4 dissolved district polygons (MUNIWARD)

# The real redistricting event (spot-checked against source minutes 2022-03-15):
#   Ordinance 2022-9 (Joint Resolution 2022-3), "revising the four municipal districts and
#   adopting the official municipal district boundary map of Ogden City" — amends Ogden
#   Municipal Code Sec 1-7-2. Adopted 2022-03-15 on a CONTESTED 6:1 roll call (AYE Blair,
#   Hyer, Richey, White, Vice Chair Lopez, Chair Nadolski; NO Choberka, who wanted more
#   community outreach). Follows the county's new Dec-2021 precincts; "this map most closely
#   resembles the existing boundaries" (minimal change). Effective IMMEDIATELY upon posting
#   after final passage -> in force for the 2023 & 2025 elections; the 2021 election used the
#   prior (pre-2022) lines.
REDISTRICT_ORD = "Ordinance 2022-9 (Joint Res. 2022-3)"
REDISTRICT_ADOPTED = "2022-03-15"
PLAN_OLD = "plan_2012"      # boundaries in force through the 2021 election
PLAN_NEW = "plan_2022"      # Ordinance 2022-9; in force for the 2023 election onward
PLAN_SWITCH = "2022-03-15"  # effective-immediately date in the ordinance text
SRC_URL = ("https://arcgis.ogdencity.com/arcgis/rest/services/Public/"
           "Ogden_Voting_Precincts/FeatureServer/0")

# Swearing-in / term-start = the first council meeting of January (matches cities.db
# role.first_seen and the oath administered there). Verified dates from the record:
#   2020-01-07 (Caldwell/Hyer/Lopez/Nadolski sworn) · 2022-01-04 (Choberka re-sworn, Richey
#   seated) · 2024-01-02 (Graf/Hyer/Myers + Mayor Nadolski sworn) · 2026-01-06 (Washington/
#   Lundell + Vice Chair Graf sworn; Flor Lopez sworn 2026-01-20 — see D1). Pre-floor
#   2017-cycle B-seat terms start 2018-01 (inferred, medium) — Ogden minutes begin 2020.
SEAT_DISTRICT = {
    "D1": "District 1", "D2": "District 2", "D3": "District 3", "D4": "District 4",
    "AL-A": "At-Large", "AL-B": "At-Large", "AL-C": "At-Large",
    "MAYOR": "Citywide",
}

# ---------------------------------------------------------------------------
# LAYER 1-3 (reconciled). Each tenure anchored to a cited source. end_date is
# computed by chaining unless an explicit departure reason is needed.
# ---------------------------------------------------------------------------
TENURES = [
    # ===== A-cycle geographic seats (elected 2019 / 2023 — both IN the election data) =====
    # ---- D2  (Hyer -> Hyer; unopposed both cycles) ----
    dict(body="Council", seat_id="D2", person_name="Richard A. Hyer", person_key="richard_hyer",
         start_date="2020-01-07", start_event="elected", election_year="2019",
         end_event="reelected", confidence="high",
         sources="election:2019 (District 2 winner, UNOPPOSED 100%); minutes:2020-01-07 (Oath of Office administered to newly elected Council member Richard A. Hyer)",
         note="Elected D2 2019 (unopposed). Longest-tenured member in the window ('16 years' of service he noted in 2020). Chair 2024-2026. Re-elected D2 2023 (unopposed) -> continuous."),
    dict(body="Council", seat_id="D2", person_name="Richard A. Hyer", person_key="richard_hyer",
         start_date="2024-01-02", start_event="reelected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (District 2 winner, UNOPPOSED 100%); minutes:2024-01-02 (Oath of Office administered to newly elected/re-elected Council members Dave Graf, Richard A. Hyer, and Shaun Myers)",
         note="Re-elected D2 2023 unopposed (continuous service). Currently serving (Chair)."),

    # ---- D4  (Nadolski -> Graf) — THE council-chair -> mayor crossover ----
    dict(body="Council", seat_id="D4", person_name="Ben Nadolski", person_key="ben_nadolski",
         start_date="2020-01-07", start_event="elected", election_year="2019",
         end_event="became-mayor", confidence="high",
         sources="election:2019 (District 4 winner, UNOPPOSED 100%); minutes:2020-01-07 (Chair Ben Nadolski, oath administered — re-elected); votes:cities.db role 2020-01-07..2023-12-19 (last council vote); election:2023 (WON the Mayor race, def. Knuth); minutes:2024-01-02 (sworn as Mayor, vacating D4)",
         note="Held DISTRICT 4 and was Council CHAIR 2020-2023 (a VOTING member — his council votes run 2020-01-07..2023-12-19 in cities.db). WON the 2023 MAYOR race and was sworn as Mayor 2024-01-02, so his D4 term expired at the regular cycle boundary the same day (a CLEAN term-end handoff, NOT a mid-term vacancy — the 2023 election filled D4 with Graf). His D4 tenure ends 2024-01-02 and his MAYOR tenure begins 2024-01-02 (half-open intervals — no overlap). See the MAYOR block; the non_voting_mayor flag empties his mayor-row vote bounds, and the tenure-window clamp independently confines this D4 row to [2020-01-07, 2024-01-02) (first_vote 2020-01-07, last_vote 2023-12-19) — his 2020-2023 council span cannot land on the mayoralty."),
    dict(body="Council", seat_id="D4", person_name="Dave Graf", person_key="dave_graf",
         start_date="2024-01-02", start_event="elected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (District 4 winner, def. Steven Van Wagoner 52.68-47.32); minutes:2024-01-02 (Oath of Office administered … Dave Graf); votes:cities.db first_seen 2024-02-06",
         note="Elected D4 2023 (newcomer replacing Nadolski, who moved to Mayor). Vice Chair 2026. first_vote in cities.db is 2024-02-06 — the named-roll-call seam (seated 2024-01-02; his first recorded named vote is 2024-02-06), a recording lag not the term start. Currently serving."),

    # ---- AL-C  (Luis Lopez -> Myers) ----
    dict(body="Council", seat_id="AL-C", person_name="Luis Lopez", person_key="luis_lopez",
         start_date="2020-01-07", start_event="elected", election_year="2019",
         end_event="did-not-run", confidence="high",
         sources="election:2019 (At-Large Seat C winner, UNOPPOSED 100%); minutes:2020-01-07 (Oath of Office administered … Luis Lopez); votes:cities.db role last_seen 2023-12-19; election:2023 (not a candidate)",
         note="Elected At-Large C 2019 (unopposed). Vice Chair 2022. NOT a candidate in the 2023 At-Large C race (won by Myers) -> term expired Jan 2024 -> did-not-run. DISTINCT from Flor Lopez (D1, 2025+) — two different people, disambiguated by first name."),
    dict(body="Council", seat_id="AL-C", person_name="Shaun Myers", person_key="shaun_myers",
         start_date="2024-01-02", start_event="elected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (At-Large Seat C winner, def. J. Levi Andersen 59.3-40.7); minutes:2024-01-02 (Oath of Office administered … Shaun Myers); votes:cities.db first_seen 2024-02-06",
         note="Elected At-Large C 2023 (newcomer replacing Luis Lopez). first_vote 2024-02-06 is the named-roll-call seam. Currently serving."),

    # ===== B-cycle seats (elected 2021 / 2025; the 2020-2021 holders elected 2017 = pre-floor) =====
    # ---- D1  (Choberka[2017] -> Choberka[2021] -> Flor Lopez[2025]) ----
    dict(body="Council", seat_id="D1", person_name="Angela Choberka", person_key="angela_choberka",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="reelected", confidence="medium",
         sources="votes:2020-01-07.. (observed serving, cities.db role first_seen); minutes:2020-01-07 ('Vice Chair Choberka' present and NOT among those sworn in that day -> a continuing 2017-cycle incumbent, not a 2019 winner); election:2021 (District 1 winner — re-election)",
         note="PRE-FLOOR term: the 2017 election predates the 2019 election-data floor and the 2020 minutes floor; term-start 2018-01 inferred from Ogden's B-cycle 4-year stagger (row confidence medium — only the START date is inferred; her 2020-2021 membership is documented). Held DISTRICT 1 (Vice Chair 2020), then RE-ELECTED to D1 in 2021 -> D1 was her seat continuously."),
    dict(body="Council", seat_id="D1", person_name="Angela Choberka", person_key="angela_choberka",
         start_date="2022-01-04", start_event="reelected", election_year="2021",
         end_event="did-not-run", confidence="high",
         sources="election:2021 (District 1 winner, def. Thomas H. Gooch 64.1-35.9); minutes:2022-01-04 (Oath of Office administered to newly re-elected Council member Angela Choberka); minutes:2026-01-06 (her final meeting — 'her last meeting … after eight years on the Council')",
         note="Re-elected D1 2021. NOT a candidate in the 2025 D1 race (won by Flor Lopez) -> term expired Jan 2026 -> did-not-run. Her last ATTENDED meeting was 2026-01-06; she held the seat as a holdover until her successor Flor Lopez qualified (sworn 2026-01-20), so D1 chains 2026-01-20 with NO vacancy. NB: the 2026-05-19 minutes carry a preserved clerk roll-call typo whose single VOTING-AYE line lists departed members BLAIR & CHOBERKA (that meeting's own present-list shows the correct seated council). That stray 2026-05-19 vote falls OUTSIDE her D1 tenure window [2022-01-04, 2026-01-20), so the tenure-window clamp excludes it and her last_vote is her true last vote 2026-01-06."),
    dict(body="Council", seat_id="D1", person_name="Flor Lopez", person_key="flor_lopez",
         start_date="2026-01-20", start_event="elected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (District 1 winner, def. Jase Reyneveld 60.12-39.88); minutes:2026-01-06 (Chair noted 'Council member Elect Lopez was unavailable to be sworn in to office until the second week of January'); minutes:2026-01-20 (present + voting); votes:cities.db first_seen 2026-01-20",
         note="Elected D1 2025 — the first D1 seat won under the NEW (plan_2022) district lines. Sworn ~mid-January and first attested voting 2026-01-20 (her predecessor Choberka held the seat over from her 2026-01-06 final meeting until then -> no gap). DISTINCT from Luis Lopez (At-Large C, <=2023) — two different people, disambiguated by first name. Currently serving."),

    # ---- D3  (Stephens[2017] -> Richey[2021] -> Richey[2025]) ----
    dict(body="Council", seat_id="D3", person_name="Doug Stephens", person_key="doug_stephens",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="did-not-run", confidence="medium",
         sources="votes:2020-01-07.. (observed serving, cities.db role first_seen); minutes:2020-01-07 ('Council member Stephens' present and NOT among those sworn in that day -> a continuing 2017-cycle incumbent); election:2021 (District 3 won by Ken Richey — Stephens not a candidate)",
         note="PRE-FLOOR term (2017 cycle; term-start 2018-01 inferred from the B-cycle stagger, medium). SEAT ASSIGNED BY ELIMINATION: the four 2020-2021 B-cycle incumbents were Choberka (D1), White (AL-A), Blair (AL-B) — each RE-ELECTED to that seat in 2021 — and Stephens, the departing incumbent, whose seat (D3) was won by newcomer Ken Richey in 2021. Not a 2021 candidate -> term expired Jan 2022 -> did-not-run. NB: the Jan-2022 chair-election roll calls PRINT departed member STEPHENS (a preserved source clerk typo — Richey was the sitting D3 member; see meeting_minutes/CLAUDE.md), giving him a stray 2022-01-11 db vote. That date falls OUTSIDE his D3 tenure window [2018-01-01, 2022-01-04), so the tenure-window clamp excludes it and his last_vote is 2021-12-21. His true last service ended in 2021."),
    dict(body="Council", seat_id="D3", person_name="Ken Richey", person_key="ken_richey",
         start_date="2022-01-04", start_event="elected", election_year="2021",
         end_event="reelected", confidence="high",
         sources="election:2021 (District 3 winner, def. Priscilla Martinez 51.61-48.39); minutes:2022-01-04 (seated; present as Council member Ken Richey); votes:cities.db first_seen 2022-01-04",
         note="Elected D3 2021 (newcomer replacing Stephens). Election name 'KEN RICHEY' (2021) == 'KEN R. RICHEY' (2025) — same person. Re-elected 2025 (continuous D3)."),
    dict(body="Council", seat_id="D3", person_name="Ken Richey", person_key="ken_richey",
         start_date="2026-01-06", start_event="reelected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (District 3 winner, def. Heath Satow 52.15-47.85); minutes:2026-01-06 (present, first meeting of the new term — re-elected incumbent)",
         note="Re-elected D3 2025 (continuous service; a returning incumbent so no swearing gap). First D3 term contested on the plan_2022 lines. Currently serving."),

    # ---- AL-A  (White[2017] -> White[2021] -> Washington[2025]) ----
    dict(body="Council", seat_id="AL-A", person_name="Marcia L. White", person_key="marcia_white",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="reelected", confidence="medium",
         sources="votes:2020-01-07.. (observed serving, cities.db role first_seen); minutes:2020-01-07 ('Council member White' present and NOT among those sworn in that day -> a continuing 2017-cycle incumbent); election:2021 (At-Large Seat A winner — re-election)",
         note="PRE-FLOOR term (2017 cycle; term-start 2018-01 inferred from the B-cycle stagger, medium). Held AT-LARGE SEAT A, then RE-ELECTED to At-Large A in 2021 -> continuous. Vice Chair 2022-2023. DISTINCT from Alicia Washington (AL-A successor) — different people."),
    dict(body="Council", seat_id="AL-A", person_name="Marcia L. White", person_key="marcia_white",
         start_date="2022-01-04", start_event="reelected", election_year="2021",
         end_event="lost", confidence="high",
         sources="election:2021 (At-Large Seat A winner, def. Daniel J. Gladwell 60.47-39.53); minutes:2022-01-04 (seated); votes:cities.db role last_seen 2025-12-16; election:2025 (ran At-Large A, LOST to Alicia Washington 43.37-56.63)",
         note="Re-elected At-Large A 2021. LOST the 2025 general to Alicia Washington -> term ended Jan 2026. Served through the 2025-12-16 meeting (her genuine last recorded vote)."),
    dict(body="Council", seat_id="AL-A", person_name="Alicia Washington", person_key="alicia_washington",
         start_date="2026-01-06", start_event="elected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (At-Large Seat A winner, def. Marcia White 56.63-43.37); minutes:2026-01-06 (present + sworn); votes:cities.db first_seen 2026-01-06",
         note="Elected At-Large A 2025 (defeated incumbent Marcia White). Currently serving."),

    # ---- AL-B  (Blair[2017] -> Blair[2021] -> Lundell[2025]) ----
    dict(body="Council", seat_id="AL-B", person_name="Bart E. Blair", person_key="bart_blair",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="reelected", confidence="medium",
         sources="votes:2020-01-07.. (observed serving, cities.db role first_seen); minutes:2020-01-07 ('Council member Bart E. Blair' present and NOT among those sworn in that day -> a continuing 2017-cycle incumbent); election:2021 (At-Large Seat B winner — re-election)",
         note="PRE-FLOOR term (2017 cycle; term-start 2018-01 inferred from the B-cycle stagger, medium). Held AT-LARGE SEAT B, then RE-ELECTED to At-Large B in 2021 -> continuous. Council Chair 2022-2023."),
    dict(body="Council", seat_id="AL-B", person_name="Bart E. Blair", person_key="bart_blair",
         start_date="2022-01-04", start_event="reelected", election_year="2021",
         end_event="lost", confidence="high",
         sources="election:2021 (At-Large Seat B winner, def. Sebastian Benitez 54.27-45.73); minutes:2022-01-04 (seated, Chair); election:2025 (ran At-Large B, LOST to Kevin Lundell 39.76-60.24); minutes:2026-01-06 ('Former Council Member Blair spoke …')",
         note="Re-elected At-Large B 2021 (Council Chair 2022-2023). LOST the 2025 general to Kevin Lundell -> term ended Jan 2026; addressed as 'Former Council Member Blair' at the 2026-01-06 meeting. NB: the 2026-05-19 minutes carry a preserved clerk roll-call typo whose single VOTING-AYE line lists departed members BLAIR & CHOBERKA (that meeting's present-list shows the correct seated council). That stray 2026-05-19 vote falls OUTSIDE his AL-B tenure window [2022-01-04, 2026-01-06), so the tenure-window clamp excludes it and his last_vote is 2025-12-16. His true last service ended 2026-01-06."),
    dict(body="Council", seat_id="AL-B", person_name="Kevin Lundell", person_key="kevin_lundell",
         start_date="2026-01-06", start_event="elected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (At-Large Seat B winner, def. Bart E. Blair 60.24-39.76); minutes:2026-01-06 (present + sworn); votes:cities.db first_seen 2026-01-06",
         note="Elected At-Large B 2025 (defeated incumbent Bart Blair). Currently serving."),

    # ===== MAYOR (A-cycle; strong-mayor form — does NOT vote on council motions) =====
    dict(body="Mayor", seat_id="MAYOR", person_name="Michael P. Caldwell", person_key="mike_caldwell",
         start_date="2020-01-07", start_event="elected", election_year="2019",
         end_event="did-not-run", confidence="high",
         sources="election:2019 (Mayor winner, def. Angel Castillo 57.47-42.53); minutes:2020-01-07 ('Administration of the Oath of Office for newly elected Mayor Michael P. Caldwell'); election:2023 (not a candidate — race was Nadolski vs Knuth); minutes:2024-01-02 (replaced by Mayor Nadolski)",
         note="Mayor 2020-2023 (his third term; elected 2011/2015/2019 — the 2019 win is IN the election data so no pre-floor inference needed). Strong-mayor form: he does NOT vote on council legislation and never appears in a council roll call (0 cities.db council rows) -> the non_voting_mayor flag keeps his vote bounds empty. Did not run in 2023 -> term ended Jan 2024."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Ben Nadolski", person_key="ben_nadolski",
         start_date="2024-01-02", start_event="became-mayor", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (Mayor winner, def. Taylor Knuth 54.36-45.64); minutes:2024-01-02 ('newly elected Mayor Benjamin K. Nadolski' sworn); minutes:2024-01-09+ (presiding as Mayor Nadolski)",
         note="MAYOR (not a council seat). SAME person as the D4 councilmember ben_nadolski — he held D4 + Council Chair 2020-2023 (a voting member), then WON the mayoralty and was sworn 2024-01-02, so his D4 and MAYOR tenures do NOT overlap (D4 ends 2024-01-02; Mayor begins 2024-01-02). NON-VOTING as Mayor: his cities.db council votes stop 2023-12-19 and he casts ZERO votes as Mayor — the non_voting_mayor flag empties this row's vote bounds (and the tenure-window clamp would independently leave them blank: no council vote falls within the mayoral window; cf. Logan/Anderson, Millcreek/Jackson). Currently serving."),
]

# canonical UPPER-CASE election name -> our person_key (surname sufficient except LOPEZ,
# which is disambiguated by first name below).
NAME_TO_KEY = {
    "HYER": "richard_hyer", "NADOLSKI": "ben_nadolski", "CALDWELL": "mike_caldwell",
    "RICHEY": "ken_richey", "WHITE": "marcia_white", "BLAIR": "bart_blair",
    "CHOBERKA": "angela_choberka", "GRAF": "dave_graf", "MYERS": "shaun_myers",
    "WASHINGTON": "alicia_washington", "LUNDELL": "kevin_lundell",
    "STEPHENS": "doug_stephens",
}

# Shared-surname disambiguation: two Lopez (Luis, At-Large C <=2023; Flor, District 1 2025+)
# are DIFFERENT people. Resolved by first name BEFORE the flat surname lookup.
DISAMBIGUATORS = {
    "LOPEZ": {"LUIS": "luis_lopez", "FLOR": "flor_lopez"},
}

# cities.db person.name_key -> our person_key (Mayor Caldwell intentionally NOT here — he
# never votes on council motions; Nadolski IS here for his 2020-2023 D4 council votes, and
# his MAYOR row is emptied by the non_voting_mayor flag).
DB_KEY = {
    "richardahyer": "richard_hyer", "angelachoberka": "angela_choberka",
    "marcialwhite": "marcia_white", "barteblair": "bart_blair",
    "kenrichey": "ken_richey", "bennadolski": "ben_nadolski",
    "luislopez": "luis_lopez", "davegraf": "dave_graf",
    "shaunmyers": "shaun_myers", "dougstephens": "doug_stephens",
    "aliciawashington": "alicia_washington", "kevinlundell": "kevin_lundell",
    "florlopez": "flor_lopez",
}


def seat_for_contest(office, district):
    """election (office, district) -> seat_id (or None if unmapped)."""
    if office == "Mayor":
        return "MAYOR"
    d = district.strip()
    if d in ("1", "2", "3", "4"):
        return "D" + d
    if d in ("At-Large A", "At-Large 1"):
        return "AL-A"
    if d in ("At-Large B", "At-Large 2"):
        return "AL-B"
    if d in ("At-Large C", "At-Large 3"):
        return "AL-C"
    return None


REDISTRICT = Redistrict(
    plan_old=PLAN_OLD, plan_new=PLAN_NEW, plan_switch=PLAN_SWITCH,
    ord=REDISTRICT_ORD, adopted=REDISTRICT_ADOPTED,
    districts=["District 1", "District 2", "District 3", "District 4"],
    geom_ref=GEOM_REF, source_url=SRC_URL, data_floor=DATA_FLOOR,
    current_note=(f"CURRENT post-2020-census boundaries. {REDISTRICT_ORD} adopted "
                  f"{REDISTRICT_ADOPTED} (contested 6:1 roll call; Choberka dissenting), amending "
                  "Ogden Municipal Code Sec 1-7-2; effective immediately upon posting. Follows the "
                  "county's Dec-2021 precincts; the memo notes the adopted map 'most closely "
                  "resembles the existing boundaries'. geometry_ref = 4 dissolved district polygons "
                  "(Ogden City GIS MUNIWARD)."),
    prior_adopted_by="prior map (pre-2022 redistricting cycle, Ogden Municipal Code Sec 1-7-2)",
    prior_note=("historical boundaries not acquired — the pre-2022 district lines (in force for the "
                "2019/2021 elections) are NOT in geo/. Only the current (plan_2022) MUNIWARD layer is "
                "on disk, and no pre-2022 Ogden precinct SOVC is available, so the old geometry is not "
                "reconstructable from data on disk. effective_start = data floor. Acquisition gap, not "
                "a guess."),
    citywide_rows=[("At-Large", "citywide", "the 3 At-Large council seats (Seats A/B/C)"),
                   ("Citywide", "citywide", "the separately-elected Mayor")],
    citywide_adopted_by="Ogden Municipal Code (at-large seats / mayor — whole city)",
    citywide_note_template=("{who}: represents the ENTIRE city on every date, unchanged by the 2022 "
                            "redistricting. geometry_ref = union of all precinct polygons (city extent)."),
    precinct_hi_source="2025",
    precinct_hi_note=("authoritative Ogden City GIS MUNIWARD assignment (source_year 2025 = the current "
                      "layer). Districts D1/D3 (2025) and D4 (2023) are additionally corroborated by the "
                      "district-winner precinct cross-check (see --check); D2 was unopposed both cycles."),
    precinct_med_note="Ogden City GIS layer only (no additional election corroboration)",
    precinct_prior_note=("prior precinct->district composition not acquired — the pre-2022 lines "
                         "(2019/2021 elections) are not on disk and no pre-2022 Ogden precinct SOVC is "
                         "available. Acquisition gap, not a guess."),
    crosscheck_districts=("1", "2", "3", "4"), precinct_prefix="29OG", geo_seat_prefix="D",
    plan_switch_year="2023", citywide_seats=("AL-A", "AL-B", "AL-C"),
)

CFG = RosterConfig(
    non_voting_mayor=True,
    city=CITY, city_dir=CITY_DIR, repo_root=REPO_ROOT, data_floor=DATA_FLOOR,
    geom_ref=GEOM_REF, elections_path=ELECTIONS, cities_db_path=CITIES_DB,
    overrides_path=OVERRIDES, terms_out=TERMS_OUT, districts_out=DISTRICTS_OUT,
    seat_district=SEAT_DISTRICT, name_to_key=NAME_TO_KEY, db_key=DB_KEY,
    disambiguators=DISAMBIGUATORS,
    seat_order=["D1", "D2", "D3", "D4", "AL-A", "AL-B", "AL-C", "MAYOR"],
    keep_election_row=lambda r: r["election_type"].strip().lower() == "municipal general",
    contest_key=seat_for_contest, crosscheck_field="seat_id",
    winners_have_district=True,
    elected_events=("elected", "reelected", "became-mayor"),
    redistrict=REDISTRICT, precincts_out=PRECINCTS_OUT,
    precinct_map_path=PRECINCT_MAP, precincts_byprecinct_path=PRECINCTS_BYP_SRC,
)


# ---------------------------------------------------------------------------
# Demo queries (Ogden presentation)
# ---------------------------------------------------------------------------
def demo():
    def line(r):
        end = r["end_date"] or "—(serving)"
        return (f"    {r['seat_id']:<6} {r['person_name']:<20} {r['start_date']} -> {end:<12}"
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

    print("\n(c) NON-DEGENERATE address+date -> representatives (via geo/address_to_district.py):")
    addr = "2549 Washington Blvd, Ogden, UT 84401"   # Ogden Municipal Building -> OGD21 -> District 1
    for d in ("2025-06-01", "2022-07-01"):
        res = roster_lib.representatives_for_address(CFG, addr, d, latlon=(41.2230, -111.9706),
                                                     precinct="OGD21")
        who = ", ".join(f"{x['person_name']}({x['seat_id']})" for x in res["reps"])
        loc = (f"District {res['district']} via {res.get('precinct')} "
               f"[{res.get('method')}]") if res.get("district") else f"[{res.get('gap','?')}]"
        print(f"  '{addr}'")
        print(f"    on {d} (plan={res['plan']}): {loc}")
        print(f"    -> your reps: {who}")

    print("\n(d) SAME address across the 2022 REDISTRICTING (versioned district_versions):")
    for d in ("2021-06-01", "2025-06-01"):
        res = roster_lib.representatives_for_address(CFG, addr, d, latlon=(41.2230, -111.9706),
                                                     precinct="OGD21")
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
          f"(4 districts x 2 plans + At-Large + Mayor; redistricting {REDISTRICT_ORD})")
    print(f"Wrote {os.path.relpath(PRECINCTS_OUT, CITY_DIR)} "
          f"(plan_2022 precinct map + plan_2012 gap rows)")
    if "--check" in sys.argv:
        print("\nValidation: PASS (no overlaps; every row has sources+confidence).")
        print("Precinct cross-check:")
        roster_lib.precinct_crosscheck(CFG, verbose=True)
    if "--demo" in sys.argv:
        demo()
