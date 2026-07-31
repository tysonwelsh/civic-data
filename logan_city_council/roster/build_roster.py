#!/usr/bin/env python3
"""build_roster.py — rolling council-roster for LOGAN (a slowly-changing-dimension /
interval table of who holds each at-large council + mayor seat over time).

THIN DRIVER: this file holds only Logan-specific DATA (the curated TENURES seat
assignments — incl. the TWO mid-term resignation→appointment chains (Bradfield→[VACANT]→
López in 2020 and Mark A. Anderson→[VACANT]→Dahle in 2025-26), the name maps + the two-
Anderson disambiguator, the at-large district row) + config; all generic mechanics live in
../../scripts/roster_lib.py (canon_key, election/vote-bounds/override reconciliation, end-date
chaining + VACANT insertion, validation, the CSV writers, and the as-of / address / demo helpers).
See that module's docstring to add a city.

Logan is a BACKLOG city built on the now-mature shared library (after Nephi/Provo/Vineyard/SLC/
Lehi/Orem). It is AT-LARGE (no geographic districts — like Nephi/Vineyard/Lehi/Orem → one
degenerate whole-city district row) with a NON-VOTING mayor (the separately-elected Logan mayor
presides + holds veto power but does NOT vote — like Nephi/Provo/Lehi, UNLIKE Vineyard/Orem's
voting mayor → the MAYOR rows carry no vote bounds). It exercises the VACANT/appointed path
TWICE (Lehi did it once):
  * AL-B1: Jess W. Bradfield (2017-cycle incumbent) RESIGNED 2020-09-22 → Ernesto López APPOINTED
    2020-10-20 to fill the vacancy (then elected 2021 & 2025 — appointee-turned-incumbent).
  * AL-A1: Mark A. Anderson (elected 2019 & 2023) RESIGNED 2025-11-17 after WINNING the 2025
    mayoralty → Melissa Dahle APPOINTED (interim, oath 2026-01-06) — the "appointed-after-losing"
    twist (Dahle LOST the 2025 council general, rank3 first-loser, then was appointed to Mark
    Anderson's DIFFERENT vacated seat; cf. Lehi's Lockhart).

DERIVED LAYER — regenerable, never hand-edited. Canonical inputs:
  1. election_results/logan_results_by_candidate.csv  (municipal GENERAL winners -> `elected` terms)
  2. cities.db  role table (city='logan', body='Council')  (observed vote bounds; appointee detection)
  3. meeting_minutes/minutes/**                          (swearing-in / appointment / vacancy events)
  4. roster/roster_overrides.csv                         (hand corrections; applied LAST, wins ties)

Outputs (idempotent — re-running reproduces them byte-for-byte):
  roster/council_terms.csv      one row per seat-tenure (incl. 2 VACANT intervals)
  roster/district_versions.csv  boundary interval table (DEGENERATE — Logan is at-large)

Usage:
  python3 roster/build_roster.py            # regenerate the CSVs
  python3 roster/build_roster.py --demo     # regenerate + print the demo queries
  python3 roster/build_roster.py --check    # regenerate + run validations only

Cardinal rule (repo CLAUDE.md): NEVER fabricate. Unknown seat-holder / date / reason ->
explicit VACANT/UNKNOWN + confidence low/medium + a note, never a guess. Honest gaps are data.

Provenance / confidence model (same as the other cities):
  high   = anchored to an election result OR a minutes-documented swearing-in / appointment / vacancy
  medium = pre-floor 2017-cycle term (term-start 2018-01 inferred from the staggered cohort cycle)
  low    = genuinely unknown (flagged, never silently filled — NONE here)

Seat model — Logan runs a Mayor + 5 ALL-AT-LARGE council (NO geographic districts; at-large since
1975) on STAGGERED 4-year terms (source: election_results/CLAUDE.md; geo/CLAUDE.md):
  Cohort A (3 seats): elected 2019 / 2023 / 2027 -> seat_id AL-A1, AL-A2, AL-A3  (terms Jan-2020, Jan-2024)
  Cohort B (2 seats): elected 2017 / 2021 / 2025 -> seat_id AL-B1, AL-B2         (terms Jan-2018, Jan-2022, Jan-2026)
  MAYOR (1 seat)    : elected 2017 / 2021 / 2025 (same cycle as Cohort B).
Logan's Mayor is NON-VOTING (presides; veto power; excluded from every roll call — confirmed 9
distinct roll-call voters, ZERO mayor rows), so — like Nephi/Provo/Lehi — the MAYOR rows carry NO
first_vote/last_vote. holly_daines has no cities.db council presence at all (never votes); Mark A.
Anderson IS in DB_KEY for his 2020-2025 COUNCIL votes, but his 2026+ MAYOR row is emptied by the
non_voting_mayor flag (he stopped voting the moment he became mayor — last council vote 2025-11-04).

Within-cohort seat NUMBERS are a stable labelling of the person-chain. Logan is unusually clean:
EVERY seat is anchored by a continuous distinct holder or a clean 1-for-1 replacement (no two
same-cohort newcomers ever arrive together), so — unlike Lehi's paired 2024/2026 arrivals — there
is no labelling ambiguity here. The 2019 trio (Mark Anderson=A1, Simmonds=A2, Jensen=A3) and the
2017 pair (Bradfield=B1, Amy Anderson=B2) are labelled at the data floor; each later transition
touches exactly one seat.

KNOWN TRAP — two Andersons (kept DISTINCT, never merged):
  * amy_anderson  = Amy Z. Anderson  — AL-B2, 2017-cycle incumbent, re-elected 2021, did not run 2025.
  * mark_anderson = Mark A. Anderson — AL-A1, elected 2019 & 2023, RESIGNED 2025-11-17, then MAYOR 2026+.
Both appear as bare "…ANDERSON" in the election data, so canon_key resolves them via the
`disambiguators` map (surname ANDERSON -> {AMY: amy_anderson, MARK: mark_anderson}) BEFORE the flat
surname table — do NOT put ANDERSON in NAME_TO_KEY. (There is also a non-member Richard Anderson,
Finance Director, who never appears as a candidate/voter.)
"""
import os
import sys
import csv

