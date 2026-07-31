# Midvale City Council — data repository

Canonical datasets about the Midvale City Council, its in-session Redevelopment Agency (RDA),
and the Planning & Zoning Commission, modeled on the Salt Lake City reference repo and
conforming to the collection-wide standard at `/Users/tysonwelsh/civic-data/SCHEMA_SPEC.md`
(check with `scripts/validate_city.py`). Built by the `build-city-data-repo` skill. Data
floor: **2020** (Midvale incorporated **1909** — full modern history exists; 2020 is a normal
floor, not an incorporation edge like Millcreek).

```
meeting_minutes/      City Council + in-session RDA minutes (markdown) + extracted votes
                      (all_votes.csv, motions_std.csv) + retained raw/ originals
planning_commission/  SAME schemas for the Planning & Zoning Commission (body=PlanningCommission)
public_comments/      AVAILABILITY.md — comments are HONEST-EMPTY (submit-only; no published
                      written-comment archive). all_comments_clean.csv is header-only by design
ordinances/           adopted ordinance PDFs (2012-2026) + text sidecars + §9 index with
                      motion linkage (ADDITIVE — expand-city-sources source 3)
election_results/     Salt Lake County SOVC filtered to Midvale council+mayor races
geo/                  official 5-district FeatureServer + 38 precincts + address→district tool
db/                   relational SQLite civic.db (build_db.py + build_referrals.py; regenerable)
weeks/                DERIVED weekly bundles tying minutes + votes together
build_weeks.py        regenerates weeks/ (meeting_weekday = Tuesday = 1)
convert_minutes.py    Revize raw PDF/docx -> markdown converter (pdftotext + OCR fallback)
fetch_new.py          incremental Revize Document Center refresh driver (see "Keeping it current")
recon.md / SOURCES.md provenance map — portal vendor, URL patterns, and the honest-gap record
VERIFICATION.md       independent QA + external election cross-check (REQUIRED; extend with
                      dated addenda whenever the data is repaired or re-audited)
```

## The structural facts that make Midvale different
1. **Six-member council form — the Mayor votes ONLY on ties.** Five district councilmembers
   (D1–D5) legislate; a separately-elected **Mayor presides and casts a vote only to break a
   tie**. A full council roll therefore tops out at **5**. In the whole record the Mayor
   appears in **exactly one** vote row — **Robert Hale**'s 2020-05-05 m14 tie-break (a 2–2
   split the minutes record as "passed 3-2" after his Aye). A literal `Mayor <Name> <vote>`
   line inside a roll block is a genuine tie-break (flagged `mayor_voted:true` by the
   validator); "Mayor Pro-Tem <Name>" is a councilmember chairing, not a mayor vote. This is
   unlike Taylorsville/South Jordan (mayor never votes) and unlike Millcreek (mayor is a full
   5th voter). See `meeting_minutes/CLAUDE.md`.
2. **The Gettel council→mayor transition — join carefully across it.** **Dustin Gettel** votes
   as **councilmember (D5)** 2020-01-07 → 2024-12-10, then — after Mayor **Marcus Stevenson**
   (elected 2021) resigned — was **appointed mayor** (sworn in 2025-01-03) and **won the 2025
   mayoral race** (60.89%). **Denece Mikolash** was appointed to the vacated D5 seat 2025-01-07
   and won it in Nov 2025. So Gettel's 2020–2024 rows are legitimate councilmember votes;
   **"Mayor Stevenson" is the 2022–2024 mayor**; the current mayor is Gettel (like Herriman's
   Hales). Current roster (Jan 2026): D1 Billings, D2 Glover, D3 Robinson, D4 Brown, D5
   Mikolash, Mayor Gettel. The extractor never assumes a fixed roster — it records whoever the
   minutes name.
3. **RDA (and MBA) ride the `body` column — two capture modes since 2026-07-16.** The Council
   recesses in-session into the **Redevelopment Agency** board; the audited Revize minutes
   capture that as CC-doc motions tagged **`body=RDA`**. The city ALSO files **standalone RDA
   board minutes** (and one **Municipal Building Authority** doc, `body=MBA`) that were never
   on the Revize portal — recovered from Utah Public Notice and **promoted 2026-07-16** with
   `provenance=pmn_minutes` ("Board Member"/"Chair" roles; the tie-break-only Mayor presides
   as RDA/MBA Chair and does not vote). Totals now: **RDA 84 motions / 280 vote rows; MBA 5
   motions / 13 rows**. The same five councilmembers sit as the board.
4. **The 2020–2021 OCR seam.** The 2020–2021 council minutes (and a few later scans) are
   scanned image PDFs recovered via OCR (**30 council + 16 PC** files `format=ocr`; 2022+ is
   born-digital text; 2020 has 9 `.docx` originals). OCR is clean enough that roll calls parse,
   but ~0.4% of OCR-era council rows carry garbled name variants (`Geftel`/`Oustin Gettel`/
   `Pau! Glover`) — a known limitation, not fabrication (`VERIFICATION.md` §e).

