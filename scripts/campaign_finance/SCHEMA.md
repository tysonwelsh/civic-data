# Campaign-finance normalization contract (Phase 0)

Normative spec for the **structured campaign-finance layer** — the derived, regenerable,
queryable money layer built on top of each city's `campaign_finance/` document set. Modeled
on the `motions_std` normalization contract (`SCHEMA_SPEC.md` §8): city-faithful values are
preserved verbatim, normalized/derived fields live *alongside*, honest gaps are recorded not
filled, and the derived CSVs are **regenerated, never hand-edited**.

Status: **Phase 0 + Phase 1 (Provo F1) + Phase 3 (born-digital Lehi F5 + West Jordan EasyVote
F2) implemented.** This doc is a standalone contract; the owner integrates the relevant parts
into the canonical `SCHEMA_SPEC.md` after review. Validators tolerate the layer's absence until
a city has been built (like the `motions_std` contract).

### Framework generalization (Phase 3)

- **Form-family dispatch** — `families/registry.py` maps a family id (`provo_form` /
  `lehi_formab` / `easyvote_schedab`) to its parser module; each city's `build_finance.py`
  selects its family through the shared engine `driver.py` (Provo, Lehi, WJ all route through
  it). A new family = a new `families/<name>.py` exposing `parse(text, meta)` + a registry row.
- **Dated per-transaction donations** — Provo prints no per-donation date (`date` blank); F5
  (Lehi) and F2 (EasyVote) date each contribution/expenditure, so `date` (+ `reporting_period`)
  are populated. The row model already carried both fields — no schema change.
- **Incremental vs cumulative dedup** (`is_incremental`, drives cycle-total queries):
  - **EasyVote F2 = incremental** (`is_incremental=True`): the Summary "Column A / Total this
    Period" is per-period and Schedule A/B itemize only that period, so a cycle total is the
    **sum** of the period reports' Column-A figures (the final report's Column B / Year-to-Date
    is the cross-check). An amendment (or exact re-file) of the same period **supersedes** the
    original — noted in `filing_totals.notes`, kept never dropped.
  - **Lehi F5 = cumulative** (`is_incremental=False`): each report restates whole-cycle-to-date
    Form-A/Form-B totals (verified: Condie 2021 Oct→Dec), so a cycle total is the **latest**
    (non-superseded) report per candidate+cycle, NOT a sum; every earlier snapshot is noted
    `superseded (cumulative snapshot)`. (The plan assumed Lehi was incremental — it is not.)
  - `driver.run(dedup_mode="incremental"|"cumulative", amend_fn=…)` applies the marking.
- **In-kind** — both F5 and F2 record an in-kind item at a single value in its own column, at
  full value (like Provo). So NO `in_kind_amount` companion column was added (the plan made it
  conditional on a family recording in-kind at a value ≠ the amount; none here does). In-kind
  rows carry `in_kind=True` and `amount` = the in-kind value. **EasyVote + Lehi variant-2 state
  their "TOTAL CONTRIBUTIONS/EXPENDITURES" EXCLUDING in-kind** (in-kind is a separate stated
  line), so per-side reconciliation sums **cash rows only** (`driver.run(reconcile_cash_only=
  True)`); Provo includes in-kind at full value in its printed total and sums all rows.
- **Totals-only filings** — a side with a positive stated total but zero itemized rows (Utah's
  under-$500 non-itemization exemption; or a fillable form whose typed totals live in AcroForm
  fields `pdftotext` cannot recover) reconciles as **unknown** (blank `reconciles_*` + a note),
  never a fabricated mismatch.

Scope of the money layer: **campaign Contribution & Expenditure (C&E) reports only.** Annual
financial / conflict-of-interest statements are out of scope (recorded as excluded in the
city `CLAUDE.md`).

---

## 1. Files per city

