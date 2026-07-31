# housing_plans — availability & verification (Kearns)

**As of:** 2026-07-13. Built by the `expand-city-sources` skill (Source 2, moderate-income
housing). Additive dataset — nothing in any existing Kearns dataset was modified; the parent
`README.md`/`CLAUDE.md` are the orchestrator's to edit, not this folder's.

**Headline finding: NOT honest-empty; NOT below the reporting threshold; NOT absorbed under an
MSD umbrella entry.** At ~36k pop. Kearns (the largest former SLCo metro township) has a
**standalone adopted Moderate Income Housing (MIH) Plan** (2022, amended Sept 27 2022; adopting
Resolution 2023-01-02) plus a 2020 General Plan, and it **files a 10-9a-408 report under its own
name every state year checked** (SB 34 2019–2021, RY 2023/2024/2025). Long-range planning is
**staffed by the Greater Salt Lake Municipal Services District (GSL-MSD)**, so the plan, its
adopting resolution, and the General Plan all live on **`msd.utah.gov`** (CivicPlus DocumentCenter)
— NOT on the Cloudflare-blocked `kearns.utah.gov` city site — but the **entity of record in the
state compilations is "Kearns" / "Kearns, Metro Township."** 8 indexed docs (4 raw PDFs fetched
here + the 3 shared statewide compilations + SB 34).

## Why not the city site

`kearns.utah.gov` serves a Cloudflare "Just a moment…" JS challenge to every bot UA (see
`../recon.md`) and is not scrapable. It is also not needed here: like White City, Kearns's
planning is MSD-staffed, so the housing/general-plan documents are hosted on the **MSD CivicPlus
site**, discovered via the MSD **City-of-Kearns** page (`msd.utah.gov/239/City-of-Kearns`). The
statewide HCD reports' **"Link to Plan" / "Link to Ordinance or Resolution"** fields point
straight at those MSD-hosted docs (`msd.utah.gov/DocumentCenter/View/442` and `.../View/738`),
which is how the plan + adopting instrument were confirmed as the documents of record.

## What was checked

Two source families, per the skill:

1. **City / MSD** — the **MSD City-of-Kearns page** (`msd.utah.gov/239/City-of-Kearns`) exposes
   three Kearns documents: the **General Plan and Appendix (2020)** (`View/273`), the **Moderate
   Income Housing Plan (2022)** (`View/442`), and the **Resilience + Infrastructure Element**
   (`View/270`). The MSD **Moderate-Income-Housing-Plan** page (`/446`) and **Planning-Development**
   page (`/203`) were also checked — `/446` lists only White City's MIH docs, not a second Kearns
   copy. The **adopting/correcting resolution** (`View/738`, Resolution 2023-01-02) was found via
   the state reports' "Link to Ordinance or Resolution" field.
2. **State HCD** — Utah Dept. of Workforce Services, Housing & Community Development, index
   `https://jobs.utah.gov/housing/affordable/moderate/reporting/`. Annual reports are **statewide
   compilation PDFs, not per-city files** (`{23,24,25}reports.pdf`) plus the `sb34.pdf` SB 34
   Municipal Progress Summaries (2019–2021).

## What was FILED / retrieved (8 index rows)

### City / MSD documents (4 PDFs fetched here, all born-digital `text`)
- **General Plan and Appendix (2020)** — `msd.utah.gov/DocumentCenter/View/273`, 536 pp, 98 MB.
  Kearns's FIRST general plan (metro-township era). The MIH element is a **separate standalone
  plan**, not embedded here.
- **Resilience + Infrastructure Element** — `View/270`, 44 pp. An adopted supplemental element of
  the 2020 General Plan (land-use / growth context); indexed as `general_plan`, not the MIH element.
- **Moderate Income Housing Plan (2022, as amended Sept 27 2022)** — `View/442`, 74 pp. The
  standalone MIH element (Utah Code 10-9a-403/408, HB 462 2022), GSL-MSD-staffed. The document the
  state reports cite as "Link to Plan."
- **Resolution 2023-01-02 (PASSED 9 Jan 2023)** — `View/738`, 3 pp. Corrects a technical error in
  the MIH Plan (inserts a statutory strategy option verbatim so Kearns qualifies for HB 462
  priority funding after DWS flagged the cite-not-quote defect on 22 Nov 2022). Named roll:
  Bush / Snow / Schaeffer / Peterson **Y**, Butterfield **Excused**. The state reports' "Link to
  Ordinance or Resolution."

### State HCD compilations (4 — Kearns PRESENT in ALL of them)
Each statewide compilation was **sha256-verified-copied from `bluffdale_city_council/housing_plans/raw/`**
(they are shared statewide PDFs; do NOT re-download — see CLAUDE.md). Kearns's alphabetical page
range was located (bracketed by the previous city **Kaysville** and the next city **Layton**) and
extracted to a `text/` sidecar, then grep-verified for zero neighbor-city bleed:

