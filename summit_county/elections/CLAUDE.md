# summit_county / elections — the canonical Summit County canvass

**County-level canonical source for Summit County elections, 2006–2026** —
built 2026-07-20 from the Summit County Clerk's self-hosted DocumentCenter
archive (<https://www.summitcountyutah.gov/288/Election-Results-Archives>).
The county repo module exists ahead of the rest of `summit_county/` (elections
was the funded first module); the entity IS registered in `registry/entities.csv` (fed_index 105; this line corrected 2026-07-25 — it predated registration)
— when it is registered, `scripts/build_cities_db.py`'s `load_election_result`
picks up `election_results_by_contest.csv` unchanged.

## Files

- `summit_results_long.csv` — **canonical precinct-grain long** (109,201 rows;
  29 elections 2006–2026). SLCo-schema: `year, election_type, source_file,
  sheet, contest, vote_for, precinct, candidate, votes, suppressed,
  vote_method, times_cast, registered_voters`. GEMS-era rows (2006–2016)
  carry real vote methods (Polling/Absentee/Early/…); 2018+ rows are
  `vote_method='Total'`. **Suppressed cells (2024+) carry `votes=''`,
  `suppressed=True` — never imputed.** Never hand-edit; rerun the build.
- `election_results_by_contest.csv` — **derived certified layer** (343 rows,
  115 contests): municipal council/mayor contests for the six Summit
  municipalities (`park_city`, `coalville`, `kamas`, `oakley`, `francis`,
  `henefer`) + Summit County offices (`jurisdiction_slug='summit_county'`:
  County Council seats, Commission (2006), Assessor/Attorney/Auditor/Clerk/
  Recorder/Sheriff/Treasurer). Loader-shape for gov.db `election_result`.
  **Votes are the CERTIFIED summary-layer values, NOT precinct sums** (Summit
  suppresses low-turnout precincts 2024+ — see DESIGN NOTE in
  `build_elections.py`); `n_precincts`/`suppressed` are measured from the
  precinct layer. State/federal/school/special-district/judicial/proposition
  contests are excluded here but fully present in the long file.
- `build_elections.py` — raw PDFs → both CSVs + printed verification gates.
- `canvass_parsers.py` — the four report-format parsers (GEMS SOVC, GEMS
  summary, Electionware per-precinct, table/crosstab) — all verification-first.
- `sources.csv` — **every raw file byte-verified** (md5) to its DocumentCenter
  URL; 81 rows, zero unrecorded. Includes the 2006-primary MISLINK record.
- `VERIFICATION.md` — the reconciliation report, suppression ledger, vision
  spot-checks, Park City verdict, and the honest-gap register. **Read before
  quoting anything unusual.**
- `raw/` — verbatim canvass PDFs (71 files, ~80 MB, 2004–2026: summary +
  precinct reports, certified canvass packets, the 2026 CVR xlsx, the archive
  index page) + `ev_*.json` (Utah Enhanced Voting API snapshots 2023–2026,
  cross-check channel only).

## The Park City relationship (verified 2026-07-20)

Park City self-administers its municipal elections (its own Board of
Canvassers certifies) but the county tabulates under contract — and the
county canvass **contains Park City's contests at precinct grain** (11 PC
precincts), 2011–2025. Cross-checked against the audited
`park_city_city_council/election_results/` layer: **49/50 candidate rows
2019–2025 match exactly** (the 50th is a `Withdrawn` 0-vote ballot line the
city layer omits). The per-city re-point to this canonical is queued
separately (byte-identity-gated; do NOT touch the city layer from here).

## Quirks (details in VERIFICATION.md)

- **No RCV in any Summit contest** (Park City block plurality throughout).
- Three format eras: GEMS SOVC/summary (2006–2016), Electionware per-precinct
  (2018–2021), rotated precinct tables (2021–2026).
- 2011 municipal general: precinct groups are UNNAMED in the SOVC → contest
  grain only. 2014 general SOVC excludes paper ballots by design → long rows
  partial-methods, certified totals from the summary. 2015 HENEFER is an
  all-zero write-in contest in the SOVC (excluded, documented).
- Duplicate GEMS write-in columns are disambiguated `WRITE IN (column 2)`.
- Honest gaps: 2004 (scan), 2006 primary (county mis-link serves the 2010
  file), 2019 primary (dead links), 2022 primary (all docs scanned; OCR
  queued), 2024 June regular primary (unpublished on every county channel),
  2005–2017 odd years except 2011/2015 (municipal self-administration era).
- Candidate names verbatim as printed (GEMS summaries attach the party token:
  `GRANATO, SAM F. DEM`; tables print `REP TRUMP/VANCE`; the `party` column
  in by-contest extracts these).

## Refresh

New election → download the new Summary + Precinct reports into `raw/`,
append to `ELECTIONS` in `build_elections.py`, add `sources.csv` rows (md5),
rerun `python3 build_elections.py` (gates must PASS), update VERIFICATION.md.
