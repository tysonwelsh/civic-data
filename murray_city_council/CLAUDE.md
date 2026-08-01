# Murray City Council — data repository

Canonical datasets about the Murray City Municipal Council and Planning Commission, modeled
on the Salt Lake City reference repo and conforming to the collection-wide standard at
`/Users/tysonwelsh/civic-data/SCHEMA_SPEC.md` (check with `scripts/validate_city.py`). Built
by the `build-city-data-repo` skill, 2026-07-11. Data floor: **2020** (Murray incorporated
**1902** — full modern history exists; 2020 is a normal floor, not an incorporation edge).

```
meeting_minutes/      City Council minutes (markdown) + extracted votes (all_votes.csv,
                      motions_std.csv) + retained raw/ originals + fetch_new.py refresh
planning_commission/  SAME schemas for the Planning Commission (body=PlanningCommission)
public_comments/      header-only all_comments_clean.csv (HONEST-EMPTY — submit-only city)
                      + AVAILABILITY.md audit
election_results/     Salt Lake County results filtered to Murray council+mayor races
geo/                  official 5-district polygons + precinct map + address→district tool
db/                   relational SQLite (civic.db; build_db.py + build_referrals.py; regenerable)
weeks/                DERIVED weekly bundles tying minutes + votes together
build_weeks.py        regenerates weeks/ (MEETING_WEEKDAY = Tuesday)
fetch_new.py          incremental refresh driver (CivicPlus Archive; probes BOTH datasets)
recon.md / SOURCES.md map of this city's data sources (provenance) — portal vendor, URL
                      patterns, and the honest-gap record
VERIFICATION.md       independent QA + external election cross-check (REQUIRED; PASS on
                      every dataset, 0 FAIL; extend with dated addenda on any re-audit)
```

## The structural facts that make Murray different
1. **The MAYOR does NOT vote.** Murray uses Utah's **council–mayor (executive-mayor) form**:
   **five district councilmembers (D1–D5, no at-large seats)** legislate, and a
   separately-elected **Mayor is the executive** who presides over the city but **casts no
   council vote**. A full council roll call tops out at **5** (never 6). This matches
   Taylorsville / South Jordan (mayor uncounted), unlike Millcreek (mayor votes).
