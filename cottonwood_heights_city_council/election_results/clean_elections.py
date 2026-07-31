#!/usr/bin/env python3
"""Build Cottonwood Heights City (Salt Lake County, UT) election_results.

Cottonwood Heights is a **4-district council + a separately elected Mayor who
VOTES** as a full council member (max roll-call tally = 5). Non-partisan,
4-year staggered terms. As the contests appear in the Salt Lake County
Statement-of-Votes-Cast (SOVC) files, the stagger is:

  * Cycle A (Mayor + District 3 + District 4): 2009, 2013, 2017, 2021, 2025
  * Cycle B (Districts 1, 2):                   2011, 2015, 2019, 2023

(Early county labels vary: "COTTONWOOD HEIGHTS COUNCIL 3", "...CITY CNCL 3",
"Cottonwood Hts Council 1" (2011), "COT Council 1" (2019), and from 2021 on
"...COUNCIL DISTRICT N". All normalize to "Cottonwood Heights City Council
District N"; the mayor to "Cottonwood Heights City Mayor".)

EXCLUSIONS (not city council/mayor — never emitted):
  * "Cottonwood Heights Parks & Recreation Service Area" trustee (a separate
    special-service district: 2017 "Park & Rec 2", 2021 D1/D2 trustee, 2025 D1
    trustee, 2019 "COT ParksRec 3").
  * "Cottonwood Improvement Board" trustee (2011 "Cottonwood Improve Brd
    Trust-N/S", 2019 "COT Imprv") — the water/sewer improvement district.
  * "COUNTY PROP #6 - ISLAND NO. 1" (2015 annexation ballot question).

SOURCES  (Salt Lake County Clerk, mirrored in ~/Desktop/slco-election-archive)
-----------------------------------------------------------------------------
Three provenance layers, all retained under raw/:

1. raw/municipal_results_long_cottonwood_heights.csv
      The repo-canonical SOVC normalization
      (salt_lake_county/elections/slco_municipal_results_long.csv) filtered to
      rows whose contest matches "COTTONWOOD HEIGHTS". Precinct- and
      vote-method-level; sums cleanly with ZERO suppression for the
      **2009/2013/2015/2017 generals (+ their primaries), the 2023 general +
      primary, and the 2025 general** — consumed straight from this slice.
      (2021 is present here but 462/572 rows are privacy-SUPPRESSED at the
      In-Person/Vote-By-Mail split -> re-parsed from raw instead.)

2. raw/municipal_2011_general_cottonwood_heights.csv
      The archive's own 2011 normalization (data/municipal/
      2011_municipal_general.csv) filtered to CH. The 2011 seats were labelled
      "Cottonwood Hts Council 1/2" -> a "%COTTONWOOD HEIGHTS%" filter on the
      main long file MISSES them ("Hts" != "Heights"). Recovered here so the
      Cycle-B 2011 D1/D2 general is not a false gap. (No 2011 CH primary
      sheet exists -> each district drew <=2 candidates; logged, not fabricated.)

3. raw/sovc/*.xlsx  (the true county SOVC spreadsheets), re-parsed for the two
   contests the parsed layers do not deliver cleanly:
      * 2019 general (D1/D2) -- present in the raw file only under the sheet
        codes "COT Council 1/2" (a Family-A wide crosstab); the archive's
        %COTTONWOOD% normalizer never emitted them, so they are ABSENT from the
        main long file. RECOVERED from raw for faithful district numbers,
        candidate names and precinct totals. (No 2019 CH primary sheet -> no
        2019 primary.)
      * 2021 general (Mayor/D3/D4) -- present in the long slice but privacy-
        SUPPRESSED at the method split (462/572 rows), destroying precinct
        totals. RE-PARSED from raw, whose per-precinct "Total" sub-rows are
        NOT suppressed (Sheet8=Mayor, Sheet9=D3, Sheet10=D4).

Reproducible:  python3 clean_elections.py            (reads raw/, writes 3 CSVs)
               python3 clean_elections.py --report    (+ per-race summary)
"""
import os, re, csv, sys, openpyxl

OUT = os.path.dirname(os.path.abspath(__file__))
SLICE = os.path.join(OUT, 'raw', 'municipal_results_long_cottonwood_heights.csv')
SLICE_2011 = os.path.join(OUT, 'raw', 'municipal_2011_general_cottonwood_heights.csv')
SOVC = os.path.join(OUT, 'raw', 'sovc')
REPORT = '--report' in sys.argv


