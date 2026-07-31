#!/usr/bin/env python3
"""Build South Jordan City (Salt Lake County, UT) election_results.

South Jordan is a **Council-Mayor** city: **5 council DISTRICTS (1-5) + a separately
elected Mayor** (citywide). 4-yr staggered terms. As the contests appear in the county
Statement-of-Votes-Cast (SOVC) files, the stagger is:

  * Cycle A (Mayor + District 3 + District 5): 2009, 2013, 2017, 2021, 2025
  * Cycle B (Districts 1, 2, 4):                2007, 2011, 2015, 2019, 2023

(2007 is Cycle B but the county labelled the seats "SOUTH JORDAN CITY COUNCIL 1/2/4"; by
2009 the label became "...COUNCIL DISTRICT N".)  Mayor sits only on the A cycle.

SOURCES  (Salt Lake County Clerk, mirrored locally in ~/Desktop/slco-election-archive)
--------------------------------------------------------------------------------------
Two provenance layers, both retained under raw/:

1. raw/municipal_results_long_south_jordan.csv
      The archive's own canonical SOVC normalization (built by the archive's
      scripts/normalize_sovc.py from the raw spreadsheets; each row carries the true
      source_file + sheet).  Filtered here to South Jordan.  Precinct- and
      vote-method-level; sums cleanly to contest totals with ZERO suppression for
      2007/2009/2013/2015/2017 (+ primaries) and for the 2023 & 2025 generals.  These
      years are consumed straight from this slice.

2. raw/sovc/*.xlsx  (the true county SOVC spreadsheets)
      Re-parsed directly for the THREE contests the archive's parsed layer does not
      deliver cleanly:
        * 2011 general (Districts 1/2/4) -- ABSENT from the parsed layer (the archive's
          normalizer skipped South Jordan's 2011-general sheets). RECOVERED from raw.
        * 2019 general (Districts 1/2/4) -- present in the parsed layer only under the
          raw sheet code "SJD Council N" (the normalizer keyed the contest off the sheet
          name, so a '%SOUTH JORDAN%' filter misses it).  RECOVERED from raw for faithful
          district numbers, candidate names and precinct totals.
        * 2021 general (Mayor/D3/D5) -- present in the parsed layer but 198/246 rows are
          privacy-SUPPRESSED at the In-Person/Vote-By-Mail method split, which destroys
          the precinct totals.  RE-PARSED from raw, whose per-precinct 'Total' sub-rows
          are NOT suppressed.

2019 municipal PRIMARY: the raw 2019 primary SOVC contains NO South Jordan sheet (checked)
-> South Jordan held no 2019 primary (each Cycle-B district drew <=2 candidates). Logged,
not fabricated.

Reproducible:  python3 clean_elections.py            (reads raw/, writes the 3 CSVs)
               python3 clean_elections.py --report    (prints a per-race summary)
"""
import os, re, csv, sys, openpyxl

OUT = os.path.dirname(os.path.abspath(__file__))
# The long-format canvass is consumed DIRECTLY from the Salt Lake County canonical
# (salt_lake_county/elections/slco_municipal_results_long.csv) — the county-clerk SOVC held
# once at the level where it originates. The old per-city redundant copy
# (raw/municipal_results_long_south_jordan.csv) was retired 2026-07-19 (re-point verified
# byte-identical). The raw SOVC spreadsheets under raw/sovc/ remain the source for the three
# contests the long file does not deliver cleanly for South Jordan (2011/2019/2021 general).
SLICE = os.path.join(OUT, '..', '..', 'salt_lake_county', 'elections',
                     'slco_municipal_results_long.csv')
SOVC = os.path.join(OUT, 'raw', 'sovc')
REPORT = '--report' in sys.argv


# --------------------------------------------------------------------------- helpers
def g(r, j):
    return r[j] if (r is not None and j < len(r)) else None


