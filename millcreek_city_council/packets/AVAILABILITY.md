# Agenda Packets — Availability & Coverage (INDEX-ONLY) — as-of 2026-07-06

**Dataset:** `packets/` — agenda packets / staff reports behind Millcreek **City Council**,
**Community Reinvestment Agency (CRA)**, and **Planning Commission** agenda items.
**Portal:** CivicPlus / CivicEngage **AgendaCenter** (`www.millcreekut.gov`).
**Enumeration:** `POST /AgendaCenter/UpdateCategoryList` with `{year, catID}` — catID
**3**=City Council, **7**=CRA, **2**=Planning Commission — walked for every year 2016→2026;
Agenda-row anchors parsed and classified by title. All 834 discovered AgendaCenter documents
returned **HTTP 200** on the 2026-07-06 probe (`raw/_fetch_log.jsonl`).

## The one structural fact that shapes this dataset
On Millcreek's AgendaCenter the meeting document titled **"… Meeting Agenda and Packet"** — the
combined **Agenda + full staff Packet** PDF, 4–8 MB (up to ~35 MB) — is served at the
`ViewFile/**Minutes**/_<MMDDYYYY>-<docId>` path (CivicPlus shares one `docId` across the
Agenda/Minutes "views"; the bare `ViewFile/Agenda/_…` path returns only a thin ~35 KB agenda
outline). **The `meeting_minutes/` and `planning_commission/` datasets already downloaded exactly
these combined PDFs** (that is where their minutes text comes from) — they are retained verbatim
in `../meeting_minutes/raw/` (979 MB) and `../planning_commission/raw/` (499 MB). Re-storing them
here would duplicate ~1.2 GB of already-retained originals, so this dataset is a **link + join
index**, not a second copy. `path` points each full packet at the sibling raw file
already on disk; nothing new is written to `packets/raw/` except the provenance log.

This retention exception is deliberate and scoped to this dataset: the combined packet PDFs are
public + re-fetchable from `source_url`, AND the bytes are already retained in the two sibling
datasets. The thin `agenda_packet` agendas (35 KB–~2 MB) are the only docs neither stored here nor
in a sibling; they are low-value (item list, no staff analysis), public, and re-fetchable, and
their provenance is in `raw/_fetch_log.jsonl`. (The normal "retain every raw original" rule still
governs every *other* dataset in this repo.)

## Coverage (what exists)
Index rows = 552 packet documents (notices and meeting-cancellation stubs were **excluded** — 225
notices + 57 cancellations seen in AgendaCenter, not packets; counts noted here for the record).

| Body | `full_packet` (combined Agenda+Packet) | years | `agenda_packet` (thin) |
|---|---|---|---|
| City Council | 186 | 2018–2026 | 141 |
| CRA | 54 | 2018–2026 | 9 |
| Planning Commission | 100 | 2018–2026 | 62 |
| **Total** | **340** (335 retained in sibling raw, 1.22 GB) | | **212** |

- Combined-packet sizes (from the retained sibling files): typical 4–8 MB, up to ~35 MB.
- The **"Agenda and Packet" convention began in 2018–2019**; 2016–2017 meetings posted a thin
  agenda only (no combined staff packet) — a city publishing evolution, **not a scraper miss**.

## Vote-date join coverage (`date` + `body` → `../*/all_votes.csv`)
Every distinct vote date in the minutes/PC vote tables has **at least an agenda document** indexed
here; the `full_packet` gap is concentrated entirely in the pre-2018 agenda-only era.

| Body | vote dates | with `full_packet` | full-packet gap (all have a thin `agenda_packet`) |
|---|---|---|---|
| Council | 272 | 181 | 91 — by year: 2017×40, 2018×21, 2019×8, 2020×4, 2021×5, 2022×5, 2023×1, 2024×3, 2025×3, 2026×1 |
| CRA | 58 | 52 | 6 — 2018×4, 2019×1, 2020×1 |
| Planning Commission | 130 | 96 | 34 — 2017×13, 2018×14, 2019×3, 2020×1, 2021×3 |

