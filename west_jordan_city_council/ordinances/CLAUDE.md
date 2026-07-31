# ordinances/ — build & linkage notes

**Dataset:** Adopted West Jordan City ordinances 2020–2026, focused on zoning / land-use
(rezones, General Plan & Future Land Use Map amendments, Title 13 land-development-code text
amendments, master development agreements, annexations). Additive; does not modify any
existing dataset.
**As-of:** 2026-07-03; **backfill 2026-07-19** (8 owed ordinances 26-26..33 added — 6 signed
PDFs retrieved `high`, 2 postponed/tabled `within_source`). Built by `expand-city-sources` SOURCE 3.

## What this dataset is

Two layers merged into one `index.csv` (293 rows):

1. **Backbone (290 rows) — derived from the council vote record.** Every distinct
   `Ordinance No. YY-NN` cited in a motion in `meeting_minutes/all_votes.csv` (2020-01 →
   2026-06). For each number we take its last *passing* approve/adopt motion as the adoption
   event (or the last motion if it was denied/tabled). This gives number → adoption_date →
   subject → the exact motion (`matched_motion_date`, `matched_motion_no`).
2. **Signed ordinance PDFs (67 files) — the independent City-Recorder text.** Recorder-
   certified signed PDFs retrieved from the city website, one per ordinance where the city posts
   one (zoning/land-use plus, from the 2026-07-19 backfill, the compensation/budget/streetlight/
   code-amendment ordinances the Recorder page now posts). 64 of these correspond to a backbone
   motion; 3 do not (see discrepancy note below).

## Linkage method & confidence (the `match_confidence` column)

- **`within_source` (226 rows)** — ordinance known ONLY from the motion text. The number→date
  →subject index is *derived from* the motion, so the linkage is true **by construction, not by
  independent corroboration.** Per the SKILL's minutes-as-backbone rule this is deliberately a
  distinct value (NOT `high`) so it is never read as cross-checked. `format=na`, `path` empty,
  `source_url` = the minutes markdown that the motion was extracted from.
- **`high` (64 rows)** — a backbone ordinance for which we ALSO retrieved the independent
  recorder-signed PDF. Two independent sources (the council motion AND the certified ordinance
  document) agree on the ordinance number; where the PDF's enactment clause was checkable the
  adoption date agreed too (e.g. 22-47 signed "2nd day of November 2022" = motion 2022-11-02).
  Every signed PDF was verified to internally cite the same ordinance number as its filename
  (0 mislabels across 61 files), so no false match inflates this bucket.
- **`none` (3 rows)** — 22-08, 23-08, 24-18: a real signed ordinance PDF exists (retrieved),
  but the number is **not cited in any all_votes.csv motion.** No motion to match → empty match
  fields, `disposition=pdf_only`. This is a genuine cross-source discrepancy, flagged in
  `AVAILABILITY.md`; the votes layer was **not** edited.

**Never forced a match.** A backbone ordinance with no PDF keeps `within_source`; a PDF with no
motion keeps `none`. The two 2026-07-19 postponed ordinances (26-29 / 26-30, Sugar Factory on
Town Creek, postponed 2026-06-09 to a date uncertain) correctly have no adopted signed PDF and
stay `within_source` / `disposition=tabled` — the Recorder posts nothing for a matter still pending.

## Extraction

- 64 born-digital signed PDFs → `pdftotext -layout` (text sidecars in `text/`, `format=text`).
  (The 6 backfilled 2026-06 PDFs are all born-digital; each internally cites its own number and a
  matching adoption date — 26-26/27/28/31 "9th day of June 2026", 26-32/33 "23rd day of June 2026".)
- 3 pure-image scans (22-14, 24-14, 24-59 — one image/page, no text layer) → **tesseract OCR
  @200dpi**, `format=scanned`, `extraction_method` labels this. OCR text is error-prone; preserved
  as produced (no LLM clean-up).
- `screen_corpus.py` over `text/` (67 files): clean — 0 mojibake / garble / stub / dup;
  dict_ratio median 0.81. The only advisory flag is `ends_mid` (55/61), expected because
  ordinances end in signature blocks / exhibits.

## Host findings (see AVAILABILITY.md for the full gap ledger)

- **Codified code host = Municode** (`library.municode.com/ut/west_jordan`) — an **Angular SPA
  serving only the current consolidated code**; no per-ordinance adoption archive is reachable
  by a polite GET. Current-text-only, as the SKILL warns. Not used as a per-ordinance source.
- **Adopted-ordinance list = City Recorder "Adopted Ordinances" page**
  (`westjordan.utah.gov/city-recorder/adopted-ordinances/`) — best source for **2024–2026** but
  lazy-loads (WebFetch saw ~90 links, raw curl ~51). Signed PDFs live at
  `/wp-content/uploads/YYYY/MM/Ordinance-No.-YY-NN-<slug>-signed.pdf`. The WordPress media REST
  API is **locked** (`/wp-json/wp/v2/media?search=` returns 0), so PDFs are discovered via web
  search, not enumeration.
- **Pre-2022 signed PDFs** sit on a legacy hashed host `assets.westjordan.utah.gov/ugd/c1b6d4_<hash>.pdf`
  (pre-migration Wix/Duda) that is **not enumerable** — only surfaces when a search engine has
  indexed the exact hash. **All of 2020 is effectively unavailable** as signed PDFs.
- **PrimeGov** (`westjordan.primegov.com`) exposes **no dedicated ordinance document type** — the
  adopted ordinance is embedded inside each meeting's bulky "Complete Packet" PDF, not published
  as a standalone document. So PrimeGov is not a practical per-ordinance source here.

## Reproduce

1. Backbone: parse `meeting_minutes/all_votes.csv` for `Ordinance No\.?\s*(\d{2}-\d+)` in the
   `motion` column; group by number; pick last passing approve/adopt motion.
2. PDFs: web-search `westjordan.utah.gov "Ordinance No. YY-NN" <subject> signed pdf`; fetch via
   `scripts/polite_fetch.py --out ordinances/raw/ --now 2026-07-03T00:00:00Z --batch <urls>`.
3. Extract (`pdftotext -layout`; tesseract for image scans), screen, then merge → `index.csv`.

## Columns

`ordinance_no, adoption_date, date` (=adoption_date alias, required non-empty), `title` (subject
from the motion or the pdf-only note), `source_url` (signed-PDF URL for high/none rows; the
minutes markdown for within_source rows), `retrieved_date, format, extraction_method, path`
(incl. `raw/`; empty for within_source), `land_use` (Y/N), `result` (the vote tally string;
blank where no motion), `matched_motion_date, matched_motion_no,
match_confidence`, plus `disposition` (adopted/denied/tabled/unclear/pdf_only).
