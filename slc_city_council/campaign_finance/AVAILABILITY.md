# Salt Lake City — campaign-finance disclosures: availability & sourcing

**As-of: 2026-07-05.** Dataset scope: municipal candidates for **Salt Lake City Council
(7 geographic districts) + Mayor**, cycles **2019 / 2021 / 2023 / 2025** (see "Deeper
availability" for what the portal holds beyond this window).

This file records every host tried, the portal's real structure, and the honest gaps —
per the repo's cardinal rule that gaps are data.

---

## The one real source: SLC's own Campaign Finance Reporting System

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
- **Pre-portal cycles (2007–2017):** no digitized filings were found on any SLC host
  (see "Absent, and how verified"). Election *results* exist back to 2007
  (`election_results/`), but the campaign-finance *filings* for those cycles are not
  published online. Honest gap.

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
- **Wayback Machine** — CDX sweeps of `slcdocs.com`, `www.slcgov.com`, `www.slc.gov` for
  `campaign|pcc|disclosure|financial-statement` PDFs returned **0 rows**. The portal's own
  XHR/API JSON responses are **not** archived (CDX `…/api*` = 0 rows), so Wayback cannot
  substitute for the live API during the outage.
- **Salt Lake County Clerk** — county/state filings only; not the venue for SLC municipal
  filings (which the city self-hosts).

## Proven absent, and how verified

| Claim | How verified |
|---|---|
| No PDF/document filings anywhere (portal is data-only) | Read the SPA service layer (`campaign-finance.service.js`) — all endpoints return JSON; no document/attachment/file endpoint exists |
| SLC files nothing to `disclosures.utah.gov` | Expanded the state county→year→city tree by GET; SLC leaf empty/redirect for 2021 & 2023 |
| No pre-portal (2007–2017) filings online | Wayback CDX of all three SLC hosts for finance-term PDFs = 0 rows |
| Not an EasyVote city | 4 candidate subdomains fail DNS |
| Live API genuinely down (not a bad guess at the base URL) | Static asset `app/main.js` served 200 from the same app while `GetElections` returned the 503 maintenance page; base URL taken verbatim from the app's own service code |

## Reproduce

```
python3 harvest.py --probe      # list the portal's election cycles (needs backend up)
python3 harvest.py              # full council+mayor 2019–2025 harvest into raw/
python3 build_index.py          # text/ sidecars + index.csv + election_results join
python3 .claude/skills/expand-city-sources/scripts/validate_dataset.py \
        slc_city_council/campaign_finance
```
