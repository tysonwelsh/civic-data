# Ogden, Utah (Weber County) — Civic-Data Recon

**Recon date:** 2026-06-25. Scope: 2020–present. City form: **Mayor–Council (strong-mayor) since 1992**.
Full-time Mayor (executive) + part-time 7-member Council (legislative). **Mayor does NOT vote on
Council motions** (confirmed in minutes — Mayor listed under "Also present," never in vote tallies).

---

## 1. Council meeting minutes

### Vendor / hosting — TWO systems, both CivicPlus-family
Ogden's website is **CivicPlus / CivicEngage** ("Government Websites by CivicPlus®"). Minutes
are surfaced two ways; **use the DocumentCenter, not the AgendaCenter** (disk lesson below).

- **Primary minutes hub (USE THIS):**
  `https://www.ogdencity.gov/2698/Approved-Minutes-for-City-Council-Redeve`
  Title: *"Approved Minutes for City Council, Redevelopment Agency, and Municipal Building Authority."*
  Links resolve to **DocumentCenter** PDFs:
  - **2024–2026:** individual per-meeting minutes PDFs.
    Pattern: `https://www.ogdencity.gov/DocumentCenter/View/<ID>/<MM-DD-YY>-CC`
    Verified example (Jan 6 2026 regular mtg): `https://www.ogdencity.gov/DocumentCenter/View/37178/01-06-26-CC`
    Suffix `-CC` = City Council; RDA and MBA have their own suffixes.
  - **2010–2023:** **annual COMPILATION PDFs** (one big PDF per year, all CC meetings concatenated).
    Pattern: `https://www.ogdencity.com/DocumentCenter/View/<ID>/CC-<YEAR>` (e.g. `.../28029/01-02-24-CC` style for per-mtg; `CC-2023` for the yearly roll-up).
    → For 2020–2023, retrieval = grab the four annual PDFs and split by the "Minutes of … Meeting of
      Council of Ogden City, Utah, <DATE>" header that starts each meeting.

- **Secondary (CivicPlus AgendaCenter) — host alias `brand.ogdencity.com` (and `ut-ogden.civicplus.com`):**
  `https://brand.ogdencity.com/AgendaCenter` — City Council category present.
  Minutes ViewFile pattern: `/AgendaCenter/ViewFile/Minutes/_<MMDDYYYY>-<ID>`
  (e.g. `/AgendaCenter/ViewFile/Minutes/_04222026-1719`).
  **Coverage here is patchy** (2024, 2020, 2019…2013 with gaps in 2021–2023) AND the AgendaCenter
  also serves giant agenda **packets**. The DocumentCenter "Approved Minutes" page is cleaner and
  more complete for minutes. Keep AgendaCenter only as a backfill for any DocumentCenter gap.

> **DISK LESSON:** Do NOT bulk-pull the AgendaCenter — it bundles multi-hundred-page agenda packets
> alongside minutes. The DocumentCenter `.../View/<ID>/<date>-CC` files are minutes-ONLY. For
> pre-2024, take the four annual compilation PDFs (small, minutes-only) rather than packets.

### Domain quirk (handle in scraper)
`www.ogdencity.com` **301-redirects to `www.ogdencity.gov`** (cross-host). Some council pages live on
`council.ogdencity.com`. WebFetch returns the redirect instead of following it — the retrieval scraper
must follow 301s and normalize `.com`→`.gov`. CivicPlus internal alias surfaced as `ut-ogden.civicplus.com`.

### Years of MINUTES available
**2010 → 2026 (present).** In-scope 2020–present fully covered:
- 2024–2026: per-meeting PDFs.
- 2020–2023: annual compilation PDFs (split needed).

### Meeting cadence / weekday
- **Formal/regular Council meetings: 1st and 3rd TUESDAYS, 6:00 p.m.**, Council Chambers, 3rd floor,
  Municipal Building, 2549 Washington Blvd, Suite 340 (also electronic/hybrid).
- **Work sessions: most Tuesdays, 4:00 p.m.**, Conf. Room 310 (less likely to have formal votes).
- Council also sits as **RDA (Redevelopment Agency)** and **MBA (Municipal Building Authority)** —
  same body, separate minutes; capture CC primarily, RDA/MBA optionally.

