#!/usr/bin/env python3
"""
Build Orem's tidy election_results from Utah County raw sources.

Orem City = 6 council members + 1 Mayor, ALL ELECTED AT-LARGE (no districts),
nonpartisan, 4-yr staggered terms -> 3 council seats up each odd year; Mayor on a
separate 4-yr cycle (elected 2017, 2021, 2025).  Cycles covered: 2019, 2021, 2023, 2025.

AT-LARGE VOTE-FOR-N MODEL (council):
  City Council runs as ONE multi-winner field per cycle. All candidates appear in the
  single "Orem City Council" contest; the TOP N vote-getters win the N open seats.
  N = number of council seats up that cycle = 3 in every cycle here ("Vote For 3" on the
  official county PDFs).  district = "At-Large" for council; Mayor is single-winner.
    - is_winner = Y for rank <= N (general) / rank <= 2N (primary: top 2N advance).
    - runner_up / margin in <city>_races.csv = the SEAT-DECIDING boundary
      (rank N winner minus rank N+1 first-loser), i.e. the closeness of the final seat.
    - total_votes is inflated by vote-for-N (each voter may pick up to N), so candidate
      pct = share of all council votes cast, NOT turnout.  Mayor pct is normal.

Sources (in raw/, never edited):
  - 2021 & 2025 SOVC CSVs (wide crosstab) -> precinct-level + citywide  (general + primary*)
  - 2019 & 2023 born-digital rollup PDFs   -> citywide ONLY (no precinct SOVC CSV published)
  (* 2025 had NO mayor primary: only 2 mayor candidates, so no primary needed.)

Outputs:
  orem_races.csv                one row per race (winner/runner-up/seat-margin/turnout)
  orem_results_by_candidate.csv race x candidate (votes, pct, rank, is_winner)
  orem_results_by_precinct.csv  precinct x candidate (2021/2025 CSV cycles only; 2023&2019 absent)

Re-run: python3 clean_elections.py
"""
import csv, os

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")

# Council seats up per cycle (= N for the vote-for-N model). Orem: 3 each odd year.
SEATS = {2019: 3, 2021: 3, 2023: 3, 2025: 3}

# Header labels that are NOT real candidates -> drop. (WRITE-IN is kept.)
NON_CANDIDATE = {"OVER VOTES", "UNDER VOTES", "VOTERS", "BALLOTS CAST",
                 "TOTAL VOTES CAST", "TOTAL", "CONTEST TOTALS", "FOR", "AGAINST", ""}


# ---- contest normalization -------------------------------------------------
def normalize_contest(raw):
    """Map a raw contest header to (office, district, canonical_contest) or None.
    Keep ONLY Orem Mayor / Orem City Council. Exclude every other Utah County city."""
    s = raw.strip()
    low = s.lower()
    if "orem" not in low:
        return None
    if "proposition" in low or "rap tax" in low or "parc" in low or "bond" in low:
        return None  # ballot measures excluded
    if "mayor" in low:
        return ("Mayor", "", "Orem Mayor")
    if "council" in low:
        return ("Council", "At-Large", "Orem City Council")
    return None


# ---- wide-crosstab SOVC CSV parser ----------------------------------------
def parse_sovc_csv(path, header_rows, precinct_col, precinct_prefix):
    """Unpivot a Utah County wide-crosstab SOVC CSV for Orem columns.

    header_rows : number of header rows; row 0 = contest (spans candidate cols),
                  LAST header row = candidate names (middle rows = party 'NON', ignored).
    precinct_col: 0-indexed column holding the precinct CODE (e.g. 25OR01 / OR01).
    Returns (citywide_totals, precinct_rows).
    """
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    contest_row = rows[0]
    cand_row = rows[header_rows - 1]

    colmap = {}
    for i, craw in enumerate(contest_row):
        norm = normalize_contest(craw)
        if not norm:
            continue
        cand = cand_row[i].strip().rstrip(":")
        if cand.upper() in NON_CANDIDATE:
            continue
        office, district, contest = norm
        colmap[i] = (office, district, contest, cand)

    citywide = {}
    precinct_rows = []
    for r in rows[header_rows:]:
        if precinct_col >= len(r):
            continue
        pcode = r[precinct_col].strip().upper()
        idx = pcode.find(precinct_prefix)
        if idx == -1:
            continue
        precinct = pcode[idx:]                 # 25OR01 / OR01
        if precinct.startswith("25"):
            precinct = precinct[2:]            # -> OR01 (canonical, county-prefix stripped)
        for i, (office, district, contest, cand) in colmap.items():
            if i >= len(r):
                continue
            cell = r[i].replace(",", "").strip()
            if not cell:
                continue
            try:
                v = int(cell)
            except ValueError:
                continue
            d = citywide.setdefault(contest, {"office": office, "district": district, "cands": {}})
            d["cands"][cand] = d["cands"].get(cand, 0) + v
            if v:
                precinct_rows.append({"office": office, "district": district,
                                      "contest": contest, "precinct": precinct,
                                      "candidate": cand, "votes": v})
    return citywide, precinct_rows


