#!/usr/bin/env python3
"""Build Riverton City (Salt Lake County, UT) election_results.

Riverton is a **six-member council form**: **5 council DISTRICTS (1-5) + a separately
elected Mayor** (citywide; the Mayor chairs the council and votes only to break a tie).
4-yr staggered non-partisan terms.  The stagger, as the contests appear in the county
Statement-of-Votes-Cast (SOVC) files:

  * Cycle A (Mayor + District 3 + District 4): 2009, 2013, 2017, 2021, 2025
  * Cycle B (Districts 1, 2, 5):               2007, 2011, 2015, 2019, 2023

(Riverton's council was numbered "#1/#2/#5" at-large in 2007, became "DIST 3/DIST 4" from
2009, and "DISTRICT N" from 2021.  All normalize to "Riverton City Council District N".
Note Riverton's B-cycle seats are 1/2/**5** and A-cycle 3/**4**+Mayor -- unlike the
sibling South Jordan, whose split is 1/2/4 vs 3/5.)

SOURCES  (Salt Lake County Clerk)
---------------------------------------------------------------------------------------
Two provenance layers, both retained under raw/:

1. raw/riverton_slco_results_long.csv
      A verbatim filter (contest LIKE '%RIVERTON%') of the collection-canonical
      salt_lake_county/elections/slco_municipal_results_long.csv -- the county SOVC
      normalized to one row per (year, contest, precinct, candidate, vote_method).
      Every Riverton year the county published under a RIVERTON label is consumed
      straight from this slice: 2007, 2009, 2011, 2013, 2015, 2017, 2021, 2023, 2025
      (generals + the 2007/2009/2011/2025 primaries).  Votes are summed across
      vote-method rows to the precinct x candidate level.

2. raw/sovc/2019-11-05-general-election-sovc.xlsx  +  2019-08-13-municipal-primary-sovc.xlsx
      The 2019 municipal election is the documented GAP: the canonical long CSV carries
      NO Riverton 2019 rows because the county keyed the contest off the worksheet name
      and Riverton's 2019 sheets are named "RIV Council 1/2/5" (no "RIVERTON" string),
      so a '%RIVERTON%' filter never matched them (identical failure mode to the sibling
      South Jordan "SJD Council N" gap).  RECOVERED here by parsing the raw SOVC directly
      (Family-A wide crosstab; the per-candidate "Total Votes" column is the precinct
      count).  2019 is a Cycle-B year -> Districts 1, 2, 5; its winners are the 2020-2023
      voting bench (in scope for the 2020-floor minutes record).

3. raw/sovc/november-2-2021-general-election-statement-of-votes-cast.xlsx
      The 2021 municipal general (Cycle A: District 3, District 4, Mayor).  The canonical
      slice carries it privacy-SUPPRESSED (see the 2021 caveat below), so 2021 is dropped
      from the slice and recovered here directly from the raw county SOVC 'Total' sub-rows
      (parse_2021).

2019 municipal PRIMARY: the raw 2019 primary SOVC carries Riverton District 2 and
District 5 (three+ candidates each) but NO District 1 sheet -> District 1 drew <=2
candidates (Sheldon B. Stewart ran effectively unopposed) so no D1 primary was triggered.
Logged, not fabricated.

CAVEATS folded into the output
------------------------------
* Registered voters are carried per precinct for every year -> contest reg total = sum of
  per-precinct registrations.  BALLOTS CAST (times_cast) are carried only for 2021/2023/
  2025 -> turnout_pct is populated only for those years (blank elsewhere, incl. 2019).
* 2021 general (RECOVERED): the canonical long CSV carries 2021 privacy-SUPPRESSED -- the
  county split every precinct cell at the In-Person / Vote-By-Mail method line ('****'),
  which collapsed the candidate totals (e.g. District 3 winner McCay read 0 votes / all
  '****').  We SKIP 2021 from the slice (load_slice) and rebuild it from the raw SOVC
  (raw/sovc/november-2-2021-general-election-statement-of-votes-cast.xlsx) via parse_2021,
  which reads each precinct's UNsuppressed 'Total' sub-row -- so only the method split was
  ever hidden, and the recovered per-precinct totals reconcile exactly to the candidate
  totals.  Result: McCay (D3)=863, Buroker (D4)=1160, Staggs (Mayor)=4973; all three
  contests are UNCONTESTED (one candidate) and no longer carry suppressed_precincts.
* A handful of split-precinct rows (a precinct that straddles a district line) appear
  twice in a contest -- one copy carries the votes, the duplicate carries zeros -- so
  summing all rows is exact (verified: every duplicate's second copy is 0).

Reproducible:  python3 clean_elections.py            (reads raw/, writes the 3 CSVs)
               python3 clean_elections.py --report    (prints a per-race summary)
"""
import os, re, csv, sys, openpyxl

