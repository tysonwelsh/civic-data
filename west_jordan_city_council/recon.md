# West Jordan, Utah — Civic Data Recon

**City:** West Jordan City, Salt Lake County, Utah
**Recon date:** 2026-06-24
**Scope of interest:** 2020–present
**Official site:** https://www.westjordan.utah.gov/ (note: `wjordan.gov` / `gis.wjordan.com` also referenced but the live CMS is `westjordan.utah.gov`)

---

## 1. Council meeting minutes

### Vendor & host
- **Vendor: PrimeGov** (same platform family as Salt Lake City).
- **Portal host:** `https://westjordan.primegov.com/public/portal`
- **Public website meetings hub:** https://www.westjordan.utah.gov/government/agendas/ and https://www.westjordan.utah.gov/citycouncil/meetings/

### API (confirmed working)
- **Meeting list (per year):**
  `GET https://westjordan.primegov.com/api/v2/PublicPortal/ListArchivedMeetings?year=YYYY`
  → JSON array. Confirmed working for **2020 (47 meetings), 2025 (76), 2026**.
  Each meeting object: `id` (meetingId), `title`, `dateTime`, `documentList[]`.
  Each `documentList` entry: `id` (doc id), `templateId`, `templateName`, `compileOutputType`, `publishStatus`, `meetingId`.
- **Minutes identification:** the `documentList` entry with **`templateName == "Minutes"`** (NOT "HTML Minutes" — WJ minutes are PDFs, unlike SLC's HTML). Agendas use `templateName` "Agenda" / "HTML Agenda" / "Complete Packet".

### Minutes document retrieval pattern (SOLVED — important)
The naive SLC pattern `/Portal/Meeting?meetingTemplateId=<id>` **fails** here (returns
PublishedDocumentError). The working pattern is:

```
GET https://westjordan.primegov.com/Public/CompiledDocument?meetingTemplateId=<TEMPLATE_ID>
```
where `<TEMPLATE_ID>` = the `templateId` field of the **"Minutes"** documentList entry
(NOT the doc `id`). This **302-redirects** to a time-limited Azure blob:
```
https://pgwest.blob.core.windows.net/westjordan/Meetings/<meetingId>/Minutes_<stamp>.pdf?sv=...&sig=...&se=<expiry>...
```
The SAS token is short-lived (~2 days), so **resolve + download in one pass** (curl `-L`).
Use a browser User-Agent. Verified live: meeting 939 (2026-01-13) templateId 4684 →
`.../Meetings/939/Minutes_20260219123701202.pdf` (200, application/pdf, 8 pp).

Endpoints that 404/error (do NOT use): `/Portal/Meeting?meetingTemplateId=`,
`/Public/Document?documentId=`, `/Public/CompiledDocument?meetingId=&compileOutputType=`,
`/Portal/MeetingPreview` (requires login).

### Coverage, format, cadence
- **Years of MINUTES available:** at least **2020 → present (2026)**, born-digital.
  (2020 list returns Minutes docs published retroactively in 2022; pre-2020 not confirmed
  via this API — would need PMN/Laserfiche fallback if older is wanted, but scope is 2020+.)
- **Format:** **born-digital, text-layer PDF** (clean `pdftotext -layout`; ~8 pp per regular
  meeting; 22 KB of text). *[Corrected 2026-07-02: not entirely OCR-free — early
  ≈2020–mid-2021 files end in scanned/OCR'd signature pages (cosmetic junk in the attest
  block) and the 2020-02-12 minutes are an OCR'd scan throughout ("occmTed"); motion/vote
  text verified clean. The original "NOT scanned. No OCR needed." claim was wrong for
  those files.]*
