#!/usr/bin/env python3
"""Build South Salt Lake City (Salt Lake County, UT) election_results.

South Salt Lake is a **Council-Mayor (strong-mayor)** city: a **7-member council =
5 geographic DISTRICTS (1-5) + 2 AT-LARGE seats**, plus a **separately elected Mayor**
(citywide, non-voting on council). 4-year staggered, non-partisan terms. As the contests
appear in the Salt Lake County Statement-of-Votes-Cast (SOVC) files, the stagger is:

  * Cycle A (Mayor + one At-Large + District 2 + District 3): 2009, 2013, 2017, 2021, 2025
  * Cycle B (the other At-Large + District 1 + District 4 + District 5): 2007, 2011, 2015,
    2019, 2023

There are TWO physical At-Large seats (one on each cycle) but the county labels do NOT
distinguish them, so both normalize to the single canonical contest "...Council At-Large"
(the year disambiguates the seat). The 2025 "AT-LARGE (2 YEAR TERM)" is an off-cycle
unexpired-term SPECIAL and is kept as its own distinct contest so member-term logic does
not misread it as a cycle shift.

SOURCES  (Salt Lake County Clerk; local mirror ~/Desktop/slco-election-archive)
--------------------------------------------------------------------------------------
Two provenance layers, both retained under raw/:

1. raw/municipal_results_long_south_salt_lake.csv
     The archive's canonical SOVC normalization (repo-root
     salt_lake_county/elections/slco_municipal_results_long.csv) filtered to
     'SOUTH SALT LAKE'. Precinct- and vote-method-level. Consumed directly for
     2007, 2009, 2013, 2015, 2017 (+ their primaries) and the 2023 & 2025 generals --
     all zero-suppression, summing cleanly to contest totals.

2. raw/sovc/*.xlsx  (true county SOVC spreadsheets)
     Re-parsed directly for the contests the normalized slice does not deliver:
       * 2011 general (At-Large + D1/D4/D5) and 2011 primary (D4) -- ABSENT from the slice
         (the archive normalizer keyed the contest off the SHEET NAME -- 'S Salt Lake City
         Coun N' -- so a '%SOUTH SALT LAKE%' filter never matched). RECOVERED from raw.
       * 2019 general (At-Large + D1/D4/D5) and 2019 primary (At-Large + D1/D4/D5) --
         ABSENT for the same reason (general sheets 'SSL Council N'; primary sheets named
         numerically '21'-'24'). RECOVERED from raw.
       * 2021 general (Mayor + At-Large + D2 + D3) -- present in the slice but
         privacy-SUPPRESSED at the In-Person/Vote-By-Mail method split (102/168 cells
         '****'). RE-PARSED from raw (Sheet42-45), whose per-precinct 'Total' sub-rows
         are NOT suppressed.

KNOWN GAPS (documented, never fabricated):
  * 2021 municipal PRIMARY -- NEVER EXISTED. Not a gap; a non-event. (Corrected
    2026-07-17, re-verified at the primary source 2026-07-31 -- see the RCV_2021 block
    below.) South Salt Lake joined Utah's 2021 Municipal Alternate Voting Methods (RCV)
    pilot, and the pilot REPLACES the municipal primary, so all 3 mayoral candidates
    advanced straight to the ranked general. Corroborated by the county's only 2021
    primary publication (2021-08-10-primary-election-results.pdf), which carries just 6
    contests -- Herriman Mayor, Murray Mayor, Taylorsville D5, West Jordan At-Large,
    West Valley Mayor, West Valley D2, all NON-pilot cities -- and no SSL contest.
    The earlier reading here ("3 candidates -> a primary was almost certainly held") was
    WRONG and is retained in this note only so the false lead is not re-opened.
  * 2023 & 2025 municipal PRIMARY -- the archive normalized both years' primaries but they
    contain NO South Salt Lake sheet (each seat drew <=2 candidates -> no primary
    triggered). Verified in raw. True no-contest, not a data gap.
  * 2007 municipal PRIMARY -- the 2007 primary SOVC contains no South Salt Lake sheet
    (only SLC). No 2007 SSL primary.
  * SPECIAL BOND measures (2011 'S Salt Lake Bond', 2015 'SOUTH SALT LAKE SPECIAL BOND')
    are ballot questions, not council/mayor seats -> intentionally EXCLUDED from the races
    file (noted here for completeness).

Reproducible:  python3 clean_elections.py            (reads raw/, writes the 3 CSVs)
               python3 clean_elections.py --report    (+ per-race summary)
"""
import os, re, csv, sys, openpyxl

