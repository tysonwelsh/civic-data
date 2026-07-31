# Campaign-finance disclosures — availability & sources checked

**As-of: 2026-07-05.** Dataset for **Ogden City** (Weber County, ~87k) municipal
candidates — **Mayor + City Council** (4 Districts + 3 At-Large seats; the mayor is
separately elected and does not vote) — for the **2019, 2021, 2023** cycles. **2025 is a
verified gap** (see below).

**Result: SUBSTANTIALLY COMPLETE for 2019–2023; 2025 not yet published.** Ogden runs its
**own** municipal campaign-finance disclosure and posts every candidate's filed
"Combined Report of Contributions & Expenditures" as a PDF on the city website, linked
from each cycle's Election-Information year page. **38 filings retrieved** (2019: 7,
2021: 13, 2023: 18); **all 12 general-election winners in 2019–2023 have a filing**, and
**all 20 general-election candidates in those cycles have a filing** (100% coverage). The
2025 cycle's filings were not found on any host as of this date (documented below).

---

## Where Ogden candidate financial disclosures actually live

**Ogden self-hosts its municipal disclosures — it does NOT use the state system.** The
Lt. Governor's `disclosures.utah.gov` municipal tree, under Weber County, lists the
smaller Weber cities (North Ogden, Roy, Riverdale, Plain City, Pleasant View, …) but has
**no "Ogden City" entry at all** — Ogden proper is absent, i.e. delegated to the city
recorder (Utah Code 10-3-208). Ogden does **not** use EasyVote (the `ogden`, `ogdencity`,
`ogdenut` subdomains at `easyvotecampaignfinance.com` do not resolve).

The filings live on the **City Recorder's Election-Information pages** on the CivicPlus
site (`ogdencity.gov`; the legacy `ogdencity.com` links 301-redirect there). There is one
**per-cycle "…-Elections" page**, each with a candidate list and a `DocumentCenter/View/<id>`
link to that candidate's combined report:

| Cycle | Election-Information year page | DocumentCenter View id range |
|---|---|---|
| **2019** | `ogdencity.com/1624/2019-Elections` | 31386–31392 |
| **2021** | `ogdencity.com/2589/2021-Elections` | 17252–17495 |
| **2023** | `ogdencity.com/2048/2023-Elections` | 30766–30783 |

All PDFs were downloaded **live** from the city site (no Wayback needed — the pages and
their PDFs are all still live). Provenance (url, HTTP status, bytes, sha256, final_url) is
in each `raw/<year>/_fetch_log.jsonl`; the four index HTML pages are retained in
`raw/index_pages/`.

---

## Sources checked (each URL / query, and what it had)

| Source | URL / query | Result |
|---|---|---|
| **City Recorder page** | `ogdencity.gov/205/City-Recorder` | ✅ Links to Election Information (`/208`). |
| **Election Information hub** | `ogdencity.gov/208/Election-Information` | ✅ Links to Filing (`/209`), Forms (`/220`), **Financial Reports (`/2971`)**. |
| **"Financial Reports" page** | `ogdencity.gov/2971/Financial-Reports` | ⚠️ Container page; **no documents server-side** (empty widget). Its sidebar links the per-year election pages 2013→**2023** — **no 2025 page listed.** |
| **Forms to File page** | `ogdencity.gov/220/Forms-to-File-for-Office-Misc` | ⚠️ **Blank templates only** (2025 Financial Report *form* View/33638, Declaration, etc.) — not filed candidate reports. |
| **2019 Elections page** | `ogdencity.com/1624/2019-Elections` | ✅ 7 candidate combined-report PDFs (4 mayor + 3 council) + canvass reports. |
| **2021 Elections page** | `ogdencity.com/2589/2021-Elections` | ✅ 13 candidate PDFs (11 combined + 2 "place-holder" stubs) + canvass reports. |
| **2023 Elections page** | `ogdencity.com/2048/2023-Elections` | ✅ 18 candidate combined-report PDFs (7 mayor + 11 council) + canvass reports. |
| **2025 Elections page** | (looked-for) | ❌ **Does not exist.** No `2025-Elections` page in the site nav, the 2971 sidebar, `sitemap.xml`, or the Wayback CDX index of `ogdencity.com*election*` (which lists 2011/2013/2015/2017/2019/2021/2023 — and stops at 2023). |
| **Wayback CDX — Ogden DocumentCenter "Combined"** | `web.archive.org/cdx/search/cdx?url=ogdencity.com/DocumentCenter*&filter=original:.*Combined.*` | ✅ Confirms the 2019/2021/2023 sets; also surfaces **out-of-scope 2013 & 2015** combined reports (see note). **No 2025** combined reports at any capture (incl. `from=20250601`). |
| **CivicPlus DocumentCenter root / site search** | `ogdencity.gov/DocumentCenter`, `/Search/Results?searchPhrase=Combined%20financial` | ⚠️ JS-rendered; no server-side document links (folder tree loads client-side). Year pages are the authoritative index. |
| **State — LG municipal disclosures, Weber** | `disclosures.utah.gov/Municipal/weber_2023`, `/Municipal/weber` | ⚠️ Lists smaller Weber cities only; **no "Ogden City" entry** — Ogden self-hosts. |
| **EasyVote** | `ogden` / `ogdencity` / `ogdenut` `.easyvotecampaignfinance.com` | ❌ Do not resolve — Ogden does not use EasyVote. |
| **Weber County** | (elections authority) | Runs the *election* (canvass), not municipal candidate *filings* — those are the city recorder's. |

