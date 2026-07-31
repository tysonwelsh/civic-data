# Town of Alta, Utah — Civic Data Recon

**Municipality:** Town of Alta, **Salt Lake County**, Utah (~380 pop.; incorporated 1970;
top of Little Cottonwood Canyon, ski-resort town).
**Recon date:** 2026-07-11
**Scope / floor:** **2020-01-01 → present** (town has operated continuously since 1970;
2020 is a normal floor, minutes exist well before it).
**Form of government:** Utah **Town** form — a **Mayor + four-member at-large Town Council**.
⚠ **THE MAYOR VOTES** (confirmed against a real roll call, §2). A full roll call tops out at
**5** (Mayor + 4 councilmembers). This differs from the council–mayor executive cities
(Taylorsville/South Jordan) and matches Millcreek's voting-mayor pattern.
**Official site:** `https://townofalta.utah.gov/` — a **WordPress-based "Juniper" govtech CMS**
(a Utah.gov-hosted `*.utah.gov` subdomain; nginx/Plesk). The old `townofalta.com` now
**301-redirects here** (deprecated). Documents live in a Google Cloud Storage media bucket
`storage.googleapis.com/juniper-media-library/130/<YYYY>/<MM>/<file>` (Alta = tenant `130`).
Browser-UA `curl` works fine (no bot 403 seen); the `/meetings/` page is a **client-side JS
search app** (`juniperMeetings`/`juniperMeetingsSearch`) with no static doc links and no
public REST/AJAX route exposed — so **enumerate documents via Utah PMN**, not the HTML.

---

## 1. Town Council meeting minutes

### Portal — Juniper CMS front-end + Utah PMN archive (use PMN to enumerate)
- **Agendas & Minutes landing (canonical):** `https://townofalta.utah.gov/meetings/`
  — a JS app with a **Category** filter (Town Council / Planning Commission / Capital
  Committee) + a date-range search. Document links are injected by JS; the raw HTML exposes
  none, and `wp-json`/`admin-ajax` probes 404. **Do not scrape the HTML for doc URLs.**
- **Town-council landing page:** `https://townofalta.utah.gov/town-council/`
- **Enumerable archive = Utah Public Notice (PMN):**
  - **Council body id = `1601`** → `https://www.utah.gov/pmn/sitemap/publicbody/1601.html`
    (each meeting notice lists Agenda + Meeting Packet + Approved Minutes as separate PDFs).
  - **Minutes/agenda/packet doc URL pattern (PMN):**
    `https://www.utah.gov/pmn/files/<fileId>.pdf`
    (e.g. **2026-06-17 approved minutes = `utah.gov/pmn/files/1459201.pdf`** — the doc verified
    below; its agenda = `1448387.pdf`, packet = `1448693.pdf`).
  - **Town-hosted copy pattern (Juniper GCS):**
    `https://storage.googleapis.com/juniper-media-library/130/<YYYY>/<MM>/<filename>.pdf`
    (this is where the `/meetings/` app resolves docs; harvestable if the app's JSON payload is
    captured, but PMN is the simpler enumeration path).
- **Audio recordings:** the town posts meeting audio to **SoundCloud** —
  `https://soundcloud.com/townofalta` (a Whisper-transcript lead, out of scope for minutes).

### Coverage years
- **Minutes confirmed available 2020 → present** (well within scope). The now-deprecated
  `townofalta.com/…/agendas-minutes-2/` archive listed Town Council minutes year-by-year
  **2014–2023**; the current Juniper site + PMN body 1601 carry the current era (through
  July 2026 at recon). **PMN pagination holds pre-2020 years (out of scope below the floor).**
  → Enumerate the exact per-year doc set from **PMN body 1601** at acquisition (the JS app has
  no static index; PMN is the reliable list).

### Format — born-digital clean text PDF (NOT OCR)
`pdftotext -layout` on the **2026-06-17 council minutes** yields clean, selectable,
line-numbered text with proper names intact (`Mayor Roger Bourke`, `Councilmember Elise
Morgan`, `Councilmember Dan Schilling`). Not scanned; parses directly. (Confirm the
format holds on a 2020–2022 doc during acquisition — small towns occasionally change clerks.)