OUT = os.path.dirname(os.path.abspath(__file__))
SLICE = os.path.join(OUT, 'raw', 'municipal_results_long_south_salt_lake.csv')
SOVC = os.path.join(OUT, 'raw', 'sovc')
REPORT = '--report' in sys.argv
PR = re.compile(r'SSL\d+', re.I)          # South Salt Lake precinct id


# --------------------------------------------------------------------------- helpers
def g(r, j):
    return r[j] if (r is not None and j < len(r)) else None


def norm_name(s):
    """Normalize a candidate name ALONGSIDE the verbatim value (never overwrites raw):
    collapse whitespace, strip the (NP) non-partisan tag, canonicalize write-ins."""
    s = re.sub(r'\s+', ' ', str(s).replace('\n', ' ')).strip()
    s = s.lstrip('*').strip()
    s = re.sub(r'\s*\(\s*(?:NP|NON)\s*\)', '', s, flags=re.I)
    s = re.sub(r'\bUNRESOLVED\s+WRITE[- ]?IN\b', 'Write-in (unresolved)', s, flags=re.I)
    s = re.sub(r'\bWRITE[- ]?IN\b', 'Write-in', s, flags=re.I)
    return re.sub(r'\s+', ' ', s).strip().strip('"').strip()


def to_int(v):
    return int(v) if isinstance(v, (int, float)) else None


# ---- contest canonicalization ----------------------------------------------
def canon(label):
    """Map a county contest label to (office, district, canonical_contest).
    Returns None for non-seat measures (bond questions) so they are skipped."""
    U = re.sub(r'\s+', ' ', str(label).upper()).strip()
    if 'BOND' in U:
        return None
    if 'MAYOR' in U:
        return ('Mayor', '', 'South Salt Lake City Mayor')
    is_al = ('AT LARGE' in U or 'AT-LARGE' in U or 'AT LRG' in U or '@' in U)
    if is_al:
        if re.search(r'2\s*-?\s*YEAR', U):
            return ('Council', 'At-Large-2yr',
                    'South Salt Lake City Council At-Large (2-Year Term)')
        return ('Council', 'At-Large', 'South Salt Lake City Council At-Large')
    m = (re.search(r'DIS\w*\s*(\d+)', U)
         or re.search(r'(?:COUNCIL|CNCL|COUN)\s*#?\s*(\d+)', U)
         or re.search(r'(\d+)\s*$', U))
    d = m.group(1) if m else '?'
    return ('Council', d, f'South Salt Lake City Council District {d}')


# --------------------------------------------------------------------------- containers
RECORDS = {}


