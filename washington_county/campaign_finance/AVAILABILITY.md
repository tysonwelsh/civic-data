# AVAILABILITY — Washington County county-office campaign finance

**As-of 2026-08-01; itemisation of the machine-readable era CLOSED 2026-08-23 (§8).**
Sources checked, what each held, and what is honestly missing.
Method and channel anatomy: **`RECON.md`** (read it first). Per-file provenance:
`index.csv` + `raw/<channel>/_fetch_log*.jsonl`.

**Result: the deepest county campaign-finance record in the repo — 2006 → 2025**, assembled
from **five generations of county URL** plus a state channel the folder labels disguise.
Nothing was hand-typed: every row traces to a retrieved file with a sha256.

---

## 1. Sources checked

| # | Source | Reachable | What it held for COUNTY offices |
|---|---|---|---|
| 1 | **Live county page** `washco.utah.gov/departments/clerk/elections/campaign-financial-reports/` | ✅ 200 (browser UA **+** `Referer: https://www.washco.utah.gov/` required — the host 403s plain fetchers) | Current officeholders' **annual** reports (Jan-2026 filings for 2025) + a "Historic Reports" table reaching **2006**. **Organised by CURRENT OFFICE HOLDER — defeated and former candidates are absent.** |
| 2 | **`outpost.washco.utah.gov/apps/clerk/elections/<year>/reports/`** | ✅ 200 by known URL; **directory listing disabled** (`/2018/`,`/2020/`,`/2022/`,`/2024/` → 403 = exists-but-unlistable; `/2016/`,`/2026/` → 404 = absent) | The live 2024-cycle filings linked from source 1. **Wayback has ZERO captures of this host**, so anything here survives only while the county keeps linking it. |
| 3 | **Wayback** `washco.utah.gov/forms/clerk-auditor/elections/<year>/reports/` | ✅ files archived; **listing page never archived with content** (all 14 CDX rows are 404/403/301/302) | 2016 / 2018 / 2020 / 2024 filings — **this is what restores the defeated candidates source 1 drops** (the whole 2020 Recorder field, the 2018 Attorney and Sheriff races). |
| 4 | **Wayback** `washco.utah.gov/clerk/pdf/financialreports/` (+ the 2011 twin `clerk/electAdmin/pdf/`) | ✅ 454 files. The `electAdmin` path replays **401 for every file**; the identical files under `pdf/financialreports/` replay 200 — **use `financialreports`** | 2011–2013 (**PDF**) and 2014–2015 (**`.xls`**), each filing split three ways: `Summary` + `Contributions` + `Expenditures`. Enumerated from the archived listing pages `clerk/electFinancialReport.php?year=2010\|2012\|2014`. |
| 5 | **Wayback** `washco.utah.gov/clerk/pdf/` and `clerk/pdf/2010elections/` | ✅ 12 + 144 files | The original **HB 29 (2008)** implementation and the 2010 cycle. The 2008 listing page `clerk/campaignReporting.php` (38 captures) **printed each filer's totals in HTML** — transcribed to `portal_stated_totals.csv`. |
| 6 | **LG / state** `disclosures.utah.gov` → `municipal.utah.gov` | ✅ **and NOT empty** | **23 county-clerk-filed PDFs the county's own site does not hold** — of which **11 are county-office** and indexed here (`channel=state_disclosures`); the rest are Local School Board filers on the same county form, ledgered as out-of-scope. See §2. |
| 7 | **Utah Public Notice (PMN)** | n/a | Not a channel: PMN publishes meeting notices, not campaign filings. (No PMN query was run, so no PMN negative is claimed — see the `keyword`-param caveat recorded in `RECON.md`.) |

## 2. The state channel — folder labels lie, form headers decide

