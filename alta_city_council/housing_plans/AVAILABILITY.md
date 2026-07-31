# housing_plans — availability & verification (Town of Alta)

**As of:** 2026-07-13. Built by the `expand-city-sources` skill (Source 2, moderate-income
housing). Additive dataset — nothing in any existing Alta dataset was modified.

**Headline:** Alta is a **~380-person resort town** and behaves accordingly. It **HAS a General
Plan with a (legacy, embedded) moderate-income-housing element**, but it is **ABSENT from every
modern state HCD reporting compilation** (2023/2024/2025 annual + SB 34 2019–2021) — Alta sits
**below the population thresholds** that trigger the HB 462 / 10-9a-408 annual-reporting
obligation. This is a **near-empty-by-design** dataset (2 index rows, both pointing at the single
General Plan PDF), and that is the **correct, honest** deliverable for a town this size — not a gap.

## What was checked

Two source families, per the skill.

### 1. Town of Alta site (`townofalta.utah.gov`, Juniper WordPress CMS; docs in GCS bucket `juniper-media-library` tenant 130)
The `/meetings/` app is a JS SPA (unscrapable — recon), but the **static govtech pages carry direct
GCS document links**. Checked:

- **`/planning-commission/`** — links **"Town of Alta General Plan (Updated 2016)"**
  (`.../130/2024/08/Town of Alta General Plan (Updated 2016).pdf`). The page states the PC's
  primary function is to "author and approve the Town of Alta General Plan." **No** separate MIH
  or housing-element document is linked.
- **`/general-plan-studies/`** (the GOVERNMENT-menu "General Plan & Studies" page) — links the base
  **"2005 Town of Alta General Plan"** plus **~25 special plans/studies** (Commercial Core Plan,
  water/sewer CIPs, transportation, Albion Basin ecology, community-center studies, dark-sky, etc.).
  **NONE** is a moderate-income-housing plan, affordable-housing study, or HB462 MIH element.
  (Housing-related content: none, beyond the General Plan's own Section 3.18.)
- **`/town-council/`** — no housing-plan / MIH links.
- **`/general-plan/`** — **HTTP 404** (no such page; the General Plan lives under
  `/general-plan-studies/` and `/planning-commission/`).

**Retrieved:** the current **General Plan (Updated 2016)** PDF (38 pp, born-digital text). It
**contains the town's MIH element as Section 3.18 "Plan for Moderate Income Housing" (printed
p.13)** — a legacy element that cites the **pre-2019 statute "Title 10, Chapter 9, Part 307"**
(the MIH statute superseded by the current 10-9a-403/408) and frames Alta's obligation as
**employee housing**: the 1989 zoning ordinance requires employee living accommodations for new
Base-Facilities-zone commercial development and caretaker units elsewhere, with a current
employee-housing inventory kept at the Town Office. This is a genuine MIH element — brief, legacy,
and embedded in the General Plan rather than a standalone HB462-era document.

### 2. State HCD compilations (Utah DWS Housing & Community Development, `jobs.utah.gov`)
The four current statewide compilation PDFs were **copied sha256-verified from
`bluffdale_city_council/housing_plans/raw/`** (NOT re-downloaded; the original DWS retrievals were
2026-07-13). Each was searched for a **Town of Alta** entry. **Alta is present in NONE of them:**

| Compilation | Total pp | Town of Alta present? | Evidence |
|---|---|---|---|
| `23reports.pdf` (RY 2023 annual) | 1109 | **NO** | TOC & body run **Alpine → American Fork → Bluffdale**; no Alta entry |
| `24reports.pdf` (RY 2024 annual) | 1030 | **NO** | TOC runs **Alpine city → American Fork city → Bluffdale city**; no Alta |
| `25reports.pdf` (RY 2025 annual) | 1303 | **NO** | TOC runs **Alpine city → American Fork city → Bluffdale city**; no Alta |
| `sb34.pdf` (SB 34 Municipal Progress Summaries 2019–2021) | 199 | **NO** | SUMMARY ORDER **1. ALPINE, 2. AMERICAN FORK, 3. BLUFFDALE**; no Alta |