def rec(year, etype, label, source_file):
    c = canon(label)
    if c is None:
        return None
    office, district, contest = c
    k = (year, etype, contest)
    if k not in RECORDS:
        RECORDS[k] = dict(year=year, election_type=etype, office=office,
                          district=district, contest=contest,
                          cand={}, per={}, reg={}, ballots={}, ballots_pm={},
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
# 2021 general re-parsed from raw (suppression); 2011/2019 absent from the slice anyway.
SLICE_SKIP = {('2021', 'municipal general')}


def load_slice():
    with open(SLICE, newline='') as fh:
        for row in csv.DictReader(fh):
            year = str(int(float(row['year'])))
            etype = row['election_type']
            if (year, etype) in SLICE_SKIP:
                continue
            R = rec(year, etype, row['contest'], row['source_file'])
            if R is None:                       # bond measure -> skip
                continue
            prec = row['precinct'].strip()
            cand = norm_name(row['candidate'])
            v = row['votes'].strip()
            votes = int(float(v)) if v not in ('', 'nan') else None
            supp = row['suppressed'].strip().lower() == 'true'
            add_vote(R, prec, cand, None if (supp or votes is None) else votes)
            reg = row['registered_voters'].strip()
            tc = row['times_cast'].strip()
            method = row['vote_method'].strip()
            if reg not in ('', 'nan'):
                R['reg'][prec] = max(R['reg'].get(prec, 0), int(float(reg)))
            if tc not in ('', 'nan'):           # ballots keyed per (precinct, method)
                R['ballots_pm'][(prec, method)] = int(float(tc))


# --------------------------------------------------------------------------- (2) raw parsers
def parse_type_layout(path, etype, sheet_ok):
    """2011 layout: header row 'Precinct'/'Type'/'Reg. Voters'/'Cards Cast'/'Total Votes'
    then candidate columns (each followed by an empty-header pct col); each precinct has
    method sub-rows and a 'Total' Type row carrying the real count. Precinct ids = SSL###.
    Contest label comes from the sheet's own title cell (rows above the header)."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    for sh in wb.sheetnames:
        if not sheet_ok(sh):
            continue
        ws = wb[sh]
        rows = [list(x) for x in ws.iter_rows(values_only=True)]
        try:
            hi = next(i for i, r in enumerate(rows)
                      if any(str(g(r, j)).strip() == 'Precinct' for j in range(len(r))))
        except StopIteration:
            continue
        hdr = rows[hi]
        pj = next(j for j in range(len(hdr)) if str(g(hdr, j)).strip() == 'Precinct')
        typej = pj + 1
        regj = next((j for j in range(len(hdr)) if 'Reg' in str(g(hdr, j))), None)
        cardj = next((j for j in range(len(hdr)) if 'Cards Cast' in str(g(hdr, j))), None)
        tvj = next(j for j in range(len(hdr)) if str(g(hdr, j)).strip() == 'Total Votes')
        cand_cols = {j: norm_name(g(hdr, j)) for j in range(tvj + 1, len(hdr))
                     if g(hdr, j) not in (None, '') and str(g(hdr, j)).strip()}
        # title = a cell above the header that names the contest
        label = None
        for r in rows[:hi]:
            for c in r:
                if c and 'salt lake' in str(c).lower() and 'coun' in str(c).lower():
                    label = str(c)
        if not label:
            label = sh
        year, kind = etype
        R = rec(year, kind, label, os.path.basename(path))
        if R is None:
            continue
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


def parse_wide_crosstab(path, etype):
    """2019 'Family-A' wide crosstab: row1 candidate names sparse; row2 sub-header marks
    each candidate's total with 'Total Votes' + a 'Registered' col; precinct rows (col0 ==
    SSL###) follow. Contest label = row0 title cell. Handles both the general (sheets
    'SSL Council N'/'SSL At-Large') and primary (numeric page-sheet names) uniformly: a
    sheet is South Salt Lake iff its row0 TITLE cell names the city (the numeric primary
    sheet names are page numbers and are NOT used)."""
    year, kind = etype
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    for sh in wb.sheetnames:
        ws = wb[sh]
        rows = [list(x) for x in ws.iter_rows(values_only=True)]
        if len(rows) < 4:
            continue
        title = str(g(rows[0], 0) or '')
        if 'SOUTH SALT LAKE' not in title.upper():
            continue
        name_row, sub_row = rows[1], rows[2]
        cand_cols = [(j, norm_name(name_row[j])) for j in range(len(name_row))
                     if name_row[j] not in (None, '')]
        tv_cols = [j for j, v in enumerate(sub_row) if str(v).strip() == 'Total Votes']
        if not cand_cols or not tv_cols:
            continue
        cands = [n for _, n in cand_cols]
        cand_tv = dict(zip(cands, tv_cols))
        regj = next((j for j, v in enumerate(sub_row) if 'Registered' in str(v)), None)
        R = rec(year, kind, title, os.path.basename(path))
        if R is None:
            continue
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
    """2021 columnar: a second 'Precinct' marker precedes candidate columns; each precinct
    has In Person / Vote By Mail sub-rows (small counts '****' suppressed) and a 'Total'
    sub-row with the UN-suppressed precinct count. Title cell names the contest."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    for sh in sheets:
        ws = wb[sh]
        rows = [list(x) for x in ws.iter_rows(values_only=True)]
        title = next(str(g(r, 0)) for r in rows[:4]
                     if g(r, 0) and 'SOUTH SALT LAKE' in str(g(r, 0)).upper())
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
        R = rec('2021', 'municipal general',
                re.sub(r'\s*\(Vote.*', '', title).strip(), os.path.basename(path))
        if R is None:
            continue
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
# 2011 general + primary (Type-layout; 'S Salt Lake ...' sheets, skip the Bond sheet)
parse_type_layout(os.path.join(SOVC, '2011-11-08-municipal-general-sovc.xlsx'),
                  ('2011', 'municipal general'),
                  lambda sh: sh.lower().startswith('s salt lake') and 'bond' not in sh.lower())
