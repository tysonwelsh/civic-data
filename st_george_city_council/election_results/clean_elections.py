#!/usr/bin/env python3
"""
Build St. George (Utah) municipal election results from Washington County
wide-crosstab CSV exports.

Source files (in raw/) are county-wide precinct x candidate crosstabs:
  row 0 = contest name (repeated once per candidate column)
  row 1 = party (all "NON" for municipal)
  row 2 = candidate name
  rows 3.. = one row per precinct (cols: COUNTY NUMBER, PRECINCT CODE,
             PRECINCT NAME, REGISTERED VOTERS TOTAL, BALLOTS CAST TOTAL,
             BALLOTS CAST BLANK, then one int per candidate column)
  last data row is usually a "Total"/"Totals" precinct row.

We keep ONLY St. George City contests (Mayor + City Council), drop the
OVER VOTES / UNDER VOTES / Withdrawn / Disqualified / Cancelled pseudo-
candidates, and emit:
  st_george_results_by_precinct.csv   precinct x candidate
  st_george_results_by_candidate.csv  race x candidate (votes, pct, rank, is_winner)
  st_george_races.csv                 one row per race (winner, runner-up, margin)

AT-LARGE MODEL
--------------
St. George elects ALL seats citywide (no districts). City Council runs as a
SINGLE multi-winner field: the top N vote-getters win the N open seats that
cycle (N = SEATS[year][type]). So a council "race" has multiple winners;
is_winner = (rank <= N). In st_george_races.csv, `winner` is the top vote-getter,
`runner_up` is the candidate at rank N+1 (the first loser / the seat-deciding
margin), and `margin_*` is rank N vs rank N+1 (the closest seat boundary).
Mayor is a normal single-winner race. district column = "At-Large".
"""
import csv, os, sys

RAW = os.path.join(os.path.dirname(__file__), "raw")
OUT = os.path.dirname(__file__)

# (filename, year, election_type)
FILES = [
    ("washco-2019-general-municipal-export.csv", 2019, "municipal general"),
    ("washco-20210810-municipal-primary.csv",    2021, "municipal primary"),
    ("washco-20211102-results-export.csv",       2021, "municipal general"),
    ("washco-202309-results-export.csv",         2023, "municipal primary"),
    ("washco-20231121-results-export.csv",       2023, "municipal general"),
    ("washco-20250812-results-export.csv",       2025, "municipal primary"),
    ("washco-20251104-results-export.csv",       2025, "municipal general"),
]

# Number of seats each contest fills (general) / advances x2 (primary).
# Council seats up per cycle (confirmed via county positions-to-be-filled
# notices + Ballotpedia/St. George News cross-check):
#   2019: 3 council seats | 2021: mayor + 2 council | 2023: 3 council
#   2025: mayor + 2 council
# In a primary the field is narrowed to twice the seats (top 2N advance);
# we still rank, and is_winner in a primary = advanced to general (rank<=2N).
SEATS = {
    (2019, "municipal general", "Council"): 3,
    (2021, "municipal general", "Mayor"): 1,
    (2021, "municipal general", "Council"): 2,
    (2021, "municipal primary", "Mayor"): 1,    # advances 2
    (2021, "municipal primary", "Council"): 2,  # advances 4
    (2023, "municipal general", "Council"): 3,
    (2023, "municipal primary", "Council"): 3,  # advances 6
    (2025, "municipal general", "Mayor"): 1,
    (2025, "municipal general", "Council"): 2,
    (2025, "municipal primary", "Mayor"): 1,    # advances 2
    (2025, "municipal primary", "Council"): 2,  # advances 4
}

NON_CANDIDATES = {
    "OVER VOTES", "UNDER VOTES", "WITHDRAWN", "WITHDREW", "DISQUALIFIED",
    "CANCELLED", "WITHDRAWAL",
}

def is_stgeorge(contest):
    c = contest.strip()
    # St George Mayor / St George City Mayor / St George City Council
    if "St George" not in c and "St. George" not in c:
        return False
    if "Bond" in c:           # St George City Special Bond Election - exclude
        return False
    return True

def office_of(contest):
    return "Mayor" if "Mayor" in contest else "Council"

def is_total_row(row):
    pn = (row[2] or "").strip().lower()
    pc = (row[1] or "").strip().lower()
    return (pn in ("total", "totals", "county totals", "grand total")
            or pc in ("total", "totals", "zzz"))

def load(fname):
    with open(os.path.join(RAW, fname), newline="", encoding="utf-8-sig") as fh:
        return list(csv.reader(fh))

