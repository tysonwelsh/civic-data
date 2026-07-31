# Bluffdale City, Utah — Civic Data Recon

**City:** Bluffdale City, **primarily Salt Lake County** (small southern/western portion in
**Utah County** — largely Camp Williams / undeveloped, essentially unpopulated), Utah (~17k pop.)
**Recon date:** 2026-07-11
**Scope of interest:** 2020–present (floor **2020**; city **incorporated 1978**, so full modern
history exists — 2020 is a normal floor, not an incorporation edge).
**Form of government:** **Mayor–Council, six-member form.** Six elected officials: a **Mayor**
elected citywide + **5 Council Members, ALL at-large** (no districts). The **Mayor presides**
over council meetings (calls to order, gives reports) **but does NOT vote on ordinary motions**
— **CONFIRMED against real roll calls** (see §2 & §4): every `Vote on Motion:` tally names the
**5 Council Members only**; Mayor Hall never appears in a tally, even on contested 3-to-2 / 4-to-1
votes. → **Max council tally = 5, Mayor non-voting** (statutory tie-break possible but not
observed — would be a separate line, not a routine tally entry).
**Official site:** `https://www.bluffdale.gov/` — **CivicPlus / CivicEngage Central** CMS
(`/AgendaCenter/`, `/DocumentCenter/`, `ViewFile` doc pattern). (Older docs reference the legacy
`www.bluffdale.com` domain; `.gov` is canonical and live.) ✅ **Site does NOT bot-block** — both
`curl` (browser UA) and WebFetch succeeded; no 403 seen (unlike Taylorsville). Use the browser UA
anyway as a courtesy.

---

## 1. Council meeting minutes

### Portal — CivicPlus / CivicEngage AgendaCenter (single portal, all bodies)
- **Host:** `https://www.bluffdale.gov`
- **City Council landing (info):** `https://www.bluffdale.gov/333/City-Council`
- **AgendaCenter (all bodies):** `https://www.bluffdale.gov/AgendaCenter`
- **City Council agendas & minutes tab:** `https://www.bluffdale.gov/AgendaCenter/City-Council-2`
  (the default tab shows **current year only**; back-years reached via the Search endpoint below
  or the DocumentCenter — "Previous years' agendas and minutes can be found in the Document Center").
