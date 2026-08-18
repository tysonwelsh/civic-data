# Campaign-finance disclosures — availability & sources checked

**As-of 2026-08-01.** Summit County **COUNTY-OFFICE** candidate campaign financial reports
(Utah Code **17-16-6.5**, filed with the County Clerk): County Council, Attorney, Auditor,
Clerk, Sheriff, Assessor, Recorder/Surveyor, Treasurer — cycles **2014, 2016, 2018, 2020, 2022,
2024, 2026**.

**Result: COMPLETE against every channel that publishes this material.** **131 filings / 74
candidate-cycles**, and **every one of the 56 county candidates who appeared on a Summit ballot
2014–2026 — including all 38 general-election winners — has at least one report here.** The
channel survey behind these numbers is `RECON.md`; the per-filing record is `index.csv`.

**Money layer (2026-08-17): STATED TOTALS COMPLETE (131) + the ITEMIZED LAYER COMPLETE (131 of
131 — the born-digital 15 parsed 2026-08-02, the 116 SCANS vision-transcribed 2026-08-14/17).**
All 131 cover pages were vision-transcribed and `filing_totals.csv` carries each
filing's printed contribution / expenditure / ending-balance figures — see "Stated totals"
below. The **15 born-digital filings** were then parsed by the registered `summit_form` family:
**105 contribution + 386 expenditure rows over 11 filings**, 4 contribution sides and 11
expenditure sides reconciling EXACTLY to the published stated total (100% `geometry` coverage;
0 of 131 `stated_*` values changed). **The 116 SCANS were then itemized by Read-tool vision in
TRANCHE 3 Phase B — 24 filings verified 2026-08-14, and the remaining 92 completed and verified
2026-08-17, when the queue CLOSED** (of those 92, **90 were transcribed by the paused wave's
killed legs on 2026-08-14 and re-screened from scratch on 08-17** — see the state audit — and
**2 were transcribed on 08-17**; 1,170 contribution + 1,349 expenditure rows in all, 100%
geometry-carrying, 165 of 196 transcribed sides reconciling exactly). Full record: "The SCAN itemization wave — QUEUE CLOSED
2026-08-17" at the end of this file. What the gates refused — Harte 2026's period-scoped ledger
under a cumulative cover, the wrapped-2014 sections, and the 21 sides withheld on the
period-vs-cumulative grain question — is itemised there and in `CLAUDE.md`.

---

## Where these actually live

The **County Clerk publishes them, nobody else.** County-office candidates file under Utah Code
17-16-6.5 with the Clerk; the state Lieutenant Governor's system covers **state** offices and a
`/Municipal/` tree for **city/town** filings (10-3-208), and school-board candidates file under
20A-11-1301..1305 on yet another form. So the entire dataset comes from one county page —
`https://www.summitcountyutah.gov/536/Financial-Reports` — plus the DocumentCenter IDs that page
used to list and still serves.

## Sources checked (each URL, and what it had)

| source | URL / query | result |
|---|---|---|
| **County Financial Reports page (live)** | `summitcountyutah.gov/536/Financial-Reports` | ✅ **69 county-office filings**, cycles **2020 / 2022 / 2024 / 2026**. Downloaded directly (urllib + browser UA — CivicEngage is Akamai-403 to plain fetchers). Page capture kept at `raw/index_pages/536_Financial-Reports_2026-08-01.html`. |
| **Wayback — the live page** | CDX `summitcountyutah.gov/536*` | ⚠ only 3 captures, all 2025-01+. No pre-2020 depth here. |
| **Wayback — the PREDECESSOR host** | CDX `co.summit.ut.us/536*` → captures `20150303`, `20151230`, `20161130`, `20170421`, `20190618` | ✅ recovered the **2014 / 2016 / 2018** candidate→document listings that the live page dropped. 5 captures kept under `raw/index_pages/`. |
| **DocumentCenter, delisted-but-live-by-ID** | the 2014/2016/2018 IDs read off those listings, fetched against the **current** host | ✅ **62 of 63 served live** (200 + `%PDF-`, original filename in `Content-Disposition`). The CMS kept the objects; only the listing dropped them. Original bytes preferred over a Wayback replay. |
| **State LG — `/Municipal/summit*`** | full recursive walk: **34 folders**, **165 files**; every fetchable file opened, **158 rendered + OCR'd** to read the form header AND the "Office Filed For" line | ❌ **0 county-office filings.** Per-folder ledger: `state_sweep.csv`. |
| **State LG — county / even-year folders** | `/County/`, `/Municipal/summit_2020`, `/Municipal/summit_2022`, `/Municipal/summit_2016`, `_2024`, `_2025`, `_2026` | ❌ `/County/` 404; `summit_2020` and `summit_2022` return *"Path … does not exist"*; `2016/2024/2025/2026` exist but are **empty**. |
| **DocumentCenter IDs below the 2014 band** | probe ID 681 (a pre-2014 listing target) | ❌ 404 — the pre-2014 objects are gone. |
| **PMN (Utah Public Notice)** | not applicable | campaign-finance reports are not meeting notices; no PMN path exists. |

### The state-folder check was done under the FORM-HEADER rule — and the rule inverted

Per the coordinator's residence-town warning, folder labels were treated as meaningless and every
file was opened. The header rule ("county filings cite 17-16-6.5") produced **29 false positives**
in Summit: those 29 carry the county statute header but every one names a **city, town or
special-district** office inside — Coalville City Council, Mayor of Coalville, Henefer town
council, Oakley City Council, South Summit Fire District. Summit's Clerk supplies the *county*
blank form to the small municipalities. The discriminator that actually holds is the **"Office
Filed For" line inside the form**, backed by cycle parity (Summit county offices are elected in
**even** years; all 29 sit in 2017/2019 folders). The one even-year state folder, `summit_2008`,
holds **9 school-board reports** filed under 20A-11-1301. Details in `RECON.md` §3.

---

## Coverage matrix — filings by office × cycle

| office | 2014 | 2016 | 2018 | 2020 | 2022 | 2024 | 2026 | total |
|---|---|---|---|---|---|---|---|---|
| County Council seat A | · | 1 | · | 2 | · | 5 | · | **8** |
| County Council seat B | · | 3 | · | 2 | · | 3 | · | **8** |
| County Council seat C | · | 2 | · | 3 | · | 6 | · | **11** |
| County Council seat D | 4 | · | 2 | · | 4 | · | · | **10** |
| County Council seat E | 4 | 4 | 4 | · | 8 | · | · | **20** |
| County Council district 4 | · | · | · | · | · | · | 3 | **3** |
| County Council district 5 | · | · | · | · | · | · | 3 | **3** |
| County Attorney | 4 | · | 2 | · | 2 | · | 1 | **9** |
| County Auditor | 4 | · | 2 | · | 2 | · | 1 | **9** |
| County Clerk | 4 | · | 2 | · | 4 | · | 3 | **13** |
| County Sheriff | 4 | · | 2 | · | 2 | 2 | 1 | **11** |
| County Assessor | 2 | · | · | 2 | · | 2 | · | **6** |
| County Recorder/Surveyor | 6 | · | 2 | 2 | · | 3 | · | **13** |
| County Treasurer | 4 | · | · | 1 | · | 2 | · | **7** |
| **total filings** | **36** | **10** | **16** | **12** | **22** | **23** | **12** | **131** |
| distinct candidates | 18 | 6 | 8 | 6 | 13 | 14 | 9 | **74** |

