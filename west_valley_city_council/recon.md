# West Valley City, Utah — Civic Data Recon

Recon date: 2026-06-24. Salt Lake County. Scope: 2020–present.
Official site: https://www.wvc-ut.gov/ (also reachable as westvalleycity.gov)

---

## 1. Council meeting minutes

**Portal vendor: Hyland OnBase — "OnBase Agenda Online"** (an OnBase Agenda Management module).
Self-hosted by the city on its own subdomain — NOT PrimeGov / Granicus / CivicPlus / Legistar / CivicClerk.

- Host domain: **`ob.wvc-ut.gov`**
- Landing page (city site): https://www.wvc-ut.gov/105/Agendas-Minutes
  - 302-redirects into the OnBase portal search.
- Portal search base: `https://ob.wvc-ut.gov/OnBaseAgendaOnline/Meetings/Search`
- Watch-online / video page: https://www.wvc-ut.gov/837/View-Online (YouTube live stream + Comcast Ch. 17)

### URL / query pattern (this is the key for retrieval)

Meeting search (returns a list of meetings + per-meeting agenda/minutes links):
```
https://ob.wvc-ut.gov/OnBaseAgendaOnline/Meetings/Search?dropid=11&mtids=109,110,111&dropsv=MM/DD/YYYY%2000:00:00&dropev=MM/DD/YYYY%2000:00:00
```
- `dropid` = the date-range dropdown selection (11 = custom range observed).
- `mtids` = comma-separated **meeting-type IDs**. Observed for City Council: `109,110,111`
  (City Council Regular + City Council Study; the portal also has Planning Commission,
  Board of Adjustment, etc. under other mtids — enumerate from the meeting-type dropdown).
- `dropsv` / `dropev` = range **start** / **end** datetime (URL-encoded `MM/DD/YYYY 00:00:00`).
- One calendar-year window at a time works well, e.g. 2020-01-01 → 2020-12-31 returned ~94 meetings (all types), ~40+ City Council.

Per-meeting document viewer:
```
/OnBaseAgendaOnline/Meetings/ViewMeeting?id=<MEETING_ID>&doctype=1   # AGENDA
/OnBaseAgendaOnline/Meetings/ViewMeeting?id=<MEETING_ID>&doctype=2   # MINUTES
```
Direct PDF download (pattern observed):
```
/OnBaseAgendaOnline/Documents/DownloadFile/<MeetingType>_<ID>_<DocType>_<Date>.pdf?documentType=<1|2>&meetingId=<ID>
```
**`doctype=2` / `documentType=2` = MINUTES; `doctype=1` = AGENDA.**

NOTE: `ob.wvc-ut.gov` returned **HTTP 403** to one WebFetch (a 2020 search variant) but **200** to others.
Likely bot/UA or referrer filtering. Retrieval should send a browser-like User-Agent and possibly
hit the city `wvc-ut.gov/105/...` redirect first to pick up any cookie. Not a hard blocker, but plan for it.

### Secondary / fallback source — Utah Public Notice Website (PMN)

State of Utah Public Meeting Notice site mirrors WVC agendas + minutes as PDFs. Very scrape-friendly, no 403.
- Public body page (City Council, body id 398): https://www.utah.gov/pmn/sitemap/publicbody/398.html
- Example minutes PDF (Feb 10 2026 Regular): https://www.utah.gov/pmn/files/1396745.pdf
- Files live at `https://www.utah.gov/pmn/files/<id>.pdf` — IDs discoverable by crawling the body page / notice pages.
- This is a strong **backup** for minutes if OnBase blocks; PMN retention typically covers recent years (verify back to 2020).

### Years of MINUTES available
- OnBase shows **2020 through present (2026)** with minutes attached to past meetings. Confirmed 2020 range returns meetings with `doctype=2` minutes; 2026 confirmed. Need to spot-check the earliest year with *minutes* (vs agenda-only) — likely 2020 or earlier.
- PMN is a parallel store for recent years.

### Format
- PDFs. The recent minutes are **scanned-but-with-a-good-text-layer** — `pdftotext -layout` produced **clean, well-structured text** (headers, member rosters, motions, full public-comment transcriptions). Effectively born-digital quality for extraction. Run OCR fallback only if a given file lacks a text layer.

### Meeting cadence
- **Tuesdays — 2nd and 4th Tuesday of each month.**
- Study Session 4:30 PM (Multipurpose Room); Regular Council Meeting 6:30 PM (Council Chambers, 3600 S Constitution Blvd).

