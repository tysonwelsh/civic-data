# Orem, Utah — Civic-Data Recon

City of Orem, Utah County. Recon date: 2026-06-24. Focus: 2020–present.
Mandate: map sources WITH EXACT URLS, no bulk download.

---

## 1. Council meeting minutes

### Portal vendor
**Two systems coexist** — and this is the central wrinkle for Orem:

1. **CivicClerk (CivicPlus)** — the *live agenda/meeting* portal.
   - Public portal: `https://oremut.portal.civicclerk.com/`  (JS-rendered SPA; WebFetch returns only "Public Portal • CivicClerk", so the live page is useless to scrape directly).
   - **OData API (this is the key):** `https://oremut.api.civicclerk.com/v1/`
     - `Events` entity set. Page size is **15**; must follow `@odata.nextLink` (`$skiptoken`) to paginate.
     - Full enumeration: **254 events total**, span **2021-07-13 → 2027-01-06** (future meetings included).
     - Categories: City Council **122**, Planning Commission **117**, Board of Adjustments 7, General 8.
     - Filter example: `…/Events?$filter=categoryName eq 'City Council'&$top=400` (URL-encode the space as `%20`; **do NOT add `$select` together with `$orderby … asc` → HTTP 500**).
     - **CRITICAL: `minutesFile.fileName` is null for ALL 122 council events**, and `agendaFile.fileName` is also null. Orem publishes **born-digital HTML web agendas** (each event has `agendaId` > 0, `hasAgenda: true`) rather than uploaded agenda/minutes PDFs in the CivicClerk file slots. So the CivicClerk API alone does **not** yield minutes PDFs.
   - OData functions discovered in `$metadata` that matter:
     - `GetMeetingItemMinutesVotes(id)` — CivicClerk stores **structured per-item minutes/votes** (potential clean vote source if populated; not yet verified populated).
     - `GetEventFile(fileId,fileType)` / `GetEventFileStream(...)` / `GetMeetingFileStream(fileId,plainText)` / `GetAttachmentFile(fileId)` — file-fetch functions. `PublishFileModel` has fields `{id,fileId,publishTo,type,name,url,fileType,streamUrl}` → published files carry a direct `url`.
     - Public-comment actions: `PublicCommentWritten`, `SendEmailPublicComment(model)`, `PublicCommentSignUp(eventId,itemId,name,address,…,participationMethod,…)` and Event field `publicCommentsEnabled` (was `false` on the events sampled). See §3.

2. **Google Drive archive** — the *official minutes/agenda PDF archive* that `orem.gov/meetings` links as "View Archived Meeting Agendas & Minutes":
   - Root folder: `https://drive.google.com/drive/folders/1EEBkHidmn6PrXj9ib0thApFSqmgU9QSv`
   - Subfolders seen: **Minutes**, **Minutes-City Council**, **Agendas**, **Agendas-City Council**, CC Presentations, Meeting Recordings, Training items.
   - This is the primary born-digital **minutes PDF** store. (Sub-agent enumerating year-range + folder IDs; see "Pending" below.)

3. **Utah Public Notice (PMN)** — state mirror, good fallback / pre-2021:
   - `https://www.utah.gov/pmn/` ; Orem council notices like `https://www.utah.gov/pmn/sitemap/notice/<id>.html` with attached PDFs at `https://www.utah.gov/pmn/files/<id>.pdf`.
   - **Verified working sample:** `https://www.utah.gov/pmn/files/806281.pdf` = Orem City Council minutes **Jan 11, 2022** (born-digital text PDF; see vote confirmation below).

### Years of *minutes*
- CivicClerk events: **2021-07 → present** (but no PDF in file slots).
- Google Drive "Minutes-City Council": primary archive — year range pending sub-agent (folders modified through Sept 2025, so current).
- PMN: individual notices 2020–present; **PMN is the go-to for pre-2021** and as a CivicClerk gap-filler.

### Format
**Born-digital, text-layer PDFs** → clean `pdftotext -layout` (verified). Not scanned. Markdownable.

