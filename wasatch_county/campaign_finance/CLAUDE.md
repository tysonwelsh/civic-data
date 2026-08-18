# campaign_finance/ — Wasatch County county-office campaign finance

**As-of 2026-08-14** (itemized layer; stated-totals layer 2026-08-01). The first dataset built
for `wasatch_county`, which is otherwise a
**REGISTERED-ONLY** entity (registry row since 2026-07-20, carrying Park City's second
within-county edge; no db, no vote layer, no federation). Nothing here is in `gov.db`.

## What this is

**111 campaign-finance reports** filed by candidates for **Wasatch County COUNTY offices** —
County Council, Clerk/Auditor, Sheriff, Attorney, Assessor, Recorder, Treasurer, Surveyor —
across the **2010, 2018, 2020, 2022, 2024 and 2026** cycles (61 distinct candidate-cycles).
Raw PDFs are retained verbatim in `raw/<year>/`; a text sidecar per filing is in
`text/<year>/`; one index row per filing is in `index.csv`.

**School board is out of scope** (32 filings identified and catalogued in `out_of_scope.csv`,
never fetched).

**A STATED-TOTALS layer exists as of 2026-08-01** — `filing_totals.csv`, 111 rows, built from
111 curated `vision/<key>.json` cover-page transcriptions. See "The stated-totals layer" below.

**A FULL ITEMIZED layer exists as of 2026-08-14** (tranche 3 Phase B) — **851 donor/vendor rows,
346 contributions + 505 expenditures, over 73 of the 111 filings; every one of the 111 has an
itemized layer and 0 sides are withheld.** See "The itemized layer" below. This SUPERSEDES the
Phase A state of "8 expenditure rows over 2 filings".

```
RECON.md              channels probed + every negative, with reasoning     ← read first
AVAILABILITY.md       coverage matrix, per-cycle sourcing, the gap ledger
index.csv             one row per retained filing (22 cols; schema below)
unrecovered.csv       5 known-missing 2024 general reports (dead everywhere)
out_of_scope.csv      32 school-board filings identified but not fetched
text_extraction.csv   per-file text-extraction manifest (format + method)
raw/<year>/           the filing PDFs + per-year _fetch_log.jsonl (url, bytes, sha256, utc)
raw/index_pages/      the 10 LISTING pages the map was read off (live + Wayback) + fetch log
text/<year>/          one .txt per PDF (pdftotext -layout, or 300dpi tesseract)
vision/<key>.json     CURATED — one cover-page transcription per filing (111). `<key>` =
                      sha1(index.csv `path`)[:8]. Schema below; corrections go HERE.
filing_totals.csv     DERIVED — one row per filing (111), SCHEMA.md §4 + `filing_regime`
contributions.csv     DERIVED — SCHEMA.md §2 (+ `geometry`); 346 rows
expenditures.csv      DERIVED — SCHEMA.md §3 (+ `geometry`); 505 rows
build_finance.py      rebuild the three CSVs from index.csv + vision/    (idempotent)
make_itemized_caches.py  merge a wave's transcription RECORDS into vision/<key>.json as the
                      `contributions`/`expenditures` lists + `_meta.itemized`. THE ONLY WRITER
                      of the itemized half of a cache; re-screens every record from scratch
                      (reconciliation, field shift, privacy, dates) and is idempotent
refetch.py            verify every retained PDF against index.csv sha256 (currently 111/111)
extract_text.py       rebuild text/ + text_extraction.csv
build_index.py        rebuild index.csv / out_of_scope.csv / unrecovered.csv
```

## `index.csv` schema

