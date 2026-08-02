# campaign_finance/ — Utah County COUNTY-OFFICE candidate financial disclosures

Additive dataset, as-of **2026-08-01** (Package B of the county acquisition wave). Does **not**
modify any existing `utah_county/` dataset and is **not** federated into `gov.db` — it is a
document + provenance + **stated-totals** layer.

> **2026-08-01 — VISION-TRANSCRIPTION PASS (cover page + stated totals).** Every one of the
> 267 acquired filings has been read *from the page* by Claude vision (`/cf-vision-transcribe`,
> Read-tool method, **$0 API**) and now has a curated transcript in `vision/<key>.json`. Three
> things changed as a result: a **`filing_totals.csv` money layer exists** (265 rows — the old
> "no structured layer" statement below is superseded); the **19 unresolved offices are
> adjudicated** (8 promoted, 4 proved school-board and dropped, 7 honestly unresolved); and
> `index.csv` is now **263 rows**, not 267.
>
> **2026-08-02 — THE MACHINE-READABLE ITEMIZED LAYER (TRANCHE 3 Phase A).** The registered
> `utahcounty_schedab` family was wired in for the **17 filings whose text layer is real**
> (`index.format == 'text'`, i.e. `pdftotext -layout` — never an OCR sidecar). **2 of the 17
> ship: 72 contribution + 81 expenditure rows** (Tanner Ainge 2018, Isaac Paxman 2026), 100%
> carrying `geometry`. Every other side emits **nothing** with a stated reason. **The
> handwritten 245 remain unitemized** — *not transcribed*, never *no donors*.

**The repo's first COUNTY campaign-finance dataset.** All 31 existing `campaign_finance/`
datasets are municipal; this one is county-office, files under a different statute
(**Utah Code 17-16-6.5**, filed with the *County Clerk*) and on a different form.

## What this is

**263 campaign financial reports filed by Utah County COUNTY-office candidates, 2008 → 2026** —
every cycle the county has ever published. Offices: Board of Commissioners (Seats A/B/C),
County Attorney, Clerk / Clerk-Auditor / Auditor, Sheriff, Assessor, Recorder, Treasurer,
Surveyor. **Local school board, judicial retention and municipal filers are OUT of scope** and
are ledgered in `out_of_scope.csv` (93 rows), not retained.

*(267 filings were acquired; the 2026-08-01 vision pass proved **4** of them local-school-board
filers from their own Office field, so they moved to `out_of_scope.csv`. Their transcripts stay
in `vision/` as the evidence for the exclusion. The per-cycle table below is the pre-exclusion
acquisition count and is kept as the acquisition record; the four dropped filings are all 2022
`(office unresolved)` rows.)*

| | 2008 | 2010 | 2012 | 2014 | 2016 | 2018 | 2020 | 2021 | 2022 | 2024 | 2026 | total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Commission A | | 8 | | 7 | | 7 | | | 12 | | 7 | 41 |
| Commission B | 1 | 7 | | 12 | | 3 | | | 7 | | 8 | 38 |
| Commission C | | | 8 | | 8 | | 10 | | | 9 | | 35 |
| Commission (seat unresolved) | 1 | | | | | | 1 | | 1 | | | 3 |
| Attorney | | 4 | | 5 | | 5 | | | 9 | | | 23 |
| Recorder | | 5 | | 4 | | | 8 | | | 4 | | 21 |
| Sheriff | | 3 | | 4 | | 5 | | | 8 | | | 20 |
| Clerk | | | | | | | | 1 | 9 | | 3 | 13 |
| Auditor | | | | | | | | | 9 | | 2 | 11 |
| Clerk/Auditor | | 2 | | 4 | | 4 | | | | | | 10 |
| Surveyor | | 4 | | 3 | | | 2 | | | 3 | | 12 |
| Treasurer | | 2 | | 5 | | | | | 1 | 3 | | 11 |
| Assessor | | 4 | | 3 | | | | | | 3 | | 10 |
| *(office unresolved)* | | | | | | | 4 | 1 | 13 | 1 | | 19 |
| **total** | **2** | **39** | **8** | **47** | **8** | **24** | **25** | **2** | **69** | **23** | **20** | **267** |

