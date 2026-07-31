# Copperton, Utah — Civic Data Recon

**Place:** Copperton, **Salt Lake County**, Utah (~800 residents — TINY).
**Recon date:** 2026-07-12
**Data floor:** **2017** (incorporated as a **metro township 2017-01-01** — full history; no
gap). ⚠ See the structural note below: Copperton **converted from a metro township to a
TOWN on 2024-05-01**, so the governing-body form changed mid-record.

> ⚠️ **TASK PREMISE CORRECTION.** The recon brief assumed a *metro township* with a
> 5-member council electing its own chair and **no separately-elected mayor**. That was true
> **2017–2024**. But Copperton **converted to a Town (Utah town form) effective 2024-05-01**.
> The current body is **Mayor + 4 Council Members = 5**, the **Mayor is separately elected by
> the voters** (Sean Clayton, ran **unopposed for Mayor in Nov 2025**), and **the Mayor VOTES**
> — every roll call is a **5-member tally** ("vote was 5-0"). So `has_mayor = TRUE` (voting),
> `max_tally = 5`. This differs from the Alta/metro-township model the brief anticipated.

---

## 1. Township/Town Council minutes

### Primary portal — the town's own site (GoDaddy Website Builder)
- **Host:** `https://copperton.utah.gov/` (a `utah.gov` vanity domain, but the site is served
  from **GoDaddy Website Builder** / `*.secureserversites.net`). ⚠ **TLS cert mismatch** — the
  cert covers `secureserversites.net`, **not** `copperton.utah.gov`, so **WebFetch fails**
  ("Hostname does not match certificate's altnames"). Fetch with **`curl -k` (or plain
  `http://`) + a browser UA** — verified working this recon.
- **Agendas & Minutes landing — one page per year:**
  ```
  https://copperton.utah.gov/2023-agendas-%26-minutes
  https://copperton.utah.gov/2024-agendas-%26-minutes-1
  https://copperton.utah.gov/2025-agendas-%26-minutes-1
  https://copperton.utah.gov/2026-agendas-%26-minutes
  ```
  Each page lists that year's **Agenda / Supporting Documents / Minutes (APPROVED)** per meeting.
  The listing is **JS-rendered** (a GoDaddy JSON island) — a bare tag-strip yields only the nav;
  harvest the document anchors from the rendered DOM, not the static HTML.
- **Document URL pattern (opaque GoDaddy GUIDs — cannot be guessed, must harvest):**
  ```
  https://img1.wsimg.com/blobby/go/07a53a68-a6f6-4bc0-a742-37221fdbac6f/downloads/<doc-guid>/<filename>.pdf?ver=<n>
  ```
  Site GUID `07a53a68-a6f6-4bc0-a742-37221fdbac6f` is stable; each doc has its own GUID.
  Filenames encode the date + type, e.g. `07-16-2025 Copperton Meeting Minutes - APPROVED.pdf`,
  `11-19-2025 Copperton TC Minutes - APPROVED.pdf`.
- **Coverage on the town site:** **2023 → 2026** year folders. 2025 is near-complete
  (Jan–Nov minutes present; **Sep-2025 and Dec-2025 minutes not in the snapshot**). 2026 has
  Jan–May minutes. **Pre-2023 (2017–2022 metro-township era) is NOT on the town site** → use
  the PMN mirror or treat as a recovery gap (blocker below).

### Enumerable fallback / cross-check — Utah PMN
- **Body:** **"Copperton Council" = PMN public body `5831`** (long-standing — it carries both the
  metro-township-era and town-era notices; older notice e.g. `notice/974779.html` resolves to
  body 5831). Contact **Diana Baun, `dbaun@msd.utah.gov`** (town clerk, MSD-staffed).
  - Sitemap: `https://www.utah.gov/pmn/sitemap/publicbody/5831.html` (⚠ displays **only the
    current year** — 2026 shows 9 meetings; older years live in the notice archive, not this page).
  - Minutes/agendas/audio at `https://www.utah.gov/pmn/files/<fileId>.pdf` (+ `.mp3` audio).
  - Every meeting posts Agenda + Supporting Docs + **MP3 audio** + Minutes.

### Format — CONFIRMED born-digital clean-text PDF (no OCR)
`pdftotext -layout` on the **2025 minutes** yields clean, selectable text; proper names intact
(`Sean Clayton, Mayor`, `Tessa Stitzer, Mayor Pro Tempore`). Not scanned.
**Confirmation doc saved:** `meeting_minutes/raw/copperton_2025-07-16_minutes_DRAFT.pdf`.

