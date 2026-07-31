#!/usr/bin/env python3
"""Build Millcreek City (Salt Lake County, UT) election_results.

Millcreek is a **Council-Mayor** city: a **Mayor elected at-large** plus **4 council
DISTRICTS (1-4)**.  The **mayor is a full voting member** of the council (max council
tally = 5).  4-yr staggered terms.  Millcreek incorporated Dec 2016; its FIRST election
was the founding **Nov 2016** general (preceded by a **June 2016 primary**), so there is
no municipal-election record before 2016.  As the contests appear in the Salt Lake County
Statement-of-Votes-Cast (SOVC) files, the stagger is:

  * Cycle A (Mayor + District 1 + District 3): 2016(founding), 2019, 2023, 2027
  * Cycle B (Districts 2 + 4):                 2016(founding, 1-yr seat), 2017, 2021, 2025

(The founding 2016 election filled all five seats; D2/D4 drew short initial terms and were
re-filled in 2017, putting them on the 2017/2021/2025 cycle, while Mayor/D1/D3 landed on
the 2019/2023/2027 cycle.)

SOURCES  (Salt Lake County Clerk, mirrored locally in ~/Desktop/slco-election-archive)
--------------------------------------------------------------------------------------
Two provenance layers, both retained under raw/:

1. raw/municipal_results_long_millcreek.csv
      The archive's own canonical SOVC normalization (sovc_long.csv), filtered to
      Millcreek council/mayor candidate contests 2016-2025 (pre-incorporation ballot
      questions -- 2012 INCORPORATION/COUNCIL DISTS, 2015 METRO TOWNSHIP/MSD -- are
      excluded).  Precinct- and vote-method-level; sums cleanly to contest totals with
      ZERO suppression for **2016 (primary + general), 2017, 2023 (D3) and 2025** -- these
      are consumed straight from this slice.

2. raw/sovc/*.xlsx  (the true county SOVC spreadsheets)
      Re-parsed directly for the two general cycles the archive's parsed layer does not
      deliver cleanly:
        * 2019 general (Mayor / D1 / D3) -- present in the parsed layer only under the raw
          sheet codes "MIL Mayor" / "MIL Council 1" / "MIL Council 3", where the
          normalizer lost the candidate names (it emitted "Total"/method strings as
          candidates).  A '%MILLCREEK%' contest filter also misses them.  RECOVERED from
          raw for faithful candidate names + precinct totals.
        * 2021 general (D2 / D4) -- present in the parsed layer but privacy-SUPPRESSED at
          the In-Person / Vote-By-Mail method split (64/80 + 104/120 rows '****'), which
          destroys the precinct totals.  RE-PARSED from raw, whose per-precinct 'Total'
          sub-rows are NOT suppressed.

RANKED-CHOICE VOTING (RCV):
  Millcreek joined Utah's municipal RCV pilot in **2021 and 2023**, so those council
  races were tabulated by instant-runoff, not plurality.  The county SOVC only carries
  **first-choice** tallies (the round-by-round tabulation is published separately), so the
  by_candidate / by_precinct vote counts here are FIRST-CHOICE.  The race `winner` is the
  official FINAL-ROUND winner (sourced externally), which can differ from the first-choice
  leader: in **2021 District 2 the first-choice leader Jeremiah Clark LOST** after Bagley-
  Gibson's and Vice's ballots transferred -- **Thom DeSirant won the final round 51.75% to
  48.25%**.  In 2021 D4 (Uipi 56.9% v Parker 43.1% final) and 2023 D3 (Jackson 76% first-
  choice = round-1 majority) the first-choice leader also won.  For RCV rows
  `voting_method='ranked choice (RCV)'`; see election_results/CLAUDE.md for the final-round
  figures.  (2016/2017/2019/2025 were plurality; 2025's two-candidate races are plurality-
  equivalent regardless.)

VERIFIED external facts (see election_results/CLAUDE.md for citations):
  * 2016 general MAYOR was **uncontested**: Silvestrini won the 9-way June primary; the
    primary runner-up Fred Healey **withdrew in Aug 2016** (cancer), so Silvestrini ran
    unopposed and took 100% (21,288) in the general.  The single-candidate raw sheet is
    faithful, not a defect.
  * 2023 MAYOR and 2023 D1 were **NOT held** -- both were uncontested (only the incumbent
    filed, no write-ins), so Millcreek **canceled** those races under Utah law
    (UCA 20A-1-206).  No vote counts exist; Silvestrini (Mayor) and Silvia Catten (D1)
    were re-elected by default.  Recorded here as uncontested/cancelled race rows with
    BLANK vote fields (winner sourced from the city / Millcreek Journal) -- never
    fabricated counts.  Logged, not filled.
  * 2025 MAYOR was **not on the ballot** (Mayor is on the 2027 cycle).  Cheri Jackson
    became Millcreek's 2nd mayor by **council APPOINTMENT** on 2025-11-03 (special
    meeting, unanimous) to serve the ~2 remaining years of Silvestrini's term after his
    health retirement -- an appointment/succession, NOT an election.  She vacated D3; the
    council then appointed Nicole Handy to D3.

Reproducible:  python3 clean_elections.py            (reads raw/, writes the 3 CSVs)
               python3 clean_elections.py --report    (prints a per-race summary)
"""
import os, re, csv, sys, openpyxl

