# Emigration Canyon — data repository

Canonical datasets about the **Emigration Canyon** City Council and Planning Commission
(Salt Lake County, Utah; ~1,600 residents). Modeled on the collection standard
(`/Users/tysonwelsh/civic-data/SCHEMA_SPEC.md`). Built by the minutes-acquisition +
vote-extraction task. **Read `recon.md` first** for provenance. **Data floor: 2017.**

## The one structural fact that shapes everything: a FORM CHANGE, one 5-member body
Emigration Canyon incorporated as an **Emigration Canyon Metro Township** (effective
**2017-01-01**) and converted to a **CITY** effective **2024-05-01** (H.B. 35). It is the
**same 5-member, all-at-large council throughout** — one member is peer-selected **Mayor**,
who **PRESIDES AND VOTES** (the **Millcreek pattern** — mayor counted in the 5, **max tally
= 5**), NOT an executive non-voting mayor. Do **not** treat the two eras as two entities;
the vintage is carried in each doc's provenance (`**Era:** Metro Township | City`) and in
the meeting titles ("Metro Township Council Meeting" pre-2024, "City Council Meeting" after).
The **presiding mayor changed by era**: **Joe Smolka** (township) → **David Brems** (city).

```
meeting_minutes/       City Council + Metro Township Council minutes (markdown) + extracted
                       votes (all_votes.csv) + retained raw/ PDFs + extract_votes.py
planning_commission/   SAME schemas for the Planning Commission (body=PlanningCommission)
recon.md               source map (Utah PMN, no city CMS) — written BEFORE acquisition
```
Elections, geo (single-polygon boundary — the canyon is all-at-large, no districts),
public comments (submit-only / in-person — honest-empty per recon §5), and the `db/`
layer are **NOT built by this task** (empty scaffold dirs remain). See recon.md §5–7.

## Source: Utah Public Notice (PMN), not a city CMS
There is **no city document portal**. The canonical, re-fetchable source is **Utah PMN**:
**Council = body 5809**, **Planning Commission = body 1562**. Minutes are born-digital,
DocuSign-signed PDFs at `https://www.utah.gov/pmn/files/<fileId>.pdf` (non-guessable ids).
- Enumerate: `https://www.utah.gov/pmn/list/notices.html?id=<5809|1562>&page=N` — the
  **`&page=N` form is required** (the bare `?id=` endpoint 500s "Technical Difficulties";
  paging is cumulative — page N contains the first ~5·(N+1) notices; walk until the count
  stops growing). Use a **browser User-Agent**.
- **PMN purged its older file store:** notices exist back to 2017 (council) / 2008 (PC), but
  the attached PDFs for **2017 (and scattered 2018–2019)** now return **404**. Recovered
  coverage therefore begins **2018-10** (council) / **2018-11** (PC). The 2017 absence is an
  **honest gap** (files purged upstream), logged in each `minutes_unrecovered.csv`, **not**
  fabricated. MSD AgendaCenter (secondary mirror) is the documented backfill avenue for it.

## Vote grammar — NARRATIVE TALLY (council) vs STRUCTURED (PC), both handled
- **Council** is narrative-tally: mover + seconder named, a printed count, **majority
  unnamed** on unanimous motions. Two era-forms, both parsed by
  `meeting_minutes/extract_votes.py`:
  - City (2024+): *"Council Member Griffith moved to approve … Council Member Harris
    seconded the motion; vote was 5-0, unanimous in favor."*
  - Township (2017–2024): *"Council Member Harris, seconded by Council Member Pinon, moved
    to accept … The motion passed unanimously."*
  - Contested (rare): *"… passed 4 to 1, showing Mayor Smolka voted in opposition/abstained."*
  A unanimous/tally-only motion is **one tally-only row (blank member)** — never five
  fabricated Ayes. Named dissent yields the named Nay/Abstain row(s); the majority stays
  unnamed. **5 contested council motions** in the whole record (2021-04-27 Brems recusal,
  2021-08-24, 2021-12-14, 2023-08-22 full 5-name roll — Harris nay, 2023-10-24; recount
  2026-07-12 T3.1(k)).
- **PC** is structured (`planning_commission/extract_votes.py`): `Motion: …` / `Motion by:
  Commissioner X` / `Vote: Commissioners voted unanimously in favor` (or `Commissioner
  Wallace voted nay, all other commissioners voted in favor`). Plus inline procedural
  *"Commissioner X motioned to open the public hearing, Commissioner Y seconded that
  motion."* The PC is a **recommending body** (motions that `recommend` a file to the
  Council are tagged `Land-Use/Recommendation`). **3 contested PC motions.**

## What's on disk (both datasets, identical schemas)
- `minutes/<year>/<meeting-date>/<date>_<slug>.md` — born-digital text (or OCR) + provenance
  front matter (`**Body:**`, `**Meeting type:**`, `**Era:**`, `**Source:** pmn`,
  `**In-body date match:**`). **Council 86 · PC 60** files (PC 2025-11-13 promoted from
  `pmn_backfill/` 2026-07-16, `format=ocr`).
- `raw/<year>/<date>_<Body>_<Type>_<fileid>.pdf` — the retained PMN originals (never modified).
- `minutes_index.csv` — 8-col standard + `meeting_type,pmn_notice_id,pmn_file_id`;
  `source` = **`pmn`** for every row.
- `minutes_unrecovered.csv` — meetings whose PMN notice exists but no minutes doc was
  recovered (2017 purge + notice/meeting-date gaps). **Council 14 · PC 73** (the PC
  2025-11-13 row was satisfied 2026-07-16 by the promoted late-posted minutes).
