# Campaign-finance disclosures — availability & sources checked

**As-of: 2026-07-05.** Dataset for **Sandy City** (Salt Lake County, Utah) municipal
candidates — Mayor + 7-member Council (Districts 1–4 + 3 At-Large) — for the **2019,
2021, 2023, 2025** cycles.

**Result: SUBSTANTIAL for 2021/2023/2025 registered filers; a real, verified GAP for
2019 and for candidates who never registered in the city's portal.** Sandy's authoritative,
currently-published campaign-finance source is the **EasyVote** portal
(`sandycityut.easyvotecampaignfinance.com`), which holds **83 "Report of Contributions &
Expenditures" filings for 7 filers** (all fetched). The pre-portal 2019 filings and the
filings of candidates who never used EasyVote are published only on Sandy's CivicPlus
"engage" year pages, which render their document lists **client-side** and expose **no
retrievable PDF URLs** in either the live or archived HTML — a genuine acquisition gap
(documented below).

---

## Where Sandy candidate campaign-finance filings actually live

Sandy **self-administers** candidate campaign finance (Utah Code 10-3-208; Sandy Ord.
#05-18 and #18-09). It does **not** file candidate reports with the state or the county.
Two eras:

1. **EasyVote portal (current, authoritative) — 2021 onward.**
   `https://sandycityut.easyvotecampaignfinance.com/home/publicfilings` — an Angular SPA
   whose "Public Filings" tab lists every registered filer's reports. Data comes from a
   JSON API at **`https://ecf-api.easyvoteapp.com`** (discovered by reading the app
   bundle):
   - `/authentication/getwebsiteuser/sandycityut` → Sandy's `CustomerId`
     `07F88007-99BF-4B37-B0D3-2CFDD2EEAED3`.
   - `/filer/documentsearch/{CustomerId}` → the full public filer + document list
     (7 filers, 83 documents).
   - `/documents/{documentId}/viewfinalredactedpdf` → the public (redacted) PDF the site
     serves when you click a filing.
   All three require two headers (`Easy-Vote-Authenticated-User`, `ZUMO-API-VERSION`);
   the public "website user" carries a null ZumoToken. Filings dated **2021-10 → 2026-01**.
   The redacted PDFs are **flattened scanned images** (no text layer) — OCR'd here.

2. **CivicPlus city pages (legacy + index) — where 2019 and non-portal filings *should* be.**
   `sandy.utah.gov/343/2019-Financial-Disclosures`, `/338/2021-…`, `/2161/2023-…`,
   `/2349/2025-…` (plus the `/341/Disclosures` hub). These pages exist and load, but the
   per-candidate document list is fetched at runtime from a CivicPlus content module; the
   HTML (live **and** every Wayback capture) contains only an empty content container
   (`[]`). No `DocumentCenter/View/...` PDF URLs are present, and **no Sandy DocumentCenter
   captures exist in the Wayback CDX at all**. So the 2019 candidate PDFs and any
   non-EasyVote filings are **not machine-retrievable** from these pages.

---

## Sources checked (every URL / host tried, and what it had)

| Source | URL / query | Result |
|---|---|---|
| **EasyVote public filings (portal)** | `sandycityut.easyvotecampaignfinance.com/home/publicfilings` | ✅ SPA; data via `ecf-api.easyvoteapp.com`. |
| **EasyVote API — website user** | `ecf-api.easyvoteapp.com/authentication/getwebsiteuser/sandycityut` | ✅ CustomerId `07F88007-…`. |
| **EasyVote API — document search** | `ecf-api.easyvoteapp.com/filer/documentsearch/07F88007-…` | ✅ **7 filers, 83 documents** (saved verbatim as `raw/easyvote/_api_documentsearch.json`). |
| **EasyVote API — redacted PDF** | `ecf-api.easyvoteapp.com/documents/{id}/viewfinalredactedpdf` | ✅ **83/83 PDFs** (application/pdf, scanned). |
| **EasyVote API — elections list** | `ecf-api.easyvoteapp.com/documents/elections/07F88007-…` | Only **"2025 Municipal Election"** is a registered election object (2021/2023 filings exist as documents but predate EasyVote's election records). |
| **State LG — municipal disclosures index** | `disclosures.utah.gov/Municipal/` and `/Municipal/salt%20lake` | County→year folders exist (2019/2021/2023/2025). |
| **State LG — Sandy 2019 folder** | `disclosures.utah.gov/Municipal/salt%20lake_2019_Sandy%20City` | ⚠️ Contains only a **redirect link back to the city page** — NO state-hosted Sandy filings. |
| **State LG — Sandy 2021 folder** | `…/salt%20lake_2021_Sandy%20City` | ⚠️ Empty (nav only) — delegated to city. |
| **State LG — salt lake 2023** | `…/salt%20lake_2023` | ❌ **No "Sandy" entry at all** (Alta, Bluffdale, … West Jordan listed; Sandy absent). |
| **State LG — salt lake 2025** | `…/salt%20lake_2025` | Sandy entry links **out** to `sandy.utah.gov/341/Financials` and to the **EasyVote** portal. |
| **Sandy city — disclosures hub** | `sandy.utah.gov/disclosures`, `/341/Financials` | CivicPlus "engage" hub; points to year pages + EasyVote. |
| **Sandy city — year pages** | `/343/2019-…`, `/338/2021-…`, `/2161/2023-…`, `/2349/2025-…` | ⚠️ Pages load, but candidate document lists render **client-side**; HTML content region is empty (`[]`). |
| **Sandy city — legacy CMS pages** | `/departments/city-recorder/financial-disclosures` (2018/2019 captures) | ⚠️ Same — no inline PDF/DocumentCenter links. |
| **Wayback CDX — Sandy DocumentCenter** | `web.archive.org/cdx/…url=sandy.utah.gov/DocumentCenter*` | ❌ **Zero captures** — Sandy's document store was never archived. |
| **Wayback CDX — disclosure/campaign pages** | `…url=sandy.utah.gov&matchType=domain&filter=urlkey:.*(disclosure\|campaign\|finance).*` | ✅ Located the year pages above; none expose filing PDFs. |
| **Salt Lake County Clerk** | (runs Sandy *elections*, per `election_results/CLAUDE.md`) | County posts **vote results**, not municipal **campaign-finance** filings. |

---

## What was retrieved (see `index.csv`)

| Cycle (election_year) | Filings | Distinct filers | Notes |
|---|---|---|---|
| **2021** | 21 | 5 | interim + year-end C&E reports for the 2021 cycle window |
| **2023** | 27 | — | includes 2023 primary + general interim reports |
| **2025** | 35 | — | includes 2025 primary + general interim + final reports |
| **Total** | **83** | **7** | ~34 MB, all `format=scanned` (OCR'd) |

The 7 filers: **Brooke D'Sousa, Brooke Christensen, Alison Stroud, Parry Harrison,
Kris Nicholl, Cyndi Sharkey, Monica Zoltanski.** Every filing is a Sandy "Report of
Contributions and Expenditures" (Ord. #05-18 / #18-09), combining contributions +
expenditures in one form; `filing_type=interim` for periodic 28/7-day-before reports,
`summary` for year-end **Annual** and post-election **Final** reports.

**`election_year` derivation:** `effective_year = (Jan/Feb filing ? filing_year−1 :
filing_year)`; `election_year = effective_year if odd else effective_year−1`. This buckets
each filing into a Sandy municipal cycle (odd years). Off-cycle **annual** reports by
*sitting* officials land in the nearest cycle window and legitimately do **not** join to a
ballot appearance (see below) — that is honest, not an error.

---

## Gaps — verified absent, and how

1. **2019 cycle: no filings retrievable.** Sandy's 2019 candidate filings predate EasyVote
   and live only on `/343/2019-Financial-Disclosures`, whose document list renders
   client-side; neither the live page nor any Wayback capture exposes the PDF URLs, and
   there are **zero** Sandy `DocumentCenter` captures in the Wayback CDX. The 2019 filers
   (Sharkey, Edwards, Stroud, Zoltanski, D'Sousa, Barker, Theodore, Houseman) are therefore
   **absent** — a portal/archive limitation, not fabricated.
2. **Non-EasyVote candidates (all cycles).** EasyVote holds only the **7 filers who
   registered in it**. Winners who never registered — e.g. **Jim Edwards** (AL 2019),
   **Ryan Mecham** (D1 2021), **Zach Robinson** (D3 2021), **Marci Houseman** (D4 2023) —
   and all losing candidates (Jim Bennett, Aaron DeKeyzer, Iva Williams, Evan Tobin, Shana
   Davis, Scott Earl, Katie Johnson, …) have **no filings here**. Their reports, if filed,
   sit behind the same client-side CivicPlus module and could not be reached.
3. **Redaction.** The only PDF the portal serves publicly is the **redacted** rendering
   (`viewfinalredactedpdf`) — donor street addresses etc. are masked at source. This is
   the public record as published; no un-redacted version is available to the public.

## Cross-dataset finding (documented, NOT altering election_results)

**Parry Harrison** filed a full set of **2025 D3 campaign-finance reports** (28-day-before
primary, 7-day, 30-day post-primary — all dated 2025) but does **not appear anywhere in
`election_results/sandy_races.csv` or `…_by_candidate.csv`.** Sandy's `election_results`
captures only the **general** election; Harrison was a **2025 District 3 primary
candidate** who did not advance (the 2025 D3 general was Kris Nicholl vs. Iva Williams).
His filings are in `index.csv` with `join_confidence=none` and `election_year=2025`. Flagged
here as a data-quality observation for a future `election_results` (primary-coverage)
review; this dataset is **additive** and does not modify `election_results`.