### Meeting cadence / weekday
**Tuesday** evenings, regular meetings 6:00 p.m. at City Center, 56 North State Street. (Historically some 5:00 p.m. work sessions same day — the Jan 2022 sample shows a 5:00 work session + regular meeting in one combined minutes doc.) Annual published schedule:
- 2025: `https://orem.gov/2025-city-council-schedule/`
- 2026: `https://orem.gov/city-council-meetings-for-2026/`
Roughly 2× per month (≈ City Council events 2021–present averages ~24/yr).

### Roll-call votes in minutes — **YES, CONFIRMED**
From `https://www.utah.gov/pmn/files/806281.pdf` (2022-01-11), minutes contain full roll-call detail:
- Mover + seconder named: *"Mr. Spencer moved to by Ordinance to amend… Mr. Peterson seconded the motion."*
- Per-member Aye/Nay lists: *"Those voting aye: David A. Young, Terry Peterson, David Spencer, Jeff Lambson, and LaNae Millet. Those voting nay: Debbie Lauret and Tom Macdonald. The motion passed."*
- Consent agenda + individual motions both recorded. **Contested votes parse cleanly.** Note name-spelling drift ("Millet"/"Millett", "Debby"/"Debbie") → normalize.

---

## 2. Council structure

- **Form of government:** Council-Manager (adopted 1980, effective Jan 1, 1982). Nonpartisan.
  - `https://orem.gov/form-of-government/`
- **Seats: 6 council members + 1 Mayor (7 elected). ALL ELECTED AT-LARGE — CONFIRMED. Zero districts.**
- **Terms:** 4 years, staggered — **3 council seats up each odd year**; Mayor on a separate 4-yr cycle.
- **Current members** (`https://orem.gov/citycouncil/`):
  - **Mayor Karen McCandless** — elected 2025, term to **2030**.
  - **Jeff Lambson** — elected 2023 (2nd term), to **2028**.
  - **Jenn Gale** — elected 2023 (1st term), to **2028**.
  - **Chris Killpack** — elected 2023 (1st term), to **2028**.
  - **Quinn Mecham** — elected 2025, to **2030**.
  - **LaNae Millett** — re-elected 2025, to **2030**.
  - **Crystal Muhlestein** — elected 2025, to **2030**.
  - Sworn in Jan 5–6, 2026 (the 2025 cohort): Daily Herald / Hoodline coverage.
- Stagger check: 2023 cohort (3 seats → 2028) + 2025 cohort (3 seats → 2030) = all 6 council seats accounted for. Prior holders of the 2025 seats (the 2021 cohort, terms 2022–2026) included David Spencer, Debby Lauret, Tom Macdonald, Terry Peterson — replaced/retired in 2025.

---

## 3. Public comments (genuine written/online)

**Verdict so far: UNCLEAR — promising but not yet confirmed published. Do NOT conclude unavailable.**

Hunt status against the 4-source checklist:

1. **Dedicated published-comments page** — none found on orem.gov yet. `https://orem.gov/councilrecap/` ("City Council Recap") is a staff summary blog, NOT public-submitted comments. `https://orem.gov/transparency` — transparency portal, unchecked for a comment archive.
2. **eComment / Open City Hall portal** — **CivicClerk has a written-public-comment feature** (OData actions `PublicCommentWritten`, `SendEmailPublicComment`, `PublicCommentSignUp`; Event field `publicCommentsEnabled`). On the events sampled `publicCommentsEnabled = false`, so it may be off or selectively enabled. **MUST verify**: (a) whether any event has it enabled, and (b) whether submitted written comments are *published back* on the portal/agenda (CivicClerk often surfaces them as agenda-item attachments). This is the single most promising lead.
3. **Agenda-packet attachments "correspondence"/"written comments received"** — CivicClerk per-event published files (`PublishFileModel.url`, fetched via `GetEventFile`/`GetAttachmentFile`) and the Google Drive "Agendas-City Council" packets may bundle emailed comments. **Unverified — needs a packet opened.** (The live `…/event/<id>/files` pages are JS-only; enumerate files via the API, not WebFetch.)
4. **Records/correspondence archive** — not located yet.

