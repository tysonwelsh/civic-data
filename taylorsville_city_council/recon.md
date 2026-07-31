# Taylorsville City, Utah — Civic Data Recon

**City:** Taylorsville City, **Salt Lake County**, Utah (~60k pop.)
**Recon date:** 2026-07-06
**Scope of interest:** 2020–present (floor 2020 — city **incorporated 1996**, so full modern
history exists; 2020 is a normal floor, not an incorporation edge like Millcreek).
**Form of government:** **Council–Mayor form** (a.k.a. "six-member"? — NO). Taylorsville is a
**5-district council + a separately-elected executive Mayor + an appointed City Administrator**.
The council **elects its own Chair / Vice-Chair to preside** (the Mayor does NOT chair the
council). → **The Mayor is the EXECUTIVE and does NOT vote on ordinary council motions;
max council tally = 5.** See §2 (confirmed against a real minutes doc).
**Official site:** `https://www.taylorsvilleut.gov/` — **CivicPlus / CivicEngage Central**
CMS (Granicus-owned; "granicus" in page chrome). ⚠ Site **403s a bare bot User-Agent** — must
fetch with a browser UA (use `polite_fetch.py`; WebFetch was blocked, `polite_fetch` succeeded).

---

## 1. Council meeting minutes

### Portal — CivicPlus / CivicEngage Central (single portal, all bodies)
- **Host:** `https://www.taylorsvilleut.gov`
- **Agendas & Minutes landing:**
  `https://www.taylorsvilleut.gov/government/elected-officials/city-council-agendas-minutes`
- **Structure = year folders** (three parallel columns on the page = **Agendas**, **Minutes**,
  **Audio Recordings**), each a CivicEngage document folder:
  ```
  /government/elected-officials/city-council-agendas-minutes/-folder-<N>
  ```
  The **Minutes** column runs **year folders 2008 → 2026** (folder ids incl. 2026=`-folder-437`,
  2025=`340`, 2024=`312`, 2023=`288`, 2022=`257`, 2021=`193`, **2020=`151`**, 2019=`101` …).
  → **2020 floor is fully covered on the city portal itself** (no PMN dependency needed, though
  PMN is a live fallback — see below). Folder ids are NOT sequential-by-year; **harvest the
  labeled `<a>` links, don't guess ids.**
- **Minutes document URL pattern (CivicEngage `showpublisheddocument`):**
  ```
  https://www.taylorsvilleut.gov/home/showpublisheddocument/<docId>/<versionToken>
  ```
  (older docs also appear as `/Home/ShowDocument?id=<n>`). Enumerate a year folder → harvest its
  `showpublisheddocument` links → curl each PDF (browser UA) into `raw/`.
- **PMN fallback / cross-check:** every meeting is also mirrored on **Utah Public Notice**
  (`utah.gov/pmn`). **Council body id = 720** (`utah.gov/pmn/sitemap/publicbody/720.html`).
  Minutes PDFs live at `https://www.utah.gov/pmn/files/<fileId>.pdf`
  (e.g. **Sept 3 2025 minutes = `utah.gov/pmn/files/1321911.pdf`** — the doc verified below).
  Use PMN if a city-portal year is missing or the CMS blocks.

### Format — CONFIRMED born-digital clean text PDF (NO OCR garble)
`pdftotext -layout` on the **2025-09-03 council minutes** yields clean, selectable, line-numbered
text — proper names intact (`Mayor Kristie Overson`, `Chair Meredith Harker`, `Council Member
Anna Barbieri`). **Not scanned, no OCR corruption** (unlike Millcreek). Read parses directly.

### Meeting cadence — **Wednesday**
- **City Council: 1st & 3rd Wednesdays.** Each meeting-day = a **6:00 PM Briefing Session** +
  a **6:30 PM Regular Meeting**, both captured in **one combined minutes doc** (verified).
  Council Chambers (Room 140), 2600 W Taylorsville Blvd.
- Every **5th Wednesday** is *"Let's Talk Taylorsville"* — an informal constituent session
  (likely little/no formal voting; keep if minutes exist, flag as non-standard).

