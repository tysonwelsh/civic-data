# Millcreek City, Utah — Civic Data Recon

**City:** Millcreek City, **Salt Lake County**, Utah (~62k pop.)
**Recon date:** 2026-07-06
**Scope of interest:** 2020–present (floor 2020)
**Form of government:** **Council–Mayor form.** **Mayor (elected at-large) + 4 council
districts = 5 voting members.** The **mayor VOTES as a full member** (confirmed in a real
minutes sample — see §1). No at-large council seats.
**Incorporation:** Residents voted to incorporate **Nov 3, 2015**; first officials
(mayor + all 4 districts) elected **Nov 2016**; incorporation legally recorded
**Dec 28, 2016**. → **There is NO Millcreek council/PC record before 2016–2017. The short
history is legitimate, not a gap.** City Council minutes start 2016; PC 2017. **The 2020
floor is fully covered** — no early-year hole to backfill.
**Official site:** `https://www.millcreekut.gov/` (CivicPlus/CivicEngage CMS).
⚠ **Domain moved:** the old `millcreek.us` now **301-redirects to `millcreekut.gov`** —
use `millcreekut.gov` everywhere; treat `millcreek.us` as a legacy alias.

---

## 1. Council meeting minutes

### Portal — CivicPlus / CivicEngage **AgendaCenter** (single portal, all bodies)
- **Host:** `https://www.millcreekut.gov`
- **Landing:** `https://www.millcreekut.gov/AgendaCenter` (JS-rendered category app; the
  static HTML still carries the current-window links — harvestable).
- **Minutes doc URL pattern (CONFIRMED, direct GET):**
  ```
  https://www.millcreekut.gov/AgendaCenter/ViewFile/Minutes/_<MMDDYYYY>-<docId>
  ```
  e.g. `.../ViewFile/Minutes/_05112026-1037` (City Council, May 11 2026). Agenda variant:
  `.../ViewFile/Agenda/_<MMDDYYYY>[-docId]`. Each `<a>` carries an `aria-label` naming the
  **date + body** ("May 11, 2026, City Council Meeting … Minutes") — parse it to route the
  file to the right body. `<docId>` is NOT date-ordered; harvest links, don't guess IDs.
- **Category enumeration:** categories render as `cat2…cat15` in the JS app; the plain
  AgendaCenter HTML only exposes the current time-window. To enumerate ALL years, use the
  CivicPlus paged views — `AgendaCenter/PreviousVersions` and the per-category
  `AgendaCenter/Search` / `UpdateCategoryList` endpoints (or the standard CivicPlus
  `/AgendaCenter/Search/?term=&CIDs=<cat>&startDate=&endDate=` POST). Time-boxed here; the
  ViewFile pattern itself is proven.
- **Bodies present in AgendaCenter (with minutes):**
  | Body | Years w/ minutes | Notes |
  |---|---|---|
  | **City Council** | **2016 → 2026** | primary dataset; work + regular each meeting |
  | **Planning Commission** | **2017 → 2026** | OWN PC — see §3 |
  | **Community Reinvestment Agency (CRA)** | 2018 → 2026 | redevelopment body (RDA-equivalent); separate meetings/votes — analogous to SLC/Ogden RDA |
  | Historic Preservation Commission | 2022 → 2026 | |
  | Millcreek Community Foundation | 2022 → 2026 | |
  | Board of Canvassers / Hearing Officer / Mayor / Planning Director | various | mostly non-vote or sparse |

### Format — text PDF **with OCR-grade garble** (⚠ acquisition risk)
`ViewFile/Minutes/_…` returns a **large combined Agenda + Packet + Minutes PDF**
(8–10 MB each; minutes text is the first ~1,000 lines/pp). `pdftotext -layout` yields
readable text BUT with **systematic OCR-style corruption**: `Councn Member`,
`TTipi voterl yes`, `Coinmission`, `Plaru'ier`, `01son`, `snd Maynr.Tsirkqnn vnt`,
`Coinrnunications`. So the PDFs are **scanned-and-OCR'd (or a bad text layer)**, not clean
born-digital. **Vote extraction must tolerate garbled member names** (fuzzy-match against
the known 5-member roster). CONFIRMED on two 2026 docs (council + PC).

### Meeting cadence — **Monday**
- **City Council: 2nd & 4th Monday.** Two sessions same day → **Work Meeting 5:00 p.m.**
  + **Regular Meeting 7:00 p.m.** (one combined minutes doc per meeting-day observed).
  City Hall, 1330 E. Chambers Ave.

