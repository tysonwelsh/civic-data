# campaign_finance/ — Cottonwood Heights City (ACQUISITION layer)

Municipal candidate campaign-finance disclosures for Cottonwood Heights City, completing the
**elections → members → votes** chain (who funded the people casting the votes). **Acquisition-only:**
raw PDFs retained with full provenance; **no OCR/vision extraction and no dollar totals** — those are
deferred (`extraction_method='none (raw acquisition; OCR/vision deferred)'` on every row).

- **Built:** 2026-07-13 · **In-scope cycles:** 2021 (D3/D4/Mayor), 2023 (D1/D2), 2025 (D3/D4/Mayor).
  **Bonus (pre-scope, trivially available):** 2019 (D1/D2), 2017 (D3/D4/Mayor).
- **86 filings, 46 MB, all under `raw/`** (verbatim; each with sha256 + HTTP status in
  `raw/_fetch_log.jsonl`). Fetched GET-only via `scripts/polite_fetch.py`.
- **Format split:** 31 born-digital `text` / 55 `scanned`.
- **Structural reminder:** Cottonwood Heights is a **4-district council + a VOTING Mayor** — the Mayor
  is a candidate/`person` like any district member (max council roll = 5). Mayor filings sit alongside
  the District 1–4 filings; do not treat the Mayor as a non-candidate.

## Sources (full checklist in AVAILABILITY.md)

1. **State — `disclosures.utah.gov/Municipal` → `salt lake_<year>_Cottonwood Heights`**
   (`source=state_lg_municipal_disclosures`, 56 files). The GET-navigable folder tree; files served
   from `municipal.utah.gov` with Windows **backslash** paths → rewrite to https + forward-slash +
   `%20`. Holds **2021, 2023, 2019, 2017**. The **2025 folder only redirects to the city page.**
2. **City elections page** (`source=city_elections_page`, 30 files) —
   `www.cottonwoodheights.utah.gov/your-government/elections`, the "2025 Election Information" table
   of `/home/showpublisheddocument/<id>/<ver>` PDFs (the site edge-403s a bare UA; `polite_fetch.py`
   sends enough headers to get 200). This page holds **2025 only** (rolling window).

Neither source alone is complete: the state tree carries 2017–2023 but not 2025; the city page carries
only 2025. Merging the two gives full in-scope coverage.

## index.csv schema

SCHEMA_SPEC §9 `campaign_finance` contract header first (exact order):
`date,candidate,office,election_year,filing_type,reporting_period,title,source_url,retrieved_date,format,extraction_method,path`
then city-specific extras: `district,source,date_precision,is_incremental,matched_election_candidate,join_confidence,sha256`.

- **`filing_type`** — `statement` (initial / declaration-era financial disclosure statement, incl. 2025
  "initial" + 2019/2023 pre-primary), `interim` (dated pre-election reports: 2021 pre-general
  candidate statements, 2023 Oct-24 reports, 2025 Oct-7/Oct-28, 2019 Oct/Sept), `summary` (cumulative
  year-end **Final** reports: 2021 Final, 2023 Final, 2025 Dec-4, 2019 Dec-5), `conflict_of_interest`
  (the 6 candidate COI forms in the 2025 city packets). No closed enum — these mirror the Riverton
  sibling's extended vocabulary.
- **`date` + `date_precision`** — best filing-date estimate, precision flagged honestly:
  `filename_filing_date` (an exact date in the filename, e.g. 2023 `10.24`, 2019 `Dec 5`),
  `label_report_date` (2025 Oct-7/Oct-28/Dec-4 table columns), `label_month` (2019 "Oct 2019" →
  first-of-month), `cycle_anchor_general_election_day` / `cycle_anchor_primary_election_day` (undated
  statements anchored to the election day — 2021 general 11-02, 2023 general **11-21** / primary
  **09-05** [Utah shifted 2023 to Sept 5 / Nov 21], 2019 general 11-05 / primary 08-13, 2025 general
  11-04), `statutory_year_end_deadline` (undated year-end Finals → the ~Jan-10 filing deadline). **No
  internal report dates were read** (acquisition-only); dates come from filenames/table labels only.
- **`matched_election_candidate` / `join_confidence`** — the UPPER-CASE
  `election_results/cottonwood_heights_races.csv` winner/runner-up name for that person (`high`), or
  blank + `none` when the person is a mid-field candidate not named in `races.csv` (which stores only
  winner + runner-up names) or is otherwise absent (McHugh — see the 2019 flag). `none` here is NOT a
  data gap.