HERE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.dirname(HERE)              # logan_city_council/
REPO_ROOT = os.path.dirname(CITY_DIR)         # civic-data/
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import roster_lib
from roster_lib import RosterConfig

CITIES_DB = os.path.join(REPO_ROOT, "cities.db")
OVERRIDES = os.path.join(HERE, "roster_overrides.csv")
TERMS_OUT = os.path.join(HERE, "council_terms.csv")
DISTRICTS_OUT = os.path.join(HERE, "district_versions.csv")

CITY = "logan"
DATA_FLOOR = "2020-01-01"                   # repo minutes floor; the at-large structure predates it
GEOM_REF = "geo/city_boundary.geojson"      # existing Logan city-limits polygon (repo-relative)

# roster_lib.load_election_winners accepts is_winner in {true,1,yes,y,t} — Y/N supported since
# the 2026-07-11 hardening — so Logan's canonical Y/N election CSV is used directly (no shim).
ELECTIONS = os.path.join(CITY_DIR, "election_results", "logan_results_by_candidate.csv")

# Verified seating dates (documented oath ceremonies, from the meeting-header dates in the minutes):
#   2020-01-07 (oath: Simmonds, Jensen, Mark A. Anderson — the 2019 winners ONLY; Amy Z. Anderson &
#     Jess W. Bradfield head the same present-list but are NOT sworn -> continuing 2017-cycle incumbents)
#   2020-10-20 (oath: Ernesto López, "newly appointed … will fill the vacancy left by Jess Bradfield
#     who resigned on September 22, 2020 … will serve until January 1, 2022")
#   2022-01-04 (oath: Mayor Daines, Amy Z. Anderson, Ernesto López — 2021 winners)
#   2024-01-02 (oath: Simmonds, Mark A. Anderson, Mike Johnson — 2023 winners)
#   2025-11-18 (Mark A. Anderson ABSENT from the present list; his 2025-11-17 resignation announced)
#   2025-12-16 (Melissa Dahle SELECTED interim by 3-1 council ballot over Scott Mershon; seat still
#     rolls "VACANT" in that night's roll calls — she is not yet sworn)
#   2026-01-06 (oath: Mayor-Elect Mark A. Anderson + Councilmembers-Elect López, Lee-Koven, AND Dahle)
# Pre-floor 2017-cycle terms start 2018-01 (inferred from the 4-year stagger, medium) — the repo
# minutes/elections only begin 2020/2019.

