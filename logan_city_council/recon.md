# Recon — Logan, Utah (Logan Municipal Council) civic-data repository

City of Logan, Cache County, Utah. ~52,000 residents (USU college town), largest city in
northern Utah. Council-mayor form of government (Utah Code Title 10, Ch. 3B, Part 2).
Scope: **2020–present**. This is a read-only source map, not a bulk download.

Recon date: 2026-06-26.

> Domain note: the city CMS answers on both `www.loganutah.gov` and `www.loganutah.org`
> (the `.org` is the legacy/redirect host). Page URLs below use `.gov`; document files
> resolve under either domain but ultimately live on the Revize file CDN
> `cms9files.revize.com/loganut/...`.

---

## 1. Council minutes — portal, format, votes

**Vendor / host:** Custom **Revize CMS** ("Powered by Revize"). No Granicus/Legistar/
PrimeGov/CivicClerk/Laserfiche. There is **no JSON API** — minutes are static PDF files
linked from year-by-year HTML listing pages. Per the portal playbook this is the "Revize
CMS (static files, no API)" pattern: scrape the listing pages for the minutes PDF links.

**Listing pages (HTML):**
- Minutes index: `https://www.loganutah.gov/government/city_council/minutes.php`
  (minutes listed by year, ~2008–2026).
- Agendas & packets by year, e.g.:
  `https://www.loganutah.gov/government/city_council/2023_council_agendas_and_packets.php`
  (each year has its own `YYYY_council_agendas_and_packets.php` page; 2026 page also
  reachable via the vanity link `go.loganutah.gov/2026councilpackets`).

**File host / URL pattern (PDFs):** documents are served from the Revize file CDN and
from the city domain. Observed real paths:
- `https://cms9files.revize.com/loganut/departments/admin/council/<FILE>.pdf`
  (e.g. the 2025 Candidate Guide: `.../council/2025%20CANDIDATE%20GUIDE%20-%20Updated.pdf`).
- Mirror via city domain: `https://www.loganutah.org/departments/admin/council/<FILE>.pdf`.
- **Filenames are human-typed and inconsistent** (spaces, mixed conventions). Examples:
  `AGENDA 2023January17.pdf`, `DRAFT Minutes 23January3.pdf`, plus short forms like
  `25December16.pdf`. Must distinguish "Minutes" from "AGENDA"/"Packet"/resolution files
  by the label/filename — do not mistake an agenda for minutes.

**Years of minutes:** listing advertises **2008–2026**; our window 2020–present is fully
covered. Recent meetings posted as "DRAFT Minutes" until approved (keep, note status).

**Format:** **Born-digital text-layer PDFs** (clean, parseable — `pdftotext -layout` or
Read tool both work). Not scanned/OCR. (Verified by reading the Oct 17, 2023 minutes;
text extracts cleanly, line-numbered, with a "DRAFT" watermark.)

**Meeting weekday:** **Tuesday.** Verbatim from minutes: "regular Council meetings are
held on the **first and third Tuesdays** of the month at 5:30 p.m." in the Logan Municipal
Council Chambers, 290 North 100 West.

**Roll-call votes — CONFIRMED present and richly structured.** Each motion records a named
**mover and seconder** and an explicit per-member **Aye/Nay roll**. Verbatim example
(Oct 17, 2023):
> "ACTION. Motion by Councilmember Simmonds seconded by Councilmember Jensen to approve
> Resolution 23-41 as presented. Motion carried by roll call vote.
> A. Anderson: Aye / M. Anderson: Aye / Jensen: Aye / López: Aye / Simmonds: Aye"

This is ideal for vote extraction (mover, seconder, item, per-member vote, result).

**Alternate / fallback source — Utah Public Notice (PMN):** `https://www.utah.gov/pmn`.
The Logan Municipal Council is a PMN public body; each meeting notice page links the
agenda **and** draft minutes as individual `/pmn/files/<id>.pdf`. Example notice (Nov 7,
2023 combined Council + RDA): agenda `https://www.utah.gov/pmn/files/1041937.pdf`,
draft minutes `https://www.utah.gov/pmn/files/1041939.pdf`. Use PMN's live search API
(`POST https://www.utah.gov/pmn/searchresult.html`, CSRF from the search page meta tag,
empty `sortColumn`/`sortOrder`) to enumerate notices when the Revize listing is awkward,
or for any year the city page omits. The April 21, 2026 agenda confirms the body is still
active on PMN (`https://www.utah.gov/pmn/files/1419709.pdf`).

**Video/audio (not minutes, for cross-reference):** City of Logan YouTube channel
`https://www.youtube.com/channel/UCFLPAOK5eawKS_RDBU0stRQ`; PMN also attaches per-meeting
audio (.m4a/.mp3).

