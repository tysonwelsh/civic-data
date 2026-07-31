# Holladay — Campaign-Finance Disclosures: Availability

**As-of:** 2026-07-13 (index/acquisition); vision transcription 2026-07-17 (wave 2); **STRUCTURED
DOLLAR LAYER BUILT 2026-07-17** (cf-structuring — see the dated section near the bottom). · **Layer:**
ACQUISITION + `vision/*.json` caches + the DERIVED structured CSVs (`contributions`/`expenditures`/
`filing_totals`/`cycle_totals`). `index.csv` `extraction_method` stays `none (acquisition-only; …)`
by design — the dollar figures live in the derived layer, not the index. **Cycles in scope:**
2021 (D1/D3/Mayor), 2023 (D4), 2025 (D1/D3/Mayor). **Bonus (pre-scope, trivially available):**
2017 (Mayor/D1/D3) from the state tree.

**52 files, 46 MB, all under `raw/`** (each with sha256 + HTTP status in `raw/_fetch_log.jsonl`),
fetched GET-only via `scripts/polite_fetch.py`. **Two document classes:**
- **40 campaign-finance filings** — Utah "FINANCIAL DECLARATION OF CANDIDATE" reports
  (contributions/expenditures), the campaign-finance dataset proper.
- **12 Conflict-of-Interest (COI) disclosures** — "Elected Officer Annual Conflict of Interest
  Disclosure Statement" (Utah Code 10-3-1313 / 20A-11-1604(6)), FY2025 (6) + FY2026 (6). These are
  **officeholder ethics disclosures, NOT campaign contribution/expenditure reports** —
  `filing_type='coi_disclosure'`; **exclude them from any cycle/money total.** Captured because they
  sit on the same city disclosure page and document each seated member's financial interests
  (useful to the elections→members→votes chain), but they are not campaign filings for any race.

**Format split: 13 born-digital `text` / 39 `scanned`** (image-only; OCR/vision deferred). Most
scanned files are the hand-filled state/city PDF declaration forms; the born-digital ones are the
typed 2025 D1/D3 reports, the 2021 Brewer pair, and the COI form for Sundwall.

## What was checked (search order)

1. **City recorder / elections page** — the state 2025 folder links to
   **`https://www.holladayut.gov/departments/city_recorder/elections/disclosure.php`** (Revize
   Document Center). This page is the live host for the **2023 and 2025** campaign-finance reports
   plus the FY2025/FY2026 COI forms (files under `Document Center/Departments/City Recorder/
   Elections/…` and `…/Elections/Financial disclosures/…`). `source=city_cf_page`. (The guessed
   `/elections.php` and `/financial_disclosures.php` paths 404; the real page is under
   `/elections/disclosure.php`. `holladayut.gov/sitemap.xml` 404s — enumerate from the state link.)
2. **State — `disclosures.utah.gov/Municipal`** (GET-navigable; files served from `municipal.utah.gov`
   with Windows **backslash** paths → rewritten to https + forward-slash + `%20`). County→year
   folders are `salt lake_<year>` with a `salt lake_<year>_Holladay City` (2019/2021) or
   `_Holladay` (2017) subfolder. Present with files: **`_2021_Holladay City`** (7 files),
   **`_2017_Holladay`** (4). The **`_2023_` entry redirects to the legacy
   `cityofholladay.com/government/elections/financial-disclosures/`** and the **`_2025_` entry
   redirects to the city `disclosure.php` page** — i.e. the city hosts the recent cycles (same
   pattern as Cottonwood Heights / Riverton). `source=state_lg_municipal_disclosures`.
3. **SLCo Clerk financial-disclosures** — `saltlakecounty.gov/clerk/elections/financial-disclosures/`
   hosts **county / school-board / metro-township / state** filings, **not** municipal city-council/
   mayor candidates (verified 2026-07-13; it cites UCA 10-3-208 but links no Holladay municipal
   candidate). Not a source here.
4. **Wayback** — **not needed**: the city `disclosure.php` page + the state `_2021_`/`_2017_`
   folders together cover every in-scope ballot candidate, and all 52 files fetched live (200).

## Coverage vs the election roster (`election_results/holladay_races.csv`)

**Every candidate who appeared on a ballot in an in-scope cycle (2021/2023/2025) has campaign-finance
filings — coverage is COMPLETE.**

| Cycle | Ballot candidates (office) | Finance filers held | Status |
|---|---|---|---|
| **2021** (D1/D3/Mayor) | D1 ×2 (Brewer\*, Hilton); D3 ×1 (Fotheringham\*, unopposed); Mayor ×1 (Dahle\*, unopposed) | all **4** | **COMPLETE** |
| **2023** (D4) | D4 ×2 (Quinn\*, Tracy) | all **2** | **COMPLETE** |
| **2025** (D1/D3/Mayor) | D1 ×2 (Sundwall\*, Bilstad); D3 ×2 (Bradley\*, Jones); Mayor general ×2 (Fotheringham\*, Watts) + primary 3rd (Wilson) | all **7** | **COMPLETE** |

