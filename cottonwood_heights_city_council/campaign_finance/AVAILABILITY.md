# Cottonwood Heights — Campaign-Finance Disclosures: Availability

**As-of:** 2026-07-13 · **Layer:** ACQUISITION-ONLY (raw filings retained with full
provenance; **no OCR/vision extraction and no dollar totals** — those are deferred,
`extraction_method='none (raw acquisition; OCR/vision deferred)'` on every row). **Cycles in
scope:** 2021 (D3/D4/Mayor), 2023 (D1/D2), 2025 (D3/D4/Mayor). **Bonus (pre-scope, trivially
available):** 2019 (D1/D2) and 2017 (D3/D4/Mayor) — see below.

**86 filings, 46 MB, all under `raw/`** (each with sha256 + HTTP status in
`raw/_fetch_log.jsonl`). Fetched GET-only via `scripts/polite_fetch.py`. **Format split:
31 born-digital `text` / 55 `scanned`.**

## What was checked (search order)

1. **City recorder / elections page** — `www.cottonwoodheights.utah.gov/your-government/elections`
   (CivicEngage Central; the site edge-403s a bare UA — `polite_fetch.py` gets 200). The current
   page is the **"2025 Election Information"** table: one row per 2025 candidate with linked
   `/home/showpublisheddocument/<id>/<ver>` PDFs — an **initial Financial Disclosure Statement**, a
   **Conflict-of-Interest disclosure**, and the three campaign-finance reports (**Oct 7**, **Oct 28**,
   **Dec 4 2025**). This page holds **2025 only** (rolling window); older cycles are **not** linked
   here and there is **no** dedicated `campaign-finance-disclosures` / Document-Center listing
   (the guessed `/elections/campaign-finance-disclosures` path 404s). `source=city_elections_page`.
2. **State — `disclosures.utah.gov/Municipal`** (GET-navigable folder tree; individual files served
   from `municipal.utah.gov`). The county→year folders are named **`salt lake_<year>`**, each holding
   a **`salt lake_<year>_Cottonwood Heights`** subfolder. File links carry Windows **backslash**
   paths (`.../salt lake\2021\Cottonwood Heights\<file>.pdf`) → rewritten to https + forward-slash +
   `%20`. Present: **`salt lake_2021_Cottonwood Heights`** (29 files), **`_2023_`** (14 files),
   **`_2019_`** (12), **`_2017_`** (4). The **`_2025_` entry only links back to the city page** (the
   city hosts 2025, like Riverton). `source=state_lg_municipal_disclosures`.
3. **SLCo Clerk financial-disclosures** — posts county/state candidate filings, **not** municipal
   candidates (per skill guidance); not a source for Cottonwood Heights council/mayor candidates.
4. **Wayback** — not needed: the state folder tree and the city 2025 page together cover every
   in-scope ballot candidate, and all files fetched live (200) from the primary hosts.

## Coverage vs the election roster (`election_results/cottonwood_heights_races.csv`)

**Every candidate who appeared on a ballot in an in-scope cycle (2021/2023/2025) has campaign-finance
filings — coverage is COMPLETE.**

| Cycle | Ballot candidates (office) | Finance filers held | Status |
|---|---|---|---|
| **2021** (D3/D4/Mayor) | D3 ×5 (Newell*, Hanson, Rawlings, Boman, McShaffrey); D4 ×3 (Birrell*, Kim, Walker); Mayor ×5 (Weichers*, Kraan, Evans, Hallbeck, Schwartz) | all **13** | **COMPLETE** |
| **2023** (D1/D2) | D1 ×2 (Holton*, Cottam); D2 general ×2 (Hyland*, Daurelle) + primary 3rd (Bracken) | all **5** | **COMPLETE** |
| **2025** (D3/D4/Mayor) | D3 ×2 (Newell*, Prazen); D4 ×2 (Birrell*, Kim); Mayor ×2 (Bennion*, Weichers) | all **6** | **COMPLETE** |

