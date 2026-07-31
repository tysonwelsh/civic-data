#!/usr/bin/env python3
"""Build Herriman City (Salt Lake County, UT) election_results.

Herriman is a **Council-Mayor** city.  Its seat structure CHANGED below the 2020
data floor: the council was elected **AT LARGE** in 2007 & 2009 (top-2, 2 seats per
cycle), then transitioned to **4 single-member DISTRICTS (1-4) + a separately elected
Mayor** by 2013 (numbered "Council N" contests first appear in 2011).  4-yr staggered,
non-partisan terms.  As the contests appear in the county Statement-of-Votes-Cast (SOVC):

  * Cycle A (Mayor + District 2 + District 3): 2013, 2017, 2021, 2025
  * Cycle B (District 1 + District 4):          2011, 2015, 2019, 2023
  * At-large era: 2007 (2 seats), 2009 (2 seats + Mayor)

The **entire 2020+ modelled record is stable 4-district + Mayor** -- the at-large->
district change is well below the floor and does not affect member joins.
2025 additionally carried a **District 4 (2 Year Term)** off-cycle SPECIAL (Anderson) to
fill an unexpired D4 seat -- flagged in the `note` column so term logic does not read it
as a cycle shift.

SOURCES  (Salt Lake County Clerk SOVC, retained under raw/)
-----------------------------------------------------------
1. raw/municipal_results_long_herriman.csv
      Slice of the repo-wide canonical SOVC normalization
      (salt_lake_county/elections/slco_municipal_results_long.csv) filtered to Herriman.
      Precinct- and vote-method-level; sums cleanly (ZERO suppression) for
      2007/2009/2013/2015/2017 (+ their primaries), the 2011 PRIMARY, and the 2023 & 2025
      generals (+ 2025 primary).  These are consumed straight from this slice
      (summing the per-method rows to precinct + candidate totals).

2. raw/sovc/*.xlsx  (the true county SOVC spreadsheets)
      Re-parsed directly for the THREE general contests the canonical layer does not
      deliver cleanly:
        * 2011 general (Council 1/2/4) -- ABSENT from the canonical slice (the archive
          normalizer skipped Herriman's 2011-general sheets, same failure as South Jordan).
          RECOVERED from raw ("Herriman City Council N" sheets; per-precinct 'Total' rows).
        * 2019 general (District 1 & 4) -- present in the canonical slice only under the
          raw sheet codes "HER Council 1"/"HER Council 4" with the candidate name replaced
          by "Total"/method labels (the normalizer keyed off the sheet name AND mangled the
          Family-A wide crosstab).  RECOVERED from raw for faithful candidate names +
          precinct totals.  (This is the "2019 GAP" flagged in recon.md -- the data was
          on disk, mis-labelled, not missing.)
        * 2021 general (Mayor/D2/D3) -- present but privacy-SUPPRESSED at the In-Person/
          Vote-By-Mail method split (100 '****' cells), which destroys precinct totals.
          RE-PARSED from raw, whose per-precinct 'Total' sub-rows are NOT suppressed.

2019 municipal PRIMARY: the raw 2019 primary SOVC contains NO Herriman sheet (D1 drew 1
candidate, D4 drew 2) -> Herriman held no 2019 primary.  Logged, not fabricated.

Reproducible:  python3 clean_elections.py            (reads raw/, writes the 3 CSVs)
               python3 clean_elections.py --report    (+ per-race summary)
"""
import os, re, csv, sys, openpyxl

OUT = os.path.dirname(os.path.abspath(__file__))
SLICE = os.path.join(OUT, 'raw', 'municipal_results_long_herriman.csv')
SOVC = os.path.join(OUT, 'raw', 'sovc')
REPORT = '--report' in sys.argv


# --------------------------------------------------------------------------- helpers
def g(r, j):
    return r[j] if (r is not None and j < len(r)) else None


def norm_name(s):
    """Normalize a candidate name ALONGSIDE the verbatim value (never overwrites raw):
    collapse whitespace, strip the (NP) non-partisan tag, canonicalize write-ins."""
    s = re.sub(r'\s+', ' ', str(s).replace('\n', ' ')).strip()
    s = s.lstrip('*').strip()
    s = re.sub(r'\s*\(\s*(?:NP|NON)\s*\)', '', s, flags=re.I)     # strip (NP)/(NON)
    s = re.sub(r'\bUNRESOLVED\s+WRITE[- ]?IN\b', 'Write-in (unresolved)', s, flags=re.I)
    s = re.sub(r'\bWRITE[- ]?IN\b', 'Write-in', s, flags=re.I)
    return re.sub(r'\s+', ' ', s).strip().strip('"').strip()