OUT = os.path.dirname(os.path.abspath(__file__))
SLICE = os.path.join(OUT, 'raw', 'riverton_slco_results_long.csv')
SOVC = os.path.join(OUT, 'raw', 'sovc')
RAW2021 = os.path.join(OUT, 'raw', 'sovc')
REPORT = '--report' in sys.argv


# --------------------------------------------------------------------------- helpers
def g(r, j):
    return r[j] if (r is not None and j < len(r)) else None


def norm_name(s):
    """Normalize a candidate name ALONGSIDE the verbatim source value (never overwrites
    raw): collapse whitespace, strip the (NP)/(NP ) non-partisan tag + leading write-in
    star, canonicalize write-ins."""
    s = re.sub(r'\s+', ' ', str(s).replace('\n', ' ')).strip()
    s = s.lstrip('*').strip()
    s = re.sub(r'\s*\(\s*(?:NP|NON)\s*\)', '', s, flags=re.I)     # (NP)/(NP )/(NON)
    s = re.sub(r'\bUNRESOLVED\s+WRITE[- ]?IN\b', 'Write-in (unresolved)', s, flags=re.I)
    s = re.sub(r'\bWRITE[- ]?IN\b', 'Write-in', s, flags=re.I)
    return re.sub(r'\s+', ' ', s).strip().strip('"').strip()


def to_int(v):
    if isinstance(v, (int, float)):
        return int(v)
    if isinstance(v, str) and v.strip().replace('.', '', 1).isdigit():
        return int(float(v))
    return None


# ---- contest canonicalization ----------------------------------------------
def canon(label):
    """Map any county contest label to (office, district, canonical_contest)."""
    U = label.upper()
    if 'MAYOR' in U:
        return ('Mayor', '', 'Riverton City Mayor')
    m = (re.search(r'DIST(?:RICT)?\s*#?\s*(\d+)', U)
         or re.search(r'#\s*(\d+)', U)
         or re.search(r'(\d+)\s*$', U.strip()))
    d = m.group(1) if m else '?'
    return ('Council', d, f'Riverton City Council District {d}')


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
    """Accumulate a precinct x candidate vote.  votes=None marks a suppressed cell."""
    R['per'].setdefault(precinct, {})
    if votes is None:
        R['suppressed_any'] = True
        R['per'][precinct].setdefault(cand, None)
        return
    R['cand'][cand] = R['cand'].get(cand, 0) + votes
    cur = R['per'][precinct].get(cand)
    R['per'][precinct][cand] = (cur + votes) if isinstance(cur, int) else votes


# --------------------------------------------------------------------------- (1) canonical slice
def load_slice():
    with open(SLICE, newline='') as fh:
        for row in csv.DictReader(fh):
            year = int(float(row['year']))
            # 2021 general is privacy-SUPPRESSED in the canonical slice (the county split
            # every cell at the In-Person/Vote-By-Mail method line -> '****', e.g. District 3
            # winner McCay shows 0 votes / all-suppressed).  We drop 2021 here and rebuild it
            # from the raw SOVC 'Total' sub-rows (parse_2021), which are UNsuppressed.
            if year == 2021:
                continue
            R = rec(year, row['election_type'], row['contest'], row['source_file'])
            prec = row['precinct'].strip()
            cand = norm_name(row['candidate'])
            v = row['votes'].strip()
            supp = row['suppressed'].strip().lower() == 'true'
            votes = None if (supp or v in ('', 'nan')) else int(float(v))
            add_vote(R, prec, cand, votes)
            reg = row['registered_voters'].strip()
            tc = row['times_cast'].strip()
            meth = row['vote_method'].strip()
            if reg not in ('', 'nan'):
                R['reg'][prec] = max(R['reg'].get(prec, 0), int(float(reg)))
            if tc not in ('', 'nan'):
                # ballots are per (precinct, vote_method); keep max within that cell
                R['ballots'][(prec, meth)] = max(R['ballots'].get((prec, meth), 0),
                                                 int(float(tc)))


