# murray ordinances/ — adopted zoning & land-use ordinances (build notes)

Built 2026-07-13 by the `/expand-city-sources` skill (source type 3). Additive dataset;
never touches the audited `meeting_minutes/` layer (it only READS `all_votes.csv` +
minutes markdown to compute the motion linkage).

## Where the documents come from (and why not the city portal)

- **CivicPlus Archive Center AMID=95 "Public Ordinance Adoption Archive"** — the module
  exists in the Archive dropdown but the listing returns **"There are no published
  items"** (verified 2026-07-13; no Wayback captures of the listing exist either). The
  city's own ordinance archive is publicly EMPTY.
- **The real archive is Utah Public Notice (PMN) body 7321 "Public Notices &
  Ordinances"** (entity 213 = Murray, govType 3). The Recorder posts each adopted
  ordinance as a notice titled `O<YY>-<NN> <subject>` with the signed, certified
  ordinance PDF attached (`/pmn/files/<FILE_ID>.pdf`). The full history is one GET:
  `https://www.utah.gov/pmn/list/notices.html?id=7321&page=200`. Crawled notice
  metadata is retained in `pmn_notices.csv` (notice_id, title, event/posted dates,
  attachment file ids) — the build input.
- **Codified-code host: American Legal** —
  `https://codelibrary.amlegal.com/codes/murrayut/latest/murray_ut/` (the "City Code"
  link in the site nav). **403 bot-protected** (probe 2026-07-13) and
  current-consolidated-text only — NOT mirrored, per the skill's standing rule. The
  adopted-ordinance PDFs + council minutes are the backbone; use the code host manually
  for current consolidated text.

## Files

- `raw/` — every PMN attachment verbatim (172 PDFs, ~170 MB) + `_fetch_log.jsonl`
  (url, status, bytes, sha256 per fetch). Filenames: `<OrdNo>_n<noticeId>_f<fileId>.pdf`.
- `text/` — 171 sidecars (172 files minus the suppressed O26-15 wrong-attachment
  duplicate). **~98% of the corpus is 200-dpi CCITT scanned images**
  (Recorder-certified wet-signature scans; no text layer), so the sidecars are
  **tesseract 5 OCR @300 dpi** — expect OCR noise (garbled ordinals, `'` for `th`),
  flagged per row in `extraction_method`. 3 files are born-digital
  (`pdftotext -layout`). Source typos and OCR errors are preserved, never "cleaned".
  `screen_corpus.py` run 2026-07-13: clean (no cid/mojibake/stub/dupes; outliers are
  benign scan artifacts — see AVAILABILITY.md).
- `index.csv` — SCHEMA_SPEC §9 contract header + extras
  (`pmn_notice_id,pmn_notice_url,pmn_event_date,adoption_date_source,linkage_note`).
  **172 rows / 166 distinct ordinances** (O21-10 2021-04-20 → O26-19 2026-06-16);
  one row per retained PDF; multi-attachment notices (5) produce one row per file
  sharing the `ordinance_no` and its linkage. Distinct-ordinance linkage (rebuilt
  2026-07-16 after the pmn_backfill minutes promotion landed the 2023 enacting
  motions): **medium 145 · low 21 · none 0** (row-level 151/21/0; was distinct
  132/16/18 — every TMM-gap `none` resolved; O24-05 is `low` with no motion_no, its
  2024-02-20 adoption date carrying only Committee-of-the-Whole-style minutes);
  `land_use=yes`: 81 distinct.
- `unrecovered.csv` — the honest gap log (see AVAILABILITY.md).
- `build_index.py` — regenerates `index.csv` + `unrecovered.csv` from `pmn_notices.csv`
  + `raw/` + `text/` + the minutes layer. Idempotent, no network.

## Adoption date (`adoption_date` / `date`, provenance in `adoption_date_source`)

1. `pdf+calendar` — parsed from the signed document's adoption clause
   ("PASSED, APPROVED AND ADOPTED … this Nth day of Month, YYYY"). OCR mangles the
   ordinal day token (`20"`, `1S'`, `215'`), so the day reading is validated against
   the actual council-meeting dates in `all_votes.csv` for that month+year (2-digit
   reading preferred, then 1-digit). Strongest.
