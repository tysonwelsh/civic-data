# Campaign-finance disclosures — availability & gap log

**As-of:** 2026-07-02 · City: St. George, **UTAH** (Washington County — NOT Louisiana).
Source type 6 of the `expand-city-sources` skill.

St. George municipal candidates file **Campaign Finance Reports** with the **City
Recorder** (Utah Code 10-3-208 makes municipal campaign-finance filing a city, not a
county or state, responsibility). The city posts them as **combined per-filing-period
PDF packets** (all candidates for that deadline scanned into one file), NOT per-candidate
files. This dataset covers the **2021, 2023, and 2025** municipal cycles. **2019 is an
unrecoverable gap** (see below). Every filing is a **scanned image** of the state
"Campaign Finance Report" form (front = summary balances; back = Form A itemized
contributions / Form B itemized expenditures); text was recovered by **OCR (tesseract)**.

## What each source had

### 1. City recorder / campaign-finance page — PRIMARY SOURCE (has filings) ✅
Two live city pages carry the disclosures:

- **Dedicated page:** `https://sgcityutah.gov/departments/city_manager_s_office/campaign_financials_and_disclosures_and_conflict_of_interest.php`
  — the **2025** cycle packets + officeholder conflict-of-interest statements.
- **Elections page:** `https://sgcityutah.gov/government/mayor_and_council/election_information.php`
  — the **2023** cycle packets.
  (Note: `.../city_council/election_information.php` is a 404; the live path is under
  `mayor_and_council/`.)

Revize CMS URL nuance (confirmed): the **2025 packets resolve root-relative** —
`https://sgcityutah.gov/<filename>.pdf` (e.g. `.../2025.08.05 Campaign Finance Reports.pdf`,
200 application/pdf); the **2023 packets** live under
`https://sgcityutah.gov/Documents/Government/Mayor%20And%20Council/Election%20Information/`.
`= cms3.revize.com/revize/stgeorge/Documents/...` (same bytes).

**Retrieved (10 live packets):**
| Cycle | Packet (filing date) | filing_type | candidates |
|---|---|---|---|
| 2023 | 2023-08-29 pre-primary (all filers) | interim | 14 council |
| 2023 | 2023-08-29 pre-primary (non-advancer re-post, undated) | interim | 8 council |
| 2023 | 2023-10-24 (period 08/25–10/19) | interim | 5 council |
| 2023 | 2023-11-14 (period 10/20–11/09) | interim | 5 council |
| 2023 | 2023-12-21 year-end (period 11/10–12/21) | summary | 5 council |
| 2025 | 2025-08-05 pre-primary | interim | 4 mayor + 7 council |
| 2025 | 2025-09-11 post-primary (eliminated) | summary | 3 council |
| 2025 | 2025-10-07 pre-general | interim | 2 mayor + 4 council |
| 2025 | 2025-10-28 pre-general | interim | 2 mayor + 4 council |
| 2025 | 2025-12-04 year-end | summary | 2 mayor + 4 council |

### 2. Wayback Machine — SECONDARY SOURCE, recovered the 2021 cycle ✅
The 2021 packets are **gone from the live site** (they lived on the pre-migration domain
`www.sgcity.org`, retired when the city moved to `sgcityutah.gov`). They survive only in
the Internet Archive under
`www.sgcity.org/pdf/administration/general/campaignfinancialreports/`.

**Recovered (4 packets) via CDX → `web/<ts>id_/<pdf>`:**
| Filing date | filing_type | candidates | Wayback ts |
|---|---|---|---|
| 2021-08-03 pre-primary (all filers) | interim | 4 mayor + 11 council | 20210807165937 |
| 2021-09-09 post-primary (eliminated) | summary | 2 mayor + 7 council | 20211230092356 |
| 2021-10-26 pre-general | interim | 2 mayor + 4 council | 20211228222439 |
| 2021-12-02 year-end | summary | 2 mayor + 3 council* | 20211228222338 |

\*Larsen's year-end (2021-12-02) report is not in the archived packet (only 5 of the 6
general finalists appear). Recorded as present-in-file only; not fabricated.

