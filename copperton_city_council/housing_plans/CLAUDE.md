# housing_plans/ — Town of Copperton moderate-income housing dataset

Source 2 of the `expand-city-sources` skill: Copperton's **2020 General Plan** and its **embedded
housing / moderate-income element (Chapter Six)**, plus the checked-and-absent **state HCD
reporting** record. Purely **additive** — no existing Copperton dataset was touched. As-of 2026-07-14.

**READ `AVAILABILITY.md` FIRST.** This is a **near-empty-by-design** dataset: a ~800-person,
MSD-staffed town (metro township 2017–2024 → Town 2024-05-01) that has a General Plan housing
element but is **below the population threshold** for modern state MIH annual reporting, so it is
**absent from every state HCD compilation**. That absence is the correct, honest finding — not a
gap. Direct analogue: **Alta** (~380 pop, embedded legacy element, absent from all compilations).

## Layout
```
raw/    1 Copperton General Plan PDF (born-digital, 90pp/57MB) + 4 state HCD compilation PDFs
        (copied from bluffdale, sha256-verified, UN-INDEXED — reference evidence for the
        "Copperton absent" finding) + _fetch_log.jsonl provenance
text/   pdftotext -layout sidecar of the General Plan (1 file)
index.csv         §9 housing contract header (2 rows, both -> the one General Plan PDF)
AVAILABILITY.md   what was checked, per-year state presence/absence, threshold reasoning (READ FIRST)
CLAUDE.md         this file
```

## index.csv schema
Exact SCHEMA_SPEC §9 housing contract header, in order:
`date,title,doc_type,source_url,retrieved_date,format,extraction_method,path,pages,repository,notes`
- `doc_type` used here: `general_plan`, `mih_element`. (No `mih_annual_report` / `compliance_letter`
  rows — Copperton files none; see AVAILABILITY.md.)
- **Both rows point at the SAME raw PDF** (`raw/copperton-general-plan-2020.pdf`): Copperton's
  housing/MIH element is **Chapter Six: Housing** of the General Plan, not a standalone file.
  `pages` = 90 for the whole plan, `103-109` for the element's printed pages. **Do NOT double-count
  these as two documents/files.**
- `path` is dataset-relative including `raw/` (linter requirement); `format=text`.

## The two source families

1. **Town of Copperton → MSD** (the town is MSD-staffed). The GoDaddy town site
   (`copperton.utah.gov`, TLS mismatch → `curl -k`) has **no** general-plan/housing page; its
   `/planning-and-zoning` page **delegates long-range planning to Greater Salt Lake MSD**. Followed
   the delegation to the MSD CivicPlus front (`ut-greatersaltlakemsd.civicplus.com`, = `msd.utah.gov`):
   **Copperton community page `/233/Copperton` → General Plan `/360/General-Plan`** lists the town's
   planning docs. The **2020 Copperton Adopted General Plan** (`DocumentCenter/View/216`) was
   retrieved there; it embeds the housing element as **Chapter Six: Housing** (pp 103-109; a
   "Cost-Burdened and Moderate-Income Housing" subsection + a Housing Work Program; cites 10-9a-401/403;
   **no** HB462/10-9a-408 framing). **No standalone MIH plan exists for Copperton** — the MSD LRP
   index's standalone MIH pages belong to the larger siblings (**White City** `/446`, **Kearns**
   `/405,/407`), verified by page content, NOT Copperton. Other Copperton MSD docs (annexation plan
   View/218, technical assessment View/217, historic-district nomination View/494) are not housing
   plans and are out of the §9 doc_type vocab — noted in AVAILABILITY, not indexed here.
2. **State HCD** (Utah DWS, `jobs.utah.gov`) — the four statewide compilations
   `{23,24,25}reports.pdf` + `sb34.pdf` were **copied sha256-verified from
   `bluffdale_city_council/housing_plans/raw/`** (not re-downloaded; provenance + true
   `jobs.utah.gov` URLs + original 2026-07-13 retrieval timestamps recorded in `raw/_fetch_log.jsonl`
   with a `copied_from` note). **Copperton is present in NONE** (whole-word grep = 0 in all four;
   TOCs run …Cottonwood Heights → Kearns / Magna with no Copperton). Hence no `text/copperton-*.txt`
   sidecar and no annual-report index rows. The compilation PDFs are kept **un-indexed in `raw/`** so
   the absence is independently re-verifiable from this folder.

## Key facts
- Copperton **HAS** a moderate-income housing element (embedded General-Plan **Chapter Six**, 2020) —
  but publishes/files **NO** modern (HB462 / 10-9a-408) standalone element, annual report, or HCD
  compliance letter. It is **below the state MIH population-reporting threshold** (~800 pop).
- The threshold contrast is visible inside the MSD family itself: the **larger** MSD siblings
  **White City, Magna, Kearns** file standalone MIH plans and appear in the state compilations;
  **Copperton** (and **Alta**) do not.
- The General Plan PDF is **born-digital text** (`pdftotext -layout`, `format=text`); the
  council-minutes OCR seam does NOT apply here. The plan is **metro-township-era** (2020) — it
  predates the 2024 Town conversion.

## Regenerating / extending
- Raw fetch: `python3 ../../.claude/skills/expand-city-sources/scripts/polite_fetch.py --out raw --name <f>.pdf <URL>`.
- Sidecar: `pdftotext -layout raw/copperton-general-plan-2020.pdf text/copperton-general-plan-2020.txt`.
- Validate: `python3 ../../.claude/skills/expand-city-sources/scripts/validate_dataset.py .` → PASS.
- On a future refresh, re-check `/233/Copperton` + `/360/General-Plan` on the MSD site for a NEW
  (town-era, post-2024) General Plan or a first standalone HB462 MIH element, and re-grep any newer
  `NNreports.pdf` compilation for a first "Copperton" entry (would appear only if the town ever
  crosses the reporting threshold).
- This dataset feeds `cities.db` `document` catalog + `fts_*` on the next
  `scripts/build_cities_db.py` run (do NOT run that here — out of scope for this build).

## Do not
- Do not fabricate an annual report / compliance letter — Copperton files none; the absence is the record.
- Do not double-count the two index rows as two files (same raw PDF; the element is a plan chapter).
- Do not attribute the White City / Kearns standalone MIH plans to Copperton (different communities).
- Do not edit any existing Copperton dataset or the parent README/CLAUDE from this folder.
- Do not delete/normalize `raw/` originals, including the un-indexed state-compilation evidence PDFs.
