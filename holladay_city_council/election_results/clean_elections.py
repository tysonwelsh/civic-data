#!/usr/bin/env python3
"""Build Holladay City (Salt Lake County, UT) election_results.

Holladay is a **Council-Manager** city with a **5-member council elected by DISTRICT
(Districts 1-5)** plus a **Mayor elected at-large** (citywide). 4-yr staggered terms:

  * Cycle A (Mayor + District 1 + District 3): 2009, 2013, 2017, 2021, 2025
  * Cycle B (Districts 2, 4, 5):               2007, 2011, 2015, 2019, 2023

(In 2007 the county labelled the B seats "HOLLADAY CITY COUNCIL 2/4/5"; from 2009 on the
label drifted through "...COUNCIL DIST N" / "...CNCL DIST N" / "CITY OF HOLLADAY COUNCIL
DISTRICT N" -- all normalize to "Holladay City Council District N".)  The Mayor is elected
only on the A cycle.

SOURCES
-------
1. PRIMARY  -- the repo-canonical county SOVC normalization:
     /Users/tysonwelsh/civic-data/salt_lake_county/elections/slco_municipal_results_long.csv
   filtered to contest LIKE '%HOLLADAY%'.  Precinct- and vote-method-level; every year
   EXCEPT 2021 sums cleanly (zero suppression) to contest totals.  Consumed directly for
   2007/2009/2011/2013/2015/2017 (+ their primaries) and the 2023 & 2025 generals + the
   2025 mayoral primary.  (2025 rows carry a single 'ALL' method already aggregated.)

2. RAW re-parse (Salt Lake County Clerk SOVC spreadsheets in the local archive mirror
   ~/Desktop/slco-election-archive -- NOT re-downloaded) for the two contests the canonical
   layer does not deliver cleanly:
     * 2019 general (Dist 2/4/5) -- ABSENT from the canonical file: the SLCo normalizer keyed
       the contest off the raw sheet name "HOL Council N", so a '%HOLLADAY%' filter never
       matched it.  RECOVERED from raw/historical-election-results/2019-11-05-general-
       election-sovc.xlsx (sheets 'HOL Council 2/4/5').
     * 2021 general (Mayor/D1/D3) -- present in the canonical file but privacy-SUPPRESSED at
       the In-Person / Vote-By-Mail method split (**** cells).  RE-PARSED from
       raw/2021/november-2-2021-general-election-statement-of-votes-cast.xlsx (Sheets 16/17/
       18), whose per-precinct 'Total' sub-rows are NOT suppressed.

2019 municipal PRIMARY: the raw 2019 primary SOVC contains NO Holladay sheet (checked) ->
Holladay held no 2019 primary (each Cycle-B seat drew <=2 candidates). Logged, not fabricated.

2023 general: only District 4 appears (Quinn vs Tracy). Districts 2 & 5 drew a single
candidate each and were UNCONTESTED -- Salt Lake County omits uncontested municipal seats
from the ballot/SOVC, so there is no row to recover (a true no-contest, not a data gap).

Reproducible:  python3 clean_elections.py            (writes the 3 CSVs)
               python3 clean_elections.py --report    (+ per-race summary)
"""
import os, re, csv, sys, openpyxl

OUT = os.path.dirname(os.path.abspath(__file__))
CANON = '/Users/tysonwelsh/civic-data/salt_lake_county/elections/slco_municipal_results_long.csv'
ARCHIVE = os.path.expanduser('~/Desktop/slco-election-archive')


def _raw(name, *archive_rel):
    """Prefer a retained local copy under raw/; fall back to the county archive mirror."""
    local = os.path.join(OUT, 'raw', name)
    return local if os.path.exists(local) else os.path.join(ARCHIVE, *archive_rel)


SOVC_2019 = _raw('2019-11-05-general-election-sovc.xlsx',
                 'raw', 'historical-election-results', '2019-11-05-general-election-sovc.xlsx')
SOVC_2021 = _raw('november-2-2021-general-election-statement-of-votes-cast.xlsx',
                 'raw', '2021', 'november-2-2021-general-election-statement-of-votes-cast.xlsx')
REPORT = '--report' in sys.argv


# --------------------------------------------------------------------------- helpers
def g(r, j):
    return r[j] if (r is not None and j < len(r)) else None


def norm_name(s):
    """Normalize a candidate name ALONGSIDE the verbatim value (never overwrites raw):
    collapse whitespace, strip the (NP) non-partisan tag, canonicalize write-ins."""
    s = re.sub(r'\s+', ' ', str(s).replace('\n', ' ')).strip()
    s = s.lstrip('*').strip()
    s = re.sub(r'\s*\(\s*(?:NP|NON)\s*\)', '', s, flags=re.I)   # strip (NP)/(NON)/(NP )
    s = re.sub(r'\bUNRESOLVED\s+WRITE[- ]?IN\b', 'Write-in (unresolved)', s, flags=re.I)
    s = re.sub(r'\bWRITE[- ]?IN\b', 'Write-in', s, flags=re.I)
    return re.sub(r'\s+', ' ', s).strip().strip('"').strip()


