# South Jordan City, Utah — Civic Data Recon

**City:** South Jordan City, **Salt Lake County**, Utah (~80k pop.)
**Recon date:** 2026-07-06
**Scope of interest:** 2020–present
**Form of government:** **Six-member council form** (council + city manager). Council =
**5 district members + the Mayor = 6 members total.** See §2 for the mayor-vote nuance.
**Official sites:**
- CivicPlus / CivicEngage CMS: `https://www.sjc.utah.gov/` (canonical alias
  `https://ut-southjordan.civicplus.com/` — same site, both hosts serve identical paths)
- Newer marketing site: `https://ww2.southjordanutah.gov/` (WordPress; bios/overview only)
- CityView permit/planning-application portal: `https://cityview.southjordanutah.gov/`
  (land-use *applications*, NOT minutes)

---

## 1. Council meeting minutes

**Two independent portals carry the same meetings. Both confirmed.**

### Portal A — CivicPlus / CivicEngage (RECOMMENDED PRIMARY, 2021→present)
- **Host:** `www.sjc.utah.gov` (= `ut-southjordan.civicplus.com`).
- **Minutes archive (year-tabbed):**
  `https://www.sjc.utah.gov/484/City-Council-Meeting-Minutes-Archive`
  — year tabs run **2021 → 2026** (earliest tab is "2021 Meeting Minutes Archive"; **no 2020
  tab** — see 2020 note below).
