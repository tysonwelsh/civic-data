# RECON — Utah County COUNTY-OFFICE campaign finance

**Recon date: 2026-08-01.** Package B of the owner-approved county acquisition wave.
Scope: **Utah County COUNTY offices** — Board of Commissioners (Seats A/B/C), Clerk /
Clerk-Auditor / Auditor, Sheriff, Attorney, Assessor, Recorder, Treasurer, Surveyor.
**Local school board and judicial-retention filers are OUT OF SCOPE** (Utah County's clerk
posts them in the same lists; they are ledgered, not acquired — see `AVAILABILITY.md`).

This file is the channel map produced BEFORE any acquisition, kept as the honest record of
what was probed and what each probe returned.

---

## 1. Who holds these filings, and why they are here and not on the state site

County-office candidates file **Contribution & Expenditure / financial disclosure statements
with the Utah County Clerk** (Utah Code 17-16-6.5 for county officers; 20A-11 for the
reporting calendar). The Lieutenant Governor's `disclosures.utah.gov` system is for STATE
candidates and, separately, a **municipal** landing area organized county → year — and for
Utah County that municipal area is mostly a **pointer back to the county's own page**. So the
county clerk's own web estate is the primary channel, and it has been rebuilt **four times**
since 2008. Every rebuild changed the URL scheme; three of the four schemes are dead on the
live web and survive only in the Internet Archive.

## 2. The four county URL schemes (chronological)

| Era | Listing scheme | PDF host | Live today? |
|---|---|---|---|
| **A. 2008–2018** | `…/Dept/ClerkAud/Elections/CandidateFinancialDisclosure<YEAR>.asp` and its successor `…/Dept/Clerk/Elections/candidates/disclosures/<YEAR>Disclosures.html` | `www.utahcounty.gov/dept/Clerk/Data/Minutes/CANDFINDISC<OFFICE>/<YEAR>/<file>.pdf` | **listing pages DEAD** (301→404 shell) · **PDFs LIVE** (verified 200/application/pdf 2026-08-01) |
| **B. 2020** | `…/Dept/ClerkAud/Elections/Disclosures/index.asp` + `Past/2020.asp` + `name.asp?LINK_NAME=<NAME>` (per-candidate pages), and the successor `…/candidates/disclosures/2020Disclosures.html` | `www.utahcounty.gov/apps/WebLink/Dept/CLERKAUD/<file>.pdf` and `…/Dept/Clerk/elections/documents/<file>.pdf` | **listing DEAD · PDF hosts DEAD (404)** — but every 2020 filing was **re-hosted** into scheme C |
| **C. 2020–2024** | `…/Dept/clerk/elections/candidates/disclosuresByYear.html?year=<YYYY>` — a JS page that calls a **Strapi CMS API** | `https://api.utahcounty.gov/cms/elections/uploads/<slug>_<hash>.pdf` | **listing page DEAD · API LIVE** (see §3) |
| **D. 2024–present** | `https://vote.utahcounty.gov/financial-disclosures` → a public **Google Sheet** ("Open") with per-cell hyperlinks | `https://drive.google.com/file/d/<id>/view` | **LIVE** |

`ssl.utahcounty.gov` (the old TLS host named in the work order) **no longer resolves/connects
at all** (TCP timeout, 2026-08-01) — every `ssl.utahcounty.gov/dept/clerkaud/elections/*` path
is dead at the host level, not the path level. `https://www.utahcounty.gov/Elections/Disclosures/index.asp`
and `…/dept/clerkaud/elections/financialdisclosures.html` both **302 to `vote.utahcounty.gov`**,
so the 2020/2022 per-year pages named in the work order are recoverable **only from Wayback**.

## 3. The Strapi API (scheme C) — the significant recon find

`…/candidates/disclosure.js` (recovered from Wayback, capture `20230406205153`) contains the
CMS endpoint **and a public read Bearer token** that the county shipped in client-side
JavaScript:

```
api      = https://api.utahcounty.gov/cms/elections
endpoint = /api/candidate-disclosures?populate=disclosureDocs&populate=disclosureDocs.disclosurePDF.media
           &filters[candidacyYear][$gt]=<Y>-01-01&filters[candidacyYear][$lt]=<Y>-12-31
```

