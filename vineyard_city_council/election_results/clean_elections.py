#!/usr/bin/env python3
"""
Build Vineyard (Utah County) municipal election CSVs.

TWO election methods (see CLAUDE.md):
  * 2019, 2021, 2023 = RANKED-CHOICE VOTING (Utah County RCV pilot). Source = rcvis.com
    round-by-round tabulations (raw HTML mirrored in raw/rcvis_*.html). Vineyard ran
    SEQUENTIAL multi-seat RCV: a separate single-winner tabulation per seat, with each
    seat's winner removed before the next seat is tabulated. We model each year's council
    contest as ONE multi-winner "At-Large" race with N winners. The per-candidate
    first-choice column = the FULL-FIELD round-1 totals (the first seat's round-1 count,
    where the whole field is present). final_round_votes = each candidate's vote total in
    the round in which the relevant seat was decided. "Margin" for an RCV race = the
    final-round margin of the seat that decided the last open seat (winner vs runner-up
    in that seat's final round); method noted in election_type.
  * 2025 = PLURALITY (Vineyard dropped RCV in April 2025). Vote-for-N at-large + a
    City-Council-only August primary. Source = Utah County / Enhanced Voting state portal
    JSON (raw/ev_*.json), which carries citywide summary AND per-precinct breakdowns.

Outputs:
  vineyard_races.csv               one row per race
  vineyard_results_by_candidate.csv  race x candidate
  vineyard_results_by_precinct.csv   precinct x candidate (2025 only; RCV years citywide)
"""
import json, csv, os

RAW = os.path.join(os.path.dirname(__file__), "raw")

def load(fn):
    with open(os.path.join(RAW, fn)) as f:
        return json.load(f)

# ----------------------------------------------------------------------------
# RCV YEARS (2019, 2021, 2023) -- transcribed from rcvis.com round tabulations.
# Each council race is modeled as ONE multi-winner At-Large contest.
# fc = full-field round-1 first-choice votes (from the first/full tabulation).
# final = candidate's total in the deciding round for their/ the last seat.
# winners = list of (name) who won a seat that cycle, in finish order.
# seat_winners: per-seat (winner_name, winner_final_votes, runnerup_name,
#               runnerup_final_votes, rounds) -- used to derive the seat-deciding margin.
# Source pages (mirrored in raw/):
#   2019 Seat1 (full field, Welsh wins R6): rcvis_2019_seat1.html
#   2019 Seat2 (Welsh removed, Flake wins R5): rcvis_2019_seat2.html
#   2021 Seat1 (Sifuentes wins R2):           rcvis_2021_seat1_sifuentes.html
#   2021 Seat2 (Rasmussen wins R3):           rcvis_2021_seat2_rasmussen.html
#   2023 (full field, Holdaway wins R6):      rcvis_2023_holdaway.html
#   2023 (Cameron majority R1):               rcvis_2023_cameron.html
#   2021 Mayor (Fullmer majority R1):         rcvis_2021_mayor.html
# ----------------------------------------------------------------------------

# Single-winner RCV mayor races. 2021 mayor (rcvis_2021_mayor.html, slug 21g_vi_m_u4):
# Julie Fullmer won outright on the first count (majority, no elimination rounds).
RCV_MAYOR = {
    2021: {
        "first_choice": {
            "JULIE FULLMER": 1329, "MARC BRIMHALL": 132,
            "MARIA GUADALUPE CANE": 73,
        },
        "winner": "JULIE FULLMER",
        "rounds": 1,
    },
}

