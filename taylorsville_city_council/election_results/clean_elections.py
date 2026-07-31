#!/usr/bin/env python3
"""Build Taylorsville City (Salt Lake County, UT) election_results.

Taylorsville is a **Council-Mayor (executive-mayor) city**: **5 council DISTRICTS (1-5)
+ a separately elected Mayor** (citywide). 4-yr staggered, non-partisan terms. As the
contests appear in the Salt Lake County Statement-of-Votes-Cast (SOVC) files, the stagger
is:

  * Cycle A (Mayor + District 4 + District 5): 2009, 2013, 2017, 2021, 2025
  * Cycle B (Districts 1, 2, 3):               2007, 2011, 2015, 2019, 2023

**TWO out-of-cycle District 3 SPECIAL / unexpired-term races** show up (District 3's
regular cycle is Cycle B, so a D3 contest in a Cycle-A year is a special):
  * 2013 D3 -- the 2011 D3 winner (Jerry Rechtenbach) ran for Mayor in 2013 (he is the
    2013 Mayor runner-up), vacating D3; Brad Christopherson won the balance, then the full
    D3 term in 2015.
  * 2021 D3 -- the 2019 D3 winner (Christopherson) vacated; Anna Barbieri won the balance,
    then the full D3 term in 2023.
Both are flagged distinctly in the `note` column of `taylorsville_races.csv` (neither is a
permanent cycle shift).

The Mayor is elected only on the **A** cycle. Contest labels drift year to year
(`TAYLORSVILLE CITY COUNCIL 1`, `TAYLORSVILLE COUNCIL DISTRICT 4`, `Taylorsville City Coun
2`, `TAYLORSVILLE CITY CNCL DIST 4`, `CITY OF TAYLORSVILLE COUNCIL DISTRICT 3`, ...); all
normalize to `Taylorsville City Council District N` / `Taylorsville City Mayor`. The
Taylorsville-Bennion **Improvement District** contests (a separate special district, not
the city council/mayor) are excluded.

SOURCES  (Salt Lake County Clerk, mirrored locally in ~/Desktop/slco-election-archive)
--------------------------------------------------------------------------------------
Two provenance layers:

1. The county canonical long file --
      salt_lake_county/elections/slco_municipal_results_long.csv
      (the county-clerk SOVC held ONCE at the level where it originates; built by the
      archive's scripts/normalize_sovc.py from the raw spreadsheets). Read DIRECTLY here
      and filtered to Taylorsville council+mayor contests. Precinct- and vote-method-level;
      sums cleanly to contest totals with ZERO suppression for 2007/2009/2011/2013/2015/2017
      (+ their primaries), the **2019 municipal primary (District 1)**, and the 2023 & 2025
      generals. Those contests are consumed straight from this file.
      (**Re-point 2026-07-19:** the old redundant per-city copy
      raw/municipal_results_long_taylorsville.csv was retired after verifying the
      re-pointed build reproduces all three CSVs byte-identically; the
      `precinct='Cumulative'` workbook-rollup rows the county canonical now labels are
      excluded -- never a precinct; the 2019 general the canonical carries only under the
      raw sheet code "TAY Council N" is skipped in the long-file read because the raw
      parser below recovers it with faithful district numbers + the in-cell contest label.)

2. raw/sovc/*.xlsx  (the true county SOVC spreadsheets)
      Re-parsed directly for the TWO contests the long file does not deliver cleanly:
        * 2019 general (Districts 1/2/3) -- present in the long file only under the raw
          SHEET code "TAY Council N" (the normalizer keyed the contest off the sheet name,
          which lacks "TAYLORSVILLE", so a %TAYLORSVILLE% contest filter misses it).
          RECOVERED from raw (the in-cell contest label IS
          "TAYLORSVILLE CITY COUNCIL DISTRICT N").
        * 2021 general (Mayor/D3/D4/D5) -- present in the long file but privacy-SUPPRESSED
          ('****') at the In-Person/Vote-By-Mail method split, which destroys the precinct
          totals. RE-PARSED from raw, whose per-precinct 'Total' sub-rows are NOT suppressed.

2019 municipal PRIMARY (District 1): a primary WAS held -- District 1 drew 3 candidates
(Burgess / Gehrke / Quigley), triggering it. The county canonical carries it
(Burgess 728 / Gehrke 371 / Quigley 229, from 2019-08-13-municipal-primary-sovc.xlsx,
cell-verified against the raw workbook); ADOPTED into the audited layer 2026-07-19,
correcting the prior "no 2019 primary" claim. The primary's top-2 (Burgess, Gehrke) are
exactly the 2019 D1 general's two candidates -- an internal cross-corroboration. The other
Cycle-B districts (D2 = 2 candidates, D3 = 1) drew no primary, and 2007/2009/2015/2023/2025
likewise drew <=2 per seat -> no primary those cycles. Logged, not fabricated.

Reproducible:  python3 clean_elections.py            (reads the county canonical, writes the 3 CSVs)
               python3 clean_elections.py --report    (prints a per-race summary)
"""
import os, re, csv, sys, openpyxl

