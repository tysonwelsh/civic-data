# Park City, Utah — Civic Data Recon

**Body:** Park City Municipal Corporation, City Council (Summit County, UT)
**Form of government:** Council-Manager (City Manager = Matthew J. Dias)
**Recon date:** 2026-06-26
**Scope:** Data 2020–present. Read-only mapping (no bulk download).

> NOTE ON DOMAIN: Park City migrated `parkcity.org` → **`parkcity.gov`**. The `.org`
> URLs 301-redirect to `.gov`. Some `.gov` "pretty" paths (e.g. `/government/city-council`)
> 404 to scrapers/WebFetch even though they render in a browser (CMS = likely a
> CivicEngage/CivicPlus front end). Use the API and `showpublisheddocument` deep links
> instead of the HTML nav pages.

---

## 1. Council Minutes

### Portal vendor — CivicClerk (CivicPlus)
- **Public portal (human):** https://parkcityut.portal.civicclerk.com/ (JS app — not scrapable directly)
- **API host (the real source):** `https://parkcityut.api.civicclerk.com/v1/` — OData, open, no auth.
- **City landing page:** https://parkcity.gov/government/city-council/city-council-meetings
  ("City Council Meeting Info & Listen Live"; packets posted since **May 2015**).

### API / URL pattern (VERIFIED working via curl)
- **Enumerate meetings:**
  `GET /v1/Events?$filter=categoryId eq 26 and startDateTime ge 2020-01-01T00:00:00Z&$orderby=startDateTime&$top=N`
  - `categoryId eq 26` = **City Council** (other categories: Planning Commission,
    Historic Preservation Board, "Planning Department Administrative Public Hearing").
  - Each event object carries an **inline `publishedFiles[]`** array; entries have
    `type` ∈ {`Agenda`, `Agenda Packet`, `Minutes`}, a `fileId`, a `name`
    (e.g. `"2.1.24 Minutes"`), and `url` (`stream/PARKCITYUT/<guid>.pdf`).
  - (Top-level `minutesFile`/`agendaFile` objects are usually empty — use
    `publishedFiles` instead.)
- **Download a document (VERIFIED, HTTP 200, application/pdf):**
  `GET /v1/Meetings/GetMeetingFileStream(fileId=<fileId>,plainText=false)`
  - Example minutes (Feb 1 2024): `fileId=4447` → 10.6 MB born-digital PDF.

### Minutes years, format
- **CivicClerk covers minutes back through ≥2019** (spot-checked: 2019/2021/2023 summer
  council meetings each had a `Minutes` file on essentially every meeting). **2020–present
  fully covered.** Agendas/media in the system go back to **1995** (deep archive, not needed).
- **Format: born-digital text-layer PDF.** `pdftotext -layout` extracts cleanly (1,426
  lines on the test doc, no OCR artifacts). Minutes file is large because it embeds the
  full packet/exhibits, but the narrative + votes are clean text.
- **Mirrors (fallback / pre-2015):**
  - Utah Public Notice site `utah.gov/pmn` mirrors Park City council minutes PDFs
    (e.g. `https://www.utah.gov/pmn/files/1078073.pdf` = Feb 1 2024 council;
    `https://www.utah.gov/pmn/files/1442829.pdf` = June 4 2026 council).
  - `parkcity.gov/home/showpublisheddocument/<id>/<ticks>` hosts individual older minutes.

### Meeting weekday — **Thursday**
- Council Chambers, 445 Marsac Avenue. Meetings open at **3:30 p.m.** (work session) and
  continue to an evening regular session. Verified: Feb 1 2024 + Feb 15 2024 were both
  Thursdays. (Occasional special meetings on other days exist.)

### Roll-call votes — **YES, present in minutes (VERIFIED)**
Minutes carry a structured **ROLL CALL** attendance block plus per-motion recorded votes
with **mover, seconder, and AYES/NAYS by member name**. Sample lines from 2024-02-01:
```
Council Member Rubell moved to appoint ... Council Member Ciraco seconded the motion.
AYES: Council Members Ciraco, Parigian, and Rubell
NAYS: Council Members Dickey and Toly
```
Split votes are recorded individually (not just "carried"). High parse confidence.
Note: the **Mayor is listed in ROLL CALL attendance but does NOT appear in AYES/NAYS
tallies** — consistent with mayor voting only to break ties (see §2).

