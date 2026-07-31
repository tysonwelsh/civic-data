# cache_county / elections — the canonical Cache County canvass

**The county-level canonical source for Cache County elections** (SLCo model:
`salt_lake_county/elections/` is the normative sibling). Holds the Cache County
Clerk canvass once, at the level where it originates. The held city is **logan**;
every other Cache municipality's contests are carried and jurisdiction-tagged
too. Built 2026-07-20; all reconciliation gates PASS (`VERIFICATION.md`).

## Files

- `cache_municipal_results_long.csv` — **canonical municipal canvass**, tidy
  long (2,107 rows; SLCo 13-col schema: precinct × candidate × vote-method).
  Years **2021, 2023, 2025** (primary + general). Sources: Cache County Clerk
  Electionware PDFs (2021–2023) + the Enhanced Voting state portal JSON
  (2025 — the channel the county itself linked as its official results;
  `isOfficialResults:false` ceiling recorded). `precinct='Electionwide'` rows
  are the source's own countywide totals (summary-grain sources and the portal
  summaries) — exclude from precinct counts, prefer for vote totals.
- `cache_county_office_results_long.csv` — even-year county canvass (12,582
  rows): 2020 presidential primary / primary / general, 2022 primary /
  general, 2026 Republican primary — **every contest in each document
  verbatim** (federal/state/county/school/props; party prefixes like
  "REP "/"DEM " are the source's own text). Not loaded into gov.db (the
  `election_result` loader is municipal by design); an analysis layer.
- `election_results_by_contest.csv` — **derived** (`build_elections.py`): one
  row per contest × candidate, municipal council/mayor only, 285 rows / 82
  contests / 18 jurisdictions (`jurisdiction_slug='logan'` = the held city).
  Conforms exactly to `scripts/build_cities_db.py::load_election_result()`
  (14 SLCo columns; insert simulated clean). Loads once `cache_county` is
  registered in `registry/entities.csv` (not this module's task).
- `parse_canvass.py` — raw → the two long files (Electionware PDF normalizer,
  3 precinct-header dialects + wrapped-name repair, + portal JSON). Idempotent.
- `build_elections.py` — municipal long → by_contest. Idempotent.
- `verify_elections.py` — the reconciliation gates; run after any re-parse.
- `sources.csv` — byte-verified catalog (sha256) of all 94 raw files, **all
  years 2006–2026**, incl. catalogued-not-parsed eras and explicit gap rows.
- `raw/` — verbatim originals (36 MB: county PDFs, portal JSON, 2018 HTML).

## The two decisive findings (details in VERIFICATION.md)

1. **RCV:** the county canvass contains NO RCV tabulation ever; the one Cache
   RCV election found (**Nibley 2021**) was town-self-administered and is
   ABSENT from the county canvass (PMN minutes evidence in raw/). North Logan
   never used RCV (held plurality primaries 2021/2023/2025). Every
   `rank_in_contest` here is plurality order; no RCV final exists to misstate.
2. **Logan administration:** Logan self-administered **2019 and 2021** — the
   county published NOTHING for 2019 municipal (any town) and Logan is absent
   from the 2021 county canvass. County-administered from **2023** (certified
   canvass; the recount-episode figures reproduced exactly) and 2025 (state
   portal). ⇒ any future logan re-point covers **2023+ only**; logan's
   2019/2021 city-certified PDFs remain the sole primary source (millcreek-2016
   pattern).

## Ceilings to respect (recording limits, not gaps)

- 2021 general: electionwide grain only, county-labeled UNOFFICIAL (its final
  posting). 2023 primary: contest grain only. 2025: portal
  `isOfficialResults:false`; 55 null precinct-cells kept blank; precinct sums
  undercount summaries by 1–3 votes (unassigned bucket) — totals come from the
  Electionwide rows. 2026: public precinct report withholds 36 of 126
  precincts (suppression preserved). Vote-method split unparsed
  (`vote_method='Total'`; 2022 + 2020-presidential method columns live in
  raw/). Precinct-id dialects verbatim per era, not reconciled.
- Aggregate rows (`Write-In Totals`, `Not Assigned`, bare `Write-in`) are in
  the long files but excluded from by_contest ranking; NAMED write-ins rank
  (`Write-In: David E. Lee` won 2023 Amalga 2yr). `CANDIDATE DISQUALIFIED`
  (2021 Lewiston primary) is the source's own text, kept.

## Honest gaps

2011/2015/2017/2019 municipal: no county publication exists. 2013: per-precinct
files only (catalogued). 2010 general: no documents. 2024 primary + general:
canvass reports are image-only scans — retained, unparsed (OCR/vision queued).
2006–2016 GEMS SOVC era + 2018 HTML pages: mirrored + catalogued, unparsed
(extension candidates). Nibley 2021 RCV results: only in Nibley's own records
(acquisition gap). Cancelled/uncontested races leave no canvass (20A-1-206).

## Refresh

New canvass documents appear under
`cachecounty.gov/assets/department/clerk/elections/results/{year}/` (directory
listing 403 — walk `elections/election-results/`, whose year links 301-redirect
to the PDFs) and on the portal API
`electionresults.utah.gov/results/public/api/elections/cache-county-ut/{election}`
(org slug `cache-county-ut`; `.../ballot-items` then `.../ballot-items/{uuid}`
for precinct breakdowns). Add files to raw/ + sources.csv, extend the lists in
parse_canvass.py, rerun parse → build → verify.
