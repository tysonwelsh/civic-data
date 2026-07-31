# campaign_finance — Magna candidate campaign-finance disclosures

**ACQUISITION-ONLY layer** (source type 6 of `/expand-city-sources`). Raw filings retained verbatim
under `raw/` with a machine-readable `raw/_fetch_log.jsonl`; `index.csv` catalogs every retrieved
artifact against the SCHEMA_SPEC.md §9 contract. **No OCR/vision extraction and no dollar totals are
computed here** — `extraction_method` is `none (raw acquisition; text/OCR/vision deferred)` on every
row. Read `AVAILABILITY.md` for the full coverage/threshold/discrepancy record and `unrecovered.csv`
for the one blocked cycle (2023).

## Scope & the jurisdiction split (this is the whole story)

Magna is a **metro township (2017–2025) → city (2024-05-01, HB35; first city election 2025-11-04)**,
elections administered by the **Salt Lake County Clerk**. Filing jurisdiction — and retrievability —
split by era:

- **Township filings 2016–2021** were filed with the **county** and posted on the SLCo Clerk's
  **static** metro-township-councils page → **50 PDFs** (`source=slco_clerk_static`).
- **2023 (still a township)** moved to the county's **EasyVote** SPA (2022+), which is
  **HTTP-500/auth-gated** → **not retrievable** under polite GET (honest gap; `unrecovered.csv`).
- **2025 (now a city)** files with the **city recorder** and is posted on **magna.utah.gov**, which
  — **unlike Kearns's Cloudflare-blocked site** — is **reachable** (HTTP 200) → **13 city-era
  artifacts** retrieved (`source=magna_city_site`).

Per the metro-township cluster lesson (White City / Kearns builds): these entities are **absent from
`disclosures.utah.gov/Municipal`** — the state tree has zero Magna entries. Do NOT expect Magna there.

## What's in `raw/` (63 PDFs)

- **50 township `*.pdf`** — SLCo Clerk redacted candidate disclosures, 2016 (38) / 2017 (2) / 2019 (4)
  / 2021 (6). All scanned images except the 2019 Pierce form (born-digital template layer).
- **9 city per-candidate `202508_*_primary_v*.pdf`** — 2025 primary disclosures (Mayor: Sudbury,
  Adriano, Romero, White; D2: Olsen, Barney, Rodriguez; D4: George, Hull).
- **3 city bundle `*bundle_v*.pdf`** — 2025 general Oct-7 (v642) + Oct-28 (v643) finalists' reports,
  and the primary-eliminated final disclosures (v644). **Multi-candidate; one artifact = one row.**
- **1 `2025_magna_candidate_coi_forms_v533.pdf`** — 2025 candidate conflict-of-interest packet →
  `filing_type=coi_disclosure`.
- **`_fetch_log.jsonl`** — every fetch (url, status, bytes, sha256, retrieved_utc); the build script
  reads each row's `source_url` from here (never hard-coded).

## index.csv schema

§9 campaign_finance contract prefix (exact, in order):
`date,candidate,office,election_year,filing_type,reporting_period,title,source_url,retrieved_date,format,extraction_method`
then Magna extras (mirrors the Kearns/White City CF schema):
`path,source,date_precision,is_incremental,matched_election_candidate,join_confidence,sha256,notes`.

- **`filing_type`** ∈ `interim` (57) · `summary` (5 — the Dec year-end totals: Peay 2019, Barney/Peel/
  Hull 2021) · `coi_disclosure` (1 — the COI packet).
- **`office`** = `Metro Township Council Seat N` (2016/2017 labels) / `… District N` (2019/2021) /
  `City Mayor` · `City Council District 2/4` (2025) — matched to the era labels in `magna_races.csv`.
- **`format`** = `scanned` (56) / `text` (7: Pierce 2019, Barney+White 2025 primary, 3 bundles, COI).
  `extraction_method` is uniform `none (raw acquisition; text/OCR/vision deferred)` regardless.
- **`date` / `date_precision`** — `county_folder_ym` (2016, year+month from the `/2016_disclosures/`
  path) · `county_month_label_year_ocr` (2017/2019/2021 root files — the page shows only a month; the
  **year was OCR-read from each form's "&lt;YYYY&gt; Financial Disclosure" header**, which corrected 3
  path-guesses to 2021) · `city_primary_cycle` / `city_report_date` / `city_filing_period` (2025).
