# Draper — pmn_backfill availability (checked 2026-07-13)

**What was checked:** the full Utah Public Notice (`utah.gov/pmn`) notice history for
Draper City (entity **114**), via one cumulative GET per body
(`/pmn/list/notices.html?id=<body>&page=200` — returns the body's entire history;
the historical *search* is POST/CSRF and was never used). Bodies crawled: City
Council **5555** + defunct **379**, Planning Commission **383**, CRA **7261** +
CRA-formerly-RDA **382**, Municipal Building Authority **381**, Historic
Preservation Commission **380**, Zoning Administrator **6647**, Board of
Adjustments **378**. Raw discovery HTML retained in `raw/_disc_*.html` /
`raw/_notices_*.html`; parsed intermediate in `raw/_parsed_notices.json`.

**What exists / was recovered (6 meetings, 7 files):**
- Council 2021-07-20, PC 2020-12-10, PC 2024-10-10 — the repo's three
  broken-Granicus-stub gaps, all recovered from PMN.
- Council 2022-08-24, 2024-08-14 (posted twice, byte-identical), 2025-08-13 —
  August **Truth-in-Taxation special sessions absent from Granicus entirely**;
  PMN is their only public source.

**What does NOT exist on PMN (honest gaps, re-checked 2026-07-13):**
- Council **2026-07-07** adopted minutes — PMN carries only the agenda/packet
  and the tally-only Recap (same as Granicus). Re-check after adoption.
- PC **2026-06-11 / 2026-06-25 / 2026-07-09** — pending adoption; PMN PC minutes
  stop at 2026-05-28.
- Council **2023-10-15** — no such doc on PMN; PMN + repo both hold 2023-10-17
  (the Granicus 10-15 listing looks like a phantom row for the 10-17 meeting).
- Board of Adjustments minutes — none ever posted (5 notices, 0 minutes).

**Stale log row noticed (not edited — audited layer untouched):**
`planning_commission/minutes_unrecovered.csv` still lists 2024-03-14 as
`no_minutes_posted`, but the meeting IS in `planning_commission/minutes_index.csv`
(Granicus doc). PMN also holds it (file 1133863). Maintainer should drop the row.

**Separate Granicus bodies (RDA/MBA/CRA/HPC/ZA):** PMN holds a thinner mirror
than Granicus (per-year inventory in `coverage.md`); nothing fetched — if these
bodies are ever promoted to core datasets, acquire from Granicus, using PMN only
for holes.

**Pre-2020 (below repo floor):** PMN council minutes reach back to 2013-04
(defunct body 379, incl. "Action Taken" tally sheets) and PC to 2013-04.
Inventory only; not gaps.
