#!/usr/bin/env python3
"""normalize_weber.py — Weber County election canvass raw files -> canonical tidy long CSV.

Raw inputs (all retained verbatim):
  raw/     hash-named files from weberelections.gov (Wix; labels + provenance in sources.csv)
  ev_api/  Enhanced Voting portal JSON harvest (electionresults.utah.gov), 2024-2026

Output: weber_results_long.csv — one row per (source, contest, precinct-or-summary,
candidate), schema identical to salt_lake_county/elections/slco_municipal_results_long.csv:
  year, election_type, source_file, sheet, contest, vote_for, precinct, candidate,
  votes, suppressed, vote_method, times_cast, registered_voters

Grain honesty:
  precinct = ''   -> the county published only contest-grain totals for that election
                     (no precinct canvass on its site); vote_method is always 'Total'
                     (Weber publishes no by-method split in any covered report).
  suppressed=True -> the county printed the precinct with vote cells suppressed
                     (<15 voters rule); votes is left EMPTY. Never imputed.

Scope: ALL contests from odd-year municipal canvasses (city + special-district rows kept,
like the SLCo model — filtered downstream by build_elections.py); COUNTY-office contests
only from even-year federal cycles (commission + row offices + countywide props). The
county published its 2023 general canvass bond-only (municipal results deferred to the
cities' own sites — an honest gap recorded in VERIFICATION.md).

Never fabricates: every row parses from a retained raw file; reconciliation of candidate
sums vs each report's own printed "Total Votes" is written to reconciliation.csv.
"""
import csv
import json
import os
import re
import subprocess
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
EV = os.path.join(HERE, "ev_api")
OUT = os.path.join(HERE, "weber_results_long.csv")
RECON_OUT = os.path.join(HERE, "reconciliation.csv")

COLS = ["year", "election_type", "source_file", "sheet", "contest", "vote_for",
        "precinct", "candidate", "votes", "suppressed", "vote_method",
        "times_cast", "registered_voters"]


def pdftext(fname, layout=True):
    path = os.path.join(RAW, fname)
    args = ["pdftotext"]
    if layout:
        args.append("-layout")
    args += [path, "-"]
    t = subprocess.run(args, capture_output=True, text=True).stdout
    return t.split("\f")


def to_int(s):
    return int(s.replace(",", "").strip())


_NUMWORD = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
            "six": "6", "seven": "7"}


def dedup_contest(name):
    """Electionware prints '<LONG TITLE> <Short Title>' as adjacent text runs
    with no separator ('FARR WEST CITY MAYOR Farr West City Mayor'). Keep the
    county's LONG title: cut at a later re-start of the leading token(s), but
    ONLY when the would-be tail is an abbreviated echo of the head (every tail
    token already appears in the head, up to case/hyphen/number-word variants)
    — so genuinely distinct info ('... AT-LARGE ... AT-LARGE 2 YR') is never
    truncated. Verbatim otherwise."""
    toks = name.split()

    def norm(t):
        t = t.lower().replace("-", "").rstrip(".,")
        return _NUMWORD.get(t, t)

    if len(toks) >= 4:
        k0, k1 = norm(toks[0]), norm(toks[1])
        headset_all = None

        def tail_is_echo(i):
            head = {norm(t) for t in toks[:i]} | {"", "-", k0 + k1}
            return all(norm(t) in head or t == "-" for t in toks[i:])

        cut = None
        for i in range(2, len(toks) - 1):
            if norm(toks[i]) == k0 and norm(toks[i + 1]) == k1:
                cut = i
                break
        if cut is None:
            for i in range(2, len(toks)):
                if norm(toks[i]) == k0 + k1:
                    cut = i
                    break
        if cut is None and k0.isalpha() and len(k0) >= 4:
            for i in range(3, len(toks)):
                if norm(toks[i]) == k0:
                    cut = i
                    break
        if cut is not None and tail_is_echo(cut):
            return " ".join(toks[:cut])
    if len(toks) >= 2 and len(toks) % 2 == 0:
        h = len(toks) // 2
        if [t.lower() for t in toks[:h]] == [t.lower() for t in toks[h:]]:
            return " ".join(toks[:h])
    return name


def row(year, etype, src, sheet, contest, vote_for, precinct, cand, votes,
        suppressed, times_cast="", reg=""):
    return dict(year=year, election_type=etype, source_file=src, sheet=sheet,
                contest=dedup_contest(contest), vote_for=vote_for,
                precinct=precinct, candidate=cand, votes=votes,
                suppressed=suppressed, vote_method="Total",
                times_cast=times_cast, registered_voters=reg)


