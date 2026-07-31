# Alta — `pmn_backfill/` (Utah Public Notice cross-check + recovery)

**Source 4 of `expand-city-sources`.** A SEPARATE, review-only dataset that cross-checks
the audited `meeting_minutes/` and `planning_commission/` layers against the statewide
Utah Public Notice repository (`utah.gov/pmn`) and holds the minutes genuinely missing from
the repo. **Additive — it never modifies the audited layers.** Built 2026-07-13.

## Headline result

**5 genuinely-missing minutes documents recovered** (Town Council 3 · Planning Commission
2); **0 still-missing** after recovery. See `coverage.md` for the per-year tables.

✅ **PROMOTED (2026-07-16): 4 of the 5** are now in the audited vote layer — merged into
`meeting_minutes/all_votes.csv` / `planning_commission/all_votes.csv` by each dataset's
`extract_backfill_votes.py` with a documented trailing **`provenance=pmn_minutes`** column
(audited rows = `minutes`), flowing into `db/civic.db` `motion.provenance`. 22 council +
2 PC motions (incl. 4 contested Sondak-era/2024 votes). **NOT promoted: PC 2023-11-28** —
in-body verification found a **DRAFT watermark on every page** and a PDF authored
**2024-02-23, four days BEFORE** its pre-printed "Minutes Approved on February 27, 2024"
line (the *scheduled* approval meeting — it cannot attest approval). Drafts are never
promoted: it stays a sidecar here, logged in
`planning_commission/minutes_unrecovered.csv` (the meeting is real; its minutes were
approved unamended at the audited 2024-02-27 meeting, but the approved version was never
posted to PMN).

Alta's audited minutes were themselves harvested from PMN (bodies 1601/1602), so this is a
completeness re-audit of that harvest — **not** a fresh source. It is **not** a pure
superset (contrast bluffdale): the original harvest filtered on PMN's `(Meeting Minutes)`
attachment **label**, so it missed minutes that PMN posted under a `Public Information
Handout` label or filed under the **wrong body**. This pass keys on the meeting date parsed
from the attachment **filename** (label-agnostic) and recovered them.

## What PMN holds for Alta

- **Entity id 72** (`utah.gov/pmn/list/publicBodies.html?id=72`). Four bodies:
  **1601** Town Council · **1602** Planning Commission · **8621** Budget Committee ·
  **1603** Land Use Appeal Authority.
- The Town of Alta has **no "Capital Committee"** in PMN — the `/meetings/` app's "Capital
  Committee" category corresponds to the **Budget Committee** (body 8621), inventoried in
  `coverage.md` but **not** built into a dataset (task scope: inventory only).

## The 5 recovered meetings (each verified against its own internal header)

- **Council 2020-05-06** (fid 618395), **2020-06-17** (fid 618397) — born-digital; missed
  because attached under the `Public Information Handout` label. Fill the May/June-2020 gap.
- **Council 2024-08-14** (fid 1168819) — a COUNCIL meeting **mis-filed under PC body 1602**
  (bundled in the 2024-08-28 PC notice); image-only scan → OCR. Fills the Aug-2024 gap.
- **PC 2023-11-28** (fid 1089283, **DRAFT** — no approved version on PMN) and
  **PC 2024-04-24** (fid 1124533) — born-digital.

## Method (reproducible, GET-only)

1. `entities.html?id=3` (govType 3) → Alta = entity **72** →
   `publicBodies.html?id=72` → the four body ids.
2. Per body, one cumulative GET `notices.html?id=<body>&page=300` → entire notice history
   (historical *search* is POST/CSRF — never used).
3. Parse each notice's title/date and every attachment's file-id + **filename** + label.
   Filter to minutes by `minutes` in the filename OR the label.
4. **Parse the true meeting date from each filename** (PMN's notice event-date ≠ meeting
   date — a naive event-date diff produces false positives/negatives; the filename carries
   the real meeting date). Dedupe by meeting date; prefer approved over draft.
5. **Per-meeting-date set-difference** vs `meeting_minutes/minutes_index.csv` /
   `planning_commission/minutes_index.csv` (±4-day tolerance), NOT per-year counts.
6. For each non-match: fetch the PDF and **VERIFY its internal body-name header + date**
   before recovering (this is how the 2024-08-14 doc was confirmed to be a council meeting
   despite its PC-body filing, and how draft-vs-already-approved dupes were rejected).

## Layout / schema

```
raw/
  _disc_entities.html / _disc_bodies.html    PMN entity + body discovery (provenance)
  _notices_<bodyid>_*.html                   cumulative notice history per body (1601/1602/8621/1603)
  pmn_council_2020-05-06_618395.pdf           the 5 recovered minutes PDFs (verbatim)
  pmn_council_2020-06-17_618397.pdf
  pmn_council_2024-08-14_1168819.pdf          (scanned)
  pmn_pc_2023-11-28_draft_1089283.pdf
  pmn_pc_2024-04-24_1124533.pdf
  _fetch_log.jsonl                            polite_fetch provenance (url/status/bytes/sha256/utc)
text/
  <same stems>.txt                            extracted sidecars (pdftotext-layout ×4; tesseract-ocr ×1)
index.csv                                     §9 pmn_backfill contract header (14 cols)
coverage.md                                   per-year/per-body tables + cancellation-notice proof + inventory
AVAILABILITY.md                               what was checked / exists / honest gaps
CLAUDE.md                                     this file
```

