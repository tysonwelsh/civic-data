# ordinances/ — availability & honest gaps (as-of 2026-07-13)

## What exists and was retrieved

Midvale publishes its **complete signed-ordinance archive on its own Revize Document
Center** (unusual — most cities post only current-year Recorder notices). Retrieved:

- **256 signed ordinances** (Recorder-certified instruments) from
  `recorder_s_office/midvale_city_ordinances.php`, year folders **2012–2026**
  (252 O-numbered + 4 R-numbered items the city files in that folder; the 2022-O-03 a/b pair
  is two source files for one number).
- **5 publication-notice PDFs** from `recorder_s_office/public_notices.php`, retained only
  where the ordinance number has **no** signed PDF (gap-fillers): 2023-O-15, 2024-O-02,
  2024-R-06, 2024-R-08, 2024-R-20. (The other ~70 publication notices duplicate a signed
  ordinance and were deliberately not mirrored.)
- **2 `within_source` rows** (2023-O-12, 2023-O-13): adopted by a council motion but with no
  signed PDF posted — logged in `unrecovered.csv`.

**261 documents on disk (~1.0 GB), 261 text sidecars** (151 born-digital, 110 OCR).
Window **2012-O-01 → 2026-O-22**; the 2020→present mandate is **142 documents**.

## Coverage of the 2020→present mandate

Every ordinance number Midvale adopted 2020+ that has a signed PDF is here. Cross-checked
against the ordinance numbers cited in `../meeting_minutes/all_votes.csv`:

- **Adopted numbers with a signed PDF:** present.
- **Adopted numbers WITHOUT a signed PDF (real gaps):** only **2** — 2023-O-12 and
  2023-O-13 (both adopted on the record; the city simply never posted the PDF). Logged as
  `within_source` + `unrecovered.csv`.
- **Numbers that appear in a motion but were NOT adopted** (tabled/denied/failed —
  2020-O-12 failed 1-4, 2022-O-16 tabled, 2024-O-22 tabled, 2025-O-09 denied, 2026-O-05
  denied, 2026-O-13/18 tabled) are **correctly excluded** — they are not adopted ordinances.

## Linkage confidence (263 rows)

| tier | n | meaning |
|---|---|---|
| high | 107 | ordinance number cited in a passing adopting motion (all 2020+; 0 false) |
| medium | 2 | same-date subject match, number not cited |
| low | 8 | date-only, or only a table/deny motion cites the number |
| none | 144 | no adopting motion — **119 are pre-2020 (no minutes exist before the 2020 floor)** + 25 consent-agenda 2020+ adoptions with no number in the motion and an unparseable OCR clause |
| within_source | 2 | adopted by motion, no PDF (derived only from the motion) |

## Known limitations (honest)

- **Pre-2020 back-catalog (119 docs) cannot link to motions** — the audited minutes layer
  starts at the 2020 data floor. These rows are `none` by construction; kept for their
  ordinance text (they feed `fts_ordinance`).
- **OCR corpus (110 files).** The signed ordinances are wet-signature scans; adoption
  clauses and body text carry OCR noise. OCR is capped at the first 15 pages (operative text
  is at the front; trailing pages are image-only plat/map exhibits with no text).
- **106 rows are dated year-only** (`adoption_date_source=year-only`, `date=YYYY-01-01`
  placeholder, `adoption_date` blank). The year is certain; the exact day is not — either
  pre-2020 back-catalog or 2016–2017 signed templates with the day/month left blank in the
  posted copy. This is honest incompleteness, not fabrication.
- **2018-O-06 / 2018-O-08** source PDFs had corrupt xref tables (as posted by the city) —
  `gs`-repaired before OCR; noted in `extraction_method`.
- **2017-O-06** is titled "…No Action Taken" on the portal (a boundary-adjustment ordinance
  the council may not have finally enacted); pre-2020, so unlinked regardless.
- **Codified code** (`midvale.municipal.codes`) is current-consolidated text only and is not
  mirrored (skill rule) — use it manually for current MMC text.

## What was checked

City site recorder pages (ordinances + resolutions + public notices), the codifier link,
PMN entity 201 public-body list, and the ordinance-number set cited across all 2020+ council
minutes. No online source for adopted ordinances was left unretrieved.
