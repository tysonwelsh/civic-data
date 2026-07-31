# Vineyard campaign-finance disclosures

Municipal candidate **campaign-finance filings** (contributions & expenditures) for Vineyard
City, retrieved as documents + a filing-level index. This closes the
**elections → members → votes** chain: who funded the people who cast the roll-call votes in
`../meeting_minutes/all_votes.csv`. Built by the `expand-city-sources` skill (Source 6).

**Scope:** documents + `index.csv` AND (as-of **2026-07-06**) a **structured contribution /
expenditure / filing-totals layer** — see "## Structured layer" below. The raw PDF remains the
authoritative record; the structured CSVs are DERIVED and every figure is reconciled or honestly
flagged, never asserted beyond what the form prints.

```
raw/<cycle>/       filing PDFs verbatim, View-id/period-prefixed + _fetch_log.jsonl (provenance)
text/<cycle>/      one text sidecar per filing (pdftotext born-digital; tesseract OCR scanned)
index.csv          one row per filing (see columns below)
build_index.py     idempotent: OCR -> sidecars -> index.csv, joined to election_results/
AVAILABILITY.md    every host tried, per-cycle coverage, the 2023 hole, honest gaps
discovery/         CDX enumerations + fetch plan (reproducibility)
```

## What's here (59 filings, 5 cycles)

| Cycle | Filings | Source | Read the caveat |
|------:|--------:|--------|-----------------|
| 2015 | 16 | Wayback (dead CivicPlus DocumentCenter) | pre-2019 floor; office **inferred** |
| 2017 | 11 | Wayback | pre-floor; office inferred (Fullmer=Mayor verified) |
| 2019 | 13 | Wayback | 7 council candidates; 3 PDFs archive-truncated (unreadable) |
| 2021 | 16 | Wayback | **complete** mayor+council; 1 PDF truncated |
| **2023** | **0** | — | **UNRECOVERABLE** — filed but purged pre-archival; see AVAILABILITY.md |
| 2025 | 3 | Live `vineyardutah.gov` | only 2 primary-losing council candidates posted a statement |

**Vineyard self-hosts** on the city website — no EasyVote, no `disclosures.utah.gov` (both
verified absent). Legacy filings (2015–2021) survive only in the Internet Archive; the old
`vineyardutah.org` Document Center is dead. See `AVAILABILITY.md` for the full host list and
the 2023 hole.

## index.csv columns

`date, title, source_url, retrieved_date, format, extraction_method` (the six required) plus:
- **candidate** — display name; **office** — Council/Mayor; **election_year** — cycle;
- **filing_type** — `interim` (pre-primary / pre-general statement) or `summary` (final,
  ~30-day post-election report). Vineyard's form is a single combined
  contributions+expenditures sheet, so there are no separate `contribution`/`expenditure`
  filing types in practice.
- **reporting_period** — (§9 contract column; blank where not recorded)
- **path** — repo-relative, always under `raw/<cycle>/`.
- **matched_election_candidate / join_confidence** — join to
  `../election_results/vineyard_results_by_candidate.csv`. `exact` = joined (all 2019+);
  `pre_floor` = 2015/2017, no election row by design (not a defect).
- **office_confidence** — `verified` (2019/2021/2025, from election_results + repo notes) or
  `inferred` (2015/2017 offices, from public record).
- **date_precision** — `exact` (date in the PDF/filename), `deadline` (statutory due date
  printed on the 2025 form), or `cycle` (anchored to the report class's statutory deadline
  for that cycle — **not** the exact filing timestamp; treat as approximate).
- **redacted** — `yes` if the city posted a redacted copy (some 2019/2021 filings exist in
  both redacted and unredacted form — both retained as distinct rows).
- **source_archive** — `wayback` or `live`.

## How to use

