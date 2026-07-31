# campaign_finance/ — availability & gap log

As-of **2026-07-13**. Additive acquisition-only dataset; no existing dataset modified.

## What exists

- **City website (`herriman.gov/elections`, Lunasoft CMS)** — Herriman self-hosts its
  municipal candidates' campaign-finance filings on the City Recorder's elections page,
  under `/uploads/files/<docid>/<name>.pdf`. The page is **rewritten each cycle**: only the
  current/most-recent cycle (2025) is live.
- **Wayback Machine (`herriman.org/elections.php`)** — the 2021 and 2023 cycles survive
  only in Internet Archive captures of the pre-rename domain (herriman.org 301s to
  herriman.gov; same CMS, same `/uploads/files/` ids — the old ids now 404 on the live
  host, verified 2026-07-13). Every 2021/2023 filing PDF linked from the archived pages
  had its own Wayback capture; **all were recovered — nothing unrecoverable**.

## Coverage — 50 filings across 3 cycles, 16 candidates, no known missing filing

| cycle | filings | candidates (filings each) |
|---|---|---|
| 2021 | 14 | Palmer 3, Smith 3, Esselman 1, Grange 1 (Mayor); Escobar 2, Hodges 2 (D2); Ohrn 2 (D3) |
| 2023 | 12 | Henderson 3, Roberts 3 (D1); Shields 3, Bello 3 (D4) |
| 2025 | 24 | Brady 3, Palmer 3 (Mayor); Hodges 3 (D2); Basham 4, Garcia 4, Grimm 4* (D3); Anderson 3 (D4) |

\* Grimm's 4 index rows are only **2 distinct documents** — the city published each of his
two filings under two URLs (docid 5673 ≡ 5785, 5719 ≡ 5786; byte-identical sha256, see
`duplicate_of` in index.csv). Distinct-document count: **48**.

- **Format split: 17 born-digital `text` / 33 `scanned`** (three of the scanned —
  Henderson's 2023 set — carry an embedded OCR text layer with heavy OCR junk
  ("Ceneral", "Citv"); treated as scanned).
- **Election join:** 46/50 rows match a candidate in
  `../election_results/herriman_results_by_candidate.csv` (`join_confidence=high`).
  The 4 unmatched rows are honest: Esselman + Grange (2021 mayoral primary, see FLAG
  below) never appear in the election dataset, and their two pre-primary filings are the
  proof of the missing contest.

## How verified / method

- All fetches GET-only via `scripts/polite_fetch.py` (browser UA, throttled; Wayback via
  the CDX API → `id_` raw captures — web.archive.org connection-limits aggressively, so
  the archive files were trickled with 20–45 s backoff). sha256 + status for every byte
  logged to `raw/_fetch_log.jsonl`.
- Filenames are `<docid>_<original-basename>.pdf` — Lunasoft docids are globally unique,
  so cross-period basename collisions (e.g. `District-4Terrah-Anderson.pdf` published
  under three different docids) cannot overwrite.
- All 50 PDFs pass `pdfinfo` (2–17 pages); the standard Utah **§10-3-208 "Municipal
  Elections Campaign Finance Report"** form is confirmed in every text-bearing file.
- Report-class due dates were read off the forms themselves (2021: Aug 3 / Oct 26 /
  Dec 2; 2023: Oct 24 / Nov 14 / Dec 21; 2025: Aug 5 / Sep 11 / Oct 7 / Oct 28 / Dec 4)
  and drive the `date` + `reporting_period` columns; `date_precision` says whether the
  date is document-exact (`exact_*`, `from_filename`) or the statutory due date
  (`est_report_class`) or a Wayback upper bound (`est_capture_bound`).

## Checked and NOT a source (honest empties)

- **disclosures.utah.gov** — no Herriman municipal filings; the Municipal section is a
  search app (POST/JS, outside the polite-GET rule) and Utah cities of this size
  self-host. Checked 2026-07-13.
- **Salt Lake County Clerk financial-disclosures page** — posts county offices, local
  school board, and metro-township council filings only; no municipal (Herriman) section.
  Checked 2026-07-13.
- **Below-floor cycles (2019 and earlier):** the 2021-01-20 Wayback capture of
  `herriman.org/elections.php` shows the page already reset ("Check back … for the 2021
  Municipal Elections") — no 2019 filings survive at that URL. Not trivially present;
  deeper recovery would need a different legacy URL and is out of scope.
- **Conflict-of-Interest disclosures + Declarations of Candidacy** (2025 page) and the
  city's 2023 canvass resolution are on the elections page but are **not campaign-finance
  filings** — deliberately excluded from this dataset's index (URLs recoverable from the
  page itself).

## Known limits / gaps

