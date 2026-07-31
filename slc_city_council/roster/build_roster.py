#!/usr/bin/env python3
"""build_roster.py — rolling council-roster for SALT LAKE CITY (a slowly-changing-
dimension / interval table of who holds each council + mayor seat over time). SLC is
the largest, most complex city in the repo: **7 geographic council districts** (D1..D7,
NO at-large/citywide council seats) + a **separately-elected Mayor** who does NOT vote on
council motions; council votes are **2021+ only** (LLM-extracted), but the county election
record runs **2007+** (the repo's longest); the 7 districts were **redrawn after the 2020
Census** (Resolution 9 of 2022).

THIN DRIVER: this file holds only SLC-specific DATA (the curated TENURES, the name maps,
the 2022-redistricting facts + prose) + config; all generic mechanics live in
../scripts/roster_lib.py (canon_key, election/vote-bounds/override reconciliation, end-date
chaining + VACANT insertion, validation incl. the gap/vacate guards, the CSV writers, and
the as-of / address / precinct-crosscheck query helpers). See that module's docstring to
add a city; the DISTRICT reference is provo_city_council/roster/build_roster.py.

DERIVED LAYER — regenerable, never hand-edited. Canonical inputs:
  1. election_results/slc_results_by_candidate.csv  (winners -> `elected`/`reelected` terms; 2007+)
  2. cities.db  role table (city='slc', body='Council')  (observed vote bounds, 2021+)
  3. meeting_minutes/minutes/**  (oath/appointment/resignation dates, the redistricting resolution)
  4. roster/roster_overrides.csv  (hand corrections; applied LAST, win ties)

Outputs (idempotent — re-running reproduces them byte-for-byte):
  roster/council_terms.csv       one row per seat-tenure (7 district seats + MAYOR)
  roster/district_versions.csv   boundary interval table — REAL 7 districts x 2 plans + Mayor
  roster/district_precincts.csv  versioned precinct->district composition (plan-scoped)

Usage:
  python3 roster/build_roster.py            # regenerate the CSVs
  python3 roster/build_roster.py --demo     # regenerate + print the demo queries
  python3 roster/build_roster.py --check    # regenerate + validations + precinct cross-check

Cardinal rule (repo CLAUDE.md): NEVER fabricate. Unknown seat-holder / boundary / date ->
explicit VACANT/gap + confidence + a note, never a guess.

Provenance / confidence model:
  high   = anchored to an election result (2007+ county file) confirmed by minutes/votes,
           OR a minutes-documented oath / appointment / resignation / the redistricting resolution
  medium = an election-anchored term that PREDATES the 2021 vote-data floor (no vote
           corroboration — flagged), a gap-bounded (last-vote..appointment) vacancy/departure,
           or a pre-2020-minutes-floor date inferred from the election chain
  low    = genuinely unknown / not-yet-acquired (flagged, never silently filled) — here only
           in the prior-plan district/precinct GAP rows

SLC seat model (STABLE ids — a redistricting redraws boundaries, it does NOT renumber seats):
  D1..D7  seven geographic district seats     MAYOR  separately-elected mayor (does NOT vote)
Staggered 4-year cycles (odd calendar years):
  ODD  districts 1,3,5,7  elected 2009/13/17/21/25  -> terms seated Jan 2010/14/18/22/26
  EVEN districts 2,4,6    elected 2007/11/15/19/23  -> terms seated Jan 2008/12/16/20/24
  MAYOR                   elected 2007/11/15/19/23  -> terms seated Jan 2008/12/16/20/24

FORMER SOURCE DEFECTS — FIXED at the elections layer 2026-07-19 (backups:
_backups/2026-07-19-slc-elections-fix/; details in election_results/CLAUDE.md):
  * 2019 general SOVC was a stale, garbled slice (ballot-METHOD sub-headers parsed as the
    candidates — "Vote By Mail" winner rows). Re-synced from the archive's family-B re-parse:
    the real 2019 winners (Johnston D2, Valdemoros D4, Dugan D6, Mendenhall Mayor) are now in
    the election file, verified against the raw workbook's own Total: rows. The affected
    tenures keep their minutes/vote anchoring and confidence UNCHANGED (terms byte-identical).
  * 2021 general (the RCV pilot year): privacy-suppressed precincts' votes were dropped
    (method rows print '****' but each precinct's Total row IS printed — the normalizer now
    recovers them). The old D2 "Puy-not-Palmer swap" (Palmer 363 / Puy 361) was a
    partial-count artifact: the certified first-choice totals are PUY 1084 / PALMER 751 —
    Puy is the plurality leader AND the seated member (2022-01-04+). Puy's tenure note was
    written against the defective 363/361 numbers; it has now been REFRESHED to the corrected
    tallies (2026-07-19) — only the note/text field changed, the interval/person/seat/
    confidence are byte-identical. Read election_results/ for the canonical tallies.
  Both directions of the election cross-check now reconcile with NO exceptions.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.dirname(HERE)                 # slc_city_council/
REPO_ROOT = os.path.dirname(CITY_DIR)            # civic-data/
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import roster_lib
from roster_lib import RosterConfig, Redistrict

ELECTIONS = os.path.join(CITY_DIR, "election_results", "slc_results_by_candidate.csv")
PRECINCTS_BYP = os.path.join(CITY_DIR, "election_results", "slc_results_by_precinct.csv")
PRECINCT_MAP = os.path.join(CITY_DIR, "geo", "precinct_to_district.csv")
CITIES_DB = os.path.join(REPO_ROOT, "cities.db")
OVERRIDES = os.path.join(HERE, "roster_overrides.csv")
TERMS_OUT = os.path.join(HERE, "council_terms.csv")
DISTRICTS_OUT = os.path.join(HERE, "district_versions.csv")
PRECINCTS_OUT = os.path.join(HERE, "district_precincts.csv")

CITY = "slc"
DATA_FLOOR = "2020-01-01"            # minutes floor (2020 Laserfiche OCR; PrimeGov 2021+)
GEOM_REF = "geo/slco_precincts_current.geojson"

# The real redistricting event (spot-checked against source minutes 2022-05-17):
#   Resolution 9 of 2022, "Redistricting City Council District Boundaries", designating the
#   seven district boundaries from the 2020 Census results (Exhibit A). Originally adopted at
#   the 2022-05-10 limited formal meeting; RECONSIDERED and re-adopted 7-0 on 2022-05-17 to
#   correct a single property inadvertently placed in District Six (moved to District Three).
#   First used for the 2023 (even D2/D4/D6) and 2025 (odd D1/D3/D5/D7) elections.
REDISTRICT_ORD = "Resolution 9 of 2022"
REDISTRICT_ADOPTED = "2022-05-17"
PLAN_OLD = "plan_2012"     # post-2010-census boundaries, in force through the 2021 elections
PLAN_NEW = "plan_2022"     # Resolution 9 of 2022; in force for the 2023 election onward
PLAN_SWITCH = "2022-05-17"  # documented legal designation of the new boundaries
SRC_URL = ("https://slc.primegov.com/meeting/attachment/20796.pdf"
           "?name=Exhibit A Redistricting Reconsideration Map for May 17")

SEAT_DISTRICT = {
    "D1": "District 1", "D2": "District 2", "D3": "District 3", "D4": "District 4",
    "D5": "District 5", "D6": "District 6", "D7": "District 7", "MAYOR": "Citywide",
}

# ---------------------------------------------------------------------------
# LAYER 1-3 (reconciled). Each tenure anchored to a cited source. Ordered by seat.
#   Documented Jan swearing-in / first-meeting dates (cities.db role.first_seen):
#     2020-01-07 · 2022-01-04 · 2024-01-09 · 2026-01-13. Pre-2020-floor term-starts use
#     YYYY-01-01 (inferred from the staggered cycle, flagged medium — same as Provo).
# ---------------------------------------------------------------------------
TENURES = [
    # ============================ D1 (odd cycle) ============================
    dict(body="Council", seat_id="D1", person_name="Carlton Christensen", person_key="carlton_christensen",
         start_date="2010-01-01", start_event="elected", election_year="2009", end_event="did-not-run",
         confidence="medium",
         sources="election:2009 (District 1 winner, def. Reynolds-Benns 66-33)",
         note="PRE-VOTE-FLOOR (elected 2009; council votes only exist 2021+). Term-start inferred Jan 2010 from the odd-district stagger; continuous service inferred from the election chain (not verifiable below the 2020 minutes floor). Not the 2013 D1 candidate -> Rogers won."),
    dict(body="Council", seat_id="D1", person_name="James Rogers", person_key="james_rogers",
         start_date="2014-01-01", start_event="elected", election_year="2013", end_event="reelected",
         confidence="medium",
         sources="election:2013 (District 1 winner, def. Parke 51.8-48.2)",
         note="PRE-VOTE-FLOOR term (elected 2013). Re-elected 2017."),
    dict(body="Council", seat_id="D1", person_name="James Rogers", person_key="james_rogers",
         start_date="2018-01-01", start_event="reelected", election_year="2017", end_event="resigned",
         confidence="medium", vacate_date="2021-09-21", vacate_confidence="medium",
         vacate_source="votes:last recorded council vote 2021-09-21 (cities.db); minutes:2021-11-09 ('interview applicants for the vacant Council District One seat')",
         sources="election:2017 (District 1 winner, UNOPPOSED 100%); votes:2021-01-05..2021-09-21 (cities.db, D1)",
         note="Elected 2017 (term start inferred Jan 2018, pre-floor). RESIGNED mid-term in autumn 2021: last recorded vote 2021-09-21; by 2021-11-09 the Council was interviewing applicants for 'the vacant Council District One seat'. Exact resignation-effective date not pinned to a single quote -> vacate_confidence=medium (row capped to medium per the gap-bounded-departure invariant)."),
    dict(body="Council", seat_id="D1", person_name="Victoria Petro", person_key="victoria_petro",
         start_date="2021-11-16", start_event="elected", election_year="2021", end_event="reelected",
         confidence="high",
         sources="election:2021 (District 1 winner, def. Perez 45.1-43.0); minutes:2021-11-09 (Petro-Eschler seated as Councilmember, thanking voters); votes:first D1 vote 2021-11-16 (cities.db)",
         note="Won the Nov-2021 D1 general and was SEATED EARLY (2021-11-16) to fill the remainder of Rogers' unexpired term after his Sept-2021 resignation, then continued into her own full term. NAME CHANGE: filed as 'Victoria Petro-Eschler' in 2021, 'Victoria Petro' from 2025 — cities.db carries BOTH name_keys (victoriapetroeschler + victoriapetro) for the SAME person; both map to person_key=victoria_petro. first_vote/last_vote here are clamped to this tenure's own [start_date, end_date) window (2021-11-16..2025-12-09 — the early-seat + first-full term); the two db name_keys are UNIONed by the vote-date loader, so her 2025 'Petro' votes are included in the window. Her 2026+ re-elected term carries its own later bounds."),
    dict(body="Council", seat_id="D1", person_name="Victoria Petro", person_key="victoria_petro",
         start_date="2026-01-13", start_event="reelected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (District 1 winner, def. Otterstrom 51.6-48.4); votes:continuous through 2026-06-09 (cities.db)",
         note="Re-elected D1 2025 (as 'Victoria Petro'; first D1 seat contested on the plan_2022 boundaries)."),

    # ============================ D2 (even cycle) ============================
    dict(body="Council", seat_id="D2", person_name="Van Blair Turner", person_key="van_turner",
         start_date="2008-01-01", start_event="elected", election_year="2007", end_event="did-not-run",
         confidence="medium",
         sources="election:2007 (District 2 winner, def. Clara 52.9-47.1)",
         note="PRE-VOTE-FLOOR (elected 2007; earliest tenure in this roster). Term-start inferred Jan 2008; continuous service inferred from the election chain (not verifiable below the 2020 minutes floor). LaMalfa won D2 2011."),
    dict(body="Council", seat_id="D2", person_name="Kyle LaMalfa", person_key="kyle_lamalfa",
         start_date="2012-01-01", start_event="elected", election_year="2011", end_event="did-not-run",
         confidence="medium",
         sources="election:2011 (District 2 winner, def. Turner 57.4-42.0)",
         note="PRE-VOTE-FLOOR term (elected 2011). Johnston won D2 2015."),
    dict(body="Council", seat_id="D2", person_name="Andrew Johnston", person_key="andrew_johnston",
         start_date="2016-01-01", start_event="elected", election_year="2015", end_event="reelected",
         confidence="medium",
         sources="election:2015 (District 2 winner, def. Turner 52.7-47.3)",
         note="PRE-VOTE-FLOOR term (elected 2015). Re-elected 2019 (2019 SOVC lost names — see next row)."),
    dict(body="Council", seat_id="D2", person_name="Andrew Johnston", person_key="andrew_johnston",
         start_date="2020-01-07", start_event="reelected", election_year="2019", end_event="resigned",
         confidence="medium", vacate_date="2021-04-20", vacate_confidence="medium",
         vacate_source="votes:last recorded council vote 2021-04-20 (cities.db); minutes:Faris present as D2 by 2021-05-18",
         sources="minutes:2020-01-07 (present, conducting D2); votes:2021-01-05..2021-04-20 (cities.db, D2)",
         note="2019-elected term (seated 2020-01-07, documented present). The 2019 general SOVC lost the candidate names, so the win is anchored to the 2020 present-list + 2021 votes, not the election file -> medium. RESIGNED spring 2021 (last vote 2021-04-20; joined the state homelessness effort) -> seat filled by appointment (Faris). Gap-bounded departure -> vacate_confidence=medium."),
    dict(body="Council", seat_id="D2", person_name="Dennis Faris", person_key="dennis_faris",
         start_date="2021-05-18", start_event="appointed", election_year="", end_event="lost",
         confidence="high",
         sources="minutes:2021-05-18 (Dennis Faris present as a Council Member — appointed to fill the D2 vacancy); votes:2021-05-18..2021-12-14 (cities.db, D2); election:2021 (ran the D2 special, 3rd, 16.0%)",
         note="APPOINTED to the vacant D2 seat (Johnston's resignation); first present/vote 2021-05-18. Ran in the Nov-2021 D2 SPECIAL election and LOST (166 first-choice, 3rd) -> served only the interim; term ended when Puy was seated 2022-01-04."),
    dict(body="Council", seat_id="D2", person_name="Alejandro Puy", person_key="alejandro_puy",
         start_date="2022-01-04", start_event="elected", election_year="2021", end_event="reelected",
         confidence="high",
         sources="election:2021 (District 2 special — first-choice PLURALITY leader, PUY 1,084 vs Palmer 751; see note); votes:first D2 vote 2022-01-04 (cities.db)",
         note="Won the 2021 D2 election (off-cycle special filling Johnston's vacancy, held at the Nov general — election_type 'municipal general' in the county file) as the first-choice PLURALITY leader: PUY 1,084 (42.53%) to Billy Palmer 751 (margin 333, 13.06%); SEATED 2022-01-04 (cities.db). SLC 2021 was an RCV pilot (the SOVC stores first-choice tallies) and Puy leads both the first-choice count and the seat. The earlier 'Palmer 363 / Puy 361' ordering was a suppressed-precinct partial-count artifact, FIXED at the elections layer 2026-07-19 (see election_results/); the election cross-check now reconciles with no exception. Puy filled the remainder of the D2 term, then was re-elected 2023."),
    dict(body="Council", seat_id="D2", person_name="Alejandro Puy", person_key="alejandro_puy",
         start_date="2024-01-09", start_event="reelected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 2 winner, UNOPPOSED 100%); votes:continuous through 2026-06-09 (cities.db)",
         note="Re-elected D2 2023 unopposed (first full D2 term on the plan_2022 lines; continuous service)."),

    # ============================ D3 (odd cycle) ============================
    dict(body="Council", seat_id="D3", person_name="Stan Penfold", person_key="stan_penfold",
         start_date="2010-01-01", start_event="elected", election_year="2009", end_event="reelected",
         confidence="medium",
         sources="election:2009 (District 3 winner, def. Carroll 52.4-47.6)",
         note="PRE-VOTE-FLOOR (elected 2009). Term-start inferred Jan 2010; continuous service inferred from the election chain. Re-elected 2013."),
    dict(body="Council", seat_id="D3", person_name="Stan Penfold", person_key="stan_penfold",
         start_date="2014-01-01", start_event="reelected", election_year="2013", end_event="did-not-run",
         confidence="medium",
         sources="election:2013 (District 3 winner, def. Clow 76.7-23.3)",
         note="PRE-VOTE-FLOOR term (re-elected 2013). Wharton won D3 2017."),
    dict(body="Council", seat_id="D3", person_name="Chris Wharton", person_key="chris_wharton",
         start_date="2018-01-01", start_event="elected", election_year="2017", end_event="reelected",
         confidence="medium",
         sources="election:2017 (District 3 winner, def. Carroll 56.6-43.4); votes:2021-01-05.. (cities.db, D3)",
         note="Elected 2017 (term-start inferred Jan 2018, pre-floor -> medium). Serving continuously ever since (longest-tenured current member); vote-corroborated from the 2021 floor."),
    dict(body="Council", seat_id="D3", person_name="Chris Wharton", person_key="chris_wharton",
         start_date="2022-01-04", start_event="reelected", election_year="2021", end_event="reelected",
         confidence="high",
         sources="election:2021 (District 3 winner, def. Berg 55.6-25.0); votes:continuous (cities.db)",
         note="Re-elected D3 2021 (last D3 term on the OLD plan_2012 lines)."),
    dict(body="Council", seat_id="D3", person_name="Chris Wharton", person_key="chris_wharton",
         start_date="2026-01-13", start_event="reelected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (District 3 winner, def. McClary 42.5-23.8); votes:continuous through 2026-06-09 (cities.db)",
         note="Re-elected D3 2025 (first D3 term on the plan_2022 lines; continuous service)."),

    # ============================ D4 (even cycle) ============================
    dict(body="Council", seat_id="D4", person_name="Luke Garrott", person_key="luke_garrott",
         start_date="2008-01-01", start_event="elected", election_year="2007", end_event="reelected",
         confidence="medium",
         sources="election:2007 (District 4 winner, def. Saxton 57.2-42.4)",
         note="PRE-VOTE-FLOOR (elected 2007). Term-start inferred Jan 2008; continuous service inferred from the election chain. Re-elected 2011."),
    dict(body="Council", seat_id="D4", person_name="Luke Garrott", person_key="luke_garrott",
         start_date="2012-01-01", start_event="reelected", election_year="2011", end_event="did-not-run",
         confidence="medium",
         sources="election:2011 (District 4 winner, def. Gray 77.7-20.7)",
         note="PRE-VOTE-FLOOR term (re-elected 2011). Kitchen won D4 2015."),
    dict(body="Council", seat_id="D4", person_name="Derek Kitchen", person_key="derek_kitchen",
         start_date="2016-01-01", start_event="elected", election_year="2015", end_event="resigned",
         confidence="medium", vacate_date="2019-01-01", vacate_confidence="medium",
         vacate_source="Derek Kitchen elected to the Utah State Senate (term began Jan 2019) and left D4; exact resignation date below the 2020 minutes floor",
         sources="election:2015 (District 4 winner, def. Salazar 51.8-48.2)",
         note="PRE-VOTE-FLOOR term (elected 2015). Left D4 mid-term ~Jan 2019 on election to the Utah State Senate; Valdemoros was appointed to fill the vacancy. The intervening VACANT window and its endpoints are pre-2020-minutes-floor (approximate) -> vacate_confidence=medium."),
    dict(body="Council", seat_id="D4", person_name="Ana Valdemoros", person_key="ana_valdemoros",
         start_date="2020-01-07", start_event="appointed", election_year="2019", end_event="did-not-run",
         confidence="medium",
         sources="minutes:2020-01-07 (present as D4 — 'Analia Valdemoros'); votes:2021-01-05..2023-12-12 (cities.db, D4)",
         note="Held D4 via a 2019 APPOINTMENT (to fill Kitchen's mid-term departure) AND the 2019 general (whose SOVC lost candidate names -> the win is not in the election file). Exact 2019 appointment date is below the 2020 minutes floor; first documented present 2020-01-07 -> anchored there, medium. Not a 2023 candidate -> Lopez Chavez won; last served 2023-12-12."),
    dict(body="Council", seat_id="D4", person_name="Eva Lopez Chavez", person_key="eva_lopez_chavez",
         start_date="2024-01-09", start_event="elected", election_year="2023", end_event="resigned",
         confidence="medium", vacate_date="2026-05-05", vacate_confidence="medium",
         vacate_source="votes:last recorded council vote 2026-05-05 (cities.db); minutes:2026-05-14 ('an update regarding the District 4 Council vacancy process, including the timeline'); 2026-05-12/05-19 sittings show 6 members (D4 empty)",
         sources="election:2023 (District 4 winner, def. Valdemoros 39.5-33.5, 3-way); votes:2024-01-09..2026-05-05 (cities.db, D4)",
         note="Elected 2023 (first D4 term on plan_2022). RESIGNED mid-2026: last vote 2026-05-05; the Council ran a documented D4 vacancy/appointment process (minutes 2026-05-12/05-14) and seated Napier-Pearce 2026-06-09. Exact resignation-effective date not pinned to a single quote -> vacate_confidence=medium."),
    dict(body="Council", seat_id="D4", person_name="Jennifer Napier-Pearce", person_key="jennifer_napier_pearce",
         start_date="2026-06-09", start_event="appointed", election_year="", end_event="serving",
         confidence="high",
         sources="minutes:2026-06-09 (present — 'all CM's plus jennifer napier pearce'); votes:first D4 vote 2026-06-09 (cities.db)",
         note="APPOINTED to the vacant D4 seat (Lopez Chavez's resignation); first present/vote 2026-06-09. Fills the remainder of the D4 term (next regular D4 election 2027)."),

    # ============================ D5 (odd cycle) ============================
    dict(body="Council", seat_id="D5", person_name="Jill Remington Love", person_key="jill_love",
         start_date="2010-01-01", start_event="elected", election_year="2009", end_event="did-not-run",
         confidence="medium",
         sources="election:2009 (District 5 winner, def. Write-In 94.8-5.2)",
         note="PRE-VOTE-FLOOR (elected 2009). Term-start inferred Jan 2010; continuous service inferred from the election chain. Mendenhall won D5 2013."),
    dict(body="Council", seat_id="D5", person_name="Erin Mendenhall", person_key="erin_mendenhall",
         start_date="2014-01-01", start_event="elected", election_year="2013", end_event="reelected",
         confidence="medium",
         sources="election:2013 (District 5 winner, def. Davis 81.8-18.2)",
         note="PRE-VOTE-FLOOR term (elected D5 2013). Re-elected 2017. (Same person as Mayor Mendenhall below — she moved from the D5 council seat to the Mayor's office in Jan 2020.)"),
    dict(body="Council", seat_id="D5", person_name="Erin Mendenhall", person_key="erin_mendenhall",
         start_date="2018-01-01", start_event="reelected", election_year="2017", end_event="became-mayor",
         confidence="medium", vacate_date="2020-01-07", vacate_confidence="high",
         vacate_source="minutes:2020-01-07 (present as 'Erin Mendenhall, Mayor' — no longer on the D5 council roll); minutes:2020-01-21 (Council appoints her D5 successor)",
         sources="election:2017 (District 5 winner, def. Chapman 83.9-16.1)",
         note="Re-elected D5 2017 (term-start inferred Jan 2018, pre-floor). WON the 2019 Mayoral race and VACATED D5 to take the Mayor's office in Jan 2020 (present as Mayor by 2020-01-07). Both endpoints documented in the 2020 minutes -> vacate_confidence=high; the short VACANT interval runs to Mano's 2020-01-21 appointment."),
    dict(body="Council", seat_id="D5", person_name="Darin Mano", person_key="darin_mano",
         start_date="2020-01-21", start_event="appointed", election_year="", end_event="elected",
         confidence="high",
         sources="minutes:2020-01-21 ('Adopting a resolution appointing Darin Masao Mano as ... District Five Councilmember. All Council Members were in favor'); votes:2021-01-05.. (cities.db, D5)",
         note="APPOINTED to the vacant D5 seat 2020-01-21 (unanimous resolution) after Mendenhall became Mayor. Then WON the 2021 D5 general (next row); continuous service."),
    dict(body="Council", seat_id="D5", person_name="Darin Mano", person_key="darin_mano",
         start_date="2022-01-04", start_event="elected", election_year="2021", end_event="did-not-run",
         confidence="high",
         sources="election:2021 (District 5 winner, def. Reale 49.7-25.6); votes:2022-01-04.. (cities.db, D5)",
         note="Elected D5 2021 (full term). Not a 2025 D5 candidate -> Carlsen won; term ended 2026-01-13. NOTE: cities.db shows a lone Mano vote-attribution on 2026-03-24 (one of two same-day meetings), AFTER Carlsen was seated 2026-01-13 — a known stray LLM vote-extraction artifact (SLC council votes are LLM-extracted); it does NOT extend his tenure and no post-2026-01-13 Mano tenure is created."),
    dict(body="Council", seat_id="D5", person_name="Erika Carlsen", person_key="erika_carlsen",
         start_date="2026-01-13", start_event="elected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (District 5 winner, def. Hawkins 66.0-31.2); votes:2026-01-13..2026-06-09 (cities.db, D5)",
         note="Elected D5 2025 (first D5 term on the plan_2022 lines). Succeeded Mano, who did not run."),

    # ============================ D6 (even cycle) ============================
    dict(body="Council", seat_id="D6", person_name="J T Martin", person_key="jt_martin",
         start_date="2008-01-01", start_event="elected", election_year="2007", end_event="did-not-run",
         confidence="medium",
         sources="election:2007 (District 6 winner, def. McConkie 53.3-46.4)",
         note="PRE-VOTE-FLOOR (elected 2007). Term-start inferred Jan 2008; continuous service inferred from the election chain. Luke won D6 2011."),
    dict(body="Council", seat_id="D6", person_name="Charlie Luke", person_key="charlie_luke",
         start_date="2012-01-01", start_event="elected", election_year="2011", end_event="reelected",
         confidence="medium",
         sources="election:2011 (District 6 winner, def. Martin 60.6-38.9)",
         note="PRE-VOTE-FLOOR term (elected 2011). Re-elected 2015."),
    dict(body="Council", seat_id="D6", person_name="Charlie Luke", person_key="charlie_luke",
         start_date="2016-01-01", start_event="reelected", election_year="2015", end_event="did-not-run",
         confidence="medium",
         sources="election:2015 (District 6 winner, def. Harty 63.5-36.5)",
         note="PRE-VOTE-FLOOR term (re-elected 2015; term runs to Jan 2020). Dugan won D6 2019."),
    dict(body="Council", seat_id="D6", person_name="Daniel Dugan", person_key="daniel_dugan",
         start_date="2020-01-07", start_event="elected", election_year="2019", end_event="reelected",
         confidence="medium",
         sources="minutes:2020-01-07 (present as D6 — 'Daniel Dugan'); votes:2021-01-05.. (cities.db, D6)",
         note="2019-elected term (seated 2020-01-07, documented present). The 2019 general SOVC lost candidate names, so the win is anchored to the 2020 present-list + 2021 votes, not the election file -> medium. Re-elected 2023."),
    dict(body="Council", seat_id="D6", person_name="Daniel Dugan", person_key="daniel_dugan",
         start_date="2024-01-09", start_event="reelected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 6 winner, def. Semnani 45.5-34.9); votes:continuous through 2026-06-09 (cities.db)",
         note="Re-elected D6 2023 (first D6 term on the plan_2022 lines; continuous service). Election-file name 'DAN DUGAN' vs the vote-record 'Daniel Dugan' — same person (see precinct cross-check note)."),

    # ============================ D7 (odd cycle) ============================
    dict(body="Council", seat_id="D7", person_name="Soren Simonsen", person_key="soren_simonsen",
         start_date="2010-01-01", start_event="elected", election_year="2009", end_event="did-not-run",
         confidence="medium",
         sources="election:2009 (District 7 winner, def. Adams 50.0-49.7 — 13-vote margin)",
         note="PRE-VOTE-FLOOR (elected 2009 by 13 votes). Term-start inferred Jan 2010; continuous service inferred from the election chain. Adams won D7 2013."),
    dict(body="Council", seat_id="D7", person_name="Lisa Ramsey Adams", person_key="lisa_adams",
         start_date="2014-01-01", start_event="elected", election_year="2013", end_event="did-not-run",
         confidence="medium",
         sources="election:2013 (District 7 winner, def. Paulson 68.9-31.1)",
         note="PRE-VOTE-FLOOR term (elected 2013). Fowler won D7 2017."),
    dict(body="Council", seat_id="D7", person_name="Amy Fowler", person_key="amy_fowler",
         start_date="2018-01-01", start_event="elected", election_year="2017", end_event="reelected",
         confidence="medium",
         sources="election:2017 (District 7 winner, def. Smith 63.4-36.6); votes:2021-01-05.. (cities.db, D7)",
         note="Elected D7 2017 (term-start inferred Jan 2018, pre-floor -> medium). Re-elected 2021."),
    dict(body="Council", seat_id="D7", person_name="Amy Fowler", person_key="amy_fowler",
         start_date="2022-01-04", start_event="reelected", election_year="2021", end_event="resigned",
         confidence="medium", vacate_date="2023-06-13", vacate_confidence="medium",
         vacate_source="votes:last recorded council vote 2023-06-13 (cities.db); minutes:2023-06-13 (Fowler 'took a moment of personal privilege'); minutes:2023-07-13 ('Sarah Young was appointed as the new District 7 Council [member]')",
         sources="election:2021 (District 7 winner, def. Raskin 63.1-32.8); votes:2022-01-04..2023-06-13 (cities.db, D7)",
         note="Re-elected D7 2021. RESIGNED mid-term June 2023 (last vote/farewell 2023-06-13) -> seat filled by appointment (Young). Gap-bounded departure -> vacate_confidence=medium."),
    dict(body="Council", seat_id="D7", person_name="Sarah Young", person_key="sarah_young",
         start_date="2023-07-18", start_event="appointed", election_year="", end_event="elected",
         confidence="high",
         sources="minutes:2023-07-13 ('Sarah Young was appointed as the new District 7 Council [member]'); votes:first D7 vote 2023-07-18 (cities.db)",
         note="APPOINTED to the vacant D7 seat (Fowler's resignation); first vote 2023-07-18. Then WON the Nov-2023 D7 SPECIAL election (next row)."),
    dict(body="Council", seat_id="D7", person_name="Sarah Young", person_key="sarah_young",
         start_date="2024-01-09", start_event="elected", election_year="2023", end_event="reelected",
         confidence="high",
         sources="election:2023 (District 7 SPECIAL winner, def. Jones 52.2-47.8); votes:continuous (cities.db, D7)",
         note="Won the 2023 D7 special (on the Nov-2023 general ballot) for the unexpired term; continuous service from her July-2023 appointment. Re-elected 2025."),
    dict(body="Council", seat_id="D7", person_name="Sarah Young", person_key="sarah_young",
         start_date="2026-01-13", start_event="reelected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (District 7 winner, UNOPPOSED 100% vs Unresolved Write-In); votes:continuous through 2026-06-09 (cities.db)",
         note="Re-elected D7 2025 unopposed (first full D7 term on the plan_2022 lines)."),

    # ============================ MAYOR (does NOT vote) ============================
    dict(body="Mayor", seat_id="MAYOR", person_name="Ralph Becker", person_key="ralph_becker",
         start_date="2008-01-01", start_event="elected", election_year="2007", end_event="reelected",
         confidence="medium",
         sources="election:2007 (Mayor winner, def. Buhler 63.8-35.9)",
         note="PRE-VOTE-FLOOR (elected Mayor 2007). Term-start inferred Jan 2008. Mayor does NOT vote on council motions. Re-elected 2011."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Ralph Becker", person_key="ralph_becker",
         start_date="2012-01-01", start_event="reelected", election_year="2011", end_event="lost",
         confidence="medium",
         sources="election:2011 (Mayor winner, def. Kimball 74.9-23.9); election:2015 (LOST to Biskupski 48.4-51.6)",
         note="PRE-VOTE-FLOOR term (re-elected 2011). LOST the 2015 general to Biskupski -> term ended Jan 2016."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Jackie Biskupski", person_key="jackie_biskupski",
         start_date="2016-01-01", start_event="elected", election_year="2015", end_event="did-not-run",
         confidence="medium",
         sources="election:2015 (Mayor winner, def. incumbent Becker 51.6-48.4)",
         note="PRE-VOTE-FLOOR term (elected Mayor 2015; first openly-LGBTQ SLC mayor). Did not seek re-election in 2019 -> Mendenhall won."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Erin Mendenhall", person_key="erin_mendenhall",
         start_date="2020-01-07", start_event="became-mayor", election_year="2019", end_event="reelected",
         confidence="high",
         sources="minutes:2020-01-07.. (presiding as 'Erin Mendenhall, Mayor'); election:2023 (Mayor winner — re-election)",
         note="Won the 2019 Mayoral race (moving up from her D5 council seat — see D5 rows). The 2019 general SOVC lost candidate names, so this is anchored to the 2020+ minutes (she presides as Mayor throughout) rather than the election file -> still HIGH (minutes-documented presiding). Mayor does NOT vote on council motions (absent from the cities.db council role table — correct). Re-elected 2023."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Erin Mendenhall", person_key="erin_mendenhall",
         start_date="2024-01-01", start_event="reelected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (Mayor winner, def. former-mayor 'Rocky' Anderson 58.4-34.4); minutes:presiding through 2026 (Mayor)",
         note="Re-elected Mayor 2023. Continues to preside; does not vote on council motions."),
]

# canonical UPPER-CASE election name token -> our person_key.
# LUKE/GARROTT disambiguation: 'Luke Garrott' (D4) shares the token LUKE with 'Charlie Luke'
# (D6). We key Garrott on his surname GARROTT and Luke on his FIRST name CHARLIE (both
# unique), and deliberately do NOT map the bare token LUKE.
NAME_TO_KEY = {
    "TURNER": "van_turner", "LAMALFA": "kyle_lamalfa", "JOHNSTON": "andrew_johnston",
    "FARIS": "dennis_faris", "PUY": "alejandro_puy",
    "CHRISTENSEN": "carlton_christensen", "ROGERS": "james_rogers",
    "PETRO": "victoria_petro", "PETRO-ESCHLER": "victoria_petro",
    "PENFOLD": "stan_penfold", "WHARTON": "chris_wharton",
    "GARROTT": "luke_garrott", "KITCHEN": "derek_kitchen",
    "VALDEMOROS": "ana_valdemoros", "LOPEZ": "eva_lopez_chavez", "CHAVEZ": "eva_lopez_chavez",
    "NAPIER-PEARCE": "jennifer_napier_pearce", "NAPIER": "jennifer_napier_pearce",
    "LOVE": "jill_love", "MENDENHALL": "erin_mendenhall", "MANO": "darin_mano",
    "CARLSEN": "erika_carlsen",
    "MARTIN": "jt_martin", "CHARLIE": "charlie_luke", "DUGAN": "daniel_dugan",
    "SIMONSEN": "soren_simonsen", "ADAMS": "lisa_adams", "FOWLER": "amy_fowler",
    "YOUNG": "sarah_young",
    "BECKER": "ralph_becker", "BISKUPSKI": "jackie_biskupski",
}

# cities.db person.name_key -> our person_key (only the 2021+ voters exist in the db;
# Mayor Mendenhall is intentionally NOT in the council role table — she does not vote).
# NOTE: Victoria Petro appears under TWO name_keys (the 2021 'Petro-Eschler' spelling +
# the 2025 'Petro' spelling) for the SAME person; both map to victoria_petro.
DB_KEY = {
    "amyfowler": "amy_fowler", "anavaldemoros": "ana_valdemoros",
    "andrewjohnston": "andrew_johnston", "chriswharton": "chris_wharton",
    "danieldugan": "daniel_dugan", "darinmano": "darin_mano",
    "jamesrogers": "james_rogers", "dennisfaris": "dennis_faris",
    "victoriapetroeschler": "victoria_petro", "victoriapetro": "victoria_petro",
    "alejandropuy": "alejandro_puy", "sarahyoung": "sarah_young",
    "evalopezchavez": "eva_lopez_chavez", "erikacarlsen": "erika_carlsen",
    "jennifernapierpearce": "jennifer_napier_pearce",
}


def seat_for_contest(office, district):
    """election (office, district) -> seat_id (or None). SLC: 7 geographic districts + Mayor;
    NO at-large/citywide council seats."""
    if office == "Mayor":
        return "MAYOR"
    d = district.strip()
    if d in ("1", "2", "3", "4", "5", "6", "7"):
        return "D" + d
    return None


REDISTRICT = Redistrict(
    plan_old=PLAN_OLD, plan_new=PLAN_NEW, plan_switch=PLAN_SWITCH,
    ord=REDISTRICT_ORD, adopted=REDISTRICT_ADOPTED,
    districts=["District 1", "District 2", "District 3", "District 4",
               "District 5", "District 6", "District 7"],
    geom_ref=GEOM_REF, source_url=SRC_URL, data_floor=DATA_FLOOR,
    current_note=(f"CURRENT post-2020-census boundaries. {REDISTRICT_ORD} (Redistricting City "
                  "Council District Boundaries) adopted 2022-05-10 and RE-ADOPTED 7-0 on "
                  f"{REDISTRICT_ADOPTED} to correct one property (D6->D3), designating the seven "
                  "district lines from the 2020 Census (Exhibit A). geometry_ref carries the "
                  "current SLC precinct polygons; precinct->district in geo/precinct_to_district.csv "
                  "(2023 even + 2025 odd generals). First used for elections 2023 (D2/D4/D6) and "
                  "2025 (D1/D3/D5/D7)."),
    prior_adopted_by="prior plan (post-2010-census redistricting)",
    prior_geom_ref="geo/council_districts_pre2022.geojson",
    # ALL DISTRICTS confidence=low (DOWNGRADED 2026-07-19 from the earlier per-district medium/low). The
    # earlier assumption that D1-D6 "recover cleanly" (100% of old codes present) was FALSIFIED by a
    # fragmentation control: dissolving CURRENT precinct shapes by the CURRENT assignment yields clean
    # 1-piece districts, but this pre-2022 dissolve yields 2-15-piece fragments (D6=15,D5=9,D4=7,D2=6) even
    # where all codes are "present" -> the old SLC codes were RENUMBERED to different geography (the county
    # renumber the recon already noted), so code-presence != geometric fidelity. No authoritative pre-2022
    # layer exists (both SLC org layers — Salt_Lake_City_Council_Districts + City_Council_Boundries — are the
    # current 2022 plan, IoU 0.995 to each other). Millcreek defect, city-wide. See prior_note.
    prior_confidence={"District 1": "low", "District 2": "low", "District 3": "low",
                      "District 4": "low", "District 5": "low", "District 6": "low",
                      "District 7": "low"},
    prior_confidence_default="low",
    prior_note=("Prior-plan (pre-2022 / plan_2012, post-2010-census) district boundaries RECONSTRUCTED "
                "2026-07-19 (scripts/build_prior_district_map.py --city slc_city_council --years 2019,2021 "
                "--precincts geo/slco_precincts_current.geojson) by dissolving the current-vintage SLCo "
                "precinct shapes by the pre-2022 precinct->district assignment read from the 2019 (D2/D4/D6) "
                "+ 2021 (D1/D2/D3/D5/D7) district-contest precinct rows — the same derivation used for the "
                "current plan_2022 map. geometry_ref=geo/council_districts_pre2022.geojson. APPROXIMATE: the "
                "OLD assignment over CURRENT precinct shapes -> medium ceiling. 107/124 old SLC precinct codes "
                "carry current geometry; 17 renumbered/retired codes are HONEST holes. THE HOLES ARE HIGHLY "
                "UNEVEN: D1-D5 = 0 holes (clean), D6 = 1/22 hole (SLC135), but D7 = 16/22 holes "
                "(SLC146-152/155/156/158-160/163/164/166/167) so its reconstructed polygon is a fragment "
                "covering only ~6 precincts -> D7 marked confidence=low (see prior_note_by_district). 2 conflicts: "
                "SLC055 + SLC062 appear under 2019 D4 and 2021 D5 -> resolved to D5 (latest). In force for the "
                "2007-2021 elections. effective_start = data floor. Probed the SL County 2020-vintage "
                "VistaBallotAreas layer to firm up the holes (esp. D7); not acquirable as a simple open endpoint "
                "(UGRC serves only the current vintage) -> holes left as honest gaps. "
                "VALIDATION 2026-07-19 (LM-wave follow-up): fetched SLC's own authoritative GIS "
                "(services.arcgis.com/mMBpeYj0vPFotzbe: Salt_Lake_City_Council_Districts + the legacy "
                "City_Council_Boundries) — BOTH are the CURRENT 2022 plan (IoU 0.995 to each other; carry "
                "2022-era members Puy/Petro/etc.). SLC publishes NO 2012-vintage boundary layer. A fragmentation "
                "control PROVES the renumbering is CITY-WIDE, not just D7: the CURRENT-assignment dissolve yields "
                "clean 1-piece districts, but this pre-2022 dissolve yields 2-15-piece fragments (D6=15, D5=9, "
                "D4=7, D2=6) EVEN for D1-D6 whose codes are all 'present' -> code-presence != geometric fidelity; "
                "the county renumbered the SLC precinct codes between the SOVC vintage and the current UGRC shapes "
                "(the millcreek defect). No authoritative prior layer exists to replace it -> ALL districts' "
                "geometry confidence DOWNGRADED to low (was D1-D6 medium / D7 low). The district_precincts "
                "precinct-CODE composition stays medium (a faithful SOVC record, geometry-independent). See "
                "scripts/roster_boundary_recon.md."),
    prior_note_by_district={
        "District 6": ("Prior-plan (plan_2012) D6 boundary RECONSTRUCTED 2026-07-19, DOWNGRADED to low 2026-07-19: "
                       "21/22 old codes are 'present' but the dissolve is a 15-PIECE fragment (fragmentation control "
                       "shows the CURRENT-assignment dissolve is 1 clean piece) -> renumbering-corrupted, not a "
                       "faithful boundary. See the citywide prior_note + scripts/roster_boundary_recon.md."),
        "District 7": ("Prior-plan (plan_2012) D7 is HOLE-DOMINATED (confidence=low): only 6 of D7's 22 old "
                       "precinct codes carry current geometry — 16 were renumbered/retired in 2022 (SLC146-152, "
                       "155, 156, 158-160, 163, 164, 166, 167). The dissolved geometry_ref polygon is therefore a "
                       "FRAGMENT of the true pre-2022 D7 extent, NOT a faithful boundary — do NOT treat it as D7's "
                       "actual 2012-plan area. The recovered 6-precinct composition is in district_precincts (medium). "
                       "Firming this up needs the SL County 2020-vintage VistaBallotAreas layer (probed; not a simple "
                       "open endpoint). See scripts/roster_boundary_recon.md."),
    },
    citywide_rows=[("MAYOR", "citywide", "the separately-elected Mayor")],
    citywide_adopted_by="Salt Lake City (Mayor — whole city)",
    citywide_note_template=("{who}: represents the ENTIRE city on every date, unchanged by the 2022 "
                            "redistricting. SLC has NO at-large council seats — all 7 council seats are "
                            "geographic districts; only the Mayor is citywide. geometry_ref = full city extent."),
    precinct_hi_source="2025",
    precinct_hi_note="post-redistrict precinct->district cross-validated against the 2025 (odd-district) municipal general",
    precinct_med_note=("post-redistrict precinct->district from the 2023 (even-district) municipal "
                       "general — EQUALLY authoritative as the 2025 rows; 'medium' here is only the "
                       "shared library's single-high-source-year limitation (see roster CLAUDE.md), "
                       "NOT a data-quality distinction"),
    precinct_prior_note=("Reconstructed pre-2022 (plan_2012) precinct->district composition (107/124 old SLC "
                         "precinct codes present, from the 2019 D2/D4/D6 + 2021 D1/D2/D3/D5/D7 SOVC district "
                         "contests; SLC055/SLC062 conflict resolved to the 2021 D5 assignment; 17 renumbered/"
                         "retired codes are honest holes, absent here — 16 of them in D7). medium — current-vintage "
                         "precinct shapes. See scripts/roster_boundary_recon.md."),
    crosscheck_districts=("1", "3", "4", "5", "7"),   # exact election-name matchers (see CLAUDE.md re D2/D6)
    precinct_prefix="SLC", geo_seat_prefix="D",
    plan_switch_year="2023", citywide_seats=(),
)

CFG = RosterConfig(
    non_voting_mayor=True,
    # H-C reverse-election-crosscheck exceptions: NONE since 2026-07-19. The four entries
    # curated earlier that day (Johnston/Dugan/Mendenhall 2019 + Puy 2021 D2) cited two SLC
    # election-source defects that were FIXED at the source layer the same day
    # (_backups/2026-07-19-slc-elections-fix/): the garbled 2019 general slice was re-synced
    # from the archive's family-B re-parse (real winners restored: Johnston D2 1745, Valdemoros
    # D4 4734, Dugan D6 4655, Mendenhall Mayor 26762), and the 2021 suppressed-precinct
    # Total-recovery normalizer fix restored full first-choice tallies (D2: PUY 1084 > Palmer
    # 751 — Puy is the plurality leader AND the seated member; the old 363/361 "swap" was a
    # partial-count artifact of dropped privacy-suppressed precincts). Both directions of the
    # election cross-check now reconcile with no exceptions; H-C fails loudly if a stale entry
    # is ever re-added.
    reverse_crosscheck_exceptions={},
    city=CITY, city_dir=CITY_DIR, repo_root=REPO_ROOT, data_floor=DATA_FLOOR,
    geom_ref=GEOM_REF, elections_path=ELECTIONS, cities_db_path=CITIES_DB,
    overrides_path=OVERRIDES, terms_out=TERMS_OUT, districts_out=DISTRICTS_OUT,
    seat_district=SEAT_DISTRICT, name_to_key=NAME_TO_KEY, db_key=DB_KEY,
    seat_order=["D1", "D2", "D3", "D4", "D5", "D6", "D7", "MAYOR"],
    keep_election_row=lambda r: r["election_type"].strip().lower() == "municipal general",
    contest_key=seat_for_contest, crosscheck_field="seat_id",
    winners_have_district=True,
    elected_events=("elected", "reelected", "became-mayor"),
    redistrict=REDISTRICT, precincts_out=PRECINCTS_OUT,
    precinct_map_path=PRECINCT_MAP, precincts_byprecinct_path=PRECINCTS_BYP,
    prior_precinct_map_path=os.path.join(CITY_DIR, "geo", "precinct_to_district_pre2022.csv"),
)


# ---------------------------------------------------------------------------
# Demo queries (SLC presentation)
# ---------------------------------------------------------------------------
def demo():
    def line(r):
        end = r["end_date"] or "—(serving)"
        return (f"    {r['seat_id']:<6} {r['person_name']:<22} {r['start_date']} -> {end:<12}"
                f" [{r['start_event']}/{r['end_event']}] conf={r['confidence']}")

    print("\n(a) CURRENT council roster + mayor (end_date empty, end_event=serving):")
    for r in roster_lib.load_terms(CFG):
        if not r["end_date"] and r["end_event"] == "serving":
            print(line(r))

    print("\n(b) Roster AS OF 2021-06-01 (mid the D1/D2 vacancy churn):")
    for r in roster_lib.roster_as_of(CFG, "2021-06-01", body="Council"):
        print(line(r))
    for r in roster_lib.roster_as_of(CFG, "2021-06-01", body="Mayor"):
        print(line(r))

    print("\n(c) NON-DEGENERATE address+date -> representative (via geo/address_to_district.py):")
    # SLC addresses are grid intersections, not parcels — the Census geocoder still resolves
    # a street address to a point; point-in-polygon then gives the precinct -> district. We
    # pass a lat/lon + precinct fallback so the demo runs OFFLINE (no Census call needed).
    addr = "451 S State St, Salt Lake City, UT 84111"   # City & County Building
    for d in ("2026-07-01", "2025-06-01"):
        res = roster_lib.representatives_for_address(CFG, addr, d, latlon=(40.7596, -111.8879),
                                                     precinct="SLC054")
        who = ", ".join(f"{x['person_name']}({x['seat_id']})" for x in res["reps"])
        loc = (f"District {res['district']} via {res.get('precinct')} "
               f"[{res.get('method')}]") if res.get("district") else f"[{res.get('gap','?')}]"
        print(f"  '{addr}'  (SLC grid-intersection geocode)")
        print(f"    on {d} (plan={res['plan']}): {loc}")
        print(f"    -> your reps: {who}")

    print("\n(d) SAME address across the 2022 REDISTRICTING (versioned district_versions):")
    for d in ("2021-06-01", "2025-06-01"):
        res = roster_lib.representatives_for_address(CFG, addr, d, latlon=(40.7596, -111.8879),
                                                     precinct="SLC054")
        if res.get("district"):
            reps = [x['person_name'] for x in res['reps'] if x['seat_id'].startswith('D')]
            print(f"    {d} (plan={res['plan']}): geographic District {res['district']} -> {reps}")
        else:
            print(f"    {d} (plan={res['plan']}): {res.get('gap')}")

    print("\n(e) Precinct-map cross-check (district_precincts vs election outcomes):")
    roster_lib.precinct_crosscheck(CFG, verbose=True)


if __name__ == "__main__":
    rows = roster_lib.build(CFG, TENURES)
    n = {c: sum(1 for r in rows if r["confidence"] == c) for c in ("high", "medium", "low")}
    nvac = sum(1 for r in rows if r["start_event"] == "vacated")
    print(f"Wrote {os.path.relpath(TERMS_OUT, CITY_DIR)} "
          f"({len(rows)} tenures incl. {nvac} VACANT: {n['high']} high / {n['medium']} medium / {n['low']} low)")
    print(f"Wrote {os.path.relpath(DISTRICTS_OUT, CITY_DIR)} "
          f"(7 districts x 2 plans + Mayor; redistricting {REDISTRICT_ORD})")
    print(f"Wrote {os.path.relpath(PRECINCTS_OUT, CITY_DIR)} "
          f"(plan_2022 precinct map + plan_2012 gap rows)")
    if "--check" in sys.argv:
        print("\nValidation: PASS (no overlaps; sources+confidence present; gap/vacate guards clear).")
        print("Precinct cross-check:")
        roster_lib.precinct_crosscheck(CFG, verbose=True)
    if "--demo" in sys.argv:
        demo()
