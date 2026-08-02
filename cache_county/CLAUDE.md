# Cache County — county-level data repository

The MID-tier **county** entity in civic-data (FIPS **49005**, fed_index **104**;
**Council–Executive** form). Cache County contains the repo's Cache-Valley city
**logan** (+ every other Cache municipality, carried in the canvass). Federated into
repo-root `gov.db` (`cities.db`) as `gov_level='county'`. Registry:
`registry/entities.csv`; geography (city↔county) in `registry/relationships.csv`. Source
map: `recon.md`. Counties are modeled as **modules**, not as big cities. Built 2026-07-20.

## Governance & the vote-recording CENTERPIECE (read first)

- **7-member elected County Council** (legislative) + a **separately elected County
  Executive** (currently **David Zook**; formerly Craig Buttars) who is the executive and
  **does NOT vote**. A full Council roll therefore tallies to **7**. Meets ~**2nd & 4th
  Tuesdays** in Logan.
- **The centerpiece is the legislative NAMED roll-call layer.** In the born-digital era
  Cache County prints **every member's Aye/Nay on every motion, unanimous ones included** —
  richer than Salt Lake County's own tally-only minutes. **1,714 of 3,215 legislative motions carry a named roll call** in `db/cache_county.db` — 100% of the born-digital 2021+ era; the OCR'd 2015-2020 era is tally-only by source (see the era split below).

### Two legislative eras (a document property — never trust the seam silently)
- **Era A — born-digital NAMED roll calls (≈2021 → present): HIGH confidence.** Grammar:
  an `Action:` line (optional video timecode) carrying `Motion made by <mover> … ;
  seconded by <seconder>`, a verbatim result line (`Motion passes.`/`Motion Fails`), then
  `Aye: N <names>` / `Nay: N <names>` / optional `Absent:` / `Abstain:`. Name lists are
  comma-separated and **wrap across physical lines**. `names_recorded=1`.
- **Era B — scanned, TALLY-ONLY narrative (2015 → ≈early 2021): recording ceiling.**
  **⚠ OCR'd 2026-07-26 (audit F1).** This era had been 145 `[SCANNED … DEFERRED]` placeholder
  files contributing **zero** motions, while `CLAUDE.md` claimed they were already OCR'd and
  `document.has_text` said 307/307. They are now real text and yield **1,505 tally-only
  motions**. Movers/seconders here are frequently **surname-only** (White, Yeates, Potter,
  Robison, Merrill) because the narrative prose prints no first name — an honest partial,
  never merged into a 2021+ person without evidence.
  Image-only scans, narrative tally grammar (`"…approve the agenda. White seconded. The
  vote was unanimous, 5-0. Potter & Zilles absent."`). **Mover + seconder + a numeric
  tally are named; individual members are NOT enumerated** unless a division is called.
  `names_recorded=0`, LOW confidence, honestly tally-only — never trusted as a named roll.
  These minutes are OCR (tesseract; `ocr: true`, `provenance: citysite_scanned` in
  front-matter), pdftotext char-density <~300/pg.
- **2021 is a MIXED, transitional-grammar seam** (early-2021 meetings still scanned; named
  born-digital begins mid-year) and is flagged **lower-fidelity** — it was NOT re-extracted
  (a documented audit flag, per the closing pass). Spot-check 2021 roll calls before
  quoting a divided vote.
- **Full-history OCR-backfill pipeline is READY, not run:** the year pages 2011–2014 and
  the Archive page (`countycouncil/minutes-archive.html`, **396 PDFs 1995–2010**) are
  reachable by the same scrape method (all scanned/tally-only). Data floor here is
  **2015-01-01**; 1995–2014 is an honest, dated depth gap (TODO backfill).

## Bodies in the db (5) — totals: **3,388 motions / 12,560 votes / 193 contested / 30 persons**

*(2026-07-29: down from 3,495 / 13,200 / 206 — extraction became INDEX-DRIVEN and stopped
double-counting 107 motions / 640 votes out of 12 orphan duplicate files. Nothing was lost;
see "the duplicate-file double count" under Honest gaps.)*