`*` = seat winner. **Money-filing counts** (excludes the 12 COI forms): 2021 — Dahle, Brewer, Hilton
each an Oct pre-general interim + a year-end Final (Fotheringham, unopposed, filed only the Oct
interim). 2023 — Quinn and Tracy each 3 (a 7-day pre-general + an Oct-24 interim + a Final). 2025 —
D1/D3 candidates each 3 (Oct 7 + Oct 28 + Final); Mayor Fotheringham & Watts each 4 (Aug pre-primary
+ Oct 7 + Oct 28 + Final); Wilson 2 (Aug pre-primary + a Sept 11 Final after losing the primary).

**Bonus 2017** (pre-scope): Mayor Dahle, D1 Petersen, D3 Fotheringham + D3 runner-up Roach — one Aug
pre-primary declaration each (state `_2017_Holladay` folder). All four are in `races.csv` 2017.

## Discrepancy FLAGS (recorded here only — `election_results/` was NOT edited)

1. **⚠ Zac Wilson is the un-named eliminated 3rd 2025 mayoral primary candidate.** `holladay_races.csv`
   shows the **2025 municipal-primary Mayor** row with `n_candidates=3` but names only winner
   Fotheringham + runner-up Watts. The city page holds **Wilson's** Aug pre-primary + Sept 11 Final
   campaign-finance reports — the footprint of that third candidate. Finance **corroborates** the
   3-way primary; `races.csv` simply stores winner+runner-up only. `in_election_results=no`,
   `join_confidence=none` for Wilson is expected, not a coverage miss.
2. **Emily Gray filed a 2023 D5 campaign-finance report though the election dataset carries no 2023
   D5 row.** `election_results/CLAUDE.md` documents that 2023 D2 (Durham) and D5 (Gray) were
   **uncontested and omitted from the SLCo SOVC** (declared elected to Jan-2028 terms). Gray's filing
   corroborates that she stood (and was elected) in 2023 D5; it is **not** an election-record gap.
   `in_election_results=no` for this row reflects the omission, not missing data.
3. **No 2023 D2 (Matt Durham) campaign-finance filing surfaced.** Durham ran **uncontested** in 2023
   D5→D2 and the disclosure page carries no 2023 Durham campaign report (only his FY2025/FY2026 COI
   forms). An uncontested candidate may file a minimal/no report; treated as an honest absence, not a
   scraper miss.
4. **2019 cycle — no campaign-finance filings anywhere.** The state `salt lake_2019_Holladay City`
   folder is **registered but holds ZERO files** (0 vs 7 in the 2021 folder), and the city page's
   rolling window does not reach back to 2019. This aligns with the **known 2019 election-record gap**
   flagged in `recon.md` / `election_results/CLAUDE.md` (the 2019 general D2/D4/D5 were dropped from
   the canonical SLCo archive and had to be recovered by a raw SOVC re-parse). **No 2019 filings
   surfaced to corroborate the recovered contests** — the finance channel is silent for 2019, not a
   new recovery.
5. **Name spellings differ from the election roster** (normalized in `matched_election_candidate`,
   election names UPPER-CASE): 2023 D4 winner filed as **"Drew"** (= Drew B. Quinn); Watts' Oct-7
   report is the file literally named `Watts Financial Disclosure.pdf`; Bradley = Natalie Bellamy
   Bradley; Bilstad = Grant Jacob Bilstad.

## Roster-turnover notes (for the elections→members→votes join — the Jan-2026 seam)

The council **turned over at the Jan-2026 seating** (see `recon.md`): Mayor **Dahle → Fotheringham**;
D1 **Brewer → Sundwall**; D3 **Fotheringham → Bradley**. The finance set spans the seam:
**Fotheringham appears in three cycles** — 2017 D3 + 2021 D3 (as councilmember) and 2025 Mayor (as
mayoral winner) — the same person filing across offices. **Dahle** (outgoing Mayor) has 2013/2017/2021
election wins and 2017+2021 finance filings; he did not run in 2025 (his FY2025 COI is his last
officeholder disclosure). A date-aware join is required across the seam.

## The double-count trap (per SKILL §6) — READ BEFORE ANY DOLLAR TOTAL

Holladay candidates file **multiple reports per cycle** (2025 D1/D3 = Oct 7 + Oct 28 + Final; Mayor =
Aug + Oct 7 + Oct 28 + Final; 2021/2023 = interim(s) + a year-end Final). The "FINANCIAL DECLARATION
OF CANDIDATE" form is **cumulative-to-date** (each states total contributions/expenses and end-of-
period balance), so **NEVER sum a candidate's filings** for a cycle total — the year-end Final (or the
latest interim, if no Final) is the cumulative figure. `is_incremental='no'` on every campaign-finance
row reflects the cumulative style; verify per-candidate at extraction time via
`scripts/campaign_finance/cycle_totals.py` before quoting any total. COI rows carry blank
`is_incremental` (not applicable).

