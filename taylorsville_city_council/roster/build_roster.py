#!/usr/bin/env python3
"""build_roster.py — rolling council-roster for TAYLORSVILLE (a slowly-changing-dimension /
interval table of who holds each council + mayor seat over time). Taylorsville is a
**PURE-DISTRICT** Council-Mayor (executive-mayor) city: **5 geographic council districts**
(D1..D5, NO at-large/citywide council seats) + a **separately-elected executive Mayor who does
NOT vote** on council legislation (she is the executive; the council elects its own Chair/
Vice-Chair from the five members to conduct meetings). Council votes exist from **2020** (named
roll-calls; the majority is honestly UNNAMED on unanimous motions — narrative-tally minutes),
while the Salt Lake County election record runs **2007+**. The 5 districts were **redrawn after
the 2020 Census** (Resolution No. 22-11, adopted 2022-05-04).

THIN DRIVER: this file holds only Taylorsville-specific DATA (the curated TENURES, the name maps,
the 2022-redistricting facts + prose) + config; all generic mechanics live in
../../scripts/roster_lib.py (canon_key, election/vote-bounds/override reconciliation, end-date
chaining + VACANT insertion, validation incl. the gap/vacate guards, the CSV writers, and the
as-of / address / precinct-crosscheck query helpers). The DISTRICT reference template is
south_jordan_city_council/roster/build_roster.py (pure 5 districts + non-voting mayor +
redistricting + precinct + address-join).

DERIVED LAYER — regenerable, never hand-edited. Canonical inputs:
  1. election_results/taylorsville_results_by_candidate.csv (winners -> `elected`/`reelected`; 2007+)
  2. cities.db  role table (city='taylorsville', body='Council')  (observed vote bounds)
  3. meeting_minutes/minutes/**  (oath dates, the redistricting resolution, member departures)
  4. roster/roster_overrides.csv  (hand corrections; applied LAST, win ties)

Outputs (idempotent — re-running reproduces them byte-for-byte):
  roster/council_terms.csv        one row per seat-tenure (5 district seats + MAYOR)
  roster/district_versions.csv    boundary interval table — REAL 5 districts x 2 plans + Mayor
  roster/district_precincts.csv   versioned precinct->district composition (plan-scoped)
  (The two per-city precinct SIDECARS — _precinct_to_district.csv + _precinct_votes.csv — were
   RETIRED 2026-07-11: roster_lib now reads the canonical geo/precinct_to_district.csv and
   election_results/*_results_by_precinct.csv directly (multi-year precinct_hi_source +
   blank/suppressed vote guard), so no collapse/clean sidecar is needed.)

Usage:
  python3 roster/build_roster.py            # regenerate the CSVs
  python3 roster/build_roster.py --demo     # regenerate + print the demo queries
  python3 roster/build_roster.py --check    # regenerate + validations + precinct cross-check

Cardinal rule (repo CLAUDE.md): NEVER fabricate. Unknown seat-holder / boundary / date ->
explicit VACANT/gap + confidence + a note, never a guess.

Provenance / confidence model (Taylorsville):
  high   = a documented Jan oath (2022-01-05 / 2024-01-03 / 2026-01-07 swearing-in ceremonies)
           or a documented in-window appointment/departure (the 2020 Christopherson->Barbieri D3
           chain), corroborated by the cities.db named-vote record.
  medium = an election-anchored term that PREDATES the 2020 data floor (no minutes/vote
           corroboration for its start — the win is a fact, continuous service is inferred from the
           election chain), incl. every pre-2018 term-start (inferred YYYY-01-01) and the 2017-cycle
           terms whose Jan-2018 start is inferred (their tail IS vote-corroborated from 2020).
  low    = genuinely unknown / not-acquired (flagged) — now ONLY the one D2 2018-2020 interim-appointee
           VACANT (Overson vacated D2 to become Mayor; the below-floor interim holder is undocumented).
           The prior-plan district/precinct rows were RECONSTRUCTED to `medium` 2026-07-11 (approximate;
           see the Redistrict prior_note / scripts/roster_boundary_recon.md).

Taylorsville seat model (STABLE ids — a redistricting redraws boundaries, it does NOT renumber
seats):
  D1..D5  five geographic district seats     MAYOR  separately-elected executive mayor (does NOT vote)
Staggered 4-year cycles (odd calendar years):
  A  Mayor + D4 + D5   elected 2009/13/17/21/25  -> terms seated Jan 2010/14/18/22/26
  B  D1 + D2 + D3       elected 2007/11/15/19/23  -> terms seated Jan 2008/12/16/20/24

KNOWN nuances handled honestly (never fabricated around):
  * NON-VOTING EXECUTIVE MAYOR. Taylorsville uses Utah's council-mayor (executive-mayor) form: the
    Mayor is the executive and does NOT vote on council motions; the council elects its own Chair
    from the five district members to conduct meetings. A full council roll call tops out at 5.
    Mayor Kristie Overson appears in ZERO vote rows and is absent from the cities.db person table.
    `non_voting_mayor=True` empties every MAYOR-body vote-bound. Verified: the only distinct named
    voters in all_votes.csv are the seven district members (2020-06-17 Ord 20-14 deny roll call is
    a 4-1 with exactly Armstrong/Burgess/Harker/Christopherson/Cochran named, Mayor Overson absent
    from the vote though she led the Pledge — see roster/CLAUDE.md for the verbatim quote).
  * TWO councilmember->Mayor CROSSOVERS. (1) Larry Johnson: D5 (elected 2009) -> Mayor (elected
    2013) — a CLEAN term-boundary handoff (D5 term ended Jan 2014 exactly as his Mayor term began;
    Armstrong won D5 2013). (2) Kristie Overson: D2 (elected 2011 & 2015) -> Mayor (elected 2017) —
    she vacated D2 ~2 years EARLY (sworn Mayor Jan 2018 mid her 2016-2020 D2 term). Both are entirely
    BELOW the 2020 data floor, so neither person has any council vote in cities.db; their MAYOR rows
    are emptied by the flag and their (pre-floor) council rows carry empty vote bounds naturally.
  * THE IN-WINDOW D3 VACANCY (the headline documented case). Brad Christopherson (D3, re-elected 2019)
    DEPARTED mid-term after the 2020-08-19 meeting (his last day served / last cities.db vote) — the
    minutes describe a MOVE OUTSIDE Taylorsville (residency-loss; 'resign' never appears), and
    end_event='resigned' is the coarse normalized 'left the seat mid-term' bucket. The council
    took applications (deadline 2020-09-09), interviewed on 2020-09-30, and appointed **Anna Barbieri**
    by **Ordinance No. 20-17** that same night ("Barbieri had become a member of the city council
    immediately upon approval of Ordinance 20-17"); she was formally sworn 2020-10-07. She then won
    the **2021 D3 SPECIAL** (unexpired-term balance, uncontested) and the **2023 D3** full term. This
    yields an explicit VACANT interval D3 [2020-08-20, 2020-09-30).
  * TWO out-of-cycle D3 SPECIALS. D3 is a B-cycle seat (2007/11/15/19/23), so a D3 contest in an
    A-cycle year is a special filling an unexpired term: (a) 2013 D3 — the 2011 D3 winner Rechtenbach
    ran for Mayor 2013 (lost) and vacated D3; Christopherson won the balance. (b) 2021 D3 — see above.
  * NARRATIVE-TALLY vote naming. On unanimous council motions the majority is honestly UNNAMED
    (mover + seconder named, tally printed) — so a member's first/last NAMED vote can lag/precede
    their real service. The authoritative interval is always start_date/end_date, not the vote bounds.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.dirname(HERE)                 # taylorsville_city_council/
REPO_ROOT = os.path.dirname(CITY_DIR)            # civic-data/
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import roster_lib
from roster_lib import RosterConfig, Redistrict

ELECTIONS = os.path.join(CITY_DIR, "election_results", "taylorsville_results_by_candidate.csv")
PRECINCTS_BYP_SRC = os.path.join(CITY_DIR, "election_results", "taylorsville_results_by_precinct.csv")
GEO_PRECINCT_MAP = os.path.join(CITY_DIR, "geo", "precinct_to_district.csv")
CITIES_DB = os.path.join(REPO_ROOT, "cities.db")
OVERRIDES = os.path.join(HERE, "roster_overrides.csv")
TERMS_OUT = os.path.join(HERE, "council_terms.csv")
DISTRICTS_OUT = os.path.join(HERE, "district_versions.csv")
PRECINCTS_OUT = os.path.join(HERE, "district_precincts.csv")

CITY = "taylorsville"
DATA_FLOOR = "2020-01-01"            # data floor (city standard: 2020)
GEOM_REF = "geo/council_districts.geojson"

# The real redistricting event (spot-checked against source minutes 2022-05-04):
#   Resolution No. 22-11, "A Resolution of the City of Taylorsville adopting Final Redistricting Maps
#   Pursuant to the Requirements of Utah Code Annotated 10-3-205.5(2)(b)(ii)." Adopted 2022-05-04 on
#   a 4-1 roll call (motion Harker / second Burgess; Cochran No): 60,448 residents / ~12,100 per
#   district, "0% deviation," lines drawn NOT to dissect voting precincts. First used for the 2023
#   (B: D1/D2/D3) and 2025 (A: D4/D5) elections; the 2021 election used the prior lines. (Taylorsville
#   redistricts by RESOLUTION — like SLC/Sandy, unlike South Jordan's ordinance.)
REDISTRICT_ORD = "Resolution 22-11"
REDISTRICT_ADOPTED = "2022-05-04"
PLAN_OLD = "plan_pre2022"   # pre-2022 boundaries, in force through the 2021 elections (RECONSTRUCTED 2026-07-11, medium)
PLAN_NEW = "plan_2022"      # Resolution 22-11; in force for the 2023 election onward
PLAN_SWITCH = "2022-05-04"  # documented adoption of the 2020-census boundaries
SRC_URL = ("meeting_minutes/minutes/2022/2022-05-02/2022-05-04_city-council.md "
           "(Public Hearing + Resolution No. 22-11 adopting Final Redistricting Maps, Utah Code "
           "10-3-205.5); city news /Home/Components/News/News/496/")

SEAT_DISTRICT = {
    "D1": "District 1", "D2": "District 2", "D3": "District 3", "D4": "District 4",
    "D5": "District 5", "MAYOR": "Citywide",
}

# ---------------------------------------------------------------------------
# LAYER 1-3 (reconciled). Each tenure anchored to a cited source. Ordered by seat.
#   Documented seating dates: 2020-01-08 (first documented 2020 council meeting; cities.db first_seen
#   for the 2019-cycle members), 2022-01-05 (oath, 2021-cycle A: D3/D4/D5), 2024-01-03 (oath,
#   2023-cycle B: D1/D2/D3), 2026-01-07 (oath, 2025-cycle A: Mayor/D4/D5). Pre-2020-floor term-starts
#   use YYYY-01-01 (inferred from the stagger -> medium). The 2020-09-30 D3 appointment (Ord 20-17) is
#   a documented in-window seating.
# ---------------------------------------------------------------------------
TENURES = [
    # ============================ D1 (B cycle) ============================
    dict(body="Council", seat_id="D1", person_name="D.L. 'Bud' Catlin", person_key="dl_catlin",
         start_date="2008-01-01", start_event="elected", election_year="2007", end_event="did-not-run",
         confidence="medium",
         sources="election:2007 (District 1 winner, def. Gidney 65.1%)",
         note="PRE-DATA-FLOOR (elected 2007; earliest D1 tenure). Term-start inferred Jan 2008 from the "
              "B-cycle stagger; continuous service inferred from the election chain (not verifiable below "
              "the 2020 data floor). Not a 2011 D1 candidate -> Burgess won."),
    dict(body="Council", seat_id="D1", person_name="Ernest Glen Burgess", person_key="ernest_burgess",
         start_date="2012-01-01", start_event="elected", election_year="2011", end_event="reelected",
         confidence="medium",
         sources="election:2011 (District 1 winner, def. Grossman 53.1% — a +70-vote squeaker; also won the "
                 "2011 primary +17)",
         note="PRE-DATA-FLOOR term (elected 2011; term-start inferred Jan 2012). Re-elected 2015. "
              "first_vote/last_vote are BLANK on this row: the per-tenure vote clamp finds no Council "
              "vote inside this 2012-2016 window (his earliest named cities.db votes, 2020-01-08+, fall "
              "in a LATER term)."),
    dict(body="Council", seat_id="D1", person_name="Ernest Glen Burgess", person_key="ernest_burgess",
         start_date="2016-01-01", start_event="reelected", election_year="2015", end_event="reelected",
         confidence="medium",
         sources="election:2015 (District 1 winner, def. Grossman 63.3%)",
         note="PRE-DATA-FLOOR term (elected 2015; term-start inferred Jan 2016). Re-elected 2019. Vote-"
              "corroborated for the tail from the 2020-01-08 named-vote floor."),
    dict(body="Council", seat_id="D1", person_name="Ernest Glen Burgess", person_key="ernest_burgess",
         start_date="2020-01-08", start_event="reelected", election_year="2019", end_event="reelected",
         confidence="high",
         sources="election:2019 (District 1 winner, def. Gehrke 63.6% — recovered from the raw SOVC, see "
                 "election_results); minutes:present 2020-01-08 (first documented 2020 council meeting); "
                 "votes:2020-01-08..2026-06-03 (cities.db, D1)",
         note="Re-elected D1 2019 (last D1 term on the OLD plan_pre2022 lines). Seated 2020-01-08 (first "
              "documented 2020 council meeting). Continuous service to present. Re-elected 2023."),
    dict(body="Council", seat_id="D1", person_name="Ernest Glen Burgess", person_key="ernest_burgess",
         start_date="2024-01-03", start_event="reelected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 1 winner, def. Sanok 64.7%); minutes:2024-01-03 (swearing-in "
                 "ceremony — 'Council members Barbieri, Burgess, and Cochran had all been reelected ... The "
                 "oath of office was administered to all three'); votes:continuous through 2026-06-03 (cities.db, D1)",
         note="Re-elected D1 2023 (first D1 term on the plan_2022 lines; oath 2024-01-03). Currently serving. "
              "Ballot name 'ERNEST GLEN BURGESS' vs roster 'Ernest Glen Burgess' — D1 is excluded from the "
              "automated precinct string-match (middle name) and hand-verified (see CLAUDE.md)."),

    # ============================ D2 (B cycle) ============================
    dict(body="Council", seat_id="D2", person_name="Morris K. Pratt", person_key="morris_pratt",
         start_date="2008-01-01", start_event="elected", election_year="2007", end_event="lost",
         confidence="medium",
         sources="election:2007 (District 2 winner, 97.7% vs Write-in); election:2011 (LOST to Overson, rank 2)",
         note="PRE-DATA-FLOOR term (elected 2007; term-start inferred Jan 2008). LOST re-election in 2011 to "
              "Kristie Overson -> left office Jan 2012."),
    dict(body="Council", seat_id="D2", person_name="Kristie Steadman Overson", person_key="kristie_overson",
         start_date="2012-01-01", start_event="elected", election_year="2011", end_event="reelected",
         confidence="medium",
         sources="election:2011 (District 2 winner, def. Pratt 59.9%)",
         note="PRE-DATA-FLOOR term (elected 2011; term-start inferred Jan 2012). Re-elected 2015. SAME PERSON "
              "as the Mayor below — she moved up to Mayor in 2018 (COUNCILMEMBER->MAYOR CROSSOVER; see the "
              "next D2 row and the MAYOR block)."),
    dict(body="Council", seat_id="D2", person_name="Kristie Steadman Overson", person_key="kristie_overson",
         start_date="2016-01-01", start_event="reelected", election_year="2015", end_event="resigned-to-mayor",
         confidence="medium",
         vacate_date="2018-01-01", vacate_confidence="medium",
         vacate_source="election:2017 (won Mayor, def. incumbent Mayor Larry Johnson 57.2%) — sworn Mayor Jan 2018",
         sources="election:2015 (District 2 winner, def. Spencer 76.5%)",
         note="PRE-DATA-FLOOR term (elected 2015; term-start inferred Jan 2016; D2 term ran 2016-2020). "
              "COUNCILMEMBER->MAYOR CROSSOVER: Overson won the 2017 Mayor race and was sworn Mayor ~Jan 2018, "
              "VACATING D2 ~2 years early. Her D2 tenure ends 2018-01-01 (no overlap with her MAYOR tenure, which "
              "begins the same day). The below-floor interim D2 holder (2018-2020) is undocumented -> an explicit "
              "low-confidence VACANT interval (see roster_overrides.csv), NOT a fabricated appointee."),
    dict(body="Council", seat_id="D2", person_name="Curt Cochran", person_key="curt_cochran",
         start_date="2020-01-08", start_event="elected", election_year="2019", end_event="reelected",
         confidence="high",
         sources="election:2019 (District 2 winner, def. McElreath 60.6% — recovered from the raw SOVC); "
                 "minutes:present 2020-01-08 (first documented 2020 council meeting); votes:2020-01-08.."
                 "2026-06-03 (cities.db, D2)",
         note="Elected D2 2019 (the 2019 general is the REGULAR B-cycle D2 election — its new term begins exactly "
              "when Overson's unexpired 2016-2020 term ends, so no special was needed). Seated 2020-01-08 (last D2 "
              "term on the OLD plan_pre2022 lines). Re-elected 2023."),
    dict(body="Council", seat_id="D2", person_name="Curt Cochran", person_key="curt_cochran",
         start_date="2024-01-03", start_event="reelected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 2 winner, uncontested 100%); minutes:2024-01-03 (swearing-in ceremony, "
                 "oath administered to Barbieri/Burgess/Cochran); votes:continuous through 2026-06-03 (cities.db, D2)",
         note="Re-elected D2 2023 (first D2 term on the plan_2022 lines; oath 2024-01-03). Currently serving."),

    # ============================ D3 (B cycle + TWO specials + the in-window vacancy) ============================
    dict(body="Council", seat_id="D3", person_name="Jerry W. Rechtenbach", person_key="jerry_rechtenbach",
         start_date="2008-01-01", start_event="elected", election_year="2007", end_event="reelected",
         confidence="medium",
         sources="election:2007 (District 3 winner, 98.0% vs Write-in)",
         note="PRE-DATA-FLOOR term (elected 2007; term-start inferred Jan 2008). Re-elected 2011."),
    dict(body="Council", seat_id="D3", person_name="Jerry W. Rechtenbach", person_key="jerry_rechtenbach",
         start_date="2012-01-01", start_event="reelected", election_year="2011", end_event="ran-for-mayor-lost",
         confidence="medium",
         sources="election:2011 (District 3 winner, def. Ballou 60.0%); election:2013 (LOST Mayor to Larry "
                 "Johnson, rank 2)",
         note="PRE-DATA-FLOOR term (elected 2011; D3 term 2012-2016). Ran for MAYOR in 2013 and LOST (2013 Mayor "
              "runner-up), VACATING D3; Brad Christopherson won the 2013 D3 SPECIAL for the unexpired balance "
              "(seated Jan 2014). Left office Jan 2014."),
    dict(body="Council", seat_id="D3", person_name="Brad Christopherson", person_key="brad_christopherson",
         start_date="2014-01-01", start_event="elected", election_year="2013", end_event="reelected",
         confidence="medium",
         sources="election:2013 (District 3 SPECIAL winner, uncontested 99.0% — balance of Rechtenbach's "
                 "unexpired term)",
         note="PRE-DATA-FLOOR term (won the 2013 D3 SPECIAL for the unexpired balance; term-start inferred Jan "
              "2014). Re-elected to the full term 2015. The 2013 D3 contest is an out-of-cycle special (D3 is a "
              "B-cycle seat) — not a permanent cycle shift."),
    dict(body="Council", seat_id="D3", person_name="Brad Christopherson", person_key="brad_christopherson",
         start_date="2016-01-01", start_event="reelected", election_year="2015", end_event="reelected",
         confidence="medium",
         sources="election:2015 (District 3 winner, def. Morley 74.7%)",
         note="PRE-DATA-FLOOR term (elected 2015; term-start inferred Jan 2016). Re-elected 2019. first_vote/"
              "last_vote are BLANK on this row: the per-tenure vote clamp finds no Council vote inside this "
              "2016-2020 window (his named cities.db votes, 2020-01-08..2020-08-19, fall in his NEXT term)."),
    dict(body="Council", seat_id="D3", person_name="Brad Christopherson", person_key="brad_christopherson",
         start_date="2020-01-08", start_event="reelected", election_year="2019", end_event="resigned",
         confidence="high",
         vacate_date="2020-08-20", vacate_confidence="high",  # VACANT begins the day AFTER his last day served (2020-08-19)
         vacate_source="minutes:2020-08-19 (his last meeting served — Council/Chief recognized 'Vice Chair "
                       "Christopherson'; Mayor 'expressed her very best wishes'; last cities.db D3 vote 2020-08-19); "
                       "2020-09-02 minutes note 'The District No. 3 council seat was temporarily vacant'",
         sources="election:2019 (District 3 winner, uncontested 100%); minutes:present 2020-01-08..2020-08-19; "
                 "votes:2020-01-08..2020-08-19 (cities.db, D3)",
         note="Re-elected D3 2019 (seated 2020-01-08). DEPARTED mid-term after the 2020-08-19 meeting (his last day "
              "served / last recorded vote): the minutes describe a MOVE OUTSIDE Taylorsville (a residency-loss "
              "vacancy — the word 'resign' does not appear); end_event='resigned' is the coarse normalized "
              "'left the seat mid-term' bucket, the faithful reason lives here in the note (repo cardinal rule #2). "
              "The council opened applications (deadline 2020-09-09) and interviewed/appointed on 2020-09-30 -> "
              "explicit VACANT interval D3 [2020-08-20, 2020-09-30). Documented in-window departure."),
    dict(body="Council", seat_id="D3", person_name="Anna Barbieri", person_key="anna_barbieri",
         start_date="2020-09-30", start_event="appointed", election_year="", end_event="elected",
         confidence="high",
         sources="minutes:2020-09-30 (SPECIAL meeting — Ordinance No. 20-17 'appointing Anna Barbieri to represent "
                 "District No. 3 on the City Council'; motion Armstrong; 'Barbieri had become a member of the city "
                 "council immediately upon approval of Ordinance 20-17'); minutes:2020-10-07 (formal Swearing-In "
                 "Ceremony, oath administered); votes:2020-10-07.. (cities.db, D3, first named vote)",
         note="APPOINTED to the D3 vacancy 2020-09-30 by Ordinance No. 20-17 (became a member immediately upon "
              "approval; formal oath 2020-10-07). Serves the appointment through the 2021 special. She also sat on "
              "the Planning Commission earlier (a single person with two body roles — see the db). Her first NAMED "
              "cities.db vote is 2020-10-07."),
    dict(body="Council", seat_id="D3", person_name="Anna Barbieri", person_key="anna_barbieri",
         start_date="2022-01-05", start_event="elected", election_year="2021", end_event="reelected",
         confidence="high",
         sources="election:2021 (District 3 SPECIAL winner, uncontested 100% — unexpired-term balance); "
                 "minutes:2022-01-05 (Swearing In of Elected Officials, oath administered to 'Anna Barbieri – "
                 "Council District No. 3'); votes:continuous (cities.db, D3)",
         note="Won the 2021 D3 SPECIAL (uncontested, unexpired-term balance of Christopherson's 2019 term); oath "
              "2022-01-05. The 2021 D3 contest is an out-of-cycle special (D3 is a B-cycle seat) — not a permanent "
              "cycle shift. Re-elected to the full term 2023."),
    dict(body="Council", seat_id="D3", person_name="Anna Barbieri", person_key="anna_barbieri",
         start_date="2024-01-03", start_event="reelected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 3 winner, uncontested 100%); minutes:2024-01-03 (swearing-in ceremony, "
                 "oath administered to Barbieri/Burgess/Cochran); votes:continuous through 2026-06-03 (cities.db, D3)",
         note="Re-elected D3 2023 (first full D3 term on the plan_2022 lines; oath 2024-01-03). Currently serving."),

    # ============================ D4 (A cycle) ============================
    dict(body="Council", seat_id="D4", person_name="Dama Barbour", person_key="dama_barbour",
         start_date="2010-01-01", start_event="elected", election_year="2009", end_event="reelected",
         confidence="medium",
         sources="election:2009 (District 4 winner, def. Rogers 66.4%)",
         note="PRE-DATA-FLOOR term (elected 2009; earliest D4 tenure; term-start inferred Jan 2010). Re-elected 2013."),
    dict(body="Council", seat_id="D4", person_name="Dama Barbour", person_key="dama_barbour",
         start_date="2014-01-01", start_event="reelected", election_year="2013", end_event="did-not-run",
         confidence="medium",
         sources="election:2013 (District 4 winner, def. aggregate Write-in 58.8% and reg. write-in Wendel — a "
                 "genuine write-in contest)",
         note="PRE-DATA-FLOOR term (elected 2013). Not a 2017 D4 candidate -> Harker won -> left office Jan 2018."),
    dict(body="Council", seat_id="D4", person_name="Meredith Harker", person_key="meredith_harker",
         start_date="2018-01-01", start_event="elected", election_year="2017", end_event="reelected",
         confidence="medium",
         sources="election:2017 (District 4 winner, def. Allred 62.2%); votes:2020-01-08.. (cities.db, D4)",
         note="Elected D4 2017 (term-start inferred Jan 2018, below the 2020 floor -> medium). Vote-corroborated "
              "for the tail from the 2020-01-08 named-vote floor. Re-elected 2021. (Council Chair in the current term.)"),
    dict(body="Council", seat_id="D4", person_name="Meredith Harker", person_key="meredith_harker",
         start_date="2022-01-05", start_event="reelected", election_year="2021", end_event="reelected",
         confidence="high",
         sources="election:2021 (District 4 winner, uncontested 100%); minutes:2022-01-05 (Swearing In of Elected "
                 "Officials, oath administered to 'Meredith Harker – Council District No. 4'); votes:continuous (cities.db, D4)",
         note="Re-elected D4 2021 (oath 2022-01-05; last D4 term on the OLD plan_pre2022 lines). Re-elected 2025."),
    dict(body="Council", seat_id="D4", person_name="Meredith Harker", person_key="meredith_harker",
         start_date="2026-01-07", start_event="reelected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (District 4 winner, def. Munoz 56.0%); minutes:2026-01-07 (Administration of Oath "
                 "of Office to Mayor Overson and Council Members Harker [and Knudsen]); votes:continuous through "
                 "2026-06-03 (cities.db, D4)",
         note="Re-elected D4 2025 (first D4 term on the plan_2022 lines; oath 2026-01-07). Currently serving (Council Chair)."),

    # ============================ D5 (A cycle) ============================
    dict(body="Council", seat_id="D5", person_name="Larry Johnson", person_key="larry_johnson",
         start_date="2010-01-01", start_event="elected", election_year="2009", end_event="became-mayor",
         confidence="medium",
         sources="election:2009 (District 5 winner, def. Handy 57.7%); election:2013 (won Mayor, def. Rechtenbach 53.5%)",
         note="PRE-DATA-FLOOR term (elected D5 2009; earliest D5 tenure; term-start inferred Jan 2010). "
              "COUNCILMEMBER->MAYOR CROSSOVER: won the 2013 Mayor race; his D5 term ended Jan 2014 exactly as his "
              "Mayor term began (CLEAN term-boundary handoff — Armstrong won D5 2013 and was seated Jan 2014, so no "
              "vacancy). SAME PERSON as the 2013/17 Mayor rows and the 2021 D5 loser (see below)."),
    dict(body="Council", seat_id="D5", person_name="Dan Armstrong", person_key="dan_armstrong",
         start_date="2014-01-01", start_event="elected", election_year="2013", end_event="reelected",
         confidence="medium",
         sources="election:2013 (District 5 winner, def. Acker 53.3% — a +103 general after LOSING the primary to "
                 "Acker)",
         note="PRE-DATA-FLOOR term (elected 2013; term-start inferred Jan 2014). Re-elected 2017."),
    dict(body="Council", seat_id="D5", person_name="Dan Armstrong", person_key="dan_armstrong",
         start_date="2018-01-01", start_event="reelected", election_year="2017", end_event="did-not-run",
         confidence="medium",
         sources="election:2017 (District 5 winner, def. Fuller 66.2%); votes:2020-01-08..2021-12-15 (cities.db, D5)",
         note="Re-elected D5 2017 (term-start inferred Jan 2018, below the 2020 floor -> medium; D5 term 2018-2022). "
              "Vote-corroborated for the tail from 2020-01-08 through his last vote 2021-12-15. Did not seek "
              "re-election in 2021 -> Knudsen won. CLEAN cycle-boundary handoff (no vacancy)."),
    dict(body="Council", seat_id="D5", person_name="Bob Knudsen", person_key="bob_knudsen",
         start_date="2022-01-05", start_event="elected", election_year="2021", end_event="reelected",
         confidence="high",
         sources="election:2021 (District 5 winner, def. former Mayor Larry Johnson 52.6%, margin 89); minutes:"
                 "2022-01-05 (Swearing In of Elected Officials, oath administered to 'Bob Knudsen – Council "
                 "District No. 5'); votes:2022-01-05..2026-06-03 (cities.db, D5)",
         note="Elected D5 2021 (def. former Mayor Larry Johnson; oath 2022-01-05; last D5 term on the OLD "
              "plan_pre2022 lines). Re-elected 2025. (Council Vice Chair, later Chair in the current term.)"),
    dict(body="Council", seat_id="D5", person_name="Bob Knudsen", person_key="bob_knudsen",
         start_date="2026-01-07", start_event="reelected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (District 5 winner, def. Schulte 56.7%); minutes:2026-01-07 (Administration of "
                 "Oath of Office; 'Knudsen had been elected to serve as Chair'); votes:continuous through "
                 "2026-06-03 (cities.db, D5)",
         note="Re-elected D5 2025 (first D5 term on the plan_2022 lines; oath 2026-01-07). Currently serving; "
              "elected Council Chair for the term."),

    # ============================ MAYOR (executive — does NOT vote) ============================
    dict(body="Mayor", seat_id="MAYOR", person_name="Russ Wall", person_key="russ_wall",
         start_date="2010-01-01", start_event="elected", election_year="2009", end_event="did-not-run",
         confidence="medium",
         sources="election:2009 (Mayor winner, def. Whyte 63.6%)",
         note="PRE-DATA-FLOOR (elected Mayor 2009; earliest Mayor tenure; term-start inferred Jan 2010). Executive "
              "Mayor does NOT vote on council motions. Not a 2013 Mayor candidate -> Larry Johnson won."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Larry Johnson", person_key="larry_johnson",
         start_date="2014-01-01", start_event="became-mayor", election_year="2013", end_event="lost",
         confidence="medium",
         sources="election:2013 (Mayor winner, def. Rechtenbach 53.5%); election:2017 (LOST Mayor to Overson, rank 2)",
         note="PRE-DATA-FLOOR term (elected Mayor 2013). COUNCILMEMBER->MAYOR CROSSOVER from D5 (see the first D5 "
              "row; SAME PERSON, hence start_event=became-mayor). Executive Mayor does NOT vote (MAYOR vote bounds "
              "emptied by non_voting_mayor). LOST re-election 2017 to Kristie Overson -> left office Jan 2018. Later "
              "ran for D5 2021 and lost to Knudsen."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Kristie Steadman Overson", person_key="kristie_overson",
         start_date="2018-01-01", start_event="became-mayor", election_year="2017", end_event="reelected",
         confidence="medium",
         sources="election:2017 (Mayor winner, def. incumbent Mayor Larry Johnson 57.2%); minutes:presiding "
                 "2020-01-08+ (as 'Mayor Overson')",
         note="Elected Mayor 2017 (term-start inferred Jan 2018, below the 2020 floor -> medium). COUNCILMEMBER->"
              "MAYOR CROSSOVER from D2 (she vacated D2 ~2 years early — see the D2 block; SAME PERSON, hence "
              "start_event=became-mayor). Executive Mayor does NOT vote on council motions (MAYOR vote bounds "
              "emptied by non_voting_mayor; she is absent from the cities.db person table). Re-elected 2021."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Kristie Steadman Overson", person_key="kristie_overson",
         start_date="2022-01-05", start_event="reelected", election_year="2021", end_event="reelected",
         confidence="high",
         sources="election:2021 (Mayor winner, uncontested 100%); minutes:2022-01-05 (Swearing In of Elected "
                 "Officials, Mayor Overson among those sworn); presiding throughout",
         note="Re-elected Mayor 2021 (oath 2022-01-05). Presides; does NOT vote on council legislation (MAYOR vote "
              "bounds empty). Re-elected 2025."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Kristie Steadman Overson", person_key="kristie_overson",
         start_date="2026-01-07", start_event="reelected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (Mayor winner, uncontested 100%); minutes:2026-01-07 (Administration of Oath of "
                 "Office to Mayor Overson ...); presiding",
         note="Re-elected Mayor 2025. Continues to preside; does not vote on council motions (MAYOR vote bounds "
              "empty). Currently serving."),
]

# canonical UPPER-CASE election name token -> our person_key. No shared council surnames in
# Taylorsville (each token below is unique), so no disambiguators are needed. Kristie Overson and
# Larry Johnson each have two bodies (council + mayor) but one key covers each person.
NAME_TO_KEY = {
    "CATLIN": "dl_catlin", "BURGESS": "ernest_burgess",
    "PRATT": "morris_pratt", "OVERSON": "kristie_overson", "COCHRAN": "curt_cochran",
    "RECHTENBACH": "jerry_rechtenbach", "CHRISTOPHERSON": "brad_christopherson", "BARBIERI": "anna_barbieri",
    "BARBOUR": "dama_barbour", "HARKER": "meredith_harker",
    "JOHNSON": "larry_johnson", "ARMSTRONG": "dan_armstrong", "KNUDSEN": "bob_knudsen",
    "WALL": "russ_wall",
}

# cities.db person.name_key -> our person_key (council voters only). Mayor Overson and mayor-era
# Larry Johnson are DELIBERATELY absent — neither cast a council vote in the loaded window (both
# were pre-floor councilmembers, and the Mayor is non-voting), so cities.db has no council rows for
# them (verified: the only distinct named voters are the seven district members).
DB_KEY = {
    "ernestburgess": "ernest_burgess", "curtcochran": "curt_cochran",
    "bradchristopherson": "brad_christopherson", "annabarbieri": "anna_barbieri",
    "meredithharker": "meredith_harker", "danarmstrong": "dan_armstrong",
    "bobknudsen": "bob_knudsen",
}


def seat_for_contest(office, district):
    """election (office, district) -> seat_id (or None). Taylorsville: 5 geographic districts + a
    citywide executive Mayor; NO at-large/citywide council seats."""
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
    current_note=(f"CURRENT post-2020-census boundaries. {REDISTRICT_ORD} ('adopting Final Redistricting "
                  "Maps Pursuant to Utah Code 10-3-205.5') adopted " + REDISTRICT_ADOPTED + " on a 4-1 roll "
                  "call (motion Harker / second Burgess; Cochran No): 60,448 residents, ~12,100 per district, "
                  "'0% deviation,' lines drawn NOT to dissect voting precincts. geometry_ref is the "
                  "PRECINCT-DERIVED council-district polygons in geo/council_districts.geojson (Taylorsville "
                  "publishes no official district GIS layer — the 5 polygons are dissolved from the 44 TAY "
                  "precincts via the district-contest precinct rows); precinct->district in "
                  "geo/precinct_to_district.csv. First used for elections 2023 (D1/D2/D3) and 2025 (D4/D5)."),
    prior_adopted_by="prior plan (pre-2022 boundaries)",
    prior_geom_ref="geo/council_districts_pre2022.geojson",
    prior_confidence="low",
    prior_note=("Prior-plan (pre-2022) district boundaries RECONSTRUCTED 2026-07-11 by dissolving current-vintage "
                "precinct shapes by the pre-2022 (2012-cycle) precinct->district assignment (geometry_ref = "
                "geo/council_districts_pre2022.geojson; 38 of 39 TAY precincts present — TAY045 is a "
                "missing-geometry edge hole — 0 conflicts). In force through the 2021 elections. effective_start = "
                "data floor. "
                "VALIDATION 2026-07-19 (LM-wave follow-up): Taylorsville publishes NO council-district GIS layer "
                "at all (city ArcGIS carries only a retail/demographic map; legal lines live textually in "
                "municipal code 13.04.100) -> no authoritative layer, prior OR current, to validate against. A "
                "fragmentation control still exposes precinct renumbering: dissolving CURRENT precinct shapes by "
                "the CURRENT assignment yields clean 1-piece districts, but this pre-2022 dissolve yields up to "
                "4-piece fragments (D1/D3/D5; D2/D4 stay clean) -> some old TAY codes were renumbered between the "
                "SOVC vintage and the current UGRC shapes, the same millcreek/SLCo defect proven in sibling "
                "cities (sandy/south_jordan/slc). Geometry confidence DOWNGRADED medium->low. The district_precincts "
                "precinct-CODE composition stays medium (a faithful SOVC record, geometry-independent). See "
                "scripts/roster_boundary_recon.md."),
    citywide_rows=[("MAYOR", "citywide", "the separately-elected executive Mayor Kristie Steadman Overson")],
    citywide_adopted_by="Taylorsville City (Mayor — whole city)",
    citywide_note_template=("{who}: represents the ENTIRE city on every date, unchanged by the 2022 "
                            "redistricting. Taylorsville has NO at-large council seats — all 5 council seats are "
                            "geographic districts; only the Mayor is citywide (and the executive Mayor does NOT "
                            "vote on council legislation). geometry_ref = full city extent."),
    precinct_hi_source=("2023", "2025"),   # both current-plan source_years -> all rows high (roster_lib multi-year)
    precinct_hi_note=("post-redistrict precinct->district from the current (post-2020-census) Taylorsville map — "
                      "the 44 TAY precincts assigned via the 2023 (D1/D2/D3) + 2025 (D4/D5) district-contest "
                      "precinct rows (geo/precinct_to_district.csv; 0 splits, 0 conflicts; per-district counts "
                      "D1=7, D2=6, D3=10, D4=7, D5=14). PRECINCT-DERIVED (no official city GIS layer)."),
    precinct_med_note="",   # unused — every plan_2022 row shares the one current-map source token
    precinct_prior_note=("Reconstructed pre-2022 (2012-cycle) precinct->district composition (38/39 TAY precincts — "
                         "TAY045 is a missing-geometry edge hole; from the pre-2022 SOVC district contests); medium "
                         "— current-vintage precinct shapes. See scripts/roster_boundary_recon.md."),
    crosscheck_districts=("1", "2", "3", "4", "5"),   # ALL districts: roster_lib's canon_key winner compare handles 'ERNEST GLEN BURGESS' vs 'Ernest Glen Burgess'
    precinct_prefix="TAY", geo_seat_prefix="D",
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
    elected_events=("elected", "reelected", "became-mayor"),
    redistrict=REDISTRICT, precincts_out=PRECINCTS_OUT,
    precinct_map_path=GEO_PRECINCT_MAP, precincts_byprecinct_path=PRECINCTS_BYP_SRC,
    prior_precinct_map_path=os.path.join(CITY_DIR, "geo", "precinct_to_district_pre2022.csv"),
)


# ---------------------------------------------------------------------------
# Precinct SIDECARS RETIRED 2026-07-11. The two per-city adapters (_write_precinct_to_district
# collapsing geo/precinct_to_district.csv's per-row 2023/2025 source_years to a single token, and
# _write_clean_byprecinct dropping suppressed/blank by-precinct rows) are gone: roster_lib now reads
# geo/precinct_to_district.csv and election_results/taylorsville_results_by_precinct.csv directly, via
# a multi-year precinct_hi_source (both 2023 & 2025 -> high) and an in-library blank/suppressed vote
# guard. No sidecar files are generated anymore.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Demo queries (Taylorsville presentation)
# ---------------------------------------------------------------------------
def demo():
    def line(r):
        end = r["end_date"] or "—(serving)"
        return (f"    {r['seat_id']:<6} {r['person_name']:<26} {r['start_date']} -> {end:<12}"
                f" [{r['start_event']}/{r['end_event']}] conf={r['confidence']}")

    print("\n(a) CURRENT council roster + mayor (end_date empty, end_event=serving):")
    for r in roster_lib.load_terms(CFG):
        if not r["end_date"] and r["end_event"] == "serving":
            print(line(r))

    print("\n(b) Roster AS OF 2020-09-15 (during the D3 vacancy — Christopherson departed/moved out, Barbieri not yet appointed):")
    for r in roster_lib.roster_as_of(CFG, "2020-09-15", body="Council"):
        print(line(r))
    for r in roster_lib.roster_as_of(CFG, "2020-09-15", body="Mayor"):
        print(line(r))

    print("\n(c) Address+date -> representatives (via geo/address_to_district.py — Mayor is non-voting/citywide):")
    # A Taylorsville address -> its District 1-5 member + the citywide (non-voting) executive Mayor.
    # City Hall (2600 W Taylorsville Blvd) resolves to District 5; we pass a lat/lon + precinct
    # fallback so the demo runs OFFLINE (the geocoder needs network; point-in-polygon is offline).
    addr = "2600 W Taylorsville Blvd, Taylorsville, UT 84129"
    for d in ("2026-02-01", "2020-06-01"):
        res = roster_lib.representatives_for_address(CFG, addr, d, latlon=(40.6677, -111.9388),
                                                     precinct="TAY001")
        who = ", ".join(f"{x['person_name']}({x['seat_id']})" for x in res["reps"])
        loc = (f"District {res['district']} via {res.get('precinct')} "
               f"[{res.get('method')}]") if res.get("district") else f"[{res.get('gap','?')}]"
        print(f"  '{addr}'")
        print(f"    on {d} (plan={res['plan']}): {loc}")
        print(f"    -> your reps: {who or '(none — see gap)'}")

    print("\n(d) SAME address across the 2022 REDISTRICTING (versioned district_versions):")
    for d in ("2021-06-01", "2026-02-01"):
        res = roster_lib.representatives_for_address(CFG, addr, d, latlon=(40.6677, -111.9388),
                                                     precinct="TAY001")
        if res.get("district"):
            reps = [x["person_name"] for x in res["reps"] if x["seat_id"].startswith("D")]
            print(f"    {d} (plan={res['plan']}): geographic District {res['district']} -> {reps}")
        else:
            print(f"    {d} (plan={res['plan']}): {res.get('gap')}")

    print("\n(e) Precinct-map cross-check (district_precincts vs election outcomes; D1 hand-verified — see CLAUDE):")
    roster_lib.precinct_crosscheck(CFG, verbose=True)


if __name__ == "__main__":
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
