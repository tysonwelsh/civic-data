# campaign_finance — Orem City candidate campaign-finance disclosures

Additive dataset completing the **elections → members → votes** chain for Orem: *who
funded the people casting the council votes.* **91 filings, 23 candidates, cycles 2023 &
2025 + sitting-member annual reports (2021 cohort)**, all from **Orem's own election page**
(`orem.gov/elections/`). Read `AVAILABILITY.md` for the full source hunt (EasyVote, state,
county, Wayback) and the honest 2019/2021 gaps. **Additive only** — this directory never
modifies `election_results/` or any other dataset.

## What this is

Each file under `raw/` is an Orem City candidate **campaign financial statement** (report
of contributions & expenditures, UCA 10-3-208), as the city published it. These are the
*campaign*-finance reports — **not** the personal conflict-of-interest (COI) disclosures,
which share the city page but are a separate genre and are **excluded** (listed in
`AVAILABILITY.md`).

## Layout

- `raw/*.pdf|.jpg|.jpeg` — the 91 filings, verbatim. Filename `YYYYMM_<original>` where
  `YYYYMM` = the upload folder (`/wp-content/uploads/YYYY/MM/`), which disambiguates
  basenames that repeat across reporting periods.
- `raw/_fetch_log.jsonl` — one JSONL line per download (url, status, bytes, sha256,
  content_type, final_url, retrieved_utc). Provenance.
- `raw/index_pages/` — HTML of every host consulted (city elections page, state
  disclosures folders, archived orem.org page, Wayback CDX) — the evidence behind
  `AVAILABILITY.md`.
- `text/*.txt` — a text sidecar for **every** filing (41 born-digital via `pdftotext
  -layout`, 50 scanned/image via `tesseract`). `text/_extract.json` records the
  format+method per file.
- `index.csv` — the machine-readable filing index (columns below).
- `manifest.tsv` — the curated download list (urlpath, candidate, office, election_year,
  label, source). Edit this + rerun the scripts to add/adjust filings.
- `harvest.py` → `make_text.py` → `build_index.py` — the reproducible pipeline.

## How it was fetched (reproduce)

Orem hosts filings as plain files linked from `orem.gov/elections/`. GET-only, public
records only:

```
python3 harvest.py       # downloads manifest.tsv -> raw/ (sha256 + JSONL log, ≥1s throttle)
python3 make_text.py     # text sidecar per filing (pdftotext born-digital; OCR scanned)
python3 build_index.py   # index.csv from manifest + _extract.json + _fetch_log + ER join
```

`harvest.py` mirrors `../../scripts`/`polite_fetch.py` discipline (browser UA, throttle,
verbatim bytes, provenance log). A handful of 2023 sitting-member annuals were discovered
via Wayback CDX but are still live on orem.gov and fetched from their live URLs.

## index.csv columns