### Roll-call votes in minutes — **CONFIRMED PRESENT, NAMED roll-call (best-case format)**
Every motion records **mover + seconder + each member's vote BY NAME**, then the tally:
> *"Council Member Catten moved … Council Member DeSirant seconded. Mayor Jackson called
> for the vote. Council Member Catten voted yes, Council Member DeSirant voted yes,
> Council Member Handy voted yes, Council Member Uipi voted yes, and **Mayor Jackson voted
> yes**. The motion passed unanimously."*

- **The MAYOR is a voting member** ("and Mayor Jackson voted yes" appears in the roll) →
  **max council tally = 5** (4 districts + mayor). This is a genuine named roll-call (like
  West Jordan council / Ogden), **NOT** a South-Jordan-style anonymous "5-0" tally →
  member-level vote extraction is possible for every motion. Attendance = `PRESENT:` header
  block (also flags electronic/late arrivals, e.g. "Bev Uipi, District 4 (electronic,
  arrived 5:35pm)"). Sample observed was unanimous; the dissent form is presumably
  "Member X voted no" — verify on a contested motion during extraction.

---

## 2. Council structure — Mayor (at-large, **votes**) + 4 districts

- **Mayor** elected citywide; **4 council districts** (Districts 1–4). 4-yr staggered
  terms. **2016 ballot confirmed the "COUNCIL-MAYOR FORM"** (mayor is a full voting
  member — confirmed in minutes).
- **Current members (from 2026-05-11 minutes header):**
  | Seat | Member |
  |---|---|
  | Mayor (citywide) | **Cheri Jackson** |
  | District 1 | Silvia Catten |
  | District 2 | Thom DeSirant |
  | District 3 | Nicole Handy |
  | District 4 | Bev Uipi |
- **Leadership note:** Jeff Silvestrini was the founding mayor (2017–2025). **Cheri
  Jackson** (previously **District 3** council, elected 2016) became **Mayor in Nov 2025**;
  **Nicole Handy** now holds District 3. Watch for this mid-record seat change when
  attributing votes by person.
- **Stagger (from election archive, see §5):** Districts **2 & 4** elected 2017, 2021, 2025;
  Districts **1 & 3 (+ Mayor)** on the 2019/2023/2027 cycle.
- Council page: `https://www.millcreekut.gov/180/City-Council` (also `/231/City-Council`).

---

## 3. Planning Commission — **Millcreek has its OWN PC (CRITICAL ANSWER: not the county)**

- **Millcreek runs its own Planning Commission** with published minutes on the SAME
  AgendaCenter portal — **2017 → 2026**. It does **NOT** rely on Salt Lake County planning.
  (Post-incorporation Millcreek stood up a full land-use apparatus: PC + Planning Director +
  Historic Preservation Commission + Hearing Officer, all in AgendaCenter.)
- **Cadence:** **Wednesday** (3rd Wednesday observed), 5:00 p.m. Regular Meeting, City Hall.
- **Votes/recommendations — CONFIRMED recorded, NAMED roll-call** (sample
  `ViewFile/Minutes/_05202026-1043`): mover + seconder + **each commissioner voted yes/no by
  name** + tally. Explicit **referral language**: *"Commissioner Reid moved that the Planning
  Commission recommend to the City Council …"* and cross-references council action
  (*"Council voted 5-0 on May 5 to recommend approval of the rezone request"*) → **excellent
  PC→Council referral linkage.** ~8–9 commissioners; absentees named in the `PRESENT:`
  header. Same OCR garble as council docs.

---

## 4. Public comments