def norm_name(s):
    """Normalize a candidate name ALONGSIDE the verbatim value (never overwrites raw):
    collapse whitespace, strip the (NP) non-partisan tag, canonicalize write-ins."""
    s = re.sub(r'\s+', ' ', str(s).replace('\n', ' ')).strip()
    s = s.lstrip('*').strip()                               # drop registered-write-in mark
    s = re.sub(r'\s*\(\s*(?:NP|NON)\s*\)', '', s, flags=re.I)  # strip (NP)/(NON) non-partisan tag
    s = re.sub(r'\bUNRESOLVED\s+WRITE[- ]?IN\b', 'Write-in (unresolved)', s, flags=re.I)
    s = re.sub(r'\bWRITE[- ]?IN\b', 'Write-in', s, flags=re.I)
    return re.sub(r'\s+', ' ', s).strip().strip('"').strip()


def to_int(v):
    return int(v) if isinstance(v, (int, float)) else None


# ---- contest canonicalization ----------------------------------------------
def canon(label):
    """Map any county contest label to (office, district, canonical_contest)."""
    U = label.upper()
    if 'MAYOR' in U:
        return ('Mayor', '', 'South Jordan City Mayor')
    m = re.search(r'(\d+)\s*$', U.strip()) or re.search(r'DIST(?:RICT)?\s*(\d+)', U)
    m = re.search(r'DIST(?:RICT)?\s*(\d+)', U) or re.search(r'(\d+)\s*$', U.strip())
    d = m.group(1) if m else '?'
    return ('Council', d, f'South Jordan City Council District {d}')


def is_sj_council_or_mayor(label):
    U = label.upper()
    if 'JORDAN' not in U or 'SOUTH' not in U and not U.startswith('SJD'):
        # allow the raw SJD sheet code
        if not U.startswith('SJD'):
            return False
    if 'MAYOR' in U:
        return True
    return bool(re.search(r'(COUNCIL|COUN|CNCL)', U) or U.startswith('SJD'))


# --------------------------------------------------------------------------- containers
# key = (year, election_type, contest)  ->  record dict
RECORDS = {}


def rec(year, etype, label, source_file):
    office, district, contest = canon(label)
    k = (year, etype, contest)
    if k not in RECORDS:
        RECORDS[k] = dict(year=year, election_type=etype, office=office,
                          district=district, contest=contest,
                          cand={}, per={}, reg={}, ballots={},
                          suppressed_any=False, source_file=source_file,
                          verbatim=label)
    return RECORDS[k]


def add_vote(R, precinct, cand, votes):
    R['cand'][cand] = R['cand'].get(cand, 0) + (votes or 0)
    R['per'].setdefault(precinct, {})
    cur = R['per'][precinct].get(cand)
    if votes is None:
        R['suppressed_any'] = True
        if cand not in R['per'][precinct]:
            R['per'][precinct][cand] = None
    else:
        R['per'][precinct][cand] = (cur or 0) + votes if isinstance(cur, int) else votes


# --------------------------------------------------------------------------- (1) archive slice
SLICE_SKIP_YEARS = {2021}          # 2021 general parsed from raw instead (suppression)
SLICE_SKIP_GEN_YEARS = {2011}      # 2011 general parsed from raw (the county canonical now
                                   # carries it under "South Jordan City Coun N" — skip to
                                   # avoid double-counting the raw-parsed recovery)


def load_slice():
    with open(SLICE, newline='') as fh:
        for row in csv.DictReader(fh):
            year = int(float(row['year']))
            contest_raw = row['contest']
            if year in SLICE_SKIP_YEARS:
                continue
            if year in SLICE_SKIP_GEN_YEARS and row['election_type'] == 'municipal general':
                continue           # raw parser covers this general (avoid double-count)
            if contest_raw.upper().startswith('SJD'):
                continue           # 2019 SJD rows -> parsed from raw instead
            if not is_sj_council_or_mayor(contest_raw):
                continue
            R = rec(year, row['election_type'], contest_raw, row['source_file'])
            prec = row['precinct'].strip()
            if prec == 'Cumulative':
                continue           # workbook rollup label, never a precinct (county canonical convention)
            cand = norm_name(row['candidate'])
            v = row['votes'].strip()
            votes = int(float(v)) if v not in ('', 'nan') else None
            supp = row['suppressed'].strip().lower() == 'true'
            add_vote(R, prec, cand, None if (supp or votes is None) else votes)
            reg = row['registered_voters'].strip()
            tc = row['times_cast'].strip()
            if reg not in ('', 'nan'):
                R['reg'][prec] = max(R['reg'].get(prec, 0), int(float(reg)))
            if tc not in ('', 'nan'):
                R['ballots'][prec] = max(R['ballots'].get(prec, 0), int(float(tc)))


