#!/usr/bin/env python3
"""Parse Kearns council/mayor contests directly from the raw SLCo SOVC workbooks
(the canonical long CSV mislabels/merges Kearns for the SheetNN years and drops 2019).
Emits the three election_results CSVs + a 2025 precinct->district map for geo."""
import openpyxl, re, csv, os, sys

RAW = os.path.expanduser("~/Desktop/slco-election-archive/raw")
SCR = os.path.dirname(os.path.abspath(__file__))

def cells(path, sheet):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[sheet]
    rows = [[c for c in r] for r in ws.iter_rows(values_only=True)]
    wb.close()
    return rows

def s(v):
    return "" if v is None else str(v).replace("\n", " ").strip()

def g(r, i):
    return r[i] if i < len(r) else None

def num(v):
    v = s(v)
    if v in ("", "****"):
        return None
    v = v.replace(",", "").replace("%", "")
    try:
        return int(round(float(v)))
    except ValueError:
        return None

def clean_name(nm):
    nm = s(nm)
    nm = re.sub(r"\s*Qualified Write In\s*$", "", nm, flags=re.I)
    nm = re.sub(r"\s*\((?:NON|NP|N/P)\s*\)\s*$", "", nm, flags=re.I).strip()
    if re.search(r"write[- ]?in", nm, re.I):
        return "Write-in"
    return nm

# collector: list of dicts precinct-level {year,etype,office,district,contest_verbatim,precinct,candidate,votes,suppressed}
PREC = []
CONTEST_META = {}  # (year,etype,office,district) -> {verbatim, reg, ballots, suppressed}

def add(year, etype, office, district, verbatim, precinct, candidate, votes, suppressed=False):
    PREC.append(dict(year=year, etype=etype, office=office, district=str(district),
                     contest=verbatim, precinct=precinct, candidate=candidate,
                     votes=votes, suppressed=suppressed))

# ---------- FORMAT A : 2016, 2017 (Type-rows; use Type=='Total') ----------
def parse_fmtA(path, sheet, year, office, district):
    rows = cells(path, sheet)
    # header row: contains 'Precinct' and 'Type'
    hi = next(i for i, r in enumerate(rows) if "Precinct" in [s(c) for c in r] and "Type" in [s(c) for c in r])
    hdr = [s(c) for c in rows[hi]]
    pcol = hdr.index("Precinct"); tcol = hdr.index("Type")
    rcol = hdr.index("Reg. Voters"); tvcol = hdr.index("Total Votes")
    verbatim = next(s(c) for r in rows[:hi] for c in r if "KEARNS" in s(c).upper())
    cand_cols = {}
    for ci in range(tvcol + 1, len(hdr)):
        h = hdr[ci]
        if h and h != "Total Votes":
            cand_cols[ci] = clean_name(h)
    supp = False
    reg_tot = bal_tot = None
    for r in rows[hi + 1:]:
        prec = s(g(r,pcol)); typ = s(g(r,tcol))
        if typ != "Total":
            continue
        if prec.upper().startswith("ELECTION TOTAL") or prec.upper() == "CUMULATIVE":
            reg_tot = num(g(r,rcol)); bal_tot = num(g(r,hdr.index("Cards Cast")))
            continue
        if not re.match(r"KRN", prec, re.I):
            continue
        for ci, nm in cand_cols.items():
            v = num(r[ci]) if ci < len(r) else None
            if v is None:
                supp = True; v_store = None
            else:
                v_store = v
            add(year, "municipal general", office, district, verbatim, prec, nm, v_store, v_store is None)
    CONTEST_META[(year, "municipal general", office, str(district))] = dict(
        verbatim=verbatim, reg=reg_tot, ballots=bal_tot, suppressed=supp)

# ---------- FORMAT B : 2019 (candidate groups of 4; total at name_col+3) ----------
def parse_fmtB(path, sheet, year, office, district):
    rows = cells(path, sheet)
    verbatim = s(rows[0][0]) or next(s(c) for c in rows[0] if s(c))
    namerow = rows[1]; subhdr = [s(c) for c in rows[2]]
    cand = {}  # total_col -> name
    for ci, c in enumerate(namerow):
        nm = s(c)
        if nm:
            tc = ci + 3
            if tc < len(subhdr) and subhdr[tc] == "Total Votes":
                cand[tc] = clean_name(nm)
    pcol = 0; rcol = 1
    reg_tot = None
    for r in rows[3:]:
        prec = s(g(r,pcol))
        if prec.lower().startswith("total"):
            reg_tot = num(g(r,rcol)); continue
        if not re.match(r"KRN", prec, re.I):
            continue
        for tc, nm in cand.items():
            v = num(r[tc]) if tc < len(r) else None
            add(year, "municipal general", office, district, verbatim, prec, nm, v, v is None)
    CONTEST_META[(year, "municipal general", office, str(district))] = dict(
        verbatim=verbatim, reg=reg_tot, ballots=None, suppressed=False)