def to_int(v):
    return int(v) if isinstance(v, (int, float)) else None


# ---- contest canonicalization ----------------------------------------------
def canon(label):
    """Map any county contest label to (office, district, canonical_contest)."""
    U = re.sub(r'\s+', ' ', str(label).replace('\n', ' ')).strip().upper()
    if 'MAYOR' in U:
        return ('Mayor', '', 'Holladay City Mayor')
    m = (re.search(r'DIST(?:RICT)?\s*#?\s*(\d+)', U)
         or re.search(r'#\s*(\d+)', U)
         or re.search(r'(\d+)\s*$', U))
    d = m.group(1) if m else '?'
    return ('Council', d, f'Holladay City Council District {d}')


# --------------------------------------------------------------------------- containers
RECORDS = {}          # key = (year, election_type, contest) -> record dict


def rec(year, etype, label, source_file):
    office, district, contest = canon(label)
    k = (year, etype, contest)
    if k not in RECORDS:
        RECORDS[k] = dict(year=year, election_type=etype, office=office,
                          district=district, contest=contest,
                          cand={}, per={}, reg={}, ballots={},
                          suppressed_any=False, source_file=source_file,
                          verbatim=str(label).strip())
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


# --------------------------------------------------------------------------- (1) canonical slice
SLICE_SKIP = {('2021', 'municipal general')}     # re-parsed from raw (suppression)


def load_canonical():
    with open(CANON, newline='') as fh:
        for row in csv.DictReader(fh):
            if 'holladay' not in row['contest'].lower():
                continue
            year = str(int(float(row['year'])))
            etype = row['election_type']
            if (year, etype) in SLICE_SKIP:
                continue
            R = rec(year, etype, row['contest'], os.path.basename(row['source_file']))
            prec = row['precinct'].strip()
            cand = norm_name(row['candidate'])
            v = row['votes'].strip()
            supp = row['suppressed'].strip().lower() == 'true'
            votes = None if (supp or v in ('', 'nan')) else int(float(v))
            add_vote(R, prec, cand, votes)
            reg = row['registered_voters'].strip()
            tc = row['times_cast'].strip()
            if reg not in ('', 'nan'):
                R['reg'][prec] = max(R['reg'].get(prec, 0), int(float(reg)))
            if tc not in ('', 'nan'):
                R['ballots'][prec] = max(R['ballots'].get(prec, 0), int(float(tc)))


# --------------------------------------------------------------------------- (2a) 2019 raw
def parse_2019_general(path):
    """2019 SOVC 'HOL Council N' sheets: row0 = contest title; row1 = candidate names sparse
    across the header (one per block); row2 = sub-header where each candidate's total sits
    under 'Total Votes'; precinct rows (col0 == HOL###) follow, col1 == Registered Voters."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    PR = re.compile(r'HOL\d+')
    for sh in wb.sheetnames:
        if not sh.upper().startswith('HOL COUNCIL'):
            continue
        ws = wb[sh]
        rows = [list(x) for x in ws.iter_rows(values_only=True)]
        title = str(g(rows[0], 0)).strip()
        name_row, sub_row = rows[1], rows[2]
        tv_cols = [j for j, v in enumerate(sub_row) if str(v).strip() == 'Total Votes']
        # pair each candidate name with the first 'Total Votes' column at/after its position
        cand_tv = []
        for j, v in enumerate(name_row):
            if v in (None, ''):
                continue
            tvj = next((t for t in tv_cols if t >= j), None)
            if tvj is not None:
                cand_tv.append((norm_name(v), tvj))
        regj = next((j for j, v in enumerate(sub_row)
                     if 'Registered' in str(v)), None)
        R = rec('2019', 'municipal general', title, os.path.basename(path))
        for r in rows[3:]:
            c0 = g(r, 0)
            if isinstance(c0, str) and PR.fullmatch(c0.strip()):
                prec = c0.strip()
                for name, tvj in cand_tv:
                    add_vote(R, prec, name, to_int(g(r, tvj)))
                if regj is not None and to_int(g(r, regj)) is not None:
                    R['reg'][prec] = to_int(g(r, regj))


# --------------------------------------------------------------------------- (2b) 2021 raw
def parse_2021_general(path, sheets):
    """2021 columnar layout: a left block (col0 Precinct / col1 Times Cast / col2 Registered)
    and a right block after a second 'Precinct' marker holding candidate value columns (each
    followed by a % column).  Each precinct has In Person / Vote By Mail method sub-rows
    (**** suppressed) and a 'Total' sub-row with the UN-suppressed precinct count."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    PR = re.compile(r'HOL\d+')
    NONCAND = {'PRECINCT', 'TIMES CAST', 'REGISTERED VOTERS', 'TOTAL VOTES', 'TOTAL', ''}
    for sh in sheets:
        ws = wb[sh]
        rows = [list(x) for x in ws.iter_rows(values_only=True)]
        title = re.sub(r'\s*\(Vote.*', '', str(g(rows[1], 0))).strip()
        hi = next(i for i, r in enumerate(rows) if str(g(r, 0)).strip() == 'Precinct')
        hdr = rows[hi]
        # candidate value columns live in the right block (index >= the 2nd 'Precinct')
        pmarks = [j for j, c in enumerate(hdr) if str(c).strip() == 'Precinct']
        right = pmarks[1] if len(pmarks) > 1 else 0
        cand_cols = {}
        for j in range(right + 1, len(hdr)):
            c = hdr[j]
            if c in (None, ''):
                continue
            L = re.sub(r'\s+', ' ', str(c).replace('\n', ' ')).strip().upper()
            L = re.sub(r'\s*\(NP\s*\)', '', L).strip()
            if L not in NONCAND and not L.endswith('%'):
                cand_cols[j] = norm_name(c)
        R = rec('2021', 'municipal general', title, os.path.basename(path))
        cur = None
        for r in rows[hi + 1:]:
            c0 = str(g(r, 0)).strip() if g(r, 0) is not None else ''
            if PR.fullmatch(c0):
                cur = c0
                R['per'].setdefault(cur, {})
            elif c0 == 'Total' and cur is not None:
                for j, name in cand_cols.items():
                    add_vote(R, cur, name, to_int(g(r, j)))
                if to_int(g(r, 1)) is not None:
                    R['ballots'][cur] = to_int(g(r, 1))
                if to_int(g(r, 2)) is not None:
                    R['reg'][cur] = to_int(g(r, 2))
                cur = None


