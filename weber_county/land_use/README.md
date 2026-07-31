# weber_county / land_use — planning-corpus (FTS-only)

**Scope of this build (owner-gated, 2026-07-20): this is a SEARCHABLE-TEXT corpus only.**
Weber County's land-use minutes are ingested as provenance-stamped markdown for the
repo's FTS layer. There is **NO vote extraction, NO `all_votes.csv`/`motions_tally.csv`,
and NO development-pipeline table** in this pass — unlike the reference county
(`salt_lake_county/land_use/`, which has the full vote layer).

**Why FTS-only.** Weber runs **three planning commissions plus a Board of Adjustment**
(see below), each with its own naming/roll-call conventions. Building the full audited
vote + referral + disposition layer across four bodies was judged too expensive for the
value at this stage. Promotion to the full layer is **queued for later** if Ogden
Valley / Western Weber growth analysis becomes a priority. This file records that scoping
honestly so no downstream reader mistakes the absence of votes for a data gap — the votes
were **never extracted**, by decision.

Cardinal rules still apply: nothing is fabricated, every document carries per-row
provenance (`minutes_index.csv` + markdown front-matter), and honest gaps are recorded
(`gaps.csv`).

## Bodies and the 2025 consolidation seam

Weber County's unincorporated land use was historically split between two area planning
commissions, with a countywide Board of Adjustment as the appeal authority. **In late
2025 the county dissolved the two area commissions into one.**

- **Weber County Planning Commission** (`weber_county_pc`) — the **consolidated**
  countywide PC. Created by **Weber County Ordinance 2025-27** (final reading
  **2025-11-18**), which dissolved the Ogden Valley PC and the Western Weber PC and
  established a single planning commission for all unincorporated areas, **effective
  2025-12-03**. First meeting in this corpus: **2025-12-09**. Portal page:
  `planning/new_planning_commission.php`.
- **Ogden Valley Planning Commission** (`ogden_valley_pc`) — the former eastern-county
  (Ogden Valley: Eden/Liberty/Huntsville/Wolf Creek) area commission. Corpus
  **2020-04-07 .. 2025-12-02** (its last independent meeting before consolidation).
  Portal page: `planning/ogden_valley.php`.
- **Western Weber Planning Commission** (`western_weber_pc`) — the former western-county
  (West Weber, Warren, Uintah Highlands, etc.) area commission. Corpus
  **2021-02-09 .. 2025-11-18**. Portal page: `planning/western_weber.php`.
- **Board of Adjustment** (`board_of_adjustment`) — the county's **Appeal Authority /
  Administrative Review** body (variances, appeals of administrative land-use decisions).
  Corpus **2022-04-28 .. 2025-10-23**. Portal page: `planning/appeal_authority.php`.

### WATCH ITEM — Ogden Valley incorporation (date-bound)

**Ogden Valley City incorporated**: the incorporation ballot passed the **2024 general
election** (63.3 sq mi covering Eden, Liberty and Wolf Creek); its city council was
elected in the **2025 general election** (new municipality at **ogdenvalley.gov**). That
incorporation **removed jurisdiction** from the former Ogden Valley PC and directly
triggered the county's 2025 consolidation (Ordinance 2025-27). Consequences for future
refreshes:
- The **Ogden Valley PC is sunset** as of the 2025-12-03 consolidation — do not expect
  new minutes on `ogden_valley.php` after 2025-12-02; new Ogden-Valley-area land use in
  unincorporated pockets now flows through the consolidated **Weber County PC**, while
  **incorporated Ogden Valley City** land use will live at its own municipality (a
  potential FUTURE city build under `build-city-data-repo`, not part of this county).
- Treat the OVPC/WWPC archives here as **closed historical series**; the live body going
  forward is `weber_county_pc`.

## Coverage (measured)

166 unique meeting minutes, floor **2020-01-01** (matches confirmed portal availability).

| Body | Minutes | Range |
|------|--------:|-------|
| Ogden Valley PC | 77 | 2020-04-07 .. 2025-12-02 |
| Western Weber PC | 69 | 2021-02-09 .. 2025-11-18 |
| Board of Adjustment | 12 | 2022-04-28 .. 2025-10-23 |
| Weber County PC (consolidated) | 8 | 2025-12-09 .. 2026-05-05 |
| **Total** | **166** | 2020-04-07 .. 2026-05-05 |

- **Text**: 165 minutes extracted directly (`pdftotext -layout`, plus a handful of
  `.docx`/`.rtf` originals decoded with `textutil`); **1** scanned image
  (WWPC 2021-10-12) recovered via **tesseract OCR** (`extraction=text_ocr`). ~3.7M
  characters total.
- **Raw originals retained** in `raw/` (91 MB) — minutes PDFs are small; kept for audit.

## Honest gaps (not fabricated)

- **Weber County PC** shows only 2025-12 onward **because the body did not exist before
  then** (consolidation floor), not because minutes are missing.
- **Western Weber PC has no 2020 minutes** — the portal's WWPC archive begins 2021-02-09;
  2020 WWPC minutes are not posted (GRAMA-only). Honest gap.
- The consolidated Weber County PC portal page **only lists 2025–2026**; older WCPC-era
  minutes are behind a **GRAMA request** ("For past years minutes please file a GRAMA
  request form"). The deep 2020–2024 history is preserved here via the OVPC/WWPC archive
  pages, which were still online 2026-07-20.
- **Board of Adjustment is sparse by nature** — only 12 posted minutes 2022–2025. Many BOA
  dates carry an agenda/packet but no minutes (meetings frequently cancelled, or minutes
  not posted). This reflects the body's low volume, not extraction loss.
- **Meetings with an agenda/packet but no posted minutes** (portal, ≥2020): OVPC ~29,
  WWPC ~43, BOA ~28, WCPC 3 (recent, minutes pending approval). These are agenda-only
  dates — not ingested (no deliberative record to search).
- **Source mis-links** (`gaps.csv`): three portal entries linked the wrong PDF (a
  neighboring commission's file or a wrong-dated file). The mislinked copies were
  **dropped** (the correctly-bodied copy is retained under its true date) and the affected
  original meeting is logged as minutes-unavailable. The first consolidated PC meeting
  (2025-12-09) was cross-posted identically on all three PC pages; kept once under
  `weber_county_pc`.
- **Filename typos retained**: a few source filenames encode the wrong year (e.g.
  `01-24-22` for a Jan 24 **2023** meeting). The portal meeting date is trusted (verified
  against the minutes' own printed date); the filename typo is recorded in the row `note`.

## Files

- `minutes/<year>/<date>_<body_slug>.md` — provenance-stamped markdown (front-matter:
  jurisdiction, body, date, source_url, source_file, source, extraction).
- `minutes_index.csv` — one row per meeting: date, body, md_path, source_url,
  source_file, minutes_status (Approved/Draft/Unlabeled), extraction, text_chars, note.
- `gaps.csv` — source mis-links and unavailable-minutes records.
- `raw/` — retained original PDFs (and a few docx/rtf) named `<date>_<body_slug>.<ext>`.

Source host: **webercountyutah.gov/planning** (`documents/uploads/…`). Verified live
2026-07-20.