# ---------------------------------------------------------------------------
# P1 — precinct-page canvass reports ("Precinct Summary" / "Precinct Level
# Results" / "Precinct Results Report", 2020-2026 era). One page per precinct:
# precinct code line (optional " Suppressed"), Statistics block, contest blocks.
# ---------------------------------------------------------------------------
P1_SKIP = re.compile(
    r"^(Total Votes Cast\b|Overvotes\b|Undervotes\b|Contest Totals\b|Statistics$|"
    r"Registered Voters|Ballots Cast|Voter Turnout|TOTAL(\s+VOTE ?%)?$)")
P1_FOOTER = re.compile(
    r"(Report generated|Page \d+ of \d+|OFFICIAL|Official Canvass|Canvass Results|"
    r"Precinct Level Results$|- \d{2}/\d{2}/\d{4})")
P1_HEADER = re.compile(
    r"^(WEBER COUNTY$|Weber County$|Precinct (Summary|Level|Results)|Summary Results Report|"
    r"\d{4} (General|Primary|Presidential|Municipal|GENERAL|PRIMARY)|November|September|August|June|"
    r"OGDEN VALLEY CITY$)")
P1_CAND = re.compile(r"^(\S.*?)\s{2,}([\d,]+)(?:\s+([\d.]+%))?\s*$")
P1_PRECINCT = re.compile(
    r"^((?=[A-Z0-9]*\d)[A-Z0-9]{4,8}(?::[A-Z0-9]{1,3})?)(\s+Suppressed)?\s*$")
P1_VOTEFOR = re.compile(r"^Vote For (\d+)\s*$")


def parse_p1(fname, year, etype, sheet, keep_contest=None):
    rows, recon = [], []
    for page in pdftext(fname):
        lines = page.splitlines()
        precinct, suppressed = None, False
        times_cast, reg = "", ""
        contest, vote_for = None, ""
        pending = []          # bare lines: next heading OR suppressed candidates
        page_rows = []        # rows emitted this page (suppressed rows fixed later)
        totals = {}
        sums = defaultdict(int)

        def flush_pending_as_candidates(upto=None):
            """pending lines (except the last `upto` kept as heading) are
            suppressed candidate cells of the CURRENT contest."""
            nonlocal pending
            cands = pending if upto is None else pending[:-upto]
            if contest and suppressed:
                for c in cands:
                    page_rows.append(row(year, etype, fname, sheet, contest,
                                         vote_for, precinct, c, "", True,
                                         times_cast, reg))
            pending = pending[-upto:] if upto else []

        for ln in page.splitlines():
            s = ln.rstrip("\n")
            st = s.strip()
            if not st:
                continue
            if precinct is None:
                m = P1_PRECINCT.match(st)
                if m and not P1_HEADER.match(st):
                    precinct = m.group(1)
                    suppressed = bool(m.group(2))
                continue
            if P1_HEADER.match(st) or P1_FOOTER.search(st):
                continue
            m = P1_VOTEFOR.match(st)
            if m:
                # last pending line = this contest's heading; earlier pending
                # lines were suppressed candidates of the previous contest
                if pending:
                    flush_pending_as_candidates(upto=1)
                    new_contest = pending[0]
                    pending = []
                else:
                    new_contest = contest or ""
                contest = new_contest
                vote_for = m.group(1)
                continue
            if st.startswith("Registered Voters - Total"):
                m2 = re.search(r"([\d,]+)\s*$", st)
                reg = to_int(m2.group(1)) if m2 else ""
                continue
            if st.startswith("Ballots Cast - Total"):
                m2 = re.search(r"([\d,]+)\s*$", st)
                times_cast = to_int(m2.group(1)) if m2 else ""
                continue
            if P1_SKIP.match(st):
                if st.startswith("Total Votes Cast") and contest:
                    m2 = re.search(r"([\d,]+)(?:\s+[\d.]+%)?\s*$", st)
                    if m2:
                        totals[contest] = to_int(m2.group(1))
                continue
            indent = len(s) - len(s.lstrip())
            if indent >= 3:
                continue        # indented sub-rows: Write-In: details, Not Assigned
            m = P1_CAND.match(st)
            if m and contest is not None:
                flush_pending_as_candidates()
                cand, votes = m.group(1).strip(), to_int(m.group(2))
                if cand.startswith("Write-In:") or cand.startswith("Not Assigned"):
                    continue
                page_rows.append(row(year, etype, fname, sheet, contest, vote_for,
                                     precinct, cand, votes, False, times_cast, reg))
                sums[contest] += votes
                continue
            pending.append(st)
        flush_pending_as_candidates()
        if keep_contest:
            page_rows = [r for r in page_rows if keep_contest(r["contest"])]
        rows.extend(page_rows)
        for c, tot in totals.items():
            if keep_contest and not keep_contest(c):
                continue
            recon.append(dict(source_file=fname, scope=f"precinct {precinct}",
                              contest=dedup_contest(c), parsed_sum=sums[c],
                              printed_total=tot, match=(sums[c] == tot)))
    return rows, recon


