# Draper City Council — data repository

Canonical datasets about the Draper City Council and Planning Commission, modeled on the Salt Lake
City reference repo and conforming to the collection-wide standard at
`/Users/tysonwelsh/civic-data/SCHEMA_SPEC.md` (check with `scripts/validate_city.py`). Built by the
`build-city-data-repo` skill. Data floor: **2020** (Draper incorporated **1978** — full modern
history exists; 2020 is a normal floor, not an incorporation edge like Millcreek).

```
meeting_minutes/      City Council minutes (markdown) + extracted votes (all_votes.csv,
                      motions_std.csv) + retained raw/ originals
planning_commission/  SAME schemas for the Planning Commission (body=PlanningCommission)
public_comments/      AVAILABILITY.md + HEADER-ONLY all_comments_clean.csv — comments are
                      HONEST-EMPTY (submit-only; in-person / email public.comment@draper.ut.us)
election_results/     Salt Lake County SOVC filtered to Draper council+mayor races (ALL at-large)
geo/                  two-county precinct union + address -> Draper-membership/"At-Large" tool
db/                   relational SQLite (db/civic.db; build_db.py + build_referrals.py; regenerable)
weeks/                DERIVED weekly bundles tying Council minutes + votes together
build_weeks.py        regenerates weeks/ (MEETING_WEEKDAY = Tuesday = 1)
fetch_new.py          incremental refresh driver (Granicus MinutesViewer, both datasets)
recon.md              map of this city's data sources (provenance) — the honest-gap record
SOURCES.md            human-readable source index (companion to sources.csv)
VERIFICATION.md       independent QA + external election cross-check (REQUIRED; extend with
                      dated addenda whenever the data is repaired or re-audited)
```

## The structural facts that make Draper different
1. **5 AT-LARGE councilmembers + a NON-voting Mayor.** Draper uses Utah's **council–mayor
   (executive-mayor) form**: **five councilmembers, ALL elected AT-LARGE — there are NO districts** —
   plus a **separately-elected Mayor** (the executive) who **presides but casts no council vote**. A
   full council roll-call tops out at **5** (never 6). **Mayor Troy K. Walker** appears in **exactly
   one** vote row in the whole corpus — see fact 2. This is like South Jordan / Taylorsville
   (mayor uncounted) but **all at-large**, unlike those districted councils, and unlike Millcreek
   (where the mayor votes on every roll).
2. **The one mayoral tie-break (2024-10-15).** Mayor Walker cast a single tie-breaking `Aye` on
   **motion 3, Ordinance #1625** (`result = 3-2 Pass`) when the five members split **2 Aye
   (Green, Roberts) / 2 Nay (Johnson, T. Lowery) / 1 Recuse (F. Lowry)**. It is stored as an
   **ordinary `Aye` vote row** (no special note field, unlike Park City) and is his only appearance in
   any vote row. `Mayor Troy K. Walker` is in the db `person` table solely because of it.
3. **Granicus Recap-vs-Minutes trap.** Draper publishes minutes on Granicus
   (`draper.granicus.com`, ViewPublisher `view_id=1`) as born-digital text PDFs via MinutesViewer.
   For recent meetings the portal offers BOTH a tally-only 1-page **Recap** and the full **Minutes**
   behind a JS document selector. **Always keep the full Minutes (named `Yes/No/Absent` roll-call
   grids) and drop the Recap.** The build did this; a recap-only meeting with no adopted Minutes yet
   (2026-07-07) is **withheld and logged**, never stubbed with the Recap. Verified in `VERIFICATION.md` §4.
4. **PC is the busy, contested body.** The Planning Commission (meets **Thursday**) runs a heavy
   land-use docket — **214 contested** motions vs the Council's 15 — and keys items to case numbers
   **`YYYY-NNNN-TYPE`** (`USE`/`SUB`/`MA`/`VAR`/`SP`; 184 distinct in the motion text). Named grid is
   `Yes / No / Abstained / Not-Participating / Absent`; **Final Action vs Positive Recommendation** is
   preserved verbatim in `result`.

