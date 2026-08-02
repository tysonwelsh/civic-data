"""normalize_sovc_county.py — EVEN-YEAR Salt Lake County SOVC workbooks → the
canonical county-office tidy long file.

Input:  raw/<year>/…            (verbatim mirror; catalogue + sha256 in sources.csv)
Output: slco_county_results_long.csv
        one row per precinct × candidate × vote-method, VERBATIM:
        year, election_date, election_type, source_file, sheet, family, contest,
        vote_for, precinct, candidate, votes, suppressed, vote_method,
        times_cast, registered_voters
        (the first 13 names/order match slco_municipal_results_long.csv, with
        election_date + family inserted, so the two long files stay comparable.)

SCOPE. Even years only — the county-office election years (Mayor, the 9 Council
seats, Sheriff, District Attorney, Clerk, Assessor, Recorder, Treasurer, Auditor,
Surveyor). The ODD-year municipal canvass is a separate canonical layer
(slco_municipal_results_long.csv) and is NOT touched by this script. EVERY contest
the workbook prints is parsed and kept (verbatim discipline — federal, state,
judicial, school and district races included); the county offices are selected
downstream by build_county_elections.py's contest classifier.

PARSER FAMILIES. Families A / B / C / D are PORTED (not imported) from the proven
upstream normalizer at ~/Desktop/slco-election-archive/scripts/normalize_sovc.py,
including its 2026-07-19 fixes (METHOD_LABELS pseudo-candidate rejection, family-C
suppressed-precinct Total recovery, verbatim 'Cumulative' rollup labelling). This
module must never depend on that Desktop path. Families E and G are NEW here — the
two even-year-only layouts the upstream parser never handled:

  G  2002 / 2004 "canvass" (.xls, ONE sheet, never parsed upstream): a legend of
     `[NNNN] <label> <certified total> <pct>` rows under contest-title rows, then
     repeated `Precinct [NNNN] [NNNN] …` column blocks of precinct rows. The
     legend total IS the county's certified total → the reconciliation gate.
  E  2006 (.xls, one named sheet per contest, two-row header): row1 PRECINCT |
     TURN OUT | VOTE TOTALS, row2 Registered Voters | Total Ballots Cast |
     % Turnout | Total Votes for Race | <candidates…>; a bare precinct-id row is
     followed by its Polling/Early/Absentee/Provisional/Total method sub-rows.
     A trailing block whose id row is 'Total' carries the certified totals.
  A  2008–2016 + the 2018 PRIMARY + the 2016 recount ("TOC" era, named sheets):
     Precinct | Type | Reg./Aff. Voters | [Cards Cast] | Total Votes | <cands…>,
     each candidate followed by a % column. Certified totals = the trailing
     'Election Total' rows (Type='Total').
  D  2018 GENERAL + the three 2020 workbooks (numbered sheets + Table of
     Contents; 2020 is SpreadsheetML XML wearing an .xls extension — read by the
     local SpreadsheetML reader, then parsed by the same family D). Certified
     totals = the trailing 'Total:' row.
  C  2022 / 2024 / 2026 (paginated 'SheetN' export): Precinct | Times Cast |
     Registered Voters | Precinct(repeat) | <cands…>; 2022 carries per-precinct
     vote-method sub-rows, 2024/2026 do not. Certified totals = the trailing
     'County - Total' / 'Countywide - Total' row (never 'Cumulative - Total').

RECONCILIATION GATE (hard, washington_county/normalize_canvass.py precedent).
For EVERY parsed sheet and EVERY candidate column, the sum of the emitted
precinct rows must equal the workbook's OWN certified-total row exactly. A
shortfall is accepted ONLY where the workbook printed '****' privacy suppression
for that candidate (status 'suppressed-deficit', the deficit recorded). Anything
else is a MISMATCH: a parser bug to fix, or a source-internal contradiction to
keep verbatim, allowlist in KNOWN_SOURCE_DISCREPANCIES and document. The run
prints a per-file gate report and writes reconciliation_county.csv.

DERIVED + idempotent. Never hand-edit the output; rerun this.

Usage:  python3 salt_lake_county/elections/normalize_sovc_county.py [--only YEAR]
"""
from __future__ import annotations

import csv
import io
import os
import re
import sys
import warnings
import zipfile
from collections import defaultdict

import pandas as pd

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from county_contest_map import classify           # noqa: E402

RAW = os.path.join(HERE, "raw")
SOURCES = os.path.join(HERE, "sources.csv")
OUT = os.path.join(HERE, "slco_county_results_long.csv")
RECON = os.path.join(HERE, "reconciliation_county.csv")
INVENTORY = os.path.join(HERE, "contest_inventory.csv")
# The all-contests parse (federal/state/judicial/school/municipal included) is
# ~3.0M rows / 416 MB — an order of magnitude over GitHub's 100 MB hard limit,
# so it is written under raw/ (gitignored repo-wide) and only with --full. The
# COMMITTED canonical is the Salt Lake County-level scope this module is for;
# contest_inventory.csv catalogues EVERY contest either way, so nothing is
# silently dropped, and `--full` reproduces the rest from the retained raws.
FULL_OUT = os.path.join(RAW, "slco_evenyear_all_contests_long.csv")

# ---------------------------------------------------------------- ported helpers
LABELS = {"precinct", "times cast", "registered voters", "registered\nvoters",
          "registered \nvoters", "total votes", "voters cast", "% turnout",
          "undervotes", "overvotes",
          # even-year header vocabulary (families A/E)
          "type", "reg. voters", "aff. voters", "cards cast", "turn out",
          "vote totals", "total ballots cast", "total votes for race",
          "voter turnout", "ballots cast", "% of votes", "reg voters"}
PRECINCT_RE = re.compile(r"^(?:\d{1,2})?[A-Za-z]{2,5}\d{2,4}[A-Za-z]?$")
SUPPRESSED = {"****", "*****", "n/a"}
METHOD_LABELS = {"cumulative", "total", "vote centers", "vote center", "vote by mail",
                 "vbm", "mail", "early voting", "early", "in person", "in-person",
                 "election day", "absentee", "provisional", "polling", "polls",
                 "in-office", "in office", "in-office voting", "ab", "ab-vbm",
                 "total:"}


