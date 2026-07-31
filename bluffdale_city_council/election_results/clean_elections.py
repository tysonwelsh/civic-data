#!/usr/bin/env python3
"""Build Bluffdale City (Salt Lake County, UT) election_results.

Bluffdale is a **Mayor + 5-member AT-LARGE council** city (NO districts).  The Mayor is
elected citywide; the five council seats are all at-large, filled on 4-year STAGGERED,
non-partisan terms.  Because seats are at-large and multi-seat, most council contests are
**vote-for-N** (top N vote-getters win).  As they appear in the Salt Lake County
Statement-of-Votes-Cast (SOVC) files the stagger is:

  * Mayor year (Mayor + 2 council seats):        2009, 2013, 2017, 2021, 2025
  * Council-only year (3 council seats):          2007, 2011, 2015, 2019, 2023
  * plus mid-cycle "2-YEAR" (unexpired-term) at-large vacancy contests: 2017, 2019.

Seat counts are DATA-VERIFIED (SOVC "Vote for N" headers, votes/ballots ratios, and
external cross-checks), not merely assumed — see N_SEATS below and CLAUDE.md.

Salt Lake County administers and reports ALL Bluffdale results (the Utah-County portion of
the city is Camp Williams / unpopulated -> no separate Utah-County Bluffdale race).

At-large multi-seat conventions (25-col superset schema, sibling of Sandy's at-large):
  * winner        = the single top vote-getter (rank 1)
  * runner_up     = the FIRST LOSER (rank n_seats+1)  [primaries: rank advance+1]
  * margin_votes  = last-winner (rank n_seats) - first-loser (rank n_seats+1)
                    i.e. how close the cutoff for the last seat was
  * note          = the full winning slate (all n_seats winners), + any RCV caveat
  * is_winner (by_candidate) = rank <= n_seats  (so ALL seat winners are flagged)
  * total_first_choice_votes = sum of candidate votes (total_votes left blank), mirroring
    the Sandy at-large sibling; winner_pct = winner_votes / that sum.

SOURCES  (Salt Lake County Clerk; canonical archive mirrored at ~/Desktop/slco-election-archive)
--------------------------------------------------------------------------------------
1. raw/municipal_results_long_bluffdale.csv
      The collection-wide canonical SOVC normalization, filtered to Bluffdale.  Precinct-
      and vote-method-level; consumed for 2007/2009/2011/2013/2015/2017/2023/2025
      (generals + primaries).  Method rows are summed per candidate; the 2023 PRIMARY
      rows are TRIPLICATED (each (precinct,candidate) row repeated 3x, identical) and are
      de-duplicated on read.

2. raw/sovc/*.xlsx  (true county SOVC spreadsheets) -- re-parsed directly for:
      * 2019 general + 2019 primary -- ABSENT from the canonical long file (0 Bluffdale
        rows; the normalizer keyed the contest off the sheet name "BLF Council ...", so a
        %BLUFFDALE% filter never matched).  Recovered here for the 4-YEAR (2 seats) and
        2-YEAR (1 seat) at-large contests.  This closes the recon-flagged 2019 gap AND
        recovers a genuine 2019 PRIMARY (which DID occur, both contests).
      * 2021 general (Mayor + Council) -- present in the long file but with method-split
        privacy suppression; re-parsed from the raw per-precinct **Total** rows (NOT
        suppressed).  2021 council was the Utah RCV pilot (2-seat, ranked-choice): the
        stored candidate figures are FIRST-CHOICE totals; the two RCV winners were Wendy
        Aston (seat 1) and Traci Crockett (seat 2) -- see note column + CLAUDE.md.

EXCLUDED: BLUFFDALE CITY PROPOSITION #13 (2023) -- a ballot proposition, not a council/
mayor candidate race (logged in CLAUDE.md, not fabricated into the candidate schema).

Reproducible:  python3 clean_elections.py            (reads raw/, writes the 3 CSVs)
               python3 clean_elections.py --report    (prints a per-race summary)
"""
import os, re, csv, sys, openpyxl