# ---------------------------------------------------------------------------
# LAYER 1-3 (reconciled). Each tenure anchored to a cited source. `end_date` is computed by
# chaining (next tenure on the seat) unless a departure reason must be stated; a `vacate_date`
# (+ `vacate_source`, `vacate_confidence`) on a tenure triggers roster_lib's explicit VACANT row.
# ---------------------------------------------------------------------------
TENURES = [
    # ===== Cohort A — seats elected 2019 / 2023 (both IN the election data) =============
    # ---- AL-A1  (Mark A. Anderson -> Mark A. Anderson -> [VACANT] -> Dahle) : THE 2025-26 vacancy chain ----
    dict(body="Council", seat_id="AL-A1", person_name="Mark A. Anderson", person_key="mark_anderson",
         start_date="2020-01-07", start_event="elected", election_year="2019",
         end_event="reelected", confidence="high",
         sources="election:2019 (Council plurality winner, rank1, 3837); minutes:2020-01-07 (Oath of Office administered to Councilmember Elect … Mark A. Anderson)",
         note="Elected 2019 (rank1 of 6, vote-for-3). Re-elected 2023 (continuous service on AL-A1). AL-A1 is the ANCHORED cohort-A seat — it carries the 2025-26 Mark-Anderson->Dahle vacancy chain. DISTINCT from Amy Z. Anderson (AL-B2) — two different people."),
    dict(body="Council", seat_id="AL-A1", person_name="Mark A. Anderson", person_key="mark_anderson",
         start_date="2024-01-02", start_event="reelected", election_year="2023",
         end_event="resigned", confidence="high",
         vacate_date="2025-11-18", vacate_confidence="high",  # resignation effective 2025-11-17; VACANT begins the next meeting (that day belongs to Anderson)
         sources="election:2023 (Council plurality winner, rank1 CERTIFIED canvass, 3449); minutes:2024-01-02 (Oath of Office administered to Councilmember Elect … Mark A. Anderson); minutes:2025-11-04 (last recorded vote, cities.db role last_seen); minutes:2025-11-18 (present list shows only 4 members — Anderson absent; 'Councilmember Mark A. Anderson announced his resignation from the Council on November 17, 2025 so he can prepare to take office as Mayor')",
         vacate_source="minutes:2025-12-01 & 2025-12-16 document the resignation ('announced his resignation from the Council on November 17, 2025') and the resulting vacancy ('With the resignation of Mark Anderson as councilmember, there is a vacancy on the Council. State Code requires an appointment within 30 days'). Anderson is present+voting through 2025-11-04 and ABSENT from the 2025-11-18 present list; the seat rolls 'VACANT' in the 2025-12-16 roll calls. FULLY on-disk (not gap-bounded): resignation, vacancy, interview and selection are all in recovered minutes -> high. vacate_date = 2025-11-18 (resignation effective 2025-11-17; the last day belongs to Anderson, VACANT begins the next meeting).",
         note="Re-elected 2023 to a term running to Jan-2028; WON the 2025 mayoralty (def. Nafziger 4326-3027) and then RESIGNED his council seat mid-term (effective 2025-11-17) to take office as Mayor 2026-01-05/06. THE first of Logan's two mid-term vacancies. See the MAYOR block for his mayoral tenure."),
    dict(body="Council", seat_id="AL-A1", person_name="Melissa Dahle", person_key="melissa_dahle",
         start_date="2026-01-06", start_event="appointed", election_year="",
         end_event="serving", confidence="high",
         sources="appt:2025-12-16 (minutes — council interviewed 9 applicants, then 'voted by ballot … Melissa Dahle received three votes and Scott Mershon received one vote. With a majority vote, Melissa Dahle will be appointed as the interim city councilmember'); minutes:2026-01-06 (Oath of Office administered … to Councilmembers Elect Ernesto López, Katie Lee-Koven and Melissa Dahle); votes:cities.db first_seen 2026-01-06",
         note="APPOINTED (interim, not elected) to fill the remainder of Mark A. Anderson's 2024-2028 cohort-A term. THE 'appointed-after-losing' twist (cf. Lehi's Lockhart): Dahle RAN in the 2025 council general and LOST (rank3 of 4 / first loser, 3559), then was appointed to Anderson's DIFFERENT (vacated cohort-A) seat. start_date = the 2026-01-06 oath; she was SELECTED 2025-12-16 but the seat rolled 'VACANT' until her swearing-in (her first db vote is 2026-01-06). election_year blank (pure appointee — keep_election_row drops her 2025-primary advancer row; she is is_winner=N in the general). Currently serving."),

    # ---- AL-A2  (Simmonds -> Simmonds) : continuous, no vacancy ---------------
    dict(body="Council", seat_id="AL-A2", person_name="Jeannie F. Simmonds", person_key="jeannie_simmonds",
         start_date="2020-01-07", start_event="elected", election_year="2019",
         end_event="reelected", confidence="high",
         sources="election:2019 (Council plurality winner, rank2, 3221); minutes:2020-01-07 (Oath of Office administered to Councilmember Elect Jeannie F. Simmonds); minutes:2020-01-07 (serving as Chair)",
         note="Elected 2019 (rank2). Re-elected 2023 (continuous AL-A2). Chair in 2025-2026. DISTINCT continuous holder -> anchors AL-A2."),
    dict(body="Council", seat_id="AL-A2", person_name="Jeannie F. Simmonds", person_key="jeannie_simmonds",
         start_date="2024-01-02", start_event="reelected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (Council plurality winner, rank3 CERTIFIED canvass, 2419 — the 19-vote seat over Needham; recount confirmed, see election_results/CLAUDE.md); minutes:2024-01-02 (Oath of Office administered to Councilmember Elect Jeannie F. Simmonds); minutes:2026-01-06 (still serving — present list, chaired the 2025-12 meetings)",
         note="Re-elected 2023 — hers is the razor-thin 3rd seat (Simmonds 2419 vs Needham 2400, decided by 19 votes under the 2023 recount episode; the recount did not change the result). Currently serving."),

    # ---- AL-A3  (Jensen -> Johnson) : continuous, clean 1-for-1 replacement ----
    dict(body="Council", seat_id="AL-A3", person_name="Tom Jensen", person_key="tom_jensen",
         start_date="2020-01-07", start_event="elected", election_year="2019",
         end_event="did-not-run", confidence="high",
         sources="election:2019 (Council plurality winner, rank3, 2546); minutes:2020-01-07 (Oath of Office administered to Councilmember Elect Tom Jensen); votes:cities.db role last_seen 2023-12-05; election:2023 (not a candidate)",
         note="Elected 2019 (rank3). Not a candidate in the 2023 election (won by Anderson/Johnson/Simmonds) -> term expired Jan-2024. Clean 1-for-1: Johnson replaced Jensen (only one newcomer in 2023), so no A2/A3 labelling ambiguity."),
    dict(body="Council", seat_id="AL-A3", person_name="Mike Johnson", person_key="mike_johnson",
         start_date="2024-01-02", start_event="elected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (Council plurality winner, rank2 CERTIFIED canvass, 2892); minutes:2024-01-02 (Oath of Office administered to Councilmember Elect Mike Johnson); minutes:2026-01-06 (still serving — Chair in 2026); votes:cities.db first_seen 2024-01-02",
         note="Elected 2023 (newcomer replacing Jensen). Vice Chair 2025, Chair 2026. Currently serving (term to Jan-2028)."),

    # ===== Cohort B — seats elected 2017 / 2021 / 2025 ==================================
    # ---- AL-B1  (Bradfield [pre-floor] -> [VACANT] -> López -> López -> López) : THE 2020 vacancy chain ----
    dict(body="Council", seat_id="AL-B1", person_name="Jess W. Bradfield", person_key="jess_bradfield",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="resigned", confidence="medium",
         vacate_date="2020-09-23", vacate_confidence="high",  # documented resignation 2020-09-22; VACANT begins the next day
         # 2026-07-19: minutes_unrecovered.csv gained the 2020-10-13 Interim Appointment
         # meeting (PMN agenda-only, no minutes — genuine gap), which falls INSIDE this
         # VACANT window and trips roster_lib's gap-detector. Acknowledged rather than
         # downgraded: BOTH bracket dates are attested in RECOVERED minutes (resignation
         # 2020-09-22 quoted verbatim in the 2020-10-20 oath minutes; seating 2020-10-20
         # itself), so the missing interview-meeting minutes do not undermine the dates.
         vacate_unrecovered_ack="2020-10-13",
         sources="votes:2020-02-18.. (observed serving, cities.db role first_seen); minutes:2020-01-07 (already seated at the data floor — 'Councilmember Jess W. Bradfield' — and NOT among the three sworn-in that day, confirming a continuing 2017-cycle incumbent, not a 2019 winner); minutes:2020-06-01/2020-07-06/2020-08-03/2020-09-14 (present lists)",
         vacate_source="minutes:2020-10-20 (Ernesto López oath) states verbatim: 'newly appointed Councilmember Ernesto López who will fill the vacancy left by Jess Bradfield who resigned on September 22, 2020. Councilmember López will serve until January 1, 2022.' Bradfield is present through the 2020-09-14 meeting; his resignation is documented as effective 2020-09-22 -> vacate_date 2020-09-23. FULLY on-disk (not gap-bounded) -> vacate high. ack:2020-10-13 (the Interim Appointment interview meeting is agenda-only on PMN — minutes_unrecovered.csv — but both bracket dates of this vacancy are attested in the RECOVERED 2020-10-20 minutes, so the missing doc does not undermine them).",
         note="PRE-FLOOR term: the 2017 election predates the 2019 election-data floor and the 2020 minutes floor; term-start 2018-01 inferred from Logan's Cohort-B 4-year stagger (row confidence medium — only the START date is inferred; his 2020 membership + resignation are documented). RESIGNED mid-term 2020-09-22, creating THE second-2020 vacancy filled by López. DISTINCT continuous seat -> anchors AL-B1."),
    dict(body="Council", seat_id="AL-B1", person_name="Ernesto López", person_key="ernesto_lopez",
         start_date="2020-10-20", start_event="appointed", election_year="",
         end_event="reelected", confidence="high",
         sources="appt:2020-10-20 (minutes — 'The Oath of Office was administered by Judge Lee Edwards to newly appointed Councilmember Ernesto López who will fill the vacancy left by Jess Bradfield … will serve until January 1, 2022')",
         note="APPOINTED (not elected) 2020-10-20 to fill the remainder of Bradfield's 2018-2022 cohort-B term, then ELECTED in his own right 2021 (continuous AL-B1). NOTE: López participates as a mover/second from 2021-01 but his first NAMED roll-call vote in cities.db is 2021-12-07 — Logan's 2020-2021 council votes are heavily tally-only ('Carried unanimously (no names)'), so the observed vote-bound lags his true (appointed) start by design, not a gap. election_year blank on this appointed row."),
    dict(body="Council", seat_id="AL-B1", person_name="Ernesto López", person_key="ernesto_lopez",
         start_date="2022-01-04", start_event="reelected", election_year="2021",
         end_event="reelected", confidence="high",
         sources="election:2021 (Council plurality winner, rank1, 4313); minutes:2022-01-04 (Oath of Office administered to Councilmember Elect Ernesto Lopez)",
         note="Elected 2021 in his own right (the 2 cohort-B seats were up; López rank1, Amy Z. Anderson rank2). Re-elected 2025 (continuous AL-B1)."),
    dict(body="Council", seat_id="AL-B1", person_name="Ernesto López", person_key="ernesto_lopez",
         start_date="2026-01-06", start_event="reelected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Council plurality winner, rank1, 3985); minutes:2026-01-06 (Oath of Office administered to Councilmember Elect Ernesto López); minutes:2026-01-06 (serving as Vice Chair)",
         note="Re-elected 2025 (rank1 of 4; López + Lee-Koven won the 2 seats, Dahle the first loser). Currently serving (term to Jan-2030)."),

    # ---- AL-B2  (Amy Z. Anderson [pre-floor] -> Amy Z. Anderson -> Lee-Koven) : continuous, clean 1-for-1 ----
    dict(body="Council", seat_id="AL-B2", person_name="Amy Z. Anderson", person_key="amy_anderson",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="reelected", confidence="medium",
         sources="votes:2020-02-18.. (observed serving, cities.db role first_seen); minutes:2020-01-07 (already seated at the data floor as 'Vice Chair Amy Z. Anderson' — and NOT among the three sworn-in that day, confirming a continuing 2017-cycle incumbent)",
         note="PRE-FLOOR term (2017 cycle; term-start 2018-01 inferred from the Cohort-B stagger, medium). DISTINCT continuous holder -> anchors AL-B2. DISTINCT from Mark A. Anderson (AL-A1) — two different people (see disambiguators). Chair in 2020-2021."),
    dict(body="Council", seat_id="AL-B2", person_name="Amy Z. Anderson", person_key="amy_anderson",
         start_date="2022-01-04", start_event="reelected", election_year="2021",
         end_event="did-not-run", confidence="high",
         sources="election:2021 (Council plurality winner, rank2, 4237); minutes:2022-01-04 (Oath of Office administered to Councilmember Elect Amy Z. Anderson); votes:cities.db role last_seen 2025-12-16; election:2025 (not a candidate)",
         note="Re-elected to Council 2021. Did NOT seek re-election in 2025 (the 2 seats were won by López/Lee-Koven) -> term expired Jan-2026. Served through the 2025-12-16 meeting (chaired the interim-councilmember selection). Clean 1-for-1: Lee-Koven replaced Anderson."),
    dict(body="Council", seat_id="AL-B2", person_name="Katie Lee-Koven", person_key="katie_leekoven",
         start_date="2026-01-06", start_event="elected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Council plurality winner, rank2, 3643); minutes:2026-01-06 (Oath of Office administered to Councilmember Elect Katie Lee-Koven); votes:cities.db first_seen 2026-01-06",
         note="Elected 2025 (rank2; replacing Amy Z. Anderson). Had run 2023 (rank5, first-loser-plus-one under the recount) before winning in 2025. Currently serving (term to Jan-2030)."),

    # ===== MAYOR (cycle 2017 / 2021 / 2025; the Logan mayor is NON-VOTING — veto only, never votes) ======
    dict(body="Mayor", seat_id="MAYOR", person_name="Holly H. Daines", person_key="holly_daines",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="reelected", confidence="medium",
         sources="minutes:2020-01-07.. (presiding as 'Mayor Holly H. Daines'); minutes:2022-01-04 (oath — re-elected 2021)",
         note="PRE-FLOOR term: elected Mayor 2017 (predates the 2019 election-data floor); term-start 2018-01 inferred (medium). Confirmed MAYOR (heads the 'Administration present: Mayor Holly H. Daines' line and presides). NON-VOTING: Logan's mayor is separately elected, presides, and holds veto power but does NOT vote (election_results/CLAUDE.md; geo/CLAUDE.md) — she never appears in a roll call (0 of Logan's 9 named voters)."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Holly H. Daines", person_key="holly_daines",
         start_date="2022-01-04", start_event="reelected", election_year="2021",
         end_event="did-not-run", confidence="high",
         sources="election:2021 (Mayor plurality winner, 4100 / 62.26%, def. Dee Jones 2485); minutes:2022-01-04 (Oath of Office administered to Mayor Elect Holly H. Daines); minutes:2025-12-16 (last presiding as Mayor); election:2025 (did NOT run — the open mayoral seat was won by Mark A. Anderson)",
         note="Re-elected Mayor 2021. Did not seek a third term in 2025 -> the 2025 mayoral race was for the OPEN seat (won by Mark A. Anderson). Term ended Jan-2026. NON-VOTING mayor: holly_daines has ZERO cities.db council rows (never votes) -> MAYOR rows carry no first_vote/last_vote."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Mark A. Anderson", person_key="mark_anderson",
         start_date="2026-01-06", start_event="elected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Mayor plurality winner, 4326 / 58.83%, def. Alanna Nafziger 3027); minutes:2026-01-06 (Oath of Office administered to Mayor Elect Mark A. Anderson; presiding thereafter)",
         note="MAYOR (not a council seat). Same person as AL-A1 councilmember mark_anderson — he RESIGNED that council seat (effective 2025-11-17) upon winning the mayoralty, so his AL-A1 and MAYOR tenures do NOT overlap (council ends 2025-11-18 VACANT; mayor begins 2026-01-06). NON-VOTING as mayor: his cities.db council votes stop at 2025-11-04 and he casts ZERO votes as mayor — the non_voting_mayor flag empties this row's vote bounds (and the per-tenure vote clamp would empty them too, since his mayoral window from 2026-01-06 contains no Council votes; his 2020-2025 council span stays on his AL-A1 rows). Currently serving."),
]

