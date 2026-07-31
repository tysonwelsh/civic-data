# Town of Copperton — data repository

Canonical datasets about the **Town of Copperton** Council and its Planning Commission (Salt
Lake County, Utah; ~800 residents), modeled on the Salt Lake City reference repo and conforming
to the collection-wide standard at `/Users/tysonwelsh/civic-data/SCHEMA_SPEC.md` (check with
`scripts/validate_city.py copperton_city_council`). Built by the `build-city-data-repo` skill.
Data floor: **2017** (Copperton incorporated as a metro township **2017-01-01** — full history;
2017 is the incorporation edge, not an arbitrary floor). **Tiny, sparse council (~11–12 mtgs/yr)
— thin is honest.** Read `recon.md` for the source map; `VERIFICATION.md` for QA.

```
meeting_minutes/      Council minutes (markdown) + extracted votes (all_votes.csv,
                      motions_std.csv) + retained raw/ originals + roster.csv
planning_commission/  SAME schemas for the Planning Commission (body=PlanningCommission)
public_comments/      AVAILABILITY.md — comments are HONEST-EMPTY (submit-only) — no
                      all_comments_clean.csv data by design
election_results/     Salt Lake County SOVC filtered to Copperton council races (2017/2021/2023)
geo/                  town boundary polygon + address→body tool (AT-LARGE — no districts)
db/                   relational SQLite (civic.db; build_db.py + build_referrals.py; regenerable)
weeks/                DERIVED weekly bundles tying minutes + votes together
build_weeks.py        regenerates weeks/ (MEETING_WEEKDAY = Wednesday = 2)
fetch_new.py          incremental refresh driver (GoDaddy year pages + PMN bodies 5831/1560)
recon.md              provenance map, written BEFORE acquisition (portal vendor, URL patterns,
                      honest-gap record). ⚠ recon expected all born-digital text; 14 town-era
                      minutes turned out to be RICOH OCR scans (corrected here + in subfolder).
VERIFICATION.md       independent QA + external cross-checks (Mayor Clayton; the 404 gap)
```

## The structural facts that make Copperton different

1. **A metro-township → TOWN seam (2024-05-01) — but the presiding officer VOTES in BOTH eras.**
   Copperton was a **metro township 2017–2024** (5 at-large seats **A–E**, council-elected chair
   titled "Mayor/Chair", **no separately-elected mayor**) and **converted to a Town on 2024-05-01**
   (H.B. 35 — a separately-elected **VOTING Mayor**, Sean Clayton, + 4 Council Members). In **both**
   eras the presiding officer is counted in the roll call, so **max roll-call tally = 5** always.
   Verified in-source: 2020-03-18 (township era) "**Mayor Clayton voted 'Nay'**" as the 5th vote in
   a 3-2 split; 2025-07-16 (town era) "vote was **5-0**" with Mayor Clayton presiding. This matches
   **Millcreek** (mayor votes) and is the OPPOSITE of Taylorsville/South Jordan (mayor uncounted).
   **Key the roster off the MEETING DATE.**
2. **Roster spans the seam — join carefully across years** (`meeting_minutes/roster.csv`):
   township-era **Apollo Pazell, Ron Patrick, Sorensen, Dave Olsen, Kevin Severson** →
   town-era **Sean Clayton (Mayor), Tessa Stitzer (Mayor Pro Tempore), Kathleen Bailey,
   Linda McCalmon** (seat D, 2025), **Jonathan Pratt** (2025, succeeds Severson). Clayton appears
   across the whole record — as "Mayor/Chair" throughout (he won township Seat B in 2023, then the
   first Town Mayor race in 2025). Bailey (74 mtgs) and Severson (66) are the long-servers.
3. **Narrative-tally minutes — unanimous majorities are honestly UNNAMED.** Motions name the
   **mover + seconder** and record a collective outcome ("The motion passed unanimously") or a
   numeric tally ("vote was 5-0, unanimous in favor"). A genuine roll call is taken but the printed
   minutes usually give the tally, not each Aye. **Per-member rows exist for only ~10 council
   motions** (2 township 3-2 splits on the 2020 UFA agreement/resolution; the 2023 0-4 tax-rate
   rejection; named abstentions 2024–2026). The parser leaves ayes unnamed rather than
   Present-filling; a named abstention/dissent IS recorded, the unnamed consensus majority is
   **never** fabricated as five individual Ayes. **PC** is uniformly consensus, mover-only,
   tally-only (no seconder field is ever printed; no mayor).
4. **OCR seam.** Recon expected born-digital clean text, but **14 town-era (2024-H2 → 2025) council
   minutes are RICOH scans** requiring OCR (per-page hybrid; `format=ocr`, plus one `text+ocr`).
   OCR is clean — proper names intact, the corpus screener found 0 anomalies in the OCR years.

## Index + vote schemas are the collection standard

- `minutes_index.csv`: `date,year,title,slug,path,source,source_url,format` — one row per document
  on disk; unrecoverable meetings live in `minutes_unrecovered.csv`, never as stub/wrong-doc rows.
  `source` = `pmn` (Utah Public Notice) / `godaddy` (town site). `format` ∈ `text`/`ocr`/`text+ocr`.