```
<city>_city_council/campaign_finance/
  contributions.csv     DERIVED — one row per itemized donation line (or per unnamed line, flagged)
  expenditures.csv      DERIVED — one row per itemized expenditure ledger line
  filing_totals.csv     DERIVED — one row per filing (not per cycle; cycle totals are a query)
  donor_aliases.csv     CURATED — reviewed raw→normalized donor merges (human-confirmed)
  finance_overrides.csv CURATED — documented row-level corrections vs the raw PDF
  build_finance.py      thin driver: index.csv + text/*.txt → the 3 DERIVED CSVs
```

Shared framework (repo root): `scripts/campaign_finance/` — `common.py` (tokenizers + row
model), `reconcile.py`, `normalize_donors.py`, `families/<form>.py` (one per form family),
`validate_finance.py`. Regenerate a city with `python3 <city>/campaign_finance/build_finance.py`.

**Stable keys (db-friendly; DB integration is a later phase).** Every derived row keys back
to a filing via `source_filing` (= the city's `index.csv` `path`, e.g.
`raw/cf_2021_4458_George_Handley.pdf`) plus `document_id` (the city's stable filing id) and,
for itemized rows, `line_no` (1-based line in the `text/` sidecar). `(source_filing, line_no)`
is the itemized-row key.

---

## 2. `contributions.csv` — schema

One row per itemized donation line. Blank = not extractable, never guessed.

| column | semantics |
|---|---|
| `candidate` | filer name, carried verbatim from `index.csv` (not re-derived) |
| `office` | `Mayor` / `Council` — from `index.csv` |
| `seat` | from the existing election-results join in `index.csv` (blank if unmatched) |
| `election_year` | odd-year cycle — from `index.csv` |
| `filing_date` | the filing's own date — from `index.csv` |
| `reporting_period` | period label if the row is period-scoped; blank when the row spans the cycle |
| `date` | contribution date — **blank for Provo** (form prints none); dated where the form dates donations |
| `donor_raw` | verbatim donor string incl. typos (trailing `)`/`,` artifacts stripped). **Blank = source printed no name** (unnamed donation) — never a promoted geography token |
| `donor_normalized` | tier-1 normalization output, or an alias override |
| `donor_type` | enum (§5) |
| `donor_city`, `donor_state`, `donor_district` | where the form prints them (blank elsewhere; public copies are address-redacted in some cities) |
| `amount` | decimal string, or blank when not cleanly parsed |
| `in_kind` | `True`/`False`, from the form's own in-kind column/flag |
| `is_incremental` | per-city constant: does this filing exclude previously-reported items (drives dedup). Provo = `False` (whole-cycle summary) |
| `source_filing` | = `index.csv` `path` |
| `document_id` | city's stable filing id |
| `line_no` | 1-based line in the `text/` sidecar |
| `extraction_confidence` | `high` / `medium` / `low` (§6) |
| `extract_method` | family id + mode, e.g. `provo_form/text`, `provo_form/ocr` |
| `needs_review` | `1` when a value is blank/uncertain or the row's side did not reconcile; else `0` |

## 3. `expenditures.csv` — schema

One row per itemized expenditure ledger line. Same shared columns as §2 plus:
`vendor_raw` (verbatim), `vendor_normalized` (tier-1; no alias layer in v1), `purpose`
(verbatim), `amount`, `in_kind`. `date` is the ledger date normalized to ISO `YYYY-MM-DD`
where cleanly parseable (Provo ledgers carry real dates that can span prior years for
officeholder accounts), else blank + `needs_review=1`. No `donor_*` columns.

## 4. `filing_totals.csv` — schema

One row per filing. Columns: `candidate, office, election_year, filing_date,
reporting_period, filing_type, stated_total_contributions, stated_total_expenditures,
stated_beginning_balance, stated_ending_balance, itemized_contrib_sum, itemized_expend_sum,
reconciles_contrib, reconciles_expend` (`True`/`False`/blank; tolerance $0.01),
`recon_delta_contrib, recon_delta_expend` (itemized − stated, signed), `self_funded_amount`
(Σ `candidate-self` + `loan` rows), `n_contrib_rows, n_expend_rows, source_filing,
document_id, extraction_confidence, notes`.

`stated_*` are the form's own PRINTED totals (verbatim source values). `itemized_*` are the
sums the extractor counted. The pair, and their reconciliation, is the layer's integrity
signal — the same "printed tally vs counted member rows" discipline the vote layer uses.

---

## 5. `donor_type` enum (owner-locked 2026-07-05)

```
candidate-self | family-of-candidate | individual | business | pac | party |
loan | carryover | anonymous | aggregate-unitemized | other | unknown
```

Deterministic classification, conservative, never identity-fabricating; unclassifiable →
`unknown` (never guessed). Rules, in priority order:

1. name/description contains "loan" → **`loan`**.
2. "Previous balance" / "carried forward" / "beginning balance" → **`carryover`**.
3. starts with / contains "Refund" → **`other`**.
4. "Anonymous" (or bare "Cash") → **`anonymous`**; "unitemized"/period-aggregate → **`aggregate-unitemized`**.
5. donor surname **and** a first-name token match the candidate's own name → **`candidate-self`**
   (first-name match allows a ≥3-char prefix, so *Jeff* ≡ *Jeffrey*; joint spouse forms like
   "Dudley, Ken & Vickie" match on the candidate's own tokens).
6. donor shares the candidate's **surname but not the candidate** → **`family-of-candidate`**
   (owner-locked: a same-surname relative is NOT `individual` and NOT `candidate-self`).
7. contains PAC / "Political Action Committee" → **`pac`**; a party name → **`party`**;
   a business/org token (`LLC`, `Inc`, `Association`, `Homebuilders`, `Enterprises`, …) or a
   leading `*` org marker → **`business`**.
8. otherwise a person-shaped name (comma form, or two alpha tokens) → **`individual`**; else
   **`unknown`**.

`self_funded_amount` = Σ of `candidate-self` + `loan` amounts.

**Donor normalization (tier-1, deterministic):** strip the `*` org marker + trailing
punctuation/OCR artifacts (`$100.00)`), collapse whitespace, de-cap SHOUTED tokens
(`REALTORS`→`Realtors`, preserving mixed-case like `MacKay`), and reorder a *simple*
`Last, First` → `First Last` (single comma, ≤2-token RHS, no joint "and", no surname repeat —
joint/complex donors are left as printed to avoid mangling). Joint donors stay **one row**;
the amount is never split (the form doesn't).

**Alias tier (curated):** `donor_aliases.csv`
(`city, donor_raw, donor_normalized, donor_type, evidence, added`) is the ONLY place
cross-spelling merges happen (e.g. "Utah Central Association of Realtors" ≡ the
`REALTORS`-cased OCR variant). Human-confirmed; no automatic fuzzy merging; no cross-city
donor identity resolution in v1.

---

## 6. Reconciliation + confidence (the anti-fabrication core)

Per filing, per side (contributions, expenditures): sum the itemized rows and compare to the
form's own printed total. Tolerance **$0.01**.

- **Match** → the side reconciles; its rows earn `high` (born-digital text) / `medium` (OCR).
- **Mismatch** → the filing is flagged (`reconciles_*=False` + signed `recon_delta_*`); its
  rows are capped at `low` and marked `needs_review=1`. **A mismatch is never adjusted** —
  a source that is internally inconsistent stays flagged, verbatim (like the vote layer's
  printed-tally-vs-names typos).
- A figure that does not parse cleanly stays **blank** with `needs_review=1` — never a guessed
  digit. OCR repair (future OCR corpora) is limited to reversible, whitelisted transforms and
  every repaired value is marked `extract_method=…+repair`.

`extraction_confidence` vocabulary: **`high` | `medium` | `low`** (blank only where a side was
not attempted). Filing-level confidence = the weaker of the two sides.

**Dedup / cycle totals — `filing_totals.csv` is ONE ROW PER FILING, NOT per candidate-cycle.**
Candidates file several reports per cycle (interims + a year-end summary/final), so **naively
summing a candidate's filings double-counts.** The correct per-candidate-cycle rollup is the
canonical layer **`scripts/campaign_finance/cycle_totals.py`** → writes `cycle_totals.csv`
(one row per candidate×election_year with deduped `raised`/`spent`, `basis`, `review_flag`).
**Always read `cycle_totals.csv` for a candidate/race total; never sum `filing_totals` yourself.**
Regenerate it after any `build_finance.py` (`python3 scripts/campaign_finance/cycle_totals.py --all`).

The dedup rule (encoded in cycle_totals.py) — because the filing style is **per-candidate, NOT a
per-city constant** (Logan: 7 incremental + 2 cumulative filers; Orem: some year-end summaries are
the true cumulative total, others are near-empty while the money is in the interims):
1. drop `superseded` filings (amendments/re-files, flagged in `filing_totals.notes`);
2. `summary_val` = latest summary/final report's stated total (cumulative-to-date **in principle**);
3. `interim_val` = SUM of interim reports — UNLESS the interim stated-totals are monotonically
   non-decreasing (a *cumulative* interim chain, e.g. Orem mayor Dave Young: 6 interims ≈ $22k each →
   $132k if summed), in which case take the **last** interim;
4. **cycle total = max(summary_val, interim_val)** — picks the true figure whether the summary is
   cumulative or near-empty;
5. `review_flag` fires when both are substantial (>$1k) yet disagree by >25% — a genuinely ambiguous
   filer to spot-check. **These flags are a real follow-up: several cities' `is_incremental` was set
   as a per-city constant in `build_finance.py` and should be re-derived per candidate.**

---

## 7. Override / alias file formats

- **`donor_aliases.csv`**: `city, donor_raw, donor_normalized, donor_type, evidence, added`.
  Applied by exact `donor_raw` match; overrides tier-1 output. Seed only with human-verified
  merges (cite the raw filing in `evidence`).
- **`finance_overrides.csv`**: `source_filing, line_no, csv, field, old_value, new_value,
  reason, added [, mode]` — documented row-level corrections vs the raw PDF. Header-only when
  none are needed. Corrections go here, never as in-place edits to the derived CSVs.
  **WIRED into `driver.py` 2026-07-19** via the trailing, optional `mode` column: `mode=apply`
  rows are applied at build time (loud per-row logging; STALE rows — unmatched
  source_filing/line_no, unknown csv/field, or a current value ≠ `old_value` — FAIL the build,
  the vote_overrides discipline). Any other row (or a file without the `mode` column) is a
  DOCUMENTATION-ONLY record, never applied — the historical contract, so pre-existing files
  (nephi, riverton) behave exactly as before. `csv` ∈ contributions | expenditures |
  filing_totals; row-level targets key on `(source_filing, line_no)` and are applied after
  normalization / before reconciliation (a corrected amount flows into the itemized sums and
  the printed-total test); filing_totals targets key on `source_filing` alone and do NOT
  recompute reconciliation. `extraction_confidence`/`needs_review` are pipeline-computed and
  cannot be overridden. `old_value`/`new_value` compare against the value as it appears in the
  output CSV.

---

## 8. Conformance checking

`python3 scripts/campaign_finance/validate_finance.py <city>/campaign_finance` — never
mutates. Checks: the three CSVs present with exact headers; every `source_filing` exists as an
`index.csv` `path`; amounts are valid decimals or blank (no blank amount without
`needs_review=1`); `donor_type`/`extraction_confidence`/booleans within their enums; no
contribution row lacking BOTH a `donor_raw` and an unnamed-flag (blank `donor_raw` ⇒
anonymous/aggregate-unitemized/unknown + `needs_review=1`); reconciliation columns internally
consistent (`reconciles=True` ⇒ |itemized − stated| ≤ $0.01); `filing_totals` row counts match
the actual per-filing itemized-row counts; every `(candidate, election_year)` in the CSVs
exists in `index.csv`. Exit code = number of FAILs.
