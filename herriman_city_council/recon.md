# Herriman City, Utah — Civic Data Recon

**City:** Herriman City, **Salt Lake County**, Utah (~60k pop., **incorporated 1999**, fast-growing SW-valley city)
**Recon date:** 2026-07-11
**Data floor:** **2020-01-01 → present.**
**Form of government:** **4 council districts (D1–D4) + a separately-elected Mayor + an appointed City Manager**
(Nathan Cherpeski). The **Mayor presides but does NOT cast a vote on ordinary roll-call motions** — every
roll call in the sampled minutes (2020, 2021, 2025) lists **only the four councilmembers** (max tally = 4).
Whether the Mayor breaks a 2–2 tie is **UNCONFIRMED** (watch for it). See §4.

> ⚠️ **CORRECTION (2026-07-11, post-build):** this recon assumption is **WRONG**. The Herriman
> **Mayor IS a full voting member** (Millcreek model) — a full council roll tops out at **5**
> (D1–D4 + Mayor), not 4. Verified at source in `VERIFICATION.md` §4 (Mayor Watts casts a
> decisive Nay on a 3:2 vote 2020-01-08; Mayor Palmer votes in every roll 2022+). The extractor,
> `CLAUDE.md`, and `VERIFICATION.md` all reflect the corrected max-tally-5 fact — do NOT follow §4 below.
**Official site:** `https://www.herriman.gov/` (the old `herriman.org` **301-redirects** to `herriman.gov`).
**Meeting portal vendor:** **PrimeGov** (`herriman.primegov.com`) — same vendor family as **West Jordan**
(reuse its `fetch_new.py` API pattern). The `herriman.gov` CMS is a WordPress front that links out to PrimeGov.

⚠ **Fetch note:** `herriman.gov` and the PrimeGov API both served fine with a **browser UA** (Chrome UA used
throughout this recon; no 403 observed). Keep the browser UA as a precaution.

---

## 1. Council meeting minutes

### Portal — PrimeGov (JSON API + compiled-document endpoint)
- **Human landing (council):** `https://www.herriman.gov/agendas-and-minutes` (anchor `#ccagendas`)
- **PrimeGov portal:** `https://herriman.primegov.com/public/portal`
- **Meeting-list API (the harvest entry point):**
  ```
  https://herriman.primegov.com/api/v2/PublicPortal/ListArchivedMeetings?year=YYYY
  https://herriman.primegov.com/api/v2/PublicPortal/ListUpcomingMeetings
  ```
  Returns JSON: each meeting has `id`, `committeeId`, `dateTime`, `title`, and a `documentList[]` of
  `{templateName, templateId, id}`. **Council = `committeeId 3`** (title "City Council Regular Meeting"),
  `meetingTypeId 1`. Each council meeting's `documentList` carries `Agenda`, **`Minutes`**, and often `Packet`.
- **Minutes document URL pattern (CONFIRMED — the download uses `templateId`, NOT the doc `id`):**
  ```
  https://herriman.primegov.com/Public/CompiledDocument?meetingTemplateId=<templateId>
  ```
  where `<templateId>` is the `templateId` of the `documentList` entry whose `templateName == "Minutes"`.
  (This is exactly the West Jordan pattern. `Public/CompiledDocument?meetingDocumentId=<id>` and
  `Portal/MeetingDocument?...` return only an HTML viewer shell — use `meetingTemplateId`.)
  Verified: `.../CompiledDocument?meetingTemplateId=2175` → the **2025-01-08 council minutes** PDF (344 KB).

### Coverage — PrimeGov starts **2021-01-07**; **2020 is NOT on PrimeGov** (recover from live S3, below)
- `ListArchivedMeetings` returns **0** meetings for **2019 and 2020**, **82** for 2021 (earliest
  2021-01-07), 77 for 2025. → **The 2020 floor year is entirely absent from PrimeGov.**