### Roll-call votes in minutes — CONFIRMED PRESENT (narrative-tally style; **South-Jordan-like**)
Motions record **mover + seconder + a narrative outcome**, NOT a per-member named roll-call:
> *"MOTION: Council Member Knudsen moved to approve the minutes of the August 6, 2025 city
> council meeting. The motion was seconded by Council Member Burgess and passed unanimously on
> a roll call vote."*

- **Names appear only for mover & seconder**; unanimous outcomes are stated as *"passed
  unanimously on a roll call vote"* with **no per-member Aye/Nay list** (a genuine roll call is
  taken and attendance is a `Present:`/`Excused:` header block, but the printed minutes give the
  narrative result, not each member's vote). This is **South Jordan-style**, NOT the Millcreek
  named roll-call. → member-level attribution is possible only via mover/seconder + attendance;
  dissent must be read from *"…N-M, Council Member X opposed"*-type prose.
- **The Mayor never moves/seconds/votes** in the sample (she gives executive updates); every
  motion is by a **Council Member**. **Max council tally = 5.**
- ⚠ **Both motions in the verified sample were unanimous** — the **dissent-naming format is
  UNCONFIRMED** (same open question as South Jordan). Pull a contested rezone/budget public-
  hearing meeting to lock the parser's dissent pattern before bulk extraction.

---

## 2. Council structure — 5 districts + executive Mayor (Mayor does NOT vote)

- **5 council districts (Districts 1–5)**, one member each; **Mayor elected citywide** as the
  **executive** (appoints a **City Administrator**, John Taylor — confirmed in minutes header).
  No at-large council seats. **4-year staggered, non-partisan terms.**
- **Current roster** (from the 2025-09-03 minutes header + `/government/elected-officials/council`
  + 2023/2025 election winners in the archive):

  | Seat | Member | Council role |
  |---|---|---|
  | Mayor (citywide, executive) | **Kristie Steadman Overson** | presides over city, non-voting on council |
  | District 1 | **Ernest ("Ernie") Glen Burgess** | |
  | District 2 | **Curt Cochran** | |
  | District 3 | **Anna Barbieri** | |
  | District 4 | **Meredith Harker** | **Council Chair** (conducts meetings) |
  | District 5 | **Bob Knudsen** | **Vice Chair** |

- **⚠ MAYOR-VOTE DETERMINATION (key structural decision):** In the verified minutes, **Chair
  Harker (a council member) calls the meeting to order and conducts it**, and **every motion is
  moved/seconded/decided by the 5 Council Members** — the Mayor gives updates but is never in a
  motion or tally. This is Utah's **council–mayor (executive-mayor) form**: the Mayor is the
  executive, **not** a voting council member. → **Build with max council tally = 5, Mayor
  non-voting.** (The Mayor may hold a statutory **veto** rather than a vote; that would surface
  as separate veto language, not a roll-call entry — watch for it, but it does not change the
  tally denominator.) This differs from **Millcreek** (6-member form, mayor votes, tally 5 incl.
  mayor) and **South Jordan** (6-member, mayor uncounted in practice).
- **Term stagger (from the election archive, §5):** **Districts 4 & 5 + Mayor** on the
  **2017/2021/2025** cycle; **Districts 1, 2, 3** on the **2019/2023** cycle. (⚠ 2021 also ran a
  **District 3** contest — a special/short unexpired term — see §5.)
- Council page: `https://www.taylorsvilleut.gov/government/elected-officials/council`
  (member emails `<surname>@taylorsvilleut.gov`; the page is JS-rendered — roster came from the
  static HTML name list + minutes). Find-my-rep tool (JS-only, no static district text):
  `https://www.taylorsvilleut.gov/i-want-to/find-my-city-council-representative`.

---

## 3. Planning Commission — **Taylorsville has its OWN PC (not the county)**