# ---------------------------------------------------------------------------
# P2 — Electionware "Summary Results Report" (2018-2023 era). Contest-grain:
# per-jurisdiction sections (2019, 2023 city files) or one county section
# (2018, 2020, 2021, 2026). precinct='' — the county published no precinct
# canvass for these elections (except where a separate P1 file exists).
# ---------------------------------------------------------------------------
P2_SKIP = re.compile(
    r"^(Overvotes\b|Undervotes\b|Contest Totals\b|STATISTICS$|Statistics$|"
    r"Registered Voters|Ballots Cast|Voter Turnout|TOTAL(\s.*)?$|"
    r"Election$|Day$)")
P2_FOOTER = re.compile(
    r"(Report generated|Page \d+ of \d+|Summary - \d{2}/\d{2}/\d{4}|"
    r"- \d{2}/\d{2}/\d{4}\s|This report contains|^elections held )")
P2_CAND = re.compile(
    r"^(\S(?:.*?\S)?)\s{2,}([\d,]+)(?:\s+([\d.]+%))?(?:\s+[-\d,.%]+)*\s*$")
P2_HEADER = re.compile(
    r"^(Summary (Results|Report)|Results Report|CANVASS REPORT|"
    r"\d{4} (GENERAL|General|PRIMARY|Primary|Presidential|Municipal|Republican|"
    r"Democratic)|January|February|March|April|May|JUNE|June|JULY|July|"
    r"August|September|October|November|December|OFFICIAL|"
    r"Official|WEBER COUNTY\b|Weber County\b|OGDEN VALLEY CITY$|Final Results|"
    r"Final Canvass|Canvass Results|Tuesday November)")
CITYISH = re.compile(r"(City|Town|Elections)\s*$")


def parse_p2(fname, year, etype, default_sheet, keep_contest=None,
             attach_city_stats=True):
    """Contest-grain Electionware summary. Returns rows, recon (recon rows carry
    the printed 'Total Votes Cast' per contest so precinct files can be checked
    against them)."""
    rows, recon = [], []
    sheet = default_sheet
    times_cast, reg = "", ""
    for page in pdftext(fname):
        lines = [l for l in page.splitlines()]
        # page jurisdiction: right-most cell of the first 4 non-blank lines
        head = [l for l in lines if l.strip()][:4]
        page_sheet = None
        for hl in head:
            cells = re.split(r"\s{2,}", hl.strip())
            if len(cells) >= 2 and CITYISH.search(cells[-1]) \
                    and "Weber County" not in cells[-1]:
                page_sheet = cells[-1].strip()
        if page_sheet and page_sheet != sheet:
            sheet = page_sheet
            times_cast, reg = "", ""     # stats reset on new jurisdiction section
        contest, vote_for = None, ""
        heading = []
        for ln in lines:
            s = ln.rstrip("\n")
            st = s.strip()
            if not st:
                continue
            if P2_FOOTER.search(st) or P2_HEADER.match(st):
                continue
            if st.startswith("Registered Voters - Total"):
                m = re.search(r"Total\s+([\d,]+)", st)
                if m:
                    reg = to_int(m.group(1))
                continue
            if st.startswith("Registered Voters -"):
                continue
            if st.startswith("Ballots Cast - Total"):
                m = re.search(r"Total\s+([\d,]+)", st)
                if m:
                    times_cast = to_int(m.group(1))
                continue
            if st.startswith("Ballots Cast -"):
                continue
            m = P1_VOTEFOR.match(st)
            if m:
                contest = " ".join(heading).strip()
                vote_for = m.group(1)
                heading = []
                continue
            if st.startswith("Total Votes Cast"):
                m = re.search(r"^Total Votes Cast\s+([\d,]+)", st)
                if m and contest and (not keep_contest or keep_contest(contest)):
                    recon.append(dict(source_file=fname, scope=sheet,
                                      contest=dedup_contest(contest),
                                      printed_total=to_int(m.group(1))))
                continue
            if P2_SKIP.match(st):
                continue
            indent = len(s) - len(s.lstrip())
            if indent >= 3 and (st.startswith("Write-In:")
                                or st.startswith("Not Assigned")):
                continue
            m = P2_CAND.match(st)
            if m and contest is not None:
                cand, votes = m.group(1).strip(), to_int(m.group(2))
                if cand.startswith("Write-In:") or cand.startswith("Not Assigned"):
                    continue
                if keep_contest and not keep_contest(contest):
                    continue
                use_stats = attach_city_stats and CITYISH.search(sheet or "")
                rows.append(row(year, etype, fname, sheet, contest, vote_for,
                                "", cand, votes, False,
                                times_cast if use_stats else "",
                                reg if use_stats else ""))
                continue
            # non-candidate, non-skip line: contest heading material
            heading.append(st)
    return rows, recon