Walking `/Municipal/washington*` recursively (**83 folders, 673 links, 570 state-hosted
PDFs**) and classifying **every** PDF by the form header printed inside it (rendering +
OCR'ing page 1 where there is no text layer) found county filings in exactly two folders,
**neither of which is named for a county office**:

- **`washington_2008_Local School Board`** → 4 **County Commission** filings
  (Alan Dean Gardner Sept + Oct 2008; Linden Haner Alder — "Lin Alder" — Sept + Oct 2008).
- **`washington_2010 Elections`** → the **whole 2010 county field** (Belnap–Attorney,
  Pulsipher–Sheriff, Whitehead–Treasurer, Shirts–Recorder, Hafen–Clerk/Auditor, Aldred /
  Eardley / A. Hughes–Commission A, Drake / S. Hughes–Commission B, Brooks ×2, Tersigni,
  Despain, **Cyril Noble**) — **April/May 2010** filings, i.e. **earlier than the county's
  own 2010 folder, which starts at 6-15-2010**. Cyril Noble appears in **no** county channel.

Everything else was municipal. The state site is otherwise a **redirect**: `washington_2012`,
`washington_2020_General`, `washington_2020_Primary` and `washington_2022` contain **no
documents at all**, only a link back to the county's own page.

**`washington_2024` specifically re-checked by CONTENT** (the Utah County build found that
folder to be a real second county channel there): for Washington County it is **not**. It
holds one subfolder, `washington_2024_St. George`, with exactly **two** PDFs, and both are
**municipal** — verified by opening them, not by folder name:

- `2024.04.01  Kemp Amended 10.24.2023 Form.pdf` — header `ST. GEORGE CITY / CITY RECORDER'S
  OFFICE`, `CAMPAIGN FINANCE REPORT - AMENDED`, **"Candidate for Office Of City Council"**,
  STEVE KEMP;
- `2024.04.01  Larkin Amended 08.29.2023 Form.pdf` — same city header, **City Council**,
  DANNIELLE LARKIN.

Neither is a county filing, so neither is indexed here. **But they are a live cross-entity
finding**: both are **AMENDED 2023 St. George filings hosted only on the state channel**, and
`st_george_city_council/campaign_finance/index.csv` contains **zero `amended` rows and zero
rows sourced from `municipal.utah.gov`**. Larkin's amendment restates her 2023 pre-primary
contributions **$24,690.00 → $22,555.00** (−$2,135), while that city dataset's
`cycle_totals.csv` still sums the superseded original. Reported to the coordinator as a lead
for the St. George entity; **not acted on here** (this dataset is additive and does not touch
another entity).

**The header is evidence, not a verdict.** The same blank county form is handed to
**Local School Board** candidates and to **special districts** — this county's clearest
false-positive is `washington_2021_Northwestern Special Service District`, **6 filings whose
header reads "WASHINGTON COUNTY CANDIDATE FINANCIAL CAMPAIGN REPORT"** for NWSSD board seats
in an odd year. Office is therefore decided on the form's **office line**, with cycle parity
(county offices are **even-year only**) as the check. **Every county-office row in
`index.csv` resolves to an even cycle year; zero parity flags.**

## 3. Out of scope (checked, deliberately not indexed)

| Class | Where it is | Treatment |
|---|---|---|
| **Local School Board districts 1–7** | every channel — they file on the same county form | **`excluded_school_board.csv`** — full ledger (URL, sha256, bytes, printed office, retrieved_utc) so a scope change can re-fetch deterministically. Raw bytes are **not** retained. |
| **Judicial retention** (5th District Court, 5th District Juvenile, Justice Court) | the 2024 `reports/` folder | same ledger |
| **Northwestern Special Service District** | state `washington_2021_…` | not fetched; recorded here and in `RECON.md` |
| **Conflict-of-Interest annual disclosures** | `/wp-content/uploads/2026/01/<Name>-Conflict-of-Interest-012026.pdf`, one per officeholder | Excluded by `scripts/campaign_finance/SCHEMA.md` ("Annual financial / conflict-of-interest statements are out of scope"). A different document class from the campaign C&E report. |
| **Municipal (city/town) candidates** | state odd-year folders; city recorders | belong to the city entities (`st_george_city_council/campaign_finance/` already holds St. George) |

## 4. Honest gaps — what does NOT exist

1. **Before 2008 there is no online record to find.** Online posting began with **HB 29
   (2008 General Session, effective 2008-05-05)**, quoted on the county's own 2008 page. The
   single **2006** item is a *later re-scan* the county posted in its Historic table, not a
   2006-era publication. Anything earlier is a GRAMA request, not a fetch.
2. **`outpost` is unlistable and unarchived.** Its `/2018/`, `/2020/`, `/2022/` folders exist
   (403, not 404) but cannot be enumerated, and Wayback never crawled the host. There is no
   way to prove we have everything those folders hold — only everything the county has ever
   *linked*. **This is the single largest unquantifiable gap in the dataset.**
3. **The 2016–2024 listing page was never archived with content**, so for those cycles the
   file list comes from Wayback's crawl of the *files*, which is necessarily incomplete.
4. **Wayback 404s that are genuine**: **6** CDX-indexed URLs replay 404 at every capture
   (`batch/retry_404.py` re-tries every timestamp before giving up). They stay in
   `unrecovered.csv` with the reason recorded.
   **Every URL in `batch/manifest.json` has been attempted** — nothing is left pending.
5. **Archive replay defect — HTTP 200 with a ZERO-byte body.** Two 2020 captures return 200
   but no bytes even though CDX reports a real length. Re-requesting recovered one
   (`Attorney_Special 2 Year_Eric Wesley Clarke_October 21 2020`, 101,401 bytes, now
   indexed); the other (`Recorder_Kimberly Kay Hancock_June 23 2020 FCR`) has a **single**
   capture whose CDX length is 480 bytes — an error page, so the filing is genuinely
   unrecoverable from the Archive. Both are logged in `unrecovered.csv` as
   `fetch failed: 200`. **Do not treat a 200 from Wayback as proof of retrieval — check
   `bytes`.**
6. **Retrieved but unclassifiable — now 2 files, down from 48.** A file whose office cannot be
   established from the document, the archived listing, the person-office roster, or the
   filename is **held OUT of `index.csv`** and ledgered in `unrecovered.csv` as
   `retrieved but office not determinable …`. These are real files on disk — they are
   excluded from the index rather than guessed into an office. The other 46 were adjudicated
   one by one from the office line inside the form (`office_determinations.csv`): **7 promoted
   into the index as county-office, 38 school board, 1 a STATE House seat filed on the county
   form.** `unrecovered.csv` is now **12 rows** total.
7. **The money layer: STATED TOTALS for all 206 filings + a MACHINE-READABLE ITEMIZED LAYER
   that is now CLOSED (re-parsed 2026-08-23 — full verification in §8).**
   `filing_totals.csv` carries what each filing's cover/summary PRINTED as its totals.
   `contributions.csv` (**1,518 rows**) / `expenditures.csv` (**1,738 rows**) carry the
   itemised ledgers of **all 102** born-digital 2010–2015 file-sets — 101 filings with rows,
   one honest empty — parsed by the registered `washco_split` family, **completeness-gated**
   (one side withheld) and scope-aware **reconciliation-verdicted**. 100% of rows carry
   `geometry`. **0 of 206 `stated_*` values changed**, then or now.
   The remaining gap is real and measured: the **100 HANDWRITTEN cover forms** are still
   unitemized (a vision wave — §9 ledgers it by year and office) and the **4 ledger-only 2008
   postings emit no rows by design** (they print no totals to reconcile against). An empty
   itemized side still means *not transcribed / empty schedule*, never *no donors*.
   ⚠ The ledgers restate the cycle to date: **never sum rows across a cycle** (§8.2).

## 5. Portal defects found (labels that lie — all verified against file content)

| Defect | Evidence |
|---|---|
| A file named **`6-15-2010 Contributions - Greg Aldred.pdf` contains a County Candidate Summary**, not a contributions ledger | `pdftotext` of the file prints `County Candidate Summary … Greg Aldred … Commission Seat A` |
| The live page's Assessor row labels **`2020-Tom-Durrant.pdf` as `12-07-2024`** | the same file is also linked, correctly, as `2020` |
| The live page labels **`2011-David-Whitehead.pdf` as `2012`** | filename vs link text |
| One Recorder link has **no file extension** (`Gary L_01-08-2025. Christensen_Recorder_Final`) | serves a PDF anyway (70,622 bytes, 200) |
| The archived **`electFinancialReport.php?year=2012` page is headed "Campaign Financial Report (2010)"** | its content is entirely 2012 files |
| The county's own workbooks are headed **"All Expeditures for …"** (sic) | 2014–15 `.xls`; matched verbatim, never corrected |
| A filename reads **`4 4 2001 Expenditures - Mark Boyer_04-04-2014.xls`** — a 2001 deadline on a 2014 posting | source typo; the posted date governs |
| `County Candidate Summary - Brock Belnap.pdf` (2010) prints **blank candidate/office/district cells** | the county's export dropped them; recovered via the roster, flagged `office_source=person_roster` |

## 6. Residual risk, stated rather than assumed

- Odd-year state folders were header-screened but are **municipal-suspect by construction**;
  a county *annual* report misfiled into one would not have been caught by the parity rule.
- The screening OCR reads a **printed header**, which is reliable; it does **not** rely on
  reading handwriting.
- `office_confidence=medium/low` rows (see `index.csv`) are exactly the rows whose office did
  not come from the document itself. Filter on `office_confidence='high'` for a
  document-verified subset. **113 of 409 rows are medium/low.** The 2026-08-02 pass proved this
  is not a formality: a systematic sweep comparing every high-confidence document office line
  against `index.csv` found **4 rows the cascade had got WRONG or under-specified** — 3 Gil
  Almquist 2016 filings placed in Commission Seat A when every form says **seat C**, and one
  Slade Hughes 2020 filing left "seat not stated" when the form says **Seat C**. All four came
  from the `person_roster` / `portal_listing` / `filename` tiers, i.e. exactly the medium/low
  band. They are corrected via `office_determinations.csv`. **The remaining medium/low rows
  have not been individually document-verified.**

## 7. The stated-totals tranche (2026-08-02) — what it covers and what it leaves

**Scope transcribed: cover-page office + the filing's stated totals.** 206 logical filings
across 409 files; every indexed file is reachable from exactly one filing.

- **100 filings** were **vision-transcribed** from page images (the handwritten/typed scans of
  2006 and 2016–2025 — `pdftotext` yields nothing on them). An 11-filing stratified re-read at
  200dpi matched **156/156 money cells and 13/13 cover blocks**.
- **106 filings** were read from machine-readable sources (`.xls` cells via xlrd; the
  born-digital PDF text layer) and are byte-reproducible by `extract_born_digital.py`.
- **11 filings state no totals** — 4 published as itemised ledgers with no summary sheet, the
  rest filers who left the cumulative column blank or wrote `None/Zero`. Recorded blank.

**⚠ `index.csv` `format` is not a safe proxy for "has a readable text layer."** Several county
PDFs carry a text layer holding nothing but a stamped transmittal note while the report faces
are images (Ryan Sullivan 2024, Gil Almquist 2016, Dean J. Cox 2016). Those were read by
vision; `extract_born_digital.py` carries a hard guard that refuses to overwrite any cache
stamped `vision-transcribed`, because a naive text-layer re-read would have replaced good
transcriptions with empty ones. **It tried to, and the guard is why it did not.**

### Scoring against the county's own printed totals (`portal_reconciliation.csv`)

The 2008 clerk page printed each filer's totals in HTML above the links to that filer's PDFs —
a **second, independent statement** of the same figures and the only external anchor in the
record. It yields **7 snapshots**, of which the linked PDFs survive for **3**:

| snapshot | result |
|---|---|
| **Gregory Aldred, June 9 2008** | **AGREES EXACTLY on both sides** — portal `$2,847.51` / `$2,822.51`; the itemised ledgers count to `$2,847.51` / `$2,822.51`. |
| **Alan Dean Gardner, "December 12 2008"** | **DISAGREES** on contributions: portal `$37,644.00`, ledger counts `$29,511.00`. |
| **Lin Alder, October 28 2008** | **not scorable** — see the completeness gate below. |

The Gardner disagreement is **kept verbatim on both sides and not reconciled away.** The
evidence points at a portal-label defect rather than a transcription error: the counted
`$29,511.00` falls between Gardner's own Aug-31 portal snapshot (`$7,243.00`) and this row's
`$37,644.00`, and the PDFs this row links are named for the **October 28** deadline while the
row's `submitted` date is **December 12** — i.e. the county hung an EARLIER pair of detail
sheets under a LATER row, the same class `§5` already catalogues. The parse is provably
complete: every money token in the file body is consumed by a parsed row, and the file's
trailing page was rendered and confirmed genuinely blank.

**The completeness gate is why only some ledgers are counted.** A counted ledger sum is
DERIVED, never a stated total, and is published **only when the matched rows consume every
money token in the document body**. Aldred's ledgers are clean one-line-per-entry tables and
pass. Alder's wrap entries across two lines, date some entries "Various", run the date into the
payee, and carry a negative adjustment; Gardner's expenditure sheet has two undated "Sept 2008"
rows. Those sums are **withheld with the shortfall recorded** (e.g. 133 money tokens vs 116
parsed rows) rather than published short — a partial sum presented as a ledger total would be
worse than no sum.

**4 portal snapshots reference PDFs that were never retrieved** (the June/August 2008
`…-2.pdf` pairs are not in any Wayback capture). For those reports the county's printed totals
in `portal_stated_totals.csv` are **the only surviving record**, and they are retained as such.

### If the itemisation tranche is authorised, start here

1. **2014–2015 `.xls`** — real spreadsheet cells, donor name + address + amount + in-kind flag.
   Lowest risk, highest fidelity. **`PRIVACY.md` binds: `donor_city`/`donor_state` only, the
   street line is discarded, never promoted into `donor_raw`.**
2. **2010–2013 born-digital PDFs** — real text layer, but the ledgers are **column-positional**
   (`Amount` / `In Kind` / `Loan` share a line and are distinguished by x-offset). A naive
   "last money token on the line" reader **will** mis-column in-kind and loan rows; this is
   exactly why the 2011 Pulsipher ledgers were left uncounted in this tranche.
3. **2006 + 2016–2025 handwritten Form A/B** — vision territory, the largest effort.

*(Steps 1 and 2 were executed 2026-08-23 — see §8. Step 3 is the remaining queue, §9.)*

---

## 8. THE PARSER TRANCHE — VERIFICATION (2026-08-23)

**Scope: the MACHINE-READABLE era, and it is now CLOSED there.** No page image was read; no
handwritten filing was touched; **0 of 206 `stated_*` / candidate / office / filing-date values
moved** (proved by a column-level diff against the pre-tranche `filing_totals.csv`).

### 8.1 The queue, derived from `index.csv` — not from a prior sizing

A prior scoping note sized this work as "189 spreadsheet + 125 text machine-readable, 95
scanned". That counts **FILES**, and this county's unit of work is a **FILING**. Derived here
from `index.csv` joined to the 206 filing caches:

| filing class | filings | files | index `format` of those files | whose queue |
|---|---:|---:|---|---|
| born-digital `summary_sheet` (Summary + Contributions + Expenditures, 2010–2015) | **102** | **301** | 189 spreadsheet + 112 text | **this tranche** |
| `ledger_only` (2008 HB-29 `Detailed … Report` pairs + one 2011 pair) | **4** | **8** | text | machine-readable, but emits nothing — §8.5 |
| `cover_form` (handwritten 17-16-6.5, 2006 + 2016–2025) | **100** | **100** | **95 scanned + 5 `text`** | the vision queue, §9 |
| | **206** | **409** | | |

⚠ **The scanned count is 100 filings, not 95.** Five files carry a text layer holding nothing
but a stamped transmittal note while the report faces are images (Dean Cox 2016, Gil Almquist
2016 ×2, Ryan Sullivan 2024 ×2), so `index.csv` `format` calls them `text`. The authority on who
owns a filing is its cache's `transcribed_by`, never the index's `format` — the same trap
`extract_born_digital.py`'s hard guard already exists for.

### 8.2 What was published

| | |
|---|---:|
| file-sets parsed | **102 of 102** |
| filings carrying at least one itemized row | **101** (the 102nd, Whitehead 6/15/2010, has an empty ledger on both sides — honest) |
| **contribution rows** | **1,518** (was 181) |
| **expenditure rows** | **1,738** (was 308) |
| rows carrying `geometry` | **3,256 of 3,256 (100%)** — 2,659 real `Sheet1!F5` cell refs, **597 `pct:` boxes** |
| cycles / filers / offices | 2010, 2012, 2014 · 34 filers · all 9 county offices |
| gross itemized | $560,319.17 contributions · $528,128.44 expenditures **— see the restatement warning below** |

**⚠ NEVER SUM THESE ROWS ACROSS A CYCLE.** The ledgers restate the whole cycle to date, so the
same donation is republished under every later deadline: the 1,518 contribution rows carry only
**676 distinct donations** and the 1,738 expenditure rows **758 distinct payments**. Every row
therefore ships `is_incremental=False`, and a cycle total is the **latest filing's ledger**.

### 8.3 The 204 sides, and the basis each was scored on

| verdict | sides | what it means |
|---|---:|---|
| `stated-exact` | **57** | sums EXACTLY to the figure in `stated_total_*` → `reconciles_*=True`, delta `0.00` |
| `cumulative-exact` | **63** | sums EXACTLY to the summary sheet's **own column read down to this deadline** → `reconciles_*` left **BLANK** |
| `delta` | **42** | a PROVABLY COMPLETE parse matching neither printed figure → published verbatim, `reconciles_*=False`, `needs_review=1` |
| `empty-schedule` | **41** | the ledger exists and prints no lines |
| **`withheld`** | **1** | the parse is provably short — nothing published |

**Why `cumulative-exact` leaves `reconciles_*` BLANK rather than True.** Under the
owner-ratified RECONCILIATION-BASIS RULE a side is scored against the printed figure that
matches ITS OWN SCOPE. These rows reconcile to the cent against a quantity the sheet states,
but that is a *different scope* from the single printed row this module publishes in
`stated_total_*`. Asserting `True` would claim a match the published columns do not make. This
is the mirror of `utah_county`'s `cumulative-exact` verdict and is treated identically there.
**A blank `reconciles_*` here is NOT a failure.**

**Why `delta` sides are published rather than withheld.** Publication is gated on
**completeness**, not agreement: the family reports how many money-bearing rows it FOUND in each
ledger body against how many it EMITTED, and they must agree. On a complete parse the residual
can only be the FILER's arithmetic — a fact about the document — so the rows ship verbatim with
every competing printed figure named in `filing_totals.notes`. `recon_delta_*` is left blank on
purpose: differencing a cycle-scoped sum against a period-scoped total is a basis error, not a
delta (utah_county reached the same conclusion 2026-08-20 and reverted the derivation).

Worked example, verifiable in the source: **Brock Belnap, Attorney, 2010** — the contributions
ledger prints one line, `Brock Belnap 3/12/2010 $500.00`, while the summary states `$0.00`
contributions, `$500.00` expenditures and a `-$500.00` balance. The filer omitted his own
contribution from the summary. The row is published; the summary is not corrected.

**The one withheld side: Cory Pulsipher, Sheriff, 2010-04-06 contributions.** The county's own
export prints **`$5,00.00`** for the Accu Form Plastics line (the summary's arithmetic implies
$5,000.00). A malformed money token is never repaired, so that row cannot be emitted, so the
side's sum is provably short and the whole side emits nothing with the reason recorded.

### 8.4 Four defects found in the reading path, each fixed at emission

1. **Multi-page column drift (the largest loss).** The ledgers were read through
   `pdftotext -layout`, whose character-cell reconstruction is **not stable between pages of one
   document**: on `Expenditures - Rob Tersigni.pdf` the Amount column lands at character columns
   40-47 on page 1 and 19-26 on page 2, while the header is printed once, on page 1. Every row
   on pages 2+ failed the column test and was dropped — that 2-page file emitted **23 of its 36
   rows**, and its 4-page sibling `6-15-2010 Expenditures - Rob Tersigni.pdf` **23 of 77**. In
   the PDF's own coordinates there is no drift at all (both files' amounts right-align to
   `x=305.0` on every page). The module now reads word boxes from `pdftotext -bbox-layout`
   (`bbox_lib.py`), builds ONE column model from the printed header, and applies it to every
   page. That also yields the `pct:` geometry these rows now carry — measured, not inferred.