- **Council** (3,183 motions) — regular County Council meetings, the named-roll spine.
- **Workshop** (27) — Council workshops (often vote-less).
- **BoardOfCanvassers** (4) — Council sitting as canvassers.
- **ServiceArea1** (1) — county Service Area No. 1 governing body (appears on the council
  page; body tagged from the filename).
- **PlanningCommission** (173) — the **named-era** PC motions only, auto-appended from
  `land_use/all_votes.csv` (see land_use below; the 852 tally-only PC motions live in
  `land_use/motions_tally.csv`, NOT in the standard `motion` table).

Contested councils are high-consensus; `v_contested` = 193 (named dissent). Cache is a
prose county — motions/votes are parsed from minutes text, NOT a Legistar API.

## Modules

```
legislative/  Council + Workshop + Board of Canvassers + Service Area 1 — 305 minutes
              PDFs → markdown (2015+, 305 docs) + minutes_index.csv (carries
              snapshot_url/snapshot_timestamp; **the CANONICAL document list — extract_
              votes.py reads IT, never the directory**) + minutes_unrecovered.csv (4
              genuinely-lost dates) + wayback_snapshots.csv (the 25 dead-URL docs' archive
              pointers, regenerate with recover_snapshots.py).
              raw/ = a DELIBERATE 25-of-305 SLICE (150 MB): only the dead-URL documents,
              the module's sole irreplaceable bytes — fetch_raw_wayback.py + raw_index.csv.
              The 280 still-live PDFs (2.80 GB) are NOT retained (re-fetchable; see gaps).
              Votes prose-extracted: named 2021+, tally-only 2015–20 (OCR'd 2026-07-26).
land_use/     County Planning Commission (unincorporated land use) — 123 minutes markdown
              (2015-01→2026-03, first-Thursday) + all_votes.csv (NAMED era, 2024-11+, 939
              rows) + motions_tally.csv (tally era 2015→2024-10, 848 tallies) + roster.csv.
              1,025 PC motions total. NO development/ module (county has no tabular dev-app
              log — the PC motions ARE the development record; each names its project).
elections/    CANONICAL Cache County Clerk canvass — cache_municipal_results_long.csv
              (2,107 rows, 2021/2023/2025) + cache_county_office_results_long.csv (even-year
              county contests, 12,582 rows) + derived election_results_by_contest.csv (285
              rows, 18 jurisdictions; logan = the held city). gov.db: election_result once
              cache_county is registered.
ordinances/   Codified County Code (American Legal, through Ord. 2023-18) text + index.csv
              catalog (169 code-amending ordinances) + code_structure.csv. Enacting-vote
              linkage is DERIVED by db/link_ordinances.py (17 unique; see below).
              Rezones are NOT here (caveat).
plans/        6 governing plans (searchable text) + index.csv. Current General Plan (2023,
              Imagine Cache) is StoryMap-ONLY (link, no text sidecar); 1998 Comprehensive
              Plan is the prior full-text plan; MIH Plan 2019/2023, CRMP 2017, Envision
              Cache Valley, South Corridor Plan.
campaign_finance/  COUNTY-OFFICE candidate C&E disclosures 2008→2026 (added 2026-08-01;
              vision pass 2026-08-01/02) — 495 filing PDFs + text/ sidecars + a 171-file
              vision/ transcription layer. index.csv 239 county-office rows (234
              county_confirmed, 5 undetermined) + excluded.csv 256 (237 school board — the
              owner's out-of-scope ruling) + unrecovered.csv 2. filing_totals.csv carries
              each filing's OWN STATED TOTALS (210 contributions / 212 expenditures
              figures); contributions.csv/expenditures.csv are HEADER-ONLY — **no itemized
              donor or vendor rows exist**. Document-tier in gov.db (no cf_* rows).
              Read `campaign_finance/CLAUDE.md` before quoting any figure.
projections/  Gardner Institute county population/household/jobs (140 rows, vintages 2025+2022).
gis/          CATALOG ONLY (link, never mirror) — 24 UGRC + county ArcGIS layers + derived/
              (base-zoning counts: 8 districts, mostly A10 + FR40).
              (Rebuild order: `legislative/extract_votes.py` → `db/build_db.py` →
              `db/link_ordinances.py`.)
db/           build_db.py → cache_county.db (STANDARD 8-table schema; reuses the shared
              scripts/db_build_lib.py READ-ONLY). vote_overrides.csv + person_aliases.csv
              (documented correction layers, below). DERIVED — rerun `python3 db/build_db.py`
              THEN `python3 db/link_ordinances.py` (a rebuild renumbers motion_id, which
              invalidates ordinances/index.csv links); never hand-edit the db or tables/.
```