`*` = seat winner. **Money-filing counts** (excluding the 6 COI forms): 2021 — most candidates
2 each (pre-general statement + Final Financial Report); Newell/Rawlings/Kim have a 3rd (an
AMENDED pre-general statement); **McShaffrey and Schwartz filed only the pre-general statement, no
Final report**. 2023 — Holton/Bracken/Daurelle ×2, Hyland ×3, Cottam ×4 (Cottam & Hyland each add
an Oct 24 2023 interim; Cottam adds a separate contributions/expenditure schedule). 2025 — every
candidate exactly 4 (initial statement + Oct 7 + Oct 28 + Dec 4) + 1 COI.

**The 2021 finance filer counts (D3=5, D4=3, Mayor=5) exactly match `races.csv` `n_candidates`** —
strong corroboration. Cottonwood Heights ran all 2021 candidates on the general ballot (no 2021
primary), consistent with the election dataset. **Mid-field 2021/2019 candidates who are neither
the winner nor runner-up** (Rawlings, McShaffrey, Boman, Walker, Evans, Schwartz, Hallbeck)
legitimately carry `matched_election_candidate=` blank / `join_confidence=none` — `races.csv` stores
only the winner + runner-up **names** per contest, not the full field. This is NOT a coverage gap.

## Discrepancy FLAGS (recorded here only — `election_results/` was NOT edited)

1. **⚠ 2019 D1 finance filings indicate a 2019 CH primary that the election dataset says did not
   happen.** `election_results/CLAUDE.md` states *"2019 municipal primary raw SOVC contains no CH
   sheet (checked) → confirmed no 2019 CH primary."* Yet the state 2019 folder holds **Christopher
   McHugh**'s `Financial Disclosure PRIMARY` + a `September 10 2019` report, and **Deborah Case**'s
   `Financial Disclosure PRIMARY` + an `AMENDED Campaign Financial Report 8-23-19` — i.e. **three
   D1 candidates (Petersen, Case, McHugh) with pre-primary (Aug/Sept 2019) filings**, which is the
   footprint of a **2019 District-1 primary** (>2 candidates → primary trigger). **McHugh is absent
   from `races.csv` entirely.** This is the classic "finance data surfaces an election-record gap"
   case. It is BONUS/pre-scope (2019), flagged for a maintainer to reconcile — **do not edit the
   election dataset from here.** (Plausible reconciliation: a 2019 CH primary sheet the SLCo SOVC
   normalizer dropped, mirroring the 2019 general D1/D2 recovery already documented for this city.)
2. **2023 D2 primary — Scott Bracken is the un-named eliminated 3rd candidate.** `races.csv` shows
   the 2023 D2 **primary** with `n_candidates=3` but names only winner Daurelle + runner-up Hyland.
   The state folder holds **two Scott Bracken 2023 D2 statements** — Bracken is that eliminated third
   (finance corroborates, does not contradict). No general-ballot appearance; no Final report.
3. **2017 Tonia Dalton** — a pre-primary (Aug 31 2017) filer not among the 2017 winners/runner-ups;
   consistent with the 2017 D3/D4 primaries already in `races.csv` (an eliminated primary candidate).
4. **Name spellings differ from the election roster** (normalized in `matched_election_candidate`):
   Weichers is filed **"Michael Wiechers"** (2021 candidate PDF) and **"Mike Weichers - Fina[l]
   Financial Report"** (typo in the source filename) → `MIKE WEICHERS`; **Jen Cottam** is filed
   both "Cottam" and "Cottham" → `JEN COTTAM`.

## Roster-turnover notes (for the elections→members→votes join)

- **Mayoral turnover Weichers → Bennion (2025).** Incumbent **Mike Weichers** (won Mayor 2021) was
  defeated by **Gay Lynn Bennion** in 2025 (Bennion 57.5%). **Both filed the full 2025 city packet**
  (initial statement + Oct 7 + Oct 28 + Dec 4 + COI). Weichers also has 2021 Mayor filings — the same
  person appears in two cycles.