2. **In-kind and loan figures dropped silently.** Rows whose money sits in the `In Kind` or
   `Loan` column with `Amount` empty were skipped without a word. Kevin Brooks 2010 is the
   specimen: J Ryan Lee's `$400.00 / $100.92 / $243.13` right-align to `x=454` under `In Kind`
   while cash amounts right-align to `x=395` under `Amount`, and the summary's own `$744.05`
   row proves the county counts them as contributions. They now ship with `in_kind=True`; a
   Loan-column figure ships as `donor_type='loan'`.
3. **A second stacking layout, and a PRIVACY leak waiting in it.** The 2014–15 workbooks print
   NAME INLINE with the figures and the street address on the row below; the **2012** generation
   prints the NAME ABOVE and the ADDRESS on the figures' row. Read as if it were the first, the
   *address* becomes `donor_raw`. The two are told apart by whether the figure row's own name
   cell reads as an address, and a held-over line **carrying digits is always an address**
   (`460 N 2460 W, Hurricane UT 84737` matches no street-word hint) — kept as city/state only.
4. **The multi-file emission bug** (`SCHEMA.md` §2a caveat 1, queued since 2026-08-02). Rows
   were stamped with the *group's* Summary file as `source_filing` while their `line_no` and
   `geometry` were measured inside the ledger file, so `(source_filing, line_no)` — the schema's
   itemized-row key — pointed at the wrong document. **Fixed at emission**: each row now names
   the part file it was read from. `make_snippet.py` no longer needs its span-content repair for
   this family.

