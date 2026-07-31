# housing_plans — St. George moderate-income housing + general plan

Additive dataset built by the `expand-city-sources` skill (Source 2). **St. George, UTAH**
(Washington County) — not Louisiana. As-of **2026-07-02**. Purely additive; no existing
dataset was modified.

## Statutory context

Utah Code **10-9a-403 / 10-9a-408** require every municipality to adopt a **moderate income
housing (MIH) element** in its general plan and to file an **annual implementation report**
with the Utah Dept. of Workforce Services, **Housing & Community Development (HCD)**. The
framework stems from **SB 34 (2019)** and was tightened by **HB 462 (2022)** and later
sessions (menu of required strategies, deadlines, funding-eligibility consequences).
St. George's compliance chain here: the **2022 MIH Plan** (the element) → annual state reports
(FY2023–FY2025) documenting progress on adopted strategies → the SB 34 progress summary.

## Contents (7 index rows)

**City site (`sgcityutah.gov`, Revize CMS):**
- `general_plan` — **St. George General Plan**, published as an interactive web plan (index +
  arts_and_culture, connection_to_nature, downtown, economic_vitality, lifestyle,
  responsible_growth, transportation). All 8 pages in `raw/general_plan_web/*.html`
  (format=html). No downloadable full-plan PDF exists. **Class-3 addendum (2026-07-16, primary-docs
  rollout):** each stored page was tag-stripped to a verbatim text sidecar `text/gp_<slug>.txt`
  (`extraction_method=html_strip`; html.parser, Revize nav chrome retained, source text incl.
  typos/curly quotes preserved, no LLM cleanup). The stored HTML was re-verified complete first (all 8
  = 200, proper `</html>` close, not truncated) so no re-fetch was needed. Substantive GP prose is
  present despite the nav chrome — goals, the Land Use Plan, and housing/density policy (e.g.
  `gp_responsible_growth.txt` §2.3 "Increase and Diversify Housing Supply").
- `general_plan` — **2040 Downtown Area Plan (DAP)**, `raw/Downtown_Area_Plan.pdf`
  (37 pp, born-digital, 63 MB — graphics-heavy). A sub-area element of the 2040 General Plan;
  the MIH strategies repeatedly reference amending Title 10 to implement it.
- `mih_element` — **2022 Moderate Income Housing Plan**,
  `raw/2025-GPA-005_Moderate_Income_Housing_Update.pdf` (29 pp, born-digital). This is the
  general-plan MIH element: terminology, demographics, housing-affordability analysis (HUD
  2022 Section 8 limits / HAMFI), zoning regulatory environment, fair housing, estimated MIH
  need, and the **STRATEGIES** section. File slug is `2025-GPA-005 … Clean`; document body
  self-identifies as "2022 MIH Plan".

**State HCD (`jobs.utah.gov/housing/affordable/moderate/reporting/`):**
- `mih_annual_report` ×3 — **statewide annual compilation PDFs** FY2023/24/25
  (`state_2023reports.pdf` … `state_2025reports.pdf`). St. George's own report is a page
  range inside each; extracted to `text/stgeorge-<year>.txt`.
- `mih_annual_report` ×1 — **SB 34 statewide progress summary** (`state_sb34_summary.pdf`,
  199 pp), St. George extract `text/stgeorge-sb34.txt`.

## Extraction & the compilation page-bracketing

PDFs born-digital throughout — `pdftotext -layout`; **no scanned/OCR files**. The GP web pages are
instead `html_strip` sidecars (`text/gp_*.txt`, added 2026-07-16). State compilations
list jurisdictions alphabetically; St. George's block was isolated by bracketing on the next
jurisdiction's header. Critical nuance: **"St. George" sorts before "Summit County" before
"Sunset"**, and a first naive bracket (St. George → Sunset) swept in Summit County /
Snyderville Basin content. Corrected ranges (verified 0 Summit/Snyderville tokens in the
sidecars):

| Report | PDF pages | Sidecar |
|---|---|---|
| FY2023 (`23reports.pdf`) | 820–833 | `text/stgeorge-2023.txt` |
| FY2024 (`24reports.pdf`) | 782–794 | `text/stgeorge-2024.txt` |
| FY2025 (`25reports.pdf`) | 953–971 | `text/stgeorge-2025.txt` (Summit-Snyderville starts p.972) |
| SB 34 (`sb34.pdf`) | 151–152 | `text/stgeorge-sb34.txt` |

Reproduce: `pdftotext -layout -f <first> -l <last> raw/<file> text/<sidecar>`. St. George is
confirmed present in all four (jurisdiction contact "Brenda Hatch, Planner II — CDBG & Housing";
FY2025 links its MIH element to `general_plan.php`).

## Provenance & QC

- Every raw byte retained in `raw/` (+ `raw/_fetch_log.jsonl`, `raw/general_plan_web/_fetch_log.jsonl`
  — url, status, bytes, sha256, retrieved_utc), fetched via `scripts/polite_fetch.py` with a
  frozen clock `--now 2026-07-02T00:00:00Z`.
- `screen_corpus.py` run on `text/` (now **14 sidecars** after the 8 GP web pages were added
  2026-07-16): no cid artifacts, replacement chars, mojibake, PUA, or dict-ratio outliers on the new
  files. The `ends_mid` (HTML/page-range excerpts) and `repeated_line`/`long_tokens` (PDF
  headers/footers; Google-Drive URLs in the pre-existing FY2025 state extract) flags are expected and
  benign.

## Linkage to the rest of the repo

MIH strategies and annual-report narratives cite specific council actions and
ordinances/resolutions (e.g. Switchpoint / Friends of Switchpoint projects, form-based-code
adoption, Downtown Area Plan implementation) — these join by date/subject to
`meeting_minutes/all_votes.csv` and to `ordinances/` if built. Not auto-linked here; the
annual reports are the *policy* layer behind land-use votes.

## Caveats (see AVAILABILITY.md for full gap log)

- General Plan is web-only (no PDF); adoption date not printed — dated 2022 (content vintage);
  an "updated General Plan" adoption was reported for 2025.
- Downtown Area Plan adoption date not printed — dated 2021 (approximate).
- MIH adoption resolution is a Google-Drive link (untrusted host) — not fetched.
- No standalone HCD compliance-determination letter published for St. George.
