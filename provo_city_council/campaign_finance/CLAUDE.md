# Provo campaign-finance disclosures — build & linkage

Additive dataset built by `expand-city-sources` **Source 6**. Completes the
**elections → members → votes** chain: who funded each Provo Mayor/Council candidate.
**As-of 2026-07-03.** Do not edit `election_results/` from here (flags only).

```
campaign_finance/
  raw/            41 candidate PDFs verbatim + _fetch_log.jsonl (sha256/status/bytes)
  text/           41 extracted-text sidecars (pdftotext or OCR), for screening/analysis
  discovery/      the Election-Documents HTML + CDX JSON used to find the filings (provenance)
  index.csv       one row per candidate filing (schema below)
  AVAILABILITY.md what was checked, what exists, the 2019 gap, source verification
  unrecovered.csv 2019 (unpublished) + 3 filed-but-not-on-ballot candidates
  CLAUDE.md       this file
```

## Source

Single canonical source: **https://www.provo.gov/1001/Election-Documents**, section
**"CAMPAIGN FINANCIAL DISCLOSURES"** (CivicPlus DocumentCenter, City Recorder). One PDF per
candidate per cycle = a full-cycle **Campaign Finance Disclosure Form** (per-period money
summary + itemized donations + expenditures). Fetched via
`scripts/polite_fetch.py` (`--referer` the page, `--now 2026-07-03T00:00:00Z`); URLs are
`https://www.provo.gov/DocumentCenter/View/<id>/<slug>`. The DocumentCenter **View id is the
stable unique id** (kept in `index.csv.document_id` and in every raw filename as
`cf_<year>_<viewid>_<slug>.pdf`) — used as the collision-proof prefix the skill requires.

**Coverage: 2021, 2023, 2025 complete. 2019 unpublished/unrecovered** (see AVAILABILITY.md).
The state (`disclosures.utah.gov`, links back to city + 500s) and county sites do **not**
host these; **no EasyVote instance exists** for Provo (DNS fails). Provo self-hosts.

## index.csv schema

Required six: `date, title, source_url, retrieved_date, format, extraction_method`. Plus:

