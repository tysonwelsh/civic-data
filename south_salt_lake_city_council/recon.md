# South Salt Lake City, Utah — Civic Data Recon

**City:** South Salt Lake City, **Salt Lake County**, Utah (~26k pop.; **incorporated 1938**).
**Recon date:** 2026-07-11
**Scope of interest:** 2020–present (floor **2020** — city is old, so 2020 is a normal floor,
not an incorporation edge).
**Form of government:** **Council–Mayor (strong-mayor) form.** A **7-member City Council**
(**5 geographic districts + 2 At-Large**) legislates; a **separately-elected executive Mayor**
runs the administration and **does NOT vote** on council motions (VERIFIED against a real roll
call — see §1/§4). The council **elects its own Chair** to preside. → **Max council tally = 7.**
**Official site:** `https://sslc.gov/` — **CivicPlus / CivicEngage Central** CMS (AgendaCenter).
(`southsaltlakecity.com` is a legacy alias; **`sslc.gov` is canonical** — all live docs are here.)
Browser-UA `curl` worked cleanly on both `sslc.gov` and `utah.gov/pmn` this recon (no 403s
observed; keep the browser UA as a precaution).

---

## ⚠ HEADLINE FINDING — the recorded minutes are on Utah Public Notice (PMN), NOT the AgendaCenter

South Salt Lake's **CivicEngage AgendaCenter "Minutes" slot serves the AGENDA PACKET**
(agenda + staff reports + ordinance drafts + attachments), **not the recorded roll-call
minutes.** Verified across **2023, 2024, 2025 and 2026** meetings: every
`/AgendaCenter/ViewFile/Minutes/_<date>-<id>` returned a multi-MB packet headed
`… REGULAR MEETING AGENDA` whose only motion content is a **"MOTION SHEET"** of *proposed*
motions — **no `Aye/Nay`, no per-member roll call.** (One 2024 packet even embeds a **Salt
Lake City** Code-of-Conduct resolution as a reference attachment.)

**The clean, recorded minutes — with named per-member roll calls — live on the Utah Public
Notice website (`utah.gov/pmn`):**
- **City Council = PMN public body `1295`** → `https://www.utah.gov/pmn/sitemap/publicbody/1295.html`
- **Planning Commission = PMN public body `1297`** → `https://www.utah.gov/pmn/sitemap/publicbody/1297.html`
- **RDA = a separate PMN body** (id not captured this recon — resolve during acquisition; RDA
  meets the same Wednesday at **6:15 p.m.**, agenda `utah.gov/pmn/files/1367221.pdf`).
- Minutes are attachments at `https://www.utah.gov/pmn/files/<fileId>.pdf`. Council minutes are
  labeled **`DRAFT Reg Council YYYY.M.D.pdf`** (draft) / **`Reg Council YYYY.M.D.pdf`**
  (approved); PC minutes **`MMDDYY SSLC PC Mtg_Final.pdf`**.

→ **Acquisition strategy: harvest minutes from PMN bodies 1295/1297/RDA; use the AgendaCenter
for agenda PACKETS / staff reports** (an `expand-city-sources` packets layer, effectively) and
as a date index. This is the single most important structural fact for this city.

---

## 1. Council meeting minutes

### Portal A (minutes, CANONICAL) — Utah Public Notice, body 1295
- Landing: `https://www.utah.gov/pmn/sitemap/publicbody/1295.html` (lists recent notices; each
  notice attaches its agenda packet + the approved/draft **minutes** PDF).
- Doc pattern: `https://www.utah.gov/pmn/files/<fileId>.pdf`.
- **Coverage:** PMN body 1295 carries council notices well before the 2020 floor (needed —
  the city AgendaCenter only reaches **2022** for council, see below), so **2020–2021 council
  minutes come from PMN.**

### Portal B (agendas/packets + index) — CivicPlus AgendaCenter
- Landing: `https://sslc.gov/AgendaCenter` · City Council category `https://sslc.gov/AgendaCenter/City-Council-4`
- **Categories:** `cat4` City Council · `cat3` Planning Commission · `cat5` Redevelopment
  Agency (RDA) · `cat2` Civilian Review Board.