`date` (filing/period date, ISO) · `candidate` · `office` (Mayor / Council At-Large — Orem
is **all at-large, no districts**) · `election_year` (the seating cycle) · `filing_type`
(`interim` = primary/general/28-day/7-day/primary reports; `summary` = final/post +
year-end **annual** reports) · `title` · `source_url` (the direct file URL on orem.gov) ·
`retrieved_date` · `format` (`text` born-digital / `scanned` OCR) · `extraction_method` ·
`path` (dataset-relative, incl. `raw/`) · `reporting_period` (the city's own label) ·
`date_precision` (`day` = date in the filename; `cycle_stage` = statutory stage default;
`annual_deadline` = Jan-10; `upload_month`) · `sha256` · `source_page` · `matched_election_candidate`
· `join_confidence`.

### `election_year` rule
Cycle filings (primary/general/28-day/7-day/final) take their **own cycle** (2023 or 2025).
**Annual** sitting-member reports map to the odd-year **cycle in which that member was last
elected to the current term** (e.g. Lambson/Gale/Killpack → 2023; Young/Macdonald/Spencer →
2021; Millett's post-2025 annuals → 2025). This makes each annual join the member's winning
campaign.

## Join to election_results (who funded the voters)

`build_index.py` left-joins each filing's `(candidate, election_year)` to
`../election_results/orem_results_by_candidate.csv` (the full ballot universe; one row per
person per year). Names normalized (upper-case, punctuation/suffixes stripped, first+last
tokens). **Result: 83 filings join `exact`, 8 `medium`; 28 of 28 (candidate, year) pairs
join — 100 %.** No election-record discrepancy surfaced (unlike Sandy's Parry Harrison
case). Coverage gaps are documented in `AVAILABILITY.md`:

- **2019 field: absent** (city publishes nothing pre-2023; winners Peterson & Lauret have
  no filing).
- **2021 candidate cycle filings: absent** — represented only by the 2021 cohort's later
  **annual** reports (Young, Millett, Spencer, Macdonald).

## Caveats

- **Not the full field for every year.** 2023 & 2025 are complete; 2019/2021 are gaps or
  annual-only — a source limitation, verified, never fabricated.
- **OCR, not born-digital, for 50 files** (photographed / scanned forms). `text/*.txt` is
  machine OCR — the raw file is authoritative.
- **Structured amounts now exist** — see "## Structured layer" below. Filing line-items are in
  `contributions.csv` / `expenditures.csv` / `filing_totals.csv` (DERIVED). The raw files +
  `text/` sidecars remain authoritative.
- **Rebuild:** `python3 build_index.py` (index only). Re-harvest: `python3 harvest.py`.

## Structured layer (contributions / expenditures / filing_totals) — as-of 2026-07-05

Additive, DERIVED money layer built by the shared framework in `scripts/campaign_finance/`.
Contract: `scripts/campaign_finance/SCHEMA.md`. Rebuild: `python3 build_finance.py` (idempotent).
Validate: `python3 ../../scripts/campaign_finance/validate_finance.py .` → **PASS**.

- **contributions.csv** 1,011 rows · **expenditures.csv** 806 rows · **filing_totals.csv** 91 rows.
- **SCOPE — all 91 filings are in-scope campaign C&E reports.** Orem's personal conflict-of-
  interest statements are a separate genre, already excluded at harvest (`AVAILABILITY.md`).

### Form family — `utah_standard_form` (NEW, built to generalize)
Orem is **NOT** an EasyVote / third-party-portal city. It self-hosts the **Utah municipal
"Financial Disclosure / Report of Contributions and Expenditures" form** (UCA 10-3-208): a
numbered totals block (1. contributions >$50 · 2. aggregate ≤$50 · 3. expenditures) over three
itemized sections — **Cash Contributions** (Date/Donor/Amount), **In-Kind Contributions**
(Date/Donor/Est.Amount), **Cash Expenditures** (Date/Recipient/Purpose/Amount) — each ending in
a printed **section TOTAL**. This is a **new form family**, `families/utah_standard_form.py`,
written to **generalize**: Logan, Nephi, and Vineyard file the same/near-identical statutory form
and should reuse the module unchanged (any label drift is passed via `meta["form_opts"]`; no
city name/office logic lives in the family — candidate/office/year come from `index.csv`).
Registered in `families/registry.py`; selected by `build_finance.py`.

**Reconciliation anchor = the sections' own printed TOTALs** (not the numbered headline, which
folds in-kind into line 1 and splits the ≤$50 aggregate inconsistently between filers): the
contributions side sums ALL contribution rows (cash + in-kind) vs (Cash-Contributions TOTAL +
In-Kind TOTAL); the expenditures side sums expenditure rows vs the Cash-Expenditures TOTAL.
The unitemized ≤$50 aggregate (line 2) is NOT emitted as a synthetic row (would fabricate donor
identities + break the itemized check) — it is recorded in `filing_totals.notes`.

### Modes — born-digital + OCR + gated vision (the Sandy pattern)
- **41 born-digital** (`format=text`, `pdftotext -layout`) → text mode: **34/41 reconcile
  both sides** (`high`). The 7 honest born-digital flags are genuine layout oddities, not
  extraction failures: **4 Doyle Mortimer** filings use a bespoke **two-column side-by-side**
  ledger (two donor rows per physical line — the standard linear parser captures one column);
  **Jeff Lambson Primary** is a nested ledger (a reimbursement line re-sums itemized detail →
  ambiguous double-count); **Angela Moulton Final** (source printed `$222` in the row vs `$222.22`
  in the TOTAL — a 22¢ source truncation, kept verbatim); **Crystal Muhlestein 7-day** (the PDF's
  Amount column rendered blank/truncated). All raw-PDF-authoritative, `low` + `needs_review`.
- **50 scanned** (`format=scanned`, tesseract; a few are `.jpg/.jpeg` photos) → OCR mode: the
  shared `common.py` currency-repair whitelist + date-sanity, plus a `$`-spacing normalizer
  (`$      5,599.00` / `($ 850.00)` spreadsheet right-alignment, which the strict money regex
  would otherwise miss). **20/50 reconcile on OCR alone** (`medium`).
- **Vision escalation (GATED, scanned-only):** the **30 scanned filings** still unreconciled after
  OCR were escalated to Claude vision (`vision_extract.py`, model `claude-sonnet-5`, strict
  "transcribe exactly / never infer" prompt; transcriptions cached in `vision/<doc8>.json`, fed
  back through the SAME reconciliation via the driver `rows_override_fn`, `extract_method=…/vision`).
  **Cost ≈ $1.71 total** (~2019 pages across two runs, 23+7 filings; ~147k input + ~84k output
  tokens, synchronous list price). **Vision reconciled 22 of 30.** Standout recovery: the two
  **David M. Spencer 2025** interim reports OCR'd **mirror-reversed** (`SNOILNGIYLNOS GND-NI` =
  "IN-KIND CONTRIBUTIONS") — unusable OCR, cleanly recovered by vision (both sides reconcile).