### Roll-call votes in minutes — CONFIRMED PRESENT, **named per-member roll call**
Verified in the 2026-06-17 minutes (saved to `meeting_minutes/raw/alta_2026-06-17_minutes.pdf`):
> *"MOTION: Elise Morgan motioned to approve Resolution 2026-R-14. Dan Schilling seconded.*
> *ROLL CALL VOTE: Councilmember Heimark – yes, Councilmember Morgan – yes, Councilmember*
> *Schilling – yes, **Mayor Bourke – yes**, Resolution 2026-R-14 was unanimously [approved]."*

- **Format:** `MOTION: <name> motioned … <name> seconded.` then a **named `ROLL CALL VOTE:`
  listing each member's yes/no** (unlike the narrative-tally cities — Alta prints per-member
  votes). Simple motions (e.g. adjourn) use `VOTE: All were in favor.`
- **Mayor is a full voting member** — appears by name in every roll call (see §2). The minutes
  even note *"Mayor Bourke brought attention to the significance of his vote to increase his own
  taxes"* — the mayor casts a counted vote. **Max council tally = 5.**
- Attendance header block: `PRESENT:` / `NOT PRESENT:` (e.g. Councilmember Anctil marked
  `NOT PRESENT` on 2026-06-17; virtual attendance flagged inline). A member absent from a roll
  call is a recording fact, not a non-vote by choice.
- ⚠ The verified motions were all unanimous → the **dissent-naming format is technically
  UNCONFIRMED**, but since Alta prints each member's yes/no by name, a `no` would simply read
  `Councilmember X – no`. Spot-check on the first contested motion.

---

## 2. Council structure — Mayor + 4 at-large councilmembers; **MAYOR VOTES** (max tally 5)

