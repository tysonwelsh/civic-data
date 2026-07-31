# Campaign finance / campaign-finance disclosures — availability & sources

**As-of:** 2026-07-06 · **City:** Taylorsville City, Salt Lake County, Utah (~60k)
**Scope:** municipal **candidate & elected-official campaign-finance disclosures** (Mayor +
5 district council members), covering annual statements 2017–2026 and the election cycles
found on the city page (**2021, 2023**). Utah municipal campaign-finance filing is with the
**city recorder** (Utah Code **10-3-208**); Taylorsville **self-hosts** its filings.

**71 filings retrieved, ~139 MB. Acquisition-only** — **28 born-digital** (a real text
layer; `format=text`) + **43 scanned image PDFs** (`format=scanned`). No dollar figures are
extracted yet; text/OCR/vision extraction is deliberately **deferred to the structuring
step** (`extraction_method=none` in `index.csv`).

## Two filing regimes — BOTH are campaign finance (this city is unusual)

Taylorsville City Code **2.36.040** requires **two** campaign-finance filings, and both are
"Report of Contributions & Expenditures" forms:

1. **Annual Campaign Finance Statement** (`filing_regime=annual`, **50 filings**) — *"Annual
   Campaign Finance Statement for Elected Officials/Candidates … Report of Campaign
   Contributions and Expenditures — Due March 1st each year"* (code 2.36.040(B)). **Every
   sitting elected official files one every year, even in non-election years and even when
   not on the ballot.** This is why annual statements exist for 2017–2026 for all seated
   members. (The single **2022 "Campaign Financial Disclosure"** grouped under Anna Barbieri
   is one of these — its face reads "MARCH 1, 2022 FINANCIAL DISCLOSURE", all-zeros — so it
   is classified `annual`, not election-cycle.)
2. **Election-cycle campaign disclosures** (`filing_regime=election_cycle`, **21 filings**) —
   the *"CAMPAIGN DISCLOSURE STATEMENT — Report of Contributions & Expenditures for
   Candidates for City of Taylorsville Mayor and City Council Member — <YEAR> Municipal
   Election"* forms: **Primary Initial**, **Pre-General** (interim), and **Final** (summary)
   reports filed by candidates during a race. Present for **2021** (12) and **2023** (9).

> **⚠ DOUBLE-COUNT TRAP (per the skill §6):** candidates file **multiple** election-cycle
> reports per race (e.g. 2021 Larry Johnson & Robert Knudsen each filed Primary + Pre-General
> + Final; 2023 filers each filed 1st + 2nd + Final). `filing_type`/`filing_phase` are set
> **per PDF**. When the structuring step computes any per-candidate/per-race dollar total it
> MUST dedup via `scripts/campaign_finance/cycle_totals.py`, never sum the raw filings.

## Where Taylorsville campaign-finance filings live (verified)

The city **self-hosts** on its CivicEngage/CivicPlus site (Granicus). No third-party portal.

- Landing: `https://www.taylorsvilleut.gov/government/elections/financial-disclosures`
- Per-year subpages: `.../financial-disclosures/<YYYY>-financial-disclosures` (**2017–2025**).
  Each page groups links under "Elected Officials Annual Financial Statements" (annual regime)
  and, in election years, "Disclosures for <Candidate>" (election-cycle regime).
- Each filing: `/home/showpublisheddocument/<docId>/<versionToken>` → the PDF (200,
  application/pdf; GET, browser UA — the site **403s bare bots**, so `polite_fetch.py` was
  used for every fetch). `docId` is unique and is embedded in each stored filename.

## What was searched, and the result of each source

| Source | URL / query | Result |
|---|---|---|
| **City sitemap** | `taylorsvilleut.gov/sitemap.xml` → `sitemap-page-1.xml` | Found `/government/elections/financial-disclosures` (+ `/conflict-of-interest-disclosures`). |
| **Elections page** | `/government/elections` | Links to the Financial Disclosures page (the CF home). |
| **Financial Disclosures page + 9 year subpages** | `.../financial-disclosures/<YYYY>-financial-disclosures` 2017–2025 | **HIT** — 71 filing PDFs (50 annual + 21 election-cycle). All fetched 200/application/pdf. |
| **Wayback CDX** | `web.archive.org/cdx …/financial-disclosures*` | **One** capture only (`2025-08-12`, pre-election). Year subpages & filing PDFs were **never archived** → no Wayback recovery possible for the missing cycles. |
| **`disclosures.utah.gov`** | state candidate/PAC system | Returns 200 (does **not** redirect to the city). State system covers state offices/PACs; Taylorsville **municipal** filings are not there (10-3-208 → city recorder). |
| **EasyVote** | `taylorsville*/cityoftaylorsville*.easyvotecampaignfinance.com` (7 host variants) | **All NXDOMAIN.** Taylorsville does **not** use EasyVote (control `cityofwestjordanut.easyvotecampaignfinance.com` resolves — test valid). |
| **Salt Lake County Clerk** | `saltlakecounty.gov/clerk/elections/` | Runs the **election** (SOVC → `election_results/`), not candidate finance filings. |