OUT = os.path.dirname(os.path.abspath(__file__))
SLICE = os.path.join(OUT, 'raw', 'municipal_results_long_millcreek.csv')
SOVC = os.path.join(OUT, 'raw', 'sovc')
REPORT = '--report' in sys.argv


# --------------------------------------------------------------------------- helpers
def g(r, j):
    return r[j] if (r is not None and j < len(r)) else None


def norm_name(s):
    """Normalize a candidate name ALONGSIDE the verbatim value (never overwrites raw):
    collapse whitespace, strip the (NP)/(NON) non-partisan tag, canonicalize write-ins."""
    s = re.sub(r'\s+', ' ', str(s).replace('\n', ' ')).strip()
    s = s.lstrip('*').strip()
    s = re.sub(r'\s*\(\s*(?:NP|NON)\s*\)', '', s, flags=re.I)     # strip (NP)/(NON)
    s = re.sub(r'\bUNRESOLVED\s+WRITE[- ]?IN\b', 'Write-in (unresolved)', s, flags=re.I)
    s = re.sub(r'\bWRITE[- ]?IN\b', 'Write-in', s, flags=re.I)
    return re.sub(r'\s+', ' ', s).strip().strip('"').strip()


def to_int(v):
    return int(v) if isinstance(v, (int, float)) else None


def norm_etype(e):
    e = e.strip().lower()
    if e in ('primary', 'municipal primary'):
        return 'municipal primary'
    return 'municipal general'


PRECINCT = re.compile(r'[A-Z]{2,3}\d+[A-Z]*$')


# ---- contest canonicalization ----------------------------------------------
def canon(label):
    """Map any county contest label to (office, district, canonical_contest)."""
    U = re.sub(r'\s+', ' ', str(label).upper()).strip()
    if 'MAYOR' in U:
        return ('Mayor', '', 'Millcreek City Mayor')
    m = (re.search(r'DIST(?:RICT)?\s*#?\s*(\d+)', U)
         or re.search(r'(?:CNCL|COUNCIL)\s*#?\s*(\d+)', U)
         or re.search(r'(\d+)\s*(?:\(VOTE|$)', U))
    d = m.group(1) if m else '?'
    return ('Council', d, f'Millcreek City Council District {d}')


# --------------------------------------------------------------------------- containers
RECORDS = {}   # key = (year, election_type, contest) -> record


def rec(year, etype, label, source_file):
    etype = norm_etype(etype)
    office, district, contest = canon(label)
    k = (year, etype, contest)
    if k not in RECORDS:
        RECORDS[k] = dict(year=year, election_type=etype, office=office,
                          district=district, contest=contest,
                          cand={}, per={}, reg={}, ballots={},
                          suppressed_any=False, cancelled=False,
                          source_file=source_file, verbatim=str(label).strip())
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
# Consume clean years straight from the slice; 2019 (broken names) & 2021 (suppressed)
# are re-parsed from raw instead.
SLICE_SKIP = {'2021'}