82 distinct candidate-cycles. **Odd years carry nothing by design** — county offices are elected
on the even-year partisan cycle; the sole exception, the **2021 County Clerk/Auditor special
election**, is present (2 filings).

## Layout

```
RECON.md            the channel map + exhaustive probe log, written BEFORE acquisition
AVAILABILITY.md     what each source had; the honest-gap ledger; scope + privacy notes
raw/<year>/         the retained filings, verbatim, + a per-year _fetch_log.jsonl
                    (url, fetch_url, http status, bytes, sha256, retrieved_utc, channel)
raw/index_pages/    26 LISTING artifacts kept as evidence: 7 Wayback <YEAR>Disclosures.html,
                    6 predecessor .asp pages, the 2020 name.asp set, the JS listing page,
                    disclosure.js (the API + token), the portal Google Sheet (xlsx + csv),
                    the full API JSON, and 5 disclosures.utah.gov state pages
text/               one .txt sidecar per acquired filing (266) — a FINDING AID, not a
                    transcript (see "Do-nots"); superseded for money by vision/
vision/             CURATED — 267 vision transcripts, one per ACQUIRED filing, keyed
                    sha1(index.csv `path`)[:8]. The authority for every figure below
index.csv           DERIVED — one row per RETAINED FILING (263), deduped by sha256
filing_totals.csv   DERIVED — one row per FILING/REPORT (265), SCHEMA.md §4
contributions.csv   DERIVED — the machine-readable itemized layer, 72 rows (+ `geometry`)
expenditures.csv    DERIVED — ditto, 81 rows
out_of_scope.csv    93 school-board filings: fetched, classified, ledgered, NOT retained
unrecovered.csv     4 items that could not be fetched, with the reason
office_overrides.csv  CURATED, evidence-cited office corrections (21 rows; 14 APPLIED)
batch/manifest.json   build input for build_index.py
build_index.py        regenerates index.csv; `--check` verifies every sha256 on disk
build_finance.py      regenerates filing_totals/contributions/expenditures from vision/
```

## Which artifact for which question

