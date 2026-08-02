# Campaign-finance disclosures — availability, coverage & gaps

**As-of: 2026-08-01.** Wasatch County **COUNTY-OFFICE** candidate campaign-finance reports —
County Council, Clerk/Auditor, Sheriff, Attorney, Assessor, Recorder, Treasurer, Surveyor.

**Result: 111 filings across 6 even-year cycles (2010, 2018, 2020, 2022, 2024, 2026), 61
distinct candidate-cycles, 104 of them pulled from the county's / the state's own origin host.**
Channels probed and the reasoning behind every negative are in `RECON.md`; this file is the
coverage matrix and the gap ledger.

**Stated-totals coverage (added 2026-08-01): 111 / 111 filings transcribed** from the cover
page by vision, into `vision/<key>.json` → `filing_totals.csv`. Itemized donor/vendor rows are
NOT transcribed. See "Stated-totals coverage" below.

---

## Coverage matrix — filings by cycle × office

| office | 2010 | 2018 | 2020 | 2022 | 2024 | 2026 | total |
|---|---:|---:|---:|---:|---:|---:|---:|
| County Council | · | 3 | 16 | 7 | 12 | 15 | **53** |
| Clerk/Auditor | · | 1 | 7 | 2 | · | 4 | **14** |
| County Attorney | 2 | 4 | · | 2 | · | 4 | **12** |
| County Sheriff | · | · | · | 2 | · | 5 | **7** |
| County Assessor | · | · | 3 | · | 4 | · | **7** |
| County Surveyor | · | · | 5 | · | 2 | · | **7** |
| County Treasurer | 2 | · | 3 | · | 1 | · | **6** |
| County Recorder | · | · | 3 | · | 2 | · | **5** |
| **total filings** | **4** | **8** | **37** | **13** | **21** | **28** | **111** |
| distinct candidates | 4 | 8 | 14 | 7 | 13 | 15 | — |

`·` is a **true blank, and usually means the office was not on that year's ballot**, not that a
filing is missing — Utah county offices run on staggered 4-year terms, so (e.g.) Assessor,
Recorder, Surveyor and Treasurer appear in 2020 and 2024 but not 2022 or 2026, while Sheriff,
Attorney and Clerk/Auditor appear in 2022 and 2026. The one substantive `·` is **2010**, where
only 4 filings survive on the state site at all.

### Reports per candidate, by cycle

| cycle | filing points published | typical reports/candidate |
|---|---|---|
| 2010 | one pre-primary report | 1 |
| 2018 | one report per candidate as posted | 1 |
| **2020** | **June (7 days pre-primary) / October (7 days pre-general) / December (30 days post-general)** | **3** — the deepest cycle |
| 2022 | Primary/June + General | 1–2 |
| 2024 | June (pre-primary) + General (Sept 30 / Oct 29) | 1–3 |
| 2026 | March (partisan convention) + June (primary / elimination) | 1–2 (cycle still open) |

**2026 is an OPEN cycle.** The general (due 2026-10-28) and final (due 2026-12-03) reports do
not exist yet. This module will be materially incomplete for 2026 until a refresh after
December 2026.

---

## Where each cycle came from

| cycle | channel | host | notes |
|---|---|---|---|
| **2026** (28) | live CivicPlus DocumentCenter | `wasatchcounty.gov/DocumentCenter/View/<id>/…` | listed on the live elections hub; needs an archive-browser UA (CivicPlus 403s bare fetchers) |
| **2024** (21) | 13 June + 1 state copy from **live origin**; 7 general from **Wayback** | `wasatch.utah.gov/Portals/…/2024 Election/DisclosureNotices/`, `disclosures.utah.gov`, `web.archive.org` | the general reports lived only on the retired Jadu CMS — 5 of 12 are unrecoverable (below) |
| **2022** (13) | **live origin** (DNN) | `wasatch.utah.gov/Portals/…/2022 Election/Financial/` | link list recovered from TWO Wayback captures of the clerk page (Oct = primary links, Dec = general links) |
| **2020** (37) | **live origin** (DNN) | `wasatch.utah.gov/Portals/…/2020 Election/Financial/` | the county's 2020 clerk page listed every candidate WITH office headings — the office map is authoritative |
| **2018** (8) | **live origin** (DNN) | `wasatch.utah.gov/Portals/…/2018Elections/DC/` | office assignments taken from the Declaration-of-Candidacy filenames on the same county page |
| **2010** (4) | Lt. Governor disclosures site | `municipal.utah.gov/wasatch\2010 Primary\…` | 4 county + 6 school board in one folder; split by form header |