def to_int(v):
    try:
        return int(round(float(v)))
    except (TypeError, ValueError):
        return None


# ---- contest canonicalization ----------------------------------------------
def canon(label):
    """Map any county contest label -> (office, district, canonical_contest, note)."""
    U = label.upper()
    note = ''
    if 'MAYOR' in U:
        return ('Mayor', '', 'Herriman City Mayor', note)
    if 'AT LARGE' in U or 'AT-LARGE' in U:
        return ('Council', 'At-Large', 'Herriman City Council At-Large', note)
    if '2 YEAR' in U or '2-YEAR' in U or '2 YR' in U:
        note = ('2-year short term -- off-cycle special election to fill an unexpired '
                'District 4 seat (not a cycle shift)')
    m = (re.search(r'DIST(?:RICT)?\s*(\d+)', U)
         or re.search(r'COUNCIL\s+(\d+)', U)
         or re.search(r'(\d+)', U))
    d = m.group(1) if m else '?'
    return ('Council', d, f'Herriman City Council District {d}', note)


def is_her_race(label):
    U = label.upper()
    if 'HERRIMAN' not in U and not U.startswith('HER '):
        return False
    if 'INITIATIVE' in U or 'IMPRV' in U or 'PROP' in U or 'PRP' in U:
        return False   # ballot questions (e.g. 2015 HERRIMAN HILLS INITIATIVE) -- not a seat
    return bool('MAYOR' in U or re.search(r'COUNCIL|COUN|CNCL', U))


# --------------------------------------------------------------------------- containers
RECORDS = {}   # key = (year, election_type, contest) -> record


def rec(year, etype, label, source_file):
    office, district, contest, note = canon(label)
    k = (year, etype, contest)
    if k not in RECORDS:
        RECORDS[k] = dict(year=year, election_type=etype, office=office,
                          district=district, contest=contest, cand={}, per={},
                          reg={}, ballots={}, suppressed_any=False,
                          source_file=source_file, verbatim=label, note=note)
    elif note and not RECORDS[k]['note']:
        RECORDS[k]['note'] = note
    return RECORDS[k]


def add_vote(R, precinct, cand, votes):
    R['cand'][cand] = R['cand'].get(cand, 0) + (votes or 0)
    R['per'].setdefault(precinct, {})
    cur = R['per'][precinct].get(cand)
    if votes is None:
        R['suppressed_any'] = True
        R['per'][precinct].setdefault(cand, None)
    else:
        R['per'][precinct][cand] = (cur or 0) + votes if isinstance(cur, int) else votes


# --------------------------------------------------------------------------- (1) canonical slice
# Years/contests taken from raw instead of the canonical slice:
SKIP_SLICE = {
    (2011, 'municipal general'),   # absent from slice -> raw
    (2019, 'municipal general'),   # mangled crosstab   -> raw
    (2021, 'municipal general'),   # suppressed split   -> raw
}


def load_slice():
    with open(SLICE, newline='') as fh:
        for row in csv.DictReader(fh):
            year = int(float(row['year']))
            etype = row['election_type']
            contest_raw = row['contest']
            if (year, etype) in SKIP_SLICE:
                continue
            if contest_raw.upper().startswith('HER '):
                continue           # 2019 sheet-code rows -> raw
            if not is_her_race(contest_raw):
                continue
            R = rec(year, etype, contest_raw, row['source_file'])
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


