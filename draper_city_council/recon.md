# Draper City, Utah — Civic Data Recon

**City:** Draper City, **straddles Salt Lake County (FIPS 49035) + Utah County (FIPS 49049)**,
Utah (~51k pop., 2020 census; ~30.3 sq mi land). The Salt Lake County portion is in the SLC
metro; the Utah County portion (Traverse Mountain / SunCrest ridge) is in the Provo–Orem metro.
**Draper is a single municipality in two counties** (confirmed: Wikipedia, Census QuickFacts,
and the city's own elections page linking BOTH county clerks).
**Recon date:** 2026-07-11
**Scope of interest:** 2020-01-01 → present (floor 2020; Draper incorporated **1978** — full
modern history exists; 2020 is a normal floor).
**Form of government:** **Six-member council–mayor form** — a separately-elected **Mayor** +
**five at-large Council Members** (NO districts). The Mayor **presides but does NOT vote** on
ordinary motions (confirmed against a real roll call — see §1/§4). Max council tally = **5**.
**Official site:** `https://www.draperutah.gov/` — a **custom/"GovBuilt-style" CMS** (Azure-edge,
`/sb/` sitebuilder bundle, Cludo search) for the general site, but **meetings live on Granicus**.
The site returned **HTTP 200 to a browser UA** this recon (no 403 observed), but keep the browser
UA as a precaution (Azure edge in front).

---

## 1. Council meeting minutes

### Portal — **Granicus** (`draper.granicus.com`, single `view_id=1`)
- **Host / listing (all public bodies in ONE view):**
  `https://draper.granicus.com/ViewPublisher.php?view_id=1`
  (also reachable from `https://www.draperutah.gov/city-government/mayor-and-council/agendas-and-minutes/`).
- **One flat "Past Meetings" table lists EVERY body** (row 1 cell = body name, then date/duration,
  then Agenda / Minutes / Video / MP4 / Agenda-Packet links). Bodies present with minutes counts:
  Planning Commission (303), **City Council (206) + "City Council Meeting" (156, older label) +
  Special/Retreat/Canvassers variants**, Historic Preservation Commission (152), Parks-Trails-Rec
  Committee, **Redevelopment Agency (60)**, Tree Committee/Commission, Emergency Preparedness Exec
  Cmte, **Zoning Administrator/Hearing (57)**, Equestrian Center Advisory Board, **Municipal
  Building Authority (29)**, **Community Reinvestment Agency (25)**, Appeals & Variance Hearing
  Officer, Diversity/Community-Engagement Cmte, arena boards, etc. → **RDA / MBA / CRA are SEPARATE
  Granicus bodies with their own minutes** (unlike Taylorsville's in-recess RDA — acquire them as
  distinct `body=` rows).
- **Document URL patterns (Granicus):**
  - Agenda: `//draper.granicus.com/AgendaViewer.php?view_id=1&clip_id=<clip>`
  - **Minutes/Recap: `//draper.granicus.com/MinutesViewer.php?view_id=1&clip_id=<clip>&doc_id=<uuid>`
    — this endpoint returns the raw **PDF bytes directly** (verified: `%PDF-1.6`, born-digital),
    despite the `.php` URL. Save with a `.pdf` extension and `pdftotext -layout` works cleanly.**
  - Video: `MediaPlayer.php?...&clip_id=<clip>` ; Agenda Packet: separate download.
- **⚠ TWO documents per recent meeting via a JS "Documents Selector"** (`<select>` `<option value>`
  list, NOT plain `<a href>` — my per-row `MinutesViewer` anchor regex missed them; parse the
  `<option value=".../MinutesViewer.php?...">` list). For 2024→present each Council meeting carries
  **BOTH** a **"CC M.D Recap"** and a **"CC M.D Minutes"** doc:
  - **"Recap" = tally-only summary**, explicitly stamped *"This document does not constitute the
    meeting minutes. The final minutes will be available once adopted by the Council."* — records
    outcomes as **"Ordinance #1692 was approved 4-0"** with **NO mover/seconder and NO named roll
    call**. **Do NOT feed Recaps to the vote extractor** — resolve to the "Minutes" doc.
  - **"Minutes" = full adopted minutes** with a **named per-member roll-call grid** (below).
  A single `MinutesViewer` anchor per row (older meetings) is the full Minutes; the selector only
  appears where both exist.
- **Coverage:** City Council minutes docs run **2012 → 2026** on Granicus (202 of 206 rows have a
  minutes doc). **2020 floor fully covered on the city's own portal** (no PMN dependency needed;
  Utah PMN is a live fallback — Draper entity on `utah.gov/pmn`).