def load_slice():
    with open(SLICE, newline='') as fh:
        for row in csv.DictReader(fh):
            year = str(int(float(row['year'])))
            if year in SLICE_SKIP:
                continue
            contest_raw = row['contest']
            R = rec(year, row['election_type'], contest_raw, row['source_file'])
            prec = row['precinct'].strip()
            cand = norm_name(row['candidate'])
            v = row['votes'].strip()
            votes = int(float(v)) if v not in ('', 'nan') else None
            supp = str(row['suppressed']).strip().lower() == 'true'
            add_vote(R, prec, cand, None if (supp or votes is None) else votes)
            reg = row['registered_voters'].strip()
            tc = row['times_cast'].strip()
            if reg not in ('', 'nan'):
                R['reg'][prec] = max(R['reg'].get(prec, 0), int(float(reg)))
            if tc not in ('', 'nan'):
                R['ballots'][prec] = max(R['ballots'].get(prec, 0), int(float(tc)))


# --------------------------------------------------------------------------- (2) raw parsers
def parse_2019(path):
    """2019 Family-A wide crosstab (sheets 'MIL Mayor' / 'MIL Council 1' / 'MIL Council 3'):
    r0 contest title; r1 candidate names sparse; r2 sub-header where each candidate's total
    sits under a 'Total Votes' marker and col1 == 'Registered Voters'; precinct rows
    (col0 == MIL###) follow.  No ballots-cast column -> turnout left blank."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    for sh in wb.sheetnames:
        if not sh.upper().startswith('MIL '):
            continue
        ws = wb[sh]
        rows = [list(x) for x in ws.iter_rows(values_only=True)]
        title = str(g(rows[0], 0))
        name_row, sub_row = rows[1], rows[2]
        cand_cols = [(j, norm_name(name_row[j])) for j in range(len(name_row))
                     if name_row[j] not in (None, '')]
        tv_cols = [j for j, v in enumerate(sub_row) if str(v).strip() == 'Total Votes']
        cand_tv = dict(zip([n for _, n in cand_cols], tv_cols))
        regj = next((j for j, v in enumerate(sub_row) if 'Registered' in str(v)), None)
        R = rec('2019', 'municipal general', title, os.path.basename(path))
        for r in rows[3:]:
            c0 = g(r, 0)
            if isinstance(c0, str) and PRECINCT.match(c0.strip()):
                prec = c0.strip()
                for c, tvj in cand_tv.items():
                    add_vote(R, prec, c, to_int(g(r, tvj)))
                if regj is not None and to_int(g(r, regj)) is not None:
                    R['reg'][prec] = to_int(g(r, regj))


def parse_2021(path, sheets):
    """2021 columnar: header row (col0 == 'Precinct') carries Times Cast (col1),
    Registered (col2), a 2nd 'Precinct' marker, then candidate value columns (each
    followed by a % column) and a trailing 'Total Votes' column.  Each precinct block ends
    in a 'Total' sub-row whose candidate cells are the UN-suppressed precinct counts."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    SKIP = {'PRECINCT', 'TIMES CAST', 'REGISTERED', 'REGISTERED VOTERS', 'TOTAL VOTES'}
    for sh in sheets:
        ws = wb[sh]
        rows = [list(x) for x in ws.iter_rows(values_only=True)]
        title = next(str(g(r, 0)) for r in rows[:3]
                     if g(r, 0) and 'MILLCREEK' in str(g(r, 0)).upper())
        hi = next(i for i, r in enumerate(rows) if str(g(r, 0)).strip() == 'Precinct')
        hdr = rows[hi]
        tcj = next((j for j in range(len(hdr)) if 'Times Cast' in str(g(hdr, j))), None)
        rgj = next((j for j in range(len(hdr)) if 'Registered' in str(g(hdr, j))), None)
        cand_cols = {}
        for j, c in enumerate(hdr):
            if c in (None, ''):
                continue
            L = re.sub(r'\s+', ' ', str(c).replace('\n', ' ')).strip().upper()
            if L not in SKIP and not L.endswith('%'):
                cand_cols[j] = norm_name(c)
        R = rec('2021', 'municipal general',
                re.sub(r'\s*\(Vote.*', '', title).strip(), os.path.basename(path))
        cur = None
        for r in rows[hi + 1:]:
            c0 = str(g(r, 0)).strip() if g(r, 0) is not None else ''
            if PRECINCT.match(c0):
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


