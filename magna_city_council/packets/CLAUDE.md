# packets/ — Magna agenda packets & staff reports (STORED)

Additive `expand-city-sources` dataset (source type 1). **Read `AVAILABILITY.md`
first** for coverage, the size math, the STORED decision, and the honest gaps. This
file documents the **build**. Purely additive — it modifies no existing dataset and no
parent doc.

## What this is
**297 agenda packets** (1.2 GB on disk) for Magna **City Council**, in-session **CRA**
(Community Reinvestment Agency), and **Planning Commission (PC)** — the staff-analysis
layer that joins to `meeting_minutes/` + `planning_commission/` + `all_votes.csv` by
**date + body (+ meeting_type)**. Recorded roll-call minutes are NOT here (core repo).

Two portals feed it (see `AVAILABILITY.md` for the full rationale):
- **CivicPlus AgendaCenter** cat3 (`magna.utah.gov`), `?packet=true` — Council + CRA,
  **2022+** (142 packets). Only cat3 exists; body is split by title (CRA vs Council).
- **Utah PMN** — body **5803** (council, used **pre-2022** only) + body **1559**
  (Planning Commission, **all years**); files from `www.utah.gov/pmn/files/<id>.pdf`
  (155 packets). PMN is the ONLY source of PC packets.

## index.csv schema
§9 packets contract header (exact, `validate_dataset.py`-enforced):
```
date,title,body,meeting_type,packet_kind,source_url,retrieved_date,format,extraction_method,path
```
then Magna extras (AFTER the contract cols):
```
source,content_length_bytes,size_mb,stored_locally,pmn_notice_id,pmn_filename
```
then the **primary-document section-layer** extension cols (added 2026-07-16, AFTER the
Magna extras — see "Primary-document section layer" below):
```
doc_class,fetch_status,sha256,text_path,text_chars,parent_path,section_seq,case_key
```
These are **blank on the 297 parent packet rows** (which are untouched) and populated
only on the 204 `packet_kind=packet_section` rows.
- `body` ∈ Council | CRA | PC.
- `meeting_type` ∈ regular | work | special (parsed from title/filename).
- `packet_kind` = `full_packet` (assembled packet / supporting docs / staff report) or
  `agenda_packet` (a thin agenda when no assembled packet was posted).
- `source` ∈ civicplus | pmn (extra col). `stored_locally=yes` for every row.
- `format` ∈ text (born-digital, 295) | scanned (image-only, 2 — vision/OCR to read).
- `path` is dataset-relative **including `raw/`** (`raw/<date>/<key>.<ext>`); `<key>` is
  the globally-unique source id (CivicPlus item id `MMDDYYYY-<seq>` / PMN file id), so
  `text/<stem>.txt` sidecar stems never collide.
- `pmn_notice_id` / `pmn_filename` are blank for CivicPlus rows.

## unrecovered.csv
**52 PC 2017–2018 packet files that HEAD-404** — the documented 2017–mid-2018 PMN blob
purge (`reason=pmn_purged_404`). The notice still lists the file; the blob is gone.
Kept as honest rows (never stubbed into the index), with the dead `source_url` + PMN
ids for a future re-check.

## Primary-document section layer (PRIMARY_DOCS_ROLLOUT, 2026-07-16)

Magna is a **Bucket-B SEPARABLE** city: the monolithic PMN packet PDFs bundle one MSD
land-use **staff report** per agenda item, each rendered from the Greater-SLC Municipal
Service District "Summary and Recommendation" template (same family as kearns/copperton/
white_city). `split_sections.py` cuts those staff reports out of the existing full-packet
text sidecars into **204 additive `packet_kind=packet_section` index rows** + one text
file each under `text/sections/`. The 297 parent `full_packet` rows are **untouched**;
this is a deterministic in-place slice of the parent's `pdftotext -layout` sidecar — **no
new fetch, no new binary**.

**Yield:** 204 sections — **PC 186** (78 packets) + **Council 18** (17 packets; the
2019–21 township-era PMN council packets that carry the PC-forwarded staff report) +
**CRA 0**. Total section text ≈ 51.7 M chars. By year: 2019×29, 2020×43, 2021×33,
2022×33, 2023×29, 2024×17, 2025×15, 2026×5.