- **⭐ Enumeration endpoint (the reliable one — use this, don't scrape the JS tab):**
  ```
  https://www.bluffdale.gov/AgendaCenter/Search/?CIDs=<CID>%2C&startDate=MM%2FDD%2FYYYY&endDate=MM%2FDD%2FYYYY&term=&dateRange=&dateSelector=
  ```
  **CID=2 = City Council**, **CID=3 = Planning Commission** (there are other CIDs for other
  bodies). Returns every Agenda + Minutes link for the date window. Verified live: a full 2025
  City-Council year (23 minutes docs, Jan 8 2025 → Dec 10 2025) came straight from `CIDs=2%2C`.
- **Minutes document URL pattern (CivicEngage `ViewFile`):**
  ```
  https://www.bluffdale.gov/AgendaCenter/ViewFile/Minutes/_<MMDDYYYY>-<internalId>
  ```
  Agendas are the parallel `.../ViewFile/Agenda/_<MMDDYYYY>-<internalId>`. **Each meeting date has
  BOTH an Agenda and a Minutes item under the same date** — take the `Minutes/` one for motion
  prose. The `<internalId>` is NOT derivable — **harvest the labeled `<a>` links from the Search
  endpoint, don't guess ids.**
- **Coverage on-portal:** City Council minutes run **~2013 → 2026** in the AgendaCenter (older in
  DocumentCenter). → **2020 floor fully covered on the city portal** (no PMN dependency required).
- **PMN mirror / fallback:** every meeting is also noticed on **Utah Public Notice** (`pmn.utah.gov`
  / `utah.gov/pmn`) — e.g. council agendas at `utah.gov/pmn/sitemap/notice/<id>.html`, PDFs at
  `utah.gov/pmn/files/<fileId>.pdf`. Use PMN if the CMS is missing a date.

### Format — ⚠ SCANNED IMAGE PDFs (Council = NO text layer; PC = has OCR text layer)
- **Council minutes** are **ScanSnap/RICOH image scans** (`Producer: PFUPDF Engine`) with **NO
  embedded text layer** — `pdftotext` yields ~20 chars on a 21-page doc. → **must OCR / read
  visually** (the Read tool renders them cleanly; pages are crisp, legible black-on-white — good
  OCR candidates via `ocrmypdf` or vision). Sample verified: **2025-09-24** (21 pp) and **2025-08-13**.
- **Planning Commission minutes** are also Fujitsu scans **BUT carry an embedded OCR text layer**
  (`Producer: PFU PDF Library`, ~30k chars on a 13-page doc) → `pdftotext -layout` works directly.
  Sample verified: **2025-05-07**. (Asymmetry is real — build the extractor to OCR council, and to
  trust the PC text layer but spot-check for OCR typos, e.g. "Griffls"/"Griffis", "Blnffdale".)
- Saved confirmation PDFs → `meeting_minutes/raw/`: `cc_20250924_min.pdf`, `cc_20250813_min.pdf`,
  `pc_20250507_min.pdf`.

### Meeting cadence — **Wednesday**
- **City Council: 2nd & 4th Wednesday**, **6:00 p.m.** (optional **5:00 p.m. Work Session as
  needed**), Council Chambers, Bluffdale City Hall, 2222 West 14400 South. (Occasional extra/
  special Wednesdays appear — e.g. 2026 shows a Jan 5 & Jan 9 in addition to the 2nd/4th pattern.)
- **Planning Commission: 1st & 3rd Wednesday**, 6:00 p.m., same chambers (see §3).

### Roll-call votes in minutes — ✅ CONFIRMED PRESENT, per-member NAMED (Yes/No), incl. contested
Bluffdale prints **full named roll-call tallies** (NOT South-Jordan-style narrative-only). Verbatim
from **2025-09-24 council minutes** (`cc_20250924_min.pdf`, saved to `raw/`):

- **Present (roll):** *"City Council: Natalie Hall, Mayor; Wendy Aston; Steve Austin; Traci Crockett;
  Alan Lord; Greg Wilding."* — "Mayor Hall called the meeting to order at 6:00 PM. All members of
  the City Council were present."
- **Unanimous named (Res. 2025-80, C-PACE):** *"Council Member Austin moved to APPROVE Resolution
  2025-80… Council Member Wilding seconded… **Vote on Motion: Council Member Aston-Yes, Council
  Member Wilding-Yes, Council Member Crockett-Yes, Council Member Lord-Yes, Council Member
  Austin-Yes. The motion passed unanimously.**"* → **5 votes; Mayor Hall NOT in tally.**
- **⭐ CONTESTED, named (Res. 2025-82 amendment):** *"**Vote on Motion: Council Member Wilding-No,
  Council Member Crockett-No, Council Member Lord-Yes, Council Member Austin-Yes, Council Member
  Aston-No. The motion failed 3-to-2.**"* → dissent format LOCKED; **5 members voting, Mayor absent
  from the tally on a contested vote.**
- **Contested, named (Res. 2025-82 table):** *"Vote on Motion: Council Member Crockett-Yes, Council
  Member Lord-No, Council Member Austin-Yes, Council Member Aston-Yes, Council Member Wilding-Yes.
  The motion passed 4-to-1."*
- **Also present:** a lighter **"passed with the unanimous consent of the Council"** phrasing on
  routine items (minutes/agenda approval, tabling) with mover+seconder named but no per-member list
  — so the extractor must handle **both** the named-tally form and the unanimous-consent form.

→ **Vote-parser spec:** max tally **5**, **Mayor non-voting** (Mayor = presider/mover-of-nothing;
never a voter). Named `Council Member <Name>-Yes/No` rows for every recorded-vote motion; a `Chair`
label does **not** appear for council (the Mayor presides, not a council chair) — every voter is a
`Council Member`. Attendance from the `Present:` block.

---

## 2. Council structure — Mayor + 5 at-large (Mayor does NOT vote; max tally 5)

- **6 elected officials:** Mayor (citywide) + **5 Council Members, all elected AT-LARGE** — **no
  districts, no mixed at-large/district**. 4-year **staggered, non-partisan** terms.
- **Election stagger:** **Mayor + 2 council seats** on the **2017 / 2021 / 2025** cycle; **3 council
  seats** on the **2019 / 2023** cycle. (2025 elected the Mayor + 2 council seats — confirmed by the
  city's 2025 election page.)
- **Current roster** (city "Mayor & City Council" page + the 2025-09-24 minutes header + 2025
  election winners):

  | Seat | Member | Term | Notes |
  |---|---|---|---|
  | **Mayor** (citywide, presides, **non-voting**) | **Natalie Hall** | Jan 2026 – Dec 2029 | incumbent Mayor in 2025, **re-elected 2025** (def. Connie Pavlakis) |
  | Council At-Large | **Wendy Aston** | Jan 2026 – Dec 2029 | re-elected 2025 |
  | Council At-Large | **Mackey Smith** | Jan 2026 – Dec 2029 | **new 2025** (seat prev. Traci Crockett) |
  | Council At-Large | **Steve Austin** | Jan 2024 – Dec 2027 | |
  | Council At-Large | **Alan Lord** | Jan 2024 – Dec 2027 | |
  | Council At-Large | **Greg Wilding** | Jan 2024 – Dec 2027 | |

- **⚠ Roster drift to encode:** the **2020–2025 voting record** names **Traci Crockett** (at-large,
  through Dec 2025) — she votes in the confirmed 2025 minutes; **Mackey Smith replaces her Jan 2026**.
  Build the roster with the mid-record change (Crockett → Smith, Jan 2026) and pull earlier
  members (pre-2024) from the 2020–2023 minutes headers during acquisition.
- **⭐ MAYOR-VOTE DETERMINATION (verified from real roll calls, not guessed):** **Mayor does NOT
  vote.** In the 2025-09-24 minutes the Mayor **presides** (calls to order, reports, runs the
  agenda) yet is **absent from every `Vote on Motion:` tally**, including the **contested 3-to-2 and
  4-to-1** votes — only the 5 Council Members are tallied. This is Utah's **six-member (mayor-council)
  form**: Mayor presides and may hold a statutory **tie-break**, but casts no routine vote. → **Build
  with max council tally = 5, Mayor non-voting** (matches South Jordan/Taylorsville denominator; the
  difference is Bluffdale prints **full named** roll calls, so per-member attribution is direct).
- Council info page: `https://www.bluffdale.gov/333/City-Council` and `.../333/Mayor-City-Council`.

---

## 3. Planning Commission — Bluffdale has its OWN PC (same portal)

- **Own Planning Commission**, minutes on the SAME CivicEngage AgendaCenter (**CID=3**):
  - Tab: `https://www.bluffdale.gov/AgendaCenter/Planning-Commission-3`
  - Enumerate: `.../AgendaCenter/Search/?CIDs=3%2C&startDate=…&endDate=…`
  - Doc pattern: `.../AgendaCenter/ViewFile/Minutes/_<MMDDYYYY>-<id>` (same as council).
- **Cadence:** **1st & 3rd Wednesday**, **6:00 p.m.**, Bluffdale City Hall.
- **Coverage:** 2025 shows 14 PC minutes docs (Jan 15 → Dec 3 2025); back-catalog runs earlier in
  AgendaCenter/DocumentCenter → **2020 floor covered.**
- **Votes/recommendations — ✅ CONFIRMED (text-verified on `pc_20250507_min.pdf`, 2025-05-07):**
  named per-commissioner roll calls **and** explicit council-recommendation language —
  *"Commissioner Griffis moved to APPROVE the proposed Kenna Lane Lot 105 Plat… seconded by
  Commissioner Swanson. **Vote on motion: Ulises Flynn-Yes, Eric Swanson-Yes, Kori Luker-Yes, Tina
  Griffis-Yes, Chair Cragun-Yes. The motion passed unanimously.**"* and (legislative item)
  *"Commissioner Griffis moved to **forward a POSITIVE recommendation to the City Council**…"*.
  → PC extractor: named tallies (a **`Chair <Name>`** DOES appear on PC — Chair Cragun votes; PC has
  a commissioner-chair, unlike council) + PC→Council `POSITIVE/NEGATIVE recommendation` referral
  language keyed to `Application <YYYY-NN>` case numbers.
- **PC commissioners (May 2025 sample):** Chair **Cragun**, **Erik/Eric Swanson**, **Kori Luker**,
  **Tina Griffis**, **Ulises Flynn** (spot-check OCR: "Griffls"→Griffis).

---

## 4. Public comments — SUBMIT-ONLY (no published written-comment archive) — LIKELY HONEST-EMPTY

- Public comment is taken **in-person at meetings** and by **email to
  `councilmeetingcomment@bluffdale.gov` by 4:00 p.m. the day of the meeting** — and the agenda
  states **emailed comments are submitted to the Council but WILL NOT be read at the meeting** and
  are **not** posted. Minutes **paraphrase in-meeting speakers inline** (e.g. 2025-09-24: *"Rob
  Hughes reported that he lives on Pastoral Way…"*) — these are **meeting-record speaker notes, NOT
  a genuine written-comment archive** → a labeled `minutes_speaker_log.csv`, never
  `all_comments_clean.csv`.
- **No dedicated comments page / eComment / Open City Hall / "correspondence received" archive**
  surfaced. → **most likely a legitimate honest zero (submit-only)** — but **auditor's call**: before
  declaring, grep council & PC **agenda packets** (in AgendaCenter/DocumentCenter) for bundled
  written correspondence.

---

## 5. Elections — Salt Lake County administers; canonical archive already covers Bluffdale

- **Administered by the Salt Lake County Clerk.** Live results:
  `https://electionresults.utah.gov/` (Bluffdale contests appear under **salt-lake-county-ut**,
  e.g. general11042025 "bluffdale city council at-large"). City pages:
  `https://www.bluffdale.gov/498/Elections`, `.../888/2025-Election`, `.../776/2023-Election`.
- **✅ Canonical shared file already has Bluffdale** —
  `/Users/tysonwelsh/civic-data/salt_lake_county/elections/slco_municipal_results_long.csv`.
  **Filter on the `contest`/`sheet` text `%BLUFFDALE%`.** Contest label is **`BLUFFDALE CITY COUNCIL
  AT LARGE`** (+ Mayor rows in mayoral years). Coverage present (row counts):
  **2007, 2009, 2011, 2013, 2015, 2017, 2021, 2023, 2025.**
  - **⚠ 2019 GAP — Bluffdale has 0 rows for 2019** in the canonical CSV (same failure mode seen for
    South Jordan / Millcreek / Taylorsville 2019 — numbered-sheet layout dropped the city string).
    2019 was a **3-council-seat** year → **re-parse the raw 2019 SLCo SOVC** for the Bluffdale
    at-large council races.
  - Winners are UPPER-CASE — normalize before joining to the minutes roster (e.g. `NATALIE HALL`→
    Mayor, `WENDY ASTON`, `STEVE AUSTIN`, `ALAN LORD`, `GREG WILDING`, `TRACI CROCKETT`,
    `MACKEY SMITH`).
- **⭐ TWO-COUNTY QUESTION (Bluffdale straddles Salt Lake + Utah counties):** the **residential/
  populated** part of Bluffdale is in **Salt Lake County**; the **Utah County portion is Camp
  Williams (Utah NG reservation) + undeveloped land — essentially NO registered residents.** →
  **Salt Lake County administers and reports ALL Bluffdale municipal results**; the SLCo SOVC (the
  canonical CSV) is the complete record. **Unlike Draper** (whose Utah-County SunCrest neighborhood
  is populated and reports separately in Utah County), Bluffdale has **no meaningful Utah-County
  voter bloc**, so **no Bluffdale results are expected only in Utah County records.** **Low-risk
  caveat to verify during acquisition:** scan a Utah County SOVC (2023/2025) for any `BLUFFDALE` rows
  (expected: zero or negligible) to confirm before declaring the SLCo file complete.

---

## 6. GIS — at-large city (NO council districts to map); municipal boundary + precincts, TWO counties

- **Bluffdale is entirely at-large → there are NO council-district polygons to build.**
  `address → representative` is **trivial**: any Bluffdale address maps to the **same** Mayor + 5
  at-large Council Members. The only geometry needed is the **city boundary** (for
  inside/outside-city) and, if desired, **voting precincts** (for precinct-level election joins).
- **City boundary:** UGRC **Utah Municipal Boundaries**
  `services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/UtahMunicipalBoundaries/FeatureServer/0`,
  `NAME='BLUFFDALE'` — a single polygon spanning **both counties**.
- **Precincts:** UGRC **VistaBallotAreas** (all 29 counties)
  `services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/VistaBallotAreas/FeatureServer/0`.
  **⚠ Pull BOTH `CountyID = 18` (Salt Lake) AND `CountyID = 25` (Utah)** to capture the full
  municipal extent — though in practice only the CountyID-18 precincts carry Bluffdale voters (the
  CountyID-25 slice is Camp Williams / unpopulated). County map tools:
  SL County `saltlakecounty.gov/clerk/elections/maps/`, Utah County `vote.utahcounty.gov/maps`.
- No Bluffdale-specific ArcGIS district FeatureServer is needed (there are no districts). If a city
  outline or parcel layer is wanted, check SLCo open data `gisdata-slco.opendata.arcgis.com`.

---

## Retrieval plan (recommended order)

1. **Council minutes 2020→present:** enumerate each year via `AgendaCenter/Search/?CIDs=2%2C&
   startDate=01/01/<yr>&endDate=12/31/<yr>` → harvest `ViewFile/Minutes/_…` links (take Minutes,
   drop Agenda) → curl each PDF (browser UA) → `raw/minutes/<year>/`. **Council PDFs are image
   scans with NO text layer → OCR** (ocrmypdf / vision) before markdown.
2. **Council vote extraction:** parse named `Vote on Motion: Council Member <Name>-Yes/No … passed
   N-to-M / passed unanimously` AND the `unanimous consent of the Council` form; mover+seconder;
   `Present:` block for attendance. **Max tally 5, Mayor NON-voting.**
3. **Planning Commission 2020→present:** `CIDs=3`. PC PDFs **have a text layer** (`pdftotext -layout`
   works — spot-check OCR typos). Capture named tallies (incl. `Chair <Name>` — PC chair votes) +
   `POSITIVE/NEGATIVE recommendation to the City Council` referrals keyed to `Application <YYYY-NN>`.
4. **Comments:** grep council & PC agenda **packets** for written correspondence; otherwise build a
   labeled `minutes_speaker_log.csv` + record the SUBMIT-ONLY honest verdict.
5. **Elections:** reuse the canonical `salt_lake_county/elections/slco_municipal_results_long.csv`
   (filter `%BLUFFDALE%`); **re-parse the raw 2019 SLCo SOVC** for the missing 3-seat council races;
   verify a Utah County SOVC shows ~zero Bluffdale rows (two-county close-out).
6. **Geo:** UGRC municipal boundary `NAME='BLUFFDALE'` + VistaBallotAreas **CountyID 18 & 25**. No
   district polygons (at-large) — address→rep tool returns the citywide Mayor + 5 at-large seats.

---

## Risks / blockers

- **Council minutes are image scans with NO text layer (MEDIUM):** `Producer: PFUPDF Engine`,
  ~20 chars extractable — **OCR required** for council (PC minutes DO have a text layer). Pages are
  clean/legible → OCR should be high-quality; verify no digit/name corruption on vote tallies.
- **No bot-block (LOW/none):** `bluffdale.gov` served both curl (browser UA) and WebFetch without a
  403. Use the browser UA regardless.
- **AgendaCenter default tab = current year only:** back-years require the `Search/?CIDs=…&
  startDate/endDate` endpoint (proven) or DocumentCenter — don't rely on the JS-rendered tab.
- **2019 election gap (3 council seats):** absent from the canonical CSV — raw-2019-SLCo-SOVC
  re-parse needed (known collection-wide 2019 failure mode).
- **Two-county edge (LOW):** Bluffdale spans SL + Utah counties, but the Utah-County portion is
  Camp Williams/unpopulated → SL administers all; confirm ~zero Bluffdale rows in a Utah County SOVC
  before declaring the SLCo archive complete (NOT a Draper-style split — Bluffdale has no populated
  Utah-County neighborhood).
- **Mayor-vote form (STRUCTURAL, RESOLVED):** Mayor presides but **does NOT vote** — confirmed on
  contested named roll calls (max tally 5). Watch for a rare **mayoral tie-break** (separate line,
  not a routine tally).
- **Roster drift:** Traci Crockett (at-large, → Dec 2025) replaced by Mackey Smith (Jan 2026);
  capture pre-2024 members from the 2020–2023 minutes headers.

---

## Key URLs (quick index)

| What | URL |
|---|---|
| City site (CivicEngage; no bot-block) | https://www.bluffdale.gov/ |
| City Council info | https://www.bluffdale.gov/333/City-Council |
| Mayor & Council roster | https://www.bluffdale.gov/333/Mayor-City-Council |
| AgendaCenter (all bodies) | https://www.bluffdale.gov/AgendaCenter |
| Council agendas/minutes tab | https://www.bluffdale.gov/AgendaCenter/City-Council-2 |
| ⭐ Enumerate council (any year) | https://www.bluffdale.gov/AgendaCenter/Search/?CIDs=2%2C&startDate=01%2F01%2F2020&endDate=12%2F31%2F2020&term= |
| Minutes doc pattern | https://www.bluffdale.gov/AgendaCenter/ViewFile/Minutes/_<MMDDYYYY>-<id> |
| Council minutes sample (verified, scanned) | https://www.bluffdale.gov/AgendaCenter/ViewFile/Minutes/_09242025-1693 |
| Planning Commission tab | https://www.bluffdale.gov/AgendaCenter/Planning-Commission-3 |
| ⭐ Enumerate PC (any year) | https://www.bluffdale.gov/AgendaCenter/Search/?CIDs=3%2C&startDate=01%2F01%2F2020&endDate=12%2F31%2F2020&term= |
| PC minutes sample (verified, text layer) | https://www.bluffdale.gov/AgendaCenter/ViewFile/Minutes/_05072025-1618 |
| Meeting schedule | https://www.bluffdale.gov/165/Meeting-Schedule |
| Elections (city) | https://www.bluffdale.gov/498/Elections |
| Live results (SL County) | https://electionresults.utah.gov/results/public/salt-lake-county-ut |
| Canonical election archive | /Users/tysonwelsh/civic-data/salt_lake_county/elections/slco_municipal_results_long.csv (filter %BLUFFDALE%; 2019 GAP) |
| PMN (agenda/minutes mirror) | https://www.pmn.utah.gov (utah.gov/pmn) |
| UGRC precincts (both counties) | https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/VistaBallotAreas/FeatureServer/0 (CountyID 18 + 25) |
| UGRC municipal boundary | https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/UtahMunicipalBoundaries/FeatureServer/0 (NAME='BLUFFDALE') |

```json
{"city":"Bluffdale","vendor":"CivicPlus/CivicEngage Central (Granicus)","minutes_landing_url":"https://www.bluffdale.gov/AgendaCenter/City-Council-2","minutes_url_pattern":"https://www.bluffdale.gov/AgendaCenter/ViewFile/Minutes/_<MMDDYYYY>-<id> ; enumerate via /AgendaCenter/Search/?CIDs=2%2C&startDate=..&endDate=.. (CID=2 council, CID=3 PC)","coverage_years":"council ~2013-2026 on portal (2020 floor fully covered; older in DocumentCenter); PMN mirror fallback","format":"SCANNED image PDF - council has NO text layer (PFUPDF Engine, OCR required); PC minutes HAVE embedded OCR text layer (pdftotext works)","votes_in_minutes":true,"vote_style":"named per-member roll call - 'Vote on Motion: Council Member <Name>-Yes/No ... passed N-to-M / unanimously'; contested 3-2 & 4-1 confirmed; lighter 'unanimous consent of the Council' form on routine items; mover+seconder named","pc_portal":"https://www.bluffdale.gov/AgendaCenter/Planning-Commission-3 (same CivicEngage, CID=3)","pc_coverage":"2020-2026 on portal; 1st & 3rd Wednesday 6pm; named tallies + POSITIVE/NEGATIVE recommendation-to-Council, Application <YYYY-NN> case numbers; PC chair (Cragun) DOES vote","council_weekday":"Wednesday (2nd & 4th, 6:00pm; optional 5:00pm work session; occasional extra Wednesdays)","num_districts":0,"at_large_seats":5,"mayor_votes":false,"max_tally":5,"current_members":["Mayor Natalie Hall (presides, non-voting; 2026-2029)","Wendy Aston (at-large, 2026-2029)","Mackey Smith (at-large, 2026-2029; new 2025, replaced Traci Crockett)","Steve Austin (at-large, 2024-2027)","Alan Lord (at-large, 2024-2027)","Greg Wilding (at-large, 2024-2027)","[2020-2025 record also names Traci Crockett, at-large through Dec 2025]"],"comments_published":false,"comments_note":"submit-only (in-person + email councilmeetingcomment@bluffdale.gov, NOT read at meeting, not posted); no eComment/correspondence archive; likely honest-empty - build minutes_speaker_log.csv; auditor confirm via packets","election_admin_county":"Salt Lake County (administers & reports ALL Bluffdale results)","two_county_notes":"Bluffdale straddles Salt Lake (populated) + Utah County (Camp Williams/unpopulated - essentially no registered voters); SL administers everything, canonical SLCo CSV is complete; NOT a Draper-style split; verify ~zero BLUFFDALE rows in a Utah County SOVC to close out","gis_source":"at-large city - NO council-district polygons needed (address->rep is citywide: Mayor + 5 at-large); UGRC UtahMunicipalBoundaries NAME='BLUFFDALE'; UGRC VistaBallotAreas precincts pull CountyID 18 (SL) AND 25 (Utah)","blockers":["council minutes are image scans with NO text layer - OCR required (PC minutes have text layer)","AgendaCenter default tab shows current year only - use Search/?CIDs endpoint for back-years","2019 election GAP in canonical CSV (3 council seats) - re-parse raw 2019 SLCo SOVC","two-county close-out: confirm ~zero Bluffdale rows in Utah County SOVC","roster drift: Crockett->Smith Jan 2026; pull pre-2024 members from 2020-2023 minutes headers"],"confidence_notes":"Site domain, vendor, URL patterns, cadence, at-large structure, and MAYOR-NON-VOTING (max tally 5) all CONFIRMED from live fetches + real 2025 scanned minutes with named contested roll calls (Res 2025-82: 3-to-2 and 4-to-1). PC votes+recommendation format CONFIRMED from 2025-05-07 PC minutes (text layer). Election coverage + at-large label CONFIRMED in canonical CSV (2007-2025, 2019 gap). No bot-block observed."}
```
