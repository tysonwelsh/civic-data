# cache_county/ordinances — SOURCES & provenance

## Codification (Cache County publishes on multiple platforms)

Cache County's ordinances are codified and published in parallel on:

1. **American Legal Publishing** — the compiled **County Code** PDF, current through
   **Ord. 2023-18 (passed 2023-05-09)**, hosted by the county at
   `https://www.cachecounty.gov/assets/department/clerk/cachecountyut-ut-2.pdf`
   (also `library.amlegal.com`). **This is the source stored in `raw/` + `text/`.**
2. **Municipal Code Online** (General Code) — `https://cachecounty.municipalcodeonline.com`
   — a live, browsable HTML copy (Title 17 = land use/zoning).
3. **Municode / CivicPlus** — `https://library.municode.com/ut/cache_county` — a second
   live HTML copy.

The county Clerk's landing page for the code is
`https://www.cachecounty.gov/clerk/county-code.html`.

## Retrieval method (2026-07-20)

1. Downloaded the American Legal compiled code PDF (260 pp, born-digital) → `raw/` and
   pypdf text → `text/`.
2. Parsed the Title/Chapter headings → `code_structure.csv` (17 Titles + the Title
   15/16/17 land-use chapters).
3. Extracted every `(Ord. <number>[, <date>])` citation from the code's section
   source-notes → `index.csv` (169 distinct ordinances, 1965-2023-ish). Each citation's
   surrounding Title context tags `land_use_type` (`land_use` if it touched Title
   15/16/17). `adoption_date` is filled only where the code printed a date.

Regenerate text: `python3 -c "from pypdf import PdfReader; open('text/cache_county_code_amlegal.txt','w').write('\n'.join((p.extract_text() or '') for p in PdfReader('raw/cache_county_code_amlegal.pdf').pages))"`

## Honest gaps / scope limits

- **Code-amending ordinances only.** The catalog is derived from codified source-notes, so
  it lists ordinances that changed **code text**. **Rezone (map-amending) ordinances are
  absent** — they don't source-note into the code; find them in `land_use/` (PC motions)
  and the County Council record.
- **Enacting-vote linkage is DERIVED** (2026-07-29): `python3 db/link_ordinances.py`
  computes `motion_id`/`match_confidence` from the named-roll legislative db under seven
  documented guards; 17 of 169 link uniquely (all 2021–2022), 8 more are named on the floor
  but honestly unlinkable. **Rerun it after every `db/build_db.py`** — a rebuild renumbers
  `motion_id`, and stale hand-written ids are what audit F8 caught.
- **Dates only where printed.** Many citations carry no date in the code; those rows have
  blank `adoption_date` (never inferred). Ordinance numbers are verbatim, including old
  2-digit-year forms (`65-03`, `91-02`) — no calendar year is asserted onto them.
- **Coverage floor:** codified through **Ord. 2023-18 (2023-05-09)**; later ordinances are
  not in this snapshot. Refresh by re-pulling the compiled PDF when the county re-codifies.
- Individual pre-2020 ordinance PDFs (the signed originals) are not attached by the county
  online the way a Legistar county attaches them; the compiled code is the authoritative
  consolidated text.