---

## 2. Council structure

- **Form of government:** Council-mayor (Utah Code 10-3b-2). Executive = separately elected
  **Mayor**; legislative = 5-member Municipal Council.
- **Seats:** **5 council members, ALL elected at-large.** **0 districts** — "Logan does not
  use districts for election purposes; the mayor and council members are elected at-large"
  (in place since 1975).
- **Mayor votes?** **No.** The Mayor is the executive and is listed in minutes under
  "Administration present," separate from the voting "Council Members present." Mayor has
  veto power, not a council vote (standard Utah council-mayor form).
- **Chair:** Council elects a Chair and Vice Chair from among its 5 members; the Chair runs
  meetings and is a voting member.

**Current members (sworn in Jan 6, 2026):**
- **Mayor:** Mark A. Anderson (moved from council seat to mayor)
- Mike Johnson — Council **Chair**
- Jeannie F. Simmonds
- Ernesto López
- Katie Lee-Koven
- Melissa Dahle

*(2023-era council, for vote-history joins: Chair Ernesto López, Vice Chair Amy Z.
Anderson, Jeannie F. Simmonds, Mark A. Anderson, Tom Jensen; Mayor Holly H. Daines. The
member list on `members.php` was stale/cached at recon time — confirm names per-era from
the minutes header roster, which lists who was present each meeting.)*

Reference: Rules & Procedures for the Logan Municipal Council —
`https://www.utah.gov/pmn/files/926229.pdf` (PDF binary; couldn't text-extract via fetch,
read locally or via city site if needed).

---

## 3. RDA / CRA / CDRA

- **Separate meetings: YES.** Logan operates a **Redevelopment Agency (RDA)** as a distinct
  public body. Governing board = the City Council members; Chief Administrative Officer =
  the Mayor. The Council **adjourns its regular meeting and reconvenes as the RDA** the same
  evening (e.g. Council 5:30 PM → "ADJOURN to a meeting of the Logan Redevelopment Agency"
  ~8:00 PM). The RDA produces its **own agenda and its own minutes**, separate from the
  Council minutes.
- **Where RDA minutes live:**
  - PMN public body for the Logan Redevelopment Agency: `https://www.utah.gov/pmn/sitemap/publicbody/1277.html`
    (and notice history `https://www.utah.gov/pmn/sitemap/noticehistory/79437.html`).
    RDA notices carry separate agenda + draft-minutes PDFs under `/pmn/files/<id>.pdf`.
  - RDA overview / project areas on city site:
    `https://www.loganutah.gov/government/mayor_s_office/economic_development/rda/rda_overview/index.php`
    (project areas: Downtown RDA, South Main, Northwest, Logan River, Logan North Retail,
    600 West EDA, Auto Mall CDA, etc.).
- **Note:** because Council and RDA meet back-to-back and are often noticed together, some
  combined notices bundle both agendas; the RDA *minutes* are a distinct file. Treat RDA as
  a second meeting body in the repo (own folder), not folded into council minutes.

---

## 4. Public comments

- **Published: YES — transcribed/summarized inside the minutes.** Every regular meeting has
  a **"QUESTIONS AND COMMENTS FOR MAYOR AND COUNCIL"** section, plus per-item **PUBLIC
  HEARING** sections. Speakers are named with city of residence and their remarks
  paraphrased, with staff/council responses. Verbatim example (Oct 17, 2023): "Joshua
  Molitor, a resident of Logan acknowledged the approval of the 1400 North Main RDA and
  asked if the parking concerns... Mayor Daines responded that there was more parking than
  needed." Public-hearing speakers likewise (e.g. "Dr. Gail B. Yost, a resident of Logan
  inquired when the sediment removal...").
- **How submitted:** in person — step to the microphone, state name + address for the
  record, **3-minute limit** (groups appoint a spokesperson). No evidence of a separate
  eComment / SpeakUp / online-comment portal; written correspondence, if any, would arrive
  in the agenda packet (the per-year "agendas and packets" PDFs) rather than a dedicated
  comments page.
- **Extraction approach:** parse the named-speaker blocks under "QUESTIONS AND COMMENTS"
  and "PUBLIC HEARING" headings in each minutes PDF. There is no machine-readable comment
  feed; comments == the minutes prose.

---

## 5. Elections — administered by Cache County

- **Administered by:** Cache County Clerk/Auditor (not the city). Logan municipal elections
  are **odd-year November**, **at-large** (mayor single-winner; council = top-N at-large,
  N = seats up that cycle). **No districts.**
