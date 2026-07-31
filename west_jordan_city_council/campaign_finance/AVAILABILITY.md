# Campaign finance / financial disclosures — availability & sources

**As-of:** 2026-07-03 · **City:** West Jordan City, Salt Lake County, Utah
**Scope:** municipal candidate campaign-finance reports + elected-official financial /
conflict-of-interest disclosures, Mayor + City Council, odd-year cycles (2019, 2021, 2023, 2025).

Utah municipal campaign-finance filing is with the **city recorder** (Utah Code 10-3-208),
and West Jordan **does publish** its filings online. Result here is **PARTIAL by design**:
strong 2021 / 2023 / 2025 coverage; **2019 not online** (GRAMA-only). 135 filings retrieved.

## Where West Jordan campaign-finance filings actually live (verified)

West Jordan splits its disclosures across **two live systems**, both reachable from the City
Recorder → Elections pages:

1. **City website (WordPress `wp-content/uploads`), disclosures page**
   `https://www.westjordan.utah.gov/elections/conflict-of-interest-and-financial-disclosures/`
   Hosts the **2021 election-cycle campaign-finance PDFs** (8 candidates) plus **annual
   financial-disclosure** (2021–2023) and **elected-official conflict-of-interest** (2024, 2026)
   forms. This page explicitly says: *"To view financial disclosures from 2023 and onward
   [click here]"* → links to the EasyVote portal below.

2. **EasyVote campaign-finance portal (West Jordan's own instance)** — the primary store for
   **2023 and later**.
   - Public UI: `https://cityofwestjordanut.easyvotecampaignfinance.com/home/publicfilings`
     (Angular SPA — empty to a plain fetch).
   - API base (found in the SPA's `main.js`): `https://ecf-api.easyvoteapp.com`
   - Customer id (`/customer/current`, scoped by Origin header):
     `96E8AE5D-966C-406F-AFD4-493B2A8BBF05` = "City of West Jordan".
   - **List filers + their documents:** `GET /filer/documentsearch/{customerId}` (JSON, no auth).
   - **List elections:** `GET /documents/elections/{customerId}` (returned 2025 general + primary).
   - **Public PDF download (redacted):** `GET /documents/{documentId}/viewfinalredactedpdf`
     (200 `application/pdf`, no auth). The authenticated variants `/previewpdf`, `/pdf/{x}`,
     `/viewfinalpdf` all return **401** — `viewfinalredactedpdf` is the public one.
   All GET-only; Origin/Referer headers set to the public site. 101 documents retrieved this way.

## What was searched, and the result of each source

| Source | URL / query | Result |
|---|---|---|
| **City Recorder page** | `/city-recorder/` | Points to `/elections/` → "View Financial Disclosures". No PDFs directly here. |
| **City Elections page** | `/elections/` | Links to `…/conflict-of-interest-and-financial-disclosures/` and the 2025 at-large candidates page. |
| **City disclosures page** | `…/conflict-of-interest-and-financial-disclosures/` | **HIT** — 8 × 2021 campaign-finance PDFs + 9 annual disclosures (2021–23) + 16 conflict-of-interest (2024, 2026). Points to EasyVote for "2023 and onward". |
| **EasyVote portal (WJ)** | `cityofwestjordanut.easyvotecampaignfinance.com` → `ecf-api.easyvoteapp.com` | **HIT** — 101 documents, 16 filers, 2023–2026 (campaign reports + annual disclosures). |
| **`disclosures.utah.gov`** | public search | State-level system (state candidates/PACs). West Jordan **municipal** filings are NOT here — they are on the city/EasyVote systems, per Utah Code 10-3-208 (municipal filing with the recorder). |
| **Salt Lake County Clerk** | `saltlakecounty.gov/clerk/elections/financial-disclosures/` | County/state filings only, via a **separate** EasyVote instance (`saltlakecountyut.easyvotecampaignfinance.com`). Does not carry West Jordan municipal candidates. |
| **Wayback Machine (2019)** | CDX for `westjordan.utah.gov/elections*`, `…/wp-content/uploads/2019*financ*`, `…*campaign-finance*`, `westjordancity.org*`, `wjordan.com*` | **No 2019 campaign-finance PDFs.** Earliest `/elections/` capture is **2021-10-17** — West Jordan's current CMS did not exist online in 2019, and no earlier disclosure page/PDFs are archived. |

## Coverage by election cycle

| Cycle | On ballot (general) | Campaign-finance filings retrieved | Source | Join to `election_results` |
|---|---|---|---|---|
| **2019** | Mayor + At-Large(1) + Dist 1–4 | **NONE online** (GRAMA-only) | — | n/a — gap |
| **2021** | At-Large (Vote-for-3) | **9 filings, 8 candidates** | city website | 6/8 candidates in general results; **2 primary-only** (Tyrone Fields, Craig F. Heath) |
| **2023** | Mayor + Dist 1–4 | **28 filings, 8 candidates** | EasyVote | **8/8** candidates matched |
| **2025** | At-Large (Vote-for-3) | **45 filings, 11 candidates** | EasyVote | 6/11 in general results; **5 primary-only** (Kelvin Green, Rulon Green, Eric Hanna, David Pack, JD Sheppard) |

Plus **53 elected-official financial-disclosure statements** (`filing_type=statement`): annual
financial disclosures (2021–2026) and annual conflict-of-interest disclosures (2024, 2026),
covering seated Mayor + Council members. These are Utah Code 10-3-1304-type personal financial
disclosures, **not** campaign contribution/expenditure reports — kept here (same source pages)
and clearly typed.

## Flags — filings that surface an election-record gap (NOT edited into election_results)

`election_results/` deliberately records **general-election** results only (see
`election_results/CLAUDE.md`: "Primaries … are not output here"). The campaign-finance filings
therefore surface **primary-only candidates** absent from `election_results`:

- **2021 At-Large primary:** Tyrone Fields, Craig F. Heath (filed campaign finance; eliminated
  in the primary; not in the general-only results).
- **2025 At-Large primary:** Kelvin Green, Rulon Green, Eric Hanna, David Pack, JD Sheppard
  (per the city's own "2025 Municipal At-Large Candidates" page these are marked
  "Eliminated in Primary").

These are consistent with the documented general-only scope of `election_results`, **not**
data errors. Flagged here per the skill; `election_results/` was **not** modified.

## Known limitations / caveats

- **2019 is a genuine online gap.** Filings exist as public records with the City Recorder
  (Tangee Sloan, tangee.sloan@westjordan.utah.gov) obtainable by GRAMA request, but are not
  posted online and are not in the Internet Archive. Not fabricated here.
- **Redacted copies.** EasyVote serves the public *redacted* PDF (`viewfinalredactedpdf`);
  personal addresses etc. are blacked out. City-website PDFs are likewise `_Redacted`.
- **~50% are scanned/handwritten forms** (67/135) — candidates upload hand-filled PDFs. These
  were OCR'd with `tesseract` (`extraction_method=ocr:tesseract`); expect word errors. The other
  68 are born-digital (`pdftotext`). Corpus screener (`screen_corpus.py`) is clean
  (dict_ratio median 0.81; no mojibake/garble/outliers).
- **One filing duplicated across sources:** Kelvin Green's 2023 Annual Financial Disclosure
  appears both on the city website (`202303_…`) and in EasyVote (`2023_Green_2023-Annual-…`).
  Both kept (distinct `source_url`/`path`) — honest raw retention, not double-counting a race.
- **No dollar amounts are stored in the index** (per "do not fabricate amounts"); the index
  catalogs filings + provenance. Amounts live in the raw PDFs / OCR text sidecars.