# ---------------------------------------------------------------------------
# P3 — GEMS "Election Summary Report" (2004-2017 era; Diebold/Premier GEMS).
# Two-column pages (municipal 2007-2017) or one wide column (2006/2010
# re-prints). Contest-grain. Parsed via pdfplumber word coordinates.
# ---------------------------------------------------------------------------
P3_CAND = re.compile(r"^(\S.*?)\s+([\d,]+)\s+([\d.]+)%$")
P3_LABEL = re.compile(
    r"^(Number of Precincts|Precincts Reporting|Vote For|Times Counted|"
    r"Total Votes|Total$)")


P3_HEADFOOT = re.compile(
    r"^(Election Summary Report|Weber County, Utah|Municipal |Municipal$|"
    r"General Election|Primary Election|Special Election|Summary For |OFFICIAL|"
    r"Official |Canvass Report|Date:|Time:|Page:?\s?\d|GEMS ELECTION|"
    r"\d+/\d+/\d{4}|November \d|September \d|August \d|June \d|February \d|"
    r"Registered Voters \d|Num\. Report|Statement of|SOVC For|TURN OUT|"
    r"Election Night|Utah Election|All Counters|All Races|RESULTS$|"
    r"Absentee/ ?Early)")
P3_LABEL_START = re.compile(r"^(Times|Total|Vote|Number|Precincts)$")


def p3_column_lines(pdf_path):
    """Lines per page reconstructed per visual column. Columns are located from
    the x positions of the GEMS per-contest label rows (Times Counted / Total
    Votes / Vote For / Number of Precincts), which sit at each column's left
    edge — robust across the 1/2/3-column GEMS layout variants.
    Full-width header/footer lines are dropped before splitting. Pages that are
    SOVC precinct grids (the 2007 primary compilation) are skipped."""
    import pdfplumber

    def cluster_lines(words):
        """Group words into visual lines by BASELINE (bottom) sweep-clustering
        — robust when adjacent runs use different font sizes (the GEMS 'name
        and its numbers land in different top-buckets' failure)."""
        out = defaultdict(list)
        if not words:
            return out
        ws = sorted(words, key=lambda w: w["bottom"])
        key, last = 0, None
        for w in ws:
            if last is None or w["bottom"] - last > 2.5:
                key = w["bottom"]
            out[key].append(w)
            last = w["bottom"]
        return out

    out_pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words()
            # drop words on full-line header/footers
            byline = cluster_lines(words)
            kept = []
            is_sovc = False
            juris = None
            for k, ws in byline.items():
                ws = sorted(ws, key=lambda w: w["x0"])
                full = " ".join(w["text"] for w in ws)
                if re.match(r"^(Statement of Votes|SOVC For)", full):
                    is_sovc = True
                m = re.match(r"^Summary For ([^,]+),", full)
                if m:
                    juris = m.group(1).strip()
                if P3_HEADFOOT.match(full):
                    continue
                kept.extend(ws)
            if is_sovc:
                out_pages.append((None, []))  # SOVC grid page: not summary form
                continue
            # column left edges from label-row anchors
            anchors = []
            for k, ws in byline.items():
                ws = sorted(ws, key=lambda w: w["x0"])
                for i, w in enumerate(ws):
                    nxt = ws[i + 1]["text"] if i + 1 < len(ws) else ""
                    if (w["text"], nxt) in (("Times", "Counted"),
                                            ("Total", "Votes"),
                                            ("Vote", "For"),
                                            ("Number", "of")):
                        anchors.append(w["x0"])
            edges = []
            for x in sorted(anchors):
                if not edges or x - edges[-1][-1] > 60:
                    edges.append([x])
                else:
                    edges[-1].append(x)
            col_lefts = [min(e) for e in edges] or [0]
            bounds = [cl - 15 for cl in col_lefts]
            cols = defaultdict(list)
            for w in kept:
                ci = 0
                for j, b in enumerate(bounds):
                    if w["x0"] >= b:
                        ci = j
                cols[ci].append(w)
            lines = []
            for c in sorted(cols):
                rows_ = cluster_lines(cols[c])
                for k in sorted(rows_):
                    ws = sorted(rows_[k], key=lambda w: w["x0"])
                    lines.append(" ".join(w["text"] for w in ws))
            out_pages.append((juris, lines))
    return out_pages


