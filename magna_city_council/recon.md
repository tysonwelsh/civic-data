# Magna City (formerly Magna Metro Township), Utah — Civic Data Recon

**Entity:** Magna, **Salt Lake County**, Utah (~29k pop.)
**Recon date:** 2026-07-12
**Data floor:** **2017** — Magna is one of the five Salt Lake County **metro townships** created by
the Nov-2015 voter process; its 5-member council was elected Nov 2016 and **seated Jan 1, 2017**
(full history from incorporation, not a gap).
**⚠ FORM-OF-GOVERNMENT CHANGED MID-RECORD (the single most important fact):**
- **2017 – 2025 (Metro Township):** a **5-member council** whose members were styled **"Trustee,"**
  presiding over itself via an **elected Chair** (e.g. **Chair Joe Smolka**). **No separately-elected
  mayor.** The Chair is one of the five and **votes** → max tally **5 incl. Chair**. Municipal
  *services* (roads, engineering, planning staff, parks) delivered by the Salt Lake County
  **Greater Salt Lake Municipal Services District (MSD)**.
- **Became a CITY on 2024-05-01** (Utah **H.B. 35**, which converted all five SLCo metro townships
  — Magna, Copperton, Emigration Canyon, Kearns, White City — to city status).
- **2025 general election** created, for the first time, a **directly-elected executive Mayor**
  (**Mick "Mickey" Sudbury**, seated ~Jan 2026 — Magna's first elected mayor). From 2026 the
  members are styled **"Council Member,"** the **Mayor presides but does NOT vote** (confirmed
  below — a `4-0` tally excludes the mayor), and the council elects a **Mayor Pro Tem**
  (Terry George). Administration is run by a **City Manager** (Kelly Bush). MSD still provides
  engineering/planning/land-use staff.
- **Net:** max council tally is **5 in both eras**, but the presiding officer flips from a
  **voting Chair (≤2025)** to a **non-voting Mayor (2026+)**, and the member noun flips
  **Trustee → Council Member**. The vote extractor MUST handle both seams at the 2025/2026 line.

**Official site:** `https://magna.utah.gov/` — **CivicPlus** CMS ("Government Websites by
CivicPlus®" in footer). Legacy/alternate hosts: `magnametrotownship.org` (metro-township-era
site) and `magnautah.org` (a community/"Magna Town Council" site — **NOT** the official
government portal; non-authoritative). MSD portal: `https://msd.utah.gov/351/Magna-City`.

---

## 1. Council meeting minutes

### Primary portal — CivicPlus **Agenda Center** on `magna.utah.gov`
- **Landing:** `https://magna.utah.gov/AgendaCenter` → **City Council = `/AgendaCenter/Council-3`**
- **Minutes doc URL pattern (CivicPlus):**
  ```
  https://magna.utah.gov/AgendaCenter/ViewFile/Minutes/_<MMDDYYYY>-<id>
  ```
  (e.g. `/AgendaCenter/ViewFile/Minutes/_05262026-209`). Agendas use the parallel
  `/AgendaCenter/ViewFile/Agenda/...`. Harvest the labeled links per year — do NOT guess ids.
- **Coverage on CivicPlus:** **2022 → 2026** readily visible (a "View More" reveals earlier years);
  treat **2022** as the reliable CivicPlus floor. The Agenda Center also carries **Community
  Reinvestment Agency (CRA)** meetings (Magna's RDA-equivalent — capture like Taylorsville's RDA).

### Deep archive / authoritative cross-check — **Utah Public Notice (PMN)**
PMN holds the full record back to the metro-township era (2017+) and is the source for **pre-2022**
minutes and for the Planning Commission.
- **Magna Council = PMN public body `5803`** (`https://www.utah.gov/pmn/sitemap/publicbody/5803.html`).
  Each meeting posts **Agenda + Supporting Docs + Audio (MP3) + Draft/Approved Minutes**.
- **File URL pattern:** `https://www.utah.gov/pmn/files/<fileId>.pdf`
  ⚠ **Use the `www.utah.gov` host — `pmn.utah.gov/pmn/files/<id>.pdf` 302-redirects to the PMN
  home page (returns HTML, not the PDF).** (Verified: same id served HTML on `pmn.` and a 10 MB
  PDF on `www.`)
- Metro-township-era body may also appear under older labels; body 5803 currently spans the
  city era. A **~pre-2022 metro-township minutes harvest should come from PMN 5803** (CivicPlus
  only reliably exposes 2022+).

### Format — CONFIRMED born-digital **text PDF**, with mild character-substitution garble
`pdftotext -layout` on the **2026-05-26 approved council minutes**
(`https://www.utah.gov/pmn/files/1447331.pdf`, saved to `meeting_minutes/raw/`) yields a
selectable text layer, **44 pages** (minutes + appended Attachments A/B/C). Text is clean enough
to parse but carries systematic font/OCR-style substitutions — e.g. `quonrm`→quorum,
`Hoffrnan`→Hoffman, `Masna.Utah.gov`, `at8z2l`→"at 8:21", `produced3T`→"produced 37". **Normalize
during extraction; not a blocker.**

### Roll-call votes in minutes — CONFIRMED PRESENT (narrative-tally style; Taylorsville/South-Jordan-like)
From the verified 2026-05-26 minutes:
> *"Council Member Jensen moved that the review committee consist of himself, Council Member
> [Prokopis]… Council Member Prokopis seconded the motion; **vote was 4-0, unanimous in favor
> with Council Member Pierce absent from the vote.**"*

- **Mover + seconder named; a numeric tally is printed; absentees/dissenters named.** No per-member
  Aye list on unanimous motions (a genuine roll call is taken; the printed minutes give the tally).
- **Present that night:** Mayor Sudbury (presiding) + Council Members Olsen, Prokopis, Jensen,
  George; **Pierce absent** → tally `4-0`. **The Mayor is NOT in the tally** → confirms
  **Mayor non-voting, max council tally = 5 (city era).**
- **Metro-township era (verified via 2023 PMN minutes):** members are **"Trustees,"** presided by
  **"Chair Smolka,"** with the same grammar — *"Trustee Flint moved… Trustee Bush seconded the
  motion."* The **Chair votes** (one of the five). → **max tally 5 incl. Chair, no separate mayor.**
- ⚠ Contested/dissent naming format not yet sampled (both eras' samples were unanimous) — pull a
  contested rezone/budget meeting to lock the dissent pattern before bulk extraction.

---

## 2. Council structure — 5 single-member districts; presiding officer flipped 2026

- **5 districts (D1–D5), one member each; non-partisan; 4-year staggered terms.** No at-large council
  seats. Since 2024 cityhood there is **also** a citywide **executive Mayor** (a 6th elected
  official, **not** a district seat).
- **Current roster (2026, from `/171/City-Council` + the 2026-05-26 minutes header):**

  | Seat | Member | Note |
  |---|---|---|
  | **Mayor** (citywide, executive) | **Mick "Mickey" Sudbury** | elected 2025 (first elected mayor); presides, **non-voting** |
  | District 1 | **Steve Prokopis** | (also a UFA fire chief — "Chief Prokopis") |
  | District 2 | **Megan L. Olsen** | elected 2025 |
  | District 3 | **Michael H. Jensen** | |
  | District 4 | **Terry George** | elected 2025; **Mayor Pro Tem** |
  | District 5 | **Audrey Pierce** | |

- **City Manager:** Kelly Bush (formerly a metro-township Trustee). **City Recorder:** Diana Baun.
  **Legal:** Jay Springer / Deputy City Attorney Claire Gillmore. **Land-use staff:** MSD Long-Range
  Planner Matt Starley + MSD engineering (Chad Anderson) / MSD Asst GM Brian Hartsell.
- **Term stagger:** **D2 / D4 (+ Mayor from 2025)** ran in **2017 / 2021 / 2025**; **D1 / D3 / D5**
  are on the **other (2019/2023) cycle** — see the elections gap in §5.
- **Meeting cadence — 2nd & 4th Tuesday, 6:00 PM**, **Webster Center, 8952 W Magna Main St**
  (verified: 2026-05-26 = a Tuesday; 2022 samples Tuesdays). ⚠ A 2023 metro-township doc fell on a
  **Wednesday** — historical cadence varied; treat **Tuesday** as the current/join weekday but
  confirm per-meeting dates rather than assuming.

---

## 3. Planning Commission — **Magna has its OWN PC** (MSD-staffed, county land-use body)

- Magna operates its **own Planning Commission** that recommends on **Magna land-use** (rezones
  keyed `REZ2026-…`, zoning code amendments, land-use fee schedule), **staffed by MSD** planning
  personnel. Land use is **NOT** handled purely at county level — it runs through Magna's PC.
- **Records host:** **PMN public body `1559`** ("Magna Planning Commission",
  `https://www.utah.gov/pmn/sitemap/publicbody/1559.html`), files at `www.utah.gov/pmn/files/<id>.pdf`
  (+ linked from the MSD site). **Whether the CivicPlus Agenda Center carries a PC tab is unconfirmed**
  (the Council-3 fetch showed only Council/CRA) — verify; PMN 1559 is the safe source.
- **Cadence:** **2nd Thursday** (all sampled PC agenda dates — 2022-04-14, 2023-03-16, 2023-10-12,
  2024-06-13, 2025-07-10, 2025-10-16, 2026-04-09, 2026-05-14, 2026-07-09 — are Thursdays).
- **Votes/recommendations:** expected recorded (same clerk shop). PC minutes **not text-verified this
  recon** — spot-check the first PC doc's vote/recommendation grammar during acquisition.

---

## 4. Public comments — most likely SUBMIT-ONLY / in-person (honest-empty candidate)

- Minutes carry a standing **"PUBLIC COMMENTS (Limited to 2 minutes per person)"** item taken
  **in person** at the meeting (sample: *"no individuals had signed up for public comment"*). No
  standalone published written-comment / eComment / correspondence archive surfaced.
- PMN posts a **meeting Audio MP3** per meeting (comment is spoken, not archived as text).
- **Verdict (provisional):** treat as **submit-only / honest-empty** like Taylorsville/South Jordan
  — do NOT build `all_comments_clean.csv` unless a written-comment archive is found; record the
  SUBMIT-ONLY finding in `public_comments/AVAILABILITY.md`. Inline hearing-speaker paraphrase in
  minutes → a labeled `minutes_speaker_log.csv`, never genuine comments. (Auditor's call — confirm
  no eComment before declaring the zero.)

---

## 5. Elections — Salt Lake County Clerk; already in `slco_municipal_results_long.csv`

Canonical shared file: `/Users/tysonwelsh/civic-data/salt_lake_county/elections/slco_municipal_results_long.csv`
(filter `contest ~ MAGNA`). **⚠ 2,660 "magna" rows are ~95% DECOYS** (Magna Water District). The
**genuine Magna township/city council + mayor contests** are:

| Year | Contest label(s) in file | Winner (aggregated) |
|---|---|---|
| 2017 | `MAGNA METRO TOWNSHIP CNCL 2` / `CNCL 4` | Brint D. Peel (D2), Trish Hull (D4) |
| 2021 | `MAGNA METRO TOWNSHIP COUNCIL DISTRICT 2` / `DISTRICT 4` | **Eric G. Barney** (D2, 112 v. Peel 57), Trish Hull (D4, uncontested) |
| 2025 | `MAGNA CITY COUNCIL DISTRICT 2` / `DISTRICT 4` / **`MAGNA CITY MAYOR`** | **Megan Olsen** (D2, 662 v. Barney 385), **Terry George** (D4, 497 v. Hull 468), **Mickey Sudbury** (Mayor, 3402 v. Adriano 1751 / Romero 525 / White 419) |

- **⚠ ELECTION GAP — Districts 1, 3, 5 council races are ABSENT from the archive.** The file has
  **no 2016, no 2019, and no 2023 Magna council-district rows** (2023 shows only `MAGNA WATER
  DISTRICT … AT-LARGE`). Only the D2/D4/Mayor cycle is present. Same failure mode as
  Taylorsville/South Jordan 2019 (numbered-sheet layout drops the entity string, or generic
  `CITY OF MAGNA …` sheet labels) → **re-parse the raw SOVC** for D1/D3/D5 (2019 & 2023, plus the
  Nov-2016 first metro-township election that seated all five seats).
- **⚠ 2015 rows are BALLOT QUESTIONS, not seats:** `MAGNA METRO TOWNSHIP-CITY` (the incorporation
  vote) and `MAGNA MSD` (the MSD-formation vote) — keep as context, not council races.
- **⚠ DECOYS to EXCLUDE** (all present, dominate the row count): `Magna Water Brd Trust` /
  `MAGNA WATER` / `MAGNA WATER DIST` / `MAGNA WATER BOARD OF TRUSTEES` / `MAGNA WATER DISTRICT
  BOARD OF TRUSTEES AT-LARGE` (the **Magna Water District** — a separate special district, 2011–2023),
  `MAGNA MSD`, and any mosquito-abatement / service-district contest. **Filter on the specific
  council/mayor contest strings above, never a bare `MAGNA` match.**
- **Roster transition to mind when joining winners → votes:** **Eric Barney** (D2 Trustee & council
  chair/"mayor" through the transition) **lost D2 to Olsen in 2025**; **Trish Hull** (long-time D4)
  **lost D4 to George in 2025**; **Sudbury** took the new Mayor seat. Names are UPPER-CASE with
  `(NP)` suffixes in the township years — normalize before joining.

---

## 6. GIS — UGRC city outline present; derive districts from precincts (no council-district layer)

- **City boundary:** UGRC **Municipalities** FeatureServer (service name `Municipalities`) —
  `https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/UtahMunicipalBoundaries/FeatureServer/0`,
  field `NAME='MAGNA'`, **`COUNTYNBR='18'` (Salt Lake)** — verified the service/fields exist and
  respond. Use for the city outline.
- **No standalone Magna council-district FeatureServer found** → **derive D1–D5 polygons from
  precinct→district assignment** as done for Taylorsville/South Jordan: SLCo precinct geometry
  (`~/Desktop/slco-election-archive/geo/slco_precincts_current.geojson`) × the D2/D4/Mayor SOVC
  precinct rows; the D1/D3/D5 precincts require the recovered 2019/2023 (or 2016) SOVC (see §5 gap).
  UGRC **VistaBallotAreas CountyID = 18** for the precinct join. Vintage caveat: district lines were
  set at 2016 incorporation and may have been adjusted — flag pre-vs-post for boundary-edge questions.

---

## Retrieval plan (recommended order)

1. **Council minutes 2022→2026 (CivicPlus):** harvest `/AgendaCenter/Council-3` per year →
   `ViewFile/Minutes/_<MMDDYYYY>-<id>` → `raw/`. Also pull **CRA** meetings (RDA-equivalent).
2. **Council minutes 2017→2021 (PMN body 5803):** harvest metro-township-era minutes from
   `www.utah.gov/pmn/files/<id>.pdf` (CivicPlus doesn't reliably expose pre-2022).
3. **Vote extraction — TWO regimes:** pre-2026 `Trustee … / Chair … presides & votes` (tally 5 incl.
   Chair, no mayor) vs 2026+ `Council Member … / Mayor presides, non-voting` (tally 5, mayor
   excluded). Normalize the text-substitution garble. Verify dissent wording on a contested meeting.
4. **Planning Commission (PMN body 1559):** harvest PC minutes/agendas; text-verify vote/recommendation
   format + capture land-use case numbers (`REZ####-…`). Check if CivicPlus also carries PC.
5. **Comments:** confirm no eComment; else build `public_comments/AVAILABILITY.md` (submit-only) +
   optional `minutes_speaker_log.csv`.
6. **Elections:** reuse `slco_municipal_results_long.csv` (council/mayor contest strings only, exclude
   Water District); **re-parse raw SOVC for D1/D3/D5 (2016/2019/2023)**.
7. **Geo:** UGRC Municipalities `NAME='MAGNA'` outline; derive D1–D5 from precincts (CountyID 18).

---

## Risks / blockers

- **Form-of-government seam (STRUCTURAL, the big one):** presiding officer flips voting-Chair (≤2025)
  → non-voting elected Mayor (2026+), and member noun flips **Trustee → Council Member**. Both eras
  cap the council tally at 5, but the extractor and roster logic must key off the meeting date.
- **PMN host trap:** fetch files from **`www.utah.gov/pmn/files/<id>.pdf`**, not `pmn.utah.gov/...`
  (the latter serves the PMN home HTML).
- **Text-layer garble:** clean but character-substituted (`quonrm`, `at8z2l`) — normalize.
- **Election gap:** D1/D3/D5 council races missing from the archive (no 2016/2019/2023 rows);
  Water-District decoys dominate — filter on exact contest strings and re-parse raw SOVC.
- **CivicPlus floor 2022:** pre-2022 relies on PMN 5803; PC relies on PMN 1559 (CivicPlus PC tab
  unconfirmed).
- **No city district GIS layer:** derive from precincts; boundary vintage (2016 incorporation) caveat.
- **CRA body** exists (RDA-like) — model like Taylorsville's `body=RDA`.
- **Contested-vote naming format unsampled** in both eras (samples unanimous) — lock before bulk extract.

---

## Key URLs (quick index)

| What | URL |
|---|---|
| Official site (CivicPlus) | https://magna.utah.gov/ |
| Council Agenda Center | https://magna.utah.gov/AgendaCenter/Council-3 |
| Minutes doc pattern | https://magna.utah.gov/AgendaCenter/ViewFile/Minutes/_<MMDDYYYY>-<id> |
| City Council page (roster) | https://magna.utah.gov/171/City-Council |
| Admin / cityhood note | https://magna.utah.gov/263/Mayors-Office-Administration |
| Elections (city page) | https://magna.utah.gov/161/Elections |
| PMN — Magna Council (body 5803) | https://www.utah.gov/pmn/sitemap/publicbody/5803.html |
| PMN — Magna Planning Commission (body 1559) | https://www.utah.gov/pmn/sitemap/publicbody/1559.html |
| PMN file pattern | https://www.utah.gov/pmn/files/<fileId>.pdf |
| Council minutes sample (verified, 2026-05-26) | https://www.utah.gov/pmn/files/1447331.pdf |
| MSD — Magna City | https://msd.utah.gov/351/Magna-City |
| MSD — Agendas/Minutes | https://msd.utah.gov/257/Agendas-Minutes-Meetings |
| Legacy metro-township site | https://magnametrotownship.org/ |
| Community site (NON-official) | https://magnautah.org/ |
| Elections archive (local) | /Users/tysonwelsh/civic-data/salt_lake_county/elections/slco_municipal_results_long.csv |
| Precinct geometry (for districts) | ~/Desktop/slco-election-archive/geo/slco_precincts_current.geojson |
| UGRC municipal boundary | https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/UtahMunicipalBoundaries/FeatureServer/0 (NAME='MAGNA', COUNTYNBR='18') |

```json
{"vendor":"CivicPlus (magna.utah.gov Agenda Center) — primary; Utah PMN (body 5803 council, 1559 planning) — deep archive + authoritative cross-check; MSD site links to both","minutes_landing_url":"https://magna.utah.gov/AgendaCenter/Council-3","minutes_url_pattern":"https://magna.utah.gov/AgendaCenter/ViewFile/Minutes/_<MMDDYYYY>-<id>  (PMN fallback: https://www.utah.gov/pmn/files/<fileId>.pdf — USE www.utah.gov host, NOT pmn.utah.gov)","coverage_years":"2017-2026 (governance floor 2017 = metro-township incorporation; CivicPlus reliably exposes 2022+, PMN body 5803 covers 2017-2021)","format":"born-digital text PDF, selectable; mild systematic character-substitution garble (quonrm/Hoffrnan/at8z2l) — normalize; combined doc with appended attachments","votes_in_minutes":true,"votes_style":"narrative tally — mover+seconder named + numeric tally (e.g. 'vote was 4-0, unanimous in favor with Council Member Pierce absent'); absentees/dissenters named, no per-member Aye list on unanimous; max council tally 5 in BOTH eras","has_own_pc":true,"pc_location":"Magna's OWN Planning Commission (MSD-staffed) — recommends on Magna land use (REZ####- rezones, zoning); records on PMN body 1559 (+MSD site); meets 2nd Thursday","council_weekday":"Tuesday (2nd & 4th, 6:00 PM, Webster Center) — current/city era; metro-township-era cadence varied (a 2023 doc fell on Wednesday) — confirm per-meeting","num_seats":5,"has_mayor":"CHANGED MID-RECORD: NO separate mayor 2017-2025 (5-member council elected its own Chair, e.g. Chair Joe Smolka, who VOTED); YES from cityhood — first directly-elected executive Mayor Mick Sudbury seated ~Jan 2026, PRESIDES but does NOT vote (confirmed tally excludes him)","structure_notes":"Metro township 2017-2024 (members styled 'Trustee', Chair presides+votes, no mayor, services via SLCo MSD) -> became CITY 2024-05-01 (HB 35) -> 2025 election created directly-elected Mayor + City Manager (Kelly Bush) form. 5 single-member districts D1-D5, non-partisan, 4-yr staggered (D2/D4/Mayor on 2017/2021/2025 cycle; D1/D3/D5 on 2019/2023). Council elects a Mayor Pro Tem (Terry George). CRA (RDA-equivalent) body exists. EXTRACTOR MUST HANDLE the Trustee->Council Member + voting-Chair->non-voting-Mayor seam at 2025/2026.","current_members":["Mayor Mick 'Mickey' Sudbury (executive, non-voting, elected 2025)","D1 Steve Prokopis","D2 Megan L. Olsen (elected 2025)","D3 Michael H. Jensen","D4 Terry George (Mayor Pro Tem, elected 2025)","D5 Audrey Pierce"],"comments_published":"provisionally NO — in-person/submit-only 2-min public comment at meetings; no written-comment/eComment archive found; PMN posts meeting audio MP3s. Treat as honest-empty pending confirmation (AVAILABILITY.md); inline hearing speakers -> minutes_speaker_log.csv","elections_decoys_to_exclude":["Magna Water Brd Trust / MAGNA WATER / MAGNA WATER DIST / MAGNA WATER BOARD OF TRUSTEES / MAGNA WATER DISTRICT BOARD OF TRUSTEES AT-LARGE (Magna Water District — separate special district; ~95% of 'magna' rows)","MAGNA MSD (2015 MSD-formation ballot question)","MAGNA METRO TOWNSHIP-CITY (2015 incorporation ballot question)","any mosquito-abatement / service-district contest"],"gis_source":"UGRC Municipalities FeatureServer NAME='MAGNA', COUNTYNBR='18' (Salt Lake) for city outline; NO council-district layer — derive D1-D5 from SLCo precinct geometry (~/Desktop/slco-election-archive/geo/slco_precincts_current.geojson) x district SOVC precinct rows, UGRC CountyID 18; district-vintage caveat (set at 2016 incorporation)","data_floor":2017,"blockers":["FORM-OF-GOV SEAM: voting-Chair(<=2025) -> non-voting elected Mayor(2026+) + Trustee->Council Member noun change; both eras cap council tally at 5 but extractor must key off meeting date","PMN files must be fetched from www.utah.gov/pmn/files/<id>.pdf — pmn.utah.gov redirects to the PMN home HTML","text-layer character-substitution garble — normalize during extraction","ELECTION GAP: Districts 1/3/5 council races absent from slco archive (no 2016/2019/2023 rows) — re-parse raw SOVC; Water-District decoys dominate — filter on exact council/mayor contest strings","CivicPlus floor ~2022 — pre-2022 council from PMN 5803; PC only confirmed on PMN 1559 (CivicPlus PC tab unconfirmed)","contested/dissent vote-naming format unsampled in both eras — lock before bulk extraction","CRA (RDA-equivalent) body to capture"],"confidence_notes":"HIGH: council portal+pattern, born-digital format, vote style, mayor-non-voting (city era) & Chair-voting (township era) both source-verified; current roster + 2025 winners from CSV+site; PC exists (own, MSD-staffed) on PMN 1559; decoys enumerated from actual CSV rows. MEDIUM: exact CivicPlus year floor / whether CivicPlus carries PC & pre-2022; comments honest-empty (pending eComment check); UGRC district-derive vintage. TO-CONFIRM: D1/D3/D5 election recovery; contested-vote dissent wording; precise metro-township seating/first-election dates."}
```
