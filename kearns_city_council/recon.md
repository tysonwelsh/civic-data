# Kearns, Utah — Civic Data Recon

**Entity:** City of Kearns, **Salt Lake County**, Utah (~36k pop. — the largest of the SLCo
metro townships before it incorporated).
**Recon date:** 2026-07-12
**Data floor:** **2017** (Kearns Metro Township was created by the **2015-11-03** county vote and
took effect **Jan 1, 2017**; 2017–present is FULL HISTORY, not a gap).
**Form of government — TWO regimes (a hard structural seam at Nov 2025 / Jan 2026):**
- **Metro-township era (2017 → Dec 2025):** a **5-member Township Council (seats 1–5)** that
  **elected its own Chair**; **NO separately-elected mayor**; executive/municipal services
  supplied by the **Greater Salt Lake Municipal Services District (MSD)**. Land use ran through
  the MSD-staffed Kearns Planning Commission.
- **City era (incorporated as a CITY 2024-05; first city election 2025-11-04; officials seated
  ~Jan 2026):** **a directly-elected Mayor + 4 district Council Members (4 districts)** — 5
  elected officials. **⚠ THE MAYOR VOTES** (see §2 — this is the opposite of Taylorsville and
  matches Millcreek's voting-mayor form). Kearns is now the **first Utah city with a Hispanic
  mayor** (Jesse Valdez, elected 2025).
**Official site:** `https://www.kearns.utah.gov/` — a **Cloudflare-protected custom CMS**
(Revize/BC-style). ⚠ **Every page returns the Cloudflare "Just a moment…" JS interstitial to any
bot UA (including a browser UA) — the city site is NOT directly scrapable.** Old township domains
`kmtutah.org` / `kearnsmetrotownship` redirect here. → **Utah PMN is the canonical acquisition
source for this repo** (born-digital clean-text PDFs; verified live). Elections page also mentions
a **CRA (Community Reinvestment Agency)** the council convenes as in-recess (§ "Other bodies").

---

## 1. Council minutes — acquire from Utah PMN (city site is Cloudflare-blocked)

### Portal — Utah Public Notice Website (PMN), council body **5823**
- **Body page:** `https://www.utah.gov/pmn/sitemap/publicbody/5823.html`
  ("Kearns Council", entity "Kearns"; **City Recorder Diana Baun, `dbaun@msd.utah.gov`** — the
  recorder is MSD staff). **Meeting location (as of 2025-12-01): Element Event Center, North
  Ballroom, 5658 Cougar Ln, Kearns.**
- **Notice → attachments pattern:** each meeting is a notice
  `https://www.utah.gov/pmn/sitemap/notice/<noticeId>.html`; PDFs live at
  **`https://www.utah.gov/pmn/files/<fileId>.pdf`**. ⚠ **Minutes are posted as an attachment to
  the NEXT meeting's notice** (e.g. the **05-11-2026 minutes** = file **1445065**, posted on the
  **06-08-2026** notice `1086959`). Each council notice also carries the **Agenda**, a combined
  **"Meeting Supporting Documents"** packet (agenda + ordinance texts, NOT the minutes), and an
  **audio MP3**. Harvest the notice list on body 5823 → for each, pull the attachment whose
  filename contains **"Meeting Minutes"** (drop agendas/packets/audio).
- **Filename convention (council):** `MM-DD-YYYY Kearns CC Meeting Minutes - FINAL DRAFT.pdf`
  (regular) / `MM-DD-YYYY Kearns CC Special Meeting Minutes - FINAL DRAFT.pdf` (special).
- **Coverage confirmed live:** 2026 regular + special meetings present on body 5823 (the body
  page surfaces only the **~10 most-recent notices** — see Blockers for the 2017–2024 back-catalog
  question).
- **Verified minutes doc:** `https://www.utah.gov/pmn/files/1445065.pdf` (2026-05-11 council),
  saved to `meeting_minutes/raw/minutes_2026-05-11.pdf`.