- **`is_incremental='no'`** on every row — Utah municipal statements are cumulative-to-date (see the
  double-count trap).

## Linkage / analysis rules

- **Join to elections/members on PERSON, normalizing names.** Election names are UPPER-CASE; filenames
  vary: Weichers filed "Michael **Wiechers**" / "Mike Weichers - **Fina** Financial Report" → `MIKE
  WEICHERS`; Jen **Cottam/Cottham** → `JEN COTTAM`. The same person recurs across cycles (Weichers:
  Mayor 2021 + 2025; Newell/Birrell/Kim: 2021 + 2025).
- **Roster turnover to respect** (see AVAILABILITY.md): the **Weichers → Bennion** mayoral turnover
  (2025 — both filed full 2025 packets), and the **Petersen → Holton** District-1 mid-2023 appointment
  (Petersen's finance is 2019; Holton's is 2023; the appointment itself files no report — honest gap).
- **DOUBLE-COUNT TRAP** — candidates file several cumulative reports per cycle. Do **NOT** sum a
  candidate's filings for a cycle total; use `scripts/campaign_finance/cycle_totals.py` at extraction
  time. See AVAILABILITY.md.
- **Discrepancy flags** (documented in AVAILABILITY.md, NOT applied to `election_results/`): the
  **2019 D1 primary** implied by McHugh's + Case's "PRIMARY" disclosures (McHugh absent from
  `races.csv`); Scott **Bracken** as the un-named 3rd 2023 D2 primary candidate; Tonia **Dalton** as a
  2017 eliminated primary filer.

## Build / regenerating / extending

Helper scripts live **in this directory** (unique `ch_cf_` prefix):
- `ch_cf_parse_links.py` — discovery: extract `(anchor_text, href)` from a saved CivicEngage HTML page
  (maps the opaque `showpublisheddocument` ids to candidate/report labels).
- `ch_cf_build_batch.py` — emits the `polite_fetch --batch` `url,name` lists (`batch_state.csv`,
  `batch_city.csv`): rewrites the state backslash paths → https + `%20`; names the 2025 city docs from
  the discovered id→label map.
- `ch_cf_build_index.py` — **builds `index.csv`** (idempotent). Derives `source_url` + `sha256` from
  `raw/_fetch_log.jsonl` and `format` (text vs scanned) from each PDF via pymupdf; all human
  classification (candidate/office/district/filing_type/period/date) is the explicit per-file table in
  the script. Re-run after re-fetching: `python3 ch_cf_build_index.py`.

Re-fetch: `polite_fetch.py --out raw --batch batch_state.csv --now 2026-07-13T00:00:00Z` (state) and
`... --batch batch_city.csv --referer <elections page> ...` (city). Retain `raw/_fetch_log.jsonl`.

Validate: `python3 .claude/skills/expand-city-sources/scripts/validate_dataset.py
cottonwood_heights_city_council/campaign_finance` — **PASS** as of 2026-07-13.

This layer feeds `cities.db` `document`/`cf_*` on the next `build_cities_db.py` (run by the
orchestrator, not here). Extraction to `filing_totals.csv` / `cycle_totals.csv` is future work.

## 2026-07-17 — CF VISION TRANSCRIPTION (tranche 1, 2025 cycle) — vision/ caches written

Transcribed the **2025-cycle scanned C&E filings** via `/cf-vision-transcribe` (Read-tool
vision, **$0 Anthropic API**). **18 of 30** scanned 2025 filings cached (455 contributions +
218 expenditures). The **12 excluded** are `statement` (initial financial disclosure) +
`conflict` (conflict-of-interest disclosure) filings — **not C&E reports by design** (no
contributions/expenditures); out of scope, not a gap.

- **Cache contract (provisional-standard, no build yet):** WJ `_did8` filenames
  (`sha1(index_path)[:8].json`) + WJ vision schema; each cache has a `_meta` block for lossless
  re-keying. CH form uses the standard **$50-or-less** aggregate line → `contributions_50_or_less`;
  prints **no beginning balance** (`beginning_balance` null throughout); Form B has **no purpose
  column** (payee+purpose combined — split on "/" where present, else `purpose` null).
- **STRUCTURING PENDING:** no `build_finance.py` yet — additive caches only; structuring build
  is owner-gated later-tranche work, not scaffolded here.
