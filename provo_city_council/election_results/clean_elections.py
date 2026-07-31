#!/usr/bin/env python3
"""
Build Provo's tidy election_results from Utah County raw sources.

Provo Municipal Council = 5 districts + 2 citywide seats + Mayor, odd-year staggered.
Cycles covered: 2019, 2021, 2023, 2025.

Sources (in raw/):
  - 2021 & 2025 SOVC CSVs (wide crosstab) -> precinct-level + citywide  (PRIMARY + GENERAL)
  - 2019 & 2023 born-digital rollup PDFs   -> citywide ONLY (no precinct SOVC CSV published)

Outputs:
  provo_races.csv               one row per race (winner/runner-up/margin/turnout)
  provo_results_by_candidate.csv race x candidate (votes, pct, rank, is_winner)
  provo_results_by_precinct.csv  precinct x candidate (2021/2025 CSV cycles only)

Re-run: python3 clean_elections.py
"""
import csv, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")

# Pseudo-candidate header labels that are NOT real candidates -> drop.
NON_CANDIDATE = {"OVER VOTES", "UNDER VOTES", "VOTERS", "BALLOTS CAST",
                 "TOTAL VOTES CAST", "TOTAL", "FOR", "AGAINST", ""}

# ---- contest normalization -------------------------------------------------
def normalize_contest(raw):
    """Map a raw Provo contest header to (office, district, canonical_contest)
    or None if it is not a Provo Mayor/Council race we keep."""
    s = raw.strip()
    low = s.lower()
    if "provo" not in low:
        return None
    if "proposition" in low or "rap tax" in low or "parc" in low:
        return None  # ballot measures excluded; council+mayor only
    if "mayor" in low:
        return ("Mayor", "", "Provo City Mayor")
    if "council" not in low:
        return None
    # at-large / citywide seats
    if "city wide" in low or "citywide" in low or "at-large" in low or "at large" in low:
        # roman/arabic: I/1 and II/2
        if "ii" in low.replace("city wide", "").replace("citywide", "") or " 2" in low or "wide 2" in low:
            return ("Council", "Citywide II", "Provo City Council Citywide II")
        return ("Council", "Citywide I", "Provo City Council Citywide I")
    # district seats
    for n in ("1", "2", "3", "4", "5"):
        if f"district {n}" in low:
            return ("Council", n, f"Provo City Council District {n}")
    return None


# ---- wide-crosstab SOVC CSV parser ----------------------------------------
def parse_sovc_csv(path, header_rows, precinct_col, precinct_prefix):
    """Unpivot a Utah County wide-crosstab SOVC CSV.

    header_rows: number of header rows. Row 0 = contest names (spanning columns).
                 The LAST header row = candidate names. (Middle rows = party, ignored.)
    Returns (citywide_totals, precinct_rows) where:
      citywide_totals: {canonical_contest: {"office","district","cands":{name:votes}}}
      precinct_rows:   list of dicts {office,district,contest,precinct,candidate,votes}
    """
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    contest_row = rows[0]
    cand_row = rows[header_rows - 1]

    # column -> (office, district, contest) for Provo columns only
    colmap = {}
    for i, craw in enumerate(contest_row):
        norm = normalize_contest(craw)
        if not norm:
            continue
        cand = cand_row[i].strip().rstrip(":")  # "WRITE-IN:" -> "WRITE-IN"
        if cand.upper() in NON_CANDIDATE:
            continue
        office, district, contest = norm
        colmap[i] = (office, district, contest, cand)

    citywide = {}
    precinct_rows = []
    for r in rows[header_rows:]:
        if precinct_col >= len(r):
            continue
        pname = r[precinct_col].strip()
        # keep only Provo precinct rows (PR..). Skip totals / vote-center rollups.
        idx = pname.upper().find(precinct_prefix)
        if idx == -1:
            continue
        precinct = pname[idx:]  # e.g. 25PR01 -> PR01 below
        if precinct.upper().startswith("25"):
            precinct = precinct[2:]
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
# 2019 general + 2023 general have NO SOVC CSV; values verified from the
# Utah County OFFICIAL results PDFs (raw/2019_General_Results_PDF... ,
# raw/2023_General_voting_results...). Primaries 2019 & 2023 likewise PDF-only.
PDF_CITYWIDE = {
    # (year, election_type) -> {contest: {office,district,cands:{name:votes}}}
    (2019, "municipal general"): {
        "Provo City Council Citywide II": {"office": "Council", "district": "Citywide II",
            "cands": {"DAVID SHIPLEY": 8235, "JANAE MOSS": 6586}},
        "Provo City Council District 1": {"office": "Council", "district": "1",
            "cands": {"BILL FILLMORE": 3890}},
        "Provo City Council District 3": {"office": "Council", "district": "3",
            "cands": {"SHANNON ELLSWORTH": 1697, "ROBIN ROBERTS": 923}},
        "Provo City Council District 4": {"office": "Council", "district": "4",
            "cands": {"TRAVIS HOBAN": 2625, "VALERIE PAXMAN": 2053}},
    },
    (2019, "municipal primary"): {
        "Provo City Council District 3": {"office": "Council", "district": "3",
            "cands": {"SHANNON ELLSWORTH": 862, "ROBIN ROBERTS": 460, "JEFF HANDY": 291}},
        "Provo City Council District 4": {"office": "Council", "district": "4",
            "cands": {"TRAVIS HOBAN": 1085, "VALERIE PAXMAN": 894,
                      "BETH ALLIGOOD": 630, "ERIC LUDWIG": 161}},
    },
    (2023, "municipal general"): {
        "Provo City Council Citywide II": {"office": "Council", "district": "Citywide II",
            "cands": {"GARY GARRETT": 5801, "MCKAY R. JENSEN": 5435}},
        "Provo City Council District 1": {"office": "Council", "district": "1",
            "cands": {"CRAIG CHRISTENSEN": 2315, "STAN JENSEN": 1532}},
        "Provo City Council District 3": {"office": "Council", "district": "3",
            "cands": {"BECKY BOGDIN": 1409, "DAVID LEWIS": 894}},
        "Provo City Council District 4": {"office": "Council", "district": "4",
            "cands": {"TRAVIS HOBAN": 1625}},
    },
    (2023, "municipal primary"): {
        "Provo City Council Citywide II": {"office": "Council", "district": "Citywide II",
            "cands": {"GARY GARRETT": 3360, "MCKAY R. JENSEN": 2265, "TANNER BENNETT": 1496,
                      "WENDY AHLMAN": 1076, "JOSEPH PENROSE": 389, "NATHAN SMITH JONES": 146}},
    },
}


