# campaign_finance/ — Logan municipal candidate financial disclosures

Additive dataset built by the `expand-city-sources` skill (**Source 6**), as-of
**2026-07-05**. Does **not** modify any existing dataset. Completes the
**elections → members → votes** chain: who funded the candidates whose roll-call votes
live in `../meeting_minutes/` and `../planning_commission/`, and whose wins are in
`../election_results/`.

## What this is
**45 municipal campaign financial statements** (Utah "Financial Disclosure Report" forms)
filed by Logan **Mayor + City Council** candidates: **38 for 2025** (13 candidates × up to
5 statutory deadlines) and **7 for 2021** (5 candidates). All are **scanned handwritten
forms**. Raw PDFs retained verbatim in `raw/<year>/`; an OCR text sidecar per filing in
`text/<year>/`; provenance in each `raw/<year>/_fetch_log.jsonl`.

This directory is BOTH the filing-level document archive + index AND (as-of **2026-07-06**)
a **structured contribution / expenditure / filing-totals layer** — see "## Structured layer"
below. The raw PDF remains the authoritative record; the structured CSVs are DERIVED and every
figure is reconciled or honestly flagged, never asserted beyond what the form prints.

## Coverage (see `AVAILABILITY.md` for the full source log)
| Cycle | Retrieved | Status |
|---|---|---|
| 2025 | 38 / 38 | **Complete** — live on the city site. |
| 2021 | 7 / 8 | Wayback recovery; Garrity Oct-26 unrecoverable; Lopez never posted one. |
| 2023 | 0 / 21 | **Unrecoverable** — Wayback holds only dead redirects to a 404 CDN. |
| 2019 | 0 | **Not published online** by the city. |

24 known-missing filings + gap reasons: **`unrecovered.csv`**.

## Where the data comes from
Logan self-hosts on the **city recorder's election page**
(`loganutah.gov/government/mayor_s_office/election.php`, Revize CMS). The state
(`disclosures.utah.gov`) and county do **not** host Logan candidate PDFs; Logan does
**not** use EasyVote.
- **2025** — live page, `/departments/admin/council/<Name> <Month D, YYYY>.pdf`. Fetched direct.
- **2021** — legacy `loganutah.org` (now 404). Recovered from the **Wayback Machine**
  (`web/<ts>id_/<original-url>`), enumerated via the Wayback **CDX** API.

## Layout
```
raw/
  2021/  2025/          the filing PDFs, names <YYYYMMDD>_<orig-filename> (report deadline)
  2021/ 2025/ _fetch_log.jsonl   provenance (url, http status, bytes, sha256, retrieved_utc)
  2023/  _fetch_log.jsonl only   documents the failed 2023 fetch attempts (0 bytes recovered)
text/
  2021/ 2025/  <same-basename>.txt   OCR sidecar per filing (tesseract; lossy; header-labeled)
index.csv                one row per retrieved filing (schema below)
unrecovered.csv          24 known-missing/never-published filings + reason
build_index.py           regenerates index.csv from batch/manifest.json + files on disk
batch/manifest.json      the candidate→url→file→period manifest (build input)
AVAILABILITY.md          every host/query tried, per-cycle coverage, discrepancies
```

## `index.csv` schema
Required minimum columns (`date,title,source_url,retrieved_date,format,extraction_method`)
plus source-specific columns:

| column | meaning |
|---|---|
| `date` | statutory **report deadline** (`YYYY-MM-DD`), parsed from the filename — not the exact filing moment. |
| `candidate` | filer name as published (mixed case; e.g. "Holly H Daines" vs "Holly H. Daines" across periods — same person, resolved by the join). |
| `office` | `Mayor` / `Council`, assigned from the election-page section headers + `election_results`. |
| `election_year` | 2021 / 2025. |
| `filing_type` | `interim` (pre-primary / pre-general deadline, 31) or `summary` (post-primary "eliminated" + year-end, 14). |
| `reporting_period` | e.g. "Before Primary (Aug 5)", "Before General (Oct 28)", "Year-End Summary (Dec 4)". |
| `title` | human label incl. the report period. |
| `source_url` | the **original** city URL (`loganutah.gov` 2025 / `loganutah.org` 2021), not the Wayback wrapper. |
| `retrieved_date` | 2026-07-05. |
| `format` | `scanned` (all — handwritten form images). |
| `extraction_method` | `ocr_tesseract` (all). |
| `path` | repo-relative path to the retained PDF under `raw/`. |
| `amended` | `no` (no amendments in the recovered set). |
| `matched_election_candidate` | canonical `election_results` name this filer joins to. |
| `join_confidence` | `exact` (all 45 — normalized name+year match). |