- **4 Town Council seats, ALL AT-LARGE** (confirmed by the election contest labels — every
  Alta council race is `… COUNCIL AT LARGE`, §5; **no districts**). **Non-partisan.** Seats are
  **staggered 4-year terms** (2 up every odd year — the 2007 ballot shows both a "COUNCIL AT
  LARGE 4 YEAR" and a "COUNCIL AT LARGE 2 YEAR" seat). Mayor elected townwide to a 4-year term.
- **Current roster** (from `town-council/` + the 2026-06-17 minutes header):

  | Seat | Member | Note |
  |---|---|---|
  | **Mayor** (townwide, **VOTING**) | **Roger Bourke** | votes in every roll call |
  | Council Member | **Elise Morgan** | Mayor Pro Tempore |
  | Council Member | **Carolyn Anctil** | (NOT PRESENT 2026-06-17) |
  | Council Member | **Dan Schilling** | |
  | Council Member | **Craig Heimark** | Capital Committee liaison |

- **⚠ MAYOR-VOTE DETERMINATION (key structural decision — RESOLVED):** Utah **Town** form.
  The Mayor **presides AND votes** — every verified `ROLL CALL VOTE` lists `Mayor Bourke – yes`
  alongside the councilmembers, and the minutes explicitly frame the mayor casting his own vote.
  → **Build with max council tally = 5, Mayor VOTING** (contrast Taylorsville/South Jordan where
  the mayor is a non-voting executive; matches Millcreek's voting mayor). Watch for the mayor
  breaking/making ties as an ordinary vote, not a separate tie-break entry.

---

## 3. Planning Commission — Alta HAS its own PC (Land Use Authority)

- **Yes — a standing Planning Commission exists** (`https://townofalta.utah.gov/planning-commission/`).
  It **authors/approves the General Plan** and is the town's **Land Use Authority** ("hear,
  review and act on all land use applications").
- **Members (2026):** David Abraham, Maren Askins, Paul Moxley, Jeff Niermeyer, Jon Nepstad,
  plus **Mayor Roger Bourke (Ex Officio)**. Volunteer commissioners with staggered terms
  (expiries 2027–2031).
- **Cadence:** *"tentatively meets on the **fourth Wednesday** of each month. However, when there
  is no business before the commission, meetings are cancelled."* → **sparse, frequently
  cancelled** (expect many months with no PC meeting — an honest gap, not a miss).
- **Minutes:** same `/meetings/` app (Category = Planning Commission) and **PMN body id `1602`**
  (`https://www.utah.gov/pmn/sitemap/publicbody/1602.html`); same `utah.gov/pmn/files/<id>.pdf`
  doc pattern. PC minutes format text-UNVERIFIED this recon — verify vote/recommendation grammar
  on the first PC doc (expect the same named roll call + PC→Council land-use recommendation).

---

## 4. Cadence

- **Town Council: monthly, 2nd Wednesday, 4:00 PM** (Alta Community Center), "unless otherwise
  noted." Additional work sessions / special meetings appear (the 2026-06-17 doc bundles a work
  session + public hearings + the regular meeting). **~12 regular meetings/year** (far fewer than
  the big cities) → sparse record by design.
- **Planning Commission: 4th Wednesday, as-needed** (cancelled when no business).

---

## 5. Elections — Salt Lake County (in the canonical long CSV; beware "ALTA CANYON" decoys)

- **Run by:** Salt Lake County Clerk. Non-partisan, **at-large** council + townwide Mayor.
- **Canonical file:** `/Users/tysonwelsh/civic-data/salt_lake_county/elections/slco_municipal_results_long.csv`.
  **Filter on the `contest` text, and EXCLUDE the "ALTA CANYON" decoys.**
- **GENUINE Town-of-Alta contests present:**

  | Year | Genuine Alta contest(s) | In-scope (≥2020)? |
  |---|---|---|
  | 2007 | `ALTA COUNCIL AT LARGE 4 YEAR`, `ALTA COUNCIL AT LARGE 2 YEAR` | no |
  | 2011 | `Alta Council At Large` | no |
  | 2013 | `ALTA COUNCIL AT LARGE` (+ `… 2 YEAR`), **`ALTA MAYOR`** | no |
  | 2015 | `ALTA COUNCIL AT LARGE` | no |
  | 2017 | `ALTA CNCL AT LARGE`, **`ALTA MAYOR`** | no |
  | **2021** | **`TOWN OF ALTA COUNCIL AT-LARGE`**, **`TOWN OF ALTA MAYOR`** | **YES** |
  | **2023** | **`TOWN OF ALTA COUNCIL AT-LARGE`** | **YES** |

- **⚠ FALSE MATCHES — DO NOT COUNT:** `ALTA CANYON REC BOARD MEMBER` / `ALTA CANYON REC SERVICE
  DIST` / `Alta Canyon Rec Service` / `ALTA CANYON REC` (2007, 2009, 2011, 2013). These are the
  **Alta Canyon Recreation Special Service District** (a Sandy/Cottonwood-Heights-area rec
  district), **NOT** the Town of Alta. Exclude on the `CANYON` token.
- **⚠ 2025 general appears ABSENT from the local CSV** (file currently tops out at 2023). A Nov
  **2025** municipal general (Mayor + 2 at-large council seats) almost certainly occurred —
  Bourke is the sitting 2026 mayor — so **2025 Alta results are a likely-pending gap**; re-pull
  the raw 2025 SLCo SOVC during acquisition. (2019 also predates the floor but is a check-worthy
  cycle if pre-2020 history is ever wanted.)
- Winner names are UPPER-CASE — normalize before joining to the minutes roster (e.g. current
  roster surnames Bourke/Morgan/Anctil/Schilling/Heimark). Note **Roger Bourke ran for council
  as far back as 2007** — a real continuity, not a name collision.

---

## 6. GIS — AT-LARGE (no council districts); town-boundary only

- **Alta elects at-large → there are NO council districts**, so **no address→district tool is
  needed** (the standard geo layer degenerates to "is this address in Town of Alta?").
- **Town boundary:** UGRC **Municipal Boundaries** `NAME='ALTA'`
  (`services1.arcgis.com/99lidPhWCzftIe9K/…/UtahMunicipalBoundaries/FeatureServer/0`), and Salt
  Lake County open data (`https://gisdata-slco.opendata.arcgis.com/`). **UGRC CountyID = 18**
  (Salt Lake) for any precinct/parcel join. Parcels via UGRC SGID Salt Lake County parcels /
  SLCo Assessor ParcelViewer.
- **Precincts:** Alta sits in a small number of SLCo precincts (2007 SOVC shows precinct `4790`
  / `4790D`); if precinct-level election geometry is wanted, reuse SLCo precinct geometry
  (CountyID 18). No town-specific FeatureServer needed.

---

## 7. Public comments — SUBMIT-ONLY / inline-in-minutes (honest zero expected)

- **No dedicated public-comment portal / eComment / written-comment archive found**
  (`/public-comment/` → 404). Public comment is taken **in-person at meetings** and paraphrased
  **inline in the minutes** (the 2026-06-17 doc transcribes speakers — Mark Haik, Margaret
  Bourke, an Alta Ski Area rep — as clerk paraphrase, i.e. **meeting-record speaker notes, NOT
  genuine written comments**). Live meetings also stream on the town **YouTube channel**.
- → Treat as a **legitimate honest zero** (like Taylorsville/South Jordan): build no
  `all_comments_clean.csv`; if desired, a labeled `minutes_speaker_log.csv` + an
  `AVAILABILITY.md` recording the SUBMIT-ONLY verdict. Do **not** declare a gap.

---

## Retrieval plan (recommended order)

1. **Enumerate + fetch Council minutes 2020→present via PMN body 1601**
   (`utah.gov/pmn/sitemap/publicbody/1601.html`, paginate back through 2020) → each notice's
   **Approved Minutes** PDF (`utah.gov/pmn/files/<id>.pdf`, keep the minutes, drop agenda/packet)
   → `raw/`. Cross-check against the Juniper `/meetings/` app if a PMN month is missing. Browser
   UA (no 403 seen, but keep it polite). Born-digital → markdown.
2. **Vote extraction (council):** parse `MOTION: <name> motioned … <name> seconded.` +
   `ROLL CALL VOTE: Councilmember X – yes/no, … Mayor Bourke – yes` → **named per-member rows,
   MAYOR IS A VOTER, max tally 5**; `PRESENT:`/`NOT PRESENT:` header for attendance; `VOTE: All
   were in favor` = unanimous. Verify dissent wording on the first contested motion.
3. **Planning Commission 2020→present via PMN body 1602** (sparse; many months cancelled = honest
   gaps). Text-verify the first PC doc's vote/recommendation grammar; capture land-use case refs.
4. **Comments:** record the SUBMIT-ONLY verdict (`AVAILABILITY.md`); optional speaker log.
5. **Elections:** reuse the canonical `slco_municipal_results_long.csv` (filter `contest` for
   Alta, **exclude `CANYON`**); **re-pull the raw 2025 SLCo SOVC** for the missing 2025 general.
6. **Geo:** at-large → town-boundary only (UGRC `NAME='ALTA'`, CountyID 18); no district tool.

---

## Risks / blockers

- **JS-only meetings app (LOW):** `townofalta.utah.gov/meetings/` renders doc links client-side
  (`juniperMeetings`); no static index, `wp-json`/`admin-ajax` 404. → **Enumerate via PMN bodies
  1601/1602**, not the HTML (or capture the app's JSON payload). No bot-403 observed (unlike the
  CivicEngage cities).
- **Sparse cadence (EXPECTED, not a defect):** ~12 council meetings/yr; PC meets only when it has
  business (frequently cancelled). Low document counts are correct for a ~380-person town.
- **2025 election gap:** local CSV stops at 2023; the 2025 Alta general (Mayor + 2 council) is
  likely uningested → re-pull raw 2025 SOVC. Exclude the `ALTA CANYON` rec-district decoys.
- **Dissent format unconfirmed:** verified motions were unanimous; named-`no` format inferred
  (`Councilmember X – no`) — confirm on the first contested roll call.
- **PC vote format text-unverified this recon.**
- **Format drift:** 2026 minutes are born-digital clean text; confirm a 2020–2022 doc isn't an
  older/scanned layout before bulk extraction.

---

## Key URLs (quick index)

| What | URL |
|---|---|
| Town site (Juniper CMS; `*.utah.gov`) | https://townofalta.utah.gov/ |
| Meetings — Agendas & Minutes (JS app) | https://townofalta.utah.gov/meetings/ |
| Town Council page | https://townofalta.utah.gov/town-council/ |
| Planning Commission page | https://townofalta.utah.gov/planning-commission/ |
| Council minutes sample (verified) | https://www.utah.gov/pmn/files/1459201.pdf (2026-06-17) |
| PMN — Council body | https://www.utah.gov/pmn/sitemap/publicbody/1601.html (id 1601) |
| PMN — Planning Commission body | https://www.utah.gov/pmn/sitemap/publicbody/1602.html (id 1602) |
| PMN doc pattern | https://www.utah.gov/pmn/files/<fileId>.pdf |
| Juniper doc/media pattern | https://storage.googleapis.com/juniper-media-library/130/<YYYY>/<MM>/<file> |
| Meeting audio | https://soundcloud.com/townofalta |
| Old site (301 → utah.gov) | https://townofalta.com/ (deprecated) |
| Elections (canonical, local) | /Users/tysonwelsh/civic-data/salt_lake_county/elections/slco_municipal_results_long.csv |
| SLCo open GIS | https://gisdata-slco.opendata.arcgis.com/ |

```json
{"vendor":"WordPress-based 'Juniper' govtech CMS on a Utah.gov-hosted *.utah.gov subdomain (nginx/Plesk); docs in GCS bucket juniper-media-library tenant 130; old townofalta.com 301-redirects here",
 "minutes_landing_url":"https://townofalta.utah.gov/meetings/ (JS search app; enumerate via Utah PMN council body 1601)",
 "minutes_url_pattern":"PMN: https://www.utah.gov/pmn/files/<fileId>.pdf (e.g. 2026-06-17 minutes=1459201.pdf); town-hosted: https://storage.googleapis.com/juniper-media-library/130/<YYYY>/<MM>/<file>.pdf",
 "coverage_years":"2020->present confirmed (deprecated old site listed council minutes 2014-2023; PMN body 1601 archive extends earlier, pre-2020 out of scope); enumerate exact set via PMN",
 "format":"born-digital clean text PDF (no OCR) - verified 2026-06-17; confirm on a 2020-2022 doc",
 "votes_in_minutes":true,
 "vote_style":"named per-member ROLL CALL VOTE ('Councilmember X - yes, ... Mayor Bourke - yes'); simple motions 'VOTE: All were in favor'; dissent format inferred 'X - no' (unconfirmed - all verified motions unanimous)",
 "has_planning_commission":true,
 "pc_portal":"same /meetings/ app (Category=Planning Commission) + Utah PMN body 1602; meets 4th Wednesday as-needed, frequently cancelled; PC is the Land Use Authority + General Plan author; PC vote format text-unverified this recon",
 "council_weekday":"Wednesday (2nd Wednesday, 4:00 PM monthly)",
 "cadence":"Council monthly (~12/yr) + occasional special/work sessions; PC 4th Wednesday as-needed (sparse, often cancelled)",
 "num_seats":4,
 "at_large":true,
 "mayor_votes":true,
 "max_tally":5,
 "current_members":["Mayor Roger Bourke (VOTING)","Elise Morgan (Mayor Pro Tem)","Carolyn Anctil","Dan Schilling","Craig Heimark"],
 "comments_published":false,
 "comments_note":"submit-only / in-person; paraphrased speaker notes inline in minutes; no written-comment archive (/public-comment 404) - honest zero",
 "elections_genuine_alta_contests":"GENUINE: 'ALTA COUNCIL AT LARGE'/'TOWN OF ALTA COUNCIL AT-LARGE' (2007,2011,2013,2015,2017,2021,2023) + 'ALTA MAYOR'/'TOWN OF ALTA MAYOR' (2013,2017,2021); in-scope>=2020 = 2021 (council+mayor) & 2023 (council). FALSE MATCHES to EXCLUDE: 'ALTA CANYON REC*' = Alta Canyon Recreation Special Service District, NOT Town of Alta. 2025 general likely-pending (absent from local CSV - re-pull raw SOVC)",
 "gis_source":"AT-LARGE, no council districts (no address->district tool needed); town boundary via UGRC Municipal Boundaries NAME='ALTA' (CountyID 18) + SLCo open data gisdata-slco.opendata.arcgis.com; parcels via UGRC SGID / SLCo Assessor",
 "blockers":["/meetings/ is JS-only (no static doc links, wp-json/admin-ajax 404) - enumerate via PMN bodies 1601/1602","sparse cadence by design (~12 council mtgs/yr; PC often cancelled) - low counts are correct not gaps","2025 election absent from local CSV - re-pull raw 2025 SLCo SOVC; exclude ALTA CANYON decoys","dissent roll-call format unconfirmed (all verified motions unanimous)","PC vote format text-unverified","confirm born-digital format holds on a 2020-2022 doc"],
 "confidence_notes":"HIGH on structure (mayor votes / at-large / 4 seats / PC exists) and vote format - all confirmed against the 2026-06-17 minutes PDF (saved to meeting_minutes/raw/) and the live town-council/planning-commission pages. MEDIUM on exact minutes coverage floor (confirmed >=2020 available but not enumerated doc-by-doc) and on 2025 election status. Site is browser-UA friendly (no 403 seen)."}
```
