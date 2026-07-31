#!/usr/bin/env python3
"""
Build White City (Salt Lake County, Utah) municipal election results.

Three CSVs, normalized to the SLC/South-Jordan sibling 25-column schema:
  white_city_races.csv              one row per race
  white_city_results_by_candidate.csv   race x candidate
  white_city_results_by_precinct.csv    precinct x candidate

Sources (retained under raw/):
  raw/slco_municipal_results_white_city.csv
      -- the Salt Lake County Clerk SOVC, archive-normalized
         (salt_lake_county/elections/slco_municipal_results_long.csv),
         filtered to every 'WHITE CITY' contest.  Delivers the genuine
         2023 + 2025 council/mayor contests cleanly (precinct WHT001-004).
  raw/2019-11-05-general-election-sovc.xlsx
      -- the true county SOVC spreadsheet, re-parsed directly for the ONE
         council contest the archive normalizer dropped: the 2019 general
         'WHITE CITY METRO TOWNSHIP COUNCIL AT LARGE' (sheet 'WHT At-Large').
         Same failure mode South Jordan hit in 2019 (metro-township sheets
         keyed off a sheet code, so a '%WHITE CITY%' filter never matched).

DECOYS excluded (verified, never council races):
  * WHITE CITY WATER (2013)  -- White City Water Improvement District board.
  * WHITE CITY MSD (2015)    -- Municipal Services District ballot question.
  * WHITE CITY METRO TOWNSHIP-CITY (2015) -- incorporation ballot question.

GAP note (documented, NOT fabricated):
  * 2017 & 2021 have NO White City council contest in the raw SOVC (the peer
    small townships Copperton/Emigration/Kearns/Magna ARE present, White City
    is not).  The initial 5-member metro-township council was elected in the
    Nov-2016 EVEN-year general (incorporated Jan 1 2017), so 2017 is off-cycle;
    the seats later labelled B/C appear to have been filled uncontested in 2021
    (uncontested SLCo seats routinely carry no SOVC tally sheet) -> genuine
    absence, recovered where it exists (2019), documented where it does not.

Idempotent.  Run:  python3 clean_elections.py [--report]
"""
import csv, os, re, sys
from collections import defaultdict, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
CANON = os.path.join(HERE, "raw", "slco_municipal_results_white_city.csv")
SOVC2019 = os.path.join(HERE, "raw", "2019-11-05-general-election-sovc.xlsx")

RACES_HDR = ["year","election_type","office","district","contest","contest_verbatim",
    "n_seats","n_candidates","voting_method","total_votes","total_first_choice_votes",
    "winner","winner_votes","winner_pct","runner_up","runner_up_votes","margin_votes",
    "margin_pct","registered_voters","ballots_cast","turnout_pct","uncontested",
    "suppressed_precincts","note","source_file"]

# genuine White-City council/mayor contests carried cleanly by the archive parse
CANON_CONTESTS = {
    ("2023","WHITE CITY METRO TOWNSHIP COUNCIL AT-LARGE"):
        dict(office="Council", district="At-Large", n_seats=3,
             contest="White City Metro Township Council At-Large",
             note="Metro-township era (pre-city). 3 at-large seats; winners Flint/Shelton/Huish."),
    ("2025","WHITE CITY MAYOR"):
        dict(office="Mayor", district="", n_seats=1,
             contest="White City Mayor",
             note="First directly-elected mayor (city era, HB35 2024). Mayor votes on council."),
    ("2025","WHITE CITY COUNCIL AT-LARGE B"):
        dict(office="Council", district="At-Large B", n_seats=1,
             contest="White City Council At-Large B",
             note="City era. Single at-large seat B."),
    ("2025","WHITE CITY COUNCIL AT-LARGE C"):
        dict(office="Council", district="At-Large C", n_seats=1,
             contest="White City Council At-Large C",
             note="City era. Single at-large seat C; Mahoney unseated incumbent Cardenaz."),
}

def norm_name(raw):
    """Normalize a candidate name alongside (never replacing) the verbatim source."""
    s = re.sub(r"\s+", " ", (raw or "").strip())
    s = re.sub(r"\s*\((NP|NON|NP )\)\s*$", "", s, flags=re.I).strip()
    low = s.lower()
    if low.startswith("unresolved write") or low in ("write-in", "write in"):
        return "Write-in (unresolved)"
    # qualified write-in: keep the person's name, note the mode in verbatim
    s = re.sub(r"\s+qualified write.?in\s*$", "", s, flags=re.I).strip()
    s = s.lstrip("*").strip()
    return s

