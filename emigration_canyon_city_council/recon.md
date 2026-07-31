# Emigration Canyon, Utah — Civic Data Recon

**Entity:** Emigration Canyon, **Salt Lake County**, Utah (~1,600 residents — a small
canyon community east of Salt Lake City, up Emigration Canyon Rd.)
**Recon date:** 2026-07-12
**Scope of interest:** 2017–present (**data floor 2017** — full history).
**Form of government — CHANGED (key finding):** Emigration Canyon was incorporated as an
**Emigration Canyon Metro Township** (voters approved metro-township status Nov 2015;
effective **Jan 1, 2017**), and then **converted from a Metro Township to a CITY effective
May 1, 2024** (per **H.B. 35**, 2024 Utah Legislature — confirmed on the official site and
by the 2026 minutes/agendas all titled "**Emigration Canyon City Council**"). The 2025
municipal election contest is already labeled "**CITY OF EMIGRATION CANYON COUNCIL
AT-LARGE**." → The repo directory name `emigration_canyon_city_council` is correct; treat it
as a **city since 2024-05-01**, a **metro township 2017–2024**, both governed by the same
5-member body.
**Governing form throughout:** a **5-member council**, all elected **AT-LARGE** (no
districts), **one of whom is selected by the other members to serve as Mayor** (Utah's
five-member "metro-township / small-city council" form). → **The Mayor is one of the five,
PRESIDES, and VOTES.** **Max council tally = 5** (this is the **Millcreek pattern — mayor
votes and is counted in the 5**, NOT the Taylorsville/South-Jordan executive-mayor pattern).
Confirmed against a real minutes doc in §1: **Mayor David Brems both moves motions and is
counted in the "5-0" tally.**
**Official site:** `https://emigration.utah.gov/` (the older `https://www.ecmetro.org/`
**301-redirects** to it; a legacy `emigrationcanyon.org` "Community Council" site is a
separate historical/advocacy entity — do NOT treat as the government). Government
administrative services (recorder, land-use staff, engineering) are provided by the
**Greater Salt Lake Municipal Services District (MSD)** — the City Recorder is
**Diana Baun** (`dbaun@msd.utah.gov`), an MSD employee.

> ⚠ **DO NOT CONFUSE with the Emigration Canyon Improvement District** (a separate special
> district providing sewer/water). It runs its own elected Board of Trustees and appears in
> the election data and on PMN under names like "EMIGRATION IMPROVEMENT",
> "EMIGRATION IMPROVEMENT DIST", "EMIGRATION IMPROVEMENT DISTRICT BOARD OF TRUSTEES." Those
> are **NOT** Township/City Council seats. See §6.

---

## 1. Council minutes — published on **Utah Public Notice (PMN)**, not a city CMS

There is **no city-hosted document CMS** (no CivicPlus/Granicus/Legistar). The
**canonical, re-fetchable source is Utah Public Notice (PMN)**; the MSD **AgendaCenter**
(`msd.utah.gov`) is a secondary mirror.

### Portal — Utah PMN, council body id **5809**
- **Body page (enumerate here):**
  `https://www.utah.gov/pmn/sitemap/publicbody/5809.html`
  ("Emigration Canyon Council", Public Body Type = **City Council**; contact Diana Baun,
  MSD). Full-archive listing: `https://www.utah.gov/pmn/list/notices.html?id=5809`
  (⚠ this list endpoint intermittently 500s / "technical difficulties" — retry; the sitemap
  page reliably renders the recent notices).
- **Each meeting notice** carries links to **Agenda**, **Approved Minutes**, **Supporting
  Docs/packet**, and often an **Audio Recording (.MP3)**.
- **Document URL pattern (PMN file store):**
  ```
  https://www.utah.gov/pmn/files/<fileId>.pdf        (agenda / minutes / supporting docs)
  https://www.utah.gov/pmn/files/<fileId>.MP3        (audio)
  ```
  fileIds are **non-sequential / non-guessable** — harvest the labeled links off each
  notice, do not synthesize ids.
- **Coverage:** current cycle richly covered on body 5809 (2026 verified live). Township-era
  minutes 2017→2024 should also be on PMN — **enumerate the full `list/notices.html?id=5809`
  archive at acquisition** to confirm the earliest date, with MSD AgendaCenter as fallback
  for any gap. **Data floor = 2017** (metro-township incorporation).
