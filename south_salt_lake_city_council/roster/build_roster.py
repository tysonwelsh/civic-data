#!/usr/bin/env python3
"""build_roster.py — rolling council-roster for SOUTH SALT LAKE (a slowly-changing-dimension /
interval table of who holds each council + mayor seat over time). South Salt Lake is a MIXED
strong-mayor city: **5 geographic council districts** (D1..D5) + **2 city-wide AT-LARGE seats**
(AL1..AL2) + a **separately-elected executive Mayor who does NOT vote** on council motions. A full
council/RDA roll tops out at **7** (never 8). The council elects its own Chair to preside (a
`Council Chair <Name>` maps to that councilmember, never a separate person).

THIN DRIVER: this file holds only South-Salt-Lake-specific DATA (curated TENURES, name maps, the
redistricting facts + prose) + config; all generic mechanics live in ../../scripts/roster_lib.py.
Modeled on the west_jordan driver (the MIXED districts + at-large + non-voting-mayor template).

DERIVED LAYER — regenerable, never hand-edited. Canonical inputs:
  1. election_results/south_salt_lake_results_by_candidate.csv (winners -> elected/reelected; 2017+)
  2. cities.db  role table (city='south_salt_lake', body='Council')  (observed vote bounds)
  3. meeting_minutes/minutes/**  (present-lists / roll calls at 2020-07-08.., 2025-03-12, 2026-06-10)
  4. roster/roster_overrides.csv  (hand corrections; applied LAST, win ties)

⚠ THE COVERAGE CLIFF governs confidence here. SSL's recorded council minutes exist essentially
only for **2020 -> early-2021**, plus **2025-03-12** and **2026-06-10/17** (253 council dates in
meeting_minutes/minutes_unrecovered.csv are agenda-only — an HONEST publication gap, not a scraper
miss; see the city CLAUDE.md). Consequences the roster models honestly and never fabricates around:
  * Every tenure is anchored to an in-file ELECTION WIN (2007-2025, winners cross-checked in
    VERIFICATION.md) -> the term-HOLDER is `high`. Where a term's END or an appointee's START falls
    in the 2025-03..2026-06 gap, the exact date is UNRECOVERABLE -> that row reads `medium` with an
    explicit note (weakest-link rule).
  * SSL's January organizational minutes are all in the gap, so no oath ceremony is on disk. Term
    starts use the statutory first-Monday-in-January commencement (UCA 10-3-205), labelled as such —
    the election win, not a claimed ceremony, is the anchor.
  * The two 2026 mid-term appointees (Glad D1, Jones D5) are now DOCUMENTED, not gap-dated: the
    2026 spring council minutes have been recovered/ingested, and the 2026-02-25 regular meeting
    records the appointing resolutions ('... for the Remaining Term of Office Commencing February
    25, 2026, and Concluding January 3, 2028') AND the City Recorder swearing both in -> Glad D1
    and Jones D5 start 2026-02-25, confidence HIGH (was medium/2026-06-10 pre-recovery). Their
    predecessors also anchor to documented departures: Huff (D1) ANNOUNCED her resignation at the
    2026-01-28 meeting (high); Sanchez (D5) has no resignation instrument on disk (last
    substantive vote 2025-12-10, absent 2026-01-14, seat documented vacant 2026-01-28 -> medium).
    deWolfe's Jan-2025 at-large interim appointment is likewise documented (2025-01-22 oath).

Distinctive facts handled honestly (never fabricated around):
  * NON-VOTING executive Mayor Cherie Wood — absent from every cities.db council role and vote roll
    (0 rolls exceed 7 voters) -> `non_voting_mayor=True` (MAYOR vote bounds emptied; cherie_wood not
    in DB_KEY).
  * D3 NAME CHANGE — Sharla BEVERLY (elected 2013/2017) -> Sharla BYNUM (2021/2025), one person, the
    current Council Chair. `BEVERLY` and `BYNUM` both map to sharla_bynum.
  * ONE PERSON, TWO AT-LARGE SEATS (non-contiguous) — Ray deWolfe won at-large 2017 (AL2, 2018-2022,
    lost 2021 to Williams), left, then was appointed to the OTHER at-large seat (AL1, Pinkney's) in
    Jan-2025 and won the 2025 At-Large 2-YEAR special. One ray_dewolfe key spans both; vote bounds
    are CLAMPED per tenure (roster_lib.clamp_vote_bounds), so the AL2 rows carry his 2020-21 votes
    and the AL1 rows carry his 2025-26 votes.
  * THE 2025 AT-LARGE 2-YEAR SPECIAL — Natalie Pinkney (AL1, elected 2019 + 2023) left mid-term for
    the Salt Lake COUNTY council (took office Jan-2025); deWolfe was appointed to the interim, then
    won the off-cycle "At-Large (2-Year Term)" special (district='At-Large-2yr') filling Pinkney's
    unexpired 2023 term to Jan-2028. Kept as its own contest so it doesn't misread as a cycle shift.
  * AT-LARGE seat ids are an ANALYTICAL construct. The 2 at-large seats sit on offset 4-year cycles
    (AL1 = the 2015/2019/2023 cycle; AL2 = the 2013/2017/2021/2025 cycle). The election cross-check
    keys on the LABEL "At-Large" (crosscheck_field='district'), not the analytical id, so both
    at-large winners in a year map without a fake per-seat ballot number.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CITY_DIR = os.path.dirname(HERE)                 # south_salt_lake_city_council/
REPO_ROOT = os.path.dirname(CITY_DIR)            # civic-data/
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import roster_lib
from roster_lib import RosterConfig, Redistrict

ELECTIONS = os.path.join(CITY_DIR, "election_results", "south_salt_lake_results_by_candidate.csv")
PRECINCTS_BYP_SRC = os.path.join(CITY_DIR, "election_results", "south_salt_lake_results_by_precinct.csv")
GEO_PRECINCT_MAP = os.path.join(CITY_DIR, "geo", "precinct_to_district.csv")
CITIES_DB = os.path.join(REPO_ROOT, "cities.db")
OVERRIDES = os.path.join(HERE, "roster_overrides.csv")
TERMS_OUT = os.path.join(HERE, "council_terms.csv")
DISTRICTS_OUT = os.path.join(HERE, "district_versions.csv")
PRECINCTS_OUT = os.path.join(HERE, "district_precincts.csv")

CITY = "south_salt_lake"
DATA_FLOOR = "2020-01-01"
GEOM_REF = "geo/districts.geojson"

# Statutory term commencement — UCA 10-3-205, first Monday in January. SSL's January
# organizational minutes are all in the coverage-cliff gap (no oath ceremony on disk),
# so these are the STATUTORY term-start dates, not claimed ceremonies; the election win
# is the anchor.
SEAT_JAN = {"2020": "2020-01-06", "2022": "2022-01-03",
            "2024": "2024-01-01", "2026": "2026-01-05"}

# The two documented mid-term seams fall in the 2025-03..2026-06 coverage gap; each appointee is
# dated at their FIRST DOCUMENTED vote, noted as approximate (the true appointment predates it).
FIRST_2025 = "2025-03-12"   # first recovered 2025 council minutes (legacy anchor; retained for reference)
FIRST_2026 = "2026-06-10"   # legacy: pre-recovery "first recovered 2026 minutes". The 2026 spring
                            # council minutes (2026-01..05) are now on disk, so the Glad/Jones
                            # appointments are anchored to the DOCUMENTED 2026-02-25 oath, not this.

SEAT_DISTRICT = {
    "D1": "District 1", "D2": "District 2", "D3": "District 3", "D4": "District 4",
    "D5": "District 5", "AL1": "At-Large", "AL2": "At-Large", "MAYOR": "Citywide",
}

TENURES = [
    # ============================ D1  (Huff -> VACANT/gap -> Glad appointed) ============================
    dict(body="Council", seat_id="D1", person_name="LeAnne Huff", person_key="leanne_huff",
         start_date=SEAT_JAN["2020"], start_event="elected", election_year="2019", end_event="reelected",
         confidence="high",
         sources="election:2019 (District 1 winner, 63.95%); votes:2020-07-08.. (cities.db, D1); "
                 "statutory term start UCA 10-3-205 (SSL Jan organizational minutes are in the coverage gap)",
         note="Elected D1 2019, re-elected 2023 (continuous)."),
    dict(body="Council", seat_id="D1", person_name="LeAnne Huff", person_key="leanne_huff",
         start_date=SEAT_JAN["2024"], start_event="reelected", election_year="2023", end_event="resigned",
         confidence="high",
         vacate_date="2026-01-29", vacate_confidence="high",
         vacate_unrecovered_ack="2026-02-11",
         vacate_source="minutes:2026-01-28 (regular council minutes, now on disk): 'Council Member Huff ... shared a "
                       "statement that announced her resignation from the District 1 City Council seat.' She was "
                       "present and voting that night (last D1 vote 2026-01-28); by the 2026-02-11 REGULAR meeting "
                       "(on disk) D1 is off the roll (present list of 5) and the recorder solicits 'City Council "
                       "vacancy applications for District 1 & District 5 ... due on February 18th'. vacate_date = day "
                       "after her last day served (2026-01-28). ACK: the sole un-recovered date inside the vacancy "
                       "window, 2026-02-11, is the agenda-only WORK meeting (WM) — the 2026-02-11 REGULAR meeting is "
                       "recovered and itself shows D1 vacant; BOTH bracket dates (Huff's 2026-01-28 resignation, "
                       "Glad's 2026-02-25 oath) are attested in recovered minutes, so the missing WM does not "
                       "undermine the high-confidence bracket -> acknowledged via vacate_unrecovered_ack.",
         sources="election:2023 (District 1 winner, 71.47%); votes:2024-01-10..2026-01-28 (cities.db, D1); "
                 "minutes:2026-01-28 (resignation announced)",
         note="Re-elected D1 2023. RESIGNED MID-TERM: announced her resignation from the D1 seat at the DOCUMENTED "
              "2026-01-28 regular meeting (present + voting that night). The 2026 spring council minutes are now on "
              "disk (the old coverage cliff is closed for this seam), so the departure is DOCUMENTED, not gap-"
              "inferred -> confidence upgraded MEDIUM->HIGH and last-observed vote corrected 2025-03-12 -> "
              "2026-01-28. Explicit VACANT interval [2026-01-29, 2026-02-25) to appointee Glad (D1 seat empty on "
              "the 2026-02-11 roll; applications solicited)."),
    dict(body="Council", seat_id="D1", person_name="Joy Glad", person_key="joy_glad",
         start_date="2026-02-25", start_event="appointed", election_year="", end_event="serving",
         confidence="high",
         sources="minutes:2026-02-25 (regular council minutes, recovered/promoted since the 2026-07 waves: 'A "
                 "Resolution ... Appointing an Individual to Serve ... for the Remaining Term of Office Commencing "
                 "February 25, 2026, and Concluding January 3, 2028'; council roll unanimous for Joy Glad to fill "
                 "the District 1 vacancy; then 'City Recorder, Ariel Andrus, administered the Oath of Office to Joy "
                 "Glad, who was subsequently sworn in as a City Council Member'); votes:2026-03-11.. (cities.db, D1)",
         note="APPOINTED + SWORN IN 2026-02-25 to fill the D1 mid-term vacancy left by Huff's 2026-01-28 "
              "resignation (documented instrument — the 2026 spring council minutes are now on disk, closing the "
              "coverage cliff for this seam). REFUTES the pre-recovery note that gap-dated her at her first vote "
              "(2026-06-10, medium): the appointment resolution + oath are DOCUMENTED, term commences 2026-02-25 -> "
              "confidence upgraded MEDIUM->HIGH, exact date. First observed vote 2026-03-11 (the swearing predates "
              "it). Currently serving."),

    # ============================ D2  (Thomas, continuous) ============================
    dict(body="Council", seat_id="D2", person_name="Corey Thomas", person_key="corey_thomas",
         start_date="2018-01-01", start_event="elected", election_year="2017", end_event="reelected",
         confidence="high",
         sources="election:2017 (District 2 winner, 53.04%); votes:2020-07-08.. (cities.db, D2); "
                 "statutory term start UCA 10-3-205 (pre-floor Jan-2018 seating; win is in-data)",
         note="Elected D2 2017 (seated Jan-2018, pre the 2020 minutes floor; the WIN is in the election data). "
              "Serving continuously at the floor; re-elected 2021 + 2025."),
    dict(body="Council", seat_id="D2", person_name="Corey Thomas", person_key="corey_thomas",
         start_date=SEAT_JAN["2022"], start_event="reelected", election_year="2021", end_event="reelected",
         confidence="high",
         sources="election:2021 (District 2 winner, 54.88%); votes:continuous (cities.db, D2)",
         note="Re-elected D2 2021."),
    dict(body="Council", seat_id="D2", person_name="Corey Thomas", person_key="corey_thomas",
         start_date=SEAT_JAN["2026"], start_event="reelected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (District 2 winner, 100% unopposed); votes:2026-06-10.. (cities.db, D2)",
         note="Re-elected D2 2025 (unopposed). Currently serving."),

    # ============================ D3  (Beverly/Bynum, continuous; Council Chair) ============================
    dict(body="Council", seat_id="D3", person_name="Sharla Bynum", person_key="sharla_bynum",
         start_date="2018-01-01", start_event="elected", election_year="2017", end_event="reelected",
         confidence="high",
         sources="election:2017 (District 3 winner as 'Sharla Beverly', 66.44%); votes:2020-07-08.. (cities.db, D3); "
                 "statutory term start UCA 10-3-205 (pre-floor Jan-2018 seating; win is in-data)",
         note="NAME CHANGE: elected D3 2017 as Sharla BEVERLY; appears as Sharla BYNUM from the 2021 cycle on — "
              "ONE person (the current Council Chair). Seated Jan-2018 (pre-floor; win in-data). Continuous."),
    dict(body="Council", seat_id="D3", person_name="Sharla Bynum", person_key="sharla_bynum",
         start_date=SEAT_JAN["2022"], start_event="reelected", election_year="2021", end_event="reelected",
         confidence="high",
         sources="election:2021 (District 3 winner as 'Sharla Bynum', 68.18%); votes:continuous (cities.db, D3)",
         note="Re-elected D3 2021 (as Sharla Bynum). Council Chair."),
    dict(body="Council", seat_id="D3", person_name="Sharla Bynum", person_key="sharla_bynum",
         start_date=SEAT_JAN["2026"], start_event="reelected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (District 3 winner, 64.10%); votes:2026-06-10 (presiding as Council Chair Bynum)",
         note="Re-elected D3 2025. Council Chair (presides). Currently serving."),

    # ============================ D4  (Mila -> Mitchell) ============================
    dict(body="Council", seat_id="D4", person_name="Portia Mila", person_key="portia_mila",
         start_date=SEAT_JAN["2020"], start_event="elected", election_year="2019", end_event="did-not-run",
         confidence="high",
         sources="election:2019 (District 4 winner, 67.70%); votes:2020-07-08..2021-02-24 (cities.db, D4)",
         note="Elected D4 2019. Not a candidate in D4 2023 (Mitchell won) -> left office at the 2024 term start; "
              "mechanism unrecorded (did-not-run). Clean cycle-boundary handoff."),
    dict(body="Council", seat_id="D4", person_name="Nick Mitchell", person_key="nick_mitchell",
         start_date=SEAT_JAN["2024"], start_event="elected", election_year="2023", end_event="serving",
         confidence="high",
         sources="election:2023 (District 4 winner, 52.50%); votes:2025-03-12.. (cities.db, D4, first observed "
                 "after the coverage cliff); statutory term start UCA 10-3-205",
         note="Elected D4 2023 (seated Jan-2024; first documented vote 2025-03-12 owing to the coverage cliff — "
              "his 2024 service is election-anchored, the vote record simply wasn't published). Currently serving."),

    # ============================ D5  (Siwik -> Sanchez -> VACANT/gap -> Jones appointed) ============================
    dict(body="Council", seat_id="D5", person_name="Shane Siwik", person_key="shane_siwik",
         start_date=SEAT_JAN["2020"], start_event="elected", election_year="2019", end_event="resigned",
         confidence="high",
         sources="election:2019 (District 5 winner as 'Shane Siwik', 53.20%); votes:2020-07-08..2021-02-24 (cities.db, D5); "
                 "minutes:2023-10-25 (D5 seat declared VACANT; council fills it — recovered 2026-07-17)",
         note="Elected D5 2019. RESIGNED MID-TERM: the 2023-10-25 regular council minutes (recovered 2026-07-17) record a "
              "'Selection to Fill Vacant Council District 5 Seat' -> Siwik had left before then (his exact last day is not "
              "stated in the recovered record). The seat is handed to appointee Sanchez at the documented 2023-10-25 fill; "
              "not the clean 2024 cycle-boundary 'did-not-run' the pre-recovery roster inferred."),
    dict(body="Council", seat_id="D5", person_name="Paul Sanchez", person_key="paul_sanchez",
         start_date="2023-10-25", start_event="appointed", election_year="", end_event="succeeded-by-elected",
         confidence="high",
         sources="minutes:2023-10-25 (regular council minutes, recovered 2026-07-17: 'Selection to Fill Vacant Council "
                 "District 5 Seat' — Sanchez the sole applicant; Council Chair Bynum 'congratulated him on his new position "
                 "as the Council Member for District 5')",
         note="APPOINTED 2023-10-25 to fill the D5 mid-term vacancy left by Siwik (documented instrument — first recovered "
              "by the 2026-07-17 promotion). Sanchez then won the concurrent Nov-2023 D5 general (unopposed) for the full "
              "2024-2028 term (next row) -> continuous service; this appointed tenure covers the ~2-month remainder of "
              "Siwik's term. Confidence HIGH (documented appointment date)."),
    dict(body="Council", seat_id="D5", person_name="Paul Sanchez", person_key="paul_sanchez",
         start_date=SEAT_JAN["2024"], start_event="elected", election_year="2023", end_event="resigned",
         confidence="medium",
         vacate_date="2026-01-28", vacate_confidence="medium",
         vacate_source="No resignation instrument is on disk (unlike Huff's announced 2026-01-28 resignation). "
                       "Sanchez's last substantive D5 vote is 2025-12-10; he is recorded ABSENT on the 2026-01-14 "
                       "roll (still listed as the D5 member), then is OFF the roll entirely at 2026-01-28 (present "
                       "list of 6) where Council Chair Bynum 'shared a brief statement to provide some clarity on "
                       "what led to the vacancy in the District 5 City Council seat'. Exact departure date UNSTATED "
                       "-> vacancy dated at the first meeting D5 is documented empty (2026-01-28), medium (bracketed "
                       "2025-12-10 last substantive vote / 2026-01-14 last roll appearance .. 2026-01-28 documented "
                       "vacant).",
         sources="election:2023 (District 5 winner, 100% unopposed); votes:2024-01-10..2025-12-10 substantive, "
                 "recorded Absent 2026-01-14 (cities.db, D5); minutes:2026-01-28 (D5 vacancy acknowledged)",
         note="Elected D5 2023 (unopposed; had already been APPOINTED to the seat 2023-10-25 — prior row). Seated "
              "for the full term Jan-2024. LEFT MID-TERM: no resignation instrument on disk; last substantive vote "
              "2025-12-10, absent on the 2026-01-14 roll, seat documented vacant by 2026-01-28 -> explicit VACANT "
              "interval [2026-01-28, 2026-02-25) to appointee Jones, confidence MEDIUM (exact departure date "
              "unstated). Corrects the pre-recovery last-observed 2025-03-12 (the 2026 spring minutes are now on "
              "disk)."),
    dict(body="Council", seat_id="D5", person_name="Irvin Jones", person_key="irvin_jones",
         start_date="2026-02-25", start_event="appointed", election_year="", end_event="serving",
         confidence="high",
         sources="minutes:2026-02-25 (regular council minutes, recovered/promoted since the 2026-07 waves: 'A "
                 "Resolution ... Appointing an Individual to Serve ... for the Remaining Term of Office Commencing "
                 "February 25, 2026, and Concluding January 3, 2028'; council roll 3-2 for Irvin Jones over Darlene "
                 "McDonald, then the appointing motion carried 5-0 to fill the District 5 vacancy; then 'City "
                 "Recorder, Ariel Andrus, administered the Oath of Office to Irvin Jones, who was subsequently sworn "
                 "in as a City Council Member'); votes:2026-03-11.. (cities.db, D5)",
         note="APPOINTED + SWORN IN 2026-02-25 to fill the D5 mid-term vacancy left by Sanchez (documented "
              "instrument — the 2026 spring council minutes are now on disk). REFUTES the pre-recovery gap-date at "
              "his first vote (2026-06-10, medium): the appointment resolution + oath are DOCUMENTED, term commences "
              "2026-02-25 -> confidence upgraded MEDIUM->HIGH, exact date. First observed vote 2026-03-11. Irvin "
              "Jones also won D5 back in 2011 (pre-floor) — the same person returning by appointment. Currently "
              "serving."),

    # ============================ AL1  (Pinkney -> Pinkney -> deWolfe interim -> deWolfe 2yr special) ============
    dict(body="Council", seat_id="AL1", person_name="Natalie Pinkney", person_key="natalie_pinkney",
         start_date=SEAT_JAN["2020"], start_event="elected", election_year="2019", end_event="reelected",
         confidence="high",
         sources="election:2019 (At-Large winner, 63.66%); votes:2020-07-08..2021-02-24 (cities.db, at-large)",
         note="Elected to an at-large seat 2019 (the 2015/2019/2023-cycle at-large seat -> analytical id AL1). "
              "Re-elected 2023."),
    dict(body="Council", seat_id="AL1", person_name="Natalie Pinkney", person_key="natalie_pinkney",
         start_date=SEAT_JAN["2024"], start_event="reelected", election_year="2023", end_event="resigned",
         confidence="medium",
         sources="election:2023 (At-Large winner, 77.33%); city CLAUDE.md (Pinkney left At-Large for the Salt Lake "
                 "COUNTY council; deWolfe appointed Jan-2025, then won the 2025 At-Large 2-year special)",
         note="Re-elected at-large 2023. LEFT MID-TERM for the Salt Lake COUNTY council (took county office "
              "Jan-2025). Her exact SSL resignation date is still unstated, but is now bounded to BEFORE the documented "
              "2025-01-22 fill (the 2025-01-22 minutes, recovered 2026-07-17, treat the seat as already vacant and seat "
              "deWolfe) -> the seat is handed to interim appointee deWolfe at his documented 2025-01-22 appointment "
              "(was 2025-03-12 pre-recovery), confidence MEDIUM (resignation date still inferred)."),
    dict(body="Council", seat_id="AL1", person_name="Ray deWolfe", person_key="ray_dewolfe",
         start_date="2025-01-22", start_event="appointed", election_year="", end_event="succeeded-by-elected",
         confidence="high",
         sources="minutes:2025-01-22 (regular council minutes, recovered 2026-07-17: council selected deWolfe 5-1 to fill "
                 "the vacant At-Large seat, adopted the appointing Resolution per UCA 10-3-507, and City Recorder Ariel "
                 "Andrus SWORE HIM IN as At-Large Council Member the same night); votes:2025-03-12.. (cities.db, at-large)",
         note="APPOINTED + SWORN IN 2025-01-22 to fill Pinkney's vacant at-large seat (AL1) 'for the remainder of the "
              "term', per UCA 10-3-507. This oath is now DOCUMENTED on disk (recovered by the 2026-07-17 promotion), "
              "REFUTING the pre-recovery note that dated it approximately at his first 2025 vote (2025-03-12) -> confidence "
              "upgraded MEDIUM->HIGH, exact date. Interim ends when he is seated for the 2-year special he won in Nov-2025. "
              "SAME PERSON as the AL2 holder 2018-2022 (non-contiguous; vote bounds clamped per tenure)."),
    dict(body="Council", seat_id="AL1", person_name="Ray deWolfe", person_key="ray_dewolfe",
         start_date=SEAT_JAN["2026"], start_event="elected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (At-Large 2-YEAR special winner, district='At-Large-2yr', 69.48% as 'G. Ray "
                 "deWolfe'); votes:2026-06-10.. (cities.db, at-large); statutory term start UCA 10-3-205",
         note="Won the 2025 off-cycle At-Large 2-YEAR SPECIAL filling Pinkney's unexpired 2023 term (to Jan-2028). "
              "Seated for the special at the 2026 term start. Currently serving."),

    # ============================ AL2  (deWolfe 2017 -> Williams 2021/2025) ============================
    dict(body="Council", seat_id="AL2", person_name="Ray deWolfe", person_key="ray_dewolfe",
         start_date="2018-01-01", start_event="elected", election_year="2017", end_event="lost",
         confidence="high",
         sources="election:2017 (At-Large winner, 56.16%); votes:2020-07-08..2021-02-24 (cities.db, at-large); "
                 "statutory term start UCA 10-3-205 (pre-floor Jan-2018 seating; win is in-data)",
         note="Elected to the OTHER at-large seat 2017 (the 2013/2017/2021/2025 cycle -> analytical id AL2; seated "
              "Jan-2018, pre-floor, win in-data). LOST the 2021 at-large race to Williams -> left at the 2022 term "
              "start. (Returned to council in 2025 via the AL1 special — see above; vote bounds clamped per tenure.)"),
    dict(body="Council", seat_id="AL2", person_name="Clarissa Williams", person_key="clarissa_williams",
         start_date=SEAT_JAN["2022"], start_event="elected", election_year="2021", end_event="reelected",
         confidence="high",
         sources="election:2021 (At-Large winner, 51.65%); votes:2025-03-12.. (cities.db, at-large, first observed "
                 "after the coverage cliff)",
         note="Elected at-large 2021 (unseating holdover deWolfe on AL2). Seated Jan-2022 (first documented vote "
              "2025-03-12 owing to the coverage cliff — her 2022-24 service is election-anchored). Re-elected 2025."),
    dict(body="Council", seat_id="AL2", person_name="Clarissa Williams", person_key="clarissa_williams",
         start_date=SEAT_JAN["2026"], start_event="reelected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (At-Large winner, 100% unopposed); votes:2026-06-10.. (cities.db, at-large)",
         note="Re-elected at-large 2025 (unopposed). Currently serving."),

    # ============================ MAYOR  (Cherie Wood — non-voting exec) ============================
    dict(body="Mayor", seat_id="MAYOR", person_name="Cherie Wood", person_key="cherie_wood",
         start_date="2018-01-01", start_event="reelected", election_year="2017", end_event="reelected",
         confidence="high",
         sources="election:2017 (Mayor winner, 50.46%; also won 2009/2013 — mayor since Jan-2010); minutes:2020-07-08.. "
                 "(presents items as Mayor Wood, casts no council vote)",
         note="Executive Mayor (since Jan-2010; her 2009/2013 terms are pre-floor, not rostered). Does NOT vote on "
              "council motions -> non_voting_mayor empties her vote bounds; cherie_wood is absent from cities.db."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Cherie Wood", person_key="cherie_wood",
         start_date=SEAT_JAN["2022"], start_event="reelected", election_year="2021", end_event="reelected",
         confidence="high",
         sources="election:2021 (Mayor winner, 58.24%); minutes:presents items, casts no council vote",
         note="Re-elected Mayor 2021 (non-voting exec)."),
    dict(body="Mayor", seat_id="MAYOR", person_name="Cherie Wood", person_key="cherie_wood",
         start_date=SEAT_JAN["2026"], start_event="reelected", election_year="2025", end_event="serving",
         confidence="high",
         sources="election:2025 (Mayor winner, 66.76%); minutes:2026-06-10 (Mayor Wood presents the budget; no vote)",
         note="Re-elected Mayor 2025 (non-voting exec). Currently serving."),
]

# canonical UPPER-CASE election-name token -> our person_key. Only 2017+ winners pass through the
# cross-check (keep_election_row filters year>=2017); pre-floor surnames (RUTTER/BRUSCH/TURNER/
# MARSHALL/WEAVER/GOLD/KINDRED/SNOW/PENDER/RAPP) are never mapped. D3 name change: BEVERLY & BYNUM
# BOTH -> sharla_bynum (one person). No two 2017+ winners share a surname, so no disambiguators.
NAME_TO_KEY = {
    "HUFF": "leanne_huff", "THOMAS": "corey_thomas", "BEVERLY": "sharla_bynum", "BYNUM": "sharla_bynum",
    "MILA": "portia_mila", "MITCHELL": "nick_mitchell", "SIWIK": "shane_siwik", "SANCHEZ": "paul_sanchez",
    "PINKNEY": "natalie_pinkney", "DEWOLFE": "ray_dewolfe", "WILLIAMS": "clarissa_williams",
    "WOOD": "cherie_wood", "GLAD": "joy_glad", "JONES": "irvin_jones",
}

# cities.db person.name_key -> our person_key (council voters only). cherie_wood is DELIBERATELY
# EXCLUDED — the non-voting exec Mayor is absent from the cities.db person table.
DB_KEY = {
    "leannehuff": "leanne_huff", "coreythomas": "corey_thomas", "sharlabynum": "sharla_bynum",
    "portiamila": "portia_mila", "nickmitchell": "nick_mitchell", "shanesiwik": "shane_siwik",
    "paulsanchez": "paul_sanchez", "nataliepinkney": "natalie_pinkney", "raydewolfe": "ray_dewolfe",
    "clarissawilliams": "clarissa_williams", "joyglad": "joy_glad", "irvinjones": "irvin_jones",
}


def seat_for_contest(office, district):
    """election (office, district) -> the DISTRICT LABEL used as the cross-check key
    (crosscheck_field='district'). SSL is MIXED: 5 geographic districts + 2 city-wide at-large seats
    (keyed on the LABEL 'At-Large' so both at-large winners in a year map, incl. the 2025 2-year
    special district='At-Large-2yr') + a citywide non-voting Mayor."""
    if office == "Mayor":
        return "Citywide"
    d = district.strip()
    if d in ("1", "2", "3", "4", "5"):
        return "District " + d
    if d in ("At-Large", "At-Large-2yr"):
        return "At-Large"
    return None


# The post-2020-census redistricting. SSL publishes its OWN authoritative 5-district ArcGIS layer
# (current vintage). The pre-2022 boundaries are NOT acquired (honest gap), and the adoption
# resolution falls in the coverage-cliff gap (no 2022-24 minutes on disk) -> plan_switch is the
# nominal statewide post-2020-census cycle boundary, labelled as inferred, prior plan = low gap.
REDISTRICT = Redistrict(
    plan_old="plan_pre2022", plan_new="plan_2022", plan_switch="2022-01-01",
    ord="post-2020-census redistricting (adoption resolution in the coverage-cliff gap)",
    adopted="2022 (nominal cycle boundary; exact date not recovered)",
    districts=["District 1", "District 2", "District 3", "District 4", "District 5"],
    geom_ref=GEOM_REF,
    source_url="geo/districts.geojson (South Salt Lake official 5-district ArcGIS FeatureServer, current vintage)",
    data_floor=DATA_FLOOR,
    current_note=("CURRENT post-2020-census 5-district boundaries — South Salt Lake's OWN authoritative ArcGIS "
                  "layer (geo/districts.geojson; no precinct-derivation needed). effective_start is the nominal "
                  "2022 post-2020-census cycle boundary: SSL's redistricting adoption resolution falls in the "
                  "2021-mid..2025 coverage-cliff gap and is not on disk, so the date is inferred from the statewide "
                  "cycle, not a locally-documented adoption. precinct->district in geo/precinct_to_district.csv "
                  "(source_year 2023 + 2025)."),
    prior_adopted_by="prior plan (pre-2022 boundaries)",
    prior_geom_ref="",
    prior_confidence="low",
    prior_note=("Pre-2022 district boundaries NOT acquired (honest GAP — SSL keeps only its current ArcGIS layer; "
                "no pre-2022 geometry on disk) AND the redistricting adoption is in the coverage-cliff gap. "
                "effective_start = data floor. Never reconstructed/guessed."),
    citywide_rows=[
        ("At-Large", "citywide", "the two at-large councilmembers (AL1 Pinkney->deWolfe, AL2 Williams)"),
        ("MAYOR", "citywide", "the separately-elected non-voting executive Mayor Cherie Wood"),
    ],
    citywide_adopted_by="South Salt Lake City (city-wide seats)",
    citywide_note_template=("{who}: represent(s) the ENTIRE city on every date, unchanged by redistricting. SSL's "
                            "TWO at-large council seats + the Mayor are city-wide (only the 5 numbered districts are "
                            "geographic). The Mayor does not vote on council legislation."),
    precinct_hi_source=("2023", "2025"),   # both current-plan source_year values in geo/precinct_to_district.csv
    precinct_hi_note=("post-redistrict precinct->district from SSL's current map (geo/precinct_to_district.csv; "
                      "source_year 2023 + 2025 district contests). Districts only — the 2 at-large seats + Mayor "
                      "are city-wide and have no precinct->district composition."),
    precinct_med_note="",
    precinct_prior_note=("Pre-2022 precinct->district composition NOT acquired (honest GAP; the redistricting is in "
                         "the coverage-cliff gap). Never reconstructed."),
    crosscheck_districts=("1", "2", "3", "4", "5"),
    precinct_prefix="SSL", geo_seat_prefix="D",
    plan_switch_year="2022", citywide_seats=("AL1", "AL2"),
)

CFG = RosterConfig(
    non_voting_mayor=True,
    city=CITY, city_dir=CITY_DIR, repo_root=REPO_ROOT, data_floor=DATA_FLOOR,
    geom_ref=GEOM_REF, elections_path=ELECTIONS, cities_db_path=CITIES_DB,
    overrides_path=OVERRIDES, terms_out=TERMS_OUT, districts_out=DISTRICTS_OUT,
    seat_district=SEAT_DISTRICT, name_to_key=NAME_TO_KEY, db_key=DB_KEY,
    seat_order=["D1", "D2", "D3", "D4", "D5", "AL1", "AL2", "MAYOR"],
    # municipal GENERAL winners only, 2017+ (the earliest cycle that seats a tenure still active at
    # the 2020 floor — D2 Thomas, D3 Beverly, AL2 deWolfe, Mayor Wood, all seated Jan-2018). Pre-2017
    # winners are wholly pre-floor and deliberately not rostered; including them would print
    # forever-unmappable cross-check flags.
    keep_election_row=lambda r: ("general" in r["election_type"].lower() and int(r["year"]) >= 2017),
    contest_key=seat_for_contest, crosscheck_field="district",
    winners_have_district=True,
    elected_events=("elected", "reelected"),
    redistrict=REDISTRICT, precincts_out=PRECINCTS_OUT,
    precinct_map_path=GEO_PRECINCT_MAP, precincts_byprecinct_path=PRECINCTS_BYP_SRC,
)


def demo():
    def line(r):
        end = r["end_date"] or "—(serving)"
        return (f"    {r['seat_id']:<6} {r['person_name']:<20} {r['start_date']} -> {end:<12}"
                f" [{r['start_event']}/{r['end_event']}] conf={r['confidence']}")

    print("\n(a) CURRENT council roster + mayor (end_date empty, end_event=serving):")
    for r in roster_lib.load_terms(CFG):
        if not r["end_date"] and r["end_event"] == "serving":
            print(line(r))

    print("\n(b) Roster AS OF 2020-10-01 (the 2020 seven):")
    for r in roster_lib.roster_as_of(CFG, "2020-10-01", body="Council"):
        print(line(r))
    for r in roster_lib.roster_as_of(CFG, "2020-10-01", body="Mayor"):
        print(line(r))


if __name__ == "__main__":
    rows = roster_lib.build(CFG, TENURES)
    n = {c: sum(1 for r in rows if r["confidence"] == c) for c in ("high", "medium", "low")}
    nvac = sum(1 for r in rows if r["start_event"] == "vacated")
    print(f"Wrote {os.path.relpath(TERMS_OUT, CITY_DIR)} "
          f"({len(rows)} tenures incl. {nvac} VACANT: {n['high']} high / {n['medium']} medium / {n['low']} low)")
    print(f"Wrote {os.path.relpath(DISTRICTS_OUT, CITY_DIR)} "
          f"(5 districts x 2 plans + At-Large + Mayor; redistricting inferred — see prior_note)")
    print(f"Wrote {os.path.relpath(PRECINCTS_OUT, CITY_DIR)} "
          f"(plan_2022 precinct map + plan_pre2022 gap rows; districts only)")
    if "--check" in sys.argv:
        print("\nValidation: PASS (no overlaps; sources+confidence present; non-voting-mayor + gap/vacate guards clear).")
        print("Precinct cross-check:")
        roster_lib.precinct_crosscheck(CFG, verbose=True)
    if "--demo" in sys.argv:
        demo()