**The API is still live and still serves the PDFs** (probed 2026-08-01): 78 candidate records
carrying **158 disclosure documents**, distributed **2020 = 18 docs / 12 candidates · 2021 = 2 /
1 · 2022 = 135 / 62 · 2024 = 3 / 3**. This is the ONLY working channel for the **2022** county
cycle and it is also a **live re-host of the 2020 filings** whose original `apps/WebLink` URLs
404.

⚠ **The API record carries NO office field** — only `candidateFirstName`, `candidateLastName`,
`candidacyYear`, and a `disclosureType` label. Office attribution for 2020/2021/2022 therefore
cannot come from the channel; it must come from the **filing's own printed "office sought"**
plus the county's own canvass (`../elections/election_results_by_contest.csv`). This is the
`portal labels lie` rule applied structurally: the portal here prints no label at all.

## 4. Channel-by-channel probe log (2026-08-01)

| # | Channel / URL probed | Result |
|---|---|---|
| 1 | `https://vote.utahcounty.gov/financial-disclosures` | ✅ 200 — one content link: the Google Sheet `docs.google.com/spreadsheets/d/1siVwIRXEyLTa-4831LlYQBNcJFYbtPrQllENQJGC9Vc` |
| 2 | `https://vote.utahcounty.gov/candidate-information#financial-disclosures` | ✅ 200 — blank FORMS only (2026 Candidate Manual, fillable disclosure form, conflict-of-interest form, signature thresholds). **No filings.** |
| 3 | Google Sheet — CSV export (`/export?format=csv`) | ✅ 200, but exports **only the first tab** and **drops the hyperlinks** (the filings ARE the hyperlinks) |
| 4 | Google Sheet — **XLSX export** (`/export?format=xlsx`) | ✅ 200 — **3 tabs: `2026`, `2025`, `2024`**, with per-cell hyperlink relationships preserved. **This is the usable export.** 26 + 223 + 59 = 308 hyperlinks total |
| 5 | Sheet tab **2026** | ✅ County offices §: 31 candidate rows (Attorney 1, Auditor 4, Clerk 5, Commission Seat A 10, Seat B 10, Sheriff 1) + a Local School Board § (out of scope) |
| 6 | Sheet tab **2025** | ⚠ **Not county** — Spring Lake town municipal races + Aspen Peaks School District. Out of scope for Package B (a **lead**, see `AVAILABILITY.md`) |
| 7 | Sheet tab **2024** | ✅ County offices: Assessor 2, Commission Seat C 6, Recorder 2, Treasurer 1, Surveyor 1 (= 12 candidate rows) + school board + judicial (out of scope) |
| 8 | `https://ssl.utahcounty.gov/dept/clerkaud/elections/Disclosures/index.asp` (2020 page, per work order) | ❌ **host dead** — TCP connect timeout on `ssl.utahcounty.gov:443` |
| 9 | `https://ssl.utahcounty.gov/dept/clerkaud/elections/financialdisclosures.html` / `CampaignFinanceReporting.html` | ❌ same host-level failure |
| 10 | `https://www.utahcounty.gov/Elections/Disclosures/index.asp` (2022 page, per work order) | ⚠ 200 but **302→`vote.utahcounty.gov/candidate-information`** — the historical page is gone |
| 11 | Wayback CDX, `utahcounty.gov` domain, URLs matching `disclos` | ✅ 161 distinct URLs — the full four-scheme map in §2 |
| 12 | Wayback `<YEAR>Disclosures.html` for 2008/2010/2012/2014/2016/2018/2020 | ✅ all 7 recovered (200) — accordion listings, **office in the accordion heading AND in the PDF path** |
| 13 | Wayback `CandidateFinancialDisclosure<YEAR>.asp` for 2008–2018 (the older scheme) | ✅ recovered; **link sets are identical subsets** of the `<YEAR>Disclosures.html` pages (diffed — zero asp-only URLs). The HTML pages are the superset; the .asp pages add nothing |
| 14 | Wayback for a **pre-2008** disclosure page | ❌ none exists. `CandidateFinancialDisclosure2008.asp` is the earliest. **2008 is the true depth floor of the county's publication** |
| 15 | Live probe: `…/dept/Clerk/Data/Minutes/CANDFINDISCATTORNEY/2018/Leavitt.pdf` | ✅ **200 application/pdf** — the 2008–2018 PDF store is still served |
| 16 | Live probe: `…/apps/WebLink/Dept/CLERKAUD/AllenAndrea_Redacted.pdf` (2020 scheme) | ❌ 404 → use the Strapi re-host / Wayback |
| 17 | Live probe: `…/Dept/Clerk/elections/documents/andrea-4-15-22-General_Redacted.pdf` | ❌ returns the site's HTML 404 shell |
| 18 | `api.utahcounty.gov/cms/elections/api/candidate-disclosures` (+ shipped Bearer token) | ✅ **LIVE** — 78 records / 158 docs / years 2020, 2021, 2022, 2024 |
| 19 | Live probe: `api.utahcounty.gov/cms/elections/uploads/<slug>.pdf` | ✅ 200 application/pdf |
| 20 | `disclosures.utah.gov/Municipal/utah_2022` | ⚠ **no filings** — the page's only content link is a **pointer back** to the county's `disclosuresByYear.html` |
| 21 | `disclosures.utah.gov/Municipal/utah_2024` | ✅ **DOES host filings** — 20 direct `municipal.utah.gov/utah\2024\<Name>.pdf` documents + 1 `.xlsx` + 1 `.JPG`, covering county offices (Allen, Canto, Jackson, Beltran, Wessman, McCabe) AND school board. **A genuine second 2024 channel** (Weber-like), verified fetchable |
| 22 | `disclosures.utah.gov/Municipal/utah_2016` / `_2018` / `_2020` / `_2026` | ⚠ effectively empty for county offices — 2018 has one Provo pointer; 2026 lists only city **conflict-of-interest** pages (a different instrument, not C&E) |
| 23 | `drive.google.com/uc?export=download&id=<id>` for a Sheet-linked filing | ✅ 200 application/pdf — Drive filings are fetchable without auth (3 of the 2026 objects are the exception: not publicly shared → `unrecovered.csv`) |
| 24 | **state RESIDENCE-TOWN sub-folders** `/Municipal/utah_<year>_<Town>` (coordinator directive, Juab finding) | ⚠ **Utah County's state tree has NONE.** Every `utah_<year>` page was re-enumerated for `/Municipal/utah_*` sub-links (the first sweep had filtered them out); the whole tree contains exactly one sub-folder, **`utah_2020_Primary`**, and it holds **no documents** — only a link to the (dead) `ssl.utahcounty.gov` page. Negative established by enumeration, not assumption |
| 25 | `municipal.utah.gov/utah/`, `/utah/2020/`, `/utah/2022/`, `/utah/2024/` directory listings | ❌ **403 Forbidden** — the rendered state page is the only enumeration of that file store |
| 26 | `vote.utahcounty.gov/candidate-records` (a SECOND public Google Sheet) | ⚠ candidate FILING records, tabs 2026/2025/2024 only — **no 2022 tab**, so it cannot supply office attribution for the 2022 cycle. Not acquired (logged as a lead) |