- **"Who filed, for what office, in which cycle, and where did it come from"** → `index.csv`.
- **"What did this candidate report raising / spending"** → **`filing_totals.csv`** (one row per
  filing/report; the figures are the form's own printed totals). Read "THE PROMOTION REGIME"
  below before adding rows together, and treat `notes` as part of the value.
- **"What exactly does the page say"** → **`vision/<sha1(path)[:8]>.json`** — the curated
  transcript, with every line/box under its own printed label, per-field confidence, and an
  explicit `unreadable` list. Then open `raw/<year>/<file>` for the image itself.
- **"Who donated / what did they buy"** → `contributions.csv` / `expenditures.csv`, but only
  for **2 of 263 filings** (Ainge 2018, Paxman 2026). Everywhere else the answer is still
  "open the raw PDF": the forms are handwritten and this module never quotes a figure off an
  OCR sidecar. See "The machine-readable itemized layer" below.
- **"Was anything missed"** → `AVAILABILITY.md` §4 / §4a + `unrecovered.csv` + `out_of_scope.csv`.
- **"How was this found at all"** → `RECON.md` (four dead URL schemes and one undocumented API).

## The channels, and why there are five

`index.csv` carries `channel` + `channel_desc` on every row, because provenance here is not
uniform — the county rebuilt its site four times and each era survives differently.

| channel | rows | what it is |
|---|---|---|
| `county_static` | 128 | 2008–2018. Listing recovered from Wayback; **the PDFs are still live** at `utahcounty.gov/dept/Clerk/Data/Minutes/CANDFINDISC<OFFICE>/<YEAR>/`. The path segment names the office |
| `county_api` | 86 | **`api.utahcounty.gov/cms/elections`** — a Strapi CMS whose read Bearer token the county shipped inside `candidates/disclosure.js`. The **only** channel for 2022, and a live re-host of 2020 |
| `county_sheet` | 37 | the current portal's public **Google Sheet** → Google Drive PDFs (2024, 2026) |
| `county_2020_page` | 10 | the 2020 listing; its `apps/WebLink` PDFs 404 live, recovered from Wayback |
| `state_municipal` | 6 | `disclosures.utah.gov/Municipal/utah_2024` → `municipal.utah.gov` — the one year the STATE system holds Utah County documents |

**Cross-channel duplicates are collapsed by sha256**, not by name: 9 filings are served
byte-identically by two channels, and `alt_source_urls` / `alt_reporting_periods` /
`n_channel_copies` record the others. One of those is a **county publishing error worth knowing
about**: Anthony Canto's 2020 `General` and `30 Days after General` API entries point at the
*same bytes* — the county posted one document under two report periods. Retained as one filing
with both labels, not silently deduped away.

## How `office` was determined (and why it is a column with three companions)

The Summit agent's finding applies here: a county form header is **not** proof of a county
office. So office is resolved from the **stated office**, corroborated, never guessed — every
row carries `office_source`, `office_confidence`, `office_note`:

1. **`listing` (164 rows, `high`)** — the channel itself printed the office: the 2008–2018 pages
   group filings under an office heading *and* encode it in the PDF path; the Google Sheet has
   an Office column.
2. **`filing text (Office field)` (48, `high`/`medium`)** — read from the form's own
   "Office Seeking" / "Office" field.
3. **`county canvass` (29, `medium`)** — joined to `../elections/election_results_by_contest.csv`
   on candidate + year (surname + a ≥3-character first-name prefix, so *Rod* ≡ *Rodd*).
4. **`filing text (curated override)`** — `office_overrides.csv`, each with the evidence quoted
   (e.g. Hyrum Cox 2022: the Office block OCRs "Sherif" beside his own
   `vote@hyrumcoxforsheriff.com`).
5. **blank (`needs_review=1`)** — nothing stated it. Left blank. See "Do-nots".

**Reconciliation result: where two or more sources resolved, they agreed 39/39 — zero real
conflicts.** (Apparent conflicts were naming conventions only: listing `Assessor` vs form
`County Assessor`; a form printing `County Commission` with no seat.) The 2026-08-01 vision pass
re-ran that reconciliation against the county's own canvass on the page-face office of every
filing: **89 agree, 0 substantive disagreements**, 157 filers fall outside the canvass's
2016–2026 depth, 17 filings print no office (or no name) to match on.

### The 19 unresolved offices — adjudicated 2026-08-01 (vision pass)

| outcome | n | how |
|---|---|---|
| **promoted to a county office** | **8** | the Office field was legible on the page: Forbush 2020 → Commission Seat C · White 2020 ×2 → Commission Seat C · Powers Gardner 2021 → Commission Seat A · Graves 3/31/22 → Commission Seat A · Diamond 4/11/22 → Commission Seat A · Diamond 3/30/22 → Commission Seat A (`low` — its own Office box is REDACTED; attributed only by same-filer/same-cycle/same-email corroboration) · Sakievich 2022 → **County Commission, seat NOT inferred** |
| **proved LOCAL SCHOOL BOARD → dropped from `index.csv`** | **4** | McCabe "Provo School Board District 5" · Warnick "Nebo School Board district 3" · Hoiland "School board" · Nielsen (name field: "Rebecca Nielsen - Provo School District Board Member"). Each re-read at the source by the orchestrator before exclusion; ledgered in `out_of_scope.csv` |
| **still honestly UNRESOLVED** | **7** | Osborn 2020 · Balderree 2022 ×2 · Clement 2022 · Riley 2022 — Office box **blank on the form**; Taylor 2022 and Bird 2024 — the Office box contains a **street address**, which is not an office claim |

**Two further office corrections came out of the same pass, closing a documented open case:**
both 2008 **Larry Alton Ellertson** filings now read `County Commission Seat C`. The Office
Seeking line is legible at 250 dpi and reads *"Utah County Commission Seat (c)"* — so the
county's own filename (`CountyCommissionSeatC-…`) is right and the Wayback listing accordion
heading "Commission Seat B" is the outlier. That is a portal LABEL losing to the filer's own
hand; the CLAUDE.md "seat is left unresolved" note it replaces is retired.

Corrections are applied by `build_index.py` from `office_overrides.csv` — see "Rebuild / verify".

⚠ **A body-keyword fallback was deliberately REMOVED from the extractor.** Searching the whole
filing for office words is a ~90%-false-positive signal on this corpus, for two structural
reasons: (a) the form's own title is "FINANCIAL CAMPAIGN REPORT FOR COUNTY **& LOCAL SCHOOL
BOARD** CANDIDATES", so every filing "mentions" school board; (b) the filing-address block says
"Mail or deliver to **Utah County Clerk's Office**", so every filing "mentions" County Clerk.
An early pass produced 91 bogus offices from exactly these two strings. Only the *field* counts.

## The money layer — `vision/` → `filing_totals.csv` (stated totals only)

**Why it is vision-transcribed and not parsed.** The shared library
(`scripts/campaign_finance/`) dispatches on form FAMILY and Utah County files on **two forms of
its own**, neither of which `easyvote_schedab` / `southjordan_form` / `utah_standard_form` reads
without new shared code — and **93% of the corpus is scanned handwriting** (`format`: 245
scanned · 17 text · 1 spreadsheet), for which `pdftotext` returns nothing and the tesseract
sidecars render money as `AoA 3.05 APRS oe`. So the figures come from **reading the page**
(`/cf-vision-transcribe`, Read-tool method, $0 API), and `build_finance.py` is **module-local**
(the juab precedent) while honoring the SCHEMA.md column contract exactly.

### The two form variants — and why BOTH columns are captured

| variant | cycles | cover | summary page | per-period cell | cumulative cell |
|---|---|---|---|---|---|
| **`legacy_colAB`** (135) | 2008–2018, some 2020/2026 | p1 | usually **p2** | `Column A — Total this Period` | `Column B — Year-to-Date Total` |
| **`modern_boxAF`** (130) | 2020+ (`v. 2.22` / `v. 4.20` / `v. 12.23` / unversioned) | p1 | usually the **LAST** page | `Box B` / `Box D` | `Box C` / `Box E` |
| **`other`** (2) | — | — | — | one wholly blank form; one candidate-made spreadsheet | |

`legacy_colAB` prints lines 1–7 (1 contributions · 2 expenditures · 3 balance at beginning ·
4 contributions · 5 subtotal · 6 expenditures · 7 balance at close). `modern_boxAF` prints
A (balance at beginning) · B/C (contributions period/YTD) · D/E (expenditures period/YTD) ·
F (subtotal before expenditures = A+B) · balance at close (F−D; some revisions letter it **G**).
**Every line and box is captured verbatim under its own printed label** in
`vision/<key>.json → reports[].totals_verbatim`.

### THE PROMOTION REGIME (read this before summing anything)

`stated_total_contributions` / `stated_total_expenditures` carry the **PER-PERIOD** figure —
`filing_regime` says `per-period` on every row. The **cumulative** figures are kept in `notes`
as `ytd_contrib=` / `ytd_expend=` and in full in the transcript, and are **NEVER summed as
increments**. A candidate-cycle total is therefore **Σ the per-period rows**, cross-checked
against the LAST report's cumulative — never a sum of the cumulative column. `stated_beginning_balance`
= legacy line 3 / Box A; `stated_ending_balance` = legacy line 7 / balance at close.

### `vision/<key>.json` — the cache format

Filename is the repo-wide cf-vision convention: **`sha1(index.csv `path`)[:8]`**
(`scripts/campaign_finance/vision_lib.cache_key`). `vision/3ebf4721.json` (legacy) and
`vision/6d4ca26f.json` (modern) are the **reference caches** — match them.

```
path, key, transcribed_by, transcribed_utc, pages_read,
form_variant (legacy_colAB|modern_boxAF|other), form_version, form_title,
reports: [ {                    # >1 element ONLY for a genuine multi-report PDF
   candidate_printed, party_printed, office_printed, residence_city,
   report_type_printed, is_amendment, report_date, summary_page,
   totals:          { contrib_this_period, contrib_cumulative, expend_this_period,
                      expend_cumulative, balance_beginning, subtotal_before_expend,
                      balance_close }          # NORMALIZED cross-variant slots — the build reads these
   totals_verbatim: { <every line/box, keyed by its own printed label> },
   confidence:      { <field>: high|medium|low },     # PER FIELD
   unreadable:      [ <fields left ""> ],
   notes, scope_flag? } ],
notes
```
Amounts are **strings, verbatim as printed**. `transcribed_by` is
`vision-transcribed(claude-opus-5; 2026-08-01 totals tranche)` on all 267.
**`vision/` is CURATED — corrections go there (with a note saying what was re-read at the
source), then rebuild. Never hand-edit `filing_totals.csv`.**

### The three whitelisted normalizations (and the things deliberately left blank)

`build_finance.py` applies exactly three reversible transforms, each recorded in `notes`:
written nil marks `-0-` / `0.-` / `Zero` → `0`; accountant's parentheses `(65.00)` → `-65.00`;
a dash in the cents position `2,250.-` → `2250.00`. **Everything else that is not a clean
decimal stays BLANK with its verbatim form in `notes`** — notably a **bare dash `-` is NOT a
zero** (the filers who use it write explicit zeros elsewhere on the same page), and a compound
cell such as `94009.26 +Inkind 666.67` states two numbers and is not reduced to one.

### What the layer contains

**265 rows for 263 filings** (2 PDFs are genuine multi-report bundles: Buhman 2014
original+amendment, Westmoreland 2024 two reports — each emitted as its own row, never merged).
Filing-level `extraction_confidence`: **high 153 · medium 96 · low 16**.
**252 of 265 rows carry at least one stated figure**; the 13 that carry none, and the 19/13
one-sided blanks, are itemized in `AVAILABILITY.md` §4a — every one is a document-level gap or a
cell the filer left empty, none is a failed read.

## Do-nots

- **Do not read `text/*.txt` as a transcript.** The sidecars are tesseract OCR of handwritten
  forms. They are a *finding aid* (they carry the Office field, the filer's name and email,
  often the report type). **Amounts in them are unreliable and none were transcribed** — the
  money in `filing_totals.csv` comes from `vision/`, never from `text/`.
- **Do not infer a commission SEAT that the filing does not print.** 3 rows resolve only to
  `County Commission` (Sakievich 2022 and the 2020 pair) because the page names no seat, and
  many more filings print "County Commissioner" with no letter while `index.csv` carries one
  from the channel. Where they differ, the row's `notes` says so. *(The 2008 Ellertson case
  formerly cited here is CLOSED — the seat proved legible at 250 dpi; see "How `office` was
  determined".)*
- **Do not adjudicate a filer's own inconsistency.** Gregory Graves types `Commission Seat A` on
  3/31/22 and writes seat `"B"` on 4/11/22; dozens of filings carry balance ladders that do not
  follow their own formula (Gordon's close box has the wrong sign; Diamond's Box F is half of
  A+B). Everything is transcribed as printed and flagged in `notes` — nothing was recomputed.
- **Do not treat a blank `office` as "not a county filing."** It means *no source stated an
  office*. 7 such rows are retained precisely so they are not lost.
- **Do not use `provenance`-style filters from the city tier here** — this dataset's channel
  column is `channel`, and its vocabulary is the five above.
- **Do not re-derive the office or the FILER from the file NAME, or from `index.csv.candidate`.**
  Names are the clerk's and they drift (`Danise Farren` cell → `Danise Farron_Redacted.pdf`;
  `Brian Bird` → `Brian Baird.pdf`). Worse, the channel is sometimes simply wrong about who
  filed: the county's Strapi record files **Paul V. Child's** 2020 Recorder filing under
  **Taylor Dayton** (`Child 5.1.20 Redacted`). **`filing_totals.csv.candidate` is therefore the
  PAGE-FACE name**, and the channel's label is preserved as `candidate_index=` in `notes`
  wherever the two differ. Join to `index.csv` on `source_filing`, not on `candidate`.