# --------------------------------------------------------------------------- (2a) 2011 general
def parse_2011_general(path):
    """Layout: header row has Precinct/Type/Reg. Voters/Cards Cast/Total Votes then
    candidate name columns (each followed by an empty-header pct col).  Each precinct has
    method sub-rows + a 'Total' Type row carrying the real count."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    PR = re.compile(r'HER\d+')
    for sh in wb.sheetnames:
        if not sh.lower().startswith('herriman'):
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
        dm = re.search(r'(\d+)\s*$', sh.strip())
        label = f'HERRIMAN CITY COUNCIL {dm.group(1)}' if dm else sh
        R = rec(2011, 'municipal general', label, os.path.basename(path))
        for r in rows[hi + 1:]:
            if str(g(r, typej)).strip() == 'Total':
                prec = str(g(r, pj)).strip()
                if not PR.fullmatch(prec):
                    continue          # skips 'Election Total'
                for j, name in cand_cols.items():
                    add_vote(R, prec, name, to_int(g(r, j)))
                if regj is not None and to_int(g(r, regj)) is not None:
                    R['reg'][prec] = to_int(g(r, regj))
                if cardj is not None and to_int(g(r, cardj)) is not None:
                    R['ballots'][prec] = to_int(g(r, cardj))


# --------------------------------------------------------------------------- (2b) 2019 general
def parse_2019_general(path):
    """Family-A wide crosstab: row1 = sparse candidate names; row2 marks each candidate's
    total with 'Total Votes'; col1 = Registered Voters; precinct rows col0 == HER###.
    The final 'Total' column is ballots-cast for the seat (not a candidate)."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    PR = re.compile(r'HER\d+')
    for sh in wb.sheetnames:
        if not sh.upper().startswith('HER COUNCIL'):
            continue
        ws = wb[sh]
        rows = [list(x) for x in ws.iter_rows(values_only=True)]
        name_row, sub_row = rows[1], rows[2]
        cand_cols = [(j, norm_name(name_row[j])) for j in range(len(name_row))
                     if name_row[j] not in (None, '')]
        tv_cols = [j for j, v in enumerate(sub_row) if str(v).strip() == 'Total Votes']
        cand_tv = dict(zip([n for _, n in cand_cols], tv_cols))
        regj = next((j for j, v in enumerate(sub_row) if 'Registered' in str(v)), None)
        ballj = next((j for j, v in enumerate(sub_row)
                      if str(v).strip() == 'Total'), None)   # ballots-cast column
        dm = re.search(r'(\d+)\s*$', sh.strip())
        label = f'HERRIMAN CITY COUNCIL DISTRICT {dm.group(1)}'
        R = rec(2019, 'municipal general', label, os.path.basename(path))
        for r in rows[3:]:
            c0 = g(r, 0)
            if not (isinstance(c0, str) and PR.fullmatch(c0.strip())):
                continue
            prec = c0.strip()
            for c, tvj in cand_tv.items():
                add_vote(R, prec, c, to_int(g(r, tvj)))
            if regj is not None and to_int(g(r, regj)) is not None:
                R['reg'][prec] = to_int(g(r, regj))
            if ballj is not None and to_int(g(r, ballj)) is not None:
                R['ballots'][prec] = to_int(g(r, ballj))


# --------------------------------------------------------------------------- (2c) 2021 general
NONCAND = {'PRECINCT', 'TIMES CAST', 'REGISTERED VOTERS', 'REGISTERED', 'TOTAL VOTES',
           'TOTAL', 'TYPE'}


