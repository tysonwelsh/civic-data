# packets/ — availability & gap record (Bluffdale)

**As-of:** 2026-07-13 · **Source:** CivicPlus / CivicEngage Central AgendaCenter,
`https://www.bluffdale.gov` (no bot-block; browser UA used as courtesy).
**Mode:** **INDEX-ONLY** (documented allowed exception — see below).

## Headline verdict
Bluffdale publishes a **genuine full staff-report PACKET for every regular
City Council and Planning Commission meeting**, 2020 → present. These are
**bundled whole-meeting PDFs** (agenda + all staff reports + all exhibits: maps,
plats, site plans, fiscal notes) — median **6.1 MB**, max **144 MB**, **217
packets totalling 2.85 GB**. Because a stored copy would consume ~2.85 GB of disk
for one city, this dataset is built **INDEX-ONLY**: `index.csv` catalogs every
packet with a **live `source_url`**, exact `content_length_bytes`/`size_mb`, and
`packet_kind=full_packet`; `format=na`, `stored_locally=no`, no PDFs on disk. An
LLM fetches a specific packet on demand via `polite_fetch.py` and reads it with
`pdftotext` (born-digital staff-report text) or vision/OCR (the map/plat exhibit
pages). `raw/_fetch_log.jsonl` holds the HEAD-probe provenance for all 217 URLs.

This is the same allowed exception used for South Jordan and Vineyard packets.
The files are public and re-fetchable; retaining a live index + sizes + provenance
satisfies the spirit of "retain every raw original" without the disk cost.

## Is there a distinct "packet" document type on this CivicEngage site?
**No dedicated doc-type — but a real packet document exists.** The AgendaCenter
`ViewFile` endpoint exposes only two doc-types: **`Agenda`** and **`Minutes`**
(no `AgendaPacket`/`Packet` type; the DocumentCenter holds no parallel
"Agenda Packets" area either). Bluffdale uploads the full packet **as an
additional `Agenda`-type document**, distinguished only by the word
**"PACKET"/"Packet"** in its title (e.g. *"Bluffdale City Council Meeting Agenda
10-08-2025 PACKET"*, *"Planning Commission Packet 05-07-2025"*, older 2020 form
*"…Agenda and Packet"*). So on each regular meeting date the portal carries BOTH
a **thin agenda** (the row that also has the Minutes link) AND a **separate full
PACKET** row. This dataset indexes the **PACKET** rows only. Enumeration is via
the reliable Search endpoint (`/AgendaCenter/Search/?CIDs=<2|3>%2C&startDate=…&
endDate=…`), harvesting labeled `<a>` links — internal ids are not derivable and
were never guessed.

## Coverage — packets present (full_packet count) by year and body
Both bodies publish full packets across the entire 2020→2026 window. Counts
track meeting cadence (Council 2nd/4th Wed ≈ 18–21/yr; PC 1st/3rd Wed ≈ 9–15/yr),
**not** a publishing gap.

| Year | Council | Planning Commission |
|---|---|---|
| 2020 | 21 | 12 |
| 2021 | 21 | 15 |
| 2022 | 20 | 11 |
| 2023 | 21 | 9 |
| 2024 | 17 | 14 |
| 2025 | 18 | 15 |
| 2026* | 14 | 9 |
| **Total** | **132** | **85** |

\*2026 is partial (through the 2026-07-15 posted PC packet).

## Council vs Planning Commission asymmetry
**None in publishing behavior.** Both the Council and its own Planning Commission
publish a full staff-report packet for every regular meeting, every year in the
window. The Council carries more packets (132 vs 85) purely because it meets more
often and its packets bundle the in-session **RDA + LBA** business into the same
document. Total indexed volume: Council 1.73 GB / 132 docs; PC 1.12 GB / 85 docs.

## What is NOT a packet (excluded, by design)
The Search endpoint returns many other `Agenda`-type rows that are **not**
staff-report packets and are excluded from `index.csv`:
- **Thin meeting agendas** — the 1–2 page outline that carries the Minutes link
  (the canonical minutes are already in `meeting_minutes/` / `planning_commission/`).
