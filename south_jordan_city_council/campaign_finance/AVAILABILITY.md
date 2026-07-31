# Campaign finance / financial disclosures — availability & sources

**As-of:** 2026-07-06 · **City:** South Jordan City, Salt Lake County, Utah
**Scope:** municipal candidate campaign-finance disclosure reports, Mayor + City Council
(5 single-member districts), general-election cycles.
**Status:** **ACQUISITION ONLY** — raw filing PDFs + `index.csv` retrieved and retained.
The structured contribution/expenditure extraction layer (OCR/vision → `contributions.csv`
/ `expenditures.csv` / `cycle_totals.csv`) is a **deferred later step** (see CLAUDE.md).

**Result:** **PARTIAL-but-strong.** 46 filing PDFs across **four general cycles
(2019, 2021, 2023, 2025)** for **every general-election candidate in those cycles** (14
distinct candidates; 100% join to `election_results/south_jordan_races.csv`). Pre-2019
campaign-finance filings were **not located online** (see below).

## Where South Jordan campaign-finance filings actually live (verified)

South Jordan files campaign-finance disclosures with the **City Recorder** (Utah Code
10-3-208 / South Jordan Municipal Code 1.12.050) and publishes them on the **city
Elections page** — but the hosting has migrated across two CMSes, so the filings are split
across three retrieval routes:

1. **Current CivicPlus/CivicEngage site — `/230/Elections`** (`https://www.sjc.utah.gov/230/Elections`).
   The **current cycle only** (2025) is displayed here, as per-candidate tables with a
   *"Financial Disclosure Reports"* column linking `DocumentCenter/View/<id>` PDFs
   (Pre-General 28 Day, Pre-General 7 Day, Post-General 30 Day). The page is **overwritten
   each cycle** — it no longer lists 2021/2023.
2. **Live `DocumentCenter` back-catalog.** Although the 2021 and 2023 filings are no longer
   *linked* from any live page, their `DocumentCenter/View/<id>` PDFs are **still served**
   (verified 200/application/pdf). The id→candidate→report mapping was **recovered from the
   Wayback Machine** (see route 3), then the bytes were fetched from the live host.
3. **Wayback Machine (first-class tool here).**
   - **2021 cycle** discovered in the 2022-03-20 capture of `/230/Elections`
     (`web.archive.org/web/20220320075413id_/…`) — "2021 Pre General" + "2021 Post General
     Campaign Financial Disclosure Reports" sections (DocumentCenter ids 357–364).
   - **2023 cycle** discovered in the 2023-12-03 capture (pre-general only) and completed
     from the 2024-06-09 capture (which added the Post-General reports).
   - **2019 cycle** lived on the **old WordPress site** at `/elections/`
     (`/wp-content/uploads/2019/10/<Name>-Pre-General-Post-General-Financial-Reports.pdf`),
     one combined pre+post PDF per candidate. Those URLs are **404 on the live CivicPlus
     site** and were retrieved from the Internet Archive (captures 2020-10-16/17).
   Archived-HTML captures used for discovery are retained under `raw/discovery/`.

`disclosures.utah.gov` (Lt. Governor) is the **state** disclosure system and does **not**
carry these municipal filings (it did not redirect to the city). Not a source here.

## What was searched, and the result of each source

| Source | Query / URL | Result |
|---|---|---|
| City Elections page (CivicPlus) | `/230/Elections` | **2025** filings (19 PDFs, 6 candidates) — live |
| City Elections sub-pages | `/342/Elections`, `/341/2021-Election-Information` | Only election *results*/canvass; **no** finance links |
| `…/elections/financial-disclosures/`, `…/campaign-finance-disclosures/` | direct guess | 404 (page not found) |
| Live DocumentCenter back-catalog | `DocumentCenter/View/357…364`, `5059…5341` | 2021 (8) + 2023 (15) PDFs still served |
| Wayback `/230/Elections` | captures 2022–2026 | recovered 2021 + 2023 id→candidate mapping |
| Wayback old WordPress `/elections/` | captures 2019–2020 | recovered 2019 filings (4 combined PDFs) |
| Wayback CDX (`wp-content/uploads/2019/10*`) | finance filter | 4 live archived 2019 PDFs (200) |
| `disclosures.utah.gov` | home + search | state system; no SJ municipal filings |

## Coverage by cycle (filings retrieved)

| Cycle | Seats up | Candidates w/ filings | Filings | Notes |
|---|---|---|---|---|
| **2019** | D1, D2, D4 | Harris, Marlor, Quinn, Zander (4) | 4 | one *combined* pre+post PDF each; Wayback |
| **2021** | Mayor, D3, D5 | Fonua, McGuire, Ramsey, Shelton (4) | 8 | Pre-General + Post-General each |
| **2023** | D1, D2, D4 | Harris, Bevans, Johnson, Zander (4) | 15 | 2 pre + 1 post each = 12, **plus 3 superseded** pre-general re-uploads (flagged) |
| **2025** | Mayor, D3, D5 | Barrett, Ramsey, Shelton, Lewis, McGuire, Hughes (6) | 19 | 28-day + 7-day pre + 30-day post each (Hughes also filed an amended 28-day) |
| **total** | | **14 distinct** | **46** | |

**Every filer joins to `election_results/south_jordan_races.csv`** (100%), and conversely
**every general-election candidate in 2019–2025 filed** — no candidate in those cycles is
missing a filing. Filer names normalize cleanly to the election records (e.g. finance
"Jason Timothy McGuire" = election `JASON TIMOTHY MCGUIRE`; "Dawn R. Ramsey" = `DAWN R
RAMSEY`).

## Honest gaps / caveats

- **Pre-2019 campaign finance NOT located** (2007–2017 cycles). The oldest online filings
  are 2019; earlier cycles predate the WordPress uploads that survive in Wayback. This is
  **beyond the repo's 2020 data floor**, so it is a note, not a required gap to fill —
  GRAMA to the City Recorder would be the only route. No fabrication.
- **No primary-cycle filings** — none of 2019/2021/2023/2025 South Jordan races triggered a
  municipal primary (consistent with `election_results`: ≤2 candidates per seat those
  cycles), so there are no pre-primary interim reports to find. **No election-record gap was
  surfaced** by the finance set (it corroborates the existing election record exactly).
- **Nearly all filings are SCANNED image PDFs** (42/46; only 4 carry a text layer). These
  are photographed/handwritten state disclosure forms — **OCR or vision is required** to
  extract contribution/expenditure line items. Deferred to the structured step.
- **3 superseded 2023 pre-general uploads** retained and flagged (`filing_type=interim`,
  `note=superseded upload…`): DocumentCenter ids **5135/5148/5149** (Bevans/Johnson/Zander)
  were the versions shown in the 2023-12 capture; the 2024-06 page replaced them with
  **5330/5329/5331**. Both the superseded and current uploads are retained so the structured
  step can decide; **do not sum them as separate filings** (double-count trap).
- **Filing dates are estimated by report class** (`date_precision=est_report_class`):
  pre-general → `<year>-10-15`, post-general → `<year>-12-01`. The verbatim report label is
  preserved in the `reporting_period` column. Exact statutory filing dates are inside the
  scanned forms and can be captured during OCR.
- **One stray broken link** on the live 2025 page: a 4th anchor in Dawn Ramsey's cell
  (`DocumentCenter/View/8613`, empty label) returns 404. It is **not a missing filing** —
  Ramsey's three real reports (8620/8621/8748) are all present.