- `all_votes.csv`: the 13-column standard
  (`date,year,title,body,motion_no,motion,motion_type,result,mover,seconder,member,vote,source`);
  `result`/`motion_type` are city-verbatim — **cross-city comparison goes through `motions_std.csv`**
  (normalized outcome/tallies/motion_type_std) and the repo-root `crosswalks/`.
- Raw originals are retained under each dataset's `raw/<year>/` and are never deleted. Each minutes
  markdown carries a provenance header (`Source`, `Source URL`, `Source label`, `Format`,
  `In-body date match`, `Raw file`, `Raw sha256(16)`, `Provenance`).

## The honest gap: council 2017-02 → 2018-06 (verified genuine)

**29 meetings (2017-02-15 → 2018-06-20) are unrecoverable** — logged in
`meeting_minutes/minutes_unrecovered.csv`, never stubbed. PMN body 5831 still lists each meeting's
notice (the meetings happened) and each agenda notice references a minutes PDF file-ID, but **every
such attachment file-ID returns HTTP 404** (PMN purges attachments older than ~mid-2018; audio is
gone too), and the town's GoDaddy site only reaches back to 2023. **Re-verified 2026-07-12**: 40+
purged file-IDs all 404 while three recovered control files (459667/459671/522659) return HTTP 200
— a genuine retention purge, NOT a missed harvest. Earliest surviving doc: **2018-07-18**
(459667). See `VERIFICATION.md §Gap`. Minor later gaps (Sep-2025, Dec-2025, June-2026) are also
logged honestly.

## The join key

Everything keys to the **council meeting weekday (Wednesday** — 3rd Wednesday, 6:30 PM, Bingham
Canyon Lions Club). The PC nominally meets 1st Wednesday but **most meetings are CANCELLED**; its
records join on their own date. `build_weeks.py` buckets every record onto the Monday grid
(`MEETING_WEEKDAY = 2`). Elections are point-in-time (Nov, odd years) and are NOT in the weekly
bundles — join by **person + year** (Copperton seats are **at-large**, no district key; normalize
names — election names are UPPER-CASE).

## How to analyze (which artifact for which question)

- **Aggregate / time-series**: the flat tables — `meeting_minutes/all_votes.csv` (+ `motions_std.csv`)
  and `planning_commission/all_votes.csv`. Remember these are **narrative-tally**: on a unanimous
  motion the majority is honestly unnamed. **Member-level analysis is only meaningful for the ~10
  named council motions + 3 PC named abstentions** — do NOT read the many tally-only blank-member
  rows as extraction misses.
