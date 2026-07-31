#!/usr/bin/env python3
"""
Build Lehi City (Utah County) municipal election CSVs: Mayor + City Council,
cycles 2019, 2021, 2023, 2025.

Lehi is a SIX-MEMBER form-of-government city: Mayor + 5 Council Members, ALL elected
AT-LARGE (no geographic districts), 4-year STAGGERED terms (alternating 3-seat / 2-seat
cycles). Council seats are NOT numbered/seat-specific on the ballot in these cycles --
candidates run in one citywide "Lehi City Council" field, top-N win.

TWO tabulation methods (see CLAUDE.md):
  * 2019  -> PLURALITY (vote-for-3). Source: Utah County certified results PDF.
  * 2021  -> RANKED-CHOICE VOTING (Lehi's first RCV year; NO primary).
            Mayor (2 candidates, decided round 1) + Council (vote-for-2, sequential RCV).
            Source: Utah County certified SOVC CSV (first-choice, incl. per precinct) +
            rcvis.com round tabulations / Lehi Free Press for final-round winner totals.
  * 2023  -> RANKED-CHOICE VOTING + a revived August PRIMARY (Vote-for-3 council; no mayor
            race this cycle). The 2023 PRIMARY is the famous Corey Astill mid-count
            withdrawal -> recount-without-Astill -> top-6 advance event. Source: state
            Enhanced Voting portal (certified first-choice + precincts) + rcvis (rounds).
  * 2025  -> PLURALITY + August primary. Mayor (vote-for-1) + Council (vote-for-2).
            Source: state Enhanced Voting portal JSON (citywide + per-precinct).

voting_method column: "plurality" or "RCV".

For MULTI-SEAT at-large races (both methods) the race-row winner / runner_up / margin use
the RANKING METRIC (round1 = first-choice for RCV, total votes for plurality):
  winner    = top vote-getter (rank 1)
  runner_up = first loser (rank N+1, the candidate who just missed the last seat)
  margin    = rank-N (last winner) minus rank-(N+1) (first loser) -- the seat-deciding margin
In every Lehi cycle the RCV round-by-round winner SET equals the top-N first-choice set
(RCV did not change who won), so is_winner = rank<=N holds -- EXCEPT the 2023 primary,
where Corey Astill led on first choice (rank 4) but WITHDREW, so the certified advancers
are hard-coded (Glade advanced in his place after the recount).

Outputs:
  lehi_races.csv               one row per race
  lehi_results_by_candidate.csv  race x candidate
  lehi_results_by_precinct.csv   precinct x candidate (first-choice for RCV)
"""
import json, csv, os, collections

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")


def load(fn):
    with open(os.path.join(RAW, fn)) as f:
        return json.load(f)


def pct(n, d):
    return round(100.0 * n / d, 2) if d else 0.0


races = []
by_candidate = []
by_precinct = []

CONTEST_MAYOR = "Lehi Mayor"
CONTEST_COUNCIL = "Lehi City Council"


# ---------------------------------------------------------------------------
# Generic builder for a single contest from a {name: votes} first-choice dict.
#   n_seats      = seats up (for a general); for a primary pass the GENERAL seat count
#   advance      = number who advance (primaries) OR None for a general (=> n_seats win)
#   winners      = explicit winner/advancer name list (overrides rank<=N); else top-N
#   finals       = {name: final_round_votes} for RCV winners (else {})
# ---------------------------------------------------------------------------
def add_contest(year, election_type, office, contest, first_choice, voting_method,
                n_seats, advance=None, winners=None, finals=None, withdrawn=None):
    finals = finals or {}
    withdrawn = set(withdrawn or [])
    total = sum(first_choice.values())
    ordered = sorted(first_choice.items(), key=lambda kv: -kv[1])
    n_win = advance if advance is not None else n_seats
    if winners is None:
        winners = [nm for nm, _ in ordered[:n_win]]
    winset = set(winners)
    district = "At-Large" if office == "Council" else ""
    for rank, (name, votes) in enumerate(ordered, 1):
        by_candidate.append({
            "year": year, "election_type": election_type, "office": office,
            "district": district, "contest": contest, "candidate": name,
            "voting_method": voting_method, "round1_votes": votes,
            "round1_pct": pct(votes, total),
            "final_votes": finals.get(name, ""), "rank": rank,
            "is_winner": "True" if name in winset else "False",
        })
    # race-level winner / runner_up / margin, computed from the WINNER SET so it is robust
    # to the 2023-primary Astill anomaly (a withdrawn candidate outpolling an advancer).
    #   winner    = top vote-getter (rank 1)
    #   last_win  = the winner with the FEWEST round1 votes  (the seat/advance boundary, hi)
    #   first_lose= the highest-round1 NON-winner, excluding any withdrawn candidate (lo)
    #   margin    = last_win - first_lose  (seat/advance-deciding margin)
    winner = ordered[0]
    win_rows = [(nm, v) for nm, v in ordered if nm in winset]
    lose_rows = [(nm, v) for nm, v in ordered if nm not in winset and nm not in withdrawn]
    last_win = min(win_rows, key=lambda kv: kv[1]) if win_rows else ("", 0)
    first_lose = lose_rows[0] if lose_rows else ("", 0)
    runner = first_lose
    margin = last_win[1] - first_lose[1]
    races.append({
        "year": year, "election_type": election_type, "office": office,
        "district": district, "contest": contest, "n_seats": n_seats,
        "n_candidates": len(first_choice), "voting_method": voting_method,
        "total_first_choice_votes": total,
        "winner": winner[0], "winner_votes": winner[1],
        "winner_pct": pct(winner[1], total),
        "runner_up": runner[0], "runner_up_votes": runner[1],
        "margin_votes": margin, "margin_pct": pct(margin, total),
    })


