# housing_plans — Lehi General Plan + Moderate Income Housing (MIH) plan & annual reports

Source 2 of the `expand-city-sources` skill. **Additive dataset** — nothing here modifies the
existing `meeting_minutes/`, `planning_commission/`, `db/`, etc. **As-of 2026-07-02.**

## What this is

Lehi's land-use / housing planning record, from two repositories:
1. **City of Lehi** — the current adopted **General Plan** and the **Moderate Income Housing (MIH)
   Element** of that General Plan, plus the ordinance adopting the 2024 MIH update.
2. **Utah DWS / Housing & Community Development (HCD)** — the **annual MIH implementation reports**
   Lehi files with the state, as published in HCD's statewide compilations, plus the SB 34 progress
   summary.

## Statutory context (why these documents exist)

- **Utah Code § 10-9a-403** — every municipality's general plan must include a **moderate income
  housing (MIH) element/plan**: a written plan with **strategies** (chosen from a statutory menu) to
  provide a "reasonable opportunity" for households at **≤ 80% of county area median income** to live
  in the city.
- **Utah Code § 10-9a-408** — requires each municipality to file an **annual MIH implementation
  report** with HCD documenting progress on its chosen strategies. HCD reviews the self-reported data.
- **HB 462 (2022)** (and later amendments) strengthened these: expanded/required strategy menus,
  tied transportation funding eligibility to compliance, and — for cities with a fixed-guideway
  transit station like Lehi's FrontRunner/Thanksgiving Point area — required **Station Area Plans**.
  Lehi's MIH element was **updated 2024-05-28** to comply (goals, strategies, timeline).

## Documents (see `index.csv` for the machine-readable list)

`doc_type` ∈ `general_plan` / `mih_element` / `mih_annual_report` / `compliance_letter`.

- **general_plan** — GP Final Document 2022 (136 pp, the current adopted plan), GP Land Use Map
  (adopted 2011, amended 2022), GP Max Density Map (graphic).
- **mih_element** — Moderate Income Housing Element (adopted 2017, **updated 2024-05-28**) + its
  signed adopting ordinance (scanned).
- **mih_annual_report** — HCD statewide compilations for report years **2023, 2024, 2025**; Lehi's
  filing is a page-range within each (see `notes`/page ranges in `index.csv`).
- **compliance_letter** — HCD **SB 34 Municipal Progress Summaries 2019–2021** (Lehi = #35). HCD does
  not issue per-city compliance letters; this progress summary is the closest published compliance
  artifact.

## Build method / provenance

- Every raw PDF fetched through `.claude/skills/expand-city-sources/scripts/polite_fetch.py`
  (browser UA, Referer, ≥1s/host, logged) into `raw/`. Byte-level provenance: `raw/_fetch_log.jsonl`
  (url, http status, bytes, sha256, content_type, final_url, retrieved_utc).
- City docs discovered from the **current** General Plan page
  `https://www.lehi-ut.gov/departments/planning-zoning/general-plan/` (the site migrated off
  WordPress; old `wp-content/uploads/...` URLs 404 — do not use them). State docs from
  `https://jobs.utah.gov/housing/affordable/moderate/reporting/`.

## Extraction

- Born-digital PDFs → `pdftotext -layout` sidecars in `text/` (`extraction_method=pdftotext-layout`).
  Sidecars: GP Final Document, GP Land Use Map, MIH Element, and the **Lehi-only page ranges** cut
  from each state compilation (`text/lehi-<year>-mih-annual-report.txt`).
- **Scanned/graphic** files (`format=scanned`, `extraction_method=none`): the adopting ordinance
  (signed image, no font/text layer) and the Max Density Map (graphic). Not OCR'd — dates are
  otherwise confirmed; OCR left as future work if their body text is ever needed.
- `screen_corpus.py` run on `text/` → clean: 0 cid-artifacts / replacement-chars / mojibake /
  garbled; only advisory flags (repeated header/footer lines and tables in gov docs, hyphen breaks).

## Linkage to the rest of the repo

- The **2024-05-28 MIH element adoption** corresponds to a Council action — joinable to
  `meeting_minutes/all_votes.csv` by that date. The engage-Lehi record shows the MIH goals update went
  to Planning Commission **2024-05-09** (joinable to `planning_commission/`) before Council adoption.
- MIH strategies reference the **Thanksgiving Point / FrontRunner Station Area Plan** and North Lehi /
  Hospital / 2100 North station areas — the same CRA/HTRZ projects noted in `recon.md` §3.

## Caveats

- The state "annual report" of record is a **statewide compilation**, not a standalone Lehi PDF; the
  whole compilation is retained and Lehi's pages are sidecar-extracted. Cite the page range.
- MIH self-reported data is reviewed but not audited by HCD — treat report figures as the city's
  self-report.
- Pre-2023 individual annual compilations and General Plan pre-adoption drafts were **not** retrieved
  (superseded / not on the current index) — see `AVAILABILITY.md`.