**Do NOT count:** clerk paraphrases of in-person speakers in the minutes (e.g., Jan 2022 minutes: *"Mr. Lavenstock stated he moved to Orem from California…"*, *"Mecham finished by urging the council to vote against these proposals."*). Per extraction_standards these are meeting-record notes → at most a separate `minutes_speaker_log.csv`, never `all_comments_clean.csv`.

### Most promising URLs to chase for comments
- CivicClerk API per-event file enumeration (find a council event with `publicCommentsEnabled:true` or a "Public Comment"/"Correspondence" published file): start from `https://oremut.api.civicclerk.com/v1/Events?$filter=publicCommentsEnabled eq true` (verify filter support) and `GetEventFile`/`GetAttachmentFile`.
- Google Drive "Agendas-City Council" packets (folder under `1EEBkHidmn6PrXj9ib0thApFSqmgU9QSv`).
- `https://orem.gov/transparency` (unchecked).

### Submit channel (how the public submits)
CivicClerk written/email public comment + sign-up-to-speak (the `PublicComment*` actions). Confirms an online intake exists; publication-back is the open question.

---

## 4. Elections (run by Utah County)

- **County:** Utah County. **Orem council elections are AT-LARGE** (mirrors council structure; SOVC has single "Orem City Council" multi-winner contest column, not district columns).
- **Primary source:** `https://vote.utahcounty.gov/results/<year>` (UCG Elections).
- **Alt/secondary source:** Utah state results portal `https://electionresults.utah.gov/results/public/utah-county-ut/elections/...` (per-contest dashboards; e.g. 2025 general Orem council ballot-item page exists). Useful cross-check, esp. for 2023.

### Per-year file inventory (verified)
| Year | Precinct SOVC CSV? | Exact URL / note |
|------|--------------------|------------------|
| **2025** | ✅ YES (wide 3-row-header crosstab, per-precinct rows like `25AF01`) | `https://vote.utahcounty.gov/cms/uploads/SOVC_Simple_Redacted_7a5eddcaf2.csv` — header confirms `Orem Mayor` + `Orem City Council` columns; candidates: QUINN MECHAM, CRYSTAL MUHLESTEIN, DOYLE MORTIMER, ANGELA MOULTON, LANAE MILLETT, DAVID M. SPENCER, WRITE-IN; mayor: DAVE YOUNG, KAREN MCCANDLESS. Also `Public_CVR_b925043b8b.xlsx`, summary PDF `OFFICIAL_Countywide_Results_11_17_f09d22f26a.pdf`. |
| **2023** | ❌ NO precinct CSV — **PDF rollup ONLY** (matches Provo-build blocker) | General PDF `https://vote.utahcounty.gov/cms/uploads/2023_General_voting_results_be47c5636c.pdf`; Primary PDF `…/2023_Primary_voting_results_30a0ba993f.pdf`; Primary SOVC PDF (suppressed) `…/23_P_SOV_Cs_suppressed_1907fb1cba.pdf`. Orem council WAS on 2023 ballot (3 seats: Lambson, Gale, Killpack won; Muhlestein, McKell, Rands lost). Precinct CSV must be recovered elsewhere (see risks). |
| **2021** | ✅ YES (per-precinct, 257 rows, precincts `AF01`…) | `https://vote.utahcounty.gov/cms/uploads/21_G_Countywide_SOVC_suppressed_1b85ad469d.csv` — header has `Orem Mayor` + `Orem City Council` columns. (Despite "Countywide" in filename, it IS per-precinct.) General PDF `…/2021_General_PDF_4d36475691.pdf`. |

- Filenames are **hashed** under `/cms/uploads/` — must scrape each `/results/<year>` page for the current link (no stable pattern).
- **District-based? NO** — at-large.
- Existing scaffold: `~/Desktop/utah-elections-archive/counties/utah` (mostly README per brief).

---

## 5. GIS / boundaries