### Format — CONFIRMED born-digital clean-text PDF (no OCR garble)
`pdftotext -layout` yields clean, selectable text; proper names intact (`Jesse Valdez, Mayor`,
`Council Member Schaeffer`, `Council Member Butterfield`). Not scanned.

### Roll-call votes in minutes — CONFIRMED PRESENT (TALLY style; mover+seconder named)
Motions record **mover + seconder + a numeric tally**, NOT a per-member named roll call. Real
motions from the 2026-05-11 minutes:
> *"Council Member Schaeffer moved to approve the Minutes of the April 13, 2026, City Council
> Meeting. Council Member Butterfield seconded the motion. **Vote was 5-0, unanimous in favor.**"*

> *"Council Member Schaeffer moved to approve Resolution R2026-12. Council Member Butterfield
> seconded the motion. **The vote was 4-0, unanimous in favor with Council Member Colby abstaining
> from the vote.**"*

- **Style = tally + named dissent/abstain** (Millcreek/South-Jordan-like): the majority is
  honestly **unnamed** (only mover & seconder are named); **dissenters/abstainers ARE named**
  ("…with Council Member Colby abstaining"). Attendance is a `COUNCIL MEMBERS PRESENT:` header
  block. → member-level attribution comes from mover/seconder + attendance + named dissent; do not
  read a blank member list on a unanimous motion as missing extraction.
