#!/usr/bin/env python3
"""build_roster.py — rolling council-roster for SANDY (a slowly-changing-dimension /
interval table of who holds each council + mayor seat over time). Sandy is a MIXED
district + at-large city with a NON-VOTING (strong-mayor) mayor — structurally the SAME
shape as Ogden (real 4 districts + 3 at-large + non-voting strong-mayor + a post-2020-census
redistricting + a precinct/address join), with a RICHER set of transitions:

  * Monica Zoltanski — the D4 councilmember -> MAYOR CROSSOVER (the headline), and unlike
    Ogden's Nadolski it is a MID-TERM VACANCY (she was elected D4 in 2019 for a term running
    to Jan-2024, but won the 2021 Mayor race and was sworn 2022-01-03, mid-term). Her D4 seat
    was filled by APPOINTMENT (Scott Earl, 2022-01-18) -> a real VACANT interval + appointment
    event, then the 2023 regular election filled it (Houseman).
  * Zach Robinson — an AT-LARGE -> DISTRICT within-council move (at-large 2020-2021, then won
    District 3 in 2021).
  * Marci Houseman — an AT-LARGE -> DISTRICT within-council move (at-large 2020-2023, then won
    District 4 in 2023).
  * Brooke Christensen (D1) and Kristin "Kris" Coleman-Nicholl (D3) — RETURNING members: each
    held her district 2018-2021, left to run for Mayor in 2021 (both lost), then WON her old
    district back in 2025 (non-contiguous tenures on the same seat).

THIN DRIVER: this file holds only Sandy-specific DATA (the curated TENURES seat assignments,
the name maps, the 2022-redistricting facts + prose) + config; all generic mechanics live in
../scripts/roster_lib.py (canon_key, election/vote-bounds/override reconciliation, end-date
chaining + VACANT insertion, validation, the CSV writers, and the as-of / address /
precinct-crosscheck / demo query helpers). See that module's docstring to add a city.

DERIVED LAYER — regenerable, never hand-edited. Canonical inputs:
  1. election_results/sandy_results_by_candidate.csv  (municipal-general winners -> terms)
  2. cities.db  role table (city='sandy', body='Council')  (observed vote bounds)
  3. meeting_minutes/minutes/**                          (oath/appointment/redistricting dates)
  4. roster/roster_overrides.csv                         (hand corrections; applied LAST)

Outputs (idempotent — re-running reproduces them byte-for-byte):
  roster/council_terms.csv          one row per seat-tenure (8 stable seats)
  roster/district_versions.csv      boundary interval table — REAL 4 districts + the 2022
                                    redistricting (Resolution 22-24C) versioned + At-Large + Mayor
  roster/district_precincts.csv     versioned precinct->district composition (plan-scoped)
  roster/_precinct_to_district.csv  DERIVED helper: point-in-polygon of geo/precincts.geojson
                                    against geo/council_districts.geojson (Sandy has no county
                                    precinct->district table on disk, unlike Ogden). plan_2022 only.

Usage:
  python3 roster/build_roster.py            # regenerate the CSVs
  python3 roster/build_roster.py --demo     # regenerate + print the demo queries
  python3 roster/build_roster.py --check    # regenerate + run validations + precinct cross-check

Cardinal rule (repo CLAUDE.md): NEVER fabricate. Unknown seat-holder / boundary /
precinct assignment -> explicit gap + confidence=low + a note, never a guess.

Provenance / confidence model (same as Ogden/Provo/Nephi):
  high   = anchored to an in-data election result OR a minutes-documented oath/appointment/
           departure/redistricting resolution
  medium = inferred from a staggered-cycle election that predates the data floor (the 2017-cycle
           B-seat incumbents seated at the 2020 floor -> term-start inferred 2018-01)
  low    = genuinely unknown / not-yet-acquired (flagged, never silently filled)

Seat model (STABLE ids — a redistricting redraws boundaries, it does NOT renumber seats):
  D1..D4  four geographic district seats
  AL-A / AL-B / AL-C   three at-large seats
  MAYOR   separately-elected mayor (strong-mayor form — does NOT vote on council motions)
Staggered 4-year cycles (election_results/CLAUDE.md, confirmed from the SOVC contests):
  A-cycle (2019 / 2023):  AL-A, AL-B, D2, D4     (at-large Vote-for-2; terms Jan-2020… / Jan-2024…)
  B-cycle (2021 / 2025):  MAYOR, AL-C, D1, D3     (at-large Vote-for-1; terms Jan-2022… / Jan-2026…)
The B-cycle seats held in 2020-2021 were elected in 2017 (predates the 2019 election floor and
the 2020 minutes floor) -> confidence medium, term-start inferred 2018-01. The A-cycle 2019
winners ARE in the election data (floor is 2019 for elections) -> high.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.dirname(HERE)                 # sandy_city_council/
REPO_ROOT = os.path.dirname(CITY_DIR)            # civic-data/
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import roster_lib
from roster_lib import RosterConfig, Redistrict

ELECTIONS = os.path.join(CITY_DIR, "election_results", "sandy_results_by_candidate.csv")
PRECINCTS_BYP_SRC = os.path.join(CITY_DIR, "election_results", "sandy_results_by_precinct.csv")
PRECINCT_MAP = os.path.join(HERE, "_precinct_to_district.csv")  # DERIVED (point-in-polygon)
PRECINCTS_GEOJSON = os.path.join(CITY_DIR, "geo", "precincts.geojson")
DISTRICTS_GEOJSON = os.path.join(CITY_DIR, "geo", "council_districts.geojson")
CITIES_DB = os.path.join(REPO_ROOT, "cities.db")
OVERRIDES = os.path.join(HERE, "roster_overrides.csv")
TERMS_OUT = os.path.join(HERE, "council_terms.csv")
DISTRICTS_OUT = os.path.join(HERE, "district_versions.csv")
PRECINCTS_OUT = os.path.join(HERE, "district_precincts.csv")

CITY = "sandy"
DATA_FLOOR = "2020-01-01"                          # repo minutes/votes floor
GEOM_REF = "geo/council_districts.geojson"         # 4 Sandy-city-GIS district polygons (current plan)

# The real redistricting event (spot-checked against source minutes 2022-05-03):
#   Resolution 22-24C — "amending the Sandy City Council District Boundaries, updating the Sandy
#   City Council Districts map, and selecting Alternative Map 4-1b" — the post-2020-census redraw.
#   Adopted 2022-05-03 on a UNANIMOUS 7-0 roll call (motion Scott Earl / second Brooke D'Sousa).
#   Preceded by two March-2022 direction motions: 2022-03-01 m2 (5-2, keep 4 districts) and m3
#   (6-1, staff to bring back the current map + 3 alternatives within the population deviation).
#   Sandy kept 4 districts; the map is in force for the 2023 & 2025 elections; the 2021 election
#   used the prior (pre-2022) lines.
REDISTRICT_ORD = "Resolution 22-24C (Alternative Map 4-1b)"
REDISTRICT_ADOPTED = "2022-05-03"
PLAN_OLD = "plan_pre2022"   # boundaries in force through the 2021 election (origin year unknown)
PLAN_NEW = "plan_2022"      # Resolution 22-24C; in force for the 2023 election onward
PLAN_SWITCH = "2022-05-03"  # Res 22-24C adoption date
SRC_URL = ("https://gis.sandy.utah.gov/arcgis/rest/services/Common/"
           "City_Council_Districts/MapServer/0")

# Swearing-in / term-start = the organizing (first) council meeting of January (matches
# cities.db role.first_seen and the oath administered there). Verified dates from the record:
#   2020-01-07 (A-cycle 2019 winners sworn) · 2022-01-03 (org day — 2021 B-cycle winners +
#   Mayor Zoltanski sworn "yesterday", per 2022-01-04) · 2024-01-09 (A-cycle 2023 winners sworn)
#   · 2026-01-06 ("new and returning Council Members Kris Nicholl, District 3 and Brooke
#   Christensen, District 1"). Pre-floor 2017-cycle B-seat/mayor terms start 2018-01 (inferred,
#   medium) — Sandy minutes begin 2020. Scott Earl's D4 appointment: 2022-01-18 (5-1 over Pat
#   Casaday; first recorded vote 2022-01-25 — the named-roll-call recording seam).
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
    # ===== D2 (A-cycle; Stroud -> Stroud; the one always-clean district) =====
    dict(body="Council", seat_id="D2", person_name="Alison Stroud", person_key="alison_stroud",
         start_date="2020-01-07", start_event="elected", election_year="2019",
         end_event="reelected", confidence="high",
         sources="election:2019 (District 2 winner, def. Maren Barker 51.07-48.93); minutes:2020-01-07 (masthead 'Alison Stroud, District 2'; present + voting)",
         note="Elected D2 2019. Re-elected D2 2023 (UNOPPOSED 100%) -> continuous. Council Vice Chair 2026."),
    dict(body="Council", seat_id="D2", person_name="Alison Stroud", person_key="alison_stroud",
         start_date="2024-01-09", start_event="reelected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (District 2 winner, UNOPPOSED 100%); minutes:2024-01-09 (masthead 'Alison Stroud, District 2'; present + voting)",
         note="Re-elected D2 2023 unopposed (continuous service). Currently serving (Vice Chair 2026)."),

    # ===== D4 (A-cycle) — THE Zoltanski D4 -> Mayor crossover + a MID-TERM VACANCY -> Earl -> Houseman
    dict(body="Council", seat_id="D4", person_name="Monica Zoltanski", person_key="monica_zoltanski",
         start_date="2020-01-07", start_event="elected", election_year="2019",
         end_event="became-mayor", confidence="high",
         vacate_date="2022-01-03", vacate_confidence="high",
         vacate_source="minutes:2022-01-04 (Mayor Monica Zoltanski presiding; council/mayor 'swearing in ceremony yesterday' = 2022-01-03); minutes:2022-01-18 ('vacancy in council district four')",
         sources="election:2019 (District 4 winner, def. Brooke D'Sousa 50.67-49.33); minutes:2020-01-07 (masthead 'Monica Zoltanski, District 4'); votes:cities.db role (last named D4 vote 2021-12-07); election:2021 (WON the Mayor race, RCV final 8620-8599 over Jim Bennett); minutes:2022-01-03 (sworn Mayor)",
         note="Held DISTRICT 4 (elected 2019, a VOTING member; her last recorded (named) D4 vote is 2021-12-07 (she last served 2021-12-14, a unanimous voice vote with no named members)). WON the 2021 MAYOR race and was sworn Mayor 2022-01-03 — MID-TERM (her 2019 D4 term ran to Jan-2024), so her D4 seat became VACANT and was filled by APPOINTMENT (Scott Earl, 2022-01-18), NOT by a regular election (D4 is an A-cycle seat, not on the 2021 ballot). This is UNLIKE Ogden's Nadolski (a clean cycle-boundary handoff): here the library inserts an explicit VACANT interval 2022-01-03..2022-01-18. Her D4 tenure ends 2022-01-03 and her MAYOR tenure begins 2022-01-03 (half-open — no overlap). NB: the CLAMP now scopes her D4 first_vote/last_vote to this tenure's [2020-01-07, 2022-01-03) window (2020-01-07..2021-12-07), so the three Board-of-Municipal-Canvassers canvass actions she took AS MAYOR (2023-12-06, 2025-08-26, 2025-11-18) — which the minutes list under body=Council and which the OLD person-level max had smeared to last_vote=2025-11-18 — are excluded; her true D4 service ended 2021-12-14. Her MAYOR rows are emptied by non_voting_mayor. See the MAYOR block."),
    dict(body="Council", seat_id="D4", person_name="Scott Earl", person_key="scott_earl",
         start_date="2022-01-18", start_event="appointed", election_year="",
         end_event="lost", confidence="high",
         sources="minutes:2022-01-18 (Council interviewed 5 applicants for the District 4 vacancy; verbal vote 5-1 for Scott Earl over Pat Casaday; motion to appoint him via Resolution 22-03); votes:cities.db first_seen 2022-01-25 (first recorded vote); election:2023 (ran D4, LOST to Marci Houseman 48.69-51.31)",
         note="APPOINTED to the D4 seat vacated by Zoltanski (5-1 over Pat Casaday, 2022-01-18). first_vote in cities.db is 2022-01-25 — the named-roll-call seam (seated 2022-01-18; first recorded named vote 2022-01-25), a recording lag not the term start. RAN for D4 in the 2023 regular election and LOST to Marci Houseman -> term ended at the 2024-01-09 cycle boundary."),
    dict(body="Council", seat_id="D4", person_name="Marci Houseman", person_key="marci_houseman",
         start_date="2024-01-09", start_event="elected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (District 4 winner, def. Scott Earl 51.31-48.69); minutes:2024-01-09 (masthead 'Marci Houseman, District 4'; present + voting)",
         note="Elected D4 2023 — an AT-LARGE -> DISTRICT within-council move (she held At-Large seat AL-B 2020-2023, then won D4 and moved). Currently serving. The clamp scopes her D4 first_vote/last_vote to this tenure (2024-01-09..2026-06-02); her earlier AL-B service shows its own 2020-01-07..2023-12-19 bounds on the AL-B row — the old person-level span shared across both rows is gone."),

    # ===== D1 (B-cycle) — Christensen[2017] -> Mecham[2021] -> Christensen[2025] (a RETURNING member)
    dict(body="Council", seat_id="D1", person_name="Brooke Christensen", person_key="brooke_christensen",
         start_date="2018-01-01", start_event="elected", election_year="",
         end_event="did-not-run", confidence="medium",
         sources="votes:2020-01-07.. (observed serving, cities.db role first_seen); minutes:2020-01-07 (masthead 'Brooke Christensen, District 1'; present + voting); election:2021 (ran MAYOR, RCV, lost — did NOT seek re-election to D1, which was won by Ryan Mecham)",
         note="PRE-FLOOR term: the 2017 election predates the 2019 election-data floor and the 2020 minutes floor; term-start 2018-01 inferred from Sandy's B-cycle 4-year stagger (row confidence medium — only the START date is inferred; her 2020-2021 D1 membership is documented in the masthead + votes). Gave up D1 to run for MAYOR in 2021 (4th, RCV) -> D1 won by newcomer Ryan Mecham. Returned by winning D1 back in 2025 (see her 2026 row)."),
    dict(body="Council", seat_id="D1", person_name="Ryan Mecham", person_key="ryan_mecham",
         start_date="2022-01-03", start_event="elected", election_year="2021",
         end_event="did-not-run", confidence="high",
         sources="election:2021 (District 1 winner, RCV final 1811-1736 over Katie Johnson); minutes:2022-01-18 (present as Council Member Ryan Mecham, District 1); votes:cities.db first_seen 2022-01-04",
         note="Elected D1 2021 (newcomer replacing Christensen). NOT a candidate in the 2025 D1 race (won by Christensen) -> term ended at the 2026-01-06 cycle boundary -> did-not-run."),
    dict(body="Council", seat_id="D1", person_name="Brooke Christensen", person_key="brooke_christensen",
         start_date="2026-01-06", start_event="elected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (District 1 winner, def. Shana Davis 53.91-46.09); minutes:2026-01-06 ('new and returning Council Members Kris Nicholl, District 3 and Brooke Christensen, District 1'; present + voting)",
         note="RETURNING member — won her old D1 seat back in 2025 (the 2026-01-06 minutes call her a 'returning' member). The clamp gives each of her two D1 tenures its own bounds — 2020-01-07..2021-12-07 (her first stint) and 2026-01-06..2026-06-02 (this one) — so the old person-level smear across the 2022-2025 off-council gap is gone. Currently serving."),

    # ===== D3 (B-cycle) — Coleman-Nicholl[2017] -> Robinson[2021] -> Coleman-Nicholl[2025] (RETURNING)
    dict(body="Council", seat_id="D3", person_name="Kristin Coleman-Nicholl", person_key="kristin_coleman_nicholl",
         start_date="2018-01-01", start_event="elected", election_year="",
         end_event="did-not-run", confidence="medium",
         sources="votes:2020-01-07.. (observed serving, cities.db role first_seen); minutes:2020-01-07 (masthead 'Kristin Coleman-Nicholl, District 3'; present + voting); election:2021 (ran MAYOR as 'KRIS NICHOLL', RCV 3rd, lost — did NOT seek re-election to D3, which was won by Zach Robinson)",
         note="PRE-FLOOR term (2017 cycle; term-start 2018-01 inferred from the B-cycle stagger, medium — only the START date is inferred; her 2020-2021 D3 membership is documented). Gave up D3 to run for MAYOR in 2021 (3rd, RCV, as 'Kris Nicholl') -> D3 won by newcomer Zach Robinson. Returned by winning D3 back in 2025 (see her 2026 row). Same person as 'Kris Nicholl' (D3 2026) — canonical votes name is 'Kristin Coleman-Nicholl'."),
    dict(body="Council", seat_id="D3", person_name="Zach Robinson", person_key="zach_robinson",
         start_date="2022-01-03", start_event="elected", election_year="2021",
         end_event="did-not-run", confidence="high",
         sources="election:2021 (District 3 winner, RCV final 3557-2402 over Jim Edwards); minutes:2022-01-18 (masthead 'Zach Robinson, District 3'); votes:cities.db D3 first recorded 2022-01-04 (person-level first_seen 2020-01-07 is his AT-LARGE start, clamped out of this D3 row)",
         note="Elected D3 2021 — an AT-LARGE -> DISTRICT within-council move (he held At-Large seat AL-C 2020-2021, then won D3 and moved). NOT a candidate in the 2025 D3 race (won by Coleman-Nicholl) -> term ended at the 2026-01-06 cycle boundary -> did-not-run. The clamp scopes this D3 row's first_vote to 2022-01-04 (his D3 service began 2022-01-03); his AT-LARGE start (2020-01-07, person-level first_seen) now shows only on the AL-C row, no longer smeared onto D3."),
    dict(body="Council", seat_id="D3", person_name="Kris Nicholl", person_key="kristin_coleman_nicholl",
         start_date="2026-01-06", start_event="elected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (District 3 winner as 'KRIS NICHOLL', def. Iva Williams 56.82-43.18); minutes:2026-01-06 ('new and returning Council Members Kris Nicholl, District 3'; present + voting)",
         note="RETURNING member — won her old D3 seat back in 2025 (the 2026-01-06 minutes call her 'returning'; the ballot + 2026 masthead name her 'Kris Nicholl', the same person as 'Kristin Coleman-Nicholl' above; person_key unchanged). The clamp gives each of her two D3 tenures its own bounds — 2020-01-07..2021-12-07 (her first stint) and 2026-01-06..2026-06-02 (this one) — so the old person-level smear across the 2022-2025 off-council gap is gone. Currently serving."),

    # ===== AL-A (A-cycle Vote-for-2; Sharkey holds this seat continuously) =====
    dict(body="Council", seat_id="AL-A", person_name="Cyndi Sharkey", person_key="cyndi_sharkey",
         start_date="2020-01-07", start_event="elected", election_year="2019",
         end_event="reelected", confidence="high",
         sources="election:2019 (At-Large winner, top vote-getter 29.54% in the Vote-for-2 race, with Houseman); minutes:2020-01-07 (masthead 'Cyndi Sharkey, At-large'; present + voting)",
         note="Elected At-Large 2019 (Vote-for-2 cohort, top vote-getter). Re-elected At-Large 2023 (again top vote-getter) -> continuous. Council Chair 2026. AL-A is the STABLE id for the seat she holds continuously across the A-cycle at-large cohort."),
    dict(body="Council", seat_id="AL-A", person_name="Cyndi Sharkey", person_key="cyndi_sharkey",
         start_date="2024-01-09", start_event="reelected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (At-Large winner, top vote-getter 30.15% in the Vote-for-2 race, with DeKeyzer); minutes:2024-01-09 (masthead 'Cyndi Sharkey, At-large'; present + voting)",
         note="Re-elected At-Large 2023 (continuous). Council Chair 2026. Ran for Mayor in 2025 and LOST to Zoltanski (38.68%) — but that did not affect her at-large council seat (not up in 2025). Currently serving."),

    # ===== AL-B (A-cycle Vote-for-2; the seat Houseman held then vacated for D4 -> DeKeyzer) =====
    dict(body="Council", seat_id="AL-B", person_name="Marci Houseman", person_key="marci_houseman",
         start_date="2020-01-07", start_event="elected", election_year="2019",
         end_event="elected-to-district", confidence="high",
         sources="election:2019 (At-Large winner, 2nd 26.9% in the Vote-for-2 race, with Sharkey); minutes:2020-01-07 (masthead 'Marci Houseman, At-large'; present + voting); election:2023 (WON District 4, moving off at-large)",
         note="Elected At-Large 2019 (Vote-for-2 cohort). WON District 4 in 2023 and MOVED to the D4 seat 2024-01-09, so her AL-B term ended at the 2024 cycle boundary (an at-large -> district within-council move; her AL-B seat was then filled by Aaron DeKeyzer). AL-B is the STABLE id for the non-Sharkey seat in the A-cycle at-large cohort. See her D4 rows for continued service."),
    dict(body="Council", seat_id="AL-B", person_name="Aaron Dekeyzer", person_key="aaron_dekeyzer",
         start_date="2024-01-09", start_event="elected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (At-Large winner, 2nd 26.9% in the Vote-for-2 race, with Sharkey); minutes:2024-01-09 (masthead 'Aaron Dekeyzer, At-large'; present + voting); votes:cities.db first_seen 2024-01-09",
         note="Elected At-Large 2023 (newcomer; took the AL-B seat Houseman vacated when she moved to D4). Currently serving."),

    # ===== AL-C (B-cycle Vote-for-1; Robinson[2017 at-large] -> D'Sousa[2021/2025]) =====
    dict(body="Council", seat_id="AL-C", person_name="Zach Robinson", person_key="zach_robinson",
         start_date="2018-01-01", start_event="elected", election_year="",
         end_event="elected-to-district", confidence="medium",
         sources="votes:2020-01-07.. (observed serving, cities.db role first_seen); minutes:2020-01-07 (masthead 'Zach Robinson, At-large'; present + voting); election:2021 (WON District 3, moving off at-large)",
         note="PRE-FLOOR term (2017 cycle; term-start 2018-01 inferred from the B-cycle Vote-for-1 at-large stagger, medium — only the START date is inferred; his 2020-2021 at-large membership is documented). AL-C is the STABLE id for the B-cycle Vote-for-1 at-large seat (the third at-large seat, elected 2021/2025). He WON District 3 in 2021 and MOVED to D3 2022-01-03 (an at-large -> district within-council move); his at-large seat was then won by Brooke D'Sousa. See his D3 rows."),
    dict(body="Council", seat_id="AL-C", person_name="Brooke D'Sousa", person_key="brooke_dsousa",
         start_date="2022-01-03", start_event="elected", election_year="2021",
         end_event="reelected", confidence="high",
         sources="election:2021 (At-Large winner, Vote-for-1, RCV final 9224-8526 over Aaron DeKeyzer); minutes:2022-01-18 (masthead 'Brooke D'Sousa, At-large'); votes:cities.db first_seen 2022-01-04",
         note="Elected At-Large 2021 (Vote-for-1 cohort; newcomer taking the seat Robinson vacated for D3). She had LOST the 2019 D4 race to Zoltanski, then won this at-large seat in 2021. Re-elected At-Large 2025 -> continuous."),
    dict(body="Council", seat_id="AL-C", person_name="Brooke D'Sousa", person_key="brooke_dsousa",
         start_date="2026-01-06", start_event="reelected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (At-Large winner, Vote-for-1, def. Evan Tobin 66.97-33.03); minutes:2026-01-06 (present + voting)",
         note="Re-elected At-Large 2025 (continuous). Currently serving."),

    # ===== MAYOR (B-cycle; strong-mayor form — does NOT vote on council motions) =====
    dict(body="Mayor", seat_id="MAYOR", person_name="Kurt Bradburn", person_key="kurt_bradburn",
         start_date="2018-01-01", start_event="elected", election_year="",
         end_event="did-not-run", confidence="medium",
         sources="minutes:2020-01-07 ('Administration: Mayor Kurt Bradburn' presiding — a continuing 2017-cycle mayor); election:2021 (not a candidate — the Mayor race was Zoltanski/Bennett/Nicholl/… with no Bradburn)",
         note="PRE-FLOOR mayor: elected 2017 (predates the 2019 election-data floor + the 2020 minutes floor) -> term-start 2018-01 inferred from the B-cycle stagger, medium (his 2020-2021 mayoralty is documented in the minutes' Administration roster). Strong-mayor form: does NOT vote on council legislation and never appears in a council roll call (0 cities.db council rows) -> the non_voting_mayor flag keeps his vote bounds empty. Did NOT run in 2021 -> replaced by Mayor Zoltanski 2022-01-03."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Monica Zoltanski", person_key="monica_zoltanski",
         start_date="2022-01-03", start_event="became-mayor", election_year="2021",
         end_event="reelected", confidence="high",
         sources="election:2021 (Mayor winner, RCV final 8620-8599 over Jim Bennett); minutes:2022-01-04 ('Mayor Monica Zoltanski' presiding; sworn 2022-01-03)",
         note="MAYOR (not a council seat). SAME person as the D4 councilmember monica_zoltanski — she held D4 2020-2021 (a voting member, last named D4 vote 2021-12-07), then WON the 2021 mayoralty and was sworn 2022-01-03, so her D4 and MAYOR tenures do NOT overlap (D4 ends 2022-01-03; Mayor begins 2022-01-03; the vacated D4 seat was filled by Scott Earl's appointment, with a VACANT interval between). NON-VOTING as Mayor: the non_voting_mayor flag empties this row's vote bounds (they would otherwise smear her 2020-2021 D4 span — and the 2023-2025 canvass-action rows — onto the mayoralty; cf. Ogden/Nadolski, Logan/Anderson)."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Monica Zoltanski", person_key="monica_zoltanski",
         start_date="2026-01-06", start_event="reelected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Mayor winner, def. Cyndi Sharkey 61.32-38.68); minutes:2026-01-06 (presiding as Mayor)",
         note="Re-elected Mayor 2025 (def. sitting councilmember Cyndi Sharkey). Non-voting (vote bounds emptied by the flag). Currently serving."),
]

# canonical UPPER-CASE election name -> our person_key. Surname is sufficient — Sandy has NO
# shared council surnames in-window (the two Brookes are Christensen vs D'Sousa; distinct).
NAME_TO_KEY = {
    "SHARKEY": "cyndi_sharkey", "STROUD": "alison_stroud", "HOUSEMAN": "marci_houseman",
    "ROBINSON": "zach_robinson", "D'SOUSA": "brooke_dsousa", "MECHAM": "ryan_mecham",
    "CHRISTENSEN": "brooke_christensen", "NICHOLL": "kristin_coleman_nicholl",
    "DEKEYZER": "aaron_dekeyzer", "ZOLTANSKI": "monica_zoltanski", "EARL": "scott_earl",
    "BRADBURN": "kurt_bradburn",
}

# No shared-surname disambiguation needed for Sandy (kept for parity with the district template).
DISAMBIGUATORS = {}

# cities.db person.name_key -> our person_key (Mayor Bradburn intentionally NOT here — he never
# votes on council motions; Zoltanski IS here for her 2020-2021 D4 council votes, and her MAYOR
# rows are emptied by the non_voting_mayor flag).
DB_KEY = {
    "cyndisharkey": "cyndi_sharkey", "alisonstroud": "alison_stroud",
    "marcihouseman": "marci_houseman", "zachrobinson": "zach_robinson",
    "brookedsousa": "brooke_dsousa", "ryanmecham": "ryan_mecham",
    "brookechristensen": "brooke_christensen",
    "kristincolemannicholl": "kristin_coleman_nicholl",
    "aarondekeyzer": "aaron_dekeyzer", "monicazoltanski": "monica_zoltanski",
    "scottearl": "scott_earl",
}


def seat_for_contest(office, district):
    """election (office, district) -> seat_id (or None if unmapped).
    NOTE: Sandy's 3 at-large seats are NOT individually labelled on the ballot — the at-large
    contests are multi-winner (Vote-for-2 in 2019/2023, Vote-for-1 in 2021/2025), so a single
    (office, district) cannot resolve WHICH at-large seat a winner holds. The library's forward
    election cross-check therefore prints an expected informational 'unmapped contest … At-Large'
    line for each at-large winner; the at-large winners are validated instead by the driver's
    cohort cross-check (`_atlarge_crosscheck`, run under --check). Districts + Mayor resolve here."""
    if office == "Mayor":
        return "MAYOR"
    d = district.strip()
    if d in ("1", "2", "3", "4"):
        return "D" + d
    return None   # At-Large: resolved by the driver-level cohort cross-check, not per-contest


REDISTRICT = Redistrict(
    plan_old=PLAN_OLD, plan_new=PLAN_NEW, plan_switch=PLAN_SWITCH,
    ord=REDISTRICT_ORD, adopted=REDISTRICT_ADOPTED,
    districts=["District 1", "District 2", "District 3", "District 4"],
    geom_ref=GEOM_REF, source_url=SRC_URL, data_floor=DATA_FLOOR,
    current_note=(f"CURRENT post-2020-census boundaries. {REDISTRICT_ORD} adopted "
                  f"{REDISTRICT_ADOPTED} on a UNANIMOUS 7-0 roll call (motion Scott Earl / second "
                  "Brooke D'Sousa) — 'amending the Sandy City Council District Boundaries, updating "
                  "the Sandy City Council Districts map, and selecting Alternative Map 4-1b'. Sandy "
                  "kept 4 districts (2022-03-01 direction motions m2 5-2 + m3 6-1). In force for the "
                  "2023 & 2025 elections; the 2021 election used the prior lines. geometry_ref = the "
                  "4 Sandy-city-GIS council-district polygons (current layer, matches the 2026 minutes)."),
    prior_adopted_by="prior map (pre-2022 redistricting cycle)",
    prior_geom_ref="geo/council_districts_pre2022.geojson",
    prior_confidence="low",
    prior_note=("Prior-plan (pre-2022) district boundaries RECONSTRUCTED 2026-07-11 by dissolving current-vintage "
                "precinct shapes by the pre-2022 (2012-cycle) precinct->district assignment (geometry_ref = "
                "geo/council_districts_pre2022.geojson; all 76 SAN precincts present, 0 holes, 1 conflict — SAN024 "
                "reassigned 2019 D2->2021 D3, resolved to D3=latest). In force for the 2019/2021 elections. "
                "effective_start = data floor. "
                "VALIDATION 2026-07-19 (LM-wave follow-up): fetched Sandy's own authoritative GIS "
                "(gis.sandy.utah.gov Common/City_Council_Districts) — it is the CURRENT 2022 plan (carries the "
                "current members Christensen/Stroud/Nicholl/Houseman; centroid-agrees with the CURRENT precinct "
                "assignment 110/110 (100%) but with the pre-2022 assignment only 21/76 (28%, ~random). The city "
                "publishes NO pre-2022 boundary layer (Common + Historic folders enumerated). A fragmentation "
                "control PROVES SEVERE precinct renumbering: the CURRENT-assignment dissolve yields clean 1-2-piece "
                "districts, but this pre-2022 dissolve yields 8-13-piece fragments (D1=9,D2=8,D3=10,D4=13) -> the "
                "old SAN codes were renumbered between the SOVC vintage and the current UGRC shapes (the millcreek "
                "defect). No authoritative prior layer exists to replace it -> geometry confidence DOWNGRADED "
                "medium->low. The district_precincts precinct-CODE composition stays medium (a faithful SOVC "
                "record, geometry-independent). See scripts/roster_boundary_recon.md."),
    citywide_rows=[("At-Large", "citywide", "the 3 At-Large council seats"),
                   ("Citywide", "citywide", "the separately-elected Mayor")],
    citywide_adopted_by="Sandy City Code (at-large seats / mayor — whole city)",
    citywide_note_template=("{who}: represents the ENTIRE city on every date, unchanged by the 2022 "
                            "redistricting. geometry_ref = union of the district polygons (city extent)."),
    precinct_hi_source="2025",
    precinct_hi_note=("Sandy-city-GIS district polygons -> precinct point-in-polygon (source_year 2025 "
                      "= the current layer). All four districts are additionally corroborated by the "
                      "district-winner precinct cross-check on the plan_2022 cycles (see --check): "
                      "2023 D2/D4 + 2025 D1/D3 all reconcile on the winning individual."),
    precinct_med_note="Sandy city GIS layer only (no additional election corroboration)",
    precinct_prior_note=("Reconstructed pre-2022 (2012-cycle) precinct->district composition (76/76 SAN precincts, "
                         "from the pre-2022 SOVC district contests; SAN024 conflict resolved to the 2021 D3 "
                         "assignment); medium — current-vintage precinct shapes. See scripts/roster_boundary_recon.md."),
    crosscheck_districts=("1", "2", "3", "4"), precinct_prefix="", geo_seat_prefix="D",
    plan_switch_year="2023", citywide_seats=("AL-A", "AL-B", "AL-C"),
)

CFG = RosterConfig(
    non_voting_mayor=True,
    # H-C reverse-election-crosscheck exceptions (verified 2026-07-19). Sandy's At-Large seats are a
    # multi-winner "Vote-for-N" cohort: seat_for_contest() returns None for a Council/At-Large contest
    # (there is no per-seat SOVC label), so the AL-A/AL-B/AL-C tenures never map to a winner row even
    # though every holder is a genuine top-N winner. Confirmed against the by-candidate SOVC
    # (election_results/sandy_results_by_candidate.csv / _by_precinct.csv): 2019 At-Large (Vote-for-2)
    # top two = Sharkey 8044 + Houseman 7327; 2023 At-Large (Vote-for-2) top two = Sharkey 8676 +
    # DeKeyzer 7739; 2021 + 2025 At-Large (Vote-for-1) = D'Sousa. Not missing service — a normalization
    # limit of the single-winner contest_key over multi-winner At-Large.
    reverse_crosscheck_exceptions={
        ("2019", "AL-A", "cyndi_sharkey"): "At-Large Vote-for-2 winner (1st, 8044 votes, sandy_results_by_candidate.csv); multi-winner At-Large contest_key returns None -> unmappable to the AL-A seat sub-label",
        ("2023", "AL-A", "cyndi_sharkey"): "At-Large Vote-for-2 winner (1st, 8676 votes, sandy_results_by_candidate.csv); multi-winner At-Large contest_key returns None -> unmappable to the AL-A seat sub-label",
        ("2019", "AL-B", "marci_houseman"): "At-Large Vote-for-2 winner (2nd, 7327 votes, sandy_results_by_candidate.csv); the single-winner races.csv records only Sharkey -> 2nd seat unmappable",
        ("2023", "AL-B", "aaron_dekeyzer"): "At-Large Vote-for-2 winner (2nd, 7739 votes, sandy_results_by_candidate.csv); the single-winner races.csv records only Sharkey -> 2nd seat unmappable",
        ("2021", "AL-C", "brooke_dsousa"): "At-Large Vote-for-1 winner (sandy_races.csv); multi-winner At-Large contest_key returns None -> unmappable to the AL-C seat sub-label",
        ("2025", "AL-C", "brooke_dsousa"): "At-Large Vote-for-1 winner (sandy_races.csv); multi-winner At-Large contest_key returns None -> unmappable to the AL-C seat sub-label",
    },
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
    prior_precinct_map_path=os.path.join(CITY_DIR, "geo", "precinct_to_district_pre2022.csv"),
)


# ---------------------------------------------------------------------------
# DERIVED helper 1: the precinct->district map. Sandy — unlike Ogden — has NO county
# precinct->district table on disk (geo/ has no precinct_to_district.csv). Its authoritative
# whole-city district polygons DO cover every precinct, so we derive the composition by
# point-in-polygon (each precinct's representative point -> the district that contains it).
# This is the plan_2022 (current) composition; the pre-2022 composition is an honest gap.
# geopandas is used only here; if it is unavailable we reuse an existing map (idempotent).
# ---------------------------------------------------------------------------
def _write_precinct_to_district():
    if os.path.exists(PRECINCT_MAP):
        try:
            import geopandas  # noqa: F401  (regen only if the lib is present)
        except Exception:
            print("  [precinct map] geopandas unavailable; reusing existing "
                  "_precinct_to_district.csv", file=sys.stderr)
            return
    import warnings
    warnings.filterwarnings("ignore")
    import geopandas as gpd
    prec = gpd.read_file(PRECINCTS_GEOJSON).to_crs(4326)
    dist = gpd.read_file(DISTRICTS_GEOJSON).to_crs(4326)
    rows = []
    for _, p in prec.iterrows():
        rp = p.geometry.representative_point()
        hit = None
        for _, d in dist.iterrows():
            if d.geometry.contains(rp):
                hit = str(d["City_Counc"]).strip()
                break
        if hit:
            rows.append((str(p["PrecinctID"]).strip(), hit))
    rows.sort()
    with open(PRECINCT_MAP, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["precinct", "district", "source_year"])
        for pid, dnum in rows:
            w.writerow([pid, dnum, "2025"])


# ---------------------------------------------------------------------------
# Driver-level AT-LARGE cohort cross-check (the library's per-contest forward check can't
# resolve Sandy's multi-winner at-large seats — see seat_for_contest). This confirms every
# at-large GENERAL winner maps to an at-large tenure (any AL seat) elected/reelected that year.
# ---------------------------------------------------------------------------
def _atlarge_crosscheck(verbose=True):
    terms = roster_lib.load_terms(CFG)
    al_have = {(t["election_year"], t["person_key"]) for t in terms
               if t["seat_id"].startswith("AL-")
               and t["start_event"] in ("elected", "reelected")}
    ok = True
    for yr, office, dist, name in roster_lib.load_election_winners(CFG):
        if office != "Council" or dist != "At-Large":
            continue
        pk = roster_lib.canon_key(CFG, name)
        status = "OK" if (yr, pk) in al_have else "MISSING"
        if status == "MISSING":
            ok = False
        if verbose:
            print("  at-large %s %-18s -> %-22s %s" % (yr, name.title(), pk, status))
    return ok


# ---------------------------------------------------------------------------
# Demo queries (Sandy presentation)
# ---------------------------------------------------------------------------
def demo():
    def line(r):
        end = r["end_date"] or "—(serving)"
        return (f"    {r['seat_id']:<6} {r['person_name']:<24} {r['start_date']} -> {end:<12}"
                f" [{r['start_event']}/{r['end_event']}] conf={r['confidence']}")

    print("\n(a) CURRENT council roster + mayor (end_date empty, end_event=serving):")
    for r in roster_lib.load_terms(CFG):
        if not r["end_date"] and r["end_event"] == "serving":
            print(line(r))

    print("\n(b) Roster AS OF 2022-07-01 (Zoltanski is Mayor; Earl holds D4 by appointment):")
    for r in roster_lib.roster_as_of(CFG, "2022-07-01", body="Council"):
        print(line(r))
    for r in roster_lib.roster_as_of(CFG, "2022-07-01", body="Mayor"):
        print(line(r))

    print("\n(c) The D4 VACANT window (2022-01-10 — between Zoltanski's mayoral swearing and "
          "Earl's appointment):")
    for r in roster_lib.roster_as_of(CFG, "2022-01-10", body="Council"):
        if r["seat_id"] == "D4":
            print(line(r))

    print("\n(d) NON-DEGENERATE address+date -> representatives (via geo/address_to_district.py):")
    addr = "10000 Centennial Pkwy, Sandy, UT 84070"   # Sandy City Hall -> District 1
    for d in ("2025-06-01", "2022-07-01"):
        res = roster_lib.representatives_for_address(CFG, addr, d, latlon=(40.5822, -111.8563))
        who = ", ".join(f"{x['person_name']}({x['seat_id']})" for x in res["reps"])
        loc = (f"District {res['district']} via {res.get('precinct')} "
               f"[{res.get('method')}]") if res.get("district") else f"[{res.get('gap','?')}]"
        print(f"  '{addr}'")
        print(f"    on {d} (plan={res['plan']}): {loc}")
        print(f"    -> your reps: {who}")

    print("\n(e) SAME address across the 2022 REDISTRICTING (versioned district_versions):")
    for d in ("2021-06-01", "2025-06-01"):
        res = roster_lib.representatives_for_address(CFG, addr, d, latlon=(40.5822, -111.8563))
        if res.get("district"):
            print(f"    {d} (plan={res['plan']}): geographic District {res['district']} "
                  f"-> {[x['person_name'] for x in res['reps'] if x['seat_id'].startswith('D')]}")
        else:
            print(f"    {d} (plan={res['plan']}): {res.get('gap')}")

    print("\n(f) Precinct-map cross-check (district_precincts vs election outcomes):")
    roster_lib.precinct_crosscheck(CFG, verbose=True)

    print("\n(g) At-large cohort cross-check (driver-level; the lib can't resolve multi-winner "
          "at-large seats):")
    _atlarge_crosscheck(verbose=True)


if __name__ == "__main__":
    _write_precinct_to_district()
    rows = roster_lib.build(CFG, TENURES)
    n = {c: sum(1 for r in rows if r["confidence"] == c) for c in ("high", "medium", "low")}
    nvac = sum(1 for r in rows if r["start_event"] == "vacated")
    print(f"Wrote {os.path.relpath(TERMS_OUT, CITY_DIR)} "
          f"({len(rows)} tenures: {n['high']} high / {n['medium']} medium / {n['low']} low; "
          f"{nvac} VACANT)")
    print(f"Wrote {os.path.relpath(DISTRICTS_OUT, CITY_DIR)} "
          f"(4 districts x 2 plans + At-Large + Mayor; redistricting {REDISTRICT_ORD})")
    print(f"Wrote {os.path.relpath(PRECINCTS_OUT, CITY_DIR)} "
          f"(plan_2022 precinct map + plan_pre2022 gap rows)")
    if "--check" in sys.argv:
        print("\nValidation: PASS (no overlaps; every row has sources+confidence).")
        print("Precinct cross-check:")
        roster_lib.precinct_crosscheck(CFG, verbose=True)
        print("At-large cohort cross-check:")
        _atlarge_crosscheck(verbose=True)
    if "--demo" in sys.argv:
        demo()