- **Primary results sources:**
  - Cache County Clerk election-results hub:
    `https://www.cachecounty.gov/elections/election-results/` — links by year. Older years
    are HTML result pages hosted on the county site, e.g.:
    - 2023 Nov General: `.../elections/election-results/2023novgeneralresults.html`
      (+ details `.../2023-nov-general-details.html`)
    - 2023 Primary: `.../elections/election-results/2023-primary-results.html`
    - 2020 Nov General: `.../elections/election-results/2020-nov-general-election-results.html`
    - 2020 Jun Primary: `.../elections/election-results/2020primary.html`
    - Canvass/audit PDFs under `.../assets/department/clerk/elections/...`
  - **State / Enhanced Voting portal** (richer, structured; recent cycles): Cache County
    results on `electionresults.utah.gov` / `app.enhancedvoting.com`, e.g.:
    - 2023 Nov General Logan City Council ballot item:
      `https://electionresults.utah.gov/results/public/cachecountyutah/elections/2023-Nov-General/ballot-items/2cdb52a2-160f-4aac-b77d-f8e5143b9c4f`
    - 2025 Municipal Primary: `https://electionresults.utah.gov/results/public/cache-county-ut/elections/primary08122025`
    - 2026 Primary (Enhanced Voting): `https://app.enhancedvoting.com/results/public/cache-county-ut/elections/Primary06232026`
- **Existing Desktop archive:** **NONE for Cache County** — build from scratch (no
  `~/Desktop/...` Cache scaffold exists; the playbook table covers only Salt Lake, Utah,
  Washington counties).
- **RCV:** **Logan city itself = plurality (no RCV)** as far as observed (top-N at-large;
  2023 had a normal recount with no method change). **Caution:** several *other* Cache
  County municipalities used Utah's RCV pilot (e.g. **Nibley** 2021 mayor/council; North
  Logan results show round-by-round shares). When filtering county-wide files to "Logan,"
  exclude RCV-formatted neighbor contests. Marked `rcv: "no"` for Logan but flag county
  context as a parsing risk.
- **Watch-out:** Cache County's 2023 election had an investigation/recount and staff on
  administrative leave — official canvass/recount numbers are the authoritative figures;
  prefer canvass PDFs over election-night unofficial pages for 2023.

---

## 6. GIS

- **Precincts (statewide, authoritative):** UGRC **VistaBallotAreas** FeatureServer —
  `https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/VistaBallotAreas/FeatureServer/0`
  Query Cache County with **`CountyID = 3`**, `outSR=4326` (verify coords look like Utah
  lon/lat ≈ -111.8, 41.7, NOT UTM meters — see playbook CRS gotcha). Product page:
  `https://gis.utah.gov/products/sgid/political/voter-precincts/`.
- **Council-district layer:** **N/A — Logan is fully at-large, so there are NO council
  districts and no district FeatureServer to find.** The address tool degenerates to an
  **address → in/out-of-Logan-city-limits** check (every in-city address maps to the same
  5 at-large seats). Document this rather than forcing a district map.
- **County GIS (supporting):** Cache County Voting Precinct Viewer
  `https://www.cachecounty.gov/gis/voting-viewer.html` (precinct lookup; useful for
  reconciling precinct names in results files).
- For city-limits polygon: use UGRC SGID Municipal Boundaries (Logan) or Census place, if
  an in/out check is wanted.

---

## Retrieval plan (approach + effort)

| Dataset | Source | Approach | Effort |
|---|---|---|---|
| Council minutes 2020–present | Revize listing pages → PDF CDN; PMN fallback | Scrape `minutes.php` + each `YYYY_council_agendas_and_packets.php` for "Minutes" PDF links; curl from `cms9files.revize.com/loganut/.../council/`. Use PMN search API to backfill gaps. Born-digital → `pdftotext -layout` → markdown. | **Low–Med.** No API but stable static files; main friction = inconsistent, space-laden filenames and telling minutes from agendas. |
| Roll-call votes | Inside each minutes PDF | Regex the "ACTION. Motion by X seconded by Y to <item>... <Member>: Aye/Nay" blocks. Clean, uniform structure. | **Low.** Best-case structured prose. |
| Public comments | Inside each minutes PDF | Parse "QUESTIONS AND COMMENTS FOR MAYOR AND COUNCIL" and "PUBLIC HEARING" named-speaker blocks. | **Low–Med.** Free-text, named speakers; no separate feed. |
| RDA minutes | PMN body 1277 / city RDA pages | Enumerate RDA notices on PMN; pull separate RDA minutes PDFs. Same-night, separate body. | **Med.** Must separate RDA notice/minutes from co-noticed Council items. |
| Elections 2020/21/23/25 | Cache County Clerk pages + electionresults.utah.gov / Enhanced Voting | Pull state-portal structured results where present (2023+/2025/26); scrape county HTML pages + canvass PDFs for 2020/2021. Filter to Logan mayor + at-large council; exclude RCV neighbor contests. | **Med–High.** Mixed formats across years (HTML pages, canvass PDFs, two state portals); 2023 needs canvass/recount numbers; build from scratch. |
| Geo / precincts | UGRC VistaBallotAreas FS, CountyID=3 | Port `fetch_geometry.py` with CountyID=3, outSR=4326, verify CRS. | **Low.** |
| Geo / districts | none (at-large) | No district map; address tool = in/out city-limits only. | **Trivial.** |