def clean_p3_line(st):
    """Strip web-reprint noise from the 2006/2010 'GEMS ELECTION RESULTS'
    HTML-print PDFs: soft hyphens, the co.weber.ut.us URL + page fraction,
    and the date/time + 'WEBER COUNTY OFFICIAL RESULTS' banner fragments."""
    st = st.replace("\xad", "-")
    st = re.sub(r"https?://\S+", " ", st)
    st = re.sub(r"\S*co\.weber\.ut\.us\S*", " ", st)
    st = " ".join(st.split())
    st = re.sub(r"^\d+/\d+(\s+|$)", "", st)      # page fraction '3/7 '
    st = re.sub(r"^\d{2}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\s*", "", st)
    st = re.sub(r"^(WEBER COUNTY )?OFFICIAL RESULTS( [\d.]+%)*\s*", "", st)
    st = re.sub(r"\s+\d+/\d+$", "", st)          # trailing page fraction
    return st.strip()


def parse_p3(fname, year, etype, default_sheet, keep_contest=None):
    """GEMS contest-grain summary. Jurisdiction ('Summary For X') tracked per
    page for the multi-city 2007 primary compilation."""
    rows, recon = [], []
    sheet = default_sheet
    pages = p3_column_lines(os.path.join(RAW, fname))
    contest, vote_for, times_cast, reg = None, "", "", ""
    heading = []

    def start_contest():
        nonlocal contest, vote_for, times_cast, reg, heading
        contest = " ".join(heading).strip()
        vote_for, times_cast, reg = "", "", ""
        heading = []

    for juris, lines in pages:
        if juris:
            sheet = default_sheet if juris.lower().startswith("jurisdiction") \
                else juris
        for raw_line in lines:
            st = clean_p3_line(raw_line)
            if not st:
                continue
            if P3_HEADFOOT.match(st):
                continue
            if st == "Total":
                # GEMS prints the 'Total' column header right after the heading
                if heading:
                    start_contest()
                continue
            if st.endswith(" Total") and not st.startswith("Total Votes"):
                # 2013 variant: a wrapped heading tail shares the line with the
                # 'Total' column header ('DISTRICTS 1 2   Total')
                tail = st[:-len(" Total")].strip()
                if tail and not P3_CAND.match(tail):
                    heading.append(tail)
                    start_contest()
                    continue
            m = re.match(r"^Vote For (\d+)$", st)
            if m:
                vote_for = m.group(1)
                continue
            m = re.match(r"^Times Counted ([\d,]+)/([\d,]+)", st)
            if m:
                times_cast, reg = to_int(m.group(1)), to_int(m.group(2))
                continue
            m = re.match(r"^Total Votes ([\d,]+)$", st)
            if m:
                if contest and (not keep_contest or keep_contest(contest)):
                    recon.append(dict(source_file=fname, scope=sheet,
                                      contest=dedup_contest(contest),
                                      printed_total=to_int(m.group(1))))
                continue
            if P3_LABEL.match(st):
                continue
            m = P3_CAND.match(st)
            if m and contest:
                cand, votes = m.group(1).strip(), to_int(m.group(2))
                if keep_contest and not keep_contest(contest):
                    continue
                rows.append(row(year, etype, fname, sheet, contest, vote_for,
                                "", cand, votes, False, times_cast, reg))
                continue
            # plain text -> next contest heading fragment
            heading.append(st)
    return rows, recon


# ---------------------------------------------------------------------------
# P4 — the 2018 General "Full Precinct Report" CSV (machine-readable precinct
# grain; county-office contests kept).
# ---------------------------------------------------------------------------
def parse_p4(fname, year, etype, keep_contest):
    """The 2018 'Full Precinct Report' CSV: paginated bands, each = a header
    row carrying 1+ contest names at their starting column, a VOTE FOR row, a
    '-' row, a candidate-name row, then precinct rows (precinct code in col 0).
    Candidate columns map to the nearest contest name at or left of them."""
    path = os.path.join(RAW, fname)
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
        grid = [[c.strip() for c in r_] for r_ in csv.reader(f)]
    rows, recon = [], []
    stats = {}          # precinct -> (ballots_cast, registered)
    mode = None         # 'stats' | 'contest'
    colmap = []         # [(colidx, candidate, contest, vote_for)]
    i = 0
    while i < len(grid):
        cells = grid[i]
        c0 = cells[0] if cells else ""
        rest = cells[1:]
        if not any(cells):
            i += 1
            continue
        if not c0:
            if "STATISTICS" in rest:
                mode = "stats"
                i += 1
                continue
            if any(c.startswith("Registered Voters") for c in rest):
                i += 1
                continue
            if any(c.startswith("VOTE FOR") for c in rest):
                i += 1
                continue
            if all(c in ("", "-") for c in cells):
                i += 1
                continue
            # header row: either contest names or candidate names.
            nxt = grid[i + 1] if i + 1 < len(grid) else []
            if any(c.startswith("VOTE FOR") for c in nxt):
                # contest-name row; VOTE FOR row at i+1; '-' row; candidates row
                contests = [(j, c) for j, c in enumerate(cells) if c]
                votefor = {j: v for j, v in enumerate(nxt) if v}
                k = i + 2
                while k < len(grid) and all(c in ("", "-") for c in grid[k]):
                    k += 1
                cand_row = grid[k]
                colmap = []
                for j in range(1, len(cand_row)):
                    if not cand_row[j]:
                        continue
                    owner = None
                    vf = ""
                    for cj, cname in contests:
                        if cj <= j:
                            owner = cname
                            vf = votefor.get(cj, "")
                    if owner:
                        m = re.search(r"(\d+)", vf)
                        colmap.append((j, cand_row[j], owner,
                                       m.group(1) if m else ""))
                mode = "contest"
                i = k + 1
                continue
            i += 1
            continue
        # data row (precinct in col 0)
        if c0.lower().startswith(("total", "electionwide", "cumulative")):
            i += 1
            continue
        if mode == "stats":
            try:
                stats[c0] = (to_int(cells[2]), to_int(cells[1]))
            except (ValueError, IndexError):
                pass
        elif mode == "contest":
            tc, rv = stats.get(c0, ("", ""))
            for j, cand, contest, vf in colmap:
                if keep_contest and not keep_contest(contest):
                    continue
                val = cells[j] if j < len(cells) else ""
                if val == "":
                    continue
                ok = val.replace(",", "").isdigit()
                rows.append(row(year, etype, fname, "Weber County", contest,
                                vf, c0, cand,
                                to_int(val) if ok else "", not ok, tc, rv))
        i += 1
    return rows, recon


