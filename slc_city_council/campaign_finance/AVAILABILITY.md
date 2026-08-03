# Salt Lake City — campaign-finance disclosures: availability & sourcing

**As-of: 2026-07-05; materially CORRECTED 2026-08-02** by an adversarial channel re-hunt —
full probe log in **`RECON_2026-08-02.md`**, which is authoritative where the two disagree.
Dataset scope: municipal candidates for **Salt Lake City Council (7 geographic districts) +
Mayor**, cycles **2019 / 2021 / 2023 / 2025** (see "Deeper availability" for what the portal
holds beyond this window).

This file records every host tried, the portal's real structure, and the honest gaps —
per the repo's cardinal rule that gaps are data.

> ## ⚠ 2026-08-02 CORRECTION — the "one real source / no PDFs ever" framing was WRONG
>
> Three claims below were falsified by re-probing. Read `RECON_2026-08-02.md` first.
>
> 1. **A PDF era EXISTS.** SLC's Recorder published per-candidate filings at
>    `slcgov.com/recorder/fin_disc/pdfs/<Name>.pdf`, indexed by
>    `recorder/fin_disc/feb_fin_disc.htm` ("February 15th 2003 Candidate Financial
>    Disclosures"). **8 recovered into `raw/recorder_2003/`** — Mayor (Rocky Anderson,
>    Pignanelli) + Council D1/D2/D4/D5/D6, each with **itemized donors and expenditures**.
> 2. **A PREDECESSOR SYSTEM covered 2003–2019.** `dotnet.slcgov.com/ManagementServices/
>    CandidateReporting/` (also the now-DNS-dead `apps1.slcgov.com`), an ASP.NET WebForms
>    app whose year dropdown lists **2003, 2005, 2007, 2009, 2011, 2013, 2015, 2017, 2019**.
>    So "no pre-portal filings online" was false as a statement about what SLC published;
>    what is true is that its result pages were **POST-only and were never archived**, and
>    the app is now **HTTP 500** (IIS virtual dir no longer registered as an application).
> 3. **The 503 page is not empty — it carries live data.** Every dynamic request under
>    `CampaignFinance_Public` returns a 35,503-byte "Under Construction" page that
>    **embeds a 38-row candidate/office/balance table ("Balance as of April 2026")** for the
>    open 2027 + 2029 SLC campaigns. Captured to `raw/portal_snapshot/`.
>
> **Also reframed:** the outage is **app-specific, not a dead server**. The sibling
> `Attorneys/CampaignFinance_Candidate/api/CampaignFinanceAPI/*` answers **401** (live
> ASP.NET), and the database is demonstrably alive (it renders the balance table). The
> blocker is a switched-off public read surface, not missing data — which makes this a
> GRAMA/records-request shape, not a scraping problem.
>
> **What survives unchanged:** for the **2019–2025 ITEMIZED** layer the live public API is
> still the only source. Independently re-confirmed negative for the state tree, Salt Lake
> County/EasyVote, and PMN (see RECON).

---

## The primary source for 2019+: SLC's own Campaign Finance Reporting System

Salt Lake City **self-hosts** its campaign-finance disclosures. Everything routes here:

- **Portal shell (Angular SPA):**
  `https://dotnet.slcgov.com/Attorneys/CampaignFinance_Public/#/Candidates/Contribution`
- **Landing page:** `https://dotnet.slcgov.com/Attorneys/CampaignFinance_Public/index.html`
  ("Welcome" — two tiles: public browse vs. candidate login). Maintained by the
  **City Recorder's Office** (451 S. State St, Room 415; elections@slcgov.com; 801-535-6225).
- **City page that points to it:** `https://www.slc.gov/attorney/campaign-finance/`
  (City Attorney / Recorder). Describes Personal Campaign Committees (PCC) under SLC Code
  §2.46; links out to the portal; **posts no PDFs of its own.**

### The portal has NO documents — it is a JSON database API