*(Updated 2026-08-01: the two formerly `office unresolved` rows are Walter Brock's, now resolved to
County Recorder/Surveyor by the vision pass — see the gap ledger. No row is unresolved.)*

Blank cells are **not gaps** — Summit's county offices are staggered, so only some are on the
ballot in a given even year (2016 was a Council-only cycle; 2018 had no Assessor or Treasurer
race, etc.). Cross-check any cell against `../elections/election_results_by_contest.csv`.

**Candidate coverage (computed by `build_index.py`):** 56 county candidates appear on a Summit
county ballot 2014–2026 in the elections layer; **0 of them lack a filing here.** 38 general-
election winners 2014–2024; **0 lack a filing.**

## Reporting-period mix (131)

Pre-Election 56 · Post-Election 55 · Primary 12 · Final 2 · Withdrawn 2 · Out at Convention 2 ·
Out at Primary 1 · Appointment Report 1. The pre-2020 cycles use only Pre-/Post-Election; 2024
introduced the convention/primary-exit report; 2026 uses Pre-Primary / Primary / Final labels.

## Corpus condition

**116 of 131 are scanned handwritten forms; only 15 are born-digital.** Of the scans, **69** carry
a text layer the clerk's scanner produced (good on the printed form, poor on the handwriting) and
**47** had none and were OCR'd here at 300 dpi. Per-filing `text_quality` (does the sidecar
contain the filer's own surname AND ≥2 legible money tokens):

| | 2014 | 2016 | 2018 | 2020 | 2022 | 2024 | 2026 | total |
|---|---|---|---|---|---|---|---|---|
| high | 23 | 6 | 11 | 6 | 17 | 18 | 8 | **89** |
| medium | 3 | 2 | 5 | 3 | 3 | 4 | 2 | **22** |
| low | 10 | 2 | · | 3 | 2 | 1 | 2 | **20** |

`low` = the sidecar has **no machine-readable numbers**; the raw PDF is the only source for that
filing. These 20 were the `cf-vision-transcribe` queue — **now cleared** (below).

⚠ **`text_quality` describes the OCR, not the document.** The 2026-08-01 vision pass read a
legible cover box on **19 of the 20 `low` rows** (the twentieth, Franchek 2022 `20650`, is a dark
photocopy whose cover box is still readable but whose Current contributions cell is a struck-out
figure). Do not use `text_quality` to decide whether a filing's figures exist — use
`filing_totals.csv`.

---

## Stated totals — the 2026-08-01 vision pass

**Method:** `cf-vision-transcribe` (Read-tool, **$0 API** — billed to the Claude Code allotment,
not the Anthropic API credit balance). Every filing's page 1 was rendered with
`pdftoppm -jpeg -r 200`, cropped to the top 80%, and read natively. **131 of 131 cover pages
transcribed** (0 text-parsed: only **29 of 131** sidecars carry a machine-readable
`Current Report / Last Report / Cumulative Totals` header line, so a text path could not have
assigned columns unambiguously on the other 102 — and a silently transposed column is the exact
failure mode this dataset had to avoid).

| | 2014 | 2016 | 2018 | 2020 | 2022 | 2024 | 2026 | total |
|---|---|---|---|---|---|---|---|---|
| filings transcribed | 36 | 10 | 16 | 12 | 22 | 23 | 12 | **131** |
| with a stated **contribution** total | 36 | 10 | 14 | 9 | 22 | 22 | 12 | **125** |
| with a stated **expenditure** total | 36 | 10 | 16 | 12 | 22 | 23 | 12 | **131** |
| with a stated **ending balance** | 36 | 10 | 14 | 11 | 20 | 21 | 12 | **124** |

`extraction_confidence`: **high 116 / medium 15** (`low`: none — a cell that could not be read
was left blank/`ILLEGIBLE` rather than transcribed at low confidence).

### The column-order verification (the trap this tranche had to not fall into)

Summit prints **`Current Report | Last Report | Cumulative Totals`** — the reverse of the sheet
`millcreek_form` / `ogden_form` assume. Three independent lines of evidence fix the order:

1. **The clerk's own printed instruction box**, on the 2016/2022/2024 sheets: *"Enter the
   information from your last report in the **last report** column."* (visible on `4013`, `4305`,
   `20636`, `20640`, `20753`, `23740`, …).
2. **The born-digital calibration case, Langston 2022 (`20765`)** — the ONLY filing whose vision
   read can be checked cell-for-cell against a clean `pdftotext -layout` sidecar. They agree
   exactly: contributions `503.00 | 0.00 | $503.00`, expenditures `511.62 | 0.00 | $511.62`,
   balance `$11.14 | (empty) | $11.17`. This is the filing on which the two shared families both
   return **511.62 as "total contributions"** (RECON.md §4) — i.e. they read the **Last** column's
   neighbour, not the cumulative.
3. **Successive-report chaining, verified on 21 filer pairs.** A Post-Election sheet's **Last
   Report** column reproduces that same filer's Pre-Election **Current** column, cell for cell —
   Forsling 2014 (`1086`→`1245`), Martinez 2014 (`1064`→`1248`) and 2018 (`8205`→`8358`),
   Williams 2014 (`1059`→`1251`), Coleman 2014 (`1085`→`1256`), Shumway 2014 (`1089`→`1260`),
   Brickey 2014 (`1092`→`1264`), Hilder 2014 (`1087`→`1265`), Yost 2014 (`1098`→`1268`),
   Wharton 2014 (`1091`→`1274`), Wright 2016 (`4009`→`4180`), Stevens 2020 (`11110`→`11861`→
   `12943`), Keyes 2022 (`20636`→`20757`), Olson 2022 (`20641`→`20760`), Robinson 2022
   (`20645`→`20761`), Furse 2022 (`20651`→`20762`), McClure 2022 (`20639`→`20758`), Murphy 2022
   (`20640`→`20766`), Hanson 2024 (`24237`→`24381`), Wolbach 2024 (`24240`→`24390`),
   Ioannides 2024 (`24231`→`24382`), McKenna 2024 (`24232`→`24384`), Forsling 2024
   (`24244`→`24393`), Reed 2026 (`27208`→`27450`), Kucera 2026 (`27204`→`27451`).
   **Zero counter-examples**: no Post-Election sheet ever carried the prior Current figure in its
   Cumulative column instead.

All three cover cells are kept verbatim and labelled in `vision/<key>.json` and republished in
`cover_totals.csv` (451 rows), so every promotion in `filing_totals.csv` is auditable without
reopening a PDF. The promotion rule is documented in `CLAUDE.md`.

### Independent re-verification, 2026-08-02 (the anti-transposition audit)

The 2026-08-01 transcription pass was verified by a **separate session that re-rendered and
re-read the source PDFs from scratch** rather than trusting the caches. Recorded here because an
unrecorded verification does not count.

**Structural checks — all pass.** 131 `vision/*.json` parse; their cache keys are **1:1** with
`index.csv`'s 131 rows (no orphan cache, no uncached filing); `build_finance.py` rebuilt twice is
**byte-identical** (sha1 on all four outputs); `validate_finance.py` returns **PASS (0 fails,
0 warns)**.

**Column-order sample — 17 filings, all seven cycles, all five form variants, no transposition
found.** Each was re-rendered (`pdftoppm -jpeg -r 200`, whole page) and read against its cache
cell-by-cell. "Cols on page" is the header row as actually printed.

