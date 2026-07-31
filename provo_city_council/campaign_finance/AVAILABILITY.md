# Provo campaign-finance disclosures — availability

**As-of:** 2026-07-03. **Dataset status:** PARTIAL (2021, 2023, 2025 complete; 2019 unrecovered).

## Where Provo campaign-finance filings actually live

The **City Recorder / Elections office publishes them directly** on the CivicPlus
(CivicEngage) city site, in a DocumentCenter, linked from one page:

> **https://www.provo.gov/1001/Election-Documents** → section **"CAMPAIGN FINANCIAL
> DISCLOSURES"**, grouped Mayor / Council, one PDF per candidate per cycle.

This is the canonical source. The state and county sites do **not** independently host
Provo's municipal filings (see below). Each PDF is a single **"Campaign Finance Disclosure
Form"** covering the whole election cycle: a per-reporting-period money summary (starting
amount, donations, expenditures, ending balance for periods 1–8) plus an **itemized
Summary of Donations** (donor, council district, city, amount by period) and Summary of
Expenditures. One document per candidate = a full-cycle **summary** filing (so
`filing_type=summary` for every row; the city does not post the individual interim
period reports separately).

## What was retrieved (41 filings)

| Cycle | Office(s) on ballot | Filings retrieved | Notes |
|------|--------------------|-------------------|-------|
| **2021** | Mayor + Citywide I, D2, D5 | **15** (5 Mayor, 10 Council) | incl. primary-eliminated + 2 filers who withdrew before the ballot |
| **2023** | Citywide II, D1, D3, D4 (no mayor) | **12** (Council) | incl. primary-eliminated + 1 withdrawn filer |
| **2025** | Mayor + Citywide I, D2, D5 | **14** (4 Mayor, 10 Council) | incl. primary-eliminated |
| **2019** | Citywide II, D1, D3, D4 | **0 — UNRECOVERED** | see gap below |

Formats: **37 born-digital** (`pdftotext -layout`), **4 scanned/image** → OCR
(`tesseract`): Eric Mutch 2025 and Shay Aslett 2025 (image-only PDFs; Mutch was scanned
**upside-down** — OSD-derotated before OCR), Rachel Whipple 2025 (text cover + scanned
body), and Travis Hoban 2023 (born-digital but the embedded font has no ToUnicode map, so
`pdftotext` produced mojibake → rasterized + OCR'd instead). Labeled per row in
`index.csv.format` / `.extraction_method`.

## Sources checked and what each yielded

1. **provo.gov/1001/Election-Documents** (City Recorder, CivicPlus DocumentCenter) — **PRIMARY
   SOURCE, yielded all 41.** Also carries, in a *separate* section, **Conflict-of-Interest
   Disclosures** (sitting officials 2025 & 2026, and 2025-election candidates) — a DISTINCT
   statutory filing (personal/business financial interests, not campaign contributions/
   expenditures), so **out of scope** for this campaign-finance dataset and not downloaded.
   30 such COI PDFs exist there if ever wanted (View IDs 3810–4026, 5415–5428, 7423–7430).
2. **provo.gov/798/Election-Information** — voter/ballot logistics only; no finance links.
3. **disclosures.utah.gov/Municipal/utah_<year>** (Lt. Governor state repository) — a
   **link directory that points back to each city's own page**, not an independent host of
   Provo PDFs. Returned **HTTP 500** on `/utah_2019` and timed out on `/utah_2023` during
   retrieval (2026-07-03). Confirms the skill's note: for mid-size Utah cities the state site
   just redirects to the city.
4. **EasyVote** — checked `cityofprovout.easyvotecampaignfinance.com` and
   `provout.easyvotecampaignfinance.com`; **both fail DNS (no such host)**. Provo does **not**
   use an EasyVote instance — it self-hosts on CivicPlus.
5. **Utah County Clerk (vote.utahcounty.gov)** — posts election *results* (already in
   `election_results/`), not municipal campaign-finance filings.
6. **Wayback Machine** — used for the 2019 gap (see below). Only 2025 capture of the current
   Election-Documents page exists; no archived 2019 Provo finance page located.

## The 2019 gap (unrecovered — documented, not faked)

2019 Provo campaign-finance disclosures are **not published on any source checked**:
- **provo.gov/1001** coverage begins at **2021** (earliest DocumentCenter items).
- **Wayback CDX**: `provo.gov/1001/Election-Documents` first captured **2025-08-05** only.
  Broad CDX over `provo.org*` and `provo.gov*` filtered for
  `campaign|disclosur|financ|election` returned only Google/Yahoo-calendar splash links and
  concert-page `utm_campaign=` URLs — **no legacy 2019 finance page**. In 2019 Provo ran a
  legacy custom CMS (`provo.org/?splash=…`); its candidate-finance page, if it existed, was
  not archived.
- **disclosures.utah.gov/Municipal/utah_2019**: HTTP 500.

Recorded in `unrecovered.csv` (4 rows, one per 2019 seat). **election_results DOES have the
2019 races** (Fillmore D1, Ellsworth D3, Hoban D4, Shipley Citywide II + primary losers) —
so the finance gap is one-sided: elections known, filings not published.

## Election-record cross-check (flags only — election_results NOT modified)

The finance filings surfaced **3 candidates who filed but are absent from
`election_results`** (they are not an elections-data defect — the county file lists only
ballot-qualified candidates; these withdrew before the ballot):
- **2021 Suzanne Q.** (View/4467) and **Tom Sitake** (View/4468) — filed, not on 2021 ballot.
- **2023 Ari Emmanuel Webb** (View/3797) — filed, not on 2023 ballot.

No filing implies a *primary the elections docs omit*; every filer maps to a known cycle.
These are logged in `unrecovered.csv` (`filer_not_on_ballot`) for transparency. **Tom Sitake
(2021)** may be the same individual as **Tom Fifita Sitake Sr (2025, Citywide I)** — flagged,
not asserted.
