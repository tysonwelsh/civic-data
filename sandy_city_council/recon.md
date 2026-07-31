# Sandy City, Utah — Civic Data Recon

City: **Sandy**, Salt Lake County, Utah. Form of government: **Council–Mayor** (strong
mayor; council is the legislative branch). Council office: 10000 Centennial Parkway,
Sandy UT 84070.

Recon date: June 2026. Focus window: **2020–present**.

---

## 1. Council meeting minutes

**Vendor:** Granicus **Legistar** (footer/logo references `granicusops.com`).
**Host:** `https://sandyutah.legistar.com`

### Key pages
- Calendar (meetings + agenda/minutes links): `https://sandyutah.legistar.com/Calendar.aspx`
- Legislation search: `https://sandyutah.legistar.com/Legislation.aspx`
- Body page (City Council): `https://sandyutah.legistar.com/MainBody.aspx`
- Members: `https://sandyutah.legistar.com/People.aspx`
- City landing page: `https://sandy.utah.gov/1204/City-Council`

### Bodies on the calendar
Board of Adjustment, CDBG Committee, **City Council**, Community Development,
Planning Commission. Selectable years **2015–2026**.

### Minutes retrieval pattern (CONFIRMED working)
Legistar serves minutes as **born-digital, text-layer PDFs** via:
```
https://sandyutah.legistar.com/View.ashx?M=M&ID=<meetingId>&GUID=<guid>
```
- `M=M` = **Minutes** (this is the MINUTES-only doctype — the disk-lesson target).
- `M=MADA` = accessible/ADA minutes variant (same content).
- `M=A` = Agenda; `M=F` = a File/legislation doc; `M=AP`/packets exist separately.
  → Take **only `M=M`** to get minutes (not agendas, not giant packets).

The `<meetingId>`+`<guid>` pairs are harvested from the **Calendar.aspx HTML**
(each City Council row with a Minutes PDF icon links to a `View.ashx?M=M&...` URL).

**Confirmed example (2026-06-02 regular meeting):**
`https://sandyutah.legistar.com/View.ashx?M=M&ID=1371413&GUID=E0F5CC1A-526D-4C4E-A6DD-5AB5D4D53CA0`
**Confirmed older example (search-surfaced minutes doc):**
`https://sandyutah.legistar.com/View.ashx?M=M&ID=1264612&GUID=43BB31FF-05C5-4284-AC5B-3E420DCB1E84`

### Legistar Web API — present but NOT useful for minutes files
`https://webapi.legistar.com/v1/sandyutah/events` returns JSON events
(`EventId`, `EventDate`, `EventTime`, `EventBodyName`, `EventMinutesStatusName`
= Draft/Final, `EventAgendaFile`, `EventMinutesFile`). **`EventMinutesFile` is
`null` across events** — the API does not expose the minutes PDF URLs for this
client. So the API is good for *enumerating meetings + minutes status*, but the
actual PDFs must come from the **Calendar.aspx `View.ashx?M=M` links** (scrape route).

### Format / coverage
- **Format:** born-digital, clean text-layer PDF (NOT scanned). `pdftotext`/Read
  parses cleanly. (Note: the WebFetch small-model misreported it as "scanned" —
  direct PDF read confirms clean born-digital text with selectable layout.)
- **Minutes years:** calendar offers 2015–2026; minutes for **2020–present**
  confirmed present (2020–21-era minutes GUIDs surfaced in search; recent months
  have Minutes links). Recent weeks may show *Draft* status until approved
  (approval happens via a later "Approval of the … Draft Minutes" consent item).
- **Pre-2020 / gaps fallback:** Utah Public Notice site mirrors Sandy agendas
  (`https://www.utah.gov/pmn/` — e.g. `https://www.utah.gov/pmn/files/570621.pdf`),
  useful if a year/file is missing from Legistar.

### Meeting cadence
- **Weekday:** **Tuesday**, 5:15 PM, Council Chambers, City Hall.
- **Frequency:** roughly **weekly** (June 2026 had council meetings 6/2, 6/9,
  6/16, 6/23, 6/30). Not every weekly meeting produces formal voting minutes —
  some are work sessions; the formal meeting that produces minutes is the one with
  the `M=M` doc.