# ===========================================================================
# 2019 GENERAL -- PLURALITY, Council vote-for-3, NO mayor race this cycle.
# Source: raw/uc_2019_general_results.pdf  (Utah County OFFICIAL RESULTS,
#         "Lehi City Council / Vote For 3"). 6 candidates == 2*seats, so no primary.
# Winners (top 3): ALBRECHT, SOUTHWICK, KOIVISTO.
# ===========================================================================
add_contest(2019, "municipal general", "Council", CONTEST_COUNCIL,
            {"PAIGE ALBRECHT": 5250, "MIKE V SOUTHWICK": 4135, "KATIE KOIVISTO": 3969,
             "MATTHEW WYNN HEMMERT": 3763, "CODY BLACK": 3711, "JOHNNY REVILL": 3602},
            voting_method="plurality", n_seats=3)

# ===========================================================================
# 2021 GENERAL -- RCV (Lehi's first RCV cycle; NO primary).
# Source first-choice: raw/uc_2021_general_SOVC.csv (Utah County certified Statement of
#   Votes Cast; "Lehi Mayor 1st Choice" / "Lehi City Council 1st Choice" County-Totals row).
# Final-round winner totals: Lehi Free Press 2021-11-02 certified report
#   ("Condie won the first RCV seat with 3,073 votes in the 8th round; Hancock won the
#   second seat with 2,583 votes in the 7th round"), cross-ref rcvis_2021_council_seat*.
#   NOTE: the rcvis _u2/_u4 pages render DOUBLED cumulative finals (Condie 6167/Hancock
#   5466) -- a rcvis artifact; the certified press finals (3,073 / 2,583) are used here.
# ---------------------------------------------------------------------------
# MAYOR: only 2 candidates -> decided on first count (RCV == plurality, 1 round).
add_contest(2021, "municipal general", "Mayor", CONTEST_MAYOR,
            {"MARK I. JOHNSON": 6994, "JESSE L. RIDDLE": 4295},
            voting_method="RCV", n_seats=1,
            finals={"MARK I. JOHNSON": 6994})   # 1-round majority: final == first-choice
# COUNCIL: vote-for-2, 9 candidates, sequential RCV. Winners CONDIE & HANCOCK.
add_contest(2021, "municipal general", "Council", CONTEST_COUNCIL,
            {"CHRIS CONDIE": 2300, "PAUL HANCOCK": 1811, "MICHELLE MILES": 1376,
             "NICOLE KUNZE": 1291, "AARON BULLEN": 1134, "LORI MCINTOSH LE": 1108,
             "CAMI PURTSCHERT": 1003, "MONTANE C HAMILTON": 524, "ETHAN M. ERICKSON": 355},
            voting_method="RCV", n_seats=2,
            finals={"CHRIS CONDIE": 3073, "PAUL HANCOCK": 2583})

