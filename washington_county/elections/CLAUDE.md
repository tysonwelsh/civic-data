# washington_county / elections — the canonical Washington County canvass

**This is the county-level canonical source for Washington County (UT, FIPS 49053)
election results** — the marquee module of this county's build. The county
administers **St. George's** municipal elections (the one held city in this
county); the audited `st_george_city_council/election_results/` layer derives
from the *same* clerk files held here (13 shared files verified byte-identical;
the planned re-point of the city pipeline to this canonical is a separately
queued, byte-identity-gated package — NOT yet executed).

## Files

- `washco_results_long.csv` — **canonical.** Washington County Clerk precinct
  crosstabs in tidy long form: one row per precinct × candidate-column per
  election, **117,920 rows, 15 elections, 2018–2025** (municipal odd years
  2019/2021/2023/2025 primary+general complete; even-year generals 2018–2024;
  primaries 2020-03/06, 2023-09 consolidated, 2024-03 DPP, 2024-06). Columns
  mirror the SLCo long schema (`year,election_type,source_file,sheet,contest,
  vote_for,precinct,candidate,votes,suppressed,vote_method,times_cast,
  registered_voters`). Contest/candidate/precinct strings VERBATIM, including
  pseudo-candidate columns (OVER/UNDER VOTES, WITHDREW, Write-in) and the
  2025 "Cancelled" column group. `vote_method='Total'` throughout (the CSV era
  publishes no method grain). Zero cells are real: the crosstab prints every
  precinct under every contest — do not read row-presence as
  jurisdiction-membership. Regenerate: `python3 normalize_canvass.py`
  (hard-fails unless every candidate column sums to the file's own certified
  ZZZ COUNTY TOTALS row; 2 allowlisted source-internal discrepancies — see
  VERIFICATION.md §2).
- `election_results_by_contest.csv` — **derived** (`build_elections.py`). One
  row per contest × candidate, **municipal council/mayor contests only** (the
  SLCo contract): 435 rows, 110 contests, 7 municipal elections 2019–2025.
  `jurisdiction_slug='st_george'` on the held city's 63 rows; every other
  Washington County municipality (Washington City, Hurricane, Ivins, Santa
  Clara, La Verkin, Toquerville, Leeds, Springdale, Rockville, Virgin, Apple
  Valley, Hildale, Enterprise) is included with the schema's documented
  `jurisdiction_slug=''` ("other") — the contest string names the city.
  Loads into gov.db `election_result` via the already-generalized
  `load_election_result()` (no loader changes needed). `n_precincts` counts
  NONZERO precincts (crosstab measurement limit, documented). County/state/
  federal contests are NOT in this file — query the long file for them.
- `normalize_canvass.py` / `build_elections.py` — the pipeline; idempotent;
  outputs DERIVED, never hand-edit.
- `sources.csv` — the complete byte-verified source catalog (55 rows: 53
  mirrored with sha256 + 2 link-only ballot-level CVR workbooks; zero
  unrecorded files).
- `VERIFICATION.md` — reconciliation results, format-era ledger, honest gaps.
- `raw/<year>/<month>/…` — verbatim mirror of every published clerk file
  (CSVs, XLSX, and ALL results PDFs — unlike SLCo, the raw set is small enough
  to mirror in-repo), plus 2026 state-portal JSON snapshots.

## Provenance

**Washington County Clerk** — index:
<https://www.washco.utah.gov/departments/clerk/elections/previous-election-results/>,
files on `outpost.washco.utah.gov/apps/clerk/elections/<year>/<month>/…`
(Jun-2026 files on `washco.utah.gov/wp-content/uploads/2026/07/`). State portal
backstop: `electionresults.utah.gov/results/public/washington-county-ut`
(Enhanced Voting JSON API under `/results/public/api/elections/…`) — 2026
snapshots archived, UNOFFICIAL at capture, not loaded. Refresh: re-fetch the
index, mirror new files into `raw/`, append to `sources.csv`, extend
`normalize_canvass.py::FILES`, rerun both scripts.

## Ceilings + gaps (details in VERIFICATION.md)

- **Verbatim ceiling**: results are precinct totals only (no vote-method grain
  in the CSVs); `vote_for`/seats unpublished in machine-readable form; the
  2021-11 file's contest names carry jurisdiction suffixes (kept verbatim).
- **Honest gaps**: 2019-08 municipal primary (held — incl. St George — but
  never published as a file; no Wayback capture); 2018-06 primary
  (scanned-image PDF only, OCR queued); 2022-06 primary (only the House-72
  RECOUNT was ever posted); 2026-06 primary (official summary PDF only —
  precinct report REDACTED by the county, suppressed stays suppressed; the
  public CVR is deliberately NOT used to reconstruct redacted tallies);
  pre-2018 (index floor).
- **Multi-winner at-large**: every municipality here elects at-large;
  `rank_in_contest` is plurality order within a top-N field — the "runner-up"
  of a race is the first candidate BELOW the seat cut, not rank 2 (the audited
  `st_george_races.csv` model; reconciled 11/11 races exact).
- No RCV anywhere in this county's published record.

## Which artifact for which question

- St George winners/margins (authoritative): the audited
  `st_george_city_council/election_results/st_george_races.csv`
  (gov.db `election_race`).
- Any Washington County municipal tally, any municipality, precinct grain:
  `washco_results_long.csv` (or `election_result` once federated).
- County commission / state / federal contests, 2018–2025, precinct grain:
  `washco_results_long.csv` (NOT in the by-contest file by design).
- What the county published for an election + integrity status: `sources.csv`
  + `VERIFICATION.md`.