- **Do not sum the cumulative columns.** See "THE PROMOTION REGIME". And the donor/vendor
  layer covers **2 filings only** — an empty itemized side on the other 261 means *not
  transcribed*, **not** *no donors*, which is why their `reconciles_*` stay blank.

## The machine-readable itemized layer (built 2026-08-02, TRANCHE 3 Phase A)

| | count |
|---|---:|
| filings with a REAL text layer, handed to `utahcounty_schedab` | **17 of 263** |
| contribution sides reconciling exactly → shipped | **1** (Tanner Ainge 2018) |
| expenditure sides reconciling exactly → shipped | **2** (Ainge 2018 · Paxman 2026) |
| contribution sides published against a BLANK stated total (compound cell) | **1** (Paxman) |
| rows emitted | **72 contributions (3 in-kind) · 81 expenditures** |
| rows carrying `geometry` | **153 of 153 (100%)** |

- **The contribution anchor is CASH-ONLY** (`reconcile_cash_only`): Column A / Box B states the
  cash figure and in-kind is a separate printed line, so the reconciliation sum counts cash rows
  only. Ainge 2018 Column A **4,585.77 / 7,845.74** reconciles to the cent — and note it is
  **not** the Column B Year-to-Date pair (51,983.16 / 50,047.72), which is exactly the
  distinction the promotion regime exists to preserve.
