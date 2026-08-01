#!/usr/bin/env python3
"""Build Draper City (Utah) municipal election_results.

DRAPER IS ALL AT-LARGE (no districts): a separately-elected Mayor + 5 at-large
Council Members, 4-year staggered terms. City Council runs as a SINGLE
multi-winner field each cycle — the top N vote-getters win the N open seats
(N = vote-for). So a council "race" has MULTIPLE winners; is_winner = rank<=N.
(Model mirrors the St. George at-large build; schema is the 25-col SLC/South
Jordan superset.)  Mayor is a normal single-winner race. district = "At-Large"
for council, "" for Mayor.

ADMINISTERING COUNTY -- Salt Lake County runs the ENTIRE Draper municipal
election (Utah County reports NO Draper city race; the sole Utah-County Draper
item ever found is a 2011 bond, excluded here). So the canonical Salt Lake
County SOVC is the whole-city total.

SOURCES (all retained under raw/, never edited)
------------------------------------------------
1. raw/municipal_results_long_draper.csv
     The Salt Lake County archive's canonical SOVC normalization
     (~/Desktop/slco-election-archive), filtered to Draper. Precinct- and
     vote-method-level. Consumed for 2007, 2009, 2011, 2013, 2015, 2017,
     2023, 2025 (+ their primaries) -- all clean, ZERO suppression, summing
     across vote methods to faithful contest totals. The "Utah County Draper
     Bond" (2011) contest is EXCLUDED (bond measure, not a council/mayor race).
2. raw/sovc/2021-11-02-general-election-sovc.xlsx  (Sheet11 Mayor / Sheet12 Council)
     The 2021 general is 280/350 privacy-SUPPRESSED at the In-Person/Vote-By-
     Mail method split in the archive slice, which destroys the totals. RE-
     PARSED here from the raw county SOVC, whose per-precinct 'Total' sub-rows
     are NOT suppressed (reconciles exactly to the Electionwide-Total row:
     Mayor Walker 5360; council Lowery 3105).
3. raw/sovc/2019-11-05-general-election-sovc.xlsx  (sheet 'DRP Council')
     The 2019 Draper council race is ABSENT from the long file (0 rows -- the
     archive normalizer keyed the contest off the sheet name 'DRP Council', so
     a '%DRAPER%' filter missed it: the KNOWN 2019 GAP flagged in recon.md).
     RECOVERED from the raw county SOVC (Family-A wide crosstab). There was NO
     2019 Draper municipal PRIMARY (verified: no Draper sheet in the 2019
     primary SOVC -- 5 candidates for 3 seats, below the 2N=6 primary trigger).

SEAT COUNTS (n_seats) -- cross-confirmed, not guessed
-----------------------------------------------------
vote-for is authoritative in the source for 2021 (1) / 2023 (3) / 2025 (1).
For 2007-2019 the SOVC carries no 'Vote For' string, so n_seats is derived and
INTERNALLY CONFIRMED by the primary->general "top 2N advance" candidate counts:
  2007: primary 13 cands -> general 6  => 2N=6 => 3 seats
  2009: primary  6 cands -> general 4  => 2N=4 => 2 seats
  2013: primary  7 cands -> general 4  => 2N=4 => 2 seats
  2017: primary  6 cands -> general 4  => 2N=4 => 2 seats
  2011/2015/2019: no primary (<=2N candidates) -> seat count from the stable
     4-year re-election chain (Cycle A = 3 seats, anchored by 2023 vote-for=3).
Two staggered cycles: A (2007,2011,2015,2019,2023)=3 seats;
B (2009,2013,2017)=2 seats, then disrupted to 1 seat in 2021 & a 2-year
unexpired seat in 2025 (Draper's stagger was broken by mid-term vacancies).
Mayor is elected on the B calendar (2009,2013,2017,2021,2025), always 1 seat.

CANCELED-UNCONTESTED RACES (no ballot, no votes, no county SOVC row)
---------------------------------------------------------------------
Utah Code 20A-1-206(3) lets a municipal legislative body CANCEL a race whose
ballot would carry no contested race or ballot proposition, certifying the
candidate(s) elected by resolution instead. Such a race NEVER reaches the county
SOVC, so it cannot be parsed from raw/ -- it is recorded here from the CITY's own
adopted instrument, with BLANK vote fields (never a fabricated tally), mirroring
the millcreek (2023) and alta (2025) convention. See CANCELED below: Draper's
2025 REGULAR 2-seat 4-year at-large Council race (Res #25-49).

Reproducible:  python3 clean_elections.py            (reads raw/, writes 3 CSVs)
               python3 clean_elections.py --report    (per-race summary)
"""
import os, re, csv, sys, openpyxl

