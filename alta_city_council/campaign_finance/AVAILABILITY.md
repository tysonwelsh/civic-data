# Town of Alta — Campaign-Finance Disclosures: Availability

**As-of:** 2026-07-13 · **Layer:** ACQUISITION-ONLY (raw filings retained; no OCR/vision
extraction, no dollar totals computed — those are deferred). **Cycles in scope:** 2021
(Mayor + Council At-Large), 2023 (Council At-Large), 2025 (Mayor + Council At-Large).

Town of Alta is a **~380-person town** whose elections are **administered by the Salt Lake
County Clerk**. Utah exempts small-town candidates who raise/spend below a threshold from
detailed reporting (older $25-aggregation form; 2025 form uses a **$500** itemization floor).
**An honest near-nil result was expected here — and is largely what the record shows.** Every
Alta candidate who appeared on a ballot in an in-scope cycle nonetheless filed *a* campaign
financial report, and the town/state published them, so coverage is in fact **COMPLETE per the
ballot roster** (see the table below).

## What was checked (search order)

1. **Town recorder / elections pages (Juniper CMS + GCS bucket).** `townofalta.utah.gov`'s
   `/meetings/` app is JS-only, but the town DOES publish campaign finance at two static pages
   whose PDFs live in the Google Cloud Storage bucket
   `storage.googleapis.com/juniper-media-library/130/<YYYY>/<MM>/…` (Alta = tenant `130`):
   - `/elections-voting/` — the **2025** declared-candidate roster with each 2025 candidate's
     declaration + conflict-of-interest + **campaign-finance report series** (this is where the
     2025 money reports live; the county/state site only links back here for 2025).
   - `/conflict-of-interest-financial-disclosures/` — annual **conflict-of-interest** ethics
     statements for sitting officials (a *different* statutory instrument — NOT campaign
     finance) **plus** the **2023 town-side interim "Financial Declarations"** (period slices).
   The GCS bucket is publicly **listable** via the S3-style XML endpoint
   (`https://storage.googleapis.com/juniper-media-library?prefix=130/<YYYY>/<MM>/`), which is
   how the exact object keys here were enumerated (the HTML pages render links client-side).
2. **State `disclosures.utah.gov/Municipal` → `municipal.utah.gov` file host — PRIMARY for
   2021 & 2023.** The GET-navigable folder tree (`/Municipal/salt lake_<year>` → per-city
   subfolders) holds:
   - **`salt lake_2021_Town of Alta`** — 5 PDFs (Anctil, Byrne, M. Bourke, R. Bourke/Mayor, +
     an "All campaign financial disclosures" combined bundle).
   - **`salt lake_2023_Alta`** — 3 PDFs (Morgan, Schilling, Davis year-end summaries).
   - **`salt lake_2025_*`** — the 2025 entry only **links back to the town's own pages**
     (`townofalta.utah.gov`); the state hosts no 2025 Alta PDFs. (Directory *listing* on
     `municipal.utah.gov` is 403; individual files resolve fine — enumerated via the
     disclosures.utah.gov index.)
3. **Salt Lake County Clerk financial-disclosures page** — posts county/state offices + an
   EasyVote portal for county races; **municipal candidate filings are delegated to the state
   `disclosures.utah.gov/Municipal` tree**, not hosted by the county for Alta. Not a distinct
   source.
4. **Wayback Machine** — not needed; the live state + town hosts served every filing.

## Coverage vs the election roster (`election_results/alta_races.csv`)

| Cycle | Ballot candidates (office) | Finance filings held | Status |
|---|---|---|---|
| **2021** | Byrne, Anctil, **M. Bourke** (Council); **R. Bourke** (Mayor, unopposed) | 1 report each + 1 combined bundle (state) | **COMPLETE** |
| **2023** | Morgan, Schilling (won), **Davis** (Council) | 1 state year-end summary **+ 3 town interims + 1 town declaration** each | **COMPLETE (over-covered)** |
| **2025** | Bourke (Mayor); Anctil, Heimark (Council) — **plus withdrawn Byrne & Moxley** | 3 money reports each for the 3 winners; 1 final each for the 2 withdrawers; + 5 declarations | **COMPLETE, but NOT in `election_results` — see FLAG 1** |

