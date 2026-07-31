# washington_county/elections — verification ledger

Built 2026-07-20. Every claim below was verified from document BODIES (headers,
data rows, PDF text), never from file labels. Raw mirror: `raw/` (see
`sources.csv` — 55 rows: 53 mirrored files with sha256, 2 link-only CVR
workbooks; zero unrecorded files on disk).

## 1. Provenance cross-check against the audited St. George layer

13 files (7 CSVs + 6 PDFs) are also held in
`st_george_city_council/election_results/raw/` (downloaded there 2026-06-24 from
the same clerk server and audited for the city build). Every one of the 13
re-downloads (2026-07-20) is **byte-identical** (`cmp`) to the audited mirror —
the county source is stable and our copies match the audited chain.

## 2. Internal reconciliation — precinct sums vs certified COUNTY TOTALS

Every machine-readable canvass file carries a certified `ZZZ / COUNTY TOTALS`
row. `normalize_canvass.py` HARD-FAILS unless, for every candidate column, the
sum of precinct rows equals that row exactly.

Result: **1,030 of 1,032 candidate columns reconcile exactly** across all 15
loaded files (2018–2025). The 2 exceptions are a source-internal contradiction,
kept verbatim (cardinal rule) and allowlisted:

- `2019-general-municipal-export.csv`, contest **Dammeron Valley Fire SSD**
  (single-precinct contest, CODAV): the precinct row prints DENISE STEWART 132 /
  Write-in 122; the file's own COUNTY TOTALS row prints 127 / 121 (MICHAEL L
  THOMAS 184 agrees in both). Both figures are the county's own publication; no
  2019 precinct PDF exists to arbitrate. Non-municipal contest — never reaches
  `election_results_by_contest.csv` or gov.db.

Per-file precinct-name uniqueness also gated (no duplicates in any file).

## 3. Reconciliation vs the audited St. George races (the held city)

`election_results_by_contest.csv` (st_george-tagged rows) vs
`st_george_city_council/election_results/st_george_races.csv` — **all 11 audited
races, 0 mismatches** on winner, winner votes, runner-up (first non-winner under
the multi-winner at-large model), runner-up votes, margin, race total votes, and
candidate count:

| race | seats cut | checks |
|---|---|---|
| 2019 general Council | top 3 | OK |
| 2021 general Council / Mayor | top 2 / 1 | OK / OK |
| 2021 primary Council / Mayor | advance 4 / 2 | OK / OK |
| 2023 general Council | top 3 | OK |
| 2023 primary Council | advance 6 | OK |
| 2025 general Council / Mayor | top 2 / 1 | OK / OK |
| 2025 primary Council / Mayor | advance 4 / 2 | OK / OK |

## 4. Machine-readable ↔ PDF cross-checks (independent-artifact checks)

Where the county published both a CSV/XLSX and a results PDF for the same
election, spot contests were compared value-for-value:

- **2018-11 general**: XLSX vs certified-results PDF — US Senate all 5
  candidates exact (ROMNEY 42,602 / WILSON 11,757 / AALDERS 3,352 / BOWDEN
  1,885 / MCCANDLESS 911).
- **2020-11 general**: export CSV vs SOVC PDF — President county totals exact
  (TRUMP/PENCE 67,294; BIDEN/HARRIS 20,530; JORGENSEN 1,742; Write-in 700; all
  minor candidates match). The SOVC PDF additionally breaks out vote METHODS,
  which the CSV era does not — the long file therefore carries
  `vote_method='Total'` only.
- **2021-08 municipal primary**: CSV vs summary PDF — St George Mayor exact
  (RANDALL 7,869 / HUGHES 4,387 / WOODBURY 2,700 / TOLLY 908).
- **2023-09 primary**: CSV vs summary PDF — REP U.S. House D2 special exact
  (MALOY 13,484 / HOUGH 11,082 / EDWARDS 5,917; PDF Total Votes Cast 30,483 =
  the sum).
- **2024-11 general**: export CSV vs precinct PDF — precinct APV01 President
  row exact (TRUMP 440 / HARRIS 102 / OLIVER 3 / Write-in 2 / Overvotes 1 /
  Undervotes 2 …). The precinct PDF also names individual write-in candidates
  (CSV prints one `Write-in` column). The `…-results-canvas.pdf` for this
  election is a ballot-reconciliation STATISTICS report (99,137 counted / 4,348
  not counted), not a results report.
- **2025-08 municipal primary**: CSV vs summary PDF — St George Mayor exact
  (RANDALL 7,312 / HUGHES 6,597 / MACKEY 3,313 / RAZO 473).
- **2025-11 municipal general**: CSV vs precinct PDF — Ivins 27IVN:01 exact
  (Mayor SMITH 424; Council 116/535/527/115), RV/BC statistics exact (942/675).

No cross-check found a single divergent value.

## 5. Format-era ledger