parse_type_layout(os.path.join(SOVC, '2011-09-13-municipal-primary-sovc.xlsx'),
                  ('2011', 'municipal primary'),
                  lambda sh: sh.lower().startswith('s salt lake') and 'bond' not in sh.lower())
# 2019 general + primary (wide crosstab; title-cell driven)
parse_wide_crosstab(os.path.join(SOVC, '2019-11-05-general-election-sovc.xlsx'),
                    ('2019', 'municipal general'))
parse_wide_crosstab(os.path.join(SOVC, '2019-08-13-municipal-primary-sovc.xlsx'),
                    ('2019', 'municipal primary'))
# 2021 general (Mayor + At-Large + D2 + D3)
parse_2021_general(os.path.join(SOVC, 'november-2-2021-general-election-statement-of-votes-cast.xlsx'),
                   ['Sheet42', 'Sheet43', 'Sheet44', 'Sheet45'])


# --------------------------------------------------------------------------- compute + write
def real_cands(items):
    return [(n, v) for n, v in items
            if not (n.startswith('Write-in') and (v or 0) == 0)]


# ------------------------------------------------------------- the 2021 RCV pilot
# South Salt Lake joined Utah's 2021 Municipal Alternate Voting Methods (ranked-choice)
# pilot, so its ENTIRE 2021 municipal general was ranked-choice -- and, because the pilot
# replaces the municipal primary, no Aug-2021 SSL primary was held (see KNOWN GAPS above).
#
# PRIMARY-SOURCE PROOF (2026-07-31): the Salt Lake County Clerk's "Official Final Ranked
# Choice Results, 2021 General Election" -- raw/2021-general-election-ranked-choice-
# summary-report.pdf, p.20 of 21 -- tabulates CITY OF SOUTH SALT LAKE MAYOR:
#     Round 1 -- CHERIE WOOD 1,777 (58.24%) | JAKE CHRISTENSEN 678 (22.22%)
#                L. SHANE SIWIK 596 (19.53%) | threshold 1,526
#     "Tabulation status: All Positions Filled"  <- filled IN ROUND 1
# Wood cleared the majority threshold outright, so no elimination round ran and the RCV
# FINAL EQUALS FIRST CHOICE. The three 2021 council contests drew 2 candidates each, so
# they are round-1 decisive and the county published no round table for them -- exactly as
# it did not for CITY OF BLUFFDALE MAYOR (2 candidates), which bluffdale's repo likewise
# records as RCV.
#
# Consequence for this file: round 1 == first choice == the SOVC 'Total' column already
# parsed here, so every stored tally, winner, and margin is CORRECT AS-IS and no number
# changes. Only the LABEL was wrong -- these four rows previously read voting_method=
# 'plurality' with total_first_choice_votes blank, which both mis-described the contest and
# left the missing-primary question looking like an acquisition gap.
_RCV_MAYOR = (
    'RCV pilot (Utah 2021 Municipal Alternate Voting Methods pilot). 3 candidates, WON IN '
    'ROUND 1: Wood 1,777 cleared the 1,526 majority threshold, so no elimination round ran '
    'and the RCV final equals first choice. Stored votes/pct/margin are ROUND-1 '
    '(first-choice) figures. Rounds: 2021-general-election-ranked-choice-summary-report.pdf '
    'p.20 (Salt Lake County Clerk, Official Final Ranked Choice Results). No Aug-2021 '
    'municipal primary was held -- the pilot replaces it.')
_RCV_COUNCIL = (
    'RCV pilot (Utah 2021 Municipal Alternate Voting Methods pilot). 2 candidates -> '
    'round-1 decisive, so the county published no elimination-round table for this contest '
    '(same treatment as CITY OF BLUFFDALE MAYOR in the same report). Stored votes/pct/'
    'margin are ROUND-1 (first-choice) figures and equal the RCV final.')
