# Holladay City, Utah — Civic Data Recon

**City:** Holladay City, **Salt Lake County**, Utah (~34k pop.)
**Recon date:** 2026-07-11
**Scope of interest:** 2020–present (floor 2020 — city **incorporated 1999**, so full
modern history exists; 2020 is a normal floor, not an incorporation edge like Millcreek).
**Form of government:** **Council–Manager form** (UCA 10-3b). Five council members elected
**by district (D1–D5)** + a **Mayor elected at-large**; a **City Manager** is the chief
administrative officer. → **CONFIRMED FROM A REAL ROLL CALL: the Mayor VOTES.** Mayor Rob
Dahle is named in every per-member roll call in the 2025-12-04 minutes (`Mayor Dahle-Yes`),
so a full council roll tops out at **6** (5 members + Mayor). This is the **opposite of
Taylorsville** (executive-mayor, tally 5) and matches Millcreek (mayor votes). See §2/§4.
**Official site:** `https://holladayut.gov/` — **Revize** CMS ("The Government Website
Experts" in footer). `cityofholladay.com` **301-redirects** to `holladayut.gov` (still the
recorder's email domain: `@cityofholladay.com`). Fetches succeeded with a browser UA; no
hard bot-block observed this recon (use the browser UA anyway).

---

## 1. Council meeting minutes

Holladay publishes minutes across **THREE parallel channels** — use PMN as the reliable
deep-archive spine, the SuiteOne portal / Revize Document Center as the city-native copies.

### (a) Utah Public Notice (PMN) — the reliable machine-readable spine ✅ PRIMARY
- **Council public body id = 388**: `https://www.utah.gov/pmn/sitemap/publicbody/388.html`
  (entity "Holladay"; recorder Stephanie Carlson, `scarlson@cityofholladay.com`).
- **Minutes/agenda/packet PDFs:** `https://www.utah.gov/pmn/files/<fileId>.pdf`
  - **VERIFIED council minutes: `https://www.utah.gov/pmn/files/1375573.pdf`** = the
    **2025-12-04** City Council minutes (saved to `meeting_minutes/raw/`).
  - Other seen: `1402249.pdf` (2026-02-05 mins), `1442031/1446063/1459527.pdf` (2026 packets).
- Every meeting is noticed here; minutes are attached as notice **revisions**. Coverage
  reaches well before 2020 (city incorporated 1999). **Recommended source of record.**

### (b) SuiteOne meeting portal (city-native agenda/minutes system)
- **`https://holladayut.suiteonemedia.com/`** — vendor **SuiteOne** ("Powered by SuiteOne").
  Lists **9 bodies**: City Council, Planning Commission, **RDA Board**, **LBA** (Local
  Building Authority), Arts Council, Historical Commission, Admin Hearing Officer, Design
  Review Board, Tree Committee.
- **Doc URL pattern (agenda packets):**
  `https://holladayut.suiteonemedia.com/event/GetAgendaPacketFile/Packet?apid=<eventId>`
  (e.g. `apid=3070` = a 2024 PC packet). Minutes hang off each event page.
- **Coverage observed: 2025→2026 mainly** (past meetings extend "back to at least early
  2025"). ⚠ **Likely does NOT hold the full 2020–2024 archive** — use PMN (388) / Revize
  archive for those years. *(Confirm the SuiteOne back-catalog depth at acquisition.)*

### (c) Revize Document Center (holladayut.gov)
- Landing: **`https://holladayut.gov/government/agendas_and_minutes.php`** ("E-packets and
  minutes … posted on the Agendas and Minutes portion of the City's website").
- Static file paths like `Document Center/Agendas And Minutes/City Council/<year>/…pdf`.
  Page carries an **Archive** link and a per-year "mtg schedule" PDF. *(The exact archive
  index URL 404'd on a naive guess — enumerate from the live landing page; the Revize
  Document Center holds the year folders.)*

### Format — CONFIRMED born-digital clean text PDF (NO OCR)
`pdftotext -layout` on the 2025-12-04 council minutes yields clean, selectable, line-numbered
text; proper names intact (`Rob Dahle, Mayor`, `Gina Chamness, City Manager`, council
members). **Not scanned.** Read/pdftotext parse directly.

### Meeting cadence — **THURSDAY** (verified)
- Council minutes header: **"Thursday, December 4, 2025, 6:00 p.m., City Council Chambers,
  4580 South 2300 East."** Each meeting-day = a **5:30 pm Briefing Session** + a **6:00 pm
  Regular Meeting**, captured in **one combined minutes doc** (both attendance blocks in one
  PDF, verified). PMN 2026 council notices are all Thursdays.
- **Frequency: ~twice monthly, Thursdays, but the schedule VARIES** (PMN shows council
  meetings on 2026-06-04 **and** 2026-06-11 — consecutive Thursdays — plus a 2025-12-18 short
  Council+RDA meeting). The city sets it annually via a **"<year> mtg schedule.pdf"** on the
  portal. Do NOT hard-code 1st/3rd — harvest the actual dates. Holladay joins Park City &
  St. George as a **Thursday** city.

### Roll-call votes in minutes — CONFIRMED PRESENT, **NAMED per-member roll** (Millcreek-style)
Motions record **mover + seconder + a per-member named roll call including the Mayor** — NOT
a narrative tally. Verified quote (2025-12-04, Ordinance 2025-22, Wildland Urban Interface
overlay):
> *"Council Member Gray moved to APPROVE Ordinance 2025-22 … Council Member Quinn seconded
> the motion. Vote on Motion: Council Member Gray-Yes; Council Member Quinn-Yes; Council
> Member Fotheringham-Yes; Council Member Durham-Yes; Council Member Brewer-Yes; **Mayor
> Dahle-Yes**. Ordinance 2025-22 was adopted by a unanimous vote."*

- **Six names in the roll (5 members + Mayor) — the Mayor is a voting member.** Consent/
  procedural motions use *"passed with the unanimous consent of the Council"* (no per-member
  list); substantive ordinances/resolutions get the full named `Name-Yes/No` roll. → the
  extractor should parse the `Vote on Motion: <Name>-Yes; …` grammar; **max tally = 6**.
- ⚠ The verified motions were all unanimous → the **dissent token** (`-No`/`-Nay`/abstain
  wording) is inferred, not yet observed. Pull a contested rezone/budget hearing to lock it.

---

## 2. Council structure — 5 districts + at-large Mayor; **Mayor VOTES** (max tally 6)

- **5 council districts (D1–D5)**, one member each; **Mayor elected at-large**; **non-partisan**
  ("(NP)" suffixes in election data). **Council–Manager** form → City Manager (**Gina
  Chamness**) is the executive; the **Mayor presides over and VOTES on the council**.
- ⚠ **ROSTER TRANSITIONED at the Jan-2026 seating** (the 2025 election reshaped the body):

  | Seat | **CURRENT (seated Jan 2026)** | Prior (2025 record) |
  |---|---|---|
  | Mayor (at-large) | **Paul Fotheringham** (won 2025 mayor; was D3 CM) | Rob ("Rob"/"Robert M.") Dahle |
  | District 1 | **David Sundwall** (won 2025) | Ty (D. Ty) Brewer |
  | District 2 | **Matt Durham** (term→Jan 2028) | Matt Durham |
  | District 3 | **Natalie Bradley** (Natalie Bellamy Bradley, won 2025) | Paul Fotheringham |
  | District 4 | **Drew Quinn** (term→Jan 2028) | Drew Quinn |
  | District 5 | **Emily Gray** (term→Jan 2028) | Emily Gray |

  - Current roster verified against the **2026-02-05 minutes attendance block** (Mayor Paul
    Fotheringham; Gray, Quinn, Durham, **Bradley**, **Sundwall**). The 2025 roster verified
    against the **2025-12-04** minutes (Mayor Dahle; Gray, Fotheringham, Quinn, Durham, Brewer).
  - **Term stagger:** **D1, D3 + Mayor** on the 2013/2017/**2021/2025** cycle (expired Jan
    2026 → filled in Nov 2025); **D2, D4, D5** on the 2015/**2019/2023** cycle (→ Jan 2028).
    (This is why 2025 elected D1, D3, Mayor — see §5.)
- Council page: `https://holladayut.gov/government/mayor_and_council/city_council/index.php`
  (states "five council members, elected by districts, and the Mayor, elected at large";
  "Council-Manager form of government"). ⚠ Its roster may lag the Jan-2026 seating — trust the
  minutes attendance blocks.

### RDA / LBA — in-record + separate-body
Council convenes as the **Redevelopment Agency (RDA Board)** (e.g. the 2025-12-18 "City
Council and RDA Meeting"); RDA + **LBA** are also listed as their own bodies on SuiteOne.
Expect `body=RDA`/`body=LBA` tagging (in-meeting recess like Taylorsville, plus possible
separate SuiteOne events). No separate portal silo beyond SuiteOne/PMN.

---

## 3. Planning Commission — Holladay has its OWN PC (not the county)

- **Own Planning Commission**, same three channels. PMN public body **id = 389**
  (`https://www.utah.gov/pmn/sitemap/publicbody/389.html`; planner contacts Carrie Marsh
  `cmarsh@holladayut.gov` / Jonathan Teerlink `jteerlink@holladayut.gov`).
- **VERIFIED PC minutes doc: `https://www.utah.gov/pmn/files/1260737.pdf`** = **2025-04-01**
  Holladay PC minutes (saved to `meeting_minutes/raw/pc_2025-04-01_minutes.pdf`).
- **Cadence: TUESDAY** (2025-04-01, 2025-01-07, 2025-10-28, 2026-02-17, 2021-02-23 all
  Tuesdays), 6:00 pm regular (5:30 pm work session), City Council Chambers. ⚠ A few **2024**
  PC meetings ran on **Wednesday** — weekday is **modal-Tuesday, verify per date**.
- **Votes CONFIRMED PRESENT — NAMED per-member roll** (same grammar as council), verified
  quote (2025-04-01):
  > *"Commissioner Prince moved to APPROVE the application … Commissioner Gong seconded the
  > motion. Vote on Motion: Commissioner Berndt-Aye; Commissioner Gong-Aye; Commissioner
  > Prince-Aye; Commissioner Vilchinsky-Aye; Commissioner Cunningham-Aye; Chair Roach-Aye.
  > The motion passed unanimously."*
- PC members (2025-04-01): **Dennis Roach (Chair)**, Ginger Vilchinsky, Berndt, Gong, Prince,
  Cunningham (6-member commission). PC forwards **recommendations to the City Council** on
  zoning/text amendments and the General Plan ("Holladay Horizons" 2025 update) — a real
  cross-body referral chain to capture.
- Coverage reaches at least **2021** on PMN (e.g. `689145.pdf` = 2021-02-23 agenda); PC born-
  digital text like council.

---

## 4. Public comments — LIKELY SUBMIT-ONLY / inline-in-minutes (label: needs final confirmation)

- **No standalone published written-comment archive / eComment / Open City Hall surfaced.**
  Public comment is taken **in-person** at the meeting and via **emailed comments read aloud
  by the Chair** — PC agendas state: *"Email: comments must be received by 5:00 pm … to the
  Community and Economic Development Department; jteerlink@holladayut.gov. Emailed comments
  will be read by the Commission Chair."* These land as **paraphrased hearing-speaker notes
  inline in the minutes**, not a genuine written-comment corpus.
- **Provisional verdict: SUBMIT-ONLY / honest-empty** (like Taylorsville & South Jordan) →
  a labeled `minutes_speaker_log.csv`, never `all_comments_clean.csv`. ⚠ Before declaring
  none, grep the Revize site (`departments/city_recorder/notices.php`) and any council/PC
  **packets** for a "correspondence received" bundle. Auditor's call; don't hard-conclude
  "unavailable" without the packet check.

---

## 5. Elections — Salt Lake County; canonical archive ALREADY covers Holladay (2019 GAP)

- **Run by:** Salt Lake County Clerk (`https://www.saltlakecounty.gov/clerk/elections/`);
  live results `https://electionresults.utah.gov/` (Salt Lake County). Non-partisan.
- **The canonical repo file already has Holladay:**
  `/Users/tysonwelsh/civic-data/salt_lake_county/elections/slco_municipal_results_long.csv`
  — filter **`contest` text `LIKE '%HOLLADAY%'`** (label style drifts across years:
  `HOLLADAY CITY COUNCIL #4` / `DIST 3` / `CITY OF HOLLADAY COUNCIL DISTRICT 1` / `HOLLADAY
  CITY MAYOR`). **Years present: 2007, 2009, 2011, 2013, 2015, 2017, 2021, 2023, 2025.**
- **⚠ 2019 GENERAL IS ABSENT (0 rows)** — same failure mode seen for Taylorsville / South
  Jordan / Millcreek (the numbered-sheet SOVC layout dropped the city string). The 2015/2019/
  2023 cycle should carry **D2/D4/D5 in 2019** → **re-parse the raw 2019 SLCo SOVC** for
  Holladay D2/D4/D5.
- **Seat structure confirmed by the data:** 5 districts + at-large Mayor; **2025** elected
  **D1 (David Sundwall), D3 (Natalie Bradley), Mayor (Paul Fotheringham** over Watts/Wilson**)**;
  **2023** elected **D4 (Drew Quinn** vs Matthew Tracy**)**; **2021** = D1/D3/Mayor (Dahle).
  Winners are UPPER-CASE with `(NP)` suffixes → normalize before joining to the minutes roster.

---

## 6. GIS — Holladay has an OFFICIAL council-district ArcGIS layer (rare — no derive needed)

- **Official city ArcGIS Hub:** `https://city-of-holladay-holladay.hub.arcgis.com/`. The
  **"Holladay City Council Districts"** layer (item id **`d0cb510277ee4f0f989c9a5de4d0a6da`**,
  **"as amended 2022"**) is a real published district polygon layer — better than the
  precinct-derived fallback used for Taylorsville/South Jordan.
  - Hosting org: `https://services6.arcgis.com/mGvwEqK9FI5j4ecF/arcgis/rest/services`
    (also hosts `Holladay_Zoning_Map_WFL1`, `Holladay_Zoning_Parcels`, `Municipal_Boundaries`,
    dev-projects, WUI web map). ⚠ The districts layer sits under a generic/WFL service name —
    **resolve its exact `.../FeatureServer/<n>` endpoint from the Hub item at acquisition**
    (the item→service lookup, not the org service name list).
- **Precincts:** UGRC **Vista Ballot Areas**, Salt Lake **CountyID = 18**
  (`https://gis.utah.gov/products/sgid/political/voter-precincts/`); SL County Clerk election
  maps (`https://www.saltlakecounty.gov/clerk/elections/maps/`). City outline also in the org's
  `Municipal_Boundaries` and UGRC Municipal Boundaries `NAME='HOLLADAY'`.
- Note the **"as amended 2022"** vintage = post-2020-census lines; pre-2022 address→district
  questions may mis-assign near moved boundaries.

---

## Retrieval plan (recommended order)

1. **Council minutes 2020→present:** enumerate PMN body **388** (reliable deep archive) →
   `utah.gov/pmn/files/<id>.pdf`; cross-fill with the Revize Document Center year folders /
   SuiteOne events for 2025+. Browser UA. Combined Briefing+Regular = one doc/day. Born-digital
   → markdown (no OCR).
2. **Vote extraction (council):** parse `Vote on Motion: <Name>-Yes; …` named rolls (**max
   tally 6, Mayor VOTES**) + mover/seconder; consent motions → `names_recorded:false`. Confirm
   the dissent token on the first contested motion.
3. **Planning Commission 2020→present:** PMN body **389** / SuiteOne. Same named-roll grammar;
   capture PC→Council recommendation language + land-use case identifiers.
4. **RDA/LBA:** capture the in-recess RDA/LBA votes (SuiteOne separate events + in-council
   minutes) as `body=RDA`/`body=LBA`.
5. **Comments:** grep recorder notices + council/PC packets for written correspondence;
   otherwise build a labeled `minutes_speaker_log.csv` + record the SUBMIT-ONLY verdict.
6. **Elections:** reuse the canonical `salt_lake_county/elections/slco_municipal_results_long.csv`
   (`contest LIKE '%HOLLADAY%'`); **re-parse the raw 2019 SOVC** for D2/D4/D5.
7. **Geo:** pull the official **Holladay City Council Districts** FeatureServer (resolve endpoint
   from Hub item `d0cb510277ee4f0f989c9a5de4d0a6da`) → address→district tool; UGRC CountyID 18
   precincts as cross-check.

---

## Risks / blockers

- **Mayor VOTES (STRUCTURAL, resolved):** Council–Manager form → **Mayor is a voting council
  member, max tally = 6** (confirmed by the named roll `Mayor Dahle-Yes`). Sets every vote's
  denominator — do NOT copy Taylorsville's tally-5 assumption.
- **Jan-2026 roster turnover:** Mayor Dahle→**Fotheringham**; D1 Brewer→**Sundwall**; D3
  Fotheringham→**Bradley**. Any who-voted analysis must be date-aware across the seam.
- **Three-channel sprawl / SuiteOne shallow archive:** SuiteOne appears to hold only ~2025+;
  the **2020–2024 back-catalog depth on SuiteOne/Revize is unverified** → lean on **PMN 388/389**
  for the floor years. Confirm no 2020–2024 minutes gaps against PMN.
- **No contested vote observed:** verified motions were unanimous → dissent token unconfirmed.
- **PC weekday drift:** Tuesday is modal but some 2024 PC meetings fell on Wednesday — read the
  date, don't assume.
- **2019 election gap (D2/D4/D5):** raw-2019-SLCo-SOVC re-parse needed (shared archive dropped it).
- **Districts FeatureServer endpoint:** the official layer exists but its exact `.../FeatureServer/<n>`
  URL must be resolved from the Hub item (org service list uses a generic WFL name).
- **Web-search source mislabeling:** a PMN search result labeled "Holladay PC minutes 11/06/2024"
  was actually **Herriman** — always open the PDF header to confirm the city before ingesting.

---

## Key URLs (quick index)

| What | URL |
|---|---|
| City site (Revize; cityofholladay.com→301) | https://holladayut.gov/ |
| Council agendas & minutes landing | https://holladayut.gov/government/agendas_and_minutes.php |
| City Council page (structure/roster) | https://holladayut.gov/government/mayor_and_council/city_council/index.php |
| SuiteOne meeting portal (all 9 bodies) | https://holladayut.suiteonemedia.com/ |
| SuiteOne packet pattern | https://holladayut.suiteonemedia.com/event/GetAgendaPacketFile/Packet?apid=<eventId> |
| PMN — Council body 388 | https://www.utah.gov/pmn/sitemap/publicbody/388.html |
| PMN — Planning Commission body 389 | https://www.utah.gov/pmn/sitemap/publicbody/389.html |
| PMN file pattern | https://www.utah.gov/pmn/files/<fileId>.pdf |
| **Council minutes sample (verified)** | https://www.utah.gov/pmn/files/1375573.pdf (2025-12-04) |
| **PC minutes sample (verified)** | https://www.utah.gov/pmn/files/1260737.pdf (2025-04-01) |
| Elections (canonical, in-repo) | /Users/tysonwelsh/civic-data/salt_lake_county/elections/slco_municipal_results_long.csv (filter %HOLLADAY%; 2019 GAP) |
| SL County Clerk elections / maps | https://www.saltlakecounty.gov/clerk/elections/maps/ |
| Live results | https://electionresults.utah.gov/ (Salt Lake County) |
| **Council Districts (official ArcGIS)** | https://city-of-holladay-holladay.hub.arcgis.com/ (item d0cb510277ee4f0f989c9a5de4d0a6da, "as amended 2022") |
| ArcGIS hosting org | https://services6.arcgis.com/mGvwEqK9FI5j4ecF/arcgis/rest/services |
| UGRC voter precincts (CountyID 18) | https://gis.utah.gov/products/sgid/political/voter-precincts/ |

```json
{"vendor":"Revize (holladayut.gov website CMS) + SuiteOne (holladayut.suiteonemedia.com meeting portal) + Utah PMN (utah.gov/pmn, council body 388 / PC body 389) as the reliable machine-readable spine","minutes_landing_url":"https://holladayut.gov/government/agendas_and_minutes.php","minutes_url_pattern":"PMN: https://www.utah.gov/pmn/files/<fileId>.pdf (council body 388, PC body 389); SuiteOne agenda packets: https://holladayut.suiteonemedia.com/event/GetAgendaPacketFile/Packet?apid=<eventId>; Revize Document Center year folders","coverage_years":"incorporated 1999; PMN 388/389 reliable back through/well before the 2020 floor; SuiteOne shallow (~2025+); confirm 2020-2024 depth on PMN","format":"born-digital clean text PDF (pdftotext clean, names intact; no OCR)","votes_in_minutes":true,"vote_style":"NAMED per-member roll call in minutes body ('Vote on Motion: Council Member Gray-Yes; ...; Mayor Dahle-Yes') incl. the Mayor; consent/procedural motions unnamed ('unanimous consent of the Council'); Millcreek-style named roll, NOT narrative tally; dissent token unconfirmed (all verified motions unanimous)","pc_portal":"same 3 channels; PMN body 389; Holladay has its OWN Planning Commission","pc_coverage":"PMN reaches >=2021 (verified 2025-04-01 minutes); named-roll votes confirmed","council_weekday":"Thursday (5:30pm Briefing + 6:00pm Regular in one combined minutes doc; ~twice monthly but schedule VARIES - harvest actual dates, do not assume 1st/3rd)","num_districts":5,"at_large_seats":0,"mayor_votes":true,"max_tally":6,"current_members":["Mayor Paul Fotheringham (at-large, won 2025, VOTES)","D1 David Sundwall (won 2025)","D2 Matt Durham (term to Jan 2028)","D3 Natalie Bradley (won 2025)","D4 Drew Quinn (term to Jan 2028)","D5 Emily Gray (term to Jan 2028)"],"prior_members_2025":["Mayor Rob Dahle","D1 Ty Brewer","D3 Paul Fotheringham (before becoming mayor)"],"comments_published":"NO (provisional) - submit-only / inline-in-minutes speaker notes; emailed comments read aloud by Chair; no standalone written-comment archive found (check recorder notices + packets before final honest-zero call)","gis_source":"OFFICIAL Holladay City Council Districts ArcGIS layer (Hub item d0cb510277ee4f0f989c9a5de4d0a6da, 'as amended 2022'; org services6.arcgis.com/mGvwEqK9FI5j4ecF - resolve exact FeatureServer endpoint from Hub item); precincts UGRC Vista Ballot Areas CountyID 18 + SL County Clerk","form_of_government":"Council-Manager (City Manager Gina Chamness is chief administrator; Mayor presides AND votes)","rda_lba":"Council convenes as RDA (in-recess) + LBA; both also listed as SuiteOne bodies; tag body=RDA/LBA","blockers":["mayor VOTES - max tally 6 (do NOT copy Taylorsville tally-5)","Jan-2026 roster turnover: Dahle->Fotheringham mayor, Brewer->Sundwall D1, Fotheringham->Bradley D3 - date-aware joins","SuiteOne archive shallow (~2025+) - lean on PMN 388/389 for 2020-2024; verify no floor-year gaps","no contested vote observed - dissent token unconfirmed","2019 election general absent from canonical archive (D2/D4/D5) - re-parse raw SLCo 2019 SOVC","PC weekday modal-Tuesday but some 2024 meetings Wednesday - verify per date","districts FeatureServer endpoint must be resolved from ArcGIS Hub item","web-search PMN results can mislabel other cities (a 'Holladay' PC result was actually Herriman) - verify PDF header city before ingest"],"confidence_notes":"CONFIRMED from real PDFs: council minutes 2025-12-04 (PMN 1375573; Thursday; named roll incl. Mayor Dahle-Yes -> mayor VOTES, tally 6) and PC minutes 2025-04-01 (PMN 1260737; Tuesday; named roll incl. Chair Roach-Aye). Both saved to meeting_minutes/raw/. Structure, form-of-government, current+prior roster all confirmed against minutes attendance blocks + council page + 2021/2023/2025 election winners. Elections coverage read directly from the canonical CSV (2019 gap real)."}
```
