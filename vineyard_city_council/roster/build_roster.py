#!/usr/bin/env python3
"""build_roster.py — rolling council-roster for VINEYARD (a slowly-changing-
dimension / interval table of who holds each at-large council + mayor seat over time).

THIN DRIVER: this file holds only Vineyard-specific DATA (the curated TENURES seat
assignments with the two MID-TERM APPOINTMENTS, the name maps, the at-large district
row) + config; all generic mechanics live in ../../scripts/roster_lib.py (canon_key,
election/vote-bounds/override reconciliation, end-date chaining + VACANT insertion,
validation, the CSV writers, and the as-of / address / demo query helpers). See that
module's docstring to add a city.

Vineyard is the city that finally EXERCISES the VACANT/appointed path that neither Nephi
(at-large, no in-window vacancy) nor Provo (district, no in-window vacancy) could: two
councilmembers left mid-term and were replaced by council APPOINTMENT, so the
`person_name=VACANT` interval + `appointed` tenure both actually produce rows here.

DERIVED LAYER — regenerable, never hand-edited. Canonical inputs:
  1. election_results/vineyard_results_by_candidate.csv  (general winners -> `elected` terms)
  2. cities.db  role table (city='vineyard', body='Council')  (observed vote bounds; appointee detection)
  3. meeting_minutes/minutes/**                           (appointment/oath/vacancy events)
  4. roster/roster_overrides.csv                          (hand corrections; applied LAST, wins ties)

Outputs (idempotent — re-running reproduces them byte-for-byte):
  roster/council_terms.csv      one row per seat-tenure (incl. 2 VACANT intervals)
  roster/district_versions.csv  boundary interval table (DEGENERATE — Vineyard is at-large)

Usage:
  python3 roster/build_roster.py            # regenerate the CSVs
  python3 roster/build_roster.py --demo     # regenerate + print the demo queries
  python3 roster/build_roster.py --check    # regenerate + run validations only

Cardinal rule (repo CLAUDE.md): NEVER fabricate. Unknown seat-holder / date / reason ->
explicit VACANT/UNKNOWN + confidence low/medium + a note, never a guess. Honest gaps are data.

Provenance / confidence model (same as Nephi/Provo):
  high   = anchored to an election result OR a minutes-documented appointment/oath/vacancy
  medium = inferred from a pre-floor staggered cycle, or bounded by documented service
           across an un-recovered minutes gap
  low    = genuinely unknown (flagged, never silently filled)

Seat model — Vineyard runs an ALL-AT-LARGE council (NO geographic districts) on STAGGERED
4-year terms, plus a separately-elected Mayor:
  Cohort A (2 seats): elected 2019 / 2023 (/2027) -> seat_id AL-A1, AL-A2  (terms Jan-2020, Jan-2024)
  Cohort B (2 seats): elected 2017 / 2021 / 2025  -> seat_id AL-B1, AL-B2  (terms Jan-2018, Jan-2022, Jan-2026)
  Seat  C (1 seat) : NEW 5th seat added by Prop 10 (2024 ballot), first filled 2025 ->
                     seat_id AL-C. McCumber drew a 2-YEAR term BY LOT to stagger it onto the
                     odd-year (Cohort-A / 2027) cycle.
  MAYOR (1 seat)   : elected 2017 / 2021 / 2025.
Vineyard's Mayor VOTES in roll calls (unlike Nephi's/Provo's non-voting mayors) — so the
Mayor rows DO carry first_vote/last_vote from cities.db (Fullmer 973 council-body votes;
Stratton named in the 2026-02-03 special-session roll call — see the MAYOR notes).

Within-cohort seat NUMBERS are a stable labelling of the person-chain; where two same-cohort
newcomers arrive together the A1/A2 (and B1/B2) split is a labelling choice (flagged in
`note`) — the person-tenures are exact. The two vacancy chains ANCHOR one seat each:
AL-A2 = Cameron->Nair, AL-B2 = Rasmussen->Clawson.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.dirname(HERE)              # vineyard_city_council/
REPO_ROOT = os.path.dirname(CITY_DIR)         # civic-data/
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import roster_lib
from roster_lib import RosterConfig

ELECTIONS = os.path.join(CITY_DIR, "election_results", "vineyard_results_by_candidate.csv")
CITIES_DB = os.path.join(REPO_ROOT, "cities.db")
OVERRIDES = os.path.join(HERE, "roster_overrides.csv")
TERMS_OUT = os.path.join(HERE, "council_terms.csv")
DISTRICTS_OUT = os.path.join(HERE, "district_versions.csv")

CITY = "vineyard"
DATA_FLOOR = "2020-01-01"                  # repo minutes floor; the at-large structure predates it
GEOM_REF = "geo/city_limits.geojson"       # existing city-limits polygon (repo-relative)

# Verified seating dates (first council meeting of the term year; match cities.db
# role.first_seen and the minutes present-lists):
#   2020-01-08 · 2022-01-12 · 2024-01-10 · 2026-01-14. Pre-floor 2017-cycle terms start
#   2018-01 (inferred, medium) — Vineyard minutes only begin 2020. The Clawson appointment
#   is dated exactly from the 2024-11-20 special session.

# ---------------------------------------------------------------------------
# LAYER 1-3 (reconciled). Each tenure anchored to a cited source. `end_date` is computed
# by chaining (next tenure on the seat) unless a departure reason must be stated; a
# `vacate_date` (+ `vacate_source`) on a tenure triggers roster_lib's explicit VACANT row.
# ---------------------------------------------------------------------------
TENURES = [
    # ===== Cohort A — seats elected 2019 / 2023 (both IN the election data) =============
    # ---- AL-A1  (Welsh -> Holdaway) : continuous, no vacancy -----------------
    dict(body="Council", seat_id="AL-A1", person_name="Cristy Welsh", person_key="cristy_welsh",
         start_date="2020-01-08", start_event="elected", election_year="2019",
         end_event="lost", confidence="high",
         sources="election:2019 (Council RCV, Seat 1 winner, 347 first-choice rank1); minutes:2020-01-08 (seated — 'Mayor Julie Fullmer, Councilmembers Tyce Flake, Chris Judd, and Cristy Welsh'); election:2023 (ran, rank3 — lost)",
         note="DISTINCT surname 'Welsh' — keep full/distinct. Re-ran in 2023 and LOST (rank3 of 7); term expired Jan 2024. A1 vs A2 split of the 2019 pair (Welsh/Flake) is a labelling choice; anchored here because A2 carries the Cameron->Nair vacancy chain."),
    dict(body="Council", seat_id="AL-A1", person_name="Jacob Holdaway", person_key="jacob_holdaway",
         start_date="2024-01-10", start_event="elected", election_year="2023",
         end_event="serving", confidence="high",
         sources="election:2023 (Council RCV winner, 1097 final-round rank1); minutes:2024-01-10 (seated); minutes:2026-01-14 (still serving — present list)",
         note="DISTINCT from Jacob Wood (AL-B1): two different Jacobs — never merge. Continuing member across the Jan-2026 turnover."),

    # ---- AL-A2  (Flake -> Cameron -> [VACANT] -> Nair) : MID-TERM APPOINTMENT #2 --------
    dict(body="Council", seat_id="AL-A2", person_name="Tyce Flake", person_key="tyce_flake",
         start_date="2020-01-08", start_event="elected", election_year="2019",
         end_event="did-not-run", confidence="high",
         sources="election:2019 (Council RCV, Seat 2 winner, 277 first-choice rank2); minutes:2020-01-08 (seated); election:2023 (not a candidate)",
         note="Elected 2019 (RCV Seat 2). Not a candidate in 2023 (won by Holdaway/Cameron) -> term expired Jan 2024. A1/A2 split of the 2019 pair is a labelling choice."),
    dict(body="Council", seat_id="AL-A2", person_name="Sara Cameron", person_key="sara_cameron",
         start_date="2024-01-10", start_event="elected", election_year="2023",
         end_event="resigned", confidence="medium",
         sources="election:2023 (Council RCV winner, 907 final-round); minutes:2024-01-10 (seated); minutes:2025-10-22 (last documented service — present + voting); election_results/CLAUDE.md cross-check + vineyardutah.gov council page (Cameron resigned, Ezra Nair appointed ~Nov 2025)",
         vacate_date="2025-10-22", vacate_confidence="medium",
         vacate_source="Cameron resigned ~Nov 2025 (election_results cross-check + city council page). EXACT resignation & Nair-appointment dates fall in the 2025-11/12 minutes GAP: no Nov-2025 council minutes were recovered and 2025-12-10 is unrecoverable (minutes_unrecovered.csv). VACANT interval bounded by Cameron's last documented service (2025-10-22) and Nair's first documented seating (2026-01-14).",
         note="MID-TERM VACANCY #2. Elected 2023 to a term running to Jan-2028; resigned mid-term. The resignation/appointment minutes are in an un-recovered gap, so the VACANT window is documented-service-bounded, not exact (medium on the dates, high on the fact). By 2026-01-14 Cameron appears only in 'Others Speaking' (a resident), confirming her departure."),
    dict(body="Council", seat_id="AL-A2", person_name="Ezra Nair", person_key="ezra_nair",
         start_date="2026-01-14", start_event="appointed", election_year="",
         end_event="serving", confidence="high",
         sources="appt:~Nov-2025 (council-appointed to fill Cameron's vacated seat — election_results/CLAUDE.md cross-check + vineyardutah.gov); minutes:2026-01-14 (first documented seating — present list 'Councilmember Ezra Nair'); votes:cities.db first_seen 2026-01-14",
         note="APPOINTED (not elected — Nair was NOT a 2025 winner; he was applicant #10 at the 2024-11-20 vacancy interview and was later appointed to Cameron's seat). start_date = first DOCUMENTED seating (2026-01-14); the actual ~Nov-2025 appointment/oath minutes are in the recovery gap, so the precise oath date is not on disk (NOT fabricated). Fills the remainder of Cameron's 2024-2027(8) term."),

    # ===== Cohort B — seats elected 2017 / 2021 / 2025 ==================================
    # ---- AL-B1  (Earnest -> Sifuentes -> Wood) : continuous, no vacancy ------
    dict(body="Council", seat_id="AL-B1", person_name="John Earnest", person_key="john_earnest",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="did-not-run", confidence="medium",
         sources="votes:2020-01-08..2021-12-30 (observed serving, cities.db role); minutes:2020-01-08 (already seated at data floor — 'Councilmember John Earnest'); election:2021 (not a candidate)",
         note="PRE-FLOOR term: the 2017 election predates the 2019 election-data floor and the 2020 minutes floor; term-start 2018-01 inferred from Vineyard's Cohort-B 4-year stagger (medium). Not a 2021 candidate (seat won by Sifuentes/Rasmussen) -> term expired Jan 2022. Earnest/Judd -> Sifuentes/Rasmussen pairing is a labelling choice."),
    dict(body="Council", seat_id="AL-B1", person_name="Mardi Sifuentes", person_key="mardi_sifuentes",
         start_date="2022-01-12", start_event="elected", election_year="2021",
         end_event="did-not-run", confidence="high",
         sources="election:2021 (Council RCV, Seat 1 winner, 764 final-round); minutes:2022-01-12 (seated); election:2025 (ran for MAYOR, lost to Stratton 1173-1417); minutes:2025-10-22 (last served)",
         note="Elected to Council 2021. Did NOT seek council re-election in 2025 — she ran for MAYOR instead and LOST (Stratton won the open seat). Council term expired Jan 2026."),
    dict(body="Council", seat_id="AL-B1", person_name="Jacob Wood", person_key="jacob_wood",
         start_date="2026-01-14", start_event="elected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Council plurality vote-for-3 winner, 1389 rank2, 4-year term); minutes:2026-01-14 (seated)",
         note="DISTINCT from Jacob Holdaway (AL-A1). Won a 4-YEAR seat in the 2025 vote-for-3 (Wood/Lauret = the two 4-yr Cohort-B seats; McCumber drew the 2-yr AL-C seat). Wood/Lauret -> B1/B2 split is a labelling choice; the person-tenures are exact."),

    # ---- AL-B2  (Judd -> Rasmussen -> [VACANT] -> Clawson -> Lauret) : MID-TERM APPT #1 -
    dict(body="Council", seat_id="AL-B2", person_name="Chris Judd", person_key="chris_judd",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="did-not-run", confidence="medium",
         sources="votes:2020-01-08..2021-12-30 (observed serving, cities.db role); minutes:2020-01-08 (already seated at data floor — 'Councilmember Chris Judd'); election:2021 (not a candidate)",
         note="PRE-FLOOR term (2017 cycle; term-start 2018-01 inferred, medium). Not a 2021 candidate -> term expired Jan 2022. Earnest/Judd -> Sifuentes/Rasmussen pairing is a labelling choice."),
    dict(body="Council", seat_id="AL-B2", person_name="Amber Rasmussen", person_key="amber_rasmussen",
         start_date="2022-01-12", start_event="elected", election_year="2021",
         end_event="resigned", confidence="high",
         sources="election:2021 (Council RCV, Seat 2 winner, 749 final-round); minutes:2022-01-12 (seated); minutes:2024-11-13 (ABSENT + publicly 'thanked ... for her service'); minutes:2024-11-20 special session ('Vineyard City Council Vacancy')",
         vacate_date="2024-11-13",
         vacate_source="minutes:2024-11-13 (first meeting Rasmussen is ABSENT from the present-list and resident Daria Evans 'thanked councilmember Rasmussen for her service' — a documented farewell); minutes:2024-11-20 special session agenda item 2.1 'Vineyard City Council Vacancy'. The word 'resign' is not printed in the recovered minutes, but a formal mid-term VACANCY was declared and filled by council appointment; vacate_date uses the first-absent meeting as the documented departure bound (exact resignation date not on disk).",
         note="MID-TERM VACANCY #1 (THE clean, fully-on-disk vacancy). Elected 2021 to a term running to Jan-2026; left mid-term in late 2024. end_event='resigned' is the standard mid-term-vacancy mechanism inferred from a declared 'Vacancy' + farewell (the exact letter/date is not in the recovered minutes — flagged)."),
    dict(body="Council", seat_id="AL-B2", person_name="Brett Clawson", person_key="brett_clawson",
         start_date="2024-11-20", start_event="appointed", election_year="",
         end_event="lost", confidence="high",
         sources="appt:2024-11-20 (minutes special session — council interviewed 20 applicants, 'voted by means of a secret ballot ... three (3) votes for Brett Clawson (winner) and two (2) votes for Kimberly Olsen', 'Ms. Spencer swore in Brett Clawson as the new councilmember'); votes:cities.db first_seen 2024-11-20; election:2025 (ran, rank5 general — lost)",
         note="APPOINTED 2024-11-20 to fill Rasmussen's vacated seat (~1-week vacancy 2024-11-13..2024-11-20). Then RAN for a full term in the 2025 general and LOST (rank5 of 6, 998 votes); term expired Jan 2026. Appointed->contested->lost — the appointee did not retain the seat."),
    dict(body="Council", seat_id="AL-B2", person_name="David Lauret", person_key="david_lauret",
         start_date="2026-01-14", start_event="elected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Council plurality vote-for-3 winner, 1348 rank3, 4-year term); minutes:2026-01-14 (seated)",
         note="Won a 4-YEAR seat in the 2025 vote-for-3. Wood/Lauret -> B1/B2 split is a labelling choice (both arrived together Jan-2026); person-tenure is exact."),

    # ===== Seat C — the NEW 5th seat (Prop 10, 2024 ballot), first filled 2025 ===========
    dict(body="Council", seat_id="AL-C", person_name="Parker McCumber", person_key="parker_mccumber",
         start_date="2026-01-14", start_event="elected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Council plurality vote-for-3 winner, 1460 rank1); minutes:2026-01-14 (seated); election_results/CLAUDE.md + Daily Herald (McCumber drew the 2-YEAR term BY LOT to stagger the new seat)",
         note="NEW 5TH SEAT added by Prop 10 (2024 ballot; council 4->5 effective Jan 2026). The 2025 vote-for-3 filled the two 4-yr Cohort-B seats (Wood/Lauret) PLUS this new seat; McCumber, though rank1, drew the 2-YEAR term by lot -> AL-C next comes up 2027 (odd-year / Cohort-A cycle). Term Jan-2026..Jan-2028."),

    # ===== MAYOR (Cycle 2017/2021/2025; the Vineyard mayor VOTES) ========================
    dict(body="Mayor", seat_id="MAYOR", person_name="Julie Fullmer", person_key="julie_fullmer",
         start_date="2018-01-01", start_event="elected", election_year="2017",
         end_event="reelected", confidence="medium",
         sources="minutes:2020-01-08.. (presiding as 'Mayor Julie Fullmer'); votes:cities.db RDA first_seen 2018-12-12 (already Mayor by end of 2018); election:2021 (Mayor winner — re-election as the incumbent)",
         note="PRE-FLOOR term: elected Mayor 2017 (predates the 2019 election-data floor); term-start 2018-01 inferred (medium). Confirmed MAYOR (not a council seat): appears as 'Mayor Julie Fullmer' heading the 2020 present-list and chairs the RDA as 'Chair Fullmer'. Vineyard's Mayor VOTES in roll calls, so this row carries first_vote/last_vote, clamped to this mayoral term's own [start_date, end_date) window (not spanning both mayoral terms — her 2nd-term row carries its own later bounds)."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Julie Fullmer", person_key="julie_fullmer",
         start_date="2022-01-12", start_event="reelected", election_year="2021",
         end_event="did-not-run", confidence="high",
         sources="election:2021 (Mayor RCV winner, 1329 / 86.64% R1 majority, def. Brimhall/Cane); minutes:2022-01-12 (term); election:2025 (did NOT run — open seat won by Stratton); minutes:2025-10-22 (last served)",
         note="Re-elected 2021. Did not seek a third term in 2025 -> the 2025 mayoral race was for the OPEN seat she vacated (per election_results/CLAUDE.md). Term ended Jan 2026."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Zack Stratton", person_key="zack_stratton",
         start_date="2026-01-14", start_event="elected", election_year="2025",
         end_event="serving", confidence="high",
         sources="election:2025 (Mayor plurality winner, 1417 / 54.71%, def. Sifuentes 1173); minutes:2026-01-14 (presiding as 'Mayor Zack Stratton'); minutes:2026-02-03 special session ('MAYOR STRATTON AND COUNCILMEMBERS ... VOTED')",
         note="MAYOR (not a council seat). cities.db shows Stratton with 2 Council-body votes on 2026-02-03 ONLY — those are his MAYORAL roll-call participation on that special session (the clerk named him: 'MAYOR STRATTON AND COUNCILMEMBERS NAIR, LAURET ...'), NOT a separate council tenure. Vineyard's mayor votes; from 2026 the clerk usually records only the councilmembers by name, so Stratton's named votes are sparse. Defeated no incumbent (Fullmer did not run)."),
]

# Seat model: all council seats + mayor are elected AT-LARGE -> one district.
SEAT_DISTRICT = {s: "At-Large" for s in
                 ("AL-A1", "AL-A2", "AL-B1", "AL-B2", "AL-C", "MAYOR")}
SEAT_ORDER = ["AL-A1", "AL-A2", "AL-B1", "AL-B2", "AL-C", "MAYOR"]

# canonical UPPER-CASE election name -> person_key. Two Jacobs (Holdaway/Wood) have
# DISTINCT surnames, so surname keys suffice — do NOT map the shared first name JACOB.
NAME_TO_KEY = {
    "WELSH": "cristy_welsh", "FLAKE": "tyce_flake",
    "HOLDAWAY": "jacob_holdaway", "CAMERON": "sara_cameron",
    "SIFUENTES": "mardi_sifuentes", "RASMUSSEN": "amber_rasmussen",
    "WOOD": "jacob_wood", "LAURET": "david_lauret", "MCCUMBER": "parker_mccumber",
    "FULLMER": "julie_fullmer", "STRATTON": "zack_stratton",
    # appointees (Clawson/Nair/Earnest/Judd) are never general-election winners, so they
    # need no election-name mapping; included for completeness / override robustness:
    "CLAWSON": "brett_clawson", "NAIR": "ezra_nair",
}

# cities.db person.name_key (surname-only in Vineyard) -> our person_key.
DB_KEY = {
    "welsh": "cristy_welsh", "flake": "tyce_flake", "earnest": "john_earnest",
    "judd": "chris_judd", "fullmer": "julie_fullmer", "rasmussen": "amber_rasmussen",
    "sifuentes": "mardi_sifuentes", "cameron": "sara_cameron",
    "holdaway": "jacob_holdaway", "clawson": "brett_clawson",
    "lauret": "david_lauret", "mccumber": "parker_mccumber",
    "nair": "ezra_nair", "wood": "jacob_wood", "stratton": "zack_stratton",
}

ATLARGE = dict(
    district_id="At-Large", plan_id="current",
    effective_start=DATA_FLOOR, effective_end="",
    geometry_ref=GEOM_REF,
    adopted_by="Vineyard Municipal Code (at-large council; Prop 10 (2024 ballot) expanded the council 4->5 seats effective Jan 2026)",
    source_url="", confidence="high",
    note=("DEGENERATE: Vineyard's council + mayor are elected entirely AT-LARGE — no wards/"
          "districts. This single row covers the whole city. NOTE: Vineyard's city LIMITS "
          "change over time by ANNEXATION (it is a fast-growth city on the former Geneva "
          "Steel site), so geometry_ref points at the CURRENT city-limits polygon "
          "(geo/city_limits.geojson); prior annexation-versioned boundaries are NOT on disk "
          "and are NOT fabricated. Because every seat is at-large, the sub-district address->"
          "representative join degenerates to whole-city -> all sitting members + mayor. "
          "effective_start = repo data floor; the at-large structure predates it."),
)

CFG = RosterConfig(
    city=CITY, city_dir=CITY_DIR, repo_root=REPO_ROOT, data_floor=DATA_FLOOR,
    geom_ref=GEOM_REF, elections_path=ELECTIONS, cities_db_path=CITIES_DB,
    overrides_path=OVERRIDES, terms_out=TERMS_OUT, districts_out=DISTRICTS_OUT,
    seat_district=SEAT_DISTRICT, name_to_key=NAME_TO_KEY, db_key=DB_KEY,
    seat_order=SEAT_ORDER,
    keep_election_row=lambda r: "general" in r["election_type"].lower(),  # drop the 2025 primary advancers
    contest_key=lambda office, district: office,   # office (Council/Mayor) == body (at-large)
    crosscheck_field="body", winners_have_district=False,
    elected_events=("elected", "became-mayor", "reelected"),
    atlarge=ATLARGE,
)


# ---------------------------------------------------------------------------
# Demo queries (Vineyard presentation)
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

    print("\n(b) Roster AS OF 2024-11-17 (during the Rasmussen->Clawson VACANT window):")
    for r in roster_lib.roster_as_of(CFG, "2024-11-17", body="Council"):
        print(line(r))
    print("    Mayor:")
    for r in roster_lib.roster_as_of(CFG, "2024-11-17", body="Mayor"):
        print(line(r))

    print("\n(b') Roster AS OF 2025-03-01 (Clawson APPOINTED and seated; Cameron still serving):")
    for r in roster_lib.roster_as_of(CFG, "2025-03-01", body="Council"):
        print(line(r))

    print("\n(c) address+date -> representative (degenerate At-Large -> all members + mayor):")
    for d in ("2024-11-17", "2026-06-01"):
        dist, reps = roster_lib.representatives_for_address(
            CFG, "125 South Main Street, Vineyard, UT 84059", d)
        who = ", ".join(f"{x['person_name']}({x['body']})" for x in reps)
        print(f"  '125 S Main' on {d}: district={dist} -> {who}")


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
