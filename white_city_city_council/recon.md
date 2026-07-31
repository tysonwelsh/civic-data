# White City, Utah — Civic Data Recon

**Entity:** White City, **Salt Lake County**, Utah (~5,000 pop.)
**Recon date:** 2026-07-12
**Data floor:** **2017** (full modern history — see the incorporation note below; not a gap).
**⚠ Entity form CHANGED mid-record — this is the single most important fact here:**

- **2015:** SLCo voters approve creating **White City Metro Township** (SB199 metro-township
  regime) + a **Municipal Services District (MSD)** to deliver services. Seated **Jan 2017**.
- **2017 → Apr 2024:** governed as the **White City Metro Township** — a **5-member council,
  all at-large**, one of whom the council selects as **Chair**, and that chair carries the
  courtesy title **"Mayor"** (e.g. Paulina Flint, "Mayor, Chair" in 2021–2025 minutes). There
  was **NO separately-elected executive mayor** in this era — the "Mayor" was one of the five
  councilmembers and **voted as a member**. Services (police UPD, fire UFA, roads via WFWRD,
  planning long-range support) run through the **Greater Salt Lake MSD**.
- **2024:** **Utah HB35 (2024)** converted White City Metro Township to a **CITY effective
  May 1, 2024**, adopting a **mayor–council form of government**. (Confirmed in the 2026-05-07
  minutes: staff describe "the transition from an MSD to a city operating under a mayor-council
  form of government," with an ~8-month municipal-code rewrite underway.)
- **Nov 2025:** first **directly-elected Mayor** (Allan Perry) + council seats B & C. New
  council seated **Jan 2026**.

**Net effect:** across BOTH eras the governing body is **5 voting people** and the mayor/chair
**votes** (Millcreek-like, NOT the Taylorsville/South-Jordan non-voting-mayor form). What
changed is the *vote-recording format* (see §1). **This is a small entity — infrequent
monthly meetings, a tiny Streamline site — but the record is real and roll-call-bearing.**

**Official site:** `https://whitecity.utah.gov/` — **Streamline** CMS (getstreamline.com;
"Powered by Streamline" footer). Document PDFs are served from a **Cloudfront CDN** at the
pattern `https://whitecity.utah.gov/files/<hash>/<filename>.pdf`. Fetches succeed with a
**browser User-Agent** (curl browser UA worked live this recon; a legacy mirror also exists at
`whitecity.specialdistrict.org`).

> **⚠ DO NOT CONFUSE WITH THE WATER DISTRICT.** The **White City Water Improvement District**
> is a *separate* special district (its own elected board — Garry True, Dortha Robinson, etc.).
> The Township/City merely **rents the Water District's building** (999 E Galena Dr) as its
> meeting venue. Water-district election contests are a **decoy** (§5); its board is not this
> entity's council.

---

## 1. Council meeting minutes

### Portal — Streamline (single site, per-year document lists)
- **Host:** `https://whitecity.utah.gov`
- **Current-year landing:** `https://whitecity.utah.gov/council-meetings`
- **Older years:** `https://whitecity.utah.gov/council-meeting?year=<YYYY>` (2022, 2023, 2024,
  2025, 2026 all confirmed live) **plus** a pre-2022 bucket at
  `https://whitecity.utah.gov/meetings-archive` (holds **2017 agendas + 2018–2021 minutes**,
  and some early Planning-Commission docs mixed in).
- **Document URL pattern (Cloudfront-backed):**
  ```
  https://whitecity.utah.gov/files/<hex-hash>/<filename>.pdf
  ```
  Filenames are date-labeled and human, e.g. `09-04-2025+WC+Minutes+APPROVED.pdf`,
  `05-02-24+Minutes.pdf`, `06-01-23+Minutes.pdf`, `07-02-20+Minutes.pdf`. Hashes are opaque —
  **harvest the labeled `<a href>` links per year page; never guess the hash.** Each meeting
  day typically has **Agenda + Packet + Minutes(+ APPROVED) + an audio MP3** (`DS######.MP3`).
- **Coverage (confirmed by direct link harvest):**
  | Year | Minutes present | Note |
  |---|---|---|
  | 2017 | agendas only seen (`07-06-2017`, `05-04-2017`) | first council seated; earliest minutes are Jan 2018 |
  | 2018 | ~12 (`01-04-18`…`12-13-18`) | metro-township era |
  | 2019 | ~15 | |
  | 2020 | ~13 | |
  | 2021 | ~13 (`…12-09-21`) | last metro-township-only year |
  | 2022 | ~16 | |
  | 2023 | ~15 | |
  | 2024 | ~13 (transition to city on 2024-05-01 mid-year) | |
  | 2025 | ~14 (incl. `11-18-25 Canvass of Election Minutes`) | last year of Chair-as-Mayor (Flint) |
  | 2026 | ongoing (Jan+; new city era, Mayor Perry) | named roll calls begin |
- **PMN cross-check / fallback:** Utah Public Notice, **council body id 5805**
  (`https://www.utah.gov/pmn/sitemap/publicbody/5805.html` = "White City Council"). PMN also
  carries "White City Special Council Meeting" / "White City Budget Retreat" postings and older
  agendas (e.g. `utah.gov/pmn/files/465183.pdf` = 2019-02-07 agenda). Use PMN if a year page
  blocks or a meeting is missing.

### Format — born-digital clean-text PDF (NO OCR garble)
`pdftotext -layout` on 2021, 2023, 2025 and 2026 minutes yields clean, selectable text with
proper names intact. No RICOH/scan seam observed. Read parses directly.

### Meeting cadence — **Thursday, roughly monthly**
- **Regular council: 1st Thursday of the month, 6:00 PM** (workshop) rolling into the regular
  meeting (dates like 2026-04-02, 2026-05-07, 2026-06-04 are all first-Thursdays). This is a
  **low-frequency ~monthly** cadence (not twice-monthly) — plus **special/adjourned meetings**
  mid-month (budget retreats, canvass, code work — e.g. `2-27-2026 Special`, `6-12-2025
  Special`, `05-16-2024`). Metro-township minutes phrase this as "MET… PURSUANT TO ADJOURNMENT
  ON THURSDAY <prior date>."
- **Venue:** White City Water Improvement District building, **999 E Galena Drive, White City
  84094** (a rented room — see the water-district warning above). The city's mailing/admin
  address on the Streamline site is **860 W Levoy Drive, Taylorsville 84123** (that is the MSD
  admin office, a shared-services artifact — not a Taylorsville affiliation).

### Roll-call votes in minutes — CONFIRMED PRESENT, but **TWO FORMATS across a 2026 seam**
**⚠ Format seam ≈ Jan 2026** (coincides with the new city council seating under Mayor Perry):

1. **2017 – 2025 (metro-township + early-city): NARRATIVE-TALLY** (South-Jordan/Taylorsville-
   like). Mover + seconder named; outcome stated as a tally; **no per-member Aye/Nay list**.
   Attendance is a header block `COUNCIL MEMBERS PRESENT:` listing the 5 (incl. "X, Mayor").
   Verified quotes:
   > *(2023-06-01, metro township)* header lists **GREG SHELTON, PHILLIP CARDENAZ, ALLAN PERRY,
   > LINDA PRICE, PAULINA FLINT (Mayor)**; a motion reads *"…seconded by Council Member…,
   > motioned to [approve] the White City Metro Township financial report. The motion passed
   > unanimously."*
   > *(2025-09-04, still Chair-as-Mayor Flint)* *"Council Member Huish, seconded by Council
   > Member Shelton, motioned to accept the minutes of August 7, 2025. The motion passed by
   > unanimous vote."*
   → Per-member attribution here is limited to **mover + seconder + the attendance header**;
   the **contested/dissent naming format is UNCONFIRMED** (all sampled motions unanimous — pull
   a contested budget/land-use meeting before locking the parser).

2. **2026+ (city, Mayor-Council): FULL NAMED ROLL CALL** (Millcreek-like). Every motion prints
   a per-member Aye/Nay and **the Mayor votes**. Verified quote (2026-05-07, Resolution
   2026-05-02, FY2027 tentative budget):
   > *"Council Member Tyler Huish MOVED… SECONDED by Council Member Linda Price… he called for a
   > roll call vote. **Mayor Allan Perry — Aye; Council Member Neil Mahoney — Aye; Council Member
   > Greg Shelton — Aye; Council Member Tyler Huish — Aye; Council Member Linda Price — Aye.**
   > The motion passed unanimously."*
   → **Max council tally = 5 (Mayor + 4 members), the Mayor is a VOTING member.**

**Saved confirmation PDFs** (`meeting_minutes/raw/`): `2026-05-07`, `2026-04-02` (named-roll,
city era), `2025-09-04`, `2023-06-01` (narrative-tally, township era), `2021-10-21` (township
header sample).

---

## 2. Structure — 5-member voting body; the mayor VOTES (both eras)

**Current (city, seated Jan 2026):** a **directly-elected executive Mayor + 4 at-large
council seats (A–D)**. The Mayor **votes on every roll call** (confirmed §1). Roster
(from the 2026 minutes headers + `/city-council` page):

| Seat | Member | Note |
|---|---|---|
| **Mayor** (citywide, elected 2025) | **Allan Perry** | executive **and voting**; was a metro-township councilmember 2021–2025 |
| Seat A (elected 2023) | **Greg Shelton** | |
| Seat B (elected 2025) | **Linda Price** | councilmember since 2021 |
| Seat C (elected 2025) | **Neil Mahoney** | **Mayor Pro-Tem** |
| Seat D (elected 2023) | **Tyler Huish** | |

- **num_seats = 4 council + 1 mayor = 5-person voting body.** No districts — **all at-large**
  (lettered seats A–D; ballots label them "AT-LARGE B", "AT-LARGE C").
- **Staff (non-voting):** **Rori Andreason** (City Administrator, long-tenured through both
  eras), Cameron Platt (Attorney, Shiel Law), plus UFA/UPD/Sandy-Fire chiefs.
- **Prior-era roster drift (for term logic):** 2021 & 2023 council = Perry, Price, Cardenaz,
  Shelton/Little/Huish, with **Paulina Flint as Chair/"Mayor."** In 2025 Flint **lost** the
  mayoral race to Perry (and left), Mahoney beat incumbent **Phillip Cardenaz** for Seat C, and
  Scott Little rotated off. Track: **Flint(chair) → Perry(mayor); Cardenaz → Mahoney (2025)**.

---

## 3. Planning Commission — White City has its OWN PC (5th-member land-use body)

- **Own Planning Commission — YES.** `https://whitecity.utah.gov/planning-commission`. Members
  (per the page): **Christy Seiger-Webster (Chair), Christopher Spagnuolo, Lavon Huntsman
  Maiersperger**, + alternates **Henry Nahalewski, Ian Hazel** (terms to Feb 2028/2029).
- **Cadence:** **4th Thursday of each month** (per the site + the 2026 PC schedule PDF
  `/files/2271d7837/2026 White City Planning Commission Meeting Schedule.pdf`).
- **⚠ PC minutes/agendas publication is THIN / not on a dedicated page.** The PC page exposes
  only the **schedule PDF + the adopted General Plan**; it links out to the **Greater SL MSD
  "Long-Range Planning"** page (`msd.utah.gov/209/Long-Range-Planning`) for the planning
  support function. Historical PC docs appear **mixed into the general `meetings-archive`**
  (e.g. `2019.11.04_pc_wcmtc.pdf`, `2019.11.04_pc_packet.pdf`) rather than a clean PC minutes
  series. → **PC votes exist but the minutes must be harvested per-meeting (site + PMN); do not
  assume a tidy PC minutes archive.** Verify the PC vote-recording format on the first PC doc
  during acquisition (land-use recommendations → council; watch for MSD-routed items).
- **Adopted General Plan (April 2022):**
  `https://whitecity.specialdistrict.org/files/ea3ef2b51/White City General Plan Adopted April 2022.pdf`.

---

## 4. Public comments — in-meeting / submit-only; NO published written-comment archive

- Minutes carry a **"PUBLIC COMMENTS"** agenda item recording in-person speakers inline
  (clerk paraphrase, e.g. the 2023-06-01 resident complaint about park parking). These are
  **meeting-record speaker notes, NOT genuine published written comments** → if built, a
  labeled `minutes_speaker_log.csv`, never `all_comments_clean.csv`.
- **No eComment / Open City Hall / correspondence-received archive** surfaced on the Streamline
  site. Verdict: **HONEST-EMPTY / submit-only** (public comment taken in-person at meetings).
  Confirm during acquisition, then record the submit-only verdict in
  `public_comments/AVAILABILITY.md` (like Taylorsville / South Jordan).

---

## 5. Elections — Salt Lake County; existing archive covers 2015/2023/2025 (2017/19/21 GAP)

- **Run by:** Salt Lake County Clerk. Non-partisan, **all at-large** (no council districts).
- **Canonical source (existing shared archive):**
  `~/Desktop/slco-election-archive/data/municipal_results_long.csv` (the
  `slco_municipal_results_long.csv` the task references). **Filter on the `contest` column text
  `%WHITE CITY%` — then EXCLUDE the decoys below.**
- **White City TOWNSHIP/CITY contests present in the archive:**
  | Year | Contest(s) | Winners (from archive tallies) |
  |---|---|---|
  | 2015 | **WHITE CITY METRO TOWNSHIP-CITY** (incorporation ballot Q) + **WHITE CITY MSD** (services-district Q) | *ballot measures, not council races* — Metro-Township option 914>183; MSD **YES 961 / NO 142** |
  | 2023 | **WHITE CITY METRO TOWNSHIP COUNCIL AT-LARGE** (5 candidates) | top vote-getters **Paulina Flint (579), Greg Shelton (558), Tyler Huish (448)** > Van Horn (375), West (252) |
  | 2025 | **WHITE CITY MAYOR** + **COUNCIL AT-LARGE B** + **COUNCIL AT-LARGE C** | **Mayor: Allan Perry (740)** > Flint (456); **B: Linda Price (730)** > write-in Denning (307); **C: Neil Mahoney (635)** > Cardenaz (536) |
- **⚠ DECOYS to EXCLUDE** (`elections_decoys_to_exclude`):
  1. **`WHITE CITY WATER`** — the **White City Water Improvement District** board (2013 rows:
     Garry True, Dortha Robinson, Don McCaffree, Susan Muecke). A different special district —
     **never the township/city council.**
  2. **2015 `WHITE CITY MSD`** and **`WHITE CITY METRO TOWNSHIP-CITY`** — **ballot questions**
     (incorporation + services district), not candidate council races. Keep as historical
     context, but do NOT ingest as council contests.
- **⚠ ELECTION GAP:** the archive has **NO White City council races for 2017, 2019, or 2021**
  (the metro township's first cycles — seated 2017, staggered at-large seats elected 2019 &
  2021). Same failure mode seen elsewhere (numbered-sheet SOVC layout drops the entity string).
  → **re-parse the raw SLCo SOVC for 2017/2019/2021** to recover White City council contests
  before treating the election series as complete. Also flag the **2025 "AT-LARGE B/C" lettered
  seats** vs the **2023 single "AT-LARGE" multi-winner** contest so seat-term logic maps
  lettered seats correctly across the metro-township → city transition.

---

## 6. GIS — UGRC (Salt Lake CountyID 18); city boundary only (no districts)

- White City is now an **incorporated city** (2024) — it should carry a UGRC **Municipal
  Boundaries** polygon `NAME='WHITE CITY'`
  (`services1.arcgis.com/99lidPhWCzftIe9K/…/UtahMunicipalBoundaries/FeatureServer/0`); for the
  metro-township era its outline was the same footprint under the MSD.
- **No council districts** (all at-large) → **no district polygons needed**; an
  address→representative question is simply **in-White-City vs not** (the whole city elects the
  same mayor + 4 at-large members). For the precinct join / voter geography, UGRC
  **VistaBallotAreas / SLCo precincts CountyID = 18** (precincts SAN049/050/051 appear in the
  White City water rows) — same slco-election-archive precinct geometry used for the other SLCo
  cities.

---

## Retrieval plan (recommended order)

1. **Council minutes 2017→present (Streamline):** harvest labeled `<a>` links from
   `/council-meeting?year=<YYYY>` (2022–2026) + `/meetings-archive` (2017–2021) → curl each
   `/files/<hash>/…Minutes….pdf` (**browser UA**) into `raw/`. Keep the `…APPROVED`/signed
   variant when both draft + approved exist; drop agendas/packets/MP3s from the minutes index.
   Cross-check gaps against **PMN body 5805**.
2. **Vote extraction — TWO parsers across the ~Jan-2026 seam:** (a) 2017–2025 narrative-tally
   (mover+seconder+"passed unanimously"; attendance header for the 5 present; **verify dissent
   wording on a contested meeting**); (b) 2026+ named roll call (per-member Aye/Nay, **Mayor
   votes**, max tally 5). Both eras: **max tally = 5**.
3. **Planning Commission:** harvest per-meeting PC docs from the site + PMN (no clean archive);
   verify PC recommendation/vote format on the first doc; note MSD long-range-planning routing.
4. **Comments:** confirm no eComment portal → `AVAILABILITY.md` submit-only verdict; optional
   `minutes_speaker_log.csv` from the in-meeting PUBLIC COMMENTS sections.
5. **Elections:** reuse `~/Desktop/slco-election-archive` (`contest LIKE '%WHITE CITY%' AND
   contest NOT LIKE '%WATER%'`); **re-parse raw 2017/2019/2021 SOVC**; drop the 2015 ballot
   measures from council races; map lettered at-large seats.
6. **Geo:** UGRC municipal boundary `NAME='WHITE CITY'` (CountyID 18); no district layer needed
   (all at-large) — address→rep is citywide.

---

## Risks / blockers

- **Entity-form change mid-record (STRUCTURAL — resolved):** metro township (2017–2024) → city
  (2024-05-01, HB35) → first elected mayor (2025). **Both eras: 5 voting people, mayor/chair
  votes, max tally 5.** Model the "Mayor/Chair" of 2021–2025 as a **councilmember**, not a
  separate person.
- **Vote-format seam ≈ Jan 2026 (MEDIUM):** narrative-tally before, named roll call after —
  needs two parser modes; the **pre-2026 contested/dissent naming format is unconfirmed** (all
  sampled motions unanimous).
- **Water-district decoy (data-integrity):** exclude `WHITE CITY WATER` contests and the
  water-district board; the shared meeting venue (999 E Galena) is not a governance link.
- **Election gap 2017/2019/2021 (MEDIUM):** metro-township council races absent from the
  archive — raw SOVC re-parse required.
- **PC minutes not cleanly published (MEDIUM):** own PC exists (4th-Thursday) but minutes are
  scattered (site + PMN + MSD), not a tidy series — per-meeting harvest + format verification.
- **Small-entity sparsity (LOW, expected):** ~monthly meetings, tiny Streamline site — a thin
  but genuine record; honest gaps (e.g. an occasional workshop-only month) are data.
- **Streamline hashed URLs:** opaque `/files/<hash>/` paths — never guess; always harvest the
  labeled anchors per year page.

---

## Key URLs (quick index)

| What | URL |
|---|---|
| Official site (Streamline) | https://whitecity.utah.gov/ |
| Council meetings (current year) | https://whitecity.utah.gov/council-meetings |
| Council meetings by year | https://whitecity.utah.gov/council-meeting?year=2022 … 2026 |
| Pre-2022 archive (2017–2021) | https://whitecity.utah.gov/meetings-archive |
| Minutes doc pattern | https://whitecity.utah.gov/files/&lt;hash&gt;/&lt;M-D-YYYY&gt;+Minutes.pdf |
| Verified named-roll minutes (2026-05-07) | https://whitecity.utah.gov/files/0adf5cf17/5-7-2026+Minutes+APPROVED.pdf |
| Verified narrative-tally minutes (2025-09-04) | https://whitecity.utah.gov/files/f055c5004/09-04-2025+WC+Minutes+APPROVED.pdf |
| City Council page (roster) | https://whitecity.utah.gov/city-council |
| Planning Commission | https://whitecity.utah.gov/planning-commission |
| Adopted General Plan (2022) | https://whitecity.specialdistrict.org/files/ea3ef2b51/White+City+General+Plan+Adopted+April+2022.pdf |
| PMN council body (id 5805) | https://www.utah.gov/pmn/sitemap/publicbody/5805.html |
| Greater SL MSD — White City page | https://msd.utah.gov/352/White-City |
| Election archive (local) | ~/Desktop/slco-election-archive/data/municipal_results_long.csv (filter %WHITE CITY%, exclude %WATER%) |
| SLCo precinct geometry | ~/Desktop/slco-election-archive/geo/slco_precincts_current.geojson (CountyID 18) |

```json
{"vendor":"Streamline (getstreamline.com); PDFs on Cloudfront CDN at whitecity.utah.gov/files/<hash>/<file>.pdf; browser UA works; PMN body 5805 fallback",
 "minutes_landing_url":"https://whitecity.utah.gov/council-meetings (per-year: /council-meeting?year=YYYY ; pre-2022: /meetings-archive)",
 "minutes_url_pattern":"https://whitecity.utah.gov/files/<hex-hash>/<M-D-YYYY>+Minutes(+APPROVED).pdf — harvest labeled anchors, never guess the hash",
 "coverage_years":"2017-2026 (2017 agendas + 2018-2021 minutes in /meetings-archive; 2022-2026 in year pages; each meeting has Agenda+Packet+Minutes+audio MP3)",
 "format":"born-digital clean-text PDF (no OCR garble)",
 "votes_in_minutes":true,
 "votes_note":"TWO formats across a ~Jan-2026 seam: (a) 2017-2025 narrative-tally (mover+seconder named, 'passed unanimously', no per-member roll; dissent format unconfirmed); (b) 2026+ FULL NAMED ROLL CALL with per-member Aye/Nay. Mayor/Chair VOTES in BOTH eras. MAX TALLY = 5.",
 "has_own_pc":true,
 "pc_location":"OWN Planning Commission (Chair Christy Seiger-Webster; 4th-Thursday monthly) but minutes are NOT cleanly published — scattered on site + PMN + Greater SL MSD long-range-planning; harvest per-meeting and verify vote format",
 "council_weekday":"Thursday",
 "cadence":"~monthly: 1st Thursday regular council 6pm + occasional mid-month special/adjourned meetings; PC 4th Thursday",
 "num_seats":"5-person voting body = directly-elected Mayor + 4 at-large council seats (A-D); all at-large, no districts",
 "has_mayor":"YES since 2025 (directly-elected executive Mayor Allan Perry) — and the Mayor VOTES; 2017-2025 the 'Mayor' was the council-selected Chair (Paulina Flint), also a voting member",
 "current_members":["Mayor Allan Perry (voting)","Seat A Greg Shelton (2023)","Seat B Linda Price (2025)","Seat C Neil Mahoney - Mayor Pro-Tem (2025)","Seat D Tyler Huish (2023)"],
 "comments_published":"NO published written-comment archive — in-person/submit-only; minutes carry an in-meeting PUBLIC COMMENTS speaker log only (label minutes_speaker_log.csv, not all_comments_clean.csv)",
 "elections_decoys_to_exclude":["WHITE CITY WATER (White City Water Improvement District board — Garry True/Dortha Robinson/etc.)","2015 WHITE CITY MSD ballot question","2015 WHITE CITY METRO TOWNSHIP-CITY incorporation ballot question"],
 "elections_present":"archive municipal_results_long.csv: 2015 (measures), 2023 (council at-large, winners Flint/Shelton/Huish), 2025 (Mayor Perry; At-Large B Price; At-Large C Mahoney)",
 "elections_gap":"2017/2019/2021 metro-township council races ABSENT from the archive — re-parse raw SLCo SOVC",
 "gis_source":"UGRC Municipal Boundaries NAME='WHITE CITY' (now a city); Salt Lake CountyID=18; NO council districts (all at-large) -> address-to-rep is citywide; precincts SAN049/050/051",
 "data_floor":"2017 (metro township seated 2017 via 2015 vote; became a CITY 2024-05-01 via HB35; first elected mayor 2025) — full history, not a gap",
 "blockers":["entity-form change mid-record (township 2017-2024 -> city 2024) but mayor/chair votes in both eras, max tally 5","vote-format seam ~Jan 2026 (narrative-tally -> named roll call) needs two parser modes; pre-2026 dissent naming unconfirmed","EXCLUDE White City Water Improvement District decoy contests + shared 999-E-Galena venue is not a governance link","election gap 2017/2019/2021 - raw SOVC re-parse","PC minutes scattered (site+PMN+MSD), not a clean series","Streamline hashed /files/<hash>/ URLs - harvest anchors, don't guess"],
 "confidence_notes":"Council minutes portal/pattern/coverage, born-digital format, Thursday monthly cadence, 5-person mayor-voting body, own PC, comments submit-only, and the water-district decoy are all DIRECTLY CONFIRMED live (2026 named-roll + 2021/2023/2025 narrative-tally minutes downloaded and read; HB35 2024-05-01 city conversion confirmed). Pre-2026 contested-vote naming and the PC vote format are the two UNVERIFIED items; the 2017/2019/2021 election gap is confirmed absent."}
```