OUT = os.path.dirname(os.path.abspath(__file__))
SLICE = os.path.join(OUT, 'raw', 'municipal_results_long_draper.csv')
SOVC = os.path.join(OUT, 'raw', 'sovc')
REPORT = '--report' in sys.argv

# Years taken from the archive slice. 2019 & 2021 come from raw (gap / suppression);
# ALL of 2025 comes from raw too: the archive normalizer silently DROPPED the new
# 2025-vintage precincts labelled "25DR0N" (its precinct regex didn't match the
# year-prefix), undercounting every 2025 Draper race by ~600 votes. Re-parsed here
# from the raw SOVC so the totals reconcile to the certified Electionwide-Total.
SLICE_YEARS = {2007, 2009, 2011, 2013, 2015, 2017, 2023}

# n_seats the cycle fills, keyed (year, office). Primaries reuse the same n.
SEATS = {
    (2007, 'Council'): 3, (2009, 'Council'): 2, (2011, 'Council'): 3,
    (2013, 'Council'): 2, (2015, 'Council'): 3, (2017, 'Council'): 2,
    (2019, 'Council'): 3, (2021, 'Council'): 1, (2023, 'Council'): 3,
    (2025, 'Council'): 1,
    (2009, 'Mayor'): 1, (2013, 'Mayor'): 1, (2017, 'Mayor'): 1,
    (2021, 'Mayor'): 1, (2025, 'Mayor'): 1,
}
# Draper ran Utah's municipal RANKED-CHOICE-VOTING pilot in 2021. The 2021 council
# GENERAL (7 candidates, vote-for-1) was decided by instant-runoff, so — mirroring the
# Millcreek RCV convention — its race row is stamped voting_method='ranked choice (RCV)'.
# The Salt Lake County SOVC publishes only FIRST-CHOICE tallies (the round-by-round
# tabulation is separate), so winner_pct (36.95%) is a first-choice share, NOT the
# RCV-final margin; the first-choice leader (Tasha Lowery) also won the final round, so the
# `winner` is correct. First-choice tallies are retained verbatim. The 2021 MAYOR race had
# a SINGLE candidate (uncontested, 100% — no ranking occurred), so it stays plurality.
RCV = {(2021, 'municipal general', 'Council')}

# 2025 council seat is a short/unexpired (2-year) term
NOTE = {(2025, 'municipal general', 'Council'): '2-year unexpired/short term',
        (2025, 'municipal primary', 'Council'): '2-year unexpired/short term',
        (2021, 'municipal general', 'Council'):
            'RCV pilot (2021) — winner_pct is a first-choice share, not the RCV-final '
            'margin; winner led first choice and won the final round'}

PREC = re.compile(r'^(?:25)?DRP?\d+$')   # DRP001, DR01, 25DR02 (2025 vintage)