def norm(s) -> str:
    if s is None:
        return ""
    try:
        if pd.isna(s):
            return ""
    except (TypeError, ValueError):
        pass
    return re.sub(r"\s+", " ", str(s)).strip()


def is_pseudo_candidate(name: str) -> bool:
    """True when a would-be candidate header cell is a vote-method/section label."""
    return norm(name).lower() in METHOD_LABELS


def is_subtotal(precinct: str) -> bool:
    """True for non-precinct rows: blanks, county headers, and any
    '... - Total' / 'Cumulative' subtotal/grand-total row."""
    pl = precinct.strip().lower()
    if pl in ("", "nan"):
        return True
    if "total" in pl or "cumulative" in pl:
        return True
    return pl in ("county", "electionwide", "countywide") or pl.startswith("salt lake county")


def clean_contest(name: str) -> str:
    name = re.sub(r"\s*\(vote for.*?\)\s*", " ", name, flags=re.I)
    name = re.split(r"\*{2,}", name)[0]
    return re.sub(r"\s+", " ", name).strip(" -")


def parse_votes(raw):
    s = norm(raw)
    if s.lower() in SUPPRESSED:
        return None, True
    if s == "" or s.lower() == "nan":
        return None, False
    s = s.replace(",", "")
    try:
        return int(float(s)), False
    except ValueError:
        return None, False


def vote_for_of(title):
    m = re.search(r"\(vote for\s*=?\s*(\d+)\)", title, re.I)
    return int(m.group(1)) if m else None


# ------------------------------------------------------------------- readers
def read_spreadsheetml(path):
    """SpreadsheetML 2003 XML (the 2020 workbooks wear an .xls extension).
    Returns [(sheet_name, DataFrame)]. MergeAcross is expanded to blanks after
    the first cell, matching how openpyxl/xlrd surface merged ranges — family D
    depends on a merged candidate label appearing exactly once."""
    import xml.etree.ElementTree as ET
    tree = ET.parse(path)
    ns = {"ss": "urn:schemas-microsoft-com:office:spreadsheet"}
    out = []
    for ws in tree.getroot().findall(".//ss:Worksheet", ns):
        name = ws.get("{urn:schemas-microsoft-com:office:spreadsheet}Name") or ""
        rows = []
        for row in ws.findall("./ss:Table/ss:Row", ns):
            vals = []
            for cell in row.findall("./ss:Cell", ns):
                idx = cell.get("{urn:schemas-microsoft-com:office:spreadsheet}Index")
                if idx:                       # sparse row: pad to the 1-based index
                    while len(vals) < int(idx) - 1:
                        vals.append(None)
                data = cell.find("./ss:Data", ns)
                txt = None if data is None else (data.text or "")
                vals.append(txt if txt not in ("",) else None)
                span = cell.get("{urn:schemas-microsoft-com:office:spreadsheet}MergeAcross")
                if span:
                    vals.extend([None] * int(span))
            rows.append(vals)
        width = max((len(r) for r in rows), default=0)
        rows = [r + [None] * (width - len(r)) for r in rows]
        out.append((name, pd.DataFrame(rows)))
    return out


def read_workbook(path):
    """[(sheet_name, DataFrame)] for .xlsx / .xls (BIFF or SpreadsheetML) / .zip."""
    low = path.lower()
    if low.endswith(".zip"):
        with zipfile.ZipFile(path) as zf:
            names = [n for n in zf.namelist() if n.lower().endswith((".xlsx", ".xls"))]
            if not names:
                return []
            blob = zf.read(names[0])
        if names[0].lower().endswith(".xlsx"):
            xl = pd.ExcelFile(io.BytesIO(blob))
        else:
            xl = pd.ExcelFile(io.BytesIO(blob))
        return [(s, xl.parse(s, header=None)) for s in xl.sheet_names]
    if low.endswith(".xls"):
        with open(path, "rb") as f:
            head = f.read(400)
        if b"<?xml" in head or b"Workbook" in head and b"urn:schemas" in head:
            return read_spreadsheetml(path)
    xl = pd.ExcelFile(path)
    return [(s, xl.parse(s, header=None)) for s in xl.sheet_names]