- `extract_votes.py` (PURE deterministic, no LLM/network, resumable `--force`) →
  `votes/<year>/<date>/<file>.json` → `all_votes.csv` (13-col standard; the PC file carries
  the trailing `provenance` 14th column since 2026-07-16: `minutes` | `pmn_minutes`) +
  `roster.csv`.
- `validate_votes.py` → `votes/_validation_report.txt` (PASS/FAIL; never mutates).

## OCR caveat
Minutes are **born-digital clean text** (extract WITHOUT `-layout` for these DocuSign PDFs).
**7 council docs + 1 PC doc (2025-11-13, promoted 2026-07-16) are scanned** (image-only
"Approved Minutes" or packet-embedded "Minutes with Attachments") — recovered via
**tesseract OCR** (`format=ocr` in the index; raw PDF retained). OCR text is imperfect: **2 scanned council docs (2024-02-22, 2025-01-28) yielded
0 extractable motions** — an OCR-quality limit (the meetings occurred; a born-digital
re-fetch is a TODO), **not** a fabrication. All other docs are `pdf-text`.

## Rosters (OBSERVED, keyed on meeting date)
- **Council** (`meeting_minutes/roster.csv`): Joe Smolka (Mayor, township), David Brems
  (Mayor, city), Jennifer Hawkes, Catherine Harris, Gary Bowen, Robert Pinon, Robert Paine
  (early), Steve Hook (brief), Nicholas Griffith (2026). The mayor per document is detected
  from the PRESENT block, not hard-coded.
- **PC** (`planning_commission/roster.csv`): Wallace, Karkut, Berreth, Geroux, Harpst,
  Pinon, Tippets (+ earlier TPC members). Born-digital text is trusted verbatim; an unmapped
  "Commissioner <Surname>" is kept as printed, never dropped or guessed.

## Cardinal rules (collection-wide — apply here)
Never fabricate. Blank member = tally-only motion (source printed no roll). `result`/
`motion_type` are city-faithful (verbatim). Derived layers (`votes/`) are regenerated, not
hand-edited: `python3 extract_votes.py && python3 validate_votes.py` in each dataset.

## Expansion datasets (`expand-city-sources`, additive, as-of 2026-07-14)
Six source layers, each with its own `CLAUDE.md`/`AVAILABILITY.md`, all `validate_dataset.py`
PASS; none modify the core layer. Join by `date` (+ `body`). PMN-only entity: council body 5809
/ PC 1562 (www.utah.gov/pmn) + MunicipalCodeOnline S3 + MSD DocumentCenter. No city CMS.
- **`packets/`** — **375 docs STORED (1.65 GB)**: Council 269 + PC 106; 2019→2026. Packet floor
  **2019** (later than the 2018-10 minutes floor — PMN purges bulky handouts sooner; 17 2017-18
  attachments 404). Size driven by a few huge embedded General-Plan PDFs (a 472 MB PC packet),
  not volume. Classify by filename (PMN "Public Information Handout" label wraps everything).
  - **doc_class layer** (2026-07-16): 17 classified (staff_report 15 / plan_amendment 2), gates
    100% — see packets/CLAUDE.md.
- **`housing_plans/`** — **near-empty (correct)**: the 2022 General Plan (MSD-hosted, housing
  only within Land Use — no standalone MIH element); ABSENT from all 4 state compilations
  (below the Utah Code 10-9a-403 ~5,000 threshold, like Copperton/Alta). Confirms the sub-5,000
  MSD template: general_plan-only + total state-compilation absence.
- **`ordinances/`** — **98 instruments (49 ord + 49 res, 2017–2026; 24 land-use)** from
  MunicipalCodeOnline S3 (slug `emigrationcanyon`). Linkage **54 high** / 2 medium / 42 none.
  EC adds an `orddoc/` prefix holding city-era signed PDFs + an authoritative `Ordinance Log.xlsx`
  (number→Date Signed — a high-value adoption-date source). Parallel-numbering + OCR `0↔O`
  handled; no cross-entity decoys. ~15 minute-cited numbers unposted (code-rewrite lag).
- **`pmn_backfill/`** — PMN entity **1317** (council 5809, PC 1562; no third body). **1 recovery**
  (a late-posted PC 2025-11-13 minutes — **PROMOTED into `planning_commission/` 2026-07-16**:
  index `format=ocr`, `provenance=pmn_minutes`, +2 motions, unrecovered row dropped).
  ⚠ The recon's "MSD AgendaCenter secondary mirror" claim
  is a TRAP — MSD's AgendaCenter hosts the MSD Board of Trustees' minutes, NOT the townships' own
  bodies (enumerated all 189 meeting-ids → 0 EC minutes). So the 2017 purge stays a genuine gap;
  the repo is a confirmed superset. The 2 OCR-0-motion council scans have no born-digital twin.
- **`transcripts/`** — AUDIO-ONLY (no YouTube — a piano-video name-collision decoy only): PMN MP3
  archive **244 files 2017→2026; 211 live / 33 purged**. 211 Whisper candidates (owner-gated),
  highest-value the 8 contested motions + the 2 OCR-0-motion scans. EC uses uppercase `.MP3`.
- **`campaign_finance/`** — **35 rows**: township 2016/2017/2019 (SLCo static archive) + 2025 city
  CF (Wix site) + 5 COI. FLAG: the finance record PROVES a **2019 council cycle existed**
  (Hawkes/Brems/Tippetts/Harris filed) — directly contradicting the recon's "no 2019 contest"
  (the SLCo 2019-drop pattern). Also **Griffith was appointed, not elected**. 2023 EasyVote-blocked.

## README note
This entity has no separate README.md — this CLAUDE.md is the human + agent overview. The core
build left elections/geo/public_comments/db as empty scaffolds (see the intro); the expansion
layers above are complete and federated into cities.db.