The only whole-word "Alta" hit across all four compilations is **"Alta View"** (a Sandy-area school
referenced inside another city's report) — **not** the Town of Alta. There is **no "Alta Canyon"**
content either. Because Alta appears in none of the compilations, **no `text/alta-<year>.txt`
sidecar was extracted** (the skill: extract a sidecar "only where present"), and **no
`mih_annual_report` index rows were created** — creating one would fabricate an Alta report that
does not exist. The four compilation PDFs are **retained un-indexed in `raw/`** purely so the
absence finding is independently re-verifiable from Alta's own folder (re-run the TOC grep).

## Exemption status — why Alta files nothing with the state

Utah's SB 34 overview (in `sb34.pdf`) states annual progress reporting is required only of
**"Communities, counties, and metro-townships meeting specific population thresholds."** The modern
HB 462 MIH-plan-and-annual-report regime (10-9a-403/408) is likewise gated: the demanding
plan/reporting duties fall on municipalities above population thresholds and/or within the more
urbanized county classes. **Alta (~380 residents) is far below any such threshold**, which is
exactly why it is **absent from every state compilation** while its immediate alphabetical
neighbors (Alpine ~10k, American Fork ~40k, Bluffdale ~19k) all appear. Alta's obligation is
satisfied by the **legacy MIH element (Section 3.18) in its General Plan** — the older, lighter
requirement appropriate to a town of its size. (This is a well-supported inference from the
statutory threshold language + the observed state-compilation absence; the town publishes no
explicit "we are exempt" letter, and none is expected.)

## What is NOT published / not applicable (honest gaps — none of these is a defect)

- **No standalone HB462-era MIH element PDF** — Alta's MIH element is the embedded Section 3.18.
- **No annual 10-9a-408 implementation report** filed with or published by the state (absent from
  23/24/25 compilations) — Alta is below the reporting-threshold population.
- **No HCD compliance/notice letter** — none is issued because no annual report is filed.
- **No affordable-housing study or MIH-specific plan** among the ~25 town special plans/studies.

## Extraction & verification method

- The General Plan PDF is **born-digital** (`Producer: PDFium`; text layer present).
  `pdftotext -layout` → clean selectable text (`format=text`, `extraction_method=pdftotext -layout`).
- Fetched through `scripts/polite_fetch.py` (browser UA, throttled, logged); provenance in
  `raw/_fetch_log.jsonl` (HTTP 200, `application/pdf`, sha256 recorded).
- State compilations **sha256-verified byte-identical** to the bluffdale copies after `cp`; their
  true `jobs.utah.gov` source URLs + original retrieval timestamps are recorded in the fetch log
  with an explicit `copied_from` / `COPIED (not re-downloaded)` note.
- Corpus screened with `audit-city-data/scripts/screen_corpus.py`: **0 outliers** (dict_ratio
  0.779, split-word 0.11/1k, weird-char 0.0007) across the 1 sidecar. The lone advisory `ends_mid`
  flag is a footer/page-number artifact of the plan layout, not an extraction defect.
- Alta-absence in each compilation verified by inspecting the printed **Table of Contents /
  SUMMARY ORDER** (alphabetical city index) AND a whole-word `\balta\b` grep of the full extracted
  text of all four compilations.

## Do not

- Do **not** manufacture an annual-report or compliance-letter row — Alta genuinely files none; the
  absence is the finding.
- Do **not** double-count the two index rows as two files: both `general_plan` and `mih_element`
  point at the **same** `raw/alta-general-plan-2016.pdf` (the element is Section 3.18 of the plan).
- Do **not** delete/normalize the un-indexed state-compilation PDFs in `raw/` — they are the
  on-disk evidence for the "Alta absent" claim.