- **Dollar extraction DONE 2026-07-17** (CF-structuring wave) — the structured
  contributions/expenditures/filing_totals/cycle_totals layer exists (`build_finance.py`;
  see `CLAUDE.md`'s dated section). Read `cycle_totals.csv` for any candidate/race total
  (it encodes the incremental/cumulative dedup); never blind-sum `filing_totals`.
  - **VISION-TRANCHE FOLLOW-UP — ✅ RESOLVED 2026-07-19 (Basham ×2 tranche):** the 2
    born-digital 2025 filings whose §10-3-208 section headers did not render in
    `pdftotext -layout` are now **vision-transcribed** (Read-tool, $0 API) into
    `vision/73687d99.json` (5784) + `vision/c96909aa.json` (5802) and built:
    - **Matt Basham 5784** (2025 Pre-Primary, Aug-5) — 5 cash contributions $5,799.00
      (reconciles) + 7 Schedule-C in-kind; 30 expenditures cover $4,850.83. VERBATIM filer
      slip: itemized expenditures sum $4,850.76 vs cover $4,850.83 (a $0.07 page-2 subtotal
      error, incl. refund `($8.59)` + date typo `07/18/2028`) → expenditure side flagged
      `low`/`needs_review`, kept verbatim.
    - **Matt Basham 5802** (2025 Pre-General) — Schedule A empty (0 cash); 3 expenditures
      $1,693.78 (reconciles) + 2 in-kind ($2,500 SL Board of Realtors / $60 Sam Winkler).
    **Matt Basham 2025 `cycle_totals` is no longer a lower bound:** raised **$7,824.00** /
    spent **$7,748.34** (documented `cycle_overrides.csv` row — the Nov-7 Final 5880 is a
    distinct $9.03 period the `max(summary, sum-interims)` dedup would otherwise drop, same
    defect class as Hodges/Palmer/Smith).
  - **Lorin Palmer 5768** (2025 Oct-7 Mayor) — as published the PDF has only Schedule A pages
    (no Schedule B / no signed cover). Contributions ($406.02) are captured; its
    **expenditures are unrecovered**, so **Lorin Palmer 2025's cycle `spent` is a LOWER
    BOUND** (documented in `cycle_overrides.csv`).
  - **Two MIXED cycle review-flags for human adjudication** (`cycle_totals.csv`): **Clint
    Smith 2021** and **Lorin Palmer 2021** (Mayor). Their per-cycle reports carry per-period
    donor rosters but a repeated candidate self-loan (and, for Palmer, one repeat donor),
    so an incremental sum cannot be confidently distinguished from a cumulative restatement —
    left computed (`sum-interim`) + flagged, NOT overridden. An adjudicator should read the
    three filings and set `cycle_overrides.csv` if per-period.
  - **Grimm 2025 $0-vs-$2,525 contradiction** (5786 Summary "-0-" over a $2,525 Schedule A)
    preserved verbatim + flagged `needs_review` — adjudication is the owner's, no override.
- **2021 eliminated-primary candidates (Esselman, Grange):** their statutory
  30-days-after-primary final reports (due 2021-09-09) were **never published** — the
  city page dropped both candidates after the primary. Their only recovered filing each
  is the Aug 3 pre-primary report. City-publishing gap, not a fetch miss.
- **Bello 2023 first report is an "Amended-Financial-Disclosure"** — the original
  (pre-amendment) first report was never on any capture.
- **Palmer 2025 October-7 report (docid 5768)** as published contains only Schedule A/B
  pages — no signed cover form. Recorded verbatim.
- Scanned filings' `date` values are mostly statutory due dates (`est_report_class`) —
  refine from the documents when the OCR/vision pass happens.

## ⚠ FLAGGED discrepancies for the elections dataset (do NOT edit election_results/ from here)

1. **A 2021 Herriman municipal PRIMARY existed and is absent from
   `election_results/`** (and from the county SOVC dataset). Proof: the 2021-08-11
   Wayback capture of `herriman.org/elections.php` lists **four mayoral candidates**
   — Jared Esselman, Nicole Grange, Lorin Palmer, Clint Smith — each with a "Primary
   Financial Report" (all four PDFs recovered here), plus a posted **Sample Primary
   Election Ballot** (`/uploads/files/2074/…Sample-Ballot2021-Primary2Page1.png`).
   The repo's `herriman_races.csv` has no 2021 primary rows and the recon table
   lists 2021 general only. Esselman and Grange (both eliminated 2021-08-10) appear
   nowhere in the election data. → An elections review should re-check the 2021 SLCo
   primary SOVC for a Herriman mayoral contest.
2. No other contest-level discrepancies: the filings imply no 2023 primary (consistent —
   two candidates per seat) and a 2025 D3-only primary (already in `herriman_races.csv`).