# ---- assemble all cycles ---------------------------------------------------
def build():
    citywide_all = {}   # (year, etype) -> {contest: {office,district,cands}}
    precinct_all = []   # rows with year, etype added

    # CSV cycles
    csv_specs = [
        (2021, "municipal primary", "21_PP_2021_Primary_Statement_of_Votes_Cast_SUPPRESSED_bd47a35ddf.csv", 3, 2, "PR"),
        (2021, "municipal general", "21_G_Countywide_SOVC_suppressed_1b85ad469d.csv", 2, 0, "PR"),
        (2025, "municipal primary", "2025_Primary_SOVC_suppressed_4bc086dabf.csv", 3, 2, "PR"),
        (2025, "municipal general", "SOVC_Simple_Redacted_7a5eddcaf2.csv", 3, 2, "PR"),
    ]
    for year, etype, fname, hdr, pcol, pref in csv_specs:
        cw, pr = parse_sovc_csv(os.path.join(RAW, fname), hdr, pcol, pref)
        citywide_all[(year, etype)] = cw
        for row in pr:
            row = dict(row, year=year, election_type=etype)
            precinct_all.append(row)

    # PDF-only cycles
    for key, data in PDF_CITYWIDE.items():
        citywide_all[key] = data

    return citywide_all, precinct_all


def pct(v, total):
    return round(100.0 * v / total, 2) if total else 0.0


def write_outputs(citywide_all, precinct_all):
    races = []          # provo_races rows
    by_cand = []        # provo_results_by_candidate rows

    for (year, etype) in sorted(citywide_all):
        for contest, d in sorted(citywide_all[(year, etype)].items(),
                                 key=lambda kv: (kv[1]["office"] != "Mayor", kv[1]["district"], kv[0])):
            office, district = d["office"], d["district"]
            cands = sorted(d["cands"].items(), key=lambda kv: -kv[1])
            total = sum(d["cands"].values())
            ranked = []
            for rank, (name, votes) in enumerate(cands, 1):
                p = pct(votes, total)
                is_win = (rank == 1)
                ranked.append((name, votes, p, rank, is_win))
                by_cand.append({"year": year, "election_type": etype, "office": office,
                                "district": district, "contest": contest, "candidate": name,
                                "votes": votes, "pct": p, "rank": rank, "is_winner": is_win})
            winner, wv, wp = ranked[0][0], ranked[0][1], ranked[0][2]
            if len(ranked) > 1:
                ru, ruv = ranked[1][0], ranked[1][1]
            else:
                ru, ruv = "", 0
            margin = wv - ruv
            races.append({"year": year, "election_type": etype, "office": office,
                          "district": district, "contest": contest,
                          "n_candidates": len(ranked), "total_votes": total,
                          "winner": winner, "winner_votes": wv, "winner_pct": wp,
                          "runner_up": ru, "runner_up_votes": ruv,
                          "margin_votes": margin, "margin_pct": pct(margin, total)})

    # races.csv
    with open(os.path.join(HERE, "provo_races.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["year", "election_type", "office", "district",
            "contest", "n_candidates", "total_votes", "winner", "winner_votes", "winner_pct",
            "runner_up", "runner_up_votes", "margin_votes", "margin_pct"])
        w.writeheader()
        w.writerows(races)

    # by_candidate.csv
    with open(os.path.join(HERE, "provo_results_by_candidate.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["year", "election_type", "office", "district",
            "contest", "candidate", "votes", "pct", "rank", "is_winner"])
        w.writeheader()
        w.writerows(by_cand)

    # by_precinct.csv  (2021/2025 only)
    precinct_all.sort(key=lambda r: (r["year"], r["election_type"], r["district"],
                                     r["contest"], r["precinct"], -r["votes"]))
    with open(os.path.join(HERE, "provo_results_by_precinct.csv"), "w", newline="") as f:
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
        yrs.setdefault(r["year"], 0)
        yrs[r["year"]] += 1
    print("by year:", yrs)