- Doc pattern: `https://sslc.gov/AgendaCenter/ViewFile/{Agenda|Minutes}/_MMDDYYYY-<id>`
  (two ids per council date = **Work Meeting** + **Regular Meeting**).
- Year listing (AJAX): `https://sslc.gov/AgendaCenter/UpdateCategoryList?catID=<n>&year=<YYYY>&term=&Keywords=`
  → harvest `ViewFile/Minutes/_…` ids per year.
- **On-portal coverage years:** City Council **2022–2026**, Planning Commission **2022–2026**,
  Civilian Review Board **2022–2026**, **RDA 2020–2026**. (Council 2020–2021 → PMN only.)
- ⚠ Remember: on this portal both the "Agenda" and "Minutes" links return the **agenda packet**
  — do NOT treat them as recorded minutes.

### Format — CONFIRMED born-digital clean-text PDF (no OCR garble)
`pdftotext -layout` on the PMN council minutes is clean, selectable, **line-numbered**; proper
names intact. The AgendaCenter packets are also born-digital (large, with embedded reports).

### Roll-call votes in minutes — CONFIRMED PRESENT, **named per-member** (max tally 7)
Verified against **council minutes 2026-06-10** (PMN file `1452459`, `DRAFT Reg Council 2026.6.10.pdf`).
Two vote formats appear — a **Voice Vote** and a **Roll Call Vote**, *both* listing **every one
of the 7 council members by name** with `Yes` / `No` / `Not Present`:

> **MOTION:** Joy Glad **SECOND:** Corey Thomas
> **Roll Call Vote:** Glad: Yes · Thomas: Yes · Bynum: Yes · Mitchell: Yes · Jones: Yes ·
> Williams: Yes · deWolfe: Yes *(motion to approve Mr. Okobia as Finance Director)*

> **MOTION:** Clarissa Williams **SECOND:** Joy Glad — **Voice Vote:** Glad: Yes · Thomas: Yes ·
> Bynum: Yes · **Mitchell: Not Present** · Jones: Yes · Williams: Yes · deWolfe: Yes
> *(approve minutes)*

- Header block gives `PRESIDING: Council Chair Sharla Bynum`, `CONDUCTING: Ray deWolfe, At-Large`,
  plus `COUNCIL MEMBERS PRESENT/NOT PRESENT`, `STAFF PRESENT`, `OTHERS PRESENT`.
- **The Mayor is NOT in the roll call.** In the same doc **Mayor Wood *presents* items** to the
  council (a Finance-Director appointment, the budget update) but casts **no vote** — see §4.
  → **This is a clean, named, 7-member roll call; parser target is per-member `Name: Yes/No`.**

---

## 2. Planning Commission — own PC (not the county)

- **PMN body `1297`** (`https://www.utah.gov/pmn/sitemap/publicbody/1297.html`) — canonical
  minutes; also AgendaCenter `cat3` (`https://sslc.gov/AgendaCenter/Planning-Commission-3`,
  2022–2026, agenda packets).
- **Cadence: Thursday, 7:00 p.m.**, South Salt Lake Council Chambers (220 East Morris Ave).
  Dates seen June 4 & June 18 2026 = **1st & 3rd Thursday** (verify exact frequency in the run).
- **Votes — CONFIRMED named per-commissioner.** Verified against **PC minutes 2026-06-04**
  (PMN file `1452287`, `060426 SSLC PC Mtg_Final.pdf`; saved to `raw/` as `PC_MIN_2026-06-04.pdf`):
  > **Motion to APPROVE** the application by Fred Cox for a Preliminary Subdivision Plat …
  > **Motion:** Commissioner Southey · **Second:** Commissioner Self ·
  > **Vote:** Commissioner Self – Yes; … **The vote was unanimous.**
  Commissioners named individually (Southey, Self, Spencer, Pechman, …). PC minutes reproduce
  the agenda then append the motion/vote records ("_Final" = approved).

---

## 3. Cadence

- **City Council: 2nd & 4th Wednesday.** Each meeting-day = a **6:30 p.m. Work Meeting** + a
  **7:00 p.m. Regular Meeting** (two AgendaCenter items / two PMN attachments per date).
