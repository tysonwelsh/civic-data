# campaign_finance — Emigration Canyon candidate campaign-finance & COI disclosures

**ACQUISITION-ONLY layer** (source type 6 of `/expand-city-sources`). Raw filings retained verbatim
under `raw/` with a machine-readable `raw/_fetch_log.jsonl`; `index.csv` catalogs every retrieved
artifact against the SCHEMA_SPEC.md §9 contract. **No OCR/vision extraction and no dollar totals are
computed here** — `extraction_method` is `none (raw acquisition; text/OCR/vision deferred)` on every
row. Read `AVAILABILITY.md` for the full coverage/threshold/discrepancy record and `unrecovered.csv`
for the blocked/absent cycles (2023, 2025 general CF).

## Scope & the jurisdiction split (this is the whole story)

Emigration Canyon (~1,600 pop., Salt Lake County) is a **metro township (2017–2024) → CITY
(2024-05-01, HB35)**, MSD-staffed, with **no city document CMS** (a minimal Wix site + Utah PMN).
Elections are administered by the **Salt Lake County Clerk**, so filing jurisdiction — and
retrievability — split by era exactly like the sibling cluster (Copperton/Kearns/Magna/White City):

- **Township campaign-finance filings 2016–2019** were filed with the **county** and posted on the
  SLCo Clerk's **static** metro-township-councils page → **26 PDFs** (`source=slco_clerk_static`).
- **2023 (still a township)** moved to the county's **EasyVote** SPA (2022+), which is
  **HTTP-500/auth-gated** → **not retrievable** under polite GET (honest gap; `unrecovered.csv`).