This is the key structural fact. The public site is an **Angular 5 / SystemJS SPA**
(`app/main.js`, `app/app.module.js`, services under `app/Services/`). It renders filings
from a **.NET WebAPI**, not from stored PDFs. There is no per-filing document to download;
a "filing" is a candidate's electronic disclosure for one election cycle, returned as JSON.

**WebAPI base:** `https://dotnet.slcgov.com/Attorneys/CampaignFinance_Public/api/CampaignFinanceAPI/`
(reverse-engineered from `app/Services/campaign-finance.service.js`). GET endpoints:

| Endpoint | Params | Returns |
|---|---|---|
| `GetElections` | — | election cycles (ElectionId, ElectionYear, CycleStart/EndDate, periods) |
| `GetCandidatesByElection` | `pElectionId` | candidates (CandidateId, name, OfficeType, District, Status, Total\*, EndingBalance) |
| `GetPeriodsByElection` | `pElectionId` | reporting periods (interim vs. summary filing windows) |
| `GetElectionSummaryByCandidate` | `pElectionId,pCandidateId` | a candidate's disclosure summary |
| `GetFinancialInfo` | `pElectionId,pCandidateId,pThruDate` | running financial totals |
| `GetContributionsByElectionCandidate` | `pElectionId,pCandidateId,pThruDate` | itemized contributions |
| `GetExpendituresByElectionCandidate` | `pElectionId,pCandidateId,pThruDate` | itemized expenditures |
| `GetContributionsByPeriodCandidate` | `pPeriodId,pCandidateId` | per-period contributions |
| `GetExpendituresByPeriodCandidate` | `pPeriodId,pCandidateId` | per-period expenditures |
| `GetContributionsByContributor` / `GetContributorsByNameSearch` / `…ByStartingIndex` | contributor-side lookups |
| `GetSevenDayContributions` / `GetSevenDayTotals` | pre-election 7-day reports |

**Ten further endpoints recovered 2026-08-02** by re-reading the live service layer — the
2026-07-05 map was incomplete. Add these to any future harvest:

| Endpoint | Params |
|---|---|
| `GetElectionReportNames` | — |
| `GetComplianceByElection` | `pElectionId` |
| `GetComplianceByElectionCandidate` | `pElectionId,pCandidateId` |
| `GetContributionCountByElectionCandidate` | `pElectionId,pCandidateId,pThruDate` |
| `GetContributionListByElectionCandidate` | `pElectionId,pCandidateId` |
| `GetExpenditureCountByElectionCandidate` | `pElectionId,pCandidateId,pThruDate` |
| `GetExpenditureListByElectionCandidate` | `pElectionId,pCandidateId` |
| `GetContributionSummaryByContributor` | `pContributorId` |
| `GetContributorById` | `pContributorId` |
| `GetLookupById` / `GetLookupListByCategoryKey` | `pLookupId` / `pCategory,pLookupKey` |

Base is built as `UserInfo.urlPrefix + "api/CampaignFinanceAPI/"`. The SPA bundles
**`angular2-csv`** ⇒ the public UI has a **CSV export** — worth using if the app returns.

**How this dataset uses it:** `harvest.py` walks GetElections → GetCandidatesByElection →
per-candidate summary/financial/contribution/expenditure calls, **retaining every JSON
payload verbatim** in `raw/` (with `raw/_fetch_log.jsonl` provenance: url, status, sha256,
bytes, retrieved_utc). `build_index.py` renders a `text/` sidecar for every filing and an
`index.csv` at the (election, candidate) grain. The itemized contribution/expenditure
arrays are **kept as documents but NOT parsed into structured tables** — that is a separate
planned layer.

`format=json`, `filing_type=summary` (one disclosure record per candidate per cycle).

---

## HARVEST STATUS (2026-07-05): portal in scheduled-maintenance outage

