# wfrc_mpo/plans — how to use this module

The **published PLANS/REPORTS corpus** for the Wasatch Front Regional Council, as a
searchable plain-text corpus for growth / housing / transportation / development
questions. Self-contained: raw PDFs (or their live links), extracted text, a manifest.
This is the **published-report layer** — the ADOPTION record (who moved/seconded/adopted
what) stays in `legislative/` + `db/wfrc_mpo.db`; nothing here feeds the relational
spine. It federates ONLY into the search layer (`cities.db` plan docs / `fts_minutes`),
where `text_path` is the searchable artifact.

## Layout

- `raw/<stem>.pdf` — source PDF when <=50MB. Larger docs are **link-only** (not stored);
  fetch from `source_url` in `index.csv`.
- `text/<stem>.txt` — pdftotext plain text of **every** document (28/28), including the
  link-only ones. **This is the searchable layer — read/grep these.**
- `index.csv` — manifest. Columns:
  `doc_class,title,adopted_date,jurisdiction,path,text_path,format,source_url,retrieved_date,notes`.
  `path` blank = link-only; `text_path` always present; `jurisdiction` = a repo slug only
  when a doc is about ONE member city (else blank).
- `SOURCES.md` — provenance, publishers, size policy, TLC signal, honest gaps.

## Which document for which question

- **What the region is planning to build long-range:** `adopted_rtp_2023_2050`.
- **Short-range programmed projects / obligated federal dollars:**
  `tip_2026_2031_project_tables`, `federal_obligation_report_2024`/`_2023`.
  (For structured project rows, use `projects/` — this is the narrative form.)
- **Air-quality conformity:** `rtp_air_quality_conformity_memo42_2023` (RTP),
  `tip_air_quality_conformity_memo42b_2026` (TIP).
- **Regional economic-development strategy:** `ceds_2023_2028` (current, link-only),
  `ceds_2018_2023` (prior).
- **Wasatch Choice growth vision:** `wasatch_choice_2050_program_brochure_2016` (the only
  WFRC-hosted vision PDF; the live vision is a GIS map + embedded in the RTP).
- **Housing / equity / access-to-opportunity:** `housing_and_opportunity_assessment_2019`
  (no standalone Equity Focus Areas report exists — GIS/open-data only).
- **TLC — which member cities got land-use/SAP study co-funding:** grep the
  `tlc_awarded_projects_*` rollups + `tlc_report_card_2024`; single-city SAP scoping =
  `sap_murray_millcreek_rploq_2023` (jurisdiction=murray). See SOURCES.md for the repo-city
  match list.
- **HB462 station-area-planning progress / guidance:** `sap_progress_update_2025_06`,
  `sap_progress_update_final`, `hb462_station_area_planning_overview_2022`.
- **Land-use/transportation design guidance:** `creating_communities_walkable_centers_guide_2023`,
  `utah_street_connectivity_guide_2023` (link-only), `utah_active_transportation_plan_standards_2023`,
  `tlc_ordinance_assistance_one_pager`.

## doc_class vocabulary

`rtp | tip | conformity | ceds | vision | program_report | guidance | other`.
(Open set — extend if new types are added.)

## Cardinal rules (inherited from repo root)

- **Never fabricate.** Missing standalone plans (current Vision PDF, RTP amendments log,
  Equity Focus Areas report, per-study TLC reports) are **honest gaps** in `SOURCES.md`,
  not invented rows. `index.csv` lists only documents retrieved with a byte-verified live
  `source_url` whose BODY matches the title.
- **Text is derived; PDFs/URLs are canonical.** To regenerate a `text/` file, re-run
  `pdftotext raw/<stem>.pdf text/<stem>.txt` (re-fetch link-only ones from `source_url`).
