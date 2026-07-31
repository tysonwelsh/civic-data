# pmn_backfill/AVAILABILITY.md — Holladay

**As-of:** 2026-07-14. Polite GET-only throughout (`scripts/polite_fetch.py`,
`_fetch_log.jsonl` in `raw/`). **No existing dataset was modified** — this is an additive,
review-before-merge backfill. Source 4 of `/expand-city-sources`.

## What this dataset is
Holladay's audited `meeting_minutes/` and `planning_commission/` layers were themselves built
**from PMN** (council body **388**, PC body **389**), so PMN is largely a superset-verify for
this city, not a source of new council minutes. The one real, documented upstream gap is that
**PMN never posted the 2020 / 2021 / 2023 Planning Commission minutes** (only agendas/packets).
This dataset (a) runs the full-history PMN sweep of **all 16 Holladay bodies** to confirm the
council/PC/RDA superset and quantify the PC gap, and (b) recovers what it can of the PC gap from
the **independent city channels** (SuiteOne / Revize Document Center / the former WordPress site
via the Wayback Machine).

## What was checked
- **PMN (utah.gov/pmn), entity Holladay = 160, all 16 public bodies.** Body ids resolved via
  `/pmn/list/publicBodies.html?id=160`. Cumulative notice lists swept
  (`/pmn/list/notices.html?id=<body>&page=300`); 1,165 attachments parsed. **Minutes live only
  under 388 (Council), 389 (PC), 791 (RDA).** Result: council + PC + RDA are all complete
  supersets of PMN for the 2020+ floor; PMN 389 confirmed to hold **no** 2020/2021/2023 PC
  minutes. Full table in `coverage.md`.
- **SuiteOne** (`holladayut.suiteonemedia.com`): **2025+ only** — every body carries
  `data-yearFrom="2025"`, and the historical search is a POST/CSRF form (outside polite-GET).
  Cannot reach 2020/2021/2023.
- **Live Revize Document Center** (`holladayut.gov/Document Center/Agendas And Minutes/…`):
  the current `agendas_and_minutes.php` embeds the SuiteOne iframe; individual older minutes
  are not linked. Folder probes: `Planning Commission/2020/` and `/2021/` return **403**
  (exist, listing forbidden); `/2022/`, `/2023/`, `/2024/` return **404**. 75 candidate
  filenames probed inside the 2020/2021 folders — no hits (filenames not guessable). The
  former WordPress `/file/…` paths now **404** on the live host (fully migrated).
- **Wayback Machine** (CDX over `cityofholladay.com` — 54k URLs — and `holladayut.gov`): the
  city's pre-migration WordPress site is where the recoverable PC minutes live, as
  `/file/<yr>/<mo>/<MMDDYY>-PC-Mtg.pdf`. `WebFetch` cannot reach web.archive.org — all fetches
  went through `polite_fetch.py`.

## What was recovered — 27 PC minutes (2020 H1 + 2021 H1)
Born-digital, header-verified Holladay Planning Commission minutes, in `raw/` +
`text/`, catalogued in `index.csv`. 16 of the 2020 gap dates + 11 of the 2021 gap dates.
Every file's meeting date was read from **inside** the PDF, not trusted from the filename.

## What is NOT available (35 dates) — honest gaps in `unrecovered.csv`
- **2020-04-07:** the source file at `…/040720-PC-Mtg.pdf` is a **mislabeled upload** — its
  content is the 2020-06-16 minutes (city error, preserved by Wayback). True 04-07 minutes not
  found anywhere. (Cross-city precedent for "city published the wrong file": st_george
  2025-10-09, orem 2025-10-15.)
- **Late-2020 (6) + 2021 H2 (9):** Wayback captured only the *packets*; the minutes were
  uploaded after the final WordPress crawl and are not exposed on the live Document Center.
- **All 2023 (19):** no PC minutes on PMN, none in Wayback (packets only), no live
  `Planning Commission/2023/` folder — appears never published in any recoverable form.

## Out of scope, retained
- `_out_of_scope/cc_2021-03-25_retreat_minutes__…pdf` — a **City Council** annual-planning
  retreat found under the WordPress PC folder (`032521-Retreat-Minutes.pdf`), header
  `HOLLADAY CITY COUNCIL ANNUAL PLANNING MEETING`. The date 2021-03-25 is **already covered by
  the audited council layer** (`meeting_minutes/`, PMN file 716411), so it is not indexed here.
  (This is the recon's "a 'Holladay PC' result was actually another body" warning realised —
  always open the header.) Retained for provenance, not part of the dataset.
- `_out_of_scope/pc_2020-04-07_minutes__ACTUALLY-0616-dup.pdf` — the mislabeled 04-07 upload.

## Merge guidance
These 27 PC minutes are **not** in `planning_commission/minutes_index.csv`. If merged, they
would fill 2020 H1 + 2021 H1 of the PC record with a non-PMN provenance (`source=wayback`,
`recovery_source` = the WordPress/Revize origin). They are held here for deliberate review;
this dataset does **not** touch the audited PC layer, `all_votes.csv`, `db/`, or `cities.db`.
