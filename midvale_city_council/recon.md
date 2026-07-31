# Midvale City, Utah — Civic Data Recon

**City:** Midvale City, **Salt Lake County**, Utah (~36k pop.; incorporated **1909**).
**Recon date:** 2026-07-11
**Scope of interest:** 2020–present (**floor 2020** — Midvale is a century-old city, so full
modern history exists; 2020 is a normal floor, not an incorporation edge like Millcreek).
**Form of government:** **Utah "six-member council" form** — a council of **five district
council members (Districts 1–5)** + a **separately-elected Mayor**. The **Mayor votes only in
limited cases** (a council **tie**, ordinances affecting the mayor's own powers, and
appointment/removal of the City Manager) — NOT on ordinary motions. Day-to-day administration
runs through an appointed **City Manager** (Matt Dahl). → **On ordinary motions max tally = 5
(mayor does not cast); the mayor's vote surfaces only as a tie-break, so an absolute max = 6.**
Confirmed against a real roll call (§2) **and** the city's own "Form of Government" statement.
**Official site:** `https://www.midvale.utah.gov/` — **Revize CMS** ("revize" throughout page
chrome; a `<base href="https://www.midvale.utah.gov/">` is set). **`midvalecity.org` 301-redirects
to `midvale.utah.gov`.** Browser UA fetches return **200** (no bot-403 wall observed, unlike
Taylorsville); a browser UA is still used on every fetch out of caution.

> ⚠ **URL-encode every document URL** — paths contain spaces (`%20`) and a literal `&` (`%26`),
> e.g. `Document%20Center/Agendas%20%26%20Minutes/...`. A raw curl of the un-encoded path returns
> curl code 000. Docs also carry an optional `?t=<timestamp>` cache-buster (droppable).

---

## 1. Council meeting minutes

