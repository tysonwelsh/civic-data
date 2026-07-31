# Kearns packets — build method, linkage, caveats

Agenda packets / staff reports for the **City of Kearns** council (+ CRA) and the
MSD-staffed Planning Commission, harvested from **Utah PMN** (the city site is
Cloudflare-blocked — see recon.md / `AVAILABILITY.md`). **Additive dataset** — nothing
in `meeting_minutes/`, `planning_commission/`, or any other layer was touched.

## What a "packet" is here

The **bundled supporting-documents PDF** attached to a meeting notice — agenda +
ordinance/resolution texts + staff analysis + exhibits — as distinct from the
separately-posted minutes, the agenda-only PDF, and the MP3 audio. Standalone **staff
reports** posted alongside a PC/Council notice (keyed to an `OAM/REZ/CUP/VAR<YYYY>-<NNNNNN>`
land-use case) are also indexed, as `packet_kind=staff_report`.

## Sources

- Council + CRA: PMN body **5823**. City-era notices carry one bundled packet each;
  township-era notices (2017–2024-06) do **not** — see `AVAILABILITY.md` gap 1.
- PC: PMN body **1561** (MSD Planning & Development). `YYMMDD_KearnsPC_Packet.pdf`
  (+ older `KearnsTPC` / `KearnsMetroTC` / `Kearns_Packet_Final` variants) + case staff reports.

## Build steps (reproduce)

```
# 1. Enumerate every notice + attachment from the cumulative PMN list, classify each.
python3 crawl_notices_kearns.py 5823 Council   # -> _candidates_5823.csv
python3 crawl_notices_kearns.py 1561 PC        # -> _candidates_1561.csv
#    (PACKET / STAFF_REPORT kept; AGENDA / MINUTES / AUDIO / CANCELLED / NOTICE dropped)

# 2. HEAD-size every keep candidate (polite_fetch --size-only) -> _sizes.csv
#    fetchable ones -> _sized_keep.csv + _download_batch.txt ; 404s -> unrecovered.csv

# 3. Fetch (STORED; 584 MB < budget) into raw/<date>/, one consolidated fetch log:
python3 ../../.claude/skills/expand-city-sources/scripts/polite_fetch.py \
    --batch _download_batch.txt --out raw --now 2026-07-13T00:00:00Z

# 4. Text sidecars (feeds cities.db fts_packet on the next build_cities_db.py):
python3 ../../scripts/extract_packet_text.py kearns

# 5. Build index.csv (reads _sized_keep.csv + raw/_fetch_log.jsonl + text/_extraction_log.csv):
python3 build_packets_index_kearns.py

# 6. Validate:
python3 ../../.claude/skills/expand-city-sources/scripts/validate_dataset.py .
```

`build_packets_index_kearns.py` is idempotent; re-run it after extraction to pick up the
real `format`/`extraction_method` per file. Only STORED (fetched-ok) rows enter
`index.csv`; the 404-purged files live in `unrecovered.csv`.

## index.csv schema (SCHEMA_SPEC §9 packets contract + extras)

`date,title,body,meeting_type,packet_kind,source_url,retrieved_date,format,
extraction_method,path` then extras `pmn_body_id,pmn_file_id,size_mb,stored_locally`,
then the §9 primary-document text columns `doc_class,fetch_status,sha256,text_path,
text_chars` (added 2026-07-16 — see "Primary-document text layer" below).

- `date` = the meeting/event date (from the PMN notice), not the posting date. Some
  filenames carry a typo year (e.g. `01-12-2025 …` on the 2026-01-12 notice) — the
  `date` column is the true event date; `title` preserves the verbatim filename.
- `body` ∈ Council | CRA | PC. `packet_kind` ∈ full_packet | staff_report.
- `format` = text (79) | scanned (1: `AgendaPacket07082024.pdf`, image-only, no sidecar).
- `path` is dataset-relative including `raw/` (e.g. `raw/2026-05-11/…pdf`).

## Linkage

- **Council/CRA** packets join to `meeting_minutes/all_votes.csv` (and the CRA rows once
  acquired) by **date + body** — the packet is the "why" behind that night's motions.
  Council meets 2nd Monday; the packet date matches the meeting date.
- **PC** packets join to `planning_commission/` by **date**, and to the referral chain by
  the **`OAM/REZ/CUP/VAR` case number** in the staff-report filename/title (the same case
  keys the PC uses to recommend to Council).
