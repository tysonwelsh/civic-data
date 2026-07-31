# Murray City, Utah — Civic Data Recon

**City:** Murray City, **Salt Lake County**, Utah (~50k pop.)
**Recon date:** 2026-07-11
**Scope of interest:** 2020-01-01 → present (floor 2020 — Murray is a long-incorporated
city (1902); 2020 is a normal floor, full modern history exists).
**Form of government:** **Council–Mayor (executive-mayor / "strong mayor") form.** Five
council districts (D1–D5, no at-large), a separately-elected **executive Mayor** (Brett
Hales), and a **Council Executive Director** (Jennifer Kennedy). The **council elects its
own Chair / Vice-Chair** to preside. → **The Mayor is the EXECUTIVE and does NOT vote on
ordinary council motions; max council roll-call tally = 5.** CONFIRMED against a real roll
call (§4). This matches Taylorsville / South Jordan (mayor non-voting), NOT Millcreek.
**Official site:** `https://www.murray.utah.gov/` — **CivicPlus / CivicEngage Central** CMS
(classic ASP.NET `Archive.aspx` / `AgendaCenter` / `DocumentCenter` chrome).
⚠ **Portal split:** the CivicPlus **Archive Center** is the primary store, but **2023 minutes
were diverted to a Tyler "Minutes Management" (TMM) SPA** — see §1. The site serves fine to a
browser UA over `curl` (no 403 seen this recon; unlike Taylorsville's Akamai edge).
**UPDATE 2026-07-16:** the TMM never needed cracking — the 2023 council minutes AND the
post-2022 PC minutes were recovered from **Utah Public Notice** (`pmn_backfill/`, entity 213)
and PROMOTED into the audited layers; both gaps described below are CLOSED (2023-07-11 was a
proven cancellation; PC 2025-04-17/2025-07-17 remain the only minute-less dates).

---

## 1. Council meeting minutes

### Portal — CivicPlus Archive Center (primary) + a Tyler TMM seam for 2023
- **Host:** `https://www.murray.utah.gov`
- **Human landing (instructions):** `https://www.murray.utah.gov/1683/Agendas-and-Minutes`
- **Minutes listing (the machine-harvestable index):**
  `https://www.murray.utah.gov/Archive.aspx?AMID=31` (**AMID 31 = "City Council Minutes"**).
  Each row links to a landing page `Archive.aspx?ADID=<n>`.
- **Minutes document URL pattern (CONFIRMED, direct PDF):**
  ```
  https://www.murray.utah.gov/Archive/ViewFile/Item/<ADID>
  ```
  The `ADID` from the listing **is** the `Item` id — e.g. ADID **8347** →
  `…/Archive/ViewFile/Item/8347` returns the **2026-06-16** council minutes PDF (verified);
  **7772** → the **2024-04-16** minutes (verified). Harvest the `ADID=<n>` links from the
  AMID=31 listing, then GET `Archive/ViewFile/Item/<n>` for each PDF. (The `ADID` landing page
  is HTML chrome; the `ViewFile/Item` URL is the actual file.)
- **Related council AMIDs on the same Archive Center** (harvest identically):
  `30` City Council Agendas · `83` City Council Agenda Packet · **`84` City Council Results
  (on-portal election canvasses)** · `45` Committee of the Whole Minutes.
- **Other in-record bodies** (same portal, same `ViewFile/Item` pattern — relevant, like
  sibling cities' RDA/MBA): **`61` Redevelopment Agency Minutes** (`62` agendas) ·
  **`46` Municipal Building Authority Minutes** (`47` agendas) · **`64` Murray City Center
  District Minutes** (`63` agendas) · **`95` Public Ordinance Adoption Archive** (adopted
  ordinances, for an expand-sources pass).

### Coverage (council minutes) — CONFIRMED by counting the AMID=31 listing
Archive Center holds **2006 → 2026**. Docs per year in the current listing:
`2020:22 · 2021:20 · 2022:30 · 2023:4 (SEAM) · 2024:22 · 2025:24 · 2026:10 (YTD).`
→ **2020, 2021, 2022, 2024, 2025, 2026 fully covered on the CivicPlus Archive Center.**

- ⚠ **2023 SEAM (KEY BLOCKER):** the AMID=31 listing carries only **4** of 2023 and prints a
  banner: *"All 2023 Minutes minutes will now be posted in TMM"* → **Tyler Minutes Management**
  at `https://cityofmurraycityuttmm.tylerhost.net/7452prod/tylermm/calendar/#/` (302→
  `cityofmurraycityuttmmapp.tylerhost.net/…`). This is a **JS SPA** (loads to "Meeting
  Manager… Loading…"; my `/tylermm/api/…` guesses 404'd) — **no static index, no obvious public
  JSON API found this recon.** The 2023-only diversion appears **temporary**: 2024–2026 council
  minutes are **back in the CivicPlus Archive Center** (verified downloads). → **Acquisition
  plan for 2023 must resolve TMM** (browser-driven harvest, or re-check whether the ~4 posted +
  PMN/agenda-packet route can backfill; treat any 2023 meeting not recoverable as an honest
  `minutes_unrecovered.csv` row until TMM is cracked).

### Format — CONFIRMED born-digital clean text PDF (NO OCR)
`pdftotext -layout` on **2024-04-16** and **2026-06-16** council minutes yields clean,
selectable text; proper names intact (`Brett Hales Mayor`, `Pam Cotter District #2 – Council
Chair`, `Adam Hock District #5 – Council Vice-Chair`). **Not scanned.** (No RICOH-scan seam
like Taylorsville observed in the sampled docs.)

### Meeting cadence — **Tuesday** (2× / month)
Council meets **Tuesdays, twice monthly**, **6:30 p.m.**, Council Chambers, Murray City Hall,
**10 East 4800 South** (older PC docs cite 5025 South State Street — building/address language
varies). Schedule: `https://www.murray.utah.gov/713/Council-Meeting-Schedule`. Livestream:
`http://www.murraycitylive.com` (+ Facebook `/Murraycityutah`).

### Roll-call votes in minutes — CONFIRMED PRESENT, **named per-member** (Millcreek-style)
Substantive motions print a **named roll call**, not just a tally (stronger than Taylorsville's
narrative style). Real example (2024-04-16 minutes):
> **MOTION:** Ms. Dominguez moved to adopt the joint resolution. Mr. Pickett SECONDED the motion.
> **Council Roll Call Vote:** Ms. Dominguez — Aye · Mr. Hock — Aye · Mr. Pickett — Aye ·
> Ms. Cotter — Aye · **Motion passed: 4-0**

- **Two motion grammars coexist:** (a) routine/consent items → *"Voice vote taken, all
  'Ayes.' Approved 4-0"* (mover + seconder named, no per-member list); (b) resolutions/
  ordinances/land-use → *"Council Roll Call Vote:"* with a **per-member Aye/Nay list** + a
  `Motion passed: N-M` line. Members are keyed by **honorific + surname** (`Mr. Pickett`,
  `Ms. Cotter`) — resolve to the district roster (§2).
- In the verified sample **Diane Turner (D4) was Excused**, so the roll was **4-0** with 4
  members; a full roll tops at **5**. The **Mayor is in the "Others" attendee block, never in
  a roll call** — confirms non-voting (§4).
- ⚠ Verified motions were unanimous; the **named-dissent pattern is UNCONFIRMED** — pull a
  contested rezone/budget meeting to lock the `Nay`/split-tally wording before bulk extraction.

---

## 2. Council structure — 5 districts + executive Mayor (Mayor does NOT vote)

- **5 council districts (D1–D5), one member each; NO at-large seats.** Mayor elected citywide
  as the **executive**. Non-partisan, 4-year staggered terms. Council **elects its own
  Chair/Vice-Chair** (a `Council Chair <Name>` is always one of the 5 members, never the Mayor).
- **Current roster** (from `https://www.murray.utah.gov/683/Council-Members`, Jan 2026 swear-ins):

  | Seat | Member | Term ends |
  |---|---|---|
  | Mayor (citywide, executive, **non-voting**) | **Brett A. Hales** | 2029 (re-elected 2025) |
  | District 1 | **Paul Pickett Acevedo** ("Mr. Pickett") | 2027 |
  | District 2 | **Pam Cotter** (was **Council Chair** in 2024) | 2029 |
  | District 3 | **Clark Bullen** (sworn Jan 2026; won the 2025 D3 2-yr special) | 2027 |
  | District 4 | **Diane Turner** (serving since 2014) | 2029 |
  | District 5 | **Adam Hock** (was **Vice-Chair** in 2024) | 2027 |

- **Roster drift inside the 2020→present window (must be handled):** the 2024 minutes show
  **Rosalba Dominguez (D3)** and Chair **Cotter** / Vice-Chair **Hock**; D3 then went vacant →
  **Scott Goodman appointed interim D3 (Jan 2025)** → **Clark Bullen** won the **2025 D3 2-year
  special** (mid-term vacancy). Expect additional 2020–2023 members in the early record — build
  the roster from the minutes attendance headers + election winners, don't assume the 2026 five.
- **⚠ MAYOR-VOTE DETERMINATION (structural, RESOLVED):** council–mayor executive form → Mayor
  **Brett Hales** appears only in the "Others"/attendee block and **casts no roll-call vote**;
  the council elects its own Chair to preside. **Build with max council tally = 5, Mayor
  non-voting** (like Taylorsville/South Jordan). Watch for a statutory **mayoral veto** (would
  surface as separate veto language, not a tally row).
- Council page: `https://www.murray.utah.gov/260/City-Council` ·
  Members: `https://www.murray.utah.gov/683/Council-Members`.

---

## 3. Planning Commission — Murray's OWN PC (same portal, different AMID)

- **Own Planning Commission**, minutes on the **same CivicPlus Archive Center**:
  - **Minutes listing:** `https://www.murray.utah.gov/Archive.aspx?AMID=33`
    (**AMID 33 = "Planning Commission Minutes"**) → same `Archive/ViewFile/Item/<ADID>` PDFs.
  - Agendas/attachments: `AMID=32`, plus a rotating recent page
    `https://murray.utah.gov/779/Agendas-Attachment`.
- **Cadence:** **Thursday, 6:30 p.m.** (confirmed in the doc header + agenda dates), Council
  Chambers.
- **Votes/recommendations — CONFIRMED PRESENT** (verified on **2022-11-17** PC minutes,
  born-digital clean text). Two grammars, like council: *"A voice vote was made, motion passed
  6-0"* and explicit *"Roll Call Vote:"* lists. Records mover/seconder, **findings of fact**,
  subdivision/land-use recommendations, and applicant presentations. PC is ~6–7 members
  (e.g. Vice Chair **Jake Pehrson**, Nay, Hacker, Richards, Patterson, Milkavich).
- **⚠ PC COVERAGE SEAM (KEY BLOCKER):** the AMID=33 Archive-Center listing **stops at 2022**
  (2011 → 2022; `2020:22 · 2021:20 · 2022:22`). **PC minutes for 2023, 2024, 2025, 2026 are
  NOT in the Archive Center** — they are presumably in **Tyler TMM** (same 2023 diversion) and/
  or only as agendas on the `/779/Agendas-Attachment` rotating page. → **PC 2023→present is the
  single biggest recovery gap**; resolve via TMM (browser-driven) + PMN cross-check; log any
  meeting not recoverable as `minutes_unrecovered.csv`. (Council came back to CivicPlus in 2024;
  PC apparently did not.)

---

## 4. Public comments

**Verdict: likely SUBMIT-ONLY / inline-in-minutes speaker notes; no standalone published
written-comment archive located** (do NOT declare unavailable — auditor's Phase-2 call).
- PC/council minutes invite comment **via email** (`planningcommission@murray.utah.gov`) and
  **in-person at meetings / livestream** (`murraycitylive.com`), and transcribe hearing speakers
  inline (clerk paraphrase) with an attendee (`Others:` / `Present:`) block — these are
  **meeting-record speaker notes, NOT genuine written comments** → a labeled
  `minutes_speaker_log.csv`, never `all_comments_clean.csv`.
- **No dedicated eComment / Open City Hall / "correspondence received" portal surfaced.**
- **Phase-2 leads before declaring none:** the **City Council Agenda Packet** archive
  (`AMID=83`) and PC attachments (`AMID=32`) may bundle emailed correspondence; grep those.

---

## 5. Elections — Salt Lake County (canonical file ALREADY covers Murray; DO NOT re-scrape)

**CONFIRMED:** `salt_lake_county/elections/slco_municipal_results_long.csv` already contains
Murray's contests — **7,592 candidate-rows** matching `MURRAY`. County = **Salt Lake
(CountyID 49035 / FIPS 49035)**. **District-based council (D1–D5) + citywide Mayor**, so the
seat structure the joins need is clean. Filter on the **`contest`** column
(`contest LIKE '%MURRAY%'`; some years carry duplicate UPPER/mixed-case rows — de-dup).

Murray contests present by year (from the file):

| Year | Murray contests present | Cycle |
|---|---|---|
| 2007 | Council **1, 3, 5** | D1/3/5 |
| 2009 | Council **2, 4** + **Mayor** | D2/4/Mayor |
| 2011 | Council **1, 3, 5** (dup case rows) | D1/3/5 |
| 2013 | Council **2, 4** + **Mayor** | D2/4/Mayor |
| 2015 | Council **1, 3, 5** | D1/3/5 |
| 2017 | Council **2, 4** + **Mayor** | D2/4/Mayor |
| **2019** | **NONE — 0 rows (GAP)** | should be D1/3/5 |
| 2021 | Council **2, 4** + **Mayor** | D2/4/Mayor |
| 2023 | Council **1, 3, 5** (dup case rows) | D1/3/5 |
| 2025 | Council **2, 4** + **Mayor** + **District 3 (2 YEAR TERM)** | D2/4/Mayor + D3 special |

- **In-scope (2020+) elections — 2021, 2023, 2025 — are ALL present.** No re-scrape needed.
- **⚠ 2019 general absent (Districts 1/3/5)** — same failure mode seen for Taylorsville /
  South Jordan / Millcreek 2019 (numbered-sheet layout dropped the city string). **Below the
  2020 floor**, but flag for the roster's pre-2020 term stagger; re-parse raw 2019 SOVC only
  if pre-floor member terms matter.
- **⚠ 2025 "District 3 (2 YEAR TERM)"** is a **SPECIAL / unexpired-term** race (the Goodman→
  Bullen mid-term vacancy) — off the normal D1/3/5 (2023/2027) cycle. Note it so member-term
  logic doesn't read it as a cycle shift.
- **Cycle:** D1/D3/D5 on 2023/2027; **D2/D4/Mayor** on 2021/2025/2029. Normalize UPPER-CASE
  election names before joining to the minutes roster (person + year + district).
- On-portal cross-check (secondary): **AMID=84 "City Council Results"** on the Archive Center.

---

## 6. GIS — Murray runs its OWN ArcGIS org (a district FeatureServer likely exists)

- **District Maps page:** `https://www.murray.utah.gov/368/District-Maps`.
- **Council district boundary PDF (2025):**
  `https://www.murray.utah.gov/DocumentCenter/View/16904/City_Council_Boundaries_2025`
  (verified — 1-page PDF, retained). Static reference; not machine boundaries.
- **Murray City ArcGIS org: `murraycity.maps.arcgis.com`** — the District-Maps page embeds
  four Instant-App viewers (appids `0a325fe8cdfd413d985fe5fc3b136d5b`,
  `19538ce2154a44699355942d75d73567`, `205857560c114e24abdce078a04c3cff`,
  `54d937a7384d469882a0a6f3707b5d96`). Because Murray hosts its own ArcGIS org, a **council-
  district FeatureServer very likely exists** (better than Taylorsville, which had none) —
  **Phase-2: query the org's REST catalog / open the appids to extract the district
  FeatureServer URL** and pull polygons directly.
- **Fallbacks (same as sibling SLCo cities):** derive District 1–5 polygons from the SOVC
  precinct rows over Salt Lake County precinct geometry; **UGRC VistaBallotAreas — Salt Lake
  County (CountyID 49035 per task; the sibling repos used UGRC internal `CountyID = 18` for Salt
  Lake — reconcile which field the service expects at query time)**; UGRC Municipal Boundaries
  `NAME='MURRAY'` for the city outline. Boundaries were **redrawn after the 2020 census**
  (current = the 2025 map) — an address near a moved line may mis-assign for pre-2022 questions.

---

## Retrieval plan (recommended order)

1. **Council minutes 2020→present:** harvest `ADID=<n>` from `Archive.aspx?AMID=31`, GET each
   `Archive/ViewFile/Item/<n>` (browser UA) → `raw/minutes/<year>/`. Fully covers 2020–2022 +
   2024–2026. **Resolve the 2023 TMM seam separately** (browser-driven TMM harvest; log
   unrecoverables).
2. **Council vote extraction:** parse both grammars — `Voice vote taken, all "Ayes." Approved
   N-M` (tally-only) **and** `Council Roll Call Vote:` per-member `Mr./Ms. <Surname> — Aye/Nay`
   + `Motion passed: N-M`. **Max tally 5, Mayor NON-voting.** `Present:`/`Excused:` header for
   attendance. Verify the dissent wording on the first contested motion.
3. **Planning Commission:** `Archive.aspx?AMID=33` (Thursday). **Archive stops at 2022 → 2023+
   is a TMM/agenda-only gap; recover via TMM + PMN** or log unrecovered. Extractor handles the
   voice-vote + `Roll Call Vote:` grammars; capture PC→Council recommendations + case/subdivision
   numbers + findings of fact.
4. **Other bodies (optional, additive):** RDA (`AMID=61`), MBA (`AMID=46`), Murray City Center
   District (`AMID=64`), Committee of the Whole (`AMID=45`) — same `ViewFile/Item` pattern.
   Adopted ordinances via `AMID=95` for an `expand-city-sources` pass.
5. **Comments:** grep Agenda Packet (`AMID=83`) + PC attachments (`AMID=32`) for emailed
   correspondence; otherwise build a labeled `minutes_speaker_log.csv` + record the honest verdict.
6. **Elections:** reuse `salt_lake_county/elections/slco_municipal_results_long.csv`
   (`contest LIKE '%MURRAY%'`, de-dup case rows); 2021/2023/2025 present; flag the **2025 D3
   2-yr special**; 2019 gap is below floor.
7. **Geo:** extract the council-district FeatureServer from `murraycity.maps.arcgis.com`
   (Instant-App appids above); fall back to precinct-derived polygons + UGRC → address→district
   tool.

---

## Risks / blockers

- **2023 TMM seam (MEDIUM–HIGH):** 2023 council minutes were diverted to a **Tyler Minutes
  Management SPA** (`cityofmurraycityuttmm.tylerhost.net/7452prod/tylermm/…`) with **no static
  index / no public API found** this recon. Needs browser-driven harvest or a PMN/agenda backfill.
- **PC 2023→present gap (HIGH):** the PC Minutes Archive Center **ends at 2022**; recent PC
  minutes are not in CivicPlus. Biggest single recovery gap — resolve via TMM + PMN, else honest
  `minutes_unrecovered.csv`.
- **Mayor-vote form (STRUCTURAL, RESOLVED):** council–mayor executive form → **Mayor does NOT
  vote, max tally = 5** (confirmed: Mayor in "Others" block, council elects its own Chair). Watch
  for a mayoral veto (separate language).
- **No named dissent observed:** verified motions were unanimous → contested-vote naming format
  UNCONFIRMED. Pull a rezone/budget hearing to lock the dissent parser.
- **Roster drift 2020→2026:** D3 churned (Dominguez → vacancy → Goodman interim 2025 → Bullen
  2025 special); build the roster from minutes attendance headers, not the 2026 five.
- **2019 election gap (D1/3/5) + 2025 D3 2-yr special:** 2019 below floor (re-parse raw SOVC
  only if needed); don't let the 2025 D3 special masquerade as a cycle change.
- **GIS field ambiguity:** reconcile the UGRC VistaBallotAreas county key (task says CountyID
  **49035**; sibling repos used internal **18** for Salt Lake) at query time; prefer the Murray
  ArcGIS org's own district FeatureServer if reachable.

---

## Key URLs (quick index)

| What | URL |
|---|---|
| City site (CivicPlus; served to browser UA over curl) | https://www.murray.utah.gov/ |
| Agendas & Minutes (human landing) | https://www.murray.utah.gov/1683/Agendas-and-Minutes |
| **Council Minutes listing (AMID 31)** | https://www.murray.utah.gov/Archive.aspx?AMID=31 |
| **Minutes/PDF pattern (CONFIRMED)** | https://www.murray.utah.gov/Archive/ViewFile/Item/&lt;ADID&gt; (e.g. /8347 = 2026-06-16) |
| Council Agendas / Packet / Results | Archive.aspx?AMID=30 / 83 / 84 |
| 2023 minutes (TMM SPA seam) | https://cityofmurraycityuttmm.tylerhost.net/7452prod/tylermm/calendar/#/ |
| Council Meeting Schedule (Tuesday) | https://www.murray.utah.gov/713/Council-Meeting-Schedule |
| Council Members roster | https://www.murray.utah.gov/683/Council-Members |
| **Planning Commission Minutes (AMID 33; ends 2022)** | https://www.murray.utah.gov/Archive.aspx?AMID=33 |
| PC Agendas/Attachments | https://www.murray.utah.gov/Archive.aspx?AMID=32 · https://murray.utah.gov/779/Agendas-Attachment |
| RDA / MBA / Ctr District / CoW minutes | Archive.aspx?AMID=61 / 46 / 64 / 45 |
| Adopted-ordinance archive | https://www.murray.utah.gov/Archive.aspx?AMID=95 |
| Livestream | http://www.murraycitylive.com |
| Elections (existing archive) | salt_lake_county/elections/slco_municipal_results_long.csv (contest LIKE '%MURRAY%') |
| District Maps page | https://www.murray.utah.gov/368/District-Maps |
| Council district boundary PDF (2025) | https://www.murray.utah.gov/DocumentCenter/View/16904/City_Council_Boundaries_2025 |
| Murray ArcGIS org | https://murraycity.maps.arcgis.com/ |
| Verified minutes samples (in raw/) | Item/7772 (2024-04-16 council), Item/8347 (2026-06-16 council), 2022-11-17 PC |

```json
{"city":"Murray","vendor":"CivicPlus/CivicEngage Central (Archive.aspx/DocumentCenter) + Tyler Minutes Management (TMM) SPA for 2023","minutes_landing_url":"https://www.murray.utah.gov/Archive.aspx?AMID=31","minutes_url_pattern":"https://www.murray.utah.gov/Archive/ViewFile/Item/<ADID> (ADID harvested from Archive.aspx?AMID=31; ADID==Item id, verified 7772=2024-04-16, 8347=2026-06-16)","coverage_years":"council 2006-2026 on CivicPlus (2020:22,2021:20,2022:30,2023:ONLY 4->TMM,2024:22,2025:24,2026:10); 2020-2022 & 2024-2026 fully covered on portal","format":"born-digital clean text PDF (no OCR in samples)","votes_in_minutes":true,"vote_style":"named per-member roll call ('Council Roll Call Vote:' Mr./Ms.<Surname> Aye/Nay + 'Motion passed: N-M') on resolutions/ordinances/land-use; 'Voice vote taken, all Ayes. Approved N-M' (mover+seconder, tally-only) on routine items; dissent format unconfirmed (samples unanimous)","pc_portal":"same CivicPlus Archive Center, Archive.aspx?AMID=33 (Planning Commission Minutes); same ViewFile/Item PDF pattern","pc_coverage":"2011-2022 in Archive Center; ARCHIVE STOPS AT 2022 -> 2023+ PC minutes are a TMM/agenda-only GAP; PC votes+recommendations+findings-of-fact confirmed present (2022-11-17)","council_weekday":"Tuesday (twice monthly, 6:30pm)","num_districts":5,"at_large_seats":0,"mayor_votes":false,"max_council_tally":5,"current_members":["Mayor Brett A. Hales (executive, non-voting)","D1 Paul Pickett Acevedo","D2 Pam Cotter (Chair 2024)","D3 Clark Bullen (won 2025 D3 2-yr special; prior: Dominguez->vacancy->Goodman interim 2025)","D4 Diane Turner","D5 Adam Hock (Vice-Chair 2024)"],"comments_published":"likely submit-only/inline speaker notes; no eComment/correspondence archive found; check Agenda Packet AMID=83 + PC attachments AMID=32 (Phase 2)","gis_source":"Murray runs own ArcGIS org murraycity.maps.arcgis.com (4 Instant-App appids on District-Maps page -> extract district FeatureServer); District_Council_Boundaries_2025 PDF DocumentCenter/View/16904; UGRC VistaBallotAreas Salt Lake (task CountyID 49035; sibling repos used internal 18 - reconcile); precinct-derived fallback","other_bodies_same_portal":{"RDA":"AMID=61/62","MBA":"AMID=46/47","Murray City Center District":"AMID=64/63","Committee of the Whole":"AMID=45","adopted_ordinances":"AMID=95","council_results_onportal":"AMID=84"},"elections":{"county":"Salt Lake (49035)","canonical_file":"salt_lake_county/elections/slco_municipal_results_long.csv (7592 MURRAY rows; filter contest LIKE '%MURRAY%')","in_scope_present":"2021,2023,2025 all present","structure":"D1-D5 by district + Mayor citywide; D1/3/5 cycle 2023/2027, D2/4/Mayor cycle 2021/2025/2029","flags":["2019 general absent (D1/3/5) - below floor","2025 'District 3 (2 YEAR TERM)' = special/unexpired-term","de-dup UPPER/mixed-case rows in 2011/2023"]},"blockers":["2023 council minutes diverted to Tyler TMM SPA - no static index/API found; browser-driven harvest or PMN backfill","PC minutes archive ENDS 2022 - 2023+ PC is a TMM/agenda-only gap (biggest recovery gap)","named-dissent vote format unconfirmed (samples unanimous)","D3 roster churn 2020-2026 (Dominguez/vacancy/Goodman/Bullen)","reconcile UGRC county-id field (49035 vs internal 18)"],"confidence_notes":"HIGH: vendor, ViewFile/Item pattern (2 council PDFs downloaded+parsed), 2020-2022/2024-2026 council coverage, born-digital format, named roll call, mayor non-voting (mayor in Others block, council elects own Chair), tally=5, Tuesday cadence, 5 districts/no at-large, PC on AMID=33 Thursday votes-present (1 PC PDF parsed), elections present 2021/23/25. MEDIUM/UNVERIFIED: TMM internals + whether 2023 council & 2023+ PC are recoverable there; contested-dissent wording; exact current PC roster; district FeatureServer URL (org exists, not opened); pre-2024 full council roster."}
```