## Which artifact for which question

- **Aggregates / member vote records / time series** → `db/cache_county.db` (or gov.db
  `motion`/`vote` WHERE `city='cache_county'`): standard 8-table schema, views
  `v_contested`, plus the federated cross-city views. The named-roll layer makes
  per-member propensity real for **2021+**; 2015–2020 is tally-only (`names_recorded=0`).
- **Unincorporated land-use / rezone / CUP / subdivision decisions** → `land_use/`: the PC
  motions. **Named voters exist only 2024-11+**; the prior decade is tally-only by source
  (never infer who dissented). Contested: 44 tally-era split votes (counts only) + 17
  named-era contested motions.
- **What an ordinance did / who enacted it** → `ordinances/index.csv` (+ `text/` for the
  code). `motion_id` links the enacting Council roll call where unique (**17 linked**, all
  `match_confidence=high`, 2021–2022) — **DERIVED: rerun `python3 db/link_ordinances.py`
  after every `db/build_db.py`**, because a db rebuild renumbers `motion_id` (2026-07-29:
  all 10 previously hand-written links had gone stale onto unrelated 2015–2017 motions
  after the 2026-07-26 OCR backfill). **The derived linker was PROVEN against a second
  renumbering the same day** — the duplicate-file repair shifted every 2021+ motion_id by
  ~14, and all 17 links re-derived onto the identical physical motions (same meeting date,
  same motion text, same source file, each still naming its own ordinance), with the 8
  honestly-unlinkable ordinances still unlinkable. Hand-written ids would have broken
  again; derived ids did not. Ords 2022-06/07/08/09/10 share ONE motion_id — a
  single printed bundled roll call, not a matching error. **CAVEAT: this catalog is CODE-amending ordinances
  ONLY — rezones (map amendments) are NEVER source-noted by American Legal, so they are
  absent; the rezone record is in `land_use/` + the Council legislative motions.** Coverage
  floor: through Ord. 2023-18 (2023-05-09); later ordinances not yet in the code snapshot.
- **Elections (canonical)** → `elections/`: the Cache County Clerk canvass, held once at
  the county grain (logan + all Cache municipalities). **Two decisive findings:** (1) **NO
  RCV in any county canvass ever** — the one Cache RCV election (Nibley 2021) was
  town-self-administered and absent from the county canvass; every `rank_in_contest` is
  plurality order, no RCV final to misstate. (2) **Logan self-administered 2019 AND 2021** —
  the county published nothing for 2019 municipal and Logan is absent from the 2021
  canvass; county-administered from **2023**. Any future logan re-point covers **2023+
  only**; logan's 2019/2021 city-certified PDFs remain the sole primary source
  (millcreek-2016 pattern). **2024 primary + general canvass reports are image-only scans
  — retained, unparsed (OCR/vision follow-up queued).**