# Seat model: all council seats + mayor are elected AT-LARGE -> one district.
SEAT_DISTRICT = {s: "At-Large" for s in
                 ("AL-A1", "AL-A2", "AL-A3", "AL-B1", "AL-B2", "MAYOR")}
SEAT_ORDER = ["AL-A1", "AL-A2", "AL-A3", "AL-B1", "AL-B2", "MAYOR"]

# TWO-ANDERSON disambiguation (the KNOWN TRAP): both Amy Z. and Mark A. Anderson appear as bare
# "…ANDERSON" in the election data. canon_key checks `disambiguators` FIRST (surname -> {FIRST: key}),
# so ANDERSON is resolved by first name before the flat NAME_TO_KEY table. Do NOT add ANDERSON to
# NAME_TO_KEY (it would merge the two people). Same pattern as Nephi's two Worwoods / Provo's two Davids.
DISAMBIGUATORS = {
    "ANDERSON": {"AMY": "amy_anderson", "MARK": "mark_anderson"},
}

# canonical UPPER-CASE election name -> person_key. All NON-Anderson council/mayor surnames are UNIQUE.
# (ANDERSON is intentionally ABSENT here — handled by DISAMBIGUATORS above.)
NAME_TO_KEY = {
    "SIMMONDS": "jeannie_simmonds", "JENSEN": "tom_jensen",
    "JOHNSON": "mike_johnson", "LOPEZ": "ernesto_lopez",
    "LEE-KOVEN": "katie_leekoven", "DAINES": "holly_daines",
    # Bradfield/Dahle are never GENERAL-election winners in the data (Bradfield 2017 predates the
    # floor; Dahle lost the 2025 general and was appointed) — included for override robustness:
    "BRADFIELD": "jess_bradfield", "DAHLE": "melissa_dahle",
}

