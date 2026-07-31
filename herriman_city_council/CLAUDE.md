# Herriman City Council — data repository

Canonical datasets about the Herriman City Council (with in-session **CDRA / HCSEA / HCFSA**
agency bodies) and Planning Commission, modeled on the Salt Lake City reference repo and
conforming to the collection-wide standard at `/Users/tysonwelsh/civic-data/SCHEMA_SPEC.md`
(check with `scripts/validate_city.py`). Built by the `build-city-data-repo` skill. Data
floor: **2020** (Herriman incorporated **1999** — full modern history exists; 2020 is a
normal floor).

```
meeting_minutes/      City Council + CDRA/HCSEA/HCFSA minutes (markdown) + extracted votes
                      (all_votes.csv, motions_std.csv) + retained raw/ + fetch_new.py refresh
planning_commission/  SAME schemas for the Planning Commission (body=PlanningCommission)
public_comments/      AVAILABILITY.md + header-only all_comments_clean.csv — comments are
                      HONEST-EMPTY (submit-only PrimeGov eComment / Request-To-Speak)
election_results/     Salt Lake County SOVC results filtered to Herriman council+mayor races
geo/                  official 4-district FeatureServer polygons + address→district tool
db/                   relational SQLite (db/civic.db; build_db.py + build_referrals.py)
weeks/                DERIVED weekly bundles tying minutes + votes together
build_weeks.py        regenerates weeks/ (MEETING_WEEKDAY = Wednesday)
fetch_new.py          incremental refresh driver (PrimeGov council + PC)
recon.md              provenance map written BEFORE acquisition. ⚠ its §4 assumed the Mayor
                      was NON-voting (max tally 4) — WRONG; corrected here + in VERIFICATION.md
SOURCES.md / sources.csv   human + machine-readable per-document source index
VERIFICATION.md       independent QA + external election cross-check (REQUIRED; extend with
                      dated addenda on any repair/re-audit)
```

## The structural fact that makes Herriman different — the MAYOR VOTES
Herriman uses Utah's **six-member council form in which the Mayor is a full voting member**
(the **Millcreek** model). Four district councilmembers (**D1–D4**) **plus the Mayor** all
cast roll-call votes, so a full council roll tops out at **5** (never 4). This is the single
most important structural fact for anyone counting tallies or building rosters:
- A `Mayor <Name>` entry in a roll call is a **real vote**, not a presiding non-voter — map
  it to the Mayor as a voting member.
- Verified at source (`VERIFICATION.md` §4): Mayor **David Watts** (2020–2021) casts a
  decisive **Nay** on a 3:2 vote (2020-01-08 m5); Mayor **Lorin Palmer** (2022+) votes in
  every roll (e.g. 2023-01-11 m2, and a 4-1 on 2025-01-22 m6 with Ohrn dissenting). Watts =
  167 vote rows, Palmer = 478 council vote rows.
- ⚠ **This CORRECTS `recon.md` §4**, which assumed "max council tally = 4, Mayor non-voting."
  Do not follow the recon's assumption — follow the verified data.
- Contrast: Taylorsville / South Jordan mayors are **non-voting** (max 5, mayor excluded);
  Herriman's Mayor **is** the 5th vote (like Millcreek).

## Agency bodies (CDRA / HCSEA / HCFSA) — the `body` column
Three district agencies convene around council meetings, published as **separate minutes
docs** (a few via the portal, most via PMN) and tagged by `body` (motions):
- **CDRA** — Community Development & Renewal Agency (64 motions)
- **HCSEA** — Herriman City Safety Enforcement Area (39 motions)
- **HCFSA** — Herriman City Fire Service Area (31 motions)
Default `body=Council` (1,209 motions). The same officials sit as
"Trustee/Board Member/Director" (the mayor as Chair).
✅ **PROMOTED (2026-07-16):** the 2026-07-13 correction ("in-meeting captures complete"
was WRONG — standalone agency minutes on Utah Public Notice are ABSENT from the combined
council docs) is now RESOLVED: all 29 absent standalone agency minutes (30 recovered −
one 2021-01-13 CDRA duplicate) are merged into `meeting_minutes/all_votes.csv` with
**`provenance=pmn_minutes`** (a documented trailing 14th column; audited rows =
`minutes`). Merge driver: `meeting_minutes/extract_backfill_votes.py` (run it after any
`extract_votes.py` re-run, or the pmn rows drop out).

