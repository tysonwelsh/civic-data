# Adopted ordinances — what exists, what doesn't (as of 2026-07-13)

## What was checked

1. **CivicPlus Archive Center AMID=95 "Public Ordinance Adoption Archive"**
   (`https://www.murray.utah.gov/Archive.aspx?AMID=95`) — the module named in
   `recon.md` as the adopted-ordinance lead. Fetched 2026-07-13 with a browser UA:
   the listing renders **"There are no published items."** The module exists in the
   Archive.aspx dropdown but is publicly empty. No Wayback Machine captures of the
   listing exist (CDX query returned nothing), so no historical state is recoverable.
2. **Archive Center AMID=73 "Recorder"** — 14 items, all election canvasses / audit
   notices; no ordinances.
3. **Utah Public Notice (PMN)** — entity 213 (Murray), all 26 public bodies listed.
   Body **7321 "Public Notices & Ordinances"** is the Recorder's adopted-ordinance
   feed: 206 notices total, of which **167 are ordinance notices** (165 numbered
   `O<YY>-<NN>` titles + one dot-form `O22.23` + one untitled-number notice that the
   signed document identifies as **O22-33**). The City Recorder body (2442) and
   Municipal Council body (735, 1,427 notices) were also swept — no additional
   ordinance postings.
4. **Codified code** — American Legal (`codelibrary.amlegal.com/codes/murrayut`),
   the site nav's "City Code" link. **HTTP 403 to non-browser clients** (probed
   2026-07-13) and current-consolidated-text only. Not mirrored (skill standing
   rule); recorded as the number→current-text reference for manual use.

## What exists (retrieved)

- **172 adopted-ordinance PDFs / 166 distinct ordinances** (~170 MB; 5 notices carry
  2–3 attachments) from PMN body 7321 — every attachment of every ordinance notice,
  retained verbatim in `raw/` with a sha256-bearing `_fetch_log.jsonl`.
- Coverage window: **O21-10 (adopted 2021-04-20) → O26-19 (2026-06-16)**. Distinct
  ordinances per series year: **2021: 25** (O21-10..34) · **2022: 32** ·
  **2023: 19** · **2024: 32** · **2025: 39** (incl. O25-07, mislabeled "O24-07" on
  PMN — see CLAUDE.md) · **2026: 19** (YTD).
- **81 distinct land-use ordinances** (`land_use=yes`: zoning map/text amendments,
  general-plan amendments, subdivision-code changes, annexations, street/easement
  vacations, station-area & other plan elements).
- Motion linkage (distinct ordinances): **medium 132 · low 16 · none 18** — `high`
  is structurally unattainable (Murray motions never cite ordinance numbers; see
  CLAUDE.md rubric).
- Nearly the entire corpus is **scanned** (Recorder-certified wet-signature scans,
  200-dpi CCITT; 169 of 172 files): OCR sidecars in `text/` (tesseract 5 @300 dpi),
  method labeled per row. 3 files are born-digital (`pdftotext -layout`).
  `screen_corpus.py` (2026-07-13): no cid/mojibake/PUA/stub/duplicate findings;
  flagged outliers are benign OCR artifacts (dotted TOC leaders in the 107-page
  O24-16 exhibit, noisy trailing map/exhibit pages, repeated headers in long plans).

## What does NOT exist (honest gaps — `unrecovered.csv`, 58 rows)

- **2020 and early 2021 (through 2021-04-19): no ordinance texts anywhere public.**
  PMN body 7321's feed begins at O21-10 (April 2021); AMID=95 is empty; nothing on
  Wayback. The council minutes prove **54 ordinance-adopting motions** in that window
  (43 in 2020, 11 in Jan–Apr 2021 ≈ O21-01..O21-09 plus the 2020 series) — each is a
  row in `unrecovered.csv` keyed by meeting date + motion_no, with `ordinance_no`
  blank (the minutes don't print numbers). The adoptions are real; the instruments
  are unpublished.
- **O22-02** (school-board district boundaries): PMN notice 727827 exists but has no
  attachment — adoption documented, text unrecovered.
- **O26-15** (FY2025-26 budget amendment, adopted 2026-06-02): PMN notice 1088829's
  attachment is **byte-identical (sha256) to O26-14's signed document** — a city
  mis-upload. The wrong file is retained in `raw/` (provenance) and indexed with the
  defect spelled out; its sidecar is suppressed so the wrong text can't surface under
  O26-15 in search. The true O26-15 text is unrecovered.
- **O22-30, O23-14**: absent from the PMN number series. Adoption unverified — a
  skipped number is NOT evidence an ordinance was adopted, so these are logged as
  series holes only, never as stub index rows.
- **2023 enacting motions**: the ordinance PDFs for 2023 are all here, but Murray's
  2023 council minutes are mostly lost to the Tyler TMM portal migration (5 of ~24
  meetings recovered — see the city CLAUDE.md), so 17 of the 19 2023 ordinances carry
  `match_confidence=none` with empty match fields. That is a minutes-layer gap
  reflected honestly in the linkage, not an ordinance-layer gap.
- **O24-05** (adopted 2024-02-20 per its signed text): the archive's only 2024-02-20
  minutes document is a 4:00 pm work session with no adopting motion — the evening
  meeting's minutes are not in the council archive, so the row is honestly `none`.

## Linkage confidence ceiling (structural)

Murray motions and minutes never cite ordinance numbers, so `high` (date + number
in the motion) is unattainable by source limitation; `medium` (date + subject
agreement) is the ceiling. See CLAUDE.md for the full rubric and spot-check record.