# --------------------------------------------------------------------------- run loaders
load_canonical()
parse_2019_general(SOVC_2019)
parse_2021_general(SOVC_2021, ['Sheet16', 'Sheet17', 'Sheet18'])


# --------------------------------------------------------------------------- compute + write
def real_cands(items):
    return [(n, v) for n, v in items
            if not (n.startswith('Write-in') and (v or 0) == 0)]


races, by_cand, by_precinct = [], [], []
mismatches = 0
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
               if (isinstance(ballots_total, int) and isinstance(reg_total, int) and reg_total)
               else '')
    # reconcile by-precinct sum -> by-candidate total (non-suppressed)
    for name, cv in R['cand'].items():
        psum = sum(R['per'][p].get(name) or 0 for p in R['per'])
        if not R['suppressed_any'] and psum != (cv or 0):
            mismatches += 1
            print(f"  ! precinct-sum mismatch {k} {name}: cand={cv} precsum={psum}")
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


writecsv('holladay_races.csv', races,
         ['year', 'election_type', 'office', 'district', 'contest', 'contest_verbatim',
          'n_seats', 'n_candidates', 'voting_method', 'total_votes',
          'total_first_choice_votes', 'winner', 'winner_votes', 'winner_pct', 'runner_up',
          'runner_up_votes', 'margin_votes', 'margin_pct', 'registered_voters',
          'ballots_cast', 'turnout_pct', 'uncontested', 'suppressed_precincts', 'note',
          'source_file'])
writecsv('holladay_results_by_candidate.csv', by_cand,
         ['year', 'election_type', 'office', 'district', 'contest', 'candidate',
          'votes', 'pct', 'rank', 'is_winner'])
writecsv('holladay_results_by_precinct.csv', by_precinct,
         ['year', 'election_type', 'office', 'district', 'contest', 'precinct',
          'candidate', 'votes', 'suppressed'])

# --------------------------------------------------------------------------- report
gen = [r for r in races if r['election_type'] == 'municipal general']
pri = [r for r in races if r['election_type'] == 'municipal primary']
print(f"races: {len(races)}  (general {len(gen)}, primary {len(pri)})")
print(f"by_candidate rows: {len(by_cand)}   by_precinct rows: {len(by_precinct)}")
print(f"precinct-sum reconciliation mismatches: {mismatches}")
if REPORT:
    for r in sorted(races, key=lambda x: (x['year'], x['election_type'], x['contest'])):
        tag = 'PRIMARY ' if r['election_type'] == 'municipal primary' else ''
        unc = ' [UNCONTESTED]' if r['uncontested'] == 'True' else ''
        sup = ' [suppressed]' if r['suppressed_precincts'] == 'True' else ''
        to = f" turnout {r['turnout_pct']}%" if r['turnout_pct'] != '' else ''
        print(f"  {r['year']} {tag}{r['contest']:34s} n={r['n_candidates']} "
              f"WIN {r['winner']} {r['winner_votes']} ({r['winner_pct']}%) vs "
              f"{r['runner_up']} {r['runner_up_votes']}  margin {r['margin_votes']} "
              f"[tot {r['total_votes']}{to}]{unc}{sup}")