---

## 2. Council Structure

- **All seats AT-LARGE** — no districts. 5 council members + 1 mayor, all elected citywide.
- **Mayor:** does **not** vote on ordinary motions; presides and **votes only to break ties**
  (e.g., the Jan 2026 council-vacancy appointment "tie vote was broken by [Mayor] Dickey").
  → `mayor_votes: false`.
- **Terms:** 4-year, staggered. One cycle elects **Mayor + 2 council**; the next elects
  **3 council**.
- **Form:** Council-Manager (City Manager Matthew J. Dias is CEO/administrator).

### Current members (sworn Jan 5 2026)
| Role | Name | Notes |
|---|---|---|
| Mayor | **Ryan Dickey** | Won 2025 (recount); was a council member 2024–25 |
| Council | **Tana Toly** | Re-elected 2025, term to Jan 2030 |
| Council | **Diego Zegarra** | Elected 2025 (first Latino councilor), term to Jan 2030 |
| Council | **Ed Parigian** | Elected 2023, term to ~Jan 2028 |
| Council | **Bill Ciraco** | Elected 2023, term to ~Jan 2028 |
| Council | **Molly Miller** | **Appointed Jan 2026** to fill Dickey's vacated 2023 seat (to ~2028) |

(2024 roster for older minutes: Mayor Nann Worel; council Ciraco, Dickey, Parigian,
Rubell, Toly.)

---

## 3. Redevelopment Agency (RDA) — HIGH VALUE

Park City operates **two RDA project areas**: **Main Street RDA** and **Lower Park Avenue
RDA** (created 1989); historically very active (Historic Main Street, Bonanza Park, Lower
Park Ave). Each has dedicated capital-improvement & debt-service funds.