### Roll-call votes — CONFIRMED PRESENT (narrative-tally, 5-member)
Motions record **mover + seconder + a numeric tally**, e.g. (verified in the saved doc):
> *"Council Member Stitzer moved to approve the June 18, 2025 Council Meeting Minutes as
> published. Council Member McCalmon seconded the motion; **vote was 5-0, unanimous in favor**."*

- Four motions in the sample, **all `5-0` unanimous**. **Max tally = 5** = **Mayor + 4 Council
  Members, all voting** (the Mayor moves the agenda and is counted in the 5). This is
  **South-Jordan/Taylorsville-style narrative tally** (numeric count, not a per-member Aye/Nay
  list on unanimous motions).
- ⚠ **Dissent-naming format UNCONFIRMED** — every sampled motion was unanimous. Pull a contested
  meeting to lock the per-member format before bulk extraction.

### Cadence — **3rd Wednesday, monthly, 6:30 PM**
Bingham Canyon Lions Club, **8725 Hillcrest Street, Copperton UT 84006** (all 2026 council
dates are 3rd Wednesdays: 01-21, 02-18, 03-18, 04-15, 05-20, 06-17). Occasional **special
meetings** (e.g. 2025-12-09 Rio Tinto). Roughly **~11–12 meetings/yr** (very low volume).

---

## 2. Governing-body structure — Town form (Mayor VOTES); 5 members; **at-large, no districts**

- **Current form (since 2024-05-01 town conversion):** **Mayor + 4 Council Members = 5**, all
  voting. Mayor is **separately elected citywide**; the council designates a **Mayor Pro Tempore**.
  **No council districts** — seats are **at-large**.
- **Current roster (2026, from the 2025 minutes + Jan-2026 swearing-in reports):**

  | Role | Member | Notes |
  |---|---|---|
  | **Mayor** (elected, voting) | **Sean Clayton** | ran **unopposed for Mayor, Nov 2025** |
  | **Mayor Pro Tempore** | **Tessa Stitzer** | |
  | Council Member | **Kathleen Bailey** | |
  | Council Member | **Linda McCalmon** | re-elected 2025 (seat D), sworn 2026-01-21 |
  | Council Member | **Jonathan Pratt** | new 2025, sworn 2026-01-21 (succeeds **Kevin Severson**) |

  **Kevin Severson** served through 2025 (in the July-2025 minutes) and was **replaced by Pratt**
  after the Nov-2025 election.
- **Metro-township era (2017–2024):** 5 **at-large** seats lettered **A–E**; the council elected
  its own chair; **no separate mayor**. The town conversion (2024) introduced the directly-elected
  mayor seat, first contested Nov 2025.
- **Staff/support:** legal counsel **Nathan Bracken**; clerk **Diana Baun**; economic-dev
  **Dan Torres** — all via **Greater Salt Lake MSD** (`msd.utah.gov/348`). Public safety by
  **UFA** (fire) + **UPD** (police). Roster page: `https://copperton.utah.gov/meet-copperton-council`.

---

## 3. Planning Commission — **Copperton has its OWN (nominal) PC, but it barely meets**

- **Own body exists:** **"Copperton Planning Commission" = PMN public body `1560`**
  (`https://www.utah.gov/pmn/sitemap/publicbody/1560.html`). Staff **Wendy Gurr,
  `wgurr@msd.utah.gov`** (MSD-staffed). Town site: `https://copperton.utah.gov/planning-and-zoning`.
- **Cadence:** nominally **1st Wednesday monthly** — but **most meetings are CANCELLED**
  (2026: Feb 4, Mar 4, Apr 1, May 6 all cancelled; **held** Jun 3 & Jul 1 2026). Land-use volume
  is tiny; long-range planning support runs through **MSD** (`ut-greatersaltlakemsd.civicplus.com/209/Long-Range-Planning`).
- **Vote format text-UNVERIFIED** this recon (no PC minutes doc parsed) — verify on the first held
  meeting's minutes. Expect very few substantive land-use actions.

---

## 4. Public comments — inline speaker notes only (submit-only / likely honest-empty)

- Minutes carry a **"COMMUNITY INPUT"** section and an **"Others Present:"** attendee list;
  public comment is taken **in person** at the monthly meeting (paraphrased in the minutes).