**Verdict: UNCLEAR → most likely inline-in-minutes + live online comment; no separate
published written-comment archive located (do NOT conclude unavailable — auditor's call).**
- Minutes state each meeting "had an **option for online public comment**" (livestream +
  online comment during the meeting) and transcribe **public-hearing** speakers inline
  (e.g. *"Dale Reeves, 2890 E, expressed concern about pedestrian safety…"*). Per
  extraction_standards these are **meeting-record speaker notes, NOT genuine written
  comments** → a labeled `minutes_speaker_log.csv`, never `all_comments_clean.csv`.
- **No dedicated comments page / eComment / Open City Hall archive** surfaced.
- **Best remaining lead:** the ViewFile/Minutes docs are **combined Agenda + Packet** PDFs
  (8–10 MB) — written correspondence/emailed comments may be bundled **inside the packet
  portion** (as with West Jordan). Grep the packet pages for "correspondence"/emailed
  comment before declaring none.
- **Live stream / video:** `https://www.millcreekut.gov/373/Meeting-Live-Stream` (potential
  transcript source for an expand-sources phase).

---

## 5. Elections — Salt Lake County (existing archive covers Millcreek, with gaps)

- **Run by:** Salt Lake County Clerk (`https://saltlakecounty.gov/clerk/elections/`).
- **District-based council** + at-large mayor.
- **Existing shared archive `~/Desktop/slco-election-archive/` already carries Millcreek.**
  **Filter on the `contest` column, NOT `sheet`** — 2021/2023/2025 contests sit under
  generic `SheetNN` names but the `contest` field holds the real string
  (`MILLCREEK … COUNCIL DISTRICT N`). Coverage:

  | Year | File | Millcreek contests present |
  |---|---|---|
  | 2012 | `sovc_long.csv` | ballot Qs: INCORPORATION OF MILLCREEK, FORM OF GOVERNMENT, COUNCIL DISTS (pre-history) |
  | 2015 | `2015_municipal_general.csv` | MILLCREEK METRO TOWNSHIP-CITY, MILLCREEK MSD (incorporation questions) |
  | **2016** | **`sovc_long.csv`** (even-year general/primary) | **MILLCREEK CITY MAYOR + all 4 COUNCIL DISTS + COUNCIL-MAYOR FORM Q** — the FOUNDING election. NOTE: even-year → lives in `sovc_long`, **not** the odd-year `*_municipal_general.csv` files. |
  | 2017 | `2017_municipal_general.csv` | Council **Dist 2, Dist 4** |
  | **2019** | `2019_municipal_general.csv` | **ZERO Millcreek rows** — see gap ⚠ |
  | 2021 | `2021_municipal_general.csv` | Council **District 2, District 4** (Sheet22/23) |
  | 2023 | `2023_municipal_general.csv` | Council **District 3** only (Sheet22) |
  | 2025 | `2025_municipal_general.csv` | Council **District 2, District 4** (Sheet29/30) |

- **⚠ ELECTION GAPS (biggest election risk):**
  1. **2019 general — entirely absent for Millcreek.** The 2019/2023 cycle should carry
     **Districts 1 & 3 (+ Mayor)**; 2019 has none. Likely uncontested/omitted-from-SOVC or a
     numbered-sheet layout that dropped the city string (same failure mode as South Jordan
     2019). → **re-parse the raw 2019 SOVC** for Millcreek Dist 1/3 (+ mayor).
  2. **2023 — only District 3 present; District 1 and any Mayor race missing.** Verify
     against raw 2023 SOVC.
  3. **Mayor odd-year races (2019, 2023) not found** in the archive. Founding mayor race is
     2016 (`sovc_long`). Silvestrini's re-election(s) and Jackson's 2025 mayor accession need
     sourcing — **confirm the mayor's election cycle** (the 2025 municipal file shows NO
     Millcreek mayor contest, consistent with Jackson being seated by council appointment /
     succession in Nov 2025 rather than elected — VERIFY).
- **Names carry `(NON)`/`(NP )` non-partisan suffixes** and are UPPER-CASE — normalize
  before joining to minutes rosters.

---

## 6. GIS — Millcreek council-district layer CONFIRMED (ArcGIS Online hosted)