| column | meaning |
|--------|---------|
| `date` | the filing's own date — its **Creation Date** where present; see `date_basis` |
| `candidate` | filer name as printed on provo.gov (mixed case; e.g. `McKay R Jensen`) |
| `office` | `Mayor` or `Council` — assigned by **document year + page section**, never a portal "current seat" field |
| `election_year` | odd-year cycle (2021/2023/2025), from the document/section grouping |
| `filing_type` | always `summary` (each PDF is the whole-cycle summary form; the city posts no separate interim reports) |
| `reporting_period` | (§9 contract column; blank where not recorded) |
| `format` | `text` (37 born-digital) or `scanned` (4 OCR'd) |
| `extraction_method` | `pdftotext -layout`, or `tesseract OCR (pdftoppm; OSD-derotated)` |
| `path` | `raw/<file>` (dataset-relative incl. `raw/`, per validator) |
| `seat` | District 1–5 / Citywide I–II / Mayor — **from the election_results join** (blank if unmatched) |
| `is_winner` | did this person win that cycle's race (from election_results) |
| `matched_to_results` | `yes` (38) / `no` (3 filed-but-withdrawn) |
| `date_basis` | `creation_date` (35) / `signature_date` (3) / `latest_period_end` (3) — how `date` was derived, no fabrication |
| `document_id` | CivicPlus DocumentCenter View id (stable key) |

## Join to election_results (`../election_results/provo_results_by_candidate.csv`)

Assign office/seat/is_winner by **normalized name + election_year**. Normalization (the join
key): uppercase, drop middle initials (`R.`) and `SR/JR`, strip punctuation, match on
`(year, first_token, last_token)`. **38 of 41 filings matched** a results candidate and got
their seat; **3 did not** and carry `seat=''`, `matched_to_results=no`:
- 2021 **Suzanne Q.**, 2021 **Tom Sitake**, 2023 **Ari Emmanuel Webb** — filed a disclosure
  but were **not on the ballot** (withdrew pre-primary). This is expected: the county results
  file lists only ballot-qualified candidates. Logged in `unrecovered.csv`.

Watch-outs baked into the join (from `election_results/CLAUDE.md`): two different `JENSEN`s in
2023 (**McKay R. Jensen** Citywide II ≠ **Stan Jensen** District 1) — kept distinct by
first+last token. `WRITE-IN` in results is an aggregate, never a filer.

**Assign cycle/office by document YEAR, not any current-seat field** — e.g. Rachel Whipple and
Katrice MacKay each have BOTH a 2021 and a 2025 filing (re-elections); they are two separate
rows keyed on `election_year`, not merged onto their current seat.

## Extraction notes / gotchas

- **4 files needed OCR**, labeled `format=scanned`: Eric Mutch 2025 (image-only, **scanned
  upside-down** → tesseract OSD detected 180°, de-rotated, then OCR — recovered Creation Date
  9/12/2025), Shay Aslett 2025 (image-only, 39 MB, rendered at low DPI), Rachel Whipple 2025
  (scanned body under a text cover), Travis Hoban 2023 (born-digital but font lacks a
  ToUnicode map → `pdftotext` mojibake → rasterized + OCR'd; recovered 12/19/2023).
- OCR temp images were written to the **session scratchpad**, never `/tmp` or the repo.
- `screen_corpus.py` on `text/`: clean (dict_ratio median 0.655, 0 mojibake/CID/outliers).
  The `ends_mid` advisory fires 41/41 — expected, these are tabular disclosure forms.
  `cf_2021_4468_Tom_Sitake` has 1 replacement char + a repeated line (26-page itemized donor
  list) — cosmetic, verbatim-preserved, not a hallucination.
- **Preserve source values verbatim** — donor names/typos in the forms are NOT cleaned.

## Out of scope (available but not campaign finance)

The same Election-Documents page has a **"CONFLICT OF INTEREST DISCLOSURES"** section — a
distinct statutory filing (officials'/candidates' personal & business financial interests, not
contributions/expenditures). ~30 PDFs (sitting officials 2025/2026 + 2025 candidates). Not
included here; noted in AVAILABILITY.md with their View-id ranges if ever wanted.

## Refreshing

Re-fetch the page, re-run the link extractor (`discovery/`), diff new View ids, download new
PDFs with `polite_fetch.py`, extract (OCR the image-only ones), re-run the index builder and
`validate_dataset.py`. The 2027 cycle (Cycle B: Citywide II, D1, D3, D4) will appear as a new
Mayor-less group on the same page.

## Structured layer (contributions / expenditures / filing_totals) — as-of 2026-07-05

Additive, DERIVED money layer built on top of the 41 raw filings by the shared framework in
`scripts/campaign_finance/` (Provo is the **F1** family + the Phase-1 prototype). Contract:
`scripts/campaign_finance/SCHEMA.md`. Rebuild: `python3 build_finance.py` (idempotent; reads
`index.csv` + `text/*.txt`, writes the 3 CSVs). Validate:
`python3 ../../scripts/campaign_finance/validate_finance.py .` → **PASS**.

- **contributions.csv** 741 rows · **expenditures.csv** 1,009 rows · **filing_totals.csv** 41 rows.
- **Reconciliation: 34 of 41 filings reconcile clean** (itemized Σ = the form's printed period
  + grand totals, both sides, tolerance $0.01). **7 flagged** (`reconciles_*=False`/blank,
  rows capped `low`, `needs_review=1`) — all honest, none forced:
  - **4 scanned** (`format=scanned`): Travis Hoban 2023, Eric Mutch 2025, Shay Aslett 2025,
    Rachel Whipple 2025 — OCR tears the tables into vertical token streams; we extract ONLY the
    period-pivot **stated totals** (which survive OCR) and emit **no itemized rows**. A vision
    pass is a later owner-gated phase.
  - **Tom Sitake 2021** — a **different, older Provo form** ("CAMPAIGN FINANCE STATEMENT /
    FINANCIAL REPORT TO PROVO CITY RECORDER"), heavily OCR-garbled; not the F1 pivot form, not
    machine-extractable here.
  - **Suzanne Q 2021** — an F1 form but the scanned copy is degraded (`$75`→`SO.CO`/`SiS.00`);
    stated totals unparseable.
  - **Marsha Judkins 2025** — a **genuine internal inconsistency in the source**: her
    Summary-of-Expenses vendor pivot Grand Total carries a stray extra `$739.27` column
    ($63,306.90) while her period-pivot Expendatures total says $62,567.63. Our itemized ledger
    sums to $63,306.90 (matches the vendor pivot). Flagged `dE=+739.27`, **not adjusted**.
- **donor_type distribution** (741): individual 611, business 52, family-of-candidate 26,
  candidate-self 24, unknown 11, loan 10, pac 4, anonymous 1, carryover 1, other 1. The 11
  `unknown` are all **blank-donor-name rows** (the source printed no name — `donor_raw=''`,
  geography routed to `donor_city/state/district`, `needs_review=1`); never a promoted city.
- **self_funded_amount** = Σ `candidate-self` + `loan`. Examples verified: Jeff Whitlock 2025
  $34,460.66, Sally Clayton 2025 $500.08, Katrice MacKay 2025 $0.00 (her same-surname donor
  "MacKay, Marci" is `family-of-candidate`, correctly not self).

### F1 parser gotchas handled (verified in the real corpus)
- Donor amounts come from the **per-period columns**, not the Total column — the Total is
  sometimes rounded to whole dollars ($10.73→"$11"); the period sum carries exact cents.
- **"ti" ligature dropout** in the 2023 born-digital cycle: `pdftotext` renders "Donations"→
  "Dona ons", "Starting"→"Star ng" — pivot labels are ligature-tolerant.
- Expenditure **Amount = the first (leftmost) money token** after the purpose; a second money
  token *equal* to it marks a true in-kind item (Provo records in-kind at full value), while an
  *unequal* trailing money is the form's reporting-period artifact ($2.00 on period-2 rows,
  Jeff Whitlock) and is ignored.
- A purpose glued to its amount by a single space ("...supplies. $108.19", Rachel Whipple 2021)
  is captured by locating money by regex position, not column split.
- Expense ledgers carry **real dates spanning prior years** (officeholder accounts back to
  2018) and a **space-separated date form** ("29 Jul 2021", Neil Mitchell).
- Trailing `)` artifact on donor totals ($100.00)) stripped; `Previous balance from 2018
  Campaign` → `carryover`, `Refund from Well Fargo` → `other`.
- Filings that omit the top period-pivot (Tom Fifita 2025) fall back to the `Total of
  Purchases` grand-total row for the expenditure total.

### Hand-verification (5 filings, line-by-line vs `raw/*.pdf`, 2026-07-05) — all MATCH
| filing | check | result |
|---|---|---|
| Katrice MacKay 2025 | fresh `pdftotext -layout` of raw: Donations $19,629.27 / Expend $18,413.20 | ✓ stated + itemized match |
| Jeff Whitlock 2025 | raised/spent $39,230.91; self-fund $34,460.66; Hungry Hawaiian in_kind=True; NextDayFlyers period-2 in_kind=False | ✓ |
| George Handley 2021 | 6 donors (incl. self $250, carryover $3,298.92, refund $2.11); multi-year ledger Σ $1,527.34 | ✓ |
| Sally Clayton 2025 | 1 donor (self $500.08); 5 expenses incl. −$39.85 reversal; Σ $119.89 | ✓ |
| Travis Hoban 2023 (scanned) | stated $850/$850 from OCR pivot; no itemized rows; flagged low | ✓ honest floor |

Corrections go in `finance_overrides.csv` (row-level, vs raw PDF) / `donor_aliases.csv`
(reviewed merges) — never in-place edits to the DERIVED CSVs. `finance_overrides.csv` is
currently header-only (no corrections needed for the 34 clean filings).
