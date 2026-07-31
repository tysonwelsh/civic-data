# housing_plans — availability & gap log

**As-of:** 2026-07-02 · **City:** St. George, **Utah** (Washington County, UGRC ID 27) —
NOT St. George, Louisiana. Only `sgcityutah.gov` and `jobs.utah.gov` (Utah DWS / Housing &
Community Development) were trusted as sources.

## What was retrieved

| Item | doc_type | Source | Result |
|---|---|---|---|
| St. George General Plan (interactive web plan) | general_plan | city site | Retrieved as HTML (index + 7 chapters) |
| 2040 Downtown Area Plan (DAP) | general_plan | city site | Retrieved (37-pp born-digital PDF) |
| 2022 Moderate Income Housing Plan / MIH element | mih_element | city site | Retrieved (29-pp born-digital PDF) |
| MIH annual implementation reports FY2023/24/25 | mih_annual_report | state HCD | Retrieved (statewide compilation PDFs; St. George extracted) |
| SB 34 statewide MIH progress summary | mih_annual_report | state HCD | Retrieved (St. George extract) |

## Discovery method (city site)

- Crawled `https://sgcityutah.gov/sitemap.xml` (933 URLs, Revize CMS). Located
  `departments/community_development/general_plan.php`, which hosts a Revize "document
  center" listing the **Moderate Income Housing Plan** and the **Downtown Area Plan**, and
  links to the interactive **St. George General Plan** at
  `departments/community_development/st._george_general_plan/index.php`.
- **Revize relative-path gotcha:** doc-center links render as `Documents/<file>.pdf` relative
  to the page, but that path 404s. The files actually live at the CMS document root
  `https://cms3.revize.com/revize/stgeorge/Documents/<file>.pdf` (equivalently
  `https://sgcityutah.gov/Documents/<file>.pdf`, which is what we fetched — 200 OK).

## Discovery method (state)

- Index `https://jobs.utah.gov/housing/affordable/moderate/reporting/` links four PDFs we
  pulled: `23reports.pdf`, `24reports.pdf`, `25reports.pdf` (annual statewide compilations)
  and `sb34.pdf` (SB 34 progress summary). Reports are **statewide compilations, not
  per-city files** — expected; absence of a standalone St. George report is not a gap.
- St. George's page range in each compilation was bracketed by the neighbouring city header
  (St. sorts before **Summit County** before **Sunset**). Ranges confirmed and de-contaminated
  (0 Summit/Snyderville bleed): FY2023 pp.820–833, FY2024 pp.782–794, FY2025 pp.953–971,
  SB 34 pp.151–152. Sidecars in `text/stgeorge-<year>.txt`. St. George is **present in all
  four** (jurisdiction contact "Brenda Hatch, Planner II — CDBG & Housing").

## Gaps / not published / not fetched

- **No single adopted General Plan PDF.** St. George publishes its current General Plan as an
  **interactive multi-page web plan** (7 chapters), not a downloadable document. We captured
  all 8 pages as HTML in `raw/general_plan_web/`. The pages are Revize-templated (heavy nav
  chrome); the land-use/housing detail is deepest in the MIH element and the Downtown Area Plan PDFs,
  but the web chapters DO carry substantive policy prose (goals, the Land Use Plan, housing/density
  strategy). **Class-3 addendum (2026-07-16, primary-documents rollout):** the stored HTML had no text
  sidecars; each of the 8 pages was tag-stripped to `text/gp_<slug>.txt` (verbatim, no cleanup) so the
  GP text is now in the corpus. The stored HTML was re-verified complete before stripping (no
  re-fetch needed).
- **General Plan adoption date is not printed on the web pages.** Public engagement ran 2021,
  a draft circulated summer 2022. Separately, the City's **FY2025** MIH report lists "Adopt the
  updated General Plan (Jan–Apr 2025)" as an implementation task, indicating a General Plan
  update was being adopted in 2025. We date the captured web plan **2022** (its confirmed
  content vintage) and flag that an updated General Plan adoption was reported for 2025; the
  web version is the current published plan as of retrieval.
- **Downtown Area Plan adoption date not printed** in the document; dated **2021** from its
  content (most recent internal year besides the "2040" horizon). Server upload timestamp was
  Aug 2025. Treated as approximate.
- **MIH element adoption resolution** — the FY2025 state report links the adoption
  resolution as a **Google Drive** file
  (`drive.google.com/file/d/1tEiDrXaiui4eYIMdH78uDsiFZ0YSiNwX`). Not fetched: Google Drive is
  outside the trusted city/state hosts and is not a polite public-records GET target. The MIH
  document itself self-identifies as the **"2022 MIH Plan"** and is dated 2022 accordingly.
- **No standalone HCD compliance-determination letter** for St. George was found on the state
  reporting index (only compilations + the SB 34 summary). No `compliance_letter` row recorded.
- **modeltemplate.pdf / mihfaq.pdf / affordhouseprofile.pdf** on the state index are generic
  statewide instructional/template docs (not St. George-specific) and were not retained.