- **Redevelopment Agency (RDA): same Wednesdays, 6:15 p.m.** (in Council Chambers; separate
  PMN body — the council convenes as the RDA board, akin to other cities' in-record RDA).
- **Planning Commission: Thursday, 7:00 p.m.** (≈1st & 3rd).
- **Civilian Review Board (CRB):** a 4th active body on the same portal (police use-of-force
  review) — not a land-use body, but present if wanted.
- Meetings livestreamed on **Zoom** + archived on **YouTube `@SouthSaltLakeCity`**.

---

## 4. Council structure — 7 members (5 districts + 2 At-Large) + executive Mayor; **Mayor does NOT vote**

- **5 council districts (Districts 1–5) + 2 At-Large seats** = **7-member council**; **Mayor
  elected citywide as the executive.** City page: *"divided into five geographic districts, with
  a council member representing each district. Additionally, there are two council members who
  represent the entire city as At-Large representatives."* **4-year staggered, non-partisan terms.**
- **Current roster** (city council page `sslc.gov/160/City-Council` + verified in the 2026-06-10
  minutes header + 2025 election winners):

  | Seat | Member |
  |---|---|
  | Mayor (citywide, executive) | **Cherie Wood** (won 2025 re-election, 2,203–1,097 vs Brittany Karzen) — **non-voting on council** |
  | District 1 | **Joy Glad** |
  | District 2 | **Corey Thomas** |
  | District 3 | **Sharla Bynum** (**Council Chair** / Presiding) |
  | District 4 | **Nick Mitchell** |
  | District 5 | **Irvin Jones** |
  | At-Large | **Ray deWolfe** |
  | At-Large | **Clarissa Williams** |

- **⚠ MAYOR-VOTE DETERMINATION (VERIFIED FROM A REAL ROLL CALL):** In the 2026-06-10 minutes,
  the **roll call lists exactly the 7 council members** (Glad, Thomas, Bynum, Mitchell, Jones,
  Williams, deWolfe); **Mayor Wood appears only as the presenter** of agenda items and gives the
  budget update — **she is never in a motion, second, or tally.** The council **elects its own
  Chair (Bynum)** to preside. → **Build with max council tally = 7, Mayor NON-voting.** Strong-mayor
  form confirmed. (Watch for a statutory mayoral **veto** as separate language, not a tally entry.)
- **Term stagger (from the election archive, §6):** **Mayor + one At-Large + D2 + D3** on the
  **2021/2025** cycle; **the other At-Large + D1 + D4 + D5** on the **2023** cycle. ⚠ **2025 also
  ran an "AT-LARGE (2 YEAR TERM)" special** (won by **Ray deWolfe**) — an unexpired-term seat off
  the normal cycle; flag it so member-term logic doesn't read it as a cycle shift.

---

## 5. Public comments — most likely SUBMIT-ONLY / honest-empty (auditor to confirm)

- Public comment is taken **in-meeting** (in person + Zoom): minutes carry a
  `Public Comments/Questions` item, an `OTHERS PRESENT:` attendee list, and paraphrased
  hearing-speaker notes (meeting-record speaker notes, **not** genuine written comments).
- A **"connect line" 801-464-6757 / `connect@sslc.gov`** is the intake channel.
- **No dedicated eComment / Open City Hall / published written-comment archive surfaced.**
  Written correspondence occasionally appears **embedded inside PMN agenda packets** (e.g. a
  resident refund email in the 2022-08-24 packet) — a lead, not an archive.
- **Verdict:** most likely **submit-only → build `public_comments/AVAILABILITY.md` as an honest
  zero**, exactly like Taylorsville/South Jordan — do NOT declare unavailable until the packet
  sweep is done (Phase 2: grep council/PC/RDA packets for emailed/written correspondence).

---

## 6. Elections — Salt Lake County (canonical archive already covers South Salt Lake)

- **Run by the Salt Lake County Clerk**; **non-partisan** (`(NP)` suffixes on some names).
- **Canonical file already present:**
  `/Users/tysonwelsh/civic-data/salt_lake_county/elections/slco_municipal_results_long.csv` —
  **filter `contest LIKE '%SOUTH SALT LAKE%'`** (label styles drift: `SOUTH SALT LAKE CITY
  COUNCIL 4` / `… CNCL @ LRG` / `CITY OF SOUTH SALT LAKE COUNCIL DISTRICT 2` / `SOUTH SALT LAKE
  CITY COUNCIL AT-LARGE (2 YEAR TERM)`). Also federated in `cities.db` `election_race`.
- **Seat structure confirmed in the data:** 5 districts + At-Large + Mayor (matches §4).
- **Contests present by year:** 2007 (D1/D4/D5 + At-Lrg), 2009 (Mayor + D2/D3), 2013 (Mayor +
  D2/D3 + @Lrg), 2015 (D1/D4/D5 + @Lrg + special bond), 2017 (Mayor + D2/D3 + @Lrg), 2021
  (Mayor + D2/D3 + At-Large), 2023 (D1/D4/D5 + At-Large), 2025 (Mayor + D2/D3 + At-Large +
  **At-Large 2-yr special**).
- **⚠ Apparent gaps to verify:** **no 2011 and no 2019** South Salt Lake rows in the long file
  (same failure mode seen for Taylorsville/South Jordan/Millcreek 2019 — numbered-sheet layout
  dropping the city string, or uncontested seats omitted). **Re-parse the raw 2011 & 2019 SOVC**
  for the districts due those cycles before declaring them uncontested.
- Winners are UPPER-CASE with `(NP)` suffixes — normalize before joining to the minutes roster
  (`JOY GLAD`→D1, `COREY THOMAS`→D2, `SHARLA BYNUM`→D3, `NICK MITCHELL`→D4, `IRVIN JONES`→D5,
  `RAY DEWOLFE`/`CLARISSA WILLIAMS`→At-Large, `CHERIE WOOD`→Mayor).

---

## 7. GIS — OFFICIAL city Council-District FeatureServer EXISTS (better than Taylorsville)

- **Official layer (live, verified):**
  `https://services5.arcgis.com/3nLdZUaMqOeKxP26/arcgis/rest/services/Council_Districts/FeatureServer/2`
  — **5 district polygons**, fields `CITY_COUNC` (1–5) + `LABEL` ("South Salt Lake Dist #N").
  Query `?where=1=1&outFields=*&f=geojson` returns all 5. Source ArcGIS app
  `appid=94faefd2f4f34fb3ab067c2583ab61ec` → webmap `44d87811f82449c1830afc85a34fe8c8`
  (item title *"South Salt Lake City Council Districts"*, owner `nmelville78`).
  → **Use this directly for `geo/` — no precinct-derivation needed** (unlike Taylorsville/SJ).
- **UGRC fallback:** Municipal Boundaries `NAME='SOUTH SALT LAKE'`; VistaBallotAreas
  **CountyID = 18** (Salt Lake) for a precinct cross-check. Precinct geometry already on disk:
  `~/Desktop/slco-election-archive/geo/slco_precincts_current.geojson` (+ `salt_lake_county/gis/`).
- Redistricting: districts are post-2020-census; treat the FeatureServer as **current** vintage
  (pre-2022 address→district questions may need older lines).

---

## Retrieval plan (recommended order)

1. **Council minutes 2020→present:** harvest **PMN body 1295** notices → the `Reg Council
   YYYY.M.D.pdf` / `DRAFT …` attachment per meeting date → `raw/minutes/<year>/`. Prefer the
   **approved** (non-DRAFT) version when both exist. Text-layer → markdown (clean, no OCR).
   Use the AgendaCenter (`UpdateCategoryList?catID=4`) as a **date index / agenda-packet source**,
   NOT for recorded minutes.
2. **Council vote extraction:** parse the `MOTION:` / `SECOND:` blocks and the per-member
   `Name: Yes/No/Not Present` **Roll Call Vote** / **Voice Vote** lists; attendance from the
   `COUNCIL MEMBERS PRESENT/NOT PRESENT` header. **Max tally 7, Mayor NON-voting.** Two At-Large
   members share the roster; key members by name (7 distinct).
3. **Planning Commission 2020→present:** PMN body 1297 (`… SSLC PC Mtg_Final.pdf`); Thursday
   cadence; per-commissioner `Vote:` lists → PC votes + PC→Council recommendation language.
4. **RDA:** resolve the RDA PMN body id (same Wednesday, 6:15 p.m.); model as an in-record body
   like other cities (`body=RDA`). CRB (`cat2`) optional.
5. **Comments:** grep council/PC/RDA **packets** (AgendaCenter + PMN) for emailed/written
   correspondence; otherwise a labeled `minutes_speaker_log.csv` + honest submit-only verdict.
6. **Elections:** reuse `slco_municipal_results_long.csv` (`contest LIKE '%SOUTH SALT LAKE%'`);
   **re-parse raw 2011 & 2019 SOVC**; flag the **2025 At-Large 2-yr special** (deWolfe).
7. **Geo:** pull the **official Council_Districts FeatureServer** (5 polygons) → address→district
   tool; UGRC CountyID 18 + precinct geojson as cross-check.

---

## Risks / blockers

- **Minutes are on PMN, not the AgendaCenter (STRUCTURAL — resolved):** the CivicEngage "Minutes"
  slot serves agenda **packets** with no roll call; the recorded named roll-call minutes are on
  **Utah Public Notice bodies 1295 (council) / 1297 (PC) / RDA**. Getting this right is the whole
  ballgame for this city.
- **Council 2020–2021 not on the city portal** (AgendaCenter council starts 2022) → **PMN body
  1295** supplies the 2020 floor.
- **RDA PMN body id not captured this recon** — resolve during acquisition (RDA meets Wed 6:15 p.m.).
- **Election gaps to verify:** **2011 & 2019** South Salt Lake rows absent from the long file —
  raw-SOVC re-parse before treating as uncontested. **2025 At-Large 2-yr special** must not be
  read as a cycle change.
- **Public-comment availability unconfirmed** — most likely submit-only (honest zero); do the
  packet sweep before finalizing.
- **Mayor-vote form (resolved):** strong-mayor, **Mayor does NOT vote, max tally = 7** — confirmed
  by a real roll call listing only the 7 council members while the Mayor merely presents. Watch
  for a mayoral veto (separate language).
- **Access:** browser-UA `curl` succeeded on `sslc.gov` and `utah.gov/pmn` this recon (no 403s);
  keep the browser UA regardless. PMN attachment PDFs can be large (agenda packets 10–45 MB;
  the clean minutes are small, ~0.2 MB).

---

## Key URLs (quick index)

| What | URL |
|---|---|
| City site (CivicEngage AgendaCenter) | https://sslc.gov/ |
| AgendaCenter (all bodies) | https://sslc.gov/AgendaCenter |
| City Council category | https://sslc.gov/AgendaCenter/City-Council-4 |
| AgendaCenter year listing (AJAX) | https://sslc.gov/AgendaCenter/UpdateCategoryList?catID=4&year=2025&term=&Keywords= |
| AgendaCenter doc pattern | https://sslc.gov/AgendaCenter/ViewFile/{Agenda\|Minutes}/_MMDDYYYY-<id> |
| City Council info page (roster) | https://sslc.gov/160/City-Council |
| **PMN — City Council (minutes, body 1295)** | https://www.utah.gov/pmn/sitemap/publicbody/1295.html |
| **PMN — Planning Commission (minutes, body 1297)** | https://www.utah.gov/pmn/sitemap/publicbody/1297.html |
| PMN attachment pattern | https://www.utah.gov/pmn/files/<fileId>.pdf |
| Council minutes sample (verified) | https://www.utah.gov/pmn/files/1452459.pdf (2026-06-10, DRAFT Reg Council) |
| PC minutes sample (verified) | https://www.utah.gov/pmn/files/1452287.pdf (2026-06-04, SSLC PC Mtg_Final) |
| RDA agenda (body TBD) | https://www.utah.gov/pmn/files/1367221.pdf |
| **Official Council Districts FeatureServer** | https://services5.arcgis.com/3nLdZUaMqOeKxP26/arcgis/rest/services/Council_Districts/FeatureServer/2 |
| Council Districts ArcGIS app | https://www.arcgis.com/apps/View/index.html?appid=94faefd2f4f34fb3ab067c2583ab61ec |
| Election archive (canonical) | /Users/tysonwelsh/civic-data/salt_lake_county/elections/slco_municipal_results_long.csv (filter `%SOUTH SALT LAKE%`) |
| Precinct geometry (cross-check) | ~/Desktop/slco-election-archive/geo/slco_precincts_current.geojson |

```json
{"city":"South Salt Lake","vendor":"CivicPlus/CivicEngage Central (AgendaCenter) for agendas/packets; Utah Public Notice (PMN) for the RECORDED minutes","minutes_landing_url":"https://www.utah.gov/pmn/sitemap/publicbody/1295.html (council, PMN body 1295) ; AgendaCenter https://sslc.gov/AgendaCenter/City-Council-4 = agenda PACKETS only","minutes_url_pattern":"PMN: https://www.utah.gov/pmn/files/<fileId>.pdf (labels 'Reg Council YYYY.M.D.pdf' / 'DRAFT Reg Council …') ; AgendaCenter: /AgendaCenter/ViewFile/{Agenda|Minutes}/_MMDDYYYY-<id> (both slots = agenda packet, NOT minutes)","coverage_years":"PMN council back before 2020 (2020 floor OK); AgendaCenter council/PC/CRB 2022-2026, RDA 2020-2026","format":"born-digital clean-text PDF (line-numbered; no OCR garble)","votes_in_minutes":true,"vote_style":"named per-member roll call — 'Roll Call Vote:' / 'Voice Vote:' listing all 7 council members 'Name: Yes/No/Not Present'; MOTION/SECOND named; confirmed council 2026-06-10 (PMN 1452459)","pc_portal":"PMN body 1297 (minutes) + AgendaCenter Planning-Commission-3 (packets); votes named per-commissioner, confirmed 2026-06-04 (PMN 1452287)","pc_coverage":"AgendaCenter 2022-2026; PMN back further","council_weekday":"Wednesday (2nd & 4th; Work Meeting 6:30pm + Regular 7:00pm; RDA same night 6:15pm). PC = Thursday 7pm (~1st & 3rd)","num_districts":5,"at_large_seats":2,"mayor_votes":false,"max_tally":7,"current_members":["Mayor Cherie Wood (executive, non-voting)","D1 Joy Glad","D2 Corey Thomas","D3 Sharla Bynum (Council Chair)","D4 Nick Mitchell","D5 Irvin Jones","At-Large Ray deWolfe","At-Large Clarissa Williams"],"comments_published":"most likely submit-only / honest-empty (in-meeting + Zoom + connect@sslc.gov; correspondence sometimes embedded in PMN packets; no eComment archive found) — confirm via packet sweep","gis_source":"OFFICIAL live FeatureServer https://services5.arcgis.com/3nLdZUaMqOeKxP26/arcgis/rest/services/Council_Districts/FeatureServer/2 (5 polygons, CITY_COUNC 1-5); UGRC CountyID 18; SLCo precinct geojson as cross-check","blockers":["RECORDED minutes are on PMN (bodies 1295 council / 1297 PC / RDA-tbd), NOT the AgendaCenter, whose Minutes slot serves agenda packets — verified 2023-2026","council 2020-2021 not on AgendaCenter (starts 2022) -> use PMN","RDA PMN body id not captured this recon - resolve in acquisition (Wed 6:15pm)","election gaps to verify: no 2011 & no 2019 SSL rows in slco long file - re-parse raw SOVC; 2025 At-Large 2-yr special (deWolfe) is off-cycle","public-comment availability unconfirmed - likely submit-only, do packet sweep before finalizing"],"confidence_notes":"HIGH: vendor, PMN-vs-AgendaCenter split, minutes format, named 7-member roll call, mayor-non-voting (all from real 2026 PDFs saved to raw/), council/PC cadence, 7-seat 5+2 structure, current roster, official district FeatureServer (5 polygons live), election archive coverage. MEDIUM: PC exact frequency (1st&3rd Thu inferred from 2 dates); 2020-2021 PMN completeness (assumed, spot-check); election 2011/2019 gap cause. LOW/TBD: RDA PMN body id; whether any AgendaCenter council record ever holds true minutes (none found)."}
```
