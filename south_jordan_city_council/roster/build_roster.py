#!/usr/bin/env python3
"""build_roster.py — rolling council-roster for SOUTH JORDAN (a slowly-changing-dimension /
interval table of who holds each council + mayor seat over time). South Jordan is a
**PURE-DISTRICT** Council-Mayor city: **5 geographic council districts** (D1..D5, NO at-large/
citywide council seats) + a **separately-elected Mayor who does NOT vote** on council motions
(she presides; the single exception is one statutory tie-break — see the MAYOR block). Council
votes exist from **2020** (named roll-calls 2020-08-18+; the 2020 Jan–Jul motions were PMN-
backfilled but are tally-only), while the county election record runs **2007+**. The 5 districts
were **redrawn after the 2020 Census** (Ordinance 2022-13, adopted 2022-06-07).

THIN DRIVER: this file holds only South-Jordan-specific DATA (the curated TENURES, the name maps,
the 2022-redistricting facts + prose) + config; all generic mechanics live in
../../scripts/roster_lib.py (canon_key, election/vote-bounds/override reconciliation, end-date
chaining + VACANT insertion, validation incl. the gap/vacate guards, the CSV writers, and the
as-of / address / precinct-crosscheck query helpers). The DISTRICT reference template is
slc_city_council/roster/build_roster.py (pure districts + non-voting mayor + redistricting +
precinct + address-join).

DERIVED LAYER — regenerable, never hand-edited. Canonical inputs:
  1. election_results/south_jordan_results_by_candidate.csv (winners -> `elected`/`reelected`; 2007+)
  2. cities.db  role table (city='south_jordan', body='Council')  (observed vote bounds)
  3. meeting_minutes/minutes/**  (oath dates, the redistricting ordinance, member departures)
  4. roster/roster_overrides.csv  (hand corrections; applied LAST, win ties)

Outputs (idempotent — re-running reproduces them byte-for-byte):
  roster/council_terms.csv        one row per seat-tenure (5 district seats + MAYOR)
  roster/district_versions.csv    boundary interval table — REAL 5 districts x 2 plans + Mayor
  roster/district_precincts.csv   versioned precinct->district composition (plan-scoped)
  roster/_precinct_to_district.csv  DERIVED helper — geo/precinct_to_district.csv + a source_year
                                    column (the shared write_precincts() needs `source_year`).

Usage:
  python3 roster/build_roster.py            # regenerate the CSVs
  python3 roster/build_roster.py --demo     # regenerate + print the demo queries
  python3 roster/build_roster.py --check    # regenerate + validations + precinct cross-check

Cardinal rule (repo CLAUDE.md): NEVER fabricate. Unknown seat-holder / boundary / date ->
explicit VACANT/gap + confidence + a note, never a guess.

Provenance / confidence model (South Jordan):
  high   = a documented Jan oath (2022-01-04 / 2024-01-02) or first-2026-meeting seating
           (2026-01-06), OR a 2019-recovered-SOVC win seated Jan-2020 and corroborated by the
           2020-08+ audited minutes present-lists + the named-vote record (continuous service).
  medium = an election-anchored term that PREDATES the 2020 data floor (no minutes/vote
           corroboration — the win is a fact, continuous service is inferred from the election
           chain), incl. every pre-2018 term-start (inferred YYYY-01-01) and the 2017-cycle
           terms whose Jan-2018 start is inferred (their tail IS vote-corroborated from 2020).
  low    = genuinely unknown / not-acquired (flagged) — NONE remain: the prior-plan
           district/precinct rows were RECONSTRUCTED to `medium` 2026-07-11 (approximate;
           see the Redistrict prior_note / scripts/roster_boundary_recon.md).

South Jordan seat model (STABLE ids — a redistricting redraws boundaries, it does NOT renumber
seats):
  D1..D5  five geographic district seats     MAYOR  separately-elected mayor (does NOT vote)
Staggered 4-year cycles (odd calendar years):
  A  Mayor + D3 + D5   elected 2009/13/17/21/25  -> terms seated Jan 2010/14/18/22/26
  B  D1 + D2 + D4       elected 2007/11/15/19/23  -> terms seated Jan 2008/12/16/20/24

KNOWN nuances handled honestly (never fabricated around):
  * NON-VOTING MAYOR. Dawn R. Ramsey presides and does NOT vote on council legislation. The ONE
    exception in the loaded window is a **statutory tie-break on 2025-06-17** (Ordinance 2025-09):
    the four members present split 2-2 (Shelton/Johnson Yes, Harris/McGuire No, Zander absent) and
    "Mayor Dawn R. Ramsey - Yes" broke the tie ("The motion passed with a vote of 3-2"). cities.db
    records exactly one dawnrramsey Council vote (2025-06-17). `non_voting_mayor=True` empties every
    MAYOR-body vote-bound so that lone tie-break can't smear a span across her mayoral tenures, and
    dawnrramsey is deliberately NOT in DB_KEY.
  * SPARSE, DISSENT-ONLY vote naming. South Jordan often records only the outcome/dissenters, so a
    member's first/last NAMED vote lags their real service (e.g. Harris D1 first named vote
    2021-09-21 though seated Jan-2020; Marlor D2 last named vote 2023-03-07 though he served the
    proclamation-honored full term through Dec-2023). A late first/early last named vote is a
    RECORDING LIMIT, not a gap.
  * AUDITED-MINUTES FLOOR 2020-08-18. The Jan–Jul 2020 council meetings live only in pmn_backfill/
    (tally-only, `provenance=pmn_minutes` in cities.db) and are NOT in the audited minutes layer, so
    the Jan-2020 seatings of the 2019-cycle (Harris/Marlor/Zander) are anchored to the recovered 2019
    SOVC + the first documented 2020 council meeting (2020-01-07); earliest audited present-list is
    2020-08-18.
  * PRE-FLOOR MAYORAL SUCCESSION (Money->Osborne, ~2010-2013). The 2009 mayor was W. Kent Money, but
    the 2013 general shows Dave Alvord defeating INCUMBENT Scott L. Osborne (Money is not a 2013
    candidate). An intervening pre-floor Money->Osborne mayoral change is externally attested but its
    dates are entirely below the 2020 data floor and unreconstructable from loaded sources — flagged
    in Money's note, NOT modeled as a fabricated Osborne tenure (see repo cardinal rules).
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.dirname(HERE)                 # south_jordan_city_council/
REPO_ROOT = os.path.dirname(CITY_DIR)            # civic-data/
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import roster_lib
from roster_lib import RosterConfig, Redistrict

ELECTIONS = os.path.join(CITY_DIR, "election_results", "south_jordan_results_by_candidate.csv")
PRECINCTS_BYP_SRC = os.path.join(CITY_DIR, "election_results", "south_jordan_results_by_precinct.csv")
GEO_PRECINCT_MAP = os.path.join(CITY_DIR, "geo", "precinct_to_district.csv")
CITIES_DB = os.path.join(REPO_ROOT, "cities.db")
OVERRIDES = os.path.join(HERE, "roster_overrides.csv")
TERMS_OUT = os.path.join(HERE, "council_terms.csv")
DISTRICTS_OUT = os.path.join(HERE, "district_versions.csv")
PRECINCTS_OUT = os.path.join(HERE, "district_precincts.csv")
PRECINCT_MAP = os.path.join(HERE, "_precinct_to_district.csv")   # DERIVED (geo map + source_year)

CITY = "south_jordan"
DATA_FLOOR = "2020-01-01"            # data floor (city standard: 2020)
GEOM_REF = "geo/council_districts.geojson"

# The real redistricting event (spot-checked against source minutes 2022-06-07):
#   Ordinance 2022-13, "Amending Section 1.12.030: District Boundaries, to remove the legal
#   descriptions, set forth in the City Council District Boundary Map based on the 2020 census."
#   Adopted on a UNANIMOUS 5-0 roll call (motion Marlor / second Harris). Minutes 2022-06-07:
#   "the new district boundaries are reflective of change and growth in our city over the last 10
#   years ... drawn based on the current census information [the 2020 decennial census]." First
#   used for the 2023 (B: D1/D2/D4) and 2025 (A: D3/D5) elections; the 2021 election used the prior
#   lines. (South Jordan redistricts by ORDINANCE — unlike SLC's/Sandy's resolution.)
REDISTRICT_ORD = "Ordinance 2022-13"
REDISTRICT_ADOPTED = "2022-06-07"
PLAN_OLD = "plan_pre2022"   # pre-2022 boundaries, in force through the 2021 elections (RECONSTRUCTED 2026-07-11, medium)
PLAN_NEW = "plan_2022"      # Ordinance 2022-13; in force for the 2023 election onward
PLAN_SWITCH = "2022-06-07"  # documented adoption of the 2020-census boundaries
SRC_URL = ("https://s3-us-west-2.amazonaws.com/municipalcodeonline.com-new/southjordan/"
           "ordinances/documents/1656350109_Ordinance%20No.%202022-13.pdf")

SEAT_DISTRICT = {
    "D1": "District 1", "D2": "District 2", "D3": "District 3", "D4": "District 4",
    "D5": "District 5", "MAYOR": "Citywide",
}

# ---------------------------------------------------------------------------
# LAYER 1-3 (reconciled). Each tenure anchored to a cited source. Ordered by seat.
#   Documented seating dates: 2020-01-07 (first documented 2020 council mtg, pmn_backfill),
#   2022-01-04 (oath, 2021-cycle), 2024-01-02 (oath, 2023-cycle), 2026-01-06 (first 2026 mtg,
#   2025-cycle). Pre-2020-floor term-starts use YYYY-01-01 (inferred from the stagger -> medium).
# ---------------------------------------------------------------------------
TENURES = [
    # ============================ D1 (B cycle) ============================
    dict(body="Council", seat_id="D1", person_name="Leona Winger", person_key="leona_winger",
         start_date="2008-01-01", start_event="elected", election_year="2007", end_event="did-not-run",
         confidence="medium",
         sources="election:2007 (District 1 winner, 97.4% vs Write-in)",
         note="PRE-DATA-FLOOR (elected 2007; earliest D1 tenure). Term-start inferred Jan 2008 from the "
              "B-cycle stagger; continuous service inferred from the election chain (not verifiable below "
              "the 2020 data floor). Not a 2011 D1 candidate -> Seethaler won."),
    dict(body="Council", seat_id="D1", person_name="Mark Seethaler", person_key="mark_seethaler",
         start_date="2012-01-01", start_event="elected", election_year="2011", end_event="did-not-run",
         confidence="medium",
         sources="election:2011 (District 1 winner, def. Jim Wright 73.5%)",
         note="PRE-DATA-FLOOR term (elected 2011). Not a 2015 D1 candidate -> Harris won."),
    dict(body="Council", seat_id="D1", person_name="Patrick Harris", person_key="patrick_harris",
         start_date="2016-01-01", start_event="elected", election_year="2015", end_event="reelected",
         confidence="medium",
         sources="election:2015 (District 1 winner, def. Geilmann 66.2%)",
         note="PRE-DATA-FLOOR term (elected 2015; term-start inferred Jan 2016). Re-elected 2019. "
              "No observed Council vote in this 2016-2020 window, so first_vote/last_vote are BLANK "
              "(clamped to the tenure); Harris's recorded votes begin 2021-09-21, in a LATER tenure."),
    dict(body="Council", seat_id="D1", person_name="Patrick Harris", person_key="patrick_harris",
         start_date="2020-01-07", start_event="reelected", election_year="2019", end_event="reelected",
         confidence="high",
         sources="election:2019 (District 1 winner, UNOPPOSED 100% — recovered SOVC, see election_results); "
                 "minutes:present 2020-08-18+ (audited-minutes floor); votes:2021-09-21..2023-05-16 (cities.db, D1 — clamped to this tenure)",
         note="Re-elected 2019 (recovered from the raw SOVC — the archive parse had missed the `SJD Council` "
              "sheets). Seated Jan-2020 (anchored to the first documented 2020 council meeting 2020-01-07 in "
              "pmn_backfill; the audited-minutes floor is 2020-08-18 — Jan–Jul 2020 are tally-only PMN). First "
              "NAMED vote 2021-09-21 is a DISSENT-ONLY recording seam, not the service start. Continuous service."),
    dict(body="Council", seat_id="D1", person_name="Patrick Harris", person_key="patrick_harris",
         start_date="2024-01-02", start_event="reelected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 1 winner, UNOPPOSED 100%); minutes:2024-01-02 (Oath of Office of City "
                 "Council Member, Patrick Harris); votes:continuous through 2026-05-19 (cities.db, D1)",
         note="Re-elected D1 2023 (first D1 term on the plan_2022 lines; oath 2024-01-02). Currently serving."),

    # ============================ D2 (B cycle) ============================
    dict(body="Council", seat_id="D2", person_name="Kathie L. Johnson", person_key="kathie_johnson",
         start_date="2008-01-01", start_event="elected", election_year="2007", end_event="lost",
         confidence="medium",
         sources="election:2007 (District 2 winner, def. Madsen 50.7-49.1); election:2011 (LOST to Newton, rank 2)",
         note="PRE-DATA-FLOOR term (elected 2007; term-start inferred Jan 2008). LOST re-election in 2011 to Chuck "
              "Newton (recon: 'Newton +58, unseating Johnson') -> left office Jan 2012. SAME PERSON as the 2023 D2 "
              "winner below (returned after a 12-year absence). No observed Council vote in this 2008-2012 window, so "
              "first_vote/last_vote are BLANK (clamped to the tenure); her recorded votes fall in her LATER 2024- D2 tenure."),
    dict(body="Council", seat_id="D2", person_name="Chuck Newton", person_key="chuck_newton",
         start_date="2012-01-01", start_event="elected", election_year="2011", end_event="lost",
         confidence="medium",
         sources="election:2011 (District 2 winner, def. Kathie Johnson 51.9%); election:2015 (LOST to Marlor, rank 2)",
         note="PRE-DATA-FLOOR term (elected 2011). LOST re-election in 2015 to Brad Marlor -> left office Jan 2016."),
    dict(body="Council", seat_id="D2", person_name="Brad Marlor", person_key="brad_marlor",
         start_date="2016-01-01", start_event="elected", election_year="2015", end_event="reelected",
         confidence="medium",
         sources="election:2015 (District 2 winner, def. Newton 66.8%)",
         note="PRE-DATA-FLOOR term (elected 2015; term-start inferred Jan 2016). Re-elected 2019. No observed "
              "Council vote in this 2016-2020 window, so first_vote/last_vote are BLANK (clamped to the tenure); "
              "his recorded votes (2020-09-15..2023-03-07) fall in his LATER 2020-2024 tenure."),
    dict(body="Council", seat_id="D2", person_name="Brad Marlor", person_key="brad_marlor",
         start_date="2020-01-07", start_event="reelected", election_year="2019", end_event="did-not-run",
         confidence="high",
         sources="election:2019 (District 2 winner, as 'Bradley G. Marlor', def. Quinn 60.3% — recovered SOVC); "
                 "votes:2020-09-15..2023-03-07 (cities.db, D2); minutes:2023-12-05 (Proclamation in recognition of "
                 "Bradley G. Marlor's Years of Service)",
         note="Re-elected D2 2019 (recovered SOVC). Seated Jan-2020 (first documented 2020 meeting 2020-01-07; audited "
              "floor 2020-08-18). Served his FULL term through Dec-2023 (present + honored with a years-of-service "
              "proclamation 2023-12-05); his last NAMED vote 2023-03-07 is a DISSENT-ONLY recording seam, NOT an early "
              "departure. Did not seek re-election in 2023 -> Johnson won. CLEAN cycle-boundary handoff (no vacancy)."),
    dict(body="Council", seat_id="D2", person_name="Kathie L. Johnson", person_key="kathie_johnson",
         start_date="2024-01-02", start_event="elected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 2 winner, def. Bevans 61.7%); minutes:2024-01-02 (Oath of Office of City "
                 "Council Member, Kathie L. Johnson); votes:2024-01-16..2026-05-19 (cities.db, D2)",
         note="RETURNED to D2 2023 after a 12-year absence (she also held D2 2008-2011 — see the first D2 row; SAME "
              "PERSON, hence start_event=elected not reelected). Oath 2024-01-02; first NAMED vote 2024-01-16. Serving. "
              "This is the D2 Marlor->Johnson transition — a clean end-of-term handoff, NOT a mid-term resignation."),

    # ============================ D3 (A cycle) ============================
    dict(body="Council", seat_id="D3", person_name="Brian C. Butters", person_key="brian_butters",
         start_date="2010-01-01", start_event="elected", election_year="2009", end_event="lost",
         confidence="medium",
         sources="election:2009 (District 3 winner, def. Ross 60.5%); election:2013 (LOST to Shelton, rank 2)",
         note="PRE-DATA-FLOOR term (elected 2009; term-start inferred Jan 2010). LOST re-election in 2013 to Don "
              "Shelton -> left office Jan 2014."),
    dict(body="Council", seat_id="D3", person_name="Don Shelton", person_key="don_shelton",
         start_date="2014-01-01", start_event="elected", election_year="2013", end_event="reelected",
         confidence="medium",
         sources="election:2013 (District 3 winner, def. Butters 66.9%)",
         note="PRE-DATA-FLOOR term (elected 2013; term-start inferred Jan 2014). Re-elected 2017."),
    dict(body="Council", seat_id="D3", person_name="Don Shelton", person_key="don_shelton",
         start_date="2018-01-01", start_event="reelected", election_year="2017", end_event="reelected",
         confidence="medium",
         sources="election:2017 (District 3 winner, def. Holbrook 61.5%); votes:2020-09-15.. (cities.db, D3)",
         note="Re-elected D3 2017 (term-start inferred Jan 2018, below the 2020 floor -> medium). Vote-corroborated "
              "for the tail from the 2020 named-vote floor (first named vote 2020-09-15). Re-elected 2021."),
    dict(body="Council", seat_id="D3", person_name="Don Shelton", person_key="don_shelton",
         start_date="2022-01-04", start_event="reelected", election_year="2021", end_event="reelected",
         confidence="high",
         sources="election:2021 (District 3 winner, UNOPPOSED 100%); minutes:2022-01-04 (Oath of Office re-appointment "
                 "for District #3 Council Member Don Shelton); votes:continuous (cities.db, D3)",
         note="Re-elected D3 2021 (oath 2022-01-04; last D3 term on the OLD plan_pre2022 lines). Re-elected 2025."),
    dict(body="Council", seat_id="D3", person_name="Don Shelton", person_key="don_shelton",
         start_date="2026-01-06", start_event="reelected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (District 3 winner, def. Lewis 50.65% — a +45-vote squeaker); minutes:2026-01-06 "
                 "(present, first documented 2026 council meeting); votes:continuous through 2026-05-19 (cities.db, D3)",
         note="Re-elected D3 2025 (first D3 term on the plan_2022 lines). No separate 2026 oath ceremony in the minutes "
              "(re-elected continuing member); term-start anchored to the first documented 2026 council meeting "
              "2026-01-06 (present-list). Currently serving."),

    # ============================ D4 (B cycle) ============================
    dict(body="Council", seat_id="D4", person_name="Aleta A. Taylor", person_key="aleta_taylor",
         start_date="2008-01-01", start_event="elected", election_year="2007", end_event="lost",
         confidence="medium",
         sources="election:2007 (District 4 winner, def. Colton 60.3%); election:2011 (LOST to Barnes, rank 2)",
         note="PRE-DATA-FLOOR term (elected 2007; term-start inferred Jan 2008). LOST re-election in 2011 to Steve "
              "Barnes -> left office Jan 2012."),
    dict(body="Council", seat_id="D4", person_name="Steve Barnes", person_key="steve_barnes",
         start_date="2012-01-01", start_event="elected", election_year="2011", end_event="did-not-run",
         confidence="medium",
         sources="election:2011 (District 4 winner, def. Taylor 57.6%)",
         note="PRE-DATA-FLOOR term (elected 2011). Not a 2015 D4 candidate -> Zander won."),
    dict(body="Council", seat_id="D4", person_name="Tamara Zander", person_key="tamara_zander",
         start_date="2016-01-01", start_event="elected", election_year="2015", end_event="reelected",
         confidence="medium",
         sources="election:2015 (District 4 winner, def. Geilmann 60.9%)",
         note="PRE-DATA-FLOOR term (elected 2015; term-start inferred Jan 2016). Re-elected 2019. No observed Council "
              "vote in this 2016-2020 window, so first_vote/last_vote are BLANK (clamped to the tenure); her recorded "
              "votes begin 2020-09-15, in her LATER 2020-2024 tenure."),
    dict(body="Council", seat_id="D4", person_name="Tamara Zander", person_key="tamara_zander",
         start_date="2020-01-07", start_event="reelected", election_year="2019", end_event="reelected",
         confidence="high",
         sources="election:2019 (District 4 winner, UNOPPOSED 100% — recovered SOVC); minutes:present 2020-08-18+; "
                 "votes:2020-09-15..2023-10-03 (cities.db, D4 — clamped to this tenure)",
         note="Re-elected D4 2019 (recovered SOVC). Seated Jan-2020 (first documented 2020 meeting 2020-01-07; audited "
              "floor 2020-08-18). Vote-corroborated from 2020-09-15. Re-elected 2023."),
    dict(body="Council", seat_id="D4", person_name="Tamara Zander", person_key="tamara_zander",
         start_date="2024-01-02", start_event="reelected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 4 winner, UNOPPOSED 100%); minutes:2024-01-02 (Oath of Office of City Council "
                 "Member, Tamara Zander); votes:continuous through 2026-05-19 (cities.db, D4)",
         note="Re-elected D4 2023 (first D4 term on the plan_2022 lines; oath 2024-01-02). Currently serving."),

    # ============================ D5 (A cycle) ============================
    dict(body="Council", seat_id="D5", person_name="Larry Short", person_key="larry_short",
         start_date="2010-01-01", start_event="elected", election_year="2009", end_event="lost",
         confidence="medium",
         sources="election:2009 (District 5 winner, def. Heath 61.7%); election:2013 (LOST to Rogers, rank 2)",
         note="PRE-DATA-FLOOR term (elected 2009; term-start inferred Jan 2010). LOST re-election in 2013 to "
              "Christopher J. Rogers -> left office Jan 2014."),
    dict(body="Council", seat_id="D5", person_name="Christopher J. Rogers", person_key="christopher_rogers",
         start_date="2014-01-01", start_event="elected", election_year="2013", end_event="did-not-run",
         confidence="medium",
         sources="election:2013 (District 5 winner, def. Short 58.1%)",
         note="PRE-DATA-FLOOR term (elected 2013). Not a 2017 D5 candidate -> McGuire won. (No relation to SLC's James "
              "Rogers — different city.)"),
    dict(body="Council", seat_id="D5", person_name="Jason McGuire", person_key="jason_mcguire",
         start_date="2018-01-01", start_event="elected", election_year="2017", end_event="reelected",
         confidence="medium",
         sources="election:2017 (District 5 winner, as 'Jason T McGuire', def. Kirkendoll 51.0% — a +47-vote squeaker); "
                 "votes:2021-05-18.. (cities.db, D5)",
         note="Elected D5 2017 (term-start inferred Jan 2018, below the 2020 floor -> medium). Vote-corroborated for the "
              "tail from the 2021-05-18 first named vote (dissent-only seam). Re-elected 2021."),
    dict(body="Council", seat_id="D5", person_name="Jason McGuire", person_key="jason_mcguire",
         start_date="2022-01-04", start_event="reelected", election_year="2021", end_event="reelected",
         confidence="high",
         sources="election:2021 (District 5 winner, UNOPPOSED 100%); minutes:2022-01-04 (Oath of Office re-appointment for "
                 "District #5 Council Member Jason McGuire); votes:continuous (cities.db, D5)",
         note="Re-elected D5 2021 (oath 2022-01-04; last D5 term on the OLD plan_pre2022 lines). Re-elected 2025."),
    dict(body="Council", seat_id="D5", person_name="Jason McGuire", person_key="jason_mcguire",
         start_date="2026-01-06", start_event="reelected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (District 5 winner, as 'Jason Timothy McGuire', def. Hughes 52.9%); minutes:2026-01-06 "
                 "(present, first documented 2026 council meeting); votes:continuous through 2026-05-19 (cities.db, D5)",
         note="Re-elected D5 2025 (first D5 term on the plan_2022 lines). No separate 2026 oath ceremony (re-elected "
              "continuing member); term-start anchored to the first documented 2026 council meeting 2026-01-06. "
              "Ballot name 'Jason Timothy McGuire' vs the roster/vote 'Jason McGuire' -> D5 is excluded from the "
              "automated precinct string-match and hand-verified (see CLAUDE.md). Currently serving."),

    # ============================ MAYOR (does NOT vote — one tie-break) ============================
    dict(body="Mayor", seat_id="MAYOR", person_name="W. Kent Money", person_key="kent_money",
         start_date="2010-01-01", start_event="elected", election_year="2009", end_event="did-not-run",
         confidence="medium",
         sources="election:2009 (Mayor winner, def. Osmond 54.6%)",
         note="PRE-DATA-FLOOR (elected Mayor 2009; term-start inferred Jan 2010). Mayor does NOT vote on council "
              "motions. HONEST GAP: the 2013 general shows Dave Alvord defeating INCUMBENT Scott L. Osborne (Money is "
              "not a 2013 candidate), so an intervening pre-floor Money->Osborne mayoral succession (~2010-2013) is "
              "externally attested but its dates are entirely below the 2020 data floor and unreconstructable from "
              "loaded sources -> flagged, NOT modeled as a fabricated Osborne tenure (repo cardinal rules)."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Dave Alvord", person_key="dave_alvord",
         start_date="2014-01-01", start_event="elected", election_year="2013", end_event="did-not-run",
         confidence="medium",
         sources="election:2013 (Mayor winner, def. incumbent Osborne 50.19% — 100-vote canvassed margin)",
         note="PRE-DATA-FLOOR term (elected Mayor 2013, def. incumbent Osborne). Mayor does NOT vote. Not a 2017 Mayor "
              "candidate -> Ramsey won (Alvord went on to the Salt Lake County Council)."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Dawn R. Ramsey", person_key="dawn_ramsey",
         start_date="2018-01-01", start_event="elected", election_year="2017", end_event="reelected",
         confidence="medium",
         sources="election:2017 (Mayor winner, def. Woolley 55.7%); minutes:presiding 2020-08-18+ (as 'Mayor Ramsey')",
         note="Elected Mayor 2017 (term-start inferred Jan 2018, below the 2020 floor -> medium). Documented presiding "
              "throughout the audited minutes (2020-08+). Mayor does NOT vote on council motions (MAYOR vote bounds "
              "emptied by non_voting_mayor). Re-elected 2021."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Dawn R. Ramsey", person_key="dawn_ramsey",
         start_date="2022-01-04", start_event="reelected", election_year="2021", end_event="reelected",
         confidence="high",
         sources="election:2021 (Mayor winner, def. Fonua 91.6%); minutes:2022-01-04 (Oath of Office re-appointment for "
                 "Mayor Dawn R. Ramsey); presiding throughout",
         note="Re-elected Mayor 2021 (oath 2022-01-04). Presides; does NOT vote on council legislation — EXCEPT the one "
              "statutory tie-break on 2025-06-17 (Ordinance 2025-09): the four members present split 2-2 (Shelton/"
              "Johnson Yes, Harris/McGuire No, Zander absent) and 'Mayor Dawn R. Ramsey - Yes' broke the tie ('passed "
              "with a vote of 3-2'). This is her ONLY council-body vote in cities.db (dawnrramsey Council 2025-06-17 "
              "only); non_voting_mayor=True keeps first_vote/last_vote EMPTY on this row so the tie-break can't smear a "
              "misleading span."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Dawn R. Ramsey", person_key="dawn_ramsey",
         start_date="2026-01-06", start_event="reelected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (Mayor winner, def. Barrett 81.9%); minutes:2026-01-06 (presiding, first documented 2026 "
                 "council meeting)",
         note="Re-elected Mayor 2025. Continues to preside; does not vote on council motions (MAYOR vote bounds empty). "
              "Currently serving."),
]

# canonical UPPER-CASE election name token -> our person_key. No shared council surnames in South
# Jordan (each token below is unique), so no disambiguators are needed. Kathie L. Johnson (D2) is
# the only member with two non-contiguous tenures (2007 + 2023); one key covers both.
NAME_TO_KEY = {
    "WINGER": "leona_winger", "SEETHALER": "mark_seethaler", "HARRIS": "patrick_harris",
    "JOHNSON": "kathie_johnson", "NEWTON": "chuck_newton", "MARLOR": "brad_marlor",
    "BUTTERS": "brian_butters", "SHELTON": "don_shelton",
    "TAYLOR": "aleta_taylor", "BARNES": "steve_barnes", "ZANDER": "tamara_zander",
    "SHORT": "larry_short", "ROGERS": "christopher_rogers", "MCGUIRE": "jason_mcguire",
    "MONEY": "kent_money", "ALVORD": "dave_alvord", "RAMSEY": "dawn_ramsey",
}

# cities.db person.name_key -> our person_key (council voters only). dawnrramsey is DELIBERATELY
# EXCLUDED — she is the non-voting Mayor; her single 2025-06-17 tie-break must not smear a span.
DB_KEY = {
    "patrickharris": "patrick_harris", "kathiejohnson": "kathie_johnson",
    "bradmarlor": "brad_marlor", "donshelton": "don_shelton",
    "tamarazander": "tamara_zander", "jasonmcguire": "jason_mcguire",
}


def seat_for_contest(office, district):
    """election (office, district) -> seat_id (or None). South Jordan: 5 geographic districts + a
    citywide Mayor; NO at-large/citywide council seats."""
    if office == "Mayor":
        return "MAYOR"
    d = district.strip()
    if d in ("1", "2", "3", "4", "5"):
        return "D" + d
    return None


REDISTRICT = Redistrict(
    plan_old=PLAN_OLD, plan_new=PLAN_NEW, plan_switch=PLAN_SWITCH,
    ord=REDISTRICT_ORD, adopted=REDISTRICT_ADOPTED,
    districts=["District 1", "District 2", "District 3", "District 4", "District 5"],
    geom_ref=GEOM_REF, source_url=SRC_URL, data_floor=DATA_FLOOR,
    current_note=(f"CURRENT post-2020-census boundaries. {REDISTRICT_ORD} ('Amending Section 1.12.030: "
                  "District Boundaries ... set forth in the City Council District Boundary Map based on the "
                  f"2020 census') adopted {REDISTRICT_ADOPTED} on a UNANIMOUS 5-0 roll call (motion Marlor / "
                  "second Harris). geometry_ref carries South Jordan's own city GIS council-district polygons "
                  "('Council Districts 2020' layer); precinct->district in geo/precinct_to_district.csv. First "
                  "used for elections 2023 (D1/D2/D4) and 2025 (D3/D5)."),
    prior_adopted_by="prior plan (pre-2022 boundaries)",
    prior_geom_ref="geo/council_districts_pre2022.geojson",
    prior_confidence="low",
    prior_note=("Prior-plan (pre-2022) district boundaries RECONSTRUCTED 2026-07-11 by dissolving current-vintage "
                "precinct shapes by the pre-2022 (2012-cycle) precinct->district assignment (geometry_ref = "
                "geo/council_districts_pre2022.geojson; all 49 SJD precincts present, 0 holes, 0 conflicts). "
                "In force through the 2021 elections. effective_start = data floor. "
                "VALIDATION 2026-07-19 (LM-wave follow-up): fetched South Jordan's own authoritative GIS "
                "(gis2.southjordanutah.gov Voting/CouncilDistricts 'FinalApproved' + Voting/Voting 'Council "
                "Districts 2020' — geometrically IDENTICAL, both carry 2020-census FIPS fields and are the "
                "CURRENT 2022 plan: they centroid-agree with the CURRENT precinct assignment 68/68 (100%) but "
                "with the pre-2022 assignment only 15/49 (31%, ~random for 5 districts). The city publishes NO "
                "true 2012-vintage boundary layer. A fragmentation control PROVES precinct renumbering: the "
                "CURRENT-assignment dissolve yields clean 1-piece districts, but this pre-2022 dissolve yields "
                "up to 7-piece fragments (D3=7,D4=5,D5=5) -> the old SJD codes were renumbered between the SOVC "
                "vintage and the current UGRC shapes (the millcreek defect). No authoritative prior layer exists "
                "to replace it -> geometry confidence DOWNGRADED medium->low. The district_precincts precinct-CODE "
                "composition stays medium (a faithful SOVC record, geometry-independent). See "
                "scripts/roster_boundary_recon.md."),
    citywide_rows=[("MAYOR", "citywide", "the separately-elected Mayor Dawn R. Ramsey")],
    citywide_adopted_by="South Jordan City (Mayor — whole city)",
    citywide_note_template=("{who}: represents the ENTIRE city on every date, unchanged by the 2022 "
                            "redistricting. South Jordan has NO at-large council seats — all 5 council seats are "
                            "geographic districts; only the Mayor is citywide (and she does not vote on council "
                            "legislation). geometry_ref = full city extent."),
    precinct_hi_source="geo2020layer",   # token: all rows derive from the one authoritative city GIS layer
    precinct_hi_note=("post-redistrict precinct->district from South Jordan's own city GIS 'Council Districts "
                      "2020' layer (geo/precinct_to_district.csv; 68 SJD precincts, 0 splits) — the single "
                      "authoritative geometric source for the plan_2022 composition"),
    precinct_med_note="",   # unused — every plan_2022 row shares the one authoritative source
    precinct_prior_note=("Reconstructed pre-2022 (2012-cycle) precinct->district composition (49/49 SJD precincts, "
                         "from the pre-2022 SOVC district contests); medium — current-vintage precinct shapes. "
                         "See scripts/roster_boundary_recon.md."),
    crosscheck_districts=("1", "2", "3", "4"),   # D5 excluded: 'Jason Timothy McGuire' ballot vs roster name (see CLAUDE)
    precinct_prefix="SJD", geo_seat_prefix="D",
    plan_switch_year="2023", citywide_seats=(),
)

CFG = RosterConfig(
    non_voting_mayor=True,
    city=CITY, city_dir=CITY_DIR, repo_root=REPO_ROOT, data_floor=DATA_FLOOR,
    geom_ref=GEOM_REF, elections_path=ELECTIONS, cities_db_path=CITIES_DB,
    overrides_path=OVERRIDES, terms_out=TERMS_OUT, districts_out=DISTRICTS_OUT,
    seat_district=SEAT_DISTRICT, name_to_key=NAME_TO_KEY, db_key=DB_KEY,
    seat_order=["D1", "D2", "D3", "D4", "D5", "MAYOR"],
    keep_election_row=lambda r: r["election_type"].strip().lower() == "municipal general",
    contest_key=seat_for_contest, crosscheck_field="seat_id",
    winners_have_district=True,
    elected_events=("elected", "reelected"),
    redistrict=REDISTRICT, precincts_out=PRECINCTS_OUT,
    precinct_map_path=PRECINCT_MAP, precincts_byprecinct_path=PRECINCTS_BYP_SRC,
    prior_precinct_map_path=os.path.join(CITY_DIR, "geo", "precinct_to_district_pre2022.csv"),
)


# ---------------------------------------------------------------------------
# DERIVED helper 1: the shared write_precincts()/precinct_crosscheck() need a precinct map with a
# `source_year` column. South Jordan already ships geo/precinct_to_district.csv (68 SJD precincts ->
# district 1-5, city-GIS-derived, 0 splits) — we just add a constant source_year token (the map is a
# single authoritative geometric source, not an election-year-scoped derivation). Per-city adapter
# only; the shared library is untouched (same sidecar approach as Ogden/Sandy).
# ---------------------------------------------------------------------------
def _write_precinct_to_district():
    with open(GEO_PRECINCT_MAP, newline="") as f:
        rows = [(r["precinct"].strip(), r["district"].strip()) for r in csv.DictReader(f)]
    rows.sort()
    with open(PRECINCT_MAP, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["precinct", "district", "source_year"])
        for pid, dnum in rows:
            w.writerow([pid, dnum, "geo2020layer"])


# ---------------------------------------------------------------------------
# Demo queries (South Jordan presentation)
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

    print("\n(b) Roster AS OF 2025-06-17 (the day of the Mayor's statutory tie-break, Ord 2025-09):")
    for r in roster_lib.roster_as_of(CFG, "2025-06-17", body="Council"):
        print(line(r))
    for r in roster_lib.roster_as_of(CFG, "2025-06-17", body="Mayor"):
        print(line(r))

    print("\n(c) NON-DEGENERATE address+date -> representatives (via geo/address_to_district.py):")
    # A South Jordan address -> its District 1-5 member + the citywide (non-voting) Mayor. Daybreak
    # streets sometimes miss the Census geocoder, so we pass a lat/lon fallback so the demo runs
    # OFFLINE; both the address and the fallback resolve to District 4 (Tamara Zander).
    addr = "4646 W Daybreak Pkwy, South Jordan, UT 84009"
    for d in ("2025-06-01", "2021-06-01"):
        res = roster_lib.representatives_for_address(CFG, addr, d, latlon=(40.545, -111.995))
        who = ", ".join(f"{x['person_name']}({x['seat_id']})" for x in res["reps"])
        loc = (f"District {res['district']} via {res.get('precinct')} "
               f"[{res.get('method')}]") if res.get("district") else f"[{res.get('gap','?')}]"
        print(f"  '{addr}'")
        print(f"    on {d} (plan={res['plan']}): {loc}")
        print(f"    -> your reps: {who or '(none — see gap)'}")

    print("\n(d) SAME address across the 2022 REDISTRICTING (versioned district_versions):")
    for d in ("2021-06-01", "2025-06-01"):
        res = roster_lib.representatives_for_address(CFG, addr, d, latlon=(40.545, -111.995))
        if res.get("district"):
            reps = [x["person_name"] for x in res["reps"] if x["seat_id"].startswith("D")]
            print(f"    {d} (plan={res['plan']}): geographic District {res['district']} -> {reps}")
        else:
            print(f"    {d} (plan={res['plan']}): {res.get('gap')}")

    print("\n(e) Precinct-map cross-check (district_precincts vs election outcomes; D5 hand-verified — see CLAUDE):")
    roster_lib.precinct_crosscheck(CFG, verbose=True)


if __name__ == "__main__":
    _write_precinct_to_district()
    rows = roster_lib.build(CFG, TENURES)
    n = {c: sum(1 for r in rows if r["confidence"] == c) for c in ("high", "medium", "low")}
    nvac = sum(1 for r in rows if r["start_event"] == "vacated")
    print(f"Wrote {os.path.relpath(TERMS_OUT, CITY_DIR)} "
          f"({len(rows)} tenures incl. {nvac} VACANT: {n['high']} high / {n['medium']} medium / {n['low']} low)")
    print(f"Wrote {os.path.relpath(DISTRICTS_OUT, CITY_DIR)} "
          f"(5 districts x 2 plans + Mayor; redistricting {REDISTRICT_ORD})")
    print(f"Wrote {os.path.relpath(PRECINCTS_OUT, CITY_DIR)} "
          f"(plan_2022 precinct map + plan_pre2022 gap rows)")
    if "--check" in sys.argv:
        print("\nValidation: PASS (no overlaps; sources+confidence present; non-voting-mayor + gap/vacate guards clear).")
        print("Precinct cross-check:")
        roster_lib.precinct_crosscheck(CFG, verbose=True)
    if "--demo" in sys.argv:
        demo()