- **Final: 76 of 91 reconcile both sides.** The **15 honest residual flags** = the 7 born-digital
  oddities above + **8 scanned**: **3 Matt McKell** filings (submitted as a QuickBooks *Profit &
  Loss* export, not the standard form — vision transcribes rows but they don't map to a section
  TOTAL); **2 near-empty Annual-2026** nil filings (Killpack, Millett — all `$ -` placeholders,
  totals unreadable → honest unknown); **Heather Fry** Primary + Final; **Greg Duerden** Final.
  All carry `needs_review=1` + `low` — nothing fabricated.

### Dedup — INCREMENTAL (`is_incremental=True`)
Empirically determined: each report covers a **discrete, non-overlapping** reporting period
(Primary May13–Aug29 / General Aug30–Oct24 / Final Oct25–Nov14) and the per-period loan-to-
campaign amounts differ each report (Killpack $2,200 → $3,300 → $14,400), so a candidate's cycle
total is the **SUM** of the period reports, NOT the latest snapshot (contrast Lehi = cumulative).
`driver.run(dedup_mode="incremental")`. **4 filings carry amendment notes** (`updated`/`revised`
labels the period-grouping couldn't pair) — kept + flagged, never dropped; cycle sums exclude
`superseded…` rows.

### donor_type distribution (1,011 contribution rows)
individual 759 · loan 47 · business 47 · candidate-self 29 · family-of-candidate 24 · pac 8 ·
anonymous 5 · party 1 · **unknown 91** (of which **7 blank-donor** → `unknown` + `needs_review`;
the rest are single-token names / parenthetical-note joint donors the conservative classifier
won't force). **105 in-kind** contribution rows. **37 filings carry self-funding** (loans
dominate — many "X Loan to Campaign"). `donor_aliases.csv` + `finance_overrides.csv` header-only.

### Hand-verification (5 filings, line-by-line vs the raw source, 2026-07-05)
| filing | mode | check | result |
|---|---|---|---|
| Chris Killpack — Primary 2023 | born-digital | 13 cash rows + 1 in-kind vs raw PDF re-extract | ✓ cash Σ **$6,575.00 = TOTAL**; +in-kind $3,367.11 → **$9,942.11 = stated**; expend **$6,513.80** ✓ |
| Quinn Mecham — Primary 2025 | born-digital | 39 contrib (incl in-kind $6,706.37) + 14 expend | ✓ Σ contrib **$22,624.37 = stated**; expend **$8,809.93 = stated** |
| Tom Macdonald — Annual 2023 | OCR | OCR artifacts `$3,000.00)` / `$3,000.00.`; headline `$4,995.21` vs section TOTAL `$4,955.21` | ✓ trailing punct stripped, Σ contrib **$6,000.00**; anchored on section TOTAL not garbled headline → expend **$4,955.21** ✓ |
| Karen McCandless — 7-day 2025 | vision | 19 contrib (in-kind $7,999.83) + 9 expend | ✓ Σ contrib **$27,439.15 = stated**; expend **$19,439.32 = stated** |
| David M. Spencer — 7-day 2025 | vision (reversed-OCR) | OCR was mirror-reversed/unusable; vision rows | ✓ 6 contrib (2 David Spencer Loans) Σ **$5,920.00 = stated**; 6 expend Σ **$8,943.33 = stated** |

### What the new family needs before Logan / Nephi / Vineyard reuse it
- **Confirm their section-header + totals-label wording** matches the Utah-standard defaults; if a
  city drifts (e.g. a differently-worded headline), pass overrides via `meta["form_opts"]` from
  that city's `build_finance.py` — do **not** edit the family.
- **Re-determine incremental-vs-cumulative empirically** per city (Orem = incremental; verify each
  new city's period structure before trusting cycle sums).
- The **two-column side-by-side ledger** variant (Orem's Doyle Mortimer) and **QuickBooks P&L
  attachments** (Orem's Matt McKell) are NOT handled — if a reuse city leans on either, they stay
  honestly flagged (or need a dedicated path); they are rare and left `low`+`needs_review` here.

## Regression fix + per-candidate regime pass (2026-07-20)

- **Stale-key regression FIXED** (same defect as sandy): the index column was renamed
  `report_period` → `reporting_period` after this build was written; the stale key blanked every
  filing's period, the dedup collapsed each candidate-cycle into one group (**63 false
  supersessions**) and cycle_totals saw only the last filing per cycle. Keys fixed in
  `build_finance.py`; with real period labels Orem has **0 supersessions** (no same-period
  re-files).
- **`is_incremental`** now runs the shared empirical per-candidate derivation
  (`derive_incremental=True`): four candidate-cycles are evidence-backed **cumulative**
  (`False`) — Garber 2023 (Final re-lists the Primary 1.0/0.98), McKell 2023 (full restatement
  chain — the documented $59.5k case, figure unchanged), Fry 2023 (partial restatement), White
  2025. All other filers are per-period (`True`).
- **CAUTION — date-drift trap (Duerden):** his Final re-lists the Primary's rows *with dates
  added* where the Primary's were date-blank, so (date,amount)-signature overlap reads 0.0; a
  date-blind amount-multiset containment check catches it. Every per-period conclusion below was
  re-audited date-blind before being accepted.
- **`cycle_overrides.csv` (15 rows)**, each with its proof: Orem reports print a discrete
  **FILING PERIOD From/To range**, and for the per-period filers the near-empty-summary max()
  rule silently dropped the real Final/Post periods. Cycle = the sum of all live reports'
  reconciled stated totals (every filing reconciles stated=itemized; itemizations disjoint;
  clean date-blind checks). Page-verified anchors: Dave Young 2025 Final (10/24–12/4/25, Todd
  Pedersen $48,000 on 12/3) → cycle $186,008.46/$155,152.07; Muhlestein 2023 Post
  (11/14–12/20/23, Keep Orem Safe PAC $52,000 + Tactical Campaigns $56,401.42) → cycle
  $97,382.49/$95,345.62 with her General excluded as fully restated inside the Final. The 2023
  Final/Post reports carry the shared **Stronger Orem PAC $23,756.29 in-kind package**
  (Killpack, Lambson, Gale) and the 2025 Finals the **$10,884.17 Friends-of-Dave-Young +
  $227.93 UCRP package** (Spencer, Millett, Muhlestein) — real late attributions, itemized once
  per candidate. Fry 2023 is overridden to her Final snapshot (cumulative-leaning, OCR-floor
  flagged).