### Format & votes-in-minutes — CONFIRMED EXCELLENT
Opened **Jan 6 2026 regular meeting minutes** (View/37178). **Born-digital text-layer PDF** (Word→PDF,
clean `pdftotext`/Read extraction; NOT scanned). Roll-call votes ARE in the minutes, two phrasings —
parser MUST handle both:
- **Inline prose (consent/unanimous):** `COUNCIL MEMBER RICHEY MOVED TO … MOTION WAS SECONDED BY
  COUNCIL MEMBER GRAF, ALL VOTING AYE.` → captures mover + seconder; "ALL VOTING AYE" = unanimous
  (fill ayes from the attendance "Present:" block; set names_recorded accordingly).
- **Named roll-call (contested):** `THE FOLLOWING ROLL CALL VOTE WAS TAKEN … VOTING AYE – COUNCIL
  MEMBERS CHOBERKA, GRAF, HYER, MYERS, AND RICHEY. VOTING NO – COUNCIL MEMBERS LUNDELL AND
  WASHINGTON.` → full per-member Aye/Nay lists (a real contested 5–2 vote captured).
- Attendance roster at top (`Present: Chair … Council members …`) gives the canonical member list per
  meeting; Mayor/staff under "Also present" — exclude from vote lists.
- Public "Public Comments" section = **clerk paraphrase of in-person speakers** (3rd person) — NOT
  genuine written comments (see §3); route to a speaker-log only, never to the comments dataset.

---

## 2. Council structure

- **7 members: 4 DISTRICT seats (District 1–4) + 3 AT-LARGE seats (Seat A, B, C).**
- **4-year terms, staggered:** the 4 district seats one odd cycle; the 3 at-large seats + Mayor the
  next odd cycle. (So 2021/2025 = one group, 2023 = the other — confirm exact split from results.)
- Non-partisan elections, odd years, November (primary in August if >2 candidates).
- **Strong-mayor:** Mayor is full-time executive and **does not vote** on Council legislation.

### Current members + seats (as of Jan 2026; in transition)
| Member | Seat |
|---|---|
| Richard A. Hyer | District 2 (Council **Chair**) |
| Dave Graf | District 4 (Vice Chair) |
| Flor Lopez | District 1 (sworn in 2nd week of Jan 2026, replacing Angela Choberka) |
| Ken Richey | District 3 |
| Alicia Washington | At-Large Seat A |
| Kevin Lundell | At-Large Seat B |
| Shaun Myers | At-Large Seat C |

Mayor: **Benjamin K. Nadolski**. (Jan 6 2026 minutes still list **Angela Choberka** as the District-1
member finishing her term — the meeting captured the Choberka→Lopez handoff; account for roster change
mid-corpus when normalizing names.)

Source pages: `https://www.ogdencity.gov/717/About-the-Council`,
`https://www.ogdencity.gov/157/City-Council-Members`, `https://www.ogdencity.gov/2274/City-Council`.

---

## 3. Public comments

**Verdict so far: UNCLEAR — lean "submitted-but-publication-unconfirmed."** Do NOT conclude unavailable.

Ogden HAS a genuine public-input intake (not just in-person speakers):
- **Public Comment Submission Form:** `https://www.ogdencity.com/publicinput` (→ redirects to `.gov`).
  "Ways to Comment": `https://www.ogdencity.gov/736/Ways-to-Comment`.
  Form + voicemail line **801-629-8158** + email **citycouncil@ogdencity.com**. Per the city: *"Submitted
  forms and messages will be forwarded to the City Council and entered into the record of the next Council
  Meeting."* → genuine written comments exist; question is whether the **verbatim text is published**.
- **FlashVote survey tool:** `https://www.flashvote.com/ogdenut` (topic surveys; structured sentiment,
  not free-text council comments — secondary at best).

Hunt order still to run during retrieval (per extraction_standards §"What counts"):
1. Whether submitted forms appear **verbatim** as a "written public comments" / "correspondence"
   attachment in the **AgendaCenter agenda packet** for each meeting (most likely home — CivicPlus packets
   often bundle "Public Comments Received"). Check a recent packet's attachment list.
2. Whether the **DocumentCenter** has a "Public Comments Received" doc per meeting alongside `-CC` minutes.
3. Any dedicated comments archive page (none found yet).
4. Council correspondence / records request as last resort.

If after 1–4 only the clerk paraphrase exists, record "no genuine written comments published" in
AVAILABILITY.md and keep an in-person **speaker log** (date/name/topic) clearly labeled NON-comment.

---