- **`is_incremental`** = BLANK (deferred) — the Dec `summary` is expected cumulative; do NOT sum a
  candidate's filings, and do NOT sum a bundle row, before the extraction pass. Any dollar total →
  `cycle_totals.py`, never a row sum.
- **`matched_election_candidate`** = UPPER-CASE `magna_races.csv` name where the person is a certified
  winner/runner-up; **`join_confidence`**: `high` (roster winner/runner-up) · `medium` (real candidate
  not in the winner/runner columns — 2016 primary field + Ramos 2021 + Romero/White/Rodriguez 2025).
  BLANK on the 3 bundles + COI (multi-candidate). **No `low` rows** — every filing maps to a candidate
  of record (no Kearns-Geertsen-style phantom).
- **`sha256`** recomputed from disk by the build script.

## Bundles — do not read as one candidate

`202510_…oct07_bundle`, `202510_…oct28_bundle`, and `202508_…primary-eliminated_bundle` are
**multi-candidate PDFs** the city posted grouped by report date. Each is **one index row per file**;
the candidates inside are named in the row `notes` + `AVAILABILITY.md`. Pages are **mixed born-digital
+ scanned**. Brooks Jones (2025 D4, eliminated at primary) has **no per-candidate file** — his filing
lives in the primary-eliminated bundle. Per-candidate split + dollars are the deferred
`/cf-vision-transcribe` → `cycle_totals.py` pass.

## Counts (as-of 2026-07-13)

**63 artifacts** — by year: **2016** 38 · **2017** 2 · **2019** 4 · **2021** 6 · **2025** 13.
By source: **slco_clerk_static** 50 · **magna_city_site** 13. **2023** (D1/D3/D5) is the sole gap —
EasyVote-blocked (`unrecovered.csv`, 3 offices; candidates inferred from the 2026 roster, not certified,
and also absent from the election layer).

## Join to other layers

Join finance ↔ council votes/elections on **person + year + seat/district** — normalize the UPPER-CASE
election names first (e.g. `STEVE PROKOPIS`, `TRISH HULL`, `MICKEY M SUDBURY`). Magna seats are
single-member per cycle, so the join is unambiguous. Mind the **form-of-government seam**: 2016–2021
rows are township council (chair-"Mayor" voted); 2025 rows are the first city era (elected executive
Mayor Sudbury, non-voting). Eric Barney appears as a **2021 D2 winner** AND a **2025 D2 loser** (former
township chair-"Mayor"); Trish Hull spans 2016→2025 (four cycles).

## Rebuild / refresh

