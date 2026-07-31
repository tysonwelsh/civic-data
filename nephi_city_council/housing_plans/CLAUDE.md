# housing_plans — Nephi City General Plan + Moderate Income Housing (MIH) element

Source 2 of the `expand-city-sources` skill. **Additive dataset** — nothing here modifies the
existing `meeting_minutes/`, `election_results/`, `weeks/`, etc. **As-of 2026-07-05.**

## What this is (and the two headline facts)

Nephi's land-use / housing planning record. Nephi is a **small rural city (~6,500) in Juab County**,
and this dataset is deliberately **thin** — that thinness is itself the finding:

1. **MIH is a CHAPTER, not a standalone document.** Nephi's moderate-income housing element is
   **Element 6: Housing** inside the **2023 General Plan** (PDF pp. 56-65) — there is no separate MIH
   plan, element, or report PDF.
2. **Nephi is EXEMPT from the state MIH annual-report regime and is absent from every state
   compilation** (2023/2024/2025 + SB 34) — verified by full-text search, not assumed. See
   `AVAILABILITY.md`.

## Documents (see `index.csv` for the machine-readable list)

`doc_type` ∈ `general_plan` / `mih_element` / `mih_annual_report` / `compliance_letter`.

- **general_plan** — **Nephi City General Plan 2023** (`raw/nephi-general-plan-2023.pdf`, 89 pp.,
  born-digital). Full sidecar `text/nephi-general-plan-2023.txt`.
- **mih_element** — **the SAME PDF, Element 6: Housing** (pp. 56-65). Focused sidecar
  `text/nephi-general-plan-2023-ch6-housing.txt`. A general housing element (affordability-gap tables
  at 80/50/30% AMHI, Goal 6.2's "reasonable opportunity … including moderate-income housing", ADU /
  mixed-density-zone implementation steps) — **not** the HB462 formal menu-of-strategies element,
  because Nephi is exempt from that regime.
- **mih_annual_report** — the state HCD statewide compilations for report years **2023 / 2024 / 2025**.
  **Nephi is ABSENT from all three** (exempt). Retained in `raw/` as **evidence of the negative check**;
  there is **no** Nephi sidecar because there is no Nephi content.
- **compliance_letter** — HCD **SB 34 Municipal Progress Summaries 2019-2021**. **Nephi ABSENT.**
  HCD issues no per-city compliance letter; this is the closest published proxy.

## Statutory context

- **Utah Code §10-9a-403** — a municipal general plan must include a **moderate income housing (MIH)
  element** (strategies giving a "reasonable opportunity" for households ≤80% of county AMI). Nephi
  satisfies the *element* requirement via General Plan Element 6.
- **Utah Code §10-9a-408** — requires **specified municipalities** to file an **annual MIH report** with
  HCD. Per HCD's reporting page, "specified" = **cities over 10,000, or cities over 5,000 in counties
  with ≥40,000 population.** Nephi (~6,500) in Juab County (~11,800) meets **neither** → **exempt** →
  absent from the compilations. (HB 436, 2026, additionally paused progress reporting for a year.)

## Build method / provenance

- Every raw file fetched through `.claude/skills/expand-city-sources/scripts/polite_fetch.py`
  (browser UA, ≥1s/host, logged). Byte-level provenance: `raw/_fetch_log.jsonl`.
- City site is **CivicPlus**; unlike many CivicPlus deployments, Nephi's **`/168/City-Code-Planning-
  Documents`** page exposes real static `DocumentCenter/View/<id>` hrefs — that is where the 2023
  General Plan link was found (via `sitemap.xml`).
- State docs from `https://jobs.utah.gov/housing/affordable/moderate/reporting/` (stable
  `NNreports.pdf` / `sb34.pdf`). Each compilation was **full-text searched for `Nephi`** (word-boundary)
  before recording absence; Sandy's ~30 hits/file confirm the searches are valid.

## Extraction & QC

- The General Plan PDF is **born-digital** → `pdftotext -layout` sidecars (full doc + the Element 6
  page-range). `screen_corpus.py` on `text/` → **clean**: 0 cid-artifacts / replacement-chars /
  PUA-garbled / mojibake / outliers; only the advisory repeated-line flag (the "Nephi City General
  Plan, 2023" page footer). dict_ratio median 0.75.
- State compilations: **no Nephi sidecar** (no Nephi content); the raw PDFs are the retained evidence.
- Cosmetic note: the General Plan's section HEADERS are letter-spaced in the source ("H o u s in g"),
  so headers extract with intra-word spaces. Body text is unaffected.

## Caveats

- **Do not read the mih_element as an HB462 strategy filing.** It is a general-plan housing chapter;
  Nephi files no state MIH report and selects no formal statutory strategy menu (it is exempt).
- **The three `NNreports.pdf` + `sb34.pdf` in `raw/` are NOT Nephi filings.** They are statewide
  compilations kept only to document that Nephi is absent. Never quote them as Nephi data.
- **No embedded adoption date** in the GP; `date=2023` is the title year. An adoption vote may exist in
  `meeting_minutes/` (not cross-referenced here).

## Linkage to the rest of the repo

- Any Council adoption of the 2023 General Plan would join to `meeting_minutes/all_votes.csv` by date
  (not resolved here — the PDF carries no adoption instrument). Nephi records votes narratively
  (tally-only for most motions — see the city `CLAUDE.md`).
