# Weber County — county-level data repository

The repo's **second COUNTY entity** (after `salt_lake_county/`) and the first county built
from **prose minutes with NAMED roll-call votes** rather than a Legistar API. Weber County
(FIPS **49057**; `gov_level='county'`, **fed_index 103**, offset band 101–199) governs by a
**3-member Board of County Commissioners** (a Council-of-Commissioners form — NOT
Council–Mayor; no separately-elected executive). It **contains the repo's
`ogden_city_council`**. The Commission meets **Tuesdays, 10:00 a.m.**, Weber Center, Ogden.
Federated into repo-root `gov.db` (`cities.db`). Registry: `registry/entities.csv`
(+ `registry/relationships.csv`: `ogden within weber_county`, `weber_county within
ut_state`, `weber_county member_of wfrc_mpo`). Source map: `recon.md`. Counties are modeled
as **modules**, not big cities — only the modules that fit are built. Each module's own
`README.md`/`CLAUDE.md` is authoritative for that module.

## Governance & the voting body

- **Board of County Commissioners — 3 members, all voting**; one is **Chair**, one **Vice
  Chair** (elected internally each January). Current board (2023– ): **Gage Froerer**
  (Chair), **James "Jim" H. Harvey** (Vice Chair), **Sharon Bolos**. Prior-era
  commissioners appear across 2015–2022 (Ebert, Gibson, Jenkins, Bell) and are captured
  data-first from the roll calls. There is **no county council and no elected mayor** — the
  Commission is both legislative and executive; agencies (RDA, etc.) convene in-session as
  the same Commission. County Clerk/Auditor (Ricky Hatch) takes the minutes.

## Bodies in the db — totals: 4,415 motions / 12,580 votes / 7 persons (2015-01-06 .. 2026-04-14)

- **Board of Commissioners** — the regular meeting body: **4,415 motions / 12,580 votes**
  across **532 meetings**, **99.3% named** (4,386/4,415 carry a named roll call). Outcomes:
  4,384 Pass, 2 Fail, 29 no-result-printed (`outcome=''`). **82 contested** motions (≥1
  Nay/Abstain/Recuse). (Totals restated 2026-07-31 — see the two repair notes at the bottom:
  the phantom 2021-06-01 meeting was removed, 15 swallowed motions recovered, and 9 more
  motions surfaced by the died-for-lack-of-a-second repair.)
- **Board of Commissioners Work Session** — 3 posted work sessions in the floor (2016-07-06,
  2016-07-13, 2018-10-10), all discussion-only (**0 motions**); kept as a distinct body so
  the meeting-type distinction is preserved. Detection is **title-block-only** (regular
  meetings routinely *mention* "work session" in discussion prose — do not re-flag on that).

## The vote-recording CEILING — NAMED roll call, even on unanimous motions