OUT = os.path.dirname(os.path.abspath(__file__))
SLICE = os.path.join(OUT, 'raw', 'municipal_results_long_bluffdale.csv')
SOVC = os.path.join(OUT, 'raw', 'sovc')
REPORT = '--report' in sys.argv

# ------------------------------------------------------------------ contest canonicalization
def canon(year, label):
    """Map a county contest label to (office, district, canonical_contest, is_two_year)."""
    U = re.sub(r'\s+', ' ', label.upper()).strip()
    if 'MAYOR' in U:
        return ('Mayor', '', 'Bluffdale City Mayor', False)
    two_year = bool(re.search(r'\b2\s*Y(?:EA)?R\b', U) or '2 YEAR' in U)
    if two_year:
        return ('Council', 'At-Large', 'Bluffdale City Council At-Large (2-Year)', True)
    return ('Council', 'At-Large', 'Bluffdale City Council At-Large', False)

# ------------------------------------------------------------------ seats / method lookup
# key = (year, election_type, canonical_contest) -> n_seats  (seats up in the GENERAL)
N_SEATS = {
    (2007, 'municipal general', 'Bluffdale City Council At-Large'): 3,
    (2009, 'municipal general', 'Bluffdale City Council At-Large'): 2,
    (2009, 'municipal general', 'Bluffdale City Mayor'): 1,
    (2011, 'municipal general', 'Bluffdale City Council At-Large'): 3,
    (2013, 'municipal general', 'Bluffdale City Council At-Large'): 2,
    (2013, 'municipal general', 'Bluffdale City Mayor'): 1,
    (2015, 'municipal general', 'Bluffdale City Council At-Large'): 3,
    (2017, 'municipal general', 'Bluffdale City Council At-Large'): 2,
    (2017, 'municipal general', 'Bluffdale City Council At-Large (2-Year)'): 1,
    (2017, 'municipal general', 'Bluffdale City Mayor'): 1,
    (2019, 'municipal general', 'Bluffdale City Council At-Large'): 3,           # "4 YEAR"
    # ^ CORRECTED 2 -> 3 (2026-07-12, roster AUDIT.md F1): the raw SOVC records 4,977
    #   candidate votes against 2,154 ballots cast in this contest — impossible under
    #   vote-for-2 (cap 4,308) and over the ceiling in EVERY precinct; cohort A elects 3
    #   (2007/2015/2023) and the 2020-01-06 oath seats Kallas, Gaston AND Hales as
    #   Members-Elect. The old 2 mis-flagged Hales is_winner=False and poisoned
    #   runner_up/margin/notes.
    (2019, 'municipal general', 'Bluffdale City Council At-Large (2-Year)'): 1,
    (2021, 'municipal general', 'Bluffdale City Council At-Large'): 2,           # RCV pilot
    (2021, 'municipal general', 'Bluffdale City Mayor'): 1,
    (2023, 'municipal general', 'Bluffdale City Council At-Large'): 3,
    (2025, 'municipal general', 'Bluffdale City Council At-Large'): 2,
    (2025, 'municipal general', 'Bluffdale City Mayor'): 1,
}
RCV = {(2021, 'municipal general', 'Bluffdale City Council At-Large'),
       (2021, 'municipal general', 'Bluffdale City Mayor')}
# 2021 council RCV winning slate (order = seat awarded), from SLCo canvass / SL Tribune.
RCV_2021_WINNERS = ['WENDY W. ASTON', 'TRACI CROCKETT']

def seats_for(year, etype, contest):
    """seats up in the general; primaries inherit the general's seat count."""
    if etype == 'municipal general':
        return N_SEATS[(year, etype, contest)]
    return N_SEATS[(year, 'municipal general', contest)]