RCV = {
    2019: {
        "n_seats": 2,
        # full-field round-1 first-choice (from Seat 1 / full tabulation, rcvis_2019_seat1)
        "first_choice": {
            "CRISTY WELSH": 347, "G. TYCE FLAKE": 277, "DAVID LAURET": 155,
            "KEITH KUDER": 101, "ANTHONY JENKINS": 94,
            "HECTOR RAFAEL HERNANDEZ": 89, "TAY GUDMUNDSON": 35,
        },
        # winners in finish order with their winning-round totals
        "winners": ["CRISTY WELSH", "G. TYCE FLAKE"],
        "final_round_votes": {"CRISTY WELSH": 589, "G. TYCE FLAKE": 660},
        # The last seat decided was Flake's (Seat 2 tabulation, Welsh removed):
        # final round (R5): Flake 660 vs Lauret 351.
        "seat_deciding": {"winner": "G. TYCE FLAKE", "winner_votes": 660,
                          "runner_up": "DAVID LAURET", "runner_up_votes": 351,
                          "rounds": 5},
    },
    2021: {
        "n_seats": 2,
        # Vineyard 2021 ran two SEPARATE full-field tabulations (Seat 1 & Seat 2) with
        # different candidate fields per seat. We take each seat's round-1 first-choice.
        # Seat 1 field (Sifuentes): Sifuentes 756, Rasmussen 324, Price 313, Pacheco 106.
        # Seat 2 field (Rasmussen, after Sifuentes removed): Rasmussen 540, Price 428, Pacheco 248.
        # Canonical first-choice = the higher/full-field round-1 (Seat-1 tabulation) where a
        # candidate appears in the full field; Sifuentes only in Seat 1.
        "first_choice": {
            "MARDI SIFUENTES": 756, "AMBER RASMUSSEN": 324,
            "KRISTAL C. PRICE": 313, "NEF PACHECO": 106,
        },
        "winners": ["MARDI SIFUENTES", "AMBER RASMUSSEN"],
        "final_round_votes": {"MARDI SIFUENTES": 764, "AMBER RASMUSSEN": 749},
        # Last seat decided = Rasmussen's (Seat 2, R3): Rasmussen 749 vs Price 448.
        "seat_deciding": {"winner": "AMBER RASMUSSEN", "winner_votes": 749,
                          "runner_up": "KRISTAL C. PRICE", "runner_up_votes": 448,
                          "rounds": 3},
    },
    2023: {
        "n_seats": 2,
        # full-field round-1 (rcvis_2023_holdaway, full 7-candidate field)
        "first_choice": {
            "JACOB HOLDAWAY": 533, "SARA CAMERON": 459, "CRISTY WELSH": 291,
            "CADEN RHOTON": 212, "NATALIE HARBIN": 208,
            "ALEXANDER TEEMSMA": 75, "JOSHUA HENDRIX": 9,
        },
        # Cameron won her seat outright with a R1 majority (rcvis_2023_cameron: 907 = 50.9%);
        # Holdaway won the other seat in R6 (1097). Finish order: Cameron (majority), Holdaway.
        "winners": ["SARA CAMERON", "JACOB HOLDAWAY"],
        "final_round_votes": {"SARA CAMERON": 907, "JACOB HOLDAWAY": 1097},
        # Last seat decided = Holdaway's (full tabulation, R6): Holdaway 1097 vs Welsh 589.
        "seat_deciding": {"winner": "JACOB HOLDAWAY", "winner_votes": 1097,
                          "runner_up": "CRISTY WELSH", "runner_up_votes": 589,
                          "rounds": 6},
    },
}

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def pct(n, d):
    return round(100.0 * n / d, 2) if d else 0.0

races = []            # vineyard_races.csv rows
by_candidate = []     # vineyard_results_by_candidate.csv rows
by_precinct = []      # vineyard_results_by_precinct.csv rows


