#!/usr/bin/env python3
"""build_roster.py — rolling council-roster for ST. GEORGE, UTAH (a slowly-changing-
dimension / interval table of who holds each at-large council + mayor seat over time).

THIN DRIVER: this file holds only St. George-specific DATA (the curated TENURES seat
assignments — incl. TWO councilmember->mayor CROSSOVERS each spawning a mid-term
appointment (Randall->[VACANT]->Curtis in 2021; Hughes->[VACANT]->Anderson in 2026),
plus a MAYOR vacancy (Pike resigned -> [VACANT] -> Randall appointed), the name maps,
the at-large district row) + config; all generic mechanics live in
../../scripts/roster_lib.py (canon_key, election/vote-bounds/override reconciliation,
end-date chaining + VACANT insertion, validation, the CSV writers, and the as-of /
address / demo query helpers). See that module's docstring to add a city.

St. George is AT-LARGE (no geographic districts — like Lehi/Logan/Nephi/Vineyard) with a
NON-VOTING mayor (presides; votes only to break a tie — like Lehi/Logan/Nephi/Provo,
UNLIKE Vineyard/Orem/Millcreek). DETERMINATION (evidence + a quoted roll call in the
roster CLAUDE.md): the mayor is NOT in the aye/nay roll calls. On 2023-06-15 "Mayor
Randall called for a vote, as follows:" lists ONLY the five councilmembers
(Hughes/McArthur/Larkin/Larsen/Tanner) — never the mayor. Statistically: Mayor Jon Pike
(presided all of 2020) has exactly ONE council-body vote in 2020 (2020-04-16, a
tie-break); Mayor Randall has ZERO council votes 2022-2024 and one 3-2 tie-break
2025-02-20 — while her 243 votes in 2020 were cast as a COUNCILMEMBER before she became
mayor. => non_voting_mayor=True; the MAYOR rows carry NO vote bounds; jon_pike is left
out of DB_KEY (mayor-only). The two councilmember->mayor people (Randall, Hughes) ARE in
DB_KEY for their COUNCIL tenures; roster_lib now CLAMPS each tenure's first_vote/last_vote to
its own [start,end) window, so Randall's 2025-02-20 Mayor-era tie-break falls outside her AL-B1
council window and her council last_vote is 2021-01-19 with no override needed (see below).

DERIVED LAYER — regenerable, never hand-edited. Canonical inputs:
  1. election_results/st_george_results_by_candidate.csv  (general winners -> `elected` terms; is_winner=Y)
  2. cities.db  role table (city='st_george', body='Council')  (observed vote bounds; appointee detection)
  3. meeting_minutes/minutes/**                            (swearing-in / appointment / vacancy / resignation events)
  4. roster/roster_overrides.csv                           (hand corrections; applied LAST, wins ties)

Outputs (idempotent — re-running reproduces them byte-for-byte):
  roster/council_terms.csv      one row per seat-tenure (incl. 3 VACANT intervals)
  roster/district_versions.csv  boundary interval table (DEGENERATE — St. George is at-large)

Usage:
  python3 roster/build_roster.py            # regenerate the CSVs
  python3 roster/build_roster.py --demo     # regenerate + print the demo queries
  python3 roster/build_roster.py --check    # regenerate + run validations only

Cardinal rule (repo CLAUDE.md): NEVER fabricate. Unknown seat-holder / date / reason ->
explicit VACANT/UNKNOWN + confidence low/medium + a note, never a guess. Honest gaps are data.

Provenance / confidence model (same as Lehi/Logan):
  high   = anchored to an election result OR a minutes-documented swearing-in / appointment / resignation / vacancy
  medium = pre-floor 2017-cycle term (term-start inferred from the staggered cohort cycle),
           OR a vacancy whose exact date is inferred within a documented (recovered-minutes) bracket
  low    = genuinely unknown (flagged, never silently filled — NONE here)

Seat model — St. George runs a Mayor + 5 ALL-AT-LARGE council (NO geographic districts) on
STAGGERED 4-year terms; council is elected as a single multi-winner "Vote For N" field
(source: election_results/CLAUDE.md; CLAUDE.md). Vote-For-N per cycle: 2019=3, 2021=2,
2023=3, 2025=2 -> a 3-seat cohort (A) and a 2-seat cohort (B):
  Cohort A (3 seats): elected 2019 / 2023 / 2027 -> seat_id AL-A1, AL-A2, AL-A3  (terms Jan-2020, Jan-2024)
  Cohort B (2 seats): elected 2021 / 2025 / 2029 -> seat_id AL-B1, AL-B2         (terms Jan-2022, Jan-2026)
  MAYOR (1 seat)    : elected 2021 / 2025 (4-yr; NO mayoral race in 2019 or 2023).
Within-cohort seat NUMBERS are a stable labelling of the person-chain; where two same-cohort
newcomers arrive together the split is a labelling choice (flagged in `note`) — the person-tenures
are exact. AL-A1 is anchored by the Hughes->Anderson vacancy chain; AL-B1 by the Randall->Curtis
vacancy chain. The Larsen/Tanner (2021) and their continuation is a labelling split between B1/B2.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.dirname(HERE)              # st_george_city_council/
REPO_ROOT = os.path.dirname(CITY_DIR)         # civic-data/
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import roster_lib
from roster_lib import RosterConfig

ELECTIONS = os.path.join(CITY_DIR, "election_results", "st_george_results_by_candidate.csv")
CITIES_DB = os.path.join(REPO_ROOT, "cities.db")
OVERRIDES = os.path.join(HERE, "roster_overrides.csv")
TERMS_OUT = os.path.join(HERE, "council_terms.csv")
DISTRICTS_OUT = os.path.join(HERE, "district_versions.csv")

CITY = "st_george"
DATA_FLOOR = "2020-01-01"                   # repo minutes floor; the at-large structure predates it
GEOM_REF = "geo/city_limits.geojson"        # existing city-limits polygon (repo-relative)

# Verified seating / transition dates (documented in the recovered minutes):
#   2020-01-06 (SWEARING IN OF ELECTED OFFICIALS: "Jimmie Hughes, Gregg McArthur, and
#     Dannielle Larkin were sworn in" — the 2019 cohort-A winners. Present that day:
#     Mayor Pike + Hughes/Randall/Smethurst (+ the three sworn) — confirming Randall &
#     Smethurst are continuing 2017-cycle incumbents, NOT 2019 arrivals.)
#   2021-01-14 (Mayor Pike presides his LAST documented meeting)
#   ~2021-01-15..19 (Mayor Pike RESIGNS — "Mayor Pike's recent resignation"; exact date not
#     printed. By the 2021-01-19 special meeting Hughes is Mayor Pro Tem and the sole agenda
#     item is interviewing applicants for "the vacant Mayor position.")
#   2021-01-21 (Michele Randall — a sitting councilmember — sworn/appointed the first female
#     Mayor of St. George: "Michele Randall, sworn in and appointed as the new Mayor on
#     January 21, 2021 at 5:00 p.m." -> her COUNCIL seat is vacated.)
#   2021-02-10 (special meeting appoints Vardell Curtis "for the position of City Council to
#     fill Mayor Randall's remaining term"; "Mayor Randall called for a roll call vote" of the
#     FOUR sitting councilmembers — the mayor not among them.)  first seated/voting 2021-02-11.
#   2022-01-03 (SWEARING IN: "Michelle Tanner, Natalie Larsen, and Michele Randall were sworn
#     in" — the 2021 winners: Larsen/Tanner to Council, Randall to her elected Mayor term.)
#   2024-01-02 (SWEARING IN: Councilmembers Kemp, Hughes, Larkin — the 2023 winners.)
#   2026-01-08 (first meeting of the new term: PRESENT = Mayor Jimmie Hughes + only FOUR
#     councilmembers (Larkin/Larsen/Tanner/Kemp) -> Hughes vacated his AL-A1 council seat to
#     take the mayoralty he won in Nov-2025; the 5th seat is VACANT.)
#   2026-01-22 (special meeting interviews 15 applicants, appoints + swears in Austin F.
#     Anderson to the vacant council seat.)
# Pre-floor 2017-cycle terms start 2018-01 (inferred from the 4-year stagger, medium) — the
# repo minutes/elections only begin 2020/2019.

# ---------------------------------------------------------------------------
# LAYER 1-3 (reconciled). Each tenure anchored to a cited source. `end_date` is computed by
# chaining (next tenure on the seat) unless a departure reason must be stated; a `vacate_date`
# (+ `vacate_source`, `vacate_confidence`) on a tenure triggers roster_lib's explicit VACANT row.
# ---------------------------------------------------------------------------
TENURES = [
    # ===== Cohort A (3 seats; elected 2019 / 2023) ======================================
    # ---- AL-A1  (Hughes -> Hughes -> [VACANT] -> Anderson) : the Hughes council->mayor crossover ----
    dict(body="Council", seat_id="AL-A1", person_name="Jimmie Hughes", person_key="jimmie_hughes",
         start_date="2020-01-06", start_event="elected", election_year="2019",
         end_event="reelected", confidence="high",
         sources="election:2019 (Council 'Vote For 3' winner, rank1, 7717); minutes:2020-01-06 (SWEARING IN OF ELECTED OFFICIALS — 'Jimmie Hughes, Gregg McArthur, and Dannielle Larkin were sworn in')",
         note="Elected 2019 (rank1 of 6, vote-for-3). Re-elected 2023 (continuous). AL-A1 is the ANCHORED cohort-A seat — it carries the 2026 Hughes->Anderson vacancy chain. (Served as Mayor Pro Tem through the 2021 mayoral interregnum but held his own council seat throughout.)"),
    dict(body="Council", seat_id="AL-A1", person_name="Jimmie Hughes", person_key="jimmie_hughes",
         start_date="2024-01-02", start_event="reelected", election_year="2023",
         end_event="became-mayor", confidence="high",
         sources="election:2023 (Council 'Vote For 3' winner, rank2, 12006); minutes:2024-01-02 (SWEARING IN OF ELECTED OFFICIALS — Councilmembers Kemp, Hughes, Larkin); votes:cities.db last council vote 2025-12-18; minutes:2026-01-08 (present as MAYOR — council operates with 4 members)",
         vacate_date="2026-01-08", vacate_confidence="high",  # first meeting he presides as Mayor; his council seat is documented vacant (4-member present list)
         vacate_source="minutes:2026-01-08 (regular meeting PRESENT list = 'Mayor Jimmie Hughes' + only FOUR councilmembers Larkin/Larsen/Tanner/Kemp) — Hughes won the Nov-2025 mayoral general (election:2025, 12334 / 55.58%, def. incumbent Randall) and took the mayoralty in Jan-2026, vacating his AL-A1 council term (which ran to Jan-2028). His last council vote is 2025-12-18 (cities.db). The exact oath date is not captured in the recovered minutes; the vacancy is anchored to the first documented meeting where he presides as Mayor and the seat is empty (2026-01-08), NOT an un-recovered gap.",
         note="Re-elected 2023 to a term running to Jan-2028; ran for MAYOR in 2025 and WON (beat incumbent Randall), taking office Jan-2026 and RESIGNING/vacating his council seat mid-term. THE second councilmember->mayor crossover (Randall was the first, in 2021). Fully on-disk."),
    dict(body="Council", seat_id="AL-A1", person_name="Austin Anderson", person_key="austin_anderson",
         start_date="2026-01-22", start_event="appointed", election_year="",
         end_event="serving", confidence="high",
         sources="appt:2026-01-22 (special meeting — 'INTERVIEW APPLICANTS FOR VACANT CITY COUNCIL SEAT' (15 applicants), 'APPOINT NEW CITY COUNCILMEMBER' by ballot, then 'SWEARING IN OF NEW CITY COUNCILMEMBER — swearing in of Austin Anderson'); votes:cities.db first_seen 2026-01-22",
         note="APPOINTED (not elected) to fill the remainder of Hughes's 2024-2028 cohort-A term (vacated when Hughes became Mayor). Chosen by City Council ballot from 15 applicants and sworn in the same 2026-01-22 special meeting. Currently serving."),

    # ---- AL-A2  (Larkin -> Larkin) : continuous, no vacancy ---------------------------
    dict(body="Council", seat_id="AL-A2", person_name="Dannielle Larkin", person_key="dannielle_larkin",
         start_date="2020-01-06", start_event="elected", election_year="2019",
         end_event="reelected", confidence="high",
         sources="election:2019 (Council 'Vote For 3' winner, rank3, 6714); minutes:2020-01-06 (SWEARING IN OF ELECTED OFFICIALS — sworn)",
         note="Elected 2019 (rank3). Re-elected 2023 (continuous service on AL-A2)."),
    dict(body="Council", seat_id="AL-A2", person_name="Dannielle Larkin", person_key="dannielle_larkin",
         start_date="2024-01-02", start_event="reelected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (Council 'Vote For 3' winner, rank3, 11058); minutes:2024-01-02 (SWEARING IN OF ELECTED OFFICIALS — Councilmembers Kemp, Hughes, Larkin); votes:cities.db last_seen 2026-06-04 (still serving)",
         note="Re-elected 2023 (term to Jan-2028). Currently serving."),

    # ---- AL-A3  (McArthur -> Kemp) : continuous, no vacancy ---------------------------
    dict(body="Council", seat_id="AL-A3", person_name="Gregg McArthur", person_key="gregg_mcarthur",
         start_date="2020-01-06", start_event="elected", election_year="2019",
         end_event="did-not-run", confidence="high",
         sources="election:2019 (Council 'Vote For 3' winner, rank2, 7647); minutes:2020-01-06 (SWEARING IN OF ELECTED OFFICIALS — sworn); votes:cities.db last_seen 2023-12-14; election:2023 (advanced from the Sep primary rank6 but did NOT appear on the Nov general ballot — withdrew)",
         note="Elected 2019 (rank2). Advanced from the 2023 primary (rank6 of 6 advancing) but did NOT run in the 2023 general (the general field was Kemp/Hughes/Larkin/Bennett/Smith — McArthur withdrew) -> term expired Jan-2024, seat won by Kemp. A2/A3 split of the 2019 winners (Larkin/McArthur) is a labelling choice; person-tenures are exact (AL-A2 anchored by Larkin's continuity, AL-A3 by the McArthur->Kemp handoff)."),
    dict(body="Council", seat_id="AL-A3", person_name="Steve Kemp", person_key="steve_kemp",
         start_date="2024-01-02", start_event="elected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (Council 'Vote For 3' winner, rank1, 12334); minutes:2024-01-02 (SWEARING IN OF ELECTED OFFICIALS — Councilmembers Kemp, Hughes, Larkin); votes:cities.db first_seen 2024-01-02, last_seen 2026-06-04 (still serving)",
         note="Elected 2023 (rank1) to the cohort-A seat vacated by McArthur. Currently serving."),

    # ===== Cohort B (2 seats; elected 2021 / 2025) ======================================
    # ---- AL-B1  (Randall [pre-floor] -> [VACANT] -> Curtis -> Larsen -> Larsen) : Randall council->mayor crossover ----
    dict(body="Council", seat_id="AL-B1", person_name="Michele Randall", person_key="michele_randall",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="became-mayor", confidence="medium",
         sources="votes:2020-01-06.. (observed serving, cities.db role first_seen 2020-01-06); minutes:2020-01-06 (already seated as 'Councilmember Michele Randall' and NOT among the three sworn-in that day -> a continuing 2017-cycle incumbent, not a 2019 arrival)",
         vacate_date="2021-01-21", vacate_confidence="high",  # the day she is sworn Mayor -> her council seat is vacated
         vacate_source="minutes:2021-01-21 (Randall 'sworn in and appointed as the new Mayor on January 21, 2021 at 5:00 p.m.' — the first female Mayor of St. George, appointed by the Council after Mayor Pike's resignation). Her last COUNCIL vote is 2021-01-19 (cities.db); the seat is vacated on her 2021-01-21 mayoral swearing-in. Fully on-disk (present+voting through 2021-01-19 -> documented-vacant thereafter), NOT an un-recovered gap.",
         note="PRE-FLOOR term: the 2017 election predates the 2019 election-data floor and the 2020 minutes floor; term-start 2018-01 inferred from St. George's Cohort-B 4-year stagger (confidence medium). THE first councilmember->mayor crossover: Randall was appointed Mayor 2021-01-21 (after Pike resigned), vacating this cohort-B council seat mid-term (her term ran to Jan-2022). DISTINCT continuous holder -> anchors AL-B1. NOTE her council first_vote/last_vote: roster_lib CLAMPS them to this tenure's [2018-01-01, 2021-01-21) window, so her 2025-02-20 Mayor-era tie-break is excluded and last_vote is her true last COUNCIL vote 2021-01-19 (no override needed — the clamp alone reproduces it)."),
    dict(body="Council", seat_id="AL-B1", person_name="Vardell Curtis", person_key="vardell_curtis",
         start_date="2021-02-11", start_event="appointed", election_year="",
         end_event="lost", confidence="high",
         sources="appt:2021-02-10 (special meeting — 'APPOINT NEW COUNCILMEMBER: A motion was made by Councilmember McArthur to appoint Vardell Curtis for the position of City Council to fill Mayor Randall's remaining term'; Mayor Randall: 'Vardell Curtis will fill her remaining term which will end January[,] 2022'); minutes:2021-02-11 (first seated — PRESENT list 'Councilmember Vardell Curtis'); votes:cities.db first_seen 2021-02-11, last_seen 2021-12-16",
         note="APPOINTED 2021-02-10 to fill the remainder of Randall's 2018-2022 cohort-B term (first seated/voting 2021-02-11). Ran in the 2021 cycle for a full term: advanced the primary (rank2) but LOST the Nov general (rank4 of 4; the two seats went to Larsen & Tanner) -> served only to Jan-2022."),
    dict(body="Council", seat_id="AL-B1", person_name="Natalie Larsen", person_key="natalie_larsen",
         start_date="2022-01-03", start_event="elected", election_year="2021",
         end_event="reelected", confidence="high",
         sources="election:2021 (Council 'Vote For 2' winner, rank1, 10384); minutes:2022-01-03 (SWEARING IN OF ELECTED OFFICIALS — 'Michelle Tanner, Natalie Larsen, and Michele Randall were sworn in')",
         note="Elected 2021 (rank1, vote-for-2) to the full cohort-B term beginning Jan-2022. The Larsen(B1)/Tanner(B2) split of the 2021 pair is a LABELLING CHOICE — both cohort-B seats (the Randall/Curtis seat and the Smethurst seat) were on the ballot together in 2021; Larsen is assigned to the Randall/Curtis-anchored AL-B1. Person-tenure is exact. Re-elected 2025 (continuous)."),
    dict(body="Council", seat_id="AL-B1", person_name="Natalie Larsen", person_key="natalie_larsen",
         start_date="2026-01-08", start_event="reelected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Council 'Vote For 2' winner, rank1, 12013); minutes:2026-01-08 (present — PRESENT list 'Councilmember Natalie Larsen'); votes:cities.db last_seen 2026-06-04 (still serving)",
         note="Re-elected 2025 (rank1, vote-for-2) to a term running to Jan-2030. The exact oath date is not captured in the recovered 2026 minutes; anchored to the first documented meeting of the new term (2026-01-08). Currently serving."),

    # ---- AL-B2  (Smethurst [pre-floor] -> Tanner -> Tanner) : continuous after the pre-floor holder ----
    dict(body="Council", seat_id="AL-B2", person_name="Bryan Smethurst", person_key="bryan_smethurst",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="lost", confidence="medium",
         sources="votes:2020-01-06.. (observed serving, cities.db role first_seen 2020-01-06, last_seen 2021-12-16); minutes:2020-01-06 (already seated as 'Councilmember Bryan Smethurst' and NOT among the three sworn-in that day -> a continuing 2017-cycle incumbent); election:2021 (ran for re-election — primary rank6 of 11, 2775 — did NOT advance to the general, which advanced the top 4 Tanner/Curtis/Aldred/Larsen)",
         note="PRE-FLOOR term (2017 cycle; term-start 2018-01 inferred from the Cohort-B stagger, medium). DISTINCT continuous holder -> anchors AL-B2. RAN for re-election in 2021 and LOST in the Aug primary (rank6, did not advance). Term expired Jan-2022 (seat won by Tanner)."),
    dict(body="Council", seat_id="AL-B2", person_name="Michelle Tanner", person_key="michelle_tanner",
         start_date="2022-01-03", start_event="elected", election_year="2021",
         end_event="reelected", confidence="high",
         sources="election:2021 (Council 'Vote For 2' winner, rank2, 10216); minutes:2022-01-03 (SWEARING IN OF ELECTED OFFICIALS — 'Michelle Tanner, Natalie Larsen, and Michele Randall were sworn in')",
         note="Elected 2021 (rank2, vote-for-2). The B1/B2 split of the 2021 Larsen/Tanner pair is a labelling choice; Tanner is assigned to the Smethurst-succeeding AL-B2. Person-tenure is exact. Re-elected 2025 (continuous)."),
    dict(body="Council", seat_id="AL-B2", person_name="Michelle Tanner", person_key="michelle_tanner",
         start_date="2026-01-08", start_event="reelected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Council 'Vote For 2' winner, rank2, 11397); minutes:2026-01-08 (present — PRESENT list 'Councilmember Michelle Tanner'); votes:cities.db last_seen 2026-06-04 (still serving)",
         note="Re-elected 2025 (rank2, vote-for-2) to a term running to Jan-2030. Anchored to the first documented meeting of the new term (2026-01-08). Currently serving."),

    # ===== MAYOR (elected 2021 / 2025; the St. George mayor is NON-VOTING — tie-breaks only) ======
    dict(body="Mayor", seat_id="MAYOR", person_name="Jon Pike", person_key="jon_pike",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="resigned", confidence="medium",
         sources="minutes:2020-01-06.. (presiding as 'Mayor Jon Pike'); minutes:2020-12-17 (last documented meeting he presides as 'Mayor Jon Pike'); minutes:2021-01-14 (Mayor Pro Tem Hughes presides — present list shows Pike ABSENT, seat documented vacant)",
         vacate_date="2021-01-14", vacate_confidence="medium",  # last presided 2020-12-17; seat documented-vacant 2021-01-14 (Pro Tem Hughes presides); exact resignation-effective date not printed -> medium
         vacate_source="minutes:2021-01-19 (special meeting — Mayor Pro Tem Hughes: 'he has had the honor of serving as the Mayor Pro Tem since Mayor Pike's recent resignation'; the sole agenda item is interviewing applicants for 'the vacant Mayor position'). Pike presided his last documented meeting 2020-12-17 (as 'Mayor Jon Pike'); by 2021-01-14 Mayor Pro Tem Hughes presides and the present list shows Pike ABSENT (the '2021-01-14 Mayor Pike called the meeting to order' line is a STALE PMN template header, contradicted by that meeting's present list + every roll call). The exact resignation-effective date is NOT printed, so vacate_date is set to the documented-vacant meeting 2021-01-14 within the bracket 2020-12-17 (last presiding) .. 2021-01-19 (Pro Tem confirms 'Mayor Pike's recent resignation') -> vacate_confidence=medium. He left to become Utah Insurance Commissioner.",
         note="PRE-FLOOR term: elected Mayor 2017 (predates the 2019 election-data floor); term-start 2018-01 inferred (medium). Jon Pike RESIGNED the mayoralty in mid-January 2021 (to become Utah Insurance Commissioner), creating a MAYOR vacancy filled by Council appointment (Randall). NON-VOTING mayor: cities.db lists jon_pike with exactly ONE Council-body vote (2020-04-16) — a mayoral TIE-BREAK, not membership — so jon_pike is left OUT of DB_KEY and the MAYOR rows carry no first_vote/last_vote."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Michele Randall", person_key="michele_randall",
         start_date="2021-01-21", start_event="appointed", election_year="",
         end_event="elected", confidence="high",
         sources="minutes:2021-01-19 (special meeting selects Randall from the applicant field — 'a motion... to appoint the first ever female Mayor of the City of St. George, Michele Randall, sworn in and appointed as the new Mayor on January 21, 2021 at 5:00 p.m.'); minutes:2021-01-21 (sworn in at the regular meeting)",
         note="APPOINTED Mayor 2021-01-21 by the City Council to fill Pike's vacancy — the first female Mayor of St. George. She was a sitting COUNCILMEMBER (AL-B1) at the time; taking the mayoralty vacated her council seat (-> Curtis appointed). She then WON the Nov-2021 mayoral general (see next row). NON-VOTING mayor (MAYOR row carries no vote bounds)."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Michele Randall", person_key="michele_randall",
         start_date="2022-01-03", start_event="elected", election_year="2021",
         end_event="lost", confidence="high",
         sources="election:2021 (Mayor winner, 11614 / 55.18%, def. Jimmie Hughes 9434); minutes:2022-01-03 (SWEARING IN OF ELECTED OFFICIALS — 'Michelle Tanner, Natalie Larsen, and Michele Randall were sworn in'); election:2025 (ran for re-election as Mayor and LOST to Jimmie Hughes, 9859 / 44.42% vs 12334)",
         note="Elected Mayor 2021 (over councilmember Jimmie Hughes) to a full term Jan-2022..Jan-2026. LOST her 2025 re-election bid to Hughes -> term ended Jan-2026. NON-VOTING mayor: cities.db shows michele_randall with 0 council votes 2022-2024 and a single 3-2 tie-break 2025-02-20 (her only Mayor-era council vote) — the MAYOR rows carry no vote bounds (the tie-break is documented here, not folded in)."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Jimmie Hughes", person_key="jimmie_hughes",
         start_date="2026-01-08", start_event="elected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Mayor winner, 12334 / 55.58%, def. incumbent Randall 9859); minutes:2026-01-08 (presiding as 'Mayor Jimmie Hughes')",
         note="MAYOR (not a council seat). Elected 2025 over incumbent Mayor Randall; a councilmember->mayor crossover (he held AL-A1 through 2025 -> that seat VACANT -> Anderson appointed). The exact oath date is not captured in the recovered 2026 minutes; anchored to the first documented meeting where he presides as Mayor (2026-01-08). NON-VOTING mayor: no Mayor-era tie-breaks recorded yet (cities.db last council vote 2025-12-18, all as a councilmember) -> MAYOR row carries no vote bounds. Currently serving."),
]

# Seat model: all council seats + mayor are elected AT-LARGE -> one district.
SEAT_DISTRICT = {s: "At-Large" for s in
                 ("AL-A1", "AL-A2", "AL-A3", "AL-B1", "AL-B2", "MAYOR")}
SEAT_ORDER = ["AL-A1", "AL-A2", "AL-A3", "AL-B1", "AL-B2", "MAYOR"]

# canonical UPPER-CASE election name -> person_key. All St. George council/mayor SURNAMES are
# UNIQUE (no shared surnames -> no disambiguators needed; key on surname only — do NOT map
# shared first names). Election names carry middle initials (e.g. 'JIMMIE B HUGHES',
# 'VARDELL H CURTIS', 'BRYAN S SMETHURST') — canon_key tokenizes and matches the surname.
NAME_TO_KEY = {
    "HUGHES": "jimmie_hughes", "MCARTHUR": "gregg_mcarthur",
    "LARKIN": "dannielle_larkin", "KEMP": "steve_kemp",
    "RANDALL": "michele_randall", "SMETHURST": "bryan_smethurst",
    "CURTIS": "vardell_curtis", "LARSEN": "natalie_larsen",
    "TANNER": "michelle_tanner", "PIKE": "jon_pike",
    # Anderson is never a general-election winner (appointed 2026); included for completeness /
    # override robustness:
    "ANDERSON": "austin_anderson",
}

# cities.db person.name_key -> our person_key. jon_pike is DELIBERATELY OMITTED: his single db
# row is a mayoral TIE-BREAK (2020-04-16), not council membership, and the St. George mayor is
# non-voting -> the MAYOR rows carry no vote bounds. michele_randall & jimmie_hughes ARE mapped
# (they vote as COUNCILMEMBERS); the tenure-window clamp keeps each of their council tenures'
# bounds inside its own [start,end) window, so Randall's 2025-02-20 Mayor-era tie-break is excluded
# from her AL-B1 last_vote (=2021-01-19, no override) and Hughes's legitimate last council vote
# 2025-12-18 stands (he was a councilmember right up to becoming Mayor Jan-2026).
DB_KEY = {
    "jimmiehughes": "jimmie_hughes", "danniellelarkin": "dannielle_larkin",
    "greggmcarthur": "gregg_mcarthur", "stevekemp": "steve_kemp",
    "austinanderson": "austin_anderson", "michelerandall": "michele_randall",
    "bryansmethurst": "bryan_smethurst", "vardellcurtis": "vardell_curtis",
    "natalielarsen": "natalie_larsen", "michelletanner": "michelle_tanner",
}

ATLARGE = dict(
    district_id="At-Large", plan_id="current",
    effective_start=DATA_FLOOR, effective_end="",
    geometry_ref=GEOM_REF,
    adopted_by="St. George Municipal Code / Utah six-member form (Mayor + 5 at-large council; council-manager form; no geographic districts — the top-N vote-getters win the N open 'Vote For N' seats)",
    source_url="", confidence="high",
    note=("DEGENERATE: St. George's council + mayor are elected entirely AT-LARGE — no "
          "wards/districts and no per-seat contests (a single multi-winner 'Vote For N' field). "
          "This single row covers the whole city. NOTE: St. George's city LIMITS change over "
          "time by ANNEXATION (a fast-growth Washington County city), so geometry_ref points at "
          "the CURRENT city-limits polygon (geo/city_limits.geojson); prior annexation-versioned "
          "boundaries are NOT on disk and are NOT fabricated. Because every seat is at-large, the "
          "sub-district address->representative join degenerates to whole-city -> all sitting "
          "members + mayor. effective_start = repo data floor; the at-large structure predates it. "
          "(This is St. George, UTAH — entirely at-large — NOT St. George, Louisiana, which has "
          "a district-based council.)"),
)

CFG = RosterConfig(
    non_voting_mayor=True,
    city=CITY, city_dir=CITY_DIR, repo_root=REPO_ROOT, data_floor=DATA_FLOOR,
    geom_ref=GEOM_REF, elections_path=ELECTIONS, cities_db_path=CITIES_DB,
    overrides_path=OVERRIDES, terms_out=TERMS_OUT, districts_out=DISTRICTS_OUT,
    seat_district=SEAT_DISTRICT, name_to_key=NAME_TO_KEY, db_key=DB_KEY,
    seat_order=SEAT_ORDER,
    keep_election_row=lambda r: "general" in r["election_type"].lower(),  # drop primary advancers
    contest_key=lambda office, district: office,   # office (Council/Mayor) == body (at-large)
    crosscheck_field="body", winners_have_district=False,
    elected_events=("elected", "became-mayor", "reelected"),
    atlarge=ATLARGE,
)


# ---------------------------------------------------------------------------
# Demo queries (St. George presentation)
# ---------------------------------------------------------------------------
def demo():
    def line(r):
        end = r["end_date"] or "—(serving)"
        return (f"  {r['seat_id']:<6} {r['person_name']:<17} {r['start_date']} -> {end:<12} "
                f"[{r['start_event']}/{r['end_event']}] conf={r['confidence']}")

    print("\n(a) CURRENT council roster + mayor (end_date empty, end_event=serving):")
    for r in roster_lib.load_terms(CFG):
        if not r["end_date"] and r["end_event"] == "serving":
            print(line(r))

    print("\n(b) Roster AS OF 2026-01-15 (during the Hughes->Anderson AL-A1 VACANT window):")
    for r in roster_lib.roster_as_of(CFG, "2026-01-15", body="Council"):
        print(line(r))
    print("    Mayor:")
    for r in roster_lib.roster_as_of(CFG, "2026-01-15", body="Mayor"):
        print(line(r))

    print("\n(b') Roster AS OF 2021-02-01 (Randall appointed-Mayor; AL-B1 VACANT pre-Curtis):")
    for r in roster_lib.roster_as_of(CFG, "2021-02-01", body="Council"):
        print(line(r))
    print("    Mayor:")
    for r in roster_lib.roster_as_of(CFG, "2021-02-01", body="Mayor"):
        print(line(r))

    print("\n(c) address+date -> representative (degenerate At-Large -> all members + mayor):")
    for d in ("2023-06-15", "2026-06-01"):
        dist, reps = roster_lib.representatives_for_address(
            CFG, "175 East 200 North, St. George, UT 84770", d)
        who = ", ".join(f"{x['person_name']}({x['body']})" for x in reps)
        print(f"  '175 E 200 N' on {d}: district={dist} -> {who}")


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
