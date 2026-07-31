# packets/ — availability & gap record (Murray)

**As-of:** 2026-07-13 · **Sources:** CivicPlus / CivicEngage Central Archive Center +
DocumentCenter, `https://www.murray.utah.gov` (serves fine to a browser UA; no bot-block
encountered). **Mode:** **INDEX-ONLY** (documented allowed exception — see below).

## Headline verdict
Murray publishes **genuine bundled whole-meeting packets** for both bodies:
- **Council** — an "Agenda Packet" archive (`Archive.aspx?AMID=83`) with the full
  staff-report bundle for every Council meeting AND every **Committee of the Whole**
  work session, **continuously 2020 → 2026** (archive actually starts 2018).
- **Planning Commission** — agendas + packets in `Archive.aspx?AMID=32` through early
  2023, then (after a 2023–mid-2024 publishing collapse) full "Agenda & Packet" PDFs in
  the **DocumentCenter**, linked from the rotating page `/779/Agendas-Attachment`,
  Aug 2024 → present.

**421 documents indexed, 2020-01-02 → 2026-07-16, totalling 9.39 GB** (all 421 sized by
probe, 0 liveness failures). Because a stored copy would consume ~9.4 GB for one city,
this dataset is **INDEX-ONLY**: `index.csv` catalogs every document with a live
`source_url`, exact `content_length_bytes`/`size_mb`, and `packet_kind`; `format=na`,
`stored_locally=no`, no PDFs on disk. An LLM fetches a specific packet on demand via
`polite_fetch.py` and reads it with `pdftotext -layout` (born-digital text — verified on
two sample packets) or vision/OCR for map/plat exhibit pages. This is the same allowed
exception used for Bluffdale (217 index-only), South Jordan, and Vineyard packets; the
files are public and re-fetchable, and `raw/_fetch_log.jsonl` holds the probe provenance
for every URL.

## Size math (why index-only)
Sample HEAD probes across 2020–2026 gave means of ~26 MB (council) / ~19 MB (PC); the
full per-row probe totals **9.39 GB** (Council 4.92 GB / 232 docs; PC 4.46 GB / 186 docs;
median full_packet 16.5 MB, max 271 MB). Far over the ~1.5 GB storage budget; a blanket
`--max-bytes` cap would drop whole meetings, so none was used.

## Coverage — indexed documents by year and body

| Year | Council (incl. CoW) | Planning Commission | Other* |
|---|---|---|---|
| 2020 | 31 | 48 | 0 |
| 2021 | 23 | 44 | 2 |
| 2022 | 27 | 43 | 1 |
| 2023 | 34 | 11 | 0 |
| 2024 | 47 | 11 | 0 |
| 2025 | 46 | 20 | 0 |
| 2026† | 24 | 9 | 0 |
| **Total** | **232** | **186** | **3** |

\* Other = 2 School Coordinating Council docs (2021) + 1 MCCD Workshop packet (2022),
filed by the city inside the council packet archive; kept with faithful `body` labels.
† 2026 is partial (through the posted 2026-07-16 PC packet — a future meeting whose
packet is already published).