def method_for(year, etype, contest):
    return 'RCV' if (year, 'municipal general', contest) in RCV else 'plurality'

# ------------------------------------------------------------------ helpers
def g(r, j):
    return r[j] if (r is not None and j < len(r)) else None

def norm_name(s):
    s = re.sub(r'\s+', ' ', str(s).replace('\n', ' ')).strip()
    s = s.lstrip('*').strip()
    s = re.sub(r'\s*\(\s*(?:NP|NON)\s*\)', '', s, flags=re.I)      # strip (NP)/(NON)
    s = re.sub(r'\bUNRESOLVED\s+WRITE[- ]?IN\b', 'Write-in (unresolved)', s, flags=re.I)
    s = re.sub(r'\bWRITE[- ]?IN\b', 'Write-in', s, flags=re.I)
    return re.sub(r'\s+', ' ', s).strip().strip('"').strip()

def to_int(v):
    if isinstance(v, (int, float)):
        return int(v)
    if isinstance(v, str):
        v = v.strip().replace(',', '')
        if re.fullmatch(r'-?\d+', v):
            return int(v)
    return None

# ------------------------------------------------------------------ containers
RECORDS = {}  # key=(year, etype, contest) -> dict

def rec(year, etype, label, source_file):
    office, district, contest, _two = canon(year, label)
    k = (year, etype, contest)
    if k not in RECORDS:
        RECORDS[k] = dict(year=year, election_type=etype, office=office,
                          district=district, contest=contest,
                          cand={}, per={}, reg={}, ballots={},
                          suppressed_any=False, source_file=source_file, verbatim=label)
    return RECORDS[k], k

def add_vote(R, precinct, cand, votes):
    R['cand'][cand] = R['cand'].get(cand, 0) + (votes or 0)
    R['per'].setdefault(precinct, {})
    cur = R['per'][precinct].get(cand)
    if votes is None:
        R['suppressed_any'] = True
        R['per'][precinct].setdefault(cand, None)
    else:
        R['per'][precinct][cand] = (cur or 0) + votes if isinstance(cur, int) else votes

# ------------------------------------------------------------------ (1) canonical long slice
SLICE_SKIP_YEARS = {2019, 2021}   # 2019 absent (parsed from raw); 2021 re-parsed from raw

def load_slice():
    seen = set()   # (year,etype,contest,precinct,cand,method,votes) -> de-dup 2023-primary triplicates
    with open(SLICE, newline='') as fh:
        for row in csv.DictReader(fh):
            year = int(float(row['year']))
            if year in SLICE_SKIP_YEARS:
                continue
            if 'PROPOSITION' in row['contest'].upper():
                continue
            R, _ = rec(year, row['election_type'], row['contest'], row['source_file'])
            prec = row['precinct'].strip()
            cand = norm_name(row['candidate'])
            meth = row['vote_method'].strip()
            vraw = row['votes'].strip()
            dk = (year, row['election_type'], R['contest'], prec, cand, meth, vraw)
            if dk in seen:
                continue                       # identical triplicate row -> count once
            seen.add(dk)
            supp = row['suppressed'].strip().lower() == 'true'
            votes = int(float(vraw)) if vraw not in ('', 'nan') else None
            add_vote(R, prec, cand, None if (supp or votes is None) else votes)
            reg = row['registered_voters'].strip()
            tc = row['times_cast'].strip()
            if reg not in ('', 'nan'):
                R['reg'][prec] = max(R['reg'].get(prec, 0), int(float(reg)))
            if tc not in ('', 'nan'):
                R['ballots'][prec] = max(R['ballots'].get(prec, 0), int(float(tc)))

# ------------------------------------------------------------------ (2a) raw 2019 parser
PR19 = re.compile(r'BLF\d+')

