# Cottonwood Heights City, Utah — Civic Data Recon

**City:** Cottonwood Heights, **Salt Lake County**, Utah (~34k pop.)
**Recon date:** 2026-07-11
**Scope of interest:** 2020–present (floor 2020 — city **incorporated 2005**, so full modern
history exists; 2020 is a normal floor, not an incorporation edge like Millcreek).
**Form of government:** **Six-member council form (Utah "council-mayor"? — NO).** Cottonwood
Heights is a **4-district council + a separately-elected Mayor who VOTES.** The Mayor is a
full voting member of the council (max roll-call tally = **5**). → **CONFIRMED against a real
contested roll call** (§2). This is the key structural fact and it is the OPPOSITE of
Taylorsville/South Jordan (mayor non-voting) — do NOT copy their denominator.
**Official site:** `https://www.cottonwoodheights.utah.gov/` — **Granicus / CivicPlus
CivicEngage Central** CMS (`showpublisheddocument` doc pattern; "granicus" in page chrome;
`/DefaultContent/Default/` skin — same platform family as Taylorsville).
**Domains:** main portal `cottonwoodheights.utah.gov`; **`ch.utah.gov`** is a short **email
alias** (City Recorder = `recorder@ch.utah.gov` / `cityrecorder@ch.utah.gov`); **GIS lives on
`gis.chcity.org`** (city ArcGIS Server). All three are the same city.
⚠ **Site 403s a bare bot User-Agent AND a bare browser UA** — an Akamai-style edge requires a
**full browser header set** (Accept + Accept-Language + Sec-Fetch-Mode). `curl -A '<browser>'`
alone still 403s; add the headers below and it returns 200 (verified live this recon). WebFetch
is blocked → use the repo's `polite_fetch.py` (browser UA + headers) for every city-portal fetch.

```
Working header set (verified 200 on the CMS):
  -A 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
  -H 'Accept-Language: en-US,en;q=0.9'
  -H 'Sec-Fetch-Mode: navigate' --compressed
(PMN files at utah.gov/pmn/files/<id>.pdf download fine with the plain browser UA.)
```

---

## 1. Council meeting minutes

### Portal — Granicus / CivicPlus CivicEngage Central
- **Host:** `https://www.cottonwoodheights.utah.gov`
- **Agendas & Minutes landing:**
  `https://www.cottonwoodheights.utah.gov/your-government/elected-officials/council-meeting-agendas-and-minutes`
  (a second alias page exists at `/your-government/public-records-and-notices/agendas-and-minutes`
  but it is a thin pointer — use the elected-officials page.)
- **Structure:** a single Angular-rendered list, **three doc columns per meeting date**
  (**Agenda | Packet | Minutes**, sometimes "Cancelled"/"Amended Agenda"). Each meeting date =
  one **"Work Session and Business Meeting"** row (the work session + the business meeting are a
  combined event → the **Minutes** link is one PDF covering both — verified, see below).
- **Minutes document URL pattern (CivicEngage `showpublisheddocument`):**
  ```
  https://www.cottonwoodheights.utah.gov/home/showpublisheddocument/<docId>/<versionToken>
  ```
  (e.g. a Minutes link on the landing: `/home/showpublisheddocument/11186/639172294744630000`).
  Harvest the labeled `<a>Minutes</a>` anchors per meeting date — do NOT guess doc ids
  (they are not year-sequential). Agenda/Packet share the same pattern; keep only the **Minutes**
  anchor for the vote layer.
- **Coverage on the city portal — ROLLING ~4-5-YEAR WINDOW, not full history.** The landing
  lists Minutes for **~2022 → 2026 only** (date-label census: 2022≈4, 2023≈23, 2024≈28,
  2025≈24, 2026≈18). The page text states plainly: *"…are archived on this page. To review
  **older** agendas and minutes, please **submit a records request (GRAMA)**."* → **2020–2021
  council minutes are NOT on the live portal.**