## Index + vote schemas are the collection standard
- `minutes_index.csv`: `date,year,title,slug,path,source,source_url,format` — one row per document on
  disk; unrecoverable meetings live in `minutes_unrecovered.csv`, never as stub/wrong-doc rows.
  `source = granicus` (292 docs) **or `pmn`** (6 docs PROMOTED 2026-07-16 from `pmn_backfill/` — the
  3 healed broken-stub gaps + 3 August Truth-in-Taxation specials Granicus never listed);
  `format = text` (all 298 docs are born-digital — no OCR seam).
- `all_votes.csv`: the 13-column standard
  (`date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`)
  **+ a documented trailing 14th `provenance` column** (2026-07-16): `minutes` = audited Granicus
  doc, `pmn_minutes` = PMN-recovered promoted doc (43 council + 89 PC rows);
  `result` and `motion_type` are city-verbatim — **cross-city comparison goes through
  `motions_std.csv`** (normalized outcome/tallies/motion_type_std) and the repo-root `crosswalks/`.
- Raw originals are retained under each dataset's `raw/` and are never deleted.

## The join key
Everything keys to the **council meeting weekday (Tuesday** — 1st & 3rd). The **PC meets Thursday**;
its records join on their own date. `build_weeks.py` buckets Council records onto the Monday grid
(`MEETING_WEEKDAY = 1`). Elections are point-in-time (Nov, odd years) and are NOT in the weekly
bundles — they join by **person + year** (Draper is at-large, so **no district key**; normalize names
— election names are UPPER-CASE).

## How to analyze (which artifact for which question)
- **Aggregate / time-series**: the canonical flat tables — `meeting_minutes/all_votes.csv`
  (+ `motions_std.csv`) and `planning_commission/all_votes.csv`. A blank member/vote cell = a
  genuinely tally-only ("voice/tally-only") motion; some 2020–2021 narrative motions name only the
  in-favor side (a source limit, never Present-filled).
- **Relational / cross-body** (PC recommendation → council outcome; member records): `db/civic.db` —
  read `db/SCHEMA.md` first; start from views `v_referral_chain`, `v_project_timeline`,
  `v_member_record`, `v_contested`. The `referral` layer is reconstructed + scored (**5 links, all
  medium**) — respect the confidence column.
- **Meeting-level / contextual**: the `weeks/<Tuesday-week>/` bundle (start with `summary.md`).
  `weeks/` holds **Council only** (the collection convention — PC is analyzed via its own CSV/db).
- **By member**: join election winners (`election_results/draper_races.csv`) ↔ votes on **person +
  year** (no district — at-large; normalize UPPER-CASE names).
- **By geography**: `geo/address_to_district.py` returns **Draper membership + "At-Large"** — there
  are no council districts to resolve.

## Elections — all at-large; two recovered/re-parsed cycles + an RCV year
- **23 races, 2007–2025**, all **AT-LARGE**; council races are multi-winner "vote-for-N" fields (top
  N vote-getters seat the N open seats). **Mayor Troy Walker won 2013 / 2017 / 2021 / 2025** (all
  cross-checked, `VERIFICATION.md` §10); **Dahlin** won a new **2-year unexpired/short-term** seat in
  2025 (replacing Vawdrey), flagged in `note`.