def parse_2019_sheet(path, sheet, year, etype, label):
    """2019 SOVC wide crosstab: r1 candidate names sparse; r2 sub-headers with a
    'Total Votes' column per candidate + a 'Registered Voters' column; precinct rows
    (col0 == BLF###) follow; a 'Total:' row closes the block (skipped -> summed from
    precincts)."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[sheet]
    rows = [list(x) for x in ws.iter_rows(values_only=True)]
    name_row = rows[1]
    sub_row = rows[2]
    names = [(j, norm_name(name_row[j])) for j in range(len(name_row))
             if name_row[j] not in (None, '')]
    tv_cols = [j for j, v in enumerate(sub_row) if str(v).strip() == 'Total Votes']
    assert len(names) == len(tv_cols), f"{sheet}: {len(names)} names vs {len(tv_cols)} TV cols"
    cand_tv = [(nm, tv) for (_, nm), tv in zip(names, tv_cols)]
    regj = next((j for j, v in enumerate(sub_row) if 'Registered' in str(v)), None)
    R, _ = rec(year, etype, label, os.path.basename(path))
    for r in rows[3:]:
        c0 = g(r, 0)
        if isinstance(c0, str) and PR19.fullmatch(c0.strip()):
            prec = c0.strip()
            for nm, tv in cand_tv:
                add_vote(R, prec, nm, to_int(g(r, tv)))
            if regj is not None and to_int(g(r, regj)) is not None:
                R['reg'][prec] = to_int(g(r, regj))

# ------------------------------------------------------------------ (2b) raw 2021 parser
def parse_2021_sheet(path, sheet, year, etype):
    """2021 columnar SOVC: r1 = title '(Vote for N)'; r3 header carries candidate names
    (each followed by a % col) plus 'Times Cast' / 'Registered Voters' / 'Total Votes'.
    Each precinct has In Person / Vote By Mail method sub-rows (small counts '****'
    suppressed) and a 'Total' sub-row with the UN-suppressed precinct count."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[sheet]
    rows = [list(x) for x in ws.iter_rows(values_only=True)]
    title = next(str(g(r, 0)) for r in rows[:3] if g(r, 0) and 'BLUFF' in str(g(r, 0)).upper())
    label = re.sub(r'\s*\(Vote.*', '', title).strip()
    hi = next(i for i, r in enumerate(rows)
              if str(g(r, 0)).strip() == 'Precinct' and str(g(r, 4)).strip() == 'Precinct')
    hdr = rows[hi]
    tcj = next((j for j in range(len(hdr)) if 'Times Cast' in str(g(hdr, j))), None)
    rgj = next((j for j in range(len(hdr)) if 'Registered' in str(g(hdr, j))), None)
    SPECIAL = {'PRECINCT', 'TIMES CAST', 'REGISTERED VOTERS', 'TOTAL VOTES', ''}
    cand_cols = {}
    for j in range(5, len(hdr)):          # candidate block begins after the 2nd 'Precinct'
        cell = g(hdr, j)
        if cell in (None, ''):
            continue
        L = re.sub(r'\s+', ' ', str(cell).replace('\n', ' ')).strip().upper()
        if L in SPECIAL or L.endswith('%'):
            continue
        cand_cols[j] = norm_name(cell)
    R, _ = rec(year, etype, label, os.path.basename(path))
    cur = None
    for r in rows[hi + 1:]:
        c0 = str(g(r, 0)).strip() if g(r, 0) is not None else ''
        if PR19.fullmatch(c0):
            cur = c0
            R['per'].setdefault(cur, {})
        elif c0 == 'Total' and cur is not None:
            for j, nm in cand_cols.items():
                add_vote(R, cur, nm, to_int(g(r, j)))
            if tcj is not None and to_int(g(r, tcj)) is not None:
                R['ballots'][cur] = to_int(g(r, tcj))
            if rgj is not None and to_int(g(r, rgj)) is not None:
                R['reg'][cur] = to_int(g(r, rgj))
            cur = None