RCV_2021 = {
    'South Salt Lake City Mayor': _RCV_MAYOR,
    'South Salt Lake City Council At-Large': _RCV_COUNCIL,
    'South Salt Lake City Council District 2': _RCV_COUNCIL,
    'South Salt Lake City Council District 3': _RCV_COUNCIL,
}

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
    if R['ballots']:
        ballots_total = sum(R['ballots'].values())
    elif R['ballots_pm']:
        ballots_total = sum(R['ballots_pm'].values())
    else:
        ballots_total = ''
    turnout = (round(100 * ballots_total / reg_total, 2)
               if (isinstance(ballots_total, int) and isinstance(reg_total, int) and reg_total)
               else '')
    # 2021 municipal general only: the RCV pilot (see RCV_2021 above). Round 1 == first
    # choice, so the tallies are unchanged; the label and the first-choice column are not.
    rcv_note = (RCV_2021.get(R['contest'], '')
                if (R['year'], R['election_type']) == ('2021', 'municipal general') else '')
    races.append(dict(
        year=R['year'], election_type=R['election_type'], office=R['office'],
        district=R['district'], contest=R['contest'], contest_verbatim=R['verbatim'],
        n_seats=1, n_candidates=len(rc),
        voting_method='RCV' if rcv_note else 'plurality',
        total_votes=total,
        total_first_choice_votes=total if rcv_note else '',
        winner=winner, winner_votes=wv,
        winner_pct=round(100 * (wv or 0) / total, 2) if total else 0,
        runner_up=runner, runner_up_votes=rv,
        margin_votes=margin, margin_pct=round(100 * margin / total, 2) if total else 0,
        registered_voters=reg_total, ballots_cast=ballots_total, turnout_pct=turnout,
        uncontested='True' if len(rc) <= 1 else 'False',
        suppressed_precincts='True' if R['suppressed_any'] else 'False',
        note=rcv_note, source_file=R['source_file']))
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


RACE_COLS = ['year', 'election_type', 'office', 'district', 'contest', 'contest_verbatim',
             'n_seats', 'n_candidates', 'voting_method', 'total_votes',
             'total_first_choice_votes', 'winner', 'winner_votes', 'winner_pct',
             'runner_up', 'runner_up_votes', 'margin_votes', 'margin_pct',
             'registered_voters', 'ballots_cast', 'turnout_pct', 'uncontested',
             'suppressed_precincts', 'note', 'source_file']
writecsv('south_salt_lake_races.csv', races, RACE_COLS)
writecsv('south_salt_lake_results_by_candidate.csv', by_cand,
         ['year', 'election_type', 'office', 'district', 'contest', 'candidate',
          'votes', 'pct', 'rank', 'is_winner'])
writecsv('south_salt_lake_results_by_precinct.csv', by_precinct,
         ['year', 'election_type', 'office', 'district', 'contest', 'precinct',
          'candidate', 'votes', 'suppressed'])

# --------------------------------------------------------------------------- report
gen = [r for r in races if r['election_type'] == 'municipal general']
pri = [r for r in races if r['election_type'] == 'municipal primary']
print(f"races: {len(races)}  (general {len(gen)}, primary {len(pri)})")
print(f"by_candidate rows: {len(by_cand)}   by_precinct rows: {len(by_precinct)}")
supp = [r for r in races if r['suppressed_precincts'] == 'True']
if supp:
    print("WARNING suppressed races:", [(r['year'], r['contest']) for r in supp])
if REPORT:
    for r in sorted(races, key=lambda x: (x['year'], x['election_type'], x['contest'])):
        tag = 'PRIMARY ' if r['election_type'] == 'municipal primary' else ''
        unc = ' [UNCONTESTED]' if r['uncontested'] == 'True' else ''
        to = f" turnout {r['turnout_pct']}%" if r['turnout_pct'] != '' else ''
        print(f"  {r['year']} {tag}{r['contest']:44s} n={r['n_candidates']} "
              f"WIN {r['winner']} {r['winner_votes']} ({r['winner_pct']}%) vs "
              f"{r['runner_up']} {r['runner_up_votes']}  margin {r['margin_votes']} "
              f"[tot {r['total_votes']}{to}]{unc}")