- **"Who funded councilmember X?"** — filter `index.csv` on `candidate`, read the matching
  `text/<cycle>/*.txt` for the contribution/expenditure totals. Join to voting via
  `matched_election_candidate` → `../election_results/` → `../meeting_minutes/all_votes.csv`
  (normalize case: election/finance names differ in case).
- **Aggregates** are NOT precomputed — this layer is documents+index. Don't sum dollars from
  `index.csv` (it has none); the figures are in the sidecars only.

## Cardinal rules honored

- **Never fabricated.** 2023 = honest empty (documented). 4 truncated PDFs = labelled
  `unreadable`, not silently dropped. 2025's missing statements = a real city gap, recorded.
- **`election_results/` is never edited.** Finance data that reaches below the 2019 election
  floor (2015/2017) or would imply a record gap is **flagged in AVAILABILITY.md**, not
  back-written.
- **Raw retained verbatim** with per-fetch provenance (`_fetch_log.jsonl`: url, status,
  bytes, sha256).

## Structured layer (contributions / expenditures / filing_totals) — as-of 2026-07-06

Additive, DERIVED money layer built by the shared framework in `scripts/campaign_finance/`.
Contract: `scripts/campaign_finance/SCHEMA.md`. Rebuild: `python3 build_finance.py` (idempotent;
re-reads `vision/*.json`, never re-calls the API for a cached filing). Validate:
`python3 ../../scripts/campaign_finance/validate_finance.py .` → **PASS** (0 fails).

- **contributions.csv** 108 rows · **expenditures.csv** 127 rows · **filing_totals.csv** 59 rows.
- **SCOPE — all 59 filings are in-scope campaign C&E reports** (Vineyard hosts no separate COI genre).

### Form family — `utah_standard_form` REUSED (Orem's family, unchanged)
Vineyard files the **same statutory Utah municipal "Municipal Campaign Financial Disclosure" form
(UCA 10-3-208)** Orem/Logan/Nephi use, so it **reuses `families/utah_standard_form.py` UNCHANGED** —
no family edit; all 7 prior cities re-validate + re-build with identical counts (provo 741/1009/41,
west_jordan 366/548/43, lehi 422/300/134, sandy 1261/813/83, orem 1011/806/91, logan 309/166/45,
nephi 50/141/42). Vineyard is the **MIXED case like Orem** (born-digital + scanned), but its form is
a **FILLABLE PDF whose typed values render irregularly** — this is the Vineyard-specific reality and
is handled entirely in `build_finance.py` via `meta["form_opts"]` + a driver-local cover reader, NOT
in the shared family:
- **Cover totals FLOAT** — above, below, or inside the `$ ____` underscore field (`$ ___$3,848.00___`,
  a bare `5094.24` on the line ABOVE the label, `1451.50` on the line BELOW), across **three cover
  layouts** (2015 / 2019 / 2021-2025). A driver-local **`_robust_cover`** follows the floating value
  and **strips the printed `$50.00`/`$500.00` statutory THRESHOLD** so it is never read as a value.
- **Itemized amounts are often BARE** (no `$`, e.g. Welsh `250`/`1520`) and/or in **multi-line cells**
  (donor name on a different text line than the amount). The anti-fabrication `$`-anchored tokenizer
  (correctly) will not read bare numbers, and the family's own threshold-blind numbered-headline
  fallback would fabricate a total from the `$500` thresholds — so **`form_opts` sentinels the section
  headers AND the l1/l2/l3 fallback OFF for the scanned path**; a scanned stated total comes ONLY from
  its (threshold-aware) vision transcription. This is why a naive family parse would false-nil a real
  filing; it never does here.

### Modes — born-digital direct + gated vision (the Orem/Logan pattern)
- **16 born-digital** (`format=text`, pdftotext): the family (sections ON) captures the clean
  `$`-anchored rows and `_robust_cover` supplies the stated totals. **8 reconcile by DIRECT parse**
  (nil / simple filings — e.g. all 3 Brimhall filings, Jenkins-final, Booth). The **other 8 carry
  itemized content** and were **escalated to vision** — NOT for the amounts (the born-digital parse
  reconciles them) but because Vineyard's fillable form floats the donor NAME onto a different text
  line than the amount, so the born-digital `donor_raw` captures the *address* line (e.g. Jenkins →
  `459 East Rue Cournot`); vision restores correct donor identity.