`index.csv` columns (SCHEMA_SPEC §9 `pmn_backfill` contract):
`date,year,title,slug,body,path,source,source_url,notice_url,pmn_body_id,pmn_file_id,retrieved_date,format,extraction_method`.
`path` is dataset-relative including `raw/`. `source=pmn`. `body` = the **real** body
(Council / PlanningCommission); `pmn_body_id` = where PMN **filed** it (so the mis-filed
2024-08-14 has `body=Council` but `pmn_body_id=1602`). `format ∈ text|scanned`.

## Caveats / rules honored

- **GET-only, polite** (`scripts/polite_fetch.py`, ≥1s/host); no POST/CSRF search.
- **Raw retained** verbatim (discovery + notice-list HTML + the 5 PDFs + `_fetch_log.jsonl`).
- **Verified before recovery** — every recovered PDF's internal header + date was read;
  drafts of already-approved meetings and the LUAA duplicate of an existing council meeting
  were correctly **rejected**, not recovered.
- **Sparse gaps proven real** via PMN cancellation notices (PC "cancelled due to weather"
  2020-09-08, etc.) — see `coverage.md`.
- **Never fabricated.** The 2023-11-28 PC doc is labeled DRAFT because that is the only
  version PMN holds (verified 2026-07-16: watermark + pre-approval authoring date — never
  promoted).
- ~~Do NOT merge~~ **MERGED 2026-07-16** (4 of 5, provenance-tagged) via the deliberate
  promotion pass: `extract_backfill_votes.py` in each dataset + full derived-chain
  rebuild (`db/`, `weeks/`, `motions_std`, sources; `validate_city` 0 FAIL). The raw/text
  copies here remain the canonical on-disk source the promoted rows point at.
- Not loaded into `cities.db` by this run (`build_cities_db.py` intentionally not run —
  the orchestrator federates).


## 2026-07-17 — PMN cross-check flag verification (24 flags -> 16)
Verified every crosscheck_flags row against cache + 2 live notice-detail GETs; 8
exceptions added. 17 gaps was high for a ~12-mtg/yr town — the excess was Budget
Committee noise, not real coverage loss.
- **Exceptions (8):** the out-of-scope Budget Committee (fiscal subcommittee, body 8621)
  cross-filed under Town Council(1601) — 5 missing_minutes (2021-02-26, 2022-03-01,
  2022-03-18, 2024-03-29, 2024-04-16) -> not_minutes + 3 agenda (2020-04-13, 2021-03-12,
  2022-06-06) -> other.
- **Recovery leads (14), remain flagged:** genuine Town Council meetings the repo lacks —
  2020-01-08, 2020-09-09, 2021-03-10, 2021-10-13, 2021-11-16 (canvass), 2022-11-09,
  2023-11-08 (title year-typo "2022"; audio confirms 2023), 2023-12-06 (canvass),
  2024-09-11 & 2024-10-09 (repo council jumps 2024-07-10 -> 11-13), and 2025-07-09
  (live GET confirmed: "regularly scheduled Town Council" mtg @4pm, not a bare resolution
  notice). PC leads: 2022-04-26 & 2026-02-25 (real mtgs; alta PC minutes start 2022-06),
  and 2021-09-28 (live GET confirmed HELD as an electronic meeting — NOT cancelled;
  minutes never posted, consistent with the documented-empty 2020-21 PC era).
- **Hardening candidate (2 residual flags):** filename-date-rescue — 2020-07-28 (its only
  minutes-labeled file is a 2019-10-22 DRAFT, below the 2020 floor; the 07-28 PC mtg is
  agenda/draft-memo only) and 2024-06-26 (attaches the 2024-05-22 draft, already in repo;
  06-26 itself is a real PC mtg whose minutes were never posted).
- Re-run (`--cached`): **16 flags** (14 agenda_only + 2 missing_minutes), 8 suppressed.

## 2026-07-17 (wave2) — 14 recovery leads DISPOSITIONED: all DEAD (0 recovered)
Probed every one of the 14 agenda_only_gap leads for real recorded minutes (PMN attachments +
town site). **Result: 0 recoverable, 14 dead** — no votes added, no promotions.
- **Method:** fetched all 14 notice-detail pages live (each carries only agenda / Public
  Information Handout / audio — NO minutes attachment), then swept **every attachment filename
  across ALL four Alta PMN bodies** (Council 1601, PC 1602, Budget 8621, LUAA 1603, from the
  cached full notice history) for each meeting date. No standalone approved minutes exists on PMN
  for any of the 14. The town website is the same JS-only Juniper media library PMN draws from
  (townofalta.com now 301s to townofalta.utah.gov), so it is not an independent channel.
- **Disposition:** each is a HELD meeting whose minutes were never published → logged in the
  appropriate dataset's `minutes_unrecovered.csv` (11 Council + 3 PC), and
  `crosscheck_flags.csv` marked `known_unrecovered=yes` (suppresses future re-flagging). GRAMA
  request text drafted in the wave report.
- Several are procedurally minute-light by nature (2021-11-16 & 2023-12-06 election canvasses;
  2025-07-09 single-resolution special) but all are real meetings (agendas/audio prove it). The
  2020-21 PC entries (2021-09-28, 2022-04-26) are consistent with the documented-empty early PC era.
- **Not a superset regression:** these were always absent from the audited harvest; this pass
  just confirms them dead rather than pending. The vote layer is UNCHANGED (no db/weeks rebuild).
