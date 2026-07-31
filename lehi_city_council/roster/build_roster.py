#!/usr/bin/env python3
"""build_roster.py — rolling council-roster for LEHI (a slowly-changing-dimension /
interval table of who holds each at-large council + mayor seat over time).

THIN DRIVER: this file holds only Lehi-specific DATA (the curated TENURES seat
assignments — incl. the ONE mid-term resignation→appointment (Albrecht→[VACANT]→
Lockhart), the name maps, the at-large district row) + config; all generic mechanics
live in ../../scripts/roster_lib.py (canon_key, election/vote-bounds/override
reconciliation, end-date chaining + VACANT insertion, validation, the CSV writers, and
the as-of / address / demo query helpers). See that module's docstring to add a city.

Lehi is the first BACKLOG city built on the now-mature shared library (after the four
prototypes Nephi/Provo/Vineyard/SLC). It is AT-LARGE (no geographic districts, like
Nephi/Vineyard) with a NON-VOTING mayor (like Nephi/Provo — the mayor votes only to break
a tie), and it exercises the VACANT/appointed path once: councilmember Paige Albrecht
resigned mid-term (Dec 2025) and Emily Lockhart was appointed to fill her seat.

DERIVED LAYER — regenerable, never hand-edited. Canonical inputs:
  1. election_results/lehi_results_by_candidate.csv   (general winners -> `elected` terms)
  2. cities.db  role table (city='lehi', body='Council')  (observed vote bounds; appointee detection)
  3. meeting_minutes/minutes/**                        (swearing-in / appointment / vacancy events)
  4. roster/roster_overrides.csv                       (hand corrections; applied LAST, wins ties)

Outputs (idempotent — re-running reproduces them byte-for-byte):
  roster/council_terms.csv      one row per seat-tenure (incl. 1 VACANT interval)
  roster/district_versions.csv  boundary interval table (DEGENERATE — Lehi is at-large)

Usage:
  python3 roster/build_roster.py            # regenerate the CSVs
  python3 roster/build_roster.py --demo     # regenerate + print the demo queries
  python3 roster/build_roster.py --check    # regenerate + run validations only

Cardinal rule (repo CLAUDE.md): NEVER fabricate. Unknown seat-holder / date / reason ->
explicit VACANT/UNKNOWN + confidence low/medium + a note, never a guess. Honest gaps are data.

Provenance / confidence model (same as Nephi/Vineyard):
  high   = anchored to an election result OR a minutes-documented swearing-in / appointment / vacancy
  medium = pre-floor 2017-cycle term (term-start inferred from the staggered cohort cycle)
  low    = genuinely unknown (flagged, never silently filled — NONE here)

Seat model — Lehi runs a Mayor + 5 ALL-AT-LARGE council (NO geographic districts) on STAGGERED
4-year terms (source: election_results/CLAUDE.md; recon.md):
  Cohort A (3 seats): elected 2019 / 2023 / 2027 -> seat_id AL-A1, AL-A2, AL-A3  (terms Jan-2020, Jan-2024)
  Cohort B (2 seats): elected 2017 / 2021 / 2025 -> seat_id AL-B1, AL-B2         (terms Jan-2018, Jan-2022, Jan-2026)
  MAYOR (1 seat)    : elected 2017 / 2021 / 2025 (same cycle as Cohort B).
Lehi's Mayor is NON-VOTING (presides; votes only to break a tie — exactly 4 tie-breaks by
Mayor Johnson in the corpus), so — like Nephi/Provo and UNLIKE Vineyard — the MAYOR rows carry
NO first_vote/last_vote (mark_johnson is deliberately left out of DB_KEY; the 4 tie-break votes
are documented in the MAYOR notes, not folded into the vote-bound fields — see the MAYOR block).

Within-cohort seat NUMBERS are a stable labelling of the person-chain; where two same-cohort
newcomers arrive together the split is a labelling choice (flagged in `note`) — the person-tenures
are exact. AL-A1 is anchored by the Albrecht->Lockhart vacancy chain; AL-B1/AL-B2 are anchored by
the two DISTINCT continuous holders Condie / Hancock.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.dirname(HERE)              # lehi_city_council/
REPO_ROOT = os.path.dirname(CITY_DIR)         # civic-data/
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import roster_lib
from roster_lib import RosterConfig

ELECTIONS = os.path.join(CITY_DIR, "election_results", "lehi_results_by_candidate.csv")
CITIES_DB = os.path.join(REPO_ROOT, "cities.db")
OVERRIDES = os.path.join(HERE, "roster_overrides.csv")
TERMS_OUT = os.path.join(HERE, "council_terms.csv")
DISTRICTS_OUT = os.path.join(HERE, "district_versions.csv")

CITY = "lehi"
DATA_FLOOR = "2020-01-01"                   # repo minutes floor; the at-large structure predates it
GEOM_REF = "geo/city_boundary.geojson"      # existing city-limits polygon (repo-relative)

# Verified seating dates (documented swearing-in ceremonies / first council meeting of the term):
#   2020-01-14 (oath: Southwick, Albrecht, Koivisto — the 2019 winners only; Condie/Hancock were
#     already seated 2017-cycle incumbents, NOT sworn -> confirms their pre-floor continuity)
#   2022-01-04 (oath: Mayor Johnson, Condie, Hancock — 2021 winners)
#   2024-01-09 (oath: Albrecht, Newall, Stallings — 2023 winners)
#   2025-12-22 (Res. #2025-103 appoints Emily Lockhart to Albrecht's vacated seat; oath administered)
#   2026-01-06 (present list: Mayor Binns + Freeman, Harrison, Lockhart, Newall, Stallings)
# Pre-floor 2017-cycle terms start 2018-01 (inferred from the 4-year stagger, medium) — the repo
# minutes/elections only begin 2020/2019.

# ---------------------------------------------------------------------------
# LAYER 1-3 (reconciled). Each tenure anchored to a cited source. `end_date` is computed by
# chaining (next tenure on the seat) unless a departure reason must be stated; a `vacate_date`
# (+ `vacate_source`) on a tenure triggers roster_lib's explicit VACANT row.
# ---------------------------------------------------------------------------
TENURES = [
    # ===== Cohort A — seats elected 2019 / 2023 (both IN the election data) =============
    # ---- AL-A1  (Albrecht -> Albrecht -> [VACANT] -> Lockhart) : THE mid-term vacancy chain ----
    dict(body="Council", seat_id="AL-A1", person_name="Paige Albrecht", person_key="paige_albrecht",
         start_date="2020-01-14", start_event="elected", election_year="2019",
         end_event="reelected", confidence="high",
         sources="election:2019 (Council plurality winner, rank1, 5250); minutes:2020-01-14 (Swearing-In Ceremony — 'Councilors Southwick, Albrecht, and Koivisto were sworn in')",
         note="Elected 2019 (rank1 of 6, vote-for-3). Re-elected 2023 (continuous service on AL-A1). AL-A1 is the ANCHORED cohort-A seat (it carries the 2025 Albrecht->Lockhart vacancy chain); the A2/A3 split of the other 2019 pair (Southwick/Koivisto) is a labelling choice."),
    dict(body="Council", seat_id="AL-A1", person_name="Paige Albrecht", person_key="paige_albrecht",
         start_date="2024-01-09", start_event="reelected", election_year="2023",
         end_event="resigned", confidence="high",
         sources="election:2023 (Council RCV winner, rank2 first-choice 1754 / final-round 2973); minutes:2024-01-09 (Swearing-In Ceremony for Councilors Paige Albrecht, Heather Newall, and Michelle Stallings); minutes:2025-12-02 (last present + voting); minutes:2025-12-16 (Council operates with 4 members — 'the vacancy due to the resignation of Paige Albrecht')",
         vacate_date="2025-12-03", vacate_confidence="high",  # VACANT begins the day AFTER last service (2025-12-02, present+voting) so that day belongs to Albrecht
         vacate_source="minutes:2025-12-16 documents the seat vacant ('the current vacancy in the Lehi City Council … the resignation of Paige Albrecht'); the 4-member roll calls that day confirm it. Albrecht's last recorded vote/service is 2025-12-02 (cities.db role last_seen + present list), so vacate_date uses the last-recorded-vote convention. The written resignation letter's exact effective date is NOT printed (the 2026-01-13 review notes it 'first go[ing] to the mayor and then to the council' in December), but it is bracketed by two RECOVERED meetings (present+voting 2025-12-02 → documented-vacant 2025-12-16), NOT an un-recovered gap, so the fact and window are high.",
         note="Re-elected 2023 to a term running to Jan-2028; ran for MAYOR in 2025 (lost the general to Binns) and then RESIGNED her council seat mid-term in Dec-2025. THE mid-term vacancy for Lehi. Fully on-disk (unlike Vineyard's gap-bounded Cameron case): the resignation, the vacant council, and the successor's appointment are all in recovered minutes -> high."),
    dict(body="Council", seat_id="AL-A1", person_name="Emily Lockhart", person_key="emily_lockhart",
         start_date="2025-12-22", start_event="appointed", election_year="",
         end_event="serving", confidence="high",
         sources="appt:2025-12-22 (minutes — Resolution #2025-103 'appointing Emily Lockhart to the Lehi City Council', moved Condie / 2nd Hancock, passed unanimously; 'The Oath of Office was administered to Emily Lockhart after the adjournment'); votes:cities.db first_seen 2026-01-06",
         note="APPOINTED (not elected) to fill the remainder of Albrecht's 2024-2028 cohort-A term. NOTE the twist: Lockhart RAN in the 2025 council general and LOST (rank3 / first loser, 6972) — she was then appointed to Albrecht's DIFFERENT (vacated cohort-A) seat, so she serves to Jan-2028 despite losing the 2025 race. Was a 4-year Planning Commissioner. start_date = the 2025-12-22 oath; her first db VOTE is 2026-01-06 (the 2025-12-22 appointment vote was cast by Albrecht as the retained 'Voting Member for the Vacancy', not by Lockhart). Currently serving."),

    # ---- AL-A2  (Southwick -> Stallings) : continuous, no vacancy -------------
    dict(body="Council", seat_id="AL-A2", person_name="Mike Southwick", person_key="mike_southwick",
         start_date="2020-01-14", start_event="elected", election_year="2019",
         end_event="did-not-run", confidence="high",
         sources="election:2019 (Council plurality winner, rank2, 4135); minutes:2020-01-14 (Swearing-In Ceremony — sworn); minutes:2020-01-14 (selected Mayor Pro Tempore); election:2023 (not a candidate)",
         note="Elected 2019 (rank2). Not a candidate in the 2023 election (won by Stallings/Albrecht/Newall) -> term expired Jan-2024. A2 vs A3 split of the 2019 pair (Southwick/Koivisto) is a labelling choice; the person-tenures are exact."),
    dict(body="Council", seat_id="AL-A2", person_name="Michelle Stallings", person_key="michelle_stallings",
         start_date="2024-01-09", start_event="elected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (Council RCV winner, rank1 first-choice 2096 / final-round 2917); minutes:2024-01-09 (Swearing-In Ceremony for Councilors Paige Albrecht, Heather Newall, and Michelle Stallings); minutes:2026-01-06 (still serving — present list, elected Mayor Pro Tempore)",
         note="Elected 2023. Stallings/Newall arrived together Jan-2024 replacing the two departing 2019 members (Southwick/Koivisto), so the A2/A3 split between them is a labelling choice; person-tenure is exact. Currently serving."),

    # ---- AL-A3  (Koivisto -> Newall) : continuous, no vacancy ----------------
    dict(body="Council", seat_id="AL-A3", person_name="Katie Koivisto", person_key="katie_koivisto",
         start_date="2020-01-14", start_event="elected", election_year="2019",
         end_event="did-not-run", confidence="high",
         sources="election:2019 (Council plurality winner, rank3, 3969); minutes:2020-01-14 (Swearing-In Ceremony — sworn); election:2023 (not a candidate)",
         note="Elected 2019 (rank3). Not a candidate in 2023 -> term expired Jan-2024. A2/A3 split of the 2019 pair is a labelling choice."),
    dict(body="Council", seat_id="AL-A3", person_name="Heather Newall", person_key="heather_newall",
         start_date="2024-01-09", start_event="elected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (Council RCV winner, rank3 first-choice 1467 / final-round 2863); minutes:2024-01-09 (Swearing-In Ceremony for Councilors Paige Albrecht, Heather Newall, and Michelle Stallings); minutes:2026-01-06 (still serving — present list)",
         note="Elected 2023. Newall/Stallings arrived together Jan-2024; the A2/A3 split is a labelling choice; person-tenure is exact. Currently serving."),

    # ===== Cohort B — seats elected 2017 / 2021 / 2025 ==================================
    # ---- AL-B1  (Condie [pre-floor] -> Condie -> Harrison) : continuous, no vacancy ----
    dict(body="Council", seat_id="AL-B1", person_name="Chris Condie", person_key="chris_condie",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="reelected", confidence="medium",
         sources="votes:2020-01-14.. (observed serving, cities.db role first_seen 2020-01-14); minutes:2020-01-14 (already seated at the data floor — 'Chris Condie, Council Member' — and NOT among the three sworn-in that day, confirming he was a continuing incumbent, not a 2019 winner); minutes:2022-01-04 (oath — re-elected 2021)",
         note="PRE-FLOOR term: the 2017 election predates the 2019 election-data floor and the 2020 minutes floor; term-start 2018-01 inferred from Lehi's Cohort-B 4-year stagger (confidence medium). Cohort B (2 seats). DISTINCT continuous holder -> anchors AL-B1."),
    dict(body="Council", seat_id="AL-B1", person_name="Chris Condie", person_key="chris_condie",
         start_date="2022-01-04", start_event="reelected", election_year="2021",
         end_event="did-not-run", confidence="high",
         sources="election:2021 (Council RCV winner, rank1 first-choice 2300 / final-round 3073); minutes:2022-01-04 (Swearing In Ceremony for Mayor Johnson, Councilor Condie and Councilor Hancock); election:2025 (ran for MAYOR — primary rank3 of 4, 1701, did not advance)",
         note="Re-elected to Council 2021. Did NOT seek council re-election in 2025 — he ran for MAYOR instead and LOST in the Aug-2025 primary (rank3, did not advance to the general won by Binns). Council term expired Jan-2026 (seat won by Harrison)."),
    dict(body="Council", seat_id="AL-B1", person_name="James Harrison", person_key="james_harrison",
         start_date="2026-01-06", start_event="elected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Council plurality winner, rank1 general, 7603); minutes:2026-01-06 (seated — present list 'James Harrison, Council Member'); votes:cities.db first_seen 2026-01-06",
         note="Elected 2025 (plurality vote-for-2, rank1). Harrison/Freeman arrived together Jan-2026 replacing the departing Condie/Hancock cohort-B seats, so the B1/B2 split between them is a labelling choice; person-tenure is exact. Currently serving (term to Jan-2030)."),

    # ---- AL-B2  (Hancock [pre-floor] -> Hancock -> Freeman) : continuous, no vacancy ---
    dict(body="Council", seat_id="AL-B2", person_name="Paul Hancock", person_key="paul_hancock",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="reelected", confidence="medium",
         sources="votes:2020-01-14.. (observed serving, cities.db role first_seen 2020-01-14); minutes:2020-01-14 (already seated at the data floor — 'Paul Hancock, Council Member' — and NOT among the three sworn-in that day, confirming a continuing incumbent); minutes:2022-01-04 (oath — re-elected 2021)",
         note="PRE-FLOOR term (2017 cycle; term-start 2018-01 inferred from the Cohort-B stagger, medium). DISTINCT continuous holder -> anchors AL-B2."),
    dict(body="Council", seat_id="AL-B2", person_name="Paul Hancock", person_key="paul_hancock",
         start_date="2022-01-04", start_event="reelected", election_year="2021",
         end_event="lost", confidence="high",
         sources="election:2021 (Council RCV winner, rank2 first-choice 1811 / final-round 2583); minutes:2022-01-04 (Swearing In Ceremony for Mayor Johnson, Councilor Condie and Councilor Hancock); election:2025 (ran for council re-election — Aug-2025 primary rank5 of 10, 2239 — did NOT advance to the general)",
         note="Re-elected to Council 2021. RAN for re-election in 2025 and LOST in the Aug-2025 primary (rank5; the top-4 Lockhart/Freeman/Harrison/Peterson advanced). Council term expired Jan-2026 (seat won by Freeman)."),
    dict(body="Council", seat_id="AL-B2", person_name="Rachel Freeman", person_key="rachel_freeman",
         start_date="2026-01-06", start_event="elected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Council plurality winner, rank2 general, 7163); minutes:2026-01-06 (seated — present list 'Rachel Freeman, Council Member', gave the opening comment); votes:cities.db first_seen 2026-01-06",
         note="Elected 2025 (plurality vote-for-2, rank2). Harrison/Freeman -> B1/B2 split is a labelling choice (both arrived together Jan-2026); person-tenure is exact. Currently serving (term to Jan-2030)."),

    # ===== MAYOR (cycle 2017 / 2021 / 2025; the Lehi mayor is NON-VOTING — tie-breaks only) ======
    dict(body="Mayor", seat_id="MAYOR", person_name="Mark Johnson", person_key="mark_johnson",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="reelected", confidence="medium",
         sources="minutes:2020-01-14.. (presiding as 'Mark Johnson, Mayor'); minutes:2022-01-04 (oath — re-elected 2021)",
         note="PRE-FLOOR term: elected Mayor 2017 (predates the 2019 election-data floor); term-start 2018-01 inferred (medium). Confirmed MAYOR (heads the present-list as 'Mark Johnson, Mayor' and chairs meetings). NON-VOTING: Lehi's mayor presides and votes ONLY to break a tie (see the mayor note below)."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Mark Johnson", person_key="mark_johnson",
         start_date="2022-01-04", start_event="reelected", election_year="2021",
         end_event="did-not-run", confidence="high",
         sources="election:2021 (Mayor RCV winner, 6994 / 61.95%, def. Riddle 4295); minutes:2022-01-04 (Swearing In Ceremony for Mayor Johnson …); election:2025 (did NOT run — the open mayoral seat was won by Binns); minutes:2025-12-16 (last presiding as Mayor)",
         note="Re-elected Mayor 2021. Did not seek a third term in 2025 -> the 2025 mayoral race was for the OPEN seat (won by Binns). Term ended Jan-2026. NON-VOTING mayor: cities.db lists mark_johnson with exactly 4 votes on the Council body (2022-06-14, 2023-04-11, 2024-03-26, 2025-12-16) — these are his MAYORAL TIE-BREAKS, NOT council membership, so mark_johnson is deliberately left OUT of DB_KEY and the MAYOR rows carry NO first_vote/last_vote (like Nephi/Provo, unlike Vineyard's voting mayor). The 4 tie-breaks are documented here rather than folded into the vote-bound fields."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Paul Binns", person_key="paul_binns",
         start_date="2026-01-06", start_event="elected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Mayor plurality winner, 7909 / 53.5%, def. Albrecht 6873); minutes:2026-01-06 (presiding as 'Paul Binns, Mayor')",
         note="MAYOR (not a council seat). Elected 2025 over Paige Albrecht (who then resigned her council seat — see AL-A1). NON-VOTING mayor: Binns has 0 db votes (no tie-breaks recorded yet) -> MAYOR row correctly carries no vote bounds. Currently serving."),
]

# Seat model: all council seats + mayor are elected AT-LARGE -> one district.
SEAT_DISTRICT = {s: "At-Large" for s in
                 ("AL-A1", "AL-A2", "AL-A3", "AL-B1", "AL-B2", "MAYOR")}
SEAT_ORDER = ["AL-A1", "AL-A2", "AL-A3", "AL-B1", "AL-B2", "MAYOR"]

# canonical UPPER-CASE election name -> person_key. All Lehi council/mayor surnames are UNIQUE
# (no shared surnames -> no disambiguators, no first-name keys needed; do NOT map shared first
# names like the two PAULs — Hancock & Binns — key on surname only).
NAME_TO_KEY = {
    "ALBRECHT": "paige_albrecht", "SOUTHWICK": "mike_southwick",
    "KOIVISTO": "katie_koivisto", "CONDIE": "chris_condie",
    "HANCOCK": "paul_hancock", "STALLINGS": "michelle_stallings",
    "NEWALL": "heather_newall", "HARRISON": "james_harrison",
    "FREEMAN": "rachel_freeman", "JOHNSON": "mark_johnson", "BINNS": "paul_binns",
    # Lockhart is never a general-election winner (appointed; lost the 2025 general), so she
    # needs no election-name mapping; included for completeness / override robustness:
    "LOCKHART": "emily_lockhart",
}

# cities.db person.name_key -> our person_key. mark_johnson is DELIBERATELY OMITTED: his 4 db
# rows are mayoral TIE-BREAKS, not council membership, and the Lehi mayor is non-voting — so the
# MAYOR rows carry no vote bounds (like Nephi/Provo). paul_binns has no db presence (0 votes).
DB_KEY = {
    "paigealbrecht": "paige_albrecht", "chriscondie": "chris_condie",
    "paulhancock": "paul_hancock", "katiekoivisto": "katie_koivisto",
    "mikesouthwick": "mike_southwick", "heathernewall": "heather_newall",
    "michellestallings": "michelle_stallings", "emilylockhart": "emily_lockhart",
    "jamesharrison": "james_harrison", "rachelfreeman": "rachel_freeman",
}

ATLARGE = dict(
    district_id="At-Large", plan_id="current",
    effective_start=DATA_FLOOR, effective_end="",
    geometry_ref=GEOM_REF,
    adopted_by="Lehi Municipal Code / Utah six-member form (Mayor + 5 at-large council; no geographic districts, no numbered seats in these cycles)",
    source_url="", confidence="high",
    note=("DEGENERATE: Lehi's council + mayor are elected entirely AT-LARGE — no wards/districts "
          "and no numbered seats (the top-N vote-getters win the N open seats). This single row "
          "covers the whole city. NOTE: Lehi's city LIMITS change over time by ANNEXATION (a "
          "fast-growth 'Silicon Slopes' city), so geometry_ref points at the CURRENT city-limits "
          "polygon (geo/city_boundary.geojson); prior annexation-versioned boundaries are NOT on "
          "disk and are NOT fabricated. Because every seat is at-large, the sub-district address->"
          "representative join degenerates to whole-city -> all sitting members + mayor. "
          "effective_start = repo data floor; the at-large structure predates it."),
)

CFG = RosterConfig(
    non_voting_mayor=True,
    city=CITY, city_dir=CITY_DIR, repo_root=REPO_ROOT, data_floor=DATA_FLOOR,
    geom_ref=GEOM_REF, elections_path=ELECTIONS, cities_db_path=CITIES_DB,
    overrides_path=OVERRIDES, terms_out=TERMS_OUT, districts_out=DISTRICTS_OUT,
    seat_district=SEAT_DISTRICT, name_to_key=NAME_TO_KEY, db_key=DB_KEY,
    seat_order=SEAT_ORDER,
    keep_election_row=lambda r: "general" in r["election_type"].lower(),  # drop 2023/2025 primary advancers
    contest_key=lambda office, district: office,   # office (Council/Mayor) == body (at-large)
    crosscheck_field="body", winners_have_district=False,
    elected_events=("elected", "became-mayor", "reelected"),
    atlarge=ATLARGE,
)


# ---------------------------------------------------------------------------
# Demo queries (Lehi presentation)
# ---------------------------------------------------------------------------
def demo():
    def line(r):
        end = r["end_date"] or "—(serving)"
        return (f"  {r['seat_id']:<6} {r['person_name']:<16} {r['start_date']} -> {end:<12} "
                f"[{r['start_event']}/{r['end_event']}] conf={r['confidence']}")

    print("\n(a) CURRENT council roster + mayor (end_date empty, end_event=serving):")
    for r in roster_lib.load_terms(CFG):
        if not r["end_date"] and r["end_event"] == "serving":
            print(line(r))

    print("\n(b) Roster AS OF 2025-12-18 (during the Albrecht->Lockhart VACANT window):")
    for r in roster_lib.roster_as_of(CFG, "2025-12-18", body="Council"):
        print(line(r))
    print("    Mayor:")
    for r in roster_lib.roster_as_of(CFG, "2025-12-18", body="Mayor"):
        print(line(r))

    print("\n(b') Roster AS OF 2022-07-01 (mid Johnson-2/Condie-2/Hancock-2 + 2019 cohort A):")
    for r in roster_lib.roster_as_of(CFG, "2022-07-01", body="Council"):
        print(line(r))

    print("\n(c) address+date -> representative (degenerate At-Large -> all members + mayor):")
    for d in ("2022-07-01", "2026-06-01"):
        dist, reps = roster_lib.representatives_for_address(
            CFG, "153 North 100 East, Lehi, UT 84043", d)
        who = ", ".join(f"{x['person_name']}({x['body']})" for x in reps)
        print(f"  '153 N 100 E' on {d}: district={dist} -> {who}")


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