- **No council-district layer expected** (Orem is at-large → no districts to map). Address→"district" tool degenerates to: address → Orem city (in/out) + voting precinct.
- **UGRC VistaBallotAreas / voting precincts**, Utah County `CountyID = 25`; Orem precinct codes appear as `OR3xx` / `25OR…` family (and the SOVC uses `AF##`-style countywide precinct codes — reconcile precinct-code namespaces).
- **No council districts — confirmed** (orem.gov/citycouncil: "all elected at large"; 2025 ballots "Vote for 2" citywide). No council-district GIS layer exists; an address→district tool degenerates to address → Orem city (in/out) + voting precinct.

### UGRC Vista Ballot Areas (statewide voting precincts) — VERIFIED
- REST: `https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/VistaBallotAreas/FeatureServer/0`
- Product: `https://gis.utah.gov/products/sgid/political/voter-precincts/` ; Open data: `https://opendata.gis.utah.gov/datasets/utah::utah-vista-ballot-areas/about`
- Fields: `OBJECTID, CountyID (SmallInt), VistaID, PrecinctID, SubPrecinctID, VersionNbr, EffectiveDate, AliasName, Comments, RcvdDate, GlobalID`.
- **Utah County filter:** `where=CountyID=25` (transfer limit ~20/page; paginate `resultOffset`).
- **Orem precincts = `25OR01`…`25OR59`** (57 records; gaps at 25OR55/56; `PrecinctID==VistaID`). NOTE: this `25OR##` namespace differs from the SOVC CSV's `AF##`/`25xxNN` precinct codes — reconcile.
- Example: `…/VistaBallotAreas/FeatureServer/0/query?where=CountyID%3D25+AND+PrecinctID+LIKE+%2725OR%25%27&outFields=PrecinctID,VistaID,AliasName&returnGeometry=false&f=json`

### UGRC Utah Municipal Boundaries (Orem city boundary) — VERIFIED endpoint
- REST: `https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/UtahMunicipalBoundaries/FeatureServer/0`
- Product: `https://gis.utah.gov/products/sgid/boundaries/municipal/` ; filter `where=NAME='OREM'` (verify field via `?f=json`).

### Utah County–hosted precinct service (alternative)
- `https://maps.utahcounty.gov/arcgis/rest/services/Elections/Precinct_Only/MapServer/9`
- Interactive maps: `https://vote.utahcounty.gov/maps` , `https://www.utahcounty.gov/dept/clerk/elections/maps.html`

---

## Google Drive minutes archive — ENUMERATED (verified)

Parent `1EEBkHidmn6PrXj9ib0thApFSqmgU9QSv`. Subfolder IDs (use `https://drive.google.com/embeddedfolderview?id=<id>#list` to enumerate — static HTML; the `/drive/folders/` view is JS-only):

| Subfolder | Folder ID |
|---|---|
| Agendas | `1bYGd-3jyVsNPFpQfbQeipHqr8xzWcivm` |
| Agendas-City Council | `1jCLlNKyu1yGkYyefk0YM6cPG3_d90unz` |
| CC Presentations | `1_G62ScIQlKkQLUshlg1JlHLR8Un48UKW` |
| Meeting Recordings | `1ZGrcVHGphcST_-ctwDdwRH5e0eqmrz1w` |
| Minutes (boards/commissions — 19 subfolders: Planning Comm, Board of Adj, CARE, Cultural Arts, …) | `1FvwLsetE7QEgIXj3rS5jViumjMuXGHyD` |
| **Minutes-City Council** | `1eNNpurKDzW6YkTehj0mUBskkORO-FAF4` |
| Training items | `1_BBeW022ST2V8uJTdWkmefDw8sIOgR7x` |

