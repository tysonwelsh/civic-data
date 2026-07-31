# Town of Alta — `ordinances/` dataset

Adopted Town Council **ordinances** (`YYYY-O-N` series), 2020 → present, as an additive
expansion dataset (source type 3, `/expand-city-sources`). Built 2026-07-13. Resolutions
(`YYYY-R-N`) are intentionally **out of scope** here.

## Layout
```
raw/                     44 ordinance PDFs (verbatim) + _ordinance_list_page.html
                         (the enumeration source) + _fetch_log.jsonl (sha256 provenance)
text/<no>.txt            one text sidecar per ordinance PDF (born-digital or OCR)
index.csv                SCHEMA_SPEC §9 ordinances contract + one extra column (linkage_note)
AVAILABILITY.md          sources checked, coverage, gaps
CLAUDE.md                this file
```

## Where the data came from
- **Enumeration + PDFs:** the town's static adopted-ordinance list,
  `https://townofalta.utah.gov/ordinances-resolutions/` (retained at
  `raw/_ordinance_list_page.html`). Unlike the JS `/meetings/` app, this page carries direct
  Google Cloud Storage PDF links (`storage.googleapis.com/juniper-media-library/130/…`). Each
  posted ordinance PDF was fetched with `scripts/polite_fetch.py` (GET-only, throttled,
  sha256-logged). Two URLs with literal commas / a literal `%` in the GCS object name
  (`2022-O-6`, `2023-O-4`) were fetched individually (batch/`polite_fetch` re-encoding
  choked on them — `2023-O-4` needed a raw `%25` and is logged with a note).
- **Text extraction:** born-digital PDFs → `pdftotext -layout` (`format=text`,
  `extraction_method="pdftotext -layout"`). Scanned signature-page PDFs (most 2024→2026) →
  `pdftoppm -r 300` + `tesseract --psm 6` (`format=scanned`,
  `extraction_method="tesseract 5 OCR @300dpi …"`). Source typos/OCR artifacts are preserved,
  not cleaned. `screen_corpus.py` run clean (0 read errors, 0 dict/weird-char outliers; the
  6 split-word + ends-mid flags are expected OCR/legal-doc noise).

## Motion linkage (→ `meeting_minutes/all_votes.csv`)
`matched_motion_date` / `matched_motion_no` point at the adopting council vote; confidence:

- **`high` (40)** — the ordinance number is cited in a council **vote** motion AND an
  independent PDF exists. The adoption motion is chosen as the latest APPROVED/ADOPTED motion
  citing the number (a preceding `RECORDED (no vote line)` intro row is skipped).
  `adoption_date` = that meeting date.
  - **Number grammar:** Alta's minutes write the series both as `2021-O-1` (letter O) and, in
    2024–2026, as `2024-0-4` (digit zero). The matcher accepts **both** but requires a
    hyphen/space on **both** sides of the O/0 so it never mis-reads a date like `2026-04-08`.
- **`within_source` (6)** — **no independent PDF**; the council minutes are the sole witness
  (`format=na`, `source_url` = the witnessing PMN minutes file). These are `2020-O-4`,
  `2020-O-5` (never on the town list) and `2021-O-6`, `2022-O-3`, `2023-O-5`, `2026-O-3`
  (town list marks Did-Not-Pass / continued). High by construction (the number+date come
  from the motion itself) — **not** independently corroborated; do not read as a clean
  cross-match.
- **`none` (4)** — an independent PDF exists but no council vote motion cites the number:
  `2022-O-6`, `2024-O-7`, `2024-O-8`, `2026-O-12` (the last is July 2026, past the newest
  minutes held). Never force-matched.

`result` is the verbatim motion outcome where linked (e.g. `APPROVED (5-0)`, `FAILED (0-5)`),
else the town-list status. `land_use=yes` (10 rows) flags zoning/subdivision/rezone/Title-10
land-use ordinances (e.g. `2021-O-1` Land Use Amendments, `2024-O-9` Subdivision,
`2026-O-2` LUDMA, `2026-O-4` Petitions to Rezone, `2026-O-11` Zoning Map,
`2025-O-5` Title 10 §10-1-8 noticing).

## Codified municipal code host (recorded, NOT mirrored)
Alta's consolidated **Town Code** is published by **American Legal Publishing** at
`https://codelibrary.amlegal.com/codes/altaut/` (formerly Sterling Codifiers). It is
**current-consolidated text only** (no per-ordinance adoption PDFs) and is **bot-gated /
403** — so it is **not** mirrored here, per the skill's don't-mirror-bot-gated-hosts rule.
The per-ordinance adopted texts in `raw/` (from the town's own list) are the citable source;
use amlegal only to see how an ordinance folded into the current code.

## Rebuild / refresh
Not a hand-maintained file. To refresh: re-fetch `/ordinances-resolutions/`, diff the listed
`YYYY-O-N` numbers against `index.csv`, fetch any new PDFs into `raw/`, extract a sidecar
(pdftotext, OCR-fallback if <200 chars), and re-run the number→motion match against
`meeting_minutes/all_votes.csv`. Then `validate_dataset.py <this dir>` must PASS. The
sidecars feed `cities.db` `fts_ordinance` and the `ordinance` table on the next
`scripts/build_cities_db.py` (run separately — not part of this dataset build).

## Caveats
- **Ordinances only** — resolutions (budgets, fee schedules, appointments) are excluded even
  though they dominate Alta's `-R-` numbering; see the town list for those.
- **Sparse-town record:** 2020-O-1..O-3 were never located; the online ordinance list starts
  at 2021. `2021-O-2` is a documented zero-info numbering gap (AVAILABILITY.md), not a row.
- Mayor **votes** in Alta (max roll 5) — a linked adoption roll may legitimately include
  `Mayor …` as an ordinary Aye/Nay; don't treat the mayor as a non-voter when reading a
  linked motion's tally.