OUT = os.path.dirname(os.path.abspath(__file__))
# The long-format canvass is consumed DIRECTLY from the Salt Lake County canonical
# (salt_lake_county/elections/slco_municipal_results_long.csv) -- the county-clerk SOVC held
# once at the level where it originates. The old per-city redundant copy
# (raw/municipal_results_long_taylorsville.csv) was retired 2026-07-19 (re-point verified
# byte-identical). The raw SOVC spreadsheets under raw/sovc/ remain the source for the two
# generals the long file does not deliver cleanly for Taylorsville (2019 + 2021 general).
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
    s = re.sub(r'\s*\(\s*(?:NP|NON)\s*\)', '', s, flags=re.I)  # strip (NP)/(NON) tag
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
        return ('Mayor', '', 'Taylorsville City Mayor')
    m = re.search(r'DIST(?:RICT)?\s*(\d+)', U) or re.search(r'(\d+)\s*$', U.strip())
    d = m.group(1) if m else '?'
    return ('Council', d, f'Taylorsville City Council District {d}')


def is_taylorsville_council_or_mayor(label):
    U = label.upper()
    if 'TAYLORSVILLE' not in U:
        return False
    if any(x in U for x in ('IMPROVE', 'TRUSTEE', 'BENNION')):
        return False          # Taylorsville-Bennion Improvement District != city council/mayor
    if 'MAYOR' in U:
        return True
    return bool(re.search(r'(COUNCIL|COUN|CNCL)', U))


# Out-of-cycle District 3 special / unexpired-term races (see module docstring). District
# 3's REGULAR cycle is 2007/2011/2015/2019/2023 (Cycle B), so any D3 contest in an even-
# other odd year (2013, 2021) is a special election to fill an unexpired term:
SPECIAL_NOTES = {
    (2013, 'Council', '3'): ('special / unexpired-term election (out-of-cycle for the '
                             'D1/D2/D3 group; the 2011 D3 winner Rechtenbach ran for Mayor '
                             'in 2013 - see the 2013 Mayor runner-up - vacating D3; '
                             'Christopherson won this balance, then the full D3 term in 2015)'),
    (2021, 'Council', '3'): ('special / unexpired-term election (out-of-cycle for the '
                             'D1/D2/D3 group; the 2019 D3 winner Christopherson vacated - '
                             'Barbieri won this balance, then the full D3 term in 2023)'),
}


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