Unlike the tally-only county councils (incl. Salt Lake, whose named votes come from
Legistar), **Weber's minutes name every commissioner's individual vote on every recorded
motion** — the `motion`/`vote` layer is NAMED-primary straight from the minutes prose
(`db/extract_votes.py`). `result_raw` is the **verbatim roll-call line** ("Chair Froerer –
aye; Commissioner Harvey – aye; Commissioner Bolos – aye"); `outcome` (Pass/Fail) is derived
from the aye/nay tally (there is no separate "carried 3-0" result string). Two roll-call
grammars are handled: (a) the modern single semicolon-separated dash-joined line, and (b) an
EARLY-ERA (mostly 2015–2017) `Roll Call Vote:` header + one dot-leader member line each.
**`names_recorded=0` = an honest recording ceiling** (source printed no roll call) — **29
motions (0.66%)**: **motions that died for lack of a second** (7 — they never reach a vote,
so `outcome`/`result_raw` are empty by construction, see the 2026-07-31 repair note), a
withdrawn substitute motion that was never voted (2018-09-11 #7), a
recess motion, source-malformed rolls (e.g. 2015-07-14 prints "Commissioner Ebert; Chair
Gibson – aye" — one member, no value), and stacked organizational motions sharing one roll
call. Never fabricated.

- **Data floor 2015-01-01.** The county's own born-digital archive reaches back to **2000**
  (~690 additional meetings, same named grammar) — a high-value backfill logged in `recon.md`,
  **not harvested in this build** (per-year counts recorded there).
- **Provenance** `county_portal` on every meeting/motion. Minutes markdown carries
  front-matter (`source_url`, `source_pdf`, `source_index`); a UNION of two portal indexes
  (`commission_meetings.php` + `commission_minutes_archive.php`) is merged in
  `db/fetch_minutes.py` because neither index alone is complete.

### The Froerer alias (person-unification normalization)

"Freorer" is a **clerk typo for Chair Gage Froerer** in the roll-call lines of three Jan-2023
meetings (`2023-01-10`, `2023-01-17`, `2023-01-24`). The verbatim value is **retained
untouched in `db/staging/votes.csv`** (city-faithful); it is merged onto the canonical
person **only at name-key resolution** in `db/build_db.py` (`PERSON_ALIASES = {"freorer":
"froerer"}` — the sanctioned normalization layer, SCHEMA_SPEC §8). Result: 7 persons (not 8),
23 votes reattributed to Gage Froerer (2,639 total). Add future verbatim misspellings there,
not by editing staging.

## Modules

```
legislative/  Commission minutes markdown (532 docs, 2015+) + minutes_index.csv (UNION of
              two portal indexes). minutes_unrecovered.csv = ONE row (2021-06-01, the county
              mis-post — see the 2026-07-31 repair note); the 2026-07-26 note that it was
              empty held until then. (21 docs had been front-matter-only Konica copier scans
              with no OCR fallback — closed 2026-07-26, see the repair note below.)
db/           extract_votes.py (prose → staging/), build_db.py (→ weber_county.db, the
              STANDARD 8-table schema; federates unchanged). DERIVED — rerun in that order.
              staging/motion_refs.csv = 1,147 motion-anchored instrument refs (feeds ordinances/).
              ocr_empty_minutes.py = the 2026-07-26 image-only-scan OCR backfill.
land_use/     County planning corpus — FTS-ONLY (166 minutes, 4 bodies). NO vote layer (by
              scope). See the consolidation seam below.
ordinances/   The adopted-instruments register (NEW) + adopted-code catalog + land-use case keys.
elections/    CANONICAL Weber County Clerk canvass, 2006–2026 (weber_results_long.csv). Ogden
              re-points to it (queued, separate). gov.db: election_result + election_race.
plans/        Ogden Valley + Western Weber General Plans (MIH lives inside them) — text sidecars.
projections/  Kem C. Gardner population/household/jobs (140 rows, vintages 2022 + 2025).
gis/          CATALOG ONLY (link, never mirror) — 8 UGRC/county ArcGIS layers (LIR parcels base).
```

## Which artifact for which question

- **County vote record / contested actions / a commissioner's record:** `gov.db`
  `motion`/`vote` where `city='weber_county'`; `v_contested_all` (82 contested),
  `v_member_record_all`. NAMED roll call on 99.3% of motions.
- **Adopted ordinances + who enacted them:** the **`ordinances/` register** — the
  adopted-ordinance / resolution table Weber never published, derived from the named-roll
  minutes (`ordinances/build_adopted_instruments.py`). `adopted_instruments.csv` is the full
  working register (**846 rows — 277 ordinances + 569 resolutions**, one per distinct
  instrument, each citing its minutes). `index.csv` is the **ordinance-class subset (277
  rows)** in the federation loader's schema (direct county-db `motion_id`) → `cities.db`
  `ordinance` **with enacting-vote linkage**: **248/277 (89.5%)** carry a unique link; **29
  ambiguous/unlinked** (same-date/same-stage ties, or an ordinance number matched from a
  nearby header) are honestly `unlinked` (blank motion_id, `prior_readings` recorded).
  ⚠ **Was 198/277 before 2026-07-29**: procedural motions (adjourn / recess / reconvene)
  were competing as "adopting" motions, because a number read off an ALL-CAPS section
  header anchors to whichever motion follows it. Excluding them recovered 50 correct links
  and turned **ordinance 2019-13** from a WRONG link (it pointed at "moved to adjourn the
  public meeting and reconvene the public hearing") into an honest `unlinked`. **2019-13 is
  now correctly linked (2026-07-31)** — its real adopting motion (Solar Overlay Zone, Little
  Mountain Solar) was being swallowed by the `extract_votes.py` skip bug fixed that day; the
  ordinances/README.md note about it is superseded. ⚠ **Two more WRONG links corrected
  2026-07-31 (died-motion pass)**: **2018-14** and **2018-23** each pointed at a motion that
  had DIED FOR LACK OF A SECOND and now point at the motion that actually adopted them
  (2018-09-11 #9 and 2018-12-18 #15); **Resolution 29-2018** entered the register for the
  first time. 2018-15 stays honestly `ambiguous`. Resolutions
  stay register-only. `code_sources.csv` = the dual-codification code catalog (Municode +
  Municipal Code Online); `case_keys.csv` = 169 PC/BOA land-use case keys (a DIFFERENT
  numbering from Commission ordinances — join is a future task).
- **Thematic / keyword search:** `fts_minutes` (Commission minutes + the land_use planning
  corpus + plans), filter `city='weber_county'`.
- **Land-use decisions (Planning Commissions / BOA):** **FTS ONLY** — read the minutes.
  There is **NO vote/`all_votes.csv`/development-pipeline layer** for land use (owner-gated
  scope, not a data gap — the votes were never extracted). See the seam below.
- **Elections:** `election_result` / `election_race` / `v_election_city`; canonical canvass
  in `elections/` (see below).
- **Growth projections:** `projection` (filter ONE vintage before trending). **GIS:**
  `gis_layer` (catalog — query the live ArcGIS endpoints; nothing mirrored; LIR parcels =
  the housing/growth base for **unincorporated** Weber).
- **Cross-tier (Weber ↔ Ogden):** `entity_relationship` (`within`), then join the Ogden city
  rows to the county rows.

## Land-use — the 2025 planning-commission consolidation seam

Historically two area commissions + a countywide appeal authority; **`land_use/` ingests all
four as searchable text** (166 minutes, floor 2020):

- **Weber County PC** (consolidated, `weber_county_pc`) — created by **Weber County
  Ordinance 2025-27** (final reading 2025-11-18), which dissolved the two area PCs
  **effective 2025-12-03**; corpus 2025-12-09 → 2026-05-05 (8 minutes). This is the LIVE
  body going forward.
- **Ogden Valley PC** + **Western Weber PC** — the former eastern/western area commissions,
  now **closed historical series** (OVPC 2020-04-07..2025-12-02, 77; WWPC 2021-02-09..2025-11-18, 69).
- **Board of Adjustment** (appeal authority, sparse by nature) — 2022-04-28..2025-10-23, 12.

**WATCH ITEM — Ogden Valley incorporation.** The 2024 ballot incorporated **Ogden Valley
City** (council elected 2025; `ogdenvalley.gov`), which removed jurisdiction from the OVPC
and triggered the consolidation. New Ogden-Valley-area land use now splits: unincorporated
pockets → the consolidated county PC; the incorporated city → its own municipality (a
potential FUTURE `build-city-data-repo` target, not part of this county). Use the GIS
Municipal Boundaries layer to separate newly-incorporated land over time.

## Elections — the canonical Weber County canvass (`elections/`)

`elections/weber_results_long.csv` is **the canonical Weber County Clerk canvass** (tidy long
form, 13 columns matching the SLCo file; 11,416 rows, **2006–2026**): every odd-year
municipal canvass 2007–2025 (all contests + districts) plus even-year county-office contests
and countywide measures. `build_elections.py` derives `election_results_by_contest.csv`
(1,080 rows / 327 contests) → gov.db `election_result`. **Ogden, the repo-held Weber city,
draws from this same county canvass** — the byte-identity-gated Ogden re-point is **queued
and separate** (do NOT touch `ogden_city_council/election_results/` from here).

Honest gaps: **the 2023 municipal general is a county-publication gap** — the county
published only a **bond-only** canvass and referred voters to the municipalities, so
**Ogden's 2023 council races exist only city-side** (`ogden_city_council`), not in this
county canvass. Also missing county-side: 2009 (entire cycle), 2013 primary, 2019 primary;
no precinct grain before 2018 / for 2019g / 2021. Suppressed cells (<15-voter precincts)
stay suppressed (`suppressed=True, votes=''`). Module `elections/CLAUDE.md` is authoritative.

## 2026-07-26 repairs (audit F4 / F13 — `_audits/2026-07-25/report.md`)

- **21 image-only scans OCR'd.** They were Konica-Minolta copier scans with no text layer
  and the build had no OCR fallback, so each markdown was ~307 bytes of front matter and
  contributed nothing (19×2021, 2×2023). New `db/ocr_empty_minutes.py` renders the RETAINED
  raws and OCRs them (idempotent; born-digital rows untouched; `provenance` restamped
  `county_portal_ocr`). **motions 4,242 → 4,404 · votes 12,114 → 12,594 (CSV rows; the db
  holds 12,585 — see the documented expected 9-row difference below) · motion_refs
  1,102 → 1,148 · adopted-instruments register 807 → 844 — exactly the 37 missing 2021
  resolution numbers the audit predicted, including RESOLUTION 36-2021** (2021-09-21, the
  meeting the auditor had read visually to prove the loss).
- **Silent vote drops made LOUD.** `build_db.py` swallowed `sqlite3.IntegrityError` on
  `UNIQUE(motion_id, person_id)` and decremented the id, so 9 rows vanished between the flat
  CSV and the db with no trace (the Park City class). Each is a SOURCE clerk typo naming one
  commissioner twice on one roll ("Commissioner Harvey – aye; Commissioner Froerer – aye;
  Chair Froerer – aye"). The CSV keeps them verbatim; the build now prints every collision.
  db vote = 12,585 vs CSV 12,594 — the 9-row difference is expected and itemized on build.

## 2026-07-31 repairs (G8 duplicate-ingest / collision wave)

- **PHANTOM 2021-06-01 meeting REMOVED (13 motions / 39 votes were double-counted).** The
  portal file `min_06012021.pdf` **is the 2021-05-11 minutes verbatim** — identical body text,
  title block "Tuesday, May 11, 2021", same PDF page count/size — on **both** portal channels
  (`commission_meetings.php` and archive `minute_id=1118`), re-verified live 2026-07-31 (no
  `_1`/`_2` revision exists). Ingesting it created a second copy of the May 11 meeting under a
  June 1 date. The markdown + its `minutes_index.csv` row are gone. **The June 1, 2021 meeting
  really happened** (2021-06-15 consent: "Minutes for the meetings held on May 25 and June 1,
  2021"), so it is now the single row in `legislative/minutes_unrecovered.csv` — an honest
  gap, not silence. Downstream: ordinances **2021-13 / 2021-14 / 2021-15** were dated to the
  phantom with a bogus "prior reading" on 2021-05-11 (the same meeting, twice); they now
  correctly show **adoption_date 2021-05-11, one reading**.
- **`db/fetch_minutes.py` guard so a refresh cannot re-create it.** A date is rejected only
  when its extracted text **duplicates a date already harvested in the same run** AND the
  document's own **title-block date names that other date**. Both conditions are required:
  a bare header/date mismatch is usually a CLERK TYPO in a real document (`2022-01-11` prints
  "January 18, 2022"; `2025-08-05` prints "August 4th, 2025") and those must be kept. Replayed
  over all 533 cached raws the guard rejects exactly one date (2021-06-01) and writes it to
  `minutes_unrecovered.csv`.
- **`db/extract_votes.py` skip bug FIXED — 15 real motions / 31 votes recovered.** When the
  roll-call scan stopped at the NEXT motion (i.e. this motion had no roll call), the loop
  resumed at `j + 1` and **stepped over that next motion entirely**. Any motion printed
  directly under a retracted / lost-for-lack-of-second / unvoted motion was silently lost.
  Recovered, each verified against the minutes: **2019-07-30 Ordinance 2019-13** (the Solar
  Overlay Zone / Little Mountain Solar adoption — the G8 target; now uniquely linked in
  `ordinances/index.csv`, motion_resolution `unique`, confidence `high`), **2021-11-16
  Resolution 49-2021** (2-1, Jenkins "no" — the register had been showing the failed
  "approve Chris Davis; no second" motion as its title), **2022-11-15** (Harvey **recused**),
  **2025-12-16** (Harvey **nay**), **2015-07-21 Resolution 33-2015** (register 844 → 845),
  and 10 more. Contested motions **76 → 81**; totals **4,404 → 4,406 motions / 12,585 →
  12,577 db votes** (−13 phantom, +15 recovered; votes −39 phantom, +31 recovered, −9 the
  documented duplicate-roll drops).
- **2025-07-29 ↔ 2025-08-12 examined and left ALONE — both meetings are REAL.** Their motion
  sets are identical because the **clerk copy-pasted** the July 29 consent + budget-hearing
  block into the August 12 document, not because of a duplicate ingest: the two PDFs are
  distinct files with distinct title-block dates and distinct opening sections (July 29 has
  the Winning In Weber awards; August 12 has "there are municipality elections today" — Utah's
  2025 municipal primary was Aug 12). The duplicated block belongs to **July 29**: its
  warrants #105543-105605 sit immediately before 2025-08-05's #105606-105656, and Resolution
  33-2025 falls between 31-2025 (7/15) and 35-2025 (8/5). The county's own rev-0 and rev-2
  Aug 12 PDFs both carry the block, so this is a **source-fidelity defect, retained
  verbatim** (cardinal rule 2). ⚠ Consequence to respect: **Resolution 33-2025 appears as two
  adopting motions**, and Aug 12's real consent items/warrants (≈#105657-105718) were never
  printed. The same clerk habit shows at 2025-07-08/07-15 and 2025-08-19/08-26.

## 2026-07-31 repairs (second pass) — DIED-FOR-LACK-OF-A-SECOND motions

**A motion that died for lack of a second was displaying as a PASS with named ayes.** Weber's
clerk prints the died motion, its terminator and the **substitute motion** that follows inside
ONE hard-wrapped paragraph ("… Motion died for lack of a second. **Chair** / **Harvey** moved
to adopt Ordinance 2018-14 amending …"), and `db/extract_votes.py` anchored motions one
physical line at a time. The substitute was therefore invisible, and the died motion — matched
because the substitute's "; Commissioner Ebert seconded" fell inside its 5-line lookahead —
**swallowed the substitute's roll call**. Four motions were affected: **2018-07-03 #6,
2018-09-11 #6 and #7, 2018-12-18 #13**.

The fix, all in `db/extract_votes.py`:
- `split_at_died()` — a whitespace-only pre-pass that normalises every "motion died for lack of
  a second" phrase onto one line and breaks after it, so both motions become addressable. No
  text is added, removed or reworded; `motion_text` stays verbatim.
- A **died** motion is now registered on its own terms: no seconder required (it never got
  one), **no roll-call scan at all**, `result_raw=''`, `outcome=''`, `names_recorded=0` — the
  repo's existing convention for "the source printed no roll call".
- `SUBST_RE`, a looser anchor (`made a substitute motion` / `made a motion` / `<Name> … and
  moved`) that may span the line wrap, applied **only** within 8 non-blank lines of a died
  motion, so the corpus-wide motion anchor is unchanged.
- The roll-call scanner's "stop at the next motion" test also stops at a died motion.

Delta (proved against the pre-fix staging CSVs): **+9 motions (4,406 → 4,415), +3 votes
(12,577 → 12,580 db / 12,586 → 12,589 CSV), +7 motion_refs**; the four affected meetings are
the ONLY ones that changed — every other meeting's motions and votes are byte-identical, and
no vote value was lost or invented (the four borrowed rolls simply re-anchored to the
substitute that actually received them). The 2026-07-31 first-pass loop-resume recoveries
(Ordinance 2019-13, Resolution 49-2021, the 2022-11-15 recusal, the 2025-12-16 nays,
Resolution 33-2015) all survive unchanged.

Newly extracted, each verified against the minutes: the **five substitute motions that
actually carried** — 2018-07-03 **Resolution 29-2018** (Bell/Edwards to the Western Weber PC,
2-1), 2018-09-11 **Ordinance 2018-14** (12th St & 4700 W rezone to **C-1**, 2-1) and
**Ordinance 2018-15** (7500 W A-3→A-2, 2-1 with Chair Harvey **nay**), 2018-12-18 **Ordinance
2018-23** (impact fees, trails fee set at **$1,350**), and **2020-06-23 the Taylor Landing
appeal** (Harvey **nay** — a contested vote that had been *orphaned*, printed in the minutes
but attached to no motion at all: the +3 votes and contested **81 → 82**) — plus four more
died/withdrawn motions that had never been extracted. Ordinances **2018-14** and **2018-23**
were re-pointed off the died motions onto their real adopting motions in `ordinances/`.

## Honest gaps (not fabricated)

- **Land-use votes are out of scope** (FTS-only), not missing. 29 Commission motions are
  `names_recorded=0` (genuine recording ceilings + the 7 died-for-lack-of-a-second motions
  and one withdrawn substitute, which never reached a vote). Joint **Weber+Davis** boundary meetings
  (2020-10-14, 2023-08-01) print both boards' roll calls — visiting Davis commissioners
  (Kamalu/Stevenson) are excluded via the extractor's `VISITING` set and never become Weber
  persons; "Elliott" is left ambiguous (cast no Weber vote).
- **WWPC has no 2020 minutes** (portal begins 2021-02-09; GRAMA-only). Agenda-only dates
  (OVPC ~29 / WWPC ~43 / BOA ~28) are logged, not ingested (no deliberative record). Three
  portal source mis-links are recorded in `land_use/gaps.csv` (mislinked copies dropped).
- **2000–2014 Commission history** is a logged future backfill (~690 meetings), not a gap.
- ⚠ **KNOWN RESIDUAL (found 2026-07-31, NOT fixed): one ORPHANED roll call at `2017-06-27`.**
  The minutes print a contested roll ("Commissioner Gibson – nay; Commissioner Harvey – aye;
  Chair Ebert – aye") for **Ordinance 2017-24** (Ogden Valley outdoor lighting) that is
  attached to no motion, because the clerk narrates that whole item without the extractor's
  motion grammar: the first motion is "Commissioner Gibson **recommended** that staff …", the
  one actually voted on is "Commissioner Harvey **restated his motion** to adopt Ordinance
  2017-24 …", and the intervening substitute that died reads "Commissioner Gibson **made a
  substitute motion** …". None of those is a `<Title> <Name> moved` anchor, and the died
  motion there is likewise unanchored so the substitute-motion rescue never opens. The vote is
  in the minutes text (and in `fts_minutes`) but not in the vote layer — an extraction ceiling,
  never fabricated. Ordinance **2018-15** is the related linkage residual: its real adopting
  motion (2018-09-11 #11) ties on the same date with the Resolution 46-2018 motion that picks
  "2018-15" off the section header, so the register keeps it honestly `ambiguous`.
- ⚠ **OPEN QUESTION (flagged 2026-07-31, NOT acted on): is `2022-01-11` really January 18?**
  The portal file `min_01112022.pdf` prints "**Tuesday, January 18, 2022**" in its title block,
  and the county lists **no 01-18-2022 meeting at all** (absent from both indexes;
  `min_01182022.pdf` 404s). Evidence it is a real Jan 11 meeting with a clerk header typo:
  its warrants (#4935-4969) continue directly from Jan 4's (#4910-4934), and it approves
  "Minutes for the meeting held on January 4th, 2022". Evidence it is really the Jan 18
  meeting misfiled under a Jan 11 name: it carries **two** warrant batches (the catch-up
  pattern Weber uses after a skipped week), **nothing in the corpus ever approves "January 11,
  2022" minutes**, and **2022-02-15 approves "the meeting held on January 18, 2022"**. Both
  readings are live; resolving it needs an agenda/PMN notice for January 11 vs 18, 2022. Two
  other header/date mismatches were checked and ARE plain clerk typos in real documents
  (`2025-08-05` prints "August 4th, 2025"; the mis-post guard deliberately keeps both).
- **MIH** — Weber publishes no standalone Moderate-Income Housing plan; MIH lives as chapters
  inside the two General Plans (search the `plans/text/` sidecars).

## Rebuild (order matters; DERIVED — never hand-edit outputs)

```
python3 weber_county/db/extract_votes.py                     # minutes markdown → db/staging/
python3 weber_county/db/build_db.py                          # staging → weber_county.db (+ Froerer alias)
python3 weber_county/ordinances/build_adopted_instruments.py # register + ordinances/index.csv (needs the db)
python3 weber_county/elections/build_elections.py            # canvass → election_results_by_contest.csv
python3 scripts/build_cities_db.py                           # federate into gov.db (+ search layer)
```

## Gaps / follow-ons (root TODO "County content menu")

Land-use vote layer promotion (4 bodies) + case-key↔ordinance linkage; the 2000–2014
Commission backfill; the Ogden elections re-point; RDA/interlocal agreements; county campaign
finance; the Ogden Valley City build watch. All honest, tracked, never fabricated.