`index.csv` is generated from the retained `raw/` PDFs + `raw/_fetch_log.jsonl`:
```
python3 build_magna_cf_index.py      # idempotent; recomputes sha256 + format from disk, reads source_url from the fetch log
```
The SPEC table (year/seat/candidate/period/filing_type/match) is hard-coded from the SLCo Clerk page's
per-candidate grouping + the OCR-verified form years + the Magna city elections page. To refresh:
- **2016–2021 (static county page):** re-harvest anchors from
  `saltlakecounty.gov/clerk/elections/financial-disclosures/metro-township-councils/` (#magna section).
- **2023 (EasyVote):** requires reaching `saltlakecountyut.easyvotecampaignfinance.com`
  (`ecf-api.easyvoteapp.com`) past its HTTP-500/auth-gate — a browser/session fetch, not polite GET.
- **2025 (city site):** re-harvest `magna.utah.gov/161/Elections` DocumentCenter links (reachable).
Fetch new PDFs through `../../.claude/skills/expand-city-sources/scripts/polite_fetch.py` (GET-only,
logged) into `raw/`, extend the SPEC table, and re-run. A later dollar-extraction pass
(`/cf-vision-transcribe` → `cycle_totals.py`) is deferred and OUT OF SCOPE here.

## 2026-07-17 — CF VISION TRANSCRIPTION (2021 + 2025 cycles) — vision/ caches written

Transcribed **13 scanned filings** (2021 township ×6, 2025 city ×7) via `/cf-vision-transcribe`
(Read-tool vision, **$0 Anthropic API**; 5 chunked general-purpose agents, ~50 page-images).
`vision/*.json` = **23 contributions + 40 expenditures itemized**, printed cover TOTALS verbatim.
(2023 is the EasyVote-blocked gap — nothing to transcribe; the 2016/2017/2019 township scans and
the 2025 born-digital text filings/bundles are NOT vision-transcribed — see follow-ups.)

- **Cache contract:** pure `sha1(index_path)[:8].json` + the WJ/midvale vision schema
  (`contributions[]`{date,name,amount,in_kind} · `expenditures[]`{date,recipient,purpose,amount,
  in_kind} · cover totals · `_meta`). **NO structured layer — magna has no `build_finance.py`
  (owner-gated); these are additive caches only**, consistent with the tranche-1 (midvale) pattern.
- **2021 township forms** (6): mostly **cover-total-only** — small below-itemization races, so 0
  itemized rows; the printed lump/threshold totals are captured verbatim (Ramos $0, Barney
  $370.11 on both his interim + year-end summary, Hull $150, Peel $1,500.00). Not a miss — the
  forms print no itemized schedule.
- **2025 city forms** (7): itemized Schedules A/B. Sudbury is the largest ($6,180.05 raised),
  Hull $0, the rest $1,108–$1,408. Where a form omits a Date or Purpose column, that field is
  `null` (honest gap, not fabricated); sub-$50 aggregates go to `contributions_50_or_less` with
  any named sub-$50 donors also itemized (a future build must not double-count).
- **Anti-fabrication:** transcribed exactly as printed — verbatim amounts/typos, illegible → null,
  internal subtotal-vs-total gaps left unreconciled. Cover totals returned verbatim (never summed).
- Backup: `_backups/2026-07-17-wave2/magna/campaign_finance/` (vision/ was greenfield — nothing
  pre-existed).

## 2026-07-18 — STRUCTURED LAYER BUILT (vision-cache reference clone)

`build_finance.py` (family **`vision_cache`**, shared helpers
`scripts/campaign_finance/vision_lib.py` + `driver.py`) now writes the four derived,
regenerable, never-hand-edited CSVs: **`contributions.csv` (23)** / **`expenditures.csv` (40)**
/ **`filing_totals.csv` (62 rows = the full in-scope inventory: 13 vision-transcribed + 49
honest not-transcribed rows with dated reasons)** / **`cycle_totals.csv` (40 candidate-cycles)**.
`validate_finance.py` → **PASS (0 fails, 1 warn)**; the lone WARN is the deliberately
out-of-scope COI packet having no filing_totals row. `scripts/validate_city.py magna_city_council/`
→ **0 FAIL**. Regenerate with `python3 build_finance.py` then
`python3 ../../scripts/campaign_finance/cycle_totals.py magna`.

Key decisions (all evidence-based):
- **Cash-only reconciliation (`reconcile_cash_only=True`) — differs from midvale (False).**
  Magna's county/city C&E covers state TOTAL CONTRIBUTIONS/EXPENDITURES **excluding in-kind**
  (in-kind is a separate "In-Kind and Other Nonmonetary" line). Verified: Romero (Becky Romero
  $680 in-kind → cash-sum $1,258.80 == cover) and Olsen (Cheryl Harding $300 in-kind → cash-sum
  == cover ±$2).
- **Per-candidate regime** (`vision_lib.detect_regimes`, printed by every build): **Barney 2021**
  and **Hull 2021** each filed an interim + a Dec year-end summary that RESTATE the same
  cumulative totals → **cumulative** (latest summary wins, earlier interim marked superseded;
  cycle = $370.11 / $150, not doubled). Every 2025 filer filed a single primary-period report →
  **incremental / group-of-one**. **No `cycle_overrides.csv` needed** — all three 2021
  `summary`-typed filings are genuine cumulative year-end reports (Barney, Hull, Peel).
- **Reconciliation:** 5 of 13 vision filings reconcile both sides (Romero, Rodriguez, Adriano,
  George, Hull-2025); **2 carry verbatim, unadjusted flags** — **Olsen's $2.00** cover-vs-itemized
  gap (both sides) and **Sudbury's $100.00** expenditure cover-vs-itemized gap. The 6 2021
  township caches are **totals-only(no itemization)** (small below-itemization races print a lump
  cover, 0 itemized rows → reconciliation UNKNOWN, never a fabricated mismatch).
- **Ramos 2021** cover `total_expenditures = "Less than $1,000.00"` is a **small-budget-certificate
  THRESHOLD phrase, not a dollar total** — `build_finance.py` records that side as UNKNOWN (blank)
  + a verbatim note, rather than letting `vmoney` coerce it to $1,000 (anti-fabrication).
- **Rodriguez** cache lists his $50 both as an itemized row AND in `contributions_50_or_less`
  (an internal cache double-count) — the build reads **only the itemized schedule**, so it
  reconciles cleanly and nothing is doubled (cache left verbatim, never corrected).
- **`donor_aliases.csv` (3 rows):** Sudbury's three self-funding lines ("Mickey M Sudbury -
  Personal- Shirts / Personal - Expenses… / Candy") were mis-typed `individual` by the tier-1
  classifier (trailing tokens aren't the surname) — curated to **`candidate-self`** with
  per-row evidence → `self_funded_amount` $5,130.05. No `finance_overrides.csv` needed (all
  mismatches stay flagged, never corrected).

### What is NOT in the structured money layer (honest gaps + follow-ups)
- **2023 (D1/D3/D5)** — EasyVote acquisition gap; **no filings exist to build**. Represented
  ONLY in `unrecovered.csv`, never as an index/filing_totals row.
- **49 honest inventory rows** (unknown totals + dated reason, `n_*_rows=0`): **38** 2016
  founding-cycle below-floor township scans; **5** 2017/2019 township scans (deliberately not
  cached this tranche); **2** born-digital TEMPLATE text layers whose figures are
  handwriting-glyph junk to pdftotext (2019 Pierce, 2025 Barney — real money present, not
  machine-readable); **1** clean single-candidate born-digital 2025 report (Maxwell White, cover
  $20/$0); **3** multi-candidate 2025 BUNDLES.
- **FOLLOW-UP (real money left out — report-only):** the 2 Oct general BUNDLES + the
  primary-eliminated bundle contain **machine-readable born-digital** finalist C&E money
  (e.g. Adriano Oct-28 ≈ **$2,713 spent**; Oct-7 ≈ $159 raised / $102 spent). Because one
  artifact = one row and a per-candidate split needs per-candidate transcription (out of scope
  for this structuring pass), the 2025 CYCLE TOTALS reflect **primary-period reports only** and
  understate the general-election period. Queue: vision-transcribe White v571 + the 3 bundles,
  split per candidate. The 2016–2019 scans + the 2 handwriting-template text filings are the
  other vision follow-up.
- Backup of pre-existing files modified this pass: `_backups/2026-07-17-cf-structuring/magna/`.

## 2026-07-19 — GENERAL-BUNDLE TYPED-MONEY TRANCHE (the queued follow-up, DONE)

Closed the queued **general-bundle typed-money tranche** (TODO CF-STRUCTURING (b): "magna 2025
general bundles + White v571"). Vision-transcribed (Read tool, **$0 Anthropic API**; 3 chunked
`general-purpose` agents, ~78 page-images) the **3 multi-candidate 2025 bundles** — v642 (Oct-7
general finalists), v643 (Oct-28 general finalists), v644 (primary-eliminated closings) — plus the
clean **Maxwell White v571** single report, into per-candidate `reports:[...]` caches
(`vision/489b0ca5.json` / `8586d25d.json` / `0a3cfc7e.json`) + `8f3ed514.json` (White). Balance-chain
verified; VERBATIM covers (filer arithmetic left flagged, never corrected).

- **build_finance.py now EXPANDS bundles per candidate.** Each bundle's `reports[]` (one sub-report
  per candidate, `candidate_canonical` = the exact index candidate string) is split into synthetic
  per-candidate filings via a scratchpad expanded-index handed to `driver.run(index_name=...)` —
  the acquisition `index.csv` is UNTOUCHED (still one row per bundle; the derived CSVs gain the
  per-candidate rows). `document_id = sha1(bundle_path | canonical)`.
- **Results:** `filing_totals` **62→73** rows, both-sides-reconcile **5→16**, contributions
  **23→74**, expenditures **40→108**. `validate_finance` PASS (1 WARN = out-of-scope COI, unchanged);
  `validate_city` 0 FAIL.
- **2025 cycle totals now include the GENERAL period** (were primary-only): Sudbury **$10,734.72
  raised / $9,735.34 spent** & Adriano **$4,222.22 / $4,222.22** (Mayor); Olsen **$2,789.64** &
  Barney **$430.65** (D2); George **$1,981.62** & Hull **$30 / $191.26** (D4); Romero **$1,258.80 /
  $1,258.80**; White **$20 / $0**. The 2 pseudo-candidate "(bundle)" cycle rows are GONE.
- **`cycle_overrides.csv` (NEW, 3 rows, per-candidate balance-chain evidence)** — the forms' cumulative
  Column-A/C quirks defeat the generic dedup, so the whole-cycle figures are set from each filer's own
  balance chain: **Sudbury** (oct-07 cover restates his primary Column-A → summing double-counts;
  cycle uses the oct-07 Column-C general period), **Adriano** (oct-28 cover $38.35 EXCLUDES the
  itemized $2,617.48 self-contribution the balance chain proves funds the $2,663.14 mailing),
  **Romero** (v644 closing is a per-period final: repays the $92.76 loan the primary left open →
  generic summary-rule undercounts spent). All three verbatim covers stay flagged in `filing_totals`.
- **Verbatim reconcile flags this tranche (kept, never corrected):** Sudbury oct-07 cover 6180.05 vs
  both-period itemized 8100.05 (Column-A restatement); Adriano oct-28 38.35 vs 2655.83; plus the
  pre-existing Olsen $2.00 / Sudbury-primary $100.00. Barney's Oct general reports use the
  **$500-or-less** simplified option (totals-only, no itemization → reconcile UNKNOWN; read as a
  cumulative $430.65 whole-cycle certificate).
- **Brooks Jones (2025 D4, primary-eliminated) — transcribed, NOT structured:** his v644 section
  ($958.44 self-funded) is in `vision/0a3cfc7e.json` verbatim but had **no acquisition `index.csv`
  row** (he filed no per-candidate PDF), so it was SKIPPED by the build (would fail `validate_finance`,
  candidate ∉ index) and logged. **RESOLVED 2026-07-19 (see below).**
- **Cisco Rodriguez** filed NO v644 closing (his primary v569 is his only 2025 filing — unchanged).
- Backup: `_backups/2026-07-19-lm-wave/magna/campaign_finance/`.

## 2026-07-19 — BROOKS JONES STRUCTURED (the follow-up above, closed)

The queued Jones follow-up is done — he now auto-structures from the cache, a **Jones-only** change
(no other candidate's figures or metadata moved; diff'd before/after on all four derived CSVs).

- **Design decision: membership index row + order-independent expansion, NOT a special-case.** The
  bundle expansion derives candidates purely from each bundle's `reports[]` cache, but every bundle
  candidate must ALSO clear `validate_finance`'s `(candidate,election_year)∈index` gate — a gate the
  other bundle candidates (White, Romero, the general finalists) meet via their **own standalone
  primary index rows**. Jones filed no standalone PDF, so (1) `vision/0a3cfc7e.json`'s Jones
  `candidate_canonical` was set `null → "Brooks Jones"` (the mapping field, not a dollar value — the
  same field White/Romero already carry), and (2) an honest **membership row** for "Brooks Jones" was
  added to `index.csv` pointing at the SAME v644 bundle artifact (identical path/source_url/sha256),
  generated durably by `build_magna_cf_index.py`'s new `BUNDLE_MEMBERS` list. `build_finance.py`
  `_expand` skips membership stubs (a bundle-path row whose candidate is a real name, not a
  `…(bundle)` label) and expands only the canonical artifact row, so the expanded ordering — and
  hence every other candidate's regime/supersession marking — is byte-identical to the pre-Jones build.
- **Jones figures (verbatim from `vision/0a3cfc7e.json`, both sides reconcile):** raised **$958.44**
  (one self-contribution, `candidate-self` → `self_funded_amount` $958.44), spent **$958.44** (MSD
  candidate filing $50.00 + UnionPrintShop signs $748.13 + $160.31). `filing_totals`
  reconciles_contrib/expend **True/True**; `cycle_totals` Brooks Jones 2025 D4 = **$958.44 / $958.44**
  (basis `summary`, 1 filing). document_id `f4368180`.
- **Results:** `filing_totals` **73→74**, both-sides-reconcile **16→17**, contributions **74→75**,
  expenditures **108→111**; cycle-cycles **38→39**. `validate_finance` PASS (1 WARN = out-of-scope
  COI, unchanged); `validate_city` 0 FAIL. The null-canonical skip guard REMAINS for any future
  unmapped bundle sub-report.
- Backup of pre-existing files modified this pass: `_backups/2026-07-19-lm-wave-followups/magna/campaign_finance/`.