def add_rcv_year(year):
    spec = RCV[year]
    fc = spec["first_choice"]
    n_seats = spec["n_seats"]
    total = sum(fc.values())
    # order by first-choice desc, but winners (in finish order) take ranks 1..N for is_winner
    winners = set(spec["winners"])
    # rank by first-choice votes; is_winner = candidate is in the cycle's winner set
    ordered = sorted(fc.items(), key=lambda kv: -kv[1])
    contest = "Vineyard City Council"
    for rank, (name, votes) in enumerate(ordered, 1):
        by_candidate.append({
            "year": year, "election_type": "municipal general (RCV)",
            "office": "Council", "contest": contest, "candidate": name,
            "votes": votes, "pct": pct(votes, total), "rank": rank,
            "is_winner": "Y" if name in winners else "N",
            "final_round_votes": spec["final_round_votes"].get(name, ""),
        })
    # For a multi-winner RCV race, the race-level winner/runner_up/margin describe the
    # SEAT-DECIDING contest (the last open seat's final round) so winner_votes, runner_up,
    # and margin are all internally consistent (all final-round figures from one tabulation).
    # The OTHER seat winner(s) are flagged is_winner=Y in the by-candidate CSV. winner_pct
    # here is the seat-deciding winner's share of that final round's two-candidate split.
    sd = spec["seat_deciding"]
    fr_total = sd["winner_votes"] + sd["runner_up_votes"]
    races.append({
        "year": year, "election_type": "municipal general (RCV)", "office": "Council",
        "district": "At-Large", "contest": contest, "n_candidates": len(fc),
        "total_votes": total,  # = first-choice votes cast (round-1 full field)
        "winner": sd["winner"], "winner_votes": sd["winner_votes"],
        "winner_pct": pct(sd["winner_votes"], fr_total),
        "runner_up": sd["runner_up"], "runner_up_votes": sd["runner_up_votes"],
        "margin_votes": sd["winner_votes"] - sd["runner_up_votes"],
        "margin_pct": pct(sd["winner_votes"] - sd["runner_up_votes"], fr_total),
    })


def add_rcv_mayor(year):
    spec = RCV_MAYOR[year]
    fc = spec["first_choice"]
    total = sum(fc.values())
    ordered = sorted(fc.items(), key=lambda kv: -kv[1])
    contest = "Vineyard Mayor"
    win = spec["winner"]
    for rank, (name, votes) in enumerate(ordered, 1):
        by_candidate.append({
            "year": year, "election_type": "municipal general (RCV)",
            "office": "Mayor", "contest": contest, "candidate": name,
            "votes": votes, "pct": pct(votes, total), "rank": rank,
            "is_winner": "Y" if name == win else "N",
            # single-round majority win -> final-round = first-choice for the winner
            "final_round_votes": votes if (name == win and spec["rounds"] == 1) else "",
        })
    w, r = ordered[0], (ordered[1] if len(ordered) > 1 else ("", 0))
    races.append({
        "year": year, "election_type": "municipal general (RCV)", "office": "Mayor",
        "district": "", "contest": contest, "n_candidates": len(fc),
        "total_votes": total, "winner": w[0], "winner_votes": w[1],
        "winner_pct": pct(w[1], total), "runner_up": r[0], "runner_up_votes": r[1],
        "margin_votes": w[1] - r[1], "margin_pct": pct(w[1] - r[1], total),
    })


def ev_options(detail):
    return detail["summaryResults"]["ballotOptions"]


