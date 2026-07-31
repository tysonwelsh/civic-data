#!/usr/bin/env python3
"""Build Midvale City (Salt Lake County, UT) election_results.

Midvale is a Utah **six-member council** city: **5 council DISTRICTS (1-5) + a separately
elected Mayor** (citywide). 4-yr staggered terms, odd-year municipal elections. As the
contests appear in the county Statement-of-Votes-Cast (SOVC) files, the stagger is:

  * Cycle A (Mayor + District 4 + District 5): 2009, 2013, 2017, 2021, 2025
  * Cycle B (Districts 1, 2, 3):               2007, 2011, 2015, 2019, 2023

(In 2007 the county labelled the seats "MIDVALE CITY COUNCIL 1/2/3"; later years use
"...COUNCIL DISTRICT N", "...CNCL DIST N", mixed case, etc. All normalize to
"Midvale City Council District N".)  Mayor sits only on the A cycle.

RANKED CHOICE VOTING: Midvale joined the Utah/SL-County RCV municipal pilot in **2021,
2023 and 2025**. The county SOVC 'Total' column holds FIRST-CHOICE (round-1) tallies, not
the RCV final round, so for those years `voting_method='ranked choice'`,
`total_first_choice_votes` is populated, and any race where the winner lacked a round-1
majority carries a `note` flagging that winner_pct/margin are first-choice. Winners are
the canvassed RCV-final winners (verified: 2021 Mayor Stevenson, 2023 D3 Robinson, 2025
Mayor Gettel all led first-choice and won the final). Pre-2021 years are plurality.

SOURCES  (Salt Lake County Clerk)
---------------------------------
1. raw/municipal_results_long_midvale.csv
      The county's canonical long-form SOVC normalization
      (/Users/tysonwelsh/civic-data/salt_lake_county/elections/slco_municipal_results_long.csv)
      filtered to Midvale council + mayor contests (the BOND question is excluded). Rows
      are precinct- and VOTE-METHOD-level (no explicit "Total" method row), so precinct
      totals are recovered by SUMMING across the method rows. 26 exact-duplicate phantom
      rows (2021 Mayor, precinct MID032, all-zero) are de-duplicated. Consumed straight
      for 2007/2009/2011/2013/2015/2017 (+ their primaries), 2023 and 2025 -- all with
      ZERO usable-cell suppression.

2. raw/sovc/*.xlsx  (the true county SOVC spreadsheets)
      Re-parsed directly for the contests the long-form layer does not deliver cleanly:
        * 2021 general (Mayor / D4 / D5) -- present in the long CSV but the In-Person /
          Vote-By-Mail method split is privacy-SUPPRESSED (**** cells, blank votes),
          which destroys every precinct's usable count. RE-PARSED from
          2021-11-02-general-election-sovc.xlsx, whose per-precinct 'Total' sub-rows are
          NOT suppressed (Sheets 19/20/21).
        * 2019 general (D1 / D2 / D3) -- entirely ABSENT from the long CSV: the county
          normalizer keyed the contest off the sheet NAME and the 2019 sheets are coded
          "MID Council N", so a '%MIDVALE%' filter never matched them. This is the
          recon.md-flagged 2019 gap (same failure mode as other SL County cities).
          RECOVERED from 2019-11-05-general-election-sovc.xlsx (Family-A wide crosstab).
        * 2019 primary (D2 only) -- likewise absent from the long CSV; the 2019 primary
          sheets are numbered, and Midvale's single primary contest (D2, 3 candidates)
          sits on sheet '11' titled "MIDVALE CITY COUNCIL DISTRICT 2". RECOVERED.
      (Districts 1 and 3 drew <=2 candidates in 2019 -> no primary for them. Verified.)

Reproducible:  python3 clean_elections.py            (writes the slice + the 3 CSVs)
               python3 clean_elections.py --report    (+ per-race summary)
"""
import os, re, csv, sys, openpyxl

OUT = os.path.dirname(os.path.abspath(__file__))
CANON = '/Users/tysonwelsh/civic-data/salt_lake_county/elections/slco_municipal_results_long.csv'
SLICE = os.path.join(OUT, 'raw', 'municipal_results_long_midvale.csv')
SOVC = os.path.join(OUT, 'raw', 'sovc')
REPORT = '--report' in sys.argv


# --------------------------------------------------------------------------- helpers
def g(r, j):
    return r[j] if (r is not None and j < len(r)) else None