2. **Brett Hales: District-5 councilmember (2020–2021) → Mayor (2022+).** Hales cast **190
   council votes from 2020-01-07 to 2021-12-07**, then **won the 2021 mayoralty and took
   office in 2022** — after which he casts **0** council votes (the mayor doesn't vote).
   "Councilmember Hales" and "Mayor Hales" are the **same person**; his 2020–2021 council
   votes are legitimate. He was re-elected mayor in 2025. This is why "Councilmember Hales"
   appears in every 2020–2021 meeting and then vanishes — expected, not a data defect.
3. **The Planning Commission is a separate 7-member appointed body.** Its roll calls top out
   at **7** (not 5) — a PC motion with 7 named voters is correct, not an over-count. It meets
   **Thursday**; the council meets **Tuesday**.
4. **The two historic coverage gaps are CLOSED (PMN recovery 2026-07-13, PROMOTED into the
   audited layers 2026-07-16).** (a) The **2023 council Tyler-TMM gap**: all 18 missing 2023
   meetings (17 regular + the net-new **2023-08-21 joint special with Millcreek**, a
   no-motion discussion session) are now audited minutes (`source=pmn` in the index);
   **2023-07-11 was CANCELLED** (official notice retained in `pmn_backfill/`) — a
   non-meeting, so `meeting_minutes/minutes_unrecovered.csv` is header-only. (b) The
   **PC-ends-2022-11 gap**: 59 PC minutes 2023-01-05 → 2026-05-07 promoted; the ONLY
   remaining minute-less PC meetings are **2025-04-17 and 2025-07-17**
   (`planning_commission/minutes_unrecovered.csv`; other no-minutes PC dates are noticed
   cancellations, and 4 recent 2026 dates were agenda-only at retrieval). All promoted docs
   are born-digital and identity-verified (2023 council via minutes-approval chains — the
   letterhead date is an image). See `pmn_backfill/CLAUDE.md` + `VERIFICATION.md` addendum.

## Index + vote schemas are the collection standard
- `minutes_index.csv`: `date,year,title,slug,path,source,source_url,format` — one row per
  document on disk. `source` = `civicplus` (portal-fetched) or **`pmn`** (the 2026-07-16
  promoted Utah-Public-Notice recoveries: 18 council 2023 + 59 PC 2023–2026; their
  `source_url` is the PMN `files/<id>.pdf` link). `format` = `pdf-text` (born-digital)
  except the documented OCR files.
- `all_votes.csv`: the 13-column standard
  (`date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`);
  `result` and `motion_type` are city-verbatim — **cross-city comparison goes through
  `motions_std.csv`** (normalized outcome/tallies/motion_type_std) and the repo-root
  `crosswalks/` tables.
- **Tally-only motions are unnamed by design.** A voice vote ("Voice vote taken, all
  'Ayes.'" / "A voice vote was made, with all in favor.") records mover + seconder + tally,
  not each Aye; the extractor sets `names_recorded:false` and emits **one blank-member row**
  rather than guessing voters (80 council / 271 PC such motions). A blank member list on a
  passed motion is a **source style, not a missing extraction** — do not read it as an
  error or Present-fill it.
- Raw originals are retained under each dataset's `raw/` and are never deleted.

## The join key
Everything keys to the **council meeting weekday (Tuesday)**; the **PC meets Thursday** and
its records join on their own date. `build_weeks.py` buckets every record onto the Monday
grid (`MEETING_WEEKDAY = Tuesday`). Elections are point-in-time (Nov, odd years) and are NOT
in the weekly bundles — they join by **person + year + district** (normalize names first;
election names are UPPER-CASE, some `(NP)`/suffix variants).

## How to analyze (which artifact for which question)
- **Aggregate / time-series**: the canonical flat tables — `meeting_minutes/all_votes.csv`
  (755 motions / 3,323 rows) and `planning_commission/all_votes.csv` (678 / 2,708), each
  with its `motions_std.csv`. Remember tally-only voice votes are unnamed (see above).
- **Relational / cross-body** (PC recommendation → council outcome; member records):
  `db/civic.db` — read `db/SCHEMA.md` first; start from the standard views. The `referral`
  layer (24 PC→Council links) is reconstructed + scored — respect its confidence column.
- **Meeting-level / contextual**: the `weeks/<Tuesday-week>/` bundle (start with `summary.md`).
- **By member**: join election winners (`election_results/murray_races.csv`) ↔ votes on
  person + year + district. Mind the roster drift — **Hales (D5)→Mayor 2022**, **Dominguez
  (D3) leaves Dec 2024 → Bullen via the 2025 special**, and the 2023 appointees
  (Hrechkosy/Markham/Rodgers/Goodman) voters later replaced.
- **By geography**: `geo/address_to_district.py` resolves an address to District 1–5 (the
  Mayor is citywide, never returned). Murray has **official** 5-district FeatureServer
  polygons (not precinct-derived) + 53 precinct assignments.

## Elections — 21 races, all winners externally verified
- **21 races (13 general + 8 primary)** — the **15** across 2021 / 2023 / 2025 (Mayor +
  council districts) that `clean_elections.py` builds, by-candidate and by-precinct, filtered
  from the canonical `salt_lake_county/elections/` SOVC, **plus 6 hand-appended contest-grain
  rows** (2019 general D1/D3/D5 + 2019 primary D1/D3, added 2026-07-17 from the SLCo SOVC
  re-parse; the **2021 Mayor primary**, added 2026-07-17 and certified 2026-08-01 against the
  city canvass). The 6 appended races have **no** by-candidate/by-precinct rows — a provenance
  boundary, not a gap. Every winner and margin was cross-checked against Salt Lake County /
  Murray Journal / KSL / Ballotpedia — **0 mismatches** (`VERIFICATION.md` §(d)). Mayor
  Brett A. Hales won **2021 and 2025** (and led the 2021 primary 4,952–2,483).
- **2025 "District 3 (2-Year Term)" is an unexpired-term SPECIAL** (Clark Bullen filling the
  seat Dominguez vacated in Dec 2024), flagged in the `note` column so member-term logic
  doesn't read it as a cycle shift.
- **2019 general/primary sit below the 2020 floor** but ARE now carried (owner-approved
  2026-07-17 appends; flagged in each row's `note`).

## public_comments — HONEST-EMPTY (submit-only)
Murray publishes **no** written-comment archive / eComment / correspondence page. Public
comment is taken in-person at meetings and via the `murraycitylive.com` livestream, plus by
email to staff. The only comment content in the public record is the clerk's inline
paraphrase of who spoke inside the minutes — **meeting-record speaker notes, not genuine
written comments** — so no comments table is materialized. `all_comments_clean.csv` is the
standard header-only empty; the verdict is documented in `public_comments/AVAILABILITY.md`.
Treat this as a legitimate honest zero, not a gap.

## weeks/ and db/ are derived — regenerate, don't hand-edit
`python3 build_weeks.py` · `python3 db/build_db.py && python3 db/build_referrals.py`.
Canonical sources of truth are the dataset folders (flat CSVs + minutes markdown + retained
`raw/`); never edit files under `weeks/` or `civic.db`. Rebuild weeks/ after ANY change to
the canonical CSVs. Each subfolder has its own CLAUDE.md/SCHEMA.md with build details.

## Keeping it current
`python3 fetch_new.py --probe` (default; read-only) lists CivicPlus Archive Center items
newer than the index max for each dataset — council (`Archive.aspx?AMID=31`) and PC
(`AMID=33`) — excluding dates already indexed. `--fetch [--dataset meeting_minutes|
planning_commission]` downloads each new date's PDF → `raw/`, converts (pdftotext -layout) →
markdown → `minutes_index.csv` (byte-identical source dupes collapsed), then runs the
dataset's `extract_votes.py` + `validate_votes.py`. Rebuild db + motions_std + weeks
afterward (the CLI prints the reminder). Idempotent + resumable. **The Archive host serves
bare bots but the script uses a browser UA** (matching `meeting_minutes/fetch_minutes.py`).
NB: 2023 council minutes and post-2022 PC minutes may not reappear on the Archive (they moved
to a Tyler Minutes Management SPA) — a probe returning nothing there is expected, not a bug.

## Analysis guidance
- Councils are high-consensus — **contested votes (any Nay/Abstain/Recuse) are the signal**;
  `summary.md` surfaces them per week.
- Motion types: city-native taxonomy in `all_votes.csv` (see each `CLAUDE.md`); standardized
  categories in `motions_std.csv`.
- Coverage seams + known gaps are documented in `README.md`, `recon.md`, `SOURCES.md`, and
  `VERIFICATION.md` — read those before quantitative claims (the 2023 council TMM gap and
  the PC-ends-2022-11 gap are CLOSED as of 2026-07-16; the tally-only unnamed-voice-vote
  style and the two remaining minute-less 2025 PC dates still apply).

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-13)
Six source layers, each with its own `CLAUDE.md`/`AVAILABILITY.md`, all `validate_dataset.py`
PASS; none modify the core layer. Join to `all_votes.csv`/minutes by `date` (+ `body`).
- **`packets/`** — **421 packets INDEX-ONLY** (Council+CoW 232 / PC 186, 2020→2026; 9.39 GB
  HEAD-probed → not stored; live `Archive/ViewFile/Item/<ADID>` + DocumentCenter URLs with
  exact sizes). Covers the 18 TMM-lost 2023 council dates (packets survived on CivicPlus).
  Gotcha: CivicPlus DocumentCenter 404s HEAD requests — sizes came from header-only GETs.
- **`housing_plans/`** — **9 docs**: 2017 General Plan, HB 462 MIH element (Ch. 9),
  adopting Ord. 22-29 (2022-09-20 motion cross-checked, 4-0), state HCD compilation
  excerpts 2023/24/25 + SB 34 (Murray present each year). No HCD compliance letter exists.
- **`ordinances/`** — **166 ordinances / 172 PDFs, O21-10→O26-19; 81 land-use.** Source is
  PMN body 7321 "Public Notices & Ordinances" (the CivicPlus AMID=95 archive is publicly
  EMPTY — check PMN before declaring an ordinance archive absent). Linkage ceiling `medium`
  by construction (motions never print ordinance numbers): **145 medium / 21 low / 0 none** (distinct)
  (rebuilt 2026-07-16 after the minutes promotion landed the 2023 enacting motions; the
  former `none` rows all resolved). 171/172 text sidecars (168 tesseract — the corpus is
  Recorder wet-signature scans). 2020–Apr 2021: 54 adopting motions, no published texts
  anywhere (honest gap). Code host: American Legal (403 bot-protected, not mirrored).
  O26-15 is a city mis-upload (byte-identical to O26-14); clerk-typo "O24-07"→O25-07 noted.
- **`pmn_backfill/`** — PMN entity **213**; council **735**, PC **983**. **80 docs /
  101.9 MB — closed BOTH honest gaps:** 18/18 missing 2023 council meetings (+ 2023-08-21
  net-new joint special; 2023-07-11 proven cancelled) and 59 PC minutes 2023–2026 (2 dates
  genuinely minute-less). 2023 council identity verified via minutes-approval chains (the
  letterhead date is an image). **PROMOTED into the audited layers 2026-07-16** (77 docs;
  the cancellation notice + 2 negative probes stay here as provenance/gap documentation).
- **`transcripts/`** — YouTube channel "MURRAY CITY LIVE" under **/streams** (332 there, 7
  on /videos); murraycitylive.com is just a Wix wrapper. **339 videos, 2019-10→2026-07, ASR
  captions on all**; 10 sample VTTs fetched (owner sample-only policy). **86 videos cover
  the minutes-gap dates** (23× 2023 council, 63× 2023+ PC) — bulk caption fetch proposed.
  Gotcha: YouTube `release_date` is UTC → evening meetings roll +1 day; snap to minutes dates.
- **`campaign_finance/`** — **131 filings, 2017/2019/2021/2023/2025** (39 text / 92
  scanned); every candidate in `election_results` covered; 2017 cycle recovered via
  Wayback→live DocumentCenter ids. **ACQUISITION LAYER only** (no dollar extraction yet —
  not in `cities.db` until structured). **The old "2021 municipal primary (Mayor ×4, D4 ×3)"
  FLAG is CLOSED (2026-08-01).** The **Mayor** primary was real and IS carried by
  `murray_races.csv` (added 2026-07-17; certified 2026-08-01 against Murray's **Board of
  Canvassers' Report**, city docid 12340, retained at `election_results/raw/` — 0 tally
  discrepancies, and it supplied the row's registered-voters/ballots/turnout). The **D4**
  primary was **scheduled but never conducted**: the canvass covers "the offices of City
  Mayor" alone and the contest is absent from the countywide election-night list too, so the
  election layer carrying **no** 2021 D4 primary is CORRECT. The once-filed cause "Galt
  withdrew pre-certification" was an unsourced inference and is wrong on timing — both D4
  general candidates filed 2021-08-03 **Pre-Primary** disclosures, a slot Murray leaves empty
  when a race has no primary. Evidence: `election_results/CLAUDE.md` §2026-08-01.