# --------------------------------------------------------------------------- helpers
def g(r, j):
    return r[j] if (r is not None and j < len(r)) else None


def norm_name(s):
    """Normalize a candidate name ALONGSIDE the verbatim value (never overwrites
    raw): collapse whitespace, strip the (NP)/(NON) non-partisan tag, drop a
    leading registered-write-in mark, canonicalize write-ins."""
    s = re.sub(r'\s+', ' ', str(s).replace('\n', ' ')).strip()
    s = s.lstrip('*').strip()
    s = re.sub(r'\s*\(\s*(?:NP|NON)\s*\)', '', s, flags=re.I)
    s = re.sub(r'\bUNRESOLVED\s+WRITE[- ]?IN\b', 'Write-in (unresolved)', s, flags=re.I)
    s = re.sub(r'\bWRITE[- ]?IN\b', 'Write-in', s, flags=re.I)
    return re.sub(r'\s+', ' ', s).strip().strip('"').strip()


def to_int(v):
    return int(v) if isinstance(v, (int, float)) else None


# ---- contest classification / canonicalization -----------------------------
_EXCLUDE = ('PARK', 'REC', 'IMPRV', 'IMPROVE', 'TRUST', 'PROP', 'ISLAND', 'ANNEX')


def keep(label):
    """True iff this is a Cottonwood Heights CITY council or mayor contest."""
    U = label.upper()
    if 'COTTONWOOD' not in U and not U.startswith('COT '):
        return False
    if any(w in U for w in _EXCLUDE):
        return False
    return ('MAYOR' in U) or ('COUNCIL' in U) or ('CNCL' in U)


def canon(label):
    """Map any county contest label to (office, district, canonical_contest)."""
    U = label.upper()
    if 'MAYOR' in U:
        return ('Mayor', '', 'Cottonwood Heights City Mayor')
    m = re.search(r'DIST(?:RICT)?\s*(\d+)', U) or re.search(r'(\d+)\s*$', U.strip())
    d = m.group(1) if m else '?'
    return ('Council', d, f'Cottonwood Heights City Council District {d}')


# --------------------------------------------------------------------------- containers
RECORDS = {}     # key = (year, election_type, canonical_contest) -> record


def rec(year, etype, label, source_file):
    office, district, contest = canon(label)
    k = (int(year), etype, contest)
    if k not in RECORDS:
        RECORDS[k] = dict(year=int(year), election_type=etype, office=office,
                          district=district, contest=contest,
                          cand={}, per={}, reg={}, ballots={},
                          suppressed_any=False, source_file=source_file,
                          verbatim=label, note='')
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


# --------------------------------------------------------------------------- (1) main slice
SLICE_SKIP_YEARS = {2021}      # 2021 general re-parsed from raw (suppression)


def load_long_csv(path, skip_years=frozenset()):
    with open(path, newline='') as fh:
        for row in csv.DictReader(fh):
            year = int(float(row['year']))
            if year in skip_years:
                continue
            contest_raw = row['contest']
            if not keep(contest_raw):
                continue
            R = rec(year, row['election_type'], contest_raw, row['source_file'])
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