**Three template eras, one anchor.** All eras open each staff report with a metadata
cluster whose stable line is `Public Body:`/`Meeting Body: Magna … [Council|Planning]`:
- **2018–2019 township** — bare `File # NNNNN` (SLCo Planning & Development Services),
  `Public Body: Magna Metro Township …`. Case keys are recorded as `FILE<n>`.
- **2020–2023 mid** — case-keyed `Files # REZ2022-000725`, `<Type> Summary and
  Recommendation` heading.
- **2024+ city** — two-column `Meeting Body: Magna City Planning Commission`,
  `Project Name and File Number: OAM2024-…`.

**Splitter design (`split_sections.py`).** Anchor = `(?:Public Body|Meeting Body):\s*Magna`
**confirmed** by a `Planner:` / `Planning Staff Recommendation:` / `Staff Recommendation:` /
`Meeting Date:` within 14 lines (deduped when two anchors sit <5 lines apart — kills the
two-column duplicate). Section **start** = scan ≤16 lines above the anchor and begin at the
MSD address boilerplate → else the `File(s) #` line → else the `…Summary…` heading → else
the anchor. Section **end** = the next section's start (exclusive) or EOF, so a staff
report's trailing maps/plats/exhibits ride with it. `case_key` = first
REZ/SUB/OAM/CUP/VAR/RWD token, else a bare `File #` → `FILE<n>`, else blank. Modes:
`python3 split_sections.py` (census), `--sample STEM` (verbatim boundary dump), `--write`
(idempotent: drops prior section rows + wipes `text/sections/`, regenerates).

**Section-row column semantics** (the 8 extension cols):
- `packet_kind=packet_section`, `format=text`, `extraction_method=section_split`
  (a deterministic line-slice of the parent sidecar — not a re-extraction).
- `doc_class=staff_report` for **all** 204 (the cut anchor is literally the staff-report
  template). `fetch_status=ok`.
- `sha256` is **BLANK by design** — §9 semantics: `sha256` = a fetched **binary** hash;
  a text slice has no binary. Byte provenance lives on the parent row + `raw/_fetch_log.jsonl`.
- `stored_locally=no` — describes the (absent) standalone binary; the bytes live in the
  parent PDF, whose path this row's `path`/`parent_path` point at (both = the parent raw
  PDF, which exists on disk → `validate_dataset.py` path check passes).
- `text_path=text/sections/<parent_stem>__<NN>_<case>.txt`, `text_chars`, `section_seq`,
  `case_key` (blank on the 26 unkeyed sections — text amendments / items with no printed
  case number; still cut, seq-named).

**Honest zeros / exclusions.** All **19 CRA** files and the **123 CivicPlus council** thin
agendas carry no MSD staff-report block → 0 sections (200 of 295 sidecar files yield zero,
correctly). The **2 scanned** image-only packets (`05132025-143` CRA 2025-05-13,
`07092024-38` Council 2024-07-09) have no sidecar → skipped.

**Two plan-document-dominated OAM sections (documented, kept as `staff_report`).** Because
each section swallows its trailing exhibits, two OAM sections are dominated by an **embedded
plan document**, not staff prose: `OAM2022-000776` (2023-04-13, ~1.2 M chars — a Title-19
code element) and `OAM2024-001175` (2024-06-13, ~0.9 M chars — the **Magna Historic District
Area Plan**, a General-Plan element). They stay `doc_class=staff_report` for uniformity;
the **standalone plan documents are class-3 (`general_plan`) candidates for a future
`housing_plans/` capture** — NOT duplicated into `housing_plans/` in this wave.

**Verification gate (2026-07-16).** Invariant sweep over all 204: every section text ==
its parent slice (0 fails) and contains **exactly one** confirmed anchor → no bleed / no
missed split (204/204). Random **n=50** ground-check (legit section-start first line + own
case key present): **50/50 = 100%**. All sections of the 6 boundary-sample packets
(457049, 673399, 927579, 1132341, 520769, 709677) + the 2 OAM giants verified end-to-end.
`validate_dataset.py` → **PASS**. `screen_corpus.py` weird-char/dict outliers are the
plat/CAD/map exhibit pages riding with staff reports (parent corpus already screen-clean;
slices add no new extraction).