- **No standalone written-comment archive / eComment / correspondence page** located. Treat as
  **submit-only** → likely `all_comments_clean.csv` HONEST-EMPTY (auditor's final call at build).

---

## 5. Elections — Salt Lake County Clerk; canonical archive already local

- **Run by:** Salt Lake County Clerk. Town page: `https://copperton.utah.gov/election-information`.
- **Canonical file:** `~/Desktop/slco-election-archive/data/municipal_results_long.csv` — **98
  Copperton rows**. Filter on the **`contest`** column. Distinct Copperton contests present:

  | Year | contest | Genuine Council contest? |
  |---|---|---|
  | 2015 | `COPPERTON METRO TOWNSHIP-CITY` | ✗ incorporation ballot question (township-vs-city) |
  | 2015 | `COPPERTON MSD` | ✗ MSD-formation ballot question |
  | 2017 | `COPPERTON MT CNCL @ LRG` | ✓ Council at-large |
  | 2017 | `COPPERTON IMPROVEMENT DIST` | ✗ water/improvement-district board |
  | 2021 | `COPPERTON METRO TOWNSHIP COUNCIL AT-LARGE D` / `... E` | ✓ Council seats D, E |
  | 2023 | `COPPERTON METRO TOWNSHIP COUNCIL AT-LARGE A` / `B` / `C` | ✓ Council seats A, B, C |
  | 2023 | `COPPERTON IMPROVEMENT DISTRICT BOARD OF TRUSTEES AT-LARGE` | ✗ improvement district |

  → **Genuine Township/Town Council contests: 2017 (@LRG), 2021 (D, E), 2023 (A, B, C).**
  Seats are **at-large A–E**, staggered **A/B/C = 2019/2023 cycle**, **D/E = 2021/2025 cycle**.
- **Gaps / notes:**
  1. **2019 council (seats A/B/C prior term) — ABSENT** from the archive (same 2019 drop seen for
     South Jordan / Millcreek / Taylorsville). Re-parse raw 2019 SOVC if needed.
  2. **2025 town election NOT in this archive snapshot** — this is the **first race with a
     directly-elected MAYOR** (Clayton, unopposed) + council seats (McCalmon seat D, Pratt).
     Acquire from the 2025 SLCo SOVC / `electionresults.utah.gov`.
  3. **Exclude** the MSD, Improvement-District, and 2015 incorporation-question rows from council
     analysis.

---

## 6. GIS — UGRC municipal boundary (no council districts to derive)

- Copperton **is** in **UGRC `UtahMunicipalBoundaries`**: `NAME='Copperton'`, **`COUNTYNBR='18'`
  (Salt Lake)**, one polygon, geometry available.
  ```
  https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/UtahMunicipalBoundaries/FeatureServer/0/query?where=NAME='Copperton'
  ```
- **No sub-district geometry needed** — the council is **at-large** (no districts). An
  address→rep tool is trivial (whole-town = one body); a boundary polygon (town outline) is the
  only GIS artifact.

---

## Risks / blockers

- **City-site TLS mismatch (LOW, resolved):** `copperton.utah.gov` serves a `secureserversites.net`
  cert → **WebFetch fails**; use **`curl -k`/`http` + browser UA**.
- **Opaque doc URLs + JS-rendered listing (MEDIUM):** minutes live at non-guessable
  `img1.wsimg.com/blobby/...` GUIDs; the year-page listing is JS/JSON — **harvest anchors from the
  rendered DOM**, don't reconstruct URLs.
- **Pre-2023 minutes gap (MEDIUM):** the town site only goes back to **2023**; **2017–2022**
  metro-township minutes must come from **PMN body 5831's notice archive** (older notices exist but
  the publicbody sitemap page shows only the current year — enumerate the notice archive) or may be
  an honest recovery gap.
- **Form change mid-record (STRUCTURAL, resolved here):** metro township (2017–2024, at-large
  council, no mayor) → **Town (2024-05-01+, elected VOTING Mayor + 4 council, tally = 5)**. Model
  the mayor as a **voting member from 2024-05-01**; earlier there is no separate mayor.
- **Dissent format unconfirmed:** all sampled votes were 5-0 unanimous.
- **Election gaps:** 2019 council absent from the local archive; 2025 town election (first mayor
  race) not yet in it.

---

## Key URLs (quick index)

| What | URL |
|---|---|
| Town site (GoDaddy; cert mismatch, use curl -k) | https://copperton.utah.gov/ |
| Minutes year pages | https://copperton.utah.gov/2025-agendas-%26-minutes-1 (also 2023 / 2024-...-1 / 2026-agendas-%26-minutes) |
| Minutes doc pattern | https://img1.wsimg.com/blobby/go/07a53a68-a6f6-4bc0-a742-37221fdbac6f/downloads/&lt;guid&gt;/&lt;file&gt;.pdf?ver=&lt;n&gt; |
| Council roster page | https://copperton.utah.gov/meet-copperton-council |
| Election info | https://copperton.utah.gov/election-information |
| Planning & Zoning | https://copperton.utah.gov/planning-and-zoning |
| Municipal code | https://copperton.municipalcodeonline.com/ |
| PMN — Copperton Council (body 5831) | https://www.utah.gov/pmn/sitemap/publicbody/5831.html |
| PMN — Copperton Planning Commission (body 1560) | https://www.utah.gov/pmn/sitemap/publicbody/1560.html |
| PMN file pattern | https://www.utah.gov/pmn/files/&lt;fileId&gt;.pdf (+ .mp3 audio) |
| MSD — Copperton | https://msd.utah.gov/348 |
| Election archive (local) | ~/Desktop/slco-election-archive/data/municipal_results_long.csv (98 Copperton rows) |
| UGRC muni boundary | https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/UtahMunicipalBoundaries/FeatureServer/0 (NAME='Copperton', COUNTYNBR=18) |
| Confirmation minutes (saved) | meeting_minutes/raw/copperton_2025-07-16_minutes_DRAFT.pdf |