- Also convenes as the **Kearns Community Reinvestment Agency (CRA)** in-recess (the 2026-05-11
  council meeting opened "immediately following the adjournment of the Kearns Community
  Reinvestment Agency meeting") — an in-record body like an RDA (model as `body=CRA`).

---

## 2. Council structure — Mayor + 4 districts; ⚠ THE MAYOR VOTES (max tally = 5)

- **City era (current):** **1 Mayor (citywide) + 4 Council Members (Districts 1–4)** = 5 elected.
  The Mayor **presides over the council** (Mayor Valdez "called the meeting to order" and conducts
  it — there is no separately-elected council chair in the city era) **AND casts a vote**:
  full-council motions tally **5-0**, and only **4** Council Members exist, so the 5th vote is the
  **Mayor's**. → **Build with max council tally = 5 INCLUDING the voting mayor.** (Contrast:
  Taylorsville mayor does NOT vote. Kearns matches Millcreek's voting-mayor form.)
  ⚠ *Confidence:* the mayor-votes call rests on the 5-0 tallies in one verified doc — **confirm on
  a contested motion** where the mayor is named in a split vote before locking the denominator.
- **Current roster** (2026-05-11 minutes header + PMN body 5823 Board/Committee Contacts,
  `@kearns.utah.gov`):

  | Seat | Member | Notes |
  |---|---|---|
  | **Mayor** (citywide, VOTING + presides) | **Jesse Valdez** | first Hispanic mayor in UT; won 2025 (~58%) |
  | Council Member | **Lorrin Colby Jr.** | won a 2025 seat (D2 or D4 — confirm) |
  | Council Member | **Lyndsay Longtin** | won a 2025 seat (D2 or D4 — confirm) |
  | Council Member | **Chrystal Butterfield** | holdover/other district (D1 or D3 — confirm) |
  | Council Member | **Patrick Schaeffer** | holdover/other district (D1 or D3 — confirm) |

- **Districts are NEW for the city era.** The township used 5 at-large-ish seats (1–5); the city
  redrew to **4 districts** for the 2025 election. **2025 ballot = Mayor + Council District 2 +
  Council District 4** (4-yr terms) → **Districts 1 & 3 are on the other cycle** (short 2-yr terms
  in the transition, next up ~2027 — confirm the stagger). Exact member→district mapping needs the
  certified 2025 results (Colby & Longtin won D2/D4; Butterfield & Schaeffer hold D1/D3).
- **Cadence — MONDAY.** Regular council = **2nd Monday, 6:00 p.m.**, monthly (verified: 2026-04-13,
  05-11, 06-08, 07-13 are all 2nd Mondays); special meetings on other weekdays (e.g. budget
  hearings). Combine any CRA-then-council same-night docs by date.

---

## 3. Planning Commission — Kearns has its OWN PC, but it is **MSD-administered**

- **"Kearns Planning Commission"** is a distinct body that acts on Kearns land use, **staffed and
  minuted by the Greater Salt Lake MSD Planning & Development Services** (not city staff).
  - **PMN body 1561:** `https://www.utah.gov/pmn/sitemap/publicbody/1561.html`
    (recorder **Wendy Gurr, `wgurr@msd.utah.gov`**; MSD address 2001 S. State St / 860 W. Levoy Dr).
  - City landing (Cloudflare-blocked): `https://www.kearns.utah.gov/bc-pc`.
  - MSD program pages: `https://msd.utah.gov/239/City-of-Kearns`,
    `https://msd.utah.gov/203/Planning-Development`.
- **Minutes on PMN body 1561**, filename `YYMMDD_KearnsPC_MinutesApproved.pdf` (+ Agenda, Packet,
  Staff Report, MP3 per notice). **Verified doc:** `https://www.utah.gov/pmn/files/1458161.pdf`
  (2026-06-01 PC minutes) → `planning_commission/raw/pc_minutes_2026-06-01.pdf`. Clean text, MSD
  "MEETING MINUTE SUMMARY" letterhead. Coverage reaches **at least 2023** (PMN files 927577,
  960581, 996873, 1303815 are 2023–2025 Kearns PC agendas).
- **Cadence — MONDAY (1st Monday, 6:00 p.m.);** some months cancelled (e.g. 2026-05-04 cancelled).
- **Votes CONFIRMED PRESENT — tally style + recommendation-to-Council:** tabular attendance grid,
  then `Motion by: Commissioner X / Vote: Commissioners voted unanimously in favor`. PC issues
  **recommendations to the Kearns Council** on general-plan / zoning amendments. **Land-use cases
  are keyed `file #OAM<YYYY>-<NNNNNN>`** (e.g. `OAM2026-001628`) — the cross-body referral bridge.
  Commissioners: **David Taylor (Chair), Gray Thomas (Vice Chair), Joy Nelson, Laura Koester,
  Michael Reynolds.**

---

## 4. Public comments — most likely SUBMIT-ONLY / speaker-log-in-minutes (auditor's call)

- Meetings take **"Citizen Public Input" (3 min/person)** via a sign-up form (`wkf.ms/44QBEzy`) and
  a virtual queue (`app.be.live/...`); the public may **email written comment to the City Recorder
  (`dbaun@msd.utah.gov`) before 3:00 p.m.** on meeting day. Minutes **paraphrase** speakers
  ("Numerous members of the public offered comments…", named residents summarized) — these are
  **meeting-record speaker notes, NOT a published written-comment archive**.
- **No standalone eComment / correspondence archive located** (the only comment portals are the
  live sign-up + email-to-recorder). → likely a **`minutes_speaker_log.csv`** + an honest
  submit-only verdict in `public_comments/AVAILABILITY.md`. Do NOT declare unavailable before
  checking the council "Supporting Documents" packets and PC packets for bundled written
  correspondence.

---

## 5. Elections — Salt Lake County; canonical CSV present but 2021/2023/2025 are mis-labeled

- **Run by** the Salt Lake County Clerk; results also at `https://electionresults.utah.gov/`
  (JS-rendered — use the county SOVC, not this page). **First city (mayor+council) election =
  2025-11-04.**
- **Canonical shared file** `salt_lake_county/elections/slco_municipal_results_long.csv` already
  contains Kearns, but the labels degrade over time:

  | Year | Kearns council/mayor contest label in the CSV | Note |
  |---|---|---|
  | 2015 | `KEARNS METRO TOWNSHIP-CITY` | incorporation vote + first township council |
  | 2017 | `KEARNS METRO TOWNSHIP CNCL 2`, `… CNCL 4` | seats 2 & 4 (staggered 5-seat township) |
  | 2019 | *(not seen — check for the seat 1/3/5 cycle)* | verify |
  | 2021 | `Sheet55`–`Sheet60` (generic) | **mis-filed** — re-parse raw SOVC by content |
  | 2023 | `Sheet6/7/8/12/16/17/18/55/58` | **mis-filed** — re-parse raw SOVC by content |
  | 2025 | `Sheet8/9/20/21/22/68` | **mis-filed** — Mayor + Council D2 + Council D4 (Valdez won mayor) |

  ⚠ Same `normalize_sovc.py` sheet-mislabeling defect seen for Taylorsville/South Jordan/Millcreek
  — **filter/re-key by contest CONTENT, not the `sheet`/`contest` column**, for 2021/2023/2025.
- **⚠ DECOYS to EXCLUDE (NOT city council):**
  - `Kearns Oquirrh Park Brd Trust` (2011 — Oquirrh Park recreation/fitness district board)
  - `KEARNS IMPROVEMENT` / `KEARNS IMPROVEMENT DIST` (2013/2017 — the water district;
    `kidwater4ut.gov`)
  - `KEARNS MSD` (2015 — the Municipal Services District ballot, a service district, not the council)
- **2025 candidates seen:** Mayor **Jesse Valdez** def. **Tina Marie Snow** (~58/42); Council D2/D4
  field incl. Lorrin Colby Jr., Lyndsay Longtin, Cache Dexter, Christopher Geertsen, Michael Valdez,
  T. Jordan Hansen, Roger Snow. Pull certified results for winners + district assignment.

---

## 6. GIS — no dedicated council-district FeatureServer; districts are NEW (2025)

- **City boundary:** UGRC **Utah Municipal Boundaries** `NAME='KEARNS'` (CountyID/COUNTYNBR **18**
  = Salt Lake) — confirmed live:
  `services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/UtahMunicipalBoundaries/FeatureServer/0`.
- **Council districts (4, created for the 2025 city election):** **no standalone district
  FeatureServer found.** A **"Kearns City Council District Map" PDF** is published on the
  Cloudflare-blocked election page `https://www.kearns.utah.gov/community/page/2025-election`.
  **Recommended derivation (as done for Taylorsville/SJ/Millcreek):** map the **2025 SOVC precinct
  rows → District 1–4** over Salt Lake County precinct geometry
  (`~/Desktop/slco-election-archive/geo/slco_precincts_current.geojson`; UGRC VistaBallotAreas
  CountyID 18) and dissolve to district polygons. These are **city-era boundaries only** (no
  township-era district lines existed — township seats were not geographic districts in the same
  way).
- **MSD zoning/land-use GIS (for planning context):** `https://zoning-gslmsd.hub.arcgis.com/`
  (Greater Salt Lake MSD ArcGIS Hub) — zoning layers covering Kearns.

---

## Other bodies observed
- **Kearns Community Reinvestment Agency (CRA)** — the council convenes as the CRA board in-recess
  (referenced in the 2026-05-11 council minutes). Likely its own PMN body; model as `body=CRA`
  (RDA-analog). Not separately mapped this recon.

---

## Retrieval plan (recommended order)
1. **Council minutes (PMN body 5823):** enumerate notices → for each, download the
   `…Meeting Minutes…FINAL DRAFT.pdf` attachment (`files/<id>.pdf`) → `meeting_minutes/raw/`.
   Clean text → markdown. Combine any same-night CRA + council docs by date.
2. **Vote extraction (council):** parse `Council Member X moved … Council Member Y seconded …
   Vote was N-0, unanimous in favor` and named dissent/abstain (`…with Council Member Z
   abstaining`); `COUNCIL MEMBERS PRESENT:` for attendance; **max tally 5, mayor VOTING**. Confirm
   the mayor-in-a-split-vote pattern on the first contested motion.
3. **Planning Commission (PMN body 1561):** download `…_KearnsPC_MinutesApproved.pdf`; capture
   `file #OAM…` case keys + PC→Council recommendation language (the referral bridge).
4. **Comments:** grep council "Supporting Documents" + PC packets for bundled written
   correspondence; else build `minutes_speaker_log.csv` + record the submit-only verdict.
5. **Elections:** use `slco_municipal_results_long.csv`; **re-parse raw 2021/2023/2025 SOVC by
   content** (sheet labels are broken); exclude the Oquirrh-Park / Improvement-District / MSD
   decoys; assign D2/D4 winners.
6. **Geo:** derive District 1–4 polygons from 2025 SOVC precinct rows × SLCo precinct geometry;
   UGRC boundary `NAME='KEARNS'` for the outline.

---

## Risks / blockers
- **City site is Cloudflare-blocked (HIGH):** `kearns.utah.gov` serves a JS challenge to all bots
  (browser UA included) → **cannot scrape the city CMS**; **use PMN** (bodies 5823 / 1561) as the
  canonical source. Verified: PMN serves clean-text PDFs with a plain browser UA.
- **Township-era back-catalog UNCONFIRMED (MEDIUM):** PMN body 5823 surfaces only the ~10 most
  recent notices; **2017–2024/2025 township council minutes were NOT located this recon.** Options
  to run down before declaring the floor: (a) older PMN notice IDs / an **older township-council
  PMN body id** (the 2017-era body may differ from 5823); (b) PMN full-text search; (c) OpenUtah
  (`kearns.openutah.org` / `taylorsville.openutah.org`-style); (d) the Cloudflare site's archive
  via a headless/residential fetch or Wayback. **Coverage below ~2025 on body 5823 is an open gap.**
- **Mayor-votes call (STRUCTURAL, ~confirmed):** 5-0 tallies with only 4 Council Members ⇒ mayor
  votes (max tally 5) — but from one doc; **confirm on a contested/split vote** before locking the
  denominator. Also watch the **Nov-2025 seam**: pre-2026 township motions are a **5-member
  chair-led** roll with **no mayor**.
- **Election sheet mis-filing (MEDIUM):** 2021/2023/2025 Kearns contests sit under generic
  `SheetNN` labels — re-parse the raw SOVC by content; exclude the three special-district decoys.
- **PC is MSD-run, not city (note, not a blocker):** PC minutes/agendas live under MSD staff on PMN
  body 1561, with `OAM…` case keys — the referral bridge to Council is via recommendation subject +
  date + `OAM` file numbers.
- **No city district GIS service:** derive from precincts; districts are **city-era-only** (2025+).

---

## Key URLs (quick index)
| What | URL |
|---|---|
| City site (Cloudflare-blocked) | https://www.kearns.utah.gov/ |
| PMN — Council body 5823 | https://www.utah.gov/pmn/sitemap/publicbody/5823.html |
| PMN — Planning Commission body 1561 (MSD-run) | https://www.utah.gov/pmn/sitemap/publicbody/1561.html |
| PMN file pattern | https://www.utah.gov/pmn/files/&lt;fileId&gt;.pdf |
| Council minutes sample (verified, 2026-05-11) | https://www.utah.gov/pmn/files/1445065.pdf |
| PC minutes sample (verified, 2026-06-01) | https://www.utah.gov/pmn/files/1458161.pdf |
| MSD — City of Kearns | https://msd.utah.gov/239/City-of-Kearns |
| MSD — Planning & Development | https://msd.utah.gov/203/Planning-Development |
| MSD zoning GIS hub | https://zoning-gslmsd.hub.arcgis.com/ |
| 2025 election page (district map PDF; Cloudflare) | https://www.kearns.utah.gov/community/page/2025-election |
| County live results | https://electionresults.utah.gov/ (Salt Lake County) |
| Canonical elections CSV (local) | /Users/tysonwelsh/civic-data/salt_lake_county/elections/slco_municipal_results_long.csv |
| UGRC municipal boundary (NAME='KEARNS', CountyID 18) | services1.arcgis.com/99lidPhWCzftIe9K/…/UtahMunicipalBoundaries/FeatureServer/0 |

```json
{"vendor":"Utah PMN (utah.gov/pmn) — canonical; city site kearns.utah.gov is a Cloudflare-blocked custom CMS (not scrapable). Council PMN body 5823, PC PMN body 1561 (MSD-staffed).","minutes_landing_url":"https://www.utah.gov/pmn/sitemap/publicbody/5823.html","minutes_url_pattern":"https://www.utah.gov/pmn/files/<fileId>.pdf ; minutes attach to the NEXT meeting's notice /pmn/sitemap/notice/<noticeId>.html ; filename 'MM-DD-YYYY Kearns CC Meeting Minutes - FINAL DRAFT.pdf'","coverage_years":"2026 confirmed on body 5823 (only ~10 recent notices surface); PC 2023+ confirmed; 2017-2024 township council back-catalog NOT yet located (open gap)","format":"born-digital clean-text PDF (no OCR)","votes_in_minutes":true,"vote_style":"tally + named dissent: mover+seconder named, 'Vote was 5-0, unanimous in favor'; dissenters/abstainers named; majority unnamed; COUNCIL MEMBERS PRESENT header; max tally 5 INCLUDING voting mayor","has_own_pc":true,"pc_location":"Kearns Planning Commission = its own body BUT administered/minuted by Greater Salt Lake MSD Planning & Development (PMN body 1561, recorder Wendy Gurr@msd.utah.gov); OAM<YYYY>-<NNNNNN> land-use case keys; recommends to Council; meets 1st Monday 6pm","council_weekday":"Monday (regular = 2nd Monday, 6:00pm, monthly; specials other weekdays)","num_seats":"city era: Mayor + 4 district council members (5 elected, districts new for 2025); township era (2017-2025): 5-member council, seats 1-5","has_mayor":"YES (city era, since Jan 2026) — Mayor Jesse Valdez, directly elected, PRESIDES over council AND VOTES (max tally 5). Township era 2017-2025 had NO mayor (council elected its own chair, MSD executive).","structure_notes":"HARD SEAM at Nov 2025/Jan 2026: metro-township (5-member, chair-led, no mayor, MSD-serviced) -> city (mayor+4 districts, voting mayor). Mayor-votes call is ~confirmed via 5-0 tallies w/ only 4 CMs; verify on a split vote. CRA (Community Reinvestment Agency) is an in-recess in-record body (model body=CRA).","current_members":["Mayor Jesse Valdez (voting, presides)","CM Lorrin Colby Jr. (won 2025 D2/D4)","CM Lyndsay Longtin (won 2025 D2/D4)","CM Chrystal Butterfield (D1/D3)","CM Patrick Schaeffer (D1/D3)"],"comments_published":"likely submit-only: in-meeting Citizen Public Input (3-min, sign-up form) + email-to-recorder before 3pm; minutes paraphrase speakers; NO standalone written-comment archive found -> minutes_speaker_log.csv + honest submit-only verdict (auditor's call; check packets first)","elections_decoys_to_exclude":["Kearns Oquirrh Park Brd Trust (2011 rec district)","KEARNS IMPROVEMENT / KEARNS IMPROVEMENT DIST (water district)","KEARNS MSD (Municipal Services District ballot)"],"gis_source":"UGRC Utah Municipal Boundaries NAME='KEARNS' CountyID 18 (city outline, confirmed); NO council-district FeatureServer -> derive District 1-4 from 2025 SOVC precinct rows x SLCo precinct geometry; districts are city-era-only (2025+); district-map PDF on kearns.utah.gov 2025-election page; MSD zoning hub zoning-gslmsd.hub.arcgis.com","data_floor":2017,"blockers":["city site kearns.utah.gov Cloudflare JS-challenge blocks direct scraping - use PMN","2017-2024 township council minutes not located on PMN body 5823 (only ~10 recent notices surface) - find older PMN body id / PMN search / OpenUtah / Wayback","mayor-votes determination from 1 doc's 5-0 tallies - confirm on a contested/split vote","2021/2023/2025 elections mis-filed under generic SheetNN labels - re-parse raw SOVC by content; exclude the 3 special-district decoys","member->district (D1-D4) mapping needs certified 2025 results"],"confidence_notes":"HIGH: PMN as source, clean-text format, votes-present tally style, own-but-MSD-run PC, Monday cadence, mayor exists+presides, data floor 2017, decoys. MEDIUM: mayor VOTES (1-doc inference), exact district assignments, township-era coverage/back-catalog, comments verdict."}
```