# ===========================================================================
# 2023 PRIMARY -- RCV (Aug 2023). Council vote-for-3 => top 6 advance. The Corey Astill
# withdrawal/recount event: Astill led on 1st choice (rank 4) but withdrew mid-count to
# run for state Senate; per LG guidance the city RECOUNTED WITHOUT Astill and advanced the
# top 6 -> ALBRECHT, STALLINGS, NEWALL, KUNZE, ROBERTS, GLADE (Glade advanced in Astill's
# place). Source: raw/rcvis_2023_council_primary_astill.html (15-candidate first-choice).
# ===========================================================================
add_contest(2023, "municipal primary", "Council", CONTEST_COUNCIL,
            {"PAIGE ALBRECHT": 732, "HEATHER NEWALL": 525, "MICHELLE STALLINGS": 489,
             "COREY ASTILL": 371, "NICOLE KUNZE": 345, "KENNETH ROBERTS": 221,
             "K. CASEY GLADE": 169, "JASON HILL": 148, "IELI CHARLIE TAUTUAA": 145,
             "HALEY SOUSA": 134, "R. CURTIS PAYNE": 106, "JEREMY K BAKER": 105,
             "JASON HARRIS": 51, "TYLER R. LINDSAY": 38, "BRENT SUMMERS": 29},
            voting_method="RCV", n_seats=3, advance=6,
            winners=["PAIGE ALBRECHT", "HEATHER NEWALL", "MICHELLE STALLINGS",
                     "NICOLE KUNZE", "KENNETH ROBERTS", "K. CASEY GLADE"],
            withdrawn=["COREY ASTILL"])

# ===========================================================================
# 2023 GENERAL -- RCV, Council vote-for-3 (NO mayor race this cycle).
# Source first-choice + precincts: state Enhanced Voting certified portal
#   (raw/ev_2023_general_ballot-items.json, "Lehi City Council 1st Choice"; turnout-
#   validated -- 8,185 council ballots ~ matches the 2019 ~8,143). Winners (top 3 first
#   choice; confirmed by Lehi Free Press 2023-11-21 certification report + rcvis rounds):
#   STALLINGS, ALBRECHT, NEWALL. Final-round totals from rcvis (Albrecht 2973 / Stallings
#   2917 / Newall 2863) -- rcvis tabulated on an earlier (smaller) canvass than the final
#   EV first-choice, so final_votes reflect the RCV outcome on that base; winners identical.
# ===========================================================================
add_contest(2023, "municipal general", "Council", CONTEST_COUNCIL,
            {"MICHELLE STALLINGS": 2096, "PAIGE ALBRECHT": 1754, "HEATHER NEWALL": 1467,
             "NICOLE KUNZE": 1121, "KENNETH ROBERTS": 1048, "K. CASEY GLADE": 699},
            voting_method="RCV", n_seats=3,
            finals={"PAIGE ALBRECHT": 2973, "MICHELLE STALLINGS": 2917,
                    "HEATHER NEWALL": 2863})

# ===========================================================================
# 2025 -- PLURALITY (Lehi did NOT use RCV in 2025), Aug primary + Nov general.
# Source: state Enhanced Voting portal JSON (raw/ev_2025_*.json), citywide + per precinct.
# ===========================================================================
def ev_options(detail):
    return [(o["name"][0]["text"], o["voteCount"]) for o in
            detail["summaryResults"]["ballotOptions"]
            if not (o["voteCount"] == 0 and o.get("isWriteIn"))]


def add_ev_precincts(detail, year, election_type, office, contest):
    district = "At-Large" if office == "Council" else ""
    for br in (detail.get("breakdownResults") or []):
        prec = br["precinct"]["name"][0]["text"]
        for o in br["ballotOptions"]:
            if o["voteCount"] == 0 and o.get("isWriteIn"):
                continue
            by_precinct.append({
                "year": year, "election_type": election_type, "office": office,
                "district": district, "contest": contest, "precinct": prec,
                "candidate": o["name"][0]["text"], "votes": o["voteCount"],
            })


# 2025 PRIMARY (Aug 12): Mayor vote-for-1 (4 cand -> top 2 advance);
#                        Council vote-for-2 (10 cand -> top 4 advance).
pm = load("ev_2025_primary_mayor_detail.json")
add_contest(2025, "municipal primary", "Mayor", CONTEST_MAYOR, dict(ev_options(pm)),
            voting_method="plurality", n_seats=1, advance=2)
add_ev_precincts(pm, 2025, "municipal primary", "Mayor", CONTEST_MAYOR)

pc = load("ev_2025_primary_council_detail.json")
add_contest(2025, "municipal primary", "Council", CONTEST_COUNCIL, dict(ev_options(pc)),
            voting_method="plurality", n_seats=2, advance=4)
add_ev_precincts(pc, 2025, "municipal primary", "Council", CONTEST_COUNCIL)

# 2025 GENERAL (Nov 4): Mayor vote-for-1; Council vote-for-2.
gm = load("ev_2025_general_mayor_detail.json")
add_contest(2025, "municipal general", "Mayor", CONTEST_MAYOR, dict(ev_options(gm)),
            voting_method="plurality", n_seats=1)
add_ev_precincts(gm, 2025, "municipal general", "Mayor", CONTEST_MAYOR)