# ------------------------------------------------- family C (2021+ paginated)
def parse_family_c(df):
    """PORTED from upstream parse_contest_sheet() — 'SheetN' paginated exports
    (2022/2024/2026 here). Includes the suppressed-precinct Total recovery and
    the verbatim 'Cumulative' rollup labelling."""
    header_row = None
    for r in range(min(15, len(df))):
        if norm(df.iat[r, 0]).lower() == "precinct":
            rowvals = {norm(v).lower() for v in df.iloc[r]}
            if "times cast" in rowvals:
                header_row = r
                break
    if header_row is None:
        return "", None, []
    title = ""
    for r in range(header_row - 1, -1, -1):
        val = norm(df.iat[r, 0])
        if val and not val.lower().startswith("page:") and val.lower() not in LABELS:
            title = val
            break
    vote_for = vote_for_of(title)
    contest = clean_contest(title)

    hdr = [norm(v).lower() for v in df.iloc[header_row]]
    repeat_cols = [c for c, v in enumerate(hdr) if v == "precinct"]
    repeat_col = repeat_cols[-1] if len(repeat_cols) >= 2 else 4
    cands = [(c, norm(df.iat[header_row, c])) for c in range(repeat_col + 1, df.shape[1])
             if norm(df.iat[header_row, c]) and norm(df.iat[header_row, c]).lower() not in LABELS
             and not is_pseudo_candidate(norm(df.iat[header_row, c]))]
    if not cands:
        return contest, vote_for, []

    records = []
    current = None
    pending = {}
    total_recovered = False
    for r in range(header_row + 1, len(df)):
        label = norm(df.iat[r, 0])
        if df.shape[1] > repeat_col and norm(df.iat[r, repeat_col]) != label:
            continue
        if is_subtotal(label):
            if label.lower() == "total" and current is not None and not total_recovered:
                times_cast, _ = parse_votes(df.iat[r, 1]) if df.shape[1] > 1 else (None, False)
                registered, _ = parse_votes(df.iat[r, 2]) if df.shape[1] > 2 else (None, False)
                for col, cand in cands:
                    flags = pending.get(cand)
                    if not flags or not all(flags):
                        continue
                    votes, _sup = parse_votes(df.iat[r, col])
                    if votes is None:
                        continue
                    records.append({"contest": contest, "vote_for": vote_for,
                                    "precinct": current, "candidate": cand,
                                    "votes": votes, "suppressed": False,
                                    "vote_method": "Total", "times_cast": times_cast,
                                    "registered_voters": registered})
                total_recovered = True
            elif "cumulative" in label.lower():
                current = "Cumulative"
                pending = {}
                total_recovered = True
            continue
        if PRECINCT_RE.match(label):
            current = label
            pending = {}
            total_recovered = False
            precinct, method = label, "ALL"
        elif current is not None:
            precinct, method = current, label
        else:
            continue
        times_cast, _ = parse_votes(df.iat[r, 1]) if df.shape[1] > 1 else (None, False)
        registered, _ = parse_votes(df.iat[r, 2]) if df.shape[1] > 2 else (None, False)
        for col, cand in cands:
            votes, suppressed = parse_votes(df.iat[r, col])
            if votes is None and not suppressed:
                continue
            pending.setdefault(cand, []).append(suppressed)
            records.append({"contest": contest, "vote_for": vote_for, "precinct": precinct,
                            "candidate": cand, "votes": votes, "suppressed": suppressed,
                            "vote_method": method, "times_cast": times_cast,
                            "registered_voters": registered})
    return contest, vote_for, records


# ------------------------------------------------ family B (2018-2019 named sheets)
def parse_family_b(df, sheet_name):
    """PORTED from upstream. Candidate names on the row ABOVE a 'Precinct'
    sub-header row, each spanning method sub-columns ending in 'Total Votes'."""
    hr = None
    for r in range(min(6, len(df))):
        if norm(df.iat[r, 0]).lower() == "precinct":
            hr = r
            break
    if hr is None or hr == 0:
        return []
    cand_cols = []
    for c in range(1, df.shape[1]):
        nm = norm(df.iat[hr - 1, c])
        if (nm and nm.lower() != "nan" and nm.lower() not in LABELS
                and not is_pseudo_candidate(nm)):
            cand_cols.append((c, nm))
    if not cand_cols:
        return []
    hdr = [norm(v).lower() for v in df.iloc[hr]]
    bounds = [c for c, _ in cand_cols] + [df.shape[1]]
    cols = []
    for i, (c, nm) in enumerate(cand_cols):
        tv = [j for j in range(c, bounds[i + 1]) if hdr[j] == "total votes"]
        if not tv:
            return []
        cols.append((tv[0], nm))
    reg_col = next((j for j, v in enumerate(hdr) if v.startswith("registered")), None)
    contest = clean_contest(re.sub(r"[*◄►]+", "", sheet_name))
    records = []
    for r in range(hr + 1, len(df)):
        precinct = norm(df.iat[r, 0])
        if is_subtotal(precinct):
            continue
        registered, _ = parse_votes(df.iat[r, reg_col]) if reg_col is not None else (None, False)
        for col, cand in cols:
            votes, suppressed = parse_votes(df.iat[r, col])
            if votes is None and not suppressed:
                continue
            records.append({"contest": contest, "vote_for": None, "precinct": precinct,
                            "candidate": cand, "votes": votes, "suppressed": suppressed,
                            "vote_method": "ALL", "times_cast": None,
                            "registered_voters": registered})
    return records


# ------------------------------- family A (2008-2016 TOC era + 2018 primary/recount)
def sheet_title(df, header_row, sheet_name):
    """The in-sheet contest title: the nearest non-navigation text above the
    header row (Excel truncates sheet NAMES at 31 chars, so the printed title is
    the faithful one). Falls back to the sheet name."""
    skip = {"table of contents", "◄ to toc", "to toc", "statement of votes cast",
            "official statement of votes cast"}
    for r in range(header_row - 1, -1, -1):
        for c in (1, 0):
            if c >= df.shape[1]:
                continue
            val = norm(df.iat[r, c])
            low = val.lower().strip("◄► ")
            if not val or low in skip or low in LABELS:
                continue
            if re.match(r"^\d{4}[- ]", val) or re.search(r"salt lake county", low):
                continue
            if re.match(r"^(january|february|march|april|may|june|july|august|"
                        r"september|october|november|december)\b", low):
                continue
            if re.match(r"^\d{4}\b.*(election|primary|general)", low):
                continue
            if re.match(r"^\w+ \d{1,2}(st|nd|rd|th)?,? \d{4}$", val, re.I):
                continue
            return val
    return re.sub(r"[*◄►]+", "", sheet_name).strip()