Also corrected in the same pass: the workbooks' expenditure sheets head their date column
**`Date`**, not `Received`, so the column was never located and 1,174 rows shipped with a blank
date beside a perfectly good Excel serial.

### 8.5 What this tranche deliberately did NOT publish

* **The 4 `ledger_only` 2008 postings.** The `Detailed … Report` prints its column header once
  and re-lays the table out on every following page, and the filing prints no total at all —
  there is nothing to prove completeness against. Their counted sums remain in
  `portal_reconciliation.csv`, labelled *counted*, never *stated*.
* **The 100 handwritten cover forms** — §9.

### 8.6 Geometry, proved rather than asserted

Two-crop + control render on the page the old reader dropped entirely —
`Expenditures - Rob Tersigni.pdf` **page 2**, 13 emitted rows:

| crop | region | renders |
|---|---|---|
| first row | `2/pct:44.00,11.12,5.86,1.24` | `Office Max │ │ $153.98 │ │ Mailing` |
| last row | `2/pct:44.00,50.76,5.86,1.24` | `WalMart - Costco │ │ $547.87 │ │ Dinner & Gala` |
| **control**, one row pitch (3.30 pct) past the last | `2/pct:44.00,54.06,5.86,1.24` | **empty ruled cells** |

— so no row was missed and no row index is shifted (the failure mode that still SUMS and which
the arithmetic gate therefore cannot see). Resolve any row with
`python3 scripts/campaign_finance/make_snippet.py --csv washington_county/campaign_finance/contributions.csv --row N --module washington_county/campaign_finance`.
Spreadsheet rows carry a real cell reference and **no page image exists for them** — that is the
honest n/a, not a missing value.