- **THE COMPOUND `+Inkind` CELL — a divergence recorded, not resolved.** Paxman's v.12.23 Box B
  prints `168872.24 +Inkind 7670.68` in ONE cell. This module's `money()` refuses to reduce two
  numbers to one, so `stated_total_contributions` is **BLANK for that filing and STAYS BLANK**.
  The family splits the cell on the form's own printed marker; its 63 contribution rows sum, in
  cash, to **exactly 168,872.24**, and its 3 in-kind rows reproduce the ledger's printed IN-KIND
  total **7,670.68** to the cent (Spencer Stokes · Doug Ford · All In For Utah PAC). Those rows
  are published **alongside** the blank, never in place of it: `itemized_contrib_sum` is filled,
  `reconciles_contrib` stays **blank** (unknown — there is no published figure to test against),
  and every row is flagged `needs_review=1`. The published total was not changed.
- **IN-KIND is asserted only when proven.** The family calibrates the positional in-kind split
  against the ledger's own printed IN-KIND column total; if it cannot reproduce it exactly it
  reports every row as cash and flags them. That decision is passed through untouched.
- **What was withheld, and why** (each named in `filing_totals.notes`): 6 filings have a real
  text layer but no legible summary page at all (the OCR floor — their figures stay in
  `vision/`); on 8 more the parsed rows do not sum to the published stated total, so the side
  emits **nothing** rather than a short ledger (e.g. COMA.Ainge 2018 contributions parse to
  41,865.00 against a stated 47,397.39; Davidson 2022 parses 85,635.28 against 514.64).