- **➜ 2020–2021 fallback = Utah Public Notice (PMN)** (`utah.gov/pmn`). CH posts every meeting's
  agenda/minutes to PMN; minutes PDFs live at `https://www.utah.gov/pmn/files/<fileId>.pdf`
  (confirmed CH council minutes on PMN: **2024-01-16 = `1081987.pdf`**, **2024-10-15 =
  `1226779.pdf`** — both downloaded this recon). PMN is the recommended source for the
  **2020–2021 floor years** (and a general cross-check). The CH PMN public-body ids were not
  resolved this recon (the PMN JSON API 404'd) — **look them up at acquisition** the way
  Taylorsville did (council body 720): browse `utah.gov/pmn` → entity "Cottonwood Heights" →
  City Council / Planning Commission bodies. Alternatively GRAMA to `recorder@ch.utah.gov`.

### Format — CONFIRMED born-digital clean text PDF (no OCR garble)
`pdftotext -layout` on the **2024-01-16** and **2024-10-15** council minutes and the **2026-02-04
PC** minutes yields clean, selectable, well-structured text — proper names intact
(`Mayor Mike Weichers`, `Council Member Ellen Birrell`, `Chair Sean Steinman`). No scan/OCR
corruption seen (unlike Millcreek/Taylorsville's mid-2025 RICOH seam — **watch for a possible
OCR seam anyway** during bulk pull, but nothing observed 2024–2026).

### Roll-call votes in minutes — CONFIRMED PRESENT, **NAMED per-member (full attribution)**
This is a **named roll-call** city (NOT South-Jordan/Taylorsville narrative-tally). Every action
item prints each member's Yes/No. **CONFIRMED against a real CONTESTED (3-2) vote**, 2024-01-16
Business Meeting, Ordinance 407 (parking-hours amendment):
> *"Vote on Motion: **Council Member Holton - No, Council Member Hyland - Yes, Council Member
> Newell - No, Council Member Birrell - Yes, Mayor Weichers - Yes. The motion passed 3-to-2.**"*

- **The MAYOR VOTES and is counted in the tally** (Weichers cast the deciding "Yes" in the 3-2).
  A **full roll call names 5 people: the 4 council members + the Mayor.** → **max tally = 5,
  Mayor is a voting `person`.** (Same doc also has several unanimous action items that DO print
  each member Yes, plus routine "passed with the unanimous consent of the Council" motions for
  adjourn/minutes-approval where names aren't itemized.)
- **Mover + seconder are always named**; contested dissent is named inline; substitute/failed
  motions are recorded (e.g. Holton's substitute motion to table "failed for lack of a second").
- (An HB-176 discussion in the same minutes — "allows mayors to vote twice" — is a **state-bill
  briefing topic, not CH practice**; do not read it as a tie-break rule. CH's own roll calls
  show the mayor casting one ordinary vote.)

---

## 2. Council structure — 4 districts + a separately-elected **VOTING** Mayor (max tally 5)

- **4 council districts (Districts 1–4)**, one member each, **4-year staggered non-partisan
  terms**; **Mayor elected citywide** and **votes as a full member of the council** (no separate
  at-large council seats). **Council roll-call denominator = 5.**
- **Current roster (from the live Elected Officials page, 2026-07-11):**

  | Seat | Member | Term |
  |---|---|---|
  | Mayor (citywide, **voting**) | **Gay Lynn Bennion** | 2026–2029 |
  | District 1 | **Matt Holton** | 2024–2027 |
  | District 2 | **Suzanne Hyland** | 2024–2027 |
  | District 3 | **Shawn Newell** | (2022–)2026–2029 |
  | District 4 | **Ellen Birrell** | (2022–)2026–2029 |

  - Elected Officials page:
    `https://www.cottonwoodheights.utah.gov/your-government/elected-officials`
- **⚠ MAYOR TURNOVER at the 2020 floor's far end:** the roster in the **2024 minutes** had
  **Mayor Mike Weichers** (won 2021). **Gay Lynn Bennion won the 2025 mayoral race** and took
  office **Jan 2026** — so the mayor `person` changes mid-record. **Newell (D3)** and **Birrell
  (D4)** are continuous (won 2021, re-elected 2025 → terms run to 2029). **Holton (D1)** and
  **Hyland (D2)** won 2023 (terms to 2027). Build the roster with this drift; earlier-2020
  members (pre-2021 mayor/D3/D4 holders) must come from the 2020–2021 PMN minutes headers.
- **Term stagger (from the election archive, §6):** **D3, D4 + Mayor** on the **2021/2025**
  cycle; **D1, D2** on the **2023/2027** cycle. (Pre-2020 the district numbering ran 1–4 the same
  way; 2009/2013/2017 show Council 3/4 + Mayor, 2015 shows Council 1/2.)

---

## 3. Planning Commission — Cottonwood Heights has its OWN PC (not the county)

- **Own Planning Commission**, minutes on the SAME CivicEngage portal (confirmed, doc parsed):
  - Landing (Agendas, Packets, & Minutes):
    `https://www.cottonwoodheights.utah.gov/your-government/boards-and-commissions/planning-commission/agendas-packets-minutes`
  - Same `showpublisheddocument/<docId>/<versionToken>` doc pattern; **Agenda | Packet | Minutes**
    columns per date.
- **Coverage (portal):** same rolling window — Minutes visible **~2024 → 2026** on the live page
  (2024≈4, 2025≈27, 2026≈14 date-labels). **2020–2023 PC minutes → GRAMA or PMN fallback**
  (PMN "Cottonwood Heights City Planning Commission" body — id to resolve at acquisition;
  example PMN PC notice file `1398805.pdf`).
- **Cadence — WEDNESDAY** (from the parsed doc header): *"…PLANNING COMMISSION MEETING,
  Wednesday, February 4, 2026, 6:00 p.m., 2277 East Bengal Boulevard, City Council Chambers."*
  (Typically 1st & 3rd Wednesday — verify the exact weeks during acquisition.)
- **Votes — CONFIRMED PRESENT, NAMED per-member roll call** (verified on the **2026-02-04** PC
  minutes, `showpublisheddocument/10919/...`):
  > *"Vote on Motion: Commissioner Barnes-Yes; Commissioner Lugo-Yes; … Chair Steinman-Yes.
  > The motion passed with the unanimous consent of the Commission."*
  PC makes **recommendations to the City Council** (recommendation language + Conditions of
  Approval present; land-use case items). PC members are **Commissioners** (Chair, Vice-Chair) —
  a **separate body from the council**, its own 5–7-member roster (2026: Chair Sean Steinman,
  Vice-Chair Mike Smith, Commissioners Shelton, Poulson, Anderson, Barnes, Lugo, Mills…).
  Confirmation PDF saved to `planning_commission/raw/pc_min_10919.pdf`.
- **Architecture Review Commission** also exists (own agendas/minutes page) — out of core scope
  but a possible additional land-use body to note.

---

## 4. Meeting cadence

- **City Council: 1st & 3rd TUESDAY** (verified from meeting-date labels — e.g. 2026: Jan 20,
  Feb 3/17, Mar 3/17, Apr 7/21, May 5/19, Jun 2/17, Jul 7 — all 1st/3rd Tuesdays; occasional
  extra retreat/special dates). Each meeting day = a **Work Session (~4:00 PM) + a Business
  Meeting**, captured in **one combined "Work Session and Business Meeting" minutes doc**
  (verified 2024-01-16: the single PDF adjourns the work session then records the business-meeting
  motions/roll calls).
- **Planning Commission: Wednesday, 6:00 PM** (§3).
- Meeting location: **City Council Chambers / Work Room, 2277 East Bengal Boulevard**.

---

## 5. Public comments — **most likely SUBMIT-ONLY** (eComment form + email + inline hearing notes)

**Verdict: lean SUBMIT-ONLY / honest-empty for a standalone published written-comment archive
(auditor's call at acquisition — do NOT declare unavailable without the packet check below).**
- The city runs an **electronic Public Comment form ("eComment")**:
  `https://www.cottonwoodheights.utah.gov/your-government/public-comment` (JS-rendered form).
- **Written comments** on an agenda item are **emailed to the City Recorder**
  (`recorder@ch.utah.gov` / `cityrecorder@ch.utah.gov`) by **Tuesday noon** on the meeting date;
  **in-person** comment is 3 minutes (state name + resident status + address/district).
- Minutes **transcribe public-hearing speakers inline** (clerk paraphrase — e.g. the 2024-01-16
  trail-maintenance hearing has multiple resident speakers named/summarized). Per
  extraction_standards these are **meeting-record speaker notes, NOT genuine written comments** →
  a labeled `minutes_speaker_log.csv`, never `all_comments_clean.csv`.
- **No dedicated published-comment archive / correspondence page surfaced.** eComment/emailed
  submissions are collected by the Recorder and may be **bundled into agenda Packets** — the one
  remaining Phase-2 lead before declaring honest-empty: **grep council & PC Packet PDFs** for
  emailed/"correspondence received" comment bundles. (PMN also carries "Public Comment Courtesy
  Notice" postings, e.g. `711181.pdf`.) Absent a published archive, treat as **submit-only honest
  zero** (like Taylorsville) + build the labeled speaker log from minutes.

---

## 6. Elections — Salt Lake County (existing canonical archive ALREADY covers Cottonwood Heights)

- **Run by:** Salt Lake County Clerk. **The repo's canonical
  `salt_lake_county/elections/slco_municipal_results_long.csv` ALREADY contains Cottonwood
  Heights** (3,737 rows). **Filter on the `contest` column `LIKE '%COTTONWOOD HEIGHTS%'`**
  (the shared `slco_municipal_results_long.csv`; also the by-contest table). Live official
  results: `https://electionresults.utah.gov/` (Salt Lake County) and the SL County Clerk.
- **District-based council + citywide Mayor; non-partisan.** Contests present by year:

  | Year | Cottonwood Heights contests in the archive |
  |---|---|
  | 2009 | Council **3**, Council **4**, **Mayor** (primary rows present) |
  | 2013 | City Cncl **3**, City Cncl **4**, **Mayor** |
  | 2015 | City Cncl **1**, City Cncl **2** (+ County Prop #6 island) |
  | 2017 | City Cncl **3**, City Cncl **4**, **Mayor** (+ Parks & Rec District 2) |
  | 2021 | Council District **3**, District **4**, **Mayor** (+ Parks & Rec Svc Area D1/D2 trustee) |
  | 2023 | Council District **1**, District **2** (dup upper/mixed-case rows for D2) |
  | 2025 | City Council District **3**, District **4**, **Mayor** (+ Parks & Rec Trustee D1) |

  → **In-window (2020+): 2021, 2023, 2025** all present. Confirms the **D3/D4/Mayor (2021/2025)
  vs D1/D2 (2023)** stagger and the **voting-mayor + 4-district** structure.
- **⚠ Notes / caveats:**
  - **"Cottonwood Heights Parks & Recreation Service Area"** trustee contests appear alongside
    (2017, 2021, 2025) — that is a **separate special-service district**, **NOT** a city-council
    seat. Exclude Parks & Rec trustee rows from the council/mayor set.
  - 2023 has a **case-variant duplicate** ("Cottonwood Heights Council District 2" vs
    "COTTONWOOD HEIGHTS COUNCIL DISTRICT 2") — dedupe on normalized contest text.
  - Winners are UPPER-CASE with `(NP)` non-partisan suffixes — **normalize before joining** to
    the minutes roster (person + year + district): `MATT HOLTON`→D1, `SUZANNE HYLAND`→D2,
    `SHAWN NEWELL`→D3, `ELLEN BIRRELL`→D4, `GAY LYNN BENNION`→Mayor(2025), `MIKE WEICHERS`→
    Mayor(2021). Verify no 2019 CH gap when the full-history join is built (2019 = D1/D2 cycle;
    check archive coverage — Taylorsville/SJ/Millcreek had a 2019 SOVC drop).

---

## 7. GIS — city has an **official council-district layer** (on `gis.chcity.org`, currently
firewalled from this sandbox) + precinct fallback

- **Authoritative city layer (found via ArcGIS Online metadata, owner `Admin_CHcity`/`cwh`):**
  ```
  https://gis.chcity.org/server/rest/services/CityData/CityCouncilDistricts_SD/MapServer
  (also: .../CityData/Council_Districts/MapServer ; .../CityCouncilDistricts_individual_SD ;
         .../infoCouncilDistricts_SD  — a query service for address→district)
  ```
  This is the **official 4-district boundary service** published by the city GIS shop.
  ⚠ **`gis.chcity.org` returned connection-refused (HTTP 000) from this environment** — likely an
  internal/firewalled server or geo/rate block, **not confirmed down.** Re-probe during
  acquisition (it's a standard ArcGIS Server REST endpoint; `.../MapServer/0/query?where=1=1&f=json`
  should return the 4 district polygons). Related web maps: `Council District Map (for Reports)`
  (item `28363368d3784e349f218298ac6c46a3`), `City Council Districts` (`fadd349905e5404099969aa50d51a645`).
- **City GIS hub (public, ArcGIS Hub):** `https://cottonwood-heights-maps-chcity.hub.arcgis.com/`
  and the human Maps page `https://www.cottonwoodheights.utah.gov/community/maps` — download
  point for CSV/GeoJSON/etc.
- **SL County-hosted AGOL** (reachable, but **election-results not boundary**): a per-district
  "Cottonwood Heights City Council District 2" FeatureServer on
  `services1.arcgis.com/DJP723NX3ukQ2LtF/...` is **precinct-level results for one race**, not a
  clean boundary layer — do not use as the district polygon source.
- **Fallback (proven pattern, if `gis.chcity.org` stays unreachable):** derive District 1–4
  polygons from **Salt Lake County precinct geometry × the 2021/2023/2025 SOVC precinct rows**
  (as done for Taylorsville/SJ/Millcreek). **UGRC CountyID = 18 (Salt Lake)** for the VistaBallot
  precinct join; UGRC **Municipal Boundaries** `NAME='COTTONWOOD HEIGHTS'` for the city outline.
- **County/state indexes:** SL County Clerk election maps `https://www.saltlakecounty.gov/clerk/elections/maps/`;
  UGRC SGID Vista Ballot Areas.

---

## Retrieval plan (recommended order)

1. **Council minutes 2022→present (CivicEngage):** harvest `showpublisheddocument` **Minutes**
   anchors from `/…/council-meeting-agendas-and-minutes` (full browser headers — the site 403s
   otherwise) → `raw/minutes/<year>/`. Combined Work-Session+Business = one doc/day. Born-digital
   text → markdown.
2. **Council minutes 2020–2021 (PMN fallback):** the city portal does NOT hold these — pull from
   Utah PMN (resolve the CH council body id on `utah.gov/pmn`; files at `utah.gov/pmn/files/<id>.pdf`)
   or GRAMA `recorder@ch.utah.gov`. Record any truly-missing meeting in `minutes_unrecovered.csv`.
3. **Vote extraction (council):** parse `Vote on Motion: Council Member X - Yes/No … Mayor <Name>
   - Yes/No. The motion passed N-to-M` (**named roll call, MAYOR IS A VOTER, max tally 5**);
   `Members Present:`/`Excused:` header for attendance; mover+seconder always named; treat
   "passed with the unanimous consent of the Council" (adjourn/minutes) as a tally-only unanimous.
4. **Planning Commission 2020→present:** same portal `/…/planning-commission/agendas-packets-minutes`
   (2024+ on-site; 2020–2023 via GRAMA/PMN). Named roll call + PC→Council recommendation +
   land-use case items. Weekday = Wednesday.
5. **Comments:** grep council & PC **Packet** PDFs for emailed/eComment "correspondence received"
   bundles; otherwise build `minutes_speaker_log.csv` from inline hearing speakers + record the
   **submit-only** verdict in `public_comments/AVAILABILITY.md`.
6. **Elections:** reuse `salt_lake_county/elections/slco_municipal_results_long.csv`
   (`contest LIKE '%COTTONWOOD HEIGHTS%'`); **exclude Parks & Rec Service Area trustee** rows;
   dedupe 2023 D2 case-variant; check for a 2019 D1/D2 gap.
7. **Geo:** re-probe `gis.chcity.org/.../CityCouncilDistricts_SD/MapServer` for the official
   4-district polygons; if unreachable, derive from SLCo precincts × SOVC precinct rows
   (UGRC CountyID 18) → address→district tool.

---

## Risks / blockers

- **Edge-blocked CMS (MEDIUM):** `cottonwoodheights.utah.gov` **403s a bare UA and a bare browser
  UA** — needs the full header set (Accept + Accept-Language + Sec-Fetch-Mode). WebFetch fails;
  use `polite_fetch.py`. Verified working this recon.
- **Portal coverage is a rolling ~4-5-yr window (MEDIUM):** council minutes only **~2022+**, PC
  only **~2024+** on the live site; **2020–2021 (and 2020–2023 PC) require PMN/GRAMA** to satisfy
  the 2020 floor. This is a real acquisition dependency, not a scraper miss.
- **Mayor VOTES — structural, RESOLVED:** confirmed against a 3-2 named roll call (Mayor Weichers
  cast the deciding vote). **Max council tally = 5, Mayor is a voting `person`** — the OPPOSITE of
  Taylorsville/South Jordan. Getting this denominator right is the single most important build
  decision. (Ignore the HB-176 "mayor votes twice" briefing text — it's a state-bill topic.)
- **Mayor turnover mid-record:** Weichers (2021) → **Bennion (2025, office Jan 2026)**; roster
  drift on D1/D2 (2023) vs D3/D4/Mayor (2021/2025). Build a proper term roster.
- **PMN body ids unresolved this recon (LOW):** the PMN JSON API 404'd; resolve the CH council/PC
  public-body ids by browsing `utah.gov/pmn` at acquisition (Taylorsville-style, its council was
  body 720). CH minutes are confirmed present on PMN (file pattern `utah.gov/pmn/files/<id>.pdf`).
- **City GIS server unreachable from sandbox (LOW):** `gis.chcity.org` returned HTTP 000 here
  (likely internal/firewalled) though the official 4-district MapServer is catalogued in AGOL —
  re-probe during acquisition; precinct-derived fallback (UGRC CountyID 18) is proven.
- **Parks & Rec Service Area contests (LOW):** separate special district in the election archive —
  exclude from council/mayor races. Dedupe the 2023 D2 case-variant.

---

## Key URLs (quick index)

| What | URL |
|---|---|
| City site (CivicEngage; edge-blocks bots) | https://www.cottonwoodheights.utah.gov/ |
| Council agendas & minutes landing | https://www.cottonwoodheights.utah.gov/your-government/elected-officials/council-meeting-agendas-and-minutes |
| Minutes doc pattern | https://www.cottonwoodheights.utah.gov/home/showpublisheddocument/<docId>/<versionToken> |
| Council minutes samples (verified, PMN) | https://www.utah.gov/pmn/files/1081987.pdf (2024-01-16), https://www.utah.gov/pmn/files/1226779.pdf (2024-10-15) |
| Elected Officials (roster) | https://www.cottonwoodheights.utah.gov/your-government/elected-officials |
| Planning Commission agendas/packets/minutes | https://www.cottonwoodheights.utah.gov/your-government/boards-and-commissions/planning-commission/agendas-packets-minutes |
| PC minutes sample (verified) | https://www.cottonwoodheights.utah.gov/home/showpublisheddocument/10919/639088970409500000 (2026-02-04) |
| Public Comment (eComment) | https://www.cottonwoodheights.utah.gov/your-government/public-comment |
| City Recorder email (written comment/GRAMA) | recorder@ch.utah.gov / cityrecorder@ch.utah.gov |
| Utah Public Notice (fallback minutes) | https://www.utah.gov/pmn (files: utah.gov/pmn/files/<id>.pdf) |
| Election archive (canonical, in-repo) | salt_lake_county/elections/slco_municipal_results_long.csv (filter contest LIKE '%COTTONWOOD HEIGHTS%'; CH present 2009–2025) |
| SL County live results | https://electionresults.utah.gov/ (Salt Lake County) |
| SL County Clerk election maps | https://www.saltlakecounty.gov/clerk/elections/maps/ |
| City GIS council-district service (official) | https://gis.chcity.org/server/rest/services/CityData/CityCouncilDistricts_SD/MapServer (000 from sandbox — re-probe) |
| City GIS hub / Maps | https://cottonwood-heights-maps-chcity.hub.arcgis.com/ ; https://www.cottonwoodheights.utah.gov/community/maps |

```json
{"vendor":"Granicus / CivicPlus CivicEngage Central","minutes_landing_url":"https://www.cottonwoodheights.utah.gov/your-government/elected-officials/council-meeting-agendas-and-minutes","minutes_url_pattern":"https://www.cottonwoodheights.utah.gov/home/showpublisheddocument/<docId>/<versionToken> (harvest labeled Minutes anchors; PMN fallback utah.gov/pmn/files/<id>.pdf)","coverage_years":"council minutes ~2022-2026 on city portal (rolling window; older = GRAMA); PC minutes ~2024-2026 on portal; 2020-2021 council + 2020-2023 PC via Utah PMN / GRAMA. City incorporated 2005; 2020 is a normal floor.","format":"born-digital clean text PDF (pdftotext-clean; no OCR garble observed 2024-2026)","votes_in_minutes":true,"vote_style":"NAMED per-member roll call ('Vote on Motion: Council Member X - Yes/No ... Mayor <Name> - Yes/No. The motion passed N-to-M'); mover+seconder named; routine adjourn/minutes = 'unanimous consent'. Confirmed on a CONTESTED 3-2 vote.","pc_portal":"https://www.cottonwoodheights.utah.gov/your-government/boards-and-commissions/planning-commission/agendas-packets-minutes (own PC, same CivicEngage; showpublisheddocument pattern; named roll call + recommendations to council; confirmed doc 2026-02-04)","pc_coverage":"~2024-2026 on portal; 2020-2023 via GRAMA/PMN","council_weekday":"Tuesday (1st & 3rd; Work Session ~4:00 PM + Business Meeting in one combined minutes doc). PC = Wednesday 6:00 PM.","num_districts":4,"at_large_seats":0,"mayor_votes":true,"max_tally":5,"current_members":["Mayor Gay Lynn Bennion (2026-2029, VOTING)","D1 Matt Holton (2024-2027)","D2 Suzanne Hyland (2024-2027)","D3 Shawn Newell (to 2029)","D4 Ellen Birrell (to 2029)"],"comments_published":false,"comments_note":"submit-only: eComment form + written comment emailed to recorder@ch.utah.gov by Tue noon + in-person 3-min; public-hearing speakers transcribed inline in minutes (speaker-log, not written comments). Phase-2: grep Packets for emailed correspondence before final honest-empty call.","gis_source":"official city 4-district layer https://gis.chcity.org/server/rest/services/CityData/CityCouncilDistricts_SD/MapServer (HTTP 000 from sandbox - likely firewalled, re-probe at acquisition); city hub cottonwood-heights-maps-chcity.hub.arcgis.com; fallback = SLCo precincts x 2021/2023/2025 SOVC precinct rows, UGRC CountyID 18","elections":"canonical salt_lake_county/elections/slco_municipal_results_long.csv already covers CH 2009-2025 (filter contest LIKE '%COTTONWOOD HEIGHTS%'); in-window 2021/2023/2025 present; stagger D3/D4/Mayor (2021/2025) vs D1/D2 (2023); EXCLUDE Parks & Rec Service Area trustee rows; dedupe 2023 D2 case-variant; check 2019 D1/D2 gap","blockers":["site 403s bare UA AND bare browser UA - needs full browser header set (Accept+Accept-Language+Sec-Fetch-Mode); use polite_fetch.py; WebFetch blocked","portal is a rolling ~4-5yr window - 2020-2021 council + 2020-2023 PC minutes require PMN/GRAMA (real dependency for the 2020 floor)","MAYOR VOTES (max tally 5, mayor is a person) - opposite of Taylorsville/SJ; confirmed via 3-2 roll call","mayor turnover mid-record: Weichers(2021)->Bennion(2025, office 2026)","PMN CH body ids unresolved (API 404) - look up at acquisition","gis.chcity.org unreachable from sandbox (000) - re-probe; else precinct-derive","exclude Parks & Rec Service Area trustee contests from election set"],"confidence_notes":"HIGH-confidence & confirmed against real docs: vendor (showpublisheddocument+granicus chrome), minutes URL pattern, born-digital format, NAMED roll call, MAYOR VOTES & max tally 5 (contested 3-2, 2024-01-16), 4 districts + voting mayor, current roster w/ terms, PC own+Wednesday+named-votes (2026-02-04), elections present in canonical archive. MEDIUM/needs-acquisition-verify: exact portal floor year & 2020-2021 PMN body ids, PC 1st/3rd-Wednesday exact weeks, comments final submit-only call (packet grep pending), gis.chcity.org reachability (catalogued but 000 here)."}
```
