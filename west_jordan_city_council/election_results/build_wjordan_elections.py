#!/usr/bin/env python3
"""Build West Jordan City (Salt Lake County, UT) election_results from the COUNTY
CANONICAL SOVC. Cycles: 2019, 2021, 2023, 2025 municipal general; WJD council + mayor.

RE-POINTED 2026-07-19 (root TODO.md Phase-2 follow-up): this build previously parsed a
redundant per-city copy of the Salt Lake County SOVC .xlsx exports under raw/. It now
derives DIRECTLY from the single county canonical held at
  salt_lake_county/elections/slco_municipal_results_long.csv  (precinct x candidate x method)
  salt_lake_county/elections/election_results_by_contest.csv   (contest -> office/district/seats)
The per-city raw SOVC copies were retired after verifying this build reproduces all three
CSVs BYTE-IDENTICALLY. Possible now because the county canonical's 2026-07-19 suppression-
recovery repaired the dropped un-suppressed per-precinct 2021 totals that originally forced
this city to parse raw. Reproducible: python3 build_wjordan_elections.py

Vote-for-N at-large (2021/2025, 3 seats): winner = lowest winning seat (rank n_seats),
runner_up = first loser (rank n_seats+1), margin = the seat-deciding boundary; is_winner
for rank<=n_seats. 2019's At-Large was single-seat. Mayor + districts are single-winner.
"""
# ---------------------------------------------------------------------------
# County-canonical reader (re-pointed 2026-07-19). The Salt Lake County Clerk
# SOVC now lives ONCE, canonical, at salt_lake_county/elections/. This build
# derives DIRECTLY from it -- no per-city raw SOVC copy. Proven byte-identical
# to the prior audited CSVs (which parsed a redundant local raw/*.xlsx copy).
# ---------------------------------------------------------------------------
import os, re, csv, collections

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
LONG = os.path.join(REPO, 'salt_lake_county', 'elections', 'slco_municipal_results_long.csv')
BYC  = os.path.join(REPO, 'salt_lake_county', 'elections', 'election_results_by_contest.csv')
OUT  = HERE

_LONG = None
def _long():
    global _LONG
    if _LONG is None:
        with open(LONG, newline='') as f:
            _LONG = list(csv.DictReader(f))
    return _LONG

def city_contests(slug):
    """{(year, contest_label): {office,district,seats}} for this jurisdiction's
    municipal-general council/mayor contests, from the derived by-contest file."""
    out = collections.OrderedDict()
    with open(BYC, newline='') as f:
        for r in csv.DictReader(f):
            if r['jurisdiction_slug'] != slug: continue
            if r['election_type'] != 'municipal general': continue
            k = (r['year'], r['contest'])
            if k not in out:
                out[k] = dict(office=r['office'], district=r['district'], seats=r['seats'])
    return out

def contest_precincts(year, contest, prec_re, norm):
    """per[prec][norm_cand] = per-precinct total (int) or None; global candidate
    first-appearance order. Per-precinct total rule: for each (precinct,candidate),
    use the 'Total' vote_method row where present (the 2021 family-C recovery emits
    a Total row only where every method split was privacy-suppressed); otherwise sum
    the non-'Total' method rows (2019/2025 single 'ALL'; 2023 In-Person+Vote by Mail).
    'Cumulative' and other non-precinct rollup rows are excluded by prec_re."""
    rows = [r for r in _long()
            if r['year']==year and r['election_type']=='municipal general'
            and r['contest']==contest and prec_re.fullmatch(r['precinct'].strip())]
    prec_order, cand_order = [], []
    data = collections.defaultdict(list)
    for r in rows:
        prec = r['precinct'].strip(); cand = norm(r['candidate'])
        if prec not in prec_order: prec_order.append(prec)
        if cand not in cand_order: cand_order.append(cand)
        v = r['votes'].strip(); supp = r['suppressed'].strip().lower()=='true'
        val = None if (supp or v in ('','nan')) else int(float(v))
        data[(prec,cand)].append((r['vote_method'], val))
    per = collections.OrderedDict()
    for prec in prec_order:
        per[prec] = collections.OrderedDict()
        for cand in cand_order:
            if (prec,cand) not in data: continue
            lst = data[(prec,cand)]
            totals = [val for m,val in lst if m=='Total']
            if totals:
                real = [v for v in totals if v is not None]
                per[prec][cand] = real[0] if real else None
            else:
                nont = [val for m,val in lst if m!='Total' and val is not None]
                per[prec][cand] = sum(nont) if nont else None
    grand = collections.OrderedDict()
    for c in cand_order:
        grand[c] = sum((per[p][c] or 0) for p in per if c in per[p])
    return grand, per, cand_order