# ---- citywide-only data hand-extracted from born-digital rollup PDFs --------
# 2019 + 2023 published NO Orem SOVC CSV (PDF rollup ONLY -> citywide totals, no precinct).
# Every value verified against `pdftotext -layout` of the official Utah County PDFs in raw/.
PDF_CITYWIDE = {
    # (year, election_type) -> {contest: {office,district,cands:{name:votes}}}
    (2019, "municipal general"): {       # raw/2019_General_Results_PDF_*.pdf  ("Vote For 3")
        "Orem City Council": {"office": "Council", "district": "At-Large",
            "cands": {"TERRY D PETERSON": 9858, "JEFFREY K LAMBSON": 7995,
                      "DEBBY LAURET": 6740, "SAM LENTZ": 6728,
                      "SPENCER RANDS": 5547, "NICHELLE JENSEN": 3644}},
    },
    (2019, "municipal primary"): {       # raw/2019_Primary_Results_PDF_*.pdf  (top 6 advance)
        "Orem City Council": {"office": "Council", "district": "At-Large",
            "cands": {"TERRY D PETERSON": 6176, "DEBBY LAURET": 5005, "SAM LENTZ": 3924,
                      "JEFFREY K LAMBSON": 3909, "SPENCER RANDS": 2557,
                      "NICHELLE JENSEN": 2086, "DAVID G PRZYBYLA": 1370,
                      "MICKEY W COCHRAN": 1369, "DAVID HALLIDAY": 1159,
                      "TOMMY WILLIAMS": 697, "MARTIN WRIGHT": 567}},
    },
    (2023, "municipal general"): {       # raw/2023_General_voting_results_*.pdf  ("Vote For 3")
        "Orem City Council": {"office": "Council", "district": "At-Large",
            "cands": {"JEFFREY K. LAMBSON": 9098, "JENN GALE": 8606, "CHRIS KILLPACK": 8457,
                      "CRYSTAL MUHLESTEIN": 7994, "MATT MCKELL": 7334, "SPENCER RANDS": 5883}},
    },
    (2023, "municipal primary"): {       # raw/2023_Primary_voting_results_*.pdf  (top 6 advance)
        "Orem City Council": {"office": "Council", "district": "At-Large",
            "cands": {"JEFFREY K. LAMBSON": 7056, "JENN GALE": 6489, "CHRIS KILLPACK": 6323,
                      "CRYSTAL MUHLESTEIN": 4489, "MATT MCKELL": 4138, "SPENCER RANDS": 3573,
                      "MIKE CARPENTER": 1701, "HEATHER M. FRY": 1150, "GREG DUERDEN": 956,
                      "DAVID EDWARD GARBER": 573, "WADE A. SEWELL": 250,
                      "ARCHIE A. WILLIAMS III": 147}},
    },
}


# ---- assemble all cycles ---------------------------------------------------
def build():
    citywide_all = {}
    precinct_all = []

    # (year, etype, file, header_rows, precinct_col, precinct_prefix)
    csv_specs = [
        (2021, "municipal primary", "21_PP_2021_Primary_Statement_of_Votes_Cast_SUPPRESSED_bd47a35ddf.csv", 3, 2, "OR"),
        (2021, "municipal general", "21_G_Countywide_SOVC_suppressed_1b85ad469d.csv", 2, 0, "OR"),
        (2025, "municipal primary", "2025_Primary_SOVC_suppressed_4bc086dabf.csv", 3, 2, "OR"),
        (2025, "municipal general", "SOVC_Simple_Redacted_7a5eddcaf2.csv", 3, 2, "OR"),
    ]
    for year, etype, fname, hdr, pcol, pref in csv_specs:
        cw, pr = parse_sovc_csv(os.path.join(RAW, fname), hdr, pcol, pref)
        citywide_all[(year, etype)] = cw
        for row in pr:
            precinct_all.append(dict(row, year=year, election_type=etype))

    for key, data in PDF_CITYWIDE.items():
        citywide_all[key] = data

    return citywide_all, precinct_all


