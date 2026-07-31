# PMN backfill — availability & gap record

**As-of:** 2026-07-03 · Source: Utah Public Notice Website (PMN), `https://www.utah.gov/pmn/`

## What was checked
- **West Jordan PMN entity id:** 305 (via `entities.html?id=3`, govType 3 = Municipality).
- **Bodies cross-checked:** City Council (id **395**) and Planning Commission (id **396**),
  full notice history via the cumulative pager `notices.html?id=<body>&page=300`
  (council back to 2012, PC back to 2008).
- **Filter:** attachments labeled `(Meeting Minutes)`, meeting years 2020+ (repo data floor).
- **Comparison:** per-DATE set-difference vs `meeting_minutes/minutes_index.csv` (321 rows) and
  `planning_commission/minutes_index.csv` (84 rows), ±4-day tolerance.

## What exists / was recovered
**33 genuine date-level gaps recovered, 0 still missing** (all content-verified: body header +
internal HELD date + motion/vote text). See `coverage.md` for the per-year table.

- **City Council (5):** 2022-01-03 & 2024-01-03 Oath-of-Office ceremonies; 2024-08-13 Fairway
  Estates SSD Truth-in-Taxation hearing; the 2026-06-09 City Council Meeting + Committee of the
  Whole (both newer than the repo's last council fetch 2026-05-26).
- **Planning Commission (28):** standalone regular meetings for **2021 (16)** and **Jan–Jul 2022
  (12)** absent from the PrimeGov-sourced repo. 6 of the 2021-2022 PC files were scanned and were
  recovered by OCR (Tesseract, 300 dpi); the rest are born-digital.

## What does NOT exist / was not pursued (honest gaps)
- **Council 2020–2023, 2025:** no un-covered PMN minutes dates — the repo already holds
  equal-or-better coverage (repo is a superset). Nothing to recover.
- **PC 2023–2026:** no un-covered PMN dates; repo coverage is complete for those years.
- **PC 2020:** PMN carries **no** `(Meeting Minutes)` attachment for 2020 (notices exist but no
  minutes posted). The repo's single 2020 PC entry (2020-09-29) stands; no PMN minutes to add.
- **Agendas / packets:** PMN's non-minutes attachments (`Public Information Handout`) were not
  harvested here — agenda/staff-report packets are the domain of the `packets/` dataset
  (SOURCE 1), not this gap-recovery layer. Every recovered gap had a genuine minutes attachment,
  so no agenda-only fallback was needed.
- **Other WJ bodies on PMN** (Board of Adjustment 397, RDA 996, MBA 997, Fairway Estates SSD 998,
  Taxing Entity Committee 1129) were **not** cross-checked — out of scope (task is Council + PC).
  The RDA/MBA are the council sitting in another capacity and are modeled in `db/`; a future run
  could diff those PMN bodies too.

## Provenance
Every byte fetched through `scripts/polite_fetch.py` (browser UA, ≥1s/host, logged). Raw PDFs
in `raw/`, fetch log `raw/_fetch_log.jsonl`, extraction sidecars in `text/`, machine-readable
catalog in `index.csv`. Nothing here modifies an existing dataset.