At acquisition time the portal's **.NET backend was returning HTTP 503** with a styled
"temporarily unavailable due to scheduled maintenance" page on **every dynamic request** —
the SPA shell (`CampaignFinance_Public/`) and **all** `api/CampaignFinanceAPI/*` calls
(`GetElections` included). Static assets under the app (e.g. `app/main.js`) still served
200, which is how the API surface above was recovered — but no data endpoint would answer.

Verified repeatedly across the acquisition window (see `raw/_fetch_log.jsonl` and the
poller log). This is a **temporary source outage, not an absence of data** — the portal
demonstrably holds the filings (it has since at least 2019; see below). `harvest.py` is
complete and ready; re-run it when the backend is back up, then `build_index.py`.

<!-- HARVEST_RESULT -->

---

## Deeper availability (beyond the 2019–2025 scope)

- Wayback's earliest capture of the SPA is **2019-09-15**; the portal was live by the
  2019 cycle. `GetElections` (once reachable) enumerates exactly which cycles it holds —
  likely 2019, 2021, 2023, 2025 and possibly 2017/earlier. Scope here is council+mayor
  2019–2025; widen with `harvest.py --all-years`.
- **Pre-portal cycles (2003–2017) — REVISED 2026-08-02.** These cycles **were** published
  online, in the `CandidateReporting` app (year dropdown 2003–2019) and, for **2003 only**,
  as per-candidate PDFs. What survives today:
  - **2003: 8 filings recovered** → `raw/recorder_2003/` + `text/recorder_2003/`
    (itemized contributions *and* expenditures). Honest gaps in this tranche: 2 files
    (`David_Spatafore`, `J_Michael_Clara`) are **captured by Wayback but currently
    unretrievable** — the Archive serves a donation interstitial instead of the object
    (transient; **retry**); `Dale_Lambert` is on the index but **never captured** (permanent).
  - **2005–2019: no surviving public copy.** The app was POST-only, so Wayback holds its
    forms but never a result page; the app itself now returns HTTP 500. The files still sit
    on the city's IIS host (`D:\IISRoot\dotnet.slcgov.com\managementservices\
    candidatereporting\`, disclosed by the live error). **Honest gap, recoverable only from
    the city.**
  - Supplementary, **not filings**: `raw/recorder_limitations/` — scanned "Public Notice"
    declarations to voluntarily limit contributions/expenditures (2003/2005/2007 cycles,
    from `recorder/pdfs/limitations/`); `raw/recorder_open_committees/` — the **live**
    `slcdocs.com/recorder/Open Committee's.pdf`, the roster of 22 open Personal Campaign
    Committees as of 2019-05-03 (machine-readable text).

---

## Other hosts checked (all negative — SLC self-hosts)

- **`disclosures.utah.gov` (Lt. Governor municipal disclosures).** The municipal tree is a
  county → year → city folder directory (real GET-able paths, e.g.
  `/Municipal/salt%20lake_2023_Salt%20Lake`). Salt Lake **County** lists Salt Lake City,
  but the SLC leaf is **empty (2021) or a single hyperlink that redirects back to the SLC
  dotnet portal (2023)** — the state hosts **no** SLC documents. (Other SL-county cities —
  Sandy, West Jordan, Draper, etc. — *do* file into this tree; SLC does not.) This proves
  self-hosting, exactly as expected.
- **EasyVote** — `slc`, `saltlakecity`, `slcgov`, `saltlake` `.easyvotecampaignfinance.com`
  all fail DNS (no such subdomain). Not an EasyVote city.
- **Wayback Machine** — the API-JSON hypothesis is a **confirmed negative** (2026-08-02):
  a CDX sweep of the entire `slcgov.com` **domain** (86,666 unique URLs) returns **0**
  `CampaignFinanceAPI` captures, so Wayback cannot substitute for the live API. **But the
  2026-07-05 "0 rows for finance PDFs" sweep was wrong** — re-running it over the full
  `/recorder/` prefix (2,946 captures) surfaced the 2003 `fin_disc` tranche, the
  `limitations/` notices, and the Recorder's form library. Wayback is a **positive** channel
  for the pre-2005 era and a negative one for 2005+.
