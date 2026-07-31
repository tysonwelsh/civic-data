# WFRC — Plans module: SOURCES & provenance

The **published PLANS/REPORTS corpus** for the Wasatch Front Regional Council (WFRC),
the MPO for the greater Salt Lake–Ogden area, as a **searchable plain-text corpus** for
growth / housing / transportation / development research. Built 2026-07-20.

This is the published-document layer WFRC's data-forward build skipped. It is the
**PUBLISHED-REPORT corpus**, complementary to — not a replacement for — the adoption
record: WFRC's per-motion adoption/certification log stays in `legislative/` +
`db/wfrc_mpo.db`. Nothing here feeds gov.db/cities.db's relational spine; the plans
rows are federated only into the **search layer** (`cities.db` `fts_minutes`/plan docs),
with `text_path` as the searchable artifact.

## Where these come from

- **wfrc.utah.gov** (and its 301-alias `wfrc.org`) — the authoritative WFRC file tree.
  Publishes the adopted RTP, the TIP + Federal Obligation Reports + air-quality
  conformity memos, the CEDS (WFRC is the Wasatch Front Economic Development District),
  the Transportation and Land Use Connection (TLC) award rollups + report card, the
  HB462 Station Area Plan progress reports, and agency accomplishments reports.
- **wasatchchoice.org** — the Wasatch Choice vision/toolbox site (WFRC + partners).
  Hosts the toolbox guidance (Creating Communities walkable-centers guide, Utah Street
  Connectivity Guide, Utah Active Transportation Plan Standards).

## Retrieval method

- Documents discovered via WebSearch + WebFetch of the WFRC/Wasatch Choice landing pages
  (RTP, TIP, TLC, CEDS, Access-to-Opportunities, HB462 SAP, Wasatch Choice resources).
- Each direct file URL was **byte-verified** (`curl -sIL` → HTTP 200 + `application/pdf`)
  before capture, then fetched and text-extracted with `pdftotext` into `text/<stem>.txt`.
- All 28 documents produced clean born-digital text (no OCR floor hit). Titles/adoption
  lines were spot-checked against the extracted body (a document is verified from its
  body, not its link label).

## Size policy (link, don't store, if >50MB)

Raw PDFs **retained in `raw/`** (<=50MB): all but two.
Raw PDFs **link-only** (>50MB — `path` blank in index, `source_url` is the live PDF,
**text still extracted** to `text/`): CEDS 2023-2028 (64MB), Utah Street Connectivity
Guide (59MB).

## Inventory (28 documents, all with extracted text)

| doc_class | count | items |
|---|---|---|
| rtp | 1 | Adopted RTP 2023-2050 |
| tip | 3 | TIP 2026-2031 project tables; Federal Obligation Reports 2023, 2024 |
| conformity | 2 | RTP AQ conformity memo #42 (A1); TIP AQ conformity memo #42B |
| ceds | 2 | CEDS 2023-2028 (current, link-only), CEDS 2018-2023 (prior) |
| vision | 1 | Wasatch Choice 2050 Consortium Program brochure (2016) |
| program_report | 12 | TLC Report Card 2024; TLC Awarded Project Descriptions 2020–2026 (7); Housing & Opportunity Assessment; 2 HB462 SAP Progress Updates; WFRC FY2022 Accomplishments |
| guidance | 6 | TLC Ordinance Assistance one-pager; HB462 SAP overview (2022); Murray North SAP RPLOQ; Creating Communities guide; Utah Street Connectivity Guide (link-only); Utah ATP Standards |
| other | 1 | WFRC Racial Justice/Equity/ATO statement (2020) |

## TLC (Transportation and Land Use Connection) — the member-city co-funding signal

TLC co-funds member-city land-use / station-area / general-plan studies. WFRC does NOT
host the individual completed-study reports as discrete PDFs (they live on member-city
sites; the master index is the ArcGIS **TLC Project Map**). What IS captured here: the
**annual Awarded Project Descriptions** rollups (2020–2026) + the 10-year **Report Card
2024** (152 projects, 88% of communities, ~$18M partner investment).

Repo member-cities that appear in the recent TLC award rollups (grep the
`tlc_awarded_projects_*` / `tlc_report_card_2024` text): **alta, copperton, draper,
holladay, magna, midvale, millcreek, slc** (2026 cycle); **south_salt_lake, murray,
sandy, kearns, millcreek, ogden** (2025 cycle); plus **white_city, bluffdale, riverton**
named in the Report Card history. A study clearly about ONE repo city carries that city's
slug in the `jurisdiction` column — currently only the **Murray North Station SAP RPLOQ**
(`jurisdiction=murray`) is a WFRC-hosted single-city document; the award rollups are
multi-city and left blank.

## Honest gaps / not-retrieved

- **No standalone current Wasatch Choice 2050 Vision PDF.** The current Vision is
  delivered as an interactive map (wasatchchoice.org vision-map, ArcGIS) and embedded in
  the adopted RTP. Only the **2016 Consortium program brochure** exists as a WFRC-hosted
  vision PDF (captured, `doc_class=vision`).
- **No single RTP amendments-LOG document — but per-amendment resolutions ARE published.**
  The adopted-RTP **amendments page**
  (<https://wfrc.utah.gov/regional-plans/regional-transportation-plan/adopted-rtp/amendments/>)
  lists the RTP 2023-2050 amendments (≥4 as of 2026-07-22), each with a signed **resolution
  PDF** — there is just no rolled-up single "amendments log" file. **Capture is QUEUED**
  (WFRC_NATIVE_SPEC.md Phase 2). Per-amendment air-quality conformity lives in the AQ memo
  series (memo #42 "A1" captured).
- **No standalone Access to Opportunity / Equity Focus Areas report.** That layer is
  GIS/open-data only (ATO Impact Tool, Workplace ATO Web Map, Housing Site Evaluator, and
  the Equity Focus Areas open-data layer at data.wfrc.org). The closest published report
  is the **Housing and Opportunity Assessment** (captured, `doc_class=program_report`).
- **No WFRC-hosted per-study TLC completed-study PDFs.** Index is the ArcGIS TLC Project
  Map; the annual award rollups (captured) are the document-form proxy.
- **RTP appendices A–M** are linked separately on the adopted-RTP page (App H is a Google
  Sheet); only the main RTP narrative is captured here.
- **Federal Obligation Report set (2023 + 2024) is COMPLETE AS PUBLISHED** (note
  2026-07-22). Research verified no earlier-year obligation reports are online — WFRC's site
  links only the FFY2023 + FFY2024 reports (both captured, `doc_class=tip`). This is an
  honest publication ceiling, not a partial capture.

## Verify a link

    curl -sSI -A Mozilla/5.0 -L "<source_url>" | grep -i "http/\|content-type"

Expect `200` and `application/pdf`.