def parse_2021_general(path, sheets):
    """2021 two-block columnar: a 2nd 'Precinct' marker (col4) precedes candidate value
    columns; each precinct has In Person / Vote By Mail method sub-rows ('****' suppressed)
    and a 'Total' sub-row with the UN-suppressed precinct count.  Candidate value columns
    are the header cells carrying a name (pct cols are blank-header, excluded)."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    PR = re.compile(r'HER\d+')
    for sh in sheets:
        ws = wb[sh]
        rows = [list(x) for x in ws.iter_rows(values_only=True)]
        title = next(str(g(r, 0)) for r in rows[:4]
                     if g(r, 0) and 'HERRIMAN' in str(g(r, 0)).upper())
        title = re.sub(r'\s*\(Vote.*', '', title).strip()
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
        R = rec(2021, 'municipal general', title, os.path.basename(path))
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
                   ['Sheet13', 'Sheet14', 'Sheet15'])


# --------------------------------------------------------------------------- compute + write
def real_cands(items):
    return [(n, v) for n, v in items
            if not (n.startswith('Write-in') and (v or 0) == 0)]


def seats_for(R):
    """n_seats: at-large council in 2007/2009 elected the TOP 2 (2 seats); everything
    else is a single seat."""
    return 2 if R['district'] == 'At-Large' else 1


races, by_cand, by_precinct = [], [], []
for k in sorted(RECORDS, key=lambda x: (x[0], x[1], x[2])):
    R = RECORDS[k]
    n_seats = seats_for(R)
    items = sorted(R['cand'].items(), key=lambda kv: (-(kv[1] or 0), kv[0]))
    total = sum(v or 0 for v in R['cand'].values())
    rc = real_cands(items)
    winners = items[:n_seats]
    losers = items[n_seats:]
    winner, wv = winners[0] if winners else ('', 0)
    # runner_up = highest candidate who did NOT win a seat; margin = seat-deciding margin
    last_win_votes = winners[-1][1] if winners else 0
    runner, rv = (losers[0] if losers else ('', 0))
    margin = (last_win_votes or 0) - (rv or 0)
    reg_total = sum(R['reg'].values()) if R['reg'] else ''
    ballots_total = sum(R['ballots'].values()) if R['ballots'] else ''
    turnout = (round(100 * ballots_total / reg_total, 2)
               if (isinstance(ballots_total, int) and isinstance(reg_total, int) and reg_total)
               else '')
    note = R['note']
    if n_seats > 1:
        wl = '; '.join(f'{n} ({v})' for n, v in winners)
        note = (f'At-large, {n_seats} seats -- elected: {wl}. winner column = top vote-getter; '
                f'runner_up = highest non-winning candidate; margin = last-seat margin.'
                + (f' {note}' if note else ''))
    races.append(dict(
        year=R['year'], election_type=R['election_type'], office=R['office'],
        district=R['district'], contest=R['contest'], contest_verbatim=R['verbatim'],
        n_seats=n_seats, n_candidates=len(rc), voting_method='plurality',
        total_votes=total, total_first_choice_votes='', winner=winner, winner_votes=wv,
        winner_pct=round(100 * (wv or 0) / total, 2) if total else 0,
        runner_up=runner, runner_up_votes=rv,
        margin_votes=margin, margin_pct=round(100 * margin / total, 2) if total else 0,
        registered_voters=reg_total, ballots_cast=ballots_total, turnout_pct=turnout,
        uncontested='True' if len(rc) <= n_seats else 'False',
        suppressed_precincts='True' if R['suppressed_any'] else 'False',
        note=note, source_file=R['source_file']))
    for rank, (name, v) in enumerate(items, 1):
        by_cand.append(dict(
            year=R['year'], election_type=R['election_type'], office=R['office'],
            district=R['district'], contest=R['contest'], candidate=name,
            votes=v or 0, pct=round(100 * (v or 0) / total, 2) if total else 0,
            rank=rank, is_winner='True' if rank <= n_seats else 'False'))
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


writecsv('herriman_races.csv', races,
         ['year', 'election_type', 'office', 'district', 'contest', 'contest_verbatim',
          'n_seats', 'n_candidates', 'voting_method', 'total_votes',
          'total_first_choice_votes', 'winner', 'winner_votes', 'winner_pct', 'runner_up',
          'runner_up_votes', 'margin_votes', 'margin_pct', 'registered_voters',
          'ballots_cast', 'turnout_pct', 'uncontested', 'suppressed_precincts', 'note',
          'source_file'])
writecsv('herriman_results_by_candidate.csv', by_cand,
         ['year', 'election_type', 'office', 'district', 'contest', 'candidate',
          'votes', 'pct', 'rank', 'is_winner'])
writecsv('herriman_results_by_precinct.csv', by_precinct,
         ['year', 'election_type', 'office', 'district', 'contest', 'precinct',
          'candidate', 'votes', 'suppressed'])

# --------------------------------------------------------------------------- reconcile + report
mism = 0
for k in RECORDS:
    R = RECORDS[k]
    for cand, tot in R['cand'].items():
        psum = sum((R['per'][p].get(cand) or 0) for p in R['per']
                   if R['per'][p].get(cand) is not None)
        if not R['suppressed_any'] and psum != tot:
            mism += 1
            print(f"  MISMATCH {k} {cand}: candidate={tot} precinct-sum={psum}")

gen = [r for r in races if r['election_type'] == 'municipal general']
pri = [r for r in races if r['election_type'] == 'municipal primary']
print(f"races: {len(races)}  (general {len(gen)}, primary {len(pri)})")
print(f"by_candidate rows: {len(by_cand)}   by_precinct rows: {len(by_precinct)}")
print(f"precinct-sum reconciliation mismatches (unsuppressed races): {mism}")
if REPORT:
    for r in sorted(races, key=lambda x: (x['year'], x['election_type'], x['contest'])):
        tag = 'PRI ' if r['election_type'] == 'municipal primary' else 'GEN '
        unc = ' [UNCONTESTED]' if r['uncontested'] == 'True' else ''
        sup = ' [suppressed]' if r['suppressed_precincts'] == 'True' else ''
        to = f" turnout {r['turnout_pct']}%" if r['turnout_pct'] != '' else ''
        print(f"  {r['year']} {tag}{r['contest']:34s} seats={r['n_seats']} n={r['n_candidates']} "
              f"WIN {r['winner']} {r['winner_votes']} ({r['winner_pct']}%) vs "
              f"{r['runner_up']} {r['runner_up_votes']}  margin {r['margin_votes']} "
              f"[tot {r['total_votes']}{to}]{unc}{sup}")