### Format — CONFIRMED born-digital clean text PDF (NO OCR)
`pdftotext -layout` on the **2024-12-03 full Council minutes** and the **2025-11-20 PC minutes**
yields clean, selectable text — proper names intact (`Mayor Troy K. Walker`, `Councilmember Mike
Green`, `Commissioner Fowler`). Not scanned; Read parses directly. (Saved to `raw/` — see below.)

### Meeting cadence — **Tuesday, 1st & 3rd** (biweekly)
City Council meets **Tuesdays** (verified: every 2024–2025 date is a Tuesday; ~1st & 3rd Tuesday,
with occasional special meetings on other days, e.g. a Mon 2024-04-29 special). Chambers at
**1020 E Pioneer Road** (older minutes) — note city hall address appears as 1020 E Pioneer Rd.
Meetings have a Study Session + a Business Session (captured in one minutes doc per meeting-day).

### Roll-call votes in minutes — CONFIRMED PRESENT & NAMED (Millcreek-style grid)
The **full Minutes** record **mover + seconder + a named per-member Yes/No/Absent grid**:
> *"Councilmember Green moved to approve Ordinance #1628. Councilmember Johnson seconded the
> motion. A roll call vote was taken. The motion passed unanimously.*
> *Yes No Absent — Councilmember Green X / Councilmember Johnson X / Councilmember T. Lowery X /
> Councilmember F. Lowry X / Councilmember Vawdrey X"*

- **Every roll-call grid lists exactly the 5 Council Members** (2024 roster: Green, Johnson,
  T. Lowery, F. Lowry, Vawdrey). **Mayor Walker presides** (calls to order, opens/closes public
  hearings) **but is NEVER in the roll-call grid and casts no vote.** Adjournment recorded as
  *"passed by unanimous voice vote (5-0)"* → **max council tally = 5, Mayor NON-voting.**