### 3. `disclosures.utah.gov` (state) — NO municipal filings (verified) ❌
`https://disclosures.utah.gov/` (HTTP 200). The Utah state disclosure portal covers
**state/legislative/statewide/PAC** filers only. Municipal candidates file with the city
per Utah Code 10-3-208; St. George is **not** in the state system. No St. George
municipal campaign-finance data here.

### 4. Washington County Clerk — NO campaign-finance filings (verified) ❌
`https://www.washco.utah.gov/departments/clerk/elections/` administers **election
results** (already harvested into `../election_results/`), not candidate finance filings.
The county's `previous-election-results` index posts canvass/results files only. The
recovered 2021 folder also held two **canvass** PDFs
(`canvassofthe2021primaryelection.pdf`, `reportonthecanvass...generalelection.pdf`) —
these are election-results documents, not campaign finance, and were **not** ingested
here.

## The 2019 gap (unrecoverable)

**No 2019 St. George municipal campaign-finance filings could be located** on the live
site or in the Internet Archive, despite thorough searching:

- Live site: no 2019 packet on either the elections or campaign-finance page.
- Wayback CDX, old domain, searched exhaustively:
  - `sgcity.org/pdf/administration/general/campaignfinancialreports*` → only **2021** files.
  - `sgcity.org/election/*` → 2011, 2013, 2015 CFR PDFs, then a gap to 2021 (no 2017/2019).
  - `sgcity.org/pdf/2019electioninformation*` → **empty** (no captures).
  - `sgcity.org/2019electioninformation*` (prefix, all depths) → **empty**.
  - `sgcity.org/pdf/administration/general*` (full folder, 1000-row cap) → no 2019/2017
    campaign-finance PDF (only the 2023 `2023electiondocuments/` and 2021
    `campaignfinancialreports/` folders held finance PDFs).
  - Broad filter `original:.*(2019|2017).*(ampaign|inanc|isclos|lection).*` → only
    election-*information* landing pages and CAFRs, no candidate finance reports.
- The Aug-2019 capture of `/2019electioninformation/` is a menu page that predates the
  fall filing deadlines and links no finance PDFs.

**Conclusion:** the 2019 filings (for Hughes, McArthur, Larkin, Baca, Aldred, Arial —
the six council candidates in `../election_results`) were either never posted online or
were posted after Aug 2019 to a path the Archive never crawled. They are **not**
digitally recoverable from any trusted source. A records request to the City Recorder
(Christina Fernandez, 435-627-4003) would be the only remaining avenue. **Not
fabricated; recorded as a known gap.** (This does NOT surface an election-record gap —
`../election_results` correctly lists the 2019 race; only the finance filings are
missing.)

## Related source NOT ingested (documented for completeness)

The dedicated city page also hosts **officeholder Conflict-of-Interest disclosure
statements** (2025 & 2026, one PDF per sitting member: Hughes, Tanner, Kemp, Larsen,
Larkin, Anderson) under
`https://sgcityutah.gov/Documents/Government/Conflict of Interest Disclosures/<year>/`.
These are a **distinct document class** (annual officeholder financial-conflict
statements, not campaign contribution/expenditure reports) with an awkward mapping to
`election_year`, so they are **deliberately excluded** from this campaign-finance index
to keep its semantics clean. They are a viable future `statement`-type addition if
desired.

## OCR / extraction caveats

- All packets are **scanned** (photocopied handwritten/typed state forms). `format=scanned`,
  `extraction_method=ocr:tesseract-psm6@200dpi`. Text sidecars in `text/` are
  **machine-OCR, expect word/number errors** — do NOT treat OCR'd dollar amounts as
  authoritative; the raw PDF is the record. **No amounts are transcribed into `index.csv`.**
- Candidate identity was read from each form's "Full Name of Candidate" field. 14 of 104
  rows had OCR-mangled names assigned by **set-elimination** against the known per-cycle
  roster (`candidate_match=inferred`); the other 90 are clean OCR matches
  (`candidate_match=direct`). All 40 distinct (year, candidate) pairs join exactly to
  `../election_results/st_george_results_by_candidate.csv`.
- `screen_corpus.py`: flags `repeated_line(6+)` on 9/14 files — **expected**, each packet
  is N copies of the identical state-form template. No `dict_ratio`, `split_word`, or
  `weird_char` outliers; 0 read errors.
