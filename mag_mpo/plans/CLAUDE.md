# mag_mpo/plans — how to use this module

The **published PLANS/REPORTS corpus** for Mountainland Association of Governments, as a
searchable plain-text corpus for growth / housing / transportation / development
questions. Self-contained: raw PDFs, extracted text, a manifest. This is the
**published-report layer** — the ADOPTION record (who moved/seconded/adopted what) stays
in `legislative/` + `db/mag_mpo.db`; nothing here feeds the relational spine. It
federates ONLY into the search layer (`cities.db` plan docs / `fts_minutes`), where
`text_path` is the searchable artifact.

## Layout

- `raw/<stem>.pdf` — source PDF (all 16 retained; none exceeded 50MB this pass).
- `text/<stem>.txt` — pdftotext plain text of every document. **This is the searchable
  layer — read/grep these.** One sidecar (`rtp_aq_conformity_signed_resolution_2023`) is
  near-empty: that source is a scanned signature page (needs_ocr, kept honestly).
- `index.csv` — manifest. Columns:
  `doc_class,title,adopted_date,jurisdiction,path,text_path,format,source_url,retrieved_date,notes`.
- `SOURCES.md` — provenance, publishers, the MPO-vs-RPO scope note, honest gaps.

## Which document for which question

- **What the region is planning long-range (Utah County MPO):** `rtp_transplan50_2023`
  (the consolidated adopted 2023 RTP narrative, UDOT-hosted); amendment record =
  `rtp_amendment_process_2024`.
- **Air-quality conformity:** `rtp_aq_conformity_2023`, `rtp_aq_conformity_amendment1_2024`,
  `rtp_aq_emissions_amendment2_2024` (RTP); `tip_aq_conformity_2024_2028` (TIP).
- **Short-range obligated federal dollars:** `tip_annual_obligated_projects_2024`/`_2022`.
  (MAG's TIP narrative itself is a web app only — see SOURCES.md gaps. For structured
  project rows use `projects/`.)
- **Regional economic-development strategy:** `ceds_2024_2029`.
- **Wasatch Choice growth vision:** `wasatch_choice_vision_2019_2050` (shared WFRC/MAG).
- **How MAG adopts plans (process):** `transportation_policy_procedures_2023`;
  annual work program = `upwp_fy2025`.
- **Wasatch Back / RPO side:** `wasatch_county_transit_study` (the one captured RPO doc;
  the RPO plan proper is an ArcGIS app — gap).
- **Historic long-range plans (TransPlan-era archive):** `transplan40_2015`,
  `mtp_2040_2011`.

## doc_class vocabulary

`rtp | tip | conformity | ceds | vision | program_report | guidance | other`.
(Open set — extend if new types are added.)

## Scope note

Built records are the **Provo–Orem UZA MPO = Utah County only** (see the entity's
CLAUDE.md). The RTP/TIP/conformity/UPWP docs are the MPO's; `wasatch_county_transit_study`
is the one AOG/RPO (Wasatch Back) document. No doc carries a repo-city `jurisdiction` slug
— MAG's published plans are region-wide, not single-city. (The Lehi/Orem/Provo/Vineyard
station-area-plan work scopes are Google-Drive-hosted and could not be byte-verified — a
logged gap in SOURCES.md.)

## Cardinal rules (inherited from repo root)

- **Never fabricate.** Missing docs (MAG-hosted TIP narrative, Wasatch Back RPO plan PDF,
  HB462/SS4A program reports, RTP Amendment 3 final) are **honest gaps** in `SOURCES.md`,
  not invented rows. `index.csv` lists only byte-verified documents whose BODY matches the
  title.
- **Text is derived; PDFs/URLs are canonical.** Regenerate a `text/` file with
  `pdftotext raw/<stem>.pdf text/<stem>.txt`.