# ---------------------------------------------------------------------------
# P5 — Enhanced Voting portal JSON (electionresults.utah.gov), 2024-2026.
# Precinct grain from each ballot item's breakdownResults.
# ---------------------------------------------------------------------------
def parse_p5(election_slug, year, etype, keep_item=None, emit_summary=False):
    d = json.load(open(os.path.join(EV, election_slug, "ballot-items.json")))
    rows, recon = [], []
    import glob as _glob
    for it in d["data"]:
        name = it["name"][0]["text"].strip()
        if keep_item and not keep_item(name, it):
            continue
        bi = json.load(open(os.path.join(EV, election_slug, f"bi_{it['id']}.json")))
        vote_for = ""
        vf = bi.get("voteFor") or []
        if vf:
            m = re.search(r"(\d+)", vf[0]["text"])
            vote_for = m.group(1) if m else ""
        src = f"ev_api/{election_slug}"
        total_check = 0
        for br in bi.get("breakdownResults") or []:
            pname = br["precinct"]["name"][0]["text"].strip()
            for bo in br.get("ballotOptions") or []:
                cand = bo["name"][0]["text"].strip()
                votes = bo.get("voteCount")
                rows.append(row(year, etype, src, "Weber County", name,
                               vote_for, pname, cand,
                               votes if votes is not None else "",
                               votes is None))
                if votes:
                    total_check += votes
        summary_total = sum(bo.get("voteCount") or 0
                            for bo in bi["summaryResults"]["ballotOptions"])
        recon.append(dict(source_file=src, scope="electionwide", contest=name,
                          parsed_sum=total_check, printed_total=summary_total,
                          match=(total_check == summary_total)))
        if emit_summary:
            # election-wide certified totals as precinct='' rows (the portal's
            # summaryResults INCLUDE suppressed precincts' votes; the derived
            # by-contest layer prefers these over precinct sums)
            for bo in bi["summaryResults"]["ballotOptions"]:
                cand = bo["name"][0]["text"].strip()
                votes = bo.get("voteCount")
                rows.append(row(year, etype, src, "Weber County", name,
                                vote_for, "", cand,
                                votes if votes is not None else "",
                                votes is None))
    return rows, recon


def parse_pt(fname, year, etype):
    """Certified totals transcribed from IMAGE-ONLY signed canvass summaries
    (the 2022 general + 2023 bond Board-of-Canvassers PDFs have no text layer).
    Values come from certified_totals_transcribed.csv — tesseract OCR each
    digit-verified by direct visual reading of the rendered page (see
    VERIFICATION.md). Emitted as contest-grain rows (precinct='')."""
    rows = []
    path = os.path.join(HERE, "certified_totals_transcribed.csv")
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["source_file"] != fname:
                continue
            rows.append(row(int(r["year"]), r["election_type"], fname,
                            "Weber County", r["contest"], r["vote_for"], "",
                            r["candidate"], int(r["votes"]), False))
    return rows, []


# ---------------------------------------------------------------------------
# Build driver — the manifest of every normalized source.
# ---------------------------------------------------------------------------
COUNTY_KEEP = re.compile(
    r"^((REP |DEM )?COUNTY (COMM\b|COMMISSION|COMMISSIONER|ASSESSOR|ATTORNEY|"
    r"CLERK|RECORDER|SHERIFF|SURVEYOR|TREASURER)|"
    r"COMMISSIONER SEAT|Commissioner Seat|CLERK/AUDITOR$|WEBER LIBRARY BOND|"
    r"WEBER COUNTY JUSTICE CENTER BOND|BALLOT PROPOSITION 19)")