- **Relational / cross-body** (member records; the handful of PC→Council land-use links):
  `db/civic.db` — read `db/SCHEMA.md` first; views `v_referral_chain`, `v_project_timeline`,
  `v_member_record`, `v_contested`. The `referral` layer is reconstructed + scored (**2 medium
  links**; there is no case-number bridge — Copperton's land-use volume is tiny). 488 motions
  (431 Council + 57 PC).
- **Meeting-level / contextual**: the `weeks/<Wednesday-week>/` bundle (start with `summary.md`).
- **By member**: join election winners (`election_results/`) ↔ votes; mind the township→town seam.
- **By geography**: `geo/address_to_district.py` — Copperton is **at-large**, so it resolves an
  address to the single town body, not a district.

## Elections — two documented gaps

**6 council races, 2017 / 2021 / 2023** (at-large seats A–E; A/B/C on the 2019/2023 cycle, D/E on
the 2021/2025 cycle). **2019 is absent** from the Salt Lake County archive (the same 2019 drop
seen for South Jordan/Millcreek/Taylorsville). The **2025 first-Town-Mayor race (Clayton) was
unopposed and NOT tabulated** by the county (all seats unopposed). MSD / Improvement-District /
2015 incorporation ballot questions are EXCLUDED as non-council contests. Notables: 2021 Seat E
was won by **Kevin Severson as a qualified write-in, by 1 vote** over Ronald Patrick.

## public_comments — HONEST-EMPTY (submit-only)

Copperton publishes **no** standalone written-comment archive / eComment / correspondence page
(probed live 2026-07-12 — 404s). Public comment is taken in-person ("COMMUNITY INPUT" +
"Others Present:" inline speaker notes in the minutes — clerk paraphrase, not verbatim written
comment). `all_comments_clean.csv` is header-only **by design**; verdict in
`public_comments/AVAILABILITY.md`. A legitimate honest zero, not a gap.

## Geo — at-large, one polygon

Copperton has **no council districts** (seats are at-large), so there is no sub-district geometry.
`geo/` holds the single UGRC town-boundary polygon (`UtahMunicipalBoundaries`, COUNTYNBR 18) and a
trivial address→body tool. See `geo/CLAUDE.md`.

## Regenerate (derived layers — don't hand-edit)

```
python3 meeting_minutes/extract_votes.py && python3 meeting_minutes/validate_votes.py   # → PASS
python3 planning_commission/extract_votes.py && python3 planning_commission/validate_votes.py
python3 build_weeks.py                                    # weeks/ (Wednesday grid)
python3 db/build_db.py && python3 db/build_referrals.py  # db (run referrals AFTER build_db)
```

Canonical truth is the dataset folders (flat CSVs + minutes markdown + retained `raw/`); never
edit files under `weeks/` or the `.db`. `all_votes.csv` is RFC-4180 (motion text has
commas/quotes — parse with a real CSV reader). Corrections go through documented override CSVs
(`db/referral_overrides.csv`), never in-place edits.

## Keeping it current

`python3 fetch_new.py --probe` (default; read-only) lists candidate new meetings from the GoDaddy
year pages (`copperton.utah.gov/<YEAR>-agendas-...`, fetched with `curl -k` + browser UA for the
TLS cert mismatch) and Utah PMN (council body **5831**, PC body **1560**), excluding dates already
indexed or logged in `minutes_unrecovered.csv`. Then acquire the genuine minutes doc → `raw/`,
convert (OCR-aware) → markdown → `minutes_index.csv`, and re-run the dataset's
`extract_votes.py` + `validate_votes.py`; rebuild weeks + db afterward.

## Analysis guidance

- **Contested votes are the signal.** Council: ~10 contested/named motions (2 genuine 3-2 splits
  on the 2020 UFA agreement/resolution; a 0-4 rejection of the 2023 SLVLESA tax-rate resolution;
  the rest named abstentions/recusals). PC: 3 named Breinholt abstentions. Everything else is
  consensus.
- Coverage seams + known gaps are documented in `README.md`, `recon.md`, and `VERIFICATION.md`
  — read those before quantitative claims (the 2017–2018 404 gap, the narrative-tally
  unnamed-majority style, the mid-2024/2025 OCR seam, the township→town voting-mayor seam).

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-14)
Six source layers, each with its own `CLAUDE.md`/`AVAILABILITY.md`, all `validate_dataset.py`
PASS; none modify the core layer. Join by `date` (+ `body`). Tiny ~800-pop town: GoDaddy site
(TLS mismatch → curl -k) + PMN (council 5831 / PC 1560) + MunicipalCodeOnline S3 + MSD.
- **`packets/`** — **305 docs STORED (400 MB)**: Council 229 (PMN 5831 ≤2023 + GoDaddy ≥2024,
  non-overlapping) + PC 76. ⚠ The packet floor is **2019, LATER than the 2017 minutes floor** —
  PMN purges bulky handout/packet attachments sooner than minutes (attachment-type-dependent
  retention). PC cancels most meetings (cancellation notices excluded from the count).
  - **doc_class layer** (2026-07-16): 6 MSD land-use staff reports classified (whole-class
    verified) — see packets/CLAUDE.md.
- **`housing_plans/`** — **near-empty (correct, Alta pattern)**: the 2020 General Plan with an
  embedded Ch.6 housing element (NOT an HB462 standalone); ABSENT from all 4 state compilations
  (below the ~5,000 reporting threshold, unlike the larger MSD siblings). Compilations retained
  un-indexed as absence evidence.
- **`ordinances/`** — **129 instruments (67 ord + 62 res, 2017–2026; 24 land-use)** from
  MunicipalCodeOnline S3 (`municipalcodeonline.com-new/copperton/` — the cluster OUTLIER: 7
  subprefixes, not 2). Linkage 17 high / 22 medium / 10 low / 80 none (most Copperton motions
  say "approve the ordinance" with no number). Type-aware (parallel ord/res numbering) + OCR
  `0↔O`. Excluded a KEARNS ordinance mis-filed in Copperton's bucket (shared-MSD hazard, both
  directions). 12 minute-cited numbers unposted (the R2025-01…08 town-era run — codification lag).
- **`pmn_backfill/`** — PMN entity **1353** (council 5831, PC 1560; no CRA/agency exists). **0
  recoveries — the repo is a COMPLETE SUPERSET** of both bodies. Value = 1 OCR-upgrade lead
  (2025-10-15 born-digital council draft where the repo holds only a RICOH scan — cataloged, not
  swapped). The 2017-02→2018-06 purge RE-CONFIRMED genuine (fresh file-ID band, all 404).
- **`transcripts/`** — AUDIO-ONLY (no YouTube — all 8 handles 404): PMN MP3 archive **160 files
  2017→2026; 120 live / 40 purged**. Honest nuance: the audio purge boundary runs LATER than the
  minutes one — 2018-07→11 meetings have minutes but no recoverable audio. Whisper candidates
  proposed (owner-gated).
- **`campaign_finance/`** — **25 rows**: 19 township filings 2016–2021 (SLCo static
  metro-township archive) + 6 COI. The GoDaddy town site posts only COI (not campaign finance);
  2023 (EasyVote-blocked) + 2025 (unopposed, threshold-exempt) are honest zeros. FLAGS: the
  finance record confirms the archive-missing **2019 A/B/C cycle** existed; and corrects the
  roster — **Pratt was APPOINTED not elected** (2025 Seat C had "No Candidate Declarations").
