# summit_county/ordinances — how to use this module

**Summit County's two land-use Development Codes + adopted land-use/housing ordinances**
as a searchable plain-text corpus. Self-contained: raw PDFs, extracted text, a manifest.
Nothing here writes to the db. Built 2026-07-20.

## Layout

- `raw/<stem>.pdf` — the ordinance/code PDF (all born-digital, <50 MB, retained).
- `text/<stem>.txt` — `pypdf`-extracted text. **This is the searchable layer — grep these.**
- `index.csv` — the manifest, one row per **distinct code or adopted ordinance**. Columns:
  `ordinance_no, title, adoption_date, land_use_type, planning_district, matter_id,
  motion_id, match_confidence, path, text_path, format, source_url, notes`.
- `SOURCES.md` — provenance, retrieval method, and the honest gaps.

## Two Development Codes (the land-use foundation)

Summit County has **two separate land-use codes**, one per planning district:
- **Title 10 — Snyderville Basin Development Code** (`land_use_type=development_code`,
  Snyderville Basin). LIVE on Municode (link-only; the 20% inclusionary-zoning set-aside
  lives here).
- **Title 11 — Eastern Summit County Development Code** (Eastern). County consolidated PDF
  retained + Municode link.

## Which row for which question

- **Land-use / zoning / growth ordinances with full text**: Ord **912** (NMU-1 mixed-use
  zone in the Basin code), Ord **936** (water-wise landscaping), Ord **1003** (Basin GP
  Ch 8 — Sustainable Development / Water Use / Agriculture).
- **General Plan & Moderate-Income-Housing adoptions**: Ord **839** (Basin GP), **950/951**
  (Basin/Eastern MIH), **962/968/980** (MIH amendments) — catalogued here with **blank
  `path`**; the full text is in the **`plans/` module** (follow the note/`source_url`).
- **Full codified code text**: open Municode via the `source_url` (Title 10 / Title 11).

## Cardinal rules (inherited from repo root)

- **Enacting-vote linkage is honestly BLANK.** `matter_id` / `motion_id` /
  `match_confidence` are empty for every row (out of scope this pass) — never fabricated.
  A later pass can populate them from the county's agenda/minutes system.
- **Never fabricate dates.** Ord 912 and 936 are pre-signature drafts with blank signature
  dates → `adoption_date` blank, Council/PC dates in `notes`. Some MIH dates are
  OCR-inferred (see `plans/`).
- **Text is derived; the PDF + `source_url` are canonical.** Regenerate with `pypdf`
  (command in SOURCES.md). Title 10 is link-only (Municode).

## Scope / follow-ups

- Targeted **land-use/housing** catalog, not the complete ordinance book — enumerating
  every adopted ordinance (Municode OrdBank) is a logged follow-up (its API was not
  scrapable on 2026-07-20).
- **Enacting-vote linkage** (matter/motion ids) is the primary open follow-up.