| doc | filer / cycle / period | office | variant | cols on page | promoted (basis) | result |
|---|---|---|---|---|---|---|
| `20765` | Langston 2022 Post | Clerk | single_total | Current \| Last \| Cumulative | C 503.00 · E 511.62 · B 11.17 (cumulative) | ✅ exact; **calibration case** — also matches `pdftotext` |
| `1086` | Forsling 2014 Pre | Treasurer | split50 | Current \| Last \| Cumulative | C 13,532.96 (13,482.96+50.00) · E 13,532.96 · B 0.00 | ✅ exact |
| `1081` | Brock 2014 Pre | Recorder/Surveyor | split50 | Current \| Last \| Cumulative | C 2,662.89 · E 2,662.89 · B 0.00 | ✅ exact; office line reads **RECORDER/SURVEYOR**, party **WRITE-IN** |
| `1244` | Brock 2014 Post | Recorder/Surveyor | split50 | Current \| Last \| Cumulative | C 2,662.89 · E 2,662.89 · B 0.00 | ✅ exact; surname reads **BROCK** here (`1081` reads BLOCK) |
| `1273` | Ure 2014 Post | Council E | narrative_letter | (no column box) | C 3,400.00 · E 3,370.00 · B 30.00 | ✅ exact against the handwritten letter |
| `4278` | Adair 2016 Post | Council | split50 | Current \| Last \| Cumulative | C 22,427.00 · E −25,353.12 · B −2,926.32 (cumulative) | ✅ column assignment correct; middle cell corrected (below) |
| `8196` | Francis 2018 Pre | Recorder | single_total | Current \| Last \| Cumulative | C **blank** · E 293.54 · B **blank** | ✅ contributions + balance rows are genuinely EMPTY on the form |
| `8205` | Martinez 2018 Pre | Sheriff | split50 | Current \| Last \| Cumulative | C 5,809.71 · E 687.52 · B 5,122.19 | ✅ exact |
| `11860` | Clyde 2020 Pre | Council | single_total | Current \| Last \| Cumulative | C **blank** (nil-marked row) · E 277.38 · B −277.38 | ✅ exact |
| `12943` | Stevens 2020 Post | Council C | single_total | Current \| Last \| Cumulative | C 10,157.17 · E 9,642.52 · B 514.65 | ✅ exact; confirms the 9,642.52 correction |
| `20638` | Martinez 2022 Pre | Sheriff | split50 | Current \| Last \| Cumulative | C 2,584.54 · E 825.33 (**rule 3**: cumulative prints 0.00 against a non-zero Current) · B 1,759.21 | ✅ exact; a `split50` sheet filed in 2022 |
| `20640` | Murphy 2022 Pre | Council E | single_total | Current \| Last \| Cumulative | C 5,100 · E 3,733.22 (**current**, cumulative cell ILLEGIBLE) · B 1,366.78 | ✅ exact; the cumulative expenditure glyph is genuinely ambiguous — correctly NOT guessed |
| `20753` | Siddoway 2022 Post | Sheriff | single_total | Current \| Last \| Cumulative | C 825.33 · E 825.33 · B **blank** | ✅ exact; the Current column is the filer's slashed-zero glyph, recorded blank per the module convention |
| `23015` | Richardson 2024 Convention | Council A | single_total_2024 | Current \| **Previous** \| Cumulative | C 1,064.46 · E 904.15 · B 160.31 | ✅ money exact; confirms the 1,064.46 correction. **Signature date was wrong** (below) |
| `24231` | Ioannides 2024 Pre | Council | single_total_2024 | Current \| **Previous** \| Cumulative | C 23,744.71 · E 32,744.71 (cumulative) · B 0 | ✅ exact, incl. the three filer typography errors and the EMPTY name/office/party boxes |
| `24237` | Hanson 2024 Pre | Council B | single_total_2024 | Current \| **Previous** \| Cumulative | C 640.86 · E 640.86 (**rule 3**) · B 0.00 | ✅ exact; the template's default `$ 0.00` cumulative confirmed on the page |
| `27205` | Olson 2026 Primary | Attorney | single_total_2026 | Current \| Last \| Cumulative | C 1,140.39 · E 1,140.39 (**rule 3**, Excel zero-dash cumulative) · B 0 | ✅ exact; `Name of Office` box is genuinely EMPTY |

**Finding: zero transpositions.** In all 17 the printed header row is `Current … | Last/Previous … |
Cumulative …`, the cache's `column_order` matches it, every verbatim cell matches the page, and
every promoted figure follows the documented rule. The reversed-column trap was **not** fallen
into. (The coordinator's proposed ground-truth case, "Granger 2022", is a **`wasatch_county`**
filing — Summit has no such filer; the Summit-native ground truth is the born-digital Langston
`20765`, which can be checked against a clean text sidecar.)

**Three money-cell corrections had already been applied on 2026-08-02** before this audit and are
each confirmed correct against the page, with the evidence written into the filing's cache:
`12943` cumulative expenditure `9,647.52` → **`9,642.52`** (and 424.80 + 9,217.72 = 9,642.52
exactly); `23015` cumulative contribution `1,044.46` → **`1,064.46`** (matches the filer's own
balance, 1,064.46 − 904.15 = 160.31); `4278` Last-Report expenditure `$7760.68` → **`$7,710.68`**
(17,642.44 + 7,710.68 = 25,353.12, the printed cumulative — no promoted figure changes).

**What the audit DID find: the signature-date field was systematically under-captured.** The
2026-08-01 pass rendered page 1 **cropped to the top 80%**, which cuts the signature/date line off
most sheets — several caches even say *"signature date not visible in the cover crop."* Re-read at
full page, **45 of the 51 supposedly blank dates are legibly printed**, and one populated date was
misread (`23015` `4/10/24` → **`4/18/24`**, the second digit is a closed 8). All 46 were corrected
in the per-filing `vision/*.json` with the evidence, and the layer was rebuilt:
**`filing_date` populated 80 → 125 of 131.** Nothing else changed — a full-column diff of
`filing_totals.csv` before/after shows **`filing_date` as the only differing column**. Rebuilt
twice, byte-identical; validator still PASS.

Residual honesty note: the money layer was sampled at 17 of 131 (13%) and the date field at 51 of
51 blanks + 14 populated. **One of those 14 populated dates was wrong (~7%)**, so a small number of
transcribed dates elsewhere may still be off by a digit; the money cells showed no such error in
any sample. A full 131-filing date re-read is a described follow-up, not a claim made here.

### Honest blanks in the stated-totals layer

- **6 filings state no contribution total** — the contributions row is **empty on the form**:
  Rhonda Francis 2018 Pre/Post (`8196`, `8359`) and 2020 Post (`12944`), Douglas Clyde 2020
  Pre/Post (`11860`, `12941`), Dallin Donaldson 2024 Withdrawn (`23014`). **Blank, not zero.**
- **7 filings state no ending balance** — the balance row is empty or struck on the form:
  Francis 2018 Pre/Post + 2020 Post, Olson 2022 Post, Siddoway 2022 Post, Poll 2024 Pre, and
  Welch 2024 Post (whose balance cell still shows the fillable form's placeholder text
  *"Type text here"* — it was never filled, so the 509.44 from his Pre-Election sheet was NOT
  carried across).
- **5 individual cells are `ILLEGIBLE`** in `cover_totals.csv` — struck-through or over-written
  figures that were **not guessed** (Martin 2014 `1065` balance ×2, Murphy 2022 `20640`, Franchek
  2022 `20650`/`20751`). The consequential one: Murphy 2022 Pre-Election (`20640`)
  cumulative expenditure is genuinely ambiguous between `$3733.22` and `$3738.22`; his own
  Post-Election sheet prints `3733.22` in its Last Report column, recorded in the cache as
  evidence but **not** back-filled into `20640`.