- **`slcdocs.com`** — 12,986 archived URLs, 287 under `/recorder/`. Every campaign-finance
  PDF there is a **blank form** (verified by rendering, not by filename). Two real-document
  exceptions, both acquired/noted: the open-committee roster (above) and
  `recorder/EO_Disclosures/` (officeholder **conflict-of-interest** disclosures — a
  different instrument, not campaign finance).
- **`www.slc.gov`** (current WordPress) — 126,465 archived URLs; WP REST media API on the
  attorney subsite queried directly: `contribution` 0, `expenditure` 0, `campaign` 1 (a PNG).
  Negative.
- **Council packets / PrimeGov / repo FTS** — `fts_packet` has 0 SLC rows; `packets/index.csv`
  (583 rows) 0 matches; the 8 `fts_minutes` SLC hits are all **legislative** (§2.46
  amendments, 2021/2024/2025), with no filings attached. Negative.
- **Salt Lake County Clerk / EasyVote** — re-probed 2026-08-02 and negative on the merits
  (see the table below), not merely by assumption.

## Proven absent, and how verified — REVISED 2026-08-02

| Claim | Status | How verified |
|---|---|---|
| ~~No PDF/document filings anywhere (portal is data-only)~~ | **FALSIFIED** | `recorder/fin_disc/pdfs/` holds 11 indexed 2003 filings; 8 recovered with itemized donors. True only of the *current* SPA. |
| ~~No pre-portal (2007–2017) filings online~~ | **FALSIFIED as stated** | The `CandidateReporting` app's year dropdown lists 2003–2019. Correct statement: **no capture of its result pages survives** (POST-only WebForms; 0 CDX rows with query strings) and the app now 500s. |
| SLC files nothing to `disclosures.utah.gov` | **CONFIRMED, now earned** | 2026-08-02 sweep: 90 folders / **667 files** under `/Municipal/salt lake` downloaded and classified by the **office line inside each form** (407 image-only OCR'd). In-form jurisdiction census: **Salt Lake City = 0**. The 9 apparent hits are all *South* Salt Lake. No pre-2009 folder exists in the state system at all. The 2023/2025 folders explicitly **link out to SLC's own portal**. Statutory reason: §10-3-208 — municipal candidates file with the **municipal recorder**. |
| Not an EasyVote city | **CONFIRMED, now earned** | 18 SLC-shaped subdomains NXDOMAIN (controls resolve). SLCo's EasyVote tenant enumerated: **64 offices** — county, metro townships, school boards — **no SLC Mayor or Council**. |
| SLC files nothing to PMN | **NEW, earned** | JSON POST `/pmn/searchresult.html` with `X-CSRF-TOKEN`: `entityName='Salt Lake City' + agenda='campaign finance'` ⇒ *"No results found."* Query proven live (returns Hyrum / Ogden / Rich County / Wellsville rows unfiltered). |
| Live API genuinely down | **CONFIRMED + reframed** | Static `app/main.js` 200 while `GetElections` 503s. **New:** the sibling candidate app's identical API path returns **401**, and the 503 page renders live DB rows ⇒ the app pool/read surface is off, the data is not gone. |
| No third-party mirror holds the itemized data | see `RECON_2026-08-02.md` | Ballotpedia / FollowTheMoney / news / GitHub sweep. |

## Reproduce

```
python3 harvest.py --probe      # list the portal's election cycles (needs backend up)
python3 harvest.py              # full council+mayor 2019–2025 harvest into raw/
python3 build_index.py          # text/ sidecars + index.csv + election_results join
python3 .claude/skills/expand-city-sources/scripts/validate_dataset.py \
        slc_city_council/campaign_finance
```