## Coverage

| Filing year | Annual statements | Election-cycle filings | Cycle seats up |
|---|---|---|---|
| 2017 | 2 (Burgess, Overson) | — | (Mayor/D4/D5 — no cycle filings posted) |
| 2018 | 4 | — | — |
| 2019 | 4 | **— (GAP)** | D1/D2/D3 election — no cycle filings posted |
| 2020 | 4 | — | — |
| 2021 | 5 | **12** | Mayor/D3(special)/D4/D5 |
| 2022 | 6 (+1 annual grouped under Barbieri) | — | — |
| 2023 | 6 | **9** | D1/D2/D3 |
| 2024 | 6 | — | — |
| 2025 | 5 (+6 for 2026) | **— (GAP)** | Mayor/D4/D5 election — cycle filings not yet posted |

Election-cycle filers: **2021** — Anna Barbieri, Meredith Harker, Larry Johnson, Robert
Knudsen, Kristie Overson. **2023** — Anna Barbieri, Ernest Burgess, Curt Cochran.

## Join to `election_results` — rates & flags (nothing edited into election_results)

- **Candidate-join: 71/71 (100%).** Every filer maps to a Taylorsville officeholder /
  candidate in `election_results/taylorsville_races.csv` (Barbieri D3, Burgess D1, Cochran
  D2, Harker D4, Knudsen D5, Overson Mayor, Johnson 2021-D5 candidate).
- **Election-cycle winner flag** (`election_winner`): 18 filings by winners, 3 by a loser
  (**Larry Johnson**, 2021 D5 — lost to Knudsen 914–825). Annual statements carry no
  winner flag (not tied to a specific race).
- **Roster-drift note:** **Kristie (Steadman) Overson** is mapped to **Mayor** (her office
  2017-present). She previously served as **District 2** council member (won 2011 & 2015) —
  the same drift documented in the city `CLAUDE.md`; her CF filings here are all as Mayor.
- **No election-record mismatch surfaced** — every filer corresponds to a known contest;
  no filing proves a race the election dataset lacks.

## Honest gaps (see `unrecovered.csv`)

1. **2019 election-cycle campaign disclosures — never posted.** The 2019 page (live +
   Wayback) carries only the four annual statements; no primary/pre-general/final campaign
   filings for the 2019 D1/D2/D3 candidates. Challengers **Lisa Gehrke** (D1) and **Marc
   McElreath** (D2) have **no** filings on the page. Publishing gap, not a scraper miss.
2. **2025 election-cycle campaign disclosures — not yet posted (likely lag).** The 2025 page
   carries only the 2025 & 2026 annual statements. The 2025 candidates' final campaign
   statements were statutorily due ~Dec 2025; they are absent as of retrieval. **Re-probe on
   the next `refresh-city` run.** Challengers **Martín Muñoz** (D4) and **Paul Schulte** (D5)
   have no filings.
3. **No text extraction yet** — all 71 are scanned PDFs; OCR/vision is deferred to the
   structuring step (this run is acquisition-only). `screen_corpus.py` is therefore N/A here
   (no text corpus produced yet).
4. **Conflict-of-interest disclosures** (a separate `/conflict-of-interest-disclosures`
   page) were **not** collected — out of scope for campaign finance; noted for completeness.
5. **Overson genuine 2024 annual (CY2023) — effectively UNPUBLISHED (2026-07-19).** The
   city posted the **2025** Overson annual (doc10635) a **second time under the 2024 label**
   as **doc8378** — the two PDFs are **byte-identical** (md5 `6bad67e7…e70d5`; verified by
   md5 + in-body reporting period: contribs 11/20/2024–2/24/2025, signed 2/25/25, "Received
   FEB 26 2025" — an unambiguously 2025 statement). doc8378 is dispositioned a **verified
   content duplicate** (index `extraction_method=duplicate-excluded`; dropped from the
   structured build via `in_scope_fn` so the identical **$11,500 / $665.20** is not
   double-counted — same shape as the Barbieri doc10471≡doc10609 dup). The genuine 2024
   March-1 statement covering CY2023 was never separately posted. **Re-probed 2026-07-19**
   (live 2024 page, HTTP 200): "Overson, Kristie" still resolves to doc8378 — gap persists.
   **Annual regime only → NO race/cycle total affected** (annuals never feed `cycle_totals`).