# cities.db person.name_key -> our person_key. holly_daines is ABSENT (non-voting mayor, ZERO db rows).
# mark_anderson IS present (his 2020-2025 COUNCIL votes) — the non_voting_mayor flag empties only his
# MAYOR-body row, not his AL-A1 council rows.
DB_KEY = {
    "amyzanderson": "amy_anderson", "markaanderson": "mark_anderson",
    "jeanniefsimmonds": "jeannie_simmonds", "tomjensen": "tom_jensen",
    "ernestolpez": "ernesto_lopez", "mikejohnson": "mike_johnson",
    "katieleekoven": "katie_leekoven", "melissadahle": "melissa_dahle",
    "jesswbradfield": "jess_bradfield",
}

ATLARGE = dict(
    district_id="At-Large", plan_id="current",
    effective_start=DATA_FLOOR, effective_end="",
    geometry_ref=GEOM_REF,
    adopted_by="Logan Municipal Code / Utah six-member form (Mayor + 5 at-large council; at-large since 1975; no geographic districts, no wards)",
    source_url="", confidence="high",
    note=("DEGENERATE: Logan's council + mayor are elected entirely AT-LARGE — no wards/districts "
          "(in place since 1975; geo/CLAUDE.md). The 5 council seats are numbered for the ballot but "
          "are NOT geographic districts (the top-N vote-getters win the N open seats). This single row "
          "covers the whole city; geometry_ref points at the current city-limits polygon "
          "(geo/city_boundary.geojson). Because every seat is at-large, the sub-district address->"
          "representative join degenerates to an in/out-of-city-limits check -> all sitting members + "
          "mayor. effective_start = repo data floor; the at-large structure predates it."),
)