**The DNN host `wasatch.utah.gov` is still live and still serves its PDFs** even though its
*pages* now redirect to the CivicPlus site. That is why this module's provenance is unusually
strong (104/111 origin-fetched) — but it is also a standing risk: if that host is finally
retired, 2018–2024-June becomes Wayback-only. `refetch.py` exists to detect that early.

---

## Stated-totals coverage (2026-08-01 vision tranche)

Every one of the **111** cover pages was rendered (`pdftoppm -jpeg -r 200`, page 1) and read
with the Read tool — **$0 API, Claude Code allotment** (`/cf-vision-transcribe` method). Method
by form variant:

| variant | cycles | filings | transcription route | of which the born-digital text layer independently corroborates ≥1 figure |
|---|---|---:|---|---:|
| `carr_5_5_pg_4line` (cumulative) | 2010, 2022 | 17 | vision | 6 |
| `wasatch_fcr_3line` (cumulative) | 2018, 2020 | 45 | vision | 7 |
| `wasatch_disclosure_tableab` (period) | 2024, 2026 | 49 | vision | 19 |
| **total** | | **111** | **111 vision / 0 text-only** | **32** |

**Why zero text-only.** 71 of the 111 PDFs carry a text layer, but on all but a handful that
layer is an OCR of *handwriting* (`A\c,., L0wue ff\cDoru\d` = "Alan Wayne McDonald"); only 4
PDFs have an AcroForm at all, and their values are handwritten too. So the totals were read by
vision on every filing, and the text sidecar is used only as an **automatic cross-check**: for
each filing, any transcribed figure **distinctive enough to be meaningful** (≥4 characters with
a decimal separator — a bare "0" matches any page by chance and proves nothing) that also
appears verbatim in `text/<year>/*.txt` is listed in the cache's
`_meta.text_layer_corroborated_lines`. **32 filings — essentially the genuinely typed ones —
corroborate at least one line that way, and none of the 32 disagreed.** On scans, on
handwriting, and on all-zero filings the list is empty, which is expected and not a defect.

**What came out:**

- `filing_totals.csv` — 111 rows. `filing_regime` = `cumulative` 62 / `period` 49.
- `extraction_confidence` — **103 high, 6 medium, 2 blank** (blank = the filing states no
  contribution and no expenditure total at all: Hewlett 2024-06 and Kahler 2026-03).
- **Blank stated totals: 4 contribution, 3 expenditure** — every one an honest property of the
  face, enumerated in `CLAUDE.md` "Cardinal-rule specifics".
- **Almost nothing itemized (2026-08-02).** The registered `wasatch_disclosure_tableab` family
  was run over the **49 Table A/B filings** and shipped **8 expenditure rows over 2 filings**
  (Murphy 2026-03, Forsyth 2026-06); **0 contribution rows**. `reconciles_*` is blank on the
  other 109 rows — *unknown*, never a fabricated match. The three reasons are itemised in
  `CLAUDE.md` "The born-digital itemized layer": garbled text layers the family refuses to
  turn into numbers, a **field-shift family limitation** that put the date in the name column
  on three filings (all withheld — the amounts summed exactly, so reconciliation could not
  catch it), and one multi-report PDF whose second report is gated out. 0 of 111 `stated_*`
  values changed.

