# AVAILABILITY — Washington County county-office campaign finance

**As-of 2026-08-01.** Sources checked, what each held, and what is honestly missing.
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
7. **The money layer: STATED TOTALS for all 206 filings + a BORN-DIGITAL ITEMIZED LAYER for
   43 of them (2026-08-02).** `filing_totals.csv` carries what each filing's cover/summary
   PRINTED as its totals. `contributions.csv` (**181 rows**) / `expenditures.csv` (**308
   rows**) carry the itemised ledgers of the born-digital 2010–2015 file-sets, parsed by the
   registered `washco_split` family and **reconciliation-gated**: 15 contribution sides and 39
   expenditure sides summed EXACTLY to the filing's own stated total and shipped; every other
   side emitted **nothing** with a stated reason. 100% of emitted rows carry `geometry` (real
   `Sheet1!F5` cell references on the `.xls` generations). **0 of 206 `stated_*` values
   changed.**
   The remaining gap is real and now measured: the **100 HANDWRITTEN cover forms** are still
   unitemized (Phase B / vision work), the **4 ledger-only 2008 postings emit no rows by
   design** (they print no totals to reconcile against), and most born-digital sides are
   withheld because the Summary states a PER-PERIOD increment while the ledger restates the
   WHOLE CYCLE TO DATE — different quantities, and reconciling them would be our arithmetic,
   not the county's (`CLAUDE.md` "The BORN-DIGITAL itemized layer"). An empty itemized side
   still means *not transcribed / not reconcilable*, never *no donors*.

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