def is_real_candidate(norm):
    return norm != "Write-in (unresolved)"

# ---------------------------------------------------------------------------
# 1. read canonical (long) rows for the genuine contests
# ---------------------------------------------------------------------------
# structures: cand_votes[(year,contest)][norm] = votes ; verbatim map ; precinct
cand_votes = defaultdict(lambda: defaultdict(float))
cand_verbatim = defaultdict(dict)          # (year,contest) -> norm -> verbatim
prec_votes = defaultdict(lambda: defaultdict(float))  # (year,contest) -> (prec,norm) -> votes
reg_by_contest = defaultdict(lambda: defaultdict(float))  # (year,contest) -> prec -> reg
src_file = {}

with open(CANON) as f:
    for row in csv.DictReader(f):
        key = (row["year"], row["contest"])
        if key not in CANON_CONTESTS:
            continue
        norm = norm_name(row["candidate"])
        cand_verbatim[key].setdefault(norm, re.sub(r"\s+"," ",row["candidate"].strip()))
        v = float(row["votes"] or 0)
        cand_votes[key][norm] += v
        prec_votes[key][(row["precinct"], norm)] += v
        if row["registered_voters"]:
            # a precinct can carry a stray 0.0 alongside its true count across
            # vote-method rows -> keep the maximum (non-zero) reported value.
            rv = float(row["registered_voters"])
            reg_by_contest[key][row["precinct"]] = max(reg_by_contest[key][row["precinct"]], rv)
        src_file[key] = row["source_file"]

# ---------------------------------------------------------------------------
# 2. recover 2019 metro-township council from the raw SOVC 'WHT At-Large' sheet
# ---------------------------------------------------------------------------
import openpyxl
KEY19 = ("2019", "WHITE CITY METRO TOWNSHIP COUNCIL AT LARGE")
CANON_CONTESTS[KEY19] = dict(office="Council", district="At-Large", n_seats=3,
    contest="White City Metro Township Council At-Large",
    note="RECOVERED from raw 2019 SOVC sheet 'WHT At-Large' (dropped by the archive "
         "normalizer, which keyed metro-township contests off a sheet code). 3 at-large "
         "seats; winners Little/Perry/Flint all subsequently served on council.")
wb = openpyxl.load_workbook(SOVC2019, read_only=True, data_only=True)
ws = wb["WHT At-Large"]
rows19 = [[c for c in r] for r in ws.iter_rows(values_only=True)]
wb.close()
# row idx1 = candidate names in a repeating 4-col block; row idx2 = column labels;
# data rows have precinct in col0, reg in col1, then per-candidate blocks ending in
# a 'Total Votes' column; final col = row Total.
cand_row = rows19[1]
candidates19 = [str(c).strip() for c in cand_row if c not in (None, "", " ")]
# locate the 'Total Votes' column index for each candidate block
label_row = [str(c).strip() if c is not None else "" for c in rows19[2]]
tv_cols = [i for i, lab in enumerate(label_row) if lab == "Total Votes"]
assert len(tv_cols) == len(candidates19), (len(tv_cols), len(candidates19))
for r in rows19[3:]:
    if not r or not r[0]:
        continue
    prec = str(r[0]).strip()
    if prec.lower().startswith("total"):
        continue
    reg = r[1]
    reg_by_contest[KEY19][prec] = float(reg or 0)
    for cand, col in zip(candidates19, tv_cols):
        norm = norm_name(cand)
        cand_verbatim[KEY19].setdefault(norm, cand)
        v = float(r[col] or 0)
        cand_votes[KEY19][norm] += v
        prec_votes[KEY19][(prec, norm)] += v
src_file[KEY19] = os.path.basename(SOVC2019)

# ---------------------------------------------------------------------------
# 3. emit the three CSVs
# ---------------------------------------------------------------------------
races_rows, bycand_rows, byprec_rows = [], [], []