## 4. Elections — Weber County (#29 / UGRC CountyID 29). **No existing Desktop archive** (counties.csv row 29 = empty source).

### Primary source — Weber County Elections (BEST: born-digital precinct PDFs)
- Elections home: `https://www.weberelections.gov/` ; results index: `https://www.weberelections.gov/electionsresults`
- Files are **Wix-hosted PDFs** under `weberelections.gov/_files/ugd/92078f_<hash>.pdf` that **301-redirect**
  to `https://48b2f845-13b3-4f2f-b3f5-69e2f977e226.filesusr.com/ugd/92078f_<hash>.pdf` — follow the redirect.
- **VERIFIED 2025**: *"Precinct Level Results Report / OFFICIAL CANVASS RESULTS — WEBER COUNTY"*,
  born-digital text PDF, **one section per precinct** (`29CN01`, `29OG##`, …) with Statistics
  (Registered/Ballots/Turnout) + each contest "Vote For N" + per-candidate TOTAL & VOTE%. 175 pages;
  Ogden Council District/At-Large contests appear on the Ogden (`29OG##`) precinct pages.
  - 2025 General precinct: `…/92078f_dc2ffea70dfb409aa3f2b615a678de4b.pdf`
  - 2025 General summary: `…/92078f_ba3a3d05a36449399444d85e915efa14.pdf`
  - 2025 Primary (Ogden Valley shown; check for Ogden City primary too): summary
    `…/92078f_befa9cafc5074d28b0ef897e57fdd947.pdf`, precinct `…/92078f_5ce3b1da58b3441c88d62ef05195addc.pdf`
- **2023:** index showed County Bond summary `…/92078f_1fb5ef99870440ad9f74b83a435699ab.pdf` + precinct
  `…/92078f_def2370870034f6e9ad3b933d2f2a383.pdf`. **Must locate the 2023 MUNICIPAL general** (Ogden
  council seats) PDF on the index — not all 2023 files surfaced in one fetch; re-scrape the full page.
- **2021:** General Election PDF `…/7dc173_05b2df57deb54c439e8964cd6184e90c.pdf` (note different ugd
  prefix `7dc173` — older bucket).
- **2020:** index references a "G20 SOVC" file.
> Filenames are opaque hashes — scrape the results-index page link text to map hash→election/year, then
> curl each (following the filesusr redirect). Precinct prefix `29OG` = Ogden City precincts.

### Secondary / cross-check — Utah state portal (Enhanced Voting)
- `https://electionresults.utah.gov/` → per-county pages, e.g.
  `…/results/public/weber-county-ut/elections/general11042025`,
  `…/elections/primary08122025`, and 2023 `…/webercountyutah/elections/2023-Nov-General`.
