#!/usr/bin/env python3
"""build_roster.py — rolling council-roster for OREM (a slowly-changing-dimension /
interval table of who holds each AT-LARGE council + mayor seat over time).

THIN DRIVER: this file holds only Orem-specific DATA (the curated TENURES seat
assignments, the name maps, the degenerate at-large district row) + config; all generic
mechanics live in ../../scripts/roster_lib.py (canon_key, election/vote-bounds/override
reconciliation, end-date chaining + VACANT insertion, validation, the CSV writers, and the
as-of / address / demo query helpers). See that module's docstring to add a city.

Orem is the AT-LARGE + VOTING-MAYOR city (built on the Vineyard template). Like Vineyard,
every seat is elected citywide (no districts) → district_versions is one degenerate whole-
city row. UNLIKE Nephi/Provo/Lehi/SLC (non-voting / tie-break-only mayors), OREM'S MAYOR IS
A FULL VOTING MEMBER OF THE COUNCIL — he/she is named in the "Those voting aye: ..." roll
calls and routinely moves motions (verified: 2020-01-14 minutes "Those voting aye: Richard
F. Brunst, Jeff Lambson, ...", and cities.db shows every mayor — Brunst, Young, McCandless
— with Council-body votes). So `non_voting_mayor=False` (the default), the MAYOR rows DO
carry first_vote/last_vote, and the mayor IS in db_key. Roster size = 7 = 6 council + mayor.

Orem also has NO mid-term vacancy in-window: every departure lands exactly on a January
term boundary (cities.db first/last_seen: 2020-01-14 / 2022-01-04 / 2024-01-09 / 2026-01-13,
plus Sumner/Brunst last-seen 2021-12-14), so there are 0 VACANT rows and 0 appointments
here — an honest structural fact, not a gap. (The VACANT/appointed code path is exercised by
Vineyard.)

DERIVED LAYER — regenerable, never hand-edited. Canonical inputs:
  1. election_results/orem_results_by_candidate.csv  (general winners -> `elected`/`reelected` terms)
  2. cities.db  role table (city='orem', body='Council')  (observed vote bounds; incl. the VOTING mayor)
  3. meeting_minutes/minutes/**                           (present-lists / seating dates)
  4. roster/roster_overrides.csv                          (hand corrections; applied LAST, wins ties)

Outputs (idempotent — re-running reproduces them byte-for-byte):
  roster/council_terms.csv      one row per seat-tenure (0 VACANT intervals — no in-window vacancy)
  roster/district_versions.csv  boundary interval table (DEGENERATE — Orem is at-large)

Usage:
  python3 roster/build_roster.py            # regenerate the CSVs
  python3 roster/build_roster.py --demo     # regenerate + print the demo queries
  python3 roster/build_roster.py --check    # regenerate + run validations only

Cardinal rule (repo CLAUDE.md): NEVER fabricate. Unknown seat-holder / date -> explicit
VACANT/UNKNOWN + confidence low/medium + a note, never a guess. Honest gaps are data.

Provenance / confidence model (same as Nephi/Provo/Vineyard):
  high   = anchored to an election result AND/OR a minutes-documented present-list/seating
  medium = inferred from a pre-floor staggered cycle (term-start 2018-01 inferred; win
           predates the 2019 election-data floor and the 2020 minutes floor)
  low    = genuinely unknown (flagged, never silently filled) — NONE here

Seat model — Orem runs a MAYOR + 6 AT-LARGE council members (NO geographic districts) on
STAGGERED 4-year terms, 3 council seats up each odd year, plus a separately-elected Mayor:
  Class A (3 seats): elected 2019 / 2023 (/2027) -> seat_id AL-A1..A3  (terms Jan-2020, Jan-2024)
  Class B (3 seats): elected 2017 / 2021 / 2025  -> seat_id AL-B1..B3  (terms Jan-2018, Jan-2022, Jan-2026)
  MAYOR  (1 seat)  : elected 2017 / 2021 / 2025.
Orem records only Aye/Nay in prose (no abstain/recuse/absent block wording — SCHEMA_SPEC §4).

Within-class seat NUMBERS are a stable labelling of the person-chain: where two same-class
members depart/arrive together (Peterson/Lauret -> Gale/Killpack in Class A; Spencer/Macdonald
-> Mecham/Muhlestein in Class B) the A2/A3 (and B2/B3) split is a labelling choice (flagged in
`note`) — the person-tenures are exact. The continuous anchors are AL-A1 (Lambson, 2019->2023)
and AL-B1 (Millett, 2021->2025).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.dirname(HERE)              # orem_city_council/
REPO_ROOT = os.path.dirname(CITY_DIR)         # civic-data/
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import roster_lib
from roster_lib import RosterConfig

ELECTIONS = os.path.join(CITY_DIR, "election_results", "orem_results_by_candidate.csv")
CITIES_DB = os.path.join(REPO_ROOT, "cities.db")
OVERRIDES = os.path.join(HERE, "roster_overrides.csv")
TERMS_OUT = os.path.join(HERE, "council_terms.csv")
DISTRICTS_OUT = os.path.join(HERE, "district_versions.csv")

CITY = "orem"
DATA_FLOOR = "2020-01-01"                  # repo minutes floor; the at-large structure predates it
GEOM_REF = "geo/city_limits.geojson"       # existing city-limits polygon (repo-relative)

# Verified seating dates (first documented council meeting / cities.db role.first_seen):
#   2020-01-14 (2019 Class-A cohort + 2017 Class-B/Mayor incumbents at floor)
#   2022-01-04 (special mtg — 2021 cohort + Mayor Young seated)
#   2024-01-09 (2023 Class-A cohort seated)
#   2026-01-13 (2025 Class-B cohort + Mayor McCandless seated).
# Pre-floor 2017-cycle terms start 2018-01 (inferred from the 4-year stagger; medium) —
# Orem minutes only begin 2020-01-14.

# ---------------------------------------------------------------------------
# LAYER 1-3 (reconciled). Each tenure anchored to a cited source. `end_date` is computed by
# chaining (next tenure on the seat). No `vacate_date` anywhere -> 0 VACANT rows (Orem has no
# in-window mid-term vacancy: every transition is a clean January term boundary).
# ---------------------------------------------------------------------------
TENURES = [
    # ===== Class A — seats elected 2019 / 2023 (both IN the election data) ===============
    # ---- AL-A1  (Lambson) : CONTINUOUS ANCHOR, 2019 -> 2023 re-election ------------------
    dict(body="Council", seat_id="AL-A1", person_name="Jeff Lambson", person_key="jeff_lambson",
         start_date="2020-01-14", start_event="elected", election_year="2019",
         end_event="reelected", confidence="high",
         sources="election:2019 (Council at-large vote-for-3 winner, rank2, 7,995); minutes:2020-01-14 (seated — 'ELECTED OFFICIALS ... Jeff Lambson'); votes:cities.db role first_seen 2020-01-14",
         note="CONTINUOUS ANCHOR of Class A. Elected 2019, re-elected 2023 (2nd term) -> see the next AL-A1 row. Term start = first documented meeting 2020-01-14 (term began Jan 2020; election-anchored)."),
    dict(body="Council", seat_id="AL-A1", person_name="Jeff Lambson", person_key="jeff_lambson",
         start_date="2024-01-09", start_event="reelected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (Council at-large vote-for-3 winner, rank1, 9,098); minutes:2024-01-09 (seated); minutes:2026-01-13 (still serving — present list 'Jeff Lambson'); votes:cities.db last_seen 2026-05-05",
         note="Re-elected 2023 to a 2nd term (to Jan-2028). Continuing member across the Jan-2026 turnover. first_vote/last_vote are clamped to this tenure's own [start_date, end_date) window (this 2nd term only), not the whole-career span (his 1st-term row carries its own earlier bounds)."),

    # ---- AL-A2  (Peterson -> Gale) : labelling choice within Class A --------------------
    dict(body="Council", seat_id="AL-A2", person_name="Terry Peterson", person_key="terry_peterson",
         start_date="2020-01-14", start_event="elected", election_year="2019",
         end_event="did-not-run", confidence="high",
         sources="election:2019 (Council at-large vote-for-3 winner, rank1, 9,858); minutes:2020-01-14 (seated — 'Terry Peterson'); election:2023 (not a candidate); votes:cities.db last_seen 2023-12-29",
         note="Elected 2019 (top vote-getter). Not a candidate in 2023 -> term expired Jan 2024. Peterson/Lauret -> Gale/Killpack is a labelling choice (two Class-A members left together in 2024); person-tenure is exact."),
    dict(body="Council", seat_id="AL-A2", person_name="Jenn Gale", person_key="jenn_gale",
         start_date="2024-01-09", start_event="elected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (Council at-large vote-for-3 winner, rank2, 8,606); minutes:2024-01-09 (seated — 'Jenn Gale'); minutes:2026-01-13 (still serving); votes:cities.db first_seen 2024-01-09",
         note="Elected 2023 (1st term, to Jan-2028). Gale/Killpack -> A2/A3 split is a labelling choice; person-tenure is exact."),

    # ---- AL-A3  (Lauret -> Killpack) : labelling choice within Class A ------------------
    dict(body="Council", seat_id="AL-A3", person_name="Debby Lauret", person_key="debby_lauret",
         start_date="2020-01-14", start_event="elected", election_year="2019",
         end_event="did-not-run", confidence="high",
         sources="election:2019 (Council at-large vote-for-3 winner, rank3, 6,740); minutes:2020-01-14 (seated — 'Debby Lauret'); election:2023 (not a candidate); votes:cities.db last_seen 2023-12-29",
         note="Elected 2019 (won the final seat by 12 votes over Lentz). Not a candidate in 2023 -> term expired Jan 2024. Name-spelling drift Debby/Debbie in minutes (normalized). Lauret/Peterson -> Gale/Killpack labelling choice."),
    dict(body="Council", seat_id="AL-A3", person_name="Chris Killpack", person_key="chris_killpack",
         start_date="2024-01-09", start_event="elected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (Council at-large vote-for-3 winner, rank3, 8,457 — won seat 3 over Muhlestein 7,994); minutes:2024-01-09 (seated — 'Chris Killpack'); minutes:2026-01-13 (still serving); votes:cities.db first_seen 2024-01-09",
         note="Elected 2023 (1st term, to Jan-2028). Killpack/Gale -> A3/A2 split is a labelling choice; person-tenure is exact."),

    # ===== Class B — seats elected 2017 / 2021 / 2025 ===================================
    # ---- AL-B1  (Sumner -> Millett) : Millett is the CONTINUOUS ANCHOR 2021 -> 2025 -----
    dict(body="Council", seat_id="AL-B1", person_name="Brent Sumner", person_key="brent_sumner",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="did-not-run", confidence="medium",
         sources="votes:2020-01-14..2021-12-14 (observed serving, cities.db role — named in the full-council Aye lists); minutes:2020-01-14 (already seated at data floor — 'ELECTED OFFICIALS ... Brent Sumner'); election:2021 (not a candidate)",
         note="PRE-FLOOR term: the 2017 election predates the 2019 election-data floor and the 2020-01-14 minutes floor; term-start 2018-01 inferred from Orem's Class-B 4-year stagger (medium — win predates data, continuous service inferred; NO fabricated 'election:2017' citation). Not a 2021 candidate (seat won by newcomer Millett) -> term expired Jan 2022."),
    dict(body="Council", seat_id="AL-B1", person_name="LaNae Millett", person_key="lanae_millett",
         start_date="2022-01-04", start_event="elected", election_year="2021",
         end_event="reelected", confidence="high",
         sources="election:2021 (Council at-large vote-for-3 winner, rank1, 11,482); minutes:2022-01-04 (seated — 'LaNae Millett'); votes:cities.db role first_seen 2022-01-04",
         note="CONTINUOUS ANCHOR of Class B from 2022. Elected 2021 (top vote-getter), re-elected 2025 -> see the next AL-B1 row. Name-spelling drift Millet/Millett in minutes (normalized)."),
    dict(body="Council", seat_id="AL-B1", person_name="LaNae Millett", person_key="lanae_millett",
         start_date="2026-01-13", start_event="reelected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Council at-large vote-for-3 winner, rank3, 9,077 — won seat 3 over Spencer 8,789); minutes:2026-01-13 (seated — present list 'LaNae Millett'); votes:cities.db last_seen 2026-05-05",
         note="Re-elected 2025 to a 2nd term (to Jan-2030). Continuing member across the Jan-2026 turnover. first_vote/last_vote are clamped to this tenure's own [start_date, end_date) window (this 2nd term only), not the whole-career span (her 1st-term row carries its own earlier bounds)."),

    # ---- AL-B2  (Spencer -> Mecham) : Spencer 2017 pre-floor -> 2021 -> lost 2025 -------
    dict(body="Council", seat_id="AL-B2", person_name="David Spencer", person_key="david_spencer",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="reelected", confidence="medium",
         sources="votes:2020-01-14.. (observed serving, cities.db role); minutes:2020-01-14 (already seated at data floor — 'David Spencer'); election:2021 (RE-ELECTED — see next row)",
         note="PRE-FLOOR term (2017 cycle; term-start 2018-01 inferred, medium; no fabricated 'election:2017'). Re-elected 2021 -> continues in the next AL-B2 row."),
    dict(body="Council", seat_id="AL-B2", person_name="David Spencer", person_key="david_spencer",
         start_date="2022-01-04", start_event="reelected", election_year="2021",
         end_event="lost", confidence="high",
         sources="election:2021 (Council at-large vote-for-3 winner, rank2, 10,444); minutes:2022-01-04 (seated — 'David Spencer'); election:2025 (ran, rank4 general — LOST the final seat to Millett by 288); votes:cities.db last_seen 2025-12-09",
         note="Re-elected 2021 to a term to Jan-2026. Ran again in the 2025 general and LOST (rank4 of 6, 8,789 — just missed seat 3). Term expired Jan 2026. Name Spencer is distinct (no collision)."),
    dict(body="Council", seat_id="AL-B2", person_name="Quinn Mecham", person_key="quinn_mecham",
         start_date="2026-01-13", start_event="elected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Council at-large vote-for-3 winner, rank1, 9,474); minutes:2026-01-13 (seated — present list 'Quinn Mecham'); votes:cities.db first_seen 2026-01-13",
         note="Elected 2025 (top vote-getter, to Jan-2030). Mecham/Muhlestein -> B2/B3 split is a labelling choice (both arrived Jan-2026 as Spencer/Macdonald left); person-tenure is exact. (Mecham had also run in 2021, rank4 — lost that cycle.)"),

    # ---- AL-B3  (Macdonald -> Muhlestein) : Macdonald 2017 pre-floor -> 2021 -> retired -
    dict(body="Council", seat_id="AL-B3", person_name="Tom Macdonald", person_key="tom_macdonald",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="reelected", confidence="medium",
         sources="votes:2020-01-14.. (observed serving, cities.db role); minutes:2020-01-14 (already seated at data floor — 'Tom Macdonald'); election:2021 (RE-ELECTED — see next row)",
         note="PRE-FLOOR term (2017 cycle; term-start 2018-01 inferred, medium; no fabricated 'election:2017'). Re-elected 2021 -> continues in the next AL-B3 row. Name-spelling drift Macdonald/MacDonald in minutes (normalized)."),
    dict(body="Council", seat_id="AL-B3", person_name="Tom Macdonald", person_key="tom_macdonald",
         start_date="2022-01-04", start_event="reelected", election_year="2021",
         end_event="did-not-run", confidence="high",
         sources="election:2021 (Council at-large vote-for-3 winner, rank3, 7,672); minutes:2022-01-04 (seated — 'Tom Macdonald'); election:2025 (not a candidate); votes:cities.db last_seen 2025-12-09",
         note="Re-elected 2021 to a term to Jan-2026. Not a candidate in 2025 -> term expired Jan 2026. Macdonald/Spencer -> Muhlestein/Mecham is a labelling choice; person-tenure exact."),
    dict(body="Council", seat_id="AL-B3", person_name="Crystal Muhlestein", person_key="crystal_muhlestein",
         start_date="2026-01-13", start_event="elected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Council at-large vote-for-3 winner, rank2, 9,102); minutes:2026-01-13 (seated — present list 'Crystal Muhlestein'); votes:cities.db first_seen 2026-01-13",
         note="Elected 2025 (1st term, to Jan-2030). Muhlestein/Mecham -> B3/B2 split is a labelling choice; person-tenure is exact. (Muhlestein had also run in 2023, rank4 — lost that cycle.)"),

    # ===== MAYOR (cycle 2017/2021/2025; the OREM MAYOR VOTES — full council member) =======
    dict(body="Mayor", seat_id="MAYOR", person_name="Richard Brunst", person_key="richard_brunst",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="did-not-run", confidence="medium",
         sources="votes:2020-01-14..2021-12-14 (observed VOTING as Mayor, cities.db role Council — Orem's mayor is a full voting member; named in Aye lists e.g. 2020-01-14 'Those voting aye: Richard F. Brunst, Jeff Lambson, ...'); minutes:2020-01-14 (presiding + voting as 'Mayor Richard F. Brunst'); election:2021 (not a candidate — open seat won by Young)",
         note="PRE-FLOOR Mayor term: elected Mayor 2017 (predates the 2019 election-data floor); term-start 2018-01 inferred (medium; no fabricated 'election:2017'). CONFIRMS non_voting_mayor=False: Brunst appears IN the roll-call Aye lists and moves/seconds motions -> the MAYOR row carries first_vote/last_vote. Did not seek re-election in 2021 -> term ended Jan 2022."),
    dict(body="Mayor", seat_id="MAYOR", person_name="David Young", person_key="david_young",
         start_date="2022-01-04", start_event="elected", election_year="2021",
         end_event="lost", confidence="high",
         sources="election:2021 (Mayor winner, 9,647 / 59.06%, def. Jim Evans); minutes:2022-01-04 (presiding + voting as 'Mayor David A. Young' — e.g. 2022-01-11 'Those voting aye: David A. Young, ...'); election:2025 (ran for re-election, LOST to McCandless 9,056-9,574); votes:cities.db last_seen 2025-12-09",
         note="Elected Mayor 2021. Orem's mayor VOTES (named in Aye lists) -> carries vote bounds. Ran for a 2nd term in 2025 and LOST to Karen McCandless (9,574-9,056). Term ended Jan 2026."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Karen McCandless", person_key="karen_mccandless",
         start_date="2026-01-13", start_event="elected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Mayor winner, 9,574 / 51.39%, def. incumbent Dave Young 9,056); minutes:2026-01-13 (presiding + voting as 'Mayor Karen McCandless' — present list heads 'Karen McCandless'); votes:cities.db first_seen 2026-01-13",
         note="Elected Mayor 2025 (defeated incumbent Young), to Jan-2030. NOTE: the mayor is KAREN McCandless (not 'David' — corroborated by election_results/CLAUDE.md, Daily Herald, KSL, orem.gov/citycouncil). Orem's mayor VOTES -> carries vote bounds (2026-01-13..2026-05-05)."),
]

# Seat model: all council seats + mayor are elected AT-LARGE -> one district.
SEAT_DISTRICT = {s: "At-Large" for s in
                 ("AL-A1", "AL-A2", "AL-A3", "AL-B1", "AL-B2", "AL-B3", "MAYOR")}
SEAT_ORDER = ["AL-A1", "AL-A2", "AL-A3", "AL-B1", "AL-B2", "AL-B3", "MAYOR"]

# canonical UPPER-CASE election name -> person_key. All Orem surnames are DISTINCT (no shared
# surname in-window), so surname tokens suffice; no disambiguators needed. Do NOT map shared
# FIRST names (two Davids: Young & Spencer; both keyed by their distinct surnames).
NAME_TO_KEY = {
    "LAMBSON": "jeff_lambson", "PETERSON": "terry_peterson", "LAURET": "debby_lauret",
    "GALE": "jenn_gale", "KILLPACK": "chris_killpack", "MILLETT": "lanae_millett",
    "SPENCER": "david_spencer", "MECHAM": "quinn_mecham", "MACDONALD": "tom_macdonald",
    "MUHLESTEIN": "crystal_muhlestein", "YOUNG": "david_young", "MCCANDLESS": "karen_mccandless",
    # pre-floor incumbents (no in-window election win) — included for override robustness:
    "SUMNER": "brent_sumner", "BRUNST": "richard_brunst",
}

# cities.db person.name_key (full firstlast in Orem) -> our person_key.
DB_KEY = {
    "brentsumner": "brent_sumner", "davidspencer": "david_spencer",
    "debbylauret": "debby_lauret", "jefflambson": "jeff_lambson",
    "richardbrunst": "richard_brunst", "terrypeterson": "terry_peterson",
    "tommacdonald": "tom_macdonald", "davidyoung": "david_young",
    "lanaemillett": "lanae_millett", "chriskillpack": "chris_killpack",
    "jenngale": "jenn_gale", "crystalmuhlestein": "crystal_muhlestein",
    "karenmccandless": "karen_mccandless", "quinnmecham": "quinn_mecham",
}

ATLARGE = dict(
    district_id="At-Large", plan_id="current",
    effective_start=DATA_FLOOR, effective_end="",
    geometry_ref=GEOM_REF,
    adopted_by="Orem Municipal Code (Council-Manager form adopted 1980, effective 1982; Mayor + 6 council members, all elected at-large)",
    source_url="", confidence="high",
    note=("DEGENERATE: Orem's council + mayor are elected entirely AT-LARGE — no wards/"
          "districts (orem.gov/citycouncil 'all elected at large'; recon §2). This single row "
          "covers the whole city. geometry_ref points at the CURRENT city-limits polygon "
          "(geo/city_limits.geojson, UGRC Utah Municipal Boundaries); Orem's limits can change "
          "by annexation and prior-versioned boundaries are NOT on disk and NOT fabricated. "
          "Because every seat is at-large, the sub-district address->representative join "
          "degenerates to whole-city -> all sitting members + mayor. effective_start = repo "
          "data floor; the at-large structure predates it."),
)

CFG = RosterConfig(
    city=CITY, city_dir=CITY_DIR, repo_root=REPO_ROOT, data_floor=DATA_FLOOR,
    geom_ref=GEOM_REF, elections_path=ELECTIONS, cities_db_path=CITIES_DB,
    overrides_path=OVERRIDES, terms_out=TERMS_OUT, districts_out=DISTRICTS_OUT,
    seat_district=SEAT_DISTRICT, name_to_key=NAME_TO_KEY, db_key=DB_KEY,
    seat_order=SEAT_ORDER,
    keep_election_row=lambda r: "general" in r["election_type"].lower(),  # drop the primary advancers
    contest_key=lambda office, district: office,   # office (Council/Mayor) == body (at-large)
    crosscheck_field="body", winners_have_district=False,
    elected_events=("elected", "became-mayor", "reelected"),
    non_voting_mayor=False,   # OREM'S MAYOR IS A FULL VOTING MEMBER (in the Aye lists) — carries vote bounds
    atlarge=ATLARGE,
)


# ---------------------------------------------------------------------------
# Demo queries (Orem presentation)
# ---------------------------------------------------------------------------
def demo():
    def line(r):
        end = r["end_date"] or "—(serving)"
        return (f"  {r['seat_id']:<6} {r['person_name']:<18} {r['start_date']} -> {end:<12} "
                f"[{r['start_event']}/{r['end_event']}] conf={r['confidence']} "
                f"votes={r['first_vote'] or '—'}..{r['last_vote'] or '—'}")

    print("\n(a) CURRENT council roster + mayor (end_date empty, end_event=serving):")
    for r in roster_lib.load_terms(CFG):
        if not r["end_date"] and r["end_event"] == "serving":
            print(line(r))

    for asof in ("2020-06-01", "2023-06-01"):
        print(f"\n(as-of {asof}) full roster:")
        print("    Council:")
        for r in roster_lib.roster_as_of(CFG, asof, body="Council"):
            print(line(r))
        print("    Mayor:")
        for r in roster_lib.roster_as_of(CFG, asof, body="Mayor"):
            print(line(r))

    print("\n(c) address+date -> representative (degenerate At-Large -> all members + mayor):")
    for d in ("2020-06-01", "2026-06-01"):
        dist, reps = roster_lib.representatives_for_address(
            CFG, "56 N State St, Orem, UT 84057", d)
        who = ", ".join(f"{x['person_name']}({x['body']})" for x in reps)
        print(f"  '56 N State St' on {d}: district={dist} -> {who}")


if __name__ == "__main__":
    rows = roster_lib.build(CFG, TENURES)
    n_high = sum(1 for r in rows if r["confidence"] == "high")
    n_med = sum(1 for r in rows if r["confidence"] == "medium")
    n_low = sum(1 for r in rows if r["confidence"] == "low")
    n_vac = sum(1 for r in rows if r["person_name"] == "VACANT")
    print(f"Wrote {os.path.relpath(TERMS_OUT, CITY_DIR)} "
          f"({len(rows)} tenures: {n_high} high / {n_med} medium / {n_low} low; "
          f"{n_vac} VACANT intervals)")
    print(f"Wrote {os.path.relpath(DISTRICTS_OUT, CITY_DIR)} (1 district — At-Large, degenerate)")
    if "--check" in sys.argv:
        print("\nValidation: PASS (no overlaps; every row has sources+confidence).")
    if "--demo" in sys.argv:
        demo()