### Finding: the form seam is the 2022→2024 CYCLE boundary, and `index.csv.form_family` is wrong on 6 rows

Reading all 111 covers replaced the earlier "two families, mid-2024 seam, 2024 mixed 4-old/
16-new" account with a clean three-variant, cycle-aligned split (table above). **All 21 of the
2024 filings are on the new Table A/B sheet.** The cause of the mislabel is documented and
reproducible: **the 2024 vintage of the NEW sheet still cites Utah Code 17-16-6.5** in its
anonymous-donation line (only from 2026 does it cite 17-70-4), so a statute-header classifier
files it as the old county form. Affected rows:

| `index.csv` path | `form_family` says | the page actually is |
|---|---|---|
| `raw/2024/202403_state_Adams.pdf` | `utah_county_fcr_formab` | `wasatch_disclosure_tableab` |
| `raw/2024/202406_BobAdams.pdf` | `utah_county_fcr_formab` | `wasatch_disclosure_tableab` |
| `raw/2024/202406_JamiSmithHewlett.pdf` | `utah_county_fcr_formab` | `wasatch_disclosure_tableab` |
| `raw/2024/202406_ToddGriffin.pdf` | `utah_county_fcr_formab` | `wasatch_disclosure_tableab` |
| `raw/2024/202406_ToriBroughton.pdf` | *(blank)* | `wasatch_disclosure_tableab` |
| `raw/2020/2020_OctJGranger.pdf` | *(blank)* | `wasatch_fcr_3line` |

`index.csv` is DERIVED from `build_index.py` and was **not** edited here — the classifier fix is
a follow-up for the coordinator. Until then, read the regime from `filing_totals.filing_regime`
or `vision/<key>.json._meta.form_variant_vision`, never from `form_family`.

### Evidence for the regimes (primary-document, not inference)