**Acceptance (Sharkey pattern).** Section `text/sections/908569__03_CUP2022-000691.txt`
("The applicant, Christina Robles, is applying for a conditional use for a home day care.
Per section 19.04.293 of the Magna Code …", 7212 W Majestic Way, MSD Planner Justin Smith)
joins **PC vote 2022-11-10 motion #4** ("To approve application #CUP2022-000691 …",
result `Pass (dissent: Cripps)`, Cripps=Nay) by date+case — the primary staff analysis
behind a **contested** PC recommendation.

## Build (reproduce — all scripts live here, unique `_magna` names, idempotent)
1. **Enumerate** (browser UA) into `raw/_listings/`: CivicPlus
   `UpdateCategoryList?catID=3&year=<YYYY>` for 2022–2026, and the PMN cumulative
   `notices.html?id={5803,1559}&page=400`.
2. `python3 build_packets_catalog_magna.py` → `raw/_catalog.tsv` — parse both portals,
   classify body + meeting_type + packet_kind, select one best packet file per PMN
   notice (filename priority packet > supporting > staff report > agenda).
3. `python3 size_packets_magna.py` → `raw/_sizes.tsv` — HEAD-probe every packet URL for
   `Content-Length`; append each probe to `raw/_fetch_log.jsonl`. **PMN files that
   HEAD-404 here are the purged ones** (verified genuine 404 via GET, not a HEAD-only
   quirk).
4. `python3 fetch_packets_magna.py` → `raw/<date>/<key>.<ext>` + `raw/_fetched.tsv` —
   throttled GET of every live (200) packet via the shared `polite_fetch.fetch`,
   sha256 + provenance to `raw/_fetch_log.jsonl`. Idempotent (skips keys already on
   disk).
5. `python3 ../../scripts/extract_packet_text.py magna` → `text/<stem>.txt` +
   `text/_extraction_log.csv` (the born-digital `.docx` sidecar is written by
   `build_index_magna.py`'s companion step — a `word/document.xml` strip — since the
   shared extractor only handles `.pdf`).
6. `python3 build_index_magna.py` → `index.csv` + `unrecovered.csv` (joins
   catalog + sizes + fetch manifest + extraction log; sets `format=scanned` for
   `image_only` stems). **Re-run after extraction** so formats reconcile.
7. `python3 ../../.claude/skills/expand-city-sources/scripts/validate_dataset.py .` →
   **PASS**.
8. **Section layer (additive, idempotent):** `python3 split_sections.py --write` →
   204 `packet_section` rows appended to `index.csv` + `text/sections/*.txt`. Re-runnable
   (drops prior section rows + wipes `text/sections/` first). Re-run
   `validate_dataset.py .` after. See "Primary-document section layer" above.

## Provenance (retained in raw/)
- `raw/_fetch_log.jsonl` — 646 lines: 349 HEAD size-probes + 297 fetch records
  (url, status, bytes, sha256, saved_as, utc).
- `raw/_listings/` — the CivicPlus year listings (`cat3_20*.html`) + the two PMN
  cumulative notice pages (`pmn_5803_notices.html`, `pmn_1559_notices.html`).
- `raw/_catalog.tsv`, `raw/_sizes.tsv`, `raw/_fetched.tsv` — build intermediates.

## Linkage to the rest of the repo
Join a packet to `meeting_minutes/all_votes.csv` / `planning_commission/all_votes.csv`
/ the minutes markdown by **date + body (+ meeting_type)**. Council/CRA packets pair
with the Council/CRA minutes; PC packets with the PC minutes. Because the core minutes
have honest gaps (2017 + Jan–Jun 2018 council unrecoverable; PC votes start 2019-03-14),
a packet sometimes exists for a meeting whose recorded minutes do not — it is then the
only staff-analysis record for that date. The sidecars feed `cities.db` `fts_packet`
on the next `build_cities_db.py` (run by the orchestrator, not here).

## Caveats
- Not the recorded minutes; **no votes here**. The presiding-officer voting seam
  (voting Chair ≤2025 → non-voting Mayor 2026+) is a `meeting_minutes/` concern; a
  packet linkage must not treat the Mayor as a normal voter.
- PMN attachment **labels are unreliable** — classification is by filename; a future PMN
  re-crawl should re-run step 2, not trust the "(…)" labels.
- 2 CivicPlus packets are image-only scans (no sidecar). A handful of duplicate-content
  uploads are retained faithfully (see `AVAILABILITY.md` §6).