- **2019 general + 2021 general recovered from raw SOVC** (mislabeled/absent in the shared county
  file). **2025 re-parsed from raw SOVC** because the canonical county long file **undercounts**
  Draper (it dropped Utah-vintage `25DR0N` precinct labels) — the re-parse reconciles to the certified
  totals and matches KSL/*Draper Journal* exactly. See `SOURCES.md` / `TODO.md`.
- **⚠ 2021 was Ranked-Choice Voting** (Draper's RCV pilot). The 2021 council-general row is stamped
  `voting_method=ranked choice (RCV)` (2026-07-19, mirroring Millcreek) and stores **first-choice**
  tallies: the winner (Tasha Lowery) is correct, but `winner_pct` (36.95%) is a first-choice share,
  **not** the RCV final — take the winner, don't quote the pct as a final margin. The 2021 mayor row
  (single candidate, uncontested) stays `plurality`.

## public_comments — HONEST-EMPTY (submit-only)
Draper publishes **no** standalone written-comment archive / eComment / correspondence page. Comment
is taken in-person (3-min limit) and via email to `public.comment@draper.ut.us` (submit-only, not
archived). The only public record is the clerk's third-person paraphrase of in-person speakers inside
the minutes — a *speaker log*, **not** submitted written comment — so `all_comments_clean.csv` is
**header-only by design**. Treat as a legitimate honest zero, not a gap. See
`public_comments/AVAILABILITY.md`.

## Geo — TWO-COUNTY union, NO districts
Draper straddles **Salt Lake (primary) + Utah** counties; `geo/precincts.geojson` is a two-county
union (**33 precincts**, CountyID 18 + 25) and `geo/city_boundary.geojson` is the UGRC boundary.
Because the council is **all at-large**, `address_to_district.py` returns **Draper membership +
"At-Large"** — never a district number. **Salt Lake County administers the entire city election**, so
all races land on the SL County SOVC. See `geo/CLAUDE.md`.

## weeks/ and db/ are derived — regenerate, don't hand-edit
`python3 build_weeks.py` · `python3 db/build_db.py && python3 db/build_referrals.py`. Canonical
sources of truth are the dataset folders (flat CSVs + minutes markdown + retained `raw/`); never edit
files under `weeks/` or the .db. Rebuild `weeks/` after ANY change to the canonical CSVs. Each
subfolder has its own CLAUDE.md/SCHEMA.md with build details.

## Keeping it current
`python3 fetch_new.py --probe` lists Granicus MinutesViewer items newer than the index max for each
dataset (council + PC), excluding dates already indexed or logged in `minutes_unrecovered.csv`.
`--fetch [--dataset meeting_minutes|planning_commission]` downloads new docs → `raw/` → markdown →
`minutes_index.csv`, then runs the dataset's `extract_votes.py` + `validate_votes.py`. **Resolve
recent meetings to the full Minutes, dropping the Recap** (fact 3). Rebuild db + motions_std + weeks
afterward. The Granicus host 403s bare bots — the driver uses a browser UA.

## Analysis guidance
- Councils are high-consensus — **contested votes (any Nay/Abstain/Recuse) are the signal** (db
  `v_contested` = 229: **15 Council + 214 PC** — the PC is where the real contest is).
- Motion types: city-native taxonomy in `all_votes.csv` (Council: Procedural/Administrative,
  Ordinance, Resolution, Land-Use/Zoning, Other, Budget, Contract/Purchase, Appointment, Ceremonial);
  standardized categories in `motions_std.csv`.
- Coverage seams + known gaps are documented in `README.md`, `recon.md`, and `VERIFICATION.md` — read
  those before quantitative claims (especially the mayor's single tie-break, the Recap-vs-Minutes
  trap, the 2021 RCV method, and the 2025 SOVC re-parse).

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-13)
Six source layers, each with its own `CLAUDE.md`/`AVAILABILITY.md`, all `validate_dataset.py`
PASS; none modify the core layer. Join to `all_votes.csv`/minutes by `date` (+ `body`).
- **`packets/`** — **4,721 rows, STORED mode (1.62 GB + 58 MB sidecars)** — Draper's staff
  reports are separable text PDFs (the lehi pattern), so 339 agendas + 1,821 staff reports
  + 2,047 exhibits are on disk (373 oversize exhibits + 134 bundled full_packets index-only;
  URLs in `dropped_oversize.csv`). Council 2,939 / PC 1,594 / CRA+RDA+MBA 188. 3,591 text
  sidecars feed fts_packet. THREE-era portal archaeology (Granicus /URI-outline era 2023-09+,
  NovusAgenda 2020-04→2023-08, DocumentViewer early-2020 — broken file:/// URIs leak the
  Novus item ids that made agency packets recoverable) — see packets/CLAUDE.md.
  - **doc_class layer** (2026-07-16; index-only follow-ups resolved 2026-07-17): 922 classified
    (staff_report 895 / plan_amendment 18 / development_agreement 9; member_memo honest-empty),
    **922 ok text-linked + 0 needs_ocr, 0 index-only** (the 2 needs_ocr Avery-Townhomes
    image-only staff reports were vision-transcribed to ok 2026-07-19) — the 243 oversize >4 MB
    exhibits were fetched/extracted/discarded (2.74 GB → 204 MB text; §9 discard-binary;
    0 404/auth-wall), gates 100% — see packets/CLAUDE.md.
- **`housing_plans/`** — **12 rows**: 2019 General Plan (current amended ed.), MIH element
  as Ord #1561 (2022) + GP Ch.4 per Ord #1623 (2024) — both enacting votes cross-verified —
  city annual reports 2020/22/23/24/25 (prior years Wayback-recovered; the CMS silently
  replaces media in place) + state compilations. 2021 annual report unrecovered (Wayback
  1-MiB truncation); no compliance letter exists.
- **`ordinances/`** — **276 ordinances #1344→#1726 (272 in-window, 168 land-use)** from PMN
  Recorder adoption summaries (1-page notices, NOT full text; code host American Legal,
  bot-gated; notices live under council body 5555, not the Recorder body). Linkage: **182
  high** / 69 within_source (2020→mid-2021 — the Recorder posted zero 2020 notices) / 18
  low / 2 medium / 5 none. Tie-break Ord #1625 reconciles exactly. **#1494/#1496/#1497
  RESOLVED high 2026-07-16** — the promoted 2021-07-20 minutes carry their enacting motions
  (m3/m4/m5, each 5-0 Pass). 5 documented Recorder errors handled via override tables
  (verbatim retained).
- **`pmn_backfill/`** — PMN entity **114** (council 5555 + defunct 379; PC 383; CRA 7261 +
  RDA-era 382; MBA 381; HPC 380; ZA 6647). **6 meetings recovered**: the 2021-07-20
  broken-stub council minutes (full roll grids), 2 PC stub-dates, and **3 August
  Truth-in-Taxation specials absent from Granicus entirely** (a systematic listing gap —
  check PMN for TnT specials in any Granicus city). Draper PMN dates are EXACT — use
  exact-date diffing (±4d masks gaps here). **ALL 6 PROMOTED into the audited layers
  2026-07-16** (`source=pmn` index rows, `provenance=pmn_minutes` vote rows; see
  `VERIFICATION.md` addendum). The stale PC 2024-03-14 unrecovered row and the phantom
  Council 2023-10-15 row (a Sunday; both sources hold the real 10-17 minutes) were removed
  in the same pass.
- **`transcripts/`** — Granicus is video-complete (**1,426 clips catalogued**, Council 155 /
  PC 147 in-window) but captions are EMPTY STUBS on every clip (probe by byte size, not
  HTTP status); the city YouTube is promo-only. Captions exist only via the third-party
  "Utah Record" mirror: 25 meetings, 2026-01→2026-04, ASR; 10 samples fetched (~180k words).
  2020–2025 is video-complete but caption-less — Whisper candidates proposed (the
  2024-10-15 tie-break meeting first; direct MP4 URLs in granicus_clips.csv).
- **`campaign_finance/`** — **125 rows / 148 PDFs, 2011–2025** (9 text / 116 scanned).
  Headline: the **Tyler EagleWeb GRAMA portal is guest-GET-able** and holds per-candidate
  election records — the ONLY surviving source for the whole 2023 cycle. ACQUISITION LAYER
  only. FLAGS (not edited into elections): 2025 canceled 4-yr race corroborated (Green +
  Lowery filed CF; Turner withdrawal affidavit found); **2019: a primary was scheduled
  then NOT held** (12 declared, due-date notice retained) — settles the recon caveat;
  Wayback truncates >1 MiB PDFs (always verify %%EOF).