def norm_name(s):
    """Normalize a candidate name ALONGSIDE the verbatim value (never overwrites raw):
    collapse whitespace, strip (NP)/(NON) non-partisan tag, canonicalize write-ins."""
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
    """Map any county Midvale contest label to (office, district, canonical_contest)."""
    U = label.upper()
    if 'MAYOR' in U:
        return ('Mayor', '', 'Midvale City Mayor')
    m = (re.search(r'DIST(?:RICT)?\s*#?\s*(\d)', U)
         or re.search(r'(\d)\s*$', U.strip()))
    d = m.group(1) if m else '?'
    return ('Council', d, f'Midvale City Council District {d}')


def is_midvale_seat(label):
    U = label.upper()
    if 'MIDVALE' not in U or 'BOND' in U:
        return False
    return ('MAYOR' in U) or bool(re.search(r'(COUNCIL|COUN|CNCL)', U))


# --------------------------------------------------------------------------- containers
RECORDS = {}   # key = (year, election_type, contest) -> record dict


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


# --------------------------------------------------------------------------- (0) slice
def build_slice():
    """Filter the county canonical long CSV to Midvale council+mayor; write raw slice."""
    seen = set()
    out = []
    with open(CANON, newline='') as fh:
        rd = csv.DictReader(fh)
        cols = rd.fieldnames
        for row in rd:
            if not is_midvale_seat(row['contest']):
                continue
            # de-dupe exact-identical phantom rows (same precinct/cand/method appears once)
            k = (row['year'], row['election_type'], row['contest'],
                 row['precinct'], row['candidate'], row['vote_method'])
            if k in seen:
                continue
            seen.add(k)
            out.append(row)
    os.makedirs(os.path.dirname(SLICE), exist_ok=True)
    with open(SLICE, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(out)
    return out


SLICE_SKIP_YEARS = {'2021'}   # 2021 general re-parsed from raw (method suppression)


def load_slice(rows):
    for row in rows:
        year = row['year']
        if year in SLICE_SKIP_YEARS:
            continue
        R = rec(int(float(year)), row['election_type'], row['contest'], row['source_file'])
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


# --------------------------------------------------------------------------- (1) 2021 raw
NONCAND = {'TIMES CAST', 'REGISTERED VOTERS', 'REGISTERED', 'TOTAL VOTES', 'UNDERVOTES',
           'OVERVOTES', 'PRECINCT', 'TOTAL', 'CONTINUING BALLOTS TOTAL', 'CARDS CAST',
           'TYPE', 'COUNTY', 'ELECTIONWIDE'}


def parse_2021_general(path, sheets):
    """2021 columnar: a second 'Precinct' marker precedes candidate columns; each
    precinct has In Person / Vote By Mail method sub-rows (small counts '****'
    suppressed) and a 'Total' sub-row carrying the UN-suppressed precinct count."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    PR = re.compile(r'MID\d+')
    for sh in sheets:
        ws = wb[sh]
        rows = [list(x) for x in ws.iter_rows(values_only=True)]
        title = next(str(g(r, 0)) for r in rows[:3] if g(r, 0) and 'MIDVALE' in str(g(r, 0)).upper())
        label = re.sub(r'\s*\(Vote.*', '', title).strip()
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


# --------------------------------------------------------------------------- (2) 2019 raw
def parse_2019_familyA(path, sheet, etype, label):
    """2019 'Family-A' wide crosstab: candidate names sparse on row 1; row 2 marks each
    candidate block's total with 'Total Votes'; precinct rows (col0 == MID###) follow,
    a 'Registered Voters' column carries reg counts. Used for both the general
    (MID Council N sheets) and the D2 primary (numbered sheet)."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    PR = re.compile(r'MID\d+')
    ws = wb[sheet]
    rows = [list(x) for x in ws.iter_rows(values_only=True)]
    name_row, sub_row = rows[1], rows[2]
    cand_cols = [(j, norm_name(name_row[j])) for j in range(len(name_row))
                 if name_row[j] not in (None, '')]
    tv_cols = [j for j, v in enumerate(sub_row) if str(v).strip() == 'Total Votes']
    cand_tv = dict(zip([n for _, n in cand_cols], tv_cols))
    regj = next((j for j, v in enumerate(sub_row) if 'Registered' in str(v)), None)
    R = rec(2019, etype, label, os.path.basename(path))
    for r in rows[3:]:
        c0 = g(r, 0)
        if isinstance(c0, str) and PR.fullmatch(c0.strip()):
            prec = c0.strip()
            for c, tvj in cand_tv.items():
                add_vote(R, prec, c, to_int(g(r, tvj)))
            if regj is not None and to_int(g(r, regj)) is not None:
                R['reg'][prec] = to_int(g(r, regj))


# --------------------------------------------------------------------------- run loaders
slice_rows = build_slice()
load_slice(slice_rows)
parse_2021_general(os.path.join(SOVC, '2021-11-02-general-election-sovc.xlsx'),
                   ['Sheet19', 'Sheet20', 'Sheet21'])
parse_2019_familyA(os.path.join(SOVC, '2019-11-05-general-election-sovc.xlsx'),
                   'MID Council 1', 'municipal general', 'MIDVALE CITY COUNCIL DISTRICT 1')
parse_2019_familyA(os.path.join(SOVC, '2019-11-05-general-election-sovc.xlsx'),
                   'MID Council 2', 'municipal general', 'MIDVALE CITY COUNCIL DISTRICT 2')
parse_2019_familyA(os.path.join(SOVC, '2019-11-05-general-election-sovc.xlsx'),
                   'MID Council 3', 'municipal general', 'MIDVALE CITY COUNCIL DISTRICT 3')
# 2019 D2 primary lives in the primary workbook (numbered sheet '11')
parse_2019_familyA(os.path.join(SOVC, '2019-08-13-municipal-primary-sovc.xlsx'),
                   '11', 'municipal primary', 'MIDVALE CITY COUNCIL DISTRICT 2')


# --------------------------------------------------------------------------- compute + write
# Midvale joined the Utah RCV municipal pilot in 2021, 2023 and 2025 (SL County RCV).
# The county SOVC 'Total' column carries FIRST-CHOICE (round-1) tallies, NOT the RCV
# final round, so for these years winner_pct/margin are first-choice figures. Winners
# are unaffected (each RCV-final winner also led the first choice here), but where no
# candidate had a round-1 majority the RCV redistribution (not in the SOVC) decided the
# final spread -> flagged in `note`. Take winners as authoritative; treat margins in
# those flagged rows as first-choice only.
RCV_YEARS = {2021, 2023, 2025}


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
    is_rcv = R['year'] in RCV_YEARS
    wpct = round(100 * (wv or 0) / total, 2) if total else 0
    note = ''
    if is_rcv and len(rc) >= 3 and wpct < 50:
        note = ('RCV pilot year: winner_pct/margin are FIRST-CHOICE (round 1); the RCV '
                'final round is not in the SOVC Total column. Winner is the canvassed '
                'RCV-final winner.')
    races.append(dict(
        year=R['year'], election_type=R['election_type'], office=R['office'],
        district=R['district'], contest=R['contest'], contest_verbatim=R['verbatim'],
        n_seats=1, n_candidates=len(rc),
        voting_method='ranked choice' if is_rcv else 'plurality',
        total_votes=total,
        total_first_choice_votes=total if is_rcv else '',
        winner=winner, winner_votes=wv, winner_pct=wpct,
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


writecsv('midvale_races.csv', races,
         ['year', 'election_type', 'office', 'district', 'contest', 'contest_verbatim',
          'n_seats', 'n_candidates', 'voting_method', 'total_votes',
          'total_first_choice_votes', 'winner', 'winner_votes', 'winner_pct', 'runner_up',
          'runner_up_votes', 'margin_votes', 'margin_pct', 'registered_voters',
          'ballots_cast', 'turnout_pct', 'uncontested', 'suppressed_precincts', 'note',
          'source_file'])
writecsv('midvale_results_by_candidate.csv', by_cand,
         ['year', 'election_type', 'office', 'district', 'contest', 'candidate',
          'votes', 'pct', 'rank', 'is_winner'])
writecsv('midvale_results_by_precinct.csv', by_precinct,
         ['year', 'election_type', 'office', 'district', 'contest', 'precinct',
          'candidate', 'votes', 'suppressed'])

# --------------------------------------------------------------------------- report
gen = [r for r in races if r['election_type'] == 'municipal general']
pri = [r for r in races if r['election_type'] == 'municipal primary']
print(f"races: {len(races)}  (general {len(gen)}, primary {len(pri)})")
print(f"by_candidate rows: {len(by_cand)}   by_precinct rows: {len(by_precinct)}")
print(f"slice rows (Midvale, de-duped): {len(slice_rows)}")
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
