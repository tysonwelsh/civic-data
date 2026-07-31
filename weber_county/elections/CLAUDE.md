# weber_county / elections — the canonical Weber County canvass

**This is the county-level canonical source for Weber County elections** (the
sibling of `salt_lake_county/elections/`). Ogden — the repo-held Weber city —
draws from this same county-clerk canvass; the queued Ogden re-point package is
byte-identity-gated and separate (do NOT touch
`ogden_city_council/election_results/` from here).

## Files

- `weber_results_long.csv` — **canonical.** Tidy long form, same 13 columns as
  the SLCo long file (`year, election_type, source_file, sheet, contest,
  vote_for, precinct, candidate, votes, suppressed, vote_method, times_cast,
  registered_voters`). 11,416 rows, 2006–2026: every published odd-year
  municipal canvass 2007–2025 (ALL contests, districts included) + county-office
  contests and countywide measures from the even-year cycles. Two grains
  coexist honestly, per source: precinct rows (`precinct` set) and official
  contest-grain summary rows (`precinct=''`). `vote_method` is always `Total`
  (Weber publishes no by-method split in the covered reports).
  **Suppressed cells stay suppressed**: `suppressed=True, votes=''` (451 cells;
  <15-voter precincts). Never hand-edit.
- `election_results_by_contest.csv` — **derived** (`build_elections.py`). One
  row per contest × candidate, 1,080 rows / 327 contests; loads into gov.db
  `election_result`. **Official-summary primacy**: candidate votes come from
  the county's certified contest-grain summary wherever one exists (precinct
  sums undercount by exactly the suppressed cells — proven in
  VERIFICATION.md); `n_precincts` comes from the precinct grain.
  `jurisdiction_slug='ogden'` tags the held city; other municipalities carry
  `''` with the city name in `contest`. For the two same-named Roy 2025
  primaries, `seats` (1 vs 2) disambiguates.
- `normalize_weber.py` — raw → long. Five parser families (see the era ledger
  in VERIFICATION.md) + `certified_totals_transcribed.csv` (OCR+vision-verified
  totals from the two image-only signed canvass certifications).
- `verify_elections.py` — the reconciliation harness (internal totals,
  cross-source, certified-summary checks). Run after any rebuild; exits
  nonzero on unexplained mismatch.
- `sources.csv` — every result file discovered on the county's sites (87 rows:
  81 Wix files + 6 EV portal elections), byte-verified with sha256, both site
  labels, body-verified identity, role (normalized / crosscheck / catalogued /
  dead-link), and label-vs-body mismatch notes. Zero unrecorded files.
- `raw/` — all Wix originals RETAINED verbatim (~71 MB; the hash URLs are
  fragile and no external mirror exists) + `download_log.csv`.
- `ev_api/` — Enhanced Voting portal JSON harvest (6 elections, 2024–2026).
- `ocr/*.txt` — tesseract sidecars for the two image-only certifications
  (renders regenerable: pymupdf 300 dpi → tesseract --psm 6).
- `reconciliation.csv` — per-check ledger emitted by the normalizer.

## Provenance

- **Weber County Elections Office** (county clerk):
  <https://www.weberelections.gov/electionsresults> +
  `/copy-of-historical-election-results` (Wix; opaque hash-named files —
  identity always verified from the body, several site labels are wrong; see
  sources.csv notes).
- **Enhanced Voting portal**:
  `https://electionresults.utah.gov/results/public/weber-county-ut/elections/…`
  (JSON API under `/results/public/api/elections/weber-county-ut/<slug>/…`) —
  machine-readable channel 2024+; the ONLY published channel for the 2025
  municipal primary outside Ogden Valley City.

## The sharp edges (read before analyzing)

1. **Precinct sums ≠ certified totals** where suppression exists — always take
   contest totals from the summary rows / the derived by-contest file, and
   precinct detail from the precinct rows.
2. **2023 municipal general is a county-publication gap** (bond-only canvass;
   "visit the municipality's website"). Ogden's audited city CSV covers Ogden.
3. Missing county publications: 2009 (entire cycle), 2013 primary, 2019
   primary. No precinct grain before 2018 / for 2019g / 2021.
4. Split precincts carry colon codes (`29OV03:X`) in 2025-era files; the 2025
   OVC primary PDF truncates one candidate name (EV canonical there).
5. Contest names are verbatim per source and vary across eras ("Ogden
   Municipal Ward 4" ≈ "OGDEN CITY COUNCIL - DISTRICT 4" era forms); the
   long file never harmonizes them — `build_elections.py` parses
   office/district at derive time. Electionware's doubled LONG+short titles
   are reduced to the LONG title only when the tail is a pure echo
   (`dedup_contest`); genuinely distinct tails (Roy "2 YR") stay verbatim.
6. Even-year files are normalized for COUNTY contests only (commission, row
   offices, countywide measures). Federal/state/school/judicial contests
   remain in the retained raw files (catalogued in sources.csv).

## Verification

`VERIFICATION.md` — era/format ledger, per-contest reconciliation (1,274
internal + 290 summary + cross-source checks, 0 unexplained), suppression
model, the 2018 CSV vintage delta, honest gaps, and the external check: 12/12
matchable audited Ogden winners agree with identical vote counts.