- **Own Planning Commission**, minutes on the SAME CivicEngage portal (confirmed independently):
  - Landing: `https://www.taylorsvilleut.gov/government/planning-commission`
  - **Minutes:** `https://www.taylorsvilleut.gov/government/planning-commission/planning-commission-meeting-minutes`
  - Agendas: `.../planning-commission/planning-commission-meeting-agendas`
  - Packets: `.../planning-commission/planning-commission-packet`
  - Public Notices: `.../planning-commission/planning-commission-public-notices`
  - Livestream: `.../planning-commission/planning-commission-livestream`
- **Doc pattern:** same `showpublisheddocument` / older `/Home/ShowDocument?id=<n>` (e.g. a
  **May 10 2016 PC minutes = `/Home/ShowDocument?id=2556`**) → **coverage reaches at least 2016**,
  well before the 2020 floor.
- **Cadence:** **2nd & 4th Tuesday**, 6:00 p.m. (public hearings ~7:00 p.m.), Council Chambers.
- **Votes/recommendations — expected recorded** (same clerk shop as council; the PC minutes doc
  pattern is confirmed live, but a PC minutes doc was **not text-verified in this recon** —
  spot-check the vote/recommendation format on the first PC doc during acquisition; expect the
  same narrative-tally + PC→Council recommendation language).

---

## 4. Public comments

**Verdict: UNCLEAR → most likely inline-in-minutes speaker notes only; no separate published
written-comment archive located (do NOT conclude unavailable — auditor's call).**
- Minutes carry an **`Others Present:`** attendee list and transcribe **public-hearing** speakers
  inline (clerk paraphrase). Per extraction_standards these are **meeting-record speaker notes,
  NOT genuine written comments** → a labeled `minutes_speaker_log.csv`, never
  `all_comments_clean.csv`.
- **No dedicated comments page / eComment / Open City Hall / "correspondence received" archive**
  surfaced. Public comment is taken **in-person at meetings** and via the **livestream**
  (`/government/elected-officials/city-council-livestream`).
- **Best remaining leads (Phase 2, before declaring none):** the **Planning Commission Packets**
  page (`.../planning-commission-packet`) and any council agenda-packet docs may bundle written
  correspondence; grep packet pages for emailed/written comment.

---

## 5. Elections — Salt Lake County (existing archive covers Taylorsville 2007–2025; 2019 GAP)

- **Run by:** Salt Lake County Clerk. City elections page:
  `https://www.taylorsvilleut.gov/government/elections`. Live official results also at
  `https://electionresults.utah.gov/` (Salt Lake County) for recent cycles.
- **District-based council** + citywide Mayor; **non-partisan**.
- **Existing shared archive `~/Desktop/slco-election-archive/` ALREADY covers Taylorsville.**
  Filter **on the `contest` column text `%TAYLORSVILLE%`, NOT `sheet`** (2021/2023/2025 contests
  sit under generic labels; ⚠ the archive's `normalize_sovc.py` **mis-files sheet codes** — same
  defect seen for South Jordan). `data/municipal_results_long.csv` coverage:

  | Year | Taylorsville council/mayor contests present | Label style |
  |---|---|---|
  | 2007 | City Council 1, 2, 3 | clean |
  | 2009 | Council District 4, 5 + **Mayor** | clean |
  | 2011 | City Coun 1, 2, 3 (dup upper/mixed-case rows) | clean-ish |
  | 2013 | City Council 3, 4, 5 + **Mayor** | clean |
  | 2015 | City Council 1, 2, 3 | clean |
  | 2017 | City Cncl Dist 4, 5 + **Mayor** (+ Taylorsville-Bennion Improve. Dist) | clean |
  | **2019** | **NONE — 0 rows (GAP)** | — |
  | 2021 | Council District **3, 4, 5** + **Mayor** | `CITY OF TAYLORSVILLE …` (generic sheets) |
  | 2023 | Council District **1, 2, 3** | `CITY OF TAYLORSVILLE …` |
  | 2025 | Council District **4, 5** + **Mayor** (+ Taylorsville-Bennion Improvement Dist) | `TAYLORSVILLE CITY …` |

- **⚠ ELECTION GAPS / anomalies:**
  1. **2019 general — entirely absent for Taylorsville (0 rows).** The 2019/2023 cycle should
     carry **Districts 1, 2, 3**; 2019 has none (same failure mode as South Jordan & Millcreek
     2019 — numbered-sheet layout dropped the city string, or uncontested seats omitted). →
     **re-parse the raw 2019 SOVC** for Taylorsville Districts 1/2/3.
  2. **2021 District 3** appears **out of its normal 2019/2023 cycle** alongside the regular
     4/5+Mayor race → almost certainly a **special / 2-yr unexpired-term** election. Note it so
     the member-term logic doesn't treat it as a cycle shift (Barbieri then won the full
     District 3 term in 2023).
