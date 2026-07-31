# Provo, Utah — Civic Data Recon

City: **Provo** (Utah County, Utah). Recon date: **June 2026**. Scope: 2020–present.
Council body: **Provo Municipal Council** (mayor–council form of government).

---

## 1. Council meeting minutes

### Portal vendor
**Hyland OnBase Agenda Online** (custom OnBase "Agenda Online" web app). NOT PrimeGov / Legistar / CivicPlus-AgendaCenter / CivicClerk.

- Primary portal: **https://agendas.provo.gov/** (`agendas.provo.org` 301-redirects here).
- A separate `documents.provo.gov/OnBaseAgendaOnline/...` host appears in old search results but currently 404s. Use `agendas.provo.gov`.
- Provo also runs a CivicPlus **CivicEngage / AgendaCenter** site at `www.provo.gov/AgendaCenter` and `www.provo.gov/430/Agendas-and-Minutes` — but the AUTHORITATIVE, complete council agenda+minutes archive is the OnBase portal at agendas.provo.gov. (Note: `www.provo.gov` and `www.provo.org` are both live Provo domains; provo.org is the newer site.)
- Utah Public Meeting Notice (PMN) mirror of agendas: `https://www.utah.gov/pmn/` (search body "Provo Municipal Council", publicbody id 1600). Good fallback for agenda notices but generally agendas only, not minutes.
- Video: `https://youtube.com/ProvoCityCouncil`.

### URL / access pattern (OnBase Agenda Online)
- **Home (recent/upcoming):** `https://agendas.provo.gov/`
- **Search page (GET):** `https://agendas.provo.gov/Meetings`
- **Search (POST):** form-POST to `/Meetings` with fields:
  - `__RequestVerificationToken` (anti-CSRF; scrape from GET of `/Meetings`, send cookie jar back)
  - `Keywords` (optional)
  - `MeetingTypeIDs` (multi-select; optional — leave blank to get all)
  - `DateRangeOptionID` = `11` for "Custom Date Range" (also: 1=Last Year,7=This Year, etc.)
  - `DateRangeCustomStartDate` = `MM/DD/YYYY`
  - `DateRangeCustomEndDate` = `MM/DD/YYYY`
- **View a meeting (HTML agenda):** `https://agendas.provo.gov/Meetings/ViewMeeting?id=<meetingId>&doctype=1`
- **Download a document:** results link to `/Documents/DownloadFile/<filename>.pdf?documentType=<N>&meetingId=<id>`
  - `DownloadFile` returns an HTML "Downloading, please wait…" interstitial whose JS replaces `DownloadFile` → `DownloadFileBytes`.
  - **Fetch the bytes directly from `/Documents/DownloadFileBytes/<filename>.pdf?documentType=<N>&meetingId=<id>`** (send the session cookie + a Referer of `https://agendas.provo.gov/Meetings`).
  - `documentType` codes seen: **1 = Agenda**, **2 = Minutes**, **5 = Agenda Packet** (isAttachment=True).
- Filenames are self-describing, e.g.:
  - `Council_Meeting_2209_Minutes_3_5_2024_5_30_00_PM.pdf` (documentType=2, meetingId=2209)
  - `Work_Meeting_2165_Minutes_3_19_2024_11_15_00_AM.pdf`
  - `Council_Meeting_2330_Agenda_6_23_2026_5_30_00_PM.pdf`

### Meeting bodies / cadence
- Two related Municipal Council meetings on the **same day**:
  - **Work Meeting / Work Session** — early afternoon (~1:00 PM; format varies, e.g. 11:15 AM, 1:00 PM).
  - **Council Meeting (Regular)** — **5:30 PM**.
- **Weekday: Tuesday.** (e.g., 6/23/2026 is a Tuesday; 3/5/2024, 3/19/2024 are Tuesdays.) Generally **1st & 3rd Tuesday** of the month, ~22–26 regular council meetings/year.
- Other bodies in the same OnBase system: Redevelopment Agency (RDA) board, Planning Commission, Stormwater District, etc.

### Minutes coverage & format
- **Minutes (documentType=2) confirmed present for at least 2018 → present**, continuous through 2026. Counts of *distinct Council Meeting* minutes PDFs: 2018–19 ≈ 33, **2020 = 26, 2021 = 22**, 2024 fully present. Work Meeting minutes also present.
- **Format: born-digital PDF with real text** (NOT scanned/OCR). `pdftotext` extracts clean text. ~5 pages/12.5 KB text for a typical regular meeting.