### Roll-call votes in minutes — CONFIRMED YES (rich)
The 2026-06-02 minutes contain full recorded votes with **mover, seconder, and
per-member name lists**, including a genuinely **contested** vote:

- Item 4 (Ordinance 26-48, Communications Dept): *"A motion was made by Marci
  Houseman, seconded by Kris Nicholl … carried by the following roll call vote:*
  **Yes: 5** — Kris Nicholl, Marci Houseman, Cyndi Sharkey, Brooke Christensen,
  Brooke D'Sousa; **No: 2** — Alison Stroud, Aaron Dekeyzer; Nonvoting: 0."
- Item 2 (Resolution 26-60C): mover Dekeyzer / seconder Christensen, **Yes: 7**.
- Item 5 (D'Sousa budget proposal): mover D'Sousa / seconder Houseman, **Yes: 7**.
- Consent Calendar: "approved … by a unanimous voice vote" (no per-member names
  → `names_recorded:false`).

**Vote phrasing variants observed (for the parser):**
- `Yes: N - <names>` / `No: M - <names>` / `Nonvoting: K` (Legistar tabular block).
- `Yes:`/`No:` with name lists stacked one-per-line.
- `"carried by a unanimous voice vote"` (tally-only, no names).
- `"Item approved."` (consent items, no recorded vote).
- Attendance: `Present: 7 - <7 council member names>` (drives the absent set).

**Mayor does NOT vote** — the Mayor appears only in a separate "Mayor's Report"
and as "the Mayor stated support…" in discussion; never in the Yes/No tallies.
7 council members vote; max tally is 7.

---

## 2. Council structure

- **4 district seats + 3 at-large seats = 7 council members.** Council elects its
  own Chair (currently Cyndi Sharkey, who presides — the Mayor does not chair).
- **Mayor does NOT vote** on the council (separate executive; Council–Mayor form).
- **Terms:** 4-year terms, staggered (district seats and at-large seats elected in
  alternating odd-year cycles — confirmed by SLCo archive showing District 1/3 in
  some years and District 2/4 + At-Large in others).

### Current members (from 2026-06-02 minutes header — authoritative)
| Seat | Member |
|---|---|
| District 1 | Brooke Christensen |
| District 2 | Alison Stroud |
| District 3 | Kris Nicholl |
| District 4 | Marci Houseman |
| At-large | Aaron Dekeyzer |
| At-large | Brooke D'Sousa |
| At-large | Cyndi Sharkey (Council Chair) |

- **Mayor:** Monica Zoltanski (elected Nov 2021; per KSL coverage). Confirm current
  mayor on `https://sandy.utah.gov/` before publishing.
- Members page (bios/seat): `https://sandy.utah.gov/569/Council-Members`
- City directory: `https://sandy.utah.gov/306/City-Directory`

---

## 3. Public comments

**Genuine written/online public comments: UNCLEAR → likely NOT separately published.**

What the minutes contain is the **General Citizen Comment Period** + per-item
"Public comment opened/closed" sections — but these are **clerk paraphrases of
in-person speakers** (third-person: *"Darrin Butler … shared … He also mentioned …"*,
*"Lori Wilson … stated …"*, *"Pat Jones thanked the Council"*). Per
`extraction_standards.md`, these do **NOT** count as genuine public comments — at
most a `minutes_speaker_log.csv`, clearly labeled.

Hunt order — leads to chase before concluding unavailable:
1. **Agenda-packet attachments** ("written comments received" / "correspondence")
   — Legistar attaches per-item PDFs (`View.ashx?M=F&ID=…`). The 6/2 minutes show
   only staff memos/ordinances as attachments, no "correspondence" bundle, but
   other meetings (esp. zoning/budget public hearings) may carry emailed comments.
   **Check public-hearing-heavy meetings' packets for a "correspondence" item.**
2. **No dedicated eComment / Open City Hall portal found** — Sandy's Legistar does
   not advertise a Granicus eComment/Speak-Up portal; no comment-submission URL
   surfaced. Worth a Wayback check of `sandy.utah.gov` council pages.
3. **No standalone published-comments page** (unlike SLC weekly PDFs / St. George
   `public_comments.php`) found on `sandy.utah.gov`.
4. Records/transparency archive: not yet located.

**Submit mechanism:** General Citizen Comment is in-person/live (the 6/2 minutes
note a remote commenter "had technical issues" → there is some remote/online
participation, possibly via the meeting video platform, but no written-comment
intake URL was found). **Do not yet conclude unavailable** — packet correspondence
attachments are the most promising remaining source.

---

## 4. Elections

- **Run by:** **Salt Lake County Clerk.**
  Results: `https://www.saltlakecounty.gov/clerk/elections/election-results/`
- Sandy election info page: `https://sandy.utah.gov/337/Elections`
  Results page: `https://sandy.utah.gov/485/Results` (links back to county).
- **District-based:** YES — council elected by **District 1–4** + **At-Large**
  seats (confirmed in both minutes and county SOVC contest names).

### Existing local archive — Sandy IS present
`~/Desktop/slco-election-archive/` (README + `manifest.csv` +
`data/municipal_results_long.csv`). Sandy municipal contests already normalized:
- Distinct Sandy contests in the tidy data include: **SANDY CITY COUNCIL DISTRICT
  1/2/3/4**, **SANDY CITY COUNCIL AT-LARGE**, **SANDY (CITY) MAYOR**, plus
  council seats 2/4 in some years.
- Municipal years covered (general): 2007, 2009, 2011, 2013, 2015, 2017, **2021,
  2023, 2025** (+ primaries 2013, 2017, 2023, 2025). Raw also holds a
  **2017 Sandy Council 3 recount** and a **2021 General Sandy recount** PDF.
- Tidy table: `data/sovc_long.*` / `data/municipal_results_long.csv`
  (columns: year, election_type, contest, precinct, candidate, votes, …).
- **2019** municipal general is normalized but the **2019 municipal primary**
  ("Family B" numbered-sheet layout) is raw-only / not yet parsed — a gap if a
  2019 Sandy primary race matters.

→ For Sandy elections, **reuse the existing archive** rather than re-downloading;
just filter `municipal_results_long.csv` for `contest LIKE 'SANDY%'`.

---

## 5. GIS

- **City council-district FeatureServer/MapServer EXISTS (preferred over deriving
  from precincts):**
  `https://gis.sandy.utah.gov/arcgis/rest/services/Common/City_Council_Districts/MapServer`
  - **Layer 0 = "Districts"** (polygon). Fields: `OBJECTID`, `City_Counc`,
    **`Name`** (= "District 1".."District 4"), `Council_Member`, `Link_to_Photo`,
    `Link_To_Bio`, `Shape`. **Query supported** (JSON/geoJSON/PBF, maxRecord 1000).
  - **Layer 1 = "At-large"** (polygon) — the at-large coverage area.
  - Query endpoint:
    `…/City_Council_Districts/MapServer/0/query?where=1=1&outFields=*&f=geojson`
  - Note: this is a **MapServer** (not a FeatureServer), but it exposes
    `Query`/`Map`/`Data` capabilities — geojson export works for an address→district
    tool. SRID 102743 (state-plane); reproject to 4326 for web.
  - GIS portal: `http://gis.sandy.utah.gov/` ; apps:
    `http://gis.sandy.utah.gov/WebApplications/gismaps.html`
- **UGRC** statewide layers: `https://gis.utah.gov/` — VistaBallotAreas
  **CountyID = 18** (Salt Lake County) for precinct-based fallback.
- Precinct geometry also already in the archive:
  `~/Desktop/slco-election-archive/geo/slco_precincts_current.gpkg`
  (join field `PrecinctID`).

---

## Retrieval plan (recommended order)

1. **Enumerate meetings** — pull `Calendar.aspx` HTML for each year **2020→2026**
   (the year filter is a server postback; drive it via the `Calendar.aspx` request
   with the year viewstate, OR scrape each year's rendered page). For each **City
   Council** row, capture the `View.ashx?M=M&ID=…&GUID=…` minutes link + date +
   minutes status. (Cross-check meeting list against
   `webapi.legistar.com/v1/sandyutah/events` for completeness, since the API gives
   clean `EventDate`/`EventBodyName`/`EventMinutesStatusName` even though it lacks
   the file URL.)
2. **Download minutes PDFs** (`M=M`) → `raw/minutes/<year>/`. Use a browser
   User-Agent. Skip agendas (`M=A`) and packets.
3. **PDF → markdown** (text layer is clean). Filename:
   `minutes/<year>/<week-monday>/<YYYY-MM-DD>_city-council.md`.
4. **Extract votes** — parse the `Yes: N - …` / `No: M - …` / `Nonvoting` blocks +
   mover/seconder line; handle "unanimous voice vote" (names_recorded:false) and
   "Item approved" consent items; attendance from `Present: 7 - …`. Mayor never in
   tallies. Rebuild `all_votes.csv`.
5. **Comments** — for each public-hearing/zoning meeting, fetch the agenda packet /
   item attachments (`M=F`/packet) and look for "correspondence"/"written comments
   received" bundles → genuine comments. Wayback-check `sandy.utah.gov` council
   pages for any eComment portal. Build `minutes_speaker_log.csv` from the
   paraphrased speaker sections (clearly labeled NOT genuine comments).
6. **Elections** — filter the existing `~/Desktop/slco-election-archive` for
   `SANDY%` contests; no re-download needed. Re-run its `build_manifest`/`download`
   only if a 2026 Sandy race posts.
7. **Geo** — query the city `City_Council_Districts` MapServer layers 0+1 to
   GeoJSON, reproject to 4326, build the address→district lookup. Fallback to
   UGRC VistaBallotAreas (CountyID 18) only if the city layer is unavailable.

---

## Risks / blockers

- **Calendar year navigation via WebFetch fails** — `Calendar.aspx?M=&Y=` query
  params don't drive the JS/postback time filter through WebFetch (it kept
  returning the current period). The retrieval scraper must POST the ASP.NET
  viewstate/year selection or render the page, OR lean on the Legistar **events
  API** to enumerate and then map EventIds → calendar minutes links. Mitigated:
  the `View.ashx?M=M&ID=…&GUID=…` pattern itself is confirmed and stable.
- **Legistar API omits `EventMinutesFile`** for this client → cannot get minutes
  PDFs straight from JSON; must harvest links from Calendar HTML. (API still good
  for the authoritative meeting list + Draft/Final status.)
- **WebFetch small-model misjudged the PDF as "scanned" and found "no votes"** —
  WRONG. Direct PDF read shows clean born-digital text with full roll-call votes.
  Lesson: read Sandy minutes PDFs directly, don't trust the summarizer's verdict.
- **Draft vs approved minutes** — recent meetings post as Draft; keep them, note
  status; an approved version may replace later.
- **Public comments** — genuine written comments not yet located; verdict pending
  the packet-correspondence + Wayback checks (do not declare unavailable yet).
- **2019 municipal primary** Sandy results unparsed in the archive (Family-B
  layout) — minor gap.
- **GIS is MapServer, not FeatureServer** — fine (Query enabled), but confirm
  geometry export precision; reproject from SRID 102743.

---

## Key URLs (quick index)
- Legistar calendar: `https://sandyutah.legistar.com/Calendar.aspx`
- Minutes doc pattern: `https://sandyutah.legistar.com/View.ashx?M=M&ID=<id>&GUID=<guid>`
- Legistar events API: `https://webapi.legistar.com/v1/sandyutah/events`
- Council members: `https://sandy.utah.gov/569/Council-Members`
- Elections: `https://sandy.utah.gov/337/Elections` · results `https://sandy.utah.gov/485/Results`
- County results: `https://www.saltlakecounty.gov/clerk/elections/election-results/`
- District GIS: `https://gis.sandy.utah.gov/arcgis/rest/services/Common/City_Council_Districts/MapServer`
- Local election archive: `~/Desktop/slco-election-archive`
- PMN fallback: `https://www.utah.gov/pmn/`
