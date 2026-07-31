# St. George, Utah — Civic Data Reconnaissance

**City:** St. George, Utah (Washington County, UGRC County ID **27**)
**Recon date:** June 2026
**Scope:** Map public data sources (2020–present) for council minutes, votes, public comments, elections, GIS. No bulk download performed.

> ⚠️ **CRITICAL DISAMBIGUATION:** There is a newly-incorporated **St. George, Louisiana** (East Baton Rouge Parish, first election Apr 2025) with a *district-based* council (5 districts + 2 at-large). Many generic web searches conflate the two. **St. George, UTAH is entirely AT-LARGE.** Downstream agents must filter out all Louisiana sources (theadvocate.com, stgeorgela.gov, etc.).

---

## 1. Council Meeting Minutes

### Portal / Vendor
- **Official site:** `https://sgcityutah.gov` — *note:* the old domain `https://sgcity.org` now **302-redirects** to `sgcityutah.gov`. Update any cached links.
- **Vendor / CMS:** **Revize** (custom municipal CMS). Documents are served from a Revize file host, **not** PrimeGov / Granicus-Legistar / CivicPlus-AgendaCenter / CivicClerk / NovusAgenda / Laserfiche. **No JSON API** — this is a static-file CMS; retrieval is by direct-URL construction or HTML scrape.
- **Landing page:** `https://sgcityutah.gov/government/city_council/agendas_and_minutes.php`
  - (also `https://sgcityutah.gov/agendasandminutes/`)
- **Council meeting overview:** `https://sgcityutah.gov/government/city_council/index.php`

### File host + URL pattern (Revize)
Base file host:
```
https://cms3.revize.com/revize/stgeorge/Documents/Government/City%20Council/Agendas%20And%20Minutes/<YEAR>/<TYPE>/<file>.pdf
```
Where `<TYPE>` ∈ `Minutes` | `Agendas` | `Agenda Packets` | `Recordings` (mp3) | `Notices`.

**Minutes filename pattern** (born-digital):
- `<YYYY.MM.DD>  Minutes.pdf` (older 2025 style — note double space)
- `<YYYY.MM.DD> Minutes Regular Meeting.pdf` / `... Work Meeting.pdf` (newer style)

**Confirmed example URLs (open / valid):**
- `https://cms3.revize.com/revize/stgeorge/Documents/Government/City%20Council/Agendas%20And%20Minutes/2025/Minutes/2025.05.01%20%20Minutes.pdf`
- `https://cms3.revize.com/revize/stgeorge/Documents/Government/City%20Council/Agendas%20And%20Minutes/2025/Minutes/2025.02.06%20%20Minutes.pdf`
- Agenda example: `.../2025/Agendas/2025.05.01%20%20City%20Council%20Agenda.pdf`

### Years of MINUTES available
- **On the city site (Revize):** **2022, 2023, 2024, 2025, 2026** (the agendas/minutes page header states "Agendas and minutes prior to 2022, please visit the Utah Public Notice Website").
- **2020–2021 minutes:** only via the **Utah Public Notice Website (PMN)** — `https://www.utah.gov/pmn/` — St. George City Council public-body pages:
  - `https://www.utah.gov/pmn/sitemap/publicbody/241.html`
  - `https://www.utah.gov/pmn/sitemap/publicbody/242.html`
  - PMN attachment URL pattern: `https://www.utah.gov/pmn/files/<FILE_ID>.pdf` (opaque numeric IDs, e.g. `https://www.utah.gov/pmn/files/1388219.pdf` = Jan 15 2026 minutes). PMN files are NOT predictable by date — must be harvested by crawling each notice page (`/pmn/sitemap/notice/<ID>.html`).

### Format
- **Born-digital, text-extractable PDFs.** Confirmed with `pdftotext -layout` — clean text, no OCR needed. (A naive binary fetch looks "scanned" because the PDF uses object streams, but the text layer is fully present and high quality.)

### Meeting cadence
- **Regular meetings: 1st and 3rd THURSDAYS each month, 5:00 PM**, City Council Chambers, City Hall, 61 S Main St.
- **Work meetings:** as-needed (also produce minutes — e.g. `... Work Meeting.pdf`).
- City Code ref: `https://stgeorge.municipal.codes/Code/1-6-2`