def load_slice():
    with open(SLICE, newline='') as fh:
        for row in csv.DictReader(fh):
            year = int(float(row['year']))
            contest_raw = row['contest']
            if year in SLICE_SKIP_YEARS:
                continue
            if contest_raw.upper().startswith('TAY '):
                continue           # 2019 general "TAY Council N" sheet code -> parsed from raw instead
            if not is_taylorsville_council_or_mayor(contest_raw):
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
def parse_2019_general(path):
    """2019 'Family-A' wide crosstab (Taylorsville sheets 'TAY Council N'): row0 = contest
    label; row1 = candidate names sparse across the header; row2 sub-header marks each
    candidate total with 'Total Votes' and registered voters with 'Registered Voters';
    precinct rows (col0 == TAY###) follow."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    PR = re.compile(r'TAY\d+')
    for sh in wb.sheetnames:
        if not sh.upper().startswith('TAY'):
            continue
        ws = wb[sh]
        rows = [list(x) for x in ws.iter_rows(values_only=True)]
        label = str(g(rows[0], 0))               # in-cell "TAYLORSVILLE CITY COUNCIL DISTRICT N"
        name_row, sub_row = rows[1], rows[2]
        cand_cols = [(j, norm_name(name_row[j])) for j in range(len(name_row))
                     if name_row[j] not in (None, '')]
        tv_cols = [j for j, v in enumerate(sub_row) if str(v).strip() == 'Total Votes']
        cands = [n for _, n in cand_cols]
        cand_tv = dict(zip(cands, tv_cols))
        regj = next((j for j, v in enumerate(sub_row) if 'Registered' in str(v)), None)
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


def parse_2021_general(path):
    """2021 columnar: a second 'Precinct' marker precedes candidate columns; each precinct
    has In Person / Vote By Mail method sub-rows (small counts '****' suppressed) and a
    'Total' sub-row with the UN-suppressed precinct count. Auto-detects the Taylorsville
    council/mayor sheets (excludes the Improvement District)."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    PR = re.compile(r'TAY\d+')
    for sh in wb.sheetnames:
        ws = wb[sh]
        rows = [list(x) for x in ws.iter_rows(values_only=True)]
        title = None
        for r in rows[:4]:
            v = g(r, 0)
            if v and 'TAYLORSVILLE' in str(v).upper():
                title = str(v)
        if not title or not is_taylorsville_council_or_mayor(title):
            continue
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
        clean_title = re.sub(r'\s*\(Vote.*', '', title).strip()
        R = rec(2021, 'municipal general', clean_title, os.path.basename(path))
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
parse_2019_general(os.path.join(SOVC, '2019-11-05-general-election-sovc.xlsx'))
parse_2021_general(os.path.join(SOVC, '2021-11-02-general-election-sovc.xlsx'))


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
               if (isinstance(ballots_total, int) and isinstance(reg_total, int) and reg_total) else '')
    note = SPECIAL_NOTES.get((R['year'], R['office'], R['district']), '')
    # precinct-sum reconciliation check (skip races with any suppressed cell)
    if not R['suppressed_any']:
        for name, tot_v in R['cand'].items():
            psum = sum((R['per'][p].get(name) or 0) for p in R['per'])
            if psum != (tot_v or 0):
                mismatches += 1
                print(f"  !! RECON MISMATCH {R['year']} {R['contest']} {name}: "
                      f"cand={tot_v} precinct_sum={psum}", file=sys.stderr)
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
        note=note, source_file=R['source_file']))
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


writecsv('taylorsville_races.csv', races,
         ['year', 'election_type', 'office', 'district', 'contest', 'contest_verbatim',
          'n_seats', 'n_candidates', 'voting_method', 'total_votes',
          'total_first_choice_votes', 'winner',
          'winner_votes', 'winner_pct', 'runner_up', 'runner_up_votes', 'margin_votes',
          'margin_pct', 'registered_voters', 'ballots_cast', 'turnout_pct',
          'uncontested', 'suppressed_precincts', 'note', 'source_file'])
writecsv('taylorsville_results_by_candidate.csv', by_cand,
         ['year', 'election_type', 'office', 'district', 'contest', 'candidate',
          'votes', 'pct', 'rank', 'is_winner'])
writecsv('taylorsville_results_by_precinct.csv', by_precinct,
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
        sup = ' [suppressed-precincts]' if r['suppressed_precincts'] == 'True' else ''
        sp = ' [D3 SPECIAL]' if r['note'] else ''
        to = f" turnout {r['turnout_pct']}%" if r['turnout_pct'] != '' else ''
        print(f"  {r['year']} {tag}{r['contest']:36s} n={r['n_candidates']} "
              f"WIN {r['winner']} {r['winner_votes']} ({r['winner_pct']}%) vs "
              f"{r['runner_up']} {r['runner_up_votes']}  margin {r['margin_votes']} "
              f"[tot {r['total_votes']}{to}]{unc}{sup}{sp}")