- **MSD AgendaCenter (secondary mirror):** `https://www.msd.utah.gov/` →
  `https://www.msd.utah.gov/AgendaCenter` (community pages `msd.utah.gov/349/Emigration-Canyon`
  and `/217/Emigration-Canyon-Metro-Township`).

### Verified sample — **2026-05-19 City Council minutes**
Downloaded to `meeting_minutes/raw/emig_minutes_1456089.pdf`
(`https://www.utah.gov/pmn/files/1456089.pdf`). Also grabbed the 2026-04-21 regular minutes
(`.../1447787.pdf` → `raw/emig_minutes_1447787.pdf`, an 8.7 MB doc with embedded packet).

- **Format — CONFIRMED born-digital clean text PDF** (DocuSign-signed; `pdftotext -layout`
  yields clean, selectable text; proper names intact). **No OCR garble.** `format=pdf-text`.
- **Council Members Present (the current 5):** *"Mayor David Brems, Council Member Nicholas
  Griffith, Council Member Catherine Harris, Council Member Jennifer Hawkes, Council Member
  Robert Pinon."* Staff: City Recorder Diana Baun, City Attorney Cameron Platt, Land-Use
  Legal Counsel Claire Gillmor, Asst. City Engineer Tamaran Woodland (all MSD/contract).

### Roll-call votes in minutes — **CONFIRMED PRESENT (narrative-tally style)**
Motions record **mover + seconder + a narrative tally**, e.g. (verbatim, 2026-05-19):
> *"Council Member Griffith moved to approve Resolution R2026-10, Approving the Emigration
> Canyon Tentative Budget for FY2026-27. Council Member Harris seconded the motion; **vote
> was 5-0, unanimous in favor.**"*

and
> *"**Mayor Brems moved to adjourn** the City Council Meeting at 10:38 pm. Council Member
> Griffith seconded the motion; **vote was 5-0, unanimous in favor.**"*

- **This is South-Jordan / Taylorsville-like NARRATIVE TALLY**: mover & seconder are named,
  the outcome is a printed count ("vote was 5-0"), and there is **no per-member Aye/Nay
  roll-call list** on unanimous motions (the majority is honestly **unnamed**). → On a
  unanimous motion a blank member list is the source style, **not** missing extraction.
- **The Mayor is a full voting member** — Brems moves motions and the tally is **5-0**
  (5 = all members incl. the mayor). **Max tally = 5, mayor VOTES** (Millcreek pattern).
- ⚠ **Dissent-naming format UNCONFIRMED** — every motion in the sample was unanimous. With a
  5-member body a split likely prints as *"vote was 4-1, Council Member X opposed"*; verify
  on the first contested motion before bulk extraction.
