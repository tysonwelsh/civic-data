#!/usr/bin/env python3
"""Build Murray City (Salt Lake County, UT) election_results.

Murray is a **Council-Mayor** city: **5 council DISTRICTS (1-5), each elected by
single-member district**, plus a **separately elected Mayor** (citywide). 4-yr staggered
terms, so each odd-year cycle fills only part of the body.  As the contests appear in the
Salt Lake County Statement-of-Votes-Cast (SOVC), the in-scope stagger is:

  * 2021 general : Mayor + Districts 2, 4
  * 2023         : Districts 1, 3, 5   (D1 & D3 also had an August PRIMARY)
  * 2025 general : Mayor + Districts 2, 4 + District 3 (2-YEAR / unexpired SPECIAL)
                   (Mayor, D2 and the D3 special also had an August 2025 PRIMARY)

Data floor is 2020, so only cycles 2021 / 2023 / 2025 are built here (the 2019 general
and everything 2007-2017 sit below the floor and are omitted -- they exist in the county
long file if ever needed).

SOURCE  (Salt Lake County Clerk)
--------------------------------------------------------------------------------------
Canonical provenance = the county repo's normalized long SOVC:

    /Users/tysonwelsh/civic-data/salt_lake_county/elections/slco_municipal_results_long.csv

filtered to rows whose `contest` matches MURRAY.  Precinct- and vote-method-level; each
row carries the true source_file + sheet.  Consumed directly (summing precinct rows -- the
file has NO 'Total'/'Cumulative' precinct rows, so there is no double-count risk) for:
    * 2023 general (D1/D3/D5) and 2023 primary (D1/D3)
    * 2025 general (Mayor/D2/D4/D3-special) and 2025 primary (Mayor/D2/D3-special)

The DUPLICATE contest labels the long file carries (UPPER-CASE vs Mixed-Case, e.g.
"MURRAY CITY COUNCIL DISTRICT 1" and "Murray City Council District 1" in 2023) are NOT
duplicates of the same election -- they are the **general** vs the **primary**, carrying
different `election_type` values and different candidate sets.  Keying every race on
(year, election_type, canonical_contest) keeps them distinct with no double-count.

ONE recovered contest set -- 2021 general (Mayor/D2/D4)
--------------------------------------------------------------------------------------
In the long file the 2021 general is present only at the In-Person / Vote-By-Mail method
split, and the small In-Person cells are privacy-SUPPRESSED (D2 100%, D4 20/36, Mayor
152/208 rows blanked with '****').  Summing the surviving cells would publish a severe
undercount (e.g. Mayor Hales 983 when the true total is ~7-8k).  The unsuppressed
per-precinct **`Total`** sub-rows live in the raw county SOVC workbook, already mirrored
locally (NOT re-downloaded):

    ~/Desktop/slco-election-archive/raw/2021/november-2-2021-general-election-statement-of-votes-cast.xlsx
    Sheet24 = Mayor, Sheet25 = Council District 2, Sheet26 = Council District 4

so the 2021 general is recovered from those Total rows (identical method to the sibling
south_jordan build).  This is the SAME county SOVC provenance chain -- just the un-redacted
precinct totals the long-file method-split destroys.

Reproducible:  python3 clean_elections.py            (writes the 3 CSVs)
               python3 clean_elections.py --report    (per-race summary)
"""
import os, re, csv, sys, openpyxl

OUT = os.path.dirname(os.path.abspath(__file__))
LONG = '/Users/tysonwelsh/civic-data/salt_lake_county/elections/slco_municipal_results_long.csv'
XLSX_2021 = os.path.expanduser(
    '~/Desktop/slco-election-archive/raw/2021/'
    'november-2-2021-general-election-statement-of-votes-cast.xlsx')
YEARS = {'2021', '2023', '2025'}
REPORT = '--report' in sys.argv