for key in sorted(CANON_CONTESTS, key=lambda k: (k[0], CANON_CONTESTS[k]["office"] != "Mayor", k[1])):
    year, contest_verbatim = key
    meta = CANON_CONTESTS[key]
    n_seats = meta["n_seats"]
    votes = cand_votes[key]
    # real candidates only for ranking; keep unresolved write-in (0) as a row
    ranked = sorted(votes.items(), key=lambda x: (-x[1], x[0]))
    real = [(n, v) for n, v in ranked if is_real_candidate(n)]
    total_votes = int(round(sum(votes.values())))
    n_cand = len(real)
    reg = int(round(sum(reg_by_contest[key].values()))) if reg_by_contest[key] else ""

    winner_norm, winner_v = real[0]
    winner_pct = round(100 * winner_v / total_votes, 2) if total_votes else ""
    # runner_up = first LOSER = the (n_seats+1)-th real candidate (at-large convention)
    if len(real) > n_seats:
        ru_norm, ru_v = real[n_seats]
    elif len(real) > 1:
        ru_norm, ru_v = real[1]
    else:
        ru_norm, ru_v = "", ""
    margin_v = int(winner_v - ru_v) if ru_v != "" else ""
    margin_pct = round(100 * margin_v / total_votes, 2) if (ru_v != "" and total_votes) else ""
    uncontested = (n_cand <= n_seats)

    races_rows.append({
        "year": year, "election_type": "municipal general",
        "office": meta["office"], "district": meta["district"],
        "contest": meta["contest"], "contest_verbatim": contest_verbatim,
        "n_seats": n_seats, "n_candidates": n_cand, "voting_method": "plurality",
        "total_votes": total_votes, "total_first_choice_votes": "",
        "winner": winner_norm, "winner_votes": int(winner_v), "winner_pct": winner_pct,
        "runner_up": ru_norm, "runner_up_votes": (int(ru_v) if ru_v != "" else ""),
        "margin_votes": margin_v, "margin_pct": margin_pct,
        "registered_voters": reg, "ballots_cast": "", "turnout_pct": "",
        "uncontested": uncontested, "suppressed_precincts": False,
        "note": meta["note"], "source_file": src_file[key],
    })

    # by-candidate
    for rank, (norm, v) in enumerate(ranked, start=1):
        bycand_rows.append({
            "year": year, "election_type": "municipal general",
            "office": meta["office"], "district": meta["district"],
            "contest": meta["contest"], "candidate": norm,
            "votes": int(round(v)),
            "pct": round(100 * v / total_votes, 2) if total_votes else 0,
            "rank": rank,
            "is_winner": is_real_candidate(norm) and rank <= n_seats,
        })

    # by-precinct
    for (prec, norm), v in sorted(prec_votes[key].items()):
        byprec_rows.append({
            "year": year, "election_type": "municipal general",
            "office": meta["office"], "district": meta["district"],
            "contest": meta["contest"], "precinct": prec, "candidate": norm,
            "votes": int(round(v)), "suppressed": False,
        })

def write_csv(path, header, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        for r in rows:
            w.writerow(r)

write_csv(os.path.join(HERE, "white_city_races.csv"), RACES_HDR, races_rows)
write_csv(os.path.join(HERE, "white_city_results_by_candidate.csv"),
          ["year","election_type","office","district","contest","candidate","votes","pct","rank","is_winner"],
          bycand_rows)
write_csv(os.path.join(HERE, "white_city_results_by_precinct.csv"),
          ["year","election_type","office","district","contest","precinct","candidate","votes","suppressed"],
          byprec_rows)

# ---------------------------------------------------------------------------
# 4. reconciliation asserts (by-precinct sums == by-candidate totals)
# ---------------------------------------------------------------------------
mismatch = 0
for key in CANON_CONTESTS:
    for norm, tot in cand_votes[key].items():
        psum = sum(v for (p, n), v in prec_votes[key].items() if n == norm)
        if round(psum) != round(tot):
            mismatch += 1
            print(f"  MISMATCH {key} {norm}: cand={tot} prec={psum}")
assert mismatch == 0, f"{mismatch} precinct/candidate mismatches"

print(f"races={len(races_rows)}  by_candidate={len(bycand_rows)}  by_precinct={len(byprec_rows)}  reconcile=OK")

if "--report" in sys.argv:
    print("\nYear  Office   District      Winner                 W  Runner-up            R  n")
    for r in races_rows:
        print(f"{r['year']}  {r['office']:7s} {r['district']:12s}  {r['winner']:20s} {r['winner_votes']:>4}  "
              f"{r['runner_up']:18s} {str(r['runner_up_votes']):>4}  {r['n_candidates']}")