From 2019 forward full-packet coverage of vote dates is substantially complete (2023+ nearly
total); the shortfall is the 2017–2018 agenda-only years.

## PC packets carry the IN-PACKETS resident-comment corpus — EXTRACTED 2026-07-19
Planning Commission full packets bundle **genuine verbatim resident-comment letters** as
appendices to land-use staff reports (the Provo pattern). This dataset still only **flags where
those letters live (PC `full_packet` rows)**; the extraction now lives in `../public_comments/`.

**Note (2026-07-19): the `?packet=true` route was fetched for the comment harvest.** The `path`
column here points each PC `full_packet` at its retained **Minutes-view** sibling PDF. The much
larger **`?packet=true`** variant of the SAME `docId` (`ViewFile/Agenda/_<MMDDYYYY>-<docId>?packet=true`)
is a *different* PDF — the full staff packet with the "Public Comments from Residents" appendices.
`../public_comments/harvest_packet_true.py` fetched **all 100** PC `?packet=true` URLs (~4.8 GB;
99 ok, 1 not_pdf), extracted text, and **DISCARDED the binaries per SCHEMA_SPEC §9** (this dataset
is index-only / no-raw-duplication). Full fetch provenance — `fetch_status`, `sha256`, `bytes`,
`pages`, `text_chars` per packet — is in `../public_comments/packet_true_fetch.csv`. The
`packets/index.csv` rows were **not** modified (they remain Minutes-view-pinned by design).

## What was checked / what's absent (gaps are data)
- **Notices / cancellations** (225 + 57): present in AgendaCenter, excluded from this packet index
  (not packets). Their existence is logged in `raw/_fetch_log.jsonl`.
- **5 "Agenda and Packet"-titled items with no combined PDF posted** → `unrecovered.csv`: four are
  June-2026 meetings newer than the 2026-07-06 minutes harvest (the combined PDF will land when
  `../fetch_new.py --fetch` next runs); one, **PC 2023-12-20 (doc 757)**, is a genuine city
  publishing gap (only the agenda was posted — no combined packet, which is why the PC minutes
  dataset also lacks it). No content fabricated.
- **Pre-2016:** none — Millcreek incorporated Dec 2016; the short history is the city's entire
  record, not a gap.

## To retrieve a packet's content
1. Find the meeting in `index.csv` by `date` + `body` (+ `meeting_type`).
2. For a `full_packet`, prefer the already-retained local copy at `path`
   (`../meeting_minutes/raw/…` or `../planning_commission/raw/…`); otherwise GET `source_url`.
3. These PDFs are **OCR-grade / bad-text-layer** (see the city `CLAUDE.md` OCR caveat) and
   image/map/plat-heavy in the packet portion — read with OCR/vision, not clean `pdftotext`.

## Primary-document classes (doc_class rollout, 2026-07-16)

Assessed as part of the repo-wide primary-documents rollout (`PRIMARY_DOCS_ROLLOUT.md`,
Source-7 doc_class taxonomy: staff_report / exhibit / presentation / correspondence / GP text).
**Ruling: not separable.** The stored "packets" here are the combined Agenda+Packet PDFs
already retained via the sibling minutes `raw/`, and they are **minutes-grade OCR text** —
sampled bundles contained minutes, not cleanly-separable staff packets; the packet↔minutes
muddle is a characteristic of Millcreek's CivicPlus/CivicEngage portal (one shared `docId`
serves both the Agenda and Minutes views). Net-new text beyond the existing minutes FTS is
low, so no per-class `packet_section` rows were created. **NOTE:** the PC `full_packet`
resident-comment letters remain a **separate pending `public_comments` Provo-style harvest**
(already queued — see `../public_comments/AVAILABILITY.md` and TODO), not part of this
doc_class ruling. Classes were assessed, not forgotten.