# ------------------------------------------------------------------ run loaders
load_slice()
G19 = os.path.join(SOVC, '2019-11-05-general-election-sovc.xlsx')
P19 = os.path.join(SOVC, '2019-08-13-municipal-primary-sovc.xlsx')
parse_2019_sheet(G19, 'BLF Council - 4 yr', 2019, 'municipal general',
                 'BLUFFDALE CITY COUNCIL AT LARGE 4 YEAR')
parse_2019_sheet(G19, 'BLF Council - 2 yr', 2019, 'municipal general',
                 'BLUFFDALE CITY COUNCIL AT LARGE 2 YEAR')
parse_2019_sheet(P19, '2', 2019, 'municipal primary',
                 'BLUFFDALE CITY COUNCIL AT LARGE 4 YEAR')
parse_2019_sheet(P19, '3', 2019, 'municipal primary',
                 'BLUFFDALE CITY COUNCIL AT LARGE 2 YEAR')
G21 = os.path.join(SOVC, 'november-2-2021-general-election-statement-of-votes-cast.xlsx')
parse_2021_sheet(G21, 'Sheet4', 2021, 'municipal general')   # Mayor
parse_2021_sheet(G21, 'Sheet5', 2021, 'municipal general')   # Council At-Large (RCV, 2 seats)

# ------------------------------------------------------------------ compute + write
def real_cands(items):
    return [(n, v) for n, v in items
            if not (n.lower().startswith('write-in') and (v or 0) == 0)]

races, by_cand, by_precinct = [], [], []
for k in sorted(RECORDS, key=lambda x: (x[0], x[1], x[2])):
    R = RECORDS[k]
    year, etype, contest = k
    seats = seats_for(year, etype, contest)
    method = method_for(year, etype, contest)
    # advancement cutoff: general -> seats; primary -> 2*seats (top 2N advance)
    cutoff = seats if etype == 'municipal general' else 2 * seats

    items = sorted(R['cand'].items(), key=lambda kv: (-(kv[1] or 0), kv[0]))
    total = sum(v or 0 for v in R['cand'].values())
    rc = real_cands(items)
    n_real = len(rc)

    winner, wv = items[0] if items else ('', 0)
    all_in = len(items) <= cutoff       # nobody eliminated / more seats than candidates
    if etype == 'municipal primary' and all_in:
        # every candidate advances -> no meaningful cutoff margin
        runner, rv, margin = '', '', ''
    else:
        last_win = items[cutoff - 1] if len(items) >= cutoff else (items[-1] if items else ('', 0))
        first_loser = items[cutoff] if len(items) > cutoff else ('', 0)
        runner, rv = first_loser
        margin = (last_win[1] or 0) - (rv or 0)

    reg_total = sum(R['reg'].values()) if R['reg'] else ''
    ballots_total = sum(R['ballots'].values()) if R['ballots'] else ''
    turnout = (round(100 * ballots_total / reg_total, 2)
               if (isinstance(ballots_total, int) and isinstance(reg_total, int) and reg_total) else '')

    # note: winning slate (generals only), RCV caveat, primary advancement
    note_parts = []
    if etype == 'municipal general' and seats > 1:
        note_parts.append('winners: ' + '; '.join(
            f"{n} ({v})" for n, v in items[:seats]))
    if method == 'RCV':
        if k == (2021, 'municipal general', 'Bluffdale City Council At-Large'):
            note_parts.append('RCV pilot (2-seat, sequential ranked-choice); stored figures '
                              'are FIRST-CHOICE totals; RCV winners: Wendy Aston (seat 1), '
                              'Traci Crockett (seat 2)')
        else:
            note_parts.append('RCV pilot; 2 candidates (first round decisive)')
    if etype == 'municipal primary':
        note_parts.append('all candidates advanced (no elimination)' if all_in
                          else f'top {cutoff} advance')
    note = ' | '.join(note_parts)

    uncontested = 'True' if n_real <= seats else 'False'

    races.append(dict(
        year=year, election_type=etype, office=R['office'], district=R['district'],
        contest=contest, contest_verbatim=R['verbatim'], n_seats=seats,
        n_candidates=n_real, voting_method=method,
        total_votes='', total_first_choice_votes=total,
        winner=winner, winner_votes=wv,
        winner_pct=round(100 * (wv or 0) / total, 2) if total else 0,
        runner_up=runner, runner_up_votes=rv,
        margin_votes=margin,
        margin_pct=(round(100 * margin / total, 2) if (total and margin != '') else ''),
        registered_voters=reg_total, ballots_cast=ballots_total, turnout_pct=turnout,
        uncontested=uncontested,
        suppressed_precincts='True' if R['suppressed_any'] else 'False',
        note=note, source_file=R['source_file']))

    for rank, (name, v) in enumerate(items, 1):
        by_cand.append(dict(
            year=year, election_type=etype, office=R['office'], district=R['district'],
            contest=contest, candidate=name, votes=v or 0,
            pct=round(100 * (v or 0) / total, 2) if total else 0,
            rank=rank, is_winner='True' if (rank <= seats and etype == 'municipal general') else 'False'))

    for prec in sorted(R['per']):
        for name, v in R['per'][prec].items():
            by_precinct.append(dict(
                year=year, election_type=etype, office=R['office'], district=R['district'],
                contest=contest, precinct=prec, candidate=name,
                votes='' if v is None else v,
                suppressed='True' if v is None else 'False'))