**Where it lives / how it meets — leaning IN-COUNCIL, but a registered separate body:**
- The RDA **is registered as its own public body** on Utah PMN:
  `https://www.utah.gov/pmn/sitemap/publicbody/654.html` ("Redevelopment Agency — Park
  City"; contact = City Recorder Michelle Kellogg). → separate notices CAN be posted.
- **CivicClerk has NO Redevelopment Agency category** (`contains(eventName,'Redevelopment')`
  returns empty; only City Council / Planning Commission / HPB / Planning-Admin categories
  exist). The sampled 2024 council minutes contain **no RDA recess and no "Redevelopment"
  business** that meeting.
- RDA staff reports surface as documents authored *for the Council*
  (e.g. `parkcity.gov/home/showpublisheddocument/24343/...` "Redevelopment Agency Staff
  Report"), i.e. the **City Council convenes/acts as the RDA board**, usually as agenda
  items within (or a noticed adjacent session to) a regular Council meeting.

**Verdict:** `separate_meetings: "unclear"` — most RDA action appears to run through the
Council (no dedicated CivicClerk track), but a separate PMN body exists and may carry
stand-alone RDA notices/minutes in some years. **Auditor must check both** the CivicClerk
City Council stream (search minutes text for "Redevelopment Agency of Park City" /
"RDA") **and** PMN body 654 for any independently-noticed RDA meetings.

---

## 4. Public Comments

Park City **does** facilitate written/oral public comment; not pre-judging completeness.
- **Submit by email:** `council_mail@parkcity.gov` (group email to Mayor + all Council).
  Mailed: 445 Marsac Ave, PO Box 1480, Park City UT 84060. Phone 435-615-5000.
- **eComment portal:** the city advertises submitting comments via **eComment** and via
  **Zoom "raise hand"** for virtual participation — i.e. a CivicClerk/eComment
  electronic-comment channel tied to each meeting.
- **In minutes:** public-comment speakers and summaries are transcribed into the minutes
  narrative (the born-digital minutes include public-input sections).
- **Agenda packets** (CivicClerk `Agenda Packet` doc, `type=="Agenda Packet"`) commonly
  embed written correspondence/exhibits.
- → `published: "yes"` (in minutes + packets), submit via email / eComment / Zoom.
  Whether a standalone written-comment archive exists is for the auditor.

---

## 5. Elections — administered by **PARK CITY ITSELF** (not Summit County)

**KEY CORRECTION to the task premise:** Summit County Clerk **explicitly defers municipal
results to the city**: their archive page states *"Municipal election results are available
by contacting the municipality that was responsible for running their elections,"* and
shows **no Park City mayor/council races**. Park City runs its own municipal elections.

### Primary authoritative source — Park City
- **Results page:** https://parkcity.gov/government/elections/election_results.php
  - Canvass-resolution / precinct PDFs for **2019, 2021, 2023, 2025** (primary + general
    each), plus pre-2019. Deep links via `parkcity.gov/home/showpublisheddocument/<id>/...`
    (e.g. 2025 primary canvass `.../77160/...`; official ballot `.../77224/...`).
- **Election info / admin:** https://parkcity.gov/departments/executive/election-information

### Secondary / mirror — State portal (Enhanced Voting)
- `electionresults.utah.gov` carries Summit-County-context Park City races in recent cycles:
  - 2025 general: https://electionresults.utah.gov/results/public/summit-county-ut/elections/general11042025
    (includes **Park City Mayor**).
  - 2023 general: https://electionresults.utah.gov/results/public/summitcountyutah/elections/2023-Nov-General
  - Useful cross-check, but **precinct granularity is best on the Park City PDFs.**

### County clerk (county/state races only; NOT municipal)
- https://www.summitcountyutah.gov/288/Election-Results-Archives (summary+precinct PDFs
  via `/DocumentCenter/View/<id>`; 2004–2026; **no Park City council/mayor**).

### Structure / RCV
- **At-large, vote-for-N** (top-N win; 3 seats one cycle, 2 + mayor the other).
- **No Ranked Choice Voting.** Council **punted on RCV in Sept 2024** and was still
  studying it (awaiting a UVU study) as of 2026 → `rcv: "no"` for the whole 2020–present
  window (mark "unclear/monitor" going forward).
- Races are close: **2025 mayor went to a recount** (Dickey 1,706 vs Rubin 1,699 = 7 votes).
- **No existing Desktop election archive for Summit County / Park City** → build from scratch.

---

## 6. GIS

- **Precincts:** UGRC **VistaBallotAreas FeatureServer**, `CountyID = 22` (Summit). Query
  features with `outSR=4326`; **verify coords are Utah lon/lat (~ -111.5, 40.65), not UTM**
  (CRS gotcha from playbook). Save to `geo/precincts.geojson`.
- **Districts:** Park City is **entirely at-large → there is NO council-district map.** The
  address tool degenerates to an **address → in/out-of-city-limits** check.
- **City-limits boundary:** available from UGRC Municipal Boundaries (statewide) filtered to
  "Park City", and/or Park City's own GIS/open-data. Use this polygon for the in/out check.
- → `districts_or_atlarge: "at-large"`, `boundaries_available: true`.

---

## Retrieval Plan (approach + effort)

| Dataset | Source | Approach | Effort |
|---|---|---|---|
| **Council minutes 2020–present** | CivicClerk API | Loop `Events?$filter=categoryId eq 26` per year; for each event pull `publishedFiles` entry where `type=='Minutes'`; download via `GetMeetingFileStream(fileId,plainText=false)`; `pdftotext -layout` → markdown. | **Low** (open OData API, born-digital PDFs, votes inline) |
| **Roll-call votes** | same minutes | Regex on extracted text: `moved`/`seconded`, `AYES:`/`NAYS:` member lists; map to roster per era. | **Low–Med** (clean, consistent format) |
| **RDA** | CivicClerk text search + PMN body 654 | Grep council minutes for "Redevelopment Agency"/"RDA"; separately check PMN body 654 for any stand-alone RDA notices/minutes. | **Med** (no dedicated track; embedded in council) |
| **Public comments** | minutes + agenda packets + eComment | Parse public-input sections from minutes; harvest `Agenda Packet` PDFs for correspondence; note eComment/email channel. | **Med** (scattered across packets) |
| **Elections 2019/21/23/25** | parkcity.gov canvass PDFs (+ state portal) | Harvest `showpublisheddocument` PDFs from election_results.php; parse at-large vote-for-N; cross-check vs `electionresults.utah.gov`. | **Med** (PDF parsing, inconsistent canvass formats; at-large model per playbook) |
| **Precinct geo** | UGRC VistaBallotAreas CountyID 22 | Port `fetch_geometry.py` (CountyID→22, `outSR=4326`, verify CRS). | **Low** |
| **City-limits polygon** | UGRC Municipal Boundaries / Park City GIS | Pull Park City polygon for in/out-of-city address tool. | **Low** |

## Risks / Blockers
1. **Task premise wrong on election admin:** Park City **self-administers** municipal
   elections — Summit County Clerk has no Park City municipal results. Use **parkcity.gov
   canvass PDFs** as authoritative; state portal as mirror.
2. **HTML nav pages 404 to scrapers** (`.gov` CMS). Rely on the CivicClerk **API** and
   `showpublisheddocument` deep links, not pretty URLs.
3. **Minutes PDFs are large (~10 MB)** because they bundle full packets — fine for text
   extraction but heavy to bulk-store; consider extracting/keeping text + raw PDF.
4. **RDA ambiguity:** no separate CivicClerk category, but a registered PMN body (654)
   exists — separate RDA minutes may exist for some years and must be hunted (don't assume
   none).
5. **At-large vote-for-N normalization:** `pct` = share of council votes, not turnout;
   model winners as top-N (per election_playbook). 2025 mayor recount → use **final
   canvass** numbers.
6. **No RCV now, but Park City is actively studying it** — future cycles may switch; flag.
7. **Pre-2019 minutes** thin in CivicClerk; PMN/`showpublisheddocument` mirrors fill gaps
   if scope extends earlier (not needed for 2020+).

## Recommended order
1. Council minutes (CivicClerk API) — easiest, highest volume, votes inline.
2. Roll-call vote extraction from those minutes.
3. Elections (parkcity.gov canvass PDFs + state-portal cross-check).
4. Precinct + city-limits geo (UGRC), build in/out-of-city address tool.
5. RDA sweep (grep council minutes + PMN body 654).
6. Public comments (minutes sections + agenda-packet correspondence).

---

```json
{"city":"Park City","minutes":{"vendor":"CivicClerk (CivicPlus)","base_url":"https://parkcityut.api.civicclerk.com/v1/","minutes_years":"2019-present (2020+ fully covered; agendas/media to 1995)","format":"born-digital text-layer PDF","votes_in_minutes":true,"meeting_weekday":"Thursday"},"council":{"districts":0,"at_large":5,"mayor_votes":false,"members":["Mayor Ryan Dickey","Tana Toly","Diego Zegarra","Ed Parigian","Bill Ciraco","Molly Miller"]},"rda":{"separate_meetings":"unclear","where":"No separate CivicClerk category; RDA business runs through City Council (council acts as RDA board). Registered separately on Utah PMN body 654 (utah.gov/pmn/sitemap/publicbody/654.html) where stand-alone RDA notices may appear. Project areas: Main Street RDA + Lower Park Avenue RDA."},"comments":{"published":"yes","where":"transcribed in minutes; correspondence in CivicClerk Agenda Packet PDFs","submit":"email council_mail@parkcity.gov, eComment portal, or Zoom raise-hand"},"elections":{"county":"Summit","source_url":"https://parkcity.gov/government/elections/election_results.php (Park City self-administers; mirror at https://electionresults.utah.gov/results/public/summit-county-ut)","existing_archive":"none","district_based":false,"rcv":"no"},"geo":{"ugrc_county_id":22,"boundaries_available":true,"districts_or_atlarge":"at-large"},"risks":["Park City SELF-ADMINISTERS municipal elections; Summit County Clerk has no Park City municipal results - use parkcity.gov canvass PDFs","HTML .gov nav pages 404 to scrapers - use CivicClerk API + showpublisheddocument deep links","Minutes PDFs ~10MB (bundle full packet) - extract text, store raw separately","RDA has no separate CivicClerk track but a registered PMN body (654) - separate RDA minutes may exist some years","At-large vote-for-N: pct=share of council votes not turnout; 2025 mayor decided by recount (7 votes)","No RCV currently but Park City actively studying adoption - flag for future cycles"],"recommended_order":["council_minutes_civicclerk_api","rollcall_vote_extraction","elections_parkcity_canvass_pdfs","geo_ugrc_precincts_and_city_limits","rda_sweep_minutes_and_pmn654","public_comments_minutes_and_packets"]}
```