## Threshold-exemption / dollar reality (per-cycle)

- **2021 — nil except Byrne.** Anctil, Roger Bourke (Mayor), and Margaret Bourke each filed the
  **$25-aggregation "Campaign Financial Report" with all lines $0** (at/under threshold).
  **John J. Byrne III** is the one substantive 2021 filer: **$5,000.00 contributions, $239.89
  expenses, $4,760.11 ending balance.**
- **2023 — nil / de minimis.** Morgan and Davis filed **all-$0** year-end summaries; **Schilling**
  reported **$0 contributions, $69.96 expenditures** (−$69.96 balance). All under threshold.
- **2025 — the substantive cycle.** Real money appears: **Roger Bourke (Mayor)** reported an
  itemized **$2,000 contribution from "Abundance Political Consulting" (9/1/25)** (above the
  $500 itemization floor); **John Byrne (Mayor, withdrew)** **received $4,725.11 (6/2/25) and
  returned all $4,725.11 (11/19/25)** as an unused-contribution refund (net $0). Anctil, Heimark,
  and Moxley filings read at/near nil in the summary lines (itemized Form A/B are on scanned
  second sheets — dollar extraction deferred to a later OCR/vision pass).
- Exact per-candidate/per-cycle totals are **not computed in this acquisition layer**; because
  candidates file multiple reports per cycle (interims + a final/summary), any dollar total MUST
  be produced with the repo dedup (`scripts/campaign_finance/cycle_totals.py`), never by summing
  rows here (SKILL §6 double-count trap). See "Double-count / dedup" below.

## Discrepancy FLAGS (recorded here only — do NOT edit `election_results/`)

1. **The entire 2025 general is absent from `election_results/alta_races.csv`, yet a COMPLETE
   2025 campaign-finance set exists.** `alta_races.csv` tops out at 2023 (the SLCo SOVC hasn't
   posted Alta 2025 — a known county-file lag, tracked in repo-root `TODO.md` and
   `election_results/CLAUDE.md`). This finance dataset independently establishes the **2025
   ballot roster**: **Mayor — Roger Bourke (elected)**, John Byrne (withdrew); **Council (2
   seats) — Carolyn Anctil & Craig Heimark (elected)**, Paul T. Moxley (withdrew). This
   corroborates and *extends* the repo's existing note (which knew only "Heimark won a seat"):
   Bourke was re-elected Mayor and **Anctil returned to the Council** in 2025. All 16 rows carry
   `join_confidence=none` because there is no 2025 election row to match against — NOT a data
   defect. **Left for the elections layer to reconcile when the county posts 2025.**
2. **Two withdrawn 2025 candidates filed finance reports** (Byrne — Mayor; Moxley — Council).
   Their declarations + a final financial report are retained (`filing_type=declaration_of_candidacy`
   / `summary`), documenting that they ran and withdrew. Byrne's is notable ($4,725 raised then
   fully refunded).
3. **2023 filing series is split across two publishers.** The three **town-side interim**
   "Financial Declarations" period slices (Jan 1–Oct 19, Oct 20–Nov 9, Dec 21–remaining) live
   only on `townofalta.utah.gov`; the **year-end summary** lives only on the state
   `salt lake_2023_Alta` folder. Neither source is complete alone; this dataset merges both.
4. **2021 "All campaign financial disclosures.pdf" is a combined DUPLICATE bundle** of the four
   individual candidate reports (some pages duplicated). It is retained for provenance but marked
   `join_confidence=none` / candidate "(multiple)"; do NOT sum it with the individual files.
5. **An inadvertently un-redacted twin of Anctil's 2025 10-07 report** is present on the GCS
   bucket (same key without the `REDACTED` suffix). Only the **redacted public copy** was
   retained; the un-redacted file was deliberately **not downloaded** (contains PII the filer
   intended to redact).