### 8.7 Reproducibility

`python3 extract_born_digital.py && python3 build_finance.py` re-runs **byte-identical** on all
three CSVs. `extract_born_digital.py` rewrote only the 106 born-digital caches and only their
`generated_utc` line; **no `vision-transcribed` cache was touched** (its hard guard held).
`validate_finance.py` → **PASS (0 fails, 203 warns)**, all 203 warns the structural
`409 − 206 = 203` companion-file warning this dataset has always carried.

## 9. THE REMAINING QUEUE — 100 handwritten filings (a future vision wave)

Ledgered here so it is a measured queue, not an unknown. These are the image-faced
17-16-6.5 cover forms with Form A (contributions) and Form B (expenditures) behind them; their
**stated totals are already transcribed and published** — what is missing is the donor/vendor
itemisation.

Counted at the FILING grain from the 100 `cover_form` caches (each is one file):

| reporting year | filings | | office | filings |
|---|---:|---|---|---:|
| 2006 | 1 | | Commission Seat C | 18 |
| 2010 | 14 | | Treasurer | 12 |
| 2014 | 3 | | Recorder | 12 |
| 2016 | 7 | | Commission Seat A | 12 |
| 2018 | 15 | | Assessor | 10 |
| 2019 | 4 | | Sheriff | 9 |
| 2020 | 23 | | Clerk/Auditor | 9 |
| 2022 | 3 | | Commission Seat B | 8 |
| 2024 | 17 | | Attorney | 6 |
| 2025 | 13 | | Commission (seat not stated) | 4 |
| **total** | **100** | | **total** | **100** |