- **Who funded a county candidate** → `campaign_finance/`: 239 county-office filings
  2008–2026 with each filing's own **stated totals** (`filing_totals.csv`, verbatim detail
  in `filing_stated_detail.csv`). **There are NO itemized donor rows** — "who gave to X"
  needs the raw PDF. Never sum without grouping on `sha256` (42 cross-channel duplicates),
  and never read the summed stated figures as a per-candidate cycle total (`is_incremental`
  varies per filing). Join to votes via `db/cache_county.db` `person`; the County Executive
  files CF but has no `vote` rows (correct, not a gap).
- **Growth vision / housing obligations** → `plans/`: grep `text/` (the current 2023 GP is
  StoryMap-only — open its `source_url`; the 1998 plan is the grep-able prior full text).
- **Population / household / jobs forecasts** → `projections/` (filter to ONE `vintage`).
- **Zoning / parcels / subdivisions / annexation geography** → `gis/index.csv` live ArcGIS
  endpoints (catalog — query narrowly, never bulk-fetch).
- **Thematic / keyword search** → the repo-root `cities.db` FTS5 layer (`fts_minutes` etc.)
  once federated; do NOT grep the minutes files.

## Provenance conventions (the `provenance` column on `motion`)

- `citysite_minutes` (1,405) — audited born-digital Council minutes from the county CMS
  (`cachecounty.gov/assets/meetings/countycouncil/<year>/`).
- `wayback_minutes` (201) — the **2024 legislative folder recovered from the Internet
  Archive Wayback Machine** (the live county site had dropped it); promoted into the
  audited layer, filterable apart from live-site minutes. **All 25 wayback-recovered
  documents now carry a `snapshot_url` + `snapshot_timestamp`** (2026-07-29, audit F16) in
  `legislative/minutes_index.csv`, in each document's markdown front-matter, and in the
  standalone ledger `legislative/wayback_snapshots.csv`. `source_url` still holds the
  county's own (now-404) URL — that is a true historical fact and is never overwritten;
  the snapshot is an addition beside it. Re-derive with
  `python3 legislative/recover_snapshots.py` (Wayback CDX API, polite serial rate).
- `minutes` (173) — the named-era Planning Commission motions (land_use).
- `citysite_ocr` (1,569) / `wayback_ocr` (21) / `citysite_scanned` (19) — the 2015-2020
  era recovered by the 2026-07-26 tesseract backfill.
- Filter audited-primary Council with `provenance IN ('citysite_minutes','wayback_minutes')`.
  The flat CSVs keep every value verbatim; `provenance` marks the recovery channel.

## Correction / override layers (cardinal rule: never in-place edits)