def parse_family_a(df, sheet_name):
    """PORTED from upstream, with the in-sheet title preferred over the sheet
    name. Header row carries 'Precinct' + 'Total Votes' (+ a 'Type' method
    column); candidates follow 'Total Votes', each trailed by a % column."""
    hr = pcol = None
    for r in range(min(15, len(df))):
        for c in range(df.shape[1]):
            if norm(df.iat[r, c]).lower() == "precinct":
                hr, pcol = r, c
                break
        if hr is not None:
            break
    if hr is None:
        return "", None, []
    rowvals = [norm(v).lower() for v in df.iloc[hr]]
    if "total votes" not in rowvals:
        return "", None, []
    totcol = rowvals.index("total votes")
    tcol = rowvals.index("type") if "type" in rowvals else None
    rcol = next((i for i, v in enumerate(rowvals)
                 if v.startswith("reg") or v.startswith("aff")), None)

    cands = []
    for c in range(totcol + 1, df.shape[1]):
        name = norm(df.iat[hr, c])
        if (name and name.lower() != "nan" and name.lower() not in LABELS
                and not is_pseudo_candidate(name)):
            cands.append((c, name))
    if not cands:
        return "", None, []

    title = sheet_title(df, hr, sheet_name)
    contest = clean_contest(re.sub(r"[*◄►]+", "", title))
    vote_for = vote_for_of(title)
    records = []
    for r in range(hr + 1, len(df)):
        precinct = norm(df.iat[r, pcol])
        if is_subtotal(precinct):
            continue
        method = norm(df.iat[r, tcol]) if tcol is not None else ""
        if method.lower() in ("total", "cumulative"):
            continue                      # per-precinct subtotal of its sibling rows
        registered, _ = parse_votes(df.iat[r, rcol]) if rcol is not None else (None, False)
        cards = None
        for col, cand in cands:
            votes, suppressed = parse_votes(df.iat[r, col])
            if votes is None and not suppressed:
                continue
            records.append({"contest": contest, "vote_for": vote_for, "precinct": precinct,
                            "candidate": cand, "votes": votes, "suppressed": suppressed,
                            "vote_method": method or None, "times_cast": cards,
                            "registered_voters": registered})
    return contest, vote_for, records


def gate_family_a(df):
    """Certified totals from the trailing 'Election Total' / Type='Total' row."""
    hr = None
    for r in range(min(15, len(df))):
        for c in range(df.shape[1]):
            if norm(df.iat[r, c]).lower() == "precinct":
                hr = r
                break
        if hr is not None:
            break
    if hr is None:
        return {}
    rowvals = [norm(v).lower() for v in df.iloc[hr]]
    if "total votes" not in rowvals:
        return {}
    totcol = rowvals.index("total votes")
    tcol = rowvals.index("type") if "type" in rowvals else None
    cands = [(c, norm(df.iat[hr, c])) for c in range(totcol + 1, df.shape[1])
             if norm(df.iat[hr, c]) and norm(df.iat[hr, c]).lower() not in LABELS
             and not is_pseudo_candidate(norm(df.iat[hr, c]))]
    for r in range(len(df) - 1, hr, -1):
        lab = norm(df.iat[r, 0]) or norm(df.iat[r, 1] if df.shape[1] > 1 else "")
        meth = norm(df.iat[r, tcol]) if tcol is not None else ""
        if lab.lower() == "election total" and meth.lower() == "total":
            out = {}
            for c, nm in cands:
                v, _ = parse_votes(df.iat[r, c])
                if v is not None:
                    out[nm] = v
            return out
    return {}


# ------------------------------------------------------- family D (2018G / 2020)
def parse_family_d(df):
    """PORTED from upstream. Numbered-sheet 'Table of Contents' era: title in A1,
    candidate names above a sub-header row whose col1 is 'Registered Voters'."""
    if df.shape[1] < 3:
        return "", None, []
    hr = None
    for r in range(1, min(6, len(df))):
        if norm(df.iat[r, 1]).lower() == "registered voters":
            rowvals = {norm(v).lower() for v in df.iloc[r]}
            if "total votes" in rowvals:
                hr = r
                break
    if hr is None or hr < 2:
        return "", None, []
    title = norm(df.iat[0, 0])
    if not title:
        return "", None, []
    cand_cols = []
    for c in range(2, df.shape[1]):
        nm = norm(df.iat[hr - 1, c])
        if (nm and nm.lower() != "nan" and nm.lower() not in LABELS
                and not is_pseudo_candidate(nm)):
            cand_cols.append((c, nm))
    if not cand_cols:
        return "", None, []
    hdr = [norm(v).lower() for v in df.iloc[hr]]
    bounds = [c for c, _ in cand_cols] + [df.shape[1]]
    cols = []
    for i, (c, nm) in enumerate(cand_cols):
        tv = [j for j in range(c, bounds[i + 1]) if hdr[j] == "total votes"]
        if not tv:
            return "", None, []
        cols.append((tv[0], nm))
    vote_for = vote_for_of(title)
    contest = clean_contest(title)
    records = []
    for r in range(hr + 1, len(df)):
        precinct = norm(df.iat[r, 0])
        if is_subtotal(precinct) or precinct.lower().rstrip(":") == "total":
            continue
        registered, _ = parse_votes(df.iat[r, 1])
        for col, cand in cols:
            votes, suppressed = parse_votes(df.iat[r, col])
            if votes is None and not suppressed:
                continue
            records.append({"contest": contest, "vote_for": vote_for, "precinct": precinct,
                            "candidate": cand, "votes": votes, "suppressed": suppressed,
                            "vote_method": "ALL", "times_cast": None,
                            "registered_voters": registered})
    return contest, vote_for, records


def gate_family_d(df):
    """Certified totals from the trailing 'Total:' row."""
    hr = None
    for r in range(1, min(6, len(df))):
        if norm(df.iat[r, 1]).lower() == "registered voters":
            if "total votes" in {norm(v).lower() for v in df.iloc[r]}:
                hr = r
                break
    if hr is None or hr < 2:
        return {}
    cand_cols = [(c, norm(df.iat[hr - 1, c])) for c in range(2, df.shape[1])
                 if norm(df.iat[hr - 1, c]) and norm(df.iat[hr - 1, c]).lower() not in LABELS
                 and not is_pseudo_candidate(norm(df.iat[hr - 1, c]))]
    hdr = [norm(v).lower() for v in df.iloc[hr]]
    bounds = [c for c, _ in cand_cols] + [df.shape[1]]
    cols = []
    for i, (c, nm) in enumerate(cand_cols):
        tv = [j for j in range(c, bounds[i + 1]) if hdr[j] == "total votes"]
        if not tv:
            return {}
        cols.append((tv[0], nm))
    for r in range(len(df) - 1, hr, -1):
        if norm(df.iat[r, 0]).lower().rstrip(":") == "total":
            out = {}
            for c, nm in cols:
                v, _ = parse_votes(df.iat[r, c])
                if v is not None:
                    out[nm] = v
            return out
    return {}