| era | elections | machine-readable form | notes |
|---|---|---|---|
| 2018-06 | regular primary | **NONE** — 56-page scanned-image PDF only (no text layer) | OCR queued; machine-readable gap |
| 2018-11 | general | XLSX crosstab (E1 layout in a worksheet) | 111 precincts × 71 cols |
| 2019-08 | municipal primary (HELD: Hurricane, Ivins, La Verkin, Santa Clara, **St George**, Washington City — county news post 2019-08-13) | **NONE** — no file on the index; results page was transient; Wayback has NO 2019–2020 capture of the clerk pages | genuine publication gap; recovery lead: city-recorder canvass minutes |
| 2019-11 | municipal general | CSV crosstab **E1** (COUNTY NUMBER, PRECINCT CODE/NAME, RV/BC/BLANK meta) | 91 precincts × 54 cols |
| 2020-03 / 2020-06 | presidential + regular primary | CSV "SOVC" crosstab **P** (per-party RV/BC meta cols) | 114 precincts |
| 2020-11 … 2023-11, 2025-08/11 | generals + municipal cycles | CSV crosstab **E1** | 2021-11 file has a blank COUNTY NUMBER column and jurisdiction-suffixed contest names (kept verbatim) |
| 2022-06 | regular primary | **NONE** — the posted "Jun 2022" files are the **House District 72 RECOUNT only** (ELISON 4,134 / BILLINGS 4,124); no full-primary canvass was ever published | honest gap (the full primary incl. the US Senate REP primary is absent from the county record) |
| 2023-09 | municipal primary | CSV **P** (consolidated with the REP U.S. House D2 special primary — partisan meta cols) | 130 precincts × 64 cols |
| 2024-03 / 2024-06 | DPP + regular primary | CSV **P** | DPP is Democratic-only (Utah GOP held caucuses in 2024) |
| 2024-11 | general | CSV crosstab **E2** — NO registered-voters / ballots-cast meta columns | 136 precincts × 129 cols |
| 2025-11 | municipal general | CSV E1 + LG "standard canvass report" XLSX (statistics template, effectively unfilled) + ballot-level public CVR XLSX (link-only) | 127 precincts × 94 cols |
| 2026-06 | regular primary | **PDF only as of 2026-07-20**: official summary PDF + **REDACTED** precinct PDF + canvass-statistics PDF + public CVR XLSX (link-only), posted on wp-content (not outpost). State portal (Enhanced Voting API) still `isOfficialResults=false` at snapshot | see §7 |

## 6. Oddities verified from bodies (kept verbatim, ledgered)

- **2025-11 "Cancelled" column group** (export CSV only; absent from the
  official summary and precinct PDFs): (a) a FOR/AGAINST measure with real
  votes (1,252 / 2,327) cast **only in the seven Ivins precincts** — an
  Ivins ballot-proposition column group the county labeled "Cancelled";
  (b) eight candidate columns with 0 votes county-wide (cancelled/deemed-elected
  races, Utah Code 20A-1-206 pattern). Retained verbatim in the long file;
  excluded from the derived by-contest layer (no Council/Mayor token). The
  official PDFs' omission of these columns is the county's own presentation
  choice, not ours.
- **Pseudo-candidate columns** ("OVER VOTES", "UNDER VOTES", "WITHDREW",
  "Withdrawn", "Write-in") are part of the published crosstabs → retained in
  `washco_results_long.csv`; the by-contest layer drops over/under/withdrawn
  variants and keeps `Write-in` (a published tally).
- **Zero cells**: the crosstab format prints every precinct row under every
  contest column (zeros outside the contest's jurisdiction). The long file is
  an exact tidy transform (117,920 rows), so `build_elections.py` counts
  `n_precincts` as NONZERO precincts — a documented measurement limit (a
  jurisdiction precinct with genuinely zero in-contest votes would not count).
- **vote_for / seats** is not published in any machine-readable file (the
  summary PDFs carry "Vote For N") → `vote_for`/`seats` left blank, never
  inferred.
- **No suppression exists in the machine-readable era**: zero `*` cells across
  all 15 files → `suppressed=False` throughout. The county's only redacted
  publication is the Jun-2026 precinct PDF (§7).

## 7. Honest gaps (all verified, none fillable from the published record)

1. **2019-08 municipal primary** — held (six cities incl. St George); no
   canvass file published; no Wayback capture. The st_george audited layer has
   the same gap. Recovery leads: GRAMA to the county clerk; city-recorder
   canvass minutes.
2. **2018-06 regular primary** — published only as a 56-page scanned-image PDF;
   not loaded (OCR follow-up queued).
3. **2022-06 regular primary** — only the House-72 recount was ever posted; the
   full primary canvass is absent from the county's record.
4. **2026-06 regular primary** — official county results exist (summary PDF,
   posted ~2026-07-06: REP US House D3 MALOY 17,707 / LYMAN 9,756; REP County
   Commission Seat A ALMQUIST 15,295 / HOSTER 11,761; Seat B BELLISTON 13,838 /
   IVERSON 13,283; contest totals 27,716 each) but the precinct-level report is
   **REDACTED by the county** and no CSV/XLSX export was posted. Suppressed
   cells stay suppressed: the precinct grain is NOT loaded, and the public CVR
   was deliberately NOT used to reconstruct redacted precinct tallies. Re-check
   the index after the county posts an outpost export.
5. **Vote-method grain** — the CSV exports publish per-precinct totals only;
   method breakdowns exist only in some PDF SOVCs (e.g. 2020-11, 2018-11).
   `vote_method='Total'` throughout the long file.
6. **Pre-2018** — the county's previous-results index starts at Jun 2018.
   Older canvasses are not published there (municipal 2017 and earlier absent).

## 8. Loader conformance

`election_results_by_contest.csv` carries exactly the 14 columns
`scripts/build_cities_db.py::load_election_result()` reads (year,
election_type, contest, jurisdiction_slug, office, district, seats, candidate,
party, votes, rank_in_contest, n_precincts, suppressed, source_file), with
int-parseable year/votes/rank_in_contest/n_precincts on every row. No loader
changes are required — the loader already iterates every `level=='county'`
entity and tolerates absent county modules. (The gov.db federation itself is
the central integrator's step, not this module's.)