## 4a. The two classification rules this package was built under (coordinator directives)

1. **Residence-town folder trap (from the Juab agent).** State `/Municipal/<county>_<year>`
   folders can sub-folder filings by the candidate's TOWN OF RESIDENCE, so a county-office filing
   can hide inside what looks like a city folder, and folder labels cannot clear a folder. Probe
   #24 above is that check, done by enumerating sub-links on every even-year page rather than
   trusting the top-level listing. Utah County's tree has no town sub-folders at all.
2. **The `17-16-6.5` form header CUTS BOTH WAYS (from the Summit agent).** A county form header
   is not proof of a county office — clerks hand the blank county form to towns and districts.
   **So this package classifies by the STATED OFFICE inside the form** ("Office Seeking" /
   "Office"), using the header and the "file with the County Clerk" line as *supporting evidence
   only* (`index.csv.form_header`), plus **cycle parity** as a cross-check: county offices here
   are even-year, and odd-year material is treated as municipal-suspect. The single odd-year
   exception is real and documented — the **2021 County Clerk/Auditor special election** — and
   the odd-year 2025 sheet tab was correctly identified as municipal (Spring Lake town + Aspen
   Peaks School District) and left out of scope.
   The corollary, found empirically here: a **body-keyword** search of the filing is worthless,
   because the form's own title contains "LOCAL SCHOOL BOARD" and its filing-address block
   contains "Utah County Clerk's Office" — an early pass produced 91 false offices from those two
   strings alone. Only the office FIELD counts. See `CLAUDE.md`.

Applied together, the three evidence sources (channel listing, filing Office field, county
canvass) **agreed 39/39** wherever two or more resolved.