def gate_family_c(df):
    """Certified totals from the outermost trailing rollup — 'County - Total'
    (2024/2026) or 'Countywide - Total' (2022). NEVER 'Cumulative - Total'
    (the all-zero report-template section)."""
    header_row = None
    for r in range(min(15, len(df))):
        if norm(df.iat[r, 0]).lower() == "precinct":
            if "times cast" in {norm(v).lower() for v in df.iloc[r]}:
                header_row = r
                break
    if header_row is None:
        return {}
    hdr = [norm(v).lower() for v in df.iloc[header_row]]
    repeat_cols = [c for c, v in enumerate(hdr) if v == "precinct"]
    repeat_col = repeat_cols[-1] if len(repeat_cols) >= 2 else 4
    cands = [(c, norm(df.iat[header_row, c])) for c in range(repeat_col + 1, df.shape[1])
             if norm(df.iat[header_row, c]) and norm(df.iat[header_row, c]).lower() not in LABELS
             and not is_pseudo_candidate(norm(df.iat[header_row, c]))]
    for r in range(len(df) - 1, header_row, -1):
        lab = norm(df.iat[r, 0]).lower()
        if lab.endswith("- total") and not lab.startswith("cumulative"):
            out = {}
            for c, nm in cands:
                v, _ = parse_votes(df.iat[r, c])
                if v is not None:
                    out[nm] = v
            return out
    return {}


# ------------------------------------------------------------- family E (2006)
def parse_family_e(df, sheet_name):
    """NEW. 2006 named-sheet two-row header:
        row h-1:  PRECINCT | TURN OUT | … | VOTE TOTALS
        row h  :  '' | Registered Voters | Total Ballots Cast | % Turnout |
                  Total Votes for Race | <candidate…>
    A row whose col0 is set and whose every other cell is blank is a PRECINCT ID
    row; the rows under it are its vote-METHOD sub-rows. The trailing block whose
    id row is 'Total' is the countywide rollup (gate, not data)."""
    hr = None
    for r in range(min(12, len(df))):
        rowvals = [norm(v).lower() for v in df.iloc[r]]
        if "total votes for race" in rowvals and "registered voters" in rowvals:
            hr = r
            break
    if hr is None:
        return "", None, [], {}
    rowvals = [norm(v).lower() for v in df.iloc[hr]]
    totcol = rowvals.index("total votes for race")
    rcol = rowvals.index("registered voters")
    cands = [(c, norm(df.iat[hr, c])) for c in range(totcol + 1, df.shape[1])
             if norm(df.iat[hr, c]) and norm(df.iat[hr, c]).lower() not in LABELS
             and not is_pseudo_candidate(norm(df.iat[hr, c]))]
    if not cands:
        return "", None, [], {}
    title = norm(df.iat[0, 0]) or re.sub(r"[*◄►]+", "", sheet_name)
    contest = clean_contest(title)
    vote_for = vote_for_of(title)

    records, gate = [], {}
    current = None
    in_rollup = False
    for r in range(hr + 1, len(df)):
        label = norm(df.iat[r, 0])
        if not label:
            continue
        rest_blank = all(norm(df.iat[r, c]) == "" for c in range(1, df.shape[1]))
        if rest_blank:                       # a bare id row
            current = label
            in_rollup = label.lower() in ("total", "cumulative")
            continue
        if current is None:
            continue
        method = label
        if in_rollup:
            if method.lower() == "total":    # the countywide certified totals
                for col, cand in cands:
                    v, _ = parse_votes(df.iat[r, col])
                    if v is not None:
                        gate[cand] = v
            continue
        if method.lower() in ("total", "cumulative"):
            continue                         # per-precinct subtotal — never emitted
        registered, _ = parse_votes(df.iat[r, rcol])
        for col, cand in cands:
            votes, suppressed = parse_votes(df.iat[r, col])
            if votes is None and not suppressed:
                continue
            records.append({"contest": contest, "vote_for": vote_for, "precinct": current,
                            "candidate": cand, "votes": votes, "suppressed": suppressed,
                            "vote_method": method, "times_cast": None,
                            "registered_voters": registered})
    return contest, vote_for, records, gate


# ------------------------------------------------------- family G (2002 / 2004)
CODE_RE = re.compile(r"^\[(\d+)\]$")
META_LABELS = {"registered voters", "ballots cast", "precincts counted",
               "times cast", "total votes", "voters cast"}
TRAILING_NUM_RE = re.compile(r"^(.*?[^\d,\s])\s*(\d[\d,]*)$")
# Title-shaped rows that are PLACEHOLDER NOTES, not contest headers. Enumerated
# by scanning every title-shaped row adjacent-after a legend row in all four
# 2002/2004 canvass workbooks (2026-08-01): the only two such strings are
# 'CANDIDATE WITHDREW' (x5, a note — the withdrawn candidate has no [code] and no
# column, an honest source gap) and 'Write-In for SL County Mayor' (x1, a REAL
# sub-contest header, deliberately NOT listed here).
NOTE_LABELS = {"candidate withdrew", "candidate disqualified", "no candidate filed"}


def split_legend(label, c2, c3):
    """(candidate_label, certified_total) for one `[NNNN]` legend row.

    Normal rows print  [code] | NAME | total | pct.  The 2002 GENERAL workbook
    overflows its name column, so long labels arrive with the total CONCATENATED
    into the name cell and the percentage shifted left:
        [0429] | 'AARON D. KENNARD RE121,314' | '0.5519' | ''
    (the party suffix is clipped by the same overflow — that clipping is the
    county's own printing and is kept VERBATIM). Detect by 'no third column',
    then split the trailing comma-grouped integer off the label."""
    if c3 != "":
        total, _ = parse_votes(c2)
        return label, total
    m = TRAILING_NUM_RE.match(label)
    if m:
        return m.group(1).strip(), int(m.group(2).replace(",", ""))
    total, _ = parse_votes(c2)
    return label, total


