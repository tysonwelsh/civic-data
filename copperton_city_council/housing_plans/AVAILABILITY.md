# housing_plans — availability & verification (Town of Copperton)

**As of:** 2026-07-14. Built by the `expand-city-sources` skill (Source 2, moderate-income
housing). Additive dataset — nothing in any existing Copperton dataset was modified.

**Headline:** Copperton is a **~800-person town** (metro township 2017–2024 → Town 2024-05-01,
MSD-staffed) and behaves like the other sub-threshold small entities in the collection. It **HAS a
General Plan (2020) with an embedded housing / moderate-income element (Chapter Six)**, but it is
**ABSENT from every modern state HCD reporting compilation** (2023/2024/2025 annual + SB 34
2019–2021) — Copperton sits **below the population thresholds** that trigger the HB 462 /
10-9a-408 annual-reporting obligation. This is a **near-empty-by-design** dataset (2 index rows,
both pointing at the single General Plan PDF), and that is the **correct, honest** deliverable for
a town this size — not a gap. Pattern-match: **Alta (~380)** and, for the threshold contrast, the
larger MSD siblings **White City / Magna / Kearns** which DO appear in the state compilations.

## What was checked

Two source families, per the skill.

### 1. Town of Copperton site + the MSD planning apparatus (the town is MSD-staffed)
The town's own GoDaddy site (`copperton.utah.gov`, TLS cert mismatch → `curl -k` + browser UA) has
**no** General Plan / Long Range Plan / housing page of its own. Its `/planning-and-zoning` and
`/zoning-ordinances` pages **delegate long-range planning to Greater Salt Lake MSD** (contract
staff Wendy Gurr). Sitemap (`sitemap.website.xml`) enumerated — 25 pages, none housing/general-plan.

Followed the delegation into MSD (`ut-greatersaltlakemsd.civicplus.com`, the CivicPlus front for
`msd.utah.gov`). The **Copperton community page `/233/Copperton` → General Plan sub-page
`/360/General-Plan`** lists Copperton's planning documents:

| MSD DocumentCenter | Document | In this dataset? |
|---|---|---|
| View/216 | **2020 Copperton Adopted General Plan** (90 pp) | **YES** — general_plan + embedded mih_element |
| View/214 | 2020 General Plan Amenities & Priorities Survey Results | no — survey backup, not a housing plan |
| View/215 | Copperton General Plan SWOT/APAE Results | no — process backup |
| View/217 | Copperton Technical Assessment 2019 | no — existing-conditions backup, not a housing plan |
| View/218 | Adopted Copperton Annexation Policy Plan | no — annexation, not a housing plan (out of §9 doc_type vocab) |
| View/494 | Copperton National Historic District Nomination Form | no — historic designation, not housing |

**There is NO standalone Moderate Income Housing Plan / MIH element document for Copperton** on the
MSD site. The MSD Long-Range-Planning index (`/209`) DOES host standalone MIH pages/plans — but
those belong to the **larger** MSD siblings: `/446/Moderate-Income-Housing-Plan` = **White City**;
`/405` + `/407/Moderate-Income-Housing-Efforts` = **Kearns** (verified by page content). None is
Copperton's. Copperton's ArcGIS Hub (`copperton-lrp-gslmsd.hub.arcgis.com`) surfaces the same 2020
General Plan and no separate MIH plan.

**Retrieved:** the **2020 Copperton Adopted General Plan** (View/216; 90 pp, 57 MB, born-digital
Adobe PDF Library text). It **contains the town's housing/moderate-income element as Chapter Six:
Housing (printed pp 103-109)** — sections 6.0–6.7 including a **"Cost-Burdened and Moderate-Income
Housing"** subsection and a **Housing Work Program** (goals/objectives/actions/timeline). It cites
the general-plan-components statute **Utah Code 10-9a-401/403** (housing for residents of various
income levels) but does **not** reference **HB 462 / SB 34 / the 10-9a-408 annual-report regime**.
This is a genuine housing element — brief, embedded in the General Plan, framed under the general
land-use/general-plan statute rather than as a modern HB462 standalone MIH plan. (Note the plan is
metro-township-era: "the Mayor is the chief executive officer of the Metro Township.")

### 2. State HCD compilations (Utah DWS Housing & Community Development, `jobs.utah.gov`)
The four current statewide compilation PDFs were **copied sha256-verified from
`bluffdale_city_council/housing_plans/raw/`** (NOT re-downloaded; the original DWS retrievals were
2026-07-13, timestamps + true `jobs.utah.gov` URLs preserved in `raw/_fetch_log.jsonl` with a
`copied_from` note). Each was searched for a **Copperton** entry. **Copperton is present in NONE:**