def pct(v, total):
    return round(100.0 * v / total, 2) if total else 0.0


def write_outputs(citywide_all, precinct_all):
    races, by_cand = [], []

    for (year, etype) in sorted(citywide_all):
        is_primary = "primary" in etype
        for contest, d in sorted(citywide_all[(year, etype)].items(),
                                 key=lambda kv: (kv[1]["office"] != "Mayor", kv[0])):
            office, district = d["office"], d["district"]
            cands = sorted(d["cands"].items(), key=lambda kv: -kv[1])
            total = sum(d["cands"].values())

            # winners-cut N: Mayor single-winner (primary advances top 2);
            # Council vote-for-N (general N winners, primary top 2N advance).
            if office == "Mayor":
                win_cut = 2 if is_primary else 1
            else:
                n = SEATS.get(year, 1)
                win_cut = 2 * n if is_primary else n

            ranked = []
            for rank, (name, votes) in enumerate(cands, 1):
                p = pct(votes, total)
                is_win = rank <= win_cut
                ranked.append((name, votes, p, rank, is_win))
                by_cand.append({"year": year, "election_type": etype, "office": office,
                                "district": district, "contest": contest, "candidate": name,
                                "votes": votes, "pct": p, "rank": rank,
                                "is_winner": "Y" if is_win else "N"})

            winner, wv, wp = ranked[0][0], ranked[0][1], ranked[0][2]
            # seat-deciding boundary: rank win_cut (last winner/advancer) vs win_cut+1 (first loser).
            if len(ranked) > win_cut:
                last_win = ranked[win_cut - 1]
                first_loss = ranked[win_cut]
                ru, ruv = first_loss[0], first_loss[1]
                margin = last_win[1] - first_loss[1]
            elif len(ranked) > 1:
                ru, ruv = ranked[1][0], ranked[1][1]
                margin = ranked[0][1] - ranked[1][1]
            else:
                ru, ruv, margin = "", 0, ranked[0][1]

            races.append({"year": year, "election_type": etype, "office": office,
                          "district": district, "contest": contest,
                          "n_candidates": len(ranked), "total_votes": total,
                          "winner": winner, "winner_votes": wv, "winner_pct": wp,
                          "runner_up": ru, "runner_up_votes": ruv,
                          "margin_votes": margin, "margin_pct": pct(margin, total)})

    with open(os.path.join(HERE, "orem_races.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["year", "election_type", "office", "district",
            "contest", "n_candidates", "total_votes", "winner", "winner_votes", "winner_pct",
            "runner_up", "runner_up_votes", "margin_votes", "margin_pct"])
        w.writeheader(); w.writerows(races)

    with open(os.path.join(HERE, "orem_results_by_candidate.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["year", "election_type", "office", "district",
            "contest", "candidate", "votes", "pct", "rank", "is_winner"])
        w.writeheader(); w.writerows(by_cand)

    precinct_all.sort(key=lambda r: (r["year"], r["election_type"], r["contest"],
                                     r["precinct"], -r["votes"]))
    with open(os.path.join(HERE, "orem_results_by_precinct.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["year", "election_type", "office", "district",
            "contest", "precinct", "candidate", "votes"])
        w.writeheader()
        for r in precinct_all:
            w.writerow({k: r[k] for k in w.fieldnames})

    return races, by_cand


if __name__ == "__main__":
    cw, pr = build()
    races, by_cand = write_outputs(cw, pr)
    print(f"races={len(races)} candidates={len(by_cand)} precinct_rows={len(pr)}")
    yrs = {}
    for r in races:
        yrs.setdefault(r["year"], 0); yrs[r["year"]] += 1
    print("by year:", dict(sorted(yrs.items())))
    for r in races:
        print(f"  {r['year']} {r['election_type']:17} {r['contest']:18} "
              f"win={r['winner']} ({r['winner_votes']}) ru={r['runner_up']} "
              f"margin={r['margin_votes']}")