OVC_2024_QUESTIONS = {"OGDEN VALLEY CITY", "FORM OF GOVERNMENT OGDEN VALLEY CITY",
                      "CITY COUNCIL QUESTION"}


def keep_county(c):
    return bool(COUNTY_KEEP.match(c))


def keep_county_2024(c):
    return bool(COUNTY_KEEP.match(c)) or c in OVC_2024_QUESTIONS


MANIFEST = [
    # --- municipal odd-year canvasses (ALL contests kept; SLCo model) ---
    ("p3", "7dc173_42aefeefc8bf43f9a0e5ca43c77946a3.pdf", 2007, "municipal primary", "Weber County", None),
    ("p3", "7dc173_75aecd5191be40c68763fc99e13a3b45.pdf", 2007, "municipal general", "Weber County", None),
    ("p3", "7dc173_0357eebfbe23457f945e75debbd72387.pdf", 2011, "municipal primary", "Weber County", None),
    ("p3", "7dc173_8c4e7363ecaf4e658047382f40cbe07c.pdf", 2011, "municipal general", "Weber County", None),
    ("p3", "7dc173_50598a3c3a854e2f9c5d1c5439bb8808.pdf", 2013, "municipal general", "Weber County", None),
    ("p3", "7dc173_d0d4fc19d88f469191fe6355d8d95aab.pdf", 2015, "municipal primary", "Weber County", None),
    ("p3", "7dc173_3ab165a3f3d5495abc59146562df7ab7.pdf", 2015, "municipal general", "Weber County", None),
    ("p3", "7e3a53_dfa082bf8ece4fa59b962d928fe93aa7.pdf", 2017, "municipal primary", "Weber County", None),
    ("p3", "7e3a53_0c64e2aa8b964f81a183bb1fdbd64a17.pdf", 2017, "municipal general", "Weber County", None),
    ("p2", "7e3a53_23ef3f3f90864dfa9f4ddc93a9363215.pdf", 2019, "municipal general", "Weber County", None),
    ("p2", "7dc173_d768b44d1cba4863a7a271a2286e4944.pdf", 2021, "municipal primary", "Weber County", None),
    ("p2", "7dc173_05b2df57deb54c439e8964cd6184e90c.pdf", 2021, "municipal general", "Weber County", None),
    ("p1", "7e3a53_3364efea7ede4fb597486bf50a6e7ee8.pdf", 2023, "municipal primary", "Ogden City", None),
    ("p1", "7e3a53_e7ebd54543124bc9a93c0112efb71534.pdf", 2023, "municipal primary", "Roy City", None),
    ("p1", "7e3a53_db736b8b1f4f4a67bb7dc4418426230a.pdf", 2023, "municipal primary", "North Ogden City", None),
    ("p1", "7e3a53_693bb1b48d9b4a4bb9b727fb622e13be.pdf", 2023, "municipal primary", "Hooper City", None),
    ("p5s", "primary08122025", 2025, "municipal primary", None, None),  # EV canonical (only channel for 11 of 12 cities; OVC PDF = cross-check)
    ("p1", "92078f_dc2ffea70dfb409aa3f2b615a678de4b.pdf", 2025, "municipal general", "Weber County", None),
    ("p2", "92078f_ba3a3d05a36449399444d85e915efa14.pdf", 2025, "municipal general", "Weber County", None),   # official canvass summary (certified totals incl. suppressed precincts)
    ("p2", "7e3a53_fcceb6a6b8e343bf89fa0ab40be82b3d.pdf", 2023, "municipal primary", "Ogden City", None),
    ("p2", "7e3a53_78a11a0b224041319e8dcfbaa391bdf8.pdf", 2023, "municipal primary", "Roy City", None),
    ("p2", "7e3a53_6386b6b5d1e7436786c79677b6b4329d.pdf", 2023, "municipal primary", "North Ogden City", None),
    ("p2", "7e3a53_f138c1f1591a4eb2a59eb245cd167a0b.pdf", 2023, "municipal primary", "Hooper City", None),
    # --- county-office contests from even-year cycles + specials ---
    ("p3", "7dc173_5547b20a2256488fbb2f30d2b1102e7a.pdf", 2006, "general", "Weber County", keep_county),
    ("p3", "7dc173_dde1613fbfc743c994e963669ec9137c.pdf", 2008, "general", "Weber County", keep_county),
    ("p3", "7dc173_28650bc4d8ee4c0b9b232289bac454e1.pdf", 2010, "general", "Weber County", keep_county),
    ("p3", "7dc173_6bba5a4f176542c38e5ca332b1bbc899.pdf", 2012, "general", "Weber County", keep_county),
    ("p3", "7dc173_2a98db8543bc49c69cd91da6722f6b90.pdf", 2013, "special", "Weber County", keep_county),
    ("p3", "7dc173_9f6a145759b446e7a81286d1a5aac149.pdf", 2014, "general", "Weber County", keep_county),
    ("p3", "7dc173_12e1f107e8a34c6499478fb4f63949f1.pdf", 2016, "primary", "Weber County", keep_county),
    ("p3", "7e3a53_73d852c0d26f45028c8e2a34e747701e.pdf", 2016, "general", "Weber County", keep_county),
    ("p2", "7dc173_5e828623651a4122935479755d0e1d31.pdf", 2018, "primary", "Weber County", keep_county),
    ("p4", "7dc173_a00ce1d87e7043caa17d49e189b2dd3d.csv", 2018, "general", "Weber County", keep_county),
    ("p2", "7e3a53_1698f33fed1943edb35c3b69e5e4c813.pdf", 2018, "general", "Weber County", keep_county),   # Nov 20 Final summary (certified)
    ("p2", "7dc173_3149b34b82ff4727b18e13cd95dbe438.pdf", 2020, "primary", "Weber County", keep_county),
    ("p2", "7dc173_3fbd87144c1e47ca8ba5fc235501eadb.pdf", 2020, "general", "Weber County", keep_county),   # official summary (certified)
    ("p2", "7e3a53_203d49db31d8445fb0eaff40bb511b4a.pdf", 2022, "primary", "Weber County", keep_county),   # Final Canvass summary
    ("p1", "92078f_c4085e1a640b4548b65500d49f7affaf.pdf", 2020, "general", "Weber County", keep_county),
    ("p1", "92078f_afc450eab79548f0be83ae4dc3a358b5.pdf", 2022, "primary", "Weber County", keep_county),
    ("p1", "92078f_a083bb8c60e042c6bc102be274f3695d.pdf", 2022, "general", "Weber County", keep_county),
    ("pt", "7e3a53_847d93ca04b748b19764dfe9d4f2e2a0.pdf", 2022, "general", "Weber County", None),
    ("p1", "92078f_def2370870034f6e9ad3b933d2f2a383.pdf", 2023, "general", "Weber County", keep_county),
    ("pt", "92078f_1fb5ef99870440ad9f74b83a435699ab.pdf", 2023, "general", "Weber County", None),
    ("p5", "general11052024", 2024, "general", None, keep_county_2024),
    ("p2", "92078f_d54e5cd989d443b3942a0c9b48eab24b.pdf", 2024, "general", "Weber County", keep_county_2024),  # official canvass summary
    ("p5", "primary06232026", 2026, "primary", None, keep_county),
    ("p2", "92078f_18540fc578ac4c778574b54d6a8908dd.pdf", 2026, "primary", "Weber County", keep_county),       # official canvass summary
]