---

## What was retrieved (see `index.csv`)

| Cycle | Office(s) on the ballot | Filings (PDFs) | born-digital / scanned | Source |
|---|---|---|---|---|
| **2019** | Mayor + Council D2, D4, At-Large C | 7 | 1 / 6 | Live city page /1624 |
| **2021** | Council D1, D3, At-Large A, At-Large B | 13 | 4 / 9 | Live city page /2589 |
| **2023** | Mayor + Council D2, D4, At-Large C | 18 | 9 / 9 | Live city page /2048 |
| **Total** | | **38** | **14 / 24** | |

Each PDF is a **"Combined Report of Contributions & Expenditures for Candidates"** — a
single packet bundling that candidate's whole-cycle reports (First / Second / Third /
Final statutory filing points, each with a contributions Attachment A + expenditures
Attachment B + summary sheet). Because they are one combined packet per candidate,
`filing_type=summary` for all rows. Two 2021 rows are city-posted **"Financial Report
Place-holder"** stubs (Reyneveld, Barnes) — `placeholder=yes`; they are near-empty forms
(candidate info only, no substantive contributions), retained as honest "filed but empty".

A text sidecar exists for **every** filing in `text/` (14 `pdftotext -layout` for
born-digital; 24 `tesseract OCR (pdftoppm 300dpi)` for image-only scans — Source-6
requirement). OCR quality was screened (all files carry the expected form keywords).

---

## Join to `election_results/` (report)

Filings join to `../election_results/ogden_results_by_candidate.csv` by **normalized
name + election year** (names upper-cased, punctuation stripped, suffixes dropped;
order-independent token match, with a first+last fallback).

- **20 of 38 filings** match a general-election candidate record (`join_confidence=exact`).
- **18 of 38 filings** have **`join_confidence=none`** — every one is a **primary-eliminated
  candidate** who does not appear in `election_results` (which records **general-election
  candidates only**). The city year pages explicitly reference an "Official Primary Election
  Board of Canvass" each cycle, and list these additional primary filers (e.g. 2019 mayor:
  Tabbish, Thompson; 2021 At-Large A primary field of six; 2023 mayor field of seven, D4
  field of five, At-Large C field of six). This is data, not error.
- **Reverse coverage:** **20 of 28** `election_results` candidate records have a filing —
  and the **8 without a filing are ALL 2025** (the gap). For **2019–2023 the coverage is
  20/20 = 100%**, including **all 12 winners** (2019 Caldwell/Hyer/Nadolski/L.Lopez; 2021
  Choberka/Richey/M.White/Blair; 2023 Nadolski/Hyer/Graf/Myers).

### Flagged discrepancy (documented, NOT altering election_results)
`election_results` captures the **general election only**; the 18 primary-eliminated
filers here are additional real candidates. Ogden held municipal **primaries** in 2019,
2021, and 2023 (per the canvass links on each year page). Flagged for a future
`election_results` review; this additive dataset does not modify `election_results`.

---

## Gaps — what is proven absent, and how verified

- **2025 cycle (the current cycle) — NOT PUBLISHED as of 2026-07-05.** The 2025 municipal
  general elected Flor Lopez (D1), Ken R. Richey (D3), Alicia Washington (At-Large A),
  Kevin Lundell (At-Large B). **No 2025 candidate financial reports were found on any
  host.** Verified four ways: (1) **no `2025-Elections` page exists** — absent from the
  site nav, the `/2971/Financial-Reports` sidebar (which lists year pages 2013→2023 and
  stops), `sitemap.xml`, and the Wayback CDX index of `ogdencity.com*election*`; (2) **no
  2025 "…-Combined" or "…Financial" DocumentCenter item** in Wayback CDX, including
  captures `from=20250601`; (3) not on the state site (`disclosures.utah.gov` has no Ogden
  entry); (4) EasyVote subdomains do not resolve. Only the **2025 blank form template**
  (`DocumentCenter/View/33638`) exists — no filed reports. This is an **acquisition gap to
  revisit** once the city posts the 2025 cycle (added to `../../TODO.md`).
- **2013 & 2015 filings exist but are OUT OF SCOPE** (cycles requested are 2019–2025).
  Wayback CDX / the site expose live 2013 combined reports (View 17166–17171: White, Blair,
  Garner, Stephens, Bitton, Stephen-Thompson — report due dates Aug–Dec **2013**) and 2015
  reports (View 17369–17371: Nadolski, Ogden, L. Lopez). **Not retrieved.** Recorded here so
  a future backfill knows they are available.
- **No genuinely missing 2019–2023 in-scope filing was identified** — every candidate the
  year pages list has its linked PDF live, and every download returned a valid PDF (0 bad).