# --------------------------------------------------------------- canceled-uncontested
# Races CANCELED as uncontested under Utah Code 20A-1-206(3): no ballot line, no votes
# cast, no county SOVC row — the winners are CERTIFIED by city resolution. Emitted as a
# race row + one by_candidate row per certified winner, ALL tally columns BLANK (never a
# fabricated count) and uncontested=True. No by_precinct rows exist (no ballots).
#
# DRAPER 2025 — the REGULAR 2-seat 4-YEAR at-large Council race (Cohort B). Primary
# instrument (verbatim, on disk):
#   ../packets/text/2025-10-07_Council_exh3636839_Resolution_25-49_Canceling_Race_and_
#     Declaring_Candidates_Elected.txt   (raw PDF: ../packets/raw/2025-10-07/…pdf)
# "A RESOLUTION OF THE DRAPER CITY COUNCIL CANCELING THE ELECTION FOR THE 4-YEAR
# AT-LARGE CITY COUNCIL SEATS AND CERTIFYING THE CANDIDATES AS ELECTED" — recitals cite
# Utah Code § 20A-1-206(3) and (3)(b), record "two open 4-year at-large City Council
# seats scheduled for the November 4, 2025 Draper City General Election" and that
# "following the withdrawal of candidate Jared Turner, the number of candidates equaled
# the number of open seats"; Section 2 certifies "Tasha Lowery and Mike Green are
# considered elected". Continued from the 2025-09-16 Council meeting for a noticing
# issue (motion by F. Lowry, 5-0) and PASSED AND ADOPTED 2025-10-07 (item 7.d, motion by
# Johnson, sec. Vawdrey, roll call 5-0) — both meetings in meeting_minutes/minutes/2025/.
#
# ⚠ This is a SECOND 2025 municipal-general Council row: it coexists with the
# SOVC-counted "(2 YEAR TERM) (Vote for 1)" UNEXPIRED-seat race that Kathryn Dahlin won.
# Distinguish the two by contest_verbatim / n_seats / uncontested — never by
# (year, office) alone. `winner` carries the first-listed certified candidate (the
# 25-col schema has one winner slot); BOTH winners are in draper_results_by_candidate.csv
# (is_winner=True, blank votes/pct/rank) — that is the join surface for member records.
CANCELED = [dict(
    year=2025, election_type='municipal general', office='Council',
    district='At-Large', contest='Draper City Council At-Large',
    # verbatim from the resolution's own title (no ballot label exists — never printed)
    contest_verbatim='THE 4-YEAR AT-LARGE CITY COUNCIL SEATS',
    n_seats=2, n_candidates=2,
    winners=['TASHA LOWERY', 'MIKE GREEN'],
    note=('CANCELED-UNCONTESTED (Draper City / UCA 20A-1-206(3)); Res #25-49 adopted '
          '2025-10-07 (5-0), continued from 2025-09-16 — the 2-seat 4-YEAR at-large '
          'Council race was canceled when candidate Jared Turner withdrew, leaving 2 '
          'candidates for 2 seats, and TASHA LOWERY + MIKE GREEN were certified elected. '
          'NO ballot, NO votes cast, NOT in the county SOVC -> every tally column is '
          'intentionally BLANK. Both winners are rows in '
          'draper_results_by_candidate.csv. Separate from the 2025 "(2 YEAR TERM) '
          '(Vote for 1)" unexpired-seat race (Dahlin), which WAS on the ballot.'),
    source_file=('packets/text/2025-10-07_Council_exh3636839_Resolution_25-49_'
                 'Canceling_Race_and_Declaring_Candidates_Elected.txt'))]


# --------------------------------------------------------------------------- helpers
def g(r, j):
    return r[j] if (r is not None and j < len(r)) else None


def to_int(v):
    return int(v) if isinstance(v, (int, float)) else None


def norm_name(s):
    """Normalize a candidate name ALONGSIDE the verbatim value (never overwrites
    raw): collapse whitespace, strip (NP)/(NON) non-partisan tag + leading
    write-in mark, canonicalize write-ins."""
    s = re.sub(r'\s+', ' ', str(s).replace('\n', ' ')).strip()
    s = s.lstrip('*').strip()
    s = re.sub(r'\s*\(\s*(?:NP|NON)\s*\)', '', s, flags=re.I)
    s = re.sub(r'\bUNRESOLVED\s+WRITE[- ]?IN\b', 'Write-in (unresolved)', s, flags=re.I)
    s = re.sub(r'\bWRITE[- ]?IN\b', 'Write-in', s, flags=re.I)
    return re.sub(r'\s+', ' ', s).strip().strip('"').strip()