## Join to `election_results/`
Filings join to `../election_results/logan_results_by_candidate.csv` by **normalized
(name, year)** (Logan council is at-large — no district key). Names are normalized (UPPER,
punctuation stripped, lone middle initials + suffixes dropped). **All 45 filings join
exactly; 18/18 distinct (year,candidate) pairs matched — 100%.** From a winner's row you
reach their council roll-call votes in `../meeting_minutes/all_votes.csv` (join by person;
case-fold — finance is mixed case, minutes say "Councilor <Lastname>").

## Caveats / do-nots
- **Amounts now exist in the structured layer** (`contributions.csv` / `expenditures.csv` /
  `filing_totals.csv`, DERIVED — see "## Structured layer"). Quote only rows/filings that
  reconcile (`extraction_confidence` ≥ medium, `needs_review=0`); a flagged figure stays
  `low`+`needs_review` and the **raw PDF is authoritative**. OCR sidecars in `text/` are lossy
  handwriting OCR, for search/screening only.
- **Dates are report-deadline proxies**, not exact filing timestamps.
- **2023 is empty and 2019 was never published** — this is honest source reality, not an
  extraction failure (`AVAILABILITY.md` + `unrecovered.csv` prove what was checked). Do
  not infer a candidate "didn't file" from absence here.
- **Ernesto Lopez has a 2025 filing but no 2021 one** — the city never posted his 2021
  statement (flagged, not fabricated). Amy Z. Anderson is the only 2021 council filing
  recovered.
- **Additive only.** This dataset never edits `election_results/` or any other layer.
  Discrepancies (Lopez 2021, 2023 gap, 2019 gap) are flagged in `AVAILABILITY.md` for a
  future election-record review, not corrected in place.
- **Utah law context:** municipal candidates file under **Utah Code 10-3-208**; the city
  recorder hosts/enforces, which is why the state and county sites don't hold Logan's PDFs.

## Rebuild
`python3 build_index.py` (reads `batch/manifest.json` + the files present in `raw/`; skips
any manifest entry whose file is missing; re-joins to `election_results`). Re-fetch raw
via `.claude/skills/expand-city-sources/scripts/polite_fetch.py` (2025 from the live city
URLs in `index.csv`; 2021 from the Wayback `web/<ts>id_/<source_url>` captures logged in
`raw/2021/_fetch_log.jsonl`).

## Structured layer (contributions / expenditures / filing_totals) — as-of 2026-07-06

Additive, DERIVED money layer built by the shared framework in `scripts/campaign_finance/`.
Contract: `scripts/campaign_finance/SCHEMA.md`. Rebuild: `python3 build_finance.py` (idempotent).
Validate: `python3 ../../scripts/campaign_finance/validate_finance.py .` → **PASS** (0 fails).

- **contributions.csv** 309 rows · **expenditures.csv** 166 rows · **filing_totals.csv** 45 rows.
- **SCOPE — all 45 filings are in-scope campaign C&E reports** (Logan hosts no separate COI genre).

### Form family — `utah_standard_form` REUSED (Orem's family, unchanged)
Logan files the **same statutory Utah municipal "Financial Disclosure / Report of Contributions
and Expenditures" form (UCA 10-3-208)** Orem uses, so it **reuses `families/utah_standard_form.py`
UNCHANGED** — the shared family was NOT edited (Orem re-validates identically; Nephi/Vineyard
reuse it next). Logan's label/layout drift is handled entirely through **`meta["form_opts"]`**
overrides in `build_finance.py`:
- **No printed section TOTAL line.** Unlike Orem's Cash/In-Kind/Cash-Exp subtotals, Logan prints
  the totals only in a numbered COVER block (2025: `1a` under-$500 aggregate · `1b` itemized
  $500+ = Form "A" total · `2a`/`2b` the expenditure pair; 2021: `1` combined <$500 aggregate ·
  `2` itemized contributions · `3` itemized expenditures). So the **numbered block is the
  reconciliation anchor**: `l1←1b`, `l2←1a`, `l3←2b`; `stated_contrib = 1b+1a` (the family's
  headline-fallback already sums `l1+l2`), `stated_expend = 2b` (2a folded in via vision, below).
