#!/usr/bin/env python3
"""Emit housing_plans/index.csv for Holladay (SCHEMA_SPEC §9 housing contract header).

Reproducible generator for the Holladay moderate-income-housing dataset index. Kept
in-dataset with a unique name per build rules. Columns are the exact §9 order:
date,title,doc_type,source_url,retrieved_date,format,extraction_method,path,pages,
repository,notes
"""
import csv

HOLLADAY = "Holladay (holladayut.gov / cms3.revize.com Document Center)"
PMN = lambda fid: f"Utah Public Notice (utah.gov/pmn file {fid})"
HCD = "Utah DWS HCD (jobs.utah.gov)"
RD = "2026-07-13"

rows = [
    # --- City General Plan (Holladay Horizons 2025) + prior plan ---
    dict(date="2025-11",
         title="Holladay General Plan 2025 (\"Holladay Horizons\") — ADOPTED",
         doc_type="general_plan",
         source_url="https://holladayut.gov/Document%20Center/GP%2024/Holladay%20General%20Plan%202025_APPROVED.pdf",
         format="text", extraction_method="pdftotext -layout",
         path="raw/holladay-general-plan-2025.pdf", pages="120", repository=HOLLADAY,
         notes="Current adopted General Plan (\"Holladay Horizons\"). Adopted November 2025 per Holladay Journal (2026-02-02); final APPROVED PDF re-posted Feb 2026 (cache-buster t=202602271544170). Acknowledgments list the 2025 pre-Jan-2026 council (Mayor Dahle). The current Moderate-Income Housing element is Appendix F (see the Appendices row). Exact adoption day not printed in the plan text."),
    dict(date="2025-11",
         title="Holladay General Plan 2025 Appendices (incl. Appendix F: Moderate-Income Housing Plan)",
         doc_type="general_plan",
         source_url="https://holladayut.gov/Document%20Center/GP%2024/Holladay%20General%20Plan%202025%20Appendices_APPROVED.pdf",
         format="text", extraction_method="pdftotext -layout",
         path="raw/holladay-general-plan-2025-appendices.pdf", pages="73", repository=HOLLADAY,
         notes="Appendices A-F to the 2025 General Plan. Appendix F IS the current Moderate-Income Housing element (Utah Code 10-9a-403); Appendix F is the final/latter section of this bundle. Also contains A: Required GP Element Matrix, B: Glossary, C: Engagement Summary, D: Implementation Summary Table, E: Small Area Plans."),
    dict(date="2016-07-14",
         title="City of Holladay General Plan 2016-2031 (prior plan)",
         doc_type="general_plan",
         source_url="https://www.utah.gov/pmn/files/1329487.pdf",
         format="text", extraction_method="pdftotext -layout",
         path="raw/holladay-general-plan-2016-2031.pdf", pages="90", repository=PMN(1329487),
         notes="Prior General Plan adopted July 14 2016; superseded by the 2025 plan. Land-use/MIH context for the RY2023 state filing. PDF internal title 'General Plan_currentFeb2023' (the Feb-2023 refresh of the 2016 plan). The city's own page linked General-Plan_currentFeb2023.pdf which now 404s on the migrated CMS; PMN copy used instead."),

    # --- MIH element(s) ---
    dict(date="2019",
         title="Chapter 5: Moderate Income Housing — 2019 Update Summary (prior-plan MIH element)",
         doc_type="mih_element",
         source_url="https://www.utah.gov/pmn/files/532759.pdf",
         format="text", extraction_method="pdftotext -layout",
         path="raw/holladay-mih-2019-update.pdf", pages="18", repository=PMN(532759),
         notes="MIH element / SB 34 update to the 2016 General Plan. References the 2010 MIH Plan (reviewed 2013 & 2016) and an Oct-2017 MIH Review Report accepted by the State. Historical - superseded by the Chapter 5 plan (amended through 2024) and by 2025 GP Appendix F."),
    dict(date="2024-03",
         title="Chapter 5: Moderate Income Housing Plan (amended through March 2024) — current standalone MIH element",
         doc_type="mih_element",
         source_url="https://holladayut.gov/Document%20Center/Departments/Economic%20Development%20and%20Housing/Housing%20resources/Chapter%205%20Moderate%20Income%20Housing%20Plan.pdf",
         format="text", extraction_method="pdftotext -layout",
         path="raw/holladay-chapter5-mih-plan.pdf", pages="14", repository=HOLLADAY,
         notes="City-posted standalone MIH element on the Moderate Income Housing page. Header states *Amended September 2022, *Amended February 2023, *Amended March 2024. This is the operative MIH Plan the city links; its latest amendment was adopted by Resolution 2025-02 (2025-03-20, see next row)."),
    dict(date="2025-03-20",
         title="Resolution No. 2025-02 — Amending the Moderate Income Housing Plan (Exhibit A = Amended MIH Plan)",
         doc_type="mih_element",
         source_url="https://holladayut.gov/Document%20Center/Departments/Economic%20Development%20and%20Housing/Housing%20resources/2025-02%20-Resolution%20MIHP%202025.pdf",
         format="scanned", extraction_method="ocr (tesseract 5.5.0, 200dpi)",
         path="raw/holladay-resolution-2025-02-mihp.pdf", pages="14", repository=HOLLADAY,
         notes="Signed resolution PASSED AND APPROVED 20 March 2025 amending the MIH Plan (minor numerical amendments per HB 462); Exhibit A is the amended MIH Plan itself. Image-only scan (no text layer) -> OCR sidecar; expect OCR artifacts. Surfaces the adopting instrument the city's plan-page did not otherwise name."),

    # --- Annual reports: city-filed + state compilations ---
    dict(date="2024-08-01",
         title="2024 Moderate Income Housing Report — city-filed copy (submitted Aug 1 2024)",
         doc_type="mih_annual_report",
         source_url="https://holladayut.gov/Document%20Center/Departments/Economic%20Development%20and%20Housing/Housing%20resources/080124_2024%20MIH%20Annual%20Report_Submitted.pdf",
         format="text", extraction_method="pdftotext -layout",
         path="raw/holladay-2024-mih-annual-report-city.pdf", pages="23", repository=HOLLADAY,
         notes="City-published copy of Holladay's 10-9a-408 annual implementation report (reporting year Aug 1 2023-Jul 31 2024; submitted 2024-08-01; preparer Ann Frances Garcia). The state-published copy is the hcd-24reports.pdf excerpt (pp 230-250). Both retained (city vs state publication of one report)."),
    dict(date="2023",
         title="Holladay annual MIH report — 2023 statewide compilation (excerpt)",
         doc_type="mih_annual_report",
         source_url="https://jobs.utah.gov/housing/affordable/moderate/reporting/documents/23reports.pdf",
         format="text", extraction_method="pdftotext -layout",
         path="raw/hcd-23reports.pdf", pages="256-263", repository=HCD,
         notes="Holladay's 10-9a-408 annual report within the statewide 23reports.pdf (1109 pp). Holladay = physical pp 256-263 (printed 255-262; Hooper starts p264 => 2023 offset printed=physical-1). Sidecar text/holladay-2023.txt (bleed-verified, 0 neighbor-city headers). 'Link to Plan' fields cite General-Plan_currentFeb2023.pdf + Moderate-Income-Housing-Feb-2023.pdf (both now 404 on the migrated cityofholladay.com CMS). Copied sha256-verified from bluffdale raw/; original fetch 2026-07-13."),
    dict(date="2024",
         title="Holladay annual MIH report — 2024 statewide compilation (excerpt)",
         doc_type="mih_annual_report",
         source_url="https://jobs.utah.gov/housing/affordable/moderate/reporting/documents/24reports.pdf",
         format="text", extraction_method="pdftotext -layout",
         path="raw/hcd-24reports.pdf", pages="230-250", repository=HCD,
         notes="Holladay's 10-9a-408 annual report within the statewide 24reports.pdf (1030 pp). Holladay = physical pp 230-250 (Hooper header starts p251). NOTE: the 2024 TOC printed page numbers are ~2x physical (Holladay printed 458 -> physical 230), so the range was CONTENT-SCANNED, not TOC-derived. Sidecar text/holladay-2024.txt (bleed-verified). State copy of the city-filed 080124 report. Copied sha256-verified from bluffdale raw/; original fetch 2026-07-13."),
    dict(date="2025",
         title="Holladay annual MIH report — 2025 statewide compilation (excerpt)",
         doc_type="mih_annual_report",
         source_url="https://jobs.utah.gov/housing/affordable/moderate/reporting/documents/25reports.pdf",
         format="text", extraction_method="pdftotext -layout",
         path="raw/hcd-25reports.pdf", pages="312-326", repository=HCD,
         notes="Holladay's 10-9a-408 annual report within the statewide 25reports.pdf (1303 pp). Holladay = physical pp 312-326 (printed 309; Hooper starts p327 => 2025 offset ~+3). Sidecar text/holladay-2025.txt (bleed-verified). Preparer contact annfgarcia@holladayUT.gov; links holladayut.gov housing pages + city ArcGIS hub. Copied sha256-verified from bluffdale raw/; original fetch 2026-07-13."),
    dict(date="2021",
         title="Holladay SB 34 Municipal Progress Summary 2019-2021 (excerpt)",
         doc_type="mih_annual_report",
         source_url="https://jobs.utah.gov/housing/affordable/moderate/reporting/documents/sb34.pdf",
         format="text", extraction_method="pdftotext -layout",
         path="raw/hcd-sb34.pdf", pages="57", repository=HCD,
         notes="Holladay's SB 34 progress summary within the statewide sb34.pdf (199 pp; covers 2019-2021). Holladay = summary #26, County: Salt Lake, 3 required items, single physical page 57 (Hooper starts p58). Sidecar text/holladay-sb34-2019-2021.txt (bleed-verified). Copied sha256-verified from bluffdale raw/; original fetch 2026-07-13."),
]

HEADER = ["date", "title", "doc_type", "source_url", "retrieved_date", "format",
          "extraction_method", "path", "pages", "repository", "notes"]

with open("index.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=HEADER, quoting=csv.QUOTE_MINIMAL)
    w.writeheader()
    for r in rows:
        r["retrieved_date"] = RD
        w.writerow(r)

print(f"wrote index.csv: {len(rows)} rows")