SLUG = 'west_jordan'
PREC = re.compile(r'WJD\d+')
YEARS = {'2019','2021','2023','2025'}

def norm_name(s):
    s = str(s).replace('\n', ' ').strip()
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'\s*\(NP\s*\)', '', s, flags=re.I)
    s = re.sub(r'\s*Qualified Write In\s*', ' (Write-in)', s, flags=re.I).strip()
    s = s.replace('Unresolved Write-In', 'Write-in (unresolved)')
    s = re.sub(r'WRITE-IN', 'Write-in', s, flags=re.I)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def canon(office, district):
    if office == 'Mayor':
        return ('Mayor', '', 'West Jordan City Mayor')
    if district == 'At-Large':
        return ('Council', 'At-Large', 'West Jordan City Council At-Large')
    return ('Council', district, f'West Jordan City Council District {district}')

def orank(office, district):
    if office=='Mayor': return 0
    if district=='At-Large': return 1
    return 2+(int(district) if str(district).isdigit() else 99)

contests = city_contests(SLUG)
jobs = []
for (year, label), meta in contests.items():
    if year not in YEARS: continue
    ns = int(meta['seats']) if meta['seats'] not in ('',) else 1
    jobs.append((year, label, meta['office'], meta['district'], ns))
jobs.sort(key=lambda j: (int(j[0]), orank(j[2], j[3])))

RACES_COLS = ['year','election_type','office','district','contest','contest_verbatim',
    'n_seats','n_candidates','voting_method','total_votes','total_first_choice_votes',
    'winner','winner_votes','winner_pct','runner_up','runner_up_votes','margin_votes',
    'margin_pct','registered_voters','ballots_cast','turnout_pct','uncontested',
    'suppressed_precincts','note','source_file']

races, by_cand, by_precinct = [], [], []
for year, label, office, district, n_seats in jobs:
    office_c, district_c, contest = canon(office, district)
    grand, per, cands = contest_precincts(year, label, PREC, norm_name)
    items = sorted(grand.items(), key=lambda kv: (-(kv[1] or 0), kv[0]))
    total_votes = sum(v or 0 for v in grand.values())
    real = [(n, v) for n, v in items
            if not (n.startswith('Write-in') and (v or 0) == 0)]
    n_candidates = len(real)
    winner, winner_votes = items[0]
    if n_seats == 1:
        runner_up, runner_up_votes = (items[1] if len(items) > 1 else ('', 0))
    else:
        winner, winner_votes = items[n_seats - 1]
        runner_up, runner_up_votes = (items[n_seats] if len(items) > n_seats else ('', 0))
    wp = round(100 * winner_votes / total_votes, 2) if total_votes else 0
    margin_votes = winner_votes - (runner_up_votes or 0)
    margin_pct = round(100 * margin_votes / total_votes, 2) if total_votes else 0
    row = {c:'' for c in RACES_COLS}
    row.update({'year': year, 'election_type': 'municipal general', 'office': office_c,
        'district': district_c, 'contest': contest, 'n_seats': n_seats,
        'n_candidates': n_candidates, 'total_votes': total_votes,
        'winner': winner, 'winner_votes': winner_votes, 'winner_pct': wp,
        'runner_up': runner_up, 'runner_up_votes': runner_up_votes,
        'margin_votes': margin_votes, 'margin_pct': margin_pct})
    races.append(row)
    for rank, (name, votes) in enumerate(items, start=1):
        v = votes or 0
        by_cand.append({'year': year, 'election_type': 'municipal general', 'office': office_c,
            'district': district_c, 'contest': contest, 'candidate': name,
            'votes': v, 'pct': round(100 * v / total_votes, 2) if total_votes else 0,
            'rank': rank, 'is_winner': 'True' if rank <= n_seats else 'False'})
    for prec in sorted(per):
        for name, v in per[prec].items():
            by_precinct.append({'year': year, 'election_type': 'municipal general',
                'office': office_c, 'district': district_c, 'contest': contest,
                'precinct': prec, 'candidate': name, 'votes': '' if v is None else v,
                'suppressed': 'True' if v is None else 'False'})

def writecsv(path, rows, cols):
    with open(path, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader()
        for r in rows: w.writerow(r)

writecsv(os.path.join(OUT,'west_jordan_races.csv'), races, RACES_COLS)
writecsv(os.path.join(OUT,'west_jordan_results_by_candidate.csv'), by_cand,
    ['year','election_type','office','district','contest','candidate','votes','pct','rank','is_winner'])
writecsv(os.path.join(OUT,'west_jordan_results_by_precinct.csv'), by_precinct,
    ['year','election_type','office','district','contest','precinct','candidate','votes','suppressed'])
print('races',len(races),'by_cand',len(by_cand),'by_prec',len(by_precinct))