- **6 rows have no `filing_date`** (was 51 before the 2026-08-02 date pass — see the verification
  section). This layer's `filing_date` is the **form's own printed signature date**; the
  `index.csv` PDF-CreationDate proxy is never substituted for it. The six, each checked at full
  page: `1273` Ure 2014 (the narrative letter — no date line at all; the clerk's `RECEIVED DEC 04
  2014` stamp is the county's, not the filer's, and is never promoted), `8192` Mann 2018 Pre (date
  line left empty), `8397` Mann 2018 Post (**the filer wrote only `12/8`, no year** — kept verbatim
  in the cache, never completed from the cycle year), `20651` Furse 2022 Pre (dark photocopy, date
  illegible), `20752` + `20634` Harte 2022 (both date lines left empty).
- **Two printed dates are the filer's own oddities, retained exactly as filed:** `23014` Donaldson
  2024 Withdrawn is dated **`2/5/2023`** — a year before the cycle (`filing_date=2023-02-05`);
  `27204` Kucera 2026 wrote **`June 7th 2026`** with an ordinal.
- **Filer arithmetic errors are retained verbatim** and itemised per filing in
  `filing_totals.notes` (negative expenditure totals, template-default `$0.00` cumulative columns,
  comma-for-decimal typos, balances that do not follow from the filer's own rows).

## Gaps (honest, evidence-cited)

Machine-readable ledger: `unrecovered.csv` (8 rows).

- **Data floor 2014.** No county-office campaign-finance report exists on any channel for the
  2008 / 2010 / 2012 cycles. The predecessor page's earliest capture (2015-03-03) already listed
  2014 as its newest and oldest cycle, and the pre-2014 DocumentCenter IDs 404. The county
  canvass proves the races happened; the reports were never published.
- **2022 County Auditor — Michael Howard: no report.** The county page lists him with `n/a` in
  **both** the Pre-Election and Post-Election columns. Not a retrieval failure — nothing was
  published.
- **2026 cycle still open.** Seven candidates have a Primary report but an **empty Final cell** as
  of the 2026-08-01 capture. Not-yet-due, not missing. Re-probe after the 2026 general.
- **Walter Brock (2014), 2 filings — office RESOLVED 2026-08-01, was unresolved.** Both scans were
  illegible to the clerk's scanner OCR layer and to this repo's tesseract pass, so the rows carried
  a blank office and `office_source=unresolved`. The vision pass reads the handwritten line
  cleanly on **both** sheets: **`Office Filed For: RECORDER/SURVEYOR`**, **`Party: WRITE-IN`**.
  Recorded as two rows in `office_overrides.csv` with the evidence; `index.csv` now shows
  `office=County Recorder/Surveyor`, `office_source=override:…`, `needs_review=0` (the flagged
  count drops 44 → 42). **Zero rows in `index.csv` now have an unresolved office.**
  Two residual observations, both honest and both left alone: (a) the surname on the Pre-Election
  sheet (`1081`) reads *BLOCK* and on the Post-Election sheet (`1244`) reads *BROCK* — the county
  listing and the DocumentCenter filename say Brock, which is what `candidate` carries; (b) he is
  a **write-in**, which is why no 2014 county contest in the canvass carries his name — consistent
  with, not contradicted by, the elections layer.
- **2014 County Recorder/Surveyor is missing from the elections layer, not from here.** Vicki Sue
  Richards and Mary Ann Trussell both filed for **Recorder/Surveyor** in 2014 (stated in their own
  filings, born-digital and legible), but `../elections/election_results_by_contest.csv` has no
  2014 Recorder/Surveyor contest. **Flagged, not fixed** — this dataset is additive and does not
  alter `elections/`. → coordinator lead.
- **Reporting dates are proxies.** `date` is the PDF's own CreationDate, kept only when its year
  matches the cycle year (99 of 131 rows); `date_basis` says so. The statutory due date is printed
  inside each form — read the raw PDF if you need it.

## Out of scope (deliberate, with leads)

- **School board** (North Summit / Park City / South Summit districts) — a different statute
  (20A-11-1301..1305) and form. The county page carries them on every cycle and the state tree
  holds 9 more for 2008; roughly **~110 school-board filings** are one page-parse away.
- **Summit municipalities & special districts** — Coalville, Kamas, Oakley, Francis, Henefer,
  Park City, South Summit Fire District: **165 files across 34 state folders**, enumerated with
  sha256 in this session and summarized in `state_sweep.csv` (the PDFs were **not** retained).
  `park_city_city_council/campaign_finance/` already exists and should be diffed against the
  state tree before any bulk pull.
- **Annual conflict-of-interest / financial-disclosure statements**
  (`summitcountyutah.gov/2552/Conflict-of-Interest-Disclosures`) — out of scope per
  `scripts/campaign_finance/SCHEMA.md` (C&E reports only).
- **State-office filings** by Summit-resident legislators — `disclosures.utah.gov`, and the
  `ut_state` entity's business.

## Privacy

`raw/` and `text/` are **verbatim reproductions** of government-published filings and are not
edited — including donor addresses printed on the face of the form (repo `PRIVACY.md`: verbatim
minutes and `campaign_finance/text` are never redacted). Note that the county **itself** redacted
the 2022 and 2026 filings before publishing (black-marker address/phone boxes; `…_Redacted`
filenames), inconsistently — Harte's, Keyes' and Robinson's 2022 Pre-Election copies are redacted
while their Post-Election copies are not.

The 2026-08-01 stated-totals tranche is **candidate-level only** and carries **no donor data at
all**: the `vision/*.json` caches hold the cover box, the candidate's own name/office/party as
printed and the signature date, and nothing else. **The candidate's own street address and phone,
where the form printed them unredacted, were deliberately NOT carried into any derived file** —
the juab precedent. **The "donor city/state only" rule now binds** (2026-08-02): the born-digital
itemized layer carries `donor_city` / `donor_state` and nothing finer, and a module-local PRIVACY
GUARD discards a street fragment the family left inside a donor name (2 rows, both flagged) —
see `CLAUDE.md` "The BORN-DIGITAL itemized layer".

## The SCAN itemization wave — TRANCHE 3 Phase B, verified 2026-08-14 (PARTIAL, resumable)

> **Superseded 2026-08-17 — the queue is now CLOSED (116 of 116).** This dated section is the
> verified leg-1 record and is left exactly as written; the wave's final measured state, the
> state audit that re-screened the killed legs' work, and the full reconciliation ledger are in
> **"The SCAN itemization wave — QUEUE CLOSED 2026-08-17"** at the end of this file.

Owner-approved 2026-08-14. Target: the **116 SCANNED** filings whose donor/vendor ledgers the
cover tranche left untranscribed. **This wave itemized 24 of the 116 and stopped on agent
capacity, not on any source problem. 92 remain QUEUED** — enumerable at any moment with
`python3 _backups/2026-08-14-tranche3/summit-b/wave_stats.py --residue`, never a hand-kept list.
An empty itemized layer on those 92 means **NOT TRANSCRIBED**, never *no donors*.

**Pre-flight:** the calibration suite was re-run in full from the raw PDFs before any bulk
transcription — **13 / 13 PASS**, all five negative controls held, the Rhodes specimen reached
by the document's own arithmetic with zero glyph escalations. Recorded as a new dated section in
`_audits/cf-calibration-suite/runs.md`; prior runs' conclusions were not edited.

### Measured (regenerate: `wave_stats.py`, then the counts below from the CSVs)

| | |
|---|---:|
| scanned filings itemized | **24 of 116** |
| still queued | **92** |
| rows published | **106 contributions · 229 expenditures = 335** |
| money in those rows | **$52,001.02 contributed · $57,704.98 spent** |
| rows carrying `geometry` | **335 of 335 (100%)** — 248 `measured`, 87 `declared` |
| sides EXACT-reconciled | **19 contributions · 20 expenditures** |
| sides with a documented delta | **2 contributions · 3 expenditures** |
| sides WITHHELD (grain question) | **2 contributions · 1 expenditure** |
| sides `none` (no such page in the document) | **1** |
| tight-crop escalations used | **11** (600–1400 dpi cell crops) |
| filings with a page-gate record | **24 of 24** |
| rows flagged `needs_review=1` | 13 (12 are dates the form prints without a year or at all) |
| rows with an illegible amount | **0** |
| per-row confidence | 335 `medium` (SCHEMA §6 caps vision at medium) |

Which filings: **2014** 1058 · 1059 · 1065 · 1080 · 1081 · 1085 · 1086 · 1087 · 1088 (9);
**2024** 23013 · 23014 · 23015 · 24237 · 24239 · 24240 · 24244 · 24247 · 24377 · 24381 · 24384 ·
24385 · 24388 · 24390 · 24393 (15).

### The four deltas and the three withheld sides — every one traced on the page

* **1065 Martin 2014, expenditures +198.00.** Four handwritten rows sum to 1,376.28 against the
  filer's own boxed 1,178.28. Arithmetic alone could NOT settle it — two different single-digit
  re-readings each close the page exactly (126.37 for the Acme row, or 2.00 for the SHEDZ row;
  the two differ by exactly the same 198.00), which is the correlated-error trap the calibration
  suite screens for. All four cells and the total box were escalated to **1200 dpi tight crops**
  and every one is unambiguous. The filer's sum is short of his own rows.
* **1087 Hilder 2014, expenditures −150.00.** 21 rows sum to 7,082.57 against a printed 7,232.57.
  Five 1000–1400 dpi escalations (the three largest amounts, the total box, a stray dated line)
  found every cell legible; the 10/10 Park Record cell in particular is a clear **499.00**, not
  the 649.00 that would have closed the page.
* **23015 Richardson 2024, expenditures +3.25.** 17 rows sum to 907.40 against a handwritten
  904.15; the shortfall equals one row exactly (Hugo Coffee $3.25, re-read at 900 dpi). Recorded
  as an observation, not a conclusion about intent. His cover's balance is computed from 904.15,
  so the error is carried through consistently.
* **1085 Coleman 2014 and 1087 Hilder 2014, contributions.** STRUCTURAL, not error: the module's
  stated total sums BOTH printed contribution boxes while the pre-2022 ledger itemizes only the
  **>$50** donors. Both ledgers reproduce their **>$50** box TO THE CENT ($3,910.18 and
  $9,200.00); the residuals (135.47, 225.00) are exactly the printed `<=$50` AGGREGATE, which the
  form does not require to be itemized. **Nothing is missing that the document contains.**
* **24390 Wolbach 2024 contributions and 24384 McKenna 2024 both sides — WITHHELD, see below.**
* **23014 Donaldson 2024 contributions — `none`.** The filing is 2 pages where every other 2024
  filing is 3: **there is no Itemized Contribution Report page**. Honest non-existence, and it
  corroborates the cover tranche's finding that this filer states no contribution total at all.

### ⚠ THE PERIOD-vs-CUMULATIVE GRAIN QUESTION — unresolved, and now much better evidenced

Summit's cover is **CUMULATIVE**. Some filers' LEDGERS are **PERIOD**-scoped. Publishing period
rows against a cumulative cycle total would state an incoherent pair, so those sides are
**WITHHELD with both figures named** — the state Phase A left the Harte-2026 filing in. This wave
found two more and, crucially, **evidence that settles the factual half of the question**:

* **24390 Wolbach Post-Election** prints, on ONE filing, a period-only contribution page (one row,
  14.72) AND a fully reconciled **cumulative** expense page — the same 20 pre-election rows, a
  printed `Pre-General Election Sub-Total = 1068.68`, the 2 post-election rows, a
  `Post-General Election Sub-Total = 14.72`, and a `Campaign Total = 1083.40` equal to the cover.
  The expense side therefore SHIPS at cumulative grain (22 rows, exact); the contribution side is
  withheld. **The county's form gives no cumulative contribution ledger.**
* **24384 McKenna Post-Election** is period-scoped on BOTH sides — and the period figures are
  provable from OUTSIDE the filing: **differencing the two covers reproduces them to the cent**
  (36,199.94 − 34,199.94 = 2,000.00 monetary contributions; 35,523.63 − 28,595.91 = 6,927.72
  expenditures). So the rows are RIGHT and the ledger is COMPLETE FOR ITS PERIOD; only the
  publication grain is undecided.

A withheld side's transcription is **not thrown away**: it is parked in the cache under
`_meta_itemized.withheld_rows` (5 + 9 rows on 24384) so the owner's eventual ruling can be applied
without re-reading a page. Parked rows are **not** data this module publishes, and
`build_finance.py` refuses to emit rows for any side that is not `transcribed`.

### Source properties this wave established (each proved on the page)

1. **The blank form's PRINTED SPECIMEN ROWS are not transactions** — `Jon and Jane Doe` $435.00 on
   the contribution sheet, `Name of Business` $512.00 on the expense sheet. Several filers left
   them in place; **the printed total closes only when they are excluded**, which is the proof.
   Three filers make it explicit: Brock (1081) HIGHLIGHTED both in yellow, Hilder (1087) STRUCK
   both amounts through in pen, and Jones's copy (1088) dates the specimen `8/25/10` on a 2014 form.
2. **Page position is not a classifier.** On 1059, 23013 and 24377 the expense page is **page 2**
   and the contribution page **page 3**. Every page is read and classified, never assumed.
3. **Ledgers carry non-donations.** Robinson 2014 (1080) opens his contribution ledger with a
   `Beginning Balance Brought Forward from 2012 House District 54 Campaign` of $611.38, counted in
   the ledger's own total; it ships as a row typed `carryover` and flagged, because dropping it
   would break the filing's arithmetic.
4. **In-kind exists and is totalled separately** (24384: three rows marked `IN KIND` in bold under
   a `NO CHANGE` marker meaning the block carries forward unchanged — summing it with the period
   monetary total would double-count).
5. **Filers date badly and it is never repaired**: `8//2014` (no day), `2024` (year only),
   `3/25` and `3/26` (no year), and one cell that literally reads the filer's placeholder
   **`Need Date`**. All BLANK + `needs_review=1` with the verbatim in the row note.
6. **Handwritten corrections over the typed grid govern.** On Smith 2024 (24239/24388) the
   template's typed `$ 0.00` totals are struck through and `501 55` written beside them in pen
   (superscript cents), initialled; the handwritten figures are transcribed and they agree with
   the cover — the SLCo clerk-correction precedent.
7. **Cross-leg mirroring is common and is a useful check**: Williams 2014 records five
   self-reimbursements that match five expense rows to the cent; Jones's $371.50 party
   contribution matches a $371.50 Park Record ad.
8. **p2 is sometimes a blank sheet** (1087) — bleed-through only, bound into the scan.

### Privacy in this layer

`donor_city` / `donor_state` only, applied **at read time** — a street or PO box is never written
to a record. Where the form prints a street and a ZIP but **no city** (Williams 2014), the
geography is honestly BLANK: a city is never inferred from a zip. The parser-era PRIVACY GUARD is
deliberately **not** applied to vision rows (it has nothing to fix, and its numeric boundary
marker truncated a legitimate name containing a year the one time it ran).

---

## The SCAN itemization wave — QUEUE CLOSED 2026-08-17 (TRANCHE 3 Phase B, resumed)

The wave the owner paused on 2026-08-14 for usage pacing was resumed on 2026-08-17 with owner
approval and **finished**: **all 116 scanned filings now carry an itemized layer**, so with the
15 born-digital filings **131 of 131 Summit county-office filings are itemized**. Nothing in the
queue remains — `python3 _backups/2026-08-14-tranche3/summit-b/wave_stats.py --residue` prints
nothing, which is the only claim of completeness this module makes.

**Configuration:** unchanged from the 2026-08-14 pre-flight (`claude-opus-5`, Read-tool vision,
`$0` API), so the calibration suite was **not** re-run — the recorded pre-flight for this
configuration is `_audits/cf-calibration-suite/runs.md` §2026-08-14, **13/13 PASS**. Fan-out this
run: **2 concurrent chunk agents** (one filing each), plus the coordinator's own audit pass.

### The state audit that had to come first (and what it found)

The 2026-08-14 pause killed two legs mid-flight. They left **114 staged record files** and **92
`vision/` caches already stamped `_meta_itemized`**, of which only leg 1's **24** had ever been
verified. **All 114 were treated as UNTRUSTED and re-screened from scratch**, because a cache is
only as good as the record the sole-writer path can reproduce it from:

1. Every modified cache was diffed against its last committed state and the **cover half was
   proved byte-unchanged on all 92** — the cover tranche was never touched by the killed legs.
2. The caches' itemized half was then **discarded entirely** and rebuilt from the records by
   `make_itemized_caches.py` — the module's only writer of that half — so no published row
   survives that a record does not generate.
3. Every record was run through `checkrec.py` (key ↔ `sha1(index_path)`, cover cache exists, side
   states legal, a withheld side names a reason, **every row resolves to real geometry on the
   page**, amounts parse, dates ISO-or-blank-with-`needs_review`, and the rows' own sum against
   the record's claimed `recon.itemized`).
4. Then the arithmetic/append-only invariants: `checkpoint.py` (born-digital block unchanged,
   `cover_totals.csv` byte-identical, 11 frozen columns held, changed `filing_totals` rows ==
   exactly the itemized set, no filing shrinks against the high-water mark) and
   `validate_finance.py`.
5. Independently, **8 untrusted filings were re-verified at the page**: a stored row's `pct:`
   geometry was resolved to a crop with `make_snippet.py` and re-read blind. **8 of 8 reproduced
   their donor and amount** (1246, 24232, 27197, 11859, 8205, 1093, 20640 exactly; 20762's crop
   showed the *documented* one-row print offset described in that filing's own record, not a
   defect).

**Result: 114 KEPT, 0 REDONE.** The killed legs' work passed every gate, and their records are
unusually well evidenced — several carry page-gate narratives that name two independent arithmetic
closures per side. **Two filings had never been started** (`4020` / `4278`, the Tal Adair 2016
pair — the corpus's last two, both `text_quality=low` handwritten sheets); they were transcribed
this run and close the queue.

### Measured (regenerate with `wave_stats.py`; the money from the CSVs)

| | |
|---|---:|
| scanned filings itemized | **116 of 116 — QUEUE CLOSED** |
| still queued | **0** |
| by cycle | 2014 **29** · 2016 **10** · 2018 **16** · 2020 **12** · 2022 **19** · 2024 **19** · 2026 **11** |
| rows published (vision tier) | **1,170 contributions · 1,349 expenditures = 2,519** |
| money in those rows | **$366,556.60 monetary contributions + $20,009.33 in-kind (42 rows) · $378,747.92 spent** |
| rows carrying `geometry` | **2,519 of 2,519 (100%)** — 1,607 `measured`, 912 `declared` |
| sides transcribed | **196** (97 contributions · 99 expenditures) |
| sides EXACT-reconciled | **165** |
| sides with a documented delta | **29** |
| sides with no gate available | **2** (Francis 2018 `8196` / `8359`: the schedule page exists and is BLANK and the cover states no contribution total, so no printed figure exists to gate against) |
| sides `none` (no such page in the document) | **15**, across 8 filings |
| sides WITHHELD | **21**, across 11 filings — **20 on the owner-gated grain question, 1 on a scanner defect** |
| rows parked under `_meta_itemized.withheld_rows` | **95** |
| tight-crop escalations used | **216** (600–2000 dpi cell crops) |
| filings with a page-gate record | **116 of 116** |
| rows flagged `needs_review=1` | 250 (overwhelmingly dates the form prints without a year, or at all) |
| per-row confidence | **2,460 `medium` · 59 `low`** (SCHEMA §6 caps a page image at medium; `low` marks a genuinely doubtful cell) |

### The deltas — what a `reconciles_*=False` actually means here

**32 side-flags read `reconciles_*=False`** (16 contribution, 16 expenditure). **29** of them carry
a transcriber verdict of `delta`; the other **3** (`1092` and `20758` contributions, `4020`
contributions) carry a verdict of `exact` — their ledger closes on the page's own printed box to
the cent and the difference against the module's stated total is structural or an in-kind modeling
artifact, both described below. A `False` on a vision row is **never** a transcription defect
claim. Three distinct causes, each named in the filing's `recon.detail` and in
`filing_totals.notes`:

* **STRUCTURAL — the module's stated total and the ledger count different things** (7 sides). On
  the pre-2022 `split50` sheet the ledger itemizes only donors **>$50** while
  `stated_total_contributions` sums both printed boxes, so the residual is exactly the printed
  `<=$50` AGGREGATE (1085, 1087, 4013, 4019, 4305, 8192, 27204). **Nothing is missing that the
  document contains.**
* **THE IN-KIND MODELING ARTIFACT** — `build_finance.py` excludes in-kind from
  `itemized_contrib_sum`, but on several filers' sheets the in-kind money sits **inside** the
  schedule's printed total and inside the cover figure (below). Where that happens the ledger
  closes on the page to the cent while the published sum sits under the stated total by exactly
  the in-kind amount (4020 by 270.00 and 20758 by 500.00, both verdicted `exact`; 24234 / 24708 by
  2,780.20, verdicted `delta` because a filer-arithmetic component rides along with it).
* **FILER ARITHMETIC, retained verbatim** (the rest) — the filer's own boxed total does not equal
  his own rows. Every one was screened for the correlated-error trap first: the largest and the
  most easily-misread cells were escalated to 900–2000 dpi tight crops, and in no case did a
  legible alternative reading close the page. Examples: 1065 (+198.00, four cells at 1200 dpi),
  1087 (−150.00, five escalations), 1082 **and** 1246 (+40.00 on BOTH of the same filer's filings
  — the strongest possible evidence of filer arithmetic over misread), 20758 (+0.17 with the
  current-period half closing exactly), 4278 (+0.30), 23015 (+3.25 = one row exactly).
  Two document-internal contradictions are recorded as such, not resolved: **1093** (the schedule
  and the cover state different contribution totals) and **1267** (a Post-Election filing that
  attaches the form's BLANK expense schedule while its cover restates $1,178.28 — the itemization
  of that identical figure exists on the same filer's Pre-Election sibling 1065, and is **not**
  copied across).

### The `none` and blank-page sides — different facts, kept different

**`none` = the document has no such schedule page** (15 sides over 4279, 3806, 8397, 12947, 11860,
12941, 20760, and 23014's contribution side). **A page that exists and is blank ships as
`transcribed` with zero rows** — a real zero, e.g. 12943's ruled-but-empty contribution sheet.
Neither is ever written as "no donors" and neither is imputed from the other.

### ⚠ THE PERIOD-vs-CUMULATIVE GRAIN QUESTION — RESOLVED 2026-08-17 (owner ruling; see the
### last section of this file). The account below is the wave's evidence, retained as filed;
### 16 of the 21 withheld sides were published on the period basis the same day.

Summit's COVER is cumulative; a substantial minority of filers' LEDGERS are PERIOD-scoped.
Publishing period rows against a cumulative cycle total would state an incoherent pair, so those
sides are **WITHHELD with both figures named and no sum claimed**, and their rows are **parked**
in `_meta_itemized.withheld_rows` so a ruling can be applied without re-reading a page.

**The wave's finding is that this is a corpus-wide property, not a handful of oddities: 20
withheld sides across 10 filings spanning EVERY cycle from 2014 to 2026** — 1264 Brickey, 1265
Hilder, 1268 Yost, 1274 Wharton (2014), **4278 Adair (2016)**, 11861 + 12943 Stevens, 12944
Francis (2020), 24384 McKenna + 24390 Wolbach (2024), 27451 Kucera (2026). In most of them the
period reading is provable **from the page's own printed section total**, which equals the cover's
**Current Report** cell rather than its Cumulative one; on 24384 it is provable from **outside**
the filing, by differencing the two covers to the cent; on 4278 both sides' printed boxes (13,697
and 17,642.44) are exactly the cover's Current Report column while its Last Report column
reproduces the sibling 4020's cover. A filing can be cumulative on one side and period on the
other (24390 Wolbach). **The county's form gives no cumulative contribution ledger**, which is why
this cannot be resolved by reading harder.

**One withheld side is NOT a grain case and must not be swept in with them:** **1250 Trussell
2014 contributions — the AMOUNT COLUMN IS NOT ON THE SCAN.** The landscape sheet was fed through
the scanner in portrait, cropping the right ~23% of the page (Zipcode and Amount) clean off the
image. That is a **scanner defect**, not a redaction and not a filer omission — the same sheet is
complete on filing 1058 — and the columns could not be assigned, so the side is withheld under
gate 5 rather than guessed.

### Source properties this leg established (each proved on a page, additive to the eight from leg 1)

1. **⚠ IN-KIND TREATMENT IS PER-FILER, NOT A FORM PROPERTY — this NARROWS the leg-1 McKenna
   precedent.** Leg 1 established (twice, on the 2024 McKenna pair) that in-kind is a separate
   schedule with its own total and the cover's contribution figure is MONETARY-ONLY. This leg
   found the opposite convention on the page repeatedly: on 4020, 4278, 8191 (2018 split50),
   1268, 11110, 20758 and 24234/24708 the in-kind money is entered **inline in the contribution
   schedule and counted INSIDE its printed total and inside the cover figure**. The operative
   rule is therefore: **whether in-kind sits inside or outside the stated total must be settled by
   each filing's own arithmetic, never assumed from the cycle or the form family.**
2. **The `<=$50` aggregate is sometimes itemized after all** — on a second sheet (1082),
   interleaved with the `>$50` rows on one sheet (1098), or as anonymised `$50 or less donor`
   lines (1244). The split50 structural rule holds only where the filer left the box aggregated.
3. **Pages arrive rotated and transposed.** 20641 has both ledger pages scanned 90° rotated and
   26742 carries `/Rotate 270` on every page; the materializer resolves such a row's geometry from
   the page's own VERTICAL rules behind an explicit per-side `"transposed": true`, so the box is
   still MEASURED and never fabricated.
4. **A filer's ink can be systematically out of phase with the row it belongs to** — 20762 prints
   its right-hand columns about one row HIGH, 20639's handwritten names run one line LOW. Both
   were settled by counting columns and by a second arithmetic gate, never by eye; this is exactly
   the field-shift class gate 5 exists for.
5. **Post-Election filings that re-submit the Pre-Election schedule pages verbatim** are common
   (20751, 12941 is the same physical sheet re-submitted) and are the source's behaviour, not a
   duplication bug.
6. **Variable-height rows defeat a uniform declared frame** (1249) — a single `y0 + pitch` cannot
   contain rows of 1 to 4 text lines; those rows ship on measured bands or not at all.
7. **A narrative letter can be a complete ledger** (1273 Ure), and **a filer can replace the
   county's table entirely** with his own spreadsheet (1245, 1249, 20762, 20634 — whose expense
   tab still carries its stale 2020 title).
8. **The 2026 sheet has no Zip column and its Address column holds only city and state** (27197) —
   precedent for the whole 2026 cycle.
9. **Two vocabulary variances exist in the records and the side state is authoritative**: a
   withheld or `none` side's `recon.result` reads `withheld`/`none` on some records and `unknown`
   on others (the AGENT_BRIEF record shape documents only `exact|delta|unknown`). Read
   `_meta_itemized.sides`, never `recon.result`, to decide what a side is.

### Privacy in this layer (unchanged)

`donor_city` / `donor_state` only, applied **at read time** — a street or PO box is never written
into a record, not even in a note. Where the form prints an address but no city (or the county's
black marker removed it), the geography is honestly BLANK, and the record's note distinguishes
*redacted by the county* from *left empty by the filer*. On the 2024/2026 sheets, which print
`Mailing Address` + `Zip Code` and no city column, city/state are blank on every row — a city is
never inferred from a zip.

## THE RECONCILIATION-BASIS RULING — owner-ratified 2026-08-17, APPLIED

The grain question the wave documented above is **decided**. The owner's ruling, verbatim in
substance:

> Reconcile each itemized side against the printed cover figure that **MATCHES ITS OWN SCOPE** —
> the cover's **CURRENT REPORT** column for a period-scoped ledger, the **CUMULATIVE** column for a
> cumulative ledger. Tag published rows with `is_incremental` accordingly. **NEVER synthesize a
> figure by differencing covers.** Withhold only where **NEITHER** printed figure closes.

**What that changes, and what it deliberately does not.** `stated_total_*` in this module is
unchanged — still the CUMULATIVE cover figure, still the only per-filing total to quote. What
changes is the figure a PERIOD-scoped ledger is reconciled AGAINST: the same cover's own printed
**Current Report** cell, which the form prints natively, so nothing is inferred and no two covers
are ever differenced. `build_finance.py` gained `promote_current()` (the period sibling of
`promote()`, split50 handled the same way — the sum of only the lines actually printed) and a
period-basis promotion inside `itemize_vision()`. **No previously published value changed**; the
only diffs are new rows and the reconciliation columns of the filings that gained them.

**The gate did not move.** A side promotes only if its parked rows sum **EXACTLY** to the printed
period figure ($0.01 test, no slack). **Both in-kind conventions are tried** — monetary-only, and
monetary-plus-in-kind — because this wave established that in-kind treatment is PER-FILER, not a
form property; whichever closes exactly is recorded and named in `filing_totals.notes`. A side
with a **blank amount** on any parked row cannot promote (its sum is not the ledger's sum), and a
side with **no parked rows** is not promoted either — a reconciliation over zero rows publishes no
data and asserts what no published row supports.

### Measured (2026-08-17, after the ruling)

| | |
|---|---:|
| withheld sides before the ruling | **21**, across 11 filings |
| **PROMOTED on the period basis** | **16 sides**, across **9 filings** |
| still withheld | **5 sides**, across **5 filings** |
| rows published by the promotion | **23 contributions · 58 expenditures = 81** |
| money those rows carry | **$10,112.61 monetary + $18,064.43 in-kind contributions · $26,229.77 spent** |
| in-kind convention that closed | **monetary-only 13 sides · monetary + in-kind 3 sides** (1264 both sides, 4278 contributions) |
| vision tier after the ruling | **1,193 contributions · 1,407 expenditures = 2,600 rows**, all carrying `geometry` |
| vision-tier money | **$376,669.21 monetary + $38,073.76 in-kind contributions · $404,977.69 spent** |
| sides published from the scans | **212** (196 transcribed + 16 period-promoted); **181 EXACT-reconciled**, 29 delta, 2 with no printed gate |

### The 16 promoted sides (period figure → the cumulative total that remains `stated_total_*`)

| filing | filer / cycle | side | rows | period figure (cover **Current Report**) | cumulative `stated_total_*` | in-kind convention |
|---|---|---|---:|---:|---:|---|
| 1264 | Brickey 2014 Post | contributions | 1 | 1,200.00 | 16,800.00 | monetary + in-kind (1,200.00) |
| 1264 | Brickey 2014 Post | expenditures | 9 | 3,226.18 | 15,540.12 | monetary + in-kind (1,200.00) |
| 1265 | Hilder 2014 Post | contributions | 3 | 700.00 | 10,125.00 | monetary-only |
| 1265 | Hilder 2014 Post | expenditures | 6 | 2,651.07 | 9,888.64 | monetary-only |
| 1268 | Yost 2014 Post | expenditures | 8 | 4,332.75 | 11,642.49 | monetary-only |
| 1274 | Wharton 2014 Post | contributions | 2 | 2,250.00 | 4,515.00 | monetary-only |
| 1274 | Wharton 2014 Post | expenditures | 2 | 2,726.00 | 3,756.93 | monetary-only |
| 4278 | Adair 2016 Post | contributions | 4 | 13,697.00 | 22,427.00 | monetary + in-kind (12,697.00) |
| 11861 | Stevens 2020 Pre | contributions | 2 | 389.00 | 10,157.17 | monetary-only |
| 11861 | Stevens 2020 Pre | expenditures | 2 | 389.00 | 9,217.72 | monetary-only |
| 12943 | Stevens 2020 Post | expenditures | 4 | 424.80 | 9,642.52 | monetary-only |
| 24384 | McKenna 2024 Post | contributions | 5 | 2,000.00 | 36,199.94 | monetary-only (4,167.43 in-kind ships EXCLUDED from the sum) |
| 24384 | McKenna 2024 Post | expenditures | 9 | 6,927.72 | 35,523.63 | monetary-only |
| 24390 | Wolbach 2024 Post | contributions | 1 | 14.72 | 1,083.40 | monetary-only |
| 27451 | Kucera 2026 Final | contributions | 5 | 3,758.89 | 14,039.72 | monetary-only |
| 27451 | Kucera 2026 Final | expenditures | 18 | 5,552.25 | 13,160.87 | monetary-only |

Every promoted row carries **`is_incremental=True`** — the only rows in this module that are not
cumulative-snapshot rows — and every promoted side's `filing_totals.notes` opens with
`ITEMIZED <side> PERIOD-SCOPED (is_incremental=True)`, names both figures, states the basis and
says in as many words that **the sum is one reporting period and is not a cycle total**.

### The 5 sides that stayed withheld (correct outcomes, not failures)

* **1250 Trussell 2014 contributions** — the AMOUNT COLUMN IS NOT ON THE SCAN (the scanner defect
  described above). The parked rows have no amounts, so no sum of any scope can close.
* **1268 Yost 2014 contributions** — neither printed figure closes. The cover's Current cells read
  `>$50 1,700.00` + `<=$50 75.00` = 1,775.00, while the schedule's own boxes read 1,700.00 / 25.00
  and its rows sum to 525.00 monetary (1,725.00 with the 1,200.00 in-kind). The filer's cover and
  schedule disagree with each other on the `<=$50` line; the side is not forced.
* **4278 Adair 2016 expenditures** — the 10 rows sum to 17,642.74 against the printed period box
  17,642.44, a **+0.30** filer/transcription delta (every amount already escalated). Exact means
  exact.
* **12943 Stevens 2020 contributions** — the page exists, is blank, and prints `Total
  Contributions: $0`, which is the cover's period figure. Nothing is parked, so there is nothing
  to publish; the period-zero fact stays in the withheld reason rather than becoming a
  zero-row "reconciliation".
* **12944 Francis 2020 expenditures** — the expense page is blank and the cover's **Current
  Report** cell is EMPTY (597.80 sits only in Last/Cumulative). With no printed period figure
  there is nothing to gate against.

### Wolbach 24390 — the one re-read this ruling required

The wave had recorded Wolbach's single period contribution ($14.72) **in prose inside the withheld
reason**, never as a structured row, so the ruling could not be applied to it from disk. Page 2
was re-read on 2026-08-17 (full page first, then a 1200 dpi tight crop of the Amount cell): the
single ruled row reads `11-1-2024 | Personal Contribution | 14 ⁷²`, the page prints **no total of
its own**, and 14.72 is the cover's Current Report contribution cell exactly. The row was parked
through the sole-writer path (`make_itemized_caches.py`) with `pct:` geometry from a **validated
declared frame** — the page's vertical rules stop at the Name/Amount boundary, so a measured box
would have cropped the Amount column off the crop it exists to point at. The ruling then promoted
it. `geometry_fit='declared'`, and the box reproduces donor + amount when rendered.

### The shared validator's contract moved with the ruling

`scripts/campaign_finance/validate_finance.py` check 6 asserted `reconciles_*=True ⇒ itemized_sum
≈ stated_total_*`, which a period-basis reconciliation cannot satisfy against a cumulative stated
total. The check now admits ONE **declared and evidenced** exception: every published row on the
side carries `is_incremental=True` **and** `filing_totals.notes` contains the literal marker
`ITEMIZED <side> PERIOD-SCOPED (is_incremental=True)`; then `recon_delta_*` (not the stated total)
carries the test. Absent that declaration the original test applies unchanged — re-run over all
38 campaign-finance modules on 2026-08-17: **every one still PASSes, none newly relaxed**
(summit_county is the only dataset that opts in).

### Rebuild / re-verify

```
python3 make_itemized_caches.py ../../_backups/2026-08-14-tranche3/summit-b/records   # sole writer
python3 build_finance.py                                                              # idempotent
python3 ../../_backups/2026-08-14-tranche3/summit-b/checkpoint.py                     # append-only
python3 ../../scripts/campaign_finance/validate_finance.py .                          # -> PASS
python3 ../../scripts/validate_entity.py summit_county                                # -> 12 PASS / 3 WARN / 0 FAIL
```
Verified 2026-08-17: two consecutive `build_finance.py` runs are byte-identical; `cover_totals.csv`
is byte-identical to its pre-ruling bytes; the contribution/expenditure diffs are **additions
only** (23 / 58 rows, zero deletions, zero modified rows); and no `stated_*` cell changed on any
of the 131 filings.