- **cumulative** — the sheet's own three-column box, `TOTALS FROM LAST REPORT + TOTALS FOR THIS
  REPORT = CUMULATIVE REPORT`; ground truth Granger 2022-11-01 ($0 / $0 / $450 / −$450), and
  the 2020 chains (Lee: 1,016.57 → 3,526.57 → 4,139.36 across June/October/December) behave
  exactly as cumulative snapshots.
- **period-scoped** — three filers state it on the face: **Woodard 2026-06** annotates lines 1
  and 2 *"since last report"*; **Forsyth 2026-06** prints *"(balance of $1,263.82 in campaign
  bank account from prior contributions previously reported)"*; **Bonner 2024-11** covers
  *"Sep 26 to Oct 24, 2024"* with $700.00 raised / $3,612.69 spent (RECON.md's example, matched).
- **but not uniformly** — Kaiserman 2024 (June and general both 653.00 / 653.00 / 0), Rowland
  2026 and Farrell 2026 (June repeats March exactly) use the period sheet as a cumulative
  restatement. Each such row says so in `filing_totals.notes`. **A per-candidate regime check
  therefore belongs in any future `cycle_totals` pass — do not sum a 2024/2026 candidate's
  filings blind.**

---

## Gaps — honest, enumerated

### 1. Five 2024 general reports: dead on every channel (`unrecovered.csv`)

| candidate | office | report |
|---|---|---|
| Kendall Crittenden | County Council Seat D | general |
| Tori E. Broughton | County Council Seat D | general |
| Mark B. Nelson | County Council Seat E | general |
| Amber Gibbs | County Treasurer | general |
| Bob Adams | County Assessor | 9-30-24 |

Their Jadu ids **404 at origin** and the Wayback availability API returns
`archived_snapshots: {}` for each. **No candidate is entirely absent** — every one has a June
filing, and Adams additionally has his 10-29-24 general report.

### 2. 2014 and 2016: no county-published campaign finance exists

Checked and empty on all three channels (2016 DNN clerk page carries no CF links; the DNN
`Elections/` tree has no 2014 folder and no 2016 `Financial` folder; the state site has no
`wasatch_2014`/`wasatch_2016` folder). **County publication of campaign finance appears to begin
with the 2018 cycle.** This is a *publication* gap — the filings existed as paper records with
the clerk; they were never posted. Only a GRAMA request could close it, and this repository does
not use request-based channels (PRIVACY.md).

### 3. 2012: a county-office ZERO that looks like a haul

`disclosures.utah.gov/Municipal/wasatch_2012 Primary` holds 6 filings and **all six are school
board** (`SCHOOL BOARD CANDIDATE` / 20A-11-1301 headers). County-office filings for 2012: none,
on any channel. Recorded in `out_of_scope.csv` so the negative is not re-litigated.

### 4. Pre-2010

The state site's `wasatch_2008` folder is empty; its `2008_School Board` subfolder is school
board only. The pre-2014 county host (`co.wasatch.ut.us`) published election pages but no
campaign-finance PDFs. **Nothing exists to acquire before 2010.**

### 5. 2026 is incomplete by calendar, not by defect

General and final reports are not yet due. Additionally, **Paul Moore** (unaffiliated candidate
for Sheriff, signature threshold met) appears on the 2026 declarations list with **no campaign-
finance filing published** — an honest absence on the county's own page as of 2026-08-01.

---

## School board — OUT OF SCOPE (recorded, not fetched)

This module covers **county offices only**, per the acquisition instruction. **32 school-board
filings were identified during the sweep and are catalogued in `out_of_scope.csv`** with
candidate, cycle, source URL and the evidence used to classify each:

| cycle | school-board filings identified | how classified |
|---|---|---|
| 2010 | 6 (Horner ×2, Jones ×2, Heywood ×2) | form header `SCHOOL BOARD CANDIDATE` / 20A-11-1301 |
| 2012 | 6 (Baird, Kelson, Jacobsmeyer, Davis, Sorenson, Cowley) | form header `SCHOOL BOARD CANDIDATE` / 20A-11-1301 |
| 2018 | 2 (Cory Holmes, Tyler Wilson Bluth) | form field *Name of Office* (Bluth read from the page image) |
| 2020 | 18 (Allen, Davis, Paulsen, Dickerson, Hansen, Koumarela × June/Oct/Dec) | the county's own 2020 candidate listing (`Local School Board …` headings) |
| 2022 | 4 (Holmes, Throndson, Bluth, Prewitt) | the county's 2022 clerk page (`Wasatch County School Board Seats` heading) |
| 2024 | 10 (Stone, Ehlert, Dickerson, Lund, Dedrickson, Allen) | the 2024 Jadu page (`Wasatch County School Board - Seat …` headings) |
| 2026 | 3 (Cieslewicz, Collett, Sabey) | the live elections page (`Wasatch County School Board Seat …` headings) |

**Note the trap this avoids:** school-board candidates file on the **same county form, addressed
to the same county clerk, in the same folder** as county-office candidates. Only the statutory
citation printed on the sheet (17-16-6.5 vs 20A-11-1301) or the *Name of Office* field
distinguishes them — the folder and the link text do not. A future school-board pass has
everything it needs in `out_of_scope.csv`.

State-legislative and State-Board-of-Education candidates who appear on the same county pages
(Kohler, Monahan, Winterton, Fellow, Miller, Moss, Rupard-Blunt, Favero, Taylor) file with the
**state**, not the county, and are outside this module entirely.

---

## Legal frame

County candidates file with the **county clerk** under **Utah Code 17-16-6.5** (the citation
printed on the older form; the newer Wasatch sheet cites 17-70-4 for anonymous-donation
disposition). School-board candidates file under **20A-11-1301 et seq.** Municipal candidates
file with their **city recorder** under 10-3-208 — which is why Heber City, Midway, Charleston,
Hideout, Daniel and Wallsburg filings sit in the Lt. Governor's odd-year folders and not here.
