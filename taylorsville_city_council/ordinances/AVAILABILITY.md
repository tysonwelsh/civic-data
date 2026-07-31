# ordinances/ — availability & gap record

**As-of: 2026-07-06.** What was checked, what exists, what does not.

## What EXISTS and was retrieved

- **90 ordinances indexed, 2020-01-08 → 2026-05-06** (`index.csv`), the repo's 2020 floor.
- **84 with a retained independent ordinance PDF** in `raw/` (588 MB) from **Utah Public
  Notice, council body 720** (`utah.gov/pmn`). 81 born-digital `text`, 3 `scanned` (OCR'd).
- **6 `within_source`** ordinances (cited in adopted council motions, no independent PDF
  posted) carry the minutes doc as `source_url`, no `raw/` file.
- Per year: 2020=19, 2021=16, 2022=13, 2023=8, 2024=11, 2025=17, 2026=6.
- **Land-use share: 64/90 = 71 %** (zoning map/text amendments, general-plan amendments,
  land-development-code changes, ROW/easement vacations, etc.).
- Confidence: **75 high, 9 medium, 6 within_source** (see `CLAUDE.md` for definitions).

## What does NOT exist (verified dead ends)

- **No city-hosted adopted-ordinance archive / "Notice of Adoption and Summary" page.** The
  city's `public-notices` page carries meeting/budget/quorum notices only — zero ordinance-
  adoption notices.
- **municipalcodeonline.com** — Taylorsville is **not a client** (S3 bucket listed publicly;
  0 `taylorsville/` keys).
- **American Legal** (`codelibrary.amlegal.com/codes/taylorsvilleut`) — the codified-code
  host, but **403 bot-protected and current-consolidated-text only** (no per-ordinance
  adoption dates or downloadable ordinance list). The city's `city-code-ordinances` and
  `review-a-city-ordinance` pages only iframe it.
- Because of the above, **PMN body 720 is the sole independent ordinance-document source** —
  and it is a good one (attaches meeting-material + signed/executed final PDFs).

## Known gaps & caveats

1. **Pre-2020 back-catalog is available but NOT indexed.** PMN body 720 also holds **~129
   distinct ordinance numbers for 2012–2019** (years 12–19 all present). They are out of scope
   (below the 2020 floor; no matching votes to link) — retrievable later from the same source
   (`utah.gov/pmn/list/notices.html?id=720&page=400`) if the floor is ever lowered.
2. **Parallel ordinance/resolution numbering** — `Ordinance NN-NN` and `Resolution NN-NN` are
   different documents. 20-09/20-10/20-11, 22-27, 22-28, 25-25 are cited as **ordinances** in
   the minutes but PMN posted only a same-numbered **resolution** (or nothing) → they are
   `within_source`, not corroborated. Do not conflate with the resolutions.
3. **9 `medium` ordinances** (22-08, 24-05, 24-07, 25-01, 25-02, 25-03, 25-07, 25-08, 25-15)
   have signed PMN adopted PDFs but their number is **absent from the `all_votes.csv` motion
   text** — a vote-layer citation gap, not a missing ordinance. All 9 were adopted.
4. **3 scanned ordinances** (24-01, 24-02, 24-04) are RICOH JPEG-image PDFs, OCR'd with
   tesseract (labeled `format=scanned`, `extraction_method=tesseract-ocr`). Expect minor OCR
   noise in those text sidecars; the index title/date are clean (vote-derived).
5. **2020 PDFs are Agenda-Summary-Form bundles** (staff report + ordinance, ~3.4 MB), not
   thin signed ordinances — PMN posted no separate signed finals for 2020. They contain the
   full ordinance text.
6. Two text sidecars (20-06 form fields; 26-05 legal/parking vocabulary) are low-dictionary-
   ratio on the corpus screener — reviewed, legitimate, not garbled.
