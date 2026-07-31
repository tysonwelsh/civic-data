#!/usr/bin/env python3
"""
Build Park City (Summit County, UT) municipal election CSVs for 2019/2021/2023/2025.

PREMISE: Park City SELF-ADMINISTERS its municipal elections; Summit County Clerk
defers Park City mayor/council results to the city. Authoritative source is the
city's own canvass resolutions / precinct reports, published at
https://www.parkcity.gov/government/elections/election_results.php

Council is AT-LARGE, vote-for-N, NO ranked-choice voting (RCV). One cycle elects
Mayor + 2 council; the next elects 3 council. Primaries advance top 2N.

Candidate totals are traced to the certified canvass PDFs in raw/ where a text layer
exists; 2019 (no PDF on the server) and 2025-primary (image-only canvass PDF) totals
are traced to the official results tables embedded in the city election_results page
(raw/parkcity_election_results_page_2026-06-26.html). All cross-checked vs winners
reported by Park Record / KPCW / TownLift / electionresults.utah.gov.

pct columns: for council vote-for-N, pct = share of total council votes cast in the
contest (NOT turnout) -- the denominator is inflated by vote-for-N. See CLAUDE.md.
margin = the SEAT-DECIDING boundary (last winner rank N minus first loser rank N+1);
for primaries the boundary is the advancement cut (rank 2N vs rank 2N+1).
"""
import csv, os

OUT = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# CANDIDATE-LEVEL DATA
# Each contest: (year, election_type, office, contest, district, n_seats,
#   voting_method, source) -> list of (candidate, votes)
# n_advance: primaries advance top 2*n_seats; generals fill n_seats.
# ---------------------------------------------------------------------------
CONTESTS = [
    # ---- 2019 (HTML results table; no canvass PDF retrievable from server) ----
    dict(year=2019, etype="municipal primary", office="Council", contest="Park City Council",
         district="At-Large", n_seats=3, source="parkcity.gov election_results.php (HTML table)",
         cands=[("Nann Worel",1090),("Becca Gerber",1047),("Max Doilney",620),
                ("Ed Parigian",460),("Deanna Rhodes",420),("Daniel Lewis",193),
                ("Chadwick H. Fairbanks III",191)]),
    dict(year=2019, etype="municipal general", office="Council", contest="Park City Council",
         district="At-Large", n_seats=3, source="parkcity.gov election_results.php (HTML table)",
         cands=[("Nann Worel",1562),("Becca Gerber",1542),("Max Doilney",954),
                ("Ed Parigian",773),("Deanna Rhodes",724),("Daniel Lewis",234)]),

    # ---- 2021 (Summit County precinct reports certified by Park City) ----
    dict(year=2021, etype="municipal primary", office="Mayor", contest="Park City Mayor",
         district="", n_seats=1, source="raw/2021_primary_votes_by_precinct.pdf",
         cands=[("Nann Worel",1393),("Andy Beerman",738),("David A. Dobkin",367)]),
    dict(year=2021, etype="municipal primary", office="Council", contest="Park City Council",
         district="At-Large", n_seats=2, source="raw/2021_primary_votes_by_precinct.pdf",
         cands=[("Tana Toly",1351),("Jeremy Rubell",1246),("Tim B. Henney",806),
                ("Thomas C. Purcell",327),("John Greenfield",292),("Daniel Lewis",156),
                ("Jamison Brandi",147),("Michael J. Franchek",52)]),
    dict(year=2021, etype="municipal general", office="Mayor", contest="Park City Mayor",
         district="", n_seats=1, source="raw/2021_general_votes_by_precinct.pdf",
         cands=[("Nann Worel",2048),("Andy Beerman",1317)]),
    dict(year=2021, etype="municipal general", office="Council", contest="Park City Council",
         district="At-Large", n_seats=2, source="raw/2021_general_votes_by_precinct.pdf",
         # Thomas C. Purcell withdrew (on ballot, 0 votes); excluded as non-competing.
         cands=[("Tana Toly",2208),("Jeremy Rubell",2130),("Tim B. Henney",1439)]),

    # ---- 2023 (canvass PDFs, text layer) ----
    dict(year=2023, etype="municipal primary", office="Council", contest="Park City Council",
         district="At-Large", n_seats=3, source="raw/2023_primary_canvass.pdf",
         cands=[("Ryan Dickey",1364),("Ed Parigian",844),("Matthew Nagie",828),
                ("Bob Sertner",745),("John Greenfield",599),("Bill Ciraco",585),
                ("Jody Whitesides",338),('David "Pickleball Traffic" Dobkin',216)]),
    dict(year=2023, etype="municipal general", office="Council", contest="Park City Council",
         district="At-Large", n_seats=3, source="raw/2023_general_election_reports.pdf",
         cands=[("Ryan Dickey",1778),("Ed Parigian",1311),("Bill Ciraco",1158),
                ("Bob Sertner",1084),("Matthew Nagie",972),("John Greenfield",557)]),

    # ---- 2025 (canvass PDFs + recount) ----
    dict(year=2025, etype="municipal primary", office="Council", contest="Park City Council",
         district="At-Large", n_seats=2, source="parkcity.gov election_results.php (HTML; canvass PDF image-only)",
         cands=[("Tana Toly",1081),("Diego Zegarra",972),("Jeremy Rubell",648),
                ('John "J.K." Kenworthy',563),("Beth Armstrong",538),("Danny Glasser",520),
                ("Molly Miller",432),("Ian Hartley",205)]),
    dict(year=2025, etype="municipal general", office="Mayor", contest="Park City Mayor",
         district="", n_seats=1, source="raw/2025_general_canvass.pdf (recount: raw/2025_general_recount_canvass.pdf)",
         cands=[("Ryan Dickey",1706),("Jack Rubin",1699)]),
    dict(year=2025, etype="municipal general", office="Council", contest="Park City Council",
         district="At-Large", n_seats=2, source="raw/2025_general_canvass.pdf",
         # John "J.K." Kenworthy advanced from primary but withdrew before the general.
         cands=[("Tana Toly",2337),("Diego Zegarra",2016),("Jeremy Rubell",1530)]),
]