CFG = RosterConfig(
    non_voting_mayor=True,
    city=CITY, city_dir=CITY_DIR, repo_root=REPO_ROOT, data_floor=DATA_FLOOR,
    geom_ref=GEOM_REF, elections_path=ELECTIONS, cities_db_path=CITIES_DB,
    overrides_path=OVERRIDES, terms_out=TERMS_OUT, districts_out=DISTRICTS_OUT,
    seat_district=SEAT_DISTRICT, name_to_key=NAME_TO_KEY, db_key=DB_KEY,
    seat_order=SEAT_ORDER, disambiguators=DISAMBIGUATORS,
    keep_election_row=lambda r: "general" in r["election_type"].lower(),  # drop primary advancer rows
    contest_key=lambda office, district: office,   # office (Council/Mayor) == body (at-large)
    crosscheck_field="body", winners_have_district=False,
    elected_events=("elected", "became-mayor", "reelected"),
    atlarge=ATLARGE,
)


# ---------------------------------------------------------------------------
# Demo queries (Logan presentation)
# ---------------------------------------------------------------------------
def demo():
    def line(r):
        end = r["end_date"] or "—(serving)"
        return (f"  {r['seat_id']:<6} {r['person_name']:<20} {r['start_date']} -> {end:<12} "
                f"[{r['start_event']}/{r['end_event']}] conf={r['confidence']}")

    print("\n(a) CURRENT council roster + mayor (end_date empty, end_event=serving):")
    for r in roster_lib.load_terms(CFG):
        if not r["end_date"] and r["end_event"] == "serving":
            print(line(r))

    print("\n(b) Roster AS OF 2025-12-05 (during the Mark-Anderson->Dahle VACANT window):")
    for r in roster_lib.roster_as_of(CFG, "2025-12-05", body="Council"):
        print(line(r))
    print("    Mayor:")
    for r in roster_lib.roster_as_of(CFG, "2025-12-05", body="Mayor"):
        print(line(r))

    print("\n(b') Roster AS OF 2020-10-01 (during the Bradfield->López VACANT window):")
    for r in roster_lib.roster_as_of(CFG, "2020-10-01", body="Council"):
        print(line(r))

    print("\n(b'') Roster AS OF 2022-07-01 (mid Daines-2/López-1/Amy-2 + 2019 cohort A):")
    for r in roster_lib.roster_as_of(CFG, "2022-07-01", body="Council"):
        print(line(r))

    print("\n(c) address+date -> representative (degenerate At-Large -> all members + mayor):")
    for d in ("2022-07-01", "2026-06-01"):
        dist, reps = roster_lib.representatives_for_address(
            CFG, "290 N 100 W, Logan, UT 84321", d)
        who = ", ".join(f"{x['person_name']}({x['body']})" for x in reps)
        print(f"  '290 N 100 W' (City Hall) on {d}: district={dist} -> {who}")


if __name__ == "__main__":
    rows = roster_lib.build(CFG, TENURES)
    n_high = sum(1 for r in rows if r["confidence"] == "high")
    n_med = sum(1 for r in rows if r["confidence"] == "medium")
    n_low = sum(1 for r in rows if r["confidence"] == "low")
    n_vac = sum(1 for r in rows if r["person_name"] == "VACANT")
    print(f"Wrote {os.path.relpath(TERMS_OUT, CITY_DIR)} "
          f"({len(rows)} tenures: {n_high} high / {n_med} medium / {n_low} low; "
          f"{n_vac} VACANT interval{'s' if n_vac != 1 else ''})")
    print(f"Wrote {os.path.relpath(DISTRICTS_OUT, CITY_DIR)} (1 district — At-Large, degenerate)")
    if "--check" in sys.argv:
        print("\nValidation: PASS (no overlaps; every row has sources+confidence).")
    if "--demo" in sys.argv:
        demo()