- No motion-number linkage is computed here (that is the `ordinances/` dataset's job);
  packets are keyed by meeting date, not by a specific vote.

## Primary-document text layer (`doc_class`, PRIMARY_DOCS_ROLLOUT Source 7, 2026-07-16)

Kearns is a **Bucket A-lite / classify-in-place** city: every raw PDF is already
STORED on disk with a born-digital text sidecar under `text/`, so this layer only
ADDS the §9 columns — **nothing was fetched**. `classify_attachments.py` is
deterministic + rerunnable (idempotent; re-run any time): it verifies each broken-out
staff-report row against its sidecar's **MSD staff-report template header** (Meeting
Body + Meeting Date + a "Staff Report"/"Staff Recommendation:" field) and writes:

- `doc_class` — `staff_report` | blank (blank = honestly unclassified). **10 rows**
  carry `staff_report`; the other 70 are blank.
- `fetch_status` = `ok` on every classified row (text already extracted on disk).
- `sha256` — hash of the STORED raw binary at `path` (provenance).
- `text_path` / `text_chars` — the existing `text/<stem>.txt` sidecar + its char count.

**Whole-class ground truth (n=10): all 10 verified as genuine MSD land-use staff
reports** — each carries the template header and keys to an `OAM/REZ/CUP` land-use
case (or Titles 18/19 zoning-code revision). Whole-class precision = 10/10.

### The container boundary decision (explicit)
**The 71 `full_packet` CONTAINERS are NOT row-labeled** — a container is not a
`staff_report` even when its content is mostly one MSD staff report; its full-packet
text sidecar already serves FTS. Only the broken-out per-item staff-report rows
(`packet_kind=staff_report`, 9 of them: PC 8 / Council 1) are `doc_class`-labeled,
**plus one recall-gate catch** (below). The **1 scanned council packet**
(`AgendaPacket07082024.pdf`, 2024-07-08, `format=scanned`, no sidecar) is a container
and stays unlabeled regardless.

### Recall-gate catch (1) — documented exception, not a bug
`OAM2025-001330 - P.C. packet.pdf` (**2025-03-03, PC**) carries `packet_kind=full_packet`
from the build (its filename says "P.C. packet"), but its sidecar is decisively a
**single standalone MSD staff report** — one "Meeting Body:", the header at the top,
no agenda/roll-call markers, one item (an ordinance amendment to §§19.14.070 /
19.42.350, Vehicle & Equipment Repair). The classifier re-detects this
deterministically (`is_mis_shelved_standalone_sr`) and labels it `doc_class=staff_report`.
Its native `packet_kind` is left **verbatim** as `full_packet` (build-column, not
overwritten); the content class lives in `doc_class`. It joins PC motion #4 on
2025-03-03 (`file #OAM2025-001330`).

### Honest-empty classes
`member_memo`, `plan_amendment`, `development_agreement` are **honest empties** for
Kearns — no broken-out instances exist (verified 2026-07-16 by a title sweep of all
80 rows + a sidecar-head scan). The DA mentions that occur in the corpus are all
*inside* `full_packet` containers (agenda supporting-documents bundles), not standalone
instruments, so they correctly stay unlabeled — their full-packet text already serves
FTS. `general_plan` (class 3) lives in `housing_plans/`, not here.

### Rerun
```
python3 classify_attachments.py            # classify + rewrite index.csv (idempotent)
python3 classify_attachments.py --dry-run  # report counts, write nothing
```

## Caveats

- **Coverage is city-era-forward for council** (bundled council packets start 2024-07;
  a lone 2023-04-18 staff report aside). Township-era supporting material exists on PMN
  only as loose per-ordinance files → belongs to `ordinances/`, not here. See
  `AVAILABILITY.md`.
- **PC packet history is deep (2019→2026 stored; 2011→2018 purged/404).** The purge
  boundary (`file_id < ~457000`) is the same PMN file-rot that clipped the minutes
  back-catalog.
- Bundled packets embed maps/plats/site plans — `pdftotext` sidecars carry the text but
  the graphics need vision/OCR; the corpus screener's `ends_mid` / `weird_char`
  advisories on these files are expected (mixed text+graphics), not extraction defects.
- Helper artifacts (`_candidates_*.csv`, `_sizes.csv`, `_sized_keep.csv`,
  `_download_batch.txt`) are retained for provenance/reproducibility; they are not part of
  the §9 contract.