- **Minutes-City Council** is organized into **year folders**: ranges `1919-1962`, `1963-2000`, `2001-2017`, then individual `2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026`. **Earliest 1919, latest 2026** (2026 folder modified Jan 21, 2026 → current). Per-file naming inside year folders not yet enumerated (likely PDF; enumerate via each year folder's `embeddedfolderview`).
- Download a known file: `https://drive.google.com/uc?export=download&id=<fileId>`.
- For 2020+ scope: pull year folders **2020–2026** (each via its own folder ID from `embeddedfolderview` on `1eNNpurKDzW6YkTehj0mUBskkORO-FAF4`).
- "Agendas-City Council" (`1jCLlNKyu1yGkYyefk0YM6cPG3_d90unz`) = the place to hunt agenda **packets** for written-comment/correspondence attachments (see §3).

---

## Retrieval plan (recommended)

1. **Minutes (born-digital PDFs):**
   - **Primary:** Google Drive "Minutes-City Council" folder — enumerate via `embeddedfolderview`, harvest each PDF's file ID, download `https://drive.google.com/uc?export=download&id=<fileId>`. `pdftotext -layout`.
   - **Gap-fill / pre-2021:** Utah PMN — find Orem City Council body id, walk notices, pull `…/pmn/files/<id>.pdf`.
   - **Cross-index dates** against CivicClerk `Events` (categoryName='City Council', paginate via `$skiptoken`) to get the canonical meeting list + YouTube video ids + `agendaId` (for the HTML agenda / structured items).
   - Optional structured votes: probe `GetMeetingItemMinutesVotes(id)` per council event — if populated, it's a cleaner vote source than PDF parsing.
2. **Votes:** parse roll-calls from minutes PDFs ("Those voting aye:/nay:" + mover/seconder). Normalize member name spellings. Cross-check tallies vs `GetMeetingItemMinutesVotes` where available.
3. **Public comments:** (a) scan CivicClerk events for `publicCommentsEnabled:true` and per-event published files named comment/correspondence (`GetEventFile`/`GetAttachmentFile`); (b) open a few Google Drive "Agendas-City Council" packets for "written comments received". Only after both + transparency portal come up empty → record verdict in AVAILABILITY.md.
4. **Elections:** download 2021 + 2025 precinct SOVC CSVs (URLs above); for 2023 recover precinct data (see risk) else fall back to the rollup PDF + state portal dashboard. Subset to Orem Mayor / Orem City Council columns. Store under `~/Desktop/utah-elections-archive/counties/utah`.
5. **Geo:** build precinct lookup from UGRC VistaBallotAreas (CountyID=25, Orem precincts) + Orem municipal boundary; no district layer.

### Recommended order
1) Minutes via Google Drive + PMN  2) CivicClerk Events index + structured votes probe  3) Vote extraction  4) Public-comment hunt (CivicClerk API + packets)  5) Elections CSVs  6) GIS precinct/boundary tool.

---

## Risks / blockers

- **CivicClerk file slots empty:** minutes/agendas are NOT in `minutesFile`/`agendaFile` — they're HTML web agendas + PDFs on Google Drive. Don't rely on the CivicClerk API for the minutes PDFs themselves.
- **CivicClerk SPA is JS-only:** WebFetch on `oremut.portal.civicclerk.com/...` returns nothing; everything must go through the `oremut.api.civicclerk.com/v1/` OData API (15/page, follow `$skiptoken`; avoid `$select`+`$orderby asc` → 500).
- **Google Drive is JS-rendered:** folder/file enumeration may need `embeddedfolderview`; download counts/quotas possible if bulk-pulling.
- **2023 election precinct data = PDF rollup only** (no precinct SOVC CSV). Same blocker Provo hit. Recovery options: (a) Utah state portal `electionresults.utah.gov` 2023 dashboard; (b) request CSV from Utah County Clerk; (c) parse the rollup PDF (city-level, not precinct). Orem council results recoverable at city level regardless.
- **Public comments unproven:** feature exists in CivicClerk but `publicCommentsEnabled:false` on samples; publication-back unconfirmed. May end up "in-person speaker log only" if no written archive surfaces.
- **Name-spelling drift** in minutes (Millet/Millett, Debby/Debbie, Macdonald/MacDonald) → normalization required.
- **Precinct-code namespaces** differ (SOVC `AF##`/`25xxNN` vs UGRC precinct codes vs Orem `OR3xx`) — reconcile before building the lookup.
- **Combined work-session + regular meeting** in one minutes doc per day — handle as one file; some days may also have separate docs.