# ---------- FORMAT C : 2021, 2023, 2025 (Clarity page-per-contest) ----------
def parse_fmtC(path, sheet, year, office, district, etype="municipal general"):
    rows = cells(path, sheet)
    # title row
    ti = next(i for i, r in enumerate(rows) if any("(Vote for" in s(c) for c in r))
    title = next(s(c) for c in rows[ti] if "(Vote for" in s(c))
    verbatim = re.sub(r"\s*\(Vote for.*$", "", title).strip()
    # header row: first row whose first cell == 'Precinct'
    hi = next(i for i, r in enumerate(rows) if s(g(r,0)) == "Precinct")
    hdr = [s(c) for c in rows[hi]]
    p_idxs = [i for i, h in enumerate(hdr) if h == "Precinct"]
    p2 = p_idxs[1]
    tc_idx = hdr.index("Times Cast") if "Times Cast" in hdr else None
    rv_idx = hdr.index("Registered  Voters") if "Registered  Voters" in hdr else (
        hdr.index("Registered Voters") if "Registered Voters" in hdr else None)
    skip = {"Total Votes", "Undervotes", "Overvotes", "Registered Voters",
            "Registered  Voters", "Times Cast", "Precinct", ""}
    cand_cols = {}
    for ci in range(p2 + 1, len(hdr)):
        h = hdr[ci]
        if h and h not in skip:
            cand_cols[ci] = clean_name(h)
    supp = False
    reg_tot = bal_tot = None
    cur = None
    for r in rows[hi + 1:]:
        lab = s(g(r,0))
        if lab.startswith("Electionwide - Total"):
            reg_tot = num(g(r,rv_idx)) if rv_idx is not None else None
            bal_tot = num(g(r,tc_idx)) if tc_idx is not None else None
            cur = None; continue
        if lab.startswith(("Cumulative", "County - Total")):
            cur = None; continue
        m = re.match(r"KRN\d+", lab)
        if m:
            has_vals = any(s(g(r,ci)) not in ("", None) for ci in cand_cols)
            if has_vals:  # 2025: precinct row carries totals directly
                _emit_prec(r, lab, cand_cols, year, etype, office, district, verbatim)
                if any(num(g(r,ci)) is None for ci in cand_cols):
                    supp = True
            else:  # 2021/2023 group header
                cur = lab
            continue
        if lab == "Total" and cur:
            _emit_prec(r, cur, cand_cols, year, etype, office, district, verbatim)
            if any(num(g(r,ci)) is None for ci in cand_cols):
                supp = True
            cur = None
    CONTEST_META[(year, etype, office, str(district))] = dict(
        verbatim=verbatim, reg=reg_tot, ballots=bal_tot, suppressed=supp)

def _emit_prec(r, prec, cand_cols, year, etype, office, district, verbatim):
    for ci, nm in cand_cols.items():
        v = num(r[ci]) if ci < len(r) else None
        add(year, etype, office, district, verbatim, prec, nm, v, v is None)

# ================= RUN =================
import zipfile, tempfile
Z = tempfile.mkdtemp(prefix="kearns_sovc_")
HIST = os.path.join(RAW, "historical-election-results")
zipfile.ZipFile(os.path.join(HIST, "2016-11-08-general-election-statement-of-votes-cast.zip")).extractall(os.path.join(Z, "z2016"))
zipfile.ZipFile(os.path.join(HIST, "2017-11-07-general-election-statement-of-votes-cast.zip")).extractall(os.path.join(Z, "z2017"))
f2016 = os.path.join(Z, "z2016/SLCo_16G_SOVC_112816.xlsx")
f2017 = os.path.join(Z, "z2017/SOVC_171121_070327.xlsx")
f2019 = os.path.join(RAW, "historical-election-results/2019-11-05-general-election-sovc.xlsx")
f2021 = os.path.join(RAW, "2021/november-2-2021-general-election-statement-of-votes-cast.xlsx")
f2023 = os.path.join(RAW, "2023/statementofvotescastrpt-official-report-12-05-2023-5.22pm.xlsx")
f2025 = os.path.join(RAW, "2025-general-election-statementofvotescastrpt.xlsx")