- **Individual `NOTICE OF PUBLIC HEARING` / budget-amendment / text-amendment
  notices**, election notices (sample ballots, certified candidate lists, canvasser
  reports), cancellations, quorum notices, audit-report notices.
These were classified out by title (a packet title contains "PACKET"/"Packet";
everything else is an agenda/notice). The excluded thin agendas are the
"agenda-IS-the-packet" fallback that other cities rely on — **not needed here**
because Bluffdale posts true full packets.

## Gaps / caveats
- **No gap in the packet record itself.** Every regular meeting date in the
  2020→2026 minutes has a corresponding full packet on the portal.
- A handful of non-regular meetings (special/work-session, canvasser, cancelled)
  have only a thin agenda and no full packet — expected (no staff-report bundle is
  produced for those), not a scraper miss. 210 regular / 5 special / 2 work_session
  in the index.
- **Index-only means the PDFs are not on disk.** To read a packet, fetch its
  `source_url` through `scripts/polite_fetch.py` (browser UA); it returns
  `application/pdf`. Born-digital packets extract with `pdftotext -layout`; the
  large map/plat-heavy ones require vision/OCR for the exhibit pages.
- Sizes and liveness were HEAD-probed for all 217 URLs on 2026-07-13 (0 failures);
  see `raw/_fetch_log.jsonl`.

## Primary-document classes (doc_class rollout, 2026-07-16)

Assessed as part of the repo-wide primary-documents rollout (`PRIMARY_DOCS_ROLLOUT.md`,
Source-7 doc_class taxonomy: staff_report / exhibit / presentation / correspondence / GP text).
**Ruling: not separable WITHOUT FETCH — future targeted-fetch candidate.** The 217 `full_packet`
rows are INDEX-ONLY (~2.85 GB, not stored) and **born-digital** per prior probes. A
classify-in-place pass is impossible until the PDFs are fetched.

## Targeted text-layer fetch (2026-07-17, wave-2)

A **bounded high-value set of 60 full_packet rows** was fetched, text-extracted, and the
binaries DISCARDED (the sanctioned §9 text-only-corpus exception). Selection = packets on the
Council/PC meeting dates that carry a **contested vote** (named Nay/Abstain/Recuse **or** a
tally with nays) or a **land-use motion**, contested-first, ≤40 MB, capped at 60 (~531 MB of
PDF fetched → discarded). All 60 came back **born-digital** (`fetch_status=ok`, 0 needs_ocr,
0 error). Text sidecars live under `text/<slug>.txt`; the five §9 pilot columns
(`doc_class,fetch_status,sha256,text_path,text_chars`) are populated on these 60 rows; the
other 157 rows stay index-only (blank pilot columns).

- **`doc_class` is left BLANK on all 60** — a Bluffdale packet is a **whole-meeting bundle**
  (agenda + every staff report + all map/plat exhibits in one PDF), which does not map to any
  single §9 class at ≥95% precision. Per the "blank when unsure" rule this is the honest
  classification; it matches the cottonwood_heights/magna convention of leaving `full_packet`
  parents blank. **No section-cutting** was done — Bluffdale packets have no rigid
  machine-readable TOC/template anchor to cut on at high precision (the honest default), so the
  searchable artifact is the whole-packet sidecar (`text_path`), not per-section rows.
- **One pathology handled:** the 2020-01-08 PC packet (docid 703) made `pdftotext -layout`
  emit a degenerate 858 MB whitespace blob; re-extracted with plain `pdftotext`
  (`extraction_method=pdftotext_raw`) → 489 K clean chars. All other 59 used `pdftotext`
  (`-layout`).
- HEAD-probe provenance for the whole index remains in `raw/_fetch_log.jsonl`; the 60 targeted
  GETs (bytes/sha256/status) are logged in `raw/_targeted_fetch_log.jsonl`.
- Remaining candidate (not fetched): the 12 oversize (>40 MB) contested/land-use packets +
  the land-use-only dates beyond the cap. Lower priority than murray's lost-minutes-era packets.