- **Petersen → Holton, District 1 mid-2023 appointment.** **Douglas Petersen** (won D1 2019; his 2019
  finance filings are in the bonus set) left the D1 seat; **Matt Holton** was appointed to the D1
  vacancy (sworn ~May 2023) and then **won the November 2023 D1 general** (his 2023 finance filings
  are in scope). A mid-term *appointment* triggers no campaign-finance filing, so there is an honest
  gap between Petersen's 2019 reports and Holton's 2023 reports for the D1 seat — expected, not
  missing data.

## Formats

31 born-digital (`text`) / 55 image-only (`scanned`). **All 30 of the 2025 city PDFs are scanned**
(photographed/scanned filled forms). The 2019 set is almost entirely scanned; 2021/2023 are mixed
(most born-digital state PDFs are the "Candidate for X" pre-general statements and several Final
reports). OCR/vision extraction is deferred (acquisition-only).

## Not captured / out of scope (deliberate)

- **Parks & Recreation Service Area trustee** candidates — a separate special-service district, not a
  city council/mayor seat (excluded here exactly as in `election_results/`). The state folders did not
  surface trustee finance files for the in-scope years; none were fetched regardless.
- **Pre-2017 state folders** (`salt lake_2015_…`, `_2013_…`, etc.) exist on the state tree but are far
  below scope and were not fetched.
- **Dollar amounts / contribution + expenditure tables** — not extracted (this is the acquisition
  layer). Extraction to `filing_totals.csv` / `cycle_totals.csv` is future work.

## Double-count trap (per SKILL §6) — READ BEFORE ANY DOLLAR TOTAL

Cottonwood Heights candidates file **multiple reports per cycle** (e.g. 2025 = initial statement +
Oct 7 + Oct 28 + Dec 4; 2021/2023 = pre-general/interim statement + year-end Final). Utah municipal
statements are **cumulative-to-date**, so **NEVER sum a candidate's filings** for a cycle total — the
year-end Final (or the latest interim) is the cumulative figure. Any per-candidate/per-race total must
be computed with the repo dedup (`scripts/campaign_finance/cycle_totals.py`) at extraction time, not
by adding `index.csv` rows. `is_incremental='no'` on every row reflects the cumulative filing style.

## 2026-07-17 — vision tranche 2 (2021/2023 cycles) + metadata corrections + `duplicate_of`
- **All 12 scanned 2021/2023-cycle filings transcribed** via the Read-tool vision method
  ($0 API): 2021 — Hallbeck final, Boman pre-general + final, Walker final, Rawlings
  amended pre-general, Birrell pre-general, Newell final; 2023 — Cottham 10/24 interim,
  Bracken pre-primary + post-primary, Daurelle pre-primary + year-end final. Caches
  `vision/<sha1(path)[:8]>.json` (tranche-1 convention); vision/ now 30 caches.
  Honest limits: the Cottham interim PDF publishes the COVER ONLY (no Form A/B pages) —
  totals verbatim, itemized rows honestly empty; Birrell's "The City Journal $720"
  expenditure prints an illegible date (null); Daurelle's typed reports carry printed
  carry-forward aggregate lines ($8,166 / $6,324.13) transcribed as name-less rows so
  the report reconciles to its own cover; source typos (10/24/2024, 11/21/2021,
  12/19/2021, "30 cents") retained verbatim.
- **Index corrections (in-body + election-record evidence):**
  - `2023_state_scott-bracken-district-2.pdf` was labeled a SECOND "Pre-primary"
    statement — it is the **post-primary** statement (signed 10/5/2023, balance-forward
    $3,083.05 = the pre-primary's ending balance; election record confirms Bracken
    finished 3rd in the 9/5 primary). NOT a duplicate of `2023_state_scott-bracken.pdf`.
  - `2023_state_sharon-daurelle.pdf` was labeled "Pre-general" — in-body it is dated
    Aug 28/29 2023 with itemization spanning 7/4–8/26: the **pre-primary** statement.
  - Filing dates for the four 2023 Bracken/Daurelle rows now carry the page-stated
    signature dates (`date_precision=page_stated`).