- **Council-district polygons (preferred; verified `f=json` 200):**
  ```
  https://services9.arcgis.com/XRrSFvEwSsReIxuA/arcgis/rest/services/Millcreek_City_Council_Dist_2022/FeatureServer/2
  ```
  = **"Millcreek City Council Districts 2022-2032 Polygons"** (layer id **2** on that
  FeatureServer — layer 0/1 return "layer not found"; enumerate via the `?f=json` service
  root). ArcGIS Online item `5bf2141feb434742918a1c7b20f4b7e1` ("Millcreek City Council
  Districts 2022-2032"). ⚠ This is the **2022–2032 redistricting** boundary — for votes/
  elections **before 2022**, districts used the original 2016 lines; if pre-2022 address→
  district accuracy matters, source the earlier boundary too.
- **Millcreek GIS hub:** `https://maps-millcrk.hub.arcgis.com/` (org services9 /
  `XRrSFvEwSsReIxuA`); base-zoning layer item `7ec912e4711249c0b2cc6bf0bc5ff66f`
  ("Millcreek Base Zones") for land-use context. City maps portal: `maps.millcreekut.gov`.
- **UGRC fallbacks:** VistaBallotAreas **CountyID = 18** (Salt Lake) for precinct join;
  UGRC Municipal Boundaries (`services1.arcgis.com/99lidPhWCzftIe9K/.../UtahMunicipalBoundaries/FeatureServer/0`)
  `NAME='MILLCREEK'` for the city outline. Precinct geometry also in
  `~/Desktop/slco-election-archive/geo/`.

---

## Retrieval plan (recommended order)

1. **Council minutes 2016→present (CivicPlus AgendaCenter):** enumerate the City Council
   category (CivicPlus `Search`/`PreviousVersions` per year) → harvest
   `ViewFile/Minutes/_<MMDDYYYY>-<id>` links (route by `aria-label` body+date). Polite GET
   each (browser UA) → `raw/minutes/<year>/`. **Large (8–10 MB combined Agenda+Packet)** —
   budget bandwidth. `pdftotext -layout` → markdown; **flag OCR garble**.
2. **Vote extraction (council):** parse `<Member> voted yes/no … The motion passed …`;
   **max tally 5, MAYOR COUNTED as a voter**; `PRESENT:` header for attendance/electronic.
   **Fuzzy-match garbled names** to the 5-member roster. Verify dissent wording on first
   contested motion.
3. **Planning Commission 2017→present:** same portal/pattern (PC category). Parse named
   commissioner roll-calls; capture **"recommend to the City Council"** referral language +
   any case/file numbers for PC→Council linkage.
4. **CRA (optional Phase-2 body):** same portal; redevelopment-agency votes (RDA-equivalent)
   — treat as a separate `body` if included.
5. **Comments:** grep the Agenda+Packet PDFs' packet pages for emailed/written correspondence;
   otherwise build labeled `minutes_speaker_log.csv` + record the honest verdict.
6. **Elections:** reuse `~/Desktop/slco-election-archive` (filter `contest LIKE '%MILLCREEK%'`);
   pull founding **2016** race from `sovc_long`; **re-parse raw 2019 & 2023 SOVC** for the
   Dist 1/3 + mayor gap; resolve the mayor election cycle.
7. **Geo:** query `Millcreek_City_Council_Dist_2022/FeatureServer/2` → GeoJSON → address→
   District 1–4 tool (note 2022 boundary vintage); UGRC CountyID 18 fallback.

---

## Risks / blockers

- **OCR-garbled minutes text (HIGH):** systematic corruption of member names/words
  (`Councn`, `TTipi voterl`, `Coinmission`). Named roll-call is a gift, but the parser MUST
  fuzzy-match names to the fixed 5-member roster or votes will mis-attribute.
- **Mayor is a voting member (STRUCTURAL):** unlike South Jordan (mayor uncounted), Millcreek
  minutes count the mayor in the roll (max tally 5). Getting the denominator right is
  essential — confirmed in-sample, but re-verify on the first contested vote for the dissent
  format.
- **Large combined Agenda+Packet PDFs (8–10 MB each):** ~24 council + ~12 PC meetings/yr ×
  ~10 yrs = a heavy, slow harvest; minutes text is only the front of each file.
- **AgendaCenter full-history enumeration:** JS category app; static HTML shows only the
  current window. Needs the CivicPlus Search/PreviousVersions paged calls to reach 2016–2019.
- **2019 election entirely absent + 2023 partial (Dist 1 & mayor) + mayor cycle unclear:**
  the odd-year municipal files miss the 1/3+mayor class; needs raw-SOVC re-parse and a
  mayor-succession check (Jackson 2025 likely appointed, not elected — verify).
- **GIS boundary vintage:** only the **2022–2032** district layer is published; pre-2022
  votes/elections used the original 2016 lines (source separately if pre-2022 geo accuracy
  needed).
- **Domain migration:** `millcreek.us` → `millcreekut.gov` (301). Any cached/old URLs must be
  rewritten to `millcreekut.gov`.
- **Short history is REAL, not a gap:** record starts 2016 (council) / 2017 (PC); do not
  treat pre-2016 absence as missing data.

---

## Key URLs (quick index)

| What | URL |
|---|---|
| City site (canonical) | https://www.millcreekut.gov/ (legacy alias millcreek.us → 301) |
| AgendaCenter (all bodies) | https://www.millcreekut.gov/AgendaCenter |
| Minutes doc pattern | https://www.millcreekut.gov/AgendaCenter/ViewFile/Minutes/_<MMDDYYYY>-<docId> |
| Council minutes sample (verified) | https://www.millcreekut.gov/AgendaCenter/ViewFile/Minutes/_05112026-1037 |
| PC minutes sample (verified) | https://www.millcreekut.gov/AgendaCenter/ViewFile/Minutes/_05202026-1043 |
| City Council page | https://www.millcreekut.gov/180/City-Council |
| Meeting live stream | https://www.millcreekut.gov/373/Meeting-Live-Stream |
| SL County election results | https://saltlakecounty.gov/clerk/elections/ |
| Election archive (local) | ~/Desktop/slco-election-archive (Millcreek 2016–2025; 2019 + 2023-D1/mayor GAPS) |
| District GIS layer | https://services9.arcgis.com/XRrSFvEwSsReIxuA/arcgis/rest/services/Millcreek_City_Council_Dist_2022/FeatureServer/2 |
| Millcreek GIS hub | https://maps-millcrk.hub.arcgis.com/ |
| UGRC muni boundary | services1.arcgis.com/99lidPhWCzftIe9K/.../UtahMunicipalBoundaries/FeatureServer/0 (NAME='MILLCREEK') |

```json
{"city":"Millcreek","minutes":{"vendor":"CivicPlus/CivicEngage AgendaCenter","base_url":"https://www.millcreekut.gov/AgendaCenter","minutes_url_pattern":"/AgendaCenter/ViewFile/Minutes/_<MMDDYYYY>-<docId>","minutes_years":"City Council 2016-2026; PC 2017-2026 (no 2020 floor gap; city incorporated Dec 2016 so no earlier record exists)","format":"combined Agenda+Packet PDF 8-10MB, OCR-grade garbled text (fuzzy-match names)","votes_in_minutes":true,"vote_style":"NAMED roll-call, each member voted yes/no by name","meeting_weekday":"Monday (2nd & 4th; work 5pm + regular 7pm)"},
 "council":{"districts":4,"at_large":0,"mayor_votes":true,"max_tally":5,"members":["Mayor Cheri Jackson","D1 Silvia Catten","D2 Thom DeSirant","D3 Nicole Handy","D4 Bev Uipi"],"note":"mayor is a full voting member (max tally 5); Jackson moved from D3 council to Mayor Nov 2025, Handy now D3; founding mayor Silvestrini 2017-2025"},
 "planning_commission":{"own_pc":true,"uses_county":false,"years":"2017-2026","weekday":"Wednesday","votes_in_minutes":true,"referral_language":"'recommend to the City Council' - strong PC->Council linkage"},
 "other_bodies":["Community Reinvestment Agency (RDA-equivalent) 2018-2026","Historic Preservation Commission","Millcreek Community Foundation","Hearing Officer","Board of Canvassers"],
 "comments":{"published":"unclear","where":"inline-in-minutes speaker notes + online-comment-during-livestream; check packet pages of combined Agenda+Packet PDFs for written correspondence","submit":"in-person + online during meeting; livestream at /373/Meeting-Live-Stream"},
 "elections":{"county":"Salt Lake","source_url":"https://saltlakecounty.gov/clerk/elections/","existing_archive":"~/Desktop/slco-election-archive (Millcreek 2016 founding in sovc_long; 2017/2021/2025 D2&D4; 2023 D3; filter by contest column not sheet)","district_based":true,"gaps":"2019 general entirely absent; 2023 D1 & mayor missing; mayor odd-year cycle unclear (Jackson 2025 likely appointed - verify); re-parse raw 2019/2023 SOVC"},
 "geo":{"ugrc_county_id":18,"boundaries_available":true,"district_layer":"https://services9.arcgis.com/XRrSFvEwSsReIxuA/arcgis/rest/services/Millcreek_City_Council_Dist_2022/FeatureServer/2","layer_id":2,"vintage":"2022-2032 redistricting (pre-2022 used original 2016 lines)"},
 "risks":["OCR-garbled minutes text - fuzzy-match names to 5-member roster","mayor IS a voting member (max tally 5) unlike South Jordan - verify dissent format on first contested vote","large 8-10MB combined Agenda+Packet PDFs, minutes at front only","AgendaCenter full-history needs CivicPlus Search/PreviousVersions paging to reach 2016-2019","2019 election absent + 2023 partial + mayor cycle unclear - raw SOVC re-parse","GIS layer is 2022-2032 vintage only","millcreek.us->millcreekut.gov 301 domain move","short history 2016+ is REAL not a gap"],
 "recommended_order":["council minutes 2016+ AgendaCenter","council named-vote extraction (mayor counted, fuzzy names)","PC minutes+votes+referrals","CRA optional","comments hunt in packets + speaker log","elections reuse archive + 2016 founding + 2019/2023 gap re-parse","geo FeatureServer/2 -> address tool"]}
```