| Compilation | Total pp | Copperton present? | Evidence |
|---|---|---|---|
| `23reports.pdf` (RY 2023 annual) | 1109 | **NO** | whole-word `copperton` grep = 0; TOC C-run …Cottonwood Heights → (no Copperton) |
| `24reports.pdf` (RY 2024 annual) | 1030 | **NO** | grep = 0; TOC Clinton city → Cottonwood Heights city → Magna city; no Copperton |
| `25reports.pdf` (RY 2025 annual) | 1303 | **NO** | grep = 0; TOC Cottonwood Heights city 159 → Kearns city 398; no Copperton |
| `sb34.pdf` (SB 34 Municipal Progress Summaries 2019–2021) | 199 | **NO** | grep = 0; summary order 11.CLEARFIELD → 13.COTTONWOOD HEIGHTS; no Copperton |

Whole-word `\bcopperton\b` = **0** across all four compilations. Because Copperton appears in none
of them, **no `text/copperton-<year>.txt` sidecar was extracted** (the skill: extract a sidecar
"only where present"), and **no `mih_annual_report` / `compliance_letter` index rows were created**
— creating one would fabricate a Copperton report that does not exist. The four compilation PDFs are
**retained un-indexed in `raw/`** so the absence finding is independently re-verifiable from
Copperton's own folder (re-run the grep).

## Exemption / threshold status — why Copperton files nothing with the state

Utah's SB 34 overview states annual progress reporting is required only of **"Communities,
counties, and metro-townships meeting specific population thresholds."** The modern HB 462 MIH
plan-and-annual-report regime (10-9a-403/408) is likewise gated on population thresholds / county
class. **Copperton (~800 residents) is below that threshold**, which is exactly why it is absent
from every state compilation while its **larger** MSD siblings **White City, Magna, Kearns** all
appear (and file standalone MIH plans on the MSD site) and its immediate alphabetical neighbor
**Cottonwood Heights** (~34k) appears. Copperton's obligation is satisfied by the **general-plan
housing element (Chapter Six)** — the lighter general-plan component appropriate to a town of its
size. (Well-supported inference from the statutory threshold language + observed absence; the town
publishes no explicit "we are exempt" letter, and none is expected. This mirrors **Alta**.)

## What is NOT published / not applicable (honest gaps — none is a defect)

- **No standalone HB462-era MIH element/plan PDF** — Copperton's MIH content is the embedded
  Chapter Six of the 2020 General Plan (the MSD siblings' standalone MIH plans are NOT Copperton's).
- **No annual 10-9a-408 implementation report** filed with or published by the state (absent from
  23/24/25 compilations) — Copperton is below the reporting-threshold population.
- **No HCD compliance/notice letter** — none is issued because no annual report is filed.
- **No newer / town-era (post-2024) General Plan** — the 2020 metro-township-era plan is the
  current adopted plan; the town site has no general-plan page and MSD lists only the 2020 one.

## Extraction & verification method

- The General Plan PDF is **born-digital** (`Producer: Adobe PDF Library 15.0`; selectable text).
  `pdftotext -layout` → clean text (`format=text`, `extraction_method=pdftotext -layout`).
- Fetched through `scripts/polite_fetch.py` (browser UA, throttled, logged) from the standard
  CivicPlus DocumentCenter host (no cert issue — unlike the town's own GoDaddy site); provenance in
  `raw/_fetch_log.jsonl` (HTTP 200, `application/pdf`, sha256, `retrieved_utc` 2026-07-14).
- State compilations **sha256-verified byte-identical** to the bluffdale copies after `cp` (all
  four hashes matched); their true `jobs.utah.gov` URLs + original 2026-07-13 retrieval timestamps
  are recorded in the fetch log with a `copied_from` / `COPIED (not re-downloaded)` note.
- Corpus screened with `audit-city-data/scripts/screen_corpus.py`: **0 substantive outliers** over
  the 1 sidecar (dict_ratio 0.717, split-word 3.74/1k, weird-char 0.0007, 0 cid/PUA/mojibake). The
  lone `repeated_line` + `ends_mid` advisory flags are two-column general-plan-layout artifacts
  (page headers/footers), not extraction defects — identical benign pattern to Alta's General Plan.
- Copperton-absence in each compilation verified by whole-word `\bcopperton\b` grep of the full
  extracted text **and** by inspecting the printed alphabetical TOC / SUMMARY ORDER.

## Do not

- Do **not** manufacture an annual-report or compliance-letter row — Copperton genuinely files none;
  the absence is the finding.
- Do **not** double-count the two index rows as two files: both `general_plan` and `mih_element`
  point at the **same** `raw/copperton-general-plan-2020.pdf` (the element is Chapter Six of the plan).
- Do **not** attribute the MSD siblings' standalone MIH plans (White City View/446, Kearns /405,407)
  to Copperton — they are different communities.
- Do **not** delete/normalize the un-indexed state-compilation PDFs in `raw/` — they are the on-disk
  evidence for the "Copperton absent" claim.