# --------------------------------------------------------------------------- (2) 2019 raw parser
def parse_2019(path, etype, want_sheets):
    """Family-A wide crosstab.  Row0 title; row1 candidate names sparse at the head of
    each method block; row2 subheader (Precinct?, Registered Voters, then per candidate
    [Vote Centers, Vote (By/by) Mail, Early Voting, Total Votes], final Total); precinct
    rows (col0 == RIV###) then a 'Total:' summary row.  The per-candidate 'Total Votes'
    column is the precinct count for that candidate."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    PR = re.compile(r'RIV\w*\d+')
    for sh in want_sheets:
        ws = wb[sh]
        rows = [list(x) for x in ws.iter_rows(values_only=True)]
        title = str(g(rows[0], 0)).strip()
        name_row, sub_row = rows[1], rows[2]
        cand_cols = [(j, norm_name(name_row[j])) for j in range(len(name_row))
                     if name_row[j] not in (None, '')]
        # each candidate's Total Votes column = first 'Total Votes' at/after its name col
        tv_cols = [j for j, v in enumerate(sub_row) if str(v).strip() == 'Total Votes']
        cand_tv = {}
        for (jc, name) in cand_cols:
            after = [j for j in tv_cols if j >= jc]
            if after:
                cand_tv[name] = after[0]
        regj = next((j for j, v in enumerate(sub_row)
                     if 'Registered' in str(v)), None)
        R = rec(2019, etype, title, os.path.basename(path))
        for r in rows[3:]:
            c0 = g(r, 0)
            if isinstance(c0, str) and PR.fullmatch(c0.strip()):
                prec = c0.strip()
                for name, tvj in cand_tv.items():
                    add_vote(R, prec, name, to_int(g(r, tvj)))
                if regj is not None and to_int(g(r, regj)) is not None:
                    R['reg'][prec] = to_int(g(r, regj))


# --------------------------------------------------------------------------- (2b) 2021 raw parser
def parse_2021(path):
    """November-2-2021 SLCo general SOVC -- privacy-recovery parser.

    Layout ('precinct-block', Family-B): row1 = contest title ('RIVERTON CITY ... (Vote for
    1) **** - Insufficient Turnout to Protect Voter Privacy'); a subheader row carries the
    per-candidate name columns (each followed by a 'Total Votes' column) plus col1='Times
    Cast', col2='Registered Voters'.  Then, per precinct RIV###, a *block*: a header row
    (col0==RIV###), an 'In Person' row and a 'Vote By Mail' row -- both privacy-SUPPRESSED
    ('****') -- and a 'Total' sub-row that carries the UNsuppressed per-precinct count in the
    'Total Votes' column (and the precinct's Times Cast / Registered Voters).  We read only
    the 'Total' sub-rows, so the recovered per-precinct totals reconcile exactly to the
    candidate totals (the method split is the only thing the county suppressed).

    All three Riverton 2021 contests are single-candidate (uncontested), but the column
    logic handles multiple candidates for safety."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    PR = re.compile(r'RIV\w*\d+')

    def is_name(v):
        s = str(v).strip()
        return v not in (None, '') and not any(
            t in s for t in ('Total Votes', 'Precinct', 'Registered', 'Times Cast'))

    for sh in wb.sheetnames:
        ws = wb[sh]
        rows = [list(x) for x in ws.iter_rows(values_only=True)]
        # contest title = a cell (rows 0-3) starting 'RIVERTON'
        title = None
        for rr in rows[:4]:
            for c in (rr or []):
                if isinstance(c, str) and c.strip().upper().startswith('RIVERTON'):
                    title = c.split('(Vote')[0].strip()
                    break
            if title:
                break
        if not title:
            continue
        # subheader = first row that carries a 'Total Votes' column
        sub_i = next((i for i, rr in enumerate(rows)
                      if any(str(c).strip() == 'Total Votes' for c in (rr or []))), None)
        if sub_i is None:
            continue
        sub = rows[sub_i]
        tv_cols = [j for j, v in enumerate(sub) if str(v).strip() == 'Total Votes']
        cand_tv = {}
        for j, v in enumerate(sub):
            if is_name(v):
                after = [t for t in tv_cols if t >= j]
                if after:
                    cand_tv[norm_name(v)] = after[0]
        R = rec(2021, 'municipal general', title, os.path.basename(path))
        cur = None
        for r in rows[sub_i + 1:]:
            c0 = g(r, 0)
            s0 = c0.strip() if isinstance(c0, str) else ''
            if PR.fullmatch(s0):
                cur = s0                                    # new precinct block
            elif s0 == 'Total' and cur:                     # unsuppressed per-precinct row
                for name, tvj in cand_tv.items():
                    add_vote(R, cur, name, to_int(g(r, tvj)))
                reg = to_int(g(r, 2))
                if reg is not None:
                    R['reg'][cur] = reg
                tc = to_int(g(r, 1))
                if tc is not None:
                    R['ballots'][(cur, 'Total')] = tc
                cur = None                                  # block consumed


# --------------------------------------------------------------------------- run loaders
load_slice()
parse_2021(os.path.join(RAW2021,
           'november-2-2021-general-election-statement-of-votes-cast.xlsx'))
parse_2019(os.path.join(SOVC, '2019-11-05-general-election-sovc.xlsx'),
           'municipal general', ['RIV Council 1', 'RIV Council 2', 'RIV Council 5'])
parse_2019(os.path.join(SOVC, '2019-08-13-municipal-primary-sovc.xlsx'),
           'municipal primary', ['14', '15'])   # D2, D5 (no D1 primary -> logged)


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
        total_votes=total, total_first_choice_votes='',
        winner=winner, winner_votes=wv,
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


writecsv('riverton_races.csv', races,
         ['year', 'election_type', 'office', 'district', 'contest', 'contest_verbatim',
          'n_seats', 'n_candidates', 'voting_method', 'total_votes',
          'total_first_choice_votes', 'winner', 'winner_votes', 'winner_pct', 'runner_up',
          'runner_up_votes', 'margin_votes', 'margin_pct', 'registered_voters',
          'ballots_cast', 'turnout_pct', 'uncontested', 'suppressed_precincts', 'note',
          'source_file'])
writecsv('riverton_results_by_candidate.csv', by_cand,
         ['year', 'election_type', 'office', 'district', 'contest', 'candidate',
          'votes', 'pct', 'rank', 'is_winner'])
writecsv('riverton_results_by_precinct.csv', by_precinct,
         ['year', 'election_type', 'office', 'district', 'contest', 'precinct',
          'candidate', 'votes', 'suppressed'])

# --------------------------------------------------------------------------- report + checks
gen = [r for r in races if r['election_type'] == 'municipal general']
pri = [r for r in races if r['election_type'] == 'municipal primary']
print(f"races: {len(races)}  (general {len(gen)}, primary {len(pri)})")
print(f"by_candidate rows: {len(by_cand)}   by_precinct rows: {len(by_precinct)}")

# reconcile: precinct sums must equal candidate totals (except suppressed contests)
mism = 0
for k, R in RECORDS.items():
    for name, tot in R['cand'].items():
        psum = sum(v for p in R['per'].values()
                   for cn, v in p.items() if cn == name and isinstance(v, int))
        if psum != tot:
            mism += 1
            print(f"  MISMATCH {k} {name}: cand={tot} precinct_sum={psum}")
print(f"precinct<->candidate reconciliation mismatches: {mism}"
      f"  (suppressed contests excluded by design: "
      f"{sorted(set((k[0],k[2]) for k,R in RECORDS.items() if R['suppressed_any']))})")

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