## Roster of 9 — join carefully
Current: Mayor **Lorin Palmer**, **Henderson** (D1), **Hodges** (D2), **Basham** (D3, from
2026), **Anderson** (D4, from a 2025 off-cycle special). Earlier voters: Mayor **David
Watts** (2020–2021), **Clint Smith** (2020–2021), **Sherrie Ohrn** (2020–2025), **Steven
Shields** (2020–2025). **Lorin Palmer sat on the Planning Commission (2020–2021) before
becoming Mayor** — one `person`, two `role` rows; a person-level join spans both bodies.
**2020 `Lorin Powell` source typo** (5 PC rows since the 2026-07-16 promotion) conflates
Andy Powell + Lorin Palmer — kept verbatim, never guess-merged; flag it on any 2020 PC
person join. One more verbatim oddity: the promoted 2020-05-27 HCSEA roll prints
**"Trustee Nicole Martin"** (a 2019-era trustee; the attendance line lists Shields) —
a stale-roll clerk anomaly, retained as printed (1 vote row).

## Index + vote schemas are the collection standard
- `minutes_index.csv`: `date,year,title,slug,path,source,source_url,format` — one row per
  document on disk. `source` ∈ `primegov` / `s3-legacy` (2020 backfill from the legacy
  `herriman-agendas` AWS bucket — PrimeGov only serves 2021-01+). `format` ∈ `text`/`ocr`.
  The 2020 interior gaps were believed to be real COVID cancellations. ⚠ **CORRECTION
  (2026-07-13, PMN backfill): only HALF right** — 9 of the 2020 gaps are PROVEN
  cancellations (proof notices retained in `pmn_backfill/`), and **12 were real meetings**
  (e.g. 2020-03-25, 05-13, 09-09 council, 09-23, 10-14, 11-05, 12-09; PC 12-03).
  ✅ **PROMOTED (2026-07-16):** those recovered minutes (and every other recovered doc)
  are now in the vote layer with `provenance=pmn_minutes`. `minutes_unrecovered.csv` now
  EXISTS in both datasets for the only remaining true gaps: 2020-07-29 joint (never
  posted; PMN audio exists), PC 2022-04-21 (PMN "Minutes" file is a mislabeled zoning
  use-table) and PC 2023-11-01 (only a DRAFT exists — kept as a pmn_backfill sidecar).
- `all_votes.csv`: the 13-column standard
  (`date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`)
  **+ a documented trailing 14th `provenance` column since 2026-07-16**
  (`minutes` = audited portal/S3 doc; `pmn_minutes` = PMN-recovered doc promoted by
  `extract_backfill_votes.py`; the recovered docs live in `pmn_backfill/text/`, which is
  what their `source` paths point at). `result` and `motion_type` are city-verbatim —
  **cross-city comparison goes through `motions_std.csv`** (normalized) and the repo-root
  `crosswalks/` tables.
- Raw originals are retained under each dataset's `raw/` and are never deleted.

## The join key
Everything keys to the **council meeting weekday (Wednesday** — 2nd & 4th Wednesday, work +
general captured in one combined minutes doc). The **PC meets Wednesday too** (1st & 3rd);
its records join on their own date. `build_weeks.py` buckets every record onto the weekly
grid. Elections are point-in-time (Nov, odd years) and are NOT in the weekly bundles — they
join by **person + year + district** (normalize names — election names are UPPER-CASE).

## How to analyze (which artifact for which question)
- **Aggregate / time-series**: the canonical flat tables — `meeting_minutes/all_votes.csv`
  (+ `motions_std.csv`) and `planning_commission/all_votes.csv`. Short procedural motions are
  **tally-only** (`all voted aye`, one placeholder row, member blank) — honest, not a miss;
  substantive motions carry a full named Mayor+member roll.
- **Relational / cross-body** (PC recommendation → council outcome; agency co-actions; member
  records): `db/civic.db` — read `db/SCHEMA.md` first; start from views `v_referral_chain`,
  `v_project_timeline`, `v_member_record`, `v_contested`. The `referral` layer is
  reconstructed + scored (**51 links since the 2026-07-16 promotion: 23 high / 22 medium /
  6 low**) — respect the confidence column; do not quote `low`.
- **Meeting-level / contextual**: the `weeks/<Wednesday-week>/` bundle (start with `summary.md`).
- **By member**: join election winners (`election_results/`) ↔ votes. Mind roster drift and
  Palmer's PC→Mayor move.
- **By geography**: `geo/address_to_district.py` resolves an address to District 1–4.