def add_plurality_contest(detail, year, election_type, office, n_seats):
    """detail = a single ballot-item JSON (has summaryResults + breakdownResults)."""
    contest = detail["name"][0]["text"]
    opts = [(o["name"][0]["text"], o["voteCount"]) for o in ev_options(detail)
            if not (o["voteCount"] == 0 and o["isWriteIn"])]
    total = sum(v for _, v in opts)
    ordered = sorted(opts, key=lambda kv: -kv[1])
    for rank, (name, votes) in enumerate(ordered, 1):
        by_candidate.append({
            "year": year, "election_type": election_type, "office": office,
            "contest": contest, "candidate": name, "votes": votes,
            "pct": pct(votes, total), "rank": rank,
            "is_winner": "Y" if rank <= n_seats else "N", "final_round_votes": "",
        })
    winner = ordered[0]
    if n_seats == 1:  # single-winner (Mayor): runner_up = rank 2
        ru = ordered[1] if len(ordered) > 1 else ("", 0)
    else:             # vote-for-N: runner_up = first loser (rank N+1), seat-deciding margin
        boundary_win = ordered[n_seats - 1]
        ru = ordered[n_seats] if len(ordered) > n_seats else ("", 0)
        winner = (ordered[0][0], ordered[0][1])  # report top vote-getter as winner
    # seat-deciding margin for vote-for-N
    if n_seats == 1:
        mwin, mlose = ordered[0], (ordered[1] if len(ordered) > 1 else ("", 0))
    else:
        mwin = ordered[n_seats - 1]
        mlose = ordered[n_seats] if len(ordered) > n_seats else ("", 0)
    races.append({
        "year": year, "election_type": election_type, "office": office,
        "district": "At-Large" if office == "Council" else "",
        "contest": contest, "n_candidates": len(opts), "total_votes": total,
        "winner": winner[0], "winner_votes": winner[1], "winner_pct": pct(winner[1], total),
        "runner_up": ru[0], "runner_up_votes": ru[1],
        "margin_votes": mwin[1] - mlose[1],
        "margin_pct": pct(mwin[1] - mlose[1], total),
    })
    # precinct rows
    for br in (detail.get("breakdownResults") or []):
        prec = br["precinct"]["name"][0]["text"]
        for o in br["ballotOptions"]:
            nm = o["name"][0]["text"]
            if o["voteCount"] == 0 and o["isWriteIn"]:
                continue
            by_precinct.append({
                "year": year, "election_type": election_type, "office": office,
                "contest": contest, "precinct": prec, "candidate": nm,
                "votes": o["voteCount"],
            })


# ----- build -----
for y in (2019, 2021, 2023):
    add_rcv_year(y)

# 2021 Mayor was also an RCV race (single-winner, majority on first count).
add_rcv_mayor(2021)

# 2025 PRIMARY (City Council only; Vote for 3 -> top 6 advance). No mayor primary.
prim = load("ev_2025_primary_council_detail.json")
add_plurality_contest(prim, 2025, "municipal primary", "Council", n_seats=6)  # advance top 2N=6

# 2025 GENERAL
gmayor = load("ev_2025_general_mayor_detail.json")
gcouncil = load("ev_2025_general_council_detail.json")
add_plurality_contest(gmayor, 2025, "municipal general", "Mayor", n_seats=1)
add_plurality_contest(gcouncil, 2025, "municipal general", "Council", n_seats=3)


# ----- sort for stable, readable output: by year, then primary-before-general,
# then Mayor-before-Council -----
_type_order = {"municipal primary": 0, "municipal general": 1, "municipal general (RCV)": 1}
_office_order = {"Mayor": 0, "Council": 1}
_sort = lambda r: (r["year"], _type_order.get(r["election_type"], 9),
                   _office_order.get(r["office"], 9))
races.sort(key=_sort)
by_candidate.sort(key=lambda r: (_sort(r), r["rank"]))
by_precinct.sort(key=lambda r: (r["year"], r["office"], r["precinct"], r["candidate"]))


# ----- write -----
def writecsv(path, rows, cols):
    with open(os.path.join(os.path.dirname(__file__), path), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)

writecsv("vineyard_races.csv", races, [
    "year", "election_type", "office", "district", "contest", "n_candidates",
    "total_votes", "winner", "winner_votes", "winner_pct", "runner_up",
    "runner_up_votes", "margin_votes", "margin_pct"])

writecsv("vineyard_results_by_candidate.csv", by_candidate, [
    "year", "election_type", "office", "contest", "candidate", "votes", "pct",
    "rank", "is_winner", "final_round_votes"])

writecsv("vineyard_results_by_precinct.csv", by_precinct, [
    "year", "election_type", "office", "contest", "precinct", "candidate", "votes"])

print(f"races: {len(races)}  candidate-rows: {len(by_candidate)}  precinct-rows: {len(by_precinct)}")