## 5. Depth, by cycle (what a complete Package B should contain)

County offices are elected on the **even-year** partisan cycle, staggered:
Commission A+B / Clerk-Auditor / Attorney / Sheriff in one set, Commission C / Assessor /
Recorder / Treasurer / Surveyor in the other. Odd years are municipal — **no county-office
filings exist for 2009…2025 except the 2021 County Clerk/Auditor SPECIAL election**, and that
absence is a real property of the election calendar, not a gap.

| Cycle | Channel(s) | County-office listing count observed at recon |
|---|---|---|
| 2008 | A (Wayback listing → live PDFs) | 2 (Commission only — the county published almost nothing else that year) |
| 2010 | A | 39 (Assessor 4, Attorney 4, Clerk/Auditor 2, Comm A 8, Comm B 7, Recorder 5, Sheriff 3, Surveyor 4, Treasurer 2) |
| 2012 | A | 8 (Commission Seat C) |
| 2014 | A | 47 (Assessor 3, Attorney 5, Clerk/Auditor 4, Comm A 7, Comm B 12, Recorder 4, Sheriff 4, Surveyor 3, Treasurer 5) |
| 2016 | A | 8 (Commission Seat C) |
| 2018 | A | 24 (Attorney 5, Clerk/Auditor 4, Comm A 7, Comm B 3, Sheriff 5) |
| 2020 | B listing (13 candidates) ∪ C API (12 candidates / 18 docs) | ~18–22, office not printed by the channel |
| 2021 | C API | 2 (County Clerk/Auditor special election) |
| 2022 | **C API only** | 135 docs / 62 candidates — county subset to be determined from content |
| 2024 | D sheet (12 county candidate rows) ∪ state `utah_2024` ∪ C API (3) | ~20 |
| 2026 | D sheet | 31 county candidate rows (fewer carry a filing link — many are `NO PRIMARY` / `Out in Convention` with no document) |

## 6. Known hazards carried into acquisition

- **Portal labels lie, again, three ways.** (a) The 2008 listing files two filings under the
  accordion heading *"Commission Seat B"* while the PDF filename says
  `CountyCommissionSeatC-Ellertson…`; (b) the sheet's link TEXT and the linked Drive file often
  disagree on spelling (`Danise Farren` cell → `Danise Farron_Redacted.pdf`); (c) the API's
  `disclosureType` vocabulary is inconsistent even within one year
  (`Withdraw/Elimination` vs `Withdraw/Elmination`, `midterm` vs `Midterm`). **Office and
  filer must be confirmed from the filing's own text**, with the listing label kept verbatim
  alongside.
- **Redaction is upstream.** Nearly every posted file is named `*_Redacted.pdf` — the COUNTY
  redacted donor addresses before publishing. What is missing from these documents was removed
  by the government, not by this repository; nothing here is un-redacted or reconstructed.
- **Scanned filings are the norm, not the exception** in the 2008–2020 era (filed on paper,
  scanned by the clerk) — expect an OCR floor and, for the structured layer, an honest
  totals-only or no-structured-layer outcome rather than invented line items.
- **The 2022 cycle depends on one undocumented API with a client-shipped token.** If that CMS
  is retired, 2022 is unrecoverable from the county. The acquired raw PDFs are therefore the
  archival copy of record for that cycle.

---

## 7. Acquisition outcome (recorded 2026-08-01, after the sweep)

| | |
|---|---|
| filings fetched (all scopes) | 374 |
| **retained county-office filings** | **267** (248 office-resolved + 19 retained-unresolved) |
| distinct candidate-cycles | 82 |
| cycles covered | 2008 · 2010 · 2012 · 2014 · 2016 · 2018 · 2020 · **2021 (special)** · 2022 · 2024 · 2026 |
| out-of-scope, ledgered not retained | 89 school-board filings (`out_of_scope.csv`) |
| unrecoverable | 4 (`unrecovered.csv`) |
| format | 249 scanned · 17 born-digital text · 1 spreadsheet |
| structured money layer | **not built** — no shared family parses this form without modification, and 93% of the corpus is scanned handwriting. Vision pass queued |

The §5 depth table's pre-acquisition estimates all held except where the sweep found MORE:
2020 came in at 25 retained (the 2020-page and Strapi channels are complementary, not
duplicates — only 7 of 22 overlapped byte-for-byte), and 2022 at 69 county filings out of the
API's 135 documents.