## weeks/ and db/ are derived — regenerate, don't hand-edit
`python3 build_weeks.py` · `python3 db/build_db.py && python3 db/build_referrals.py`.
Canonical sources of truth are the dataset folders (flat CSVs + minutes markdown + retained
`raw/`); never edit files under `weeks/` or the .db. Rebuild weeks/ after ANY change to the
canonical CSVs. Each subfolder has its own CLAUDE.md/SCHEMA.md with build details.

## Elections — recovered years + one special
**38 races, 2007–2025.** **2019** was **not** a gap (mislabeled in the shared county file —
recovered from the raw SOVC); the **2011** and **2021** generals were likewise recovered from
raw SOVC. **2025 D4 is an off-cycle 2-year short-term special** (Terrah Anderson), flagged in
`note`. All winners/margins cross-checked against outside sources (SLCo canvass, Herriman
Journal, Deseret/KUTV) in `VERIFICATION.md` §7 — no material mismatch (repo = final certified
canvass; election-night reports run slightly lower).

## public_comments — HONEST-EMPTY (submit-only)
Herriman publishes **no** standalone written-comment archive. Its only channels are the
PrimeGov **eComment** ("Add a new comment") form and **Request To Speak** — both
**submission** mechanisms tied to a live/upcoming meeting. `all_comments_clean.csv` is
**header-only** by design (14-col schema, 0 rows); the completed audit is in
`public_comments/AVAILABILITY.md`. Treat as a legitimate honest zero, not a gap.

## Geo — official 4-district polygons
Unlike precinct-derived cities, Herriman publishes an **official 4-district FeatureServer**;
`geo/districts.geojson` holds those polygons and `precincts.geojson` the 44 precincts.
`geo/address_to_district.py` resolves an address/point to District 1–4 (tested: City Hall →
D2; the Mayor is citywide, never returned). Current/post-redistricting vintage — a
pre-redistricting address near a moved boundary may mis-assign.

## Keeping it current — APPEND-ONLY ingest (2026-07-19)
`python3 fetch_new.py --probe` (READ-ONLY, default) lists PrimeGov Minutes items newer than
the index max for each dataset (council committeeId 3, PC committeeId 14), excluding dates
already indexed, and writes `refresh_probe.json`.

`python3 fetch_new.py --ingest [--dataset meeting_minutes|planning_commission]` is the
**safe refresh path**: it downloads ONLY the genuinely-new minutes → `raw/` → single-file
markdown → **APPENDS** rows to `minutes_index.csv` via `scripts/refresh_lib.append_index_rows`
(dedups on `path`, re-sorts, logs `fetch_log.csv`), then runs `extract_votes.py` →
**`extract_backfill_votes.py`** → `validate_votes.py`. It **never regenerates** the index or
the markdown corpus, so curated / PMN-promoted / S3-2020 / recovered rows are preserved.
Rebuild db + weeks (+ `../scripts/normalize_motions.py`) afterward. Idempotent (no-new →
byte-identical index) + resumable. Browser UA (the portal 403s bare bots).

⚠ **`--build-md` and `--full-build` are DESTRUCTIVE** full index+markdown rebuilds that
rewrite `minutes_index.csv` from the PrimeGov+S3 harvest lists — they DROP every curated /
PMN-promoted / recovered row not in the harvest (proven 2026-07-19; the run was reverted
byte-for-byte). They now **REFUSE unless `--force-full-rebuild` is also passed** (auto-backing
up the index to `_backups/<date>-herriman-fetch/` first) and print a loud warning. **They are
NOT a refresh step — use `--ingest`.**

⚠ **CRITICAL PMN chain:** any bare `extract_votes.py` re-run REWRITES `all_votes.csv` from the
audited JSON only; **`extract_backfill_votes.py` MUST be re-run after it** or the 962
PMN-recovered rows (mm 690 + pc 272, `provenance=pmn_minutes`) silently drop. `--ingest`
chains this automatically. (mm was 677 before the 2026-07-20 short-doc audit recovered the
2022-02-09 RCCM minutes, +13 rows.)

## Analysis guidance
- Councils are high-consensus — **contested votes (any Nay/Abstain) are the signal** (db
  `v_contested` = 88 motions); `summary.md` surfaces them per week.
- Motion types: city-native taxonomy in `all_votes.csv` (see each `CLAUDE.md`); standardized
  categories in `motions_std.csv`.