# 2016 founding council: seats 1-5
for d in (1, 2, 3, 4, 5):
    parse_fmtA(f2016, f"KEARNS METRO TOWNSHIP CNCL #{d}", 2016, "Council", d)
# 2017 seats 2,4
parse_fmtA(f2017, "KEARNS METRO TOWNSHIP CNCL 2", 2017, "Council", 2)
parse_fmtA(f2017, "KEARNS METRO TOWNSHIP CNCL 4", 2017, "Council", 4)
# 2019 districts 1,3,5
parse_fmtB(f2019, "KRN Council 1", 2019, "Council", 1)
parse_fmtB(f2019, "KRN Council 3", 2019, "Council", 3)
parse_fmtB(f2019, "KRN Council 5", 2019, "Council", 5)
# 2021 districts 2,4
parse_fmtC(f2021, "Sheet57", 2021, "Council", 2)
parse_fmtC(f2021, "Sheet58", 2021, "Council", 4)
# 2023 districts 1,3,5
parse_fmtC(f2023, "Sheet16", 2023, "Council", 1)
parse_fmtC(f2023, "Sheet17", 2023, "Council", 3)
parse_fmtC(f2023, "Sheet18", 2023, "Council", 5)
# 2025 city: mayor + D2 + D4
parse_fmtC(f2025, "Sheet20", 2025, "Mayor", "")
parse_fmtC(f2025, "Sheet21", 2025, "Council", 2)
parse_fmtC(f2025, "Sheet22", 2025, "Council", 4)


# ================= EMIT =================
#!/usr/bin/env python3
from collections import defaultdict
META = CONTEST_META
OUT = os.path.dirname(os.path.abspath(__file__))

SRCFILE = {
    2016: "2016-11-08-general-election-statement-of-votes-cast.zip (SLCo_16G_SOVC_112816.xlsx)",
    2017: "2017-11-07-general-election-statement-of-votes-cast.zip (SOVC_171121_070327.xlsx)",
    2019: "2019-11-05-general-election-sovc.xlsx",
    2021: "november-2-2021-general-election-statement-of-votes-cast.xlsx",
    2023: "statementofvotescastrpt-official-report-12-05-2023-5.22pm.xlsx",
    2025: "2025-general-election-statementofvotescastrpt.xlsx",
}

def contest_norm(year, office, district):
    if office == "Mayor":
        return "Kearns City Mayor"
    if year >= 2025:
        return f"Kearns City Council District {district}"
    if year <= 2017:
        return f"Kearns Metro Township Council Seat {district}"
    return f"Kearns Metro Township Council District {district}"

# aggregate votes per (year,etype,office,district,candidate)
agg = defaultdict(lambda: {"votes": 0, "any": False})
precrows = defaultdict(dict)  # (key, precinct, candidate) -> votes
contests = set()
for p in PREC:
    key = (p["year"], p["etype"], p["office"], p["district"])
    contests.add(key)
    a = agg[(key, p["candidate"])]
    if p["votes"] is not None:
        a["votes"] += p["votes"]; a["any"] = True

# drop generic Write-in with 0 total
writein_total = defaultdict(int)
for (key, cand), a in agg.items():
    if cand == "Write-in":
        writein_total[key] += a["votes"]

def candidates_for(key):
    out = []
    for (k, cand), a in agg.items():
        if k != key:
            continue
        if cand == "Write-in" and writein_total[key] == 0:
            continue
        out.append((cand, a["votes"]))
    return out