---

## Risks / blockers

- **No portal API.** Revize serves static PDFs with inconsistent, space-containing,
  human-typed filenames; the listing pages must be scraped and minutes-vs-agenda told apart
  by label. Some year pages showed "No documents" in a quick fetch — verify each year and
  fall back to PMN where the city listing is incomplete.
- **DRAFT vs approved minutes.** Recent meetings are posted as "DRAFT Minutes"; keep but
  flag status.
- **PMN PDFs are compressed** (WebFetch returns binary; the Read/pdftotext path works) —
  not a real blocker, just don't rely on remote text extraction.
- **Stale member roster.** `members.php` was cached/old at recon; derive per-era rosters
  from minutes headers (authoritative for who was seated/voting that night).
- **Cache 2023 election integrity episode** (investigation, staff leave, recount) — use
  official canvass/recount figures, not election-night unofficial pages, for 2023.
- **RCV contamination in county files.** Logan = plurality, but Nibley/North Logan and
  other Cache cities used RCV; county-wide result files may mix formats — filter carefully
  to Logan contests only.
- **No existing Cache County archive** to reuse — election scraper built from scratch.
- **RDA / Council co-noticing.** Combined notices bundle both bodies; ensure RDA minutes
  land in their own bucket, not merged into council minutes.

---

```json
{"city":"Logan","minutes":{"vendor":"Revize CMS (static PDFs, no API; PMN fallback)","base_url":"https://www.loganutah.gov/government/city_council/minutes.php","minutes_years":"2008-2026 (2020-present fully covered)","format":"born-digital text-layer PDF","votes_in_minutes":true,"meeting_weekday":"Tuesday (1st & 3rd, 5:30pm)"},"council":{"districts":0,"at_large":5,"mayor_votes":false,"members":["Mike Johnson (Chair)","Jeannie F. Simmonds","Ernesto López","Katie Lee-Koven","Melissa Dahle"]},"rda":{"separate_meetings":"yes","where":"Same-night separate body (council adjourns into RDA); own agenda+minutes on Utah PMN public body 1277 (https://www.utah.gov/pmn/sitemap/publicbody/1277.html) and city RDA pages"},"comments":{"published":"yes","where":"Transcribed by name in minutes under 'QUESTIONS AND COMMENTS FOR MAYOR AND COUNCIL' and PUBLIC HEARING sections","submit":"In person at meeting: name+address for record, 3-minute limit; no online eComment portal"},"elections":{"county":"Cache","source_url":"https://www.cachecounty.gov/elections/election-results/ ; https://electionresults.utah.gov/results/public/cache-county-ut","existing_archive":"none","district_based":false,"rcv":"no"},"geo":{"ugrc_county_id":3,"boundaries_available":true,"districts_or_atlarge":"at-large (no council districts; address tool = in/out city limits only)"},"risks":["No portal API; scrape Revize static PDFs with inconsistent space-laden filenames; tell minutes from agendas","Some year listing pages show 'No documents' - verify per year, backfill via Utah PMN","DRAFT vs approved minutes status","members.php roster stale - derive per-era rosters from minutes headers","Cache County 2023 election investigation/recount - use official canvass figures","RCV contamination from neighbor Cache cities (Nibley/North Logan) in county-wide files","No existing Cache County election archive - build from scratch","RDA and Council co-noticed - keep RDA minutes in own bucket"],"recommended_order":["1. Council minutes 2020-present (Revize scrape + PMN backfill) - foundation","2. Roll-call vote extraction from minutes (clean structured prose)","3. Public comments extraction from same minutes","4. RDA minutes (PMN body 1277, same-night separate body)","5. Cache County elections 2020/21/23/25 (state portal + county pages/canvass PDFs)","6. Geo: UGRC VistaBallotAreas CountyID=3 precincts; at-large so address->in/out city limits only"]}
```
