# ordinances/ — sources

Cataloged 2026-07-20. This is a **metadata catalog**, not a full ordinance text corpus — see
`gaps.csv` for the two structural walls.

- **Codified code:** American Legal Publishing —
  `codelibrary.amlegal.com/codes/washingtoncout`. Numbering **YYYY-NNNN-O**, **current through
  Ord. 2026-1318-O**. Land-use titles: **Title 10 Zoning Regulations**, **Title 11 Subdivision
  Regulations** (structure confirmed via web search — e.g. §10-29-4). **HTTP 403 to every
  automated fetcher** (curl + WebFetch) — bot-blocked. Text NOT scraped around the block (repo
  rule); recover manually via browser or the county Community Development Dept.
- **County site:** publishes a browsable **resolutions** archive (684 R-YYYY-NNNN docs
  2019–2026 at `/forms/commission/resolutions/`) but **NO ordinance archive**. Ordinance PDFs
  surface only as scattered `wp-content/uploads/comdev-ordinance-*.pdf` links on topic pages.
- **Recovered free text (this pass):** **Ord. 2025-1295-O** — 2025 Moderate Income Housing
  amendment (`wp-content/uploads/2025/06/comdev-ordinance-2025-1295-O.pdf`; scanned → tesseract
  OCR). Adopted-ordinance **numbers** are otherwise discoverable in the OCR'd legislative
  minutes corpus (`../legislative/minutes/`).

No vote linkage (`matter_id`/`motion_id` blank) — this county has no vote layer (see
`../CLAUDE.md`).
