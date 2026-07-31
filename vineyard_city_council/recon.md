# Vineyard, Utah — Civic Data Recon

City of Vineyard, Utah County. Incorporated as a **town in 1989**; population lingered <200 for ~20 years, then exploded with redevelopment of the former Geneva Steel site: 139 (2010 census) → ~3,195 (2015) → 12,543 (2020 census) → ~22,000+ (2026). One of the fastest-growing cities in the U.S. in the 2010s. **Practical consequence: meaningful council records only exist from ~2014 onward** (and the body was the "Town Council" until it became a city). This is a short-history, single-portal city.

Recon date: June 2026.

---

## 1. Council meeting minutes

**Vendor: CivicClerk (CivicPlus).** Two related hosts:
- **Public portal (JS UI):** `https://vineyardut.portal.civicclerk.com/`
- **OData API (the workhorse):** `https://vineyardut.api.civicclerk.com/v1/` — live, returns OData v4. Entity set is **`Events`** (NOT `Meetings/GetMeetings`).
- **Legacy CivicClerk file host (SuiteOne):** `https://vineyardut.suiteonemedia.com/` — older meeting browser; `/event/?id=<N>` pages with `/event/GetAgendaFile/`, `/event/GetAgendaPacketFile/`, `/event/GetMinutesFile/` patterns. Superseded by the API host above; use the API.

Official city landing page that points to the portal:
- `https://www.vineyardutah.gov/government/agenda_minutes___public_notice.php`
- Annual meeting schedule: `https://www.vineyardutah.gov/government/annual_meeting_schedule.php`

### CivicClerk API specifics (verified working)
- Service doc / entity sets: `GET https://vineyardut.api.civicclerk.com/v1/` → Events, Meetings, EventCategories, EventsMedia, Search, Sections, Settings, Subscriptions.
- `$metadata`: `GET https://vineyardut.api.civicclerk.com/v1/$metadata` (EDMX, confirms schema).
- **List meetings:**
  `GET /v1/Events?$filter=categoryName eq 'City Council'&$orderby=startDateTime desc&$top=N`
  (URL-encode the space in `City Council` and the `$`). Also category `'Town Council'` for 2014 records, and `'Planning Commission'`, `'Boards and Commissions'`, `'General'`.
- Each Event has a **`publishedFiles`** array; entries have `fileId`, `type` (`Agenda`, `Agenda Packet`, `Minutes`), `name`. (Older `agendaFile`/`minutesFile` scalar objects are usually empty `id:0` for recent records — rely on `publishedFiles`.)
- **Download a file by id** (both verified HTTP 200):
  - Clean text: `GET /v1/Meetings/GetMeetingFileStream(fileId=<N>,plainText=true)` → `text/plain` (born-digital text layer; excellent quality).
  - Original PDF: `GET /v1/Meetings/GetMeetingFileStream(fileId=<N>,plainText=false)` → `application/pdf`.
  - Example verified: minutes fileId **3065** (5/5/2026 CC Work Meeting) returned clean 180-line text and a 4-page PDF.
- Total Events in portal: **1,432** (incl. future scheduled placeholders out to 2030 and all bodies).

### Minutes coverage (verified by sampling `publishedFiles` for type=Minutes)
- City/Town Council events present from **2014** (earliest event id 194, "Town Council Meeting", 2014-01-08).
- Minutes files present with strong coverage by year (sampled, ~15 council events/yr):
  - 2015: 13/15 have Minutes · 2018: 12/15 · 2020: 11/15 · 2022: 13/15 · 2024: 12/15.
- **Effective minutes range: ~2015–present** (a few early/very-recent meetings lack approved minutes). Agendas/packets often present even where minutes aren't.

### Format / votes
- Minutes are **born-digital text-layer PDFs** → `plainText=true` gives clean text. No OCR needed.
- **Roll-call votes ARE in the minutes**, with mover, seconder, and per-member name lists. Verified example (5/5/2026):
  > "Motion: Council Member Wood motioned to approve the Consent items... Council Member Nair seconded the motion. **Yes:** Council Members Holdaway, Lauret, Nair, and Wood. **No:** none. **Absent:** Council Member McCumber. Motion Passed 4-0."
  Format uses **Yes / No / Absent** (not "Aye/Nay"). Normalize accordingly. Attendance "Present/Absent" lists at top of each minutes doc.

### Meeting cadence / weekday
- **City Council meets Wednesdays** (per portal location notes: "Wednesday at 7:00 PM, City Council Chambers, 125 South Main Street"). NOTE: actual 2026 minutes show meetings on varying days/times (e.g., a Tuesday work meeting, midday work sessions). The city holds **both "City Council Meeting" (regular)** and **"City Council Work Meeting"** event types — handle both, one file each.
- Roughly **two council meetings/month** (regular + work), ~15 council-category events/year historically.