def voting_method(office, etype, n_seats):
    advance = "" if etype.endswith("general") else f"; top {2*n_seats} advance"
    if office == "Mayor":
        return f"plurality (vote-for-1){advance}; no RCV"
    return f"at-large block plurality (vote-for-{n_seats}){advance}; no RCV"

# ---------------------------------------------------------------------------
# Build races.csv + results_by_candidate.csv
# ---------------------------------------------------------------------------
races_rows, cand_rows = [], []
for c in CONTESTS:
    cands = sorted(c["cands"], key=lambda x: -x[1])
    total = sum(v for _, v in cands)
    n_seats = c["n_seats"]
    is_primary = c["etype"].endswith("primary")
    boundary = 2*n_seats if is_primary else n_seats   # how many "win/advance"
    n = len(cands)
    pct = lambda v: round(v/total*100, 2) if total else 0.0

    # winner = top vote-getter; runner_up = first non-winner (rank boundary+1)
    winner, winner_v = cands[0]
    if boundary < n:
        runner_up, runner_v = cands[boundary]
        last_winner_v = cands[boundary-1][1]
        margin_v = last_winner_v - runner_v
    else:  # everyone advances/wins (no losing boundary)
        runner_up, runner_v, margin_v = "", "", ""
    margin_p = round(margin_v/total*100, 2) if (margin_v != "" and total) else ""

    races_rows.append(dict(
        year=c["year"], election_type=c["etype"], office=c["office"], district=c["district"],
        contest=c["contest"], n_seats=n_seats, n_candidates=n,
        voting_method=voting_method(c["office"], c["etype"], n_seats),
        total_first_choice_votes=total, winner=winner, winner_votes=winner_v,
        winner_pct=pct(winner_v), runner_up=runner_up,
        runner_up_votes=runner_v, margin_votes=margin_v, margin_pct=margin_p))

    for rank, (name, v) in enumerate(cands, 1):
        cand_rows.append(dict(
            year=c["year"], election_type=c["etype"], office=c["office"], contest=c["contest"],
            candidate=name, votes=v, pct=pct(v), rank=rank,
            is_winner="Y" if rank <= boundary else "N"))

# ---------------------------------------------------------------------------
# PRECINCT-LEVEL DATA  (where the canvass provides a clean per-candidate table)
# Covered: 2021 primary (mayor+council), 2021 general (mayor+council),
#          2023 general (council), 2025 general (mayor+council).
# NOT covered: 2019 (no PDF), 2023 primary (precinct table image-garbled; turnout
#          only), 2025 primary (canvass image-only). See CLAUDE.md.
# precinct codes are reproduced verbatim from each source PDF. The 2021/2023 reports
# use Electionware short codes (e.g. Dvn1:1); the 2025 report uses CountyID-prefixed
# codes (e.g. 22DVN:15). Same physical areas, renamed between cycles.
# ---------------------------------------------------------------------------
# old-format precincts (2021/2023)
P_OLD = ["Dvn1:1","Dvs31:1","Dvs31:54","Oldn32:1","Olds2:1","Pkmn35:1",
         "Pkms5:1","Pros3:1","Quar6:1","Side33:1","Thay4:1"]
# new-format precincts (2025); 22DVS:30 = Suppressed (privacy), omitted
P_NEW = ["22DVN:15","22DVS:25","22OLDN:15","22OLDS:25","22PKMN:15",
         "22PKMS:25","22PROS:5","22QUAR:5","22RNDV:5","22SIDE:5","22THAY:5"]

