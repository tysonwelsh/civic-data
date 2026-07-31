# housing_plans — availability audit (Herriman City)

**As of: 2026-07-13.** What was checked, what exists, what doesn't.

## What exists (all acquired)

| Item | Where | Status |
|---|---|---|
| General Plan 2022 "Herriman Next" (adopted 2022-07-13) | herriman.gov `/general-plan` → `/uploads/files/3520/` | **Retained** (152 pp, born-digital) + 2030 Land Use Map (`/uploads/files/3174/`, 1 map sheet) |
| Predecessor "Herriman 2025" General Plan (rev. 2013-10-07) | herriman.gov `/general-plan` → `/uploads/files/1621/2025GPAmend.pdf` | **Retained** (98 pp, born-digital; "2025" = horizon year, not a date) |
| MIH Plan 2019 (adopted 2019-11-13) | **Wayback only** — orig. `herriman.org/uploads/files/1239/…` (live URL 404s) | **Recovered** from the 2021-08-10 capture (14 pp, born-digital) |
| MIH Plan 2022 update + Ordinance 2022-38 (adopted 2022-09-28) | herriman.gov `/master-plans` → `/uploads/files/5826/` | **Retained** (23 pp, **scanned** with OCR text layer). The state-filed `/uploads/files/3067/` URL still serves the same doc |
| Annual 10-9a-408 report, reporting year 2020 | **Wayback only** — orig. `herriman.org/uploads/files/1242/…` (live URL 404s) | **Recovered** from the 2021-08-10 capture (24 pp, DWS-HCD 899 form) |
| Annual 10-9a-408 report, reporting year 2021 | herriman.gov `/master-plans` → `/uploads/files/2462/` | **Retained** (25 pp; the only annual report the city still links) |
| Annual 10-9a-408 reports 2023 / 2024 / 2025 | Utah DWS HCD statewide compilations `{23,24,25}reports.pdf` | **Retained** (compilation PDFs + page-range sidecars). Herriman **present all three years**: 2023 pp 231–249, 2024 pp 209–223, 2025 pp 286–302 (physical) |
| SB 34 progress summary 2019–2021 | Utah DWS HCD `sb34.pdf` | **Retained**; Herriman pp 53–54 — 2019, 2020, 2021 all "REQUIRED & SUBMITTED" |

## Herriman's presence per state reporting year

- **2019 / 2020 / 2021** — submitted (SB 34 statewide progress summary, pp 53–54:
  3 required items, 6 total menu items, County Salt Lake, AOG/MPO WFRC). The city's own
  filed copies for 2020 and 2021 were also recovered/retained (see above); 2019's filing
  is summarized inside sb34.pdf only — HCD does not republish the underlying 2019 form,
  and no city-posted 2019 report copy was found live or in Wayback (the SB 34 summary is
  its public record).
- **2023, 2024, 2025** — present in each statewide compilation (verified by locating the
  Herriman section and bracketing by the alphabetically-adjacent cities' headers: Heber
  City before, Highland after in all three). 2024/2025 filed by Susan Petheram, Senior
  Planner (FFKR Architects, the city's planning consultant); 6 strategies (A, B, E, F,
  G, K) consistent across years.
- **2022** — HCD publishes **no `22reports.pdf`**; the compilation series starts with 2023
  (HB 462 took effect with the Oct 2022 plan-amendment deadline; Herriman adopted its
  updated plan 2022-09-28 by Ordinance 2022-38, three days before that deadline). Absence
  of a 2022 compilation is a state-publication fact, not a Herriman gap. Checked the HCD
  reporting index (`jobs.utah.gov/housing/affordable/moderate/reporting/`) via the
  sibling-city acquisitions (bluffdale 2026-07-12, murray 2026-07-13), which enumerated
  `23reports.pdf`, `24reports.pdf`, `25reports.pdf`, `sb34.pdf` as the complete set.

## What the city does NOT post (honest findings)

1. **No HCD compliance letter.** Some cities post their DWS/HCD "notice of compliance"
   letter (e.g. Bluffdale); Herriman does not — not on `/general-plan`, `/master-plans`,
   `/planning`, `/city-growth`, `/development-info`, `/transparency`, `/multi-family`, or
   `/iadu` (all fetched and grepped 2026-07-13). `doc_type=compliance_letter` is
   honestly absent.
2. **Old MIH documents are silently dropped on CMS migration.** The 2019 MIH Plan and the
   2020 annual report 404 on the live site (herriman.org → herriman.gov migration); both
   were recovered from the Internet Archive. The live `/master-plans` page links only the
   2022 plan and the 2021 report.
3. **No standalone city copies of the 2023+ annual reports.** After 2021 the city stopped
   posting its filed report (the 2024-form question "Post the report on their
   municipality's website" notwithstanding); the state compilations are the only public
   copies of Herriman's 2023/2024/2025 reports.
4. **Pre-2019 MIH element:** a 2010-era `planning/docs/Moderate_Income.pdf` exists in
   Wayback (captures 2010-12-15 and 2013-02-14 under herriman.org) — the pre-2019 MIH
   element. **Located but deliberately not retained**: a decade below the repo's 2020
   data floor and superseded twice; the Wayback URLs are recorded here if ever wanted.

## What was checked

- `https://www.herriman.gov/sitemap.xml` → `sitemap-pages.xml` (238 page URLs; browser
  UA). Relevant pages: `/general-plan`, `/master-plans`, `/planning`,
  `/planning-commission`, `/identical-plan-reviews`. No housing-specific page exists.
- `/general-plan` and `/master-plans` HTML link inventories (the two pages that carry
  every plan PDF); `/planning`, `/city-growth`, `/development-info`, `/transparency`,
  `/multi-family`, `/iadu` grepped for "moderate"/"housing" — zero MIH mentions.
- Wayback CDX (`web.archive.org/cdx/search/cdx?url=herriman.org&matchType=domain`,
  filtered `moderate|housing` PDFs) — surfaced the 2019 plan + 2020 report (recovered)
  and the 2010 legacy element (recorded, not retained).
- Utah DWS HCD compilations: locally reused (sha256-verified) from the bluffdale
  acquisition; Herriman's page ranges located per year by bracketing with the
  alphabetically-adjacent cities' headers (Heber City / Highland).