- Winners are UPPER-CASE and some carry non-partisan suffixes — normalize before joining to the
  minutes roster (e.g. `ERNEST GLEN BURGESS`→Burgess D1, `CURT COCHRAN`→D2, `ANNA BARBIERI`→D3,
  `MEREDITH HARKER`→D4, `BOB KNUDSEN`→D5, `KRISTIE STEADMAN OVERSON`→Mayor).

---

## 6. GIS — no dedicated city district FeatureServer found; derive from precincts + UGRC

- **No standalone Taylorsville council-district ArcGIS FeatureServer surfaced** in recon (the
  one Taylorsville ArcGIS item found — `6757e1aed9e54a48a942644139c958a6` — is a *retail/
  demographic* map by "TheRetailCoach", NOT districts). District boundaries were **redistricted
  after the 2020 census** ("0% deviation", 5 districts) — city news:
  `https://www.taylorsvilleut.gov/Home/Components/News/News/496/`. The boundaries are also
  defined **textually in municipal code 13.04.100**
  (`https://codelibrary.amlegal.com/codes/taylorsvilleut/latest/taylorsville_ut/0-0-0-5556`).
- **Recommended district-polygon approach (proven fallback, as used for SJ/Millcreek):**
  **derive district polygons from precinct→district assignment** — the archive already ships
  Salt Lake County precinct geometry:
  `~/Desktop/slco-election-archive/geo/slco_precincts_current.geojson` (+ `.gpkg`); each 2023/2025
  district contest's precinct rows (the SOVC `precinct` column) map precincts→District 1–5 →
  dissolve to district polygons.
- **UGRC fallbacks:** VistaBallotAreas **CountyID = 18** (Salt Lake) for the precinct join; UGRC
  **Municipal Boundaries** `NAME='TAYLORSVILLE'`
  (`services1.arcgis.com/99lidPhWCzftIe9K/.../UtahMunicipalBoundaries/FeatureServer/0`) for the
  city outline.
- **Also check (Phase 2):** Salt Lake County open data
  (`https://gisdata-slco.opendata.arcgis.com/`) may host municipal council-district polygons.

---

## Retrieval plan (recommended order)

1. **Council minutes 2020→present (CivicEngage):** for each **Minutes** year folder on
   `/…/city-council-agendas-minutes/-folder-<N>` (2020=`151`, 2021=`193`, 2022=`257`, 2023=`288`,
   2024=`312`, 2025=`340`, 2026=`437`), harvest `showpublisheddocument` links → curl each PDF
   **(browser UA — site 403s bots)** → `raw/minutes/<year>/`. Combined Briefing+Regular = one
   doc/day. Text-layer → markdown (clean, no OCR).
2. **Vote extraction (council):** parse `MOTION: Council Member X moved … seconded by Council
   Member Y … passed unanimously on a roll call vote` / `…N-M, Council Member Z opposed`;
   `Present:`/`Excused:` header for attendance; **max tally 5, Mayor NON-voting**;
   unanimous-no-names → `names_recorded:false`. Verify dissent wording on the first contested
   motion.
3. **Planning Commission 2020→present:** same portal, `/government/planning-commission/
   planning-commission-meeting-minutes`. Text-verify the first PC doc's vote/recommendation
   format; capture PC→Council recommendation language + any case/file numbers.
4. **Comments:** grep council & **PC packet** pages for emailed/written correspondence; otherwise
   build a labeled `minutes_speaker_log.csv` + record the honest verdict.