def main():
    all_rows, all_recon = [], []
    for kind, src, year, etype, sheet, keep in MANIFEST:
        if kind == "p1":
            r, rc = parse_p1(src, year, etype, sheet, keep_contest=keep)
        elif kind == "p2":
            r, rc = parse_p2(src, year, etype, sheet, keep_contest=keep)
        elif kind == "p3":
            r, rc = parse_p3(src, year, etype, sheet, keep_contest=keep)
        elif kind == "p4":
            r, rc = parse_p4(src, year, etype, keep)
        elif kind == "p5":
            r, rc = parse_p5(src, year, etype,
                             keep_item=(lambda n, it, k=keep: k(n)) if keep else None)
        elif kind == "p5s":
            r, rc = parse_p5(src, year, etype, emit_summary=True)
        elif kind == "pt":
            r, rc = parse_pt(src, year, etype)
        print(f"{year} {etype:18s} {src[:44]:46s} {len(r):6d} rows")
        all_rows.extend(r)
        all_recon.extend(rc)

    all_rows.sort(key=lambda x: (x["year"], x["election_type"], x["source_file"],
                                 x["contest"], x["precinct"], x["candidate"]))
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for x in all_rows:
            x = dict(x)
            x["suppressed"] = "True" if x["suppressed"] else "False"
            w.writerow(x)
    with open(RECON_OUT, "w", newline="", encoding="utf-8") as f:
        cols = ["source_file", "scope", "contest", "parsed_sum", "printed_total",
                "match"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for x in all_recon:
            w.writerow({c: x.get(c, "") for c in cols})
    n_sup = sum(1 for x in all_rows if x["suppressed"] in (True, "True"))
    print(f"\nWrote {OUT}: {len(all_rows)} rows ({n_sup} suppressed cells)")
    print(f"Wrote {RECON_OUT}: {len(all_recon)} reconciliation checks")


if __name__ == "__main__":
    main()