- **39 scanned** (`format=scanned`, tesseract; typed scans + handwritten) → OCR reconciles the rows
  0/39 (rows OCR to garbage / `$`-less handwriting), so **vision is the primary itemization path**,
  exactly like Logan/Nephi.
- **Vision (GATED):** `vineyard_vision_extract.py`, `pdftoppm -jpeg` @150 DPI into a WORKING DIR
  (`vision/_tmp`, never `/tmp`), model **`claude-sonnet-5`**, strict "transcribe EXACTLY / mark
  illegible null / never infer" prompt; cached to `vision/<doc8>.json` (doc8 = sha1(path)[:8]), fed
  back through the SAME reconciliation via the driver `rows_override_fn` (`extract_method=…/vision`).
  The vision stated-total anchor is the ITEMIZED (Form A/B) total, NOT itemized+aggregate (the ≤$500
  aggregate is unitemized → recorded in the note, Orem/Nephi discipline). **47 filings vision-
  processed** (45 first run + 2 born-digital re-runs for donor fidelity), **93 pages, ≈$1.88 total**
  (~320k input + ~61k output tokens, Sonnet list price).
- **The 4 archive-truncated filings** (`extraction_method=unreadable:*` — 1-MiB Wayback truncations:
  Lauret 2019 interim, Flake 2019 interim + summary, Cane 2021 interim) cannot be read — `pdftoppm`
  renders 0 pages, so they emit an **honest all-blank filing_totals row** (blank stated + itemized,
  `needs_review`, `low`, note "archive-truncated … unreadable"). NEVER fabricated. Flake 2019 has no
  readable filing in either report; the others have a readable companion (Lauret summary; Cane summary).

### Reconciliation — 35 of 59 both-reconcile; the 24 flagged are all honest (`low`+`needs_review`)
- **4 truncated** — honest blanks (above).
- **13 totals-only / aggregate-only "unknown"** — a candidate stated a figure with NO itemization: the
  **≤$500 small-donor aggregate** under Utah's exemption (Cane $257, Pacheco $448.60, Judd, Fullmer/…)
  or a stated side vision could not itemize (handwriting). The itemized side reconciles UNKNOWN (blank),
  the aggregate is recorded in `notes` — never synthesized as fabricated rows.
- **7 genuine SOURCE discrepancies** kept verbatim (the "internally inconsistent source stays flagged"
  discipline): **Shawn Herring 2017** (his cover Form-A total $5,094.24 but his own 5 rows sum
  $4,979.24 → −$115 candidate arithmetic error; vision transcribed the 5 rows EXACTLY, matching the
  born-digital text); **Steve Terry 2025** (his 3 expenditure rows sum $1,405.57 incl. a $759 line but
  his cover 2b states $1,395.57 → +$10 source inconsistency, `$759` confirmed verbatim in the raw PDF);
  **Keith Kuder 2019** (rows $13,230 vs his stated Form-A total $14,529.06); **Tay Gudmundson 2019**
  (±$36.05 both sides, redacted handwritten); **G. Tyce Flake 2015** (+$100 expend); **Randy Farnworth
  2017** (−$0.22 cents); **Terry Ewing 2025** ×2 (handwritten; vision misread the cover 1b as `$0.60`
  vs the true $1,447.70 self-fund row — left flagged, NOT force-corrected).