- **Section headers sentineled off** (`sec_cashc/inkind/cashe = (?!)`, never match) **on purpose**:
  Logan's itemized "Form A/B" amounts are handwritten WITHOUT a `$` sign, and the shared money
  tokenizer only accepts a `$`-anchored token (anti-fabrication). Detecting a section but reading
  0 `$`-rows would make the family coerce that section's total to $0 and **falsely reconcile a real
  filing as nil**; suppressing detection forces the correct cover-total anchor + 0 OCR rows → the
  filing flags → vision supplies the rows.

### Modes — OCR throughout + vision escalation (all 45 are handwritten scans)
- **OCR-only pass reconciles 0/45** — expected: every filing is a handwritten scan whose cover
  totals OCR to garbage (`"S sities OL)"`) and whose `$`-less itemized rows are unreadable. So the
  gated vision pass is the **primary itemization path** here (a much higher vision rate than Orem's
  30/50 — handwriting is the hardest OCR).
- **Vision (GATED):** `logan_vision_extract.py` renders each flagged filing with `pdftoppm -jpeg`
  (150 DPI) into a **working dir** (`vision/_tmp`, never `/tmp`), model **`claude-sonnet-5`**,
  strict "transcribe EXACTLY / mark illegible null / never infer" prompt; transcriptions cached to
  `vision/<doc8>.json`, fed back through the SAME reconciliation via the driver `rows_override_fn`
  (`extract_method=…/vision`). **45 of 45 filings vision-processed** (44 first run + 1 retried after
  a transient SSL EOF), **123 pages, ≈$1.78 total** (~390k input + ~39k output tokens, Sonnet list
  price). One documented build-side normalization: a STATED total vision read as negative (the form's
  dotted-leader "......$ 1,664.81" caught as `-1664.81`) is sign-normalized to its magnitude (a
  campaign total is non-negative by definition) — STATED totals only, never a row amount; noted in
  `filing_totals.notes`. This recovered 2 Melissa Dahle filings.
- **Final: 36 of 45 reconcile both sides.** The **9 honest residual flags** (all `low`+`needs_review`,
  nothing guessed): **4 Ernesto Lopez** filings (he reported contributions **NET of Venmo fees**;
  the itemized rows keep the true GROSS the donor gave, so itemized − stated = the fee total, e.g.
  Oct 28 Δ$29.03 = exact Venmo fees — a real filer discrepancy, not an extraction error); **Gail Yost
  Aug 5** + **Brian Seamons Oct 28** (a small under-$500 aggregate stated with no itemization → the
  aggregate is recorded in the note, NOT synthesized as rows → contrib side is honestly "unknown");
  **Alanna Nafziger Aug 5** (Δ$80) and **Katie Lee-Koven Oct 28** (Δ$0.09) cent/small handwriting
  misreads; **Dee Jones 2021 Aug 3** (badly degraded handwritten 2021 form). All raw-PDF-authoritative.

### Dedup — MIXED, per-candidate (empirically determined; do NOT assume one rule)
Logan filers are **not internally consistent**, so `is_incremental` is set **per candidate-cycle**
(`_classify_modes`, from consecutive-report contribution-row overlap), not as a city constant:
- **Predominant = INCREMENTAL** (`is_incremental=True`, 188 rows) — 7 of 9 traceable multi-report
  filers (Nafziger, Seamons, Dahle, Mark A. Anderson, Roesberry, Molitor, Dee Jones-2021) report
  only that period's new, non-overlapping activity (overlap 0.00 — matches the form's per-period
  "Balance at the end of THE REPORTING PERIOD"); a cycle total is the **SUM** of their periods.