- **2020 FLOOR RECOVERY — a still-live AWS S3 bucket** (`herriman-agendas`, us-west-1) from the pre-PrimeGov
  WordPress site. Bucket **listing is `AccessDenied`**, but **individual objects still serve HTTP 200**, and
  the object **keys are harvestable from the Wayback-archived `herriman.org/agendas-and-minutes/` pages**
  (2020 snapshots exist, e.g. `web.archive.org/web/20201101002908/https://www.herriman.org/agendas-and-minutes/`).
  Confirmed-live pattern:
  ```
  https://s3-us-west-1.amazonaws.com/herriman-agendas/2020-agendas/2020-city-council-minutes/YYYY_MM_DD.pdf
  https://s3-us-west-1.amazonaws.com/herriman-agendas/2020-agendas/2020-planning-commission-minutes/YYYY_MM_DD.pdf
  ```
  A `_CDA` suffix (e.g. `2020_06_10_CDA.pdf`) = the **Community Development Agency** (RDA equivalent, see §4);
  `_SCCM`/`_Special`/`_Joint`/`_HCSEA` suffixes also appear. Verified `2020_02_12.pdf` downloads (598 KB) as
  clean text with a named roll call. **ACTION: mirror this bucket early — it is a legacy host that could be
  retired at any time.** (Agendas back to 2019 also live here under `2019-agendas/…`; below the floor.)

### Format — CONFIRMED born-digital clean text PDF (NO OCR), both eras
`pdftotext -layout` on the **2025-01-08** council minutes and the **2020-02-12** council minutes both yield
clean, selectable text with intact proper names (`Mayor Lorin Palmer`, `Councilmember Jared Henderson`,
`City Recorder Jackie Nostrom`). **Not scanned, no OCR corruption.** Read parses directly.

### Roll-call votes in minutes — CONFIRMED PRESENT, **named per-member roll call (Millcreek-style)**
Motions record **mover + seconder**, then an **explicit per-member Aye/Nay list**:
> *"Councilmember Henderson moved to approve Ordinance No 2025-01 adopting the 2024 water conservation
> plan … Councilmember Hodges seconded the motion. **The vote was recorded as follows:** Councilmember
> Jared Henderson — Aye; Councilmember Teddy Hodges — Aye; Councilmember Sherrie Ohrn — Aye; Councilmember
> Steven Shields — Aye. **The motion passed unanimously.**"* (2025-01-08)

- **Every roll call names the four councilmembers**; the **Mayor is never in the tally**. Trivial procedural
  motions use the short form *"…seconded the motion, and all voted aye"* (no per-member list). An
  **attendance header** (`Presiding:` / `Councilmembers Present:` / `Staff Present:`) opens each doc.
- The **5:30 PM work meeting and the 7:00 PM general meeting are captured in ONE combined minutes doc** per
  meeting-day (both verified in the 2025-01-08 file).
- **A dissenting (Nay) roll call was not seen in the two sampled docs** (both unanimous) — the extractor
  should confirm the `Nay` wording on the first contested motion, but the per-member list format itself is
  confirmed, so attribution is unambiguous when dissent occurs.

---

## 2. Planning Commission — Herriman has its OWN PC (same PrimeGov portal)

- **Landing:** `https://www.herriman.gov/pc-agendas-minutes` (anchor `#pcagendas`); the city `planning-commission`
  page is `https://www.herriman.gov/planning-commission`.
- **PrimeGov committee = `committeeId 14`** (title "Planning Commission"), `meetingTypeId 5` (~23 meetings/yr).
  Same `Public/CompiledDocument?meetingTemplateId=<templateId>` download pattern (verified:
  `templateId=2217` → **2025-01-15 PC minutes**).
- **Coverage:** PrimeGov 2021→present; **2020 PC minutes** on the same S3 bucket path
  `2020-agendas/2020-planning-commission-minutes/YYYY_MM_DD.pdf` (object test 200).
- **Cadence — 1st & 3rd Wednesday, 6:00 PM** (work meeting ~6:00, regular ~7:00; Council Chambers, 5355 W
  Herriman Main St). Note Council and PC **both meet Wednesday** on alternating weeks (see §3).
