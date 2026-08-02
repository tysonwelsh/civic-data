# RECON — Summit County COUNTY-OFFICE campaign finance (2026-08-01)

The channel survey that preceded acquisition. Written first, kept verbatim: it records what was
probed, what each channel actually served, and the two label traps that would otherwise have
produced a wrong dataset. Retrieval results are in `AVAILABILITY.md`; the per-filing record is
`index.csv`.

**Scope:** COUNTY offices only — County Council (6 seats), Attorney, Auditor, Clerk, Sheriff,
Assessor, Recorder/Surveyor, Treasurer. School-board and municipal (Coalville / Kamas / Oakley /
Francis / Henefer / Park City / South Summit Fire District) filings are **out of scope** and were
deliberately not retained; see the "leads" section of `AVAILABILITY.md`.

---

## 1. Legal frame (why the county, not the state, holds these)

Summit **county-office** candidates file under **Utah Code 17-16-6.5** — the report goes to the
**County Clerk**, and the Clerk publishes it. The state Lieutenant Governor's disclosure system
(`disclosures.utah.gov`) hosts **state** offices and a **/Municipal/** tree for city/town filings
(Utah Code 10-3-208); it holds **no county-office content for Summit** (verified below). School
board candidates file under **20A-11-1301..1305** — a different form, out of scope.

Consequence: the **county's own Financial Reports page is the only publisher** of this material,
and the depth of the dataset is the depth of that one page plus what its old URLs still serve.

## 2. Channels probed

| # | channel | probe | result |
|---|---|---|---|
| 1 | **County Financial Reports page** — `https://www.summitcountyutah.gov/536/Financial-Reports` | urllib + browser UA (CivicPlus/CivicEngage; GOTCHAS Akamai-403 rule) | **200, 181,985 bytes.** Six HTML tables: 2026, 2024, 2022, 2020 — each split County Offices / School Board / "State offices: see disclosures.utah.gov". **69 county-office PDF links.** Capture retained at `raw/index_pages/536_Financial-Reports_2026-08-01.html`. |
| 2 | **Wayback captures of that page** | CDX `summitcountyutah.gov/536*` | Only **3** captures, all **2025-01 or later** — no pre-2020 depth on the current hostname. |
| 3 | **Wayback captures of the PREDECESSOR host** — `co.summit.ut.us/536/Financial-Reports` | CDX `co.summit.ut.us/536*` | **9 captures 2015-03 → 2019-06.** These list the **2014, 2016 and 2018** cycles, which the live page dropped entirely. 5 captures retained under `raw/index_pages/`. |
| 4 | **Delisted-but-live-by-ID DocumentCenter** (GOTCHAS "CH pattern") | fetched the 2014/2016/2018 DocumentCenter IDs read off the Wayback listings against the **current** host | **62 of 63 still served live, 200 + `%PDF-`** with the original filename in `Content-Disposition`. The CMS never deleted them; only the listing dropped them. Preferred over Wayback bytes (original, not a replay). |
| 5 | **State LG disclosures — `disclosures.utah.gov/Municipal/summit*`** | full recursive folder walk, then every file fetched and its **form header + office line read** (see §3) | **34 folders, 165 files, 0 county-office filings.** Ledger: `state_sweep.csv`. |
| 6 | **State LG disclosures — county/state trees** | `/County/`, `/Municipal/summit_2020`, `/Municipal/summit_2022` | `/County/` **404**; `summit_2020` and `summit_2022` return *"Path … does not exist"* — the even-year county cycles have no state folder at all. |
| 7 | **PMN (Utah Public Notice)** | not used | Campaign-finance reports are not public-meeting notices; no PMN path exists for them. (The coordinator's PMN gotcha — a `keyword` param is silently ignored, so a keyword negative is not a negative — is noted for whoever probes it later.) |

## 3. Two label traps found (both would have produced a wrong dataset)

**Trap A — the state system's residence-town folders (coordinator warning, verified here).**
`/Municipal/<county>_<year>` sub-folders are named for the filer's **town**, not the jurisdiction
of the office, so a county filing can hide in a small-town folder. Every one of the 34 Summit
folders was walked and every one of the 164 fetchable files was opened. **158 of them are
image-only (pdftotext = 0 chars)** and had to be rendered (`pdftoppm -r 200`) and OCR'd before the
header was readable.

**Trap A-inverted — the form header alone is NOT a discriminator in Summit.** The coordinator's
rule ("county filings carry the *17-16-6.5* header") **fails here in the false-positive
direction**: **29** files in the state tree carry the county statute header, and **every one of
them names a CITY, TOWN or SPECIAL-DISTRICT office inside** — Coalville City Council, Mayor of
Coalville, Henefer town council, Oakley City Council, South Summit Fire District. Summit's Clerk
hands the *county* blank form to the small municipalities, so the letterhead follows the printer,
not the jurisdiction. **The reliable discriminator is the "Office Filed For" line inside the
form** (plus cycle parity: Summit county offices are elected in EVEN years only; every one of
those 29 sits in a 2017 or 2019 folder). The `summit_2008` folder — an even year, and therefore
the most suspicious — turned out to be **9 school-board reports filed under 20A-11-1301**. Result
recorded per folder in `state_sweep.csv`.

**Trap B — the county page's own listing lies about office.** Three separate cases, each resolved
from the **filing text**, never from the label:
- **Dawn Mathiesen Langston (2022)** is printed in the county table with no office prefix,
  directly under two `County Auditor:` rows. Her own filing says **`Office Filed For: Summit
  County Clerk`** (both reports) — she is the 2022 Clerk write-in, confirmed by the county canvass.
- **Michael Howard (2018)** has a stray duplicate anchor pointing at **Margaret Olson's** Final
  report; the page renders it inside his row. Dropped — his real Final is document 8399.
- **Colin DeFord (2016)** is listed surname-first with no comma ("Deford Colin"); corrected to
  natural order against the DocumentCenter filename and the 2016 canvass. Recorded as a
  `candidate_override` with evidence in `batch/manifest.json`.

## 4. Form family — and why NO structured money layer was built

Every Summit county filing 2014-2026 is the clerk's own **"CAMPAIGN FINANCIAL REPORT"** (Utah Code
17-16-6.5) — a cover box plus `ITEMIZED CONTRIBUTION REPORT` / itemized expenditure pages. It is
**not** any family the shared framework already knows. The task rule was: build the structured
layer only if `scripts/campaign_finance/` parses the family **without library modification**. It
does not. Measured, on `text/20765_Langston-Post-Election-2022.txt` (a clean born-digital filing
whose printed totals are contributions **$503.00** / expenditures **$511.62**):

| family tried | contrib rows | expend rows | stated_contrib | stated_expend |
|---|---|---|---|---|
| `millcreek_form` | 21 | 0 | **511.62 (WRONG — that is the expenditure total)** | None |
| `ogden_form` | 10 | 0 | **511.62 (WRONG)** | None |
| `westvalley_form`, `lehi_formab`, `southjordan_form`, `stgeorge_formab` | ~20 | 0 | None | None |
| `parkcity_form` | 9 | 11 | None | None |
| `utah_standard_form`, `provo_form`, `easyvote_schedab`, `taylorsville_form` | 0 | 0 | None | None |

Two structural reasons, both in the cover box:
1. **Column order is reversed vs Millcreek.** Summit prints `Current Report | Last Report |
   Cumulative Totals`; Millcreek prints `LAST | THIS | CUMULATIVE`. `millcreek_form` takes the
   second-to-last token as "this period" — on a Summit filing that is the **Last Report** column.
2. **The labels differ.** Summit prints `Total expenditures` and `Campaign balance`; the shared
   anchors are `Total campaign expenses` / `Balance at the end`, and the itemization headers are
   `ITEMIZED CONTRIBUTION REPORT`, not `FORM "A"` — so section tagging finds nothing and the
   expenditure side comes back empty on every family.

A silently-wrong total is worse than no total, so this dataset ships **raw + text + index only**,
with `needs_review` and `text_quality` carrying the honest signal. The shared-library change this
would need is described in `CLAUDE.md` → "Shared-script need".

## 5. Corpus condition (why a vision pass is queued)

Summit's filings are **handwritten forms, scanned**: 116 of 131 are `format=scanned`, only 15 are
born-digital. 69 of the scans carry a text layer the **clerk's scanner** produced (not this repo)
— that layer transcribes the *printed* form well and the *handwriting* badly. 47 scans had no text
layer at all and were OCR'd here. Measured against the filer's own surname and legible money
tokens: **89 high / 22 medium / 20 low**. The 20 `low` rows have no machine-readable numbers at
all — for those the raw PDF is the only source. This is the `cf-vision-transcribe` case.

## 6. Data floor

**2014.** The predecessor page's earliest capture (2015-03-03) already showed 2014 as its newest
cycle and listed nothing older; DocumentCenter IDs below ~1058 that the pre-2014 listings would
have used now 404 (probe: ID 681 → 404). The 2008/2010/2012 county cycles have **no published
campaign-finance reports on any channel** — the county canvass (`../elections/`) proves those
races happened; the money reports were never posted. That is an availability floor, not an
extraction gap.
