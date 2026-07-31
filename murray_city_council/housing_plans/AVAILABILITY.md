# housing_plans — availability audit (Murray City)

**As of: 2026-07-13.** What was checked, what exists, what doesn't.

## What exists (all acquired)

| Item | Where | Status |
|---|---|---|
| General Plan (adopted 2017-03-07) | murray.utah.gov `/162/General-Plan` → DocumentCenter View/7570 | **Retained** (173 pp, born-digital) + Future Land Use Map (View/7571) |
| MIH element (General Plan Chapter 9, HB 462 rewrite) | `/979/Housing-Resources` → DocumentCenter View/13361 | **Retained** (16 pp, born-digital; the exact URL Murray filed with the state) |
| Adopting ordinance 22-29 (2022-09-20) | `/979/Housing-Resources` → DocumentCenter View/17009 | **Retained** (19 pp, **scanned** — tesseract OCR sidecar) |
| Annual 10-9a-408 implementation reports 2023 / 2024 / 2025 | Utah DWS HCD statewide compilations `{23,24,25}reports.pdf` | **Retained** (compilation PDFs + page-range sidecars). Murray **present all three years**: 2023 pp 430–440, 2024 pp 414–422, 2025 pp 522–533 (physical) |
| SB 34 progress summary 2019–2021 | Utah DWS HCD `sb34.pdf` | **Retained**; Murray pp 84–85 — 2019, 2020, 2021 all "REQUIRED & SUBMITTED" |

## Murray's presence per state reporting year

- **2019 / 2020 / 2021** — submitted (per the SB 34 statewide progress summary; the
  underlying filings themselves are not republished by HCD).
- **2023, 2024, 2025** — present in each statewide compilation (verified by locating the
  Murray section and bracketing it by the neighboring cities' headers: Millcreek before,
  Nibley after in all three). Filed by Zachary Smallwood, Planning Division Manager
  (named in the 2024/2025 forms).
- **2022** — HCD publishes **no `22reports.pdf`**; the compilation series starts with 2023
  (HB 462 took effect with the Oct 2022 plan-amendment deadline; the first annual
  implementation reports under the new regime were the 2023 filings). Absence of a 2022
  compilation is a state-publication fact, not a Murray gap. Checked the HCD reporting
  index (`jobs.utah.gov/housing/affordable/moderate/reporting/`) via the sibling-city
  acquisitions (bluffdale/lehi/logan/millcreek, 2026-07-02..12), which enumerated
  `23reports.pdf`, `24reports.pdf`, `25reports.pdf`, `sb34.pdf` as the complete set.

## What the city does NOT post (honest findings)

1. **No standalone city-posted annual MIH report.** The Housing Resources page
   (`/979/Housing-Resources`) *says* "Murray City must post the report that is provided
   to the State here. Below you will find Murray City's Annual Report" — but the only
   documents actually linked there are the Chapter 9 MIH element (View/13361) and
   Ordinance 22-29 (View/17009). No annual-report PDF is linked (checked the full page
   HTML, 2026-07-13). The state compilations are therefore the only public copies of
   Murray's annual reports. Absence of standalone per-city reports on the HCD side is
   expected (HCD publishes compilations only) — not a gap.
2. **No HCD compliance letter posted.** Some cities post their DWS/HCD "notice of
   compliance" letter (e.g. Bluffdale); Murray does not — neither the Housing Resources
   page nor a site search (`Search/Results?searchPhrase=moderate income housing`)
   surfaces one. `doc_type=compliance_letter` is therefore honestly absent.
3. **No newer General Plan.** The 2017 General Plan is current (the `/162/General-Plan`
   page links only the 2017 plan + Future Land Use Map). Small-area plans (Murray
   Central Station, Fashion Place West, Murray North Station, Tower Plaza) exist as
   separate documents and are out of this dataset's scope.

## What was checked

- `https://www.murray.utah.gov/sitemap.xml` (282 URLs — thin; no direct General Plan/
  housing URLs) → navigated the CMS instead: Departments → Community & Economic
  Development (`/158/`) → General Plan (`/162/`) + Housing Resources (`/979/`) +
  Planning and Zoning Division (`/2170/`). All fetches with a browser UA; no 403s.
- City site search for "moderate income housing" (2 hits: Housing Resources page +
  the View/17009 ordinance — nothing else exists on the CMS).
- Utah DWS HCD compilations: locally reused (sha256-verified) from the sibling-city
  acquisitions; Murray's page ranges located per year by bracketing with the
  alphabetically-adjacent cities' headers (Millcreek / Nibley).