def main():
    by_precinct = []   # year,type,office,contest,precinct_code,precinct_name,candidate,votes
    # races[(year,type,office)] = {candidate: total_votes}
    races = {}

    for fname, year, etype in FILES:
        rows = load(fname)
        contests, parties, cands = rows[0], rows[1], rows[2]
        ncol = len(cands)
        # identify St George candidate columns
        cols = []
        for i in range(6, ncol):
            con = contests[i] if i < len(contests) else ""
            if not is_stgeorge(con):
                continue
            cand = (cands[i] if i < len(cands) else "").strip()
            if not cand or cand.upper() in NON_CANDIDATES:
                continue
            cols.append((i, office_of(con), cand))

        for r in rows[3:]:
            if len(r) < 6 or not (r[0] or r[1] or r[2]):
                continue
            total_row = is_total_row(r)
            pcode = (r[1] or "").strip()
            pname = (r[2] or "").strip()
            for i, office, cand in cols:
                if i >= len(r):
                    continue
                v = (r[i] or "").strip()
                if v == "":
                    continue
                try:
                    votes = int(float(v))
                except ValueError:
                    continue
                key = (year, etype, office)
                con_name = f"St George {'Mayor' if office=='Mayor' else 'City Council'}"
                if total_row:
                    races.setdefault(key, {}).setdefault(cand, 0)
                    races[key][cand] += votes
                else:
                    by_precinct.append([year, etype, office, con_name,
                                        pcode, pname, cand, votes])

    # If a file had no explicit Total row, fall back to summing precinct rows.
    summed = {}
    for year, etype, office, con, pcode, pname, cand, votes in by_precinct:
        summed.setdefault((year, etype, office), {}).setdefault(cand, 0)
        summed[(year, etype, office)][cand] += votes
    for key, cmap in summed.items():
        if key not in races or not races[key]:
            races[key] = cmap

    # ---- by_candidate + races ----
    by_candidate = []
    race_rows = []
    for (year, etype, office), cmap in sorted(races.items()):
        con = f"St George {'Mayor' if office=='Mayor' else 'City Council'}"
        ranked = sorted(cmap.items(), key=lambda kv: (-kv[1], kv[0]))
        total = sum(v for _, v in ranked)
        nseats = SEATS.get((year, etype, office), 1)
        ncand = len(ranked)
        # General: top nseats WIN. Primary: top 2*nseats ADVANCE to general
        # (is_winner here = "advanced"). If field already <= the cutoff,
        # everyone advances/wins.
        cutoff = nseats if etype.endswith("general") else 2 * nseats
        for rank, (cand, votes) in enumerate(ranked, 1):
            pct = round(100.0 * votes / total, 2) if total else 0.0
            is_win = rank <= cutoff
            by_candidate.append([year, etype, office, con, cand, votes, pct,
                                 rank, "Y" if is_win else "N"])
        # race-level row
        win_c, win_v = ranked[0]
        win_pct = round(100.0 * win_v / total, 2) if total else 0.0
        # runner-up = the seat/advancement boundary: candidate at rank cutoff+1
        # (first loser). Captures the margin that decided the last seat (general)
        # or the last advancement slot (primary).
        if ncand > cutoff:
            ru_c, ru_v = ranked[cutoff]
            last_winner_v = ranked[cutoff - 1][1]
            margin_v = last_winner_v - ru_v
        else:
            ru_c, ru_v, margin_v = "", 0, win_v
        margin_pct = round(100.0 * margin_v / total, 2) if total else 0.0
        race_rows.append([year, etype, office,
                          "At-Large" if office == "Council" else "",
                          con, ncand, total, win_c, win_v, win_pct,
                          ru_c, ru_v, margin_v, margin_pct])

    # ---- write ----
    with open(os.path.join(OUT, "st_george_results_by_precinct.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["year","election_type","office","contest","precinct_code",
                    "precinct_name","candidate","votes"])
        w.writerows(sorted(by_precinct, key=lambda x: (x[0],x[1],x[2],x[4],x[6])))

    with open(os.path.join(OUT, "st_george_results_by_candidate.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["year","election_type","office","contest","candidate",
                    "votes","pct","rank","is_winner"])
        w.writerows(by_candidate)

    with open(os.path.join(OUT, "st_george_races.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["year","election_type","office","district","contest",
                    "n_candidates","total_votes","winner","winner_votes",
                    "winner_pct","runner_up","runner_up_votes","margin_votes",
                    "margin_pct"])
        w.writerows(race_rows)

    print(f"races: {len(race_rows)}  candidate-rows: {len(by_candidate)}  "
          f"precinct-rows: {len(by_precinct)}")

if __name__ == "__main__":
    main()