PC 2020–2022 counts are high because the archive carries **two documents per meeting**
(a thin agenda ~0.1–1.5 MB, `packet_kind=agenda_packet`, plus the full packet,
`packet_kind=full_packet`). Council rows are almost all `full_packet` (packets are the
archive's only doc type there); Council counts include ~2 CoW packets/month.

## The 2023 seam — packets did NOT follow the minutes into Tyler TMM
The key question this dataset answers: **2023 council packets are NOT in the Tyler TMM
seam.** While 2023 council *minutes* were diverted to the Tyler Minutes Management SPA
(only 5 of ~24 meetings recovered — see `../meeting_minutes/`), the 2023 council
*packets* stayed on the CivicPlus Archive Center: **23 distinct 2023 council/CoW meeting
dates, 34 documents**, including 18 dates whose minutes are lost
(2023-02-07 … 2023-10-17). For 2023 research, the packets are the best surviving
public record of what was before the council on those dates (agendas + staff reports —
but not outcomes; packets are pre-meeting documents and contain no votes).

## Gaps (honest, verified)
1. **PC packet gap, mid-April 2023 → July 2024.** `AMID=32` publishing collapses after
   2023-04-06: for 2023 there are full packets only for 01-05, 01-19, 02-02 (+ thin
   agendas to 04-06 and cancellation notices for 02-16, 03-16, 11-02); for
   Jan–Jul 2024 only a single 2024-03-07 packet exists. The PC met during this window
   (its 2023+ minutes are themselves unpublished — the same seam). Nothing found in the
   AgendaCenter or DocumentCenter for these dates; treated as a **publishing gap, not a
   scraper miss**. Continuous PC coverage resumes 2024-08-01.
2. **PC thin agendas stop being separately published after early 2023** — from Aug 2024
   the agenda is bundled inside the single "Agenda & Packet" PDF (still one row,
   `full_packet`).
3. **Council 2023 minutes remain lost** (see above) — the packets mitigate but do not
   replace them.
4. Two 2020-06-02 "Public Hearing - Budgeting" docs are tiny hearing notices
   (0.01/0.04 MB), kept with `packet_kind=agenda_packet`, `meeting_type=public_hearing`.
5. **Excluded from the index** (administrative, not meeting documents): AMID=83
   "Murray City Municipal Council Vacancy Application - District 1." (ADID 7549, undated)
   and AMID=32 "2023 Meeting Schedule" (ADID 6323) / "2022 Meeting Dates" (ADID 5741).
6. 14 PC rows are **cancellation notices** (`meeting_type=canceled`) — honest records
   that no meeting (and no packet) exists for those dates.

## What was checked (enumeration completeness)
- `Archive.aspx?AMID=83` (City Council Agenda Packet): 290 items, 2018→2026, one
  unpaginated listing — all harvested; 2020+ window indexed (233 rows after exclusions).
- `Archive.aspx?AMID=32` (Planning Commission agendas/attachments): 374 items,
  2009→2025 — all harvested; 2020+ indexed (160 rows after exclusions).
- `/779/Agendas-Attachment` (rotating PC page): 37 DocumentCenter "Agenda & Packet"
  links, 2024-08-01 → 2026-07-16; 28 added (9 dates already covered by identical
  AMID=32 items — byte-identity spot-verified: ADID 7904 ≡ DocumentCenter/View/15991,
  both 5,164,234 bytes).
- `/AgendaCenter` (CivicEngage AgendaCenter): categories exist (Planning Commission,
  MCCD, Hearing Officers) but hold only ~7 stale items (2017, two 2020) — **not** a
  packet source for Murray; checked per the Bluffdale lesson.
- Pre-2020 material exists (council packets to 2018, PC agendas to 2009) but is below
  this repo's 2020 data floor and was deliberately not indexed.

## Liveness / probe provenance
Every indexed URL was size-probed on 2026-07-13 — HEAD for Archive Center items; for
DocumentCenter items a **streamed GET reading headers only** (CivicPlus DocumentCenter
returns 404 to HEAD while serving GET normally — vendor quirk). Final result:
**421/421 sized, 0 failures**; log in `raw/_fetch_log.jsonl` (the early HEAD 404 records
for the 28 DocumentCenter URLs are superseded by the later streamed-GET records in the
same log). Two packet bodies were GET-verified as real born-digital packets:
2026-02-03 CoW (54 pp) and PC 2025-06-05 (153 pp, agenda + staff reports).

## Primary-document classes (doc_class rollout, 2026-07-16)

Assessed as part of the repo-wide primary-documents rollout (`PRIMARY_DOCS_ROLLOUT.md`,
Source-7 doc_class taxonomy: staff_report / exhibit / presentation / correspondence / GP text).
**Ruling: not separable WITHOUT FETCH — targeted-fetch candidate for a future owner-approved
pass.** The 339 `full_packet` rows are INDEX-ONLY (~5.6 GB, not stored). Prior probes confirmed
they are **born-digital** (a good `pdftotext` prospect), so a classify-in-place pass is
impossible until the PDFs are fetched — and **no fetch was done in this rollout** (0 classified
now). **Specific future value:** the **2023 council packets (23 dates / 34 documents)** are the
only surviving staff-analysis record of the 2023 lost-minutes (Tyler-TMM) era — those minutes
were later PMN-recovered/promoted (2026-07-16), but the packets still hold the pre-meeting staff
analysis the minutes never carried. Marked as a **targeted-fetch candidate** (the highest-value
index-only city in this rollout; a TODO note records it). Classes were assessed, not forgotten.

### DONE 2026-07-17 — targeted primary-docs fetch (2023 council set)
The highest-value set was fetched under the 2026-07-17 wave (§9 text layer). **All 34 2023
Council/CoW packets** (23 dates, ADIDs 7394–7660) were GET-fetched (browser UA, ≥1.5 s throttle,
~590 MB total), **sha256-hashed, `pdftotext -layout`-extracted, and the binaries discarded**
(the sanctioned §9 exception). Result: **34/34 `fetch_status=ok`**, born-digital, text yields
9,004–631,494 chars; text sidecars in `text/`; the 5 pilot columns
(`doc_class,fetch_status,sha256,text_path,text_chars`) appended to `index.csv`;
`raw/_primarydocs_fetch_log.jsonl` holds byte provenance. **`doc_class` left BLANK on all 34
(honest):** each is a whole-meeting BUNDLE, not a single-class primary document; the §9 taxonomy
is per-document and no machine-readable TOC anchor was present to gate a ≥95% section-cut, so
"unclassified" is the truthful value (not a miss). One byte-identical pair: 2023-10-17 CoW (7633)
≡ regular (7634), same sha256 (the city posted one combined 94 MB packet under both meeting rows).

### Future candidates (NOT fetched — recorded per the wave's "record the rest" instruction)
Highest-value first, all still INDEX-ONLY:
1. **PC packets 2024-08 → 2026 (DocumentCenter era)** and the surviving 2023 PC packets — the PC
   2023+ minutes seam; land-use staff analysis.
2. **2024–2026 council packets** (117 docs) — current land-use / rezone / development records.
3. **2020–2022 council packets** (81 docs) and **2020–2022 PC packets** — pre-seam baseline.
Optional deeper pass: **section-cutting** the fetched 2023 bundles into `packet_section` rows with
per-section `doc_class` — requires a TOC/template anchor + boundary gate (SCHEMA_SPEC §9); deferred
as the honest default until an anchor is engineered.