- Coverage seams + known gaps are documented in `README.md`, `recon.md`, and `VERIFICATION.md`
  — read those before quantitative claims (especially the **mayor-votes** correction, the
  PrimeGov + 2020-S3 two-portal seam, and the CDRA/HCSEA/HCFSA `body` split).

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-13)
Six source layers, each with its own `CLAUDE.md`/`AVAILABILITY.md`, all `validate_dataset.py`
PASS; none modify the core layer. Join to `all_votes.csv`/minutes by `date` (+ `body`).
- **`packets/`** — **372 packets INDEX-ONLY** (Council 190 / PC 121 / CDRA+HCSEA+HCFSA 53 /
  Joint 8; 2020→2026; 11.43 GiB probed → not stored; live URLs + exact sizes). The legacy
  `herriman-agendas` S3 bucket DOES hold 2020 packets (32 indexed; `+Packet.pdf` key grammar
  found via Wayback). Gotcha: this PrimeGov mis-handles HEAD — sizes via 1-byte Range GETs;
  always download via `CompiledDocument?meetingTemplateId=` (blob URLs are time-limited SAS).
- **`housing_plans/`** — **11 docs**: "Herriman Next" 2022 General Plan (+ 2030 land-use map
  + the 2013 "Herriman 2025" predecessor — 2025 is a HORIZON year, not a date), MIH plans
  2019 (Wayback-recovered) + 2022 w/ signed Ord 2022-38 (whose 5-name roll independently
  confirms the voting mayor), city-filed 2020/2021 annual reports, state compilation
  excerpts 2023/24/25 + SB 34. No HCD compliance letter exists.
- **`ordinances/`** — **274 ordinances (2014-25→2026-14; 194 in the 2020+ window, 130
  land-use).** Full signed texts from the MunicipalCodeOnline public S3 bucket (111 PDFs —
  the codifier UI is bot-gated; list `municipalcodeonline.com-new/herriman/ordinances/
  documents/` first) + 190 PMN Recorder adoption notices (HTML-only, bodies 1287+1155).
  Linkage (2020+): **125 high** / 6 medium / 9 low / 42 within_source / 12 none. 10
  documented Recorder/minutes typo-overrides in `build_index.py` (verbatim retained).
  Recorder notices double as a minutes-completeness oracle (proved 7 no-minutes dates).
- **`pmn_backfill/`** — PMN entity **155** (council 1155, PC 1151, CDRA 2256, HCSEA 6239,
  HCFSA 7553, appeals 1171, joint 1251). **NOT a superset city: 72 minutes recovered**
  (22 council incl. the 2021-01-13 RCCM fetched 2026-07-16 + the 2022-02-09 RCCM recovered
  2026-07-20, 13 PC, 5 joint, 30 standalone agency, 2 appeals) **+ 9 proven 2020
  cancellations**. ✅ **PROMOTED 2026-07-16 (+2022-02-09 on 2026-07-20)**: 67
  docs merged into the vote layer (`provenance=pmn_minutes`); NOT promoted: 2021-01-13
  CDRA (duplicate), PC 2023-11-01 (draft), PC 2022-04-21 (mislabeled non-minutes), the 2
  **AppealAuthority** hearings (no appeals body in the city model — catalogued only;
  modeling them is an open follow-up). Only 2020-07-29 joint minutes remain truly missing.
- **`transcripts/`** — YouTube "Herriman City" (/streams): **677 meeting videos,
  2017-11→2026-07** (Council 465 / PC 180 / Joint 21), ASR captions on everything, zero
  manual; 10 sample VTTs. PrimeGov `ListArchivedMeetings` carries a clerk-entered `videoUrl`
  per meeting (authoritative map; 5 unlisted videos; 2 clerk date errors resolved by title).
  **41 substantive no-minutes videos** (2022 council cluster, joint sessions, ~15 PC dates)
  — many now covered by pmn_backfill; ASR is the record for the rest. PC met THURSDAY
  through ~2022, Wednesday after — don't weekday-infer.
- **`campaign_finance/`** — **50 filings / 48 distinct docs, 2021/2023/2025** (17 text / 33
  scanned); 2021+2023 exist ONLY via Wayback (the Lunasoft elections page is rewritten each
  cycle — harvest 2027 before turnover); every race candidate covered. **ACQUISITION LAYER
  only.** FLAG: a **2021 mayoral PRIMARY existed** (4 candidates' primary reports + sample
  ballot) but is absent from `election_results/` and the county SOVC — review lead, not
  edited.