### Dedup — INCREMENTAL throughout (empirically determined, per candidate)
`is_incremental` is set PER `(candidate, election_year)` from consecutive-report contribution-row
overlap (`_classify_modes`, like Logan/Nephi). **All 108 rows came out `is_incremental=True`**: every
Vineyard interim+summary pair covers a DISCRETE period and the summary/final report is almost always
NIL (nothing new after the election — a cumulative final would restate the whole cycle), so a cycle
total is the **SUM** of a candidate's period reports. `dedup_mode=None` (no supersession asserted); no
amendment labels exist in the Vineyard set. **No duplicate filings to merge.** Note only **2019/2021/
2025** join elections; **2015/2017 are pre-floor** (`index.csv join_confidence=pre_floor` — still fully
structured); **2023 is unrecoverable** (0 filings).

### donor_type distribution (108 contribution rows)
individual 64 · candidate-self 24 · business 16 · family-of-candidate 3 · pac 1 · **unknown 0**.
**18 in-kind** rows · **0 blank-donor rows** (every transcribed row carries a name). **14 filings carry
self-funding.** `donor_aliases.csv` carries **5 curated, evidenced overrides**: three Vineyard `(self)`
self-funding designations the conservative tier-1 classifier missed on the `(self)` token (Steven Terry,
Shawn Herring, Region Engineering → candidate-self) and two org donors (ProSoft; UVRA = Utah Valley
Realtors Association → business). `finance_overrides.csv` is header-only.

### Hand-verification (6 filings, line-by-line vs the raw PDFs, 2026-07-06)
| filing | mode | check | result |
|---|---|---|---|
| Mardi Sifuentes — 2021 interim | born-digital → vision | 9 contrib (2 in-kind) + 16 expend | ✓ Σcontrib **$6,510.00 = 1b**; Σexpend **$6,424.35 = 2b**; NHE Investments LLC / Crunchy Lemons in-kind classified right; both reconcile |
| Steve Terry — 2025 interim | born-digital → vision | 6 contrib (3 self) + 3 expend | ✓ Σcontrib **$1,451.50 = 1b**; expend Σ **$1,405.57** vs stated **$1,395.57** → flagged +$10; the `$759` line is verbatim in the raw PDF (candidate arithmetic inconsistency, not an extraction error) |
| Shawn Herring — 2017 interim (V1004) | born-digital → vision | 5 contrib | ✓ vision rows (ProSoft/Anne&Jett Lee/Teri Nelson/Region Eng/Shawn Herring) Σ **$4,979.24** EXACTLY match the born-digital text; his cover Form-A total says **$5,094.24** → **−$115 = his own error**, honestly flagged |
| Kristal Price — 2021 interim (redacted, handwritten) | scanned → vision | 16 contrib (2 in-kind, 1 self) + 14 expend | ✓ Σcontrib **$3,320.95**; Σexpend **$3,104.63**; both reconcile against the cover; Steve Smart in-kind graphics classified right |
| Anthony Jenkins — 2019 interim | born-digital → vision | 1 contrib + 1 expend | ✓ Σ **$36.05 = line 3**; born-digital parse had captured the *address* (`459 East Rue Cournot`) as donor — vision restored **Anthony Jenkins (candidate-self)** |
| Marc Brimhall — 2021 summary | born-digital DIRECT | nil filing | ✓ blank cover typed `$0` throughout → stated **$0/$0**, 0 rows, reconciles nil, `high` — no vision needed |

### Rebuild / correct
`python3 build_finance.py` (idempotent). Re-run vision for one filing: delete its `vision/<doc8>.json`
and run `python3 vineyard_vision_extract.py [<doc8> …]` (or `--all`). Corrections →
`finance_overrides.csv` / `donor_aliases.csv` (never hand-edit the derived CSVs).

## Refresh

Re-probe the two live candidate pages for new `government/docs/*Financial*Disclosure*` /
`*Finance*Statement*` links (they accrete through an election year — 2025 general/final
statements may post after this build), drop new PDFs in `raw/2025/`, rerun `build_index.py`.
For any future re-publication of 2023, drop into `raw/2023/` and rerun.