- **2025 (now a city)** candidates file with the **city recorder** (MSD's Diana Baun);
  `emigration.utah.gov` (Wix) posts the **4 primary campaign-finance statements** + current
  elected-officer **COI** forms.

Per the metro-township cluster lesson: these entities are **absent from `disclosures.utah.gov/Municipal`**
(search endpoint HTTP-500 at check time). Do NOT expect Emigration there.

## What's in `raw/` (35 indexed PDFs + context)

- **26 township campaign-finance `*.pdf`** — SLCo Clerk candidate disclosures, all **scanned**:
  2016 (16, founding cohort — 8 candidates × interim + summary/dissolution) / 2017 (4, Smolka +
  Bowen) / 2019 (6, Hawkes/Brems/Tippetts/Harris).
- **4 city 2025 candidate campaign-finance `city_electioninfo_*.pdf`** — "Report of Contributions
  and Expenditures" (10-3-208), primary report DUE Aug 5 2025: Pinon (born-digital text),
  Steed/Posner/Wheelock (scanned).
- **5 city Conflict-of-Interest `city_coi_*.pdf`** (`filing_type=coi_disclosure`) — current
  elected officers Brems/Hawkes/Harris/Pinon (10-3-1301) + Griffith (candidate/officeholder 10-3-1313).
- **Context (NOT indexed):** `_slco_metro_township_archive.html` (the harvested county source page)
  and `_context_2017_township_budget_NOT-cf.pdf` (an unlabeled link on `/disclosure-statements`
  that resolved to a 2017 township **budget spreadsheet** — not a finance filing).
- **`_fetch_log.jsonl`** — every fetch (url, status, bytes, sha256, retrieved_utc); the build script
  reads each row's `source_url` from here (never hard-coded).

## index.csv schema

§9 campaign_finance contract prefix (exact, in order):
`date,candidate,office,election_year,filing_type,reporting_period,title,source_url,retrieved_date,format,extraction_method`
then extras (mirrors the Copperton/Kearns/Magna CF schema):
`path,source,date_precision,is_incremental,matched_election_candidate,join_confidence,sha256,notes`.

- **`filing_type`** ∈ `interim` (18 — Oct/Nov period reports + the 4 city 2025 primary reports) ·
  `summary` (12 — Dec year-end + 2016 dissolution/closing reports) · `coi_disclosure` (5 — city COI).
- **`office`** = cycle-level (`Metro Township Council (founding, at-large)` / `… At-Large (2017 @LRG)`
  / `… At-Large (2019 cycle)` / `City of Emigration Canyon Council (2025, at-large)` / the COI office
  labels). All seats are **at-large** (no seat key).
- **`election_year`** — 2016 / 2017 / 2019 / 2025; **BLANK** on the annual COI rows (not a cycle).
- **`format`** = `scanned` (29) / `text` (6 — Pinon 2025 CF born-digital + the 5 COI forms, which
  are scanned filled forms carrying an embedded/OCR text layer). `extraction_method` uniform
  `none (raw acquisition; text/OCR/vision deferred)`.
- **`date` / `date_precision`** — `county_folder_ym` (2016 files, year+month from the county
  `/2016_disclosures/…` URL path) · `county_page_year_label` (2017/2019 root files — the **year is
  read from the county page's own "&lt;YYYY&gt; Financial Disclosure Reporting" header**, not OCR;
  more reliable than the Copperton build) · `form_report_box` (2025 city CF — the report type box +
  received stamp gives the Aug-5 date) · `city_page_label` (city COI, anchored to the Jan filing window).
- **`is_incremental`** = BLANK (deferred). The Dec `summary` is expected cumulative; do NOT sum a
  candidate's filings before the extraction pass. Any dollar total → `cycle_totals.py`, never a row sum.
- **`matched_election_candidate`** = UPPER-CASE `emigration_canyon_races.csv` name where the person
  is a candidate of record; **`join_confidence`**: `high` (2017 @LRG winners + all 4 2025 primary
  candidates — real election rows) · `medium` (2016 founding cohort members who also appear later +
  the 2019 cohort — real people of record but no matching election row exists) · BLANK on the
  never-elected 2016 founders (Hook/Staggers/Raile/Christensen) and the appointed Griffith COI.
- **`sha256`** recomputed from disk by the build script.

## The three discrepancy FLAGS (see AVAILABILITY.md — recorded, never edited into election_results/roster)

1. **Founding year label:** finance shows a broad **2016** founding field (8 candidates);
   `election_results` labels the founding contest **2017** and keeps only Smolka + Bowen. Founding
   metro-township elections were Nov 2016 (terms Jan 2017).
2. **2019 cycle:** Hawkes/Brems/Tippetts/Harris each filed **2019** disclosures — a cycle **ABSENT
   from the election layer** AND one recon §6 explicitly said didn't happen ("no council contest
   2019"). Finance **contradicts that** and confirms the 2019 activity (the documented 2019 SLCo drop).
3. **Griffith appointed, not elected:** the 2025 certified candidate field was Pinon/Steed/Posner/
   Wheelock only, yet Griffith holds a 2026 council seat and filed an officeholder COI → **appointed**
   (roster nuance; recon flagged "Griffith vs 2023 winner Tippetts").

## COI rows — retained per the SKILL's COI→coi_disclosure note

The 5 `coi_disclosure` rows are **conflict-of-interest statements** (Utah Code 10-3-1301 / 10-3-1313),
**not** contribution/expenditure reports — no dollar figures. Retained because the city publishes no
campaign-finance dollar report for the township winners now sitting, so these are the substantive
current-officer disclosure record. Do NOT treat a COI row as a campaign-finance total.

## Counts (as-of 2026-07-14)

**35 rows** — by election_year: **2016** 16 · **2017** 4 · **2019** 6 · **2025** 4 · **(annual COI)**
5. By source: **slco_clerk_static** 26 · **city_website** 9. By filing_type: **interim** 18 ·
**summary** 12 · **coi_disclosure** 5. Format: **scanned** 29 · **text** 6. **2023** (4 candidates)
and the **2025 general-election reports** (Pinon + Steed) are the honest gaps (`unrecovered.csv`).

## Join to other layers

Join finance ↔ council votes/elections on **person + year** (Emigration seats are **at-large** — no
district key) — normalize the UPPER-CASE election names first (e.g. `JOE SMOLKA`, `DAVID PAUL BREMS`,
`CATHERINE M HARRIS`, `ROBERTO PINON`). Mind the **township→city seam** (2024-05-01) and that the
**presiding Mayor VOTES in both eras** (Millcreek pattern, max roll 5). Joe Smolka spans 2016
founding → 2017 @LRG winner → township-era Mayor; Brems/Hawkes/Harris span 2016/2019 → 2023 winners
→ current city council; Pinon appears as a 2025 CF filer AND a current-officer COI filer (two docs).

## Rebuild / refresh

`index.csv` is generated from the retained `raw/` PDFs + `raw/_fetch_log.jsonl`:
```
python3 build_emigration_cf_index.py   # idempotent; recomputes sha256 + format from disk, reads source_url from the fetch log
```
The SPEC table (year/candidate/period/filing_type/match) is hard-coded from the SLCo Clerk page's
per-candidate Emigration grouping (candidate + year headers on the page itself) + the city Wix
`/election-information` and `/copy-of-disclosure-statements` pages. To refresh:
- **2016–2019 (static county page):** re-harvest anchors from
  `saltlakecounty.gov/clerk/elections/financial-disclosures/metro-township-councils/` (#emigration).
- **2023 (EasyVote):** requires reaching `ecf-api.easyvoteapp.com` past its HTTP-500/auth-gate — a
  browser/session fetch, not polite GET.
- **2025+ (city site):** re-harvest `emigration.utah.gov/election-information` +
  `/copy-of-disclosure-statements` (Wix `_files/ugd/e1a144_<hash>.pdf`).
Fetch new PDFs through `../../.claude/skills/expand-city-sources/scripts/polite_fetch.py` (GET-only,
logged) into `raw/`, extend the SPEC table, and re-run. A later dollar-extraction pass
(`/cf-vision-transcribe` → `cycle_totals.py`) is deferred and OUT OF SCOPE here.

## `vision/` — Read-tool transcription cache (2026-07-17; ADDITIVE, still no structured layer)

The 29 **scanned** campaign-finance reports (`format=scanned`, `filing_type` interim|summary — the 2016
founding cohort, 2017/2019 township cycles, and the 3 scanned 2025 city primary reports) were
transcribed via **`/cf-vision-transcribe`** (Read-tool, **$0 API** — Claude Code allotment, NOT the
Anthropic API) into `vision/<sha1(index_path)[:8]>.json`, matching the **midvale vision schema
byte-for-byte** (`contributions[]`/`expenditures[]` verbatim strings + printed cover totals +
`beginning_balance`/`ending_balance`/`contributions_50_or_less` + a `_meta` block). This is a
**pre-staged cache only — there is STILL no structured build here** (no `build_finance.py`, no
`filing_totals.csv`, no db tables); the structured/dollar-rollup layer remains **owner-gated**, exactly
like midvale. Nothing consumes these JSONs yet; they exist so the owner can later gate the structured
layer in without re-doing vision.
- **NOT transcribed:** the 6 `format=text` rows (Pinon's born-digital 2025 CF report + the 5
  `coi_disclosure` COI forms — COI is a conflict-of-interest declaration, not a contributions/
  expenditures report, so it has no line-item schema).
- **Findings (honest, verbatim — the anti-fabrication discipline held):** the record is dominated by
  **$50 filing-fee-only, candidate-self-funded** filings ($50 in / $50 out / $0 balance) and outright
  **zero-activity** filings. Only 15 itemized contributions + 15 expenditures across all 29. Notable
  source quirks preserved as printed, NOT corrected: 2019 Harris/Hawkes carry **negative (−$50) ending
  balances**; 2016 Hawkes summary is internally inconsistent (struck-out balances, a −$50.00 close);
  2019 Tippets Dec summary is a **cover-page-only PDF with no Summary Page** (all nulls); several
  filings print activity only in the year-to-date column with a $0 "this period". Struck-out `$500`
  mis-entries (Brems 2019, Harris 2019) were read to the corrected $50. Blank date cells → `null`
  (the 2025 city Schedule A/B form has no date column).
- **Re-vision:** idempotent — re-running overwrites the same `vision/<hash>.json`. No do-NOT-re-vision
  flags are set. Never hand-edit the JSONs to "fix" a source inconsistency; a genuinely illegible digit
  stays `null`.

## 2026-07-17 — STRUCTURED LAYER BUILT (vision-cache reference implementation)

`build_finance.py` (family **`vision_cache`**, shared helpers `scripts/campaign_finance/vision_lib.py`;
reference impl = midvale) now writes the four derived CSVs — regenerable, never hand-edited:
- `contributions.csv` (**16** itemized rows) / `expenditures.csv` (**16**) /
  `filing_totals.csv` (**30** rows = every in-scope C&E filing) / `cycle_totals.csv`
  (**18** candidate-cycles). Regenerate: `python3 build_finance.py` then
  `python3 ../../scripts/campaign_finance/cycle_totals.py emigration_canyon`.
- **`validate_finance.py` PASS** (0 fails; 5 warns = the 5 COI rows correctly excluded from
  `filing_totals`). `scripts/validate_city.py emigration_canyon_city_council/` = 0 FAIL.

**Scope:** all 30 Report-of-Contributions-&-Expenditures filings are IN (26 township 2016/2017/2019 +
4 city-2025 primary — township-era retained, full-history entity). The **5 COI forms are OUT** of
scope (`in_scope_fn` excludes `filing_type='coi_disclosure'` — not C&E reports, no dollars).

**All 30 in-scope filings are transcribed** (no honest-not-transcribed inventory rows): 29 scanned
forms from the pre-staged vision caches + **Pinon 2025** transcribed from its **born-digital TEXT**
layer (`pdftotext`) into `vision/fbe3c5ba.json` (same schema; `format=text` ⇒ **HIGH** confidence).

**The honest shape (NOT a build failure):** the record is dominated by **$50 filing-fee-only,
candidate-self-funded** filings and outright **zero-activity** reports. Only two filings carry real
itemization beyond a filing fee: Brems 2016 (5 contribs / 5 expends) and the Bradley $245.69 gift.

**Per-candidate regime decisions (evidence-based, printed every build — eyeballed):**
- **Cumulative** (latest report wins; earlier snapshots marked `superseded`): Brems 2016, Bowen 2016,
  Hawkes 2016, Smolka 2016, Christensen 2016, Raile 2016, Hook 2016, Smolka 2017. Each Dec
  summary/dissolution restates the same (non-decreasing) cover totals.
- **Incremental** (per-period; summed): Staggers 2016, Bowen 2017, Harris 2019 (Dec summary is the
  NEAR-EMPTY $0 report, the $50 filing fee sits in the interim), Tippets 2019 (Oct $0 + Dec
  cover-page-only null → `insufficient chain evidence`, summing safe).
- Single-filing cycles (Brems 2019, Hawkes 2019, all four 2025) default incremental (a group of one).

**NO `cycle_overrides.csv` needed** (unlike midvale). Every EC incremental filer's "summary/dissolution"
is the $0 report, so `cycle_totals.py`'s `max(latest-summary, summed-interims)` already picks the
interim's real figure — no per-period money is dropped, so no override applies. `cycle_totals.csv` has
**zero `review_flag`s**.

**Verbatim source quirks PRESERVED, never corrected:**
- **Brems 2016 interim $100 arithmetic error** — 5 expenditure items sum to **$562.11** but the cover
  prints **$662.11**; `reconciles_expend=False`, `recon_delta_expend=-100.00`, rows capped `low` +
  `needs_review=1`. Contributions reconcile exactly ($662.11). Flagged, NOT adjusted.
- **2019 Harris/Hawkes** negative (−$50) ending balances; **2019 Tippets Dec** cover-page-only PDF
  (all nulls → blank stated totals, blank reconcile). Copied verbatim.
- **Totals-only filings** (a positive cover with zero itemized rows — Utah under-$500 exemption)
  reconcile **UNKNOWN** (blank), never a fabricated mismatch (10 such rows).

**Bowen 2016 two-report bundle — RESOLVED by re-vision.** `raw/2016_nov_gary-bowen.pdf` STAPLES two
reports (pp.1-2 November 1: Column A this-period $0 / Column B YTD $55; pp.3-4 June 21: $55/$55). The
prior cache (`773be790`) captured only the November Column-A ($0) and lost the June sub-report. **Re-visioned
into the `reports[]` multi-report schema** (top-level total = the $55 YTD the November Column B shows;
`build_result` emits the "multi-report bundle" note); the Dec summary (`cff93a02`) independently restates
$55/$55. Cycle total = **$55/$55** (was heading to $0 pre-fix). Original cache backed up to
`_backups/2026-07-17-cf-structuring/emigration_canyon/773be790.json.orig`.

**No `donor_aliases.csv` / `finance_overrides.csv`** were needed (like midvale — the record is too small
and clean to require curated merges or corrections). Minor deterministic-classifier nuance (report-only,
not overridden): Raile 2016's `"Rick Raile, Candidate for … filing fee"` self-payment classifies
`individual` (no "loan" token, comma-name form) rather than `candidate-self` — a $50 cosmetic edge; value
preserved verbatim.