## Formats

- **Born-digital text (`format=text`, 7 files):** several 2025 report templates (Bourke ×3 in
  part, Anctil final, Moxley final, Byrne final) and the 2021 Anctil report parse with
  `pdftotext`. **Scanned (`format=scanned`, 29 files):** the remaining signed forms, all 2023
  files, all declarations, and most 2025 second-sheet itemizations are image scans.
- **Extraction is deferred:** `extraction_method = "none (raw acquisition; OCR/vision deferred)"`
  on every row. No `text/` sidecars and no dollar parsing in this layer.

## Double-count / dedup (SKILL §6)

Alta candidates file **multiple reports per cycle** — 2023 = 3 period interims + 1 year-end
summary; 2025 = 2 interims + 1 final for the winners. `is_incremental=yes` marks the discrete
**period slices** (safe to add across periods); `is_incremental=no` marks a cumulative/final or
single-cycle report (do not add to the interims). Because 2021/2023 money is essentially nil the
trap is moot there, but a 2025 dollar total must still go through `cycle_totals.py`, not a row sum.

## Honest gaps / non-issues

- **No pre-2020 Alta campaign finance** is in scope (data floor 2020; the earliest in-scope
  cycle is 2021). The state tree carries older SLCo years but no Town-of-Alta subfolders were
  pursued below the floor.
- **Conflict-of-interest statements are OUT OF SCOPE** for campaign finance and were **not**
  ingested (they are annual ethics filings, a separate regime). Their existence + URLs are noted
  above; the 2025 candidacy-packet COI disclosures and the annual 2025/2026 elected-officer COI
  forms remain on `townofalta.utah.gov` if a future ethics layer wants them.
- **Alta Canyon Rec** decoys are irrelevant here (that is a separate rec district, not the Town);
  no such files appear in any Alta finance folder.

## 2026-07-17 — STRUCTURED DOLLAR LAYER BUILT (extraction no longer deferred)

The acquisition-only stance above is **superseded** for the C&E reports: `build_finance.py`
(family `vision_cache`) now extracts dollar rows into `contributions.csv` / `expenditures.csv`
/ `filing_totals.csv` and the deduped `cycle_totals.csv`. `validate_finance.py` PASS
(0 FAIL). The 21 scanned reports come from the `vision/*.json` caches; the **6 born-digital
`format=text` money reports are parsed at build with pdftotext** (that is why they were
correctly not vision-cached). The 8 declarations stay out of scope; the 2021 combined bundle
is inventory-only (duplicate).

- **The 2025 substantive figures are now in the CSVs:** Bourke's **$2,000** Abundance
  Political Consulting contribution — captured as an **in-kind** contribution (the raw Form A
  writes the $2,000 in the *In-Kind* column, "Amount of Contribution" blank; cover 1b=$2,000
  includes it, reconciles) — and Byrne's **$4,725.11** self-funded-then-refunded pair (a
  contribution + a matching "Return of unused contribution" expenditure). 2021 Byrne $5,000
  self-funded and 2023 Schilling's lone $69.96 are likewise captured (Schilling's $69.96 is
  counted **once** — 3 duplicate filings superseded via cumulative-regime detection).
- **Cycle totals (`cycle_totals.csv`):** 2025 Bourke Mayor raised $2,000 / spent $0; 2025
  Byrne Mayor $4,725.11 raised & refunded; 2021 Byrne Council $5,000 / $239.89; 2023 Schilling
  $0 / $69.96; every other candidate-cycle nil. No review flags. **Query this file, never sum
  `filing_totals`.**
- **The 2025-roster FLAG 1 above is UNCHANGED** — `election_results/alta_races.csv` still
  lacks 2025; this layer only structures the money, it does not touch the elections layer.
- **Moxley's 2025 final** is born-digital but pdftotext-garbled → inventory-only nil row (no
  totals fabricated). The Anctil 2025 redacted copy stays null-address (never reconstructed).
</content>
</invoke>
