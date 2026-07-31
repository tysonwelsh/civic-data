# Park City housing_plans — availability & gap record

**As-of:** 2026-07-05 · **Source 2 (moderate-income housing plans + annual reports + General Plan)** of `expand-city-sources`.

## What EXISTS and was retrieved (15 documents, ~71 MB in `raw/`)

### City of Park City (`parkcity.gov`)
**The city site is a Revize CMS** (`webspace=parkcityut`), *not* CivicPlus. Content pages are
`.php` (served 200); **documents live in a static file tree** at
`https://www.parkcity.gov/Documents/<section>/<File>.pdf`. The `showpublisheddocument/<id>/<ticks>`
and `showdocument?id=<id>` "deep links" (the routes the task and search engines surface) **404
sitewide** to every non-browser client we tried (IIS 404, verified below) — so the working method
was: fetch the `.php` content pages, read their **relative hrefs (rooted at `/Documents/`)**, and
GET the static files. The apex `parkcity.gov` 301-redirects to `www.parkcity.gov`.

**General Plan (adopted 2025-09-25, comprehensive update — supersedes the 2014 GP):**
- **Park City 2025 General Plan** (`.../Services/Planning/General Plan/ParkCityGeneralPlan2025.pdf`) — 37 pp.
- **2025 General Plan — Citizen's Summary** (10 pp).
- **2025 General Plan — Appendix** (55 pp).