- **Minutes doc URL pattern (direct, harvestable from each year's archive page):**
  ```
  https://www.sjc.utah.gov/DocumentCenter/View/<docId>/<MM-DD-YYYY>-South-Jordan-City-Council-Meeting-Minutes
  ```
  Same-day variants exist: `...-Study-Meeting-Minutes`, `...-Budget-Meeting-Minutes`,
  `...-Combined ... Redevelopment-Agency...`. **Older files (≈2021–2023) drop the
  "South-Jordan-" prefix**, e.g. `.../DocumentCenter/View/5373/12-05-2023-City-Council-Meeting-Minutes`.
  → Harvest the `DocumentCenter/View/<id>/<slug>` links from the archive pages (the slug
  carries the date + meeting type); do not assume `<docId>` is date-ordered.
- **AgendaCenter** (alternate, also has a `ViewFile/Minutes` pattern):
  `https://www.sjc.utah.gov/AgendaCenter` → category **City-Council-1**.
- **CONFIRMED sample fetched & read:** `View/7551/03-18-2025-...-Meeting-Minutes` (17 pp),
  and `View/11952/03-17-2026-...-Budget-Meeting-Minutes` (16 pp).

### Portal B — Municode Meetings (2020 backfill + PC alternate + HTML minutes)
- **Host:** `https://southjordan-ut.municodemeetings.com/`
- Meeting groups: **City Council** (incl. *Study Meetings* and *Combined City Council &
  Redevelopment Agency Meetings*) and **Planning Commission**. Date-range selector spans
  **1976–2029** → this is the route for **2020** (and pre-2020) minutes.
- **Document blob pattern (US-gov Azure):**
  ```
  https://mccmeetings.blob.core.usgovcloudapi.net/sojordanut-pubu/MEET-Minutes-<uid>.pdf
  MEET-Agenda-<uid>.pdf   ·   MEET-Packet-<uid>.pdf   (agenda packets)
  ```
  HTML (ADA) minutes viewer: `https://meetings.municode.com/adaHtmlDocument/...`
- **API not yet cracked:** the landing page is a JS app driven by "From/To" date + "Meeting
  Group" form controls; no plain JSON endpoint surfaced in the static HTML. Meeting detail
  pages follow `/bc-citycouncil/page/city-council-meeting-<...>`. **Enumerating Municode
  needs a rendered/POST pass** (time-boxed here — see risks). For 2021+ the CivicPlus
  DocumentCenter route is simpler; reserve Municode for **2020**.

### Format — CONFIRMED born-digital text PDF (NOT scanned)
`pdftotext -layout` yields clean, selectable text (verified on 3 docs incl. PC). Read parses
directly. No OCR needed for the recent era. (Pre-2021 / Municode-era files unverified for
scan-vs-text — check when backfilling 2020.)

### Meeting cadence
- **Weekday: Tuesday.** Each meeting Tuesday has a **Study Meeting 4:30 PM** + a
  **Regular Meeting 6:30 PM** (two separate minutes docs). Roughly **1st & 3rd Tuesdays**
  plus extra **Budget** meetings in spring. Council Chambers, 1600 W Towne Center Dr.

### Roll-call votes in minutes — CONFIRMED PRESENT (narrative tally style)
Every motion records **mover + seconder + a tally**, in two observed phrasings:
- `"Council Member Zander motioned to approve Resolution R2025-14 … Council Member Shelton
  seconded the motion. Roll Call Vote / The motion passed with a vote of 5-0."`
- `"… seconded the motion; Vote was 5-0, unanimous in favor."`

**Names are NOT listed for unanimous votes** — only the numeric tally (Sandy-style narrative
roll-call, not a West-Jordan-style YES/NO/ABSENT name block). **All ~9 votes across the two
council meetings read were 5-0** (high-consensus council — a genuinely contested council vote
was not found in the sample; the dissent-naming format is therefore **unconfirmed** — likely
"…N-M, Member X opposed", to be verified during extraction). Attendance is a `Present:` /
`Absent:` header block at the top (drives the absent set). **Max council tally observed = 5**
(see §2 on the mayor).

---

## 2. Council structure — 5 districts + Mayor (mayor-vote CAVEAT)

- **5 district council seats (Districts 1–5) + separately-elected Mayor = "six-member
  council."** No at-large council seats (Mayor is the only citywide seat).
- **Current members** (from the 2025-03-18 minutes header + `/241/City-Council`):

  | Seat | Member |
  |---|---|
  | Mayor (citywide) | Dawn R. Ramsey |
  | District 1 | Patrick Harris |
  | District 2 | Kathie L. Johnson |
  | District 3 | Donald J. ("Don") Shelton |
  | District 4 | Tamara Zander |
  | District 5 | Jason T. McGuire |

- **Terms:** 4-year, staggered. **Cycle A (2013/2017/2021/2025): Mayor + District 3 + District
  5** ("two members and a mayor"). **Cycle B (2015/2019/2023): Districts 1, 2, 4** ("the other
  three"). Confirmed against the election archive contest labels.
- **⚠ MAYOR-VOTE NUANCE (must-verify, key structural decision):** *Statutorily* the six-member
  council form makes the **Mayor a full voting member** of the council. But **every recorded
  tally observed is `5-0` with Mayor Ramsey present and presiding** — i.e. the printed tally
  counts only the **5 council members; the Mayor does not appear in the roll-call count**.
  For the build, **treat max council tally = 5 and the Mayor as non-voting on ordinary
  motions**, but **flag to confirm on the first genuinely split vote** (the Mayor may cast a
  statutory tie-breaker, which would surface as a 6th vote / "Mayor Ramsey voted…"). This is
  the single most important thing for the vote extractor to pin down.
- City Council page: `https://www.sjc.utah.gov/241/City-Council` ·
  Mayor & Council bios: `https://ww2.southjordanutah.gov/mayor-city-council/`

---

## 3. Planning Commission

- **Same CivicPlus portal, different category/archive (confirmed independently):**
  - Landing: `https://www.sjc.utah.gov/254/Planning-Commission`
  - Minutes archive: `https://www.sjc.utah.gov/486/Planning-Commission-Meeting-Minutes-Arch`
  - AgendaCenter category: `.../AgendaCenter/Planning-Commission-2`
  - DocumentCenter pattern:
    `https://www.sjc.utah.gov/DocumentCenter/View/<id>/<MM-DD-YYYY>-Planning-Commission-Meeting-Minutes`
  - Also present in the **Municode** portal (Meeting Group "Planning Commission").
- **Cadence:** **2nd & 4th Tuesday, 6:30 PM**, City Council Chambers.
- **Votes/recommendations — CONFIRMED recorded** (sample: `View/11998/04-28-2026-...`, 19 pp,
  born-digital text): mover + seconder + `"Roll Call Vote was 3-0 unanimous in favor; Chair
  Gedge and Commissioner Farnsworth were absent from the vote."` → **PC names absentees**
  (unlike the council sample). Items keyed by **File No.** (`PLCUP2025…`, `PLSP2025…`,
  `PLSP2025109`) — a **case-number system** (like West Valley), good for PC→Council referral
  linkage. PC minutes are unusually rich — near-verbatim quoted speaker/applicant statements
  (`"Mr. Naylor said…"`, `"Commissioner Hollist said…"`).

---

## 4. Public comments

**Verdict: UNCLEAR → likely transcribed-in-minutes only; no separate published archive
located (do NOT yet conclude unavailable — auditor's call).**
- The minutes' **PUBLIC COMMENT** sections are clerk notes / near-verbatim paraphrases of
  in-person speakers (e.g. "Others:" attendee list + quoted statements). Per
  extraction_standards these are **meeting-record notes, NOT genuine written comments** →
  a labeled `minutes_speaker_log.csv`, never `all_comments_clean.csv`.
- **No dedicated comments page, eComment/Open City Hall/Speak-Up portal, or "correspondence
  received" archive** surfaced on `sjc.utah.gov`.
- **Most promising remaining leads to chase (Phase 2):**
  1. **Municode agenda-packet PDFs** (`MEET-Packet-<uid>.pdf`) — may bundle emailed/written
     comments as correspondence attachments (this is where West Jordan's genuine comments hid).
  2. **CivicPlus agenda packets** in DocumentCenter for public-hearing (rezone/budget) meetings.
  3. Submission mechanism: in-person + likely an email/comment-card route (find the council
     comment email on the council page; not yet pinned down) — a GRAMA route as last resort.

---

## 5. Elections — Salt Lake County (existing archive largely covers South Jordan)

- **Run by:** Salt Lake County Clerk.
  Results: `https://saltlakecounty.gov/clerk/elections/election-results/`
  City elections page: `https://www.sjc.utah.gov/230/Elections`
- **District-based:** YES — Districts 1–5 each their own contest; Mayor citywide.
- **Existing shared archive `~/Desktop/slco-election-archive/` ALREADY covers South Jordan.**
  `data/municipal_results_long.csv` (filter `contest LIKE '%SOUTH JORDAN%'`):

  | Year | SJ contests present | Contest-label style |
  |---|---|---|
  | 2007,2009,2011,2013,2015,2017 | Council Dist 1–5 + Mayor (per cycle) + primaries | **clean** (e.g. `SOUTH JORDAN CITY CNCL DIST 3`) |
  | 2021 (general) | `CITY OF SOUTH JORDAN COUNCIL DISTRICT 3/5`, `… MAYOR` | rows under generic `Sheet39/40/41` — **filter by contest text, not sheet** |
  | 2023 (general) | `CITY OF SOUTH JORDAN COUNCIL DISTRICT 1/2/4` | generic `Sheet37/38/39` |
  | 2025 (general) | `SOUTH JORDAN CITY COUNCIL DISTRICT 3/5`, `… MAYOR` | generic `Sheet46/47/48` |

- **⚠ GAP — 2019 South Jordan missing.** The archive *has* a normalized 2019 general
  (`~/Desktop/slco-election-archive` 2019 rows exist), but **zero rows match `SOUTH JORDAN`**
  — the 2019 cycle-B council races (Districts 1, 2, 4) don't appear. Cause likely the 2019
  "Family B" numbered-sheet layout not carrying the city string, or uncontested seats omitted
  from the SOVC. **Downstream: spot-check the raw 2019 SOVC for South Jordan Dist 1/2/4 (+ the
  2019 primary, flagged unparsed in the archive README).**
- → **Reuse the archive** (filter `%SOUTH JORDAN%`); re-run its pipeline only for the 2019
  gap or a future cycle.

---

## 6. GIS — district layer CONFIRMED live (city ArcGIS Server)

- **South Jordan council-district polygons (preferred; verified queryable):**
  ```
  https://gis2.southjordanutah.gov/server/rest/services/Voting/Voting/MapServer/2
  ```
  = **"Council Districts 2020"** (Feature Layer, polygon, ArcGIS 11.5). SRID **wkid 103170 /
  latestWkid 6625** (NAD83 Utah Central, ftUS) → reproject to 4326 for the address tool.
  Parent **`Voting/Voting/MapServer`** has 5 layers: `0 Polling Places`, `1 County Voting
  Precincts 2014`, `2 Council Districts 2020`, `3 House of Representatives`, `4 Utah Senate
  Districts 2012`. Sibling services: `.../Boundaries/MapServer`, `.../Parcels_public/MapServer`.
  ⚠ **`gis2.southjordanutah.gov` (and `gis.sjc.utah.gov`/`gis.southjordanutah.gov`) failed DNS
  from this recon environment for some calls but the `gis2` REST endpoint responded 200 with
  valid layer JSON** — it is reachable; expect intermittent resolution / possible geofencing.
- **ArcGIS Online mirror** (org `SJCity`, orgId `Uh4UVFWPQDzDTxjn`,
  host `southjordancity.maps.arcgis.com`): Web Map **`8747ca4ab86e4632a6966fd40cd2ed19`**
  ("City Council Districts") references the gis2 layer above; viewer apps
  `d3dc643c229248d19e10c0bc3adba96a` (WAB) and `71aeed3b17ec471185e1a4e50aa4fa0e` (Instant).
  (No standalone `services3.arcgis.com/Uh4UVFWPQDzDTxjn` district FeatureServer — name-guesses
  returned catch-all `400 Invalid URL`; use the gis2 MapServer.)
- **UGRC fallbacks:** VistaBallotAreas **CountyID = 18** (Salt Lake) for precinct join;
  UGRC Municipal Boundaries `NAME='SOUTH JORDAN'` for the city outline. Precinct geometry also
  in `~/Desktop/slco-election-archive/geo/` (join `PrecinctID`).

---

## Retrieval plan (recommended order)

1. **Council minutes 2021→present (CivicPlus):** for each year tab on
   `/484/City-Council-Meeting-Minutes-Archive`, harvest `DocumentCenter/View/<id>/<slug>`
   links (slug = date + meeting type). Curl each PDF (browser UA) → `raw/minutes/<year>/`.
   Keep Study + Regular + Budget + Combined-RDA as separate files. Text-layer → markdown.
2. **Council minutes 2020 (Municode/PMN):** enumerate the Municode portal (rendered/POST pass)
   for 2020 City Council meetings → `MEET-Minutes-<uid>.pdf`; cross-check/fill via
   `utah.gov/pmn` (South Jordan body id — a SJ agenda lives at `utah.gov/pmn/files/662739.pdf`;
   find the exact council body id). Flag scan-vs-text on these.
3. **Vote extraction (council):** parse `motioned/moved … seconded … Vote was N-M` /
   `Roll Call Vote / passed with a vote of N-M`; `Present:`/`Absent:` header for attendance;
   **max tally 5, Mayor not counted** (verify tie-break behavior on first split vote);
   unanimous-no-names → `names_recorded:false`.
4. **Planning Commission:** same CivicPlus harvest from `/486/...` + Municode "Planning
   Commission". Parse mover/seconder/tally + **named absentees**; capture **File No. PL…**
   case numbers for referral linkage; PC does Final-Action (site plan/CUP/plat) vs
   recommendation-to-Council.
5. **Comments:** pull agenda **packets** (Municode `MEET-Packet-<uid>.pdf` / CivicPlus
   DocumentCenter) for public-hearing meetings, grep for correspondence/written comments;
   otherwise build `minutes_speaker_log.csv` (labeled NOT comments) and record verdict.
6. **Elections:** filter `~/Desktop/slco-election-archive` `%SOUTH JORDAN%`; resolve the
   2019 Dist 1/2/4 gap from the raw 2019 SOVC.
7. **Geo:** query `Voting/MapServer/2` → GeoJSON, reproject 6625→4326, build address→District
   1–5 tool; UGRC VistaBallotAreas (CountyID 18) fallback.

---

## Risks / blockers

- **Mayor-vote ambiguity (HIGH):** statutory six-member form says the Mayor votes, but all
  observed tallies are 5-0 (Mayor not counted). Resolve on the first split council vote before
  finalizing the roster/tally logic. Getting this wrong mis-states every vote's denominator.
- **No named dissent observed:** council sample was 100% unanimous (5-0); the contested-vote
  naming format is **unconfirmed**. Pull a rezone/budget public-hearing meeting known to have a
  Nay to lock the parser's dissent pattern before bulk extraction.
- **2020 not on CivicPlus:** DocumentCenter archive starts 2021. 2020 requires the Municode
  portal (API not yet cracked — JS/POST) or PMN. Time-boxed here.
- **Municode enumeration:** no plain JSON endpoint found; needs a rendered/POST harvest, or
  just rely on CivicPlus for 2021+ and Municode only for 2020.
- **GIS host reachability:** `gis2.southjordanutah.gov` served valid JSON but sibling gis hosts
  gave DNS failures in this environment — expect intermittent resolution; the ArcGIS Online
  webmap `8747ca4a…` is a reliable pointer if the direct host flaps.
- **Election CSV labeling:** 2021/2023/2025 SJ contests live under generic `SheetNN` names —
  filter by contest **text** (`%SOUTH JORDAN%`), verify exact strings against raw SOVC.
- **2019 South Jordan election gap** (Districts 1/2/4 + primary) — needs a raw-SOVC re-parse.
- **Comments genuinely unclear** — no public archive found; do not declare unavailable until
  packets are checked.

---

## Key URLs (quick index)

| What | URL |
|---|---|
| Council minutes archive (2021–26) | https://www.sjc.utah.gov/484/City-Council-Meeting-Minutes-Archive |
| Council minutes doc pattern | https://www.sjc.utah.gov/DocumentCenter/View/<id>/<MM-DD-YYYY>-South-Jordan-City-Council-Meeting-Minutes |
| AgendaCenter | https://www.sjc.utah.gov/AgendaCenter (City-Council-1 · Planning-Commission-2) |
| Municode Meetings portal | https://southjordan-ut.municodemeetings.com/ |
| Municode minutes blob | https://mccmeetings.blob.core.usgovcloudapi.net/sojordanut-pubu/MEET-Minutes-<uid>.pdf |
| PC page / minutes archive | https://www.sjc.utah.gov/254/Planning-Commission · /486/Planning-Commission-Meeting-Minutes-Arch |
| City Council page | https://www.sjc.utah.gov/241/City-Council |
| Elections (city) | https://www.sjc.utah.gov/230/Elections |
| SL County results | https://saltlakecounty.gov/clerk/elections/election-results/ |
| Election archive (local) | ~/Desktop/slco-election-archive (SJ present 2007–2025; 2019 gap) |
| District GIS layer | https://gis2.southjordanutah.gov/server/rest/services/Voting/Voting/MapServer/2 |
| Voting parent service | https://gis2.southjordanutah.gov/server/rest/services/Voting/Voting/MapServer |
| ArcGIS Online districts webmap | https://southjordancity.maps.arcgis.com item 8747ca4ab86e4632a6966fd40cd2ed19 |
| PMN fallback (2020) | https://www.utah.gov/pmn/ (sample SJ agenda utah.gov/pmn/files/662739.pdf) |
| CityView (permits, not minutes) | https://cityview.southjordanutah.gov/ |

```json
{"city":"South Jordan","minutes":{"vendor":"CivicPlus/CivicEngage (primary, 2021+) + Municode Meetings (2020 + PC alt)","base_url":"https://www.sjc.utah.gov/484/City-Council-Meeting-Minutes-Archive","minutes_years":"2021-2026 on CivicPlus; 2020 via Municode/PMN","format":"born-digital text PDF","votes_in_minutes":true,"meeting_weekday":"Tuesday"},
 "council":{"districts":5,"at_large":0,"members":["Mayor Dawn Ramsey","D1 Patrick Harris","D2 Kathie Johnson","D3 Don Shelton","D4 Tamara Zander","D5 Jason McGuire"],"mayor_votes":"statutorily yes (six-member form) but all observed tallies are 5-0 with mayor uncounted — treat max tally 5, verify on split vote"},
 "comments":{"published":"unclear","where":"transcribed in minutes only; check Municode/CivicPlus agenda packets for correspondence","submit":"in-person + likely email (TBD); GRAMA fallback"},
 "elections":{"county":"Salt Lake","source_url":"https://saltlakecounty.gov/clerk/elections/election-results/","existing_archive":"~/Desktop/slco-election-archive (SJ 2007-2025 present; 2019 Dist 1/2/4 + primary GAP)","district_based":true},
 "geo":{"ugrc_county_id":18,"boundaries_available":true,"district_layer":"https://gis2.southjordanutah.gov/server/rest/services/Voting/Voting/MapServer/2"},
 "risks":["mayor-vote ambiguity (statute=votes, tallies=5-0) — resolve on first split vote","no contested council vote in sample — dissent-naming format unconfirmed","2020 not on CivicPlus — needs Municode(API uncracked)/PMN","Municode has no plain JSON API — rendered/POST harvest","GIS host DNS intermittent (gis2 responded 200)","2021/23/25 election contests under generic SheetNN — filter by text","2019 South Jordan election rows absent — raw SOVC re-parse","comments availability unresolved until packets checked"],
 "recommended_order":["council minutes 2021+ CivicPlus","2020 backfill Municode/PMN","council vote extraction (verify mayor/tie)","PC minutes+votes CivicPlus/Municode","comments hunt in packets","elections reuse archive + 2019 gap","geo Voting/MapServer/2 -> address tool"]}
```