- **`db/vote_overrides.csv`** — the 11 contradictory (motion, person) pairs where a source
  minutes listed a member under two labels (a full-roster AYE template line PLUS a
  deliberate NAY/ABSTAIN/ABSENT dissent line — the born-digital minutes' `Aye: N` count is
  frequently wrong, e.g. "Aye: 5" over 7 names). Each has a documented `resolution` (a
  legal vote value) + `reasoning` verified against the primary minutes. The build FAILS
  LOUDLY on any uncovered conflict — a value is never silently arbitrated. **5 of the 11
  correct a buried dissent** (Worthen 2021-10-12, Beus 2023-08-08, Goodlander+Garrity
  2025-06-24 #9, Garrity 2025-07-22 #12) — these raised `v_contested` from 178 → 182. Vote
  total is unchanged (11,788): each pair was always one db row; the override only fixes
  *which* value and makes the choice auditable.
- **`db/person_aliases.csv`** — the documented person-key canonicalization: OCR typos
  ("David Ericksqn", "Nolan Gunnel"), role-prefix leakage ("Councilmembers Nolan Gunnell",
  "Vice-Chair Kathryn Beus"), and mover/seconder surname fragments ("Erickson", "Ward")
  are unified onto the canonical member. This collapsed the raw persons → **30** (20 council
  members + 2 honest unattributed placeholders "Councilmember"/"Vice-Chair" + the non-voting
  "County Executive David Zook") with vote total unchanged (fragments carry 0 votes; typos
  never co-occur with the canonical name on one motion). Two attribution fixes are noted in
  the file: `Erickson Nolan Gunnell` (comma-split failure) → Nolan Gunnell, and a corrupted
  6th-aye token `Kurt` (2025-02-06 PC #12) → Lane Parker (roster evidence). The flat
  all_votes.csv keeps every verbatim name — unification is a db concern.

Both files are consumed by `db/build_db.py`; the shared `scripts/db_build_lib.py` is
imported READ-ONLY. Rebuild: `python3 db/build_db.py` (idempotent; APPENDABLE — legislative
motion-ids are stable, land_use PC is appended last).

## Honest gaps (data, never filled)

- **Legislative:** the **312 vs 305** count discrepancy is resolved — 312 was the raw URL
  count; 305 documents are indexed, 4 are genuinely lost (below), and 2 were SUPERSEDED
  duplicate postings of the same meeting dropped 2026-07-26 (2022-10-25 "APPROVED" superseded
  by "FINAL APPROVED"; 2024-11-26 "(approved)" superseded by "amended-"). Both had been
  double-counting their meeting's motions (2022-10-25 held 32 motions where the source has
  16). The 312th URL, `12-05-20147 …pdf`, has an unparseable date and is logged below.
- **Legislative:** 4 genuinely-lost minutes dates in `legislative/minutes_unrecovered.csv`
  (2015-02-24, a 2023 unparseable-date closed-meeting declaration, 2024-02-13, 2025-02-25 —
  404 on live + Wayback). Floor 2015; **1995–2014 depth** is a queued OCR-backfill (pipeline
  ready, not run). The 2021 transitional grammar is a documented lower-fidelity audit flag.
- **Planning Commission:** **14 held meetings with agendas but NO minutes posted** on the
  county site (`land_use/minutes_index.csv` `NoMinutesPosted`) — **PMN body 1479 is the
  recovery channel, not yet pulled** — + 4 recent 2026 meetings pending approval. Named
  voters exist only 2024-11+ (source ceiling).
- **Elections:** 2011/2015/2017/2019 municipal — no county publication exists; 2024 canvass
  is image-only (unparsed); 2006–2016 GEMS + 2018 HTML catalogued-not-parsed; Nibley 2021
  RCV lives only in Nibley's own records.
- **Ordinances:** **8 catalog ordinances are named on the Council floor but not uniquely
  linkable** (2020-12, 2021-09, 2021-14, 2022-01, 2022-26, 2022-34, 2022-35, 2023-02) —
  each carries its reason in `index.csv` `notes`. Notably **2022-01's only approve motion
  FAILED** on 2022-01-25 even though the codified source-note reads `Ord. 2022-01,
  1-25-2022`; both readings are retained and neither is arbitrated. 2021-09's adoption was
  omitted from the 2021-03-09 minutes and added by a 2022-11-22 correction motion, so its
  roll call survives only as an attachment inside the 2022-11-22 document (mis-dated to the
  host meeting — honestly unlinked). Pre-2021 scanned-era ordinances stay honestly
  unmatched (no named roll call to link).
- **Legislative RAW is a DELIBERATE 25-of-305 SLICE (owner decision, 2026-07-29).**
  `legislative/raw/` holds **only the 25 dead-URL documents** — 22 `wayback_minutes` +
  3 `wayback_ocr`, every one of whose live county URLs returns **404** — **150 MB**,
  ledgered in `legislative/raw_index.csv` (md_path ↔ raw_path ↔ the exact capture used,
  bytes, sha256), re-runnable and idempotent via `python3 legislative/fetch_raw_wayback.py`.
  **The other 280 documents (2.80 GB, appended media packets up to 47 MB each) are NOT
  retained**: their `source_url`s returned HTTP 200 on 2026-07-29, so they are re-fetchable
  on demand and their provenance pointers are already recorded.
  *Why these 25 are the exception:* they are the module's only irreplaceable bytes, and
  Cache is the repo's least-settled corpus (160 documents OCR'd 2026-07-26; four extractor
  bugs found in that pass) — so **image-level re-verification ("did the OCR read this
  right?") is a live need here specifically, and only the original image can answer it.**
  Each retained PDF is verified three ways (`%PDF` magic, size floor, intact `%%EOF`
  trailer) and its page count matches the front-matter `pages` recorded when the markdown
  was extracted — 25/25 match. **5 of the ledger's chosen captures are truncated by the
  Internet Archive at exactly 1 MiB** (2024-01-09, 03-12, 03-18, 03-26, 06-25 — a real
  defect in that capture, reproducible on re-request); the fetcher detects this via the
  `%%EOF` test and falls back to the archive's other captures, all five of which are
  complete. `wayback_snapshots.csv` still names the EARLIEST capture (closest to
  publication); `raw_index.csv`'s `snapshot_used` names the one actually retained.
- **The duplicate-file double count — FOUND AND CLOSED 2026-07-29 (audit F17).** 12
  un-indexed duplicate markdown files sit under `legislative/minutes/` — second copies of
  an indexed document (`2021-12-14_council.md` ≡ `2021-12-14_council_2.md`, and 11 more
  across 2021/2023/2024/2025; 9 byte-identical, the other 3 differing only in the
  `snapshot_url` front-matter later added to the indexed twin alone). `minutes_index.csv`
  lists only the `_2` form, but `extract_votes.py` used to walk the DIRECTORY, so **107
  motions / 640 votes were exact duplicates** (~3% / ~5%).
  **Root cause:** `fetch_minutes.py`'s collision guard compared the stored `source_url`
  with `re.search(r"source_url:\s*(\S+)")` — and every Cache source_url contains SPACES
  ("… 12-14-21 APPROVED sm.pdf"), so `\S+` truncated it at the first space, the equality
  never held, and re-fetching an already-present document minted a `_2.md` second copy
  instead of overwriting in place. Both ends are fixed: the regex now matches the whole
  line, and **`extract_votes.py` is INDEX-DRIVEN** — the catalogue is the canonical
  statement of what documents exist, the directory is only a working area. Indexed-but-
  missing and on-disk-but-unindexed files are printed on every run, never silently dropped.
  **The 12 duplicate FILES are deliberately LEFT ON DISK** (this repo has no version
  control; they are inert now that nothing walks the directory, and they are the honest
  artefact of the fetch history). They are *not* in `minutes_index.csv`, so they are
  invisible to every index-driven consumer; pre-repair copies of everything touched are in
  `_backups/2026-07-29-cachedup/`. Verified: the rebuilt db is row-for-row identical to the
  old one minus exactly those 107 motions / 640 votes, and all 17 ordinance links survived
  the motion_id renumbering (the derived linker's first real test).
- **Plans:** the current 2023 General Plan is StoryMap-only (no PDF text to extract).
- **GIS:** catalog only — UGRC `HousingUnitInventory` has no Cache rows (not catalogued).

## Notes for federation

DERIVED — after any `db/build_db.py` rebuild, **rerun `python3 db/link_ordinances.py`**
and only then does the repo owner regenerate `gov.db` with
`python3 scripts/build_cities_db.py` (NOT run by module/closing agents). Cache's
`ordinance.motion_id` references the **per-county** db motion_id (the SLCo convention;
the federation loader remaps to the global id) — **which is exactly why a rebuild without
the re-link silently points every ordinance at the wrong roll call** (audit F8 follow-up,
2026-07-29). `legislative/minutes_index.csv`'s new `snapshot_url`/`snapshot_timestamp`
columns are additive; the search-layer loader reads by column name and ignores extras
(federating them is an open, optional enhancement — the ledger CSV is authoritative today). County PC motions carry NULL `disposition`
consistent with other counties (not yet computed). Register `cache_county` in
`registry/entities.csv` + `registry/relationships.csv` (each Cache city `within
cache_county`, `cache_county within ut_state`) and set `db_rel_path` before federating;
the `elections/` by_contest + `projections/` + `gis/` loaders are already generalized.