**Moderate Income Housing element + its adopting/amending resolutions** (`.../Community/Affordable Housing/...`):
- **2022 Five-Year MIHP — Housing Element to the General Plan (original)** — adopted 2022-09-01 (Res 17-2022).
- **Amended 2022 Five-Year MIHP — Housing Element to the General Plan** — adopted 2023-01-24 (Res 02-2023). *Byte-distinct from the original.*
- **Resolution No. 17-2022** (signed) — adopts the 2022 MIHP (PASSED AND ADOPTED 2022-09-01).
- **Resolution No. 02-2023** (signed) — adopts the amendment (PASSED AND ADOPTED 2023-01-24).
- **2025 Update to the 2022 MIHP** — annual update per Utah Code 10-9a-403 (adopted by Housing Resolution 12-2025, 2025-06-12 per city announcement).
- **2020 Housing Assessment and Plan** — needs assessment underpinning the element (first page: adopted 2019-11-07, Res 22-2019).
- **2021 Addendum to the Housing Assessment and Plan**.
- **2020 Annual MIH Report to the State** (Park City's own copy) — **SCANNED**, OCR'd (labeled `format=scanned`, `extraction_method=ocr-tesseract`).

### State repository — Utah DWS / Housing & Community Development (HCD)
MIH reporting index: `https://jobs.utah.gov/housing/affordable/moderate/reporting/`. HCD publishes
**statewide compilation PDFs** (one per report year), not per-city files. Park City is present in each:

- **2023 reports** compilation — Park City = PDF pp. **~508–522** (1-up; printed-page offset 0; Orem ends p.506 by its FrontRunner marker; TOC lists Park City p.509, Payson p.522).
- **2024 reports** compilation — Park City = PDF pp. **~481–492** (**TWO-UP** layout, printed pp. 960/961–982; filer Rhoda Stauffer; next filer Payson printed p.983).
- **2025 reports** compilation — Park City = PDF pp. **611–624** (1-up; header at PDF idx 610; next filer Payson at idx 624).
- **SB 34 Municipal Progress Summaries 2019–2021** — Park City = jurisdiction **#51 "PARK CITY, CITY", PDF p.97** (`compliance_letter` proxy).

Park City pages were sidecar-extracted to `text/park-city-<year>-*.txt`; full compilations retained verbatim in `raw/`.

## MIH: standalone vs chapter — and the dedicated housing plan (a FINDING)

- **Park City's MIH element is BOTH a standalone plan AND a chapter.** The city maintains a
  **standalone "Five-Year Moderate Income Housing Plan" (MIHP)** that is *adopted as the Housing
  Element of the General Plan* (Utah Code 10-9a-403). The newly adopted **2025 General Plan also
  contains a "Moderate Income Housing" element/chapter** (p.30 — one of five themes, with a goal to
  house 15% of the city's workforce). So the standalone MIHP doubles as the GP's housing element and
  the element is *also* embedded in the 2025 GP.
- **Yes, there is a dedicated housing plan** beyond the GP element: the Five-Year MIHP (updated
  annually), backed by the **2020 Housing Assessment and Plan** + **2021 Addendum**. Park City runs a
  well-known deed-restricted affordable/workforce housing program; the MIHP is its planning instrument.

## What was NOT found / gaps (findings, not failures)

- **The 2014 Park City General Plan** (the prior adopted GP, of which the standalone MIHP is the
  Housing Element). **Not retrievable.** Its only published routes are the CivicPlus/Revize
  `showdocument?id=12051` / `showpublisheddocument/15425/…` deep links, which **404 to every client
  tried** (see audit trail). It is **superseded by the adopted 2025 GP** (retrieved), so the current
  adopted GP is captured; the 2014 predecessor is a documented gap.
- **Per-city standalone annual-report PDFs on the state site.** HCD publishes only the annual
  statewide compilations (`NNreports.pdf`) + the SB 34 summary — no `jobs.utah.gov` page hosts an
  individual "Park City 20NN MIH report.pdf". The compilation IS the filed report of record.
- **A separate HCD "compliance letter" to Park City.** HCD publishes none per city; the SB 34
  progress summary is recorded as the `compliance_letter` proxy.
- **Housing Resolution 12-2025 / 05-2021 as standalone signed PDFs.** Not separately published on the
  MIHP page; only Res 17-2022 and Res 02-2023 are posted as standalone signed resolutions. The 2025
  Update PDF carries the substance adopted by Res 12-2025.
- **Report years 2019–2022 as standalone state compilations.** The `.../reporting/` index today links
  only 23/24/25 `reports.pdf` + the 2019–2021 SB 34 summary; earlier individual-year compilations are
  not linked. The 2020 state-report-form (city copy) + SB 34 cover the earlier window.

## URL-access audit trail (how absence/routing was verified)

- **`showpublisheddocument/<id>/<ticks>` and `showdocument?id=<id>` 404 sitewide.** Verified against
  `72566`, `15425`, `73229` (showpublisheddocument) and `id=12051` (showdocument) via `polite_fetch`,
  raw `curl` (browser UA and Googlebot UA), and WebFetch — all IIS `404 - File or directory not found`
  (1245-byte page). Apex 301→`www`; `www` serves the 404.
- **Working static route confirmed:** `https://www.parkcity.gov/Documents/…` returns real PDFs (e.g.
  the 2012 Housing Assessment, and every doc retrieved here). Files are rooted at `/Documents/`; the
  hrefs on `.php` pages are relative to it.
- **Working content pages:** `/community/affordable_housing/index.php`,
  `/community/affordable_housing/moderate_income_housing_plan.php`, `/services/planning/index.php`,
  `/services/planning/general_plan_comprehensive_update.php` (all 200). The "pretty" department paths
  (`/departments/planning/general-plan`, `/planning/…`, `/affordable_housing/…`) **404**.
- **`parkcity.gov/sitemap.xml` → 404** (no sitemap). `engageparkcity.org/generalplan` hosts a GP
  viewer widget (HTML wrapper, not a direct PDF); the authoritative adopted PDFs are on the city
  static tree, which is what was retrieved.
- **CivicClerk API** (`parkcityut.api.civicclerk.com`) is the *meeting* portal (minutes/packets) — the
  housing plans do not live there.
- WebSearch: "Park City General Plan PDF adopted … moderate income housing element"; "Park City 2025
  General Plan PDF adopted"; "parkcity.gov Documents Planning General Plan 2014 Volume pdf".