- **DOUBLE-COUNT TRAP (critical for the build):** the interim/summary filings are **cumulative
  restatements** — each successive filing restates the full period from 6/6/2025 and appends new
  rows (e.g. Bennion 86→100→106 contributions across Oct-7/Oct-28/Dec-4). `cycle_totals` must take
  the **final summary only** (or dedup), never sum the filings. Same pattern for Newell/Weichers
  Oct-28 supersets of Oct-7.
- **Duplicate scan NOT in index (needs a dedup flag):** Prazen `df89b7c3` (final-dec-4) is an
  identical scan of `4779b80c` (interim-oct-28) — CH index has no `duplicate_of` column (the
  `sha256` column can confirm); flag when a build is created.
- **NEEDS_REVIEW — Birrell interim `b5575361`:** cover `total_expenditures` prints **$513** but
  Form B itemizes ~**$5,363** — transcribed verbatim (cover + all 8 lines), not reconciled.
- Verbatim-preserved defects: a struck "Scott McCarty DELETE – DUPLICATE!" row (amount
  "X  100.00") on two Bennion filings (downstream should exclude); cross-filing amount variances
  (Horton/Welch 96.24 vs 94.80); date typos "9/62025", "8/11//2025", "10//2025", "10/62025", etc.
- Backup: `_backups/2026-07-17-cf-vision-t1/cottonwood_heights/` (greenfield — nothing pre-existed).

## 2026-07-17 — tranche-2 vision + `duplicate_of`
All 2021/2023 scanned filings now have `vision/` caches (30 total; see AVAILABILITY.md
for the honest limits + the four Bracken/Daurelle metadata corrections). `index.csv`
carries a trailing **`duplicate_of`** extension column (blank = not a duplicate; else
the kept row's `path`). The structured `build_finance.py` layer remains owner-gated.

## 2026-07-18 — STRUCTURED CF LAYER BUILT (`build_finance.py`, the vision-cache wave)
Built the derived money layer per `scripts/campaign_finance/SCHEMA.md` + `VISION_CITIES_ROLLOUT.md`
(family **`vision_cache`**, shared `vision_lib.py`; reference impl = midvale). Regenerate with
`python3 build_finance.py`; **never hand-edit** `contributions.csv` / `expenditures.csv` /
`filing_totals.csv` — corrections go to `cycle_overrides.csv` / `finance_overrides.csv` /
`donor_aliases.csv`. Cycle rollup: `python3 scripts/campaign_finance/cycle_totals.py cottonwood_heights`
(reads `cycle_totals.csv` — NEVER sum `filing_totals` yourself).

- **Scope:** 86 index rows → **74 in-scope** C&E filings; **12 excluded** by `in_scope_fn`
  (the 6 **2025 `statement`** initial financial-disclosure statements + 6 **`conflict_of_interest`**
  forms — not C&E reports, no contributions/expenditures). The 2017/2019/2023 `statement`-typed
  rows ARE pre-primary C&E reports and stay in scope.
- **Rows:** **1,170 contributions / 550 expenditures.** Reconcile: **21 both-sides reconcile**,
  15 flagged/partial (genuine source facts — the sub-$50 aggregate line printed separately from
  the Form-A cover; Birrell 2025 Oct-28 filer error; Newell 2025 +$75 cover<itemized), 1
  totals-only-unknown (Cottam Oct-24 cover-only disclosure), **37 inventory-only** (no cache).
- **37 caches consumed = 30 (tranches 1-2) + 7 NEW vision (2026-07-18):** the three CLEAN typed
  text reports the owner flagged — **Cottam** (schedule 10-24, pre-general, final), **Holton**
  (pre-general, final), **Kraan** (interim, final) — Read-tool vision, **$0 API**; all 7 reconcile
  both-sides True (e.g. Holton final 35,170 / 35,166.91; Cottam final 15,631.46 / 11,675.42; Kraan
  final 11,383.91).
- **37 inventory-only (`empty_result`, honest no-cache):** 2017 ×4 + 2019 ×12 (below-2020-floor
  BONUS acquisitions, midvale convention) + **2021 ×18 + 2023 Hyland ×3 (`format=text` whose COVER
  totals are handwritten/garbled in the text layer — Schwartz, Wiechers, Evans, Hanson, Kim, Newell,
  Rawlings, McShaffrey, Walker, Hallbeck, Birrell-final, Hyland — their typed itemization carries
  real money; a vision tranche is the honest follow-up, NOT dropped-as-zero).**
- **`reconcile_cash_only=False`** (evidence-based): CH cover TOTALs INCLUDE in-kind at face value
  on the expenditure side (Rawlings-amended, Newell-2021-final reconcile all-sum directly); the one
  cash-only cover (Daurelle contrib) is caught by the driver's per-filing alt-convention fallback +
  noted. The convention is genuinely mixed; the fallback documents each.
- **PER-CANDIDATE REGIMES** (eyeballed against the filings): CH 2025 filers SPLIT — Bennion, Kim,
  Newell restate cumulative snapshots (all rows restart from the cycle open; Bennion 86→100→106);
  **Weichers + Birrell file PER-PERIOD** (disjoint date ranges); Prazen cumulative w/ a duplicate.
  2023: Cottam, Holton, Daurelle cumulative; Bracken per-period (pre-/post-primary). Kraan 2021
  cumulative.
- **4 `cycle_overrides.csv` rows (all 2025, evidence-cited):**
  - **Prazen** → 3471.64 / 3556.64: Dec-4 `df89b7c3` is the `duplicate_of` re-upload of the Oct-28
    interim `4779b80c` (superseded); Oct-28 corrected Oct-7 (dropped a $507.18 self-gift). His
    GENUINE Dec-4 final is an ACQUISITION GAP (not on file).
  - **Newell** → 7465.00 / 4800.86: regime mis-detection (truly cumulative; the tiny 7615→7465 dip
    tripped `detect_regimes` to `incremental`). Cycle = the Dec-4 summary cover.
  - **Weichers** → 33700.00 / 33837.50 and **Birrell** → 10793.00 / 3807.00: per-period filers whose
    Dec-4 "summary" is itself a period report (the midvale precedent) — cycle = SUM of the three
    periods' stated covers. Birrell's Oct-28 cover-vs-Form-B discrepancy ($513 vs ~$5,363, a retained
    filer error) makes her summed spend a documented LOWER BOUND.
- **Validation:** `validate_finance.py` → **PASS (0 fail, 12 warns** = the 12 excluded statement/
  conflict rows, expected); `scripts/validate_city.py` → **24 PASS / 2 WARN / 0 FAIL** (the 2 WARNs
  are pre-existing `provenance` extension-column notes, unrelated to CF). Backups of the modified
  CLAUDE.md/AVAILABILITY.md/index.csv in `_backups/2026-07-17-cf-structuring/cottonwood_heights/`.
- **FOLLOW-UPS (report-only, not TODO-edited):** (1) vision-transcribe the 21 remaining 2021/2023
  `format=text` filings whose typed itemization carries real money (18 2021 + Hyland 2023 ×3) — a
  clean tranche; (2) Prazen's genuine 2025 Dec-4 final is an acquisition gap (recover from the
  recorder if needed); (3) the 2017/2019 below-floor bonus scans remain inventory-only.