# --------------------------------------------------------------------------- (3) raw parsers
def parse_2019_general(path):
    """2019 'Family-A' wide crosstab (sheets 'COT Council N'): row1 = candidate
    names (sparse), row2 = sub-header ('Total Votes' marks each candidate's
    total column, 'Registered Voter' the reg column); precinct rows (col0 ==
    COT###) follow."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    PR = re.compile(r'COT\d+')
    for sh in wb.sheetnames:
        if not sh.upper().startswith('COT COUNCIL'):
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
        label = f'COTTONWOOD HEIGHTS COUNCIL DISTRICT {dm.group(1)}'
        R = rec(2019, 'municipal general', label, os.path.basename(path))
        R['note'] = 'district general recovered from raw SOVC (absent from the parsed long file — sheet keyed "COT Council N")'
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
    """2021 columnar (Sheet8=Mayor, Sheet9=D3, Sheet10=D4): a second 'Precinct'
    marker precedes candidate columns; each precinct has In Person / Vote By
    Mail method sub-rows ('****' privacy-suppressed) and a 'Total' sub-row with
    the UN-suppressed precinct count."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    PR = re.compile(r'COT\d+')
    for sh in sheets:
        ws = wb[sh]
        rows = [list(x) for x in ws.iter_rows(values_only=True)]
        title = next(str(g(r, 0)) for r in rows[:4]
                     if g(r, 0) and 'COTTONWOOD' in str(g(r, 0)).upper())
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
        R = rec(2021, 'municipal general', re.sub(r'\s*\(Vote.*', '', title).strip(),
                os.path.basename(path))
        R['note'] = 'district general re-parsed from raw SOVC (long-file rows privacy-suppressed at the method split; per-precinct Total sub-rows are unsuppressed)'
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
load_long_csv(SLICE, skip_years=SLICE_SKIP_YEARS)          # 2009/2013/2015/2017/2023/2025
load_long_csv(SLICE_2011)                                  # 2011 D1/D2 (Cycle B)
parse_2019_general(os.path.join(SOVC, '2019-11-05-general-election-sovc.xlsx'))
parse_2021_general(os.path.join(SOVC, 'november-2-2021-general-election-statement-of-votes-cast.xlsx'),
                   ['Sheet8', 'Sheet9', 'Sheet10'])
# tag the 2011 records' provenance note
for k, R in RECORDS.items():
    if k[0] == 2011 and not R['note']:
        R['note'] = 'district general recovered from the archive 2011 normalization (labelled "Cottonwood Hts Council N" — missed by a "COTTONWOOD HEIGHTS" filter)'


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
        note=R['note'], source_file=R['source_file']))
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


writecsv('cottonwood_heights_races.csv', races,
         ['year', 'election_type', 'office', 'district', 'contest', 'contest_verbatim',
          'n_seats', 'n_candidates', 'voting_method', 'total_votes',
          'total_first_choice_votes', 'winner', 'winner_votes', 'winner_pct',
          'runner_up', 'runner_up_votes', 'margin_votes', 'margin_pct',
          'registered_voters', 'ballots_cast', 'turnout_pct', 'uncontested',
          'suppressed_precincts', 'note', 'source_file'])
writecsv('cottonwood_heights_results_by_candidate.csv', by_cand,
         ['year', 'election_type', 'office', 'district', 'contest', 'candidate',
          'votes', 'pct', 'rank', 'is_winner'])
writecsv('cottonwood_heights_results_by_precinct.csv', by_precinct,
         ['year', 'election_type', 'office', 'district', 'contest', 'precinct',
          'candidate', 'votes', 'suppressed'])

# --------------------------------------------------------------------------- report
gen = [r for r in races if r['election_type'] == 'municipal general']
pri = [r for r in races if r['election_type'] == 'municipal primary']
print(f"races: {len(races)}  (general {len(gen)}, primary {len(pri)})")
print(f"by_candidate rows: {len(by_cand)}   by_precinct rows: {len(by_precinct)}")
# integrity: every by-precinct sum reconciles to its by-candidate total
mm = 0
for k in RECORDS:
    R = RECORDS[k]
    for name, tot in R['cand'].items():
        psum = sum((R['per'][p].get(name) or 0) for p in R['per'])
        if psum != (tot or 0):
            mm += 1
            print(f"  MISMATCH {k} {name}: cand={tot} precsum={psum}")
print(f"reconciliation mismatches: {mm}")
if REPORT:
    for r in sorted(races, key=lambda x: (x['year'], x['election_type'], x['contest'])):
        tag = 'PRIMARY ' if r['election_type'] == 'municipal primary' else ''
        unc = ' [UNCONTESTED]' if r['uncontested'] == 'True' else ''
        sup = ' [suppressed]' if r['suppressed_precincts'] == 'True' else ''
        to = f" turnout {r['turnout_pct']}%" if r['turnout_pct'] != '' else ''
        print(f"  {r['year']} {tag}{r['contest']:42s} n={r['n_candidates']} "
              f"WIN {r['winner']} {r['winner_votes']} ({r['winner_pct']}%) vs "
              f"{r['runner_up']} {r['runner_up_votes']}  margin {r['margin_votes']} "
              f"[tot {r['total_votes']}{to}]{unc}{sup}")