### Roll-call votes in minutes — CONFIRMED YES
Opened `Council_Meeting_2209_Minutes_3_5_2024` (meetingId 2209). Minutes contain structured motion + vote records, e.g.:

> Motion: An implied motion to approve Ordinance 2024-13 … The motion was approved **5:1** with Councilors **Christensen, Garrett, Handley, Hoban, and MacKay in favor. Bogdin opposed. Whipple excused.**

Each motion records: motion text, numeric tally (e.g. `6:0`, `5:1`), **named members in favor**, **named opposed**, and **excused/absent** members. This is exactly the structured roll-call data needed for vote extraction. Minutes also include "Roll Call", prayer/pledge, public comment notes, and adjournment.

---

## 2. Council structure

**Provo Municipal Council = 7 members**, each a **4-year term**, **staggered** (half elected each odd year).

- **5 district seats:** District 1, District 2, District 3, District 4, District 5.
- **2 at-large / citywide seats:** Citywide I (a.k.a. "City Wide 1") and Citywide II ("City Wide 2").

> NOTE: an early web snippet described only Districts 1–4 (older redistricting / precinct list). The CURRENT official council page and the election ballots both confirm **5 districts + 2 citywide = 7**. Treat 5+2 as authoritative; flag if a downstream source disagrees.

### Stagger (confirmed from ballots)
- **Odd year A (2021, 2025):** Citywide I, District 2, District 5 (+ Mayor).
- **Odd year B (2023, 2019):** Citywide II ("City Wide 2"), District 1, District 3, District 4.

### Current members (per provo.gov/434/City-Council, June 2026)
- **Katrice MacKay** — Citywide I
- **Gary Garrett** — Citywide II
- **Craig Christensen** — District 1
- **Jeff Whitlock** — District 2
- **Becky Bogdin** — District 3
- **Travis Hoban** — District 4
- **Rachel Whipple** — District 5

(Chair/Vice-Chair rotates annually; not listed on the static page — confirm via a recent agenda if needed. Names like "Handley" appear in 2024 minutes — roster changes across years, so build the roster per-meeting-date from the minutes/elections, not a single snapshot.)

Sources: `https://www.provo.gov/434/City-Council`, `https://provo.municipal.codes/Code/2.01.050` (Council Districts), `https://provo.municipal.codes/Code/2.50.060` (Council Terms and Districts — 403 to bot fetch; retrieve via browser/archive).

---

## 3. Public comments

**Published: PARTIAL / yes (two channels).** Do not conclude unavailable.

1. **Open City Hall (now on OpenGov):**
   - Public-facing alias: **`OpenCityHall.provo.org`**.
   - Underlying host: **`https://communityfeedback.opengov.com/portals/provout`** (OpenGov "Community Feedback"/Open City Hall). Topic/announcement pages exist, e.g. `.../portals/provout/announcements`. (Direct bot fetch returned 403/404 — JS app; retrieve via browser or OpenGov public API.)
   - This is where residents submit and where written comments + statements are published per topic.
2. **In-minutes transcription:** the OnBase minutes include a public-comment portion; speakers and comment summaries are transcribed into the council minutes PDFs (text-extractable).
3. **Planning / Boards public comments page:** `https://www.provo.org/departments/development/boards-and-commissions/public-comments` (403 to bot; this is Planning Commission / boards comment intake, not council).
4. **Agenda Packets (documentType=5)** in OnBase often include written correspondence/comment attachments submitted ahead of a meeting.

### How the public submits comment
- Online via **OpenCityHall.provo.org** (OpenGov).
- In person at Council Chambers during the 5:30 PM Tuesday meeting, or by phone during the live broadcast.

Most promising URLs for harvesting written comments, in order:
1. `https://communityfeedback.opengov.com/portals/provout` (+ its OpenGov public API per-topic).
2. OnBase **Agenda Packet** PDFs (documentType=5) for correspondence attachments.
3. Minutes PDFs (documentType=2) for transcribed verbal comments.

---

## 4. Elections (run by Utah County)

