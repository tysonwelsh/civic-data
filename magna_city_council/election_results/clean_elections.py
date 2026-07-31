#!/usr/bin/env python3
"""Build Magna City (Salt Lake County, UT) election_results.

Magna is a Salt Lake County **metro township (2017-2024) -> CITY (2024-05-01)**. Its
council is elected by **5 single-member DISTRICTS (1-5)**; from the **2025** cycle there is
also a separately-elected citywide **executive Mayor** (Mick Sudbury; the metro-township era
had NO separate mayor - the 5-member council elected its own Chair). All contests are
plurality, single-member (vote-for-1). Non-partisan (`(NP)`/`(NON)` tags stripped alongside
the verbatim name).

TERM STAGGER (as the county SOVC files carry it):
  * Cycle A (Districts 2 & 4, + Mayor from 2025):  2017, 2021, 2025
  * Cycle B (Districts 1, 3 & 5):                   2019, 2023(*)
  * 2016 FOUNDING general seated ALL FIVE districts (metro-township incorporation).

(*) 2023 gap: the Salt Lake County SOVC archive carries NO Magna council district race for
2023 (only MAGNA WATER DISTRICT, a decoy). Utah cancels uncontested municipal races, so the
Cycle-B incumbents (D1 Prokopis, D3, D5 Pierce) most likely drew no opponent and no ballot
contest was held/tabulated. Recorded as an honest gap in CLAUDE.md - NOT fabricated.

DECOYS EXCLUDED (never council/mayor seats): MAGNA WATER DISTRICT / MAGNA WATER BOARD OF
TRUSTEES (all variants; the Magna Water District special district), MAGNA MSD (2015
MSD-formation ballot question), MAGNA METRO TOWNSHIP-CITY (2015 incorporation ballot
question). ~95% of "magna" rows in the county file are these.

SOURCES (Salt Lake County Clerk; local mirror ~/Desktop/slco-election-archive), retained
under raw/:

 1. raw/municipal_results_long_magna.csv
      The archive's canonical SOVC normalization, filtered to the 7 genuine Magna
      council/mayor contests (precinct + vote-method level; each row carries source_file +
      sheet). Consumed straight for **2017** (clean, 0 suppression) and **2025** (method
      'ALL', clean).

 2. raw/sovc/*.xlsx  (true county SOVC spreadsheets) re-parsed directly for:
      * 2016 general (D1-D5) -- the founding election; NOT in the parsed slice. Recovered
        from 2016-11-08-general-election-sovc.xlsx (crosstab with per-precinct 'Total' rows).
      * 2019 general (D1/D3/D5) -- present only under raw sheet code 'MAG Council N' (a
        %MAGNA CITY/METRO% contest-string filter misses it). Recovered from
        2019-11-05-general-election-sovc.xlsx. All three uncontested.
      * 2021 general (D2/D4) -- present in the slice but privacy-SUPPRESSED (**** ) at the
        In-Person/Vote-By-Mail method split (14/30 rows), destroying precinct totals.
        Re-parsed from 2021-11-02-general-election-sovc.xlsx (Sheet59/60), whose per-precinct
        'Total' sub-rows are NOT suppressed.

Reproducible:  python3 clean_elections.py            (reads raw/, writes the 3 CSVs)
               python3 clean_elections.py --report    (+ per-race summary)
"""
import os, re, csv, sys, zipfile, io, openpyxl

OUT = os.path.dirname(os.path.abspath(__file__))
SLICE = os.path.join(OUT, 'raw', 'municipal_results_long_magna.csv')
SOVC = os.path.join(OUT, 'raw', 'sovc')
REPORT = '--report' in sys.argv
PR = re.compile(r'MAG\w+')                       # Magna precinct id (MAG001, MAG901, ...)


# --------------------------------------------------------------------------- helpers
def g(r, j):
    return r[j] if (r is not None and j is not None and j < len(r)) else None


def norm_name(s):
    """Normalize a candidate name ALONGSIDE the verbatim value (never overwrites raw)."""
    s = re.sub(r'\s+', ' ', str(s).replace('\n', ' ')).strip()
    s = s.lstrip('*').strip()
    s = re.sub(r'\s*\(\s*(?:NP|NON|NO)\s*\)', '', s, flags=re.I)      # (NP)/(NON) tag
    s = re.sub(r'\bUNRESOLVED\s+WRITE[- ]?IN\b', 'Write-in (unresolved)', s, flags=re.I)
    s = re.sub(r'\bWRITE[- ]?IN\b', 'Write-in', s, flags=re.I)
    return re.sub(r'\s+', ' ', s).strip().strip('"').strip()