# ---- races.csv ----
race_rows = []
bycand_rows = []
byprec_rows = []
for key in sorted(contests):
    year, etype, office, district = key
    cands = candidates_for(key)
    total = sum(v for _, v in cands)
    named = [(c, v) for c, v in cands if c != "Write-in"]
    winner, winner_votes = max(named, key=lambda cv: cv[1])
    others = sorted([cv for cv in cands if cv[0] != winner], key=lambda cv: cv[1], reverse=True)
    runner_up, runner_votes = (others[0] if others else ("", 0))
    n_cand = len(cands)
    has_writein = writein_total[key] > 0
    uncontested = (len(named) == 1 and not has_writein)
    margin_votes = winner_votes - runner_votes
    margin_pct = round(margin_votes / total * 100, 2) if total else ""
    winner_pct = round(winner_votes / total * 100, 2) if total else ""
    m = META[key]
    reg = m["reg"]; bal = m["ballots"]
    turnout = round(bal / reg * 100, 2) if (bal and reg) else ""
    cnorm = contest_norm(year, office, district)
    note = ""
    if has_writein and runner_up == "Write-in" and runner_votes > winner_votes:
        note = ("aggregate write-in votes exceeded the lone named candidate; the named "
                "candidate is certified the winner (scattered write-ins are not a single person)")
    race_rows.append({
        "year": year, "election_type": etype, "office": office,
        "district": district, "contest": cnorm, "contest_verbatim": m["verbatim"],
        "n_seats": 1, "n_candidates": n_cand, "voting_method": "plurality",
        "total_votes": total, "total_first_choice_votes": "",
        "winner": winner, "winner_votes": winner_votes, "winner_pct": winner_pct,
        "runner_up": runner_up, "runner_up_votes": runner_votes,
        "margin_votes": margin_votes, "margin_pct": margin_pct,
        "registered_voters": reg if reg is not None else "",
        "ballots_cast": bal if bal is not None else "",
        "turnout_pct": turnout,
        "uncontested": uncontested, "suppressed_precincts": m["suppressed"],
        "note": note, "source_file": SRCFILE[year],
    })
    # by_candidate rows (rank by votes desc)
    ranked = sorted(cands, key=lambda cv: cv[1], reverse=True)
    for rank, (cand, v) in enumerate(ranked, 1):
        bycand_rows.append({
            "year": year, "election_type": etype, "office": office,
            "district": district, "contest": cnorm, "candidate": cand,
            "votes": v, "pct": round(v / total * 100, 2) if total else "",
            "rank": rank, "is_winner": (cand == winner),
        })

# by_precinct rows
for p in PREC:
    key = (p["year"], p["etype"], p["office"], p["district"])
    if p["candidate"] == "Write-in" and writein_total[key] == 0:
        continue
    cnorm = contest_norm(p["year"], p["office"], p["district"])
    byprec_rows.append({
        "year": p["year"], "election_type": p["etype"], "office": p["office"],
        "district": p["district"], "contest": cnorm, "precinct": p["precinct"],
        "candidate": p["candidate"],
        "votes": p["votes"] if p["votes"] is not None else "",
        "suppressed": p["suppressed"],
    })

RACE_COLS = ["year", "election_type", "office", "district", "contest", "contest_verbatim",
             "n_seats", "n_candidates", "voting_method", "total_votes", "total_first_choice_votes",
             "winner", "winner_votes", "winner_pct", "runner_up", "runner_up_votes",
             "margin_votes", "margin_pct", "registered_voters", "ballots_cast", "turnout_pct",
             "uncontested", "suppressed_precincts", "note", "source_file"]
BYCAND_COLS = ["year", "election_type", "office", "district", "contest", "candidate",
               "votes", "pct", "rank", "is_winner"]
BYPREC_COLS = ["year", "election_type", "office", "district", "contest", "precinct",
               "candidate", "votes", "suppressed"]

race_rows.sort(key=lambda r: (r["year"], r["office"] != "Mayor", str(r["district"])))
bycand_rows.sort(key=lambda r: (r["year"], r["office"] != "Mayor", str(r["district"]), -r["votes"]))
byprec_rows.sort(key=lambda r: (r["year"], r["office"] != "Mayor", str(r["district"]), r["precinct"], r["candidate"]))

def write(fn, cols, rows):
    with open(os.path.join(OUT, fn), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader(); w.writerows(rows)

write("kearns_races.csv", RACE_COLS, race_rows)
write("kearns_results_by_candidate.csv", BYCAND_COLS, bycand_rows)
write("kearns_results_by_precinct.csv", BYPREC_COLS, byprec_rows)
print(f"races={len(race_rows)} bycand={len(bycand_rows)} byprec={len(byprec_rows)}")
years = sorted({r["year"] for r in race_rows})
print("years:", years)
for r in race_rows:
    print(f"  {r['year']} {r['office']:7s} D{r['district'] or '-'}: {r['winner']} ({r['winner_votes']}) "
          f"def {r['runner_up'] or '(uncontested)'} ({r['runner_up_votes']}) "
          f"marg={r['margin_votes']} unc={r['uncontested']} supp={r['suppressed_precincts']}"
          + (f"  NOTE:{r['note'][:40]}" if r['note'] else ""))