- **Results portal:** `https://vote.utahcounty.gov/results/` with per-year pages `https://vote.utahcounty.gov/results/<YYYY>` (years 2016–2026 listed).
- **Existing local archive scaffold:** `~/Desktop/utah-elections-archive/counties/utah/` (README present; scaffold only — `data/ geo/ maps/ raw/ scripts/` empty; UGRC CountyID = 25; known-good 2024 SOVC CSVs listed). Reuse this; it already documents the wide-crosstab SOVC parser plan.
- **Provo council IS in these countywide files at precinct level.** Precinct rows are prefixed **`PR`** (PR01, PR02, …). SOVC = wide crosstab, **3-row header** (race name row, candidate row, then precinct data rows).
- Provo council races are **district-based + 2 citywide** (matches §2). Provo is vote-by-mail like the rest of Utah County.

### Per-year municipal (odd-year) results — exact files
- **2021 (`/results/2021`):**
  - **General SOVC CSV (HAS Provo, precinct-level):** `https://vote.utahcounty.gov/cms/uploads/21_G_Countywide_SOVC_suppressed_1b85ad469d.csv`
    - Header confirmed to include: `Provo Mayor`, `Provo City Council - City Wide 1`, `Provo City Council - District 2`, `Provo City Council - District 5`.
  - Primary SOVC CSV: `https://vote.utahcounty.gov/cms/uploads/21_PP_2021_Primary_Statement_of_Votes_Cast_SUPPRESSED_bd47a35ddf.csv`
  - Summary PDFs: `2021_General_PDF_4d36475691.pdf`, `2021_Primary_PDF_e05a1d3833.pdf`
- **2023 (`/results/2023`):** ⚠️ **NO general SOVC CSV published — PDF only.**
  - General results PDF (born-digital text, HAS Provo): `https://vote.utahcounty.gov/cms/uploads/2023_General_voting_results_be47c5636c.pdf`
    - Confirmed contains: `City Wide 2 - Provo City Council`, `Provo City Council District 1`, `Provo City Council District 3`, `Provo City Council District 4`.
  - Primary PDFs: `2023_Primary_voting_results_30a0ba993f.pdf`, `23_P_SOV_Cs_suppressed_1907fb1cba.pdf`
  - **No precinct CSV → only citywide/canvass rollups for 2023.** This is the main elections gap.
- **2025 (`/results/2025`):**
  - **SOVC CSV (HAS Provo):** `https://vote.utahcounty.gov/cms/uploads/SOVC_Simple_Redacted_7a5eddcaf2.csv`
    - Header confirmed: `Provo City Mayor`, `Provo City Council City Wide I`, `Provo City Council District 2`, `Provo City Council District 5`, `Proposition #5 Provo`.
  - Primary SOVC CSV: `https://vote.utahcounty.gov/cms/uploads/2025_Primary_SOVC_suppressed_4bc086dabf.csv`
  - Cast-Vote-Record (CVR) workbook: `https://vote.utahcounty.gov/cms/uploads/Public_CVR_b925043b8b.xlsx`
  - Official county summary/canvass PDFs: `OFFICIAL_Countywide_Results_11_17_f09d22f26a.pdf`, `Countywide_Summary_Results_Official_99ee333134.pdf`, `City_Detail_Canvass_Stats_47d88075dd.pdf`, etc.
- **2024 (general/primary), known-good (from archive README):** `2024_General_SOVC_FINAL_9d0c1e4b30.csv`, `24_P_SOVC_suppressed_small_precincts_41eef5de38.csv` — relevant for non-council (state/county) overlap only.