- **`duplicate_of` column added** (documented extension, per the 2026-07-17 wave
  follow-up): blank everywhere — a sha256 + metadata sweep found **0 byte- or
  logical-duplicate filings** (the suspected Bracken pair proved to be distinct filings,
  above). The column is the standing mechanism: if a future acquisition lands the same
  filing twice, mark the later row's `duplicate_of` with the kept row's `path`.
- **`duplicate_of` populated for the one confirmed logical duplicate** (2026-07-17,
  same session): `2025_city_prazen_final-dec-4-2025.pdf` → duplicate_of
  `2025_city_prazen_interim-oct-28-2025.pdf`. Different PDF bytes (re-upload) but
  page-level VISUALLY IDENTICAL (same handwritten 10/07/25 date, same totals
  $3,471.84/$85.00/$3,556.84/$0.00, same 6 rows, same signature — the tranche-1
  finding, re-verified by page image). Consequence: **Prazen's genuine Dec-4 final
  report is NOT on file** (the city's Final slot serves the interim scan) — an honest
  acquisition gap; recover from the recorder if ever needed.

## 2026-07-18 — STRUCTURED CF LAYER (extraction status: BUILT for the cached set)

The acquisition layer above is now backed by a DERIVED money layer (`build_finance.py` →
`contributions.csv` / `expenditures.csv` / `filing_totals.csv`; `cycle_totals.py` →
`cycle_totals.csv`). Extraction status per filing:

- **37 of 74 in-scope filings are TRANSCRIBED** (30 tranche-1/2 vision caches + 7 new Read-tool
  vision caches written 2026-07-18: Cottam ×3, Holton ×2, Kraan ×2 — the clean typed text reports).
  1,170 contribution + 550 expenditure rows; 21 filings reconcile both sides.
- **37 in-scope filings are INVENTORY-ONLY** (acquired, honestly NOT transcribed — unknown totals,
  low confidence, dated reason in `filing_totals.notes`; acquired ≠ transcribed, never guessed):
  - **2017 ×4 + 2019 ×12** — below-2020-floor BONUS scans (kept in scope as inventory rows).
  - **2021 ×18 + 2023 Hyland ×3** — `format=text` filings whose §10-3-208 COVER totals are
    handwritten/garbled in the text layer (typed itemized tables DO carry real money). **Queued
    vision-tranche follow-up** — deferred, not zero. Candidates: Schwartz, Wiechers, Evans, Hanson,
    Kim, Newell, Rawlings, McShaffrey, Walker, Hallbeck, Birrell-final (2021); Hyland (2023).
- **12 EXCLUDED (out of scope, not gaps):** the six 2025 `statement` (initial financial-disclosure)
  + six `conflict_of_interest` forms — no contributions/expenditures.

**In-kind convention (verified):** CH cover TOTALs INCLUDE in-kind at face value (expenditure side:
Rawlings, Newell 2021); the one cover that EXCLUDES it (Daurelle contrib) reconciles cash-only via
the driver's per-filing fallback + note. `build_finance.py` runs `reconcile_cash_only=False`.

**Per-candidate regimes + the 4 `cycle_overrides.csv` rows** (all 2025) are documented in the CF
`CLAUDE.md` 2026-07-18 section: Prazen (Dec-4 = `duplicate_of` re-upload of Oct-28; genuine final =
acquisition gap), Newell (regime mis-detection → cumulative), Weichers + Birrell (per-period filers
whose "summary" is itself a period report → cycle = SUM of the period covers; Birrell's Oct-28
$513-vs-$5,363 filer error makes her spend a documented lower bound).

**Validators:** `validate_finance.py` PASS (0 fail; 12 expected warns = the excluded set);
`scripts/validate_city.py` 0 FAIL.