- **One curated index promotion.** The acquisition channel named **no filer** for
  `raw/2018/2018_TAinge.pdf` ("filer not named by the channel"), while the shared validator
  requires a contributions row's `(candidate, election_year)` to exist in `index.csv`. A
  **candidate-only** `office_overrides.csv` row (evidence-cited to the filing's own vision
  transcript) promotes **Tanner Ainge** into that EMPTY cell. A non-empty channel label is
  never overwritten by this mechanism — a channel/face disagreement must stay visible.

## Joining to the rest of `utah_county/`

- **To elections**: `index.csv.candidate` + `election_year` → `../elections/election_results_by_contest.csv`
  (`office` + `district`). Election names are UPPER-CASE and carry party prefixes (`REP JEFF GRAY`);
  normalize and allow a first-name prefix match. `matched_election_offices` already carries the
  join result where one was found.
- **To the vote layer**: county commissioners' roll-call votes are in `utah_county/db/` — a
  commissioner's filings and their votes join on person. Note the county's own vote-recording
  ceiling flips across eras (see `../CLAUDE.md`).
- **`ut_state` legislators are a disjoint person population** — never surname-join to these
  county filers.

## Rebuild / verify

```
python3 utah_county/campaign_finance/build_index.py --check   # verify every sha256 on disk
python3 utah_county/campaign_finance/build_index.py           # rewrite index.csv (run FIRST)
python3 utah_county/campaign_finance/build_finance.py         # rewrite the 3 money CSVs
python3 scripts/campaign_finance/validate_finance.py utah_county/campaign_finance   # -> PASS
```
Order matters: `build_finance.py` reads `index.csv`, so regenerate the index first.
`build_index.py` never fetches and never edits a raw file. A filing whose raw file is missing is
dropped from `index.csv` and reported (the index can never claim a document the repo lacks); a
sha256 that no longer matches is a **FAIL** (the raw layer is verbatim and must not drift).