def add_cancelled(year, label, winner, note):
    """A race that legally occurred but was CANCELLED as uncontested (no ballot, no
    count).  Record a race row with blank vote fields + a single blank candidate row.
    Winner is documented from the city / news, never a fabricated tally."""
    R = rec(year, 'municipal general', label, note)
    R['cancelled'] = True
    R['cand'] = {norm_name(winner): None}


# --------------------------------------------------------------------------- run loaders
load_slice()
parse_2019(os.path.join(SOVC, '2019-11-05-general-election-sovc.xlsx'))
parse_2021(os.path.join(SOVC, '2021-11-02-general-election-sovc.xlsx'),
           ['Sheet22', 'Sheet23'])
add_cancelled('2023', 'MILLCREEK CITY MAYOR', 'JEFF SILVESTRINI',
              'CANCELLED-UNCONTESTED (Millcreek City / UCA 20A-1-206); not in county SOVC')
add_cancelled('2023', 'MILLCREEK CITY COUNCIL DISTRICT 1', 'SILVIA CATTEN',
              'CANCELLED-UNCONTESTED (Millcreek City / UCA 20A-1-206); not in county SOVC')


# --------------------------------------------------------------------------- RCV
# (year, contest) -> official FINAL-ROUND winner (Millcreek's 2021/2023 RCV races).
# Vote counts stay first-choice (all the SOVC carries); only the winner reflects the
# instant-runoff outcome.  The one race where the first-choice leader lost is 2021 D2.
RCV_WINNER = {
    ('2021', 'Millcreek City Council District 2'): 'THOM DESIRANT',
    ('2021', 'Millcreek City Council District 4'): 'BEV UIPI',
    ('2023', 'Millcreek City Council District 3'): 'CHERI JACKSON',
}


def rcv_key(name):
    return re.sub(r'[^A-Z ]', '', norm_name(name).upper()).strip()


# --------------------------------------------------------------------------- reconcile
def real_cands(items):
    return [(n, v) for n, v in items
            if not (n.startswith('Write-in') and (v or 0) == 0)]


mismatch = 0
for k, R in RECORDS.items():
    if R['cancelled']:
        continue
    for cand, tot in R['cand'].items():
        psum = sum((R['per'][p].get(cand) or 0) for p in R['per']
                   if isinstance(R['per'][p].get(cand), int))
        if psum != (tot or 0):
            mismatch += 1
            print(f"  !! precinct-sum mismatch {k} {cand}: cand={tot} per-sum={psum}")
assert mismatch == 0, f"{mismatch} precinct/candidate reconciliation mismatches"