| Compilation | Total pp | Kearns (physical, 1-based) pp | Sidecar | Filer |
|---|---|---|---|---|
| `23reports.pdf` (RY 2023) | 1109 | **317–331** | `text/kearns-2023.txt` | Kearns / MSD (Kaysville ends p316, Layton starts p332) |
| `24reports.pdf` (RY 2024) | 1030 | **304–313** | `text/kearns-2024.txt` | Morgan Julian, MSD LRP II (Layton starts p314) |
| `25reports.pdf` (RY 2025) | 1303 | **401–413** | `text/kearns-2025.txt` | Bianca Paulino, MSD LRP II (Layton starts p414) |
| `sb34.pdf` (SB 34 2019–2021) | 199 | **65–66** | `text/kearns-sb34-2019-2021.txt` | "KEARNS, METRO TOWNSHIP" (Kaysville p64, Layton p67) |

**Per-year presence / absence (the honest check the task asked for):**

| State filing year | Present? | Reported as | Notes |
|---|---|---|---|
| SB 34 2019–2021 | **PRESENT** | KEARNS, METRO TOWNSHIP | County Salt Lake; WFRC; 3 required + 6 total menu items; major transit corridor YES; strategies submitted 2019 & 2020. |
| RY 2023 | **PRESENT** | Kearns | Strategy #1 = ADUs in residential zones; cites the MSD MIH Plan (View/442) + Resolution 2023-01-02 (View/738). |
| RY 2024 | **PRESENT** | Kearns city | filed by MSD Long Range Planner II (Morgan Julian); notes a Sept-2023 rezone (8 ac, 5600 West, RM → Corridor Mixed Use). |
| RY 2025 | **PRESENT** | Kearns city | filed by MSD Long Range Planner II (Bianca Paulino); cites Resolution 2023-01-02 + MIH Plan; 5400 South Corridor Study launched. |

There is **no RY 2022 statewide compilation** on the current HCD index (earliest is `23reports.pdf`);
the SB 34 summary covers 2019–2021, so there is **no honest gap** between the SB 34 window and RY 2023.

## Threshold / MSD-reporting status (the task's core question)

- **NOT below the reporting threshold.** Kearns (~36k) files a full 10-9a-408 moderate-income
  housing report under its own name in every year the state has published. It adopted a plan
  (2022, corrected Jan 2023) and reports against it.
- **Reported under its OWN identity, staffed by GSL-MSD — NOT absorbed under the MSD.** The reports
  are authored/submitted by **Greater Salt Lake MSD Long-Range Planning staff** on Kearns's behalf
  (Morgan Julian 2024, Bianca Paulino 2025), and the plan/ordinance/GP are hosted on `msd.utah.gov`,
  but the **entity of record is "Kearns" (metro township in SB 34, "Kearns city" in RY 2023–2025)**
  — there is no separate "Greater Salt Lake MSD" umbrella entry standing in for it. The
  township→city transition (HB 35, city effective 2024-05-01) creates **no reporting gap**: SB 34
  files it as "Kearns, Metro Township"; RY 2023–2025 as "Kearns."

## What is NOT filed / not applicable

- **No standalone per-city report PDF on the state HCD site** — expected; the state publishes only
  the statewide compilations. Not a gap.
- **No HCD compliance / notice-of-compliance LETTER found** for Kearns. The MSD-hosted material is
  the plan + adopting resolution; the compliance status is documented *inside* Resolution
  2023-01-02's recitals (DWS found the plan compliant with HB 462 on 22 Nov 2022) and the annual
  reports, but no separate DWS letter PDF is posted on the MSD or (blocked) city site. Recorded as
  an honest absence — no `compliance_letter` row (same posture as White City).

## Extraction & verification method

- The 4 city/MSD PDFs are **born-digital** — `pdftotext -layout` yields clean, selectable text
  (proper names intact); `format=text`. Sidecars in `text/`.
- The 4 state compilations are the **shared statewide HCD PDFs**, sha256-verified-copied from the
  bluffdale build (identical bytes — see `raw/_fetch_log.jsonl` copy-provenance rows and CLAUDE.md);
  Kearns excerpts extracted by physical page range (pymupdf) bracketed by Kaysville (before) and
  Layton (after), each sidecar grep-verified to contain "Kearns" (24–75 mentions) and **zero**
  Kaysville / Layton / other neighbor strings.
- Every fetched raw byte went through `scripts/polite_fetch.py` (browser UA, throttled, logged);
  provenance in `raw/_fetch_log.jsonl` (4 MSD fetches HTTP 200 `application/pdf`; the 4 HCD rows
  are copy-provenance records carrying the true `jobs.utah.gov` URL + original bluffdale retrieval
  timestamp).
- Corpus screened with `audit-city-data/scripts/screen_corpus.py` over the 8 sidecars: **0 read
  errors, 0 dict_ratio / split_word / weird_char / mojibake / stub / duplicate-body outliers.** The
  flagged `hyphen_breaks` (General Plan multi-column layout; SB 34 form layout), `repeated_line`
  (state web-form templates + plan boilerplate), and advisory `ends_mid` (page-range excerpts /
  form layouts) are all expected, non-defect artifacts.