**Corrections to `office` go in `office_overrides.csv` with evidence — never in-place in
`index.csv`.** That file has TWO row kinds, told apart by whether `path` is filled:
*documentation-only* (blank `path`, keyed on the acquisition `staging_file` — the original 7
rows, folded into `batch/manifest.json` at acquisition time) and **APPLIED** (`path` = the
dataset-relative raw path — the 14 rows added by the vision pass, rewritten into `index.csv` at
build time with per-row logging). The sentinel office **`__school__`** DROPS the filing from
`index.csv` as out of Package-B scope (it must also be ledgered in `out_of_scope.csv`). An
override whose `path` matches no manifest filing is **STALE and FAILS the build** — the
`vote_overrides` discipline. `build_finance.py` applies the same rule to its own inputs: a
`vision/*.json` with no `index.csv` row FAILS unless the filing is ledgered out of scope.

**Corrections to a FIGURE go in `vision/<key>.json`**, with a note saying what was re-read at
the source, then rebuild. Never hand-edit `filing_totals.csv`.

**No `cycle_totals.csv`** (the juab precedent): `scripts/campaign_finance/cycle_totals.py` is
city-scoped, and its dedup contract assumes an itemized layer this tranche does not have. With
`filing_regime='per-period'` a candidate-cycle total is Σ the per-period rows for that
`(candidate, election_year)` — cross-check it against the last report's `ytd_*` in `notes`.

## Privacy

Government-published public records, **redacted upstream by the county** (nearly every file is
`*_Redacted.pdf`; donor addresses were blacked out by the clerk before publication). `raw/` and
`text/` are verbatim reproductions and are not further edited, per repo-root `PRIVACY.md`. No
structured donor rows exist in this package; if one is built later, it stores donor **city/state
only**, never street addresses.

The vision pass followed the same rule for the FILER: `vision/*.json` records
`residence_city` only — **no street address and no phone number was transcribed**, even where
the county published an unredacted copy. It did publish several: Andrea Allen 2024 and Anthony
Canto 2024 each appear TWICE, once redacted and once in the clear, and Brian Bird's 2024 filing
is unredacted. That is the county's own posting inconsistency, recorded here and in
`AVAILABILITY.md`; the raw files are retained verbatim (a repo cardinal rule) and nothing was
re-redacted or reconstructed.