## 2026-07-19 — TYPED-MONEY VISION TRANCHE (the 21 2021/2023 `format=text` filings — follow-up #1 DONE)
Vision-transcribed the 21-filing tranche flagged in the 2026-07-18 FOLLOW-UPS via
`/cf-vision-transcribe` (Read-tool page-image vision, **$0 Anthropic API** — Claude Code
allotment). These are `format=text` filings whose **cover TOTALS were handwritten/garbled in the
text layer** while their typed Form-A/Form-B itemization carried real money; they had been honest
`empty_result` inventory-only rows. Chunked across 7 parallel general-purpose agents (≤15
page-images each, disjoint filings), then ONE orchestrator rebuild.

- **Scope:** **18 2021** (`format=text`: Rawlings interim+final, McShaffrey, Schwartz, Timothy
  Hallbeck, Kim ×3, Birrell final, Walker, Newell interim+amended, Evans ×2, Hanson ×2, Weichers
  ×2) **+ 3 Hyland 2023** (interim 10-24, pre-general, year-end final). The other 16 no-cache
  in-scope rows (2017 ×4 + 2019 ×12) are the below-2020-floor BONUS scans — DELIBERATELY left
  inventory-only (midvale convention), NOT part of this tranche.
- **Caches: 37 → 58** (`vision/<sha1(index_path)[:8]>.json`, `vision_cache` family). Queue was
  NOT stale — all 21 genuinely lacked caches at start.