def canon(label):
    U = label.upper()
    if 'MAYOR' in U:
        return ('Mayor', '', 'Draper City Mayor')
    return ('Council', 'At-Large', 'Draper City Council At-Large')


# --------------------------------------------------------------------------- containers
RECORDS = {}   # (year, etype, contest) -> record


def rec(year, etype, label, source_file):
    office, district, contest = canon(label)
    k = (year, etype, contest)
    if k not in RECORDS:
        RECORDS[k] = dict(year=year, election_type=etype, office=office,
                          district=district, contest=contest, cand={}, per={},
                          reg={}, ballots={}, source_file=source_file,
                          verbatim=label)
    return RECORDS[k]


def add_vote(R, prec, cand, votes):
    if votes is None:
        return
    R['cand'][cand] = R['cand'].get(cand, 0) + votes
    R['per'].setdefault(prec, {})
    R['per'][prec][cand] = R['per'][prec].get(cand, 0) + votes


# --------------------------------------------------------------------------- (1) archive slice
def load_slice():
    with open(SLICE, newline='') as fh:
        for row in csv.DictReader(fh):
            year = int(float(row['year']))
            if year not in SLICE_YEARS:
                continue
            contest_raw = row['contest']
            if contest_raw.lower().startswith('utah county'):
                continue                       # 2011 Draper bond -> not a city race
            R = rec(year, row['election_type'], contest_raw, row['source_file'])
            prec = row['precinct'].strip()
            cand = norm_name(row['candidate'])
            v = row['votes'].strip()
            votes = int(float(v)) if v not in ('', 'nan') else None
            add_vote(R, prec, cand, votes)
            reg = row['registered_voters'].strip()
            tc = row['times_cast'].strip()
            if reg not in ('', 'nan'):
                R['reg'][prec] = max(R['reg'].get(prec, 0), int(float(reg)))
            if tc not in ('', 'nan'):
                R['ballots'][prec] = max(R['ballots'].get(prec, 0), int(float(tc)))