- Backend is **Enhanced Voting** (`app.enhancedvoting.com/results/public/<county>/elections/<slug>/ballot-items/<uuid>`).
  Pages are **JS-rendered → empty to WebFetch**; need the JSON API (discover exact path via browser
  network tab during retrieval — a guessed `/results/api/.../<slug>` 404'd). Per-race precinct detail
  exists; "Media Export" feature present. **Treat as fallback/cross-check; the county PDFs are primary.**
- 2023 example ballot-item seen: "ogden city council at-large seat c" → confirms **A/B/C at-large
  naming** and **District N** for district seats in the contest labels.

### District-based?  **YES** — 4 districts + 3 at-large (model BOTH; not purely at-large).

---

## 5. GIS

### Statewide precincts — UGRC Vista Ballot Areas (FeatureServer)
- **Endpoint:** `https://services1.arcgis.com/99lidPhWCzftIe9K/ArcGIS/rest/services/VistaBallotAreas/FeatureServer/0`
- **CountyID=29 (Weber): 153 features VERIFIED.** PrecinctIDs like `29OG15` (Ogden), `29CN05`, `29RY10`.
  Some variant/sub-precinct suffixes (`:X`,`:H`,`:B`,…) and a dup (`29CN05`) — dedupe on import.
  - Query: `…/FeatureServer/0/query?where=CountyID=29&outFields=*&outSR=4326&f=geojson`
  - **CRS GOTCHA (from playbook):** request `outSR=4326` and verify coords ≈ (-111.9, 41.2) lon/lat,
    NOT meters. (Native SR returned was Web Mercator 3857.) Re-set/reproject before point-in-polygon.

### Ogden CITY GIS — authoritative council-district map (PREFER THIS)
- City ArcGIS server: `https://arcgis.ogdencity.com/arcgis/rest/services` (folders: Public, EnerGov, …).
- **`Public/Ogden_Voting_Precincts` (FeatureServer/0)** — **41 Ogden precincts**, field **`MUNIWARD`**
  (SmallInteger) = the **council district**. **Distinct MUNIWARD = 1,2,3,4** → confirms 4 districts.
  Counts: Ward 1=11, Ward 2=8, Ward 3=10, Ward 4=12 precincts. Other fields: `PRECINCT`, `CONSOL_PRE`,
  `POLLING_PL`, `ADDRESS`. **This is the precinct→district authority for the address tool.**
  - `…/Public/Ogden_Voting_Precincts/FeatureServer/0/query?where=1=1&outFields=*&outSR=4326&f=geojson`
- The 3 **at-large** seats are citywide (no sub-geometry) → address tool returns district 1–4 +
  notes all 3 at-large seats apply citywide.
- `Public/AdministrativeAreas` MapServer = only a "Public Notification" layer (no council districts).
- Public district lookup app: `https://ogdencity.gov/211/Municipal-District-Map` (Esri Instant App;
  human-facing) and boundaries app `arcgis.com/apps/instant/lookup/index.html?appid=d1cb36845f2e45d88c4fd5eb101d33d2`.
- Reconcile naming: GIS Ogden `PRECINCT` (e.g. `OG15`) ↔ election/UGRC `29OG15` (CountyID prefix).

---

## Retrieval plan (recommended order)

1. **Minutes 2024–2026 (per-meeting):** scrape `…/2698/Approved-Minutes…` for `DocumentCenter/View/<ID>/<date>-CC`
   links (follow .com→.gov 301s); curl each PDF → `raw/minutes/`. Read (text layer) → markdown.
2. **Minutes 2020–2023 (annual compilations):** grab the 4 `CC-<YEAR>` annual PDFs; split on the
   "Minutes of … Meeting of Council of Ogden City, Utah, <DATE>" header into per-meeting files.
3. **Vote extraction:** per meeting → JSON. Handle BOTH phrasings (inline "ALL VOTING AYE" w/ mover+seconder;
   named "VOTING AYE – …/VOTING NO – …" roll-call). Flatten across page-break footers ("Page __").
   Normalize member names (watch Choberka→Lopez 2026 handoff). Mayor excluded from vote lists.
4. **Public comments:** inspect a recent **AgendaCenter packet** + DocumentCenter for a published
   "written public comments / correspondence" attachment; check `publicinput` form output. Only then verdict.
5. **Elections:** scrape `weberelections.gov/electionsresults` link text → map hashes to 2021/2023/2025
   municipal General (+ Aug primaries); curl `_files/ugd/...` PDFs (follow filesusr redirect) → `raw/elections/`.
   Read precinct PDFs; filter to `29OG` precincts + Ogden Council (Dist 1–4) & At-Large (A/B/C) & Mayor.
   Cross-check totals vs state Enhanced Voting portal.
6. **GIS:** pull `Ogden_Voting_Precincts` (MUNIWARD) as `geo/precincts.geojson` (district authority);
   pull UGRC CountyID=29 as a backup/statewide layer. Build `precinct_to_district.csv` from MUNIWARD.
   Build `address_to_district.py` (Census geocode → point-in-polygon vs Ogden precincts → MUNIWARD;
   at-large seats flagged citywide).

## Risks / blockers
- **Domain redirects** (`ogdencity.com`→`.gov`, `weberelections.gov`→`filesusr.com`): scraper MUST
  follow cross-host 301s (WebFetch did not).
- **2020–2023 minutes are annual mega-PDFs** — need reliable per-meeting splitting (header regex).
- **Election filenames are opaque Wix hashes** — must derive year/type from the index page's link text;
  some 2020/2023 municipal files didn't surface in a single fetch — re-scrape full index.
- **State portal is JS-only** — needs Enhanced Voting JSON API (path TBD via network inspection); kept
  as secondary since county PDFs are primary.
- **Public-comment publication unconfirmed** — intake form exists, but verbatim-publication not yet located.
- **Roster change mid-2026** (Choberka→Lopez, D1) and Chair/Vice-Chair annual re-election — name-normalize.
- UGRC GeoJSON CRS mislabel risk; dup precinct `29CN05`; sub-precinct suffixes — dedupe/verify outSR.