def parse_family_g(df, sheet_name):
    """NEW. 2002 / 2004 single-sheet 'canvass' export.

    Legend rows  `[NNNN] | <label> | <certified total> | <pct>` define every
    column code; contest-title rows (col0 blank, col1 text, col2 blank) group the
    candidate legend rows that FOLLOW them; a row whose col1 starts with '&' is a
    continuation of the previous candidate's printed name (2004 President /
    Vice-President) and is appended verbatim. Data comes in repeated column
    blocks headed `Precinct | [NNNN] | [NNNN] | …`.

    Returns (records, gate) where gate is {(contest, candidate): certified_total}
    taken from the legend — the county's own printed total."""
    def cell(r, c):
        return norm(df.iat[r, c]) if c < df.shape[1] else ""

    code_meta = {}      # code -> dict(label, contest, total, is_meta)
    order = []
    current_title = ""
    last_code = None
    prev_kind = None    # 'legend' | 'title' | 'other' — of row r-1 exactly
    for r in range(len(df)):
        c0, c1, c2 = cell(r, 0), cell(r, 1), cell(r, 2)
        m = CODE_RE.match(c0)
        if m:
            label, total = split_legend(c1, c2, cell(r, 3))
            is_meta = label.lower() in META_LABELS
            code_meta[c0] = {"label": label, "contest": "" if is_meta else current_title,
                             "total": total, "is_meta": is_meta}
            order.append(c0)
            last_code = c0
            prev_kind = "legend"
            continue
        if not c0 and c1 and not c2:
            if c1.startswith("&") and last_code is not None:
                # 2004 President/Vice-President: the running mate wraps onto its
                # own row — appended to the candidate's printed name, verbatim.
                code_meta[last_code]["label"] = (code_meta[last_code]["label"]
                                                 + " " + c1).strip()
                prev_kind = "legend"
                continue
            if c1.lower() == "precinct":
                prev_kind = "other"
                continue
            if c1.lower() in NOTE_LABELS:
                prev_kind = "legend" if prev_kind == "legend" else "other"
                continue
            if prev_kind == "title":
                # The exporter wraps a long title across two adjacent cells
                # ('School Prc #3 GRANITE SCHOOL' + 'DISTRICT') — rejoin it.
                current_title = (current_title + " " + c1).strip()
            else:
                current_title = c1
            last_code = None
            prev_kind = "title"
            continue
        last_code = None
        prev_kind = "other"

    records = []
    seen = set()            # (code, precinct) — guards against a repeated block
    for r in range(len(df)):
        if cell(r, 1).lower() != "precinct":
            continue
        colmap = []
        for c in range(2, df.shape[1]):
            v = cell(r, c)
            if CODE_RE.match(v) and v in code_meta:
                colmap.append((c, v))
        if not colmap:
            continue
        meta_cols = {code_meta[k]["label"].lower(): c for c, k in colmap
                     if code_meta[k]["is_meta"]}
        rcol = meta_cols.get("registered voters")
        bcol = meta_cols.get("ballots cast")
        rr = r + 1
        while rr < len(df):
            pid = cell(rr, 1)
            if not pid or cell(rr, 0) or pid.lower() == "precinct":
                break
            registered, _ = parse_votes(df.iat[rr, rcol]) if rcol is not None else (None, False)
            ballots, _ = parse_votes(df.iat[rr, bcol]) if bcol is not None else (None, False)
            for c, code in colmap:
                info = code_meta[code]
                if info["is_meta"]:
                    continue
                if (code, pid) in seen:
                    continue
                votes, suppressed = parse_votes(df.iat[rr, c])
                if votes is None and not suppressed:
                    continue
                seen.add((code, pid))
                records.append({"contest": clean_contest(info["contest"]),
                                "vote_for": None, "precinct": pid,
                                "candidate": info["label"], "votes": votes,
                                "suppressed": suppressed, "vote_method": "ALL",
                                "times_cast": ballots, "registered_voters": registered})
            rr += 1

    gate = {}
    for code in order:
        info = code_meta[code]
        if info["is_meta"] or info["total"] is None:
            continue
        gate[(clean_contest(info["contest"]), info["label"])] = info["total"]
    return records, gate


# ------------------------------------------------------------------ the driver
# Even-year SOVC/canvass workbooks, in publication order. `family` is the
# EXPECTED family (verified from each file's body 2026-08-01) — the dispatcher
# still tries the others and reports if a sheet lands elsewhere.
FILES = [
    (2002, "2002-06-25", "primary",              "2002/2002-06-25-primary-canvass.xls", "G"),
    (2002, "2002-11-05", "general",              "2002/2002-11-05-general-canvass.xls", "G"),
    (2004, "2004-06-22", "primary",              "2004/2004-06-22-primary-canvass.xls", "G"),
    (2004, "2004-11-02", "general",              "2004/2004-11-02-general-canvass.xls", "G"),
    (2006, "2006-06-27", "primary",              "2006/2006-06-27-primary-sovc.xls", "E"),
    (2006, "2006-11-07", "general",              "2006/2006-11-07-general-sovc.xls", "E"),
    (2008, "2008-06-24", "primary",              "2008/2008-06-24-primary-sovc.xls", "A"),
    (2008, "2008-11-04", "general",              "2008/2008-11-04-general-sovc.xls", "A"),
    (2010, "2010-06-22", "primary",              "2010/2010-06-22-primary-sovc.xlsx", "A"),
    (2010, "2010-11-02", "general",              "2010/2010-11-02-general-sovc.xlsx", "A"),
    (2012, "2012-06-26", "primary",              "2012/2012-06-26-primary-sovc.xlsx", "A"),
    (2012, "2012-11-06", "general",              "2012/2012-11-06-general-sovc.xlsx", "A"),
    (2014, "2014-06-24", "primary",              "2014/2014-06-24-primary-sovc.xlsx", "A"),
    (2014, "2014-11-04", "general",              "2014/2014-11-04-general-sovc.xlsx", "A"),
    (2016, "2016-06-28", "primary",              "2016/2016-06-28-primary-sovc.xlsx", "A"),
    (2016, "2016-11-08", "general",
     "2016/2016-11-08-general-election-statement-of-votes-cast.zip", "A"),
    (2016, "2016-12-06", "recount",
     "2016/2016-12-06-house-32-recount-statement-of-votes-cast.zip", "A"),
    (2018, "2018-06-26", "primary",
     "2018/2018--06-26-primary-election-statement-of-votes-cast.zip", "A"),
    (2018, "2018-11-06", "general",              "2018/2018-11-06-general-election-sovc.xlsx", "D"),
    (2020, "2020-03-03", "presidential primary", "2020/2020-03-03-presidential-primary-sovc.xls", "D"),
    (2020, "2020-06-30", "primary",              "2020/2020-06-30-primary-sovc.xls", "D"),
    (2020, "2020-11-03", "general",              "2020/2020-11-03-general-election-sovc.xlsx", "D"),
    (2022, "2022-06-28", "primary",              "2022/statementofvotescast.xlsx", "C"),
    (2022, "2022-11-08", "general",              "2022/statementofvotescastrpt-11-22-2022.xlsx", "C"),
    (2024, "2024-03-05", "presidential primary", "2024/statementofvotescastrpt_20240319.xlsx", "C"),
    (2024, "2024-06-25", "primary",              "2024/statementofvotescastrpt_20240625.xlsx", "C"),
    (2024, "2024-08-05", "recount",              "2024/statementofvotescastrpt-ushouse2recount.xlsx", "C"),
    (2024, "2024-11-05", "general",              "2024/statementofvotescastrpt-11-19-2024.xlsx", "C"),
    (2026, "2026-06-23", "primary",              "2026/statementofvotescastrptvoterprivacy.xlsx", "C"),
]