# --------------------------------------------------------------------------- (2) raw 2021
def parse_2021(path):
    """Columnar SOVC: each precinct has In-Person / Vote-By-Mail method sub-rows
    ('****' suppressed) and a 'Total' sub-row carrying the UN-suppressed count.
    Left block col0='Precinct', col1='Times Cast', col2='Registered'; a second
    'Precinct' at col4 precedes the candidate value columns."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    for shn, verbatim_key in (('Sheet11', 'MAYOR'), ('Sheet12', 'COUNCIL')):
        ws = wb[shn]
        rows = [list(r) for r in ws.iter_rows(values_only=True)]
        title = re.sub(r'\s+', ' ', str(rows[1][0]).replace('\n', ' ')).strip()
        verbatim = re.sub(r'\s*\*\*\*\*.*$', '', title).strip()   # drop privacy note
        hdr = rows[3]
        ccols = {}
        for j, c in enumerate(hdr):
            if j < 5 or c in (None, ''):
                continue
            s = re.sub(r'\s+', ' ', str(c).replace('\n', ' ')).strip()
            if 'Total Votes' in s or 'Precinct' in s:
                continue
            ccols[j] = norm_name(s)
        R = rec(2021, 'municipal general', verbatim, os.path.basename(path))
        cur = None
        for r in rows[4:]:
            c0 = (str(g(r, 0)).strip() if g(r, 0) is not None else '')
            low = c0.lower()
            if low in ('in person', 'vote by mail', 'total'):
                if low == 'total' and cur:
                    for j, name in ccols.items():
                        add_vote(R, cur, name, to_int(g(r, j)))
                    tc = to_int(g(r, 1)); rg = to_int(g(r, 2))
                    if tc is not None:
                        R['ballots'][cur] = tc
                    if rg is not None:
                        R['reg'][cur] = rg
            elif PREC.match(c0):
                cur = c0
            else:
                cur = None                     # skip Electionwide/Cumulative/County summaries


# --------------------------------------------------------------------------- (3) raw 2019
def parse_2019(path):
    """Family-A wide crosstab: row0 contest, row1 candidate names (sparse),
    row2 sub-header marking each candidate's 'Total Votes' column, rows3+ are
    precinct rows (col0 = DRP###, col1 = Registered Voters)."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb['DRP Council']
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    name_row, sub_row = rows[1], rows[2]
    # pair each candidate name col with the next 'Total Votes' col
    tv_cols = [j for j, v in enumerate(sub_row) if str(v).strip() == 'Total Votes']
    cand_tv = {}
    for j, v in enumerate(name_row):
        if v not in (None, ''):
            tv = next((t for t in tv_cols if t > j), None)
            if tv is not None:
                cand_tv[norm_name(v)] = tv
    regj = next((j for j, v in enumerate(sub_row) if 'Registered' in str(v)), None)
    R = rec(2019, 'municipal general', 'DRAPER CITY COUNCIL AT LARGE',
            os.path.basename(path))
    for r in rows[3:]:
        c0 = g(r, 0)
        if isinstance(c0, str) and PREC.match(c0.strip()):
            prec = c0.strip()
            for cand, tv in cand_tv.items():
                add_vote(R, prec, cand, to_int(g(r, tv)))
            if regj is not None and to_int(g(r, regj)) is not None:
                R['reg'][prec] = to_int(g(r, regj))


# --------------------------------------------------------------------------- (4) raw 2025
def parse_2025(path, etype):
    """2025 columnar SOVC (one row per precinct, no method sub-rows): left block
    col0='Precinct', col1='Times Cast', col2='Registered'; a second 'Precinct'
    at col4 precedes candidate value columns; a 'Total Votes' column and an
    'Unresolved Write-In' column follow. Every Draper sheet (Mayor + Council) is
    processed. Includes the 2025-vintage '25DR0N' precincts the archive dropped."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    for shn in wb.sheetnames:
        ws = wb[shn]
        rows = [list(r) for r in ws.iter_rows(values_only=True)]
        title = None
        for r in rows[:3]:
            for c in r:
                if c and 'draper' in str(c).lower():
                    title = str(c); break
            if title:
                break
        if not title or not re.search(r'MAYOR|COUNCIL', title.upper()):
            continue
        verbatim = re.sub(r'\s+', ' ', title.replace('\n', ' ')).strip()
        hdr = rows[3]
        ccols = {}
        for j, c in enumerate(hdr):
            if j < 5 or c in (None, ''):
                continue
            s = re.sub(r'\s+', ' ', str(c).replace('\n', ' ')).strip()
            if s in ('Total Votes', 'Precinct'):
                continue
            ccols[j] = norm_name(s)
        R = rec(2025, etype, verbatim, os.path.basename(path))
        for r in rows[4:]:
            c0 = (str(g(r, 0)).strip() if g(r, 0) is not None else '')
            if not PREC.match(c0):
                continue
            for j, name in ccols.items():
                add_vote(R, c0, name, to_int(g(r, j)))
            tc = to_int(g(r, 1)); rg = to_int(g(r, 2))
            if tc is not None:
                R['ballots'][c0] = tc
            if rg is not None:
                R['reg'][c0] = rg


# --------------------------------------------------------------------------- run loaders
load_slice()
parse_2021(os.path.join(SOVC, '2021-11-02-general-election-sovc.xlsx'))
parse_2019(os.path.join(SOVC, '2019-11-05-general-election-sovc.xlsx'))
parse_2025(os.path.join(SOVC, '2025-11-04-general-election-sovc.xlsx'), 'municipal general')
parse_2025(os.path.join(SOVC, '2025-08-12-primary-election-sovc.xlsx'), 'municipal primary')


# --------------------------------------------------------------------------- compute + write
def real_cands(items):
    return [(n, v) for n, v in items
            if not (n.startswith('Write-in') and (v or 0) == 0)]


races, by_cand, by_precinct = [], [], []
for k in sorted(RECORDS, key=lambda x: (x[0], x[1], x[2])):
    R = RECORDS[k]
    year, etype, office = R['year'], R['election_type'], R['office']
    items = sorted(R['cand'].items(), key=lambda kv: (-(kv[1] or 0), kv[0]))
    total = sum(v or 0 for v in R['cand'].values())
    rc = real_cands(items)
    ncand = len(rc)
    nseats = SEATS.get((year, office), 1)
    cutoff = nseats if etype.endswith('general') else 2 * nseats

    winner, wv = items[0] if items else ('', 0)
    # runner-up = seat/advancement boundary (first loser at rank cutoff+1)
    if len(items) > cutoff:
        runner, rv = items[cutoff]
        margin = (items[cutoff - 1][1] or 0) - (rv or 0)
    else:
        runner, rv, margin = '', 0, (wv or 0)

    reg_total = sum(R['reg'].values()) if R['reg'] else ''
    ballots_total = sum(R['ballots'].values()) if R['ballots'] else ''
    turnout = (round(100 * ballots_total / reg_total, 2)
               if (isinstance(ballots_total, int) and isinstance(reg_total, int)
                   and reg_total) else '')

    races.append(dict(
        year=year, election_type=etype, office=office, district=R['district'],
        contest=R['contest'], contest_verbatim=R['verbatim'], n_seats=nseats,
        n_candidates=ncand,
        voting_method=('ranked choice (RCV)'
                       if (year, etype, office) in RCV else 'plurality'),
        total_votes=total,
        total_first_choice_votes='', winner=winner, winner_votes=wv,
        winner_pct=round(100 * (wv or 0) / total, 2) if total else 0,
        runner_up=runner, runner_up_votes=rv, margin_votes=margin,
        margin_pct=round(100 * margin / total, 2) if total else 0,
        registered_voters=reg_total, ballots_cast=ballots_total,
        turnout_pct=turnout,
        uncontested='True' if ncand <= nseats else 'False',
        suppressed_precincts='False',
        note=NOTE.get((year, etype, office), ''), source_file=R['source_file']))

    for rank, (name, v) in enumerate(items, 1):
        by_cand.append(dict(
            year=year, election_type=etype, office=office, district=R['district'],
            contest=R['contest'], candidate=name, votes=v or 0,
            pct=round(100 * (v or 0) / total, 2) if total else 0, rank=rank,
            is_winner='True' if rank <= cutoff else 'False'))

    for prec in sorted(R['per']):
        for name, v in R['per'][prec].items():
            by_precinct.append(dict(
                year=year, election_type=etype, office=office,
                district=R['district'], contest=R['contest'], precinct=prec,
                candidate=name, votes=v, suppressed='False'))


# ------------------------------------------- canceled-uncontested rows (city instrument)
# Appended, then a STABLE re-sort on the same (year, election_type, contest) key the main
# loop used — so a canceled row files immediately after the SOVC-derived rows of its year
# and the rest of the file is byte-identical.
for C in CANCELED:
    races.append(dict(
        year=C['year'], election_type=C['election_type'], office=C['office'],
        district=C['district'], contest=C['contest'],
        contest_verbatim=C['contest_verbatim'], n_seats=C['n_seats'],
        n_candidates=C['n_candidates'],
        voting_method='uncontested (election cancelled)',
        total_votes='', total_first_choice_votes='',
        winner=C['winners'][0], winner_votes='', winner_pct='',
        runner_up='', runner_up_votes='', margin_votes='', margin_pct='',
        registered_voters='', ballots_cast='', turnout_pct='',
        uncontested='True', suppressed_precincts='False',
        note=C['note'], source_file=C['source_file']))
    for name in C['winners']:
        by_cand.append(dict(
            year=C['year'], election_type=C['election_type'], office=C['office'],
            district=C['district'], contest=C['contest'], candidate=norm_name(name),
            votes='', pct='', rank='', is_winner='True'))   # no ballot -> no tally, no rank

_ordkey = lambda r: (r['year'], r['election_type'], r['contest'])
races.sort(key=_ordkey)
by_cand.sort(key=_ordkey)


def writecsv(name, rows, cols):
    with open(os.path.join(OUT, name), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


writecsv('draper_races.csv', races,
         ['year', 'election_type', 'office', 'district', 'contest',
          'contest_verbatim', 'n_seats', 'n_candidates', 'voting_method',
          'total_votes', 'total_first_choice_votes', 'winner', 'winner_votes',
          'winner_pct', 'runner_up', 'runner_up_votes', 'margin_votes',
          'margin_pct', 'registered_voters', 'ballots_cast', 'turnout_pct',
          'uncontested', 'suppressed_precincts', 'note', 'source_file'])
writecsv('draper_results_by_candidate.csv', by_cand,
         ['year', 'election_type', 'office', 'district', 'contest', 'candidate',
          'votes', 'pct', 'rank', 'is_winner'])
writecsv('draper_results_by_precinct.csv', by_precinct,
         ['year', 'election_type', 'office', 'district', 'contest', 'precinct',
          'candidate', 'votes', 'suppressed'])

# --------------------------------------------------------------------------- reconcile + report
mism = 0
for k in RECORDS:
    R = RECORDS[k]
    for cand, tot in R['cand'].items():
        s = sum(R['per'][p].get(cand, 0) for p in R['per'])
        if s != tot:
            mism += 1
            print(f"  !! precinct-sum mismatch {k} {cand}: cand={tot} psum={s}")
gen = [r for r in races if r['election_type'] == 'municipal general']
pri = [r for r in races if r['election_type'] == 'municipal primary']
print(f"races: {len(races)}  (general {len(gen)}, primary {len(pri)})")
print(f"by_candidate rows: {len(by_cand)}   by_precinct rows: {len(by_precinct)}")
print(f"precinct-sum reconciliation mismatches: {mism}")
if REPORT:
    for r in sorted(races, key=lambda x: (x['year'], x['election_type'], x['office'])):
        tag = 'PRI ' if r['election_type'] == 'municipal primary' else 'GEN '
        # 2025 has TWO municipal-general Council contests (the SOVC unexpired-seat race
        # and the canceled 4-year race), so winners are matched on the canceled flag too.
        cx = {(C['year'], C['election_type'], C['office'], C['contest'], norm_name(w))
              for C in CANCELED for w in C['winners']}
        cancelled_row = r['uncontested'] == 'True' and r['total_votes'] == ''
        seatw = [c for c in by_cand
                 if (c['year'], c['election_type'], c['office'], c['contest'])
                 == (r['year'], r['election_type'], r['office'], r['contest'])
                 and c['is_winner'] == 'True'
                 and (((c['year'], c['election_type'], c['office'], c['contest'],
                        c['candidate']) in cx) == cancelled_row)]
        wl = ', '.join(f"{c['candidate']}({c['votes']})" for c in seatw)
        note = f" [{r['note']}]" if r['note'] else ''
        to = f" turnout {r['turnout_pct']}%" if r['turnout_pct'] != '' else ''
        print(f"  {r['year']} {tag}{r['office']:7s} seats={r['n_seats']} "
              f"n={r['n_candidates']} tot={r['total_votes']}{to}{note}\n"
              f"        {'WIN' if tag=='GEN ' else 'ADV'}: {wl}  "
              f"margin={r['margin_votes']} (vs {r['runner_up']} {r['runner_up_votes']})")
