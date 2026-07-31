# housing_plans — Logan General Plan + Moderate Income Housing (MIH) plan & annual reports

Source 2 of the `expand-city-sources` skill. **Additive dataset** — nothing here modifies the
existing `meeting_minutes/`, `planning_commission/`, `db/`, etc. **As-of 2026-07-05.**

## What this is

Logan's (Cache County, Utah) land-use / housing planning record, from two repositories:
1. **City of Logan — Community Development** — the current adopted **Logan 2045 General Plan** (2026),
   the standalone **Moderate Income Housing Plan (2022, Resolution 22-46)**, and the City's own **2018
   biennial MIH report**.
2. **Utah DWS / Housing & Community Development (HCD)** — the **annual MIH implementation reports**
   Logan files with the state, as published in HCD's statewide compilations (2023/2024/2025), plus the
   SB 34 progress summary.

## Statutory context (why these documents exist)

- **Utah Code § 10-9a-403** — every municipality's general plan must include a **moderate income
  housing (MIH) element/plan**: a written plan with **strategies** (statutory menu) giving households at
  **≤ 80% of county area median income** a "reasonable opportunity" to live in the city.
- **Utah Code § 10-9a-408** — requires each municipality to file an **annual MIH implementation report**
  with HCD; HCD reviews the self-reported data.
- **HB 462 (2022)** strengthened these (expanded strategy menu, tied transportation funding to
  compliance). Logan's 2022 MIHP (Resolution 22-46) explicitly revises its plan to the HB 462 version of
  10-9a-403.

## Documents (see `index.csv` for the machine-readable list)

`doc_type` ∈ `general_plan` / `mih_element` / `mih_annual_report` / `compliance_letter`.

- **general_plan** — Logan 2045 General Plan (2026, 155 pp, current adopted). **Contains** the MIH element
  as a section of its "Housing and Neighborhoods" chapter (p.45).
- **mih_element** — Moderate Income Housing Plan (2022, 123 pp, Resolution 22-46) — the **standalone**
  adopted MIH element.
- **mih_annual_report** — the City's 2018 biennial MIH report **plus** HCD statewide compilations for
  report years **2023, 2024, 2025** (Logan's filing is a page-range within each — see `notes` in `index.csv`).
- **compliance_letter** — HCD **SB 34 Municipal Progress Summary** for LOGAN CITY (2019–2021 window).
  HCD issues no per-city compliance letter; this is the closest published compliance artifact.

## Standalone vs General-Plan chapter

**Both.** Logan has a standalone 2022 MIHP (Resolution 22-46) AND an MIH element embedded in the 2026
Logan 2045 General Plan (which references the 2022 MIHP). Per 10-9a-403 the MIH plan is an *element of
the general plan*; Logan satisfies this in both a standalone document and the GP chapter.

## Build method / provenance

- Every raw PDF fetched through `.claude/skills/expand-city-sources/scripts/polite_fetch.py`
  (browser UA, Referer, ≥1s/host, logged) into `raw/`. Byte-level provenance: `raw/_fetch_log.jsonl`
  (url, http status, bytes, sha256, content_type, final_url, retrieved_utc).
- **`loganutah.gov/sitemap.xml` is 404** — city docs were discovered from the live Community-Development
  Projects & Plans page `https://www.loganutah.gov/government/departments/community_development/projects_and_plans.php`
  (docs live on the Revize CDN `cms9files.revize.com/loganut/departments/comdev/...`). State docs from
  `https://jobs.utah.gov/housing/affordable/moderate/reporting/`.

## Extraction

- All seven PDFs are **born-digital** → `pdftotext -layout` sidecars in `text/`
  (`extraction_method=pdftotext-layout`). No OCR needed; no scanned/graphic files in this dataset.
- Sidecars: the three city docs (GP, MIHP, 2018 biennial) full-text; and the **Logan-only page ranges**
  cut from each state compilation (`text/logan-<year>-mih-annual-report.txt`, `text/logan-sb34-progress-summary.txt`).
- Corpus screen: 0 `(cid:` artifacts, 0 replacement chars, no mojibake across all sidecars.

## Linkage to the rest of the repo

- **MIHP 2022 adoption = Resolution No. 22-46, 2022-11-15** — joinable to `meeting_minutes/all_votes.csv`
  by that date (Council roll-call). The 2022 MIHP names the adopting council (Amy Z. Anderson, Mark A.
  Anderson, Ernesto Lopez, Jeannie F. Simmonds, Tom Jensen) — note the **two distinct Andersons** flagged
  in the parent `CLAUDE.md`.
- The 2023 HCD report cites a **Logan Municipal Council** action of **3/7/23** (expanding an allowance) —
  joinable to `meeting_minutes/`.

## Caveats

- The state "annual report" of record is a **statewide compilation**, not a standalone Logan PDF; the whole
  compilation is retained and Logan's pages are sidecar-extracted. **Cite the page range** (see `index.csv`
  / `AVAILABILITY.md`) — and beware alphabetization bleed and the separate **North Logan city**.
- MIH self-reported data is reviewed but not audited by HCD — treat report figures as the city's self-report.
- The **prior General Plan (LoganGenPlan v20)** and pre-2023 state compilations were **not** retrieved
  (superseded / not on the current index) — see `AVAILABILITY.md` for live URLs if ever needed.
