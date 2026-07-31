# campaign_finance/ — Ogden municipal candidate financial disclosures

Additive dataset built by the `expand-city-sources` skill (**Source 6**), as-of
**2026-07-05**. Does **not** modify any existing dataset. Completes the **elections →
members → votes** chain: who funded the candidates whose roll-call votes live in
`../meeting_minutes/` and `../planning_commission/`, and whose wins are in
`../election_results/`.

## What this is
**38 municipal "Combined Report of Contributions & Expenditures" filings** by Ogden
**Mayor + City Council** candidates for the **2019 (7), 2021 (13), 2023 (18)** cycles.
Each PDF is a single packet bundling that candidate's whole-cycle statutory reports
(First/Second/Third/Final, each = contributions Attachment A + expenditures Attachment B +
summary sheet). Raw PDFs retained verbatim in `raw/<year>/`; a text sidecar for every
filing in `text/`. **The 2025 cycle is a verified gap — not yet published by the city**
(see `AVAILABILITY.md`).

## Where the data comes from (full source log in `AVAILABILITY.md`)
Ogden **self-hosts** its disclosures on the **City Recorder's Election-Information pages**
(CivicPlus `ogdencity.gov`; legacy `ogdencity.com` links 301 there). The state site
(`disclosures.utah.gov`) has **no Ogden entry**; Ogden does not use EasyVote. One page per
cycle links each candidate's report as a `DocumentCenter/View/<id>` PDF:
- **2019** — `ogdencity.com/1624/2019-Elections` (View 31386–31392)
- **2021** — `ogdencity.com/2589/2021-Elections` (View 17252–17495)
- **2023** — `ogdencity.com/2048/2023-Elections` (View 30766–30783)

All downloaded live via `polite_fetch.py` (GET-only, logged). No Wayback was needed.

## Layout
```
raw/
  2019/ 2021/ 2023/     the filing PDFs, each <ViewId>_<orig-slug>.pdf, + _fetch_log.jsonl
  index_pages/          the 4 source HTML pages (3 year pages + Financial-Reports hub) + log
  <year>/_batch.tsv     the url<TAB>name download lists (build input)
text/                   one .txt sidecar per filing (pdftotext -layout OR tesseract OCR)
manifest.json           candidate→viewid→office/district map (build input; page-transcribed)
index.csv               one row per filing (schema below)
build_index.py          regenerates text/ + index.csv from manifest.json + raw/ (idempotent)
AVAILABILITY.md         every host/URL tried, per-year coverage, the 2025 gap, join report
```

## `index.csv` schema
Required minimum columns (`date,title,source_url,retrieved_date,format,extraction_method`)
plus source-specific columns:

| column | meaning |
|---|---|
| `date` | `YYYY-01-01` for the election year. **Approximate** — the combined packet spans the whole cycle; exact statutory due dates are printed inside each PDF. |
| `candidate` | filer name as published on the year page (mixed case). |
| `office` | `Mayor` / `Council`. From `election_results` where matched, else the year page's candidate heading. |
| `election_year` | 2019 / 2021 / 2023. |
| `filing_type` | `summary` (all — these are the combined full-cycle packets, not separate schedules). |
| `reporting_period` | (§9 contract column; blank where not recorded) |
| `title` | human label. Placeholder stubs are marked in the title. |
| `source_url` | the `DocumentCenter/View/<id>/<slug>` URL as published (`.com`; 301→`.gov`). |
| `retrieved_date` | (§9 contract column; blank where not recorded) |
| `format` | `text` (14 born-digital, real text layer) / `scanned` (24 image-only, OCR'd). Measured from the actual text layer, not the file extension. |
| `extraction_method` | `pdftotext -layout` (14) / `tesseract OCR (pdftoppm 300dpi)` (24). |
| `path` | repo-relative path to the retained PDF (`raw/<year>/…`). |
| `district` | Council seat: `1`/`2`/`3`/`4` or `At-Large A/B/C`; blank for Mayor. |
| `source_page` | the year Election-Information page the filing was linked from. |
| `matched_election_candidate` | canonical `election_results` name this filer joins to (blank if none). |
| `join_confidence` | `exact` (20, normalized name+year match) / `none` (18 — primary-eliminated filers not in `election_results`). |
| `is_winner` | `True` if the matched `election_results` row won (else `False`/blank). |
| `placeholder` | `yes` for the 2 city-posted "Financial Report Place-holder" stubs (2021 Reyneveld, Barnes) — near-empty forms, retained as honest "filed but empty". |

## Join to `election_results/` (see `AVAILABILITY.md` for the full report)
Join by **normalized name + election year** to
`../election_results/ogden_results_by_candidate.csv`. **20/38 filings** match a general
candidate (`exact`); the **18 `none`** are all **primary-eliminated** filers (Ogden ran
primaries each cycle — `election_results` records the general only). Reverse: **20/28**
`election_results` candidates have a filing — the **8 without are all 2025** (the gap). For
**2019–2023, coverage is 20/20 = 100%, all 12 winners included.** From a winner here, their
council roll-call votes are in `../meeting_minutes/all_votes.csv` (join by person; the
mayor does not vote — see `../CLAUDE.md`).

## Caveats / do-nots
- **`date` is the election year, not the exact due date** — the packet spans the cycle. Read
  the raw PDF for the printed statutory dates.
- **`index.csv` carries NO dollar figures.** For amounts use the **structured layer** (below):
  `contributions.csv` / `expenditures.csv` / `filing_totals.csv`, and `cycle_totals.csv` for a
  per-candidate race total. Never quote money from `index.csv`.
- **18 `join_confidence=none` rows are real candidates, not errors** — they are primary
  filers absent from the general-only `election_results`. Flagged in `AVAILABILITY.md` for a
  future `election_results` review; this dataset does not alter `election_results`.
- **2025 is a documented gap**, not an empty result — the city had not published the 2025
  cycle as of 2026-07-05 (verified four ways in `AVAILABILITY.md`; queued in `../../TODO.md`).
- **2013 & 2015 filings exist and are live but were out of scope** (2019–2025 requested);
  noted in `AVAILABILITY.md` for a possible future backfill.

## Rebuild
`python3 build_index.py` — idempotent; reads `manifest.json` + the PDFs in `raw/`, writes
`text/` sidecars (reusing existing OCR) and `index.csv`. Re-fetch raw via
`python3 ../../.claude/skills/expand-city-sources/scripts/polite_fetch.py --out raw/<year> --batch raw/<year>/_batch.tsv --delay 2 --now 2026-07-05T00:00:00Z`.
Validate: `python3 ../../.claude/skills/expand-city-sources/scripts/validate_dataset.py .` → **PASS**.

## Structured layer (`contributions.csv` / `expenditures.csv` / `filing_totals.csv` / `cycle_totals.csv`)

DERIVED, regenerable money layer built from the `text/` sidecars by `build_finance.py` (shared
engine `../../scripts/campaign_finance/`). Additive; does not touch the CORE index/documents.
Contract: `../../scripts/campaign_finance/SCHEMA.md`. **Regenerate, never hand-edit** — corrections
go through `donor_aliases.csv` / `finance_overrides.csv`.

- **Form family: `ogden_form`** (new — `families/ogden_form.py`), NOT `utah_standard_form`. Ogden's
  "Combined Report" is a **whole-cycle packet** that concatenates a candidate's First/Second/Third/
  Final statutory reports, each = numbered SUMMARY box (lines 1–6) + `ITEMIZED REPORT OF CAMPAIGN
  CONTRIBUTIONS` (Attachment A) + `…EXPENDITURES` (Attachment B), so those section headers repeat
  N× per file (utah_standard_form finds each once). **In-kind is a per-row flag** ("Yes" column /
  purpose "In-Kind"), not a separate section. Two column layouts (older `Date/Name/Address/Amount/
  Purpose`; 2023 wide `Date/First/Last/Address/City/State/Zip/Amount/Purpose`) + appended exported
  ledgers (Mata) are all handled. `is_incremental=False` (the packet already aggregates the whole
  cycle → one filing per candidate-cycle, Provo-like; `dedup_mode=None`).
- **Reconciliation anchor** = per side, Σ(itemized rows) vs Σ(the packet's printed attachment
  TOTAL lines). Money token = a `$`/`($ …)` figure OR a bare `.dd` decimal capped at 5 leading
  digits (so a zip glued to an amount can't form a mega-number); a purpose-embedded threshold
  phrase ("Donation of $50 or less") is neutralized before amount detection. Born-digital filings
  whose itemization is an appended ledger with no attachment TOTAL fall back to the SUMMARY box
  line 4 (contributions) / line 5 (expenditures) — the form's own printed totals.
- **Completeness guard (born-digital):** these are Adobe fillable forms; some pages' text layer is
  corrupted (amounts render as lone `s`/garbage) and a whole sub-report's itemization can vanish,
  which would FALSELY reconcile on the surviving subset. When the SUMMARY box states materially more
  (> $1k AND > 50%) than the captured attachment TOTALs, the summary figure is adopted as the stated
  total so the filing honestly **flags as incomplete** (note `incomplete extraction…`) rather than
  silently undercounting — Nadolski 2023 (below) and Martinez 2021.

### Counts / reconciliation (as-of 2026-07-12)
- **contributions.csv 1,269 rows · expenditures.csv 873 rows · filing_totals.csv 38 rows** (1/filing).
- **25 / 38 filings both-sides reconcile clean; 13 flagged** (all rows `needs_review=1` + `low`).
- **cycle_totals.csv: 38 candidate-cycles, 0 review_flags** (each is one whole-cycle packet →
  `basis=summary`). **Read `cycle_totals.csv` for a candidate/race total — never sum filing_totals.**
- `donor_type`: individual 768 · unknown 213 · family-of-candidate 47 · candidate-self 18 ·
  business 16 · pac 7 · loan 3 · party 1.
- **Dedup rule:** one filing per candidate-cycle (the packet is the whole cycle), so no cross-filing
  supersession; `cycle_totals.py` treats each as the single cumulative summary.

### Gated vision (`vision_extract.py` → `vision/<viewid>.json`, `claude-sonnet-5`)
Only SCANNED filings that fail OCR reconciliation are escalated (born-digital never). Pages rendered
`pdftoppm -jpeg` 120dpi; strict "transcribe exactly, mark illegible null, do NOT infer/sum"; the
model returns each printed TOTAL verbatim and **build_finance sums them** (never the model). Fed back
through the SAME reconciliation via the driver `rows_override_fn`, so vision earns confidence only if
it reconciles; unreconciled vision output stays `low` + `needs_review`, never forced. **12 filings
vision-transcribed 2026-07-06 (~$1.7 API)**; the **5 remaining large scanned filings (Castillo-2019
31387 53pp, Graf 30773 27pp, Van Wagoner 30783 22pp, Andersen 30766 20pp, Myers 30779 20pp = 142pp)
were transcribed 2026-07-12 via the Read-tool method** (`/cf-vision-transcribe`, $0 API): 12 parallel
page-range agents wrote partials to `vision/_partials/` (kept for audit), merged into the flat
`vision/<docid>.json` caches. Notes:
- **Castillo 31387 bundles ORIGINAL + AMENDED versions of four reports.** The packet's own balance
  chain proves the amended set operative (the final Dec-5 report carries forward 22,482.48 = the
  amended chain's ending; the original chain's 19,625.27 is continued by nothing), so the cache sums
  ONLY the operative reports (amended Aug-6/Sept-12/Oct-29/Nov-4 + final Dec-5) — including the
  superseded originals would double the cycle to ~$100k. Fully documented in the cache `notes`;
  the originals' rows remain transcribed in `vision/_partials/31387_p29-41.json` / `_p42-53.json`.
  Reconciles 0.00/0.00 both sides: **raised 50,701.56 / spent 32,991.11**.
- **Graf 30773** writes handwritten amounts in ledger-dash shorthand (`100.-` = 100.00) —
  normalized deterministically in `_vmoney` (the cache keeps the verbatim string). Honest flags:
  contrib +99.70 (one overwritten digit on the Weil row) + expend +0.06 (the source total's own
  misprint).
- **Van Wagoner 30783**: expend exact; contrib flagged +2,530.00 = 1,530 of in-kind rows the printed
  schedule TOTALs exclude + a **$1,000 filer arithmetic error** on the Sept-25 schedule (its 9 rows
  sum 3,870 but the form prints 2,870, and the error is carried into the summary sheet) — verified
  against the page image, kept verbatim.

### Hand-verified against raw PDFs (5, 2026-07-06)
| filing | mode | check |
|---|---|---|
| Mata 2023 (Mayor) | born-digital | summary line-4/5 `$74,567.43` / `$73,193.50` = stated; rows reconcile ✓ |
| Castillo 2023 (Mayor) | born-digital | attachment TOTALs `1,135.00+26,920.00=28,055.00` / `3,508.01+24,194.59=27,702.60` = stated ✓ |
| Nadolski 2023 (Mayor) | born-digital | reports print `10,200+325+100,272.47=110,797.47` / `21,686.98+30,635.98+72,371.10=124,694.06`; report #3's Attachment tables absent from the text layer → correctly flagged **incomplete** (itemized only 10,525 / 52,323) ✓ |
| Bart Blair 2021 (Council At-Large B) | vision | printed totals `1,800.00` / `4,021.11` = stated; one illegible report total kept `null`; reconciles ✓ |
| Ken Richey 2021 (Council Dist 3) | vision | printed totals sum `12,620.80` / `11,858.45`; vision rows `12,555.80` / `11,828.45` (−65 / −30 over 40+22 rows) → honestly **flagged**, not forced ✓ |

### Rebuild
`python3 build_finance.py` (idempotent; reads `index.csv` + `text/` + any `vision/*.json`), then
`python3 ../../scripts/campaign_finance/cycle_totals.py ogden`. Validate:
`python3 ../../scripts/campaign_finance/validate_finance.py .` → **PASS (0 fails, 0 warns)**. Vision
backfill: `python3 vision_extract.py [<viewid>…]`.