(= 95 files the index calls `scanned` **plus** the 5 it mislabels `text`; `reporting_year` is
filled on all 100.)

Sized like juab/wasatch rather than like utah. **The calibration pre-flight has NOT been run
for washington** — the suite carries exactly one washington specimen (`washco-wrapped-ledger`,
the Lin Alder 2008 completeness-gate negative control) and `_audits/cf-calibration-suite/runs.md`
records no washington run. Do that first. (§8 needed none: it read no page images, and its gate
is the document's own arithmetic plus a machine-checkable completeness count.)

---

## 10. THE HANDWRITTEN QUEUE — CLOSED 2026-08-24 (the Phase-B final vision wave)

**§9's 100-filing queue is closed at 100 of 100.** With §8's parser tranche, **every document
this dataset holds is now itemized**, and washington_county is the first Phase-B county whose
BOTH eras are closed.

### 10.1 The queue, re-derived rather than inherited

`prep.py` re-derived it from the primary files instead of trusting §9's count: a filing is in
the queue when its `vision/<key>.json` has `sheet_type='cover_form'` **and** no row of
`contributions.csv` / `expenditures.csv` names any of its files. That returns **100 documents /
401 pages** — independently reproducing §9's 95-`scanned`-plus-5-mislabelled-`text` finding
**without using `index.csv.format` at all**, which is the column §8.1 warns is unsafe here.

### 10.2 What was published

| | |
|---|---:|
| documents transcribed | **100 of 100** · 401 pages · 0 unfinished |
| rows | **530 contributions + 778 expenditures = 1,308** |
| rows carrying `pct:` geometry | **1,308 of 1,308 (100%)** |
| sides `transcribed` / `none` / **withheld** | 199 / 1 / **0** |
| side verdicts | 173 `exact` · 12 filer-arithmetic `delta` · 15 `unknown` (no printed anchor) |
| scope split | **127 sides cumulative · 64 period · 9 undetermined** |
| amounts blank for illegibility | **0** |
| escalations (tight cell crops, 500–2400 dpi) | 524 |

`contributions.csv` is now **2,048 rows** and `expenditures.csv` **2,516** across both eras.
**Rebuild is byte-identical**; `validate_finance.py` → **PASS (0 fails, 203 warns)** — the same
structural `409 − 206 = 203` companion-file warns this dataset has always carried.

### 10.3 The reconciliation basis, and the trap it avoids

**Form "A" itemizes only contributions OVER $50.** The cover's line 2 (`Aggregate total of
contributions of $50.00 or less`) is never itemized, while `stated_total_contributions`
publishes **line 1 + line 2**. Every contribution side is therefore scored against **line 1**;
scoring against the published sum would have manufactured a false mismatch on every filing with
a small-donor aggregate. Several filers do the opposite — they itemize their sub-$50 gifts on
Form A anyway — and those sides gate on the schedule total with the decomposition recorded.

**Scope is tested per filing, not assumed.** This module publishes the CUMULATIVE column, so a
side summing to CUMULATIVE is same-scope (`reconciles_*=True`) while a side summing to the
THIS-REPORT cell is a genuinely per-period schedule at a **different scope** — published with
`reconciles_*` left BLANK, `is_incremental=True`, and both figures named. **A blank
`reconciles_*` is not a failure**, exactly as §8.3 already establishes for the parser era.

### 10.4 A THIRD form generation, found at the page

§8 and the wave brief described two generations. There is a **third**, and it breaks the rule
that would have been inferred from form age: `WASHINGTON COUNTY CANDIDATE FINANCIAL CAMPAIGN
REPORT`, citing **Washington County Code 1-7-1**, which has Generation 1's dense ~35-line ruled
grid **but does print a footer TOTAL on both schedules and does carry an `In Kind?` column**.
Newer covers also drop the `$50-or-less` line entirely (recorded `null` — the field is ABSENT,
not blank). **Decide the anchor by what the sheet actually prints, never by the form's vintage.**

### 10.5 Two currency conventions that are 100× hazards, and how they are read

The handwritten era writes cents in ways no text-layer parser ever had to meet:

* **space-separated cents** — `63 75`, `29 75`. A reader that strips spaces (as this module's
  own `dec()` does, correctly, for the genuine thousands-space `2 844.02`) yields **6375** and
  **2975**. The two are told apart by GROUP LENGTH — a 3-digit group is thousands, a 2-digit
  group is cents — and by nothing else.
* **superscript cents over a rule** — `360.⁰⁰`, `52.8²`, `916.²⁴` — plus a dash or point in the
  cents position (`200 —`) meaning whole dollars.

These are read by the shared `common.parse_vision_amount`, an explicit whitelist that leaves
anything ambiguous BLANK and **still refuses the malformed decimals** the
`utah-malformed-decimal` calibration specimen requires to stay blank (`23,744,71`, `23.744.71`,
and this county's own `$5,00.00`). Proof it is reading and not repair, on
`raw/live_wp/2006-David-Whitehead.pdf`: the nine rows sum to **916.24**, exactly the figure
printed in that schedule's TOTAL cell and on the cover's line 3; the naive space-stripping read
gives 9,228.49 and closes against nothing.

**Independent check across the whole wave:** for every side where a transcriber recorded its own
row-sum, the build's independently computed sum was compared against it — **158 of 158 sides
agree, 0 mismatches.**

### 10.6 Bundles

19 PDFs staple several reports (up to four). Every report's Form A/B is transcribed, each row
carries the report it belongs to, and `line_no` is renumbered 1..N across the whole document so
`(source_filing, line_no)` stays the schema's unique itemized-row key. Because the filing
publishes ONE cover row in `stated_*` while the PDF carries several, a bundle leaves
`reconciles_*` **BLANK** and records a **per-report verdict** in `filing_totals.notes`.

### 10.7 A defect corrected in another layer, with evidence

The wave read all 100 covers and found **36 `index.csv` `candidate` values that are tesseract
noise** — `D A v 1 9) wh, TERE AD`, `— .— Wier: Alber en ee`, `en 13 uUce Den é & ee`, and in
three cases a single stray letter. They are corrected through a **new curated override,
`candidate_determinations.csv`**, on the identical contract as `office_determinations.csv`: the
page's own `Full name of Candidate` line, quoted as evidence, wins over the OCR cascade; a file
with no determination row is untouched; and the OCR reading is still retained verbatim in
`document_candidate`. A column-level diff bounds the change at exactly **36 rows × 3 derived
columns** (`candidate`, `title`, `candidate_source`) with **0 other values moved**.

### 10.8 What is still NOT here

Nothing in the itemisation queue — it is empty. The dataset's honest gaps are unchanged and
remain the ACQUISITION ones of §4: `outpost` is unlistable and unarchived, the 2016–2024 listing
page was never archived with content, 6 Wayback URLs are genuine 404s, and 2 retrieved files
have no determinable office. The **4 ledger-only 2008 postings still emit no rows by design**
(§8.5). An empty itemized side means *empty schedule* or *no schedule page in the document* —
**never "no donors"**.