## Vision transcription status (2026-07-17, wave 2) — the dollar layer's raw inputs

The scanned C&E filings have now been **vision-transcribed** into `vision/<sha1(index_path)[:8]>.json`
caches via `/cf-vision-transcribe` (Read-tool, **$0 Anthropic API**), across two tranches:
tranche 1 (2025 cycle, 11 caches) + tranche 2 (2023 then 2021 cycles + the Bradley fix, 13 caches) =
**24 caches**. **Every in-scope 2021 / 2023 / 2025 scanned C&E filing now has a cache** (Gray 2023
D5, indexed `statement`, is in fact a full Financial Declaration form and was transcribed). The 13
born-digital `text` filings were never scanned-vision candidates. **Still un-transcribed by design:**
the 2017 bonus scanned filings (4, pre-scope) and the 12 COI ethics disclosures (not C&E reports).
Contents are **verbatim, un-reconciled** — several source cover-vs-schedule and cover-total
discrepancies are preserved as flags (see `campaign_finance/CLAUDE.md` tranche-2 note). **UPDATE
2026-07-17:** the structured `build_finance.py` / `filing_totals.csv` / `cycle_totals.csv` layer has
now been BUILT (see the dated section below) and 12 additional born-digital `text` filings were
transcribed into caches (36 total); the double-count trap below is now enforced by
`cycle_totals.csv` + `cycle_overrides.csv`.

**Bradley Oct-2025 index correction (2026-07-17):** a tranche-1 note wrongly flagged
`raw/2025_city_bradley-10282025.pdf` as Fotheringham content. On re-reading, the file is **genuinely
Natalie Bellamy Bradley / D3** (sha256 byte-identical to its fetch-log entry — never changed; the
earlier claim was a scratchpad render collision). Its `date` was refined `2025-10-27` → **`2025-10-24`**
(the form's own DATE / reporting-period-end / RECEIVED stamp all read 10/24/25, filed for the Oct-28
deadline). **Bradley's full 2025 set is present — no acquisition gap.**

## 2026-07-17 — STRUCTURED DOLLAR LAYER BUILT (cf-structuring wave)

The structured layer is now built (`build_finance.py`, family `vision_cache`): **`contributions.csv`
(308) / `expenditures.csv` (372) / `filing_totals.csv` (40) / `cycle_totals.csv` (18
candidate-cycles)**, all DERIVED + regenerable. `validate_finance.py` **PASS**; `validate_city.py`
**0 FAIL**. Read `campaign_finance/CLAUDE.md` for the full decision record.

- **All 40 in-scope C&E filings are covered.** The 24 scanned caches were joined by **12
  born-digital `format=text` filings transcribed at build time** (2021 Brewer ×2; 2025 Sundwall
  ×3, Bilstad ×2, Jones ×3, Watts Oct-7, Wilson Final) — these carry a REAL money-bearing text
  layer, so they are NOT left inventory-only. `vision/` now holds **36 caches**. The 4 below-floor
  **2017** bonus scans remain honest inventory-only rows (unknown totals). The **12 COI ethics
  disclosures stay OUT of scope** (excluded from the money layer; they surface as
  `validate_finance` WARNs by design).
- **Cover totals are CASH-ONLY** — Gray 2023's $3,000 in-kind is excluded from her printed cover
  (build uses `reconcile_cash_only=True`).
- **The double-count trap is now ENFORCED, per candidate.** 2021 filers file cumulative
  restatement chains (latest/Final = the cycle); 2023/2025 filers file per-period reports (summed,
  with `cycle_overrides.csv` supplying the 6 per-period filers whose "Final" is itself a period —
  Quinn 2023, Bradley/Fotheringham-Mayor/Sundwall/Bilstad/Jones 2025). **Tracy 2023, Watts 2025,
  Wilson 2025 are left computed + `MIXED`-flagged** (their reports overlap / don't chain — a clean
  cycle sum is ambiguous; do NOT quote a single cycle figure for them without checking the
  filings). **Always read `cycle_totals.csv`; never sum `filing_totals`.**
- Reconciliation flags are honest source artifacts (the >$50 cover excludes ≤$50 itemized donors;
  2025 filers omit the $50 filing fee from stated totals; a handful of filer typos) — kept
  verbatim, never adjusted.

## Not captured / out of scope (deliberate)

- **Structured dollar rollup (`filing_totals.csv` / `cycle_totals.csv`)** — ✅ **BUILT 2026-07-17**
  (see the section immediately above). Reconciled per-filing + deduped per-cycle totals are now
  published.
- **Pre-2017 state folders** (`salt lake_2015_…`, etc.) exist but are far below scope — not fetched.
- **COI ethics disclosures beyond FY2025/FY2026** — only the two years posted on the current page were
  captured; older COI forms (if any) are not on the rolling page.