def to_int(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return int(v)
    if isinstance(v, str):
        t = v.strip().replace(',', '')
        if re.fullmatch(r'\d+', t):
            return int(t)
    return None


# ---- contest canonicalization ----------------------------------------------
def canon(label):
    """Map any county Magna contest label to (office, district, canonical_contest)."""
    U = label.upper()
    if 'MAYOR' in U:
        return ('Mayor', '', 'Magna City Mayor')
    m = re.search(r'DIST(?:RICT)?\s*#?\s*(\d+)', U) or re.search(r'CNCL\s*#?\s*(\d+)', U) \
        or re.search(r'COUNCIL\s*#?\s*(\d+)', U) or re.search(r'#\s*(\d+)', U) \
        or re.search(r'(\d+)\s*$', U.strip())
    d = m.group(1) if m else '?'
    return ('Council', d, f'Magna City Council District {d}')


# --------------------------------------------------------------------------- containers
RECORDS = {}                                     # (year, etype, contest) -> record


def rec(year, etype, label, source_file):
    office, district, contest = canon(label)
    k = (year, etype, contest)
    if k not in RECORDS:
        RECORDS[k] = dict(year=year, election_type=etype, office=office,
                          district=district, contest=contest,
                          cand={}, per={}, reg={}, ballots={},
                          suppressed_any=False, source_file=source_file, verbatim=label)
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
SLICE_SKIP_YEARS = {2021}                        # 2021 re-parsed from raw (suppression)


def load_slice():
    with open(SLICE, newline='') as fh:
        for row in csv.DictReader(fh):
            year = int(float(row['year']))
            if year in SLICE_SKIP_YEARS:
                continue
            R = rec(year, row['election_type'], row['contest'], row['source_file'])
            prec = row['precinct'].strip()
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


# --------------------------------------------------------------------------- (2a) 2016 founding
def parse_2016_general(path):
    """2016 crosstab (one sheet per district 'MAGNA METRO TOWNSHIP CNCL #N'): a header row
    carries Precinct/Type/Reg. Voters/Cards Cast/Total Votes then candidate name columns
    (each followed by an empty-header pct column). Each precinct has method sub-rows plus a
    'Total' Type row that carries the real precinct count."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    for sh in wb.sheetnames:
        if not sh.upper().startswith('MAGNA METRO TOWNSHIP CNCL'):
            continue
        ws = wb[sh]
        rows = [list(x) for x in ws.iter_rows(values_only=True)]
        hi = next(i for i, r in enumerate(rows)
                  if any(str(g(r, j)).strip() == 'Precinct' for j in range(len(r))))
        hdr = rows[hi]
        pj = next(j for j in range(len(hdr)) if str(g(hdr, j)).strip() == 'Precinct')
        typej = pj + 1
        regj = next((j for j in range(len(hdr)) if 'Reg' in str(g(hdr, j))), None)
        cardj = next((j for j in range(len(hdr)) if 'Cards Cast' in str(g(hdr, j))), None)
        tvj = next(j for j in range(len(hdr)) if str(g(hdr, j)).strip() == 'Total Votes')
        cand_cols = {j: norm_name(g(hdr, j)) for j in range(tvj + 1, len(hdr))
                     if g(hdr, j) not in (None, '') and str(g(hdr, j)).strip()}
        dm = re.search(r'#\s*(\d+)', sh)
        label = f'MAGNA METRO TOWNSHIP CNCL #{dm.group(1)}' if dm else sh
        R = rec(2016, 'municipal general', label, os.path.basename(path))
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


# --------------------------------------------------------------------------- (2b) 2019 D1/D3/D5
def parse_2019_general(path):
    """2019 'MAG Council N' sheets: row1 candidate name(s) sparse across the header; row2 is
    the sub-header (Precinct, Registered Voters, method cols, 'Total Votes', 'Total'); precinct
    rows (col0 == MAG###) follow. All three 2019 Magna races are uncontested (one candidate)."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    for sh in wb.sheetnames:
        if not sh.upper().startswith('MAG COUNCIL'):
            continue
        ws = wb[sh]
        rows = [list(x) for x in ws.iter_rows(values_only=True)]
        name_row, sub_row = rows[1], rows[2]
        cand_cols = [(j, norm_name(name_row[j])) for j in range(len(name_row))
                     if name_row[j] not in (None, '')]
        tv_cols = [j for j, v in enumerate(sub_row) if str(v).strip() == 'Total Votes']
        cand_tv = dict(zip([n for _, n in cand_cols], tv_cols))
        regj = next((j for j, v in enumerate(sub_row) if 'Registered' in str(v)), None)
        dm = re.search(r'(\d+)\s*$', sh.strip())
        label = f'MAGNA METRO TOWNSHIP COUNCIL DISTRICT {dm.group(1)}'
        R = rec(2019, 'municipal general', label, os.path.basename(path))
        for r in rows[3:]:
            c0 = g(r, 0)
            if isinstance(c0, str) and PR.fullmatch(c0.strip()):
                prec = c0.strip()
                for c, tvj in cand_tv.items():
                    add_vote(R, prec, c, to_int(g(r, tvj)))
                if regj is not None and to_int(g(r, regj)) is not None:
                    R['reg'][prec] = to_int(g(r, regj))


# --------------------------------------------------------------------------- (2c) 2021 D2/D4
NONCAND = {'TIMES CAST', 'REGISTERED VOTERS', 'REGISTERED', 'REGISTERED VOTE', 'TOTAL VOTES',
           'UNDERVOTES', 'OVERVOTES', 'PRECINCT', 'TOTAL', 'CARDS CAST', 'TYPE'}


def parse_2021_general(path, sheets):
    """2021 columnar: a second 'Precinct' block precedes candidate columns; each precinct has
    In Person / Vote By Mail method sub-rows (small counts '****' suppressed) and a 'Total'
    sub-row with the UN-suppressed precinct count + Times Cast + Registered."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    for sh in sheets:
        ws = wb[sh]
        rows = [list(x) for x in ws.iter_rows(values_only=True)]
        title = next(str(g(r, 0)) for r in rows[:3] if g(r, 0) and 'MAGNA' in str(g(r, 0)).upper())
        hi = next(i for i, r in enumerate(rows) if str(g(r, 0)).strip() == 'Precinct')
        hdr = rows[hi]
        tcj = next((j for j in range(len(hdr)) if 'Times Cast' in str(g(hdr, j))), None)
        rgj = next((j for j in range(len(hdr)) if 'Registered' in str(g(hdr, j))), None)
        cand_cols = {}
        for j, c in enumerate(hdr):
            if c in (None, ''):
                continue
            L = re.sub(r'\s+', ' ', str(c).replace('\n', ' ')).strip().upper()
            if L not in NONCAND and not L.endswith('%'):
                cand_cols[j] = norm_name(c)
        label = re.sub(r'\s*\(Vote.*', '', title).strip()
        R = rec(2021, 'municipal general', label, os.path.basename(path))
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
parse_2016_general(os.path.join(SOVC, '2016-11-08-general-election-sovc.xlsx'))
parse_2019_general(os.path.join(SOVC, '2019-11-05-general-election-sovc.xlsx'))
parse_2021_general(os.path.join(SOVC, '2021-11-02-general-election-sovc.xlsx'),
                   ['Sheet59', 'Sheet60'])


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


writecsv('magna_races.csv', races,
         ['year', 'election_type', 'office', 'district', 'contest', 'contest_verbatim',
          'n_seats', 'n_candidates', 'voting_method', 'total_votes',
          'total_first_choice_votes', 'winner', 'winner_votes', 'winner_pct', 'runner_up',
          'runner_up_votes', 'margin_votes', 'margin_pct', 'registered_voters',
          'ballots_cast', 'turnout_pct', 'uncontested', 'suppressed_precincts', 'note',
          'source_file'])
writecsv('magna_results_by_candidate.csv', by_cand,
         ['year', 'election_type', 'office', 'district', 'contest', 'candidate',
          'votes', 'pct', 'rank', 'is_winner'])
writecsv('magna_results_by_precinct.csv', by_precinct,
         ['year', 'election_type', 'office', 'district', 'contest', 'precinct',
          'candidate', 'votes', 'suppressed'])

# --------------------------------------------------------------------------- report
gen = [r for r in races if r['election_type'] == 'municipal general']
print(f"races: {len(races)}  (general {len(gen)})")
print(f"by_candidate rows: {len(by_cand)}   by_precinct rows: {len(by_precinct)}")
if REPORT:
    for r in sorted(races, key=lambda x: (x['year'], x['contest'])):
        unc = ' [UNCONTESTED]' if r['uncontested'] == 'True' else ''
        sup = ' [suppressed]' if r['suppressed_precincts'] == 'True' else ''
        to = f" turnout {r['turnout_pct']}%" if r['turnout_pct'] != '' else ''
        print(f"  {r['year']} {r['contest']:34s} n={r['n_candidates']} "
              f"WIN {r['winner']} {r['winner_votes']} ({r['winner_pct']}%) vs "
              f"{r['runner_up']} {r['runner_up_votes']}  margin {r['margin_votes']} "
              f"[tot {r['total_votes']}{to}]{unc}{sup}")