### ✅ Roll-call votes in minutes — CONFIRMED (excellent for extraction)
Minutes contain **structured, labeled vote blocks** with mover, seconder, and **individual member aye/nay**. Verbatim example (2025.05.01 minutes):
```
MOTION:
   A motion was made by Councilmember Larkin to approve the consent calendar with the exception of item 3e.
SECOND:
   The motion was seconded by Councilmember Kemp.
VOTE:
   Mayor Pro Tem Hughes called for a vote, as follows:
       Councilmember Hughes – aye
       Councilmember Larkin – aye
       Councilmember Larsen – aye
       Councilmember Tanner – aye
       Councilmember Kemp – aye
   The vote was unanimous and the motion carried.
```
- Pattern is highly regular: `MOTION:` / `SECOND:` / `VOTE:` headers, then `Councilmember <Name> – aye|nay`. Some are labeled "roll call vote." Attendance is listed under `PRESENT:` / `EXCUSED:` / `STAFF MEMBERS PRESENT:`. Agenda packet page references and timestamped video links (`00:11:10`) are inline.
- **This is near-ideal for automated motion/vote parsing.**

---

## 2. Council Structure

- **Government type:** Council–Manager (City Manager: John Willis).
- **Composition:** **Mayor + 5 Council Members = 6-member council.**
- **Districts: 0. At-large: 5 (plus at-large Mayor).** ALL seats elected **at-large / citywide**. No wards/districts. (The "5 districts + 2 at-large" figure that appears in searches is **St. George, LOUISIANA** — ignore.)
- **Terms:** **4-year staggered terms** (mayor + ~2 council seats up each odd year). Mayor is separately elected and sits on the council.
- **Current members (as of Jan 2026, post-election/swearing-in):**
  - **Mayor: Jimmie Hughes** (won Nov 2025, sworn Jan 5 2026; was a councilmember).
  - **Dannielle Larkin** — at-large, term expires Jan 2028.
  - **Steve Kemp** — at-large, term expires Jan 2028.
  - **Austin Anderson** — at-large, term expires Jan 2028 (appointed Jan 22 2026 to fill Hughes's vacated council seat).
  - **Natalie Larsen** — at-large, term expires Jan 2030 (re-elected 2025).
  - **Michelle Tanner** — at-large, term expires Jan 2030 (re-elected 2025).
  - (Prior mayor Michele Randall, 2021–2025, lost to Hughes in 2025.)
- **Source URLs:**
  - `https://sgcityutah.gov/government/mayor_and_council/index.php`
  - `https://sgcityutah.gov/government/mayor_and_council/city_council_member_directory.php`
  - `https://sgcityutah.gov/government/mayor_and_council/election_information.php`
  - `https://ballotpedia.org/St._George,_Utah`
  - `https://en.wikipedia.org/wiki/St._George,_Utah`

---

## 3. Public Comments — **PUBLISHED (yes)**

- **Comments ARE published** on the city website, archived by year (2023, 2024, 2025, 2026), grouped in ~weekly windows (noon-to-noon). Many windows say "No comments were received"; when comments exist they're posted as PDFs.
- **Archive / publication page:** `https://sgcityutah.gov/government/city_council/public_comments.php`
- **How the public submits:** a **JotForm** written-comment form — `https://form.jotform.com/240664971368063` (linked as "Submit Public Comment"). No separate eComment/SpeakUp/Granicus portal.
- Comments are also sometimes reflected inside minutes (e.g. "COMMENTS FROM THE PUBLIC: No comments were given" / "two public comments received").
- **Recorder contact:** Christina Fernandez, City Recorder, 435-627-4003, 61 S Main St.
- **Note:** PDF attachment URLs for individual weekly comment files were not enumerated in recon; they live on the same Revize host and must be scraped from the public_comments page. Pre-2023 written comments not evident online.

---

## 4. Elections — run by **Washington County** (County #27)

St. George council/mayor are **at-large**, odd-year municipal elections. **District-based: NO.**

### Source A — Washington County Clerk (PRIMARY; richest formats, direct files)
- **Elections home:** `https://www.washco.utah.gov/departments/clerk/elections/`
- **Previous results index:** `https://www.washco.utah.gov/departments/clerk/elections/previous-election-results/`
  - Per-election the county posts: **Official Results Summary (PDF)**, **Official Results by Precinct (PDF)** ← precinct detail!, **CSV export**, and for recent years **XLSX canvass** + **Public Cast Vote Record (XLSX)**.
  - **Coverage confirmed: 2021 (Aug+Nov), 2023 (Sept+Nov), 2025 (Aug+Nov)** — all with precinct-detail PDF + CSV. (Also likely 2020 general.)
  - Files hosted on `outpost.washco.utah.gov` (exact per-file URLs not enumerated here; reachable from the previous-results index page).
- **Per-election blog posts (entry points to file links):**
  - Nov 2025: `https://www.washco.utah.gov/2025/11/04/election-results-november-2025/`
  - Aug 2025: `https://www.washco.utah.gov/2025/08/12/election-results-august-2025/`
  - Sept 2023: `https://www.washco.utah.gov/2023/09/05/election-results-september-2023/`
  - Tag feeds: `https://www.washco.utah.gov/tag/election-results/`
- St. George races confirmed present: "St George Mayor", "St George City Council".

### Source B — Utah state portal (Enhanced Voting system)
- Root: `https://electionresults.utah.gov/`
- **Washington County (current slug):** `https://electionresults.utah.gov/results/public/washington-county-ut/elections/<ELECTIONKEY>`
  - 2025 general: `.../washington-county-ut/elections/general11042025`
  - 2026 primary (live): `.../washington-county-ut/elections/Primary06232026`
- **Historical slug variant:** `https://electionresults.utah.gov/results/public/washingtoncountyutah/elections/2023-Nov-General` (older election keys used `washingtoncountyutah` + `YYYY-Mon-General` style — slug format is NOT fully stable across years; enumerate per election).
- ⚠️ This portal is a **client-side JS app** — `WebFetch`/curl of the HTML returns an empty shell. Data comes from an Enhanced Voting **JSON/CSV API** behind the page (Enhanced Voting typically exposes a downloadable CSV per contest). Must be retrieved via the in-page export or the underlying XHR endpoint, not by scraping rendered HTML.

### Existing archive
- **None.** No prior Desktop/archive exists for Washington County. This is a greenfield build.

### Misc election sources
- 2025 positions-to-be-filled notice: `https://cms3.revize.com/revize/stgeorge/Documents/Government/Elections/2025/2025.05.01%20%20Mayor%20and%20City%20Council%20Positions%20to%20be%20Filled.pdf`
- Local journalism cross-check (Utah St. George only): `stgeorgeutah.com`, `kuer.org`.

---

## 5. GIS — Precinct / District Boundaries

- **UGRC VistaBallotAreas FeatureServer (authoritative, statewide voting precincts):**
  `https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/VistaBallotAreas/FeatureServer/0`
  - Fields: `OBJECTID, CountyID (SmallInteger), VistaID, PrecinctID, SubPrecinctID, VersionNbr, EffectiveDate, AliasName, Comments, RcvdDate, GlobalID, Shape__Area, Shape__Length`. Polygon geometry. Capabilities: **Query, Extract**.
  - **Filter for Washington County:** `?where=CountyID=27&outFields=*&f=geojson` (or `f=json`). No county-name field — use numeric CountyID=27.
  - Subprecincts only where split; `Dissolve` on `PrecinctID` → precinct polygons.
  - Product page: `https://gis.utah.gov/products/sgid/political/voter-precincts/`
  - Open data mirror: `https://opendata.gis.utah.gov/datasets/utah-vista-ballot-areas`
- **St. George ward/district map:** **N/A — the city is fully at-large, so there are NO council districts to map.** Precinct→district mapping is **trivial/identity**: every St. George precinct elects the same 6 citywide officials. For an address→district tool, the only meaningful lookup is "is this address inside St. George city limits?" (use UGRC Municipal Boundaries / city limits polygon), not a district assignment.
  - Municipal boundaries source: UGRC SGID `Municipalities` layer (gis.utah.gov) — pull St. George city-limits polygon for in/out-of-city determination.

---

## Retrieval Plan (recommended approach + effort)

| Dataset | Approach | Effort | Notes |
|---|---|---|---|
| **Minutes 2022–2026** | Scrape `agendas_and_minutes.php` per year → collect Revize PDF links → `pdftotext -layout`. Filename pattern is date-predictable but spacing/suffix varies ("Minutes" vs "Minutes Regular Meeting", single/double space) — **scrape links rather than guess URLs.** | **Low–Med** | Born-digital text; clean extraction. ~2 meetings/mo + work meetings ≈ 30–50 docs/yr. |
| **Minutes 2020–2021** | Crawl Utah PMN public-body pages 241 & 242 → each notice → `/pmn/files/<ID>.pdf`. | **Med** | Opaque numeric IDs; must walk notice index. Verify these are *minutes* not just agendas/notices. |
| **Roll-call votes** | Regex/section parser over minutes text: split on `MOTION:` / `SECOND:` / `VOTE:`; capture `Councilmember <Name> – aye\|nay`; capture mover/seconder from MOTION/SECOND lines; PRESENT/EXCUSED for roster. | **Low** | Format is exceptionally regular → high-accuracy structured votes. |
| **Public comments** | Scrape `public_comments.php` → per-year/week PDF links on Revize host → extract text. | **Low–Med** | Many weeks empty. 2023→present only. |
| **Elections 2021/2023/2025** | From `previous-election-results` index, fetch **county precinct-detail PDF + CSV** (outpost.washco.utah.gov). Filter to St. George Mayor/Council contests. | **Low–Med** | County files are clean structured data; prefer CSV. Cross-check totals vs Enhanced Voting. |
| **Elections (state portal backup)** | Enhanced Voting JSON/CSV API behind `electionresults.utah.gov/results/public/washington-county-ut/...`. Use export endpoint, not HTML. | **Med** | JS app; slug format varies per year — enumerate election keys. Use only if county CSVs are incomplete. |
| **GIS precincts** | Single REST query `VistaBallotAreas/FeatureServer/0?where=CountyID=27&f=geojson`. | **Very Low** | One call. |
| **City-limits polygon** | UGRC SGID Municipalities layer → St. George polygon (for address-in-city test). | **Low** | Replaces "district" lookup since at-large. |

**Recommended order:** (1) GIS precincts + city-limits polygon (trivial, unblocks geo) → (2) Minutes 2022–2026 from Revize → (3) Vote extraction from those minutes → (4) Public comments → (5) Elections 2021/2023/2025 county CSV/PDF → (6) Minutes 2020–2021 from PMN → (7) Enhanced Voting backup only if county data has gaps.

---

## Risks / Blockers

1. **St. George, LOUISIANA contamination** — pervasive in web search; LA council IS district-based. Hard-filter LA domains; trust only `sgcityutah.gov`, `washco.utah.gov`, `electionresults.utah.gov`, `gis.utah.gov`, `ballotpedia.org/St._George,_Utah`, `stgeorgeutah.com`.
2. **Domain migration** — `sgcity.org` → `sgcityutah.gov` (302). Files on a *third* host (`cms3.revize.com`). Any old hardcoded `sgcity.org` paths may break.
3. **No machine API for minutes/agendas** — Revize is a static-file CMS. Must scrape HTML for links; filename conventions are inconsistent (double spaces, varying suffixes). Don't rely on pure date-templated URLs.
4. **2020–2021 minutes only on Utah PMN** with **opaque numeric file IDs** — no date-derivable URLs; requires crawling notice pages and disambiguating minutes vs agendas vs notices.
5. **Enhanced Voting (electionresults.utah.gov) is a JS SPA** — empty to plain HTTP fetch; needs the underlying export/JSON endpoint. Slug format is inconsistent across years (`washington-county-ut` vs `washingtoncountyutah`, `general11042025` vs `2023-Nov-General`).
6. **Precinct→district mapping is identity** (at-large), so the "address→district" deliverable degrades to "address→in/out of St. George city limits + which 6 citywide officials." Set expectations accordingly.
7. **Public comments pre-2023 not online**; comment PDFs not yet URL-enumerated (scrape required). Some comment content only summarized inside minutes.
8. **Vote nuance** — most votes are 5-0 unanimous; watch for non-unanimous and abstentions/recusals, and Mayor-Pro-Tem situations when the elected Mayor is excused (e.g. 2025.05.01 Hughes chaired as Mayor Pro Tem while still a councilmember). Roster identity changes mid-term (Hughes mayor + Anderson appointed Jan 2026).