# --------------------------------------------------------------------------- helpers
def norm_name(s):
    """Normalize a candidate name ALONGSIDE the verbatim value (never overwrites raw):
    collapse whitespace, drop leading registered-write-in '*', strip the (NP)/(NON)
    non-partisan tag, canonicalize write-ins."""
    s = re.sub(r'\s+', ' ', str(s).replace('\n', ' ')).strip()
    s = s.lstrip('*').strip()
    s = re.sub(r'\s*\(\s*(?:NP|NON)\s*\)', '', s, flags=re.I)
    s = re.sub(r'\bUNRESOLVED\s+WRITE[- ]?IN\b', 'Write-in (unresolved)', s, flags=re.I)
    s = re.sub(r'\bWRITE[- ]?IN\b', 'Write-in', s, flags=re.I)
    return re.sub(r'\s+', ' ', s).strip()


def to_int(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return int(v)
    s = str(v).strip().replace(',', '')
    return int(float(s)) if re.fullmatch(r'-?\d+(?:\.\d+)?', s) else None


def canon(label):
    """Map a county Murray contest label to (office, district, canonical_contest, special)."""
    U = label.upper()
    if 'MAYOR' in U:
        return ('Mayor', '', 'Murray City Mayor', False)
    special = '2 YEAR' in U or '2-YEAR' in U
    m = re.search(r'DIST(?:RICT)?\s*(\d+)', U) or re.search(r'\b(\d+)\b', U)
    d = m.group(1) if m else '?'
    contest = f'Murray City Council District {d}'
    if special:
        contest += ' (2-Year Term)'
    return ('Council', d, contest, special)


# --------------------------------------------------------------------------- containers
RECORDS = {}   # key = (year, election_type, canonical_contest) -> record


def rec(year, etype, label, source_file):
    office, district, contest, special = canon(label)
    k = (year, etype, contest)
    if k not in RECORDS:
        RECORDS[k] = dict(year=year, election_type=etype, office=office, district=district,
                          contest=contest, verbatim=label, special=special,
                          cand={}, per={}, reg={}, ballots={},
                          suppressed_any=False, source_file=source_file)
    return RECORDS[k]


def add_vote(R, precinct, cand, votes):
    """votes=None marks a privacy-suppressed cell."""
    R['cand'][cand] = R['cand'].get(cand, 0) + (votes or 0)
    R['per'].setdefault(precinct, {})
    cur = R['per'][precinct].get(cand)
    if votes is None:
        R['suppressed_any'] = True
        if cand not in R['per'][precinct]:
            R['per'][precinct][cand] = None
    else:
        R['per'][precinct][cand] = (cur or 0) + votes if isinstance(cur, int) else votes


# --------------------------------------------------------------------------- (1) long file
SKIP = {('2021', 'municipal general')}   # recovered from raw xlsx instead (suppression)


def load_long():
    # Collapse rows that are IDENTICAL across every field.  The 2023 PRIMARY sheets export
    # each precinct x candidate row THREE times verbatim (a county-file artifact, not three
    # ballot batches); left un-deduped it triples the primary totals.  A genuine boundary-
    # split precinct (e.g. 2023 general MUR047, which straddles a district line) differs in
    # votes or times_cast between its two portions, so it is NOT collapsed and still sums.
    seen = set()
    with open(LONG, newline='') as fh:
        for row in csv.DictReader(fh):
            if 'MURRAY' not in row['contest'].upper():
                continue
            year = row['year'].strip()
            if year not in YEARS:
                continue
            etype = row['election_type'].strip()
            if (year, etype) in SKIP:
                continue
            sig = (year, etype, row['contest'], row['precinct'], row['candidate'],
                   row['vote_method'], row['votes'], row['times_cast'],
                   row['registered_voters'], row['suppressed'])
            if sig in seen:
                continue
            seen.add(sig)
            R = rec(year, etype, row['contest'], row['source_file'])
            prec = row['precinct'].strip()
            cand = norm_name(row['candidate'])
            v = row['votes'].strip()
            supp = row['suppressed'].strip().lower() == 'true'
            votes = None if (supp or v in ('', 'nan')) else int(float(v))
            add_vote(R, prec, cand, votes)
            reg = row['registered_voters'].strip()
            if reg not in ('', 'nan'):
                R['reg'][prec] = max(R['reg'].get(prec, 0), int(float(reg)))
            tc = row['times_cast'].strip()
            if tc not in ('', 'nan'):
                # key ballots by (precinct, method) so split-method precincts sum both
                # methods while an 'ALL' precinct counts once
                bk = (prec, row['vote_method'].strip())
                R['ballots'][bk] = max(R['ballots'].get(bk, 0), int(float(tc)))


# --------------------------------------------------------------------------- (2) 2021 raw xlsx
def parse_2021(path):
    """Each precinct block: In Person / Vote By Mail (small cells '****'-suppressed) then a
    'Total' sub-row carrying the UN-suppressed precinct count.  Candidate value columns sit
    to the right of a second 'Precinct' marker; their pct columns have blank headers."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    SHEETS = {'Sheet24': 'MURRAY CITY MAYOR',
              'Sheet25': 'MURRAY CITY COUNCIL DISTRICT 2',
              'Sheet26': 'MURRAY CITY COUNCIL DISTRICT 4'}
    PREC = re.compile(r'MUR\d+[A-Z]?$')
    BLOCK = re.compile(r'PRECINCT|TIMES CAST|REGISTER|TOTAL VOTES|CARDS|UNDER|OVER', re.I)
    for sh, label in SHEETS.items():
        ws = wb[sh]
        rows = [list(x) for x in ws.iter_rows(values_only=True)]
        hi = next(i for i, r in enumerate(rows)
                  if r and str(r[0]).strip() == 'Precinct')
        hdr = rows[hi]
        tcj = next((j for j, c in enumerate(hdr) if c and 'Times Cast' in str(c)), None)
        rgj = next((j for j, c in enumerate(hdr) if c and 'Register' in str(c)), None)
        cand_cols = {}
        for j, c in enumerate(hdr):
            if c in (None, ''):
                continue
            L = re.sub(r'\s+', ' ', str(c).replace('\n', ' ')).strip()
            if BLOCK.search(L) or L.endswith('%'):
                continue
            cand_cols[j] = norm_name(c)
        R = rec('2021', 'municipal general', label, os.path.basename(path))
        cur = None
        for r in rows[hi + 1:]:
            c0 = str(r[0]).strip() if r and r[0] is not None else ''
            if PREC.match(c0):
                cur = c0
                R['per'].setdefault(cur, {})
            elif c0 == 'Total' and cur is not None:
                for j, name in cand_cols.items():
                    add_vote(R, cur, name, to_int(r[j]) if j < len(r) else None)
                if tcj is not None and to_int(r[tcj]) is not None:
                    R['ballots'][(cur, 'Total')] = to_int(r[tcj])
                if rgj is not None and to_int(r[rgj]) is not None:
                    R['reg'][cur] = to_int(r[rgj])
                cur = None


# --------------------------------------------------------------------------- run
load_long()
parse_2021(XLSX_2021)


# --------------------------------------------------------------------------- compute + write
def real_cands(items):
    return [(n, v) for n, v in items
            if not (n.startswith('Write-in') and (v or 0) == 0)]


races, by_cand, by_precinct = [], [], []
for k in sorted(RECORDS):
    R = RECORDS[k]
    items = sorted(R['cand'].items(), key=lambda kv: (-(kv[1] or 0), kv[0]))
    rc = real_cands(items)
    total = sum(v or 0 for v in R['cand'].values())
    winner, wv = items[0] if items else ('', 0)
    runner, rv = (items[1] if len(items) > 1 else ('', 0))
    margin = (wv or 0) - (rv or 0)
    reg_total = sum(R['reg'].values()) if R['reg'] else ''
    ballots_total = sum(R['ballots'].values()) if R['ballots'] else ''
    turnout = (round(100 * ballots_total / reg_total, 2)
               if isinstance(ballots_total, int) and isinstance(reg_total, int) and reg_total
               else '')
    notes = []
    if R['special']:
        notes.append('Unexpired-term SPECIAL (2-year term)')
    if R['suppressed_any']:
        notes.append('some precinct cells privacy-suppressed in county SOVC')
    races.append(dict(
        year=R['year'], election_type=R['election_type'], office=R['office'],
        district=R['district'], contest=R['contest'], contest_verbatim=R['verbatim'],
        n_seats=1, n_candidates=len(rc), voting_method='plurality',
        total_votes=total, total_first_choice_votes='',
        winner=winner, winner_votes=wv,
        winner_pct=round(100 * (wv or 0) / total, 2) if total else 0,
        runner_up=runner, runner_up_votes=rv,
        margin_votes=margin, margin_pct=round(100 * margin / total, 2) if total else 0,
        registered_voters=reg_total, ballots_cast=ballots_total, turnout_pct=turnout,
        uncontested='True' if len(rc) <= 1 else 'False',
        suppressed_precincts='True' if R['suppressed_any'] else 'False',
        note='; '.join(notes), source_file=R['source_file']))
    for rank, (name, v) in enumerate(items, 1):
        by_cand.append(dict(
            year=R['year'], election_type=R['election_type'], office=R['office'],
            district=R['district'], contest=R['contest'], candidate=name,
            votes=v if v is not None else '',
            pct=round(100 * (v or 0) / total, 2) if total else 0,
            rank=rank, is_winner='True' if rank == 1 else 'False'))
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


writecsv('murray_races.csv', races,
         ['year', 'election_type', 'office', 'district', 'contest', 'contest_verbatim',
          'n_seats', 'n_candidates', 'voting_method', 'total_votes',
          'total_first_choice_votes', 'winner', 'winner_votes', 'winner_pct', 'runner_up',
          'runner_up_votes', 'margin_votes', 'margin_pct', 'registered_voters',
          'ballots_cast', 'turnout_pct', 'uncontested', 'suppressed_precincts', 'note',
          'source_file'])
writecsv('murray_results_by_candidate.csv', by_cand,
         ['year', 'election_type', 'office', 'district', 'contest', 'candidate',
          'votes', 'pct', 'rank', 'is_winner'])
writecsv('murray_results_by_precinct.csv', by_precinct,
         ['year', 'election_type', 'office', 'district', 'contest', 'precinct',
          'candidate', 'votes', 'suppressed'])

gen = [r for r in races if r['election_type'] == 'municipal general']
pri = [r for r in races if r['election_type'] == 'municipal primary']
print(f"races: {len(races)}  (general {len(gen)}, primary {len(pri)})")
print(f"by_candidate rows: {len(by_cand)}   by_precinct rows: {len(by_precinct)}")
if REPORT:
    for r in sorted(races, key=lambda x: (x['year'], x['election_type'], x['contest'])):
        tag = 'PRI ' if 'primary' in r['election_type'] else 'GEN '
        unc = ' [UNCONTESTED]' if r['uncontested'] == 'True' else ''
        sup = ' [suppressed]' if r['suppressed_precincts'] == 'True' else ''
        to = f" turnout {r['turnout_pct']}%" if r['turnout_pct'] != '' else ''
        print(f"  {r['year']} {tag}{r['contest']:38s} n={r['n_candidates']} "
              f"WIN {r['winner']} {r['winner_votes']} ({r['winner_pct']}%) vs "
              f"{r['runner_up']} {r['runner_up_votes']}  margin {r['margin_votes']} "
              f"[tot {r['total_votes']}{to}]{unc}{sup}")