- **Exception = CUMULATIVE** (`is_incremental=False`, 121 rows) — exactly **2 filers, Ernesto Lopez
  and Katie Lee-Koven**, re-list the entire cycle-to-date every period (overlap 1.00; row counts
  grow 9→11→14→15 / 14→15→22→21); a cycle total is the **LATEST** report, NOT a sum.
- Because no single global rule is correct, **`dedup_mode=None`** (no uniform supersession is
  asserted). A cross-cycle total query MUST honor per-filing `is_incremental` (sum where True,
  take-latest where False); a blanket sum-or-latest is wrong for ~⅓ of filers.

### donor_type distribution (309 contribution rows)
individual 260 · candidate-self 19 · **unknown 12** · family-of-candidate 8 · pac 5 · business 3 ·
anonymous 2. **18 in-kind** rows. **0 blank-donor rows** (every transcribed row carries a name; the
12 `unknown` are single-token / joint slash-names the conservative classifier won't force).
`donor_aliases.csv` + `finance_overrides.csv` are header-only (no curated overrides needed).

### Hand-verification (5 filings, line-by-line vs the raw PDFs, 2026-07-06 — all vision)
| filing | check | result |
|---|---|---|
| Brian Seamons — Before Primary (Aug 5) | 1 contrib + 1 expend | ✓ BRIAN SEAMONS $11,210.81 = 1b; SPRINT IMAGE $11,210.81 = 2a; both reconcile |
| Melissa Dahle — Before General 2 (Oct 28) | 4 contrib (1 in-kind) + 1 expend | ✓ Σ $1,750.00 = 1b (incl. in-kind Mike Johnson Photography $300); Sky Mail $1,664.81 = 2b; source literally prints `$ -1664.81` (balance $85.19 ⇒ magnitude) → sign-normalized; both reconcile |
| Katie Lee-Koven — Year-End (Dec 4), CUMULATIVE | 21 contrib (2 pages) + 15 expend | ✓ Σ contrib **$2,521.91 = 1b**; Σ expend **$2,490.51 = 2b**; balance $31.40 checks; both reconcile |
| Amy Z. Anderson — 2021 Before General (Oct 26) | 19 contrib + 10 expend | ✓ 19 rows Σ **$4,210.81 = printed "Total cash and in-kind"** exactly; family-of-candidate (Allan Anderson), anonymous ×2, business (CV Realtors) all classified right |
| Ernesto Lopez — Before General 2 (Oct 28), FLAGGED | Venmo+cash ledger vs cover | ✓ gross $1,560.00 vs candidate's **net-of-fee** stated $1,530.97; Δ$29.03 = exact Venmo fees → **honestly flagged** (not an error); expend $1,507.78 reconciles |

### Robustness notes for the family before Nephi / Vineyard reuse it
- **`utah_standard_form` generalized cleanly to Logan via `form_opts` alone** — the section-header
  sentinel + numbered-headline-anchor pattern is the reusable recipe for any Utah-standard form that
  prints totals in a numbered cover block instead of per-section TOTALs. No family edit was needed
  or made; Orem re-validates byte-for-byte (1011/806/91).
- **Handwritten-scan corpora belong in vision, not OCR** — Logan's 0/45 OCR reconcile rate shows the
  `$`-anchored tokenizer (correctly) reads nothing from `$`-less handwriting; plan for a ~100% vision
  rate on a handwritten city and budget ~$0.04/filing.
- **Two build-side hooks live in `build_finance.py`, NOT the family** (so Nephi/Vineyard can copy or
  drop them): (a) STATED-total sign normalization for the dotted-leader-as-minus artifact; (b) the
  empirical per-candidate `is_incremental` classifier for mixed cumulative/incremental filing.
- **Net-vs-gross is a real Utah phenomenon** (Venmo/PayPal filers may report net-of-fee totals) —
  keep the GROSS donor amount and let it flag; do not silently subtract fees to force reconciliation.

### Rebuild / correct
`python3 build_finance.py` (idempotent; re-reads `vision/*.json`, never re-calls the API for a
cached filing). Re-run vision for a specific filing: delete its `vision/<doc8>.json` and run
`python3 logan_vision_extract.py [<doc8> …]`. Corrections → `finance_overrides.csv` /
`donor_aliases.csv` (never hand-edit the derived CSVs).