## Index + vote schemas are the collection standard
- `minutes_index.csv`: `date,year,title,slug,path,source,source_url,format` — one row per
  document on disk; unrecoverable meetings live in `minutes_unrecovered.csv`, never as
  stub/wrong-doc rows. `source` = `revize`; `format` ∈ `text`/`ocr` (`docx` for the 9 Word
  originals).
- `all_votes.csv`: the 13-column standard
  (`date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`)
  **+ a documented trailing 14th `provenance` column since 2026-07-16** (`minutes` = audited
  Revize doc; `pmn_minutes` = PMN-recovered doc promoted by
  `meeting_minutes/extract_backfill_votes.py`, whose `source` paths point into
  `pmn_backfill/text/`). `result` and `motion_type` are city-verbatim — **cross-city
  comparison goes through `motions_std.csv`** (normalized outcome/tallies/motion_type_std)
  and the repo-root `crosswalks/` tables. `body` ∈ Council/RDA/MBA (council file) or
  PlanningCommission (PC file). **Run order: `extract_votes.py` then
  `extract_backfill_votes.py`** — skipping the second drops the 179 pmn_minutes motions.
- Raw originals are retained under each dataset's `raw/` and are never deleted.

## The join key
Everything keys to the **council meeting weekday (Tuesday** — 1st & 3rd; the P&Z Commission
meets 2nd & 4th **Wednesday** and joins on its own date). A single date can carry >1 doc
(e.g. a Regular + a Truth-In-Taxation meeting — see the 2025-08-19 duplicate note below).
`build_weeks.py` buckets every record onto the Monday grid (`meeting_weekday = 1`). Elections
are point-in-time (Nov, odd years) and are NOT in the weekly bundles — join by **person + year
+ district** (normalize names; election names are UPPER-CASE).

## How to analyze (which artifact for which question)
- **Aggregate / time-series**: the canonical flat tables — `meeting_minutes/all_votes.csv`
  (+ `motions_std.csv`) and `planning_commission/all_votes.csv`. These are **named-roll**
  minutes, so most motions carry per-member Aye/Nay/Absent rows (higher attribution than the
  narrative-tally councils).
- **Relational / cross-body** (PC recommendation → council outcome; RDA co-actions; member
  records): `db/civic.db` — read `db/SCHEMA.md` first; start from views `v_referral_chain`,
  `v_project_timeline`, `v_member_record`, `v_contested`. The `referral` layer is reconstructed
  + scored (**114 links since the 2026-07-16 promotion: 42 high / 54 medium / 18 low**) —
  respect the confidence column.
- **Meeting-level / contextual**: the `weeks/<Tuesday-week>/` bundle (start with `summary.md`).
- **By member**: join election winners (`election_results/`) ↔ votes. **Mind the Gettel
  council→mayor seam** and the D5 Gettel→Mikolash succession (Jan 2025).
- **By geography**: `geo/address_to_district.py` resolves an address/point to District 1–5 off
  the official FeatureServer (the citywide Mayor is never returned).

## Elections — one recovered gap, RCV pilot years
**39 races, 2007–2025.** The **2019 general** (Sperry D1 / Glover D2 / Robinson D3) was
recovered by re-parsing the raw Salt Lake County SOVC. **2021 Mayor and 2023 D3 are RCV pilot
years** — the file's `winner_pct`/`margin` are **first-choice** round-1 values (flagged in
`note`); the `winner` is the canvassed **RCV-final** winner (Stevenson 2021 Mayor, Robinson
2023 D3). A **2023 bond question** is intentionally excluded from the races file. Winners
cross-checked against Midvale Journal / KSL / SL Tribune in `VERIFICATION.md`.

## public_comments — HONEST-EMPTY (submit-only)
Midvale publishes no standalone written-comment archive; public comment is in-person /
submit-only, with inline "Public Comments" speaker notes inside minutes (meeting-record
paraphrase, not genuine written comments). `all_comments_clean.csv` is **header-only by
design** — the verdict is documented in `public_comments/AVAILABILITY.md`. A legitimate honest
zero, not a gap.

## weeks/ and db/ are derived — regenerate, don't hand-edit
`python3 build_weeks.py` · `python3 db/build_db.py && python3 db/build_referrals.py`.
Canonical sources of truth are the dataset folders (flat CSVs + minutes markdown + retained
`raw/`); never edit files under `weeks/` or the .db. Rebuild weeks/ after ANY change to the
canonical CSVs. Each subfolder has its own CLAUDE.md/SCHEMA.md with build details.