# Source-internal contradictions kept VERBATIM: (relpath, contest, candidate)
# whose emitted precinct sum disagrees with the workbook's own certified total
# for a reason that is NOT privacy suppression. Each must be documented in
# RECON_COUNTY_2026-08-01.md. Anything not listed here FAILS the run.
KNOWN_SOURCE_DISCREPANCIES = {
    # 2004 general, "Salt Lake City School District 2" (a school-board contest —
    # never reaches the county-office deliverable). The workbook prints 15
    # precinct rows for the contest and its own legend certifies ULUAVE 1939 /
    # CLARA 1938, but those 15 rows sum to 1937 / 1934. VERIFIED 2026-08-01
    # against the county's own certified summary PDF
    # (historical-election-results/2004-11-02-general-election.pdf, "Salt Lake
    # City School District 2  ALAMA ULUAVE 1939 50.01% / J. MICHAEL CLARA 1938
    # 49.99%") — the contest-level figure is the county's certified one, and the
    # 5 unallocated votes are a source-internal contradiction, not a parse loss.
    # Both figures are the county's own publication; the precinct rows are kept
    # VERBATIM and the contest total is NOT back-filled.
    ("2004/2004-11-02-general-canvass.xls", "Salt Lake City School District 2",
     "ALAMA ULUAVE"),
    ("2004/2004-11-02-general-canvass.xls", "Salt Lake City School District 2",
     "J. MICHAEL CLARA"),
}

COLS = ["year", "election_date", "election_type", "source_file", "sheet", "family",
        "contest", "vote_for", "precinct", "candidate", "votes", "suppressed",
        "vote_method", "times_cast", "registered_voters"]
RECON_COLS = ["year", "election_date", "election_type", "source_file", "sheet",
              "contest", "candidate", "parsed_sum", "certified_total", "delta",
              "suppressed_cells", "status"]
INV_COLS = ["year", "election_date", "election_type", "source_file", "sheet",
            "family", "contest", "county_office", "district", "kind",
            "n_candidates", "n_precincts", "n_rows", "total_votes", "retained"]


def dispatch(df, sheet_name):
    """(family, contest, vote_for, records, gate_override) for one sheet."""
    contest, vote_for, recs = parse_family_c(df)
    if recs:
        return "C", contest, vote_for, recs, None
    recs = parse_family_b(df, sheet_name)
    if recs:
        return "B", recs[0]["contest"], None, recs, None
    if not re.fullmatch(r"Sheet\d+", sheet_name):
        contest, vote_for, recs = parse_family_a(df, sheet_name)
        if recs:
            return "A", contest, vote_for, recs, None
        contest, vote_for, recs, gate = parse_family_e(df, sheet_name)
        if recs:
            return "E", contest, vote_for, recs, gate
    contest, vote_for, recs = parse_family_d(df)
    if recs:
        return "D", contest, vote_for, recs, None
    return "", "", None, [], None


def gate_for(family, df, override):
    if override is not None:
        return override
    if family == "A":
        return gate_family_a(df)
    if family == "C":
        return gate_family_c(df)
    if family in ("B", "D"):
        return gate_family_d(df)
    return {}


