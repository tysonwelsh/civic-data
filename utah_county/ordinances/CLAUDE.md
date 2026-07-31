# utah_county/ordinances — how to use this module

The **codified ordinances of Utah County** as a searchable plain-text corpus, plus an
**adopted-ordinance catalog** (numbers / dates / titles) reconstructed from the code's
own amendment histories. Self-contained: extracted text, a code-book manifest, a section
catalog, and the adopted-ordinance catalog. Nothing here writes to the db. Utah County is
a **3-member Board of Commissioners** county (FIPS 49049); the **Land Use Ordinance
governs only the unincorporated areas** (incorporated cities run their own codes).

## Layout

- `text/<stem>.txt` — extracted text of each codified book. **The searchable layer —
  read/grep these.**
  - `land_use_ordinance.txt` — the zoning/land-use code (UCLUO), 132 sections.
  - `code_of_ordinances.txt` — the general county code, 915 sections.
  - `county_policies.txt` — internal administrative policies, 74 sections (not land-use).
- `index.csv` — the **code-book manifest** (3 rows), with SCHEMA_SPEC §9 primary-document
  columns (`doc_class=code_snapshot, fetch_status, sha256, text_chars`) from day one.
  `path` is blank (the code is a Municode web book, not a stored PDF).
- `code_sections.csv` — the **navigable section catalog** (1,121 rows): `book,
  section_no, section_title, char_count`. Use this as the table of contents.
- `adopted_ordinances.csv` — the **adopted-ordinance catalog** (322 rows, 1997→2026).
- `SOURCES.md` — provenance, the SPA/print-view retrieval workaround, the recodification
  correction, and honest gaps. `raw/` is empty by design.

## Which artifact for which question

- **What does the zoning / land-use code say** (setbacks, ADUs, agricultural zones,
  flood/hazard, subdivisions, conditional uses): grep `text/land_use_ordinance.txt`;
  find the section via `code_sections.csv` (book = "Land Use Ordinance").
- **General county governance rules** (finance, health, business licensing, roads):
  `text/code_of_ordinances.txt`.
- **Which ordinances were adopted, when, on what** (growth/housing trend over time):
  `adopted_ordinances.csv` — 303 land-use ordinances 1997→2026, each dated, with the
  amendment description. Filter `land_use='yes'`.
- **Who voted for an ordinance:** NOT available here yet — `matched_motion_*` columns are
  blank; a downstream closing pass links these to the enacting Commission motion.

## The adopted-ordinance catalog — what it is and is NOT

`adopted_ordinances.csv` is **reconstructed from the amendment-history citations printed
inside the codified text** (e.g. "Amended by Ord. 2025-341 Updated Parking on
4/24/2025"), because the county publishes no standalone ordinance register. Therefore:

- It is a **floor, not a complete register.** Ordinances that never amended a codified
  section — most parcel-specific **rezones** (they change the zoning MAP, a GIS layer,
  not the ordinance text), budget ordinances, one-off resolutions — are **not** captured.
- `title` is the ordinance's **amendment description**, not its formal signed caption.
- `adoption_date` and `ordinance_no` are verbatim from the code's history and reliable.

## Cardinal rules (inherited from repo root)

- **Never fabricate — especially ordinance numbers and enacting votes.** Every
  `ordinance_no`/`adoption_date` is copied verbatim from the code's amendment history;
  the enacting-vote columns are **left blank** (Utah County is not a Legistar county and
  its Commission votes are not yet in the db) rather than guessed. The catalog's
  incompleteness is documented, not papered over.
- **Text is derived; the Municode web book + `source_url` are canonical.** Regenerate by
  re-fetching `book/print?type=<book>` and re-running the section splitter (SOURCES.md).
- **Verify before quoting substance.** The codified text is the county's own published
  code; for the exact operative wording of a specific ordinance, the signed ordinance in
  the Clerk's record is the ultimate source.

## Scope / follow-ups (for the closing pass)

- **Enacting-vote linkage** for the 322 catalogued ordinances — join `ordinance_no` /
  `adoption_date` to the Commission legislative motions once that db exists.
- **Zoning-map rezone ordinances** — capture from the Commission agenda/minutes +
  the GIS zoning layer (gis/ module), since they don't surface in the code text.
- A **signed adopted-ordinance register** (if the Clerk publishes one) would upgrade the
  catalog from a floor to a complete list and supply formal captions + ordinance numbers
  for map-only rezones.