# --------------------------------------------------------------------------- compute + write
races, by_cand, by_precinct = [], [], []
for k in sorted(RECORDS, key=lambda x: (x[0], x[1], x[2])):
    R = RECORDS[k]
    items = sorted(R['cand'].items(), key=lambda kv: (-(kv[1] or 0), kv[0]))
    rc = real_cands(items)
    if R['cancelled']:
        winner = items[0][0] if items else ''
        races.append(dict(
            year=R['year'], election_type=R['election_type'], office=R['office'],
            district=R['district'], contest=R['contest'], contest_verbatim=R['verbatim'],
            n_seats=1, n_candidates=1, voting_method='uncontested (election cancelled)',
            total_votes='', winner=winner, winner_votes='', winner_pct='',
            runner_up='', runner_up_votes='', margin_votes='', margin_pct='',
            registered_voters='', ballots_cast='', turnout_pct='',
            uncontested='True', suppressed_precincts='False', source_file=R['source_file']))
        by_cand.append(dict(
            year=R['year'], election_type=R['election_type'], office=R['office'],
            district=R['district'], contest=R['contest'], candidate=winner,
            votes='', pct='', rank=1, is_winner='True'))
        continue
    total = sum(v or 0 for v in R['cand'].values())
    rcv = RCV_WINNER.get((R['year'], R['contest']))
    voting_method = 'ranked choice (RCV)' if rcv else 'plurality'
    if rcv:
        # winner = official final-round winner; runner-up = the strongest of the rest by
        # first choice; counts remain first-choice (see module docstring).
        wname = next((n for n, _ in items if rcv_key(n) == rcv_key(rcv)), None)
        assert wname is not None, f"RCV winner {rcv!r} not found in {R['contest']} {R['year']}"
        winner, wv = wname, R['cand'][wname]
        rest = [(n, v) for n, v in items if n != wname]
        runner, rv = (rest[0] if rest else ('', 0))
    else:
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
        n_seats=1, n_candidates=len(rc), voting_method=voting_method,
        total_votes=total, winner=winner, winner_votes=wv,
        winner_pct=round(100 * (wv or 0) / total, 2) if total else 0,
        runner_up=runner, runner_up_votes=rv,
        margin_votes=margin, margin_pct=round(100 * margin / total, 2) if total else 0,
        registered_voters=reg_total, ballots_cast=ballots_total, turnout_pct=turnout,
        uncontested='True' if len(rc) <= 1 else 'False',
        suppressed_precincts='True' if R['suppressed_any'] else 'False',
        source_file=R['source_file']))
    for rank, (name, v) in enumerate(items, 1):
        won = (name == winner) if rc else False   # winner respects RCV final-round outcome
        by_cand.append(dict(
            year=R['year'], election_type=R['election_type'], office=R['office'],
            district=R['district'], contest=R['contest'], candidate=name,
            votes=v or 0, pct=round(100 * (v or 0) / total, 2) if total else 0,
            rank=rank, is_winner='True' if won else 'False'))
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


writecsv('millcreek_races.csv', races,
         ['year', 'election_type', 'office', 'district', 'contest', 'contest_verbatim',
          'n_seats', 'n_candidates', 'voting_method', 'total_votes', 'winner',
          'winner_votes', 'winner_pct', 'runner_up', 'runner_up_votes', 'margin_votes',
          'margin_pct', 'registered_voters', 'ballots_cast', 'turnout_pct',
          'uncontested', 'suppressed_precincts', 'source_file'])
writecsv('millcreek_results_by_candidate.csv', by_cand,
         ['year', 'election_type', 'office', 'district', 'contest', 'candidate',
          'votes', 'pct', 'rank', 'is_winner'])
writecsv('millcreek_results_by_precinct.csv', by_precinct,
         ['year', 'election_type', 'office', 'district', 'contest', 'precinct',
          'candidate', 'votes', 'suppressed'])

# --------------------------------------------------------------------------- report
gen = [r for r in races if r['election_type'] == 'municipal general']
pri = [r for r in races if r['election_type'] == 'municipal primary']
print(f"races: {len(races)}  (general {len(gen)}, primary {len(pri)})")
print(f"by_candidate rows: {len(by_cand)}   by_precinct rows: {len(by_precinct)}")
print(f"precinct/candidate reconciliation mismatches: {mismatch}")
if REPORT:
    for r in sorted(races, key=lambda x: (x['year'], x['election_type'], x['contest'])):
        tag = 'PRIMARY ' if r['election_type'] == 'municipal primary' else ''
        unc = ' [UNCONTESTED]' if r['uncontested'] == 'True' else ''
        can = ' [CANCELLED]' if r['voting_method'].startswith('uncontested') else ''
        sup = ' [suppressed]' if r['suppressed_precincts'] == 'True' else ''
        to = f" turnout {r['turnout_pct']}%" if r['turnout_pct'] != '' else ''
        print(f"  {r['year']} {tag}{r['contest']:36s} n={r['n_candidates']} "
              f"WIN {r['winner']} {r['winner_votes']} ({r['winner_pct']}%) vs "
              f"{r['runner_up']} {r['runner_up_votes']}  margin {r['margin_votes']} "
              f"[tot {r['total_votes']}{to}]{unc}{can}{sup}")