- **Rows: contributions 1,170 → 1,605 (+435); expenditures 550 → 1,067 (+517).**
- **Both-sides reconcile: 21 → 29 (+8).** The 8 new both-sides-clean: McShaffrey, Timothy
  Hallbeck, Newell interim, Newell amended, Birrell 2021 final, and all 3 Hyland 2023.
- **13 of the tranche stay FLAGGED — all GENUINE source facts, verbatim, never "fixed":**
  - **≤$50-aggregate-excluded-from-cover** (the CH filer-arithmetic quirk: the handwritten cover
    line-1 total is the Form-A itemized total MINUS the `contributions_50_or_less` aggregate):
    Kim ×3 (dC=$65), Hanson ×2 (dC=$330), Weichers ×2 (dC=$335.51/$335.41), Newell final (dC=$714).
  - **in-kind-excluded-from-cover** (the separate "InKind Donations" schedule, $3,055, not in the
    Form-A cover): Evans interim+final (dC=$3,055 each).
  - **incremental-final-vs-cumulative-cover:** Rawlings final (the year-end form itemizes only
    post-interim activity while its cover restates the cumulative cycle) — both sides flagged.
  - **no Form A page in the PDF:** Rawlings interim (totals-only contrib; the Form-B page carries
    reimbursement lines the cover expense total excludes) — expend flagged.
  - **filer arithmetic:** Walker interim (cover 646.90/696.90 vs itemized 646.00/666.00);
    Schwartz interim (5 itemized rows 1,259.16 vs cover 1,219.16, dC=$40 — spot-check).
- **cycle_totals.csv — previously-$0 2021 candidates now carry real money** (all basis-noted;
  read `cycle_totals.csv`, NEVER sum `filing_totals`): Hanson 0→11,199.89/10,256.46; McShaffrey
  0→64.69/64.69; Kim 0→5,471.02/5,554.38; Walker 0→646.90/696.90; Schwartz 0→1,219.16/1,219.16;
  Evans 0→18,336.22/18,336.22; Weichers 0→25,662.35/21,871.89; Timothy Hallbeck 0→0.00/89.00;
  Rawlings 6,896.01/6,465.19→6,946.44/7,065.19 (refined to the cumulative final cover); Newell
  6,808.28/5,273.71 (unchanged, now vision-backed).
- **2 NEW `cycle_overrides.csv` rows (per-period filers, evidence-cited — the 2025-Birrell/Weichers
  precedent):**
  - **Ellen Birrell 2021** → 18,677.00 / 18,756.00: two DISJOINT-period reports (interim 8/20-10/24;
    final 10/29-11/30); the generic sum-interim basis dropped the final's period. Balance chain
    verified (interim end 1864 = final begin, cover margin "Balance from 10/26/21: $1864";
    1864+100-1648=316). Cycle = SUM of stated covers (18577+100 / 17108+1648). No in-kind/overlap.
  - **Suzanne Hyland 2023** → 8,514.87 / 7,430.88: three DISJOINT-period reports (pre-general
    6/7-8/23; interim 8/29-10/19; final 11/16-12/14); generic max-mixed basis undercounted spend
    (took final's 3,838.55 only). Cycle = SUM of stated covers (2281.55+5693.32+540 /
    2081.30+1511.03+3838.55). The two Scott Bracken $540 in-kind City Journal ads are DISTINCT
    (dated 9/23 and 11/16 — separate ads), NOT a double-count.
- **Inventory-only (`empty_result`) now = 16** (2017 ×4 + 2019 ×12 below-floor bonus only).
- **Validation:** `validate_finance.py` → **PASS (0 fails, 12 warns** = the 12 excluded
  2025 statement/conflict rows, unchanged); `scripts/validate_city.py` → **24 PASS / 2 WARN / 0
  FAIL** (the 2 WARNs are the pre-existing `provenance` extension-column notes, unrelated to CF).
- **Cost: $0 Anthropic API** (Read-tool vision on the Claude Code allotment).
- Backups: `_backups/2026-07-19-lm-wave/cottonwood_heights-cf/` (pre-change contributions/
  expenditures/filing_totals/cycle_overrides + CLAUDE.md/AVAILABILITY.md + the 37 pre-existing
  `vision/` caches).
- **Remaining follow-ups:** Prazen's 2025 Dec-4 final = acquisition gap (unchanged); the
  2017/2019 below-floor bonus scans stay inventory-only by convention (unchanged).