> Filename hashes are unguessable; ALWAYS scrape `/results/<year>` HTML and regex `/cms/uploads/[^"']+` to discover current links. Each link appears twice (once with a trailing backslash artifact `\` — strip it).

---

## 5. GIS — precinct & district boundaries

- **UGRC Vista Ballot Areas (voting precincts, all 29 counties):**
  - FeatureServer: `https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/VistaBallotAreas/FeatureServer/0`
  - Filter Utah County: `where=CountyID=25` → **533 ballot areas** returned (confirmed live).
  - Fields include `CountyID`, `VistaID`, geometry (polygon, WKID 102100). Query precinct names/geometry with `outFields=*`, `f=geojson`.
  - Product page: `https://gis.utah.gov/products/sgid/political/voter-precincts/`; OpenData: `https://opendata.gis.utah.gov/datasets/utah-vista-ballot-areas`.
- **Precinct → Provo council district mapping:** Provo City Code §2.01.050 lists which voting precincts compose each council district (e.g., D1 = precincts 301,302,304,…; etc.). Combine the §2.01.050 precinct lists with VistaBallotAreas geometry (CountyID=25) to dissolve precincts into council-district polygons. No single prebuilt Provo council-district FeatureLayer was found in recon — derive it from precinct lists + Vista geometry. (Provo may also publish a district map PDF via provo.gov; not located/confirmed here.)

---

## Retrieval plan (recommended approach + effort)

| # | Dataset | Source | Approach | Effort | Confidence |
|---|---------|--------|----------|--------|-----------|
| 1 | **Council minutes 2020→now** | agendas.provo.gov OnBase | POST `/Meetings` per year (DateRangeOptionID=11, Jan 1–Dec 31), regex minutes anchors (`documentType=2`), download via `DownloadFileBytes` with session cookie+Referer. `pdftotext` → markdown. | **Low–Med** | **High** |
| 2 | **Roll-call votes** | same minutes PDFs | Parse motion blocks: tally `\d+:\d+`, names after "in favor", "opposed", "excused/absent". Build per-member Aye/Nay/Absent. | **Med** (regex tuning across years) | **High** (format confirmed) |
| 3 | **Council roster/structure** | provo.gov/434 + municipal.codes 2.01.050/2.50.060 + ballots | Scrape current roster; derive historical roster per term from election winners. | **Low** | **High** |
| 4 | **Public comments** | OpenGov (communityfeedback.opengov.com/portals/provout) + Agenda Packets (docType=5) + minutes | Browser/OpenGov API for Open City Hall; harvest packet PDFs + minutes comment sections. | **Med–High** (JS portal, 403 to bots) | **Med** |
| 5 | **Elections 2021/2025 (CSV)** | vote.utahcounty.gov SOVC CSVs | Reuse `~/Desktop/utah-elections-archive`; download CSVs, parse 3-row wide-crosstab, filter `Provo*` columns + `PR*` precinct rows. | **Low–Med** | **High** |
| 6 | **Elections 2023 (PDF only)** | 2023_General_voting_results PDF | `pdftotext` the rollup PDF; parse Provo council races (no precinct granularity). | **Med** | **Med** |
| 7 | **GIS districts** | UGRC VistaBallotAreas (CountyID=25) + §2.01.050 precinct lists | Pull precinct geometry as GeoJSON; dissolve by council-district precinct lists → district polygons; build address→district lookup. | **Med** | **Med–High** |

---

## Risks / blockers

1. **OnBase download interstitial** — `DownloadFile` returns an HTML "please wait" page; MUST rewrite to `DownloadFileBytes` and carry the session cookie + Referer or downloads come back as 1.4 KB HTML, not PDF. (Solved/documented above.)
2. **CSRF token + cookie required** for the `/Meetings` POST search — scrape `__RequestVerificationToken` per session.
3. **2023 election = no precinct CSV** — only born-digital rollup PDFs. Precinct-level Provo council results for 2023 are unavailable as CSV; must parse PDF and accept citywide-rollup granularity for that cycle. **Primary elections data gap for council-district precincts in 2023.**
4. **Unguessable filename hashes** on vote.utahcounty.gov — never hardcode; always re-scrape `/results/<year>` and strip the trailing `\` artifact in links.
5. **District count ambiguity (4 vs 5)** in some secondary sources — authoritative is **5 districts + 2 citywide**; redistricting between cycles means the precinct→district map (§2.01.050) may differ by year. Pin the map to the election year.
6. **OpenGov Open City Hall is a JS SPA** (403/404 to plain fetch) — needs headless browser or OpenGov public API; comment volume/coverage uncertain.
7. **Two live city domains** (`provo.gov` CivicEngage + `provo.org`) and a third agenda host (`documents.provo.gov`, currently 404) — standardize on **agendas.provo.gov** for minutes to avoid duplicate/partial AgendaCenter data.
8. **Roster drift** — council membership changes across 2020→2026; build per-meeting roster from minutes + election winners rather than the single current snapshot.