```json
{"vendor":"GoDaddy Website Builder (copperton.utah.gov on *.secureserversites.net; docs on img1.wsimg.com) — PRIMARY; Utah PMN 'Copperton Council' body 5831 = enumerable mirror (files utah.gov/pmn/files/<id>.pdf)","minutes_landing_url":"https://copperton.utah.gov/2025-agendas-%26-minutes-1 (year pages: 2023-agendas-%26-minutes, 2024-agendas-%26-minutes-1, 2025-agendas-%26-minutes-1, 2026-agendas-%26-minutes)","minutes_url_pattern":"https://img1.wsimg.com/blobby/go/07a53a68-a6f6-4bc0-a742-37221fdbac6f/downloads/<doc-guid>/<filename>.pdf?ver=<n> (opaque GUIDs, JS-rendered listing — harvest anchors); PMN mirror https://www.utah.gov/pmn/files/<id>.pdf","coverage_years":"town site 2023-2026 (2025 near-complete; Sep+Dec-2025 minutes missing from snapshot); pre-2023 (2017-2022 metro-township era) only via PMN body 5831 / possible gap; data floor 2017","format":"born-digital clean-text PDF (no OCR)","votes_in_minutes":true,"votes_style":"narrative tally — mover+seconder named + numeric 'vote was 5-0, unanimous in favor'; max tally 5 (Mayor + 4, ALL vote); per-member dissent-naming UNCONFIRMED (all samples unanimous)","has_own_pc":true,"pc_note":"nominal Copperton Planning Commission (PMN body 1560, MSD-staffed) but MOST meetings CANCELLED; ~1st Wednesday when held; land-use volume tiny; vote format text-unverified","council_weekday":"Wednesday","cadence":"monthly — 3rd Wednesday 6:30 PM, Bingham Canyon Lions Club (~11-12 mtgs/yr; occasional specials)","num_seats":5,"has_mayor":true,"mayor_note":"TASK-PREMISE CORRECTION: Copperton CONVERTED metro township -> TOWN on 2024-05-01. Town form = separately-elected VOTING Mayor + 4 Council Members = 5, mayor counted in every 5-0 tally. Metro-township era (2017-2024) had at-large seats A-E, council-elected chair, NO separate mayor.","current_members":["Mayor Sean Clayton (elected, voting; ran unopposed for Mayor Nov 2025)","Mayor Pro Tempore Tessa Stitzer","Council Member Kathleen Bailey","Council Member Linda McCalmon (seat D, re-elected 2025)","Council Member Jonathan Pratt (new 2025, succeeds Kevin Severson)"],"comments_published":"no standalone archive — in-person 'Community Input' + 'Others Present' inline speaker notes in minutes; submit-only / likely honest-empty","pmn_body_id":{"council":5831,"planning_commission":1560,"note":"body 5831 sitemap shows only current year; older via notice archive"},"gis_source":"UGRC UtahMunicipalBoundaries FeatureServer/0, NAME='Copperton', COUNTYNBR='18' (Salt Lake); ONE polygon; NO council districts (at-large seats) so no sub-district geometry to derive","data_floor":2017,"blockers":["city site TLS cert mismatch (secureserversites.net) -> WebFetch fails; use curl -k/http + browser UA","minutes at opaque GoDaddy wsimg GUIDs + JS-rendered listing -> harvest anchors, cannot guess URLs","pre-2023 minutes (2017-2022) not on town site -> PMN body 5831 notice archive / possible gap","governing form changed mid-record (metro township 2017-2024 -> Town 2024-05-01; mayor becomes a voting member from 2024)","dissent-naming vote format unconfirmed (all samples 5-0 unanimous)","2019 council election absent from local archive; 2025 town election (first Mayor race) not yet in it"],"confidence_notes":"Council minutes portal + PMN body + vote style + cadence + 5-member/voting-mayor structure + roster + GIS all CONFIRMED against a downloaded 2025 minutes PDF, PMN pages, the election archive, and UGRC live. NOT text-verified: a PC minutes doc; the dissent-naming format; the exact seat-letter mapping post-2024 town conversion; pre-2023 minutes availability on PMN."}
```