- **Votes/recommendations — CONFIRMED, same named-roll-call format** ("The vote was recorded as follows:
  Commissioner Darryl Fenn — Aye; …") plus explicit **staff-recommendation-laden motions** on plats / CUPs /
  rezones (verified in the 2025-01-15 file — Fire Station 103 subdivision plat + CUP). PC→Council
  recommendation language should be captured for the referral layer.

---

## 3. Meeting cadence

- **City Council: 2nd & 4th Wednesday** (Jan 8 & 22, Feb 12 & 26, Mar 12 & 26 … in 2025). Each meeting-day =
  a **~5:30 PM work meeting + ~7:00 PM general meeting in one combined minutes doc**. ~25 council meetings/yr
  including **special/budget meetings** (extra Tue/Thu dates appear — e.g. 2025-05-14 & 05-15 budget).
- **Planning Commission: 1st & 3rd Wednesday**, 6:00 PM.
- Weekday join key for `build_weeks.py`: **Wednesday (MEETING_WEEKDAY = 2)** for both bodies (they bucket to
  their own dates on alternating weeks).

---

## 4. Council structure — 4 districts + non-voting presiding Mayor

- **4 council districts (D1–D4), one member each; Mayor elected citywide.** **No at-large council seats** in
  the modern (2020+) record. 4-year staggered, non-partisan terms; a City Manager runs administration.
- **⚠ MAYOR-VOTE DETERMINATION:** In **every** sampled roll call (2020-02-12, a 2021 meeting, 2025-01-08) the
  vote list contains **only the four councilmembers** — the Mayor **presides** ("Presiding: Mayor …") but is
  **not in the tally**. → **Build with max council tally = 4, Mayor non-voting on ordinary motions.** A 4-seat
  council can deadlock 2–2; whether the Mayor casts a **tie-breaking** vote (Utah six-member-form mechanism)
  is **UNCONFIRMED** — no tie appeared in the sample. Watch for it and treat any Mayor vote row as a
  tie-break, not a routine vote.
- **Council-structure history (from the election archive, §6):** contests are **"AT LARGE"** in **2007 & 2009**,
  then **numbered districts appear in 2011** ("Council 1/2/4") and are fully **"DIST" by 2013**. → Herriman
  **transitioned from at-large to 4 districts ~2010–2011.** **The entire 2020+ record is stable 4-district +
  Mayor** — the at-large→district change is well below the data floor and does **not** affect 2020+ modeling.
- **Current roster (2026, from `herriman.gov/city-council` + 2025-01-08 minutes header):**

  | Seat | Member | Term shown |
  |---|---|---|
  | Mayor (citywide, presides, non-voting) | **Lorin Palmer** (`mayorpalmer@herriman.gov`) | since Jan 2022 |
  | District 1 | **Jared Henderson** (`jhenderson`) | 2024–2028 (won 2023) |
  | District 2 | **Teddy Hodges** (`thodges`) | 2026–2030 (won 2025) |
  | District 3 | **M. Basham** (`mbasham`) | 2026–2030 (won 2025) |
  | District 4 | **T. Anderson** (`tanderson`) | 2026–2028 (**2-yr term**, won 2025) |

- **Roster drift within 2020+** (mind this for member-level joins):
  - **2020–2021 Mayor = David Watts** ("Presiding: Chair David Watts" in 2021 minutes); **Palmer** took
    office Jan 2022.
  - **2020 councilmembers** included **Steven Shields, Sherrie Ohrn, Clint Smith, Jared Henderson**.
  - **2025 councilmembers** were **Henderson, Hodges, Ohrn, Shields**; after the **2025 election** Ohrn &
    Shields left and **Hodges (D2), Basham (D3), Anderson (D4)** are seated for 2026.
- **Other PrimeGov bodies in the same API** (tag by committee; not the primary council/PC datasets):
  **CDRA `committeeId 4`** (Community Development & Renewal Agency — the RDA/"CDA" equivalent, an in-record
  board, ~3–4 mtgs/yr; 2020 files carry the `_CDA` suffix), **Appeal Authority `7`**, **HCFSA `8`**,
  **HCSEA `9`**, **Joint City Council/PC `12`**, **Youth Council `16`**.

---

## 5. Public comments

**Verdict: UNCONFIRMED → most likely inline-in-minutes speaker notes; no separate published written-comment
archive located this recon (auditor's call — do NOT prematurely declare "none").**
- Minutes carry an attendee header and **transcribe/paraphrase public-hearing speakers inline** (clerk
  notes) — per extraction_standards these are **meeting-record speaker notes, NOT genuine public-submitted
  comments** → a labeled `minutes_speaker_log.csv`, never `all_comments_clean.csv`.
- **Not yet checked:** whether PrimeGov's **eComment** feature is enabled for Herriman (some PrimeGov cities
  expose a public-comment submission/list), and whether agenda **Packets** (in each meeting's `documentList`)
  bundle written correspondence. **Phase-2 leads:** probe the PrimeGov portal UI for an eComment tab and grep
  a few council Packets for emailed/written comment before finalizing the availability verdict.

---

## 6. Elections — canonical archive already covers Herriman (2007–2025 **except 2019**)

- **DO NOT re-scrape.** `/Users/tysonwelsh/civic-data/salt_lake_county/elections/slco_municipal_results_long.csv`
  already contains Herriman contests. Filter on the **`contest`** column text `%HERRIMAN%` (labels vary by
  year — both mixed- and UPPER-case rows exist for 2011). **County = Salt Lake (FIPS 49035).**
- **Seat structure across years (for correct joins):**

  | Year | Herriman contests present | Note |
  |---|---|---|
  | 2007 | City Council **AT LARGE** | pre-district |
  | 2009 | City Council **AT LARGE**, **Mayor** | pre-district |
  | 2011 | Council **1, 2, 4** (dup upper/mixed-case rows) | districts introduced |
  | 2013 | Council **Dist 2, 3**, **Mayor** | |
  | 2015 | Council **Dist 1, 4** (+ Herriman Hills Initiative) | |
  | 2017 | Council **Dist 2, 3**, **Mayor** | |
  | **2019** | **NONE — 0 rows (GAP)** | should carry the **D1/D4** cycle (2015/2019/2023) |
  | 2021 | Council **District 2, 3**, **Mayor** | |
  | 2023 | Council **District 1, 4** | (Henderson wins D1) |
  | 2025 | Council **District 2, 3**, **District 4 (2 YEAR TERM)**, **Mayor** | D4 2-yr = special/short term |

- **⚠ Cycle map:** D2/D3(+Mayor) run **2017/2021/2025**; D1/D4 run **2015/2019/2023**. **2019 is entirely
  absent** (same failure mode as Taylorsville/South Jordan/Millcreek 2019 — the numbered-sheet layout dropped
  the city string). → **re-parse the raw 2019 SLCo SOVC** for Herriman **D1 & D4**.
- **⚠ 2025 "DISTRICT 4 (2 YEAR TERM)"** is an off-cycle **short/unexpired term** (Anderson) — flag it in the
  `note` column so member-term logic doesn't read it as a cycle shift.
- Winner names are UPPER-CASE (some `(NP)` non-partisan suffixes) — normalize before joining to the minutes
  roster on **person + year + district**.

---

## 7. GIS — Herriman ships an OFFICIAL 4-district FeatureServer (better than precinct-derivation)

- **Council districts — CONFIRMED official layer** (owner **HCPublicWorks** = Herriman City Public Works),
  ArcGIS item `f59497536e834761b5c376db68a47134`:
  ```
  https://services2.arcgis.com/XBmqwOHlPh25M7aJ/arcgis/rest/services/HerrimanDistricts/FeatureServer/0
  ```
  Query returns **exactly 4 polygons** (`District` 1–4, `Label` "District N"). → **Use this directly for
  `geo/address_to_district.py`** — no precinct-dissolve fallback needed (unlike Taylorsville/South Jordan).
  ⚠ Vintage: treat as **current / post-2020-census** boundaries; a pre-2022 address near a moved line may
  mis-assign — note the caveat but the layer is authoritative for present-day lookups.
- **City outline:** UGRC **Utah Municipal Boundaries** `NAME='HERRIMAN'` (count 1 confirmed):
  `https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/UtahMunicipalBoundaries/FeatureServer/0`.
- **Precinct / ballot-area cross-reference:** UGRC **VistaBallotAreas** for **CountyID 49035** (Salt Lake) —
  for the SOVC precinct→district reconciliation and as a fallback if the city layer is ever retired. (Note the
  sibling recons used the UGRC internal `CountyID = 18` for Salt Lake on the older VistaBallotAreas service;
  confirm which id the current service expects — `49035` is the county FIPS.)

---

## Retrieval plan (recommended order)

1. **Council minutes 2021→present (PrimeGov):** loop `ListArchivedMeetings?year=YYYY` for 2021–2026, keep
   `committeeId==3`, download each meeting's `Minutes` `templateId` via
   `Public/CompiledDocument?meetingTemplateId=<id>` → `raw/minutes/<year>/`. Combined work+general = one
   doc/day. Text-layer → markdown (clean, no OCR).
2. **Council minutes 2020 (S3 backfill):** harvest 2020 minutes keys from the Wayback-archived
   `herriman.org/agendas-and-minutes/` (+ `/pc-agendas-minutes/`) pages, then fetch each object from the
   **live** `s3-us-west-1.amazonaws.com/herriman-agendas/2020-agendas/2020-city-council-minutes/` bucket.
   **Mirror promptly.** Tag `_CDA` docs as `body=CDRA`.
3. **Vote extraction (council):** parse mover/seconder + `The vote was recorded as follows:` per-member
   Aye/Nay list; short-form `all voted aye` = unanimous-unnamed; **max tally 4, Mayor NON-voting**; verify
   the `Nay` wording on the first contested motion; watch for a Mayor tie-break row.
4. **Planning Commission 2020→present:** PrimeGov `committeeId 14` + the 2020 S3 PC folder; same extractor;
   capture PC→Council recommendation language + plat/CUP/rezone case identifiers.
5. **Comments:** probe PrimeGov eComment + council Packets; otherwise build `minutes_speaker_log.csv` and
   record the honest availability verdict.
6. **Elections:** reuse the canonical `slco_municipal_results_long.csv` (filter `contest LIKE '%HERRIMAN%'`);
   **re-parse raw 2019 SOVC** for D1/D4; flag the **2025 D4 2-year** special.
7. **Geo:** pull the **HerrimanDistricts** FeatureServer (4 polygons) → `geo/` + `address_to_district.py`;
   UGRC muni boundary + VistaBallotAreas as cross-checks.

---

## Risks / blockers

- **2020 floor not in PrimeGov (MEDIUM):** recover from the **legacy S3 bucket** (listing denied, objects
  live; keys via Wayback). **Mirror early** — a legacy host with no guaranteed longevity.
- **Mayor tie-break behavior UNCONFIRMED (STRUCTURAL):** Mayor confirmed non-voting on ordinary motions
  (tally 4); a 2–2 tie-break vote may exist — resolve on the first tied motion.
- **No contested/Nay roll call in sample:** per-member list format confirmed, but confirm `Nay` wording +
  attendance-exclusion handling on the first contested motion.
- **Public-comment availability not finalized:** check PrimeGov eComment + Packets before declaring
  submit-only.
- **2019 election gap (D1/D4) + 2025 D4 2-year special:** raw-2019-SOVC re-parse; don't let the 2025 D4 short
  term masquerade as a cycle change.
- **District-layer vintage:** the HerrimanDistricts service is current-boundary; pre-2022 address lookups may
  differ.

---

## Key URLs (quick index)

| What | URL |
|---|---|
| City site (WordPress front; herriman.org → herriman.gov) | https://www.herriman.gov/ |
| Council agendas & minutes landing | https://www.herriman.gov/agendas-and-minutes |
| PrimeGov portal | https://herriman.primegov.com/public/portal |
| Meeting-list API | https://herriman.primegov.com/api/v2/PublicPortal/ListArchivedMeetings?year=YYYY |
| Minutes/doc download pattern | https://herriman.primegov.com/Public/CompiledDocument?meetingTemplateId=&lt;templateId&gt; |
| Council minutes sample (verified) | CompiledDocument?meetingTemplateId=2175 (2025-01-08) |
| 2020 S3 backfill (council) | https://s3-us-west-1.amazonaws.com/herriman-agendas/2020-agendas/2020-city-council-minutes/YYYY_MM_DD.pdf |
| 2020 S3 backfill (PC) | https://s3-us-west-1.amazonaws.com/herriman-agendas/2020-agendas/2020-planning-commission-minutes/YYYY_MM_DD.pdf |
| PC agendas & minutes | https://www.herriman.gov/pc-agendas-minutes |
| City Council page (roster) | https://www.herriman.gov/city-council |
| Election archive (canonical) | /Users/tysonwelsh/civic-data/salt_lake_county/elections/slco_municipal_results_long.csv (filter %HERRIMAN%; **2019 GAP**) |
| Council-district FeatureServer | https://services2.arcgis.com/XBmqwOHlPh25M7aJ/arcgis/rest/services/HerrimanDistricts/FeatureServer/0 (4 districts) |
| UGRC municipal boundary | https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/UtahMunicipalBoundaries/FeatureServer/0 (NAME='HERRIMAN') |

**Confirmation PDFs saved:**
`meeting_minutes/raw/2025-01-08_council_minutes.pdf`, `meeting_minutes/raw/2020-02-12_council_minutes.pdf`,
`planning_commission/raw/2025-01-15_pc_minutes.pdf`.

```json
{"vendor":"PrimeGov (herriman.primegov.com); herriman.gov WordPress front (herriman.org 301->herriman.gov); West-Jordan-family API","minutes_landing_url":"https://www.herriman.gov/agendas-and-minutes","minutes_url_pattern":"https://herriman.primegov.com/Public/CompiledDocument?meetingTemplateId=<templateId> (templateId from ListArchivedMeetings?year=YYYY documentList where templateName='Minutes'; council committeeId=3)","coverage_years":"PrimeGov 2021-01-07 -> present; 2020 NOT in PrimeGov - recover from live S3 bucket herriman-agendas/2020-agendas/2020-city-council-minutes/ (keys via Wayback)","format":"born-digital clean text PDF (no OCR) - confirmed 2020 & 2025","votes_in_minutes":true,"vote_style":"named per-member roll call (Millcreek-style): mover+seconder then 'The vote was recorded as follows: Councilmember X Aye/Nay'; trivial motions 'all voted aye'; work+general meeting combined in one doc/day; dissent wording unconfirmed (samples unanimous)","pc_portal":"same PrimeGov, committeeId=14; landing https://www.herriman.gov/pc-agendas-minutes; 2020 on S3 2020-planning-commission-minutes/","pc_coverage":"PrimeGov 2021->present + 2020 S3; named roll call + staff-rec motions confirmed (2025-01-15)","council_weekday":"Wednesday - Council 2nd & 4th (work ~5:30pm + general ~7:00pm combined); PC 1st & 3rd 6:00pm","num_districts":4,"at_large_seats":0,"mayor_votes":false,"mayor_note":"Mayor presides, not in any roll-call tally (max tally=4); 2-2 tie-break vote UNCONFIRMED","current_members":["Mayor Lorin Palmer (citywide, non-voting, since Jan 2022)","D1 Jared Henderson (2024-2028)","D2 Teddy Hodges (2026-2030)","D3 M. Basham (2026-2030)","D4 T. Anderson (2026-2028, 2-yr term)"],"comments_published":"unconfirmed - inline public-hearing speaker notes in minutes; check PrimeGov eComment + council Packets before declaring submit-only","council_structure_history":"AT LARGE through 2009; transitioned to 4 districts ~2010-2011 (2011 first numbered contests, DIST by 2013); entire 2020+ record is stable 4-district+mayor - change is below the floor, no 2020+ effect","gis_source":"OFFICIAL HerrimanDistricts FeatureServer (owner HCPublicWorks, 4 polygons) https://services2.arcgis.com/XBmqwOHlPh25M7aJ/arcgis/rest/services/HerrimanDistricts/FeatureServer/0 ; UGRC muni boundary NAME='HERRIMAN'; VistaBallotAreas CountyID 49035 (Salt Lake) for precinct join","blockers":["2020 floor not in PrimeGov - recover from legacy S3 bucket (listing AccessDenied, objects live; keys via Wayback) and MIRROR EARLY","mayor tie-break behavior unconfirmed (mayor non-voting on ordinary motions confirmed)","no contested/Nay roll call in sample - confirm dissent wording on first contested motion","public-comment availability not finalized (check eComment + packets)","2019 election gap (D1/D4) - re-parse raw SLCo SOVC; 2025 D4 is a 2-year special","district-layer vintage current/post-2020-census (pre-2022 address lookups may differ)"],"confidence_notes":"HIGH: vendor, minutes+PC URL patterns, named-roll-call votes (3 docs across 2020/2021/2025), 4-district structure, mayor non-voting, official GIS layer, election coverage. MEDIUM: 2020 S3 recovery path (objects confirmed live, full-year completeness not enumerated), comments verdict, mayor tie-break. County=Salt Lake 49035."}
```