### Portal — Revize "Document Center" (single flat landing page, all years)
- **Host:** `https://www.midvale.utah.gov`
- **Agendas & Minutes landing (Recorder's Office):**
  `https://www.midvale.utah.gov/government/departments/recorder_s_office/agendas___minutes.php`
  This is **one large (~818 KB) flat HTML page** that lists **every** council document link for
  **2010 → 2026** in-line (Agendas | Minutes | Packets | Presentations). No JS tree to walk —
  **harvest the `<a href>` links directly.** (Council docs are prefixed **`CC`** = City Council.)
- **Minutes document URL pattern (Revize Document Center file tree):**
  ```
  https://www.midvale.utah.gov/Document Center/Agendas & Minutes/Recorders Office/<YEAR>/Minutes/CC Minutes <M-D-YYYY>.pdf
  ```
  URL-encoded, e.g. (VERIFIED, 200, 3.5 MB):
  ```
  https://www.midvale.utah.gov/Document%20Center/Agendas%20%26%20Minutes/Recorders%20Office/2025/Minutes/CC%20Minutes%2012-2-2025.pdf
  ```
  Filename dates are **inconsistently formatted** (`CC Minutes 12-2-2025.pdf`, `CC Minutes
  10-17-2023001.pdf`, older `CC Minutes 10102017.pdf`, occasional `.doc/.docx` in 2017) — **do
  not guess filenames; harvest the labeled links.** A handful of recent docs also sit at a
  **flat** path `Document Center/Agendas & Minutes/CC Minutes 6-3-2025.pdf` (no year folder).
- **Coverage (council minutes link counts by year on the landing page):** 2017≈63, 2018≈58,
  2019≈47, **2020≈93**, 2021≈46, 2022≈52, 2023 (largest), 2024≈102, 2025≈96, 2026≈52 (+ a few
  stray 2010–2016). → **2020 floor is fully covered on the city portal itself** (no PMN needed).

### Format — born-digital text PDF (CONFIRMED clean)
`pdftotext -layout` on **2025-12-02** council minutes yields clean, selectable text with proper
names intact (`Mayor Dustin Gettel`, `Council Member Denece Mikolash`). **Not OCR-garbled.**
(Watch for occasional scanned inserts in older/mid years, but the modern record is text.)

### Meeting cadence — **Tuesday (1st & 3rd)**
- **City Council: 1st & 3rd Tuesdays**, **6:00 p.m. Regular Meeting** in Council Chambers,
  7505 South Holden Street (a Work/Study session often precedes). Verified: 2025-12-02,
  2025-11-18, 2025-10-07, 2025-06-03 are all **Tuesdays**. Occasional special meetings +
  a December "Legislative Breakfast" appear as extra dated docs.

### Roll-call votes in minutes — CONFIRMED PRESENT, **NAMED roll call (high quality)**
Unlike Taylorsville/South Jordan narrative-tally, **Midvale prints a per-member Aye/Nay roll
call**. Verified in **2025-12-02** minutes:
> *"MOTION: Council Member Paul Glover MOVED to Approve the Consent Agenda. The motion was
> SECONDED by Council Member Bonnie Billings. Mayor Gettel called for … a roll call vote. The
> voting was as follows: Council Member Bryant Brown — Aye; Council Member Denece Mikolash —
> Aye; Council Member Bonnie Billings — Aye; Council Member Paul Glover — Aye. The motion
> passed unanimously."* (Council Member Heidi Robinson excused → 4 present, 4 Aye.)

- **Grammar:** `MOTION: Council Member X MOVED to …` / `SECONDED by Council Member Y` / a named
  `<Member> — Aye|Nay` block / `The motion passed unanimously` (or a tally on dissent).
- **The Mayor presides and "called for a roll call vote" but is ABSENT from the tally** on
  ordinary motions → **mayor non-voting except on ties (max ordinary tally = 5).** Ordinances
  and consent-agenda items both take named roll calls.

---

## 2. Council structure — 5 districts + Mayor (six-member form; mayor votes only on ties)

- **5 council districts (Districts 1–5)**, one member each; **Mayor elected citywide.** No
  at-large seats. **4-year overlapping non-partisan terms**, elected in **odd years**.
- **Current roster** (from `city_council.php` + the 2025-12-02 minutes header + the official
  GIS layer):

  | Seat | Member | Email |
  |---|---|---|
  | Mayor (citywide) | **Dustin Gettel** | (executive; votes only on ties/specified matters) |
  | District 1 | **Bonnie Billings** | Bbillings@midvaleut.gov |
  | District 2 | **Paul Glover** | pglover@midvaleut.gov |
  | District 3 | **Heidi Robinson** | Hrobinson@midvaleut.gov |
  | District 4 | **Bryant Brown** | Bbrown@midvaleut.gov |
  | District 5 | **Denece Mikolash** | dmikolash@midvaleut.gov |

- **⚠ MAYOR-VOTE DETERMINATION (verified two ways):** (a) The city's own **"Form of Government"**
  text: *"a six-member council, consisting of five council members and a mayor. The mayor's role
  includes casting a vote in cases where the council reaches a tie vote and in matters concerning
  ordinances that impact the mayor's powers … and … appointment or removal of a city manager."*
  (b) In the **2025-12-02 roll call**, Mayor Gettel **presides / calls the vote but casts none**;
  only the council members appear in the tally. → **Build with max ordinary tally = 5, Mayor
  non-voting; treat a mayoral tie-break as a special `vote.note`-style row (Park-City pattern),
  not a routine 6th vote.** This differs from Millcreek (mayor votes on every roll, tally 5 incl.
  mayor) and from Taylorsville (mayor never votes at all).
- **Term stagger (from the elections page + archive):** **2025 = Mayor + District 4 + District
  5**; therefore **Districts 1/2/3 = the 2023 (and 2019) cycle**; **Mayor/D4/D5 = the 2021/2025
  cycle.**
- Council page: `https://www.midvale.utah.gov/government/city_council.php`
  (a "Council District Map" is linked; member emails are `<initial><surname>@midvaleut.gov`).
- **RDA:** Midvale has a **Redevelopment Agency** (`.../redevelopment_agency/`); the Council
  convenes as the RDA board (in-record) — expect `body=RDA` motions in the same minutes stream
  (no separate RDA portal confirmed this recon; verify during acquisition).

---

## 3. Planning Commission — Midvale has its OWN **Planning & Zoning Commission**

- **Own P&Z Commission**, records on the SAME Revize Document Center, surfaced on:
  `https://www.midvale.utah.gov/government/departments/community_development/planning_and_zoning/planning___zoning_commission.php`
  (this page itself is the flat listing — ~829 KB — of all PC agendas/minutes).
- **Doc pattern (older/full-path form, VERIFIED):**
  ```
  https://www.midvale.utah.gov/Document Center/Agendas & Minutes/Planning & Zoning Commission/<YEAR>/Minutes/<M.D.YY>_Minutes_APPROVED.pdf
  ```
  e.g. `.../2025/Minutes/3.12.25_Minutes_APPROVED_w_votes.pdf` (200, 513 KB, born-digital text).
  ⚠ **Current-year (2026) PC links appear as BARE relative filenames** (`6.24.26_Minutes_Approved.pdf`)
  because of the page's `<base href>` — those 404 as-written; resolve them to the full
  `Document Center/…/Planning & Zoning Commission/2026/Minutes/…` path during acquisition.
- **Coverage:** year folders **2014 → 2026** (well before the 2020 floor).
- **Cadence:** **2nd & 4th Wednesdays**, 6:00 p.m., Council Chambers (verified: 3.12.25 &
  10.22.25 are Wednesdays; page states "2nd and 4th Wednesdays").
- **Votes/recommendations — CONFIRMED PRESENT** (2025-03-12): named commissioners, `MOTION:
  Commissioner X MOVED … SECONDED by … voice vote / passed unanimously`, plus **named tabular
  votes** for contested items (e.g. chair-election ballot table `Voting Commissioner | Vote`).
  Commissioners named (Erickson, Anderson, Liedtke, Tippetts, Snow, …). **Advisory
  recommendations to Council** — capture PC→Council recommendation language + land-use case IDs.

---

## 4. Public comments — inline speaker notes only (no standalone published archive)

**Verdict: SUBMIT-ONLY / inline-in-minutes (auditor's call — do NOT build `all_comments_clean.csv`
without a positive source).** Council minutes carry a **`II. PUBLIC COMMENTS`** section that
**paraphrases in-person speakers** (verified 2025-12-02) plus public-hearing speaker notes —
these are **meeting-record speaker notes, NOT city-published written comments** → a labeled
`minutes_speaker_log.csv` if kept, never `all_comments_clean.csv`. No dedicated eComment /
correspondence / Open City Hall archive surfaced. The city runs **`EngageMidvale.com`** for
engagement (not a comment archive) and takes comment **in-person + via livestream**. Record the
honest SUBMIT-ONLY verdict in `public_comments/AVAILABILITY.md`; re-check council/PC **packets**
for bundled written correspondence before declaring a hard zero.

---

## 5. Elections — Salt Lake County (canonical CSV already covers Midvale)

- **Run by:** Salt Lake County Clerk. City page:
  `https://www.midvale.utah.gov/government/departments/recorder_s_office/elections/index.php`
  (states: council elected to **four-year overlapping terms**, **odd-year** municipal elections,
  2025 up = **Mayor / District 4 / District 5**). Campaign-finance disclosures + declared-candidate
  lists live under the Recorder's Office.
- **Canonical archive already has Midvale:**
  `/Users/tysonwelsh/civic-data/salt_lake_county/elections/slco_municipal_results_long.csv`
  — **3,422 Midvale rows**; **filter `contest` LIKE `%MIDVALE%`** (labels vary:
  `MIDVALE CITY COUNCIL DIST #1`, `MIDVALE CITY COUNCIL DISTRICT 1`, `Midvale City Council 1`,
  `MIDVALE CITY CNCL DIST 4`, `MIDVALE CITY MAYOR`, …). District-based (1–5) + Mayor.
- **Years present:** 2007, 2009, 2011, 2013, 2015, 2017, **[2019 MISSING]**, 2021, 2023, 2025.
- **⚠ 2019 GAP:** no 2019 Midvale rows — the 2019 general should carry **Districts 1/2/3** (same
  odd-cycle as 2023). This is the **same failure mode** seen for Taylorsville/South Jordan/
  Millcreek 2019 (numbered-sheet layout dropped the city string) → **re-parse the raw 2019 SL
  County SOVC** for Midvale D1/D2/D3.
- **Also present:** a 2023 `MIDVALE CITY REVISED RESOLUTION CALLING BOND ELECTION NO. 2023-R-32`
  (a bond question, not a seat) — keep separate from candidate races.
- Winners are UPPER-CASE with occasional suffixes — normalize before joining to the minutes
  roster (Billings D1, Glover D2, Robinson D3, Brown D4, Mikolash D5, Gettel Mayor).

---

## 6. GIS — **official Midvale council-district FeatureServer EXISTS**

- **Council districts (OFFICIAL, hosted by Midvale's ArcGIS org `midvale.maps.arcgis.com`):**
  ```
  https://services6.arcgis.com/8xmMYBLanDLIUCUt/arcgis/rest/services/City_Council_Districts_view/FeatureServer/0
  ```
  Verified: **5 polygon features**, fields `Counc_Dist`, `Name` (`District 1`…`District 5`),
  `CITY`, `F_Name`/`L_Name`. Item id `20090ec1c2cd4eb5905096dd1745b6e1` (owner `matthilderman9`);
  also a Web Map `47da67ee…`, a viewer app, and a **City Council District Map PDF**
  (`de996145…`). → **Preferred district-polygon source (no precinct-derivation needed for
  current boundaries).** ⚠ The layer's **member-name attributes are STALE** (District 5 is
  labeled "Dustin Gettel", now the Mayor) — trust the **geometry / `Counc_Dist`**, not the name
  fields; take the roster from §2.
- **Midvale open-data hub:** `https://midvale-city-gis-department-midvale.opendata.arcgis.com/`
  — its `data.json` enumerates **19 datasets** incl. **City Council Districts** and **Land Use
  Zoning Districts & Overlays**; sibling geohubs for Planning & Zoning, Engineering, Parks.
- **Voting precincts:** **no Midvale-specific precinct layer found.** Use **UGRC / SL County**
  precincts (**UGRC CountyID = 18**, VistaBallotAreas) and the existing shared
  `~/Desktop/slco-election-archive/geo/slco_precincts_current.geojson` (same fallback used for
  Taylorsville) to map SOVC precinct rows → districts for **pre-redistricting** questions.
- **City outline:** UGRC Municipal Boundaries `NAME='MIDVALE'`.

---

## Retrieval plan (recommended order)

1. **Council minutes 2020→present:** harvest `CC Minutes` links from the flat
   `.../recorder_s_office/agendas___minutes.php` page → curl each PDF **(browser UA + URL-encode
   spaces/`&`)** → `meeting_minutes/raw/<year>/`. 1st & 3rd Tuesday; text-layer → markdown.
2. **Vote extraction (council):** parse the **named** `MOTION/SECONDED/<Member> — Aye|Nay/passed
   unanimously` grammar; attendance from the `Roll Call`/`Excused` header; **max tally 5, Mayor
   non-voting** (flag any mayoral tie-break as a special row). Capture RDA (`body=RDA`) motions.
3. **Planning Commission 2020→present:** harvest from the P&Z page (resolve 2026 bare-relative
   links to full Document Center paths); named-commissioner motion/voice/tabular votes; PC→Council
   recommendation language + land-use case IDs.
4. **Comments:** record the **SUBMIT-ONLY** verdict (`AVAILABILITY.md`); optional
   `minutes_speaker_log.csv` from the `II. PUBLIC COMMENTS` sections; check packets for written
   correspondence before a hard zero.
5. **Elections:** reuse `slco_municipal_results_long.csv` (`contest LIKE '%MIDVALE%'`); **re-parse
   the raw 2019 SOVC** for Districts 1/2/3; keep the 2023 bond question separate.
6. **Geo:** use the **official `City_Council_Districts_view` FeatureServer** for current district
   polygons (ignore its stale name attributes) → address→district tool; UGRC CountyID 18 +
   slco precinct geojson for pre-redistricting vintages.

---

## Risks / blockers

- **URL encoding (LOW):** all Document Center paths have spaces + a literal `&` — must encode
  (`%20`, `%26`) or curl returns code 000. Optional `?t=<token>` cache-buster.
- **2026 PC links are bare relative filenames (LOW):** a `<base href>` quirk makes current-year
  PC minutes 404 as-written — resolve to the full `.../Planning & Zoning Commission/2026/Minutes/`
  path (prior years already carry the full path).
- **Mayor-vote form (STRUCTURAL, resolved):** six-member form → **Mayor votes only on ties /
  mayoral-power ordinances / city-manager hire-fire; max ordinary tally = 5.** Confirmed by the
  city's own statement + a real roll call. Model a tie-break as a special note, not a routine
  6th vote.
- **No contested council vote in the single sample (LOW):** the verified motions were unanimous;
  named roll call is confirmed, but pull a contested rezone/budget meeting to lock the **Nay/
  tally** wording before bulk extraction.
- **2019 election gap (D1/D2/D3):** absent from the shared archive — raw-2019-SOVC re-parse
  needed (same failure mode as other SL County cities).
- **Stale GIS attributes (LOW):** the council-district FeatureServer's member-name fields are
  out of date (District 5 = "Dustin Gettel") — geometry is fine, take names from the council page.
- **No bot-403 observed:** browser UA returns 200 across the site (unlike Taylorsville's Akamai
  wall); keep the browser UA anyway.

---

## Key URLs (quick index)

| What | URL |
|---|---|
| City site (Revize; midvalecity.org → here) | https://www.midvale.utah.gov/ |
| Council agendas & minutes (flat, all years) | https://www.midvale.utah.gov/government/departments/recorder_s_office/agendas___minutes.php |
| Council minutes doc pattern | https://www.midvale.utah.gov/Document%20Center/Agendas%20%26%20Minutes/Recorders%20Office/&lt;YEAR&gt;/Minutes/CC%20Minutes%20&lt;M-D-YYYY&gt;.pdf |
| Council minutes sample (verified) | https://www.midvale.utah.gov/Document%20Center/Agendas%20%26%20Minutes/Recorders%20Office/2025/Minutes/CC%20Minutes%2012-2-2025.pdf |
| City Council page (roster) | https://www.midvale.utah.gov/government/city_council.php |
| Mayor page | https://www.midvale.utah.gov/government/mayor.php |
| Planning & Zoning Commission (agendas/minutes) | https://www.midvale.utah.gov/government/departments/community_development/planning_and_zoning/planning___zoning_commission.php |
| PC minutes sample (verified) | https://www.midvale.utah.gov/Document%20Center/Agendas%20%26%20Minutes/Planning%20%26%20Zoning%20Commission/2025/Minutes/3.12.25_Minutes_APPROVED_w_votes.pdf |
| Elections (city) | https://www.midvale.utah.gov/government/departments/recorder_s_office/elections/index.php |
| Public notices | https://www.midvale.utah.gov/government/departments/recorder_s_office/public_notices.php |
| Campaign-finance disclosures | https://www.midvale.utah.gov/government/departments/recorder_s_office/campaign_financial_disclosures.php |
| GIS maps landing | https://www.midvale.utah.gov/doing_business/geographical_information_system_(gis)_maps.php |
| Council-district FeatureServer (OFFICIAL) | https://services6.arcgis.com/8xmMYBLanDLIUCUt/arcgis/rest/services/City_Council_Districts_view/FeatureServer/0 |
| Midvale open-data hub (data.json → 19 datasets) | https://midvale-city-gis-department-midvale.opendata.arcgis.com/ |
| Canonical election CSV (Midvale present) | /Users/tysonwelsh/civic-data/salt_lake_county/elections/slco_municipal_results_long.csv (filter contest LIKE '%MIDVALE%'; **2019 GAP**) |
| Precinct geometry (for pre-redistricting) | ~/Desktop/slco-election-archive/geo/slco_precincts_current.geojson (UGRC CountyID 18) |

```json
{"vendor":"Revize CMS (Document Center file tree)","minutes_landing_url":"https://www.midvale.utah.gov/government/departments/recorder_s_office/agendas___minutes.php","minutes_url_pattern":"https://www.midvale.utah.gov/Document Center/Agendas & Minutes/Recorders Office/<YEAR>/Minutes/CC Minutes <M-D-YYYY>.pdf  (URL-encode spaces %20 and & %26; optional ?t=<token>; a few recent docs at flat /Agendas & Minutes/ no year folder; filename date formats inconsistent - harvest links)","coverage_years":"2010-2026 (dense 2017+; 2020 floor fully covered on city portal)","format":"born-digital text PDF (pdftotext clean; watch occasional older scans)","votes_in_minutes":"YES - NAMED roll call (per-member Aye/Nay), MOTION/SECONDED grammar; confirmed 2025-12-02 (Glover moved consent agenda, seconded Billings, Brown/Mikolash/Billings/Glover all Aye, Robinson excused, passed unanimously)","pc_portal":"own Planning & Zoning Commission on same Revize Document Center; page https://www.midvale.utah.gov/government/departments/community_development/planning_and_zoning/planning___zoning_commission.php ; doc pattern .../Planning & Zoning Commission/<YEAR>/Minutes/<M.D.YY>_Minutes_APPROVED.pdf (2026 links are bare-relative - resolve to full path)","pc_coverage":"2014-2026; votes CONFIRMED (named commissioners, voice/tabular votes, 2025-03-12)","council_weekday":"Tuesday (1st & 3rd, 6:00pm regular; work/study precedes)","num_districts":5,"at_large_seats":0,"mayor_votes":"only on ties, mayoral-power ordinances, and city-manager appointment/removal (NOT ordinary motions)","max_tally":"5 ordinary (mayor non-voting); 6 absolute when mayor breaks a tie","current_members":["Mayor Dustin Gettel (executive; votes only on ties)","D1 Bonnie Billings","D2 Paul Glover","D3 Heidi Robinson","D4 Bryant Brown","D5 Denece Mikolash"],"comments_published":"NO standalone published archive - inline 'II. PUBLIC COMMENTS' speaker notes in minutes; SUBMIT-ONLY/in-person + EngageMidvale.com engagement; do not build all_comments_clean.csv without a positive source","gis_source":"OFFICIAL Midvale council-district FeatureServer https://services6.arcgis.com/8xmMYBLanDLIUCUt/arcgis/rest/services/City_Council_Districts_view/FeatureServer/0 (5 district polygons; stale member-name attrs - use geometry/Counc_Dist only); Midvale open-data hub data.json = 19 datasets incl Land Use Zoning; no Midvale precinct layer - use UGRC CountyID 18 + slco-election-archive precinct geojson","blockers":["URL-encode spaces %20 & %26 in all doc paths (else curl 000)","2026 PC links are bare-relative <base href> quirk - resolve to full Document Center path","mayor votes only on ties - model as special note, not routine 6th vote; pull a contested meeting to confirm Nay wording","2019 Midvale election rows MISSING from shared archive (D1/D2/D3) - re-parse raw 2019 SOVC","GIS district layer member-name attributes stale (D5 labeled Gettel) - trust geometry not names","2023 bond question (2023-R-32) present in election CSV - keep separate from seat races"],"confidence_notes":"CONFIRMED: vendor(Revize), site+redirect, council minutes pattern+sample+named votes(2025-12-02 PDF), council Tuesday cadence, 5 districts + roster + emails, six-member mayor-vote form (city 'Form of Government' text + roll call), PC own commission + Wednesday cadence + votes(2025-03-12 PDF), election CSV has Midvale(3422 rows)+2019 gap, official council-district FeatureServer(5 polygons). GUESS/UNVERIFIED: exact term-stagger years pre-2021, RDA in-record modeling, contested/dissent vote wording, whether any mid-year minutes are scanned."}
```