def writecsv(name, rows, cols):
    with open(os.path.join(OUT, name), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

writecsv('bluffdale_races.csv', races,
         ['year', 'election_type', 'office', 'district', 'contest', 'contest_verbatim',
          'n_seats', 'n_candidates', 'voting_method', 'total_votes',
          'total_first_choice_votes', 'winner', 'winner_votes', 'winner_pct', 'runner_up',
          'runner_up_votes', 'margin_votes', 'margin_pct', 'registered_voters',
          'ballots_cast', 'turnout_pct', 'uncontested', 'suppressed_precincts', 'note',
          'source_file'])
writecsv('bluffdale_results_by_candidate.csv', by_cand,
         ['year', 'election_type', 'office', 'district', 'contest', 'candidate',
          'votes', 'pct', 'rank', 'is_winner'])
writecsv('bluffdale_results_by_precinct.csv', by_precinct,
         ['year', 'election_type', 'office', 'district', 'contest', 'precinct',
          'candidate', 'votes', 'suppressed'])

# ------------------------------------------------------------------ report
gen = [r for r in races if r['election_type'] == 'municipal general']
pri = [r for r in races if r['election_type'] == 'municipal primary']
print(f"races: {len(races)}  (general {len(gen)}, primary {len(pri)})")
print(f"by_candidate rows: {len(by_cand)}   by_precinct rows: {len(by_precinct)}")
if REPORT:
    for r in sorted(races, key=lambda x: (x['year'], x['election_type'], x['contest'])):
        tag = 'PRIMARY ' if r['election_type'] == 'municipal primary' else ''
        unc = ' [UNCONTESTED]' if r['uncontested'] == 'True' else ''
        sup = ' [suppressed]' if r['suppressed_precincts'] == 'True' else ''
        rcv = ' [RCV]' if r['voting_method'] == 'RCV' else ''
        to = f" turnout {r['turnout_pct']}%" if r['turnout_pct'] != '' else ''
        print(f"  {r['year']} {tag}{r['contest']:38s} seats={r['n_seats']} n={r['n_candidates']} "
              f"WIN {r['winner']} {r['winner_votes']} ({r['winner_pct']}%)  "
              f"cutoff-margin {r['margin_votes']} vs {r['runner_up']} {r['runner_up_votes']} "
              f"[tot {r['total_first_choice_votes']}{to}]{rcv}{unc}{sup}")
        if r['note']:
            print(f"        note: {r['note']}")