5. **Elections:** reuse `~/Desktop/slco-election-archive` (filter `contest LIKE '%TAYLORSVILLE%'`);
   **re-parse the raw 2019 SOVC** for Districts 1/2/3; flag the **2021 District 3 special**.
6. **Geo:** derive District 1–5 polygons from `geo/slco_precincts_current.geojson` × the district
   contests' precinct rows → address→district tool; UGRC CountyID 18 fallback.

---

## Risks / blockers

- **Bot-blocked CMS (MEDIUM):** `taylorsvilleut.gov` returns **403 to a bare UA**; WebFetch fails.
  Use `polite_fetch.py` (browser UA) for every fetch — proven working this recon.
- **Mayor-vote form (STRUCTURAL, but resolved):** council–mayor executive form → **Mayor does
  NOT vote, max tally = 5**; confirmed by the council electing its own Chair to preside and the
  Mayor never appearing in a motion. Watch for a **mayoral veto** (separate language, not a
  tally). Getting this right sets every vote's denominator.
- **No named dissent observed:** the verified sample was 100% unanimous → the contested-vote
  naming format is **unconfirmed**. Pull a rezone/budget public-hearing meeting to lock the
  dissent parser before bulk extraction.
- **PC vote format text-unverified:** portal + coverage confirmed, but no PC minutes doc was
  parsed this recon — verify format on the first PC file.
- **2019 election gap (Districts 1/2/3) + 2021 District 3 special:** raw-2019-SOVC re-parse
  needed; don't let the 2021 D3 special masquerade as a cycle change.
- **Election sheet mis-filing:** archive `normalize_sovc.py` mis-files sheet codes — **filter by
  `contest` text `%TAYLORSVILLE%`, not sheet** (as done here).
- **No city GIS district service:** derive districts from precincts (archive geojson) + UGRC;
  redistricting means pre-2022 vs 2022+ boundaries differ — if pre-2022 address→district accuracy
  matters, source the earlier lines (municipal code 13.04.100 / older SOVC precincts).

---

## Key URLs (quick index)

| What | URL |
|---|---|
| City site (CivicEngage; 403s bots) | https://www.taylorsvilleut.gov/ |
| Council agendas & minutes landing | https://www.taylorsvilleut.gov/government/elected-officials/city-council-agendas-minutes |
| Minutes year-folder pattern | https://www.taylorsvilleut.gov/government/elected-officials/city-council-agendas-minutes/-folder-<N> (2020=151 … 2026=437) |
| Minutes doc pattern | https://www.taylorsvilleut.gov/home/showpublisheddocument/<docId>/<versionToken> (older: /Home/ShowDocument?id=<n>) |
| Council minutes sample (verified) | https://www.utah.gov/pmn/files/1321911.pdf (2025-09-03) |
| PMN council body | https://www.utah.gov/pmn/sitemap/publicbody/720.html (id 720) |
| City Council page | https://www.taylorsvilleut.gov/government/elected-officials/council |
| Council livestream | https://www.taylorsvilleut.gov/government/elected-officials/city-council-livestream |
| Planning Commission | https://www.taylorsvilleut.gov/government/planning-commission |
| PC minutes | https://www.taylorsvilleut.gov/government/planning-commission/planning-commission-meeting-minutes |
| PC packets | https://www.taylorsvilleut.gov/government/planning-commission/planning-commission-packet |
| Elections (city) | https://www.taylorsvilleut.gov/government/elections |
| SL County live results | https://electionresults.utah.gov/ (Salt Lake County) |
| Election archive (local) | ~/Desktop/slco-election-archive (Taylorsville 2007–2025 present; **2019 GAP**) |
| Precinct geometry (for districts) | ~/Desktop/slco-election-archive/geo/slco_precincts_current.geojson |
| Redistricting news | https://www.taylorsvilleut.gov/Home/Components/News/News/496/ |
| District boundary code | https://codelibrary.amlegal.com/codes/taylorsvilleut/latest/taylorsville_ut/0-0-0-5556 (13.04.100) |

