# MAG — Plans module: SOURCES & provenance

The **published PLANS/REPORTS corpus** for Mountainland Association of Governments (MAG),
the MPO for the Provo–Orem urbanized area (Utah County) and the AOG for Utah/Summit/
Wasatch counties, as a **searchable plain-text corpus** for growth / housing /
transportation / development research. Built 2026-07-20.

This is the published-document layer MAG's data-forward build skipped. It is the
**PUBLISHED-REPORT corpus**, complementary to — not a replacement for — the adoption
record: MAG's per-motion adoption/certification log stays in `legislative/` +
`db/mag_mpo.db`. Nothing here feeds gov.db/cities.db's relational spine; the plans rows
are federated only into the **search layer** (`cities.db` `fts_minutes`/plan docs), with
`text_path` as the searchable artifact.

## Where these come from

- **magutah.gov** (`/static/files/...` tree) — the authoritative MAG file host. Publishes
  the 2023 RTP technical components + air-quality conformity determinations + amendment
  documents, the TIP conformity + Annual Listings of Obligated Projects, the transportation
  policy/procedures, the UPWP, the CEDS (MAG is the Mountainland Economic Development
  District), and the TransPlan-era long-range-plan archives.
- **frontrunner2x.utah.gov** (UDOT host) — holds the single **consolidated 2023 RTP
  narrative** PDF (TransPlan50); MAG's own RTP page serves web pages + split components,
  not one narrative file.
- **utah.gov/pmn** (Utah Public Notice) — hosts the shared **Wasatch Choice Vision
  2019-2050** (authored primarily by WFRC; MAG participates).

## Retrieval method

- Documents discovered via WebSearch + WebFetch of the MAG landing pages (RTP hub,
  RTP technical documentation, RTP amendments, TIP hub, CEDS, RPO, Station Area Planning).
- Each direct file URL was **byte-verified** (`curl -sIL` → HTTP 200 + `application/pdf`)
  before capture, then fetched and text-extracted with `pdftotext` into `text/<stem>.txt`.
- 15 of 16 documents produced clean born-digital text. The one exception — the **signed
  MPO Board AQ conformity resolution** — is a scanned signature page; `pdftotext` yielded
  no text (`needs_ocr`, near-empty sidecar), retained honestly as adoption-record
  provenance. Titles/adoption lines were spot-checked against the extracted body (a
  document is verified from its body, not its link label).

## Size policy (link, don't store, if >50MB)

All 16 raw PDFs are **retained in `raw/`** (largest = 43MB, the 2011 2040 MTP). None
exceeded the 50MB link-only threshold this pass.

## Inventory (16 documents, all with a text sidecar)

| doc_class | count | items |
|---|---|---|
| rtp | 2 | TransPlan50 RTP 2023-2050 narrative (UDOT-hosted); RTP Amendment Process (2024) |
| conformity | 4 | 2023 RTP AQ conformity (final); RTP AQ conformity Amendment 1; RTP AQ emissions Amendment 2; TIP AQ conformity 2024-2028 |
| tip | 2 | Annual Listing of Obligated Projects 2022, 2024 |
| ceds | 1 | CEDS 2024-2029 |
| vision | 1 | Wasatch Choice Vision 2019-2050 (shared WFRC/MAG, PMN-hosted) |
| guidance | 1 | 2023 Transportation Policy and Procedures |
| program_report | 1 | UPWP FY2025 |
| other | 4 | Signed AQ conformity resolution (scanned); Wasatch County Transit Study (RPO); TransPlan40 (2015); 2040 MTP (2011) |

## Scope note — MPO (Utah County) vs AOG/RPO (Wasatch Back)

Per the entity's CLAUDE.md, the built MPO records are the **Provo–Orem UZA = Utah County
only**. The plans corpus mirrors this: the RTP/TIP/conformity/UPWP documents are the Utah
County MPO's. The **Wasatch County Transit Study** (`doc_class=other`) is the one captured
document from MAG's **AOG / Wasatch Back RPO** side. No document is tagged with a repo-city
`jurisdiction` slug — MAG's published plans are region-wide, not single-city.

## Honest gaps / not-retrieved

- **No standalone MAG-hosted TIP narrative PDF.** MAG publishes the TIP as an interactive
  web app (magutah.gov/webapps/tip, apps.mountainland.org). Only the **TIP AQ conformity**
  and the **Annual Listings of Obligated Projects** exist as documents (captured).
- **No single-file 2023 RTP narrative on magutah.gov.** The consolidated narrative
  (TransPlan50) lives on UDOT's frontrunner2x host (captured, so noted); MAG serves the
  RTP as web pages (goals 1–4) + split technical components A–G.
- **Wasatch Back RPO plan / legacy RPO-library PDFs** (Wasatch County RPO Roads 2015,
  Heber Valley Parkway Study, Wasatch RTP Corridor Preservation 2010, Heber Bypass plan
  set, 2007 County Trail Projects): linked from magutah.gov/rpo-library/ but hosted on the
  legacy host **web.mountainland.org, which was UNREACHABLE** from this environment (curl
  timeout). Not byte-verifiable → logged, not captured. The current Wasatch Back RPO plan
  itself is an ArcGIS Experience app, not a PDF. The **Wasatch County Transit Study** is
  the one RPO document that verified and was captured.
- **RTP Amendment 3** emissions analysis exists only as a DRAFT PDF (not adopted) — not
  captured.
- **HB462 / Station Area Planning + Safe-Streets (SS4A) program reports** (SAP Progress
  Update Jan 2026, MPO/RPO Safety Action Plans, SAP certification policy/checklist, and
  the **city-specific SAP work scopes for Lehi/Orem/Provo/Vineyard** — all repo slugs):
  hosted on **Google Drive** (drive.google.com/file/d/… from magutah.gov/sap/ and
  ss4a.magutah.gov), not direct byte-verifiable PDF URLs. No MAG-hosted direct-PDF
  equivalents found → logged as a gap. If a direct URL is later obtained, the four city
  SAP work scopes would carry `jurisdiction` = lehi / orem / provo / vineyard.
- **No standalone regional housing plan PDF.** Housing is addressed within the CEDS and
  the shared Wasatch Choice vision.

## Verify a link

    curl -sSI -A Mozilla/5.0 -L "<source_url>" | grep -i "http/\|content-type"

Expect `200` and `application/pdf`.