- **Cadence / weekday:** **2nd and 4th Tuesdays** of each month, 7:00 pm, City Hall 3rd floor,
  8000 S Redwood Road. (Annual schedule ordinance: https://www.westjordan.utah.gov/wp-content/uploads/2025/12/Ordinance-No.-25-61-Annual-Meeting-Schedule-for-2026-signed.pdf)
- Other bodies also in the same portal: Planning Commission, RDA (Redevelopment Agency),
  Municipal Building Authority, retreats. Filter to `title` containing "City Council" for council.

### Roll-call votes — CONFIRMED PRESENT in minutes
Opened 2026-01-13 minutes (templateId 4684). Per-motion the minutes record:
- `MOTION:` text (e.g. "Council Member Whitelock moved to APPROVE Resolution No. 26-001 …")
- mover + "Council Member Shelton seconded the motion."
- "The vote was recorded as follows:" then **per-member name lists**:
  ```
  YES:   Bob Bedore, Annette Harris, Zach Jacob, Chad Lamb, Kent Shelton, Kayleen Whitelock, Jessica Wignall
  NO:
  ABSENT:
  The motion Passed 7-0.
  ```
This is a clean, parseable roll-call format (YES / NO / ABSENT + tally + Pass/Fail).
Attendance ("COUNCIL:" / "STAFF:") is listed at CALL TO ORDER. Excellent for vote extraction.

---

## 2. Council structure

- **7 members: 4 district seats + 3 at-large.** 4-year terms (staggered; districts and at-large
  cycle in alternating odd-year municipal elections — confirm stagger from election archive below).
- **Mayor:** **Dirk Burton** (separately elected; presides? — minutes show the **Council Chair**
  (a rotating council member) chairs council meetings, with the Mayor listed under STAFF/attending.
  WJ uses a council-mayor form where the Mayor is not a voting council member at the dais for these
  motions — the 7 votes are the council members.)
- **Current members** (source: https://www.westjordan.utah.gov/citycouncil/councilmembers/):
  - District 1 — **Chad Lamb**
  - District 2 — **Bob Bedore** (Council Chair)
  - District 3 — **Zach Jacob**
  - District 4 — **Kent Shelton**
  - At-Large — **Annette Harris**
  - At-Large — **Kayleen Whitelock** (Past Chair)
  - At-Large — **Jessica Wignall** (Vice Chair)
- District map (city PDF): https://www.westjordan.utah.gov/wp-content/uploads/2022/05/WJ-District-Map.pdf
  Interactive lookup: https://west-jordan-city.maps.arcgis.com/apps/instant/lookup/index.html?appid=94254757a56e4e1fa35e2182dd1570a6
- Overview: https://www.westjordan.utah.gov/citycouncil/overview/

---

## 3. Public comments — genuine written/online comments

**Verdict: UNCLEAR / likely NOT published as a separate archive.** Hunt order results:

1. **Dedicated published-comments page:** none found. No equivalent of SLC's weekly
   public-comment PDFs or St. George's `public_comments.php`.
2. **eComment / Open City Hall portal:** **None.** Remote participation is **Zoom voice only**
   ("raise hand" to speak) — not a written eComment portal. (Source: "How To Participate In
   Public Comment" PDF, https://www.westjordan.utah.gov//wp-content/uploads/2025/04/How-to-Participate-in-Public-Comment.pdf)
3. **Written-comment intake (genuine, but publication unknown):**
   - **Email:** `CouncilComments@WestJordan.Utah.Gov` — "Written comments may be submitted
     before, during, or following a council meeting via email." (the most promising genuine-written channel)
   - **Comment card / back-of-card written comments** submitted in person to Council Office staff.
   - **24-hour comment line (voice):** 801-569-5052; general council email `council.office@westjordan.utah.gov`.
   These are genuine public-submitted writings, but **no public archive of them was found**. They may
   surface inside **agenda-packet "Complete Packet" attachments** (templateName "Complete Packet" in
   PrimeGov) as "correspondence received" — **NOT yet verified; this is the #1 thing to check next.**
4. **Records/correspondence archive:** none found on the public site.

**Important distinction:** the minutes' "PUBLIC COMMENT" / "Public Hearing — Comments" sections
are **clerk third-person paraphrases of in-person speakers** (e.g. "June Christiansen, West Jordan
resident, said she lived next to the subject property. She expressed support…"). Per
extraction_standards, these are **meeting-record notes, NOT genuine written public comments** — they
belong (if extracted at all) in a clearly labeled `minutes_speaker_log.csv`, never in
`all_comments_clean.csv`.

**Most promising URLs to chase for genuine written comments:**
- PrimeGov "Complete Packet" PDFs per meeting (check for "Correspondence"/"Written Comments Received"
  sections) — fetch via the same `CompiledDocument` pattern but with the **agenda-packet** templateId.
- A targeted **GRAMA records request** to `CouncilComments@WestJordan.Utah.Gov` would retrieve the
  emailed written comments if no public archive exists.

---

## 4. Elections (Salt Lake County)

- **Run by Salt Lake County Clerk.** Results portal:
  https://saltlakecounty.gov/clerk/elections/election-results/
  (also the brief's path saltlakecounty.gov/clerk/elections/election-results/)
- **Existing local archive: `~/Desktop/slco-election-archive`** — ALREADY HAS West Jordan races.
  - West Jordan present in `data/municipal_results_long.csv` and per-year municipal files for
    **2007, 2009, 2011, 2013, 2015, 2017, 2021, 2023, 2025** (normalized; 2019/2021 primary gaps
    noted in the archive README — 2019 municipal primary "Family B" layout unparsed; 2021 municipal
    primary PDF-only).
  - Caveat: WJ council contests appear in the normalized CSVs under **generic sheet names**
    ("Sheet50", "Sheet58", etc.) rather than a clean "WEST JORDAN CITY COUNCIL DISTRICT N" contest
    label — the contest text lives inside the rows; downstream agent should filter on contest strings
    containing "WEST JORDAN", not the sheet column. Spot-check the raw SOVC xlsx for exact contest names.
- **District-based vs at-large:** **Mixed** — WJ elects 4 district council seats by district and 3
  at-large seats citywide, staggered across odd-year municipal elections. So elections are **partly
  district-based** (the 4 district seats) and partly at-large. SLCo even maintains per-district
  precinct-results services for the contested district races (see GIS below, "West Jordan City Council 2/4").
- Re-running the archive pipeline (`build_manifest.py` → `download.py` → `normalize_sovc.py`) picks
  up any new WJ results; geometry via `fetch_geometry.py`.

---

## 5. GIS

- **UGRC VistaBallotAreas, CountyID = 18** (Salt Lake County) — the statewide voting-precinct /
  ballot-area layer; confirmed Salt Lake = CountyID 18 per the brief. Access via UGRC SGID /
  opendata.gis.utah.gov (`https://opendata.gis.utah.gov/`, search "VistaBallotAreas"). This is the
  canonical precinct layer to join to SLCo SOVC precinct results (PrecinctID join, same as the
  existing archive's `geo/` workflow).
- **City council-district boundary layers (West Jordan):**
  - City's own **WJ-District-Map PDF** (4 quadrant/districts, with population per district):
    https://www.westjordan.utah.gov/wp-content/uploads/2022/05/WJ-District-Map.pdf
  - City **Data Hub** (ArcGIS Hub): https://data-hub-west-jordan-city.hub.arcgis.com/ (has CityBoundary
    etc.; a clean 4-district FeatureServer was NOT directly located via search — check the hub catalog
    or the city GIS org `west-jordan-city.maps.arcgis.com`).
  - **Salt Lake County-hosted, race-specific** precinct-results feature services (owner `CBush@slco.org_slco`,
    host `services1.arcgis.com/DJP723NX3ukQ2LtF`):
    - `West_Jordan_City_Council_2/FeatureServer` (layer 241 = "precinct level results for the WJ City
      Council District 2 race in the 2023 election") — **election-results layer, not a clean district boundary.**
    - `West_Jordan_City_Council_4/FeatureServer` (District 4 results).
    - `2023_Primary_Election_Results/FeatureServer`.
    These are precinct-results overlays for the District 2 & 4 races, useful for mapping, but the
    authoritative council-district polygons are best taken from the city (WJ-District-Map / city GIS)
    or derived by dissolving VistaBallotAreas precincts to district assignment.
  - Address→district interactive lookup: https://west-jordan-city.maps.arcgis.com/apps/instant/lookup/index.html?appid=94254757a56e4e1fa35e2182dd1570a6
- **Boundaries available:** YES (city boundary + district map confirmed; clean 4-district vector
  layer needs one more dig in the city Data Hub / city ArcGIS org).

---

## Retrieval plan (recommended order for downstream agents)

1. **Minutes (PrimeGov).** For each year 2020→2026:
   `ListArchivedMeetings?year=YYYY` → keep meetings with `title` containing "City Council" →
   for each, take the `documentList` entry where `templateName=="Minutes"` → read its `templateId`
   → `GET /Public/CompiledDocument?meetingTemplateId=<templateId>` with browser UA and `-L` →
   follow the 302 to the Azure blob → save PDF to `raw/minutes/<year>/`. **Resolve+download in one
   pass (SAS token expires ~2 days).** PDFs are text-layer → `pdftotext -layout` or Read directly.
   Filename: `minutes/<year>/<week-monday>/<YYYY-MM-DD>_city-council.md`.
2. **Vote extraction.** Parse each minutes file for `MOTION:` blocks → mover/seconder →
   "The vote was recorded as follows:" YES/NO/ABSENT (+ ABSTAIN/RECUSE if present) → tally
   (`Passed 7-0`). Member-name normalization already easy (full names in YES list). Build `all_votes.csv`.
3. **Speaker log (NOT comments).** Optionally extract the "PUBLIC COMMENT"/"Public Hearing"
   speaker paraphrases into `public_comments/minutes_speaker_log.csv` with the required header note.
4. **Genuine written comments hunt.** Fetch a sample "Complete Packet" PDF per meeting (agenda-packet
   templateId via same CompiledDocument pattern); grep for "Correspondence"/"Written Comment". If
   none, record verdict in AVAILABILITY.md and note the `CouncilComments@WestJordan.Utah.Gov` GRAMA route.
5. **Elections.** Reuse `~/Desktop/slco-election-archive`; filter normalized municipal CSVs for
   "WEST JORDAN" contests (district + at-large council). Re-run pipeline only if newer results posted.
6. **GIS.** Join VistaBallotAreas (CountyID=18) precincts to SLCo SOVC for WJ council races; pull the
   city's 4-district polygons from the WJ Data Hub / WJ-District-Map for the address→district tool.

---

## Risks / blockers

- **Azure SAS expiry:** minutes blob URLs from `/Public/CompiledDocument` carry a ~2-day SAS token —
  cannot be cached/queued; resolve and download in the same run. (Re-resolve if a download fails.)
- **Bot filter:** PrimeGov occasionally needs a real browser User-Agent; without it some endpoints
  may behave oddly. Confirmed working with a Chrome UA via curl `-L`.
- **No HTML minutes:** unlike SLC, WJ minutes are PDFs — markdown comes from PDF text extraction, not
  the PrimeGov HTML-Minutes template. (Quality is high; born-digital.)
- **Pre-2020 minutes** not confirmed in PrimeGov (API returns 2020+); if older is ever needed, fall
  back to Utah PMN (`utah.gov/pmn`) — WJ posts there (a 386-pp agenda packet was found at
  utah.gov/pmn/files/1427719.pdf), or Laserfiche. Out of scope for 2020+.
- **Genuine written public comments:** no public archive located; likely only obtainable inside
  agenda packets or via a GRAMA request. Do not conclude "unavailable" until the Complete-Packet
  attachments are checked.
- **District-boundary vector layer:** the clean 4-district polygon FeatureServer was not pinned down;
  the SLCo "Council 2/4" services are election-results overlays, not boundaries. One more dig needed
  in the WJ Data Hub / `west-jordan-city.maps.arcgis.com` org, or derive by dissolving precincts.
- **Election CSV labeling:** WJ council contests sit under generic sheet names in the normalized
  archive — filter by contest text "WEST JORDAN", verify exact contest strings against raw SOVC.

---

## Key URLs (quick reference)

| What | URL |
|---|---|
| PrimeGov public portal | https://westjordan.primegov.com/public/portal |
| Meeting list API | https://westjordan.primegov.com/api/v2/PublicPortal/ListArchivedMeetings?year=YYYY |
| Minutes download (templateId) | https://westjordan.primegov.com/Public/CompiledDocument?meetingTemplateId=<templateId> |
| Agendas & minutes hub | https://www.westjordan.utah.gov/government/agendas/ |
| Council meetings info | https://www.westjordan.utah.gov/citycouncil/meetings/ |
| Council members | https://www.westjordan.utah.gov/citycouncil/councilmembers/ |
| How to participate (comment) PDF | https://www.westjordan.utah.gov//wp-content/uploads/2025/04/How-to-Participate-in-Public-Comment.pdf |
| Written comments email | CouncilComments@WestJordan.Utah.Gov |
| District map PDF | https://www.westjordan.utah.gov/wp-content/uploads/2022/05/WJ-District-Map.pdf |
| Address→district lookup | https://west-jordan-city.maps.arcgis.com/apps/instant/lookup/index.html?appid=94254757a56e4e1fa35e2182dd1570a6 |
| City Data Hub (ArcGIS) | https://data-hub-west-jordan-city.hub.arcgis.com/ |
| SLCo Council 2 results FS | https://services1.arcgis.com/DJP723NX3ukQ2LtF/arcgis/rest/services/West_Jordan_City_Council_2/FeatureServer |
| SLCo Council 4 results FS | https://services1.arcgis.com/DJP723NX3ukQ2LtF/arcgis/rest/services/West_Jordan_City_Council_4/FeatureServer |
| SL County election results | https://saltlakecounty.gov/clerk/elections/election-results/ |
| UGRC SGID open data | https://opendata.gis.utah.gov/ (VistaBallotAreas, CountyID=18) |
| Existing election archive | ~/Desktop/slco-election-archive (WJ races present 2007–2025) |