| column | meaning |
|---|---|
| `date` | filing-period **proxy** (`YYYY-MM-DD`). Exact where the source states it (2010, the 2024 state copy); otherwise the first of the statutory reporting month. **Not** the signature date — that is inside the PDF. |
| `candidate` | filer name as published by the county. |
| `office`, `seat` | assigned from **the county's own candidate listing for that cycle** (`raw/index_pages/`), because the PDF's *Name of Office* field is usually handwritten. Where the listing was silent, from the form field itself. |
| `election_year` | 2010 / 2018 / 2020 / 2022 / 2024 / 2026. |
| `filing_type` | `statement` (all — these are full reports, not separate schedules). |
| `reporting_period` | the statutory filing point as published (e.g. `June 2020 (7 days before Primary)`, `General 2022`, `March 2026 (Partisan Convention Report, due 3/31)`). |
| `source_url` | the **government's own** URL (county origin, or `municipal.utah.gov` for the state copies). |
| `archive_url` | populated **only** for the 7 filings recovered via the Internet Archive; blank means origin-fetched. |
| `form_family` | **the vision-read variant** (coordinator fix 2026-08-01 — `build_index.py` now sources this column from each filing's `vision/<key>.json._meta.form_variant_vision`, retiring the statute-header classifier that misfiled 6 rows): `wasatch_disclosure_tableab` (49) / `wasatch_fcr_3line` (45) / `carr_5_5_pg_4line` (17). Agrees with `filing_totals.filing_regime` by construction. |
| `format` | `text` (71 born-digital / AcroForm) / `scanned` (40 image-only). Measured from the actual text layer, not the extension. |
| `extraction_method` | `pdftotext -layout` or `tesseract OCR (pdftoppm 300dpi, psm 6)`. |
| `path`, `text_path` | repo-relative PDF + sidecar. |
| `pages`, `bytes`, `sha256` | integrity triple; `refetch.py` checks the digest. |
| `channel` | `origin` (104) / `wayback` (6) / `wayback_latest` (1). |
| `needs_review` | `1` on every row. **STALE since 2026-08-14** — it predates both the stated-totals layer (2026-08-01) and the itemized layer (2026-08-14), and both are now complete. `index.csv` is DERIVED by `build_index.py`; retiring this column is a follow-up for the coordinator, not a hand edit. Use `filing_totals.reconciles_*` + `vision/<key>.json._meta.itemized` for the real per-filing state. |
| `notes` | per-row caveats (5 rows): the Farrell double-checkbox, the state-site copy, the untimestamped Adams recovery, the two undetectable form families. |

## The three things to get right before querying this

1. **THREE form variants, and the seam is the 2022→2024 CYCLE BOUNDARY — not mid-2024.**
   Every one of the 111 covers was read by vision on 2026-08-01, and the split is clean:

   | variant (`form_variant_vision`) | cycles | n | shape | regime |
   |---|---|---:|---|---|
   | `carr_5_5_pg_4line` | 2010, 2022 | 17 | Carr `FINANCIAL CAMPAIGN REPORT` + Form A/B, **4 lines** (>$50, ≤$50 aggregate, expenses, balance) × 3 columns; statute **17-16-6.5** | cumulative |
   | `wasatch_fcr_3line` | 2018, 2020 | 45 | Wasatch's own typed `FINANCIAL CAMPAIGN REPORT`, **3 lines** × 3 columns; statute misprinted **17-15-6.5** | cumulative |
   | `wasatch_disclosure_tableab` | 2024, 2026 | 49 | `CAMPAIGN FINANCIAL DISCLOSURE` + Table A/B, **one TOTALS column** + a reporting-period checkbox list | period-scoped |

   **The earlier "2024 is mixed (4 old / 16 new)" reading is FALSIFIED by the documents.** All
   21 of the 2024 filings are on the new Table A/B sheet. The mislabel has a cause worth
   knowing: **the 2024 vintage of the NEW sheet still cites Utah Code 17-16-6.5** (only from
   2026 does it cite 17-70-4 for anonymous-donation disposition), so a statute-header classifier
   reads it as the old county form. That classifier misfiled 6 rows (`202403_state_Adams`,
   `202406_BobAdams`, `202406_JamiSmithHewlett`, `202406_ToddGriffin` labelled old-but-new;
   `202406_ToriBroughton` blank-but-new; `2020_OctJGranger` blank-but-three-line) — **FIXED
   2026-08-01**: `build_index.py` now takes `form_family` from each filing's vision cache
   (`form_variant_vision`, the page-read evidence), so `index.csv`, `filing_totals.filing_regime`
   and the caches agree by construction.
2. **The variants mean different things by "a report", so a cycle total is a different
   computation on each.** The two older sheets are **cumulative** — a three-column
   `TOTALS FROM LAST REPORT + TOTALS FOR THIS REPORT = CUMULATIVE REPORT` box — so a candidate's
   cycle figure is the **latest** report and summing their filings double-counts (ground truth:
   Granger 2022-11-01, $0 / $0 / $450 expenses / −$450). The new sheet is **period-scoped**;
   three filers say so in their own hand — Woodard 2026-06 annotates lines 1 and 2 *"since last
   report"*, Forsyth 2026-06 prints *"(balance of $1,263.82 in campaign bank account from prior
   contributions previously reported)"*, and Bonner's 2024 general covers *"Sep 26 to Oct 24"*
   ($700 raised / $3,612.69 spent). So a cycle figure there is a **sum** across periods —
   **except** where a filer restates cumulatively anyway (Kaiserman 2024 June and general both
   print 653.00/653.00/0; Rowland 2026 and Farrell 2026 both repeat their March totals in June).
   Those are called out in each row's `notes`; read them before summing.
   **2020 is the trap year**: 3 reports per candidate, all cumulative — take December, do not
   add June + October + December.
3. **`reconciles_*` is defined against the PUBLISHED stated total, and `False` there does NOT
   mean a missing donor.** A side is gated against the figure the FACE prints, and on these
   forms that is often not the published total: Carr contributions gate on **cover line 1**
   (line 2 is an unitemized ≤$50 aggregate), a cumulative-sheet schedule may cover only the
   current period and gate on the **THIS REPORT** column, and several filers exclude their own
   in-kind rows from their totals. Each side's real anchor, closure and cause live in
   `vision/<key>.json._meta.itemized.recon.<side>` — read that before quoting a delta.
   79 contribution / 76 expenditure sides read `True`; 18 / 21 read `False` (almost all for one
   of the three reasons above); 14 are blank = **unknown, never a fabricated match**.

## The itemized layer (TRANCHE 3 Phase B, 2026-08-14) — 851 rows, 0 sides withheld

**851 donor/vendor rows: 346 contributions + 505 expenditures over 73 filings** ($182,337.32
contributed, $168,109.85 spent, 253 distinct normalized donors). **All 111 filings have an
itemized layer**; the 38 with no rows are enumerated below and are three different facts, not one
gap. Built by two routes and materialized through one screen.

| | count |
|---|---:|
| filings with an itemized layer | **111 of 111** |
| filings publishing >=1 row | **73** (2010 4 · 2018 7 · 2020 22 · 2022 9 · 2024 10 · 2026 21) |
| sides exact-reconciled | **168** |
| sides carrying a verbatim filer delta | **20** |
| sides **withheld** | **0** |
| sides `unknown` (no anchor on the face, or no schedule page) | **28** |
| rows carrying a `pct:` geometry anchor | **850 of 851** |
| rows flagged `needs_review=1` | 79 |
| rows with a deliberately blank date | 52 |

### Route 1 — the born-digital family, with its Phase B DATE-GRAMMAR fix (25 rows)

`scripts/campaign_finance/families/wasatch_disclosure_tableab.py` parses the machine-readable
Table A/B text layer. Phase A knew only `M/D/YY(YY)`, so three 2026 filers' own date styles —
`17 Jan 2026`, `1.2.26` / `11 .7.25`, `5May26` — left the date token in the NAME column and slid
the real name one field right. **The amounts still summed EXACTLY**, which is why reconciliation
could not see it and all six sides were withheld: that is the whole point of the
`wasatch-field-shift` calibration specimen, and it came from this county.

The grammar now matches those three shapes. **Month names are ENUMERATED, never a bare
`[A-Za-z]{3,9}`** — a bare alpha class would eat the vendor name of a row whose date cell is
empty ("May Company  $50.00"), which is the same class of error the fix exists to remove. Four
regression tests cover it in `scripts/campaign_finance/tests/test_families.py`, including that
negative control. **All 7 sides Phase A withheld are now closed** (Woodard 2026-03, Kellogg
2026-03, Vance 2026-06 by the parser; Rowland 2026-06's Table B — withheld as "OCR noise" — by
the vision read, which found a clean typed single row).

### Route 2 — the READ-TOOL VISION WAVE (826 rows)

Every page of the other 108 filings rendered at 200 dpi and read; escalation to 600–1200 dpi
TIGHT CELL CROPS only (89 of them, on 27 filings), never a bigger full page. $0 API. The configuration passed
the CF calibration suite **13/13, all five negative controls holding**, before any bulk
transcription (`_audits/cf-calibration-suite/runs.md`, 2026-08-14).

### PRECEDENCE: the vision read governs

Where both routes covered a side, the **vision rows are published and the family's are held in
the parse only** — the same rule this module already applies to the cover ("the VISION figure
governs"). The family is a regex over a text layer and is demonstrably brittle here (blank vendor
names on Forsyth 2026-06; three whole filings mis-columned before the date fix). Every
supersession writes a note naming both row counts and both sums, so nothing is silently dropped.

### RECONCILIATION: three legitimate anchors, because the forms have three

A side is gated against the figures the FACE prints, first exact closure wins, and the anchor
names itself in `vision/<key>.json._meta.itemized.recon.<side>`:

1. **Carr 4-line contributions gate on COVER LINE 1**, not the published total — line 2 is an
   **unitemized AGGREGATE of contributions of $50 or less** that Form A does not itemize and
   never could. Ground truth: Scott Sweat 2010, Form A = 340.00 = line 1 exactly, and the 250.00
   difference from the published 590.00 *is* line 2.
2. **A cumulative-sheet schedule may be PERIOD-SCOPED** while the cover states the cumulative
   figure; the residual then equals the TOTALS-FROM-LAST-REPORT cell to the cent. Common across
   2020. Closing on the THIS REPORT column is a real closure and is labelled as one.
3. **IN-KIND TREATMENT IS PER FILER, NOT PER FORM.** Tyler Dow 2018 and Aimee Armer 2020 EXCLUDE
   their in-kind rows from their own printed totals — a sum that counted them would not
   reconcile — while Jennifer Lee 2020 INCLUDES hers and still closes exactly. Both are tried.

⚠ Consequently `filing_totals.reconciles_*` — which is defined against the **published**
`stated_total_*` — reads `False` on a side that closed perfectly on line 1 or on THIS REPORT.
`recon_delta_*` carries the difference and the cache's `recon.<side>.detail` names its cause.
**`False` there is not a missing donor.**

### The 20 verbatim deltas — every one diagnosed, none adjusted

Full text in each cache; the cache also preserves the transcriber's own account verbatim, which
is where the diagnosis lives. Classes:

- **A filer wrote the wrong thing in the total cell.** *Koson 2010* prints a bare **`5`** on cover
  line 1 while Form A itemizes exactly **five** contributions totalling $2,250 — and his own
  line-3/line-4 identity (2,250 spent, 0 balance) only closes at 2,250. He entered the contributor
  COUNT in a dollar cell. The cover was re-read in full to confirm no larger figure hides there.
- **Filer arithmetic:** Kosakowski 2018 (−320.00 / +10.00; all 44 amounts re-read in 600 dpi
  column crops, unchanged), Farrell 2020-12 (+5.00), Farrell 2026-03 and 2026-06 (+1.00 both
  sides, 1200 dpi), Rigby 2026-06 (+1.00), Mainord 2026-03 (+66.00), Hokanson 2020-06 (+10.00),
  Granger 2020-06 (a SIGN only, against her printed −246.08).
- **The filer totalled a different column:** Armer 2020-10 totalled the GROSS "Total charged"
  (amount + donor-paid fee) on an attached FundHero export; Searle 2022-06's expenditure residual
  is exactly his one filing-fee row.
- **The cover asserts money the schedule never itemizes:** Bercuson 2024-06 (100.00 in),
  Bercuson 2024-11 (600.00 out); and the reverse, Hewlett 2024-11, whose struck-then-circled `0`
  cover cell sits against a Table A itemizing 1,300.00.
- **One residual survives escalation:** *Searle 2022-06 contributions*, −$50.00. The reading that
  would close it was **rejected** — the sheet is born-digital and prints `$230.00` unambiguously
  — and his cover is internally consistent. The shortfall is in the schedule.

### 38 filings publish no row, and that is THREE different facts

| state | filings | means |
|---|---:|---|
| schedule page present and **BLANK** | **26** | a real zero — the page was looked at and recorded |
| **no schedule page in the document** | **9** | cover-only 1-page PDFs (Park ×3, Nelson ×2, Burgener, Griffin, McMillan 2022-06, Tugaw 2026-06). **Non-existence, not zero**, even where the cover states 0 |
| mixed (one side blank, the other absent) | **3** | Nelson 2020-06, Griffin 2020-06 and 2020-12 |

Everywhere else in this repo an empty itemized side means NOT TRANSCRIBED. On those 26 it means
the schedule is blank, because `sides.<side> = "transcribed"` with zero rows is a recorded read.

### Geometry

`pct:x,y,w,h@p<page>` (SCHEMA §2a), resolvable by `scripts/campaign_finance/make_snippet.py`.
Born-digital rows carry an **exact** box from `pdftotext -bbox-layout` (free on a machine-readable
page; the per-cell `<line>` fragments are clustered back into rows by vertical overlap, and an
ambiguous match is refused rather than guessed). Vision rows carry an **estimated band** from the
form's own fixed ruled-row pitch, stamped `geometry_fit: "estimated"`. Either way it is a POINTER
to the row, never a value. One row keeps the coarser `p2:l81:c69-73` text-line pointer.

### How to REBUILD or EXTEND this layer

The wave's working set is preserved at `_backups/2026-08-14-tranche3-phaseb/wasatch/`:
`queue.csv`, `chunks/chunk_NN.csv`, `records/chunk_NN.json` (the raw transcription records),
`AGENT_BRIEF.md` (**the per-row contract verbatim — hand this to any agent that continues the
work**) and `wave_stats.py` (every number this doc quotes).

```
python3 wasatch_county/campaign_finance/make_itemized_caches.py \
        _backups/2026-08-14-tranche3-phaseb/wasatch/records     # --dry-run first
python3 wasatch_county/campaign_finance/build_finance.py
python3 scripts/campaign_finance/validate_finance.py wasatch_county/campaign_finance
python3 _backups/2026-08-14-tranche3-phaseb/wasatch/wave_stats.py            # and --residue
```
`make_itemized_caches.py` **re-screens every record from scratch** — it recomputes each side's
reconciliation against the right anchor, re-runs the field-shift and privacy screens and
re-derives geometry — so the published layer is reproducible from the records and never depends
on a claim a transcriber made. It is the ONLY writer of the itemized half of a cache and never
touches the stated-totals half.

## The stated-totals layer

`filing_totals.csv` (111 rows) is DERIVED — **regenerate, never hand-edit**:
`python3 wasatch_county/campaign_finance/build_finance.py`. Corrections go in the
`vision/<key>.json` cache, with a note saying what was re-read at the source.

- **`filing_regime`** (the optional trailing SCHEMA.md column) is `cumulative` (62) or
  `period` (49), taken from the variant. It is the semantics an itemized tranche would carry as
  `is_incremental`: **cumulative ⇒ `is_incremental=False`** (latest report wins),
  **period ⇒ `is_incremental=True`** (sum across periods).
- **Column selection on the cumulative sheets** is deterministic and documented in
  `build_finance.py`: use the CUMULATIVE column when it prints a figure; else, if the LAST
  REPORT column is blank/0/`N/A` (nothing precedes this report), promote THIS REPORT and say so
  in `notes`; else leave the total BLANK. All three columns stay verbatim in the cache.
- On the four-line Carr sheet a contribution total is **line 1 (>$50) + line 2 (≤$50
  aggregate)**, summing only the cells the filer actually printed (the juab precedent).
- **`stated_ending_balance` is VERBATIM** — parentheses (`(331.75)`), a stray `$-`, even
  Forsyth's parenthetical prose. `stated_total_contributions`/`_expenditures` are normalized to
  decimals only because the validator requires it.
- **`extraction_confidence`**: 103 `high`, 6 `medium`, 2 blank (nothing stated to read). Per-cell
  confidence lives in the cache, so a single shaky digit does not downgrade a whole filing
  silently.

### `vision/<key>.json` schema

```
_meta   index_path, cache_key, election_year, reporting_period_index,
        form_family_index (what index.csv says) vs form_variant_vision (what the page IS),
        form_statute_verbatim, filing_regime, is_incremental, tranche, source,
        pages_read, text_layer_corroborated_lines, transcribed_by, transcribed_utc
cover   candidate/office/district/party/residence_city/addressee/signature_date, each
        {value, confidence}; `signed`; `report_periods_checked` — verbatim box labels, where
        `null` = the variant prints NO period selector (2010/2022 Carr) and `[]` = a selector
        is present and nothing is marked; `convention_date_verbatim`
stated  per printed line -> per COLUMN cell {value, confidence}.
        cumulative variants: last_report / this_report / cumulative
          carr_5_5_pg_4line: contrib_gt50, contrib_le50, total_expenses, balance_end
          wasatch_fcr_3line: total_contributions, total_expenses, balance_end
        period variant: a single `period` cell
          wasatch_disclosure_tableab: total_contributions, total_expenditures, balance_end
itemized_transcribed  false everywhere (a Phase-A field; the live flag is `_meta.itemized`)
notes   per-filing verbatim observations

_meta.itemized  (added 2026-08-14; written ONLY by make_itemized_caches.py)
        wave, transcribed_date, record_file, variant, pages_read, itemized_pages_A/B,
        sides {contributions,expenditures} -> transcribed | withheld | none,
        withheld_reason, recon per side {stated, itemized, result, anchor, detail,
        published_stated, csv_reconciles, csv_delta}, page_subtotal_gates, escalations,
        escalation_note, n_contrib_rows, n_expend_rows, geometry {bbox_exact, estimated_band},
        screen_findings, notes
contributions / expenditures   the itemized rows themselves: line_no, page, row_i, date,
        donor_raw|vendor_raw, donor_city, donor_state (USPS code), purpose, amount, in_kind,
        needs_review, confidence, cell_confidence, verified, note, geometry, geometry_fit
```

**FOUR honest states, never conflated** (SLCo's vocabulary, same meanings):

| state | means |
|---|---|
| `sides.<side> = "transcribed"` + rows | the lines were read |
| `sides.<side> = "transcribed"` + ZERO rows | the schedule page exists and is **BLANK** — a real zero |
| `sides.<side> = "none"` | the document has no such schedule page — **non-existence, not zero** |
| `sides.<side> = "withheld"` + `withheld_reason` | columns could not be assigned or the read could not be finished — **no rows, no sum claimed** (currently 0) |
`value` is the string **as printed** (`"N/A"`, `"(331.75)"`, `"250."`); `""` = the cell is blank
on the face. `confidence` is per cell: `high` / `medium` / `""` (blank cell).
`text_layer_corroborated_lines` lists the lines whose transcribed figure also appears verbatim
in the born-digital `text/` sidecar — an independent, automatic cross-check (it is empty for the
scans and for handwriting, which is expected, not a defect).

### Still not built

`cycle_totals.csv`, `donor_aliases.csv`, `finance_overrides.csv`, and any `gov.db` federation.
**Do not derive a cycle total here without reading "The three things to get right" first** — the
regime is per CANDIDATE on the 2024/2026 sheet, and `cf_cycle` is city-only by repo design.
There is still **no shared form-family module for the two OLDER Wasatch sheets**
(`carr_5_5_pg_4line`, `wasatch_fcr_3line`); their 528 rows are vision-transcribed, which is the
right tool for handwriting and was cheaper than writing two parsers for pages whose text layers
are OCR of cursive.

## Provenance notes worth carrying

- **104 of 111 filings came from the government's own origin host.** The DNN host
  `wasatch.utah.gov` still serves its `Portals/` PDFs even though its pages now redirect to the
  CivicPlus site — so 2018/2020/2022/2024-June are origin-fetched, not archive-recovered. Only
  the 2024 general reports (retired Jadu CMS) required Wayback.
- **The county's own 2018/2020 form misprints its statute as `17-15-6.5`** (correct: 17-16-6.5).
  Retained verbatim — a source typo is data, not an error to fix.
- **A portal label can contradict the filing.** `S. Farrell Elimination Report` (2026-06) has
  BOTH the *Partisan Convention* and the *Withdrawal/Elimination* boxes checked on the form.
  Recorded as published + flagged in `notes`; not silently resolved.
- **The Farrell double-checkbox is not unique — "select only one" is widely ignored.** Of the
  **94 filings whose sheet even has a reporting-period selector** (the 17 Carr-form filings of
  2010 and 2022 print none at all), **6 mark more than one box** — Kaiserman 2024-06
  convention+primary, Park 2024-06 convention+primary, Bonner 2024-11 Sept-30+general,
  Kaiserman 2024-11 convention+general, Park 2024-11 Sept-30+general+year-end, Farrell 2026-06
  convention+elimination — and **13 mark none at all** (2018 Sweat; 2020 Griffin ×2; 2024 Gibbs,
  Adams-June, Hewlett ×2, Murray-general, Nelson, Bercuson-general; 2026 Granger-March,
  Murphy-March, Kahler-March). All are verbatim in
  `vision/<key>.json.cover.report_periods_checked`, where **`null` = the form prints no selector**
  and **`[]` = a selector is present and nothing is marked** — and each is flagged in the
  filing's `notes`. `index.csv.reporting_period` remains the county's published filing point.
- **Two filings' checked box contradicts the filing point index.csv assigns them:** Xela Thomas
  2020-06 checks *30 Days after withdraw or elimination* on a report published at the June
  pre-primary point, and Karl McMillan 2026-03 checks *Candidate Withdrawal/Disqualification/
  Elimination* on one published at the March partisan-convention point. Both kept as published
  and noted.
- **School-board and county candidates file the same form, to the same clerk, in the same
  folder.** Only the statutory citation (17-16-6.5 vs 20A-11-1301) or the *Name of Office* field
  separates them. That is how `out_of_scope.csv` was built, and it is why
  `disclosures.utah.gov/Municipal/wasatch_2012 Primary` — which looks like six county filings —
  is a county-office **zero**.
- **Privacy** follows the repo policy (root `PRIVACY.md`): `raw/` and `text/` are **verbatim
  reproductions of government-published documents and are not redacted**, including donor
  addresses printed on the face of a filing. Should a structured layer ever be built here, its
  rows must carry **donor city/state only**, never street addresses.

## Cardinal-rule specifics for the totals layer

1. **Blank is data, and it is never a zero — EXCEPT a glyph that denotes zero (owner ruling
   2026-08-02).** A slashed zero `Ø`, `-0-`, or the written word "zero" IS the filer writing
   the digit 0 and promotes to 0.00 (verbatim glyph kept in the cache): **Kahler 2026-03**'s
   Table A total, printed as the word *"zero"*, now yields `stated_total_contributions=0.00`
   (CORRECTED 2026-08-02: Table B CONTINUES to page 3, whose TOTAL row also prints 'zero' — found independently by both pilot contenders + the coordinator's page read; stated_total_expenditures=0.00 too. Only the balance stays blank — nothing states it). Everything else stands: 3
   filings state no contribution total and 3 no expenditure total, each with its reason in
   `notes` — **Hewlett 2024-06** writes `N/A` in all three cells; **Woodard 2026-06** puts a
   dash in the expenditure cell; **Jenkins 2020-06** and **Farrell 2020-06** fill only some
   lines. A non-zero-denoting non-number (`N/A`, a bare dash, an up-arrow *see-above* mark)
   is BLANK.
2. **Filer errors stand as filed.** Farrell 2020-12 prints a cumulative contribution total of
   3332.96 against 3337.96 on his own expense and balance lines; Wade 2018 prints a positive
   balance against zero contributions and $1,004.74 of expenses; Sweat 2022 prints the same
   $650.08 negative in June and positive in November; Granger 2020-06 states a NEGATIVE expense
   (−246.08); Adams 2024-11 prints a $135.55 balance against zero-and-zero; Rowland 2026-03
   prints a positive balance where the arithmetic is negative. None were corrected.
3. **Strikeouts are transcribed to the value that survives, and the fact is noted** —
   Yergensen 2010 (over a struck 535.36), Titcomb 2018 and Hewlett 2024-11 (a struck figure
   replaced with a circled 0), Farrell 2020-10 (party written over a struck "Republict").
4. **Two filings are published unsigned/undated** — McDonald 2010 (no signature) and
   Crittenden 2020-12 (neither signature nor date). Recorded in `cover.signed`.
5. **Never surname-join.** Several filers recur across cycles and offices, and two 2024 filers
   share a first name with a different 2020 filer. Resolve on full name (repo-wide rule); note
   also that `index.csv.candidate` is the county's published spelling while
   `vision.cover.candidate_verbatim` is the form face — they differ (e.g. "Joey D. Granger" vs
   "Joey Diane Granger", "Jami Smith Hewlett" vs "Jami Hewlett").
6. **`PRIVACY.md`:** campaign-finance text is never redacted, but the derived CSVs carry no
   street addresses or phone numbers — only `residence_city` in the cache. The `raw/` scans are
   unaltered.

## Joins (what is and is not possible today)

There is **no `wasatch_county` election-results layer, no roster, and no db** — the entity is
registered-only. Within this module, join on `candidate` + `election_year` (+ `office`/`seat`).
Cross-entity, the useful edge is **Park City**, which straddles Summit and Wasatch; Park City's
canvass is run by **Summit** (`summit_county/elections/`), so nothing here joins to it directly.
Note also that several filers recur across cycles and offices (Granger 2020/2022/2026;
Rigby 2018-declaration/2022/2026; Sweat 2010/2018/2022; Crittenden 2018/2020/2024;
Rowland 2022/2026) — resolve people by **full name**, not surname (repo-wide rule).

## Refresh

The 2026 cycle is **open**: general reports are due **2026-10-28** and finals **2026-12-03**.
Re-run after December 2026 against `wasatchcounty.gov/elections`, then
`python3 extract_text.py && python3 build_index.py && python3 refetch.py`.

New filings need a **vision cover transcription** before they appear in `filing_totals.csv` —
`build_finance.py` HARD-FAILS on any `index.csv` row without a `vision/<sha1(path)[:8]>.json`
cache (silence is not an option here). Transcribe with `/cf-vision-transcribe` (Read-tool
method, $0 API), then `python3 build_finance.py && python3
scripts/campaign_finance/validate_finance.py wasatch_county/campaign_finance`.

To ITEMIZE a new filing, write a transcription record under the Phase-B contract
(`_backups/2026-08-14-tranche3-phaseb/wasatch/AGENT_BRIEF.md`) and run
`make_itemized_caches.py <records_dir>` before `build_finance.py`. A born-digital 2024/2026 sheet
may need nothing: `build_finance.py` already hands every `wasatch_disclosure_tableab` filing to
the registered family, and where the family reconciles a side the row set is published
automatically. `wave_stats.py --residue` lists any filing with no itemized layer at all.