def main():
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]
    full = "--full" in sys.argv

    all_rows, recon_rows, failures, notes = [], [], [], []
    full_rows, inventory = [], []
    for year, edate, etype, rel, expected in FILES:
        if only and str(year) != str(only):
            continue
        path = os.path.join(RAW, rel)
        name = os.path.basename(rel)
        if not os.path.exists(path):
            notes.append((rel, "NOT PRESENT — see sources.csv"))
            print("  --  %s  (file not present)" % rel)
            continue
        try:
            sheets = read_workbook(path)
        except Exception as e:                                   # noqa: BLE001
            notes.append((rel, "UNREADABLE: %s: %s" % (type(e).__name__, e)))
            print("  !!  %s  (unreadable: %s)" % (rel, e))
            continue

        rows, n_contests, fams = [], 0, defaultdict(int)
        if expected == "G":
            df = sheets[0][1]
            recs, gate = parse_family_g(df, sheets[0][0])
            for rec in recs:
                rows.append({"year": year, "election_date": edate, "election_type": etype,
                             "source_file": name, "sheet": sheets[0][0], "family": "G", **rec})
            fams["G"] = len({r["contest"] for r in recs})
            n_contests = fams["G"]
            # gate: legend total per (contest, candidate)
            got = defaultdict(int)
            sup = defaultdict(int)
            for rec in recs:
                got[(rec["contest"], rec["candidate"])] += rec["votes"] or 0
                if rec["suppressed"]:
                    sup[(rec["contest"], rec["candidate"])] += 1
            for key, cert in gate.items():
                s = got.get(key, 0)
                st = ("exact" if s == cert else
                      "suppressed-deficit" if s < cert and sup.get(key) else "MISMATCH")
                if st == "MISMATCH" and (rel, key[0], key[1]) in KNOWN_SOURCE_DISCREPANCIES:
                    st = "known-source-discrepancy"
                if st == "MISMATCH":
                    failures.append((rel, sheets[0][0], key[0], key[1], s, cert))
                recon_rows.append({"year": year, "election_date": edate,
                                   "election_type": etype, "source_file": name, "sheet": sheets[0][0],
                                   "contest": key[0], "candidate": key[1],
                                   "parsed_sum": s, "certified_total": cert,
                                   "delta": s - cert, "suppressed_cells": sup.get(key, 0),
                                   "status": st})
        else:
            for sheet, df in sheets:
                if df.empty:
                    continue
                fam, contest, _vf, recs, override = dispatch(df, sheet)
                if not recs:
                    continue
                fams[fam] += 1
                n_contests += 1
                for rec in recs:
                    rows.append({"year": year, "election_date": edate,
                                 "election_type": etype, "source_file": name,
                                 "sheet": sheet, "family": fam, **rec})
                gate = gate_for(fam, df, override)
                got, sup = defaultdict(int), defaultdict(int)
                for rec in recs:
                    if rec["precinct"] == "Cumulative":
                        continue
                    got[rec["candidate"]] += rec["votes"] or 0
                    if rec["suppressed"]:
                        sup[rec["candidate"]] += 1
                if not gate:
                    recon_rows.append({"year": year, "election_date": edate,
                                   "election_type": etype, "source_file": name, "sheet": sheet,
                                       "contest": contest, "candidate": "*",
                                       "parsed_sum": sum(got.values()),
                                       "certified_total": "", "delta": "",
                                       "suppressed_cells": sum(sup.values()),
                                       "status": "NO CERTIFIED TOTAL ROW"})
                    failures.append((rel, sheet, contest, "*", sum(got.values()), None))
                    continue
                for cand, cert in gate.items():
                    s = got.get(cand, 0)
                    st = ("exact" if s == cert else
                          "suppressed-deficit" if s < cert and sup.get(cand) else "MISMATCH")
                    if st == "MISMATCH" and (rel, contest, cand) in KNOWN_SOURCE_DISCREPANCIES:
                        st = "known-source-discrepancy"
                    if st == "MISMATCH":
                        failures.append((rel, sheet, contest, cand, s, cert))
                    recon_rows.append({"year": year, "election_date": edate,
                                   "election_type": etype, "source_file": name, "sheet": sheet,
                                       "contest": contest, "candidate": cand,
                                       "parsed_sum": s, "certified_total": cert,
                                       "delta": s - cert,
                                       "suppressed_cells": sup.get(cand, 0), "status": st})
        # ---- scope + inventory: every contest is catalogued, county-level rows kept
        by_contest = defaultdict(list)
        for r in rows:
            by_contest[(r["contest"], r["sheet"])].append(r)
        kept = 0
        for (contest, sheet), grp in sorted(by_contest.items()):
            office, district, kind = classify(contest)
            keep = bool(office)
            inventory.append({
                "year": year, "election_date": edate, "election_type": etype,
                "source_file": name, "sheet": sheet, "family": grp[0]["family"],
                "contest": contest, "county_office": office, "district": district,
                "kind": kind, "n_candidates": len({g["candidate"] for g in grp}),
                "n_precincts": len({g["precinct"] for g in grp
                                    if g["precinct"] != "Cumulative"}),
                "n_rows": len(grp),
                "total_votes": sum(g["votes"] or 0 for g in grp),
                "retained": "yes" if keep else "no"})
            if keep:
                all_rows.extend(grp)
                kept += len(grp)
        if full:
            full_rows.extend(rows)
        fam_s = " ".join("%s:%d" % kv for kv in sorted(fams.items()))
        print("  ok  %4d %-22s %-52s %4d contests %8d rows  (county-level kept: %6d)  [%s]"
              % (year, etype, name[:52], n_contests, len(rows), kept, fam_s))

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in all_rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in COLS})
    with open(RECON, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=RECON_COLS)
        w.writeheader()
        w.writerows(recon_rows)
    inventory.sort(key=lambda r: (r["election_date"], r["election_type"],
                                  r["county_office"], r["district"], r["contest"]))
    with open(INVENTORY, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=INV_COLS)
        w.writeheader()
        w.writerows(inventory)
    if full:
        with open(FULL_OUT, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=COLS)
            w.writeheader()
            for r in full_rows:
                w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in COLS})
        print("Wrote %s (ALL contests, gitignored): %d rows" % (FULL_OUT, len(full_rows)))

    by_status = defaultdict(int)
    for r in recon_rows:
        by_status[r["status"]] += 1
    print("\nWrote %s: %d rows | %d contests | %d precincts"
          % (os.path.basename(OUT), len(all_rows),
             len({(r["year"], r["election_type"], r["contest"]) for r in all_rows}),
             len({r["precinct"] for r in all_rows})))
    print("Wrote %s: %d contests catalogued (%d retained as Salt Lake County-level, "
          "%d other-jurisdiction contests recorded but not carried)"
          % (os.path.basename(INVENTORY), len(inventory),
             sum(1 for r in inventory if r["retained"] == "yes"),
             sum(1 for r in inventory if r["retained"] == "no")))
    print("RECONCILIATION GATE (%s): %s"
          % (os.path.basename(RECON), dict(sorted(by_status.items()))))
    for rel, note in notes:
        print("  note: %s — %s" % (rel, note))
    if failures:
        print("\nGATE FAILURES (%d) — first 40:" % len(failures))
        for f_ in failures[:40]:
            print("   ", f_)
        sys.exit(1)
    print("GATE PASSED — every candidate column reconciles to the workbook's own "
          "certified total (or is an accounted privacy-suppression deficit).")


if __name__ == "__main__":
    main()