PRECINCT_TABLES = [
    # (year, etype, office, contest, candidate_order, precinct_codes, rows[list per precinct])
    (2021, "municipal primary", "Mayor", "Park City Mayor",
     ["Nann Worel","Andy Beerman","David A. Dobkin"], P_OLD, [
        [68,47,35],[259,108,86],[0,0,2],[87,56,24],[49,44,6],[281,100,62],
        [97,81,25],[89,41,12],[230,126,62],[108,63,18],[125,72,35]]),
    (2021, "municipal primary", "Council", "Park City Council",
     ["Thomas C. Purcell","Jamison Brandi","Jeremy Rubell","Michael J. Franchek",
      "Tim B. Henney","John Greenfield","Daniel Lewis","Tana Toly"], P_OLD, [
        [22,4,60,7,64,27,10,66],[67,28,207,14,140,62,22,241],[2,0,2,0,0,0,0,0],
        [21,25,75,3,43,17,21,97],[13,6,44,1,29,13,9,54],[55,17,274,3,129,42,25,203],
        [13,17,107,8,76,19,11,105],[23,3,61,0,42,24,11,98],[52,22,207,9,153,47,13,225],
        [19,16,82,2,61,22,16,130],[40,9,127,5,69,19,18,132]]),
    (2021, "municipal general", "Mayor", "Park City Mayor",
     ["Nann Worel","Andy Beerman"], P_OLD, [
        [130,76],[389,207],[3,0],[132,89],[76,81],[390,203],
        [140,136],[123,72],[340,222],[156,82],[169,149]]),
    (2021, "municipal general", "Council", "Park City Council",
     ["Thomas C. Purcell","Jeremy Rubell","Tim B. Henney","Tana Toly"], P_OLD, [
        [0,109,100,128],[0,364,254,388],[0,3,0,3],[0,144,86,145],[0,91,68,101],
        [0,419,237,377],[0,172,124,176],[0,112,85,143],[0,364,245,374],
        [0,148,89,182],[0,204,151,191]]),
    (2023, "municipal general", "Council", "Park City Council",
     ["Ed Parigian","Matthew Nagie","Ryan Dickey","John Greenfield","Bill Ciraco","Bob Sertner"],
     P_OLD, [
        [175,150,239,95,167,157],[114,110,163,61,129,133],[2,0,3,0,5,1],
        [123,55,116,38,71,69],[56,36,54,24,39,46],[191,156,368,69,210,176],
        [130,100,207,60,137,101],[81,63,92,44,26,58],[187,132,252,55,184,162],
        [118,84,127,61,44,81],[134,86,157,50,146,100]]),
    (2025, "municipal general", "Mayor", "Park City Mayor",
     ["Jack Rubin","Ryan Dickey"], P_NEW, [
        [374,203],[199,150],[87,122],[56,51],[273,310],[161,190],
        [91,118],[211,243],[0,0],[85,159],[158,160]]),
    (2025, "municipal general", "Council", "Park City Council",
     ["Diego Zegarra","Jeremy Rubell","Tana Toly"], P_NEW, [
        [284,321,325],[185,185,235],[136,80,143],[60,52,74],[330,280,392],
        [226,131,255],[137,75,166],[286,179,318],[0,0,0],[186,63,212],[185,161,214]]),
]

prec_rows = []
for year, etype, office, contest, order, codes, rows in PRECINCT_TABLES:
    assert len(codes) == len(rows), (year, etype, office, len(codes), len(rows))
    for code, vals in zip(codes, rows):
        assert len(vals) == len(order), (year, office, code, len(vals), len(order))
        for cand, v in zip(order, vals):
            prec_rows.append(dict(
                year=year, election_type=etype, office=office, contest=contest,
                precinct_code=code, precinct_name=code, candidate=cand, votes=v))

# ---------------------------------------------------------------------------
# WRITE
# ---------------------------------------------------------------------------
def write(path, fields, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)
    print(f"wrote {len(rows):4d} rows -> {os.path.basename(path)}")

write(os.path.join(OUT,"park_city_races.csv"),
      ["year","election_type","office","district","contest","n_seats","n_candidates",
       "voting_method","total_first_choice_votes","winner","winner_votes","winner_pct",
       "runner_up","runner_up_votes","margin_votes","margin_pct"], races_rows)
write(os.path.join(OUT,"park_city_results_by_candidate.csv"),
      ["year","election_type","office","contest","candidate","votes","pct","rank","is_winner"],
      cand_rows)
write(os.path.join(OUT,"park_city_results_by_precinct.csv"),
      ["year","election_type","office","contest","precinct_code","precinct_name","candidate","votes"],
      prec_rows)

# ---------------------------------------------------------------------------
# VERIFY precinct totals vs candidate totals (where same source).
# (2025 precinct table sums run a few votes below the certified canvass because
# late-cured/provisional ballots are not assigned to a precinct -- expected.)
# ---------------------------------------------------------------------------
from collections import defaultdict
ptot = defaultdict(int)
for r in prec_rows:
    ptot[(r["year"], r["election_type"], r["office"], r["candidate"])] += r["votes"]
print("\nprecinct-sum vs certified-total checks:")
for c in CONTESTS:
    for name, v in c["cands"]:
        key = (c["year"], c["etype"], c["office"], name)
        if key in ptot:
            flag = "OK" if ptot[key]==v else f"DIFF (cert {v}, prec {ptot[key]})"
            print(f"  {c['year']} {c['etype'][-7:]:7} {c['office']:7} {name:28} {flag}")
