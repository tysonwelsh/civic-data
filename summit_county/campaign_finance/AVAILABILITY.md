# Campaign-finance disclosures — availability & sources checked

**As-of 2026-08-01.** Summit County **COUNTY-OFFICE** candidate campaign financial reports
(Utah Code **17-16-6.5**, filed with the County Clerk): County Council, Attorney, Auditor,
Clerk, Sheriff, Assessor, Recorder/Surveyor, Treasurer — cycles **2014, 2016, 2018, 2020, 2022,
2024, 2026**.

**Result: COMPLETE against every channel that publishes this material.** **131 filings / 74
candidate-cycles**, and **every one of the 56 county candidates who appeared on a Summit ballot
2014–2026 — including all 38 general-election winners — has at least one report here.** The
channel survey behind these numbers is `RECON.md`; the per-filing record is `index.csv`.

**Money layer (2026-08-02): STATED TOTALS COMPLETE (131) + the BORN-DIGITAL ITEMIZED LAYER
(11 of 131).** All 131 cover pages were vision-transcribed and `filing_totals.csv` carries each
filing's printed contribution / expenditure / ending-balance figures — see "Stated totals"
below. The **15 born-digital filings** were then parsed by the registered `summit_form` family:
**105 contribution + 386 expenditure rows over 11 filings**, 4 contribution sides and 11
expenditure sides reconciling EXACTLY to the published stated total (100% `geometry` coverage;
0 of 131 `stated_*` values changed). **The 116 SCANS remain unitemized** — that is *not
transcribed*, never *no donors*, and it is Phase B (vision) work. What the gates refused —
Harte 2026's period-scoped ledger under a cumulative cover, and the wrapped-2014 sections — is
itemised in `CLAUDE.md`.

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