- **Meeting title convention:** a same-day **Workshop Meeting (6:00 PM)** + **Regular City
  Council Meeting (7:00 PM)** are posted as **separate notices/minutes docs** (unlike
  Taylorsville's single combined doc) — index both.

---

## 2. Council structure — 5 at-large members, mayor selected by peers (mayor VOTES)

- **5 council members, all elected AT-LARGE** (no wards/districts). 4-year staggered,
  non-partisan terms; roughly half the seats up each odd-year cycle. The council **selects
  one of its own to serve as Mayor** (David Brems) — the Mayor presides but remains a
  **voting** member. **No separately-elected mayor; no city administrator** (admin via MSD).
- **Current roster (from the 2026-05-19 minutes header + 2023/2025 election winners):**

  | Seat | Member | Role | Elected |
  |---|---|---|---|
  | At-large / **Mayor** | **David (Paul) Brems** | Mayor (presides, votes) | 2023 |
  | At-large | **Catherine M. Harris** | Council Member | 2023 |
  | At-large | **Jennifer Hawkes** | Council Member | 2023 |
  | At-large | **Robert ("Roberto") Pinon** | Council Member | 2025 |
  | At-large | **Nicholas Griffith** | Council Member | 2025 (or appointed) |

  (2023 winners: Harris, Brems, Hawkes, + Tyler Tippetts; 2025 winners drawn from Wheelock/
  Steed/Pinon/Posner — reconcile Griffith's seat vs Tippetts at acquisition; one 2023 seat
  turned over by 2026.)
- Governance page: `https://emigration.utah.gov/` (Government / Council). Mayor contact
  `dbrems@emigration.utah.gov`.

---

## 3. Planning Commission — **Emigration Canyon has its OWN PC** (PMN body **1562**)

- **Own Planning Commission** (land-use is NOT wholly delegated to the county — the canyon's
  wildfire/watershed/slope land-use issues make it active). Minutes & agendas on PMN:
  - **Body page:** `https://www.utah.gov/pmn/sitemap/publicbody/1562.html`
    ("Emigration Canyon Planning Commission").
  - **Doc pattern:** same `https://www.utah.gov/pmn/files/<fileId>.pdf`; filenames follow
    `YYMMDD_EmigrationPC_MinutesApproved.pdf` / `_Agenda.pdf` (born-digital).
  - **Recent minutes verified live:** 2026-06-11 (`/files/1459781.pdf`), 2026-05-14
    (`/files/1459779.pdf`), 2026-03-12 (`/files/1447525.pdf`), 2026-02-12 (`/files/1404213.pdf`).
- **Cadence:** roughly **monthly, ~2nd week** (2026 meetings fell 2/12, 3/12, 4/15, 5/14,
  6/11, 7/9 — mixed Wed/Thu; treat as monthly, confirm weekday per-year).
- **Votes/recommendations — expected recorded** (same MSD clerk shop; a PC minutes doc was
  not text-verified this recon — spot-check the first PC file's vote/recommendation grammar;
  expect the same narrative-tally + PC→Council recommendation language, with small-body named
  rolls likely).

---

## 4. Cadence (Council)

- **City Council: 3rd Tuesday of the month, 7:00 PM** (a Workshop at 6:00 PM precedes some
  meetings). Location: **Unified Fire Authority Station 119, 5025 E Emigration Canyon Rd,
  Salt Lake City, UT 84108** (the canyon fire station). Monthly, not bi-weekly.
- **`build_weeks.py` join key: MEETING_WEEKDAY = Tuesday (= 1).**

---

## 5. Public comments — inline speaker notes only (most likely SUBMIT-ONLY / honest-empty)

- **No standalone written-comment archive / eComment / correspondence portal** exists. The
  minutes carry a **`PUBLIC COMMENTS`** section that **paraphrases in-person speakers**
  (verified 2026-05-19: resident *Willie Stockman* on the watershed plan, green-waste
  dumpsters, WFWRD; *Emma Andreason* in "Others Present"). Per extraction standards these are
  **meeting-record speaker notes, NOT genuine written comments** → if captured, a labeled
  `minutes_speaker_log.csv`, never `all_comments_clean.csv`.
- **Verdict: treat as HONEST-EMPTY / submit-only** unless a correspondence archive surfaces
  in the PMN "Supporting Docs" packets (grep packet PDFs at acquisition before finalizing).
  Public comment is taken **in-person** at meetings (audio recordings posted on PMN).

---

## 6. Elections — Salt Lake County; existing archive covers it (44 genuine township rows)

- **Run by:** Salt Lake County Clerk (non-partisan, all AT-LARGE). Live official results:
  `https://electionresults.utah.gov/` (Salt Lake County).
- **Existing shared archive already covers Emigration Canyon:**
  `~/Desktop/slco-election-archive/data/municipal_results_long.csv`. **Filter on the
  `contest`/`sheet` TEXT, and KEEP ONLY genuine Township/City-Council contests** (exactly
  **44 rows**, matching the ~44 expected):

  | Year | Genuine contest (KEEP) | Candidates | rows |
  |---|---|---|---|
  | 2015 | `EMIGRATION CYN METRO TWNSHP-CTY` | *incorporation choice:* "Emigration Cyn Metro Township" (594) vs "Emigration Canyon City" (16) → **township chosen** | 10 |
  | 2017 | `EMIGRATION CANYON MT CNCL @ LRG` | Joe Smolka, Gary Bowen | 10 |
  | 2023 | `EMIGRATION CANYON METRO TOWNSHIP COUNCIL AT-LARGE` | Catherine M Harris, David Paul Brems, Jennifer Hawkes, Tyler Tippetts | 16 |
  | 2025 | `CITY OF EMIGRATION CANYON COUNCIL AT-LARGE` | Dillon Wheelock, Jacob Steed, Roberto Pinon, Zachary Posner, (Unresolved Write-In) | 8 |

- **⚠ DECOYS — EXCLUDE (Improvement District = sewer/water special district; + the MSD
  ballot question):**
  - 2015 `EMIGRATION IMPROVEMENT` (White, Hughes, Staggers, Irons, Bradford)
  - 2017 `EMIGRATION IMPROVEMENT DIST` (Bob Staggers, Brent Tippets)
  - 2021 `EMIGRATION IMPROVEMENT DISTRICT BOARD OF TRUSTEES AT-LARGE` (Brent R. Tippets, Steve Newton)
  - 2015 `EMIGRATION CANYON MSD` (a **YES/NO ballot question** on Municipal Services District
    formation, not a council seat)
- **⚠ Election coverage gaps to note (not defects to fabricate):** the archive shows **no
  Township *council* contest in 2019 or 2021** — only the Improvement District ran in 2021.
  This is plausibly real (staggered at-large seats not up, or uncontested/omitted). Confirm
  against certified SLCo results at acquisition; do NOT invent rows.
- **2015 is an incorporation referendum**, not a council seat — model it as the incorporation
  event, not a member term. **Name normalization:** election names are UPPER-CASE
  (`ROBERTO PINON`→ Robert Pinon; `DAVID PAUL BREMS`→ David Brems); some `(NP )` suffixes on
  the decoy rows.

---

## 7. GIS — township/city boundary is in UGRC Municipal Boundaries (CountyID 18)

- **Boundary layer CONFIRMED:** UGRC **Utah Municipal Boundaries** FeatureServer holds
  `NAME='Emigration Canyon'`, **`COUNTYNBR='18'`** (Salt Lake) — verified live:
  `https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/UtahMunicipalBoundaries/FeatureServer/0/query?where=UPPER(NAME)+LIKE+'%25EMIGRATION%25'&outFields=NAME,COUNTYNBR&f=json`
  → returns one polygon. Use this for the township/city outline.
- **No council districts** (all at-large) → **no district layer to build**; the geo tool is a
  single-polygon "is this address in Emigration Canyon" test (point-in-polygon), not an
  address→district resolver. UGRC precinct fallback: VistaBallotAreas **CountyID = 18**.
- The canyon is a long, narrow corridor along Emigration Canyon Rd; the UGRC polygon is the
  authoritative extent.

---

## Retrieval plan (recommended order)

1. **Council minutes 2017→present (PMN body 5809):** enumerate
   `utah.gov/pmn/list/notices.html?id=5809` (retry on 500) / sitemap
   `publicbody/5809.html`; for each meeting notice harvest the **Approved Minutes** PDF
   (+ agenda, supporting docs, MP3) → `raw/`. Index Workshop (6 PM) and Regular (7 PM) as
   **separate docs**. Born-digital text → markdown. Fallback: MSD AgendaCenter.
2. **Vote extraction (council):** parse `Council Member X moved … seconded by Council Member
   Y … vote was N-M[, unanimous | , Council Member Z opposed]`; `Council Members Present:`
   header for attendance; **max tally 5, MAYOR VOTES (counted in the 5)**; unanimous → tally
   only, names unrecorded. Verify dissent wording on the first contested motion.
3. **Planning Commission (PMN body 1562):** harvest `YYMMDD_EmigrationPC_MinutesApproved.pdf`;
   text-verify the first PC doc's vote/recommendation format; capture PC→Council
   recommendation + any land-use case numbers (canyon-sensitive-lands / conditional-use).
4. **Comments:** grep PMN "Supporting Docs" packets for written correspondence; otherwise
   build a labeled `minutes_speaker_log.csv` (paraphrased hearing speakers) + record the
   honest submit-only verdict.
5. **Elections:** reuse `~/Desktop/slco-election-archive` — KEEP the 44 genuine Township/City
   council rows (2015/2017/2023/2025), **EXCLUDE all Improvement-District + MSD-question
   rows**; note the 2019/2021 council-contest absence.
6. **Geo:** pull the UGRC `Emigration Canyon` municipal polygon → single-boundary
   point-in-polygon tool (no districts).

---

## Risks / blockers

- **PMN-only publishing (STRUCTURAL, resolved):** no city CMS; **Utah PMN body 5809
  (council) / 1562 (PC)** is the canonical source, MSD AgendaCenter secondary. The
  `list/notices.html?id=5809` archive endpoint **intermittently 500s** — retry; sitemap page
  is stable. Use a **browser UA** on all fetches (PMN file store served the PDFs cleanly with
  a Chrome UA this recon).
- **Township→City conversion (2024-05-01, H.B. 35):** entity type changed mid-record;
  document labels shift from "Metro Township" (2017–2024) to "City" (2024+). Same 5-member
  body throughout — do **not** treat as two entities, but note the vintage in provenance.
- **Mayor VOTES (max tally 5):** the mayor is council-selected and is one of the five voting
  members (Millcreek pattern) — confirmed (Brems moves motions, tally = 5-0). Getting this
  right sets every vote's denominator; do NOT model an executive non-voting mayor.
- **Dissent-naming format unconfirmed:** sample was 100% unanimous. Pull a contested land-use
  meeting to lock the dissent parser.
- **PC vote format text-unverified this recon:** portal + coverage confirmed; verify grammar
  on the first PC file.
- **Improvement-District confusion:** the sewer/water **Emigration Canyon Improvement
  District** shares the name and runs its own elected board — **exclude it everywhere**
  (elections §6; any PMN body that is the Improvement District, not 5809/1562).
- **Election council-contest gaps (2019/2021):** verify against certified SLCo results; the
  2015 row is an incorporation referendum, not a seat.

---

## Refresh notes

**2026-07-19 (Q3-2026 refresh) — `fetch_new.py` probe dedup fix.** The probe was
over-claiming "NEW minutes to fetch (42)" council / "(47)" PC against a repo whose coverage
was verified complete through the 2026-07-17 waves — all false positives. Root cause: a
single PMN notice bundles many attachments (agenda + the *prior* meetings' approved
minutes), and PMN frequently re-uploads the SAME minutes doc under a second, unrelated
fileId whose filename has no parseable date (e.g. notice 743839 links both the recorded
minutes fid 827423 *and* a duplicate "Meeting Minutes" fid 827715). The old dedup keyed only
on (source_url fileId) or a date parsed from the filename, so every such duplicate printed
date "?" and was flagged new. Fix (read-only semantics preserved): dedup by NOTICE
DISPOSITION — a notice id already in `minutes_index.csv` (harvested) or in
`minutes_unrecovered.csv` (reviewed → honest gap) is fully dispositioned, so the whole
notice is skipped; genuinely-new meetings still arrive on never-seen notice ids.
`filename_date` also now parses MM-DD-YY. Re-probe after the fix: **council 0 new**; **PC a
small residual** of month-name-only re-uploads/agendas riding notices whose OWN (recent)
meeting is not yet dispositioned (e.g. notice 1090275 = the 2026-07-09 PC meeting, minutes
pending) — content-verified 2026-07-19 to be **0 genuinely-new minutes** (all 5 "…minutes"
files duplicate on-disk dates 2026-06-11 / 2026-05-14 / 2025-09-24 / 2024-04-11 / 2024-05-09;
the other 2 are agendas mislabeled "minutes"). The probe deliberately surfaces
un-dispositioned notices for review rather than guessing a year from a bare month name (which
could hide a real meeting); date-based detection of late-posted minutes on an
already-dispositioned date remains the job of `scripts/pmn_crosscheck.py`, not this probe.
Down from the pre-fix 42 council / 47 PC false positives. Original backed up to
`_backups/2026-07-19-q3-refresh/emigration_canyon/`.

## Key URLs (quick index)

| What | URL |
|---|---|
| Official site (redirect target of ecmetro.org) | https://emigration.utah.gov/ |
| Legacy site (301 → emigration.utah.gov) | https://www.ecmetro.org/ |
| PMN — **Council body 5809** (sitemap) | https://www.utah.gov/pmn/sitemap/publicbody/5809.html |
| PMN — Council full archive list | https://www.utah.gov/pmn/list/notices.html?id=5809 |
| PMN — **Planning Commission body 1562** | https://www.utah.gov/pmn/sitemap/publicbody/1562.html |
| Minutes/agenda/audio doc pattern | https://www.utah.gov/pmn/files/&lt;fileId&gt;.pdf (audio: .MP3) |
| Council minutes sample (verified 2026-05-19) | https://www.utah.gov/pmn/files/1456089.pdf |
| Council minutes (2026-04-21) | https://www.utah.gov/pmn/files/1447787.pdf |
| PC minutes sample (2026-06-11) | https://www.utah.gov/pmn/files/1459781.pdf |
| MSD community page | https://www.msd.utah.gov/349/Emigration-Canyon |
| MSD AgendaCenter (secondary mirror) | https://www.msd.utah.gov/AgendaCenter |
| SL County live results | https://electionresults.utah.gov/ |
| Election archive (local) | ~/Desktop/slco-election-archive (44 genuine council rows 2015–2025; exclude Improvement District + MSD) |
| UGRC municipal boundary (CountyID 18) | https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/UtahMunicipalBoundaries/FeatureServer/0 (NAME='Emigration Canyon') |

```json
{"vendor":"Utah Public Notice (PMN) — no city CMS; MSD AgendaCenter secondary mirror","minutes_landing_url":"https://www.utah.gov/pmn/sitemap/publicbody/5809.html (full archive: https://www.utah.gov/pmn/list/notices.html?id=5809)","minutes_url_pattern":"https://www.utah.gov/pmn/files/<fileId>.pdf (non-sequential ids; harvest labeled 'Approved Minutes' links; audio .MP3)","coverage_years":"2017-2026 (metro-township incorporation Jan 2017 = data floor; PMN body 5809 verified for current cycle, enumerate list for earliest; MSD AgendaCenter fallback)","format":"born-digital clean text PDF (DocuSign-signed, pdftotext-clean, no OCR)","votes_in_minutes":true,"vote_style":"narrative tally - mover+seconder named, 'vote was 5-0, unanimous in favor'; no per-member Aye/Nay on unanimous (South-Jordan/Taylorsville-like); dissent format unconfirmed; Workshop(6pm)+Regular(7pm) posted as separate docs","has_own_pc":true,"pc_pmn_body_id":1562,"council_weekday":"Tuesday","cadence":"monthly - 3rd Tuesday 7:00 PM (6:00 PM workshop precedes some); PC ~monthly 2nd week","num_seats":5,"seats_all_at_large":true,"has_mayor":"yes but council-SELECTED from the 5 (not separately elected); mayor PRESIDES and VOTES; max tally=5 (Millcreek pattern)","form_change":"Metro Township (2017-2024) -> CITY effective 2024-05-01 via H.B. 35","current_members":["David Brems (Mayor, votes)","Catherine Harris","Jennifer Hawkes","Robert (Roberto) Pinon","Nicholas Griffith"],"comments_published":"submit-only / honest-empty likely - no written-comment archive; minutes paraphrase in-person speakers (minutes_speaker_log.csv, not all_comments_clean.csv); grep PMN supporting-docs packets before finalizing","pmn_body_id":5809,"elections_source":"~/Desktop/slco-election-archive/data/municipal_results_long.csv (SLCo) + electionresults.utah.gov","elections_genuine_rows":44,"elections_genuine_contests":["2015 EMIGRATION CYN METRO TWNSHP-CTY (incorporation referendum)","2017 EMIGRATION CANYON MT CNCL @ LRG","2023 EMIGRATION CANYON METRO TOWNSHIP COUNCIL AT-LARGE","2025 CITY OF EMIGRATION CANYON COUNCIL AT-LARGE"],"elections_decoys_to_exclude":["EMIGRATION IMPROVEMENT (2015)","EMIGRATION IMPROVEMENT DIST (2017)","EMIGRATION IMPROVEMENT DISTRICT BOARD OF TRUSTEES AT-LARGE (2021)","EMIGRATION CANYON MSD (2015 YES/NO ballot question)"],"elections_gaps":"no Township COUNCIL contest present 2019 or 2021 (verify vs certified SLCo; likely real - staggered at-large seats not up)","gis_source":"UGRC UtahMunicipalBoundaries FeatureServer/0 NAME='Emigration Canyon' COUNTYNBR=18 (verified); NO council districts (all at-large) -> single-polygon point-in-polygon, not address->district","data_floor":2017,"admin_services":"Greater Salt Lake Municipal Services District (MSD) - City Recorder Diana Baun; contract attorney/engineer","do_not_confuse":"Emigration Canyon Improvement District (sewer/water special district, own elected board) is NOT the City/Township Council","blockers":["PMN list/notices.html?id=5809 intermittently 500s - retry; use sitemap page","use browser UA on all fetches","dissent-naming vote format unconfirmed (sample all unanimous)","PC vote format text-unverified this recon","reconcile Griffith vs 2023 winner Tyler Tippetts (one seat turned over by 2026)"],"confidence_notes":"HIGH on: PMN as source, body ids 5809/1562, born-digital format, 5-member/mayor-votes form, township->city 2024 conversion, narrative-tally votes (all quoted from verified 2026-05-19 minutes), 44 election rows + decoys, UGRC boundary. MEDIUM: exact earliest PMN coverage year (enumerate at acquisition), current 5th member's election path, comments final verdict (check packets)."}
```