gc = load("ev_2025_general_council_detail.json")
add_contest(2025, "municipal general", "Council", CONTEST_COUNCIL, dict(ev_options(gc)),
            voting_method="plurality", n_seats=2)
add_ev_precincts(gc, 2025, "municipal general", "Council", CONTEST_COUNCIL)


# ===========================================================================
# PRECINCT data for the RCV years (first-choice per precinct).
# 2021: raw/uc_2021_general_SOVC.csv  -- Lehi precincts (col0 prefix "LE"); 1st-choice cols.
# 2023: raw/ev_2023_general_council_1stchoice_detail.json -- EV breakdownResults.
# (2019 precinct = GAP: only a 22 MB suppressed countywide PDF, citywide totals used.)
# ===========================================================================
def add_2021_precincts():
    path = os.path.join(RAW, "uc_2021_general_SOVC.csv")
    rows = list(csv.reader(open(path, encoding="latin-1")))
    hdr0, hdr1 = rows[0], rows[1]

    def iv(x):
        x = (x or "").strip().replace(",", "")
        return int(x) if x and x not in ("-",) else 0
    # locate Lehi 1st-choice columns by header pair (contest, candidate)
    mayor_cols, council_cols = {}, {}
    for ci, top in enumerate(hdr0):
        if top == "Lehi Mayor 1st Choice":
            mayor_cols[hdr1[ci]] = ci
        elif top == "Lehi City Council 1st Choice":
            council_cols[hdr1[ci]] = ci
    lehi = [r for r in rows[3:] if r and r[0].upper().startswith("LE")]
    for r in lehi:
        prec = "25" + r[0]            # normalize to CountyID-prefixed (e.g. LE01 -> 25LE01)
        for nm, ci in mayor_cols.items():
            by_precinct.append({"year": 2021, "election_type": "municipal general",
                                "office": "Mayor", "district": "", "contest": CONTEST_MAYOR,
                                "precinct": prec, "candidate": nm, "votes": iv(r[ci])})
        for nm, ci in council_cols.items():
            by_precinct.append({"year": 2021, "election_type": "municipal general",
                                "office": "Council", "district": "At-Large",
                                "contest": CONTEST_COUNCIL, "precinct": prec,
                                "candidate": nm, "votes": iv(r[ci])})


def add_2023_precincts():
    detail = load("ev_2023_general_council_1stchoice_detail.json")
    for br in (detail.get("breakdownResults") or []):
        prec = br["precinct"]["name"][0]["text"]
        for o in br["ballotOptions"]:
            if o["voteCount"] == 0 and o.get("isWriteIn"):
                continue
            by_precinct.append({"year": 2023, "election_type": "municipal general",
                                "office": "Council", "district": "At-Large",
                                "contest": CONTEST_COUNCIL, "precinct": prec,
                                "candidate": o["name"][0]["text"], "votes": o["voteCount"]})


add_2021_precincts()
add_2023_precincts()


# ----- sort -----
_type_order = {"municipal primary": 0, "municipal general": 1}
_office_order = {"Mayor": 0, "Council": 1}
def _sort(r):
    return (r["year"], _type_order.get(r["election_type"], 9),
            _office_order.get(r["office"], 9))
races.sort(key=_sort)
by_candidate.sort(key=lambda r: (_sort(r), r["rank"]))
by_precinct.sort(key=lambda r: (r["year"], _type_order.get(r["election_type"], 9),
                                _office_order.get(r["office"], 9),
                                r["precinct"], r["candidate"]))


def writecsv(path, rows, cols):
    with open(os.path.join(HERE, path), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


writecsv("lehi_races.csv", races, [
    "year", "election_type", "office", "district", "contest", "n_seats",
    "n_candidates", "voting_method", "total_first_choice_votes", "winner",
    "winner_votes", "winner_pct", "runner_up", "runner_up_votes",
    "margin_votes", "margin_pct"])

writecsv("lehi_results_by_candidate.csv", by_candidate, [
    "year", "election_type", "office", "district", "contest", "candidate",
    "voting_method", "round1_votes", "round1_pct", "final_votes", "rank", "is_winner"])

writecsv("lehi_results_by_precinct.csv", by_precinct, [
    "year", "election_type", "office", "district", "contest", "precinct",
    "candidate", "votes"])

print(f"races: {len(races)}  candidate-rows: {len(by_candidate)}  "
      f"precinct-rows: {len(by_precinct)}")
# winners summary
for r in races:
    print(f"  {r['year']} {r['election_type']:18s} {r['office']:7s} "
          f"-> {r['winner']} ({r['voting_method']})")
