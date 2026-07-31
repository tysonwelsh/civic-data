#!/usr/bin/env python3
"""build_roster.py — rolling council-roster for PARK CITY (a slowly-changing-dimension /
interval table of who holds each at-large council + mayor seat over time).

THIN DRIVER: this file holds only Park-City-specific DATA (the curated TENURES seat
assignments — incl. the TWO council->mayor CROSSOVERS that both vacated the SAME cohort-A
seat mid-term (Worel->[VACANT]->Dickey->[VACANT]->Miller), the name maps, the at-large
city-boundary row) + config; all generic mechanics live in ../../scripts/roster_lib.py
(canon_key, election/vote-bounds/override reconciliation, end-date chaining + VACANT
insertion, validation, the CSV writers, and the as-of / address / demo query helpers). See
that module's docstring to add a city.

Park City is the tenth city built on the shared library (after Nephi/Provo/Vineyard/SLC/
Lehi/Orem/Logan/Millcreek/Ogden). It is AT-LARGE (Mayor + 5 all-at-large council, NO
geographic districts — like Nephi/Vineyard/Lehi/Orem) with a NON-VOTING mayor (presides;
votes ONLY to break a tie — like Nephi/Provo/Lehi, UNLIKE Vineyard's/Orem's voting mayor).
There are EXACTLY 2 mayoral tie-break VOTES in the whole record (Beerman 2020-06-25 Ord
2020-31; Worel-as-mayor 2024-08-22 Res 16-2024, both "Nay (Mayor tie-break)", both 2-3 Fail),
plus a third mayoral tie-break Dickey cast 2026-01-15 that was an APPOINTMENT SELECTION
(choosing Molly Miller), not a legislative roll-call, so it is not in all_votes.csv.
`non_voting_mayor=True` empties every MAYOR-body row's vote bounds so none of those
tie-breaks smear a misleading member span across a mayor's tenure.

TWO council->mayor CROSSOVERS on the SAME seat (AL-A1) — the marquee structure here:
  * Nann WOREL: elected to COUNCIL 2019 (cohort A, term 2020-2024), ran for MAYOR in 2021 and
    WON -> vacated her council seat ~2 years early to be sworn mayor (Jan-2022). Her cohort-A
    seat was filled by APPOINTMENT (Ryan Dickey, sworn 2022-01-27).
  * Ryan DICKEY: APPOINTED to Worel's vacated cohort-A council seat (2022-01-27), then ELECTED
    to it in his own right 2023 (term 2024-2028), then ran for MAYOR in 2025 and WON (7-vote
    recount) -> vacated the SAME cohort-A seat ~2 years early to be sworn mayor (Jan-2026). The
    seat was again filled by APPOINTMENT (Molly Miller, sworn 2026-01-20).
Both are handled exactly like Ogden's Nadolski / Logan's Anderson / Millcreek's Jackson: the
COUNCIL rows carry the council vote bounds; the MAYOR row is EMPTIED by non_voting_mayor;
council and mayor tenures never overlap. Neither crossover was a clean cycle handoff — each
was a MID-TERM vacancy filled by appointment (two explicit VACANT intervals on AL-A1).

DERIVED LAYER — regenerable, never hand-edited. Canonical inputs:
  1. election_results/park_city_results_by_candidate.csv  (municipal GENERAL winners -> `elected`/`reelected` terms)
  2. cities.db  role table (city='park_city', body='Council')  (observed vote bounds; appointee detection)
  3. meeting_minutes/minutes/**                            (swearing-in / appointment / vacancy events)
  4. roster/roster_overrides.csv                           (hand corrections; applied LAST, wins ties)

Outputs (idempotent — re-running reproduces them byte-for-byte):
  roster/council_terms.csv      one row per seat-tenure (incl. 2 VACANT intervals on AL-A1)
  roster/district_versions.csv  boundary interval table (DEGENERATE — Park City is at-large)

Usage:
  python3 roster/build_roster.py            # regenerate the CSVs
  python3 roster/build_roster.py --demo     # regenerate + print the demo queries
  python3 roster/build_roster.py --check    # regenerate + run validations only

Cardinal rule (repo CLAUDE.md): NEVER fabricate. Unknown seat-holder / date / reason ->
explicit VACANT/UNKNOWN + confidence low/medium + a note, never a guess. Honest gaps are data.

Provenance / confidence model (same as the fleet):
  high   = anchored to an election result OR a minutes-documented swearing-in / appointment / vacancy
  medium = pre-floor 2017-cycle term (term-start inferred from the staggered cohort cycle)
  low    = genuinely unknown (flagged, never silently filled — NONE here)

Seat model — Park City runs a Mayor + 5 ALL-AT-LARGE council (NO geographic districts) on
STAGGERED 4-year terms (source: election_results/CLAUDE.md — one cycle elects Mayor + 2
council (2021, 2025); the next elects 3 council (2019, 2023); vote-for-N block plurality, no RCV):
  Cohort A (3 seats): elected 2019 / 2023 / 2027 -> seat_id AL-A1, AL-A2, AL-A3  (terms Jan-2020, Jan-2024)
  Cohort B (2 seats): elected 2021 / 2025        -> seat_id AL-B1, AL-B2         (terms Jan-2022, Jan-2026)
  MAYOR   (1 seat)  : elected 2021 / 2025 (same cycle as Cohort B).
AL-A1 is ANCHORED by the Worel->Dickey->Miller crossover/vacancy chain. AL-B1 is anchored by
the DISTINCT continuous holder Tana Toly (2022 -> serving, re-elected 2025). Within-cohort seat
NUMBERS are a stable labelling of the person-chain; where two same-cohort members arrive/depart
together the split is a labelling choice (flagged in `note`) — the person-tenures are exact.

Park City's mayor is NON-VOTING, so the MAYOR rows carry NO first_vote/last_vote and
andy_beerman (a pure non-voting mayor whose only cities.db 'Council' row is the 2020-06-25
tie-break) is deliberately left OUT of DB_KEY. The two crossovers (nann_worel, ryan_dickey)
ARE in DB_KEY (they have real council tenures); non_voting_mayor empties only their MAYOR rows.
Worel's cities.db person-level Council last_seen is 2024-08-22 — but that is her MAYORAL
tie-break, not council service. Because first_vote/last_vote are now CLAMPED to each tenure's
own [start_date, end_date) window (roster_lib.clamp_vote_bounds), her AL-A1 council tenure
[2020-01-09, 2022-01-06) naturally EXCLUDES that 2024-08-22 tie-break and yields last_vote=
2021-12-16 with NO override — the crossover vote-bound smear (same class as Ogden's Nadolski)
is gone structurally. roster_overrides.csv is RETIRED (0 data rows) as of 2026-07-11.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.dirname(HERE)              # park_city_city_council/
REPO_ROOT = os.path.dirname(CITY_DIR)         # civic-data/
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import roster_lib
from roster_lib import RosterConfig

ELECTIONS = os.path.join(CITY_DIR, "election_results", "park_city_results_by_candidate.csv")
CITIES_DB = os.path.join(REPO_ROOT, "cities.db")
OVERRIDES = os.path.join(HERE, "roster_overrides.csv")
TERMS_OUT = os.path.join(HERE, "council_terms.csv")
DISTRICTS_OUT = os.path.join(HERE, "district_versions.csv")

CITY = "park_city"
DATA_FLOOR = "2020-01-01"                     # repo minutes floor; the at-large structure predates it
GEOM_REF = "geo/city_boundary.geojson"        # existing Summit+Wasatch city-limits polygon (repo-relative)

# Verified transition dates (documented in the recovered minutes / cities.db first_seen):
#   2020-01-09  first recovered meeting; present council = Doilney, Gerber, Henney, Joyce, Worel; Mayor Beerman
#   2022-01-06  first meeting of the 2022 term; ROLL CALL "Mayor Nann Worel" + 4 councilmembers (Doilney,
#               Gerber, Rubell, Toly) — Worel's cohort-A seat VACANT ("the council seat vacated when she was
#               elected mayor"); interviews Jan 7 & 11; appointment set for Jan 13
#   2022-01-13  "Appointment of New City Council Member to Fill the Seat Vacated by Nann [Worel]" -> Ryan Dickey
#   2022-01-27  "Swearing In ... Ryan ... Dickey ... appointed by the Council at the last meeting to fill the
#               remaining term left vacant when Mayor Worel was elected" (Dickey's first meeting as a member;
#               cities.db first_seen 2022-01-27)
#   2024-01-04  first meeting of the 2024 term; Parigian + Ciraco sworn (cities.db first_seen 2024-01-04)
#   2026-01-05  Mayor Dickey sworn in "on Monday" (per 2026-01-08 minutes + election_results/CLAUDE.md); his
#               cohort-A council seat thereby VACANT
#   2026-01-08  first meeting of the 2026 term; Dickey chairs as mayor, 4 councilmembers (Ciraco, Parigian,
#               Toly, Zegarra) — AL-A1 VACANT (cities.db first_seen: Zegarra 2026-01-08)
#   2026-01-13  interviews to fill "Mayor Dickey's vacated Council seat"; 2026-01-15 appointment (Mayor Dickey
#               "broke the tie by voting for Molly Miller" — an appointment selection, not a legislative vote)
#   2026-01-20  "Swearing In of a Council Member ... for a Term Expiring [Jan-2028]"; Molly Miller sworn
#               (cities.db first_seen 2026-01-20)
# Pre-floor 2017-cycle terms start 2018-01-01 (inferred from the 4-year stagger, medium) — the repo
# minutes/elections only begin 2020/2019.

# ---------------------------------------------------------------------------
# LAYER 1-3 (reconciled). Each tenure anchored to a cited source. `end_date` is computed by
# chaining (next tenure on the seat) unless a departure reason must be stated; a `vacate_date`
# (+ `vacate_source`) on a tenure triggers roster_lib's explicit VACANT row.
# ---------------------------------------------------------------------------
TENURES = [
    # ===== Cohort A — 3 seats elected 2019 / 2023 =======================================
    # ---- AL-A1 (Worel -> [VACANT] -> Dickey(appt) -> Dickey(elected) -> [VACANT] -> Miller(appt)) ----
    #      THE crossover/vacancy-anchored seat: TWO councilmembers-turned-mayor both vacated it mid-term.
    dict(body="Council", seat_id="AL-A1", person_name="Nann Worel", person_key="nann_worel",
         start_date="2020-01-09", start_event="elected", election_year="2019",
         end_event="became-mayor", confidence="high",
         vacate_date="2022-01-06", vacate_confidence="high",
         vacate_source="minutes:2022-01-06 ROLL CALL heads the present list 'Mayor Nann Worel' with only 4 councilmembers, and states '17 applications were received for the council seat vacated when she was elected mayor' -> her cohort-A council seat was empty from the 2022 term start. Bracketed by two RECOVERED meetings (last council vote 2021-12-16 -> documented-vacant 2022-01-06), not an un-recovered gap -> high.",
         sources="election:2019 (Council general winner, rank1, 1562); minutes:2020-01-09 (seated — present list 'Council Member ... Worel'); election:2021 (Mayor general winner, 2048/60.86% def. Beerman); minutes:2022-01-06 (now 'Mayor Nann Worel' — vacated this council seat); minutes:2025-12-16.. and cities.db show her last council-MEMBER vote 2021-12-16",
         note="CROSSOVER #1: elected to COUNCIL 2019 (cohort A, term to Jan-2024), then elected MAYOR 2021 and vacated this seat ~2 years early to be sworn mayor (Jan-2022) -> a MID-TERM vacancy filled by appointment (Dickey). AL-A1 is the ANCHORED cohort-A seat (it carries BOTH crossover vacancy chains). Her cities.db person-level Council last_seen is 2024-08-22 — but that is her MAYORAL tie-break (Res 16-2024), NOT council service; first_vote/last_vote are clamped to this AL-A1 tenure's [2020-01-09, 2022-01-06) window, which excludes that tie-break and yields last_vote=2021-12-16 with no override needed. Her MAYOR row (below) is emptied by non_voting_mayor."),
    dict(body="Council", seat_id="AL-A1", person_name="Ryan Dickey", person_key="ryan_dickey",
         start_date="2022-01-27", start_event="appointed", election_year="",
         end_event="reelected", confidence="high",
         sources="appt:2022-01-13 (minutes — 'Appointment of New City Council Member to Fill the Seat Vacated by Nann [Worel]' -> Ryan Dickey); minutes:2022-01-27 ('Swearing In ... Ryan ... Dickey ... appointed by the Council at the last meeting to fill the remaining term left vacant when Mayor Worel was elected'); votes:cities.db first_seen 2022-01-27",
         note="APPOINTED (not elected) 2022-01-27 to fill the REMAINDER of Worel's vacated cohort-A term (to Jan-2024). Chosen from 17 applicants after interviews Jan 7 & 11; the appointment was made 2022-01-13 and he was sworn 2022-01-27 (his first meeting as a member, hence cities.db first_seen 2022-01-27). He then won this seat in his own right in 2023 (next row)."),
    dict(body="Council", seat_id="AL-A1", person_name="Ryan Dickey", person_key="ryan_dickey",
         start_date="2024-01-04", start_event="reelected", election_year="2023",
         end_event="became-mayor", confidence="high",
         vacate_date="2026-01-05", vacate_confidence="high",
         vacate_source="minutes:2026-01-08 states the 'new mayor being sworn in on Monday' (2026-01-05) and election_results/CLAUDE.md records Dickey 'sworn Jan 5 2026'; the 2026-01-08 ROLL CALL shows Dickey chairing as mayor with only 4 councilmembers -> his cohort-A council seat was empty from the 2026 term start. Bracketed by two RECOVERED meetings (last council vote 2025-12-18 -> documented-vacant 2026-01-08), not an un-recovered gap -> high.",
         sources="election:2023 (Council general winner, rank1, 1778); minutes:2024-01-04 (seated, 2024 term); election:2025 (Mayor general winner, 1706-1699 over Rubin — certified + recount, Res 25-2025/27-2025); minutes:2026-01-08 (now presiding as 'Mayor Dickey'); cities.db last council-MEMBER vote 2025-12-18",
         note="CROSSOVER #2: won this cohort-A seat outright 2023 (term to Jan-2028) after holding it by appointment since 2022, then elected MAYOR 2025 (the 7-vote recount race) and vacated the SAME seat ~2 years early to be sworn mayor (Jan-2026) -> a second MID-TERM vacancy on AL-A1, filled by appointment (Miller). His cities.db Council bounds 2022-01-27..2025-12-18 are all genuine council-member votes (the two notes on 2022-06/2022-10 are db/vote_overrides clerk-error fixes, not tie-breaks); his MAYOR row (below) is emptied by non_voting_mayor. As mayor he cast a 2026-01-15 tie-break to APPOINT Miller — an appointment selection, not a legislative roll-call, so it is not in all_votes.csv/cities.db."),
    dict(body="Council", seat_id="AL-A1", person_name="Molly Miller", person_key="molly_miller",
         start_date="2026-01-20", start_event="appointed", election_year="",
         end_event="serving", confidence="high",
         sources="appt:2026-01-15 (minutes — 'Appointment of New City Council Member to Fill the Seat Vacated by Ryan [Dickey]'; Mayor Dickey broke a 2-2 tie to select Molly Miller); minutes:2026-01-20 ('Swearing In of a Council Member ... for a Term Expiring [Jan-2028]'; 'Council Member-Elect Miller was sworn in'); votes:cities.db first_seen 2026-01-20",
         note="APPOINTED (not elected) 2026-01-20 to fill the remainder of Dickey's 2024-2028 cohort-A term. NOTE the twist (like Lehi's Lockhart): Miller RAN in the 2025 council general... no — she lost in the 2025 council PRIMARY (rank7, is_winner=N), did NOT reach the general, and was then appointed to Dickey's DIFFERENT (vacated cohort-A) seat, so she serves to Jan-2028 despite not winning a seat at the ballot. start_date = the 2026-01-20 oath; the 2026-01-15 appointment vote was the Council's + Mayor Dickey's tie-break, not Miller's. Currently serving."),

    # ---- AL-A2 (Gerber -> Parigian) : continuous, no vacancy ------------------
    dict(body="Council", seat_id="AL-A2", person_name="Becca Gerber", person_key="becca_gerber",
         start_date="2020-01-09", start_event="elected", election_year="2019",
         end_event="did-not-run", confidence="high",
         sources="election:2019 (Council general winner, rank2, 1542); minutes:2020-01-09 (seated — present list); election:2023 (not a candidate)",
         note="Elected 2019 (rank2 of the 3-seat cohort A). Not a candidate in the 2023 election (won by Dickey/Parigian/Ciraco) -> term expired Jan-2024; cities.db last vote 2023-12-14. A2 vs A3 split of the 2019 pair (Gerber/Doilney) is a labelling choice; the person-tenures are exact."),
    dict(body="Council", seat_id="AL-A2", person_name="Ed Parigian", person_key="ed_parigian",
         start_date="2024-01-04", start_event="elected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (Council general winner, rank2, 1311); minutes:2024-01-04 (seated, 2024 term; cities.db first_seen 2024-01-04); minutes:2026-05-21 (still serving)",
         note="Elected 2023 (rank2). Parigian ALSO ran in 2019 but LOST (rank4, not a winner) — the is_winner filter + keep_election_row (general-only) correctly seat him only from 2023. Parigian/Ciraco arrived together Jan-2024 replacing the departing 2019 pair (Gerber/Doilney), so the A2/A3 split is a labelling choice; person-tenure is exact. Currently serving."),

    # ---- AL-A3 (Doilney -> Ciraco) : continuous, no vacancy -------------------
    dict(body="Council", seat_id="AL-A3", person_name="Max Doilney", person_key="max_doilney",
         start_date="2020-01-09", start_event="elected", election_year="2019",
         end_event="did-not-run", confidence="high",
         sources="election:2019 (Council general winner, rank3, 954); minutes:2020-01-09 (seated — present list); election:2023 (not a candidate)",
         note="Elected 2019 (rank3). Not a candidate in 2023 -> term expired Jan-2024; cities.db last vote 2023-12-14. A2/A3 split of the 2019 pair is a labelling choice."),
    dict(body="Council", seat_id="AL-A3", person_name="Bill Ciraco", person_key="bill_ciraco",
         start_date="2024-01-04", start_event="elected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (Council general winner, rank3, 1158 — the seat-deciding 74-vote margin over Sertner); minutes:2024-01-04 (seated, 2024 term; cities.db first_seen 2024-01-04); minutes:2026-05-21 (still serving)",
         note="Elected 2023 (rank3, the 3rd/last cohort-A seat). Ciraco/Parigian arrived together Jan-2024; the A2/A3 split is a labelling choice; person-tenure is exact. Currently serving."),

    # ===== Cohort B — 2 seats elected 2021 / 2025 =======================================
    # ---- AL-B1 (Joyce [pre-floor] -> Toly -> Toly) : continuous, anchored by Toly ----
    dict(body="Council", seat_id="AL-B1", person_name="Steve Joyce", person_key="steve_joyce",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="did-not-run", confidence="medium",
         sources="votes:2020-01-09.. (observed serving, cities.db role first_seen 2020-01-09); minutes:2020-01-09 (already seated at the data floor as 'Council Member Joyce'); election:2021 (not a candidate)",
         note="PRE-FLOOR term: the 2017 election predates the 2019 election-data floor and the 2020 minutes floor; term-start 2018-01 inferred from Park City's Cohort-B 4-year stagger (confidence medium). Cohort B (2 seats). Not a candidate in 2021 -> term expired Jan-2022 (seat won by Toly); cities.db last vote 2021-12-16. The Joyce/Henney pre-floor pair -> the 2022 pair (Toly/Rubell): which maps to B1 vs B2 is a labelling choice, but Toly's DISTINCT continuous service (2022->serving) anchors AL-B1."),
    dict(body="Council", seat_id="AL-B1", person_name="Tana Toly", person_key="tana_toly",
         start_date="2022-01-06", start_event="elected", election_year="2021",
         end_event="reelected", confidence="high",
         sources="election:2021 (Council general winner, rank1, 2208); minutes:2022-01-06 (seated, 2022 term; cities.db first_seen 2022-01-06)",
         note="Elected 2021 (rank1 of the 2-seat cohort B). DISTINCT continuous holder -> anchors AL-B1. Re-elected 2025 (next row)."),
    dict(body="Council", seat_id="AL-B1", person_name="Tana Toly", person_key="tana_toly",
         start_date="2026-01-08", start_event="reelected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Council general winner, rank1, 2337); minutes:2026-01-08 (still serving, 2026 term — moved to close the meeting); minutes:2026-05-21 (still serving)",
         note="Re-elected 2025 (rank1). Continuous on AL-B1 since 2022, but first_vote/last_vote are now clamped PER TERM: this re-elected term carries 2026-01-08..2026-05-21 (her first term carries 2022-01-06..2025-12-18). Currently serving (term to Jan-2030)."),

    # ---- AL-B2 (Henney [pre-floor] -> Rubell -> Zegarra) : continuous, no vacancy ---
    dict(body="Council", seat_id="AL-B2", person_name="Tim Henney", person_key="tim_henney",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="lost", confidence="medium",
         sources="votes:2020-01-09.. (observed serving, cities.db role first_seen 2020-01-09); minutes:2020-01-09 (already seated at the data floor as 'Council Member Henney'); election:2021 (ran for re-election — general rank3 of 3, 1439, LOST the 2-seat race)",
         note="PRE-FLOOR term (2017 cycle; term-start 2018-01 inferred from the Cohort-B stagger, medium). RAN for re-election in 2021 and LOST (rank3; the 2 seats went to Toly/Rubell). Term expired Jan-2022; cities.db last vote 2021-12-16."),
    dict(body="Council", seat_id="AL-B2", person_name="Jeremy Rubell", person_key="jeremy_rubell",
         start_date="2022-01-06", start_event="elected", election_year="2021",
         end_event="lost", confidence="high",
         sources="election:2021 (Council general winner, rank2, 2130); minutes:2022-01-06 (seated, 2022 term; cities.db first_seen 2022-01-06); election:2025 (ran for re-election — general rank3 of 3, 1530, LOST the 2-seat race)",
         note="Elected 2021 (rank2). RAN for re-election in 2025 and LOST (rank3; the 2 seats went to Toly/Zegarra). Term expired Jan-2026 (seat won by Zegarra); cities.db last vote 2025-12-18."),
    dict(body="Council", seat_id="AL-B2", person_name="Diego Zegarra", person_key="diego_zegarra",
         start_date="2026-01-08", start_event="elected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Council general winner, rank2, 2016 — Park City's first Latino councilor); minutes:2026-01-08 (seated, 2026 term; cities.db first_seen 2026-01-08); minutes:2026-05-21 (still serving)",
         note="Elected 2025 (rank2). Replaced Rubell on cohort B. Currently serving (term to Jan-2030)."),

    # ===== MAYOR (cycle 2021 / 2025; Park City's mayor is NON-VOTING — tie-breaks only) ======
    dict(body="Mayor", seat_id="MAYOR", person_name="Andy Beerman", person_key="andy_beerman",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="lost", confidence="medium",
         sources="minutes:2020-01-09.. (presiding as Mayor); minutes:2020-06-25 (cast the 'Nay (Mayor tie-break)' on Ord 2020-31, 2-3 Fail — a mayoral tie-break, his ONLY cities.db 'Council' row); election:2021 (ran for re-election as Mayor and LOST to Worel, 1317-2048)",
         note="PRE-FLOOR term: elected Mayor 2017 (predates the 2019 election-data floor); term-start 2018-01 inferred (medium). Confirmed MAYOR (presides; cast the 2020-06-25 tie-break). NON-VOTING mayor: his sole cities.db Council-body row is that tie-break, so andy_beerman is deliberately left OUT of DB_KEY and this MAYOR row carries NO vote bounds (like Nephi/Provo/Lehi). Ran for re-election 2021 and LOST to Worel -> term ended Jan-2022."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Nann Worel", person_key="nann_worel",
         start_date="2022-01-06", start_event="elected", election_year="2021",
         end_event="did-not-run", confidence="high",
         sources="election:2021 (Mayor general winner, 2048/60.86% def. Beerman 1317); minutes:2022-01-06 (sworn/presiding as 'Mayor Nann Worel' — Park City's first woman mayor); minutes:2024-08-22 (cast the 'Nay (Mayor tie-break)' on Res 16-2024, 2-3 Fail); election:2025 (did NOT run — the open mayoral seat was won by Dickey)",
         note="CROSSOVER #1 (mayor side): moved up from COUNCIL (AL-A1, elected 2019) to MAYOR after winning 2021. NON-VOTING mayor: her only Council-body vote during this mayoral tenure is the 2024-08-22 tie-break -> non_voting_mayor empties this MAYOR row's vote bounds so that tie-break does NOT smear a member span across her mayoralty (and her AL-A1 council row's last_vote is separately clamped to that tenure's window = 2021-12-16, no override needed). Did not seek a second term in 2025 -> term ended Jan-2026 (open seat won by Dickey)."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Ryan Dickey", person_key="ryan_dickey",
         start_date="2026-01-05", start_event="elected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Mayor general winner, 1706-1699 over Rubin — the 7-vote recount, certified Res 25-2025 + recount-certified Res 27-2025); minutes:2026-01-08 ('the new mayor being sworn in on Monday' = 2026-01-05; presiding as 'Mayor Dickey'); election_results/CLAUDE.md ('sworn Jan 5 2026')",
         note="CROSSOVER #2 (mayor side): moved up from COUNCIL (AL-A1, appointed 2022 -> elected 2023) to MAYOR after winning the 2025 recount race. NON-VOTING mayor: this MAYOR row carries no vote bounds (his real council votes 2022-01-27..2025-12-18 live on his AL-A1 council rows). As mayor he cast a 2026-01-15 tie-break to APPOINT Molly Miller — an appointment selection, not a legislative roll-call, so it is absent from all_votes.csv (nothing to smear). Currently serving."),
]

# Seat model: all council seats + mayor are elected AT-LARGE -> one district.
SEAT_DISTRICT = {s: "At-Large" for s in
                 ("AL-A1", "AL-A2", "AL-A3", "AL-B1", "AL-B2", "MAYOR")}
SEAT_ORDER = ["AL-A1", "AL-A2", "AL-A3", "AL-B1", "AL-B2", "MAYOR"]

# canonical UPPER-CASE election name -> person_key. All Park City council/mayor surnames are
# UNIQUE (no shared surnames -> no disambiguators, no first-name keys needed).
NAME_TO_KEY = {
    "WOREL": "nann_worel", "GERBER": "becca_gerber", "DOILNEY": "max_doilney",
    "TOLY": "tana_toly", "RUBELL": "jeremy_rubell", "DICKEY": "ryan_dickey",
    "PARIGIAN": "ed_parigian", "CIRACO": "bill_ciraco", "ZEGARRA": "diego_zegarra",
    "JOYCE": "steve_joyce", "HENNEY": "tim_henney", "BEERMAN": "andy_beerman",
    # Miller is never a general-election winner (lost the 2025 primary; appointed), so she needs
    # no election-name mapping; included for completeness / override robustness:
    "MILLER": "molly_miller",
}

# cities.db person.name_key -> our person_key. andy_beerman is DELIBERATELY OMITTED: his sole db
# 'Council' row is the 2020-06-25 mayoral TIE-BREAK, not council membership, and the Park City
# mayor is non-voting -> the MAYOR rows carry no vote bounds (like Nephi/Provo/Lehi). The two
# CROSSOVERS (nann_worel, ryan_dickey) ARE included (they have real council tenures);
# non_voting_mayor empties only their MAYOR rows. Worel's would-be smeared last_vote (2024-08-22
# tie-break) is excluded by the tenure-window clamp (her AL-A1 last_vote = 2021-12-16), so
# roster_overrides.csv is retired (0 data rows) as of 2026-07-11.
DB_KEY = {
    "nannworel": "nann_worel", "beccagerber": "becca_gerber", "maxdoilney": "max_doilney",
    "stevejoyce": "steve_joyce", "timhenney": "tim_henney", "jeremyrubell": "jeremy_rubell",
    "tanatoly": "tana_toly", "ryandickey": "ryan_dickey", "billciraco": "bill_ciraco",
    "edparigian": "ed_parigian", "diegozegarra": "diego_zegarra", "mollymiller": "molly_miller",
}

ATLARGE = dict(
    district_id="At-Large", plan_id="current",
    effective_start=DATA_FLOOR, effective_end="",
    geometry_ref=GEOM_REF,
    adopted_by="Park City Municipal Code / council-manager form (Mayor + 5 at-large council; no geographic districts, no numbered seats — top-N block-plurality)",
    source_url="", confidence="high",
    note=("DEGENERATE: Park City's council + mayor are elected entirely AT-LARGE — no wards/districts "
          "and no numbered seats (the top-N vote-getters win the N open seats; no RCV). This single row "
          "covers the whole city. Park City straddles Summit + Wasatch counties; geometry_ref points at "
          "the CURRENT city-limits polygon (geo/city_boundary.geojson) — prior annexation-versioned "
          "boundaries are NOT on disk and are NOT fabricated. Because every seat is at-large, the "
          "sub-district address->representative join degenerates to whole-city -> all sitting members + "
          "mayor (geo/address_to_district.py resolves only inside/outside city limits). effective_start = "
          "repo data floor; the at-large structure predates it."),
)

CFG = RosterConfig(
    non_voting_mayor=True,
    city=CITY, city_dir=CITY_DIR, repo_root=REPO_ROOT, data_floor=DATA_FLOOR,
    geom_ref=GEOM_REF, elections_path=ELECTIONS, cities_db_path=CITIES_DB,
    overrides_path=OVERRIDES, terms_out=TERMS_OUT, districts_out=DISTRICTS_OUT,
    seat_district=SEAT_DISTRICT, name_to_key=NAME_TO_KEY, db_key=DB_KEY,
    seat_order=SEAT_ORDER,
    keep_election_row=lambda r: "general" in r["election_type"].lower(),  # drop the primary advancer rows (is_winner=Y)
    contest_key=lambda office, district: office,   # office (Council/Mayor) == body (at-large)
    crosscheck_field="body", winners_have_district=False,
    elected_events=("elected", "became-mayor", "reelected"),
    atlarge=ATLARGE,
)


# ---------------------------------------------------------------------------
# Demo queries (Park City presentation)
# ---------------------------------------------------------------------------
def demo():
    def line(r):
        end = r["end_date"] or "—(serving)"
        return (f"  {r['seat_id']:<6} {r['person_name']:<15} {r['start_date']} -> {end:<12} "
                f"[{r['start_event']}/{r['end_event']}] conf={r['confidence']} "
                f"votes:{r['first_vote'] or '—'}..{r['last_vote'] or '—'}")

    print("\n(a) CURRENT council roster + mayor (end_date empty, end_event=serving):")
    for r in roster_lib.load_terms(CFG):
        if not r["end_date"] and r["end_event"] == "serving":
            print(line(r))

    print("\n(b) Roster AS OF 2026-01-12 (during the 2nd AL-A1 VACANT window, Dickey->Miller):")
    for r in roster_lib.roster_as_of(CFG, "2026-01-12", body="Council"):
        print(line(r))
    print("    Mayor:")
    for r in roster_lib.roster_as_of(CFG, "2026-01-12", body="Mayor"):
        print(line(r))

    print("\n(b') Roster AS OF 2022-01-13 (during the 1st AL-A1 VACANT window, Worel->Dickey):")
    for r in roster_lib.roster_as_of(CFG, "2022-01-13", body="Council"):
        print(line(r))

    print("\n(c) The Worel COUNCIL->MAYOR crossover (AL-A1 council row + MAYOR row — no overlap):")
    for r in roster_lib.load_terms(CFG):
        if r["person_key"] == "nann_worel":
            print(line(r))

    print("\n(d) address+date -> representative (degenerate At-Large -> all members + mayor):")
    for d in ("2023-07-01", "2026-06-01"):
        dist, reps = roster_lib.representatives_for_address(
            CFG, "445 Marsac Avenue, Park City, UT 84060", d)
        who = ", ".join(f"{x['person_name']}({x['body']})" for x in reps)
        print(f"  '445 Marsac Ave' on {d}: district={dist} -> {who}")


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