## Keeping it current
`python3 fetch_new.py --probe` (default; read-only) lists Revize Document Center minutes newer
than each dataset's index max — council (recorder agendas-&-minutes landing) and PC (Planning
& Zoning Commission landing) — excluding dates already indexed or logged in
`minutes_unrecovered.csv`. `--fetch [--dataset meeting_minutes|planning_commission]` downloads
each new date's minutes PDF → `raw/`, converts OCR-aware → markdown → `minutes_index.csv`, then
runs the dataset's `extract_votes.py` + `validate_votes.py`. Rebuild db + weeks afterward (the
CLI prints the reminder). Idempotent + resumable. **Document Center paths carry spaces + a
literal `&` — the driver URL-encodes and uses a browser UA** (via `scripts/refresh_lib.py`).

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-13)
Six source layers, each with its own `CLAUDE.md`/`AVAILABILITY.md`, all `validate_dataset.py`
PASS; none modify the core layer. Join by `date` (+ `body`).
- **`packets/`** — **117 rows INDEX-ONLY** (110 live packets / 2.78 GB whole-meeting Revize
  bundles → over budget, not stored; St. George precedent). Council 69 / PC 48; 2020→2026
  (sparse before 2024, then a publishing ramp). 7 dead links from the city's own `<base href>`
  bare-relative quirk (catalogued, sizes blank, never fabricated).
- **`housing_plans/`** — **8 rows**: 2016 General Plan, 2019 Housing Plan + 2022 MIH Element
  (adopted via RDA-Board GP amendment), state compilation excerpts 2023/24/25 + SB34 (Midvale
  present all years — above threshold). No city-published annual report / compliance letter.
- **`ordinances/`** — **263 rows (256 signed PDFs, 2012-O-01→2026-O-22; 182 land-use)** from
  Midvale's OWN Document Center archive (`recorder_s_office/midvale_city_ordinances.php` —
  unusual; no PMN needed). Linkage **107 high** (all 2020+, 0 false — regex tolerant of OCR
  `O→0/00` and `.`-for-hyphen citation variants) / 2 medium / 8 low / 144 none (119 pre-2020
  below floor + 25 consent-agenda) / 2 within_source. Code host `midvale.municipal.codes`
  (General Code, current text only, not mirrored). 261 sidecars (110 tesseract OCR).
- **`pmn_backfill/`** — PMN entity **201** (all 9 bodies swept; 753 Council / 754 PC / 756 RDA
  / 757 MBA hold minutes). Midvale's minutes came from its own Revize portal, so PMN is an
  INDEPENDENT cross-check — recovered **14 genuine council-session dates the audited layer was
  missing** (25 docs incl. a whole 2024 cluster + recurring 3rd-Tuesday January meetings). PC
  has 0 recoverable 2020+ gaps; the 2020-21 scanned seam has no born-digital upgrade (PMN holds
  the same scans). A Harvest Days festival committee cross-files under the council body (excluded).
  ✅ **PROMOTED 2026-07-16**: 24 of 25 docs merged into the vote layer with
  `provenance=pmn_minutes` (179 motions / 549 rows; Council 125 + RDA 49 + MBA 5 motions);
  the 2023-03-30 budget retreat has no motions (honest zero, not merged). One PMN label lie
  corrected: the doc filed as "RDA Minutes 1-17-2023" contains the **2022-12-06** RDA minutes
  (promoted under the true date); the 2023-01-17 RDA session's own minutes are the one
  remaining council-family gap (`meeting_minutes/minutes_unrecovered.csv`).
- **`transcripts/`** — city YouTube channel (`UCLDszK2kMUHuc3-bV-BBslQ`): **258 meeting videos
  2020-04→2026-07** (Council 155 / PC 101), 100% ASR captions, 10 samples fetched. Utah Record
  mirror carries 0 Midvale. (yt-dlp quirk: some videos falsely report no-subs via android_vr —
  a full harvest must iterate `player_client`.)
- **`campaign_finance/`** — **84 filings, 2017–2025 — complete roster coverage, ZERO
  election-record discrepancies** (Midvale's election data already captures every implied
  primary, unlike murray/herriman/draper/alta). 27 text / 57 scanned; acquisition only. Sources:
  the city CF disclosures page + `disclosures.utah.gov/municipal` (the 2023 state folder held 4
  net-new finals). Gettel's council→mayor seam + Stevenson's resign-then-appoint noted.

## Analysis guidance
- Councils are high-consensus — **contested votes (any Nay/Abstain/Recuse) are the signal**
  (db `v_contested`); `summary.md` surfaces them per week.
- Motion types: city-native taxonomy in `all_votes.csv` (12-category, see
  `meeting_minutes/CLAUDE.md`); standardized categories in `motions_std.csv`.
- Coverage seams + known gaps are documented in `README.md`, `recon.md`/`SOURCES.md`, and
  `VERIFICATION.md` — read those before quantitative claims (especially the 2020–2021 OCR
  seam, the mayor-tie-break ceiling, the Gettel council→mayor transition, and the one
  documented duplicate motion on 2025-08-19).