### Backup source — Utah Public Notice (PMN)
- Vineyard City Council public body: **`https://www.utah.gov/pmn/sitemap/publicbody/530.html`** (body id **530**).
- PMN attaches **minutes PDFs directly** with stable file URLs, e.g. `https://www.utah.gov/pmn/files/1124513.pdf` (1/10/2024 CC Final Minutes). Use PMN as fallback for any year the CivicClerk API is missing, or to cross-check. (Note: large packets can exceed WebFetch's 10 MB limit — `curl` to disk, then read.)

---

## 2. Council structure

- **At-large**, non-district. (Small town; UCA six-member-council form.)
- **History of size:** Originally Mayor + 4 council (5-member council form). Nov 2024 ballot **Proposition 10** (~74% yes) changed the form of government to a **"six-member council"** — i.e., **Mayor + 5 council members**, effective Jan 2026. Mayor chairs meetings and votes (UCA six-member form mayor is a voting council member). The city site lists Mayor + 5 councilmembers.
- **2025 election** elected **3 at-large seats** to 4-year terms, except one seat to a 2-year term (to stagger the new sixth seat).

### Current officials (took office Jan 2026; from city site)
- **Mayor:** Zack Stratton (term 2026–Dec 31 2029)
- Council:
  - David Lauret (2026–2029)
  - Jacob Wood (2026–2029)
  - Parker McCumber (2026–2027)
  - Ezra Nair (2026–2027) — appointed Nov 2025 to replace Sara Cameron (resigned)
  - Jacob Holdaway (2024–2027)
- Source: `https://www.vineyardutah.gov/government/city_council2.php`
- Terms staggered (some to 2027, some to 2029), 4-year terms standard.
- **Earliest records:** town incorporated 1989; usable council records ~2014/2015 (CivicClerk) — pre-2014 likely sparse/nonexistent online (town had <600 residents).

---

## 3. Public comments (genuine written/online)

**Verdict so far: likely NO dedicated published written-comment archive; UNCLEAR pending packet inspection.**
- Minutes "PUBLIC COMMENTS" sections are **clerk paraphrases of in-person speakers** → these are meeting-record notes, **NOT** genuine public-submitted written comments (per extraction_standards). Do not put in `all_comments_clean.csv`; if captured, → `minutes_speaker_log.csv`.
- **Submission channel is plain email:** minutes state "Public comments can be submitted ahead of time to **robinr@vineyardutah.gov**." No public eComment/Open City Hall portal surfaced.
- CivicClerk supports eComment (`publicCommentsEnabled` field exists on Events) but sampled CC meetings have it **false** — Vineyard does not appear to use the eComment feature.
- **Most promising remaining source: Agenda Packets** — CivicClerk `publishedFiles` type **`Agenda Packet`** (download via same `GetMeetingFileStream(fileId=...)`). These frequently bundle emailed/written "correspondence received." Must inspect a sample of packets for a "written comments received" / "correspondence" section before concluding unavailable.
- Also check: city Document Center (20,266 docs) linked from the agenda/minutes page; and PMN agenda packets.
- Submit/where for record: written comments go to City Recorder Robin Bond (`robinr@vineyardutah.gov`); no public web archive of them found.

---

## 4. Elections — run by Utah County

- **Source portal:** `https://vote.utahcounty.gov/results/<year>` → redirects to **Enhanced Voting** backend `https://electionresults.utah.gov/results/public/utah-county-ut/...` (same vendor/source as Provo & Orem).
- **Existing local archive scaffold present:** `~/Desktop/utah-elections-archive/counties/utah` (has `data/ geo/ maps/ raw/ scripts/ README.md`). Reuse it.
- **Vineyard contests by cycle:**
  - 2019: Council Seat 1, Seat 2 (Vineyard + Payson were first RCV cities)
  - 2021: council seats (RCV)
  - 2023: Seat 1, Seat 2 (RCV)
  - 2025: Mayor + 3 council seats (traditional, with Aug 12 2025 primary)
- **RANKED-CHOICE VOTING caveat (important for parsing):** Vineyard used **RCV in 2019, 2021, 2023**. RCV results are visualized at **rcvis.com** (e.g., `https://rcvis.com/v/2023-vineyard-city-council-20`, `.../-21`) and shown as multi-round tabulations on the Utah County results pages. **Vineyard voted in April 2025 to drop RCV** before the state pilot ended Jan 1 2026 → **2025 was a normal plurality election with a primary.** Vote-extraction logic must handle BOTH RCV rounds (2019/21/23) and standard plurality (2025).
- Certified results PDFs and result maps also downloadable per year from Utah County Elections (`https://www.utahcounty.gov/dept/clerk/elections/results.html`).
- Election info on city site: `https://www.vineyardutah.gov/government/elections.php`, `2025_election_information.php`, `ranked_choice_voting.php`.

---

## 5. GIS / precinct → district

- **At-large city → precinct→district mapping is trivial:** every Vineyard precinct maps to the single at-large "Vineyard City" jurisdiction. The geo tool only needs address → "in Vineyard? yes" → at-large council.
- **UGRC VistaBallotAreas (voting precincts), Utah County = CountyID 25:**
  `https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/VistaBallotAreas/FeatureServer/0`
  - Fields: OBJECTID, CountyID, VistaID, PrecinctID, SubPrecinctID, VersionNbr, EffectiveDate, AliasName, Comments, RcvdDate, GlobalID, Shape\_\_Area, Shape\_\_Length.
  - Utah County has **533** precincts total. **AliasName is NOT populated for Vineyard**, and VistaID is numeric (no "VIN"/"VY" prefix) — so **name matching fails**. Use a **spatial intersect** against Vineyard's municipal polygon instead.
- **Vineyard municipal boundary** (for the spatial clip / address test):
  `https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/UtahMunicipalBoundaries/FeatureServer/0` — query `where=UPPER(NAME)='VINEYARD'` (confirmed: NAME=Vineyard, FIPS 80420, COUNTYNBR 25). Use its geometry to (a) point-in-polygon an address and (b) `geometryType=esriGeometryPolygon` intersect VistaBallotAreas to enumerate Vineyard's few precincts.
- Vineyard is small → expect only a few precincts; exact count to be derived by spatial query during build.

---

## Retrieval plan (recommended order)

1. **Minutes (CivicClerk API)** — enumerate `GET /v1/Events?$filter=(categoryName eq 'City Council' or categoryName eq 'Town Council')&$orderby=startDateTime desc&$top=...` paging the full 2014–present range; for each event pull `publishedFiles` of type `Minutes`; download `GetMeetingFileStream(fileId=N,plainText=true)` (text) + `...plainText=false` (PDF to `raw/`). Save as `minutes/<year>/<week-monday>/<YYYY-MM-DD>_<slug>.md`. Keep regular vs work meetings separate.
2. **Vote extraction** — parse the clean text; motions have mover/seconder + **Yes/No/Absent** name lists + "Motion Passed X-Y". Normalize names; flag unanimous-without-names per standards.
3. **Public comments** — pull a sample of `Agenda Packet` files (same download endpoint) and scan for "correspondence/written comments received." If none across a representative sample, record verdict in AVAILABILITY.md (genuine written comments not published; only email submission to City Recorder). Put minutes speaker paraphrases in `minutes_speaker_log.csv` only.
4. **Elections** — reuse `~/Desktop/utah-elections-archive/counties/utah`; pull Vineyard contests for 2019/2021/2023/2025 from `electionresults.utah.gov`/`vote.utahcounty.gov`; handle RCV (rcvis links) for 2019/21/23 and plurality+primary for 2025; grab certified PDFs from Utah County.
5. **Geo** — query UGRC Municipal Boundaries for the Vineyard polygon; spatial-intersect VistaBallotAreas (CountyID=25) to list precincts; build address→{in Vineyard}→at-large mapping (no districts).
6. **PMN backfill** — only for any minutes year/gap the CivicClerk API can't supply (body id 530, direct `utah.gov/pmn/files/<id>.pdf`).

## Risks / blockers

- **Short history:** No meaningful council records before ~2014/2015; town had <600 residents. Don't expect 2020+ depth equivalent to a large city — dataset will be modest.
- **"Town" vs "City" naming:** 2014-era events use category `Town Council`; query both to avoid missing early records.
- **Meeting-day inconsistency:** nominal Wednesday, but real meetings land on various days/times (regular + work). Don't assume one weekday when slugging/dedup.
- **RCV in elections (2019/21/23):** results are multi-round tabulations (rcvis.com) — parsing differs from plurality. 2025 reverted to plurality. Build must branch.
- **Public comments:** no published written-comment archive found; only email-to-recorder. Final verdict pending agenda-packet inspection — may legitimately be "not published."
- **WebFetch 10 MB cap:** large agenda packets/older minutes (one PMN packet was ~80 MB) exceed it — always `curl` to disk then Read.
- **GIS name-matching fails** (AliasName empty for Vineyard) → must use spatial intersect; minor extra step but reliable.
- CivicClerk API is unauthenticated and stable today, but is the single point of dependency for minutes — PMN (body 530) is the mitigation.
