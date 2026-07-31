# housing_plans/ — availability (Emigration Canyon)

**As-of:** 2026-07-14. Source 2 of `expand-city-sources`: moderate-income housing (MIH)
plans, the General Plan, and the state MIH annual-reporting record. **Purely additive** — no
existing Emigration Canyon dataset was touched.

## Bottom line

Emigration Canyon is a **~1,600-population municipality** (metro township 2017-2024 → city
2024-05-01) administered by the **Greater Salt Lake Municipal Services District (MSD)**. It
publishes **one relevant document — its 2022 General Plan** (land-use context). It has **no
standalone Moderate Income Housing (MIH) element**, files **no state MIH annual report**, and
holds **no HCD compliance letter** — because it is **below the statutory MIH threshold**. This
is an **honest near-empty result, expected and valid**, not a collection gap.

## Why near-empty is correct: the MIH threshold

Utah Code **10-9a-403** requires a **Moderate Income Housing element** (and, via **10-9a-408**,
an annual implementation report to the state) only for a **"specified municipality"** —
defined as a **fifth-class city with a population of 5,000 or more** located within a county of
the first, second, or third class. At **~1,600 residents Emigration Canyon is well below the
5,000 threshold**, so it is **not required** to adopt a MIH element or file the annual MIH
report. This mirrors the other tiny MSD-cluster municipalities already documented in this repo
(**Copperton ~800, Alta ~380**) — all absent from the state compilations for the same reason.

## What WAS found (indexed — 1 doc)

| doc_type | doc | date | repository | note |
|---|---|---|---|---|
| general_plan | Emigration Canyon General Plan 2022 | 2022-03-22 (adopted) | MSD `msd.utah.gov/DocumentCenter/View/252` | Land-use context; NO MIH element |

- **Discovery path (confirmed for the MSD cluster):** MSD CivicPlus front → community page
  `msd.utah.gov/349/Emigration-Canyon` and the dedicated **General Plan page**
  `msd.utah.gov/295/Emigration-Canyon-General-Plan-2022` → `DocumentCenter/View/252`.
- **Contents:** 7 chapters — Introduction, Land Use & Character Areas, Transportation &
  Mobility, Economic Development, Environment, Resilience & Infrastructure, Community Work
  Program. **No dedicated Housing chapter and no MIH element.** Housing is discussed only
  *within* Land Use / Economic Development (housing cost-burden, "support housing options",
  the 10-9a-401/403 general-plan-element framing). The plan explicitly notes only **Land Use
  and Transportation** are the state-required elements; housing is listed among optional
  elements the plan *may* include, and Emigration Canyon did not include a MIH element.
- **Not retained (duplicate/supplementary, noted for completeness):** a print-layout version
  (`View/254`) and **Appendix A-L** (`View/253`, which includes Appendix D housing
  cost-burden data). These are duplicate/supporting material to the indexed main plan; not
  downloaded to conserve disk. Both remain live at the URLs above.

## What was checked and is ABSENT (honest gaps — DATA, not fabricated)

### State HCD annual-reporting compilations — Emigration Canyon ABSENT every year
The state publishes **statewide compilation PDFs, not per-city files**. The four compilations
were **copied sha256-verified from `bluffdale_city_council/housing_plans/raw/`** (identical
bytes; NOT re-downloaded — provenance and true `jobs.utah.gov` URLs in `raw/_fetch_log.jsonl`
and `CLAUDE.md`) and each was full-text searched for "Emigration":

| Compilation | Covers | Pages | "Emigration" present? |
|---|---|---|---|
| `23reports.pdf` (RY 2023) | 2023 | 1,109 | **NO** |
| `24reports.pdf` (RY 2024) | 2024 | 1,030 | **NO** |
| `25reports.pdf` (RY 2025) | 2025 | 1,303 | **NO** |
| `sb34.pdf` (SB 34 progress) | 2019-2021 | 199 | **NO** |

The compilations are **retained un-indexed** (no `index.csv` rows) purely as **absence
evidence** — the searchable statewide record shows Emigration Canyon filed nothing in any
reporting year. Extraction was verified working (neighboring cities Draper, Cottonwood
Heights, Eagle Mountain, Bountiful all present in every compilation), so the absence is real,
not a text-extraction failure. No `text/<city>-<year>.txt` sidecar exists because the city has
no page range to extract.

### Standalone MIH element — NONE
No standalone MIH element exists on the MSD site. The MSD **"Moderate Income Housing Efforts"**
page (`msd.utah.gov/407`) and the **General Plans** index (`msd.utah.gov/371`) carry only the
**countywide / unincorporated-Salt-Lake-County** MIH plan and the **Salt Lake County** MIH
report + compliance notice — none specific to Emigration Canyon. (The county-level MIH plan is
Salt Lake County's obligation, out of scope for this city dataset.)

### MIH annual report (city-filed) — NONE. Compliance letter — NONE.
Consistent with the sub-5,000 threshold: no obligation to file, and none filed.

## Sources checked (as-of 2026-07-14)
- MSD community pages `msd.utah.gov/349/Emigration-Canyon`, `/217/Emigration-Canyon-Metro-Township`
- MSD General Plan 2022 page `msd.utah.gov/295/...` → `DocumentCenter/View/252` (retrieved, indexed)
- MSD General Plans index `msd.utah.gov/371/General-Plans` (no Emigration-specific MIH doc)
- MSD Moderate Income Housing Efforts `msd.utah.gov/407/...` (county/unincorporated only)
- State HCD compilations 23/24/25reports + sb34 (copied, searched, ABSENT — retained as evidence)
- Utah Code 10-9a-403/408 threshold definition (fifth-class city, population 5,000+)