### Recorded roll-call votes in minutes — YES (confirmed)
From Feb 10 2026 Regular minutes (https://www.utah.gov/pmn/files/1396745.pdf), verbatim example:

```
Councilmember Whetstone moved to approve Ordinance 26-03.
Councilmember Huynh seconded the motion.
A roll call vote was taken:
    Councilmember Wood          Yes
    Councilmember Whetstone     Yes
    Councilmember Harmon        Yes
    Councilmember Huynh         Yes
    Councilmember Christensen   Yes
    Councilmember Nordfelt      Yes
    Mayor Lang                  Yes
Unanimous.
```
Minutes contain: **mover, seconder, per-member Yes/No roll-call lists**, and a "Unanimous." / "The motion carried/failed" tally. Routine items use a "voice vote ... all members voted in favor." Excellent structured data for a votes table.

---

## 2. Council structure

- **7-member council**: **4 district seats + 2 at-large seats**, plus a separately-elected **Mayor** (who presides and votes — appears in roll calls).
  - "Every WVC resident is represented by four elected officials: Mayor, two Councilmembers At-Large, and their District Councilmember."
- **Term length: 4 years, staggered** (odd-year municipal elections; roughly half the council up each cycle).
- District boundaries codified at: https://westvalleycity.municipal.codes/Code/2-3-103 (Municipal Code §2-3-103, "Council Districts"). Boundaries last redrawn after the 2020 census (adopted March 2022).
- Members page: https://www.wvc-ut.gov/97/Members  (also /97/City-Council-Members)

### Current members (as of June 2026)
| Seat | Member |
|---|---|
| Mayor | Karen Lang |
| At-Large | Lars Nordfelt |
| At-Large | Don Christensen |
| District 1 | Tom Huynh |
| District 2 | Scott Harmon |
| District 3 | William (Will) Whetstone |
| District 4 | Cindy Wood |

Stagger (from election cycles, see §4): **At-Large + District 2 + District 4 + Mayor** elected in 2025; **(other) At-Large + District 1 + District 3** up in **2027**. (Note: a 2025 At-Large seat was decided by coin-toss/runoff per SL Trib — verify exact seat assignments per cycle when building.)

---

## 3. Public comments

**Published: YES — transcribed inside the minutes** (this is the primary, reliable source).
- The "PUBLIC COMMENT PERIOD" section of each Regular meeting's minutes contains **detailed paragraph summaries of each speaker by name** (e.g., Feb 10 2026: Dan Bell, Tiffany Andersson, Susann Andersson, Kimberly Sears — each with a full multi-sentence summary of their remarks). These are rich and attributable.
- No evidence of a separate eComment / Speak-Up / written-comment publication portal (no CivicPlus eComment, no Granicus). Agenda packets are in OnBase (`doctype=1`) and may contain attached written correspondence — worth a spot check, but the minutes are the dependable channel.

### How the public submits comment
- **In person / live during the Public Comment Period** at the 2nd/4th-Tuesday 6:30 PM Regular meeting (Council Chambers).
- Contact the **City Recorder's Office** (Nichole Camac, City Recorder, 801-963-3203) for agenda items; City Hall 801-966-3600.
- Meetings streamed on the city YouTube channel (https://www.wvc-ut.gov/837/View-Online).
- No dedicated online comment-submission form was found on /15/City-Council. Recommend a quick check of any "Contact Council" / email-the-council page before concluding none exists.

Most promising URLs:
- https://www.wvc-ut.gov/15/City-Council
- OnBase minutes (transcribed comments): see §1 pattern, `doctype=2`.

---

## 4. Elections

- **Run by Salt Lake County Clerk.** West Valley municipal elections are **odd-year** (2021, 2023, 2025, next 2027).
- County clerk results: https://www.saltlakecounty.gov/clerk/elections/election-results/  (also slco.org/clerk/elections/)
- City election info page: https://www.wvc-ut.gov/258/City-Election-Information
  - 2025 results archive link (city): https://westvalleycity.gov/Archive.aspx?ADID=3619
  - **2027** seats up: At-Large + District 1 + District 3 (confirms the stagger).
- WVC council is **district-based AND at-large** (mixed): district seats are voted only within the district; at-large seats are city-wide.

### Existing archive — `~/Desktop/slco-election-archive/`  (ALREADY HAS West Valley City races)
- README: tidy SOVC archive of SLCO Clerk results, **normalized 2006–2025** (~1,750 contests, ~2.9M rows), with `data/sovc_long.{csv,parquet}`, `data/elections.sqlite`, and `data/municipal_results_long.csv`.
- **West Valley City IS present**: `grep -ci "west valley" data/municipal_results_long.csv` → **26,046 rows**. Confirmed WVC contests by year:
  - 2007: Council #1, #3, At-Large; 2009: Dist 2, Dist 4, Mayor; 2013: At-Large, Dist 2, Dist 4, Mayor; 2015: At-Large, Dist 1, Dist 3; 2017: Dist 4, Mayor.
  - **2021 / 2023 / 2025**: rows present but **contest labels are `SheetNN` placeholders** (the archive's normalizer didn't extract contest titles for those years' file layout — a known parsing gap). The **vote data is there**; only the contest names need remapping for WVC's recent (2020+) races.
- Geometry: `geo/slco_precincts_current.gpkg` (join field `PrecinctID`); maps pipeline in `scripts/`.
- **Action for downstream**: rather than re-download county results, reuse this archive. For 2021/2023/2025 WVC contests, fix the `SheetNN` → contest-name mapping (cross-reference the raw SOVC spreadsheets in `raw/` and the county's posted results for those years).

---

## 5. GIS — precinct / district boundaries

### UGRC Vista Ballot Areas (precincts) — Salt Lake County CountyID = 18
- FeatureServer (already used by the slco archive's `scripts/fetch_geometry.py`):
```
https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/VistaBallotAreas/FeatureServer/0/query
  ?where=CountyID=18
  &outFields=PrecinctID,VistaID,CountyID,VersionNbr,EffectiveDate
  &outSR=4326&f=geojson
```
- This yields current SLCO precincts; **reuse `slco-election-archive/geo/slco_precincts_current.gpkg`** instead of re-fetching.

### West Valley City council districts (the 4 district boundaries)
- City code text: https://westvalleycity.municipal.codes/Code/2-3-103
- City GIS portal (ArcGIS Enterprise, self-hosted): https://gisportal.wvc-ut.gov/portal/...
  - District-finder ("Find your City Council District") Experience app:
    https://gisportal.wvc-ut.gov/portal/apps/experiencebuilder/experience/?id=16062a18d1394454b3ab718dcc6ae69e
  - Older web app viewer: https://gisportal.wvc-ut.gov/portal/apps/webappviewer/index.html?id=d077ce3988b34d9789face0bfc1eaa75
- City map gallery: https://wvc-ut.maps.arcgis.com/home/gallery.html and https://www.wvc-ut.gov/356/Maps
- **TODO for geo agent**: dig into `gisportal.wvc-ut.gov/portal/rest/services` to find the council-district polygon FeatureServer layer (the Experience app references one). If not exposed, derive districts by aggregating precincts (Vista areas) per the §2-3-103 descriptions, or digitize from a published district PDF map.

---

## Retrieval plan (recommended approach + effort)

1. **Council minutes (PRIMARY EFFORT — medium/high).**
   - Crawl OnBase `Search` per meeting-type=`109,110,111`, one year at a time, 2020→2026.
   - Parse the meeting list for `<MEETING_ID>`; download minutes via `ViewMeeting?id=...&doctype=2` (or the DownloadFile pattern, `documentType=2`).
   - Send a browser User-Agent; warm up via the `wvc-ut.gov/105/Agendas-Minutes` redirect to dodge the intermittent 403.
   - Extract text with `pdftotext -layout`; OCR only files lacking a text layer.
   - **Fallback: Utah PMN** (`utah.gov/pmn`, body id 398, files at `/pmn/files/<id>.pdf`) if OnBase blocks.
   - Effort: ~150–300 minutes docs (2nd/4th Tue × ~6 years, Regular + Study). Text quality is good.

2. **Roll-call votes (LOW once minutes in hand).** Regex the minutes text: `<Member> moved to ...`, `<Member> seconded`, then the `A roll call vote was taken:` block of `Member  Yes/No` lines, plus `Unanimous.`/`carried`/`failed`. Schema fits the SLC-style votes table directly. Member roster per meeting is in the "MEMBERS WERE PRESENT" header.

3. **Public comments (LOW).** Same minutes text — slice the `PUBLIC COMMENT PERIOD` section; each paragraph is one named speaker. No separate portal to scrape.

4. **Elections (VERY LOW — reuse).** Use `~/Desktop/slco-election-archive`. Filter `data/municipal_results_long.csv` / `elections.sqlite` for "WEST VALLEY". **Fix the 2021/2023/2025 `SheetNN` contest labels** by mapping to real WVC contests from `raw/` SOVC files + county posted results. No new downloads needed.

5. **Geo (LOW–MEDIUM).** Reuse SLCO precincts gpkg (Vista CountyID=18). Acquire WVC council-district polygons from `gisportal.wvc-ut.gov` REST services (or aggregate precincts per §2-3-103) to build an address→district tool.

## Risks / blockers
- **OnBase 403**: intermittent bot filtering on `ob.wvc-ut.gov`. Mitigate with UA + redirect warm-up; PMN is the backup. (Not fatal.)
- **Minutes earliest-year**: confirmed present 2020+; verify the earliest year that has *minutes* (not agenda-only) and whether any pre-2022 files are image-only (need OCR).
- **Archive contest-name gap (2021/23/25)**: WVC's recent races are stored as `SheetNN` in the existing slco archive normalizer — vote numbers exist but contest titles must be remapped. This is the main data-cleaning task for elections.
- **WVC council-district GIS layer** may not be openly exposed via REST; may require precinct-aggregation or digitizing a PDF map.
- **At-large seat / cycle assignment** ambiguity (2025 coin-toss runoff per SL Trib) — verify which specific At-Large seat is up 2025 vs 2027.
- **Mayor votes in roll calls** — Mayor Lang appears in Yes/No tallies; decide whether to count the mayor as a voting member in any analysis.