```json
{"city":"Taylorsville","minutes":{"vendor":"CivicPlus/CivicEngage Central (Granicus)","base_url":"https://www.taylorsvilleut.gov/government/elected-officials/city-council-agendas-minutes","minutes_url_pattern":"/home/showpublisheddocument/<docId>/<versionToken> ; year folders /-folder-<N> (2020=151..2026=437)","minutes_years":"2008-2026 on city portal (2020 floor fully covered); PMN fallback body id 720","format":"born-digital clean text PDF (no OCR garble)","votes_in_minutes":true,"vote_style":"narrative tally - mover+seconder named, 'passed unanimously on a roll call vote'; no per-member Aye/Nay (South Jordan-like); dissent format unconfirmed","meeting_weekday":"Wednesday (1st & 3rd; briefing 6:00pm + regular 6:30pm; 5th-Wed 'Let's Talk Taylorsville')","access_note":"site 403s bare UA - use polite_fetch browser UA"},
 "council":{"districts":5,"at_large":0,"mayor_votes":false,"max_tally":5,"form":"council-mayor executive form (mayor is executive, appoints city administrator, council elects own Chair to preside)","members":["Mayor Kristie Steadman Overson (executive, non-voting)","D1 Ernest Burgess","D2 Curt Cochran","D3 Anna Barbieri","D4 Meredith Harker (Chair)","D5 Bob Knudsen (Vice Chair)"],"stagger":"D4/D5/Mayor 2017/2021/2025; D1/D2/D3 2019/2023 (2021 also ran a D3 special/unexpired term)","note":"watch for a possible mayoral veto (separate from a tally)"},
 "planning_commission":{"own_pc":true,"uses_county":false,"years":">=2016 on same CivicEngage portal","weekday":"Tuesday (2nd & 4th, 6pm; hearings ~7pm)","minutes_url":"https://www.taylorsvilleut.gov/government/planning-commission/planning-commission-meeting-minutes","votes_in_minutes":"expected (same clerk shop) - text-verify first PC doc"},
 "comments":{"published":"unclear","where":"inline-in-minutes speaker notes (Others Present + hearing speakers) + livestream; check PC/council packets for written correspondence","submit":"in-person at meetings + livestream"},
 "elections":{"county":"Salt Lake","source_url":"https://electionresults.utah.gov/ (SL County) ; https://www.taylorsvilleut.gov/government/elections","existing_archive":"~/Desktop/slco-election-archive (Taylorsville 2007-2025 present; filter contest text %TAYLORSVILLE% not sheet)","district_based":true,"gaps":"2019 general entirely absent (Districts 1/2/3) - raw SOVC re-parse; 2021 District 3 is a special/unexpired term"},
 "geo":{"ugrc_county_id":18,"boundaries_available":true,"district_layer":"none found - derive District 1-5 polygons from ~/Desktop/slco-election-archive/geo/slco_precincts_current.geojson x district-contest precinct rows; UGRC muni boundary NAME='TAYLORSVILLE'; SLCo open data gisdata-slco.opendata.arcgis.com as further check","note":"boundaries redistricted after 2020 census (5 districts, 0% deviation); code 13.04.100 defines lines textually"},
 "risks":["site 403s bare UA - use polite_fetch browser UA","mayor is executive & does NOT vote (max tally 5) - confirmed; watch for veto","no contested vote in sample - dissent-naming format unconfirmed","PC vote format text-unverified this recon","2019 election gap (D1/2/3) + 2021 D3 special - raw SOVC re-parse","archive sheet mis-filing - filter by contest text","no city district FeatureServer - derive from precincts + UGRC; pre-2022 vs 2022+ boundary vintage"],
 "recommended_order":["council minutes 2020+ CivicEngage year folders (browser UA)","council vote extraction (mayor non-voting, tally 5, verify dissent)","PC minutes+votes (verify format)","comments hunt in packets + speaker log","elections reuse archive + 2019 raw re-parse + flag 2021 D3 special","geo derive districts from precinct geojson -> address tool"]}
```
