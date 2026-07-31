# _ingest/ — Holladay PMN minutes acquisition (provenance / refresh)

How the 152 council + 45 PC minutes were harvested from Utah Public Notice (PMN), the
machine-readable spine (council public body **388**, PC **389**):

1. `pmn_harvest.py enum all_notices.json` — windowed POST to `utah.gov/pmn/search.html`
   (entity=Holladay, <=25 rows/window so no broken pagination) → every notice id + public
   body + event date across 2020-01-01..2026-07-12 (`all_notices.json`, 936 notices).
2. `harvest_minutes.py` — fetches each Council/PC/RDA/LBA notice detail page, keeps only
   attachments whose **Category = "Meeting Minutes"** → `minutes_manifest.json` (197 files).
3. `fetch_convert.py` — downloads each `utah.gov/pmn/files/<id>.pdf` → `<ds>/raw/`,
   `pdftotext -layout` → markdown (provenance header), **verifies each PDF header says
   HOLLADAY** before ingest, writes `<ds>/minutes_index.csv`.

To refresh: re-run step 1 with an extended end date, then 2 and 3 (all resumable — on-disk
files are skipped), then each dataset's `extract_votes.py` + `validate_votes.py`.

Known PMN-spine gap: Holladay posted PC minutes to PMN only in 2022 & 2024-2026; 2020/2021/2023
PC minutes are agenda-only on PMN (see `planning_commission/minutes_unrecovered.csv`).