# --------------------------------------------------------------------------- (2) raw parsers
def parse_2011_general(path):
    """2011 general layout: header row has 'Precinct'/'Type'/'Reg. Voters'/'Cards Cast'/
    'Total Votes' then candidate name columns (each followed by an empty-header pct col);
    each precinct has method sub-rows and a 'Total' Type row carrying the real count."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    PR = re.compile(r'SJD\d+')
    for sh in wb.sheetnames:
        if not sh.lower().startswith('south jordan'):
            continue
        ws = wb[sh]
        rows = [list(x) for x in ws.iter_rows(values_only=True)]
        hi = next(i for i, r in enumerate(rows)
                  if any(str(g(r, j)).strip() == 'Precinct' for j in range(len(r))))
        hdr = rows[hi]
        pj = next(j for j in range(len(hdr)) if str(g(hdr, j)).strip() == 'Precinct')
        typej = pj + 1
        regj = next((j for j in range(len(hdr))
                     if 'Reg' in str(g(hdr, j))), None)
        cardj = next((j for j in range(len(hdr))
                      if 'Cards Cast' in str(g(hdr, j))), None)
        tvj = next(j for j in range(len(hdr)) if str(g(hdr, j)).strip() == 'Total Votes')
        cand_cols = {j: norm_name(g(hdr, j)) for j in range(tvj + 1, len(hdr))
                     if g(hdr, j) not in (None, '') and str(g(hdr, j)).strip()}
        label = None
        for r in rows[:hi]:
            for c in r:
                if c and 'south jordan' in str(c).lower():
                    label = str(c)
        # district from sheet name "South Jordan City Coun N"
        dm = re.search(r'(\d+)\s*$', sh.strip())
        label = f'SOUTH JORDAN CITY COUNCIL {dm.group(1)}' if dm else sh
        R = rec(2011, 'municipal general', label, os.path.basename(path))
        for r in rows[hi + 1:]:
            if str(g(r, typej)).strip() == 'Total':
                prec = str(g(r, pj)).strip()
                if not PR.fullmatch(prec):
                    continue
                for j, name in cand_cols.items():
                    add_vote(R, prec, name, to_int(g(r, j)))
                if regj is not None and to_int(g(r, regj)) is not None:
                    R['reg'][prec] = to_int(g(r, regj))
                if cardj is not None and to_int(g(r, cardj)) is not None:
                    R['ballots'][prec] = to_int(g(r, cardj))


def parse_2019_general(path):
    """2019 'Family-A' wide crosstab: A2 candidate names sparse across a header row;
    the sub-header row marks each candidate's total with 'Total Votes'; precinct rows
    (col0 == SJD###) follow, col1 == Registered Voters."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    PR = re.compile(r'SJD\d+')
    for sh in wb.sheetnames:
        if not sh.upper().startswith('SJD'):
            continue
        ws = wb[sh]
        rows = [list(x) for x in ws.iter_rows(values_only=True)]
        name_row, sub_row = rows[1], rows[2]
        cand_cols = [(j, norm_name(name_row[j])) for j in range(len(name_row))
                     if name_row[j] not in (None, '')]
        tv_cols = [j for j, v in enumerate(sub_row) if str(v).strip() == 'Total Votes']
        cands = [n for _, n in cand_cols]
        cand_tv = dict(zip(cands, tv_cols))
        regj = next((j for j, v in enumerate(sub_row)
                     if 'Registered' in str(v)), None)
        dm = re.search(r'(\d+)\s*$', sh.strip())
        label = f'SOUTH JORDAN CITY COUNCIL DISTRICT {dm.group(1)}'
        R = rec(2019, 'municipal general', label, os.path.basename(path))
        for r in rows[3:]:
            c0 = g(r, 0)
            if isinstance(c0, str) and PR.fullmatch(c0.strip()):
                prec = c0.strip()
                for c, tvj in cand_tv.items():
                    add_vote(R, prec, c, to_int(g(r, tvj)))
                if regj is not None and to_int(g(r, regj)) is not None:
                    R['reg'][prec] = to_int(g(r, regj))


NONCAND = {'TIMES CAST', 'REGISTERED VOTERS', 'REGISTERED', 'TOTAL VOTES', 'UNDERVOTES',
           'OVERVOTES', 'PRECINCT', 'TOTAL', 'CONTINUING BALLOTS TOTAL', 'CARDS CAST',
           'TYPE'}


def parse_2021_general(path, sheets):
    """2021 columnar: a second 'Precinct' marker precedes candidate columns; each
    precinct has In Person / Vote By Mail method sub-rows (small counts '****'
    suppressed) and a 'Total' sub-row with the UN-suppressed precinct count."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    PR = re.compile(r'SJD\d+')
    for sh in sheets:
        ws = wb[sh]
        rows = [list(x) for x in ws.iter_rows(values_only=True)]
        title = next(str(g(r, 0)) for r in rows[:3] if g(r, 0) and 'JORDAN' in str(g(r, 0)).upper())
        hi = next(i for i, r in enumerate(rows) if str(g(r, 0)).strip() == 'Precinct')
        hdr = rows[hi]
        # find the Times Cast / Registered columns (first block)
        tcj = next((j for j in range(len(hdr)) if 'Times Cast' in str(g(hdr, j))), None)
        rgj = next((j for j in range(len(hdr)) if 'Registered' in str(g(hdr, j))), None)
        cand_cols = {}
        for j, c in enumerate(hdr):
            if c in (None, ''):
                continue
            L = re.sub(r'\s+', ' ', str(c).replace('\n', ' ')).strip().upper()
            if L not in NONCAND and not L.endswith('%'):
                cand_cols[j] = norm_name(c)
        # keep only the true candidate value columns (they carry a numeric Total below);
        # drop the pct columns (their header is blank so already excluded)
        R = rec(2021, 'municipal general', re.sub(r'\s*\(Vote.*', '', title).strip(),
                os.path.basename(path))
        cur = None
        for r in rows[hi + 1:]:
            c0 = str(g(r, 0)).strip() if g(r, 0) is not None else ''
            if PR.fullmatch(c0):
                cur = c0
                R['per'].setdefault(cur, {})
            elif c0 == 'Total' and cur is not None:
                for j, name in cand_cols.items():
                    add_vote(R, cur, name, to_int(g(r, j)))
                if tcj is not None and to_int(g(r, tcj)) is not None:
                    R['ballots'][cur] = to_int(g(r, tcj))
                if rgj is not None and to_int(g(r, rgj)) is not None:
                    R['reg'][cur] = to_int(g(r, rgj))
                cur = None


# --------------------------------------------------------------------------- run loaders
load_slice()
parse_2011_general(os.path.join(SOVC, '2011-11-08-municipal-general-sovc.xlsx'))
parse_2019_general(os.path.join(SOVC, '2019-11-05-general-election-sovc.xlsx'))
parse_2021_general(os.path.join(SOVC, '2021-11-02-general-election-sovc.xlsx'),
                   ['Sheet39', 'Sheet40', 'Sheet41'])


# --------------------------------------------------------------------------- compute + write
def real_cands(items):
    return [(n, v) for n, v in items
            if not (n.startswith('Write-in') and (v or 0) == 0)]


races, by_cand, by_precinct = [], [], []
for k in sorted(RECORDS, key=lambda x: (x[0], x[1], x[2])):
    R = RECORDS[k]
    items = sorted(R['cand'].items(), key=lambda kv: (-(kv[1] or 0), kv[0]))
    total = sum(v or 0 for v in R['cand'].values())
    rc = real_cands(items)
    winner, wv = items[0] if items else ('', 0)
    runner, rv = (items[1] if len(items) > 1 else ('', 0))
    margin = (wv or 0) - (rv or 0)
    reg_total = sum(R['reg'].values()) if R['reg'] else ''
    ballots_total = sum(R['ballots'].values()) if R['ballots'] else ''
    turnout = (round(100 * ballots_total / reg_total, 2)
               if (isinstance(ballots_total, int) and isinstance(reg_total, int) and reg_total) else '')
    races.append(dict(
        year=R['year'], election_type=R['election_type'], office=R['office'],
        district=R['district'], contest=R['contest'], contest_verbatim=R['verbatim'],
        n_seats=1, n_candidates=len(rc), voting_method='plurality',
        total_votes=total, total_first_choice_votes='', winner=winner, winner_votes=wv,
        winner_pct=round(100 * (wv or 0) / total, 2) if total else 0,
        runner_up=runner, runner_up_votes=rv,
        margin_votes=margin, margin_pct=round(100 * margin / total, 2) if total else 0,
        registered_voters=reg_total, ballots_cast=ballots_total, turnout_pct=turnout,
        uncontested='True' if len(rc) <= 1 else 'False',
        suppressed_precincts='True' if R['suppressed_any'] else 'False',
        note='', source_file=R['source_file']))
    for rank, (name, v) in enumerate(items, 1):
        by_cand.append(dict(
            year=R['year'], election_type=R['election_type'], office=R['office'],
            district=R['district'], contest=R['contest'], candidate=name,
            votes=v or 0, pct=round(100 * (v or 0) / total, 2) if total else 0,
            rank=rank, is_winner='True' if rank == 1 and len(rc) >= 1 else 'False'))
    for prec in sorted(R['per']):
        for name, v in R['per'][prec].items():
            by_precinct.append(dict(
                year=R['year'], election_type=R['election_type'], office=R['office'],
                district=R['district'], contest=R['contest'], precinct=prec,
                candidate=name, votes='' if v is None else v,
                suppressed='True' if v is None else 'False'))


def writecsv(name, rows, cols):
    with open(os.path.join(OUT, name), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


writecsv('south_jordan_races.csv', races,
         ['year', 'election_type', 'office', 'district', 'contest', 'contest_verbatim',
          'n_seats', 'n_candidates', 'voting_method', 'total_votes',
          'total_first_choice_votes', 'winner',
          'winner_votes', 'winner_pct', 'runner_up', 'runner_up_votes', 'margin_votes',
          'margin_pct', 'registered_voters', 'ballots_cast', 'turnout_pct',
          'uncontested', 'suppressed_precincts', 'note', 'source_file'])
writecsv('south_jordan_results_by_candidate.csv', by_cand,
         ['year', 'election_type', 'office', 'district', 'contest', 'candidate',
          'votes', 'pct', 'rank', 'is_winner'])
writecsv('south_jordan_results_by_precinct.csv', by_precinct,
         ['year', 'election_type', 'office', 'district', 'contest', 'precinct',
          'candidate', 'votes', 'suppressed'])

# --------------------------------------------------------------------------- report
gen = [r for r in races if r['election_type'] == 'municipal general']
pri = [r for r in races if r['election_type'] == 'municipal primary']
print(f"races: {len(races)}  (general {len(gen)}, primary {len(pri)})")
print(f"by_candidate rows: {len(by_cand)}   by_precinct rows: {len(by_precinct)}")
if REPORT:
    for r in sorted(races, key=lambda x: (x['year'], x['election_type'], x['contest'])):
        tag = 'PRIMARY ' if r['election_type'] == 'municipal primary' else ''
        unc = ' [UNCONTESTED]' if r['uncontested'] == 'True' else ''
        sup = ' [suppressed-precincts]' if r['suppressed_precincts'] == 'True' else ''
        to = f" turnout {r['turnout_pct']}%" if r['turnout_pct'] != '' else ''
        print(f"  {r['year']} {tag}{r['contest']:34s} n={r['n_candidates']} "
              f"WIN {r['winner']} {r['winner_votes']} ({r['winner_pct']}%) vs "
              f"{r['runner_up']} {r['runner_up_votes']}  margin {r['margin_votes']} "
              f"[tot {r['total_votes']}{to}]{unc}{sup}")