2. `pdf-only` — clause parsed but the day couldn't be calendar-validated (e.g. the
   2023 minutes gap leaves no calendar); first plausible reading used.
3. `pmn-event` — fallback: the PMN notice "Event Start Date & Time". For
   meeting-linked notices this is the 6:30 PM council meeting; **early-2021 notices
   sometimes carry a Friday posting date instead** — those simply fail the meeting
   join and stay honest.

## Motion linkage (`matched_motion_date`, `matched_motion_no`, `match_confidence`)

Murray council motions **never cite ordinance numbers** ("moved to adopt the
Ordinance") and the minutes never print them, so the rubric's `high` (date + number
both cited in the motion) is **structurally unattainable here — `medium` is the
ceiling**, by source limitation, not extraction weakness.

- `medium` — adoption date has council minutes AND the PMN subject tokens clearly
  select one motion's minutes context (best keyword-overlap score ≥2 and above the
  runner-up; each motion claimable once).
- `low` — the date has minutes + ordinance-adopting motions, but subject evidence is
  weak or tied. `matched_motion_date` is set; `matched_motion_no` only when exactly
  one candidate motion exists that day.
- `none` — no council meeting/minutes on the adoption date. Was dominated by the
  **2023 TMM minutes gap**; since the 2026-07-16 promotion of the recovered 2023
  minutes there are **0 none rows**. Match fields left empty; never forced.

Mechanics: motion contexts are rebuilt with the audited extractor's own grammar
(`extract_votes.py` `INTRO_RE`/`VERB_LEAD`, imported read-only), aligning each
`all_votes` motion to its anchor line by motion-text head; a motion's context = the
minutes text from the previous motion's anchor down to its own (this window contains
the "Consider an ordinance …" agenda item heading). motion_no ↔ document order was
verified against movers (2021-06-15). `result` is the matched motion's verbatim
result string.

Spot-checked: O24-13 (zoning map C-D→R-M-20) → 2024-06-18 #3; O21-25 (ADU 17.78) →
2021-09-21 #3; O21-28 (Village/Centers Mixed Use) → 2021-10-19 #5 (a 3-2 contested
adoption) — all confirmed against the minutes text.

## `ordinance_no` quirks (city-faithful, with one documented preference)

- Numbers are as printed in the PMN notice title (`O<YY>-<NN>`, zero-padded), except:
  when the **signed document's own printed number** is legible, differs from the
  notice title, and matches the adoption year while the title doesn't, the document
  number wins (the title is a clerk label; the signed ordinance is the instrument).
  Both cases are spelled out in `linkage_note`:
  - PMN notice 979307 is titled "O24-07" but wraps **ORDINANCE NO. 25-07** (adopted
    2025-03-04) — indexed as `O25-07` (this also fills the apparent O25-07 series
    hole; the real O24-07, notice 905047, is indexed normally).
  - PMN notice 789499 has **no number in its title** ("AN ORDINANCE AMENDING CHAPTER
    17 …", event 2022-10-18) — the signed document prints **ORDINANCE NO. 22-33**,
    indexed as `O22-33` (this fills one of the two apparent 2022 series holes).
- `O22.23` (dot form, notice 768343) is normalized to `O22-23`; the notice title is
  kept verbatim in `title`.
- **O26-15 wrong attachment (city mis-upload):** notice 1088829's PDF is
  byte-identical (sha256) to O26-14's signed document. The file is retained in
  `raw/` verbatim, the row carries the defect in `linkage_note` +
  `extraction_method`, its sidecar is suppressed (the text belongs to O26-14), and
  the true O26-15 text is logged in `unrecovered.csv`. Handled via the
  `WRONG_ATTACHMENT` table in `build_index.py`.

## land_use

Keyword classification over title + PMN description + the first ~1.5 KB of document
text (zoning / land use / general plan / subdivision / annexation / vacation /
easement / Title 16–17 MCMC / station-area & master plans / ADU etc.). It is a
convenience filter, not a legal category — check the document before quoting.

## Regeneration

```
python3 build_index.py          # index.csv + unrecovered.csv (no network)
```
Re-crawling PMN (new adoptions): re-fetch `notices.html?id=7321&page=200`, append new
rows to `pmn_notices.csv`, fetch new attachments into `raw/` via
`scripts/polite_fetch.py`, OCR them into `text/`, then rerun `build_index.py`.