- Grid columns are **Yes / No / Absent** (council) — so **named dissent IS recorded** (an X in the
  No column). The verified sample was 100% unanimous, but the grid format means contested votes
  will be per-member attributable (better than Taylorsville's narrative-tally). Confirm the No-column
  behavior on the first contested rezone/budget meeting during acquisition.

---

## 2. Council structure — **5 at-large members + executive Mayor (Mayor does NOT vote)**

- **NO districts.** Five **at-large** Council Members elected citywide + a citywide **Mayor**;
  all serve **4-year staggered non-partisan terms** ("Governing Body" = Mayor + Council per the
  city's page; council code Draper 2-6-020). At-large is confirmed independently by every election
  contest label being **"DRAPER CITY COUNCIL AT LARGE"** (no district numbers ever). ~3 seats up
  one cycle, ~2 seats + Mayor the next.
- **Current roster** (city site `mayor-and-council/` member pages, 2026):

  | Seat | Member | Note |
  |---|---|---|
  | Mayor (citywide, executive) | **Troy K. Walker** | presides; **non-voting** on council |
  | Council (at-large) | **Mike Green** | |
  | Council (at-large) | **Bryn Heather Johnson** | |
  | Council (at-large) | **Tasha Lowery** | (2024 Res. #24-65 elected her Mayor **pro tempore**) |
  | Council (at-large) | **Fred Lowry** | re-elected 2023 |
  | Council (at-large) | **Kathryn Dahlin** | **NEW 2025** — succeeded **Marsha Vawdrey** |

- **⚠ Roster drift 2024→2026:** the 2024-12-03 minutes name **Marsha Vawdrey** and **Fred Lowry**;
  the current site drops Vawdrey and adds **Kathryn Dahlin** (2025 winner). Build the roster/terms
  with Vawdrey serving through 2025 → Dahlin from Jan 2026. (Also note **T. Lowery** vs **F. Lowry**
  are two different members with near-identical surnames — resolve by full name, never surname.)
- **Mayor-vote determination (structural, resolved):** council–mayor executive form → Mayor **does
  NOT vote**, roll-call denominator = **5**. Confirmed by the named grid excluding the Mayor and the
  5-0 voice votes. Watch for a possible statutory mayoral **veto** (separate language, not a tally).

---

## 3. Planning Commission — Draper has its OWN PC (same Granicus portal)

- **Own Planning Commission** on the SAME `view_id=1` Granicus listing (303 minutes docs; landing
  also at `https://www.draperutah.gov/city-government/planning-commission/`).
- **Cadence: Thursday** (verified: every 2025 PC date is a Thursday; ~2nd & 4th Thursday).
- **Coverage:** PC minutes docs span well before the 2020 floor (hundreds of docs; 295/303 rows
  carry a minutes doc). 2020 floor fully covered.
- **Votes/recommendations — CONFIRMED PRESENT & NAMED** (2025-11-20 PC minutes, text-verified):
  - Named roll-call grid: **`Commissioner | Yes | No | Abstained | Not Participating | Absent`**;
    motion/second named; e.g. *"Motion: Commissioner Fowler moved to APPROVE the Conditional Use
    Permit … application 2025-0253-USE … Second: Commissioner Shirey … Vote on Motion: 4-to-0 in
    favor."*
  - **Land-use CASE NUMBERS keyed `YYYY-NNNN-<TYPE>`** (e.g. `2025-0253-USE`) — a case-number city
    (West-Valley-like) → usable for PC→Council referral linkage.
  - **PC→Council recommendation language present** (*"forwarded a positive recommendation with a
    unanimous vote"*, *"present the item to the City Council"*) — cross-body referrals reconstructable.
  - PC roster 2025: Andrew Adams (Chair), Lisa Fowler (Vice-Chair), Kendra Shirey, Mary Squire,
    Susan Nixon, Gary Ogden + alternates (Christine Green, Laura Fidler, Shivam Shah).

---

## 4. Public comments

**Verdict: inline-in-minutes speaker notes; no separate published written-comment archive located
(do NOT conclude "unavailable" — auditor's call during acquisition).**
- Both Council and PC minutes carry a **"Public Comments"** agenda item and **transcribe in-person
  speakers inline** (clerk paraphrase, often **with the speaker's address**, e.g. *"Gus Bernardo
  gave his address as 13608 South Sher Lane and stated that he moved to Draper…"*). These are
  **meeting-record speaker notes, NOT genuine written comments** → a labeled `minutes_speaker_log.csv`,
  never `all_comments_clean.csv`.
- **No dedicated eComment / Open City Hall / "correspondence received" archive surfaced.** The site
  offers a GRAMA "request records" form + a "search all online records" portal (records requests,
  not a comment feed). Public comment is taken **in-person / via Granicus livestream**.
- **Phase-2 leads before declaring none:** check whether Granicus **Agenda Packets** bundle written
  correspondence, and whether any meeting has a Granicus **eComment** tab.

---

## 5. Elections + the two-county wrinkle

### Administering county — **Salt Lake County runs the WHOLE Draper municipal election**
- Draper physically straddles Salt Lake + Utah counties, but under Utah law the county with the
  greater share of the city's registered voters is the election officer and administers the entire
  city race. Evidence this is **Salt Lake County** for Draper's mayor/council contests:
  1. **Utah County's 2025 results list NO Draper mayor/council contest** (only a "Draper Reporting"
     PDF for **"Aspen Peaks Seat 4"** — a school/special-district item, not a city race).
     `https://vote.utahcounty.gov/results/2025`
  2. Official live results for Draper mayor/council are published under **Salt Lake County** on
     `electionresults.utah.gov` (e.g. 2023 & 2025 Draper contests under `.../salt-lake-county-ut/`).
  3. The canonical **`salt_lake_county/elections/slco_municipal_results_long.csv` ALREADY contains
     Draper's council + mayor contests, 2007–2025** (confirmed — see below), and these SL-County
     totals ARE the whole-city totals.
- **→ No Utah-County gap for Draper CITY (mayor/council) races.** The only Utah-County-administered
  Draper item found in the archive is a **2011 "Utah County Draper Bond"** (a bond/special-service-
  district item for the Utah-County portion — Traverse Ridge SSD-type). **Two-county records matter
  for bonds/special districts + GIS/precincts, NOT for the council/mayor election data.**

### Existing canonical archive coverage (confirmed in `slco_municipal_results_long.csv`)
Filter on the **`contest` text `%DRAPER%`** (label style drifts across years):

  | Year | Draper council/mayor contests present | Notes |
  |---|---|---|
  | 2007 | Council At Large (primary + general) | clean |
  | 2009 | Council At Large + **Mayor** | |
  | 2011 | Council @ Lg (+ **Utah County Draper Bond**) | the sole Utah-County row |
  | 2013 | Council At Large + **Mayor** | |
  | 2015 | Council At Large | |
  | 2017 | Council At Large + **Mayor** | |
  | **2019** | **NONE — 0 rows (PROBABLE GAP)** | see below |
  | 2021 | Council At-Large + **Mayor** | |
  | 2023 | Council At-Large (winners **Fred Lowry, Cal Roberts, Bryn Heather Johnson** — 3 seats) | |
  | 2025 | Council At-Large **(2-YEAR TERM)** + **Mayor** | 2yr = short/unexpired term |

- **⚠ 2019 gap:** **0 Draper rows for 2019** — the same failure mode seen for Taylorsville / South
  Jordan / Millcreek 2019 (numbered-sheet SOVC layout dropped the city string). Draper's 2015→2019→2023
  cycle should carry ~3 at-large seats in 2019. **Flag for raw-2019-SLCo-SOVC re-parse; whether a
  2019 Draper council election was held is UNCONFIRMED until the raw sheet is checked** (treat as a
  probable gap, not a certainty).
- **⚠ 2025 "(2 YEAR TERM)":** a short/unexpired-term seat off the normal 4-yr cycle — note it in the
  `note` column so member-term logic doesn't read it as a cycle shift.
- Winners are UPPER-CASE with occasional suffixes — normalize before joining to the minutes roster
  (`FRED LOWRY`→Lowry, `TROY K. WALKER`→Mayor, etc.).

---

## 6. GIS — **NO council districts (at-large)**; election precincts span BOTH counties

- **Draper elects at-large → there are NO council-district polygons to build.** An address→rep tool
  is trivial: every Draper resident's representatives = all 5 at-large members + the Mayor. The only
  boundary that matters is the **city limit** (which itself crosses the SL/Utah county line).
- **City outline:** UGRC **Utah Municipal Boundaries** `NAME='DRAPER'`
  (`services1.arcgis.com/99lidPhWCzftIe9K/.../UtahMunicipalBoundaries/FeatureServer/0`).
- **Precinct / ballot-area coverage MUST union BOTH counties** (the task's core GIS caveat):
  UGRC **VistaBallotAreas** internal **`CountyID = 18` (Salt Lake)** AND **`CountyID = 25` (Utah)**
  (UGRC's alphabetical county numbering; equivalently FIPS **49035** Salt Lake + **49049** Utah).
  A single-county pull would miss the Utah-County (Traverse Mountain/SunCrest) precincts of Draper.
- **SL-County precinct geometry** is already shipped in the sibling archive
  (`salt_lake_county/elections/…` / any `slco_precincts_current.geojson`); the **Utah-County
  precincts** would need a separate UGRC/Utah-County pull if precinct-level Draper analysis is wanted.
- Salt Lake County & Utah County open-data ArcGIS portals are further fallbacks for municipal/precinct
  polygons.

---

## Retrieval plan (recommended order)

1. **Council minutes 2020→present (Granicus):** enumerate `ViewPublisher.php?view_id=1`, filter
   rows where body cell = `City Council` (+ `City Council Meeting`/Special/Retreat), parse the
   **Documents Selector `<option value>`** list, **resolve to the "… Minutes" doc (drop the "Recap")**,
   curl each `MinutesViewer.php?...&doc_id=` as a **PDF** (browser UA) → `raw/minutes/<year>/`.
   Born-digital text → markdown.
2. **Council vote extraction:** parse `Councilmember X moved … seconded by Councilmember Y … A roll
   call vote was taken` + the **Yes/No/Absent named grid** (max tally **5**, **Mayor non-voting**;
   `T. Lowery` ≠ `F. Lowry`). Handle unanimous grids (all X in Yes). Verify No-column on a contested
   meeting.
3. **RDA / MBA / CRA / HPC:** SEPARATE Granicus bodies on the same view — acquire as distinct
   `body=` rows (do NOT model RDA as in-recess).
4. **Planning Commission 2020→present:** same portal, body = `Planning Commission` (Thursday).
   Capture the `Commissioner|Yes|No|Abstained|Not Participating|Absent` grid, the `YYYY-NNNN-<TYPE>`
   case numbers, and PC→Council recommendation language for the referral layer.
5. **Comments:** grep Agenda-Packet docs + any eComment tab; otherwise build a labeled
   `minutes_speaker_log.csv` + record the honest verdict (submit-only / inline).
6. **Elections:** reuse `salt_lake_county/elections/slco_municipal_results_long.csv` (filter
   `contest LIKE '%DRAPER%'`; SL County = whole-city totals). **Re-parse the raw 2019 SLCo SOVC**
   for Draper at-large; flag the **2025 "2-year term"** short seat and the **2011 Utah-County bond**.
7. **Geo:** city outline only (at-large — no districts); if precinct analysis is needed, union
   VistaBallotAreas CountyID **18 + 25**.

---

## Risks / blockers

- **Recap-vs-Minutes trap (HIGH):** recent meetings publish a tally-only **"Recap"** alongside the
  full **"Minutes"**; both are `MinutesViewer` docs behind a JS **Documents Selector**. Feeding the
  Recap to the extractor would silently lose mover/seconder + named roll call. Resolve to the
  "Minutes" option every time; where only a Recap exists (very newest meetings pre-adoption), log it
  and re-fetch after the minutes are adopted.
- **Granicus `MinutesViewer.php` serves a PDF, not HTML** — save with `.pdf` and treat as binary
  (don't tag-strip). Confirmed born-digital, no OCR.
- **Mayor is executive & does NOT vote (max tally 5)** — confirmed; watch for a mayoral veto.
- **At-large, not districts** — no district geo; but two-county precinct coverage needs CountyID 18+25.
- **2019 election gap** (0 Draper rows) — raw SLCo SOVC re-parse; election-held status unconfirmed.
- **T. Lowery vs F. Lowry** near-identical surnames — resolve by full name (per repo policy).
- **Roster drift** Vawdrey→Dahlin (2025) — set term boundaries correctly.
- **Site behind Azure edge** — returned 200 to a browser UA this recon (no 403), but keep the browser
  UA; Granicus (`draper.granicus.com`) fetched fine without issue.

---

## Key URLs (quick index)

| What | URL |
|---|---|
| City site (custom CMS) | https://www.draperutah.gov/ |
| Council agendas & minutes landing | https://www.draperutah.gov/city-government/mayor-and-council/agendas-and-minutes/ |
| **Granicus meetings listing (ALL bodies)** | https://draper.granicus.com/ViewPublisher.php?view_id=1 |
| Minutes doc pattern (returns PDF) | https://draper.granicus.com/MinutesViewer.php?view_id=1&clip_id=\<clip\>&doc_id=\<uuid\> |
| Agenda pattern | https://draper.granicus.com/AgendaViewer.php?view_id=1&clip_id=\<clip\> |
| Council minutes sample (verified, FULL) | MinutesViewer clip_id=1819 doc_id=17e18ae0-ce13-11ef-a9e2-005056a89546 (2024-12-03) |
| Council "Recap" sample (tally-only) | MinutesViewer clip_id=1989 doc_id=69cd4cfc-d066-11f0-bb28-005056a89546 (2025-12-02) |
| PC minutes sample (verified) | MinutesViewer clip_id=1988 doc_id=edffe79f-fd32-11f0-bb28-005056a89546 (2025-11-20) |
| Mayor & Council page | https://www.draperutah.gov/city-government/mayor-and-council/ |
| Planning Commission | https://www.draperutah.gov/city-government/planning-commission/ |
| Elections (city; links BOTH county clerks) | https://www.draperutah.gov/city-government/elections/ |
| SL County live results | https://electionresults.utah.gov/ (Draper under salt-lake-county) |
| Utah County results (NO Draper city race) | https://vote.utahcounty.gov/results/2025 |
| Canonical election archive (Draper 2007–2025; 2019 GAP) | /Users/tysonwelsh/civic-data/salt_lake_county/elections/slco_municipal_results_long.csv |
| Council election code (2-6-020) | https://codelibrary.amlegal.com/codes/draperut/latest/draper_ut/0-0-0-25006 |
| Utah PMN (fallback) | https://www.utah.gov/pmn (Draper entity) |
| Saved confirmation PDFs | /Users/tysonwelsh/civic-data/draper_city_council/meeting_minutes/raw/ |

```json
{"vendor":"Granicus (draper.granicus.com, view_id=1; general-site CMS is a separate custom/GovBuilt-style Azure-hosted site)","minutes_landing_url":"https://draper.granicus.com/ViewPublisher.php?view_id=1 (also https://www.draperutah.gov/city-government/mayor-and-council/agendas-and-minutes/)","minutes_url_pattern":"https://draper.granicus.com/MinutesViewer.php?view_id=1&clip_id=<clip>&doc_id=<uuid> -> returns raw PDF bytes; recent meetings expose BOTH a 'Recap' (tally-only) and full 'Minutes' via a JS Documents Selector <option value>","coverage_years":"Council 2012-2026 on Granicus; PC pre-2020->2026; 2020 floor fully covered on city portal","format":"born-digital clean text PDF (no OCR)","votes_in_minutes":true,"vote_style":"FULL minutes: mover+seconder named + per-member Yes/No/Absent roll-call grid (max tally 5, mayor non-voting); RECAP docs are tally-only ('approved 4-0', no names) - resolve to Minutes doc","pc_portal":"same Granicus view_id=1 (body=Planning Commission); landing https://www.draperutah.gov/city-government/planning-commission/","pc_coverage":"pre-2020 -> 2026; named roll-call grid (Commissioner|Yes|No|Abstained|Not Participating|Absent); land-use case numbers YYYY-NNNN-<TYPE>; PC->Council recommendation language present","council_weekday":"Tuesday (1st & 3rd; Study + Business session in one minutes doc)","num_districts":0,"at_large_seats":5,"mayor_votes":false,"current_members":["Mayor Troy K. Walker (executive, non-voting)","Mike Green (at-large)","Bryn Heather Johnson (at-large)","Tasha Lowery (at-large)","Fred Lowry (at-large)","Kathryn Dahlin (at-large, new 2025, succeeded Marsha Vawdrey)"],"comments_published":"inline-in-minutes speaker notes only (with speaker addresses); no separate eComment/correspondence archive found - submit-only/in-person + Granicus livestream (auditor's call; check agenda packets + eComment tab in Phase 2)","election_admin_county":"Salt Lake County (administers the WHOLE Draper mayor/council election; Utah County reports NO Draper city race)","two_county_notes":"Draper straddles Salt Lake (FIPS 49035) + Utah (FIPS 49049) counties; city elections page links BOTH clerks. Canonical slco_municipal_results_long.csv ALREADY holds Draper council+mayor 2007-2025 (SL totals = whole-city totals) with a 2019 GAP (0 rows - probable numbered-sheet drop, needs raw SOVC re-parse; election-held status unconfirmed). Only Utah-County-run Draper item found = a 2011 'Utah County Draper Bond' (special-district/bond, NOT city race). Two-county records matter for bonds/special districts + GIS precincts, not council/mayor data.","gis_source":"NO council districts (at-large) -> no district polygons; city outline via UGRC Utah Municipal Boundaries NAME='DRAPER'. For precinct/ballot-area coverage UNION VistaBallotAreas CountyID 18 (Salt Lake) + 25 (Utah) (FIPS 49035 + 49049); SL precinct geojson already in salt_lake_county archive, Utah-County precincts need a separate pull","blockers":["Recap-vs-Minutes trap: recent meetings ship a tally-only Recap beside the full Minutes behind a JS Documents Selector - always resolve to the Minutes doc","MinutesViewer.php serves PDF bytes (save .pdf, don't tag-strip)","mayor non-voting (max tally 5) - watch for veto","2019 Draper election gap - raw 2019 SLCo SOVC re-parse; whether an election occurred unconfirmed","2025 council seat is a 2-YEAR (short/unexpired) TERM - flag in note col","T. Lowery vs F. Lowry near-identical surnames - resolve by full name","roster drift Vawdrey->Dahlin 2025","site behind Azure edge (200 w/ browser UA this recon; keep UA)"],"confidence_notes":"HIGH on vendor/portal, born-digital format, Tuesday cadence, named roll-call grids for BOTH council & PC, mayor-non-voting (all text-verified against real 2024-12-03 council + 2025-11-20 PC minutes in raw/), at-large structure (0 districts, election labels + code), and SL-County-administers-whole-city (Utah County 2025 has no Draper city race). MEDIUM/flagged: 2019 election gap (needs raw re-parse), comments-published verdict (no eComment tab checked), exact staggering of the 5 at-large seats. RDA/MBA/CRA/HPC exist as separate Granicus bodies (counts confirmed, vote format not text-verified this recon)."}
```
