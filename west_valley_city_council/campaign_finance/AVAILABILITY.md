# Campaign finance / candidate financial disclosures — availability & sources

**As-of:** 2026-07-06 · **City:** West Valley City, Salt Lake County, Utah (~140k, UT's 2nd-largest)
**Scope:** municipal **candidate campaign-finance disclosure statements** (Mayor + City
Council: 4 districts + 2 at-large), odd-year cycles **2019 / 2021 / 2023 / 2025**.

Utah municipal campaign-finance filing is with the **city recorder** (Utah Code 10-3-208),
and West Valley City **publishes its filings online**. Result: **strong 2021 / 2023 / 2025
coverage** (self-hosted, born-digital + scanned); **2019 all but unrecoverable** (one filing
survived in the Wayback Machine; the rest are 404 + un-archived → GRAMA-only).

**105 filings retrieved, ~97.5 MB, 105 text sidecars.** Every filing has a `text/` sidecar
(born-digital → `pdftotext -layout`; scanned → Tesseract OCR @300 dpi, labeled `scanned`).

## Where West Valley City campaign-finance filings actually live (verified)

WVC **self-hosts** on its CivicPlus city website, in the **Archive Center**. There is no
third-party portal.

- Landing page: `https://www.wvc-ut.gov/2105/Campaign-Finance-Statements`
- Three Archive Center collections (the download engine), keyed by `AMID`:
  - `Archive.aspx?AMID=173` → **2025** cycle (44 filings)
  - `Archive.aspx?AMID=174` → **2023** cycle (32 filings)
  - `Archive.aspx?AMID=175` → **2021** cycle (28 filings)
  - ⚠ The page nav labels the three collections "2021 / 2023 / 2025" but the **AMID order is
    reversed** relative to that label. Year was assigned from the **candidate roster +
    embedded filename timestamps**, not the nav label. (Confirmed: AMID 173 holds June
    Freeman Hesleph / Cindy Wood / Amitonu Amosa = 2025; AMID 175 holds Steve Buhler /
    Lindie Sue Beaudoin write-in / Jake Fitisemanu = 2021.)
- Each filing: `Archive.aspx?ADID=<n>` → 302 → `ArchiveCenter/ViewFile/Item/<n>` (the PDF).
  All GET, no auth. `.docx` originals are served converted-to-PDF by CivicPlus.

## What was searched, and the result of each source

| Source | URL / query | Result |
|---|---|---|
| **City sitemap** | `wvc-ut.gov/sitemap.xml` | Found `/2105/Campaign-Finance-Statements` + `/2107/Conflict-of-Interest-Disclosures` + `/258/City-Election-Information` + `/439/City-Recorders-Office`. |
| **Campaign Finance Statements page** | `/2105/Campaign-Finance-Statements` | **HIT** — Archive Center collections AMID 173/174/175 (2025/2023/2021). **104 filings.** |
| **Archive Center download** | `Archive.aspx?ADID=<n>` → `ArchiveCenter/ViewFile/Item/<n>` | 104/104 fetched OK (200, application/pdf). |
| **Wayback CDX — 2019** | `cdx?url=wvc-ut.gov*` + `…/DocumentCenter*` filtered to finance/disclosure/statement | 2019 filings lived in the older **DocumentCenter** (not Archive Center) and are **404 on the live site**. Archived 2019 candidate pages (`/1675`,`/1676`,`/1677`) *link* six primary statements, but the **PDF bytes were never captured** (CDX = 0 captures for those doc IDs). **Only Don Christensen's 2019 Final** (`DocumentCenter/View/9949`) was actually archived → recovered via the Wayback `id_` raw variant. **+1 filing.** |
| **EasyVote** | `westvalley`, `westvalleycity`, `wvc`, `cityofwestvalleyut`, `cityofwestvalleycityut`, `westvalleyut`, `westvalleycityut` `.easyvotecampaignfinance.com` | **All NXDOMAIN.** WVC does **not** use EasyVote (control `cityofwestjordanut.easyvotecampaignfinance.com` resolves — the test is valid). |
| **`disclosures.utah.gov`** | state candidate/PAC system | WVC **municipal** candidate filings are **not** here (state system covers state offices/PACs); municipal filing is with the city recorder per Utah Code 10-3-208. |
| **Salt Lake County Clerk** | county elections office | Runs the **election** (SOVC → `election_results/`), not candidate finance filings. |
| **`westvalleycity.gov` / `wvc.utah.gov`** | Wayback CDX | No such domains carry filings (0 rows). Current + historical host is `wvc-ut.gov`. |

## Coverage by election cycle

| Cycle | Contests (general) | Filings | Distinct filers | Source | Notes |
|---|---|---|---|---|---|
| **2019** | At-Large, D1, D3 | **1** | 1 | Wayback | Only Don Christensen's Final survived online; 5 of 6 general candidates' filings are unrecoverable (see below). |
| **2021** | Mayor, At-Large, D2, D4 | **28** | 12 | city Archive Center | Includes write-in Lindie Sue Beaudoin + primary-only filers. |
| **2023** | At-Large, D1, D3 | **32** | 12 | city Archive Center | 7 primary-only filers; winner **Whetstone filed nothing** (flag below). |
| **2025** | Mayor, At-Large, D2, D4 | **44** | 16 | city Archive Center | Includes a mis-filed Declaration of Candidacy (Danny George, `filing_phase=declaration`). |

Filing types: **67 interim** (primary / post-primary / general 7-day reports) + **38 summary**
(Final campaign-finance statements). Formats: **63 scanned** (OCR) + **42 born-digital text**.

## Join to `election_results` — rates & flags (nothing edited into election_results)

- **Filing-level match:** 77 / 105 filings (73.3%) tie to a general-election candidate row.
- **General-candidate coverage:** 24 / 30 general candidates filed ≥1 statement (**80.0%**).
- **Winner (seated member) coverage:** 11 / 14 winners filed (**78.6%**).
- **Excluding recovery-limited 2019:** 23 / 24 of 2021+2023+2025 general candidates filed
  (**95.8%**) — the sole modern gap is a 2023 winner (below).

The 28 unmatched filings are **primary-only / eliminated-in-primary / write-in** candidates
absent from `election_results` **by design** (`election_results/` is general-only — see its
CLAUDE.md). These are flags, not errors — examples: 2021 Arnold Jones, Philip Wayman;
2023 Steven J Rose, Richard Nowak, Jesus Jimenez-Vivanco, Jacob Gonzalez, James (Jack) Fenn,
Jim Vesock, Darrell Curtis; 2025 Geovani Salazar, Justin Turcsanski, Rocky Thomas, Jim Vesock.

**Flag — general candidates with NO campaign-finance filing found (election-record gap surfaced, NOT edited):**

| Year | Candidate | Office | Winner? | Why absent |
|---|---|---|---|---|
| 2023 | **Will Whetstone** | Council D3 | **Yes (seated member)** | Filed **no** statement in the city Archive Center; not on live site or Wayback. Genuine gap — GRAMA to City Recorder needed. |
| 2019 | Karen Lang | Council D3 | Yes | 2019 filing 404 + never archived (see `unrecovered.csv`). |
| 2019 | Tom Huynh | Council D1 | Yes | 2019 filing 404 + never archived. |
| 2019 | Christiana Tavo | Council D1 | No | 2019 filing 404 + never archived. |
| 2019 | Darrell R Curtis | Council At-Large | No | 2019 filing 404 + never archived. |
| 2019 | Kaletta L Lynch | Council D3 | No | 2019 filing 404 + never archived. |

Reverse-direction quirk: a **2021** archive contains a "Tom Huynh" filing though his D1 seat
was not on the 2021 ballot — retained + flagged `in_election_results=no`, not "corrected."

## What is proven absent, and how verified

- **2019 primary statements (6 candidates):** referenced on archived 2019 candidate pages but
  Wayback CDX returns **0 captures** for their DocumentCenter IDs (14644/14669/14670/14671/
  14677/14678) and the live site 404s → **unrecoverable** (`unrecovered.csv`). Only
  Christensen's *Final* (9949) was archived.
- **2019 final/summary statements (5 of 6):** not posted online anywhere (live 404 + no
  Wayback) → GRAMA-only.
- **EasyVote:** not used (all subdomain guesses NXDOMAIN; control resolves).
- **`disclosures.utah.gov`:** does not carry WVC municipal candidate filings (state system).

## Known limitations / caveats

- **Dates are mostly inferred.** The Archive Center titles carry no explicit filing date.
  Where a filename embedded a document-management timestamp (`_YYYYMMDD…`, some 2025 items)
  `date_precision=day` (this is the city's **upload/scan** timestamp, close to but not
  identical to the statutory filing date; for the mis-filed Declaration it is months after
  the June filing). All other dates are a **representative date by phase**
  (`date_precision=inferred`). Trust `election_year` + `filing_phase`, not the day.
- **This is a filing-level index, not a ledger.** No contribution/expenditure amounts are
  parsed. Many filings are **scanned handwritten forms** — OCR preserves structure but not
  every handwritten dollar figure (that is the separate planned structured layer's job).
- **Conflict-of-Interest Disclosures** (`/2107`, `Archive.aspx?AMID=176`) exist but are
  personal financial/COI statements (Utah Code 10-3-1304-type), **not** campaign-finance
  reports — intentionally **out of scope** here (would not fit the `filing_type` vocabulary).
